"""Structured logging setup shared by both services.

Production systems ship JSON logs to a central aggregator; local development is
easier to read as plain text. ``configure_logging`` supports both via the
``log_format`` setting. A per-request id is carried on a context variable and
injected into every log record, so a single request can be traced end to end.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Standard LogRecord attributes; anything else on a record is treated as "extra"
# structured context and included in JSON output.
_RESERVED_RECORD_KEYS = frozenset(
    vars(logging.makeLogRecord({})).keys() | {"message", "asctime", "taskName"}
)


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_var.get()
        if request_id is not None:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_KEYS and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


class ConsoleFormatter(logging.Formatter):
    """Compact, human-readable formatter for local development."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
            datefmt="%H:%M:%S",
        )

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        request_id = request_id_var.get()
        return f"[{request_id}] {base}" if request_id else base


def configure_logging(level: str = "INFO", log_format: str = "json") -> None:
    """Configure root and uvicorn loggers idempotently."""
    formatter: logging.Formatter = JsonFormatter() if log_format == "json" else ConsoleFormatter()

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Route uvicorn's own loggers through our handler instead of its defaults.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a module logger (thin wrapper for a single import point)."""
    return logging.getLogger(name)
