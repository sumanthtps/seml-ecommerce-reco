"""Unit tests for offline evaluation."""

from __future__ import annotations

import numpy as np

from reco.domain import FeatureStore, evaluate_precision_at_k


def test_precision_value_within_unit_interval(store: FeatureStore) -> None:
    result = evaluate_precision_at_k(store.matrix_snapshot(), k=5)
    assert 0.0 <= result.value <= 1.0
    assert result.metric == "Precision@5"


def test_precision_evaluates_users(store: FeatureStore) -> None:
    result = evaluate_precision_at_k(store.matrix_snapshot(), k=5)
    assert result.evaluated_users > 0
    assert result.users_with_at_least_one_hit <= result.evaluated_users


def test_precision_is_reproducible(store: FeatureStore) -> None:
    matrix = store.matrix_snapshot()
    assert evaluate_precision_at_k(matrix, k=5).value == evaluate_precision_at_k(matrix, k=5).value


def test_precision_on_empty_matrix_is_zero() -> None:
    result = evaluate_precision_at_k(np.zeros((10, 10)), k=5)
    assert result.value == 0.0
    assert result.evaluated_users == 0
