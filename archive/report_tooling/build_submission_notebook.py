"""Build the notebook deliverable required by the assignment brief.

The group number is not known yet, so the generated notebook is named
``GXXX.ipynb``. Rename it to the actual group number before final upload.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FINAL_DIR = ROOT.parent / "final_submission"
NOTEBOOK_PATH = FINAL_DIR / "GXXX.ipynb"


def markdown_cell(source: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": source.strip() + "\n"}


def code_cell(source: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip() + "\n",
    }


def build_notebook() -> Path:
    FINAL_DIR.mkdir(exist_ok=True)

    cells = [
        markdown_cell(
            """
            # AIMLCZG546 - Software Engineering for Machine Learning
            ## Assignment I: Real-Time Product Recommendation for an E-commerce Platform

            **Domain:** E-commerce / Retail  
            **Architectural patterns:** Event-Driven Architecture and API Gateway  
            **Group No:** GXXX - replace with actual group number before submission

            | Sl. | BITS ID | Name | Contribution | % |
            |---|---|---|---|---|
            | 1 | To fill | To fill | Requirements Lead | 25 |
            | 2 | To fill | To fill | GR4ML Modelling Lead | 25 |
            | 3 | To fill | To fill | Architecture Lead | 25 |
            | 4 | To fill | To fill | Implementation Lead | 25 |
            """
        ),
        markdown_cell(
            """
            ## Assignment Coverage

            This notebook accompanies the PDF/DOCX report and demonstrates the runnable implementation:

            - Problem: rank catalogue products for a user and return a personalised top-N list.
            - GR4ML views: Business View, Analytics Design View, and Data Preparation View.
            - Architecture: ML and non-ML components shown separately.
            - Patterns implemented: Event-Driven Architecture and API Gateway.
            - Evidence: metrics, screenshots, run output, and recommendation plot.
            """
        ),
        code_cell(
            """
            from pathlib import Path
            import sys

            # This notebook may be opened from final_submission/ or from the project folder.
            cwd = Path.cwd()
            project_dir = cwd if (cwd / "recommender_engine.py").exists() else cwd.parent / "seml-ecommerce-reco"
            sys.path.insert(0, str(project_dir))
            print("Project folder:", project_dir)
            """
        ),
        markdown_cell(
            """
            ## Run the Recommendation Logic

            The recommender uses implicit feedback. Each user action is converted to a weight:

            - view = 1
            - click = 2
            - cart = 3
            - purchase = 5

            The engine builds a user-item matrix, computes item-item cosine similarity, filters already-seen
            products, and returns the top ranked unseen products.
            """
        ),
        code_cell(
            """
            import recommender_engine

            recommender_engine.reset()
            recommender_engine.seed_demo_data()

            sample_events = [
                {"user_id": "u7", "item_id": "P03", "action": "click"},
                {"user_id": "u7", "item_id": "P04", "action": "cart"},
                {"user_id": "u7", "item_id": "P12", "action": "purchase"},
            ]

            for event in sample_events:
                print(recommender_engine.track_event(**event))

            recommendations = recommender_engine.rank_items("u7", 5)
            recommendations
            """
        ),
        markdown_cell(
            """
            ## Offline Evaluation

            The prototype uses a deterministic synthetic interaction matrix so the demo can be rerun locally.
            A small leave-three-out test estimates Precision@5 for the top-N recommender.
            """
        ),
        code_cell(
            """
            metrics = recommender_engine.evaluate_precision_at_k(k=5, holdout_per_user=3)
            stats = recommender_engine.stats()
            print("Stats:", stats)
            print("Offline metric:", metrics)
            """
        ),
        markdown_cell(
            """
            ## Generate Evidence Files

            Run this cell to regenerate the metric JSON, console output, and recommendation plot used in the report.
            """
        ),
        code_cell(
            """
            import subprocess

            subprocess.run([sys.executable, str(project_dir / "report_evidence.py")], cwd=project_dir, check=True)
            print("Evidence regenerated under:", project_dir / "evidence")
            """
        ),
        markdown_cell(
            """
            ## Display GR4ML and Architecture Diagrams
            """
        ),
        code_cell(
            """
            from IPython.display import Image, display

            for image_name in [
                "gr4ml_business_view.png",
                "gr4ml_analytics_design_view.png",
                "gr4ml_data_preparation_view.png",
                "system_architecture.png",
                "recommendation_output_plot.png",
            ]:
                image_path = project_dir / "evidence" / image_name
                if image_path.exists():
                    print(image_name)
                    display(Image(filename=str(image_path)))
            """
        ),
        markdown_cell(
            """
            ## API Gateway and Event-Driven Implementation

            The API implementation is in the source files below:

            - `recommendation_api.py`: internal recommendation service, queue, and background event consumer.
            - `api_gateway.py`: public gateway with token validation, rate limiting, and request routing.
            - `demo_requests.py`: sends events and recommendation requests through the gateway.
            - `quick_test.py`: starts both services, runs the demo, saves evidence, and stops services.
            """
        ),
        code_cell(
            """
            # Optional full smoke test. This starts local services temporarily and then stops them.
            # Uncomment the next line when running the notebook locally.
            # subprocess.run([sys.executable, str(project_dir / "quick_test.py")], cwd=project_dir, check=True)
            """
        ),
        markdown_cell(
            """
            ## Final Submission Notes

            Before upload:

            - Rename `GXXX.ipynb` to your actual group number if the portal requires `<Group no>.ipynb`.
            - Fill group number, BITS IDs, names, and final contribution percentages in the PDF/DOCX and this notebook.
            - Submit the final PDF or DOCX plus the notebook/code package according to the portal instructions.
            """
        ),
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    return NOTEBOOK_PATH


if __name__ == "__main__":
    print(build_notebook())
