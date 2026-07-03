"""Domain-specific exceptions.

The service layer catches :class:`DomainError` and maps it to the appropriate
HTTP status code, so the domain never needs to know about HTTP.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all recoverable domain errors (mapped to HTTP 4xx)."""


class UnknownUserError(DomainError):
    """Raised when an event or query references an unknown user id."""


class UnknownItemError(DomainError):
    """Raised when an event references an unknown item id."""


class InvalidActionError(DomainError):
    """Raised when an activity event carries an unsupported action type."""


class InvalidParameterError(DomainError):
    """Raised when a query parameter is outside its allowed range."""
