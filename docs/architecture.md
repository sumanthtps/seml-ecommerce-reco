# Architecture

This document explains the system design behind the SEML e-commerce
recommendation prototype and maps it to the assignment's two objectives:
**requirements formulation** and **system architecture**.

## 1. Problem and goals

Online stores need to surface relevant products to keep shoppers engaged. The ML
task is **top-k product recommendation**: given a user's interaction history,
return the `k` products they are most likely to want next.

Measurable goals used in this prototype:

- **Relevance** — maximise offline `Precision@k` on held-out interactions.
- **Responsiveness** — recommendation reads return quickly; event writes never
  block on model updates.
- **Operability** — every request is traceable; services are independently
  configurable and deployable.

## 2. Components (ML and non-ML)

| Component | Type | Responsibility |
|---|---|---|
| API Gateway | non-ML | Auth, rate limiting, request correlation, routing. |
| Recommendation service | non-ML host | Hosts the ML core; exposes `/track` and `/rank`. |
| Event queue | non-ML | Decouples ingestion from processing. |
| Event consumer | non-ML | Applies events to the feature store asynchronously. |
| Feature store | non-ML (data) | User×item interaction matrix + item-item similarity. |
| Recommender | **ML** | Item-based collaborative filtering scorer. |
| Evaluation | **ML** | Leave-N-out Precision@k. |

The clean split means the ML core (`reco.domain`) has **zero** web/framework
dependencies and is exercised directly by unit tests.

## 3. Architectural patterns

### 3.1 API Gateway

The storefront talks to exactly one endpoint. The gateway centralises
cross-cutting concerns so internal services stay simple and unexposed:

- **Authentication** — `HTTPBearer` token check (constant-time compare).
- **Rate limiting** — per-user minimum interval (swappable for Redis token
  bucket).
- **Routing & error normalisation** — forwards to the internal service and maps
  upstream failures to `502`.
- **Correlation** — injects/propagates `X-Request-ID`.

Downstream calls use an injected `httpx.AsyncClient`, so tests substitute a
`MockTransport` and never need a live service.

### 3.2 Event-Driven Architecture

Writes and model updates are decoupled:

```
POST /activity (gateway)  →  POST /track (service)  →  enqueue  →  202 Accepted
                                                          │
                          background consumer thread  ◄───┘
                                   │
                                   ▼
                         FeatureStore.track_event()  →  refresh item similarity
```

`POST /track` returns `202 Accepted` immediately; the consumer drains the queue
on its own thread. The queue sits behind a `MessageQueue` protocol, so the
in-memory implementation can be replaced by Redis Streams / Kafka without
changing the consumer or routes.

### 3.3 Recommendation read path

```
GET /recommend (gateway) → GET /rank (service) → Recommender.rank(user, k)
    score = user_interaction_vector · item_similarity_matrix
    mask already-seen items → take top-k
```

## 4. Sequence (happy path)

```
Client → Gateway:  POST /activity {u7, P12, purchase} + Bearer token
Gateway:           auth ✓, rate-limit ✓
Gateway → Service: POST /track
Service:           validate ✓, enqueue, return 202
Service(consumer): dequeue → FeatureStore.track_event → similarity refresh
...
Client → Gateway:  GET /recommend?user_id=u7&k=5 + Bearer token
Gateway → Service: GET /rank?user_id=u7&k=5
Service:           Recommender.rank → top-5 unseen items
Gateway → Client:  recommendations (+ served_by, pattern)
```

## 5. Top three quality requirements

1. **Performance / responsiveness.** Event ingestion is asynchronous (`202` +
   queue), so write latency is independent of model-update cost. Chosen because
   storefront interactions are high-volume and latency-sensitive.
2. **Security.** All business endpoints sit behind gateway authentication and
   rate limiting; internal services are not publicly exposed (in Docker they have
   no published ports). Chosen because the API is internet-facing.
3. **Maintainability / testability.** Layered design (domain ⟂ services),
   dependency injection, typed config, and a CI-enforced quality gate (ruff +
   mypy + pytest). Chosen because an ML system evolves continuously and must stay
   safe to change.

## 6. From prototype to production

| Concern | Prototype | Production direction |
|---|---|---|
| Queue | in-memory `queue.Queue` | Redis Streams / Kafka |
| Feature store | NumPy matrix in memory | Feast / Redis / warehouse |
| Auth | static bearer token | OAuth2 / JWT / mTLS |
| Rate limiting | per-process dict | shared Redis token bucket |
| Model | item-based CF | ANN retrieval + ranking model |
| Observability | structured logs + request IDs | + metrics (Prometheus) + tracing |

The interfaces (`MessageQueue`, the `FeatureStore`/`Recommender` boundary, the
injected HTTP client) are designed so these swaps are local changes.

## 7. GR4ML views

The Business, Analytics Design, and Data Preparation views (GR4ML notation) and
the original system-architecture diagram are part of the assignment report,
preserved under [`../archive/`](../archive).
