"""Internal recommendation service for the SEML prototype.

This service demonstrates the Event-Driven Architecture pattern. It accepts
activity events, places them on an in-memory queue, and lets a background
consumer update the recommendation features asynchronously.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import recommender_engine

# A real production version would use Kafka, Redis Streams, or another durable
# broker. The in-memory queue keeps the assignment demo small and runnable.
EVENT_QUEUE: Queue[dict[str, str]] = Queue()
STOP_WORKER = Event()


class ActivityEvent(BaseModel):
    """Request body for one storefront activity event."""

    user_id: str = Field(examples=["u7"])
    item_id: str = Field(examples=["P12"])
    action: str = Field(examples=["purchase"])


def consumer_loop() -> None:
    """Continuously process queued events in the background."""
    while not STOP_WORKER.is_set():
        try:
            event = EVENT_QUEUE.get(timeout=0.2)
        except Empty:
            continue

        try:
            result = recommender_engine.track_event(
                event["user_id"],
                event["item_id"],
                event["action"],
            )
            print("processed event:", result, flush=True)
        except Exception as exc:  # pragma: no cover - visible demo log
            print("failed event:", event, exc, flush=True)
        finally:
            EVENT_QUEUE.task_done()
            time.sleep(0.05)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed demo data and start the event consumer when FastAPI starts."""
    recommender_engine.seed_demo_data()
    STOP_WORKER.clear()
    worker = Thread(target=consumer_loop, daemon=True, name="event-consumer")
    worker.start()
    yield
    STOP_WORKER.set()
    worker.join(timeout=1)


app = FastAPI(
    title="Recommendation and Event Service",
    description="Internal service that demonstrates the Event-Driven pattern and item-based collaborative filtering.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight health check for the internal service."""
    return {"status": "ok", "service": "recommendation-service"}


@app.get("/stats")
def service_stats() -> dict[str, Any]:
    """Return feature-store and queue statistics for demo evidence."""
    data = recommender_engine.stats()
    data["queued_events"] = EVENT_QUEUE.qsize()
    return data


@app.post("/track", status_code=202)
def track(event: ActivityEvent) -> dict[str, Any]:
    """Accept an activity event and place it on the queue.

    The endpoint returns quickly. The background consumer processes the event
    later, which is the Event-Driven pattern used in this assignment.
    """
    try:
        recommender_engine.validate_event(event.user_id, event.item_id, event.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    payload = event.model_dump()
    EVENT_QUEUE.put(payload)
    return {
        "status": "accepted",
        "pattern": "event-driven",
        "queued_events": EVENT_QUEUE.qsize(),
        "event": payload,
    }


@app.get("/rank")
def rank(user_id: str, k: int = 5) -> dict[str, Any]:
    """Return top-k recommendations from the internal ML component."""
    try:
        recommendations = recommender_engine.rank_items(user_id, k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "user_id": user_id,
        "strategy": "item-based-collaborative-filtering",
        "recommendations": recommendations,
        "recommender_engine": recommender_engine.stats(),
    }

