"""Leakage-safe leave-N-out evaluation for the top-k recommender."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from ecom_ml.ml.data import PreparedInteractions
from ecom_ml.ml.model import CollaborativeFilteringModel


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    """Offline ranking quality and reach metrics."""

    precision_at_k: float
    recall_at_k: float
    hit_rate_at_k: float
    catalogue_coverage_at_k: float
    evaluated_users: int
    k: int
    holdout_per_user: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_leave_n_out(
    prepared: PreparedInteractions,
    *,
    k: int = 5,
    holdout_per_user: int = 2,
    seed: int = 1546,
) -> EvaluationMetrics:
    """Hide interactions, fit on the remainder, and evaluate top-k recovery."""
    if k < 1:
        raise ValueError("k must be positive")
    if holdout_per_user < 1:
        raise ValueError("holdout_per_user must be positive")

    rng = np.random.default_rng(seed)
    train_matrix = prepared.matrix.copy()
    held_out: dict[int, set[int]] = {}
    for user_index in range(train_matrix.shape[0]):
        positives = np.flatnonzero(train_matrix[user_index] > 0)
        if len(positives) <= holdout_per_user:
            continue
        selected = rng.choice(positives, size=holdout_per_user, replace=False)
        train_matrix[user_index, selected] = 0.0
        held_out[user_index] = {int(index) for index in selected}

    train_data = PreparedInteractions(
        users=prepared.users,
        items=prepared.items,
        matrix=train_matrix,
        raw_event_count=prepared.raw_event_count,
        unique_event_count=prepared.unique_event_count,
    )
    model = CollaborativeFilteringModel.fit(train_data)
    precisions: list[float] = []
    recalls: list[float] = []
    hit_users = 0
    recommended_items: set[str] = set()

    for user_index, relevant in held_out.items():
        recommendations = model.recommend(prepared.users[user_index], k=k)
        predicted_ids = {recommendation.item_id for recommendation in recommendations}
        predicted_indices = {prepared.items.index(item_id) for item_id in predicted_ids}
        hits = len(predicted_indices & relevant)
        precisions.append(hits / k)
        recalls.append(hits / len(relevant))
        hit_users += int(hits > 0)
        recommended_items.update(predicted_ids)

    user_count = len(precisions)
    return EvaluationMetrics(
        precision_at_k=round(float(np.mean(precisions)) if precisions else 0.0, 4),
        recall_at_k=round(float(np.mean(recalls)) if recalls else 0.0, 4),
        hit_rate_at_k=round(hit_users / user_count if user_count else 0.0, 4),
        catalogue_coverage_at_k=round(
            len(recommended_items) / len(prepared.items) if prepared.items else 0.0,
            4,
        ),
        evaluated_users=user_count,
        k=k,
        holdout_per_user=holdout_per_user,
    )
