"""Typed application configuration via environment variables.

Each service has its own settings class with a distinct env prefix, so the two
containers can be configured independently:

* Gateway:        ``GATEWAY_*``   (e.g. ``GATEWAY_AUTH_TOKEN``)
* Recommendation: ``RECO_*``      (e.g. ``RECO_SEED_DEMO_DATA``)

Settings are also read from a local ``.env`` file when present. See
``.env.example`` for the full list.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogFormat = Literal["json", "console"]


class GatewaySettings(BaseSettings):
    """Configuration for the public API gateway."""

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"
    log_format: LogFormat = "json"

    # Downstream internal recommendation service.
    reco_service_url: str = "http://127.0.0.1:8001"
    request_timeout_seconds: float = 5.0

    # Static bearer token for the demo. ALWAYS override this outside local dev.
    auth_token: str = Field(default="seml-demo-token")

    # Minimum seconds between two requests with the same rate-limit key.
    rate_limit_seconds: float = 0.25


class RecommendationSettings(BaseSettings):
    """Configuration for the internal recommendation / event service."""

    model_config = SettingsConfigDict(
        env_prefix="RECO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    log_level: str = "INFO"
    log_format: LogFormat = "json"

    # Seed the in-memory feature store with synthetic data on startup.
    seed_demo_data: bool = True
    # How long the background consumer blocks waiting for the next event.
    consumer_poll_timeout: float = 0.2


@lru_cache
def get_gateway_settings() -> GatewaySettings:
    """Return cached gateway settings (one instance per process)."""
    return GatewaySettings()


@lru_cache
def get_recommendation_settings() -> RecommendationSettings:
    """Return cached recommendation-service settings (one instance per process)."""
    return RecommendationSettings()
