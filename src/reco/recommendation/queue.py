"""Message-queue abstraction for the Event-Driven pattern.

The service depends only on the :class:`MessageQueue` protocol, so the in-memory
implementation used for the demo can be swapped for a durable broker (Redis
Streams, Kafka, RabbitMQ) without touching the consumer or the routes.
"""

from __future__ import annotations

import queue
from typing import Protocol, runtime_checkable

Event = dict[str, str]


class QueueEmpty(Exception):
    """Raised by :meth:`MessageQueue.get` when no event is available in time."""


@runtime_checkable
class MessageQueue(Protocol):
    """Minimal queue contract shared by all broker implementations."""

    def put(self, message: Event) -> None: ...

    def get(self, timeout: float | None = None) -> Event:
        """Return the next event, or raise :class:`QueueEmpty` on timeout."""
        ...

    def task_done(self) -> None: ...

    def qsize(self) -> int: ...


class InMemoryEventQueue:
    """Thread-safe, process-local queue backed by :class:`queue.Queue`."""

    def __init__(self) -> None:
        self._queue: queue.Queue[Event] = queue.Queue()

    def put(self, message: Event) -> None:
        self._queue.put(message)

    def get(self, timeout: float | None = None) -> Event:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise QueueEmpty from exc

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()
