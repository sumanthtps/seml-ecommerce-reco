"""Drive a short scenario through the gateway and print the transcript.

Both services must be running first - either ``docker compose up`` or two local
uvicorn processes (see the README). Examples::

    python scripts/run_demo.py
    python scripts/run_demo.py --gateway http://localhost:8000 --save artifacts/demo.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

EVENTS = [
    {"user_id": "u7", "item_id": "P03", "action": "click"},
    {"user_id": "u7", "item_id": "P04", "action": "cart"},
    {"user_id": "u7", "item_id": "P12", "action": "purchase"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", default=os.environ.get("GATEWAY_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--token", default=os.environ.get("GATEWAY_AUTH_TOKEN", "seml-demo-token"))
    parser.add_argument("--user", default="u7")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--save", type=Path, default=None, help="Write the JSON transcript here.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    headers = {"Authorization": f"Bearer {args.token}"}
    transcript: list[dict] = []

    try:
        with httpx.Client(base_url=args.gateway, headers=headers, timeout=10.0) as client:
            for event in EVENTS:
                body = client.post("/activity", json=event).raise_for_status().json()
                transcript.append({"request": "POST /activity", "body": event, "response": body})
                print("POST /activity ->", json.dumps(body, indent=2))
                time.sleep(0.35)  # respect the gateway's per-user rate limit

            time.sleep(0.6)  # give the background consumer time to drain the queue
            body = (
                client.get("/recommend", params={"user_id": args.user, "k": args.k})
                .raise_for_status()
                .json()
            )
            transcript.append(
                {"request": f"GET /recommend?user_id={args.user}&k={args.k}", "response": body}
            )
            print("GET /recommend ->", json.dumps(body, indent=2))
    except httpx.ConnectError:
        print(
            f"ERROR: cannot connect to {args.gateway}. Start the services first.", file=sys.stderr
        )
        return 1
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: {exc.response.status_code} {exc.response.text}", file=sys.stderr)
        return 1

    if args.save is not None:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        print(f"Saved transcript to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
