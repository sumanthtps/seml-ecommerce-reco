"""Generate the diagrams and metrics figure used in the submission."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from ecom_ml.ml.artifact import load_artifact
from ecom_ml.ml.data import load_interactions, prepare_interactions

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
DATA = ROOT / "data" / "interactions.csv"
ARTIFACTS = ROOT / "artifacts"

NAVY = "#16324F"
BLUE = "#2563EB"
TEAL = "#0F766E"
AMBER = "#D97706"
PURPLE = "#7C3AED"
SLATE = "#475569"
LIGHT_BLUE = "#E8F0FE"
LIGHT_TEAL = "#E6F5F2"
LIGHT_AMBER = "#FFF4DD"
LIGHT_PURPLE = "#F0EAFE"
LIGHT_GRAY = "#F8FAFC"


def add_rectangle(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    face: str = LIGHT_BLUE,
    edge: str = BLUE,
    fontsize: float = 9.5,
) -> None:
    """GR4ML component/artifact notation: rectangle."""
    width, height = size
    x, y = center
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.008",
        facecolor=face,
        edgecolor=edge,
        linewidth=1.7,
    )
    axis.add_patch(patch)
    axis.text(x, y, text, ha="center", va="center", fontsize=fontsize, color=NAVY)


def add_activity(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    face: str = LIGHT_TEAL,
    edge: str = TEAL,
    fontsize: float = 9.5,
) -> None:
    """GR4ML activity/task notation: ellipse."""
    patch = Ellipse(
        center,
        width=size[0],
        height=size[1],
        facecolor=face,
        edgecolor=edge,
        linewidth=1.7,
    )
    axis.add_patch(patch)
    axis.text(center[0], center[1], text, ha="center", va="center", fontsize=fontsize, color=NAVY)


def add_arrow(
    axis: Any,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    label: str | None = None,
    color: str = SLATE,
    curve: float = 0.0,
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.25,
        color=color,
        connectionstyle=f"arc3,rad={curve}",
        shrinkA=4,
        shrinkB=4,
    )
    axis.add_patch(arrow)
    if label:
        x = (start[0] + end[0]) / 2
        y = (start[1] + end[1]) / 2 + 0.035
        axis.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=8,
            color=color,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 1.5},
        )


def finish_diagram(
    figure: Any,
    axis: Any,
    filename: str,
    title: str,
    *,
    legend: bool = True,
) -> None:
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    if title:
        axis.set_title(title, fontsize=15, fontweight="bold", color=NAVY, pad=18)
    if legend:
        add_activity(axis, (0.72, 0.045), (0.12, 0.055), "Activity / task", fontsize=7.5)
        add_rectangle(
            axis,
            (0.89, 0.045),
            (0.17, 0.055),
            "Goal / data / component / artifact",
            fontsize=6.7,
        )
        axis.text(0.61, 0.045, "GR4ML legend:", ha="right", va="center", fontsize=8, color=SLATE)
    figure.savefig(EVIDENCE / filename, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def add_notation(axis: Any, text: str) -> None:
    axis.text(
        0.50,
        0.11,
        f"Notation: {text}",
        ha="center",
        va="center",
        fontsize=8.2,
        color=SLATE,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": LIGHT_GRAY,
            "edgecolor": "#CBD5E1",
        },
    )


def add_goal(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    badge: str | None = None,
    badge_fontsize: float = 9,
    fontsize: float = 9.5,
) -> None:
    patch = Ellipse(center, size[0], size[1], facecolor="white", edgecolor="black", linewidth=1.4)
    axis.add_patch(patch)
    if badge:
        badge_center = (
            center[0] - size[0] / 2 + 0.018,
            center[1] + size[1] / 2 - 0.018,
        )
        axis.add_patch(
            Circle(
                badge_center,
                0.016,
                facecolor=LIGHT_BLUE,
                edgecolor=NAVY,
                linewidth=1.0,
                zorder=3,
            )
        )
        axis.text(
            badge_center[0],
            badge_center[1],
            badge,
            ha="center",
            va="center",
            fontsize=badge_fontsize,
            fontweight="bold",
            color=NAVY,
            zorder=4,
        )
    axis.text(center[0], center[1], text, ha="center", va="center", fontsize=fontsize)


def add_actor(axis: Any, center: tuple[float, float], label: str, *, scale: float = 1.0) -> None:
    x, y = center
    radius = 0.013 * scale
    axis.add_patch(Circle((x, y + 0.055 * scale), radius, facecolor="white", edgecolor="black"))
    axis.plot([x, x], [y + 0.042 * scale, y - 0.025 * scale], color="black", linewidth=1.2)
    axis.plot(
        [x - 0.035 * scale, x + 0.035 * scale],
        [y + 0.018 * scale, y + 0.018 * scale],
        color="black",
        linewidth=1.2,
    )
    axis.plot(
        [x, x - 0.028 * scale],
        [y - 0.025 * scale, y - 0.075 * scale],
        color="black",
        linewidth=1.2,
    )
    axis.plot(
        [x, x + 0.028 * scale],
        [y - 0.025 * scale, y - 0.075 * scale],
        color="black",
        linewidth=1.2,
    )
    axis.text(x, y - 0.105 * scale, label, ha="center", va="top", fontsize=8.5)


def add_indicator(
    axis: Any,
    center: tuple[float, float],
    label: str,
    *,
    label_side: str = "right",
    scale: float = 1.0,
) -> None:
    x, y = center
    width = 0.022 * scale
    height = 0.075 * scale
    cell_height = height / 3
    colors = ["#9AD14B", "#FFF200", "#ED1C24"]
    for index, color in enumerate(colors):
        lower_y = y + height / 2 - (index + 1) * cell_height
        axis.add_patch(
            Rectangle(
                (x - width / 2, lower_y),
                width,
                cell_height,
                facecolor=color,
                edgecolor="black",
                linewidth=0.7,
            )
        )
    offset = 0.025 if label_side == "right" else -0.025
    alignment = "left" if label_side == "right" else "right"
    axis.text(x + offset, y, label, ha=alignment, va="center", fontsize=8.3)


def add_structured_box(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    title: str,
    attributes: list[str],
    *,
    fontsize: float = 7.7,
) -> None:
    x, y = center
    width, height = size
    left = x - width / 2
    bottom = y - height / 2
    axis.add_patch(
        Rectangle(
            (left, bottom),
            width,
            height,
            facecolor="white",
            edgecolor="black",
            linewidth=1.2,
        )
    )
    title_height = min(0.055, height * 0.25)
    axis.plot(
        [left, left + width],
        [bottom + height - title_height, bottom + height - title_height],
        color="black",
        linewidth=1,
    )
    axis.text(
        x,
        bottom + height - title_height / 2,
        title,
        ha="center",
        va="center",
        fontsize=fontsize + 0.8,
        fontweight="bold",
    )
    attr_text = "\n".join(attributes)
    axis.text(
        left + 0.012,
        bottom + height - title_height - 0.012,
        attr_text,
        ha="left",
        va="top",
        fontsize=fontsize,
        linespacing=1.25,
    )


def add_algorithm(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    fontsize: float = 8.4,
) -> None:
    x, y = center
    width, height = size
    inset = width * 0.15
    vertices = [
        (x - width / 2 + inset, y - height / 2),
        (x + width / 2 - inset, y - height / 2),
        (x + width / 2, y),
        (x + width / 2 - inset, y + height / 2),
        (x - width / 2 + inset, y + height / 2),
        (x - width / 2, y),
    ]
    axis.add_patch(
        Polygon(vertices, closed=True, facecolor="white", edgecolor="black", linewidth=1.2)
    )
    axis.text(x, y, text, ha="center", va="center", fontsize=fontsize)


def add_softgoal(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    fontsize: float = 8.2,
) -> None:
    angles = np.linspace(0, 2 * np.pi, 220)
    ripple = 1 + 0.10 * np.cos(9 * angles)
    x_values = center[0] + size[0] / 2 * ripple * np.cos(angles)
    y_values = center[1] + size[1] / 2 * ripple * np.sin(angles)
    vertices = np.column_stack([x_values, y_values])
    axis.add_patch(
        Polygon(vertices, closed=True, facecolor="white", edgecolor="black", linewidth=1.2)
    )
    axis.text(center[0], center[1], text, ha="center", va="center", fontsize=fontsize)


def add_note(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    fontsize: float = 7.5,
) -> None:
    x, y = center
    width, height = size
    fold = min(width, height) * 0.15
    left, right = x - width / 2, x + width / 2
    bottom, top = y - height / 2, y + height / 2
    vertices = [
        (left, bottom),
        (right - fold, bottom),
        (right, bottom + fold),
        (right, top),
        (left, top),
    ]
    axis.add_patch(
        Polygon(vertices, closed=True, facecolor="#F2F2F2", edgecolor="black", linewidth=1)
    )
    axis.plot(
        [right - fold, right - fold, right],
        [bottom, bottom + fold, bottom + fold],
        color="black",
        linewidth=0.8,
    )
    axis.text(x - width * 0.04, y, text, ha="center", va="center", fontsize=fontsize)


def add_operator(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    fontsize: float = 8.3,
) -> None:
    x, y = center
    width, height = size
    axis.add_patch(
        Rectangle(
            (x - width / 2, y - height / 2),
            width,
            height,
            facecolor="white",
            edgecolor="black",
            linewidth=1.2,
        )
    )
    axis.text(x, y, text, ha="center", va="center", fontsize=fontsize)


def add_link(
    axis: Any,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    label: str | None = None,
    dashed: bool = False,
    arrowstyle: str = "-",
    label_offset: tuple[float, float] = (0.0, 0.018),
    linewidth: float = 1.1,
) -> None:
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=arrowstyle,
        mutation_scale=13,
        linewidth=linewidth,
        linestyle="--" if dashed else "-",
        color="black",
        shrinkA=2,
        shrinkB=2,
    )
    axis.add_patch(patch)
    if label:
        axis.text(
            (start[0] + end[0]) / 2 + label_offset[0],
            (start[1] + end[1]) / 2 + label_offset[1],
            label,
            ha="center",
            va="center",
            fontsize=7.8,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.8},
        )


def add_polyline_link(
    axis: Any,
    points: list[tuple[float, float]],
    *,
    dashed: bool = False,
    arrowstyle: str = "-|>",
    linewidth: float = 1.1,
    color: str = "black",
) -> None:
    """Draw a routed connector so relationships can avoid model elements."""
    linestyle = "--" if dashed else "-"
    if len(points) > 2:
        axis.plot(
            [point[0] for point in points[:-1]],
            [point[1] for point in points[:-1]],
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
        )
    patch = FancyArrowPatch(
        points[-2],
        points[-1],
        arrowstyle=arrowstyle,
        mutation_scale=13,
        linewidth=linewidth,
        linestyle=linestyle,
        color=color,
        shrinkA=0,
        shrinkB=2,
    )
    axis.add_patch(patch)


def add_evaluates_hashes(axis: Any, center: tuple[float, float], *, rotation: float = 0.0) -> None:
    axis.text(
        center[0],
        center[1],
        "|||",
        ha="center",
        va="center",
        fontsize=9,
        rotation=rotation,
        fontweight="bold",
    )


def business_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 6.8))
    add_actor(axis, (0.08, 0.60), "Storefront\nmanager", scale=0.95)
    add_goal(axis, (0.29, 0.66), (0.23, 0.14), "Increase revenue\nper session", fontsize=10)
    add_goal(
        axis,
        (0.54, 0.66),
        (0.20, 0.14),
        "Choose products\nto display",
        badge="D",
        fontsize=9.5,
    )
    add_goal(
        axis,
        (0.80, 0.66),
        (0.24, 0.15),
        "Which unseen products\nwill this user engage with?",
        badge="Q",
        fontsize=8.8,
    )
    add_indicator(
        axis,
        (0.29, 0.38),
        "CTR uplift and\naverage order value",
        label_side="right",
        scale=0.95,
    )
    add_structured_box(
        axis,
        (0.80, 0.35),
        (0.30, 0.19),
        "Top-5 Recommendation Insight",
        [
            "Type: predictive ranking",
            "Input: user profile + item similarity",
            "Output: five ranked unseen products",
            "Updated after model training",
        ],
        fontsize=7.4,
    )
    add_link(axis, (0.12, 0.62), (0.16, 0.65), label="desires", arrowstyle="->")
    add_link(axis, (0.405, 0.66), (0.44, 0.66), arrowstyle="->")
    axis.text(0.422, 0.76, "refined into", ha="center", fontsize=7.8, color=SLATE)
    add_link(axis, (0.64, 0.66), (0.68, 0.66), arrowstyle="->")
    axis.text(0.66, 0.76, "requires an answer", ha="center", fontsize=7.8, color=SLATE)
    add_link(axis, (0.80, 0.45), (0.80, 0.585), label="answers", dashed=True, arrowstyle="->")
    add_link(axis, (0.31, 0.43), (0.30, 0.59))
    add_evaluates_hashes(axis, (0.305, 0.50), rotation=84)
    axis.text(0.34, 0.50, "evaluates", fontsize=7.8, color=SLATE)
    add_notation(
        axis,
        "actor | oval = goal | D = decision goal | Q = question goal | "
        "traffic light = indicator | structured box = insight",
    )
    finish_diagram(
        figure,
        axis,
        "gr4ml_business_view.png",
        "GR4ML Business View - From Business Goal to Recommendation Insight",
        legend=False,
    )


def analytics_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 6.8))
    add_goal(
        axis,
        (0.48, 0.72),
        (0.32, 0.14),
        "Predict and rank unseen\ncatalogue products",
        fontsize=10,
    )
    add_indicator(axis, (0.17, 0.78), "Precision@5", scale=0.85)
    add_indicator(axis, (0.80, 0.78), "Coverage@5", scale=0.85)
    add_algorithm(axis, (0.25, 0.40), (0.20, 0.12), "Item-based\nCollaborative Filtering")
    add_algorithm(axis, (0.48, 0.40), (0.18, 0.12), "Matrix\nFactorization")
    add_algorithm(axis, (0.69, 0.40), (0.17, 0.12), "Popularity\nBaseline")
    axis.text(
        0.25,
        0.31,
        "selected for the prototype",
        ha="center",
        fontsize=7.8,
        color=TEAL,
        fontweight="bold",
    )
    add_softgoal(axis, (0.85, 0.62), (0.17, 0.09), "Recommendation\nrelevance")
    add_softgoal(axis, (0.85, 0.47), (0.17, 0.09), "Low latency")
    add_softgoal(axis, (0.85, 0.32), (0.17, 0.09), "Interpretability")
    for start in [(0.25, 0.46), (0.48, 0.46), (0.69, 0.46)]:
        add_link(axis, start, (0.48, 0.65), arrowstyle="-|>")
    axis.text(0.45, 0.54, "performs", fontsize=7.8, color=SLATE)
    add_link(axis, (0.34, 0.75), (0.19, 0.78))
    add_evaluates_hashes(axis, (0.26, 0.76), rotation=-8)
    add_link(axis, (0.64, 0.75), (0.78, 0.78))
    add_evaluates_hashes(axis, (0.71, 0.76), rotation=8)
    add_link(axis, (0.63, 0.71), (0.76, 0.63))
    add_link(axis, (0.63, 0.68), (0.76, 0.49))
    add_link(axis, (0.30, 0.35), (0.77, 0.33), dashed=True, arrowstyle="-|>")
    axis.text(0.55, 0.32, "+ supports", fontsize=7.5, color=TEAL)
    add_link(
        axis,
        (0.32, 0.72),
        (0.235, 0.61),
        dashed=True,
        arrowstyle="->",
    )
    axis.text(0.27, 0.68, "generates", ha="center", fontsize=7.8, color=SLATE)
    add_structured_box(
        axis,
        (0.14, 0.57),
        (0.19, 0.10),
        "Top-5 Recommendation",
        ["ranked unseen products"],
        fontsize=6.8,
    )
    add_notation(
        axis,
        "oval = analytics goal | hexagon = algorithm | cloud = softgoal | "
        "traffic light = indicator | dashed arrow = influence/generates",
    )
    finish_diagram(
        figure,
        axis,
        "gr4ml_analytics_design_view.png",
        "GR4ML Analytics Design View - Algorithm Choice and Quality Trade-offs",
        legend=False,
    )


def data_preparation_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 6.8))
    add_structured_box(
        axis,
        (0.13, 0.60),
        (0.20, 0.31),
        "Interaction Event",
        [
            "event_id (PK)",
            "timestamp",
            "user_id",
            "item_id",
            "action",
        ],
        fontsize=7.7,
    )
    add_structured_box(
        axis,
        (0.35, 0.31),
        (0.18, 0.19),
        "Product Catalogue",
        ["item_id (PK)", "product name", "category"],
        fontsize=7.5,
    )
    add_operator(
        axis,
        (0.35, 0.63),
        (0.16, 0.11),
        "Validate and\nDeduplicate",
        fontsize=8.5,
    )
    add_operator(
        axis,
        (0.54, 0.63),
        (0.15, 0.11),
        "Apply Action\nWeights",
        fontsize=8.5,
    )
    add_operator(
        axis,
        (0.72, 0.63),
        (0.16, 0.11),
        "Aggregate by\nUser and Item",
        fontsize=8.5,
    )
    add_structured_box(
        axis,
        (0.87, 0.39),
        (0.21, 0.28),
        "Prepared User-Item Matrix",
        [
            "user_id (PK)",
            "P001 ... P060",
            "weighted interaction values",
            "training input",
        ],
        fontsize=7.3,
    )
    add_note(
        axis,
        (0.54, 0.42),
        (0.15, 0.11),
        "view=1, click=2\ncart=3, purchase=5",
        fontsize=7.3,
    )
    add_link(axis, (0.23, 0.63), (0.27, 0.63), label="input", dashed=True)
    add_link(axis, (0.43, 0.63), (0.465, 0.63), arrowstyle="->")
    add_link(axis, (0.615, 0.63), (0.64, 0.63), arrowstyle="->")
    add_link(axis, (0.80, 0.61), (0.80, 0.535), label="output", dashed=True, arrowstyle="->")
    add_polyline_link(
        axis,
        [(0.44, 0.31), (0.64, 0.31), (0.68, 0.57)],
        dashed=True,
        arrowstyle="->",
        color=SLATE,
    )
    axis.text(0.59, 0.29, "catalogue input", fontsize=7.6, color=SLATE, ha="center")
    add_link(axis, (0.54, 0.47), (0.54, 0.57), arrowstyle="-")
    axis.text(
        0.87,
        0.20,
        "used for model training\nand recommendation ranking",
        ha="center",
        fontsize=8,
        color=SLATE,
    )
    add_notation(
        axis,
        "structured box = entity | rectangle = operator | folded box = note | "
        "solid arrow = data flow | dashed arrow = input/output",
    )
    finish_diagram(
        figure,
        axis,
        "gr4ml_data_preparation_view.png",
        "GR4ML Data Preparation View - From Raw Events to the Training Matrix",
        legend=False,
    )


def architecture_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 6.8))
    axis.text(0.035, 0.82, "PRESENTATION", fontsize=8, fontweight="bold", color=SLATE)
    axis.text(0.035, 0.57, "SERVICES", fontsize=8, fontweight="bold", color=SLATE)
    axis.text(0.035, 0.25, "DATA + ML", fontsize=8, fontweight="bold", color=SLATE)
    axis.plot([0.03, 0.97], [0.74, 0.74], color="#E2E8F0", linewidth=1)
    axis.plot([0.03, 0.97], [0.43, 0.43], color="#E2E8F0", linewidth=1)
    add_rectangle(
        axis,
        (0.50, 0.84),
        (0.34, 0.14),
        "STREAMLIT UI :8501\n\nRecommend  •  Record interaction  •  Users  •  Train",
        face="#FEECEC",
        edge="#B91C1C",
        fontsize=8.8,
    )
    add_rectangle(
        axis,
        (0.29, 0.57),
        (0.34, 0.22),
        "COMMAND SERVICE :8101\n\n"
        "Create user  •  Record interaction  •  Train model\n"
        "Owns state-changing operations",
        face=LIGHT_BLUE,
        edge=BLUE,
        fontsize=8.5,
    )
    add_rectangle(
        axis,
        (0.71, 0.57),
        (0.34, 0.22),
        "QUERY SERVICE :8102\n\n"
        "Recommendations  •  Users  •  Products\n"
        "Recent actions  •  Model information",
        face=LIGHT_TEAL,
        edge=TEAL,
        fontsize=8.5,
    )
    add_rectangle(
        axis,
        (0.50, 0.37),
        (0.20, 0.12),
        "User profile store\nnames + interests",
        face=LIGHT_AMBER,
        edge=AMBER,
        fontsize=8,
    )
    add_rectangle(axis, (0.18, 0.20), (0.20, 0.11), "Interaction event log\nCSV write store")
    add_activity(axis, (0.43, 0.20), (0.18, 0.11), "ML training\npipeline")
    add_rectangle(
        axis,
        (0.71, 0.20),
        (0.20, 0.12),
        "Versioned model artifact\nNPZ + JSON metadata",
        face=LIGHT_PURPLE,
        edge=PURPLE,
    )

    add_arrow(axis, (0.44, 0.77), (0.34, 0.68), label="commands")
    add_arrow(axis, (0.56, 0.77), (0.66, 0.68), label="queries + results")
    add_arrow(axis, (0.34, 0.46), (0.44, 0.40), label="create/update")
    add_arrow(axis, (0.66, 0.46), (0.56, 0.40), label="read interest")
    add_arrow(axis, (0.23, 0.46), (0.18, 0.26), label="append")
    add_arrow(axis, (0.28, 0.20), (0.34, 0.20), label="load")
    add_arrow(axis, (0.52, 0.20), (0.61, 0.20), label="publish")
    add_arrow(axis, (0.71, 0.26), (0.71, 0.46), label="reload")
    axis.text(
        0.50,
        0.06,
        "Microservices separate deployment and scaling. CQRS keeps writes and training away from "
        "the latency-sensitive read path.",
        ha="center",
        va="center",
        fontsize=8.5,
        color=NAVY,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": LIGHT_GRAY, "edgecolor": "#CBD5E1"},
    )
    finish_diagram(
        figure,
        axis,
        "system_architecture.png",
        "System Architecture - Streamlit, CQRS Services, and the ML Lifecycle",
        legend=False,
    )


def metric_plot() -> None:
    model, metadata = load_artifact(ARTIFACTS)
    prepared = prepare_interactions(load_interactions(DATA))
    metrics = metadata["metrics"]
    names = ["precision_at_k", "recall_at_k", "hit_rate_at_k", "catalogue_coverage_at_k"]
    labels = ["Precision@5", "Recall@5", "Hit Rate@5", "Coverage@5"]
    values = [metrics[name] for name in names]
    recommendations = model.recommend("u007", 5)

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(14, 4.8),
        gridspec_kw={"width_ratios": [1.2, 0.95, 0.95]},
        constrained_layout=True,
    )
    image = axes[0].imshow(prepared.matrix[:25], aspect="auto", cmap="YlGnBu")
    axes[0].set_title("Prepared interaction matrix")
    axes[0].set_xlabel("60 products")
    axes[0].set_ylabel(f"First 25 of {len(prepared.users)} users")
    figure.colorbar(image, ax=axes[0], fraction=0.047, pad=0.03)

    colors = [BLUE, TEAL, PURPLE, AMBER]
    bars = axes[1].bar(labels, values, color=colors)
    axes[1].set_ylim(0, 1.08)
    axes[1].set_title("Leakage-safe evaluation")
    axes[1].tick_params(axis="x", rotation=25, labelsize=8)
    for bar, value in zip(bars, values, strict=True):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 0.025, f"{value:.3f}", ha="center")

    rec_labels = [item.item_id for item in recommendations][::-1]
    scores = [item.score for item in recommendations][::-1]
    rec_bars = axes[2].barh(rec_labels, scores, color=BLUE)
    axes[2].set_title("Top-5 for user u007")
    axes[2].set_xlabel("Collaborative-filtering score")
    for bar, score in zip(rec_bars, scores, strict=True):
        axes[2].text(
            score + 0.15,
            bar.get_y() + bar.get_height() / 2,
            f"{score:.2f}",
            va="center",
            fontsize=8,
        )
    figure.suptitle(
        f"Executed ML evidence - model {model.version}, {metadata['training_events']} events",
        fontsize=14,
        fontweight="bold",
        color=NAVY,
    )
    figure.savefig(EVIDENCE / "ml_execution_metrics.png", dpi=220, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if not DATA.exists():
        raise FileNotFoundError("run python scripts/seed_data.py first")
    if not (EVIDENCE / "live_demo.json").exists():
        raise FileNotFoundError("run python scripts/verify_live.py first")

    business_view()
    analytics_view()
    data_preparation_view()
    architecture_view()
    metric_plot()
    print(f"Generated evidence under {EVIDENCE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
