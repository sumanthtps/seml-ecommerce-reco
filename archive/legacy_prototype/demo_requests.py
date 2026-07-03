"""Small client used to prove the API Gateway and Event-Driven flow.

Run this after starting both FastAPI services. It sends a few user events
through the gateway and then asks the gateway for recommendations.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

GATEWAY = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000")
HEADERS = {"Authorization": "Bearer seml-demo-token"}
EVIDENCE_DIR = Path("evidence")


def call_api(method: str, path: str, **kwargs) -> dict:
    """Call the gateway and print a helpful error if services are not running."""
    url = f"{GATEWAY}{path}"
    try:
        response = requests.request(method, url, headers=HEADERS, timeout=10, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        raise SystemExit(
            f"Could not connect to {GATEWAY}. Start the recommendation service and gateway first."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise SystemExit(f"Gateway returned {response.status_code}: {response.text}") from exc


def main() -> None:
    """Run the demo scenario and save the request/response transcript."""
    EVIDENCE_DIR.mkdir(exist_ok=True)

    # These events simulate one user browsing, adding to cart, and purchasing.
    events = [
        {"user_id": "u7", "item_id": "P03", "action": "click"},
        {"user_id": "u7", "item_id": "P04", "action": "cart"},
        {"user_id": "u7", "item_id": "P12", "action": "purchase"},
    ]

    transcript: list[dict] = []
    for event in events:
        payload = call_api("POST", "/activity", json=event)
        transcript.append({"request": "POST /activity", "body": event, "response": payload})
        print("POST /activity")
        print(json.dumps(payload, indent=2))

        # The demo gateway has a small per-user rate limit.
        time.sleep(0.35)

    # Give the background consumer time to process the queued events.
    time.sleep(0.6)
    payload = call_api("GET", "/recommend", params={"user_id": "u7", "k": 5})
    transcript.append({"request": "GET /recommend?user_id=u7&k=5", "response": payload})

    print("GET /recommend?user_id=u7&k=5")
    print(json.dumps(payload, indent=2))

    # The report builder uses these files as evidence.
    (EVIDENCE_DIR / "demo_output.json").write_text(json.dumps(transcript, indent=2), encoding="utf-8")
    (EVIDENCE_DIR / "demo_output.txt").write_text(
        "\n\n".join(
            f"{entry['request']}\n{json.dumps(entry['response'], indent=2)}" for entry in transcript
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
