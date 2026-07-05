"""Item-based collaborative-filtering training and inference."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

from ecom_ml.ml.data import PreparedInteractions

_NEGATIVE_FILL = -1e12


@dataclass(frozen=True, slots=True)
class Recommendation:
    """A ranked product prediction."""

    item_id: str
    score: float


@dataclass(frozen=True, slots=True)
class CollaborativeFilteringModel:
    """Fitted item-item similarity model plus serving features."""

    users: tuple[str, ...]
    items: tuple[str, ...]
    interaction_matrix: NDArray[np.float64]
    item_similarity: NDArray[np.float64]
    version: str

    @classmethod
    def fit(cls, prepared: PreparedInteractions) -> CollaborativeFilteringModel:
        """Fit item-item cosine similarity from a prepared interaction matrix."""
        matrix = prepared.matrix.astype(np.float64, copy=True)
        similarity = cosine_similarity(matrix.T).astype(np.float64, copy=False)
        np.fill_diagonal(similarity, 0.0)
        version_input = (
            matrix.tobytes() + "|".join(prepared.users).encode() + "|".join(prepared.items).encode()
        )
        version = hashlib.sha256(version_input).hexdigest()[:12]
        return cls(
            users=prepared.users,
            items=prepared.items,
            interaction_matrix=matrix,
            item_similarity=similarity,
            version=version,
        )

    def recommend(self, user_id: str, k: int = 5) -> list[Recommendation]:
        """Score and rank unseen items for a known user."""
        if k < 1 or k > 20:
            raise ValueError("k must be between 1 and 20")
        try:
            user_index = self.users.index(user_id)
        except ValueError as exc:
            raise KeyError(f"unknown user_id: {user_id}") from exc

        user_vector = self.interaction_matrix[user_index]
        scores = (user_vector @ self.item_similarity).astype(np.float64, copy=True)
        seen = user_vector > 0
        scores[seen] = -np.inf
        ordered = np.argsort(np.nan_to_num(scores, neginf=_NEGATIVE_FILL))[::-1]

        recommendations: list[Recommendation] = []
        for item_index in ordered:
            if len(recommendations) == k:
                break
            if seen[item_index]:
                continue
            score = scores[item_index]
            recommendations.append(
                Recommendation(
                    item_id=self.items[int(item_index)],
                    score=round(float(score if np.isfinite(score) else 0.0), 4),
                )
            )
        return recommendations
