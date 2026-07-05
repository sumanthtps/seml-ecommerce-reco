"""Typed API contracts shared by command and query services."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Action = Literal["view", "click", "cart", "purchase"]
Interest = Literal[
    "Electronics",
    "Home & Kitchen",
    "Fashion",
    "Personal Care",
    "Fitness & Lifestyle",
]


class InteractionCommand(BaseModel):
    """CQRS command to record a user action."""

    user_id: str = Field(min_length=1, examples=["u007"])
    item_id: str = Field(min_length=1, examples=["P012"])
    action: Action
    timestamp: str | None = None


class TrainCommand(BaseModel):
    """CQRS command controlling offline evaluation cutoffs."""

    k: int = Field(default=5, ge=1, le=20)
    holdout_per_user: int = Field(default=2, ge=1, le=5)


class CreateUserCommand(BaseModel):
    """CQRS command for creating a named customer profile."""

    name: str = Field(min_length=1, max_length=80, examples=["Ananya"])
    interest: Interest


class UserProfileInfo(BaseModel):
    """Public read model for one named customer."""

    user_id: str
    name: str
    interest: Interest
    created_at: str


class UserCommandResponse(UserProfileInfo):
    """Result returned after a user profile command is accepted."""

    status: Literal["created"]
    pattern: Literal["CQRS-command"]


class UserCatalogResponse(BaseModel):
    """Named users available to the dashboard."""

    users: list[UserProfileInfo]


class ProductInfo(BaseModel):
    """Human-readable metadata for one catalogue product."""

    item_id: str
    product_name: str
    category: str


class RecommendationItem(ProductInfo):
    """One ranked product returned by the read model."""

    score: float


class RecommendationResponse(BaseModel):
    """CQRS read-model response."""

    user_id: str
    model_version: str
    strategy: str
    recommendations: list[RecommendationItem]


class ProductCatalogResponse(BaseModel):
    """Products available to the interaction and recommendation workflows."""

    products: list[ProductInfo]


class RecentAction(ProductInfo):
    """One recent customer action enriched with product metadata."""

    event_id: str
    timestamp: str
    user_id: str
    action: Action


class RecentActionsResponse(BaseModel):
    """Most recent actions for one customer, newest first."""

    user_id: str
    interest: Interest | None
    actions: list[RecentAction]
