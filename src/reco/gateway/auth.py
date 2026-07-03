"""Bearer-token authentication for the gateway.

Using :class:`HTTPBearer` registers the scheme with OpenAPI, so Swagger UI shows
an "Authorize" button. The token comparison is constant-time to avoid leaking
information through timing.
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Static demo bearer token (configure via GATEWAY_AUTH_TOKEN).",
)


def require_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Reject requests that do not present the expected bearer token."""
    expected: str = request.app.state.settings.auth_token
    presented = (
        credentials.credentials
        if credentials is not None and credentials.scheme.lower() == "bearer"
        else ""
    )
    if not secrets.compare_digest(presented, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
