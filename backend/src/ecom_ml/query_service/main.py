"""FastAPI query service backed by the latest immutable model artifact."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI, HTTPException, Query

from ecom_ml.api_models import (
    Action,
    Interest,
    ProductCatalogResponse,
    ProductInfo,
    RecentAction,
    RecentActionsResponse,
    RecommendationItem,
    RecommendationResponse,
    UserCatalogResponse,
    UserProfileInfo,
)
from ecom_ml.catalog import PRODUCTS, get_product
from ecom_ml.config import Settings
from ecom_ml.ml.artifact import METADATA_FILENAME, load_artifact
from ecom_ml.ml.data import load_interactions
from ecom_ml.ml.model import CollaborativeFilteringModel
from ecom_ml.users import load_users


class ModelRepository:
    """Thread-safe, mtime-aware cache of the CQRS read model."""

    def __init__(self, artifact_dir: Path) -> None:
        self._artifact_dir = artifact_dir
        self._lock = threading.RLock()
        self._model: CollaborativeFilteringModel | None = None
        self._metadata: dict[str, Any] | None = None
        self._metadata_mtime_ns = -1

    def get(self) -> tuple[CollaborativeFilteringModel, dict[str, Any]]:
        metadata_path = self._artifact_dir / METADATA_FILENAME
        if not metadata_path.exists():
            raise FileNotFoundError("no trained model; run the training command first")
        current_mtime = metadata_path.stat().st_mtime_ns
        with self._lock:
            if self._model is None or current_mtime != self._metadata_mtime_ns:
                self._model, self._metadata = load_artifact(self._artifact_dir)
                self._metadata_mtime_ns = current_mtime
            assert self._metadata is not None
            return self._model, dict(self._metadata)


def create_app(
    *,
    artifact_dir: Path | None = None,
    data_path: Path | None = None,
    users_path: Path | None = None,
) -> FastAPI:
    """Build a query service with an injectable artifact location."""
    settings = Settings.from_env()
    repository = ModelRepository(artifact_dir or settings.artifact_dir)
    resolved_data = data_path or settings.data_path
    resolved_users = users_path or settings.users_path
    application = FastAPI(
        title="SEML Recommendation Query Service",
        version="1.0.0",
        description=(
            "CQRS read side: independently serves low-latency recommendations "
            "from a versioned collaborative-filtering model."
        ),
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        try:
            model, _ = repository.get()
        except (FileNotFoundError, ValueError):
            return {"status": "not_ready", "service": "query-service", "pattern": "CQRS-query"}
        return {
            "status": "ok",
            "service": "query-service",
            "pattern": "CQRS-query",
            "model_version": model.version,
        }

    @application.get("/queries/model-info")
    def model_info() -> dict[str, Any]:
        try:
            _, metadata = repository.get()
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"pattern": "CQRS-query", **metadata}

    @application.get("/queries/products", response_model=ProductCatalogResponse)
    def products() -> ProductCatalogResponse:
        return ProductCatalogResponse(
            products=[
                ProductInfo(
                    item_id=product.item_id,
                    product_name=product.name,
                    category=product.category,
                )
                for product in PRODUCTS
            ]
        )

    @application.get("/queries/users", response_model=UserCatalogResponse)
    def users() -> UserCatalogResponse:
        try:
            profiles = load_users(resolved_users)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return UserCatalogResponse(
            users=[
                UserProfileInfo(
                    user_id=profile.user_id,
                    name=profile.name,
                    interest=cast(Interest, profile.interest),
                    created_at=profile.created_at,
                )
                for profile in profiles
            ]
        )

    @application.get("/queries/recent-actions", response_model=RecentActionsResponse)
    def recent_actions(
        user_id: str = Query(min_length=1),
        limit: int = Query(default=3, ge=1, le=10),
    ) -> RecentActionsResponse:
        try:
            rows = load_interactions(resolved_data)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        selected = [row for row in reversed(rows) if row.user_id == user_id][:limit]
        actions: list[RecentAction] = []
        for row in selected:
            product = get_product(row.item_id)
            actions.append(
                RecentAction(
                    event_id=row.event_id,
                    timestamp=row.timestamp,
                    user_id=row.user_id,
                    item_id=row.item_id,
                    product_name=product.name,
                    category=product.category,
                    action=cast(Action, row.action),
                )
            )
        try:
            profiles = load_users(resolved_users)
        except (FileNotFoundError, ValueError):
            profiles = []
        profile = next((profile for profile in profiles if profile.user_id == user_id), None)
        interest = cast(Interest, profile.interest) if profile is not None else None
        return RecentActionsResponse(user_id=user_id, interest=interest, actions=actions)

    @application.get("/queries/recommendations", response_model=RecommendationResponse)
    def recommendations(
        user_id: str = Query(min_length=1),
        k: int = Query(default=5, ge=1, le=20),
    ) -> RecommendationResponse:
        try:
            model, _ = repository.get()
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        recommendation_items: list[RecommendationItem] = []
        strategy = "item-based-collaborative-filtering"
        if user_id in model.users:
            ranked = model.recommend(user_id, k)
            for recommendation in ranked:
                product = get_product(recommendation.item_id)
                recommendation_items.append(
                    RecommendationItem(
                        item_id=recommendation.item_id,
                        product_name=product.name,
                        category=product.category,
                        score=recommendation.score,
                    )
                )
        else:
            try:
                profiles = load_users(resolved_users)
            except (FileNotFoundError, ValueError) as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
            profile = next((profile for profile in profiles if profile.user_id == user_id), None)
            if profile is None:
                raise HTTPException(status_code=404, detail=f"unknown user: {user_id}")

            preferred_products = [
                product for product in PRODUCTS if product.category == profile.interest
            ][:k]
            recommendation_items = [
                RecommendationItem(
                    item_id=product.item_id,
                    product_name=product.name,
                    category=product.category,
                    score=round(1.0 - (index * 0.05), 4),
                )
                for index, product in enumerate(preferred_products)
            ]
            strategy = "interest-based-cold-start"

        return RecommendationResponse(
            user_id=user_id,
            model_version=model.version,
            strategy=strategy,
            recommendations=recommendation_items,
        )

    return application


app = create_app()
