"""Typed API contracts shared by command and query services."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InteractionCommand(BaseModel):
    """CQRS command to record a user action."""

    user_id: str = Field(min_length=1, examples=["u007"])
    item_id: str = Field(min_length=1, examples=["P012"])
    action: Literal["view", "click", "cart", "purchase"]
    timestamp: str | None = None


class TrainCommand(BaseModel):
    """CQRS command controlling offline evaluation cutoffs."""

    k: int = Field(default=5, ge=1, le=20)
    holdout_per_user: int = Field(default=2, ge=1, le=5)


class RecommendationResponse(BaseModel):
    """CQRS read-model response."""

    user_id: str
    model_version: str
    strategy: str
    recommendations: list[dict[str, str | float]]
