"""Thread-safe in-memory feature store for the recommendation demo.

In production this class would be backed by a real feature store or database
(Feast, Redis, a columnar warehouse, ...). For the assignment it keeps a small
user-item interaction matrix in memory so the architecture is trivial to run
locally and in tests.

The store owns three pieces of state, all guarded by a single re-entrant lock:

* ``_matrix``     - the user x item interaction-weight matrix.
* ``_similarity`` - the item x item cosine-similarity matrix (derived).
* event bookkeeping (count + last-seen timestamp) for observability.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

from reco.domain.exceptions import (
    InvalidActionError,
    UnknownItemError,
    UnknownUserError,
)

# Action weights: stronger purchase-intent signals carry more preference weight
# than lighter browsing signals.
DEFAULT_ACTION_WEIGHTS: dict[str, float] = {
    "view": 1.0,
    "click": 2.0,
    "cart": 3.0,
    "purchase": 5.0,
}

_DEFAULT_USERS: tuple[str, ...] = tuple(f"u{i}" for i in range(1, 61))
_DEFAULT_ITEMS: tuple[str, ...] = tuple(f"P{i:02d}" for i in range(1, 41))
_SEED_RNG = 546


@dataclass(frozen=True, slots=True)
class FeatureStoreStats:
    """Lightweight snapshot of store state for health/metrics responses."""

    users: int
    items: int
    events_processed: int
    matrix_density: float
    last_event_at: str | None


@dataclass(frozen=True, slots=True)
class EventResult:
    """Result of applying one activity event to the matrix."""

    user_id: str
    item_id: str
    action: str
    weight: float
    event_count: int
    processed_at: str


class FeatureStore:
    """Holds user-item interactions and derived item-item similarity.

    The store is safe to share between the API worker and the background event
    consumer: every public method that touches shared state acquires ``_lock``.
    """

    def __init__(
        self,
        users: tuple[str, ...] = _DEFAULT_USERS,
        items: tuple[str, ...] = _DEFAULT_ITEMS,
        action_weights: dict[str, float] | None = None,
    ) -> None:
        self._users: tuple[str, ...] = tuple(users)
        self._items: tuple[str, ...] = tuple(items)
        self._user_index: dict[str, int] = {u: i for i, u in enumerate(self._users)}
        self._item_index: dict[str, int] = {p: i for i, p in enumerate(self._items)}
        self._action_weights: dict[str, float] = dict(
            action_weights if action_weights is not None else DEFAULT_ACTION_WEIGHTS
        )

        self._lock = threading.RLock()
        self._matrix: NDArray[np.float64] = np.zeros(
            (len(self._users), len(self._items)), dtype=np.float64
        )
        self._similarity: NDArray[np.float64] = np.zeros(
            (len(self._items), len(self._items)), dtype=np.float64
        )
        self._event_count = 0
        self._last_event_at: str | None = None
        self._seeded = False

    # -- read-only accessors -------------------------------------------------

    @property
    def users(self) -> tuple[str, ...]:
        return self._users

    @property
    def items(self) -> tuple[str, ...]:
        return self._items

    @property
    def action_weights(self) -> dict[str, float]:
        return dict(self._action_weights)

    def has_user(self, user_id: str) -> bool:
        return user_id in self._user_index

    def has_item(self, item_id: str) -> bool:
        return item_id in self._item_index

    # -- lifecycle -----------------------------------------------------------

    def reset(self) -> None:
        """Clear all state and return the store to an empty, unseeded matrix."""
        with self._lock:
            self._matrix = np.zeros((len(self._users), len(self._items)), dtype=np.float64)
            self._similarity = np.zeros((len(self._items), len(self._items)), dtype=np.float64)
            self._event_count = 0
            self._last_event_at = None
            self._seeded = False

    def seed_demo_data(self) -> None:
        """Create repeatable, clustered shopping behaviour for the local demo.

        Users are split into four taste clusters. Each user interacts mostly with
        products from their own cluster plus a few from a neighbouring cluster,
        which gives the recommender a learnable signal. Idempotent.
        """
        with self._lock:
            if self._seeded:
                return
            rng = np.random.default_rng(_SEED_RNG)
            cluster_size = max(1, len(self._items) // 4)

            for user_index in range(len(self._users)):
                cluster = user_index % 4
                core_start = (cluster * cluster_size) % len(self._items)
                neighbour_start = (((cluster + 1) % 4) * cluster_size) % len(self._items)
                core_items = np.arange(core_start, core_start + cluster_size) % len(self._items)
                neighbour_items = np.arange(neighbour_start, neighbour_start + cluster_size) % len(
                    self._items
                )

                n_core = min(7, len(core_items))
                n_neighbour = min(2, len(neighbour_items))
                selected_core = rng.choice(core_items, size=n_core, replace=False)
                selected_neighbour = rng.choice(neighbour_items, size=n_neighbour, replace=False)

                for item_index in np.concatenate([selected_core, selected_neighbour]):
                    self._matrix[user_index, item_index] += float(
                        rng.choice([1.0, 2.0, 3.0, 5.0], p=[0.25, 0.35, 0.25, 0.15])
                    )
                    self._event_count += 1

            self._refresh_similarity_locked()
            self._seeded = True

    # -- validation ----------------------------------------------------------

    def validate_event(self, user_id: str, item_id: str, action: str) -> None:
        """Validate a storefront activity event before it reaches the model."""
        if user_id not in self._user_index:
            raise UnknownUserError(f"unknown user_id: {user_id}")
        if item_id not in self._item_index:
            raise UnknownItemError(f"unknown item_id: {item_id}")
        if action not in self._action_weights:
            allowed = ", ".join(sorted(self._action_weights))
            raise InvalidActionError(f"invalid action: {action} (allowed: {allowed})")

    # -- writes --------------------------------------------------------------

    def track_event(self, user_id: str, item_id: str, action: str) -> EventResult:
        """Apply one activity event to the interaction matrix and refresh similarity."""
        self.validate_event(user_id, item_id, action)
        weight = self._action_weights[action]
        with self._lock:
            self._matrix[self._user_index[user_id], self._item_index[item_id]] += weight
            self._event_count += 1
            self._last_event_at = datetime.now(UTC).isoformat(timespec="seconds")
            self._refresh_similarity_locked()
            return EventResult(
                user_id=user_id,
                item_id=item_id,
                action=action,
                weight=weight,
                event_count=self._event_count,
                processed_at=self._last_event_at,
            )

    def refresh_similarity(self) -> None:
        """Public wrapper to recompute item-item similarity."""
        with self._lock:
            self._refresh_similarity_locked()

    def _refresh_similarity_locked(self) -> None:
        """Recompute item-item similarity; caller must already hold the lock."""
        if not np.any(self._matrix):
            self._similarity = np.zeros((len(self._items), len(self._items)), dtype=np.float64)
            return
        # Item-based CF compares item columns, so transpose before cosine.
        similarity = cosine_similarity(self._matrix.T)
        np.fill_diagonal(similarity, 0.0)
        self._similarity = similarity

    # -- snapshots for the recommender / evaluation --------------------------

    def user_vector(self, user_id: str) -> NDArray[np.float64]:
        """Return a copy of one user's interaction row."""
        if user_id not in self._user_index:
            raise UnknownUserError(f"unknown user_id: {user_id}")
        with self._lock:
            return self._matrix[self._user_index[user_id]].copy()

    def item_similarity(self) -> NDArray[np.float64]:
        """Return a copy of the item-item similarity matrix."""
        with self._lock:
            return self._similarity.copy()

    def matrix_snapshot(self) -> NDArray[np.float64]:
        """Return a copy of the full interaction matrix (for plots/evaluation)."""
        with self._lock:
            return self._matrix.copy()

    def stats(self) -> FeatureStoreStats:
        """Return a small, JSON-friendly snapshot of store state."""
        with self._lock:
            density = float(np.count_nonzero(self._matrix) / self._matrix.size)
            return FeatureStoreStats(
                users=len(self._users),
                items=len(self._items),
                events_processed=self._event_count,
                matrix_density=round(density, 4),
                last_event_at=self._last_event_at,
            )
