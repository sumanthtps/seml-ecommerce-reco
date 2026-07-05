"""FastAPI command service: interaction writes and model training."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status

from ecom_ml.api_models import InteractionCommand, TrainCommand
from ecom_ml.config import Settings
from ecom_ml.ml.data import Interaction, append_interaction
from ecom_ml.ml.pipeline import train_pipeline


def create_app(
    *,
    data_path: Path | None = None,
    artifact_dir: Path | None = None,
) -> FastAPI:
    """Build a command service with injectable paths for testing."""
    settings = Settings.from_env()
    resolved_data = data_path or settings.data_path
    resolved_artifacts = artifact_dir or settings.artifact_dir
    training_lock = threading.Lock()
    application = FastAPI(
        title="SEML Recommendation Command Service",
        version="1.0.0",
        description=(
            "CQRS write side: records implicit-feedback commands and trains "
            "the collaborative-filtering read model."
        ),
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "command-service", "pattern": "CQRS-command"}

    @application.post("/commands/interactions", status_code=status.HTTP_202_ACCEPTED)
    def record_interaction(command: InteractionCommand) -> dict[str, str]:
        interaction = Interaction(
            event_id=f"cmd-{uuid4().hex}",
            timestamp=command.timestamp or datetime.now(UTC).isoformat(timespec="seconds"),
            user_id=command.user_id,
            item_id=command.item_id,
            action=command.action,
        )
        try:
            append_interaction(resolved_data, interaction)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "status": "accepted",
            "event_id": interaction.event_id,
            "pattern": "CQRS-command",
        }

    @application.post("/commands/train")
    def train(command: TrainCommand) -> dict[str, Any]:
        if not training_lock.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="training is already running")
        try:
            summary = train_pipeline(
                resolved_data,
                resolved_artifacts,
                k=command.k,
                holdout_per_user=command.holdout_per_user,
            )
            return {
                "status": "trained",
                "pattern": "CQRS-command",
                "summary": summary.as_dict(),
            }
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        finally:
            training_lock.release()

    return application


app = create_app()
