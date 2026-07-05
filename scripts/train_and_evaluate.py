"""Run the complete ML pipeline and print its machine-readable summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ecom_ml.ml.pipeline import train_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/interactions.csv"))
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = train_pipeline(args.data, args.artifacts)
    print(json.dumps(summary.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
