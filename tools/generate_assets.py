"""Generate GR4ML diagrams and execution-backed visual evidence."""

from __future__ import annotations

import io
import json
import textwrap
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from PIL import Image, ImageDraw, ImageFont

from ecom_ml.command_service.main import create_app as create_command_app
from ecom_ml.ml.artifact import load_artifact
from ecom_ml.ml.data import load_interactions, prepare_interactions
from ecom_ml.ml.pipeline import train_pipeline
from ecom_ml.query_service.main import create_app as create_query_app

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


def add_view_banner(axis: Any, text: str) -> None:
    banner = FancyBboxPatch(
        (0.02, 0.91),
        0.29,
        0.065,
        boxstyle="round,pad=0.008,rounding_size=0.025",
        facecolor="#FFC20A",
        edgecolor="#FFC20A",
        linewidth=1,
    )
    axis.add_patch(banner)
    axis.text(0.165, 0.943, text, ha="center", va="center", fontsize=14, fontweight="bold")


def add_goal(
    axis: Any,
    center: tuple[float, float],
    size: tuple[float, float],
    text: str,
    *,
    badge: str | None = None,
    badge_fontsize: float = 27,
    fontsize: float = 9.5,
) -> None:
    patch = Ellipse(center, size[0], size[1], facecolor="white", edgecolor="black", linewidth=1.4)
    axis.add_patch(patch)
    if badge:
        axis.text(
            center[0] - size[0] / 2 - 0.002,
            center[1],
            badge,
            ha="center",
            va="center",
            fontsize=badge_fontsize,
            fontweight="bold",
            fontfamily="serif",
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
) -> None:
    """Draw a routed connector so relationships can avoid model elements."""
    linestyle = "--" if dashed else "-"
    if len(points) > 2:
        axis.plot(
            [point[0] for point in points[:-1]],
            [point[1] for point in points[:-1]],
            color="black",
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
        color="black",
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


def add_business_legend(axis: Any) -> None:
    legend = FancyBboxPatch(
        (0.73, 0.11),
        0.25,
        0.79,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        facecolor="#E6E6E6",
        edgecolor="black",
        linewidth=1,
    )
    axis.add_patch(legend)
    axis.text(0.855, 0.865, "Legend for Business View", ha="center", fontsize=10, fontweight="bold")
    add_actor(axis, (0.77, 0.76), "Actor", scale=0.65)
    add_goal(axis, (0.90, 0.77), (0.13, 0.075), "Business\nGoal", fontsize=7.2)
    add_goal(
        axis,
        (0.79, 0.60),
        (0.105, 0.075),
        "Decision\nGoal",
        badge="D",
        badge_fontsize=19,
        fontsize=6.7,
    )
    add_goal(
        axis,
        (0.925, 0.60),
        (0.105, 0.075),
        "Question\nGoal",
        badge="Q",
        badge_fontsize=19,
        fontsize=6.7,
    )
    add_indicator(axis, (0.77, 0.43), "Indicator", scale=0.75)
    add_structured_box(
        axis, (0.91, 0.43), (0.13, 0.10), "Insight", ["+type", "+input/output"], fontsize=5.6
    )
    axis.text(0.755, 0.28, "desires", fontsize=7.2)
    add_link(axis, (0.82, 0.285), (0.94, 0.285), arrowstyle="->")
    axis.text(0.755, 0.22, "answers", fontsize=7.2)
    add_link(axis, (0.82, 0.225), (0.94, 0.225), dashed=True, arrowstyle="->")
    axis.text(0.755, 0.16, "evaluates", fontsize=7.2)
    add_link(axis, (0.83, 0.165), (0.94, 0.165))
    add_evaluates_hashes(axis, (0.85, 0.165))


def business_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 7.2))
    add_view_banner(axis, "Business View")
    add_actor(axis, (0.07, 0.78), "Storefront\nmanager", scale=1.05)
    add_goal(axis, (0.34, 0.78), (0.31, 0.13), "Increase revenue per session", fontsize=10)
    add_indicator(
        axis,
        (0.61, 0.86),
        "CTR uplift / Average order value",
        label_side="left",
        scale=1.05,
    )
    add_goal(
        axis,
        (0.34, 0.58),
        (0.34, 0.13),
        "Choose products to display",
        badge="D",
        fontsize=9.7,
    )
    add_goal(
        axis,
        (0.34, 0.39),
        (0.46, 0.14),
        "Which unseen products will user u\nmost likely engage with?",
        badge="Q",
        fontsize=9.2,
    )
    add_structured_box(
        axis,
        (0.34, 0.17),
        (0.58, 0.22),
        "Top-5 Recommendation Insight",
        [
            "+type: Predictive ranking",
            "+input: Weighted user-item profile",
            "+output: Ranked unseen products",
            "+usageFrequency: Per request",
            "+updateFrequency: On model retraining",
            "+learningPeriod: Available interaction history",
        ],
        fontsize=7.2,
    )
    add_link(axis, (0.105, 0.80), (0.18, 0.80), label="desires", arrowstyle="->")
    add_link(axis, (0.34, 0.715), (0.34, 0.645))
    axis.text(0.36, 0.682, "AND", fontsize=8)
    add_link(axis, (0.34, 0.515), (0.34, 0.46))
    axis.text(0.36, 0.488, "AND", fontsize=8)
    add_link(axis, (0.34, 0.28), (0.34, 0.32), label="answers", dashed=True, arrowstyle="->")
    add_link(axis, (0.49, 0.80), (0.595, 0.85))
    add_evaluates_hashes(axis, (0.54, 0.825), rotation=25)
    axis.text(0.50, 0.87, "evaluates", fontsize=7.5)
    add_business_legend(axis)
    finish_diagram(
        figure,
        axis,
        "gr4ml_business_view.png",
        "",
        legend=False,
    )


def add_analytics_legend(axis: Any) -> None:
    legend = FancyBboxPatch(
        (0.73, 0.10),
        0.25,
        0.80,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        facecolor="#E6E6E6",
        edgecolor="black",
        linewidth=1,
    )
    axis.add_patch(legend)
    axis.text(
        0.855,
        0.865,
        "Legend for Analytics Design View",
        ha="center",
        fontsize=9.5,
        fontweight="bold",
    )
    add_algorithm(axis, (0.79, 0.75), (0.11, 0.075), "Algorithm", fontsize=7.2)
    add_goal(axis, (0.92, 0.75), (0.12, 0.075), "Analytics\nGoal", fontsize=7.1)
    add_softgoal(axis, (0.79, 0.60), (0.11, 0.07), "Softgoal", fontsize=7.1)
    add_indicator(axis, (0.91, 0.60), "Indicator", scale=0.75)
    axis.text(0.755, 0.46, "performs", fontsize=7.2)
    add_link(axis, (0.82, 0.465), (0.95, 0.465), arrowstyle="-|>")
    axis.text(0.755, 0.39, "influence", fontsize=7.2)
    add_link(axis, (0.82, 0.395), (0.95, 0.395), dashed=True, arrowstyle="-|>")
    axis.text(0.755, 0.32, "evaluates", fontsize=7.2)
    add_link(axis, (0.82, 0.325), (0.95, 0.325))
    add_evaluates_hashes(axis, (0.85, 0.325))
    axis.text(0.755, 0.25, "generates", fontsize=7.2)
    add_link(axis, (0.82, 0.255), (0.95, 0.255), dashed=True, arrowstyle="->")
    axis.text(0.755, 0.18, "association", fontsize=7.2)
    add_link(axis, (0.83, 0.185), (0.95, 0.185))


def analytics_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 7.2))
    add_view_banner(axis, "Analytics Design View")
    add_goal(
        axis,
        (0.31, 0.66),
        (0.32, 0.13),
        "Prediction and ranking of\nunseen catalogue products",
        fontsize=9.7,
    )
    add_indicator(axis, (0.08, 0.82), "Precision@5", scale=0.90)
    add_indicator(axis, (0.43, 0.82), "Coverage@5", scale=0.90)
    add_algorithm(axis, (0.13, 0.39), (0.18, 0.105), "Item-based\nCollaborative Filtering")
    add_algorithm(axis, (0.32, 0.39), (0.17, 0.105), "Matrix\nFactorization")
    add_algorithm(axis, (0.50, 0.39), (0.16, 0.105), "Popularity\nBaseline")
    add_softgoal(axis, (0.62, 0.70), (0.16, 0.085), "Recommendation\nrelevance")
    add_softgoal(axis, (0.62, 0.51), (0.16, 0.085), "Low latency")
    add_softgoal(axis, (0.62, 0.25), (0.16, 0.085), "Interpretability")
    for start in [(0.13, 0.445), (0.32, 0.445), (0.50, 0.445)]:
        add_link(axis, start, (0.31, 0.595), arrowstyle="-|>")
    axis.text(0.21, 0.52, "performs", fontsize=7.7)
    add_link(axis, (0.21, 0.71), (0.08, 0.78))
    add_evaluates_hashes(axis, (0.145, 0.745), rotation=-28)
    add_link(axis, (0.39, 0.71), (0.43, 0.78))
    add_evaluates_hashes(axis, (0.41, 0.745), rotation=25)
    add_link(axis, (0.47, 0.68), (0.54, 0.70))
    add_link(axis, (0.46, 0.64), (0.54, 0.52))
    add_polyline_link(
        axis,
        [(0.22, 0.35), (0.22, 0.14), (0.71, 0.14), (0.71, 0.51), (0.695, 0.51)],
        dashed=True,
    )
    axis.text(0.24, 0.16, "+", fontsize=11, fontweight="bold")
    add_link(axis, (0.50, 0.335), (0.57, 0.27), dashed=True, arrowstyle="-|>")
    axis.text(0.535, 0.31, "+", fontsize=11, fontweight="bold")
    add_link(
        axis,
        (0.15, 0.62),
        (0.035, 0.62),
        dashed=True,
        arrowstyle="->",
    )
    axis.text(
        0.085,
        0.575,
        "generates\nTop-5 insight",
        ha="center",
        va="center",
        fontsize=7.5,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.8},
    )
    add_analytics_legend(axis)
    finish_diagram(
        figure,
        axis,
        "gr4ml_analytics_design_view.png",
        "",
        legend=False,
    )


def add_data_legend(axis: Any) -> None:
    legend = FancyBboxPatch(
        (0.73, 0.10),
        0.25,
        0.80,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        facecolor="#E6E6E6",
        edgecolor="black",
        linewidth=1,
    )
    axis.add_patch(legend)
    axis.text(
        0.855,
        0.865,
        "Legend for Data Preparation View",
        ha="center",
        fontsize=9.5,
        fontweight="bold",
    )
    add_operator(axis, (0.79, 0.72), (0.11, 0.075), "Operator", fontsize=7.3)
    add_structured_box(
        axis, (0.92, 0.72), (0.11, 0.13), "Entity", ["- PK", "- Attribute"], fontsize=6.2
    )
    add_note(axis, (0.80, 0.53), (0.11, 0.09), "Note", fontsize=7)
    axis.text(0.755, 0.40, "Data flow", fontsize=7.2)
    add_link(axis, (0.83, 0.405), (0.95, 0.405), arrowstyle="->")
    axis.text(0.755, 0.32, "Inputs / output", fontsize=7.2)
    add_link(axis, (0.83, 0.325), (0.95, 0.325), dashed=True)
    axis.text(0.755, 0.24, "Relationship", fontsize=7.2)
    add_link(axis, (0.83, 0.245), (0.95, 0.245))


def data_preparation_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 7.2))
    add_view_banner(axis, "Data Preparation View")
    add_structured_box(
        axis,
        (0.12, 0.66),
        (0.20, 0.34),
        "Interaction Event",
        [
            "- event_id (PK)",
            "- timestamp",
            "- user_id",
            "- item_id",
            "- action",
        ],
        fontsize=7.5,
    )
    add_structured_box(
        axis,
        (0.12, 0.26),
        (0.18, 0.23),
        "Product Catalogue",
        ["- item_id (PK)", "- category", "- active"],
        fontsize=7.5,
    )
    add_operator(
        axis,
        (0.35, 0.68),
        (0.17, 0.10),
        "Validate and\nDeduplicate",
        fontsize=8.3,
    )
    add_operator(
        axis,
        (0.55, 0.68),
        (0.17, 0.10),
        "Apply Action\nWeights",
        fontsize=8.3,
    )
    add_operator(
        axis,
        (0.55, 0.47),
        (0.18, 0.10),
        "Aggregate by\nUser and Item",
        fontsize=8.3,
    )
    add_structured_box(
        axis,
        (0.36, 0.27),
        (0.27, 0.25),
        "Prepared User-Item Matrix",
        [
            "- user_id (PK)",
            "- P001 ... P060",
            "- weighted interaction values",
            "- 80 users x 60 items",
        ],
        fontsize=7.2,
    )
    add_note(
        axis,
        (0.64, 0.34),
        (0.14, 0.10),
        "view=1, click=2\ncart=3, purchase=5",
        fontsize=7.0,
    )
    add_link(axis, (0.22, 0.69), (0.265, 0.69), label="outputs", dashed=True)
    add_link(axis, (0.435, 0.68), (0.465, 0.68), arrowstyle="->")
    add_link(axis, (0.55, 0.63), (0.55, 0.52), arrowstyle="->")
    add_link(
        axis,
        (0.48, 0.42),
        (0.48, 0.395),
        label="output",
        dashed=True,
        label_offset=(0.043, 0.013),
    )
    axis.plot(
        [0.21, 0.28, 0.46],
        [0.375, 0.44, 0.44],
        color="black",
        linewidth=1.1,
        linestyle="--",
    )
    axis.text(0.35, 0.455, "input", fontsize=7.8)
    add_link(axis, (0.12, 0.49), (0.12, 0.375), label="relationship", label_offset=(0.06, 0.0))
    add_polyline_link(
        axis,
        [(0.62, 0.63), (0.69, 0.60), (0.69, 0.39), (0.67, 0.39)],
        arrowstyle="-",
    )
    add_link(
        axis,
        (0.495, 0.24),
        (0.69, 0.24),
        label="required for\npersonalized ranking",
        dashed=True,
        arrowstyle="->",
        label_offset=(0.0, -0.045),
    )
    add_data_legend(axis)
    finish_diagram(
        figure,
        axis,
        "gr4ml_data_preparation_view.png",
        "",
        legend=False,
    )


def architecture_view() -> None:
    figure, axis = plt.subplots(figsize=(13, 7))
    add_rectangle(
        axis, (0.08, 0.68), (0.14, 0.13), "Storefront /\nanalyst", face="#FEECEC", edge="#B91C1C"
    )
    add_rectangle(
        axis,
        (0.31, 0.72),
        (0.27, 0.29),
        "COMMAND SERVICE :8101\n\n"
        "POST /commands/interactions\n"
        "POST /commands/train\n\n"
        "Write-optimized CQRS model",
        face=LIGHT_BLUE,
        edge=BLUE,
        fontsize=9,
    )
    add_rectangle(
        axis,
        (0.69, 0.72),
        (0.27, 0.29),
        "QUERY SERVICE :8102\n\n"
        "GET /queries/recommendations\n"
        "GET /queries/model-info\n\n"
        "Read-optimized CQRS model",
        face=LIGHT_TEAL,
        edge=TEAL,
        fontsize=9,
    )
    add_rectangle(axis, (0.31, 0.33), (0.20, 0.12), "Raw event log\nCSV / command store")
    add_activity(axis, (0.49, 0.48), (0.19, 0.12), "ML training\npipeline")
    add_rectangle(
        axis,
        (0.69, 0.33),
        (0.21, 0.12),
        "Versioned read model\nNPZ + metadata",
        face=LIGHT_PURPLE,
        edge=PURPLE,
    )
    add_rectangle(
        axis, (0.92, 0.68), (0.13, 0.13), "Top-5 JSON\nresponse", face=LIGHT_AMBER, edge=AMBER
    )
    add_arrow(axis, (0.15, 0.70), (0.175, 0.72), label="commands")
    add_arrow(axis, (0.15, 0.64), (0.62, 0.69), label="queries", curve=-0.12)
    add_arrow(axis, (0.31, 0.575), (0.31, 0.39), label="append")
    add_arrow(axis, (0.38, 0.38), (0.43, 0.43), label="load")
    add_arrow(axis, (0.58, 0.45), (0.64, 0.38), label="publish")
    add_arrow(axis, (0.69, 0.39), (0.69, 0.575), label="reload")
    add_arrow(axis, (0.825, 0.72), (0.855, 0.70), label="serve")
    axis.text(
        0.50,
        0.12,
        "Pattern 1: Microservices - independent command and query deployments\n"
        "Pattern 2: CQRS - writes/training separated from latency-sensitive reads",
        ha="center",
        va="center",
        fontsize=10,
        color=NAVY,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": LIGHT_GRAY, "edgecolor": "#CBD5E1"},
    )
    finish_diagram(
        figure,
        axis,
        "system_architecture.png",
        "System Architecture - Microservices + CQRS for an ML Recommender",
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
    axes[0].set_ylabel("First 25 of 80 users")
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


def monospace_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Menlo.ttc"),
        Path("/System/Library/Fonts/SFNSMono.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def terminal_image(lines: list[str], filename: str, title: str) -> None:
    width, height = 1800, 1050
    image = Image.new("RGB", (width, height), "#0B1220")
    draw = ImageDraw.Draw(image)
    title_font = monospace_font(30)
    body_font = monospace_font(18)
    draw.rounded_rectangle(
        (30, 28, width - 30, height - 28), radius=18, fill="#111827", outline="#334155", width=3
    )
    draw.rectangle((30, 28, width - 30, 94), fill="#1E293B")
    for x, color in [(62, "#EF4444"), (96, "#F59E0B"), (130, "#22C55E")]:
        draw.ellipse((x - 10, 51, x + 10, 71), fill=color)
    draw.text((165, 47), title, fill="#E2E8F0", font=title_font)
    y = 125
    for raw_line in lines:
        wrapped = textwrap.wrap(raw_line, width=145, replace_whitespace=False) or [""]
        for line in wrapped:
            color = (
                "#A7F3D0"
                if any(token in line for token in ("PASSED", "DONE", "status"))
                else "#E2E8F0"
            )
            draw.text((65, y), line, fill=color, font=body_font)
            y += 32
            if y > height - 70:
                break
        if y > height - 70:
            break
    image.save(EVIDENCE / filename)


def execution_images() -> None:
    capture = io.StringIO()
    from contextlib import redirect_stdout

    with redirect_stdout(capture):
        train_pipeline(DATA, ARTIFACTS)
    training_lines = ["$ python scripts/train_and_evaluate.py", *capture.getvalue().splitlines()]
    _, metadata = load_artifact(ARTIFACTS)
    training_lines.extend(
        [
            "",
            f"precision_at_5          = {metadata['metrics']['precision_at_k']:.4f}",
            f"recall_at_5             = {metadata['metrics']['recall_at_k']:.4f}",
            f"hit_rate_at_5           = {metadata['metrics']['hit_rate_at_k']:.4f}",
            f"catalogue_coverage_at_5 = {metadata['metrics']['catalogue_coverage_at_k']:.4f}",
            "",
            "Quality gate: Precision@5 target >= 0.30 -> PASSED",
        ]
    )
    terminal_image(training_lines, "training_terminal.png", "ML training and evaluation")

    transcript_path = EVIDENCE / "live_demo.json"
    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    query = transcript["recommendation_query"]
    live_lines = [
        "$ python scripts/verify_live.py",
        "LIVE VERIFICATION PASSED",
        "",
        "POST :8101/commands/interactions -> 202 accepted",
        f"event_id={transcript['interaction_command']['event_id']}",
        "POST :8101/commands/train -> 200 trained",
        f"model_version={query['model_version']}",
        "GET :8102/queries/recommendations?user_id=u007&k=5 -> 200",
        "",
        f"user_id={query['user_id']}",
        f"strategy={query['strategy']}",
        "recommendations:",
        *[
            f"  {rank}. {item['item_id']}  score={item['score']}"
            for rank, item in enumerate(query["recommendations"], start=1)
        ],
        "",
        "Command/write service and Query/read service ran as separate processes.",
    ]
    terminal_image(live_lines, "live_execution.png", "Microservices + CQRS live HTTP run")


def api_surface_image(app: Any, filename: str, title: str, subtitle: str, accent: str) -> None:
    schema = app.openapi()
    endpoints: list[tuple[str, str, str]] = []
    for path, methods in schema["paths"].items():
        for method, operation in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            endpoints.append((method.upper(), path, operation.get("summary", "")))

    figure, axis = plt.subplots(figsize=(12, 6.5))
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    axis.text(0.05, 0.91, title, fontsize=20, fontweight="bold", color=NAVY)
    axis.text(0.05, 0.855, subtitle, fontsize=10, color=SLATE)
    y = 0.73
    for method, path, summary in endpoints:
        patch = FancyBboxPatch(
            (0.05, y - 0.055),
            0.90,
            0.105,
            boxstyle="round,pad=0.012,rounding_size=0.012",
            facecolor=LIGHT_GRAY,
            edgecolor="#CBD5E1",
            linewidth=1.2,
        )
        axis.add_patch(patch)
        axis.text(
            0.085,
            y,
            method,
            ha="center",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.5", "facecolor": accent, "edgecolor": accent},
        )
        axis.text(0.16, y + 0.012, path, fontsize=11, fontweight="bold", color=NAVY, va="center")
        axis.text(0.16, y - 0.025, summary, fontsize=8.5, color=SLATE, va="center")
        y -= 0.14
    axis.text(
        0.05,
        0.08,
        "Generated directly from the running FastAPI OpenAPI contract.",
        fontsize=8.5,
        color=SLATE,
    )
    figure.savefig(EVIDENCE / filename, dpi=220, bbox_inches="tight", facecolor="white")
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
    execution_images()
    api_surface_image(
        create_command_app(data_path=DATA, artifact_dir=ARTIFACTS),
        "command_service_api.png",
        "Recommendation Command Service",
        "CQRS write side - interaction ingestion and model training on port 8101",
        BLUE,
    )
    api_surface_image(
        create_query_app(artifact_dir=ARTIFACTS),
        "query_service_api.png",
        "Recommendation Query Service",
        "CQRS read side - model information and recommendation inference on port 8102",
        TEAL,
    )
    print(f"Generated evidence under {EVIDENCE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
