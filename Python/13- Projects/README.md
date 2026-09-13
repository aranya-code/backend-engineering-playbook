# Projects

Applied Python projects that put the patterns from the preceding sections to work in realistic, production-style backend scenarios. Each project is a self-contained Python package with a full source tree, tests, typed configuration, and either a CLI entry point or a runnable service.

---

## Projects

### [01 — REST API Service](01-%20REST%20API%20Service/README.md)

A FastAPI + SQLAlchemy + Pydantic user-management API demonstrating the service-layer, repository pattern, dependency injection, schema/domain model separation, and typed settings.

**Key skills:** FastAPI · SQLAlchemy · Pydantic v2 · service layer · repository pattern · dependency injection · typed configuration

---

### [02 — Async API Client](02-%20Async%20API%20Client/README.md)

A production-oriented async HTTP client built with `httpx`, demonstrating connection reuse, `asyncio.Semaphore` concurrency bounds, token-bucket rate limiting, exponential-backoff retry, and meaningful CLI exit codes.

**Key skills:** asyncio · httpx · bounded concurrency · token-bucket rate limiting · exponential backoff · retry classification · async context managers

---

### [03 — Background Job System](03-%20Background%20Job%20System/README.md)

A fully async background job system with no external dependencies: in-memory queue, concurrent worker pool, heap-based cron scheduler, retry with exponential backoff, job store, visibility timeouts, metrics, and graceful shutdown.

**Key skills:** asyncio worker pool · heap-based scheduler · retry + backoff · visibility timeout · job lifecycle state machine · graceful shutdown · protocol abstraction

---

### [04 — Concurrent Data Processor](04-%20Concurrent%20Data%20Processor/README.md)

A JSONL record processor that implements the same workload using all three Python concurrency models — asyncio, threading, and multiprocessing — with backpressure, atomic output, and benchmark scripts for comparing each model's performance.

**Key skills:** asyncio · ThreadPoolExecutor · ProcessPoolExecutor · GIL trade-offs · backpressure · atomic output · benchmarking concurrency models

---

### [05 — Webhook Processing Service](05-%20Webhook%20Processing%20Service/README.md)

A FastAPI webhook receiver demonstrating HMAC-SHA256 signature verification with constant-time comparison, replay-attack prevention via timestamp windows, event routing, idempotency, persistent event storage, and asynchronous queue publishing.

**Key skills:** FastAPI · HMAC-SHA256 · constant-time comparison · replay prevention · event routing · idempotency · layered architecture · queue decoupling

---
