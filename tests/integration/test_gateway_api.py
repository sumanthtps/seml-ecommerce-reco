"""Integration tests for the gateway.

The downstream recommendation service is replaced with an ``httpx.MockTransport``,
so these tests exercise the gateway's auth, rate limiting, and forwarding logic
in isolation - no live service required.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from reco.config import GatewaySettings
from reco.gateway.main import create_app
from reco.gateway.routes import get_http_client

TOKEN_HEADER = {"Authorization": "Bearer test-token"}


def _mock_downstream(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/health":
        return httpx.Response(200, json={"status": "ok", "service": "recommendation-service"})
    if path == "/rank":
        return httpx.Response(
            200,
            json={
                "user_id": "u7",
                "strategy": "item-based-collaborative-filtering",
                "recommendations": [{"item_id": "P28", "score": 10.0}],
                "stats": {},
            },
        )
    if path == "/track":
        return httpx.Response(202, json={"status": "accepted", "pattern": "event-driven"})
    return httpx.Response(404, json={"detail": "not found"})


def _build_client(rate_limit_seconds: float = 0.0) -> TestClient:
    settings = GatewaySettings(
        auth_token="test-token", rate_limit_seconds=rate_limit_seconds, log_format="console"
    )
    app = create_app(settings)
    mock_client = httpx.AsyncClient(
        transport=httpx.MockTransport(_mock_downstream), base_url="http://reco.test"
    )
    app.dependency_overrides[get_http_client] = lambda: mock_client
    return TestClient(app)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with _build_client() as test_client:
        yield test_client


def test_health_is_public(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["service"] == "api-gateway"
    assert body["internal_service"]["status"] == "ok"


def test_recommend_requires_authentication(client: TestClient) -> None:
    assert client.get("/recommend", params={"user_id": "u7"}).status_code == 401


def test_recommend_with_token_is_forwarded(client: TestClient) -> None:
    response = client.get("/recommend", params={"user_id": "u7", "k": 5}, headers=TOKEN_HEADER)
    assert response.status_code == 200
    body = response.json()
    assert body["served_by"] == "api-gateway"
    assert body["pattern"] == "api-gateway"


def test_activity_with_token_is_forwarded(client: TestClient) -> None:
    response = client.post(
        "/activity",
        json={"user_id": "u7", "item_id": "P03", "action": "click"},
        headers=TOKEN_HEADER,
    )
    assert response.status_code == 200
    assert response.json()["served_by"] == "api-gateway"


def test_wrong_token_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/recommend", params={"user_id": "u7"}, headers={"Authorization": "Bearer wrong"}
    )
    assert response.status_code == 401


def test_rate_limit_blocks_rapid_repeats() -> None:
    with _build_client(rate_limit_seconds=100.0) as client:
        first = client.get("/recommend", params={"user_id": "u9"}, headers=TOKEN_HEADER)
        second = client.get("/recommend", params={"user_id": "u9"}, headers=TOKEN_HEADER)
    assert first.status_code == 200
    assert second.status_code == 429
