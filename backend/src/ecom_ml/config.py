"""Environment-based paths shared by the two services."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime file locations for the reproducible local deployment."""

    data_path: Path
    users_path: Path
    artifact_dir: Path

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            data_path=Path(os.environ.get("SEML_DATA_PATH", "data/interactions.csv")),
            users_path=Path(os.environ.get("SEML_USERS_PATH", "data/users.csv")),
            artifact_dir=Path(os.environ.get("SEML_ARTIFACT_DIR", "artifacts")),
        )
