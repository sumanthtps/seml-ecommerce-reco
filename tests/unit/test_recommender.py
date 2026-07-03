"""Unit tests for the recommender."""

from __future__ import annotations

import pytest

from reco.domain import FeatureStore, Recommender
from reco.domain.exceptions import InvalidParameterError, UnknownUserError


def test_rank_returns_k_items(recommender: Recommender) -> None:
    recommendations = recommender.rank("u7", k=5)
    assert len(recommendations) == 5


def test_rank_excludes_already_seen_items(store: FeatureStore, recommender: Recommender) -> None:
    seen = {
        item
        for item, weight in zip(store.items, store.user_vector("u7"), strict=True)
        if weight > 0
    }
    recommended = {r.item_id for r in recommender.rank("u7", k=10)}
    assert recommended.isdisjoint(seen)


def test_rank_scores_are_non_increasing(recommender: Recommender) -> None:
    scores = [r.score for r in recommender.rank("u7", k=10)]
    assert scores == sorted(scores, reverse=True)


def test_rank_unknown_user_raises(recommender: Recommender) -> None:
    with pytest.raises(UnknownUserError):
        recommender.rank("ghost", k=5)


@pytest.mark.parametrize("k", [0, 21])
def test_rank_rejects_out_of_range_k(recommender: Recommender, k: int) -> None:
    with pytest.raises(InvalidParameterError):
        recommender.rank("u7", k=k)


def test_rank_on_empty_store_returns_unseen_items(empty_store: FeatureStore) -> None:
    recommendations = Recommender(empty_store).rank("u1", k=3)
    assert len(recommendations) == 3
    assert all(r.score == 0.0 for r in recommendations)
