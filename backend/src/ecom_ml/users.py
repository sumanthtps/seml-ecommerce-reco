"""Persistent user profiles used for named users and cold-start interests."""

from __future__ import annotations

import csv
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from uuid import uuid4

from ecom_ml.catalog import CATEGORIES

USER_FIELDS: Final[tuple[str, ...]] = ("user_id", "name", "interest", "created_at")
DEFAULT_USER_SPECS: Final[tuple[tuple[str, str, str], ...]] = (
    ("u001", "Shreyas", "Electronics"),
    ("u002", "Sumanth", "Home & Kitchen"),
    ("u003", "Ravi", "Fashion"),
    ("u004", "Vivek", "Personal Care"),
    ("u005", "Nishant", "Fitness & Lifestyle"),
)
_WRITE_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class UserProfile:
    """One named customer profile with a cold-start interest."""

    user_id: str
    name: str
    interest: str
    created_at: str

    def as_csv_row(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "interest": self.interest,
            "created_at": self.created_at,
        }


def generate_default_users(path: Path) -> list[UserProfile]:
    """Write the five deterministic demonstration user profiles."""
    profiles = [
        UserProfile(
            user_id=user_id,
            name=name,
            interest=interest,
            created_at="2026-01-01T09:00:00+00:00",
        )
        for user_id, name, interest in DEFAULT_USER_SPECS
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(USER_FIELDS))
        writer.writeheader()
        writer.writerows(profile.as_csv_row() for profile in profiles)
    return profiles


def load_users(path: Path) -> list[UserProfile]:
    """Load and validate user profiles from the profile store."""
    if not path.exists():
        raise FileNotFoundError(f"user profile store not found: {path}")

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not set(USER_FIELDS).issubset(reader.fieldnames):
            raise ValueError(f"user profile store must contain: {', '.join(USER_FIELDS)}")
        profiles = [
            UserProfile(
                user_id=(row["user_id"] or "").strip(),
                name=(row["name"] or "").strip(),
                interest=(row["interest"] or "").strip(),
                created_at=(row["created_at"] or "").strip(),
            )
            for row in reader
        ]
    for profile in profiles:
        validate_user(profile)
    return profiles


def create_user(name: str, interest: str) -> UserProfile:
    """Create a validated profile with a readable collision-resistant ID."""
    cleaned_name = name.strip()
    slug = re.sub(r"[^a-z0-9]+", "-", cleaned_name.lower()).strip("-") or "user"
    profile = UserProfile(
        user_id=f"usr-{slug}-{uuid4().hex[:6]}",
        name=cleaned_name,
        interest=interest.strip(),
        created_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    validate_user(profile)
    return profile


def append_user(path: Path, profile: UserProfile) -> None:
    """Append one user profile after validating uniqueness and fields."""
    validate_user(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _WRITE_LOCK:
        existing = load_users(path) if path.exists() else []
        if any(user.user_id == profile.user_id for user in existing):
            raise ValueError(f"user ID already exists: {profile.user_id}")
        needs_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(USER_FIELDS))
            if needs_header:
                writer.writeheader()
            writer.writerow(profile.as_csv_row())


def validate_user(profile: UserProfile) -> None:
    """Validate profile fields shared by loading and command ingestion."""
    if not profile.user_id:
        raise ValueError("user_id is required")
    if not profile.name:
        raise ValueError("name is required")
    if profile.interest not in CATEGORIES:
        raise ValueError(f"interest must be one of: {', '.join(CATEGORIES)}")
    try:
        datetime.fromisoformat(profile.created_at)
    except ValueError as exc:
        raise ValueError("created_at must be ISO-8601") from exc
