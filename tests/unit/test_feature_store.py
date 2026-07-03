"""Unit tests for the feature store."""

from __future__ import annotations

import numpy as np
import pytest

from reco.domain import FeatureStore
from reco.domain.exceptions import (
    InvalidActionError,
    UnknownItemError,
    UnknownUserError,
)


def test_seed_is_deterministic() -> None:
    a = FeatureStore()
    b = FeatureStore()
    a.seed_demo_data()
    b.seed_demo_data()
    assert np.array_equal(a.matrix_snapshot(), b.matrix_snapshot())


def test_seed_is_idempotent(store: FeatureStore) -> None:
    events_after_first = store.stats().events_processed
    store.seed_demo_data()
    assert store.stats().events_processed == events_after_first


def test_track_event_updates_matrix_and_count(empty_store: FeatureStore) -> None:
    before = empty_store.stats().events_processed
    result = empty_store.track_event("u1", "P01", "purchase")
    assert result.weight == 5.0
    assert empty_store.stats().events_processed == before + 1
    assert empty_store.user_vector("u1")[0] == 5.0


@pytest.mark.parametrize(
    ("user_id", "item_id", "action", "error"),
    [
        ("nobody", "P01", "view", UnknownUserError),
        ("u1", "ZZZ", "view", UnknownItemError),
        ("u1", "P01", "teleport", InvalidActionError),
    ],
)
def test_validate_event_rejects_bad_input(
    empty_store: FeatureStore, user_id: str, item_id: str, action: str, error: type[Exception]
) -> None:
    with pytest.raises(error):
        empty_store.validate_event(user_id, item_id, action)


def test_snapshot_is_a_copy(store: FeatureStore) -> None:
    snapshot = store.matrix_snapshot()
    snapshot[0, 0] = 999.0
    assert store.matrix_snapshot()[0, 0] != 999.0


def test_similarity_diagonal_is_zero(store: FeatureStore) -> None:
    similarity = store.item_similarity()
    assert np.allclose(np.diag(similarity), 0.0)


def test_density_within_unit_interval(store: FeatureStore) -> None:
    assert 0.0 < store.stats().matrix_density <= 1.0


def test_empty_store_has_zero_similarity(empty_store: FeatureStore) -> None:
    assert not np.any(empty_store.item_similarity())
