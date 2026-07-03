"""Application factory for the internal recommendation service."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from reco import __version__
from reco.config import RecommendationSettings, get_recommendation_settings
from reco.domain import FeatureStore, Recommender
from reco.logging import configure_logging, get_logger
from reco.middleware import RequestContextMiddleware
from reco.recommendation.consumer import EventConsumer
from reco.recommendation.queue import InMemoryEventQueue
from reco.recommendation.routes import router

logger = get_logger("reco.recommendation")

DESCRIPTION = (
    "Internal service demonstrating the Event-Driven pattern and item-based "
    "collaborative filtering. Activity events are queued and processed by a "
    "background consumer; recommendations are scored on demand."
)


def create_app(settings: RecommendationSettings | None = None) -> FastAPI:
    """Build and wire a recommendation-service app instance."""
    settings = settings or get_recommendation_settings()
    configure_logging(settings.log_level, settings.log_format)

    store = FeatureStore()
    recommender = Recommender(store)
    message_queue = InMemoryEventQueue()
    consumer = EventConsumer(message_queue, store, poll_timeout=settings.consumer_poll_timeout)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.seed_demo_data:
            store.seed_demo_data()
            logger.info("seeded demo data", extra={"events": store.stats().events_processed})
        consumer.start()
        try:
            yield
        finally:
            consumer.stop()

    app = FastAPI(
        title="Recommendation & Event Service",
        description=DESCRIPTION,
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.store = store
    app.state.recommender = recommender
    app.state.queue = message_queue
    app.state.consumer = consumer

    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)
    return app


app = create_app()
