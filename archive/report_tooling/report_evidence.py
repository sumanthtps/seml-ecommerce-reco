"""Generate report evidence for the recommendation prototype.

This script runs the recommender without starting the APIs. It creates the
metric JSON, console-output text, and plot used in the final assignment report.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import recommender_engine

EVIDENCE_DIR = Path("evidence")


def main() -> None:
    """Create all offline evidence artifacts for the report."""
    EVIDENCE_DIR.mkdir(exist_ok=True)
    recommender_engine.seed_demo_data()

    # Apply the same sample user events used by the live demo client.
    for event in [
        {"user_id": "u7", "item_id": "P03", "action": "click"},
        {"user_id": "u7", "item_id": "P04", "action": "cart"},
        {"user_id": "u7", "item_id": "P12", "action": "purchase"},
    ]:
        recommender_engine.track_event(**event)

    recommendations = recommender_engine.rank_items("u7", 5)
    metrics = recommender_engine.evaluate_precision_at_k(k=5, holdout_per_user=3)
    stats = recommender_engine.stats()
    matrix = recommender_engine.matrix_snapshot()

    # Save machine-readable evidence for repeatability.
    evidence_payload = {
        "sample_user": "u7",
        "stats": stats,
        "offline_metric": metrics,
        "recommendations": recommendations,
    }

    (EVIDENCE_DIR / "offline_metrics.json").write_text(
        json.dumps(evidence_payload, indent=2),
        encoding="utf-8",
    )

    # Save a plain-text version that can be pasted into the report.
    output_text = [
        "=== Recommendation service - sample run ===",
        f"Dataset: {stats['users']} users x {stats['items']} items, overall matrix density {stats['matrix_density']:.2%}",
        f"Offline {metrics['metric']} (leave-three-out, synthetic interactions): {metrics['value']:.3f}",
        "Sample GET /recommend?user_id=u7&k=5 response:",
        json.dumps(
            {
                "user_id": "u7",
                "strategy": "item-based-collaborative-filtering",
                "recommendations": recommendations,
            },
            indent=2,
        ),
    ]
    (EVIDENCE_DIR / "sample_output.txt").write_text("\n".join(output_text), encoding="utf-8")

    # Plot both the interaction matrix and the returned top-5 recommendations.
    fig = plt.figure(figsize=(12, 6), dpi=160, constrained_layout=True)
    grid = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.28)

    ax_matrix = fig.add_subplot(grid[0, 0])
    shown = matrix[:20, :]
    image = ax_matrix.imshow(shown, aspect="auto", cmap="YlGnBu")
    ax_matrix.set_title("User-item interaction matrix (first 20 users)", fontsize=11, weight="bold")
    ax_matrix.set_xlabel("Products")
    ax_matrix.set_ylabel("Users")
    ax_matrix.set_xticks(np.arange(0, len(recommender_engine.item_ids()), 5))
    ax_matrix.set_xticklabels(recommender_engine.item_ids()[::5], rotation=45, ha="right")
    ax_matrix.set_yticks(np.arange(0, 20, 2))
    ax_matrix.set_yticklabels(recommender_engine.user_ids()[:20:2])
    fig.colorbar(image, ax=ax_matrix, fraction=0.046, pad=0.04, label="Interaction weight")

    ax_recs = fig.add_subplot(grid[0, 1])
    item_labels = [rec["item_id"] for rec in recommendations][::-1]
    scores = [rec["score"] for rec in recommendations][::-1]
    bars = ax_recs.barh(item_labels, scores, color="#2f80ed")
    ax_recs.set_title("Top-5 recommendations for user u7", fontsize=11, weight="bold")
    ax_recs.set_xlabel("Collaborative-filtering score")
    ax_recs.grid(axis="x", alpha=0.25)
    for bar, score in zip(bars, scores):
        ax_recs.text(score + 0.1, bar.get_y() + bar.get_height() / 2, f"{score:.2f}", va="center", fontsize=9)

    fig.suptitle(
        f"Executed evidence: {metrics['metric']}={metrics['value']:.3f}, events={stats['events_processed']}",
        fontsize=13,
        weight="bold",
    )
    fig.savefig(EVIDENCE_DIR / "recommendation_output_plot.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()

