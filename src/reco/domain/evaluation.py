"""Offline evaluation for the recommender (leave-N-out Precision@k).

This is deliberately simple: a few known interactions are hidden per user, the
model is retrained on the remainder, and we measure how often the held-out items
reappear in the top-k list. It gives the report a single, reproducible quality
number without needing a real labelled test set.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sklearn.metrics.pairwise import cosine_similarity

_EVAL_RNG = 1546
_NEG_INF_FILL = -1e12


@dataclass(frozen=True, slots=True)
class PrecisionAtK:
    """Result of an offline Precision@k evaluation."""

    metric: str
    value: float
    evaluated_users: int
    users_with_at_least_one_hit: int
    holdout_per_user: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_precision_at_k(
    matrix: NDArray[np.float64],
    k: int = 5,
    holdout_per_user: int = 3,
    *,
    seed: int = _EVAL_RNG,
) -> PrecisionAtK:
    """Compute leave-``holdout_per_user``-out Precision@k on an interaction matrix.

    Args:
        matrix: user x item interaction-weight matrix (a snapshot copy).
        k: cut-off for the top-k list.
        holdout_per_user: positives hidden per user to form the test set.
        seed: RNG seed, so the metric is reproducible across runs.
    """
    rng = np.random.default_rng(seed)
    train = matrix.copy()
    held_out: dict[int, set[int]] = {}

    for user_index in range(matrix.shape[0]):
        positives = np.flatnonzero(matrix[user_index] > 0)
        if len(positives) <= holdout_per_user:
            continue
        holdout = rng.choice(positives, size=holdout_per_user, replace=False)
        train[user_index, holdout] = 0.0
        held_out[user_index] = {int(i) for i in holdout}

    similarity = cosine_similarity(train.T)
    np.fill_diagonal(similarity, 0.0)

    precisions: list[float] = []
    hit_users = 0
    for user_index, holdout_items in held_out.items():
        scores = train[user_index] @ similarity
        scores[train[user_index] > 0] = -np.inf
        top = np.argsort(np.nan_to_num(scores, neginf=_NEG_INF_FILL))[::-1][:k]
        hits = len({int(i) for i in top} & holdout_items)
        if hits:
            hit_users += 1
        precisions.append(hits / k)

    value = float(np.mean(precisions)) if precisions else 0.0
    return PrecisionAtK(
        metric=f"Precision@{k}",
        value=round(value, 3),
        evaluated_users=len(precisions),
        users_with_at_least_one_hit=hit_users,
        holdout_per_user=holdout_per_user,
    )
