"""HTTP routes for the public API gateway.

The gateway owns cross-cutting concerns (authentication, rate limiting, error
normalisation) and forwards business calls to the internal recommendation
service. The downstream ``httpx`` client is injected from ``app.state`` so it can
be swapped for a mock transport in tests.
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from reco.gateway import schemas
from reco.gateway.auth import require_token
from reco.gateway.rate_limit import RateLimiter

router = APIRouter()

_UPSTREAM_UNAVAILABLE = "internal service unavailable"


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


async def _forward(response: httpx.Response) -> dict[str, Any]:
    """Normalise a downstream response, re-raising upstream 4xx/5xx as-is."""
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=payload)
    return payload


def _enforce_rate_limit(limiter: RateLimiter, key: str) -> None:
    if not limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many requests"
        )


@router.get("/health", response_model=schemas.HealthResponse, tags=["ops"])
async def health(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> schemas.HealthResponse:
    """Report gateway health together with the downstream service's health."""
    try:
        response = await client.get("/health")
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{_UPSTREAM_UNAVAILABLE}: {exc}") from exc
    return schemas.HealthResponse(
        status="ok", service="api-gateway", internal_service=await _forward(response)
    )


@router.get(
    "/recommend",
    tags=["recommendations"],
    dependencies=[Depends(require_token)],
)
async def recommend(
    user_id: str,
    k: int = 5,
    client: httpx.AsyncClient = Depends(get_http_client),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> dict[str, Any]:
    """Authenticated, rate-limited recommendation endpoint."""
    _enforce_rate_limit(limiter, f"recommend:{user_id}")
    try:
        response = await client.get("/rank", params={"user_id": user_id, "k": k})
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{_UPSTREAM_UNAVAILABLE}: {exc}") from exc
    payload = await _forward(response)
    payload["served_by"] = "api-gateway"
    payload["pattern"] = "api-gateway"
    return payload


@router.post(
    "/activity",
    tags=["events"],
    dependencies=[Depends(require_token)],
)
async def activity(
    event: schemas.ActivityEvent,
    client: httpx.AsyncClient = Depends(get_http_client),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> dict[str, Any]:
    """Authenticated, rate-limited activity-ingestion endpoint."""
    _enforce_rate_limit(limiter, f"activity:{event.user_id}")
    try:
        response = await client.post("/track", json=event.model_dump())
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"{_UPSTREAM_UNAVAILABLE}: {exc}") from exc
    payload = await _forward(response)
    payload["served_by"] = "api-gateway"
    return payload
