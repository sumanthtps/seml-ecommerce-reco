"""Unit tests for the explicit ML lifecycle."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ecom_ml.ml.artifact import load_artifact
from ecom_ml.ml.data import (
    Interaction,
    generate_demo_interactions,
    load_interactions,
    prepare_interactions,
)
from ecom_ml.ml.evaluation import evaluate_leave_n_out
from ecom_ml.ml.model import CollaborativeFilteringModel
from ecom_ml.ml.pipeline import train_pipeline


def test_data_loading_preprocessing_and_deduplication(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    generated = generate_demo_interactions(data_path, user_count=20, item_count=30)
    loaded = load_interactions(data_path)
    duplicated = [*loaded, loaded[0]]
    prepared = prepare_interactions(duplicated)

    assert len(generated) == len(loaded)
    assert prepared.raw_event_count == len(loaded) + 1
    assert prepared.unique_event_count == len(loaded)
    assert prepared.matrix.shape == (20, 30)
    assert np.count_nonzero(prepared.matrix) > 0


def test_invalid_action_is_rejected() -> None:
    row = Interaction(
        event_id="evt-x",
        timestamp="2026-01-01T00:00:00+00:00",
        user_id="u001",
        item_id="P001",
        action="ignore",
    )
    with pytest.raises(ValueError, match="action must be"):
        prepare_interactions([row])


def test_model_ranks_only_unseen_items(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    prepared = prepare_interactions(load_interactions(data_path))
    model = CollaborativeFilteringModel.fit(prepared)
    recommendations = model.recommend("u001", k=5)
    seen = {
        prepared.items[index]
        for index in np.flatnonzero(prepared.matrix[prepared.users.index("u001")] > 0)
    }

    assert len(recommendations) == 5
    assert {recommendation.item_id for recommendation in recommendations}.isdisjoint(seen)
    assert [recommendation.score for recommendation in recommendations] == sorted(
        [recommendation.score for recommendation in recommendations],
        reverse=True,
    )


def test_leave_n_out_metrics_are_bounded(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    generate_demo_interactions(data_path, user_count=30, item_count=40)
    prepared = prepare_interactions(load_interactions(data_path))
    metrics = evaluate_leave_n_out(prepared, k=5, holdout_per_user=2)

    assert metrics.evaluated_users == 30
    assert 0.0 <= metrics.precision_at_k <= 1.0
    assert 0.0 <= metrics.recall_at_k <= 1.0
    assert 0.0 <= metrics.hit_rate_at_k <= 1.0
    assert 0.0 <= metrics.catalogue_coverage_at_k <= 1.0


def test_pipeline_persists_a_reloadable_model(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    summary = train_pipeline(data_path, artifact_dir)
    reloaded, metadata = load_artifact(artifact_dir)

    assert summary.version == reloaded.version == metadata["version"]
    assert len(reloaded.recommend("u001", 5)) == 5
