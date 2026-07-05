"""End-to-end ML pipeline: load, prepare, evaluate, fit, and persist."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ecom_ml.ml.artifact import save_artifact
from ecom_ml.ml.data import load_interactions, prepare_interactions
from ecom_ml.ml.evaluation import evaluate_leave_n_out
from ecom_ml.ml.model import CollaborativeFilteringModel


@dataclass(frozen=True, slots=True)
class TrainingSummary:
    """Serializable outcome of one reproducible training run."""

    model_type: str
    version: str
    users: int
    items: int
    raw_events: int
    unique_events: int
    matrix_density: float
    metrics: dict[str, Any]
    model_path: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def train_pipeline(
    data_path: Path,
    artifact_dir: Path,
    *,
    k: int = 5,
    holdout_per_user: int = 2,
) -> TrainingSummary:
    """Execute and log every stage of the ML lifecycle."""
    print(f"[1/5] LOAD       {data_path}", flush=True)
    rows = load_interactions(data_path)

    print("[2/5] PREPARE    validate, deduplicate, weight, aggregate", flush=True)
    prepared = prepare_interactions(rows)

    print(f"[3/5] EVALUATE   leave-{holdout_per_user}-out Precision@{k}", flush=True)
    evaluation = evaluate_leave_n_out(
        prepared,
        k=k,
        holdout_per_user=holdout_per_user,
    )

    print("[4/5] TRAIN      fit item-item cosine similarity on all events", flush=True)
    model = CollaborativeFilteringModel.fit(prepared)

    print(f"[5/5] PERSIST    {artifact_dir}", flush=True)
    saved = save_artifact(
        model,
        artifact_dir,
        metrics=evaluation.as_dict(),
        training_event_count=prepared.unique_event_count,
    )
    density = float((prepared.matrix > 0).sum() / prepared.matrix.size)
    summary = TrainingSummary(
        model_type="item-based-collaborative-filtering",
        version=model.version,
        users=len(prepared.users),
        items=len(prepared.items),
        raw_events=prepared.raw_event_count,
        unique_events=prepared.unique_event_count,
        matrix_density=round(density, 4),
        metrics=evaluation.as_dict(),
        model_path=str(saved.model_path),
    )
    print(
        f"DONE version={summary.version} "
        f"precision@{k}={evaluation.precision_at_k:.4f} "
        f"coverage@{k}={evaluation.catalogue_coverage_at_k:.4f}",
        flush=True,
    )
    return summary
