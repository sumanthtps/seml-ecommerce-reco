"""Pydantic models for the gateway's public API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ActivityEvent(BaseModel):
    """Public request body for one storefront activity event."""

    user_id: str = Field(examples=["u7"])
    item_id: str = Field(examples=["P03"])
    action: str = Field(examples=["click"], description="view | click | cart | purchase")


class HealthResponse(BaseModel):
    status: str
    service: str
    internal_service: dict[str, Any] | None = None
