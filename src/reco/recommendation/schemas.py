"""Pydantic request/response models for the recommendation service."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ActivityEvent(BaseModel):
    """One storefront activity event."""

    user_id: str = Field(examples=["u7"])
    item_id: str = Field(examples=["P12"])
    action: str = Field(examples=["purchase"], description="view | click | cart | purchase")


class TrackAccepted(BaseModel):
    """Acknowledgement returned immediately after queueing an event."""

    status: str = "accepted"
    pattern: str = "event-driven"
    queued_events: int
    event: ActivityEvent


class RecommendationItem(BaseModel):
    item_id: str
    score: float


class StatsResponse(BaseModel):
    users: int
    items: int
    events_processed: int
    matrix_density: float
    last_event_at: str | None
    queued_events: int


class RankResponse(BaseModel):
    user_id: str
    strategy: str
    recommendations: list[RecommendationItem]
    stats: StatsResponse


class HealthResponse(BaseModel):
    status: str
    service: str
    consumer_running: bool
