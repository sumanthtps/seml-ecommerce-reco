"""Data loading and preprocessing for implicit-feedback recommendations."""

from __future__ import annotations

import csv
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

ACTION_WEIGHTS: Final[dict[str, float]] = {
    "view": 1.0,
    "click": 2.0,
    "cart": 3.0,
    "purchase": 5.0,
}
CSV_FIELDS: Final[tuple[str, ...]] = ("event_id", "timestamp", "user_id", "item_id", "action")
_WRITE_LOCK = threading.Lock()


@dataclass(frozen=True, slots=True)
class Interaction:
    """One raw storefront interaction."""

    event_id: str
    timestamp: str
    user_id: str
    item_id: str
    action: str

    def as_csv_row(self) -> dict[str, str]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "item_id": self.item_id,
            "action": self.action,
        }


@dataclass(frozen=True, slots=True)
class PreparedInteractions:
    """Validated, weighted user-item matrix and its index labels."""

    users: tuple[str, ...]
    items: tuple[str, ...]
    matrix: NDArray[np.float64]
    raw_event_count: int
    unique_event_count: int


def generate_demo_interactions(
    path: Path,
    *,
    user_count: int = 80,
    item_count: int = 60,
    seed: int = 546,
) -> list[Interaction]:
    """Generate deterministic clustered shopping behavior and save it as CSV."""
    rng = np.random.default_rng(seed)
    users = [f"u{i:03d}" for i in range(1, user_count + 1)]
    items = [f"P{i:03d}" for i in range(1, item_count + 1)]
    cluster_count = 5
    cluster_size = item_count // cluster_count
    base_time = datetime(2026, 1, 1, 9, 0, tzinfo=UTC)
    events: list[Interaction] = []

    for user_index, user_id in enumerate(users):
        cluster = user_index % cluster_count
        core_start = cluster * cluster_size
        neighbor_start = ((cluster + 1) % cluster_count) * cluster_size
        core = np.arange(core_start, core_start + cluster_size)
        neighbor = np.arange(neighbor_start, neighbor_start + cluster_size)
        selected_core = rng.choice(core, size=min(10, len(core)), replace=False)
        selected_neighbor = rng.choice(neighbor, size=min(2, len(neighbor)), replace=False)

        for item_index in np.concatenate((selected_core, selected_neighbor)):
            action = str(
                rng.choice(
                    ["view", "click", "cart", "purchase"],
                    p=[0.30, 0.35, 0.22, 0.13],
                )
            )
            event_number = len(events) + 1
            timestamp = (base_time + timedelta(seconds=event_number * 17)).isoformat()
            events.append(
                Interaction(
                    event_id=f"evt-{event_number:05d}",
                    timestamp=timestamp,
                    user_id=user_id,
                    item_id=items[int(item_index)],
                    action=action,
                )
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS))
        writer.writeheader()
        writer.writerows(event.as_csv_row() for event in events)
    return events


def load_interactions(path: Path) -> list[Interaction]:
    """Read raw events from CSV and validate the required schema."""
    if not path.exists():
        raise FileNotFoundError(f"interaction dataset not found: {path}")

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not set(CSV_FIELDS).issubset(reader.fieldnames):
            raise ValueError(f"dataset must contain columns: {', '.join(CSV_FIELDS)}")
        rows = [
            Interaction(
                event_id=(row["event_id"] or "").strip(),
                timestamp=(row["timestamp"] or "").strip(),
                user_id=(row["user_id"] or "").strip(),
                item_id=(row["item_id"] or "").strip(),
                action=(row["action"] or "").strip().lower(),
            )
            for row in reader
        ]
    if not rows:
        raise ValueError("interaction dataset is empty")
    return rows


def append_interaction(path: Path, interaction: Interaction) -> None:
    """Append one validated command to the raw interaction log."""
    validate_interaction(interaction)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _WRITE_LOCK:
        needs_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS))
            if needs_header:
                writer.writeheader()
            writer.writerow(interaction.as_csv_row())


def validate_interaction(interaction: Interaction) -> None:
    """Validate fields used by both batch loading and command ingestion."""
    if not interaction.event_id:
        raise ValueError("event_id is required")
    if not interaction.user_id:
        raise ValueError("user_id is required")
    if not interaction.item_id:
        raise ValueError("item_id is required")
    if interaction.action not in ACTION_WEIGHTS:
        allowed = ", ".join(ACTION_WEIGHTS)
        raise ValueError(f"action must be one of: {allowed}")
    try:
        datetime.fromisoformat(interaction.timestamp)
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc


def prepare_interactions(rows: list[Interaction]) -> PreparedInteractions:
    """Deduplicate, validate, weight, and aggregate raw events into a matrix."""
    unique: dict[str, Interaction] = {}
    for row in rows:
        validate_interaction(row)
        unique.setdefault(row.event_id, row)

    users = tuple(sorted({row.user_id for row in unique.values()}))
    items = tuple(sorted({row.item_id for row in unique.values()}))
    if not users or not items:
        raise ValueError("at least one user and item are required")

    user_index = {user_id: index for index, user_id in enumerate(users)}
    item_index = {item_id: index for index, item_id in enumerate(items)}
    matrix = np.zeros((len(users), len(items)), dtype=np.float64)
    for row in unique.values():
        matrix[user_index[row.user_id], item_index[row.item_id]] += ACTION_WEIGHTS[row.action]

    return PreparedInteractions(
        users=users,
        items=items,
        matrix=matrix,
        raw_event_count=len(rows),
        unique_event_count=len(unique),
    )
