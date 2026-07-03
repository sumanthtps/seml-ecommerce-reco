"""Generate offline evidence (metrics JSON + plot) without starting the API.

Runs the domain layer directly, so it is fast and deterministic. Outputs land in
``artifacts/`` by default. The plot needs the optional ``evidence`` extra::

    pip install -e .[evidence]
    python scripts/generate_evidence.py
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from reco.domain import FeatureStore, Recommender, evaluate_precision_at_k
from reco.domain.recommender import Recommendation

SAMPLE_EVENTS = [
    {"user_id": "u7", "item_id": "P03", "action": "click"},
    {"user_id": "u7", "item_id": "P04", "action": "cart"},
    {"user_id": "u7", "item_id": "P12", "action": "purchase"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts"))
    parser.add_argument("--user", default="u7")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--no-plot", action="store_true", help="Skip the matplotlib plot.")
    return parser.parse_args()


def _plot(
    store: FeatureStore,
    recommendations: list[Recommendation],
    title: str,
    out_dir: Path,
) -> None:
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib not installed - skipping plot. Install with: pip install -e .[evidence]")
        return

    matrix = store.matrix_snapshot()
    fig = plt.figure(figsize=(12, 6), dpi=160, constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.28)

    ax_matrix = fig.add_subplot(grid[0, 0])
    image = ax_matrix.imshow(matrix[:20, :], aspect="auto", cmap="YlGnBu")
    ax_matrix.set_title("User-item interaction matrix (first 20 users)", fontsize=11, weight="bold")
    ax_matrix.set_xlabel("Products")
    ax_matrix.set_ylabel("Users")
    ax_matrix.set_xticks(np.arange(0, len(store.items), 5))
    ax_matrix.set_xticklabels(list(store.items)[::5], rotation=45, ha="right")
    fig.colorbar(image, ax=ax_matrix, fraction=0.046, pad=0.04, label="Interaction weight")

    ax_recs = fig.add_subplot(grid[0, 1])
    labels = [r.item_id for r in recommendations][::-1]
    scores = [r.score for r in recommendations][::-1]
    bars = ax_recs.barh(labels, scores, color="#2f80ed")
    ax_recs.set_title("Top recommendations", fontsize=11, weight="bold")
    ax_recs.set_xlabel("Collaborative-filtering score")
    ax_recs.grid(axis="x", alpha=0.25)
    for bar, score in zip(bars, scores, strict=True):
        ax_recs.text(score + 0.1, bar.get_y() + bar.get_height() / 2, f"{score:.2f}", va="center")

    fig.suptitle(title, fontsize=13, weight="bold")
    out_path = out_dir / "recommendation_output_plot.png"
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved plot to {out_path}")


def main() -> int:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    store = FeatureStore()
    store.seed_demo_data()
    recommender = Recommender(store)
    for event in SAMPLE_EVENTS:
        store.track_event(**event)

    recommendations = recommender.rank(args.user, args.k)
    metric = evaluate_precision_at_k(store.matrix_snapshot(), k=args.k)
    stats = store.stats()

    payload = {
        "sample_user": args.user,
        "strategy": recommender.strategy,
        "stats": asdict(stats),
        "offline_metric": metric.as_dict(),
        "recommendations": [{"item_id": r.item_id, "score": r.score} for r in recommendations],
    }
    (args.out / "offline_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

    if not args.no_plot:
        title = f"{metric.metric}={metric.value:.3f}, events={stats.events_processed}"
        _plot(store, recommendations, title, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
