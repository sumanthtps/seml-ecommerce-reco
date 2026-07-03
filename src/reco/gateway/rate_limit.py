"""A tiny in-memory rate limiter for the gateway.

This is intentionally simple (a per-key minimum interval) and process-local. A
production gateway would use a shared store such as Redis with a token-bucket or
sliding-window algorithm; the interface here would stay the same.
"""

from __future__ import annotations

import threading
import time


class RateLimiter:
    """Allows at most one request per ``min_interval_seconds`` per key."""

    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = min_interval_seconds
        self._last_seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """Return ``True`` if a request for ``key`` is allowed right now."""
        if self._min_interval <= 0:
            return True
        now = time.monotonic()
        with self._lock:
            last = self._last_seen.get(key, 0.0)
            if now - last < self._min_interval:
                return False
            self._last_seen[key] = now
            return True
