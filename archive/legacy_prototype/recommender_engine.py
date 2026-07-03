"""In-memory feature store for the e-commerce recommendation demo.

The assignment prototype keeps the data in memory so the architecture is easy to
run locally. In a production system, this module would be replaced by a real
feature store or database.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

USERS = [f"u{i}" for i in range(1, 61)]
ITEMS = [f"P{i:02d}" for i in range(1, 41)]
USER_INDEX = {user_id: index for index, user_id in enumerate(USERS)}
ITEM_INDEX = {item_id: index for index, item_id in enumerate(ITEMS)}
ACTION_WEIGHT = {"view": 1.0, "click": 2.0, "cart": 3.0, "purchase": 5.0}

# Shared state for the demo. The lock keeps updates safe while the API worker
# and the background event consumer access the matrix at the same time.
_LOCK = threading.RLock()
_MATRIX = np.zeros((len(USERS), len(ITEMS)), dtype=float)
_ITEM_SIMILARITY = np.zeros((len(ITEMS), len(ITEMS)), dtype=float)
_EVENT_COUNT = 0
_LAST_EVENT_AT: str | None = None
_SEEDED = False


def reset() -> None:
    """Clear all demo data and return the feature store to an empty state."""
    global _MATRIX, _ITEM_SIMILARITY, _EVENT_COUNT, _LAST_EVENT_AT, _SEEDED
    with _LOCK:
        _MATRIX = np.zeros((len(USERS), len(ITEMS)), dtype=float)
        _ITEM_SIMILARITY = np.zeros((len(ITEMS), len(ITEMS)), dtype=float)
        _EVENT_COUNT = 0
        _LAST_EVENT_AT = None
        _SEEDED = False


def seed_demo_data() -> None:
    """Create repeatable clustered shopping behaviour for the local demo.

    Users are split into four simple taste clusters. Each user interacts mostly
    with products from their own cluster and a few products from a neighbouring
    cluster. This gives the recommender a useful pattern to learn from.
    """
    global _EVENT_COUNT, _SEEDED
    with _LOCK:
        if _SEEDED:
            return
        rng = np.random.default_rng(546)

        for user_index, _user_id in enumerate(USERS):
            cluster = user_index % 4
            core_items = np.arange(cluster * 10, cluster * 10 + 10)
            neighbour_items = np.arange(((cluster + 1) % 4) * 10, ((cluster + 1) % 4) * 10 + 10)

            # Most interactions come from the user's main taste cluster.
            selected_core = rng.choice(core_items, size=7, replace=False)
            selected_neighbour = rng.choice(neighbour_items, size=2, replace=False)
            selected = np.concatenate([selected_core, selected_neighbour])

            for item_index in selected:
                _MATRIX[user_index, item_index] += float(
                    rng.choice([1.0, 2.0, 3.0, 5.0], p=[0.25, 0.35, 0.25, 0.15])
                )
                _EVENT_COUNT += 1

        _refresh_similarity_locked()
        _SEEDED = True


def _refresh_similarity_locked() -> None:
    """Recompute item-item similarity while the caller already holds the lock."""
    global _ITEM_SIMILARITY
    if np.count_nonzero(_MATRIX) == 0:
        _ITEM_SIMILARITY = np.zeros((len(ITEMS), len(ITEMS)), dtype=float)
        return

    # Collaborative filtering compares item columns, so the matrix is
    # transposed before cosine similarity is computed.
    _ITEM_SIMILARITY = cosine_similarity(_MATRIX.T)
    np.fill_diagonal(_ITEM_SIMILARITY, 0.0)


def refresh_similarity() -> None:
    """Public wrapper used when a caller wants to refresh similarities."""
    with _LOCK:
        _refresh_similarity_locked()


def validate_event(user_id: str, item_id: str, action: str) -> None:
    """Validate one storefront activity event before it reaches the model."""
    if user_id not in USER_INDEX:
        raise ValueError(f"unknown user_id: {user_id}")
    if item_id not in ITEM_INDEX:
        raise ValueError(f"unknown item_id: {item_id}")
    if action not in ACTION_WEIGHT:
        raise ValueError(f"invalid action: {action}")


def track_event(user_id: str, item_id: str, action: str) -> dict[str, Any]:
    """Apply one user activity event to the interaction matrix."""
    global _EVENT_COUNT, _LAST_EVENT_AT
    seed_demo_data()
    validate_event(user_id, item_id, action)

    with _LOCK:
        # Stronger actions, such as purchases, add more preference weight than
        # lighter actions, such as views.
        _MATRIX[USER_INDEX[user_id], ITEM_INDEX[item_id]] += ACTION_WEIGHT[action]
        _EVENT_COUNT += 1
        _LAST_EVENT_AT = datetime.now(timezone.utc).isoformat(timespec="seconds")
        _refresh_similarity_locked()
        return {
            "user_id": user_id,
            "item_id": item_id,
            "action": action,
            "weight": ACTION_WEIGHT[action],
            "event_count": _EVENT_COUNT,
            "processed_at": _LAST_EVENT_AT,
        }


def rank_items(user_id: str, k: int = 5) -> list[dict[str, Any]]:
    """Return the top-k unseen products for a user.

    The score is the user's interaction vector multiplied by the item-item
    similarity matrix. Products already seen by the user are masked out.
    """
    seed_demo_data()
    if user_id not in USER_INDEX:
        raise ValueError(f"unknown user_id: {user_id}")
    if k < 1 or k > 20:
        raise ValueError("k must be between 1 and 20")

    with _LOCK:
        user_row = _MATRIX[USER_INDEX[user_id]].copy()

        # Item-based CF: similar items receive higher scores when the user has
        # interacted with related products.
        scores = user_row @ _ITEM_SIMILARITY
        scores = scores.astype(float, copy=True)

        # Do not recommend products the user has already interacted with.
        scores[user_row > 0] = -np.inf
        ordered = np.argsort(np.nan_to_num(scores, neginf=-1e12))[::-1]

        recommendations: list[dict[str, Any]] = []
        for item_index in ordered:
            if len(recommendations) == k:
                break
            if user_row[item_index] > 0:
                continue
            score = scores[item_index]
            recommendations.append(
                {
                    "item_id": ITEMS[item_index],
                    "score": round(float(score if np.isfinite(score) else 0.0), 3),
                }
            )
        return recommendations


def stats() -> dict[str, Any]:
    """Return small service statistics for API responses and report evidence."""
    seed_demo_data()
    with _LOCK:
        density = float(np.count_nonzero(_MATRIX) / _MATRIX.size)
        return {
            "users": len(USERS),
            "items": len(ITEMS),
            "events_processed": _EVENT_COUNT,
            "matrix_density": round(density, 4),
            "last_event_at": _LAST_EVENT_AT,
        }


def matrix_snapshot() -> np.ndarray:
    """Return a copy of the interaction matrix for plotting evidence."""
    seed_demo_data()
    with _LOCK:
        return _MATRIX.copy()


def evaluate_precision_at_k(k: int = 5, holdout_per_user: int = 3) -> dict[str, Any]:
    """Compute a simple offline Precision@k score for the demo data.

    A few known interactions are hidden for each user. The recommender is then
    tested on whether it can recover those held-out items in its top-k list.
    """
    seed_demo_data()
    with _LOCK:
        full_matrix = _MATRIX.copy()

    rng = np.random.default_rng(1546)
    train_matrix = full_matrix.copy()
    held_out: dict[int, set[int]] = {}

    for user_index in range(full_matrix.shape[0]):
        # Hold out a few positive items per user to simulate an offline test set.
        positives = np.flatnonzero(full_matrix[user_index] > 0)
        if len(positives) <= holdout_per_user:
            continue
        holdout_items = rng.choice(positives, size=holdout_per_user, replace=False)
        train_matrix[user_index, holdout_items] = 0.0
        held_out[user_index] = set(int(item) for item in holdout_items)

    similarity = cosine_similarity(train_matrix.T)
    np.fill_diagonal(similarity, 0.0)

    precision_values: list[float] = []
    hit_users = 0
    for user_index, holdout_items in held_out.items():
        scores = train_matrix[user_index] @ similarity
        scores[train_matrix[user_index] > 0] = -np.inf
        top = np.argsort(np.nan_to_num(scores, neginf=-1e12))[::-1][:k]
        hits = len(set(int(item) for item in top) & holdout_items)
        if hits:
            hit_users += 1
        precision_values.append(hits / k)

    precision = float(np.mean(precision_values)) if precision_values else 0.0
    return {
        "metric": f"Precision@{k}",
        "value": round(precision, 3),
        "evaluated_users": len(precision_values),
        "users_with_at_least_one_hit": hit_users,
        "holdout_per_user": holdout_per_user,
    }


def item_ids() -> list[str]:
    """Return product IDs in matrix column order."""
    return list(ITEMS)


def user_ids() -> list[str]:
    """Return user IDs in matrix row order."""
    return list(USERS)
