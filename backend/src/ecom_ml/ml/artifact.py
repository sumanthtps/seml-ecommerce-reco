"""Atomic persistence for the trained read-model artifact."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from ecom_ml.ml.model import CollaborativeFilteringModel

MODEL_FILENAME = "recommendation_model.npz"
METADATA_FILENAME = "model_metadata.json"


@dataclass(frozen=True, slots=True)
class SavedArtifact:
    """Locations and metadata for one persisted model version."""

    model_path: Path
    metadata_path: Path
    metadata: dict[str, Any]


def save_artifact(
    model: CollaborativeFilteringModel,
    artifact_dir: Path,
    *,
    metrics: dict[str, Any],
    training_event_count: int,
) -> SavedArtifact:
    """Atomically write NumPy model arrays and human-readable metadata."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifact_dir / MODEL_FILENAME
    metadata_path = artifact_dir / METADATA_FILENAME
    nonce = uuid4().hex
    temporary_model = artifact_dir / f".{MODEL_FILENAME}.{nonce}"
    temporary_metadata = artifact_dir / f".{METADATA_FILENAME}.{nonce}"

    with temporary_model.open("wb") as handle:
        np.savez_compressed(
            handle,
            users=np.asarray(model.users, dtype=np.str_),
            items=np.asarray(model.items, dtype=np.str_),
            interaction_matrix=model.interaction_matrix,
            item_similarity=model.item_similarity,
            version=np.asarray([model.version], dtype=np.str_),
        )

    metadata: dict[str, Any] = {
        "model_type": "item-based-collaborative-filtering",
        "version": model.version,
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "users": len(model.users),
        "items": len(model.items),
        "training_events": training_event_count,
        "metrics": metrics,
    }
    temporary_metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    os.replace(temporary_model, model_path)
    os.replace(temporary_metadata, metadata_path)
    return SavedArtifact(model_path=model_path, metadata_path=metadata_path, metadata=metadata)


def load_artifact(artifact_dir: Path) -> tuple[CollaborativeFilteringModel, dict[str, Any]]:
    """Load a model without pickle and verify its metadata version."""
    model_path = artifact_dir / MODEL_FILENAME
    metadata_path = artifact_dir / METADATA_FILENAME
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(f"trained model is missing under {artifact_dir}")

    with np.load(model_path, allow_pickle=False) as bundle:
        model = CollaborativeFilteringModel(
            users=tuple(str(value) for value in bundle["users"].tolist()),
            items=tuple(str(value) for value in bundle["items"].tolist()),
            interaction_matrix=bundle["interaction_matrix"].astype(np.float64),
            item_similarity=bundle["item_similarity"].astype(np.float64),
            version=str(bundle["version"][0]),
        )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("version") != model.version:
        raise ValueError("model and metadata versions do not match")
    return model, metadata
