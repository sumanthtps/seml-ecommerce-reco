"""HTTP routes for the internal recommendation service.

Collaborators (feature store, recommender, queue, consumer) are resolved from
``app.state`` through FastAPI dependencies, which keeps the handlers thin and
makes them trivial to override in tests.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from reco.domain import DomainError, FeatureStore, Recommender
from reco.recommendation import schemas
from reco.recommendation.consumer import EventConsumer
from reco.recommendation.queue import MessageQueue

router = APIRouter()


def get_store(request: Request) -> FeatureStore:
    return request.app.state.store


def get_recommender(request: Request) -> Recommender:
    return request.app.state.recommender


def get_queue(request: Request) -> MessageQueue:
    return request.app.state.queue


def get_consumer(request: Request) -> EventConsumer:
    return request.app.state.consumer


def _bad_request(exc: DomainError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _stats(store: FeatureStore, message_queue: MessageQueue) -> schemas.StatsResponse:
    snapshot = store.stats()
    return schemas.StatsResponse(
        users=snapshot.users,
        items=snapshot.items,
        events_processed=snapshot.events_processed,
        matrix_density=snapshot.matrix_density,
        last_event_at=snapshot.last_event_at,
        queued_events=message_queue.qsize(),
    )


@router.get("/health", response_model=schemas.HealthResponse, tags=["ops"])
def health(consumer: EventConsumer = Depends(get_consumer)) -> schemas.HealthResponse:
    """Liveness probe that also reports whether the consumer thread is alive."""
    return schemas.HealthResponse(
        status="ok",
        service="recommendation-service",
        consumer_running=consumer.is_running,
    )


@router.get("/stats", response_model=schemas.StatsResponse, tags=["ops"])
def stats(
    store: FeatureStore = Depends(get_store),
    message_queue: MessageQueue = Depends(get_queue),
) -> schemas.StatsResponse:
    """Return feature-store and queue statistics."""
    return _stats(store, message_queue)


@router.post(
    "/track",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=schemas.TrackAccepted,
    tags=["events"],
)
def track(
    event: schemas.ActivityEvent,
    store: FeatureStore = Depends(get_store),
    message_queue: MessageQueue = Depends(get_queue),
) -> schemas.TrackAccepted:
    """Validate an event, enqueue it, and return 202 immediately.

    The background consumer applies the event to the feature store later - this
    asynchronous hand-off is the Event-Driven pattern.
    """
    try:
        store.validate_event(event.user_id, event.item_id, event.action)
    except DomainError as exc:
        raise _bad_request(exc) from exc
    message_queue.put(event.model_dump())
    return schemas.TrackAccepted(queued_events=message_queue.qsize(), event=event)


@router.get("/rank", response_model=schemas.RankResponse, tags=["recommendations"])
def rank(
    user_id: str,
    k: int = 5,
    store: FeatureStore = Depends(get_store),
    recommender: Recommender = Depends(get_recommender),
    message_queue: MessageQueue = Depends(get_queue),
) -> schemas.RankResponse:
    """Return the top-k recommendations for a user from the ML component."""
    try:
        recommendations = recommender.rank(user_id, k)
    except DomainError as exc:
        raise _bad_request(exc) from exc
    return schemas.RankResponse(
        user_id=user_id,
        strategy=recommender.strategy,
        recommendations=[
            schemas.RecommendationItem(item_id=r.item_id, score=r.score) for r in recommendations
        ],
        stats=_stats(store, message_queue),
    )
