# Webhook Processing Service

A production-oriented Python webhook receiver built with FastAPI that demonstrates HMAC-SHA256 signature verification, replay-attack prevention, event routing, in-memory event storage, queue publishing, and a layered architecture separating HTTP reception from event processing.

---

## Overview

This project implements the patterns required to receive webhooks reliably and securely: constant-time HMAC signature verification, timestamp-based replay-attack prevention, event deserialization and validation, event storage, handler dispatch, and asynchronous queue publishing. It is the receiving side of the integration pattern that appears in payment systems (Stripe), source control platforms (GitHub), communication tools (Twilio), and every other SaaS product that pushes events via HTTP.

---

## Architecture

```text
External System (GitHub, Stripe, etc.)
        │  POST /webhooks/{provider}
        │  X-Signature: sha256=<hmac>
        │  X-Timestamp: <unix timestamp>
        ▼
FastAPI Route (src/api/routes.py)
        │  route by provider
        │  extract signature + timestamp headers
        ▼
SignatureValidator (src/validators/signature.py)
        │  HMAC-SHA256 verification (constant-time compare)
        │  replay-attack prevention (timestamp window)
        ▼
EventService (src/services/event_service.py)
        │  deserialize payload → EventModel
        │  validate event structure
        │  persist to EventStore
        │  publish to Queue
        │  dispatch to EventHandler
        ▼
EventHandler (src/handlers/event_handler.py)
        │  per-event-type routing
        │  business logic
        ▼
EventStore (src/storage/event_store.py)
        │  persists events with status
        │  in-memory (swappable for DB)
        ▼
Queue Publisher (src/queue/publisher.py)
        │  publishes events for async processing
        │  in-memory (swappable for SQS, RabbitMQ)
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/api/routes.py` | FastAPI routes — receive webhook, delegate to service |
| `src/validators/signature.py` | `SignatureValidator` — HMAC-SHA256 verification + replay prevention |
| `src/events/models.py` | `WebhookEvent`, `EventType` — typed event models |
| `src/services/event_service.py` | `EventService` — orchestrates validation, storage, publishing, dispatch |
| `src/handlers/event_handler.py` | `EventHandler` — routes events to per-type handlers |
| `src/storage/event_store.py` | `EventStore` — persists events and their processing status |
| `src/queue/publisher.py` | `QueuePublisher` — publishes events for downstream async processing |
| `src/config.py` | `ServiceConfig` — typed runtime configuration |

---

## Project Structure

```text
05- Webhook Processing Service/
├── config/
│   └── settings.yaml       # Baseline configuration reference
├── scripts/
│   ├── .gitignore
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── README.md           # Scripts reference
│   └── run_service.py      # CLI entry point (Uvicorn launcher)
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── events/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── event_handler.py
│   ├── queue/
│   │   ├── __init__.py
│   │   └── publisher.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── event_service.py
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── event_store.py
│   │   └── main.py
│   └── validators/
│       ├── __init__.py
│       └── signature.py
└── tests/
    ├── __init__.py
    ├── test_event_service.py
    ├── test_handlers.py
    ├── test_routes.py
    └── test_signature.py
```

---

## Key Concepts Demonstrated

### HMAC-SHA256 Signature Verification

Every incoming webhook is validated against an HMAC-SHA256 signature computed by the sender using a shared secret. This proves the payload was not tampered with and was sent by the expected system:

```python
expected = hmac.new(
    secret.encode(),
    msg=f"{timestamp}.".encode() + payload,
    digestmod=hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(expected, received_signature):
    raise SignatureValidationError("Invalid webhook signature.")
```

**Critical:** `hmac.compare_digest()` is used for constant-time comparison. Using `==` would be vulnerable to timing attacks that leak information about the secret through response latency differences.

### Replay Attack Prevention

A timestamp header is included in the signed payload. The service rejects requests whose timestamps fall outside a configurable window (default: 300 seconds):

```python
if abs(time.time() - float(timestamp)) > self.replay_window_seconds:
    raise SignatureValidationError("Webhook timestamp is outside the replay window.")
```

Without this, an attacker who captures a valid webhook request could replay it repeatedly.

### Layered Separation

The HTTP layer (FastAPI routes) never contains signature logic, storage, or business logic. The service layer owns coordination. The validator, store, and queue are each single-responsibility components that can be tested and replaced independently:

```text
Route → validate → service → store
                 ↘ publish → queue
                 ↘ handle → business handler
```

### Event Model

Events are strongly typed using Pydantic dataclasses/models. The event type determines which handler is dispatched:

```python
class WebhookEvent:
    event_id: str
    event_type: EventType
    provider: str
    payload: dict[str, Any]
    received_at: datetime
    status: EventStatus
```

### Idempotency

Duplicate webhooks (the same `event_id`) are detected using the event store. Re-delivering the same event is a normal behavior of webhook systems — the receiver must handle it gracefully.

### In-Memory Storage and Queue

`EventStore` and `QueuePublisher` use in-memory implementations. The same interface maps directly to:
- **Database-backed store:** PostgreSQL, DynamoDB, Redis
- **Queue publisher:** AWS SQS, RabbitMQ, Kafka, Redis pub/sub

Swapping implementations does not require changing the routes or service layer.

### Queue Publishing

After persistence, events are published to the internal queue for asynchronous downstream processing. This decouples reception (fast, synchronous HTTP response) from processing (potentially slow, async handlers):

```text
Receive → store → respond 200 OK immediately
                ↓
           (async) queue → downstream processing
```

Responding immediately with `200 OK` acknowledges receipt. If the sender does not receive `200 OK`, it will retry — so storing first and then publishing preserves at-least-once delivery semantics.

---

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `webhook.signing_secret` | (required via env) | HMAC signing secret |
| `webhook.replay_window_seconds` | `300` | Max age of accepted timestamps |
| `service.host` | `127.0.0.1` | Uvicorn bind host |
| `service.port` | `8000` | Uvicorn bind port |
| `service.workers` | `1` | Uvicorn worker processes |
| `queue.max_size` | `1000` | Bound on in-memory event queue |
| `storage.max_events` | `10000` | Max events retained in store |

Environment variable overrides:

```bash
export WEBHOOK_SIGNING_SECRET="your-secret"
export WEBHOOK_REPLAY_WINDOW_SECONDS=300
export SERVICE_HOST=0.0.0.0
export SERVICE_PORT=8000
```

> **Never commit `WEBHOOK_SIGNING_SECRET` to source control.** Use environment variables or a secret manager.

---

## Requirements

- Python ≥ 3.12
- fastapi ≥ 0.115
- pydantic ≥ 2.10
- uvicorn[standard] ≥ 0.34

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running the Service

```bash
export WEBHOOK_SIGNING_SECRET="your-signing-secret"

# Via script
python scripts/run_service.py

# With overrides
python scripts/run_service.py --host 0.0.0.0 --port 8000 --workers 2

# Development mode (auto-reload)
python scripts/run_service.py --reload
```

---

## Running Tests

Tests use `httpx.AsyncClient` with a test ASGI transport — no real network calls required.

```bash
pytest
pytest --cov=src --cov-report=term-missing
pytest tests/test_signature.py

ruff check src tests scripts
mypy src
```

---

## Security Checklist

| Requirement | Implementation |
|---|---|
| Signature verified on every request | `SignatureValidator.validate()` called before any processing |
| Constant-time comparison | `hmac.compare_digest()` — not `==` |
| Replay attacks prevented | Timestamp window check in `SignatureValidator` |
| Secret never logged | Secret is not emitted in any log output |
| Secret not in source control | Supplied via `WEBHOOK_SIGNING_SECRET` env var |
| Duplicate events handled | Idempotency check in `EventStore` |

---

## Production Considerations

| Concern | Approach |
|---|---|
| Storage | Replace `EventStore` with PostgreSQL or DynamoDB-backed implementation |
| Queue | Replace `QueuePublisher` with SQS, RabbitMQ, or Kafka |
| Scalability | Uvicorn multi-worker + external persistent storage and queue |
| At-least-once delivery | Store before responding `200 OK`; make handlers idempotent |
| Observability | Add request logging, signature failure metrics, processing latency |
| Secret rotation | Webhook secret rotation requires coordination with the sending system |
| Concurrent processing | Separate the queue consumer into a dedicated worker process |

---

## Navigation

| ↳ [01](../01-%20REST%20API%20Service/README.md) | REST API Service |
| ↳ [02](../02-%20Async%20API%20Client/README.md) | Async API Client |
| ↳ [03](../03-%20Background%20Job%20System/README.md) | Background Job System |
| ↳ [04](../04-%20Concurrent%20Data%20Processor/README.md) | Concurrent Data Processor |
| ↳ [05](README.md) | Webhook Processing Service |
