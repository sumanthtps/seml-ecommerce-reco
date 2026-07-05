"""Generate the deterministic raw interaction CSV used by the assignment."""

from __future__ import annotations

import argparse
from pathlib import Path

from ecom_ml.ml.data import generate_demo_interactions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/interactions.csv"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events = generate_demo_interactions(args.out)
    print(f"Generated {len(events)} interactions at {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
