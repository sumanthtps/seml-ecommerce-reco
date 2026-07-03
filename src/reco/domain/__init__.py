"""Domain layer: the machine-learning core, free of any web framework.

Nothing in this package imports FastAPI, httpx, or settings. That keeps the ML
logic unit-testable in isolation and swappable behind the service layer.
"""

from __future__ import annotations

from reco.domain.evaluation import PrecisionAtK, evaluate_precision_at_k
from reco.domain.exceptions import (
    DomainError,
    InvalidActionError,
    InvalidParameterError,
    UnknownItemError,
    UnknownUserError,
)
from reco.domain.feature_store import (
    DEFAULT_ACTION_WEIGHTS,
    FeatureStore,
    FeatureStoreStats,
)
from reco.domain.recommender import Recommendation, Recommender

__all__ = [
    "DEFAULT_ACTION_WEIGHTS",
    "DomainError",
    "FeatureStore",
    "FeatureStoreStats",
    "InvalidActionError",
    "InvalidParameterError",
    "PrecisionAtK",
    "Recommendation",
    "Recommender",
    "UnknownItemError",
    "UnknownUserError",
    "evaluate_precision_at_k",
]
