# SEML E-commerce Recommendation System

A small but **production-shaped** reference implementation of an e-commerce
product-recommendation system, built for **AIMLCZG546 – Software Engineering for
Machine Learning, Assignment I**.

It demonstrates two architectural patterns end to end:

| Pattern | Where | What it buys us |
|---|---|---|
| **API Gateway** | [`src/reco/gateway`](src/reco/gateway) | One secured public entry point: bearer-token auth, per-user rate limiting, request correlation, and routing to internal services. |
| **Event-Driven Architecture** | [`src/reco/recommendation`](src/reco/recommendation) | Activity events are accepted in milliseconds, queued, and processed asynchronously by a background consumer that updates the feature store. |

The machine-learning core (item-based collaborative filtering) lives in
[`src/reco/domain`](src/reco/domain) and is **completely decoupled** from the web
layer, so it is unit-testable in isolation and the scoring strategy can be
swapped without touching the services.

> Looking for the original assignment report, notebook, and GR4ML diagrams?
> They are preserved under [`archive/`](archive).

---

## Architecture

```
                       Authorization: Bearer <token>
 ┌──────────┐   HTTP        ┌─────────────────────┐         ┌───────────────────────────┐
 │  Client  │ ───────────►  │     API Gateway     │  ─────► │  Recommendation Service    │
 │ (store)  │    :8000      │  auth · rate-limit  │  :8001  │     (FastAPI, internal)    │
 └──────────┘               │      · routing      │         │                            │
                            └─────────────────────┘         │  POST /track ──► [ Queue ] │
                                                            │                     │ async │
                                                            │                     ▼       │
                                                            │           [ Event Consumer ]│
                                                            │                     │       │
                                                            │                     ▼       │
                                                            │   [ Feature Store: user×item│
                                                            │     matrix + item similarity]│
                                                            │                     │       │
                                                            │  GET /rank ◄────────┘       │
                                                            │  item-based CF scoring      │
                                                            └───────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full write-up,
sequence diagrams, and the quality-attribute analysis.

---

## Quickstart

### Option A — Docker (recommended)

```bash
docker compose up --build
```

- Gateway Swagger UI: http://localhost:8000/docs
- The internal service is reachable only inside the compose network (as a real
  internal service would be).

In another terminal, drive the demo scenario:

```bash
python scripts/run_demo.py            # talks to the gateway on :8000
```

### Option B — Local (two terminals)

```bash
python -m pip install -e ".[dev,evidence]"

# terminal 1 – internal service
uvicorn reco.recommendation.main:app --port 8001

# terminal 2 – gateway
uvicorn reco.gateway.main:app --port 8000
```

Then call the gateway:

```bash
curl -s "http://localhost:8000/recommend?user_id=u7&k=5" \
  -H "Authorization: Bearer seml-demo-token"
```

> Common tasks are wrapped in the [`Makefile`](Makefile): `make up`, `make test`,
> `make check`, `make demo`, `make evidence`, …

---

## API reference

### Gateway (public, `:8000`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET`  | `/health` | – | Gateway + downstream health. |
| `GET`  | `/recommend?user_id=&k=` | Bearer | Top-k recommendations for a user. |
| `POST` | `/activity` | Bearer | Record a `{user_id, item_id, action}` event. |

### Recommendation service (internal, `:8001`)

| Method | Path | Description |
|---|---|---|
| `GET`  | `/health` | Liveness + consumer status. |
| `GET`  | `/stats` | Feature-store + queue statistics. |
| `POST` | `/track` | Enqueue an event (returns `202 Accepted`). |
| `GET`  | `/rank?user_id=&k=` | Score top-k items on demand. |

`action` is one of `view | click | cart | purchase` (weights `1 / 2 / 3 / 5`).

---

## Configuration

All configuration is environment-driven (12-factor) with sensible local defaults;
see [`.env.example`](.env.example). Each service has its own prefix.

| Variable | Default | Description |
|---|---|---|
| `GATEWAY_AUTH_TOKEN` | `seml-demo-token` | Bearer token clients must present. **Override in any real deployment.** |
| `GATEWAY_RECO_SERVICE_URL` | `http://127.0.0.1:8001` | Downstream service URL. |
| `GATEWAY_RATE_LIMIT_SECONDS` | `0.25` | Min seconds between requests per key. |
| `RECO_SEED_DEMO_DATA` | `true` | Seed synthetic data on startup. |
| `RECO_CONSUMER_POLL_TIMEOUT` | `0.2` | Consumer queue poll timeout (s). |
| `*_LOG_FORMAT` | `json` | `json` for prod, `console` for local. |

---

## Development

```bash
make install-dev     # editable install + dev tools + pre-commit hooks
make check           # ruff lint + mypy + pytest  (exactly what CI runs)
make format          # auto-format & auto-fix
make cov             # tests with coverage
```

Quality gates (also enforced in [CI](.github/workflows/ci.yml) and
[pre-commit](.pre-commit-config.yaml)):

- **ruff** — linting + formatting
- **mypy** — static type checking (typed throughout)
- **pytest** — unit (domain) + integration (both services, no live deps via
  `httpx.MockTransport`)

---

## Offline evaluation

The recommender ships with a reproducible **leave-N-out Precision@k** metric:

```bash
python scripts/generate_evidence.py      # writes artifacts/offline_metrics.json + plot
```

---

## Project structure

```
src/reco/
├── domain/           # ML core (no web deps): feature store, recommender, evaluation
├── recommendation/   # internal service: queue, consumer, routes, app factory
├── gateway/          # public service: auth, rate limiter, routes, app factory
├── config.py         # pydantic-settings (typed env config)
├── logging.py        # structured JSON logging + request-id context
└── middleware.py     # request correlation + access logging
tests/{unit,integration}/
scripts/              # demo client + evidence generator
docs/architecture.md  # design write-up
archive/              # original assignment submission + flat prototype (preserved)
```

---

## License

MIT — see assignment context. For educational use under AIMLCZG546.
