# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt pyproject.toml README.md ./
COPY backend/src ./backend/src
RUN python -m pip install -r requirements.txt \
    && python -m pip install --no-deps .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SEML_DATA_PATH="/app/data/interactions.csv" \
    SEML_USERS_PATH="/app/data/users.csv" \
    SEML_ARTIFACT_DIR="/app/artifacts"

RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=appuser:appuser .streamlit ./.streamlit
COPY --chown=appuser:appuser frontend ./frontend
COPY --chown=appuser:appuser data ./data
COPY --chown=appuser:appuser artifacts ./artifacts

USER appuser
EXPOSE 8101 8102 8501

CMD ["uvicorn", "ecom_ml.query_service.main:app", "--host", "0.0.0.0", "--port", "8102"]
