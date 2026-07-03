"""Application factory for the public API gateway."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from reco import __version__
from reco.config import GatewaySettings, get_gateway_settings
from reco.gateway.rate_limit import RateLimiter
from reco.gateway.routes import router
from reco.logging import configure_logging, get_logger
from reco.middleware import RequestContextMiddleware

logger = get_logger("reco.gateway")

DESCRIPTION = (
    "Single secured entry point (API Gateway pattern). Centralises bearer-token "
    "auth, per-user rate limiting, and routing to the internal recommendation "
    "service."
)


def create_app(settings: GatewaySettings | None = None) -> FastAPI:
    """Build and wire a gateway app instance."""
    settings = settings or get_gateway_settings()
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = httpx.AsyncClient(
            base_url=settings.reco_service_url,
            timeout=settings.request_timeout_seconds,
        )
        app.state.http_client = client
        logger.info("gateway ready", extra={"reco_service_url": settings.reco_service_url})
        try:
            yield
        finally:
            await client.aclose()

    app = FastAPI(
        title="API Gateway",
        description=DESCRIPTION,
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter(settings.rate_limit_seconds)

    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)
    return app


app = create_app()
