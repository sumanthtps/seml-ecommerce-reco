"""Integration tests for the recommendation service (real app, real consumer)."""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from reco.config import RecommendationSettings
from reco.recommendation.main import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = RecommendationSettings(
        seed_demo_data=True, log_format="console", consumer_poll_timeout=0.05
    )
    # `with` runs the lifespan, which seeds data and starts the consumer thread.
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_health_reports_consumer_running(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["consumer_running"] is True


def test_stats_reports_seeded_dataset(client: TestClient) -> None:
    body = client.get("/stats").json()
    assert body["users"] == 60
    assert body["items"] == 40
    assert body["events_processed"] > 0


def test_rank_returns_five_recommendations(client: TestClient) -> None:
    response = client.get("/rank", params={"user_id": "u7", "k": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["strategy"] == "item-based-collaborative-filtering"
    assert len(body["recommendations"]) == 5


def test_rank_unknown_user_is_400(client: TestClient) -> None:
    assert client.get("/rank", params={"user_id": "ghost"}).status_code == 400


def test_track_invalid_action_is_400(client: TestClient) -> None:
    response = client.post(
        "/track", json={"user_id": "u7", "item_id": "P03", "action": "frobnicate"}
    )
    assert response.status_code == 400


def test_track_event_is_processed_asynchronously(client: TestClient) -> None:
    baseline = client.get("/stats").json()["events_processed"]

    response = client.post("/track", json={"user_id": "u7", "item_id": "P03", "action": "purchase"})
    assert response.status_code == 202
    assert response.json()["pattern"] == "event-driven"

    # The consumer applies the event on its own thread; poll until it lands.
    processed = baseline
    deadline = time.time() + 5.0
    while time.time() < deadline:
        processed = client.get("/stats").json()["events_processed"]
        if processed > baseline:
            break
        time.sleep(0.05)
    assert processed == baseline + 1
