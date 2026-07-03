"""API Gateway for the e-commerce recommendation prototype.

Clients call this service instead of calling internal services directly. The
gateway centralises token checking, simple rate limiting, and routing.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

RECO_SERVICE = os.environ.get("RECO_SERVICE", "http://127.0.0.1:8001")
VALID_TOKEN = os.environ.get("SEML_DEMO_TOKEN", "Bearer seml-demo-token")
REQUEST_LOG: dict[str, float] = {}
MIN_SECONDS_BETWEEN_REQUESTS = 0.25

# This is the only public API surface used by the demo client.
app = FastAPI(
    title="API Gateway",
    description="Single secured entry point for recommendation and activity-tracking requests.",
    version="1.0.0",
)


class ActivityEvent(BaseModel):
    """Public request body for one storefront activity event."""

    user_id: str = Field(examples=["u7"])
    item_id: str = Field(examples=["P03"])
    action: str = Field(examples=["click"])


def require_token(authorization: str | None) -> None:
    """Reject requests that do not include the expected demo token."""
    if authorization != VALID_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


def enforce_rate_limit(key: str) -> None:
    """Apply a tiny in-memory rate limit for demonstration purposes."""
    now = time.time()
    last_seen = REQUEST_LOG.get(key, 0.0)
    if now - last_seen < MIN_SECONDS_BETWEEN_REQUESTS:
        raise HTTPException(status_code=429, detail="too many requests")
    REQUEST_LOG[key] = now


async def forward_response(response: httpx.Response) -> Any:
    """Convert an internal service response into a gateway response."""
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=payload)
    return payload


@app.get("/health")
async def health() -> dict[str, Any]:
    """Check that the gateway and internal recommendation service are alive."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{RECO_SERVICE}/health")
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"internal service unavailable: {exc}") from exc
    return {
        "status": "ok",
        "service": "api-gateway",
        "internal_service": await forward_response(response),
    }


@app.get("/recommend")
async def recommend(
    user_id: str,
    k: int = 5,
    authorization: str | None = Header(default=None),
) -> Any:
    """Public recommendation endpoint exposed through the gateway."""
    require_token(authorization)
    enforce_rate_limit(f"recommend:{user_id}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{RECO_SERVICE}/rank", params={"user_id": user_id, "k": k})
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"internal service unavailable: {exc}") from exc
    payload = await forward_response(response)
    payload["served_by"] = "api-gateway"
    payload["pattern"] = "api-gateway"
    return payload


@app.post("/activity")
async def activity(
    event: ActivityEvent,
    authorization: str | None = Header(default=None),
) -> Any:
    """Public activity endpoint that forwards events to the internal service."""
    require_token(authorization)
    enforce_rate_limit(f"activity:{event.user_id}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(f"{RECO_SERVICE}/track", json=event.model_dump())
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"internal service unavailable: {exc}") from exc
    payload = await forward_response(response)
    payload["served_by"] = "api-gateway"
    return payload
