"""Integration tests proving the Microservices and CQRS implementation."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from ecom_ml.command_service.main import create_app as create_command_app
from ecom_ml.ml.data import generate_demo_interactions
from ecom_ml.ml.pipeline import train_pipeline
from ecom_ml.query_service.main import create_app as create_query_app


def test_command_service_accepts_write_and_trains(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)

    with TestClient(
        create_command_app(data_path=data_path, artifact_dir=artifact_dir)
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
        assert training.status_code == 200
        assert training.json()["status"] == "trained"


def test_query_service_reads_model_without_write_routes(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    train_pipeline(data_path, artifact_dir)

    with TestClient(create_query_app(artifact_dir=artifact_dir)) as query_client:
        health = query_client.get("/health")
        response = query_client.get(
            "/queries/recommendations",
            params={"user_id": "u001", "k": 5},
        )
        catalogue = query_client.get("/queries/products")
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
    assert write_attempt.status_code == 404


def test_query_service_reports_unknown_user(tmp_path: Path) -> None:
    data_path = tmp_path / "interactions.csv"
    artifact_dir = tmp_path / "artifacts"
    generate_demo_interactions(data_path, user_count=20, item_count=30)
    train_pipeline(data_path, artifact_dir)

    with TestClient(create_query_app(artifact_dir=artifact_dir)) as query_client:
        response = query_client.get(
            "/queries/recommendations",
            params={"user_id": "unknown", "k": 5},
        )
    assert response.status_code == 404
