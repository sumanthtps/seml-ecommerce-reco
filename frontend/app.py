"""Interactive Streamlit dashboard for the recommendation system."""

from __future__ import annotations

import html
import os
from datetime import datetime
from typing import Any, Literal

import httpx
import streamlit as st

COMMAND_URL = os.environ.get("SEML_COMMAND_URL", "http://127.0.0.1:8101").rstrip("/")
QUERY_URL = os.environ.get("SEML_QUERY_URL", "http://127.0.0.1:8102").rstrip("/")
INTERESTS = [
    "Electronics",
    "Home & Kitchen",
    "Fashion",
    "Personal Care",
    "Fitness & Lifestyle",
]


class ApiError(RuntimeError):
    """A readable error returned by one of the backend services."""


def request_json(
    method: Literal["GET", "POST"],
    url: str,
    *,
    payload: dict[str, str | int] | None = None,
    params: dict[str, str | int] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Call a backend endpoint and normalize its JSON response."""
    try:
        response = httpx.request(
            method,
            url,
            json=payload,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail: Any
        try:
            detail = exc.response.json().get("detail")
        except (ValueError, AttributeError):
            detail = exc.response.text
        raise ApiError(str(detail or f"HTTP {exc.response.status_code}")) from exc
    except httpx.RequestError as exc:
        raise ApiError(f"Cannot reach {url}: {exc}") from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise ApiError("The service returned an invalid JSON response.") from exc
    if not isinstance(result, dict):
        raise ApiError("The service returned an unexpected response.")
    return {str(key): value for key, value in result.items()}


def service_health(base_url: str) -> tuple[bool, str, dict[str, Any] | None]:
    """Return a compact health result suitable for a status card."""
    try:
        result = request_json("GET", f"{base_url}/health", timeout=3.0)
    except ApiError as exc:
        return False, str(exc), None
    status = str(result.get("status", "unknown"))
    if status != "ok":
        return False, status.replace("_", " ").title(), result
    return True, "Online", result


def inject_styles() -> None:
    """Apply the dashboard's small visual system."""
    st.markdown(
        """
        <style>
        :root {
            --ink: #17212b;
            --muted: #65717d;
            --mint: #0f766e;
            --mint-dark: #0b5f59;
            --mint-soft: #e7f6f2;
            --coral: #e76f51;
        }
        html, body, .stApp, [data-testid="stAppViewContainer"] {
            color: var(--ink) !important;
        }
        .stApp, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 92% 2%, rgba(15,118,110,.09), transparent 28rem),
                #fbfcfa !important;
        }
        [data-testid="stSidebar"] {
            background: #f0f5f3 !important;
            color: var(--ink) !important;
        }
        .block-container {max-width: 1180px; padding-top: 2.2rem;}
        .stApp h1, .stApp h2, .stApp h3,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: var(--ink) !important;
        }
        [data-testid="stWidgetLabel"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
            opacity: 1 !important;
        }
        [data-testid="stAlert"] p {color: inherit !important;}
        [data-testid="stMetricLabel"] p {color: var(--muted) !important;}
        [data-testid="stMetricValue"] {color: var(--ink) !important;}
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary p {
            color: var(--ink) !important;
            opacity: 1 !important;
        }
        [data-baseweb="tab-list"] button {
            color: #52606d !important;
            opacity: 1 !important;
        }
        [data-baseweb="tab-list"] button:hover,
        [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: var(--mint) !important;
        }
        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] input,
        [data-baseweb="select"] > div {
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
            background: #ffffff !important;
            opacity: 1 !important;
        }
        .stButton button,
        .stFormSubmitButton button {
            opacity: 1 !important;
            font-weight: 700 !important;
            transition: background-color .15s ease, border-color .15s ease;
        }
        .stButton button p,
        .stFormSubmitButton button p {color: inherit !important;}
        .stButton button[kind="primary"],
        .stFormSubmitButton button[kind="primary"] {
            color: #ffffff !important;
            background: var(--mint) !important;
            border-color: var(--mint) !important;
        }
        .stButton button[kind="primary"]:hover,
        .stFormSubmitButton button[kind="primary"]:hover {
            color: #ffffff !important;
            background: var(--mint-dark) !important;
            border-color: var(--mint-dark) !important;
        }
        .stButton button:disabled,
        .stFormSubmitButton button:disabled {
            color: #667085 !important;
            background: #e4e9e7 !important;
            border-color: #d0d8d5 !important;
        }
        .stButton button:disabled p,
        .stFormSubmitButton button:disabled p {color: #667085 !important;}
        a {color: var(--mint) !important;}
        a:hover {color: var(--mint-dark) !important;}
        .hero {
            padding: 2rem 2.2rem;
            border: 1px solid rgba(15,118,110,.16);
            border-radius: 24px;
            background: linear-gradient(125deg, #ffffff 20%, #edf9f5 100%);
            box-shadow: 0 14px 40px rgba(23,33,43,.07);
            margin-bottom: 1.4rem;
        }
        .eyebrow {
            color: var(--mint);
            font-size: .78rem;
            font-weight: 750;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        .hero h1 {
            color: var(--ink);
            font-size: clamp(2rem, 5vw, 3.4rem);
            line-height: 1.02;
            letter-spacing: -.045em;
            margin: .55rem 0 .75rem;
        }
        .hero p {color: var(--muted); font-size: 1.05rem; max-width: 720px;}
        .flow {
            display: inline-flex;
            gap: .6rem;
            align-items: center;
            color: #36505a;
            background: rgba(255,255,255,.72);
            border-radius: 999px;
            padding: .55rem .85rem;
            font-size: .84rem;
            margin-top: .55rem;
        }
        .status-card {
            border: 1px solid #e3e9e7;
            border-radius: 14px;
            padding: .8rem .9rem;
            background: white;
            margin-bottom: .65rem;
        }
        .status-row {display:flex; align-items:center; justify-content:space-between; gap:.6rem;}
        .status-name {font-weight: 700; color: var(--ink);}
        .status-note {font-size: .75rem; color: var(--muted); margin-top: .18rem;}
        .dot {height: .65rem; width: .65rem; border-radius: 50%; display:inline-block;}
        .dot.online {background:#16a34a; box-shadow:0 0 0 4px rgba(22,163,74,.12);}
        .dot.offline {background:#dc2626; box-shadow:0 0 0 4px rgba(220,38,38,.11);}
        .rec-card {
            min-height: 190px;
            padding: 1rem;
            border: 1px solid #dfe8e5;
            border-radius: 18px;
            background: white;
            box-shadow: 0 7px 18px rgba(23,33,43,.045);
            margin-bottom: .8rem;
        }
        .rec-rank {color: var(--coral); font-size: .72rem; font-weight:800; letter-spacing:.08em;}
        .rec-id {
            display: inline-block;
            color: var(--mint);
            background: var(--mint-soft);
            border-radius: 999px;
            padding: .15rem .45rem;
            font-size: .68rem;
            font-weight: 750;
            margin-top: .5rem;
        }
        .rec-item {
            font-size: 1.03rem;
            line-height: 1.28;
            font-weight: 760;
            color: var(--ink);
            margin: .45rem 0;
        }
        .rec-category {color: #475569; font-size: .76rem; margin-bottom: .45rem;}
        .rec-score {color: var(--muted); font-size: .82rem;}
        .activity-heading {margin-top: 1.25rem; margin-bottom: .2rem;}
        .activity-card {
            min-height: 168px;
            padding: 1rem;
            border: 1px solid #dfe8e5;
            border-left: 4px solid var(--mint);
            border-radius: 14px;
            background: #ffffff;
            margin: .65rem 0 .35rem;
        }
        .activity-action {
            color: var(--mint);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
        }
        .activity-product {
            color: var(--ink);
            font-size: .97rem;
            line-height: 1.3;
            font-weight: 720;
            margin: .45rem 0;
        }
        .activity-meta {color: #475569; font-size: .76rem;}
        .activity-time {color: var(--muted); font-size: .72rem; margin-top: .55rem;}
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,.82);
            border: 1px solid #e1e9e6;
            padding: .8rem 1rem;
            border-radius: 16px;
        }
        div[data-testid="stForm"] {
            background: rgba(255,255,255,.74);
            border: 1px solid #e3e9e7;
            border-radius: 18px;
            padding: 1.1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(name: str, port: int, healthy: bool, detail: str) -> None:
    """Render one service status card in the sidebar."""
    state = "online" if healthy else "offline"
    st.markdown(
        f"""
        <div class="status-card">
          <div class="status-row">
            <span class="status-name">{html.escape(name)}</span>
            <span class="dot {state}"></span>
          </div>
          <div class="status-note">:{port} · {html.escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendations(result: dict[str, Any]) -> None:
    """Render recommendation results as a ranked responsive card grid."""
    recommendations = result.get("recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        st.info("No unseen products are available for this user.")
        return

    st.caption(
        f"Model {result.get('model_version', 'unknown')} · "
        f"{result.get('strategy', 'recommendation model')}"
    )
    columns = st.columns(min(5, len(recommendations)))
    for index, raw_recommendation in enumerate(recommendations, start=1):
        if not isinstance(raw_recommendation, dict):
            continue
        item_id = html.escape(str(raw_recommendation.get("item_id", "Unknown")))
        product_name = html.escape(str(raw_recommendation.get("product_name", item_id)))
        category = html.escape(str(raw_recommendation.get("category", "Other")))
        raw_score = raw_recommendation.get("score", 0.0)
        score = float(raw_score) if isinstance(raw_score, int | float) else 0.0
        with columns[(index - 1) % len(columns)]:
            st.markdown(
                f"""
                <div class="rec-card">
                  <div class="rec-rank">RANK {index:02d}</div>
                  <div class="rec-id">{item_id}</div>
                  <div class="rec-item">{product_name}</div>
                  <div class="rec-category">{category}</div>
                  <div class="rec-score">Affinity score · {score:.3f}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def format_timestamp(value: Any) -> str:
    """Format an ISO timestamp for compact activity cards."""
    raw_value = str(value)
    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError:
        return raw_value
    return parsed.strftime("%d %b %Y · %H:%M %Z").strip()


def render_recent_actions(result: dict[str, Any]) -> None:
    """Render the three newest actions beneath recommendation results."""
    actions = result.get("actions")
    if not isinstance(actions, list):
        return

    user_id = html.escape(str(result.get("user_id", "customer")))
    st.markdown('<h4 class="activity-heading">Last 3 actions</h4>', unsafe_allow_html=True)
    st.caption(f"Most recent recorded behaviour for {user_id}, newest first.")
    if not actions:
        raw_interest = result.get("interest")
        interest = str(raw_interest) if raw_interest else "selected"
        st.info(
            "No recorded actions were found for this user. "
            f"Showing recommendations based on their {interest} interest."
        )
        return

    action_labels = {
        "view": "Viewed",
        "click": "Clicked",
        "cart": "Added to cart",
        "purchase": "Purchased",
    }
    columns = st.columns(len(actions))
    for index, raw_action in enumerate(actions):
        if not isinstance(raw_action, dict):
            continue
        action = str(raw_action.get("action", "interaction"))
        label = html.escape(action_labels.get(action, action.title()))
        product_name = html.escape(
            str(raw_action.get("product_name", raw_action.get("item_id", "Unknown product")))
        )
        item_id = html.escape(str(raw_action.get("item_id", "Unknown")))
        category = html.escape(str(raw_action.get("category", "Other")))
        timestamp = html.escape(format_timestamp(raw_action.get("timestamp", "")))
        with columns[index]:
            st.markdown(
                f"""
                <div class="activity-card">
                  <div class="activity-action">{label}</div>
                  <div class="activity-product">{product_name}</div>
                  <div class="activity-meta">{item_id} · {category}</div>
                  <div class="activity-time">{timestamp}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_model_snapshot(model_info: dict[str, Any] | None) -> None:
    """Show the current model's most useful operational facts."""
    st.subheader("Model snapshot")
    if model_info is None:
        st.info("Start the query service to see model information.")
        return

    metrics = model_info.get("metrics")
    metrics = metrics if isinstance(metrics, dict) else {}
    first, second, third, fourth = st.columns(4)
    first.metric("Users", model_info.get("users", "—"))
    second.metric("Products", model_info.get("items", "—"))
    third.metric("Training events", model_info.get("training_events", "—"))
    precision = metrics.get("precision_at_k")
    fourth.metric(
        "Precision@5",
        f"{float(precision):.3f}" if isinstance(precision, int | float) else "—",
    )

    with st.expander("Model metadata and evaluation metrics"):
        st.json(model_info)


def user_labels(users: list[dict[str, Any]]) -> dict[str, str]:
    """Build readable selectbox labels keyed by user ID."""
    return {
        str(user.get("user_id")): (
            f"{user.get('name', user.get('user_id'))} · "
            f"{user.get('interest', 'No interest')} ({user.get('user_id')})"
        )
        for user in users
        if user.get("user_id")
    }


def render_recommend_tab(
    query_healthy: bool,
    users: list[dict[str, Any]],
) -> None:
    """Render the read-only recommendation workflow."""
    st.subheader("Find products for a customer")
    st.caption("This is a CQRS query: it reads the current model without changing data.")
    with st.form("recommendation-form"):
        user_column, count_column = st.columns([2, 1])
        labels = user_labels(users)
        if labels:
            user_ids = list(labels)
            user_id = str(
                user_column.selectbox(
                    "Customer",
                    user_ids,
                    index=min(1, len(user_ids) - 1),
                    format_func=labels.__getitem__,
                    key="recommendation-user",
                )
            )
        else:
            user_id = user_column.text_input("User ID", value="u001", placeholder="u001")
        recommendation_count = count_column.slider("Number of products", 1, 20, 5)
        submitted = st.form_submit_button(
            "Generate recommendations",
            type="primary",
            disabled=not query_healthy,
            width="stretch",
        )

    if submitted:
        if not user_id.strip():
            st.warning("Enter a user ID.")
        else:
            try:
                with st.spinner("Ranking unseen products…"):
                    result = request_json(
                        "GET",
                        f"{QUERY_URL}/queries/recommendations",
                        params={"user_id": user_id.strip(), "k": recommendation_count},
                    )
                st.session_state["recommendation_result"] = result
                try:
                    recent_actions = request_json(
                        "GET",
                        f"{QUERY_URL}/queries/recent-actions",
                        params={"user_id": user_id.strip(), "limit": 3},
                    )
                except ApiError:
                    recent_actions = {"user_id": user_id.strip(), "actions": []}
                st.session_state["recent_actions_result"] = recent_actions
            except ApiError as exc:
                st.error(str(exc))

    stored_result = st.session_state.get("recommendation_result")
    if isinstance(stored_result, dict):
        render_recommendations(stored_result)
        recent_actions_result = st.session_state.get("recent_actions_result")
        if isinstance(recent_actions_result, dict):
            render_recent_actions(recent_actions_result)


def render_interaction_tab(
    command_healthy: bool,
    products: list[dict[str, Any]],
    users: list[dict[str, Any]],
) -> None:
    """Render the interaction command workflow."""
    st.subheader("Record customer behaviour")
    st.caption("This command appends one validated event to the interaction log.")
    with st.form("interaction-form"):
        user_column, item_column = st.columns(2)
        labels = user_labels(users)
        if labels:
            user_ids = list(labels)
            user_id = str(
                user_column.selectbox(
                    "Customer",
                    user_ids,
                    index=min(1, len(user_ids) - 1),
                    format_func=labels.__getitem__,
                    key="interaction-user",
                )
            )
        else:
            user_id = user_column.text_input("User ID", value="u001", key="interaction-user")
        product_labels = {
            str(product.get("item_id")): (
                f"{product.get('product_name', product.get('item_id'))} ({product.get('item_id')})"
            )
            for product in products
            if product.get("item_id")
        }
        if product_labels:
            product_ids = list(product_labels)
            default_index = min(11, len(product_ids) - 1)
            item_id = str(
                item_column.selectbox(
                    "Product",
                    product_ids,
                    index=default_index,
                    format_func=product_labels.__getitem__,
                )
            )
        else:
            item_id = item_column.text_input("Product ID", value="P012")
        action = st.selectbox("Action", ["view", "click", "cart", "purchase"], index=0)
        submitted = st.form_submit_button(
            "Record interaction",
            type="primary",
            disabled=not command_healthy,
            width="stretch",
        )

    if submitted:
        if not user_id.strip() or not item_id.strip():
            st.warning("User ID and product ID are required.")
            return
        try:
            result = request_json(
                "POST",
                f"{COMMAND_URL}/commands/interactions",
                payload={
                    "user_id": user_id.strip(),
                    "item_id": item_id.strip(),
                    "action": str(action),
                },
            )
        except ApiError as exc:
            st.error(str(exc))
            return
        st.success(f"Interaction accepted · event {result.get('event_id', 'created')}")
        st.info("Retrain the model when you want this event reflected in recommendations.")


def render_users_tab(
    command_healthy: bool,
    users: list[dict[str, Any]],
) -> None:
    """Render named user profiles and the add-user command."""
    st.subheader("Users")
    st.caption(
        "New users receive interest-based recommendations until interaction history is trained."
    )

    created_message = st.session_state.pop("user_created_message", None)
    if created_message:
        st.success(str(created_message))

    if users:
        st.dataframe(
            [
                {
                    "Name": user.get("name", "Unknown"),
                    "Interest": user.get("interest", "Unknown"),
                    "User ID": user.get("user_id", "Unknown"),
                }
                for user in users
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No user profiles are available yet.")

    st.markdown("#### Add a user")
    with st.form("add-user-form", clear_on_submit=True):
        name_column, interest_column = st.columns(2)
        name = name_column.text_input("Name", placeholder="Enter customer name")
        interest = interest_column.selectbox("Primary interest", INTERESTS)
        submitted = st.form_submit_button(
            "Add user",
            type="primary",
            disabled=not command_healthy,
            width="stretch",
        )

    if not submitted:
        return
    if not name.strip():
        st.warning("Enter a user name.")
        return
    try:
        result = request_json(
            "POST",
            f"{COMMAND_URL}/commands/users",
            payload={"name": name.strip(), "interest": str(interest)},
        )
    except ApiError as exc:
        st.error(str(exc))
        return

    st.session_state["user_created_message"] = (
        f"Added {result.get('name', name.strip())} with "
        f"{result.get('interest', interest)} interests."
    )
    st.rerun()


def render_training_tab(command_healthy: bool) -> None:
    """Render model training controls and the latest returned summary."""
    st.subheader("Train the read model")
    st.caption("This command evaluates, trains, and replaces the current model artifact.")
    st.warning("Training updates files in `artifacts/` and may take a few moments.")

    with st.form("training-form"):
        k_column, holdout_column = st.columns(2)
        evaluation_k = k_column.slider("Evaluation K", 1, 20, 5)
        holdout = holdout_column.slider("Holdout events per user", 1, 5, 2)
        submitted = st.form_submit_button(
            "Train model",
            type="primary",
            disabled=not command_healthy,
            width="stretch",
        )

    if submitted:
        status = st.status("Running the five-stage ML pipeline…", expanded=True)
        try:
            result = request_json(
                "POST",
                f"{COMMAND_URL}/commands/train",
                payload={"k": evaluation_k, "holdout_per_user": holdout},
                timeout=120.0,
            )
        except ApiError as exc:
            status.update(label="Training failed", state="error", expanded=True)
            status.error(str(exc))
        else:
            status.write("Loaded and validated interaction events")
            status.write("Evaluated leave-n-out recommendation quality")
            status.write("Persisted the refreshed read model")
            status.update(label="Model training complete", state="complete", expanded=False)
            st.session_state["training_result"] = result
            st.toast("The query service will automatically load the new model.", icon="✅")

    training_result = st.session_state.get("training_result")
    if isinstance(training_result, dict):
        summary = training_result.get("summary")
        if isinstance(summary, dict):
            st.json(summary)


def main() -> None:
    """Render the complete application."""
    st.set_page_config(
        page_title="Recommendation Control Room",
        page_icon="🛍️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    command_healthy, command_detail, _ = service_health(COMMAND_URL)
    query_healthy, query_detail, query_health = service_health(QUERY_URL)

    model_info: dict[str, Any] | None = None
    products: list[dict[str, Any]] = []
    users: list[dict[str, Any]] = []
    if query_healthy:
        try:
            model_info = request_json("GET", f"{QUERY_URL}/queries/model-info", timeout=5.0)
        except ApiError:
            model_info = None
        try:
            catalog = request_json("GET", f"{QUERY_URL}/queries/products", timeout=5.0)
            raw_products = catalog.get("products")
            if isinstance(raw_products, list):
                products = [product for product in raw_products if isinstance(product, dict)]
        except ApiError:
            products = []
        try:
            user_catalog = request_json("GET", f"{QUERY_URL}/queries/users", timeout=5.0)
            raw_users = user_catalog.get("users")
            if isinstance(raw_users, list):
                users = [user for user in raw_users if isinstance(user, dict)]
        except ApiError:
            users = []

    with st.sidebar:
        st.markdown("### Service control")
        st.caption("Live status of the three-service application")
        render_status_card("Command service", 8101, command_healthy, command_detail)
        render_status_card("Query service", 8102, query_healthy, query_detail)
        st.divider()
        st.markdown(f"[Command API docs]({COMMAND_URL}/docs)")
        st.markdown(f"[Query API docs]({QUERY_URL}/docs)")
        st.caption("Refresh the page after starting or stopping a backend service.")

    version = "No model loaded"
    if query_health is not None and query_health.get("model_version"):
        version = f"Model {query_health['model_version']}"
    st.markdown(
        f"""
        <section class="hero">
          <div class="eyebrow">Group 049 · SEML Assignment I</div>
          <h1>Recommendation<br/>Control Room</h1>
          <p>
            Explore personalised products, capture customer signals, and refresh the
            collaborative-filtering model from one focused dashboard.
          </p>
          <div class="flow">
            Streamlit :8501&nbsp; → &nbsp;Command :8101&nbsp; + &nbsp;Query :8102
            &nbsp; · &nbsp;{html.escape(version)}
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    recommend_tab, interaction_tab, users_tab, training_tab = st.tabs(
        ["✨ Recommend", "+ Record interaction", "👥 Users", "↻ Train model"]
    )
    with recommend_tab:
        render_recommend_tab(query_healthy, users)
    with interaction_tab:
        render_interaction_tab(command_healthy, products, users)
    with users_tab:
        render_users_tab(command_healthy, users)
    with training_tab:
        render_training_tab(command_healthy)

    st.divider()
    render_model_snapshot(model_info)
    st.caption("Item-based collaborative filtering · FastAPI microservices · CQRS architecture")


if __name__ == "__main__":
    main()
