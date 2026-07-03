"""Background event consumer.

This is the heart of the Event-Driven pattern: the API thread accepts events and
returns immediately, while this consumer drains the queue and updates the feature
store asynchronously on its own daemon thread.
"""

from __future__ import annotations

import threading

from reco.domain import DomainError, FeatureStore
from reco.logging import get_logger
from reco.recommendation.queue import MessageQueue, QueueEmpty

logger = get_logger("reco.consumer")


class EventConsumer:
    """Drains a :class:`MessageQueue` and applies events to the feature store."""

    def __init__(
        self,
        message_queue: MessageQueue,
        store: FeatureStore,
        *,
        poll_timeout: float = 0.2,
    ) -> None:
        self._queue = message_queue
        self._store = store
        self._poll_timeout = poll_timeout
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the consumer thread (idempotent)."""
        if self.is_running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="event-consumer", daemon=True)
        self._thread.start()
        logger.info("event consumer started")

    def stop(self, timeout: float = 2.0) -> None:
        """Signal the consumer to stop and wait briefly for it to drain."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        logger.info("event consumer stopped")

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                event = self._queue.get(timeout=self._poll_timeout)
            except QueueEmpty:
                continue
            try:
                result = self._store.track_event(
                    event["user_id"], event["item_id"], event["action"]
                )
                logger.info(
                    "processed event",
                    extra={"event": event, "event_count": result.event_count},
                )
            except DomainError as exc:
                logger.warning("rejected event", extra={"event": event, "error": str(exc)})
            except Exception:
                logger.exception("failed to process event", extra={"event": event})
            finally:
                self._queue.task_done()
