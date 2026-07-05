"""Build and execute the assignment notebook with saved outputs."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "final_submission"
DETAILS = json.loads((ROOT / "submission_details.json").read_text(encoding="utf-8"))
GROUP = DETAILS["group_number"]
OUTPUT = FINAL_DIR / f"{GROUP}.ipynb"


def source_block(relative_path: str, heading: str) -> str:
    source = (ROOT / relative_path).read_text(encoding="utf-8")
    return f"### {heading}\n\n```python\n{source}\n```"


def build_notebook() -> Path:
    """Create a self-contained narrative notebook and execute all code cells."""
    member_rows = "\n".join(
        f"| {index} | {member['bits_id']} | {member['name']} | "
        f"{member['contribution']} | {member['percentage']}% |"
        for index, member in enumerate(DETAILS["members"], start=1)
    )
    cells = [
        new_markdown_cell(
            f"""
# AIMLCZG546 - Software Engineering for Machine Learning
## Assignment I: ML-Based Product Recommendation for E-commerce

**Group:** {GROUP}

**Patterns implemented:** Microservices and CQRS

**Submission deadline:** {DETAILS["deadline"]}

| Sl. | BITS ID | Name | Contribution | Percentage |
|---:|---|---|---|---:|
{member_rows}

> Replace every `TO_FILL` value in `submission_details.json` and regenerate this
> notebook before portal upload.
"""
        ),
        new_markdown_cell(
            """
## 1. Problem statement and measurable goal

Given implicit user feedback (views, clicks, carts, and purchases), rank unseen
catalogue products for each shopper. The primary offline goal is Precision@5;
supporting goals are Recall@5, Hit Rate@5, catalogue coverage, and a low-latency
read path.

This notebook executes the complete ML lifecycle: loading, schema validation,
deduplication, action weighting, matrix construction, leakage-safe evaluation,
item-item cosine-similarity training, artifact persistence, and inference.
"""
        ),
        new_markdown_cell(
            """
## 2. Requirements engineering and goal alignment

Traditional software is usually deterministic, whereas an ML system is
probabilistic and depends on learned data patterns. Our requirements therefore
cover data quality and availability, behavior under uncertainty, reproducible
training, model updates, and continuous evaluation.

| Goal level | Goal in this application | Measure |
|---|---|---|
| Organizational | Increase revenue per shopping session | CTR uplift and average order value |
| Product | Show a useful personalized product block | Usage and response latency |
| User | Find interesting products quickly | Top-5 hit rate and user feedback |
| Model | Rank relevant unseen products | Precision@5, Recall@5, Coverage@5 |

The offline targets are Precision@5 >= 0.30, Recall@5 >= 0.70, and
Coverage@5 >= 0.80. The production targets are p95 serving latency below
200 ms and CTR uplift of at least 8%; these require load and A/B testing.
"""
        ),
        new_code_cell(
            """
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt

from ecom_ml.ml.data import (
    ACTION_WEIGHTS,
    generate_demo_interactions,
    load_interactions,
    prepare_interactions,
)
from ecom_ml.ml.pipeline import train_pipeline
from ecom_ml.ml.artifact import load_artifact

ROOT = Path.cwd()
DATA = ROOT / "data" / "interactions.csv"
ARTIFACTS = ROOT / "artifacts"

if not DATA.exists():
    generate_demo_interactions(DATA)

rows = load_interactions(DATA)
prepared = prepare_interactions(rows)
print("Action weights:", ACTION_WEIGHTS)
print("Raw events:", prepared.raw_event_count)
print("Unique events:", prepared.unique_event_count)
print("Users x items:", prepared.matrix.shape)
print("Matrix density:", round(np.count_nonzero(prepared.matrix) / prepared.matrix.size, 4))
"""
        ),
        new_markdown_cell(
            source_block("backend/src/ecom_ml/ml/data.py", "ML code: loading and preprocessing")
        ),
        new_code_cell(
            """
summary = train_pipeline(DATA, ARTIFACTS, k=5, holdout_per_user=2)
print(json.dumps(summary.as_dict(), indent=2))
"""
        ),
        new_markdown_cell(
            source_block("backend/src/ecom_ml/ml/model.py", "ML code: model training and inference")
        ),
        new_markdown_cell(
            source_block(
                "backend/src/ecom_ml/ml/evaluation.py",
                "ML code: leakage-safe evaluation",
            )
        ),
        new_code_cell(
            """
model, metadata = load_artifact(ARTIFACTS)
recommendations = model.recommend("u007", k=5)
print("Loaded model:", metadata["version"])
print("Top-5 recommendations for u007:")
for rank, recommendation in enumerate(recommendations, start=1):
    print(f"{rank}. {recommendation.item_id}  score={recommendation.score:.4f}")
"""
        ),
        new_code_cell(
            """
metrics = metadata["metrics"]
metric_names = ["precision_at_k", "recall_at_k", "hit_rate_at_k", "catalogue_coverage_at_k"]
labels = ["Precision@5", "Recall@5", "Hit Rate@5", "Coverage@5"]
values = [metrics[name] for name in metric_names]

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
axes[0].imshow(prepared.matrix[:25], aspect="auto", cmap="YlGnBu")
axes[0].set_title("Prepared user-item interaction matrix")
axes[0].set_xlabel("Products")
axes[0].set_ylabel("First 25 users")
bars = axes[1].bar(labels, values, color=["#2563EB", "#0F766E", "#7C3AED", "#D97706"])
axes[1].set_ylim(0, 1)
axes[1].set_title("Leakage-safe offline evaluation")
axes[1].tick_params(axis="x", rotation=18)
for bar, value in zip(bars, values, strict=True):
    axes[1].text(bar.get_x() + bar.get_width()/2, value + 0.02, f"{value:.3f}", ha="center")
plt.show()
"""
        ),
        new_markdown_cell(
            """
## 3. Architectural patterns

### Pattern 1 - Microservices

The Command Service and Query Service are separate FastAPI applications with
independent ports and deployment commands. Training/write workloads can scale
separately from latency-sensitive recommendation reads.

### Pattern 2 - CQRS

- **Commands:** `POST /commands/interactions` and `POST /commands/train`
- **Queries:** `GET /queries/recommendations` and `GET /queries/model-info`

The write side produces an immutable, versioned model artifact. The read side
never modifies training data and reloads the artifact when its version changes.
"""
        ),
        new_markdown_cell(
            source_block(
                "backend/src/ecom_ml/command_service/main.py",
                "Pattern code: CQRS command/write microservice",
            )
        ),
        new_markdown_cell(
            source_block(
                "backend/src/ecom_ml/query_service/main.py",
                "Pattern code: CQRS query/read microservice",
            )
        ),
        new_markdown_cell(
            """
## 4. GR4ML views and cross-view traceability

The diagrams follow the notation taught in Session 3:

- **Business View:** stick-figure Actor, oval Business Goal, D-marked Decision
  Goal, Q-marked Question Goal, traffic-light Indicator, and structured Insight.
- **Analytics Design View:** oval Analytics Goal, hexagonal Algorithm,
  cloud-shaped Softgoal, traffic-light Indicator, and the Performs, Evaluates,
  Generates, Association, and Influence links.
- **Data Preparation View:** structured Entity, rectangular Operator,
  folded-corner Note, solid Data Flow, dashed Input/Output, and Relationship.

The trace across the views is:

`Prepared User-Item Matrix` **is required for** the Prediction and Ranking
Analytics Goal -> the goal **generates** the Top-5 Recommendation Insight ->
the insight **answers** the Question Goal -> the answer supports the product
Decision Goal -> the decision contributes to the revenue Business Goal.
"""
        ),
        new_code_cell(
            """
from IPython.display import Image, display

visuals = [
    ("GR4ML Business View", ROOT / "evidence" / "gr4ml_business_view.png"),
    ("GR4ML Analytics Design View", ROOT / "evidence" / "gr4ml_analytics_design_view.png"),
    ("GR4ML Data Preparation View", ROOT / "evidence" / "gr4ml_data_preparation_view.png"),
    ("System Architecture", ROOT / "evidence" / "system_architecture.png"),
    ("Executed application evidence", ROOT / "evidence" / "live_execution.png"),
]
for title, path in visuals:
    print(title)
    if path.exists():
        display(Image(filename=str(path)))
    else:
        print("Generate with: python tools/generate_assets.py")
"""
        ),
        new_markdown_cell(
            """
## 5. Result

The execution above proves that the dataset was prepared, the model was
trained and evaluated, a versioned artifact was saved and loaded, and unseen
items were ranked for a real user. The attached report provides the complete
requirements formulation, three GR4ML views, quality requirements, architecture
justification, screenshots, limitations, and references.
"""
        ),
    ]

    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
        },
    )
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    kernel_root = ROOT / "tmp" / "jupyter"
    kernel_name = "seml-ecommerce-reco"
    kernel_dir = kernel_root / "kernels" / kernel_name
    kernel_dir.mkdir(parents=True, exist_ok=True)
    (kernel_dir / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [
                    sys.executable,
                    "-m",
                    "ipykernel_launcher",
                    "-f",
                    "{connection_file}",
                ],
                "display_name": "SEML E-commerce Recommendation",
                "language": "python",
            }
        ),
        encoding="utf-8",
    )
    old_jupyter_path = os.environ.get("JUPYTER_PATH")
    os.environ["JUPYTER_PATH"] = str(kernel_root)
    try:
        client = NotebookClient(
            notebook,
            timeout=180,
            kernel_name=kernel_name,
            resources={"metadata": {"path": str(ROOT)}},
        )
        client.execute()
    finally:
        if old_jupyter_path is None:
            os.environ.pop("JUPYTER_PATH", None)
        else:
            os.environ["JUPYTER_PATH"] = old_jupyter_path

    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nbformat.write(notebook, OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_notebook())
