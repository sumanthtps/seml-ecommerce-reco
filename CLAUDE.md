# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

An e-commerce product-recommendation system built for a Software Engineering for ML
assignment, structured as a production-shaped monorepo. It is **two FastAPI services
plus a shared, framework-free ML domain library**, demonstrating two architectural
patterns: **API Gateway** (`reco.gateway`) and **Event-Driven Architecture**
(`reco.recommendation`).

## Commands

Console scripts (`ruff`, `pytest`, `mypy`) are **not on PATH** in this environment —
invoke them via `python -m`. The `Makefile` wraps the same commands if `make` is available.

```bash
python -m pip install -e ".[dev,evidence]"   # install package + dev/test/lint tools

python -m pytest                              # full suite (33 tests)
python -m pytest tests/unit/test_recommender.py::test_rank_returns_k_items  # single test
python -m pytest tests/integration            # integration only

python -m ruff check src tests scripts        # lint
python -m ruff format src tests scripts       # auto-format
python -m mypy                                # type-check (configured to src/ only)

# Run locally (two terminals); gateway depends on the recommendation service.
python -m uvicorn reco.recommendation.main:app --port 8001
python -m uvicorn reco.gateway.main:app --port 8000      # Swagger: http://localhost:8000/docs

docker compose up --build                     # both services as containers
python scripts/run_demo.py                    # drive a scenario through a running gateway
python scripts/generate_evidence.py           # offline metrics + plot → artifacts/
```

`make check` runs lint + types + tests — the same gate as CI (`.github/workflows/ci.yml`).

## Architecture

Three layers, with a hard dependency rule: **`reco.domain` imports nothing from the
service layer and has no web/framework dependencies.** Services depend on the domain,
never the reverse.

- **`src/reco/domain/`** — the ML core. `FeatureStore` (thread-safe user×item matrix +
  derived item-item cosine similarity), `Recommender` (item-based CF scorer that reads a
  store), `evaluate_precision_at_k` (offline metric on a matrix snapshot). All state is
  instance-based and injected — there are no module globals. Errors are `DomainError`
  subclasses (`UnknownUserError`, `InvalidParameterError`, …), never HTTP types.

- **`src/reco/recommendation/`** — internal service (Event-Driven). `POST /track`
  validates then enqueues an event and returns `202` immediately; an `EventConsumer`
  background thread drains the queue and applies events to the `FeatureStore`. The queue
  is hidden behind the `MessageQueue` protocol (`queue.py`) so a real broker can replace
  the in-memory one without touching the consumer or routes.

- **`src/reco/gateway/`** — public service (API Gateway). The only exposed surface; adds
  `HTTPBearer` auth, per-key rate limiting, and forwards to the recommendation service
  over an injected `httpx.AsyncClient`. Adds `served_by`/`pattern` to responses and maps
  upstream/transport failures to `502`.

### Wiring pattern (read these together to understand the app)

Both services use the **app-factory + `app.state` + dependency-getter** pattern. To trace
how any handler gets its collaborators, read `main.py` and `routes.py` of a service together:

1. `create_app(settings)` constructs collaborators and stores them on `app.state`
   (e.g. `app.state.store`, `app.state.queue`, `app.state.rate_limiter`).
2. `lifespan` handles what needs the running loop/threads: the recommendation service
   **seeds demo data and starts the consumer here**; the gateway **creates/closes the
   httpx client here**.
3. Routes never read globals — they depend on getters like `get_store` / `get_http_client`
   that return `request.app.state.X`. This indirection is what makes the services testable.
4. Module-level `app = create_app()` at the bottom of each `main.py` is the uvicorn target.

`create_app(settings=...)` taking explicit settings is deliberate: tests build apps with
custom config without touching the environment.

### Cross-cutting

- **Config** (`config.py`): `pydantic-settings`, one class per service with distinct env
  prefixes — `GATEWAY_*` and `RECO_*` (see `.env.example`). Access via the cached
  `get_*_settings()` helpers.
- **Logging/middleware**: `configure_logging()` (JSON or `console`) is called inside each
  `create_app`. `RequestContextMiddleware` assigns/propagates `X-Request-ID` and injects it
  into every log record via a `ContextVar`.
- **Domain → HTTP error mapping** happens only in routes (`_bad_request` turns any
  `DomainError` into a `400`). Keep this boundary: domain code must not raise HTTP errors.

## Testing conventions

- **Gateway integration tests need no live downstream**: they override `get_http_client`
  via `app.dependency_overrides` with an `httpx.AsyncClient(transport=httpx.MockTransport(...))`.
- **Recommendation integration tests must use `with TestClient(app) as client:`** so the
  lifespan runs — otherwise data isn't seeded and the consumer thread never starts. Because
  the consumer is asynchronous, assert event processing by polling `/stats` until the count
  rises (see `test_track_event_is_processed_asynchronously`).
- `mypy` checks `src/` only; `ruff` whitelists `fastapi.Depends` for rule `B008`
  (calling `Depends()` in defaults is the intended FastAPI pattern here).

## Conventions

- Adding an endpoint: define request/response models in the service's `schemas.py`, add the
  handler to `routes.py` resolving collaborators through `Depends(get_…)`, and let domain
  errors propagate to `_bad_request`.
- Demo auth token is `seml-demo-token` (`GATEWAY_AUTH_TOKEN`); ports are gateway `8000`,
  recommendation `8001`.
- `requirements.txt` holds pinned **runtime** deps (used by the Dockerfile for layer
  caching); dev/test/lint tools live in `pyproject.toml` extras.
- `archive/` contains the original flat prototype and the report/notebook tooling. It is
  reference-only — nothing in `src/`, `tests/`, or `scripts/` imports from it.
