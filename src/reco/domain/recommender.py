"""Item-based collaborative-filtering recommender.

The recommender is a thin, stateless scorer on top of a :class:`FeatureStore`.
Keeping ranking separate from storage means we can swap the scoring strategy
(e.g. matrix factorisation, a two-tower model) without touching the store.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reco.domain.exceptions import InvalidParameterError, UnknownUserError
from reco.domain.feature_store import FeatureStore

_NEG_INF_FILL = -1e12


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A single scored recommendation."""

    item_id: str
    score: float


class Recommender:
    """Scores unseen items for a user via item-based collaborative filtering."""

    def __init__(self, store: FeatureStore, *, min_k: int = 1, max_k: int = 20) -> None:
        self._store = store
        self._min_k = min_k
        self._max_k = max_k

    @property
    def strategy(self) -> str:
        return "item-based-collaborative-filtering"

    def rank(self, user_id: str, k: int = 5) -> list[Recommendation]:
        """Return the top-``k`` unseen products for ``user_id``.

        The score is the user's interaction vector multiplied by the item-item
        similarity matrix; items the user has already interacted with are masked
        out so they are never recommended back.
        """
        if not self._store.has_user(user_id):
            raise UnknownUserError(f"unknown user_id: {user_id}")
        if k < self._min_k or k > self._max_k:
            raise InvalidParameterError(f"k must be between {self._min_k} and {self._max_k}")

        user_row = self._store.user_vector(user_id)
        similarity = self._store.item_similarity()
        items = self._store.items

        scores = (user_row @ similarity).astype(np.float64, copy=True)
        # Never recommend an item the user has already interacted with.
        seen = user_row > 0
        scores[seen] = -np.inf

        ranked_indices = np.argsort(np.nan_to_num(scores, neginf=_NEG_INF_FILL))[::-1]

        recommendations: list[Recommendation] = []
        for item_index in ranked_indices:
            if len(recommendations) == k:
                break
            if seen[item_index]:
                continue
            score = scores[item_index]
            recommendations.append(
                Recommendation(
                    item_id=items[item_index],
                    score=round(float(score if np.isfinite(score) else 0.0), 3),
                )
            )
        return recommendations
