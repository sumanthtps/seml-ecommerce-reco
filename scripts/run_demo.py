"""Exercise CQRS commands and queries through the two live microservices."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--command-url",
        default=os.environ.get("SEML_COMMAND_URL", "http://127.0.0.1:8101"),
    )
    parser.add_argument(
        "--query-url",
        default=os.environ.get("SEML_QUERY_URL", "http://127.0.0.1:8102"),
    )
    parser.add_argument("--save", type=Path)
    return parser.parse_args()


def execute_demo(command_url: str, query_url: str) -> dict[str, Any]:
    """Send one write, rebuild the model, and query the new read model."""
    transcript: dict[str, Any] = {}
    with httpx.Client(timeout=30.0) as client:
        write_response = client.post(
            f"{command_url}/commands/interactions",
            json={"user_id": "u007", "item_id": "P012", "action": "purchase"},
        )
        write_response.raise_for_status()
        transcript["interaction_command"] = write_response.json()

        train_response = client.post(
            f"{command_url}/commands/train",
            json={"k": 5, "holdout_per_user": 2},
        )
        train_response.raise_for_status()
        transcript["train_command"] = train_response.json()

        query_response = client.get(
            f"{query_url}/queries/recommendations",
            params={"user_id": "u007", "k": 5},
        )
        query_response.raise_for_status()
        transcript["recommendation_query"] = query_response.json()

        info_response = client.get(f"{query_url}/queries/model-info")
        info_response.raise_for_status()
        transcript["model_info"] = info_response.json()
    return transcript


def main() -> int:
    args = parse_args()
    try:
        transcript = execute_demo(args.command_url, args.query_url)
    except httpx.HTTPError as exc:
        print(f"ERROR: {exc}")
        return 1

    print("=== CQRS + MICROSERVICES LIVE DEMO ===")
    print(json.dumps(transcript, indent=2))
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        print(f"Saved transcript to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
