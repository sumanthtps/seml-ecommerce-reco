"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from reco.domain import FeatureStore, Recommender


@pytest.fixture
def empty_store() -> FeatureStore:
    """A fresh, unseeded feature store."""
    return FeatureStore()


@pytest.fixture
def store() -> FeatureStore:
    """A feature store pre-populated with the deterministic demo data."""
    s = FeatureStore()
    s.seed_demo_data()
    return s


@pytest.fixture
def recommender(store: FeatureStore) -> Recommender:
    return Recommender(store)
