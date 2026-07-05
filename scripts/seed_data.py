"""Generate the deterministic raw interaction CSV used by the assignment."""

from __future__ import annotations

import argparse
from pathlib import Path

from ecom_ml.ml.data import generate_demo_interactions
from ecom_ml.users import generate_default_users


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/interactions.csv"))
    parser.add_argument("--users", type=Path, default=Path("data/users.csv"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events = generate_demo_interactions(args.out)
    users = generate_default_users(args.users)
    print(f"Generated {len(events)} interactions at {args.out}")
    print(f"Generated {len(users)} user profiles at {args.users}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
