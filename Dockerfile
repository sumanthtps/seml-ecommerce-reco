# syntax=docker/dockerfile:1

# --------------------------------------------------------------------------- #
# Stage 1: build a self-contained virtualenv with the app installed
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install pinned dependencies first so this layer is cached across code changes.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install the application itself (no deps - already installed above).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-deps .

# --------------------------------------------------------------------------- #
# Stage 2: minimal runtime image, non-root
# --------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /opt/venv /opt/venv

USER appuser
WORKDIR /home/appuser

EXPOSE 8000 8001

# Default command runs the internal recommendation service.
# docker-compose overrides this for the gateway container.
CMD ["uvicorn", "reco.recommendation.main:app", "--host", "0.0.0.0", "--port", "8001"]
