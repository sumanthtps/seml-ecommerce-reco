"""Integration tests proving the Microservices and CQRS implementation."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ecom_ml.command_service.main import create_app as create_command_app
from ecom_ml.ml.data import generate_demo_interactions
from ecom_ml.ml.pipeline import train_pipeline
from ecom_ml.query_service.main import create_app as create_query_app
from ecom_ml.users import UserProfile, append_user, generate_default_users, load_users


def test_command_service_accepts_write_and_trains(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    users_path = tmp_path / "users.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    generate_default_users(users_path)

    with TestClient(
        create_command_app(
            data_path=data_path,
            users_path=users_path,
            artifact_dir=artifact_dir,
        )
    ) as command_client:
        response = command_client.post(
            "/commands/interactions",
            json={"user_id": "u001", "item_id": "P001", "action": "purchase"},
        )
        assert response.status_code == 202
        assert response.json()["pattern"] == "CQRS-command"

        training = command_client.post(
            "/commands/train",
            json={"k": 5, "holdout_per_user": 2},
        )
        user = command_client.post(
            "/commands/users",
            json={"name": "Ananya", "interest": "Electronics"},
        )
        assert training.status_code == 200
        assert training.json()["status"] == "trained"
        assert user.status_code == 201
        assert user.json()["name"] == "Ananya"
        assert user.json()["interest"] == "Electronics"
        assert len(load_users(users_path)) == 6


def test_query_service_reads_model_without_write_routes(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    users_path = tmp_path / "users.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    generate_default_users(users_path)
    append_user(
        users_path,
        UserProfile(
            user_id="usr-ananya",
            name="Ananya",
            interest="Electronics",
            created_at="2026-01-02T09:00:00+00:00",
        ),
    )
    train_pipeline(data_path, artifact_dir)

    with TestClient(
        create_query_app(
            artifact_dir=artifact_dir,
            data_path=data_path,
            users_path=users_path,
        )
    ) as query_client:
        health = query_client.get("/health")
        response = query_client.get(
            "/queries/recommendations",
            params={"user_id": "u001", "k": 5},
        )
        catalogue = query_client.get("/queries/products")
        users = query_client.get("/queries/users")
        cold_start = query_client.get(
            "/queries/recommendations",
            params={"user_id": "usr-ananya", "k": 5},
        )
        recent_actions = query_client.get(
            "/queries/recent-actions",
            params={"user_id": "u001", "limit": 3},
        )
        write_attempt = query_client.post(
            "/commands/interactions",
            json={"user_id": "u001", "item_id": "P001", "action": "view"},
        )

    assert health.json()["status"] == "ok"
    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 5
    assert response.json()["recommendations"][0]["product_name"]
    assert response.json()["recommendations"][0]["category"]
    assert catalogue.status_code == 200
    assert len(catalogue.json()["products"]) == 60
    assert catalogue.json()["products"][0] == {
        "item_id": "P001",
        "product_name": "Wireless Noise-Cancelling Headphones",
        "category": "Electronics",
    }
    assert users.status_code == 200
    assert [user["name"] for user in users.json()["users"][:5]] == [
        "Shreyas",
        "Sumanth",
        "Ravi",
        "Vivek",
        "Nishant",
    ]
    assert cold_start.status_code == 200
    assert cold_start.json()["strategy"] == "interest-based-cold-start"
    assert len(cold_start.json()["recommendations"]) == 5
    assert {
        recommendation["category"] for recommendation in cold_start.json()["recommendations"]
    } == {"Electronics"}
    assert recent_actions.status_code == 200
    assert recent_actions.json()["user_id"] == "u001"
    assert recent_actions.json()["interest"] == "Electronics"
    assert len(recent_actions.json()["actions"]) == 3
    assert recent_actions.json()["actions"][0]["product_name"]
    assert recent_actions.json()["actions"][0]["action"] in {
        "view",
        "click",
        "cart",
        "purchase",
    }
    assert write_attempt.status_code == 404


def test_query_service_reports_unknown_user(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    users_path = tmp_path / "users.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    generate_default_users(users_path)
    train_pipeline(data_path, artifact_dir)

    with TestClient(
        create_query_app(
            artifact_dir=artifact_dir,
            data_path=data_path,
            users_path=users_path,
        )
    ) as query_client:
        response = query_client.get(
            "/queries/recommendations",
            params={"user_id": "unknown", "k": 5},
        )
    assert response.status_code == 404
