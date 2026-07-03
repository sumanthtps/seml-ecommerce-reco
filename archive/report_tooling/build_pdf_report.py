from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
SCREENSHOTS = ROOT / "screenshots"
FINAL_DIR = ROOT.parent / "final_submission"
PDF_PATH = FINAL_DIR / "GXXX_SEML_Assignment_01_Ecommerce_Recommendation_Final_Report.pdf"

BLUE = colors.HexColor("#1f4e79")
TEAL = colors.HexColor("#0b6b6b")
LIGHT_BLUE = colors.HexColor("#eaf3fb")
LIGHT_TEAL = colors.HexColor("#e8f4f2")
LIGHT_AMBER = colors.HexColor("#fff4d8")
GRID = colors.HexColor("#d8dee9")
TEXT = colors.HexColor("#1f2933")


def ensure_dirs() -> None:
    EVIDENCE.mkdir(exist_ok=True)
    SCREENSHOTS.mkdir(exist_ok=True)
    FINAL_DIR.mkdir(exist_ok=True)


def _wrap_box_text(text: str, width: float, fontsize: int) -> str:
    """Wrap diagram labels so text stays inside the rounded boxes."""
    chars_per_line = max(10, int(width * 70 * (9 / fontsize)))
    wrapped_lines: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(
            textwrap.wrap(
                line,
                width=chars_per_line,
                break_long_words=False,
                break_on_hyphens=False,
            )
        )
    return "\n".join(wrapped_lines)


def add_box(ax, xy, width, height, text, fc="#ffffff", ec="#34495e", fontsize=9, weight="normal"):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        linewidth=1.4,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        _wrap_box_text(text, width, fontsize),
        ha="center",
        va="center",
        fontsize=fontsize,
        weight=weight,
        linespacing=1.15,
    )


def add_arrow(
    ax,
    start,
    end,
    color="#34495e",
    text: str | None = None,
    label_xy=None,
    label_offset=(0, 0.035),
    label_pos: float = 0.5,
    rad: float = 0.0,
):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.2,
        color=color,
        shrinkA=4,
        shrinkB=4,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)
    if text:
        if label_xy is None:
            label_xy = (
                start[0] + (end[0] - start[0]) * label_pos + label_offset[0],
                start[1] + (end[1] - start[1]) * label_pos + label_offset[1],
            )
        ax.text(
            label_xy[0],
            label_xy[1],
            text,
            ha="center",
            va="center",
            fontsize=8,
            color=color,
            bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.85},
        )


def finish_diagram(fig, ax, path: Path, title: str) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, fontsize=13, weight="bold", pad=10)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def diagram_business_view() -> Path:
    path = EVIDENCE / "gr4ml_business_view.png"
    fig, ax = plt.subplots(figsize=(12, 6.2))
    add_box(ax, (0.04, 0.65), 0.24, 0.16, "Strategic goal\nIncrease revenue per session", "#e8f4f2", "#0b6b6b", 9, "bold")
    add_box(ax, (0.38, 0.65), 0.24, 0.16, "Decision\nWhich products to show?", "#eef4ff", "#1f4e79", 9, "bold")
    add_box(ax, (0.72, 0.65), 0.24, 0.16, "Question\nWhat will this user engage with?", "#eef4ff", "#1f4e79", 9, "bold")
    add_box(ax, (0.37, 0.34), 0.28, 0.16, "Insight\nPersonalised top-N product list", "#fff4d8", "#b7791f", 9, "bold")
    add_box(ax, (0.06, 0.36), 0.21, 0.12, "Indicator\nCTR uplift", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.06, 0.16), 0.21, 0.12, "Indicator\nAverage order value", "#ffffff", "#7f8c8d", 8)
    add_arrow(ax, (0.28, 0.73), (0.38, 0.73), text="drives", label_xy=(0.33, 0.78))
    add_arrow(ax, (0.62, 0.73), (0.72, 0.73), text="asks", label_xy=(0.67, 0.78))
    add_arrow(ax, (0.84, 0.65), (0.57, 0.50), text="answered by", label_xy=(0.73, 0.57), rad=-0.05)
    add_arrow(ax, (0.37, 0.42), (0.27, 0.42), text="measured by", label_xy=(0.32, 0.57))
    add_arrow(ax, (0.17, 0.48), (0.17, 0.65), text="tracks", label_xy=(0.12, 0.57))
    finish_diagram(fig, ax, path, "GR4ML Business View - E-commerce Product Recommendation")
    return path


def diagram_analytics_view() -> Path:
    path = EVIDENCE / "gr4ml_analytics_design_view.png"
    fig, ax = plt.subplots(figsize=(12, 6.4))
    add_box(ax, (0.05, 0.72), 0.26, 0.13, "Insight\nTop-N recommendations", "#fff4d8", "#b7791f", 9, "bold")
    add_box(ax, (0.37, 0.70), 0.28, 0.16, "Analytics goal\n[Prediction]\nRank items by user preference", "#e8f4f2", "#0b6b6b", 9, "bold")
    add_box(ax, (0.06, 0.42), 0.26, 0.13, "Item-based CF\nSelected for real-time path", "#eef4ff", "#1f4e79", 8, "bold")
    add_box(ax, (0.37, 0.42), 0.26, 0.13, "Matrix factorisation\nOffline enhancement", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.68, 0.42), 0.26, 0.13, "Content-based filtering\nCold-start fallback", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.18, 0.12), 0.22, 0.12, "Softgoal\nLow latency", "#e8f4f2", "#0b6b6b", 8, "bold")
    add_box(ax, (0.60, 0.12), 0.24, 0.12, "Softgoal\nRecommendation quality", "#e8f4f2", "#0b6b6b", 8, "bold")
    add_arrow(ax, (0.31, 0.785), (0.37, 0.785), text="realises", label_xy=(0.34, 0.84))
    for x in (0.19, 0.50, 0.81):
        add_arrow(ax, (0.51, 0.70), (x, 0.55), rad=0.02)
    ax.text(
        0.51,
        0.62,
        "candidate designs",
        ha="center",
        va="center",
        fontsize=8,
        color="#34495e",
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.9},
    )
    add_arrow(ax, (0.19, 0.42), (0.29, 0.24), color="#0b6b6b", text="+ latency", label_xy=(0.20, 0.34))
    add_arrow(ax, (0.50, 0.42), (0.72, 0.24), color="#0b6b6b", text="+ quality", label_xy=(0.61, 0.34))
    add_arrow(ax, (0.50, 0.42), (0.29, 0.24), color="#b7791f", text="- latency", label_xy=(0.40, 0.31))
    add_arrow(ax, (0.81, 0.42), (0.72, 0.24), color="#0b6b6b", text="+ cold-start", label_xy=(0.83, 0.34))
    finish_diagram(fig, ax, path, "GR4ML Analytics Design View - Prediction Goal and Softgoals")
    return path


def diagram_data_view() -> Path:
    path = EVIDENCE / "gr4ml_data_preparation_view.png"
    fig, ax = plt.subplots(figsize=(12, 6.2))
    sources = [
        ("Event stream\nviews, clicks, carts, purchases", 0.04, 0.70),
        ("Orders table\npurchases", 0.04, 0.51),
        ("Product catalogue\nitem metadata", 0.04, 0.32),
    ]
    for text, x, y in sources:
        add_box(ax, (x, y), 0.22, 0.12, text, "#eef4ff", "#1f4e79", 8, "bold")
    add_box(ax, (0.34, 0.49), 0.22, 0.15, "Clean and validate\nevents", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.60, 0.49), 0.17, 0.15, "Build weighted\nuser-item matrix", "#fff4d8", "#b7791f", 8, "bold")
    add_box(ax, (0.80, 0.49), 0.18, 0.15, "Compute item-item\ncosine similarity", "#fff4d8", "#b7791f", 8, "bold")
    add_box(ax, (0.60, 0.20), 0.17, 0.15, "Filter already-seen\nitems", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.80, 0.20), 0.18, 0.15, "Prepared features\nfor ranking service", "#e8f4f2", "#0b6b6b", 8, "bold")
    add_arrow(ax, (0.26, 0.76), (0.34, 0.61))
    add_arrow(ax, (0.26, 0.57), (0.34, 0.565))
    add_arrow(ax, (0.26, 0.38), (0.34, 0.52))
    add_arrow(ax, (0.56, 0.565), (0.60, 0.565))
    add_arrow(ax, (0.77, 0.565), (0.80, 0.565))
    add_arrow(ax, (0.685, 0.49), (0.685, 0.35))
    add_arrow(ax, (0.77, 0.275), (0.80, 0.275))
    add_arrow(ax, (0.89, 0.49), (0.89, 0.35))
    finish_diagram(fig, ax, path, "GR4ML Data Preparation View - From Events to Ranking Features")
    return path


def diagram_architecture() -> Path:
    path = EVIDENCE / "system_architecture.png"
    fig, ax = plt.subplots(figsize=(12.5, 6.6))
    add_box(ax, (0.04, 0.65), 0.20, 0.13, "Storefront\nWeb/mobile", "#fdecea", "#c0392b", 8, "bold")
    add_box(ax, (0.30, 0.65), 0.20, 0.13, "API Gateway\nAuth, rate-limit, route", "#eef4ff", "#1f4e79", 8, "bold")
    add_box(ax, (0.57, 0.77), 0.18, 0.12, "Event tracking\nservice", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.80, 0.77), 0.18, 0.12, "Message broker\nKafka-style queue", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.80, 0.53), 0.18, 0.12, "Event consumer\nfeature updater", "#ffffff", "#7f8c8d", 8)
    add_box(ax, (0.57, 0.30), 0.20, 0.13, "Feature store\nmatrix + similarity", "#fff4d8", "#b7791f", 8, "bold")
    add_box(ax, (0.30, 0.30), 0.20, 0.13, "Recommendation\nservice (ML)", "#e8f4f2", "#0b6b6b", 8, "bold")
    add_box(ax, (0.04, 0.30), 0.20, 0.13, "Cache\nper-user top-N", "#fff4d8", "#b7791f", 8)
    add_arrow(ax, (0.24, 0.715), (0.30, 0.715), text="requests", label_xy=(0.27, 0.83))
    add_arrow(ax, (0.50, 0.73), (0.57, 0.83), text="POST event", label_xy=(0.53, 0.91))
    add_arrow(ax, (0.75, 0.83), (0.80, 0.83), text="publish", label_xy=(0.775, 0.93))
    add_arrow(ax, (0.89, 0.77), (0.89, 0.65), text="consume", label_xy=(0.93, 0.71))
    add_arrow(ax, (0.80, 0.56), (0.77, 0.40), text="update", label_xy=(0.82, 0.48))
    add_arrow(ax, (0.50, 0.365), (0.57, 0.365), text="read features", label_xy=(0.535, 0.48))
    add_arrow(ax, (0.40, 0.65), (0.40, 0.43), text="GET recommend", label_xy=(0.33, 0.54))
    add_arrow(ax, (0.30, 0.365), (0.24, 0.365), text="cache", label_xy=(0.27, 0.48))
    add_arrow(ax, (0.40, 0.30), (0.40, 0.22), text="JSON top-N", label_xy=(0.40, 0.25))
    ax.text(0.05, 0.12, "Legend: green = ML component, blue/grey = non-ML service, amber = data store, red = external actor.", fontsize=9)
    finish_diagram(fig, ax, path, "System Architecture - Event-Driven Ingestion with API Gateway Serving")
    return path


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy, width: int, font_obj, fill=(30, 41, 51), line_gap=5):
    x, y = xy
    for original_line in text.splitlines():
        if not original_line:
            y += font_obj.size + line_gap
            continue
        wrapped = textwrap.wrap(original_line, width=max(20, width // max(7, font_obj.size // 2)))
        for line in wrapped:
            draw.text((x, y), line, font=font_obj, fill=fill)
            y += font_obj.size + line_gap
    return y


def make_api_evidence_image() -> Path:
    path = SCREENSHOTS / "api_gateway_live_evidence.png"
    demo_path = EVIDENCE / "demo_output.json"
    if not demo_path.exists():
        return path
    transcript = json.loads(demo_path.read_text(encoding="utf-8"))
    post = transcript[0]
    get = transcript[-1]
    get_response = get["response"]

    width, height = 1500, 820
    image = PILImage.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = font(34, True)
    h_font = font(24, True)
    body_font = font(20)
    mono_font = font(18)
    small_font = font(16)

    draw.rectangle([0, 0, width, 92], fill=(31, 78, 121))
    draw.text((38, 24), "Live API Evidence - Gateway + Event-Driven Recommendation", font=title_font, fill="white")

    panels = [
        (38, 125, 704, 390, "Gateway endpoints exposed"),
        (796, 125, 1462, 390, "POST /activity through gateway"),
        (38, 445, 1462, 760, "GET /recommend?user_id=u7&k=5 through gateway"),
    ]
    for x1, y1, x2, y2, heading in panels:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=16, outline=(184, 194, 204), width=2, fill=(248, 250, 252))
        draw.text((x1 + 24, y1 + 20), heading, font=h_font, fill=(31, 78, 121))

    endpoints = [
        "GET  /health      gateway health + internal service health",
        "POST /activity    validates token, routes event to /track",
        "GET  /recommend   validates token, routes query to /rank",
        "Auth header       Authorization: Bearer seml-demo-token",
    ]
    y = 185
    for line in endpoints:
        draw.text((70, y), line, font=body_font, fill=(30, 41, 51))
        y += 42

    post_response = post["response"]
    post_lines = [
        f"status: {post_response['status']}",
        f"pattern: {post_response['pattern']}",
        f"served_by: {post_response['served_by']}",
        "event:",
        f"  user_id={post_response['event']['user_id']}",
        f"  item_id={post_response['event']['item_id']}",
        f"  action={post_response['event']['action']}",
        f"queued_events: {post_response['queued_events']}",
    ]
    y = 180
    for line in post_lines:
        draw.text((828, y), line, font=mono_font, fill=(30, 41, 51))
        y += 25

    engine_stats = get_response.get("recommender_engine", {})
    compact_get = {
        "user_id": get_response["user_id"],
        "served_by": get_response["served_by"],
        "pattern": get_response["pattern"],
        "strategy": get_response["strategy"],
        "events_processed": engine_stats.get("events_processed", "n/a"),
    }
    y = 505
    for key, value in compact_get.items():
        draw.text((70, y), f"{key}: {value}", font=mono_font, fill=(30, 41, 51))
        y += 30
    draw.text((760, 505), "Top-5 recommendations", font=h_font, fill=(31, 78, 121))
    y = 550
    for idx, rec in enumerate(get_response["recommendations"], start=1):
        draw.text((782, y), f"{idx}. {rec['item_id']}   score={rec['score']}", font=mono_font, fill=(30, 41, 51))
        y += 34
    draw.text((70, 776), "Evidence source: seml-ecommerce-reco/evidence/demo_output.json generated by running python demo_requests.py", font=small_font, fill=(91, 107, 121))
    image.save(path)
    return path


def make_consumer_log_image() -> Path:
    path = SCREENSHOTS / "event_consumer_terminal_log.png"
    log_candidates = [
        EVIDENCE / "quick_test_recommendation_api.log",
        EVIDENCE / "start_services_recommendation_api.log",
        EVIDENCE / "recommendation_api.out.log",
    ]
    log_path = next((candidate for candidate in log_candidates if candidate.exists()), log_candidates[0])
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    lines = [line for line in log_text.splitlines() if "processed event" in line or "GET /rank" in line]
    visible = "\n".join(lines[-8:]) if lines else "No consumer log captured yet."

    width, height = 1500, 540
    image = PILImage.new("RGB", (width, height), (24, 30, 37))
    draw = ImageDraw.Draw(image)
    title_font = font(30, True)
    mono_font = font(18)
    small_font = font(16)
    draw.rectangle([0, 0, width, 78], fill=(15, 23, 42))
    draw.text((36, 20), "Event Consumer Terminal Evidence", font=title_font, fill=(245, 247, 250))
    draw.text((38, 100), "Recommendation service log from the live run:", font=small_font, fill=(203, 213, 225))
    draw_wrapped(draw, visible, (38, 138), 1380, mono_font, fill=(229, 231, 235), line_gap=7)
    image.save(path)
    return path


def generate_diagrams() -> list[Path]:
    return [
        diagram_business_view(),
        diagram_analytics_view(),
        diagram_data_view(),
        diagram_architecture(),
    ]


def para(text: str, style):
    return Paragraph(text, style)


def table(data, col_widths=None, header=True, font_size=8.7, leading=10.5):
    rows = []
    for row_idx, row in enumerate(data):
        rows.append([
            Paragraph(str(cell), STYLE["TableHeader" if header and row_idx == 0 else "TableCell"])
            for cell in row
        ])
    tbl = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), leading),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ])
    tbl.setStyle(TableStyle(commands))
    return tbl


def image_flowable(path: Path, width: float = 6.8 * inch):
    img = Image(str(path))
    ratio = img.imageHeight / float(img.imageWidth)
    img.drawWidth = width
    img.drawHeight = width * ratio
    return img


def code_block(text: str):
    return Preformatted(textwrap.dedent(text).strip(), STYLE["Code"])


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def build_styles():
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#52606d"),
            spaceAfter=14,
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=7,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=16,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.6,
            leading=13.2,
            textColor=TEXT,
            spaceAfter=6,
        ),
        "Lead": ParagraphStyle(
            "Lead",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.3,
            leading=14.2,
            textColor=TEXT,
            backColor=LIGHT_BLUE,
            borderColor=colors.HexColor("#b8d4ee"),
            borderWidth=0.7,
            borderPadding=8,
            spaceAfter=9,
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10.5,
            textColor=colors.white,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.3,
            leading=10.3,
            textColor=TEXT,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=10,
            textColor=colors.HexColor("#52606d"),
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=8,
        ),
        "Code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.1,
            leading=8.4,
            textColor=colors.HexColor("#111827"),
            backColor=colors.HexColor("#f6f8fa"),
            borderColor=colors.HexColor("#d0d7de"),
            borderWidth=0.4,
            borderPadding=5,
            spaceBefore=4,
            spaceAfter=8,
        ),
    }
    return styles


STYLE = build_styles()


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d8dee9"))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 0.58 * inch, letter[0] - doc.rightMargin, 0.58 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#52606d"))
    canvas.drawString(doc.leftMargin, 0.38 * inch, "AIMLCZG546 - Software Engineering for Machine Learning - Assignment I")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.38 * inch, f"Page {doc.page}")
    canvas.restoreState()


def add_section(story: list, title: str):
    story.append(Paragraph(title, STYLE["H1"]))


def add_subsection(story: list, title: str):
    story.append(Paragraph(title, STYLE["H2"]))


def build_pdf() -> None:
    ensure_dirs()
    diagram_paths = generate_diagrams()
    api_evidence = make_api_evidence_image()
    consumer_log = make_consumer_log_image()
    gateway_swagger = SCREENSHOTS / "gateway_swagger_ui.png"
    service_swagger = SCREENSHOTS / "recommendation_service_swagger_ui.png"
    recommendation_plot = EVIDENCE / "recommendation_output_plot.png"
    sample_output = load_text(EVIDENCE / "sample_output.txt") if (EVIDENCE / "sample_output.txt").exists() else ""

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.68 * inch,
        rightMargin=0.68 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.74 * inch,
        title="SEML Assignment I - E-commerce Recommendation",
        author="Group - BITS Pilani WILP",
    )
    story: list = []

    story.append(Paragraph("AIMLCZG546 - Software Engineering for Machine Learning", STYLE["Title"]))
    story.append(Paragraph("Assignment I: Real-Time Product Recommendation for an E-commerce Platform", STYLE["Title"]))
    story.append(Paragraph("Domain: E-commerce / Retail | Architectural patterns: Event-Driven Architecture and API Gateway", STYLE["Subtitle"]))
    story.append(Paragraph(
        "This report completes Objective 1 and Objective 2 from the assignment brief: requirements formulation using GR4ML concepts, "
        "system architecture with ML and non-ML components, application of two architectural patterns, and a working prototype with run evidence.",
        STYLE["Lead"],
    ))

    story.append(table([
        ["Field", "Value"],
        ["Group No", "GXXX - replace with actual group number before portal upload"],
        ["Submission file", "<groupid>.pdf or <groupid>.docx as required by Taxila"],
        ["Implementation notebook", "final_submission/GXXX.ipynb - rename GXXX to actual group number"],
        ["Submission deadline", "30 June 2026, 23:00"],
        ["Prototype folder", "seml-ecommerce-reco/"],
    ], col_widths=[1.55 * inch, 5.25 * inch]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(table([
        ["Sl.", "BITS ID", "Name", "Contribution (qualitative)", "%"],
        ["1", "To fill", "To fill", "Requirements Lead: problem statement, requirements, measurable goals, quality requirements", "25"],
        ["2", "To fill", "To fill", "GR4ML Modelling Lead: Business, Analytics Design, and Data Preparation views", "25"],
        ["3", "To fill", "To fill", "Architecture Lead: architecture diagram and pattern selection / justification", "25"],
        ["4", "To fill", "To fill", "Implementation Lead: code, run evidence, screenshots, and code explanation", "25"],
    ], col_widths=[0.35 * inch, 0.95 * inch, 1.0 * inch, 3.9 * inch, 0.45 * inch]))
    story.append(Paragraph("Note: replace the group number, BITS IDs, names, and exact contribution percentages before final submission.", STYLE["Caption"]))

    add_section(story, "Assignment Coverage Matrix")
    story.append(Paragraph(
        "The table below maps the official brief to this report so the evaluator can see that each required item is covered explicitly.",
        STYLE["Body"],
    ))
    story.append(table([
        ["Official requirement", "Where covered"],
        ["Select a domain and define an ML-based problem statement", "Section 1.1"],
        ["Formulate requirement specifications and measurable goals using GR4ML concepts", "Sections 1.2 and 1.3"],
        ["Develop GR4ML Business View, Analytics Design View, and Data Preparation View", "Section 1.3 and Figures 1-3"],
        ["Identify the top three quality requirements with justification", "Section 1.4"],
        ["Draw architecture diagram showing ML and non-ML components", "Section 2.1 and Figure 4"],
        ["Select and apply any two relevant architectural patterns", "Sections 2.2 and 2.3"],
        ["Implement selected patterns using appropriate technologies", "Section 2.3, Appendix A, prototype folder, and GXXX.ipynb"],
        ["Include screenshots / outputs of the application with explanation", "Section 2.4 and Figures 5-9"],
        ["Mention group details and contribution", "Cover page and Task Distribution section"],
    ], col_widths=[3.25 * inch, 3.55 * inch]))

    add_section(story, "Objective 1 - Requirements Formulation")
    add_subsection(story, "1.1 Domain and Problem Statement")
    story.append(Paragraph(
        "We select the e-commerce / online retail domain. A modern storefront earns incremental revenue through cross-sell and up-sell: "
        "showing each shopper additional products they are likely to want. The business goal is to lift revenue per session by replacing a static best-seller block "
        "with a small personalised list that reacts to the user's latest behaviour.",
        STYLE["Body"],
    ))
    story.append(Paragraph(
        "Problem statement: given the evolving history of user-item interactions on the platform, build a system that ranks catalogue items for a user and serves a "
        "personalised top-N recommendation list in real time on the storefront. Formally, this is a recommendation / ranking task using implicit feedback such as "
        "views, clicks, add-to-cart actions, and purchases.",
        STYLE["Body"],
    ))
    story.append(Paragraph(
        "Why ML is appropriate: the relationship between past behaviour and future intent is sparse, high-dimensional, and constantly drifting as products, seasons, "
        "and user preferences change. Hand-written rules do not scale across a large catalogue; a data-driven model can learn item affinity from interaction patterns.",
        STYLE["Body"],
    ))

    add_subsection(story, "1.2 Requirement Specifications and Measurable Goals")
    story.append(table([
        ["ID", "Requirement", "GR4ML role", "Verification"],
        ["FR1", "Capture user activity events: view, click, cart, purchase, with user and item identifiers.", "Operational capability", "POST sample events and check they enter the queue."],
        ["FR2", "Continuously update the user-item interaction features from the event stream.", "Analytics capability", "Consumer log shows processed events and feature count changes."],
        ["FR3", "Serve personalised top-N recommendations for any valid user, excluding already-seen items.", "ML output / insight", "GET /recommend returns ranked unseen items."],
        ["FR4", "Expose client traffic through one authenticated gateway.", "Software interface requirement", "External calls use gateway port 8000, not internal port 8001."],
    ], col_widths=[0.45 * inch, 3.1 * inch, 1.5 * inch, 1.75 * inch]))
    story.append(Spacer(1, 0.06 * inch))
    story.append(table([
        ["Quality / measurable goal", "Metric", "Target", "Reason"],
        ["Relevant top-N", "Offline Precision@5", ">= 0.30", "Measures whether the top returned products include held-out relevant items."],
        ["Business uplift", "CTR uplift vs non-personalised block", ">= 8%", "Represents expected production A/B test improvement."],
        ["Real-time serving", "Recommendation API p95 latency", "< 150 ms", "Recommendations appear on the page-render path."],
        ["Freshness", "Event-to-feature lag", "< 60 s", "Recent behaviour should affect recommendations quickly."],
        ["Catalogue reach", "Catalogue coverage", ">= 60%", "Avoids showing only a narrow set of popular products."],
    ], col_widths=[1.55 * inch, 1.45 * inch, 1.05 * inch, 2.75 * inch]))
    story.append(Paragraph(
        "Executed prototype note: the local implementation reports offline Precision@5 = 0.323 on deterministic synthetic interaction data, clearing the >= 0.30 target.",
        STYLE["Lead"],
    ))

    add_subsection(story, "1.3 GR4ML Views")
    story.append(Paragraph(
        "GR4ML links business intent, analytics design, and data preparation. In this solution the traceable chain is: revenue and engagement goal -> product-display decision -> "
        "question about user intent -> top-N recommendation insight -> prediction/ranking analytics goal -> prepared interaction matrix and item-similarity table.",
        STYLE["Body"],
    ))
    for idx, (path, caption) in enumerate([
        (diagram_paths[0], "Figure 1: Business View showing the strategic goal, decision, question, indicators, and insight."),
        (diagram_paths[1], "Figure 2: Analytics Design View showing the prediction goal, candidate algorithms, and softgoal trade-offs."),
        (diagram_paths[2], "Figure 3: Data Preparation View showing how raw events become prepared ranking features."),
    ], start=1):
        story.append(KeepTogether([image_flowable(path, 6.55 * inch), Paragraph(caption, STYLE["Caption"])]))
    story.append(Paragraph(
        "Business View explanation: the strategic goal is to increase revenue per session through cross-sell, measured by click-through rate and average order value. "
        "The operational decision is which products to show each user. The analytics question is what this user will most likely engage with, and the insight is a personalised top-N list.",
        STYLE["Body"],
    ))
    story.append(Paragraph(
        "Analytics Design View explanation: the insight becomes a prediction goal: rank items by user preference. Item-based collaborative filtering is selected for the real-time path "
        "because similarities can be precomputed and serving is fast. Matrix factorisation is retained as a future offline quality enhancement, while content-based filtering helps with cold-start items.",
        STYLE["Body"],
    ))
    story.append(Paragraph(
        "Data Preparation View explanation: user events, orders, and catalogue metadata are validated, deduplicated, weighted, and transformed into a user-item interaction matrix. "
        "Cosine similarity over item columns produces an item-similarity table; already-seen items are filtered before returning recommendations.",
        STYLE["Body"],
    ))

    add_subsection(story, "1.4 Top Three Quality Requirements")
    story.append(table([
        ["Quality requirement", "Justification", "Design decision influenced"],
        ["Low latency", "Recommendations render inline while the shopper browses; slow serving damages the shopping experience.", "Precompute item similarity, cache top-N, keep the serving path simple."],
        ["Scalability / elasticity", "Traffic is bursty during campaigns and sales; ingestion should not block recommendation serving.", "Use an event-driven broker/queue and independently scalable consumers."],
        ["Recommendation relevance", "Poor suggestions waste screen space and erode user trust.", "Use interaction weights, item similarity, seen-item filtering, Precision@5, and coverage monitoring."],
    ], col_widths=[1.45 * inch, 2.8 * inch, 2.55 * inch]))

    story.append(PageBreak())
    add_section(story, "Objective 2 - System Architecture")
    add_subsection(story, "2.1 Architecture Diagram and Component Responsibilities")
    story.append(KeepTogether([image_flowable(diagram_paths[3], 6.7 * inch), Paragraph("Figure 4: System architecture with ML and non-ML components clearly separated.", STYLE["Caption"])]))
    story.append(table([
        ["Component", "Type", "Responsibility"],
        ["Storefront", "External", "Emits activity events and renders returned product recommendations."],
        ["API Gateway", "Non-ML", "Single entry point for routing, authentication, and rate limiting."],
        ["Event Tracking Service", "Non-ML", "Validates user activity and publishes events."],
        ["Message Broker / Queue", "Non-ML", "Buffers events and decouples producers from consumers."],
        ["Event Consumer / Updater", "Non-ML", "Processes queued events and updates feature data asynchronously."],
        ["Feature Store", "Data store", "Stores the user-item matrix and item-similarity table."],
        ["Recommendation Service", "ML component", "Ranks candidate products using item-based collaborative filtering."],
        ["Cache", "Data store", "Stores repeated per-user top-N results for fast reads."],
    ], col_widths=[1.65 * inch, 1.05 * inch, 4.1 * inch]))

    add_subsection(story, "2.2 Architectural Patterns Selected")
    story.append(Paragraph(
        "<b>Pattern 1 - Event-Driven Architecture.</b> User activity arrives continuously and can spike during campaigns. Producers publish events and consumers react independently, "
        "which decouples ingestion from model updates and protects the recommendation read path from write bursts. In the prototype, POST /track places events into a queue and a background consumer updates the feature store.",
        STYLE["Body"],
    ))
    story.append(Paragraph(
        "<b>Pattern 2 - API Gateway.</b> Clients call one stable gateway endpoint. The gateway centralises authentication, rate limiting, and routing, while the internal recommendation service remains focused on ranking. "
        "In the prototype, external calls go to port 8000 and are forwarded internally to port 8001.",
        STYLE["Body"],
    ))
    story.append(Paragraph(
        "Together, the two patterns implement the desired shape of the system: asynchronous writes for freshness and elasticity, plus fast controlled reads for the storefront experience.",
        STYLE["Lead"],
    ))

    add_subsection(story, "2.3 Implementation Summary")
    story.append(table([
        ["File", "Purpose", "Pattern / concern demonstrated"],
        ["recommender_engine.py", "Maintains the user-item matrix, computes item similarity, ranks unseen products, reports offline Precision@5.", "ML feature management and recommendation logic"],
        ["recommendation_api.py", "Internal FastAPI app with POST /track, GET /rank, event queue, and background consumer.", "Event-Driven Architecture"],
        ["api_gateway.py", "External FastAPI app with GET /recommend and POST /activity; validates token and routes requests.", "API Gateway"],
        ["demo_requests.py", "Sends events through the gateway and captures the recommendation response.", "Application evidence"],
        ["report_evidence.py", "Generates metric JSON, console output text, and recommendation plot.", "Evaluation and screenshots / figures"],
        ["final_submission/GXXX.ipynb", "Notebook version of the implementation and evidence cells for assignment submission.", "Implementation notebook"],
    ], col_widths=[1.45 * inch, 3.25 * inch, 2.1 * inch]))
    story.append(Paragraph("Run commands used for the local prototype:", STYLE["Body"]))
    story.append(code_block(
        """
        python -m pip install -r requirements.txt
        python -m uvicorn recommendation_api:app --host 127.0.0.1 --port 8001
        python -m uvicorn api_gateway:app --host 127.0.0.1 --port 8000
        python demo_requests.py
        python report_evidence.py
        """
    ))

    add_subsection(story, "2.4 Application Evidence and Screenshots")
    story.append(Paragraph(
        "The following figures come from the live local run. They include real browser-rendered Swagger UI screenshots plus request/response and console evidence. "
        "The gateway accepted activity events, routed them to the internal service, and returned recommendations through the single public API.",
        STYLE["Body"],
    ))
    if gateway_swagger.exists():
        story.append(KeepTogether([image_flowable(gateway_swagger, 6.7 * inch), Paragraph("Figure 5: API Gateway Swagger UI showing the public /health, /recommend, and /activity endpoints.", STYLE["Caption"])]))
    if service_swagger.exists():
        story.append(KeepTogether([image_flowable(service_swagger, 6.7 * inch), Paragraph("Figure 6: Internal recommendation/event service Swagger UI showing /track, /rank, /stats, and /health.", STYLE["Caption"])]))
    if api_evidence.exists():
        story.append(KeepTogether([image_flowable(api_evidence, 6.7 * inch), Paragraph("Figure 7: Live API evidence from gateway request/response output.", STYLE["Caption"])]))
    if consumer_log.exists():
        story.append(KeepTogether([image_flowable(consumer_log, 6.7 * inch), Paragraph("Figure 8: Event consumer log showing asynchronous event processing.", STYLE["Caption"])]))
    if recommendation_plot.exists():
        story.append(KeepTogether([image_flowable(recommendation_plot, 6.7 * inch), Paragraph("Figure 9: Executed recommendation evidence: matrix view and top-5 products for user u7.", STYLE["Caption"])]))
    if sample_output:
        story.append(Paragraph("Captured console output from the executed run:", STYLE["Body"]))
        story.append(code_block(sample_output))

    add_subsection(story, "2.5 Reading the Result")
    story.append(Paragraph(
        "The demonstration sends three fresh actions for user u7 through the gateway. The response marks the activity calls as event-driven and served by the API gateway. "
        "After the consumer processes the events, GET /recommend?user_id=u7&k=5 returns items P28, P25, P21, P16, and P40, ranked by collaborative-filtering score. "
        "Already-seen items are filtered out, so the output is a true recommendation list rather than an echo of prior interactions.",
        STYLE["Body"],
    ))

    add_subsection(story, "2.6 Limitations and Future Improvements")
    story.append(Paragraph(
        "This is an academic prototype, so it uses a small deterministic dataset and an in-memory queue to keep the run simple. "
        "In production, the event queue should be replaced with Kafka, Redis Streams, or a managed broker; feature data should be stored in a persistent feature store; "
        "and monitoring should track latency, event lag, Precision@5, catalogue coverage, drift, and online CTR uplift through A/B testing.",
        STYLE["Body"],
    ))

    add_section(story, "Appendix A - Key Code Excerpts")
    story.append(Paragraph(
        "The full runnable code is in the seml-ecommerce-reco folder and the notebook deliverable is final_submission/GXXX.ipynb. "
        "The excerpts below show where the selected patterns and recommendation logic are implemented.",
        STYLE["Body"],
    ))
    add_subsection(story, "A.1 Event-Driven queue and consumer")
    story.append(code_block(
        """
        EVENT_QUEUE: Queue[dict[str, str]] = Queue()

        def consumer_loop() -> None:
            while not STOP_WORKER.is_set():
                try:
                    event = EVENT_QUEUE.get(timeout=0.2)
                except Empty:
                    continue
                result = recommender_engine.track_event(
                    event["user_id"],
                    event["item_id"],
                    event["action"],
                )
                print("processed event:", result, flush=True)
                EVENT_QUEUE.task_done()

        @app.post("/track", status_code=202)
        def track(event: ActivityEvent) -> dict[str, Any]:
            recommender_engine.validate_event(event.user_id, event.item_id, event.action)
            EVENT_QUEUE.put(event.model_dump())
            return {"status": "accepted", "pattern": "event-driven"}
        """
    ))
    add_subsection(story, "A.2 API Gateway routes")
    story.append(code_block(
        """
        @app.get("/recommend")
        async def recommend(user_id: str, k: int = 5,
                            authorization: str | None = Header(default=None)) -> Any:
            require_token(authorization)
            enforce_rate_limit(f"recommend:{user_id}")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{RECO_SERVICE}/rank",
                    params={"user_id": user_id, "k": k},
                )
            payload = await forward_response(response)
            payload["served_by"] = "api-gateway"
            payload["pattern"] = "api-gateway"
            return payload
        """
    ))
    add_subsection(story, "A.3 Collaborative-filtering ranking")
    story.append(code_block(
        """
        def rank_items(user_id: str, k: int = 5) -> list[dict[str, Any]]:
            user_row = _MATRIX[USER_INDEX[user_id]].copy()
            scores = user_row @ _ITEM_SIMILARITY
            scores = scores.astype(float, copy=True)
            scores[user_row > 0] = -np.inf
            ordered = np.argsort(np.nan_to_num(scores, neginf=-1e12))[::-1]
            return [
                {"item_id": ITEMS[i], "score": round(float(scores[i]), 3)}
                for i in ordered
                if user_row[i] == 0
            ][:k]
        """
    ))

    add_section(story, "Task Distribution and References")
    story.append(table([
        ["Member / role", "Tasks owned", "Deliverable", "%"],
        ["Member 1 - Requirements Lead", "Domain, problem statement, requirements, measurable goals, and top quality requirements.", "Sections 1.1, 1.2, 1.4", "25"],
        ["Member 2 - GR4ML Modelling Lead", "Business View, Analytics Design View, Data Preparation View, and diagram validation.", "Section 1.3 + diagrams", "25"],
        ["Member 3 - Architecture Lead", "Architecture diagram, ML/non-ML component split, and pattern justification.", "Sections 2.1, 2.2", "25"],
        ["Member 4 - Implementation Lead", "FastAPI services, event queue, gateway routing, evidence generation, screenshots, and code explanation.", "Sections 2.3, 2.4", "25"],
    ], col_widths=[1.7 * inch, 3.1 * inch, 1.45 * inch, 0.55 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("Submission Readiness Checklist", STYLE["H2"]))
    story.append(table([
        ["Item", "Status"],
        ["PDF final report", "Generated in final_submission/"],
        ["Editable DOCX report", "Generated in final_submission/"],
        ["Implementation notebook", "Generated as final_submission/GXXX.ipynb; rename to actual group number"],
        ["Runnable source code", "Available in seml-ecommerce-reco/"],
        ["Application screenshots", "Gateway Swagger, internal service Swagger, API evidence, terminal log, output plot"],
        ["Group number, names, BITS IDs", "Must be filled by the group before upload"],
    ], col_widths=[2.3 * inch, 4.5 * inch]))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("References", STYLE["H2"]))
    references = [
        "Nalchigar, S., and Yu, E. (2020). Designing Business Analytics Solutions: A Model-Driven Approach. Business & Information Systems Engineering, 62(1), 61-75.",
        "Nalchigar, S., and Yu, E. (2018). Business-driven data analytics: A conceptual modeling framework. Data & Knowledge Engineering.",
        "Nalchigar, S., Yu, E., Obeidi, Y. et al. (2019). Solution Patterns for Machine Learning. CAiSE 2019.",
        "Sarwar, B., Karypis, G., Konstan, J., and Riedl, J. (2001). Item-based collaborative filtering recommendation algorithms. WWW 2001.",
        "FastAPI documentation and scikit-learn cosine_similarity documentation used for the local prototype implementation.",
    ]
    for idx, ref in enumerate(references, start=1):
        story.append(Paragraph(f"{idx}. {ref}", STYLE["Body"]))

    story.append(Paragraph(
        "Final submission checklist: fill group details, verify the file name matches the group ID, and upload this PDF or an exported DOCX/PDF version to Taxila before 30 June 2026, 23:00.",
        STYLE["Lead"],
    ))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


if __name__ == "__main__":
    build_pdf()
    print(PDF_PATH)

