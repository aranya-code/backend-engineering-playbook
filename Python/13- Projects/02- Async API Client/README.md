# Async API Client

A production-oriented asynchronous Python API client built with `httpx`, demonstrating bounded concurrency with `asyncio.Semaphore`, token-bucket rate limiting, exponential-backoff retry logic, typed configuration, and structured error handling.

---

## Overview

This project implements a reusable async HTTP client library for calling external REST APIs. It covers the concerns that matter when an API client runs continuously in a backend service or batch job: connection reuse, bounded concurrency, rate-limit compliance, graceful retry behavior, and correct resource lifecycle management.

It is designed as a library (`src/`) with a thin CLI entry point (`scripts/run_client.py`) that demonstrates how to wire the components together for production use.

---

## Architecture

```text
scripts/run_client.py
        │  loads config from environment
        │  creates rate limiter + client
        ▼
AsyncRateLimiter (src/rate_limiter.py)
        │  token-bucket algorithm
        │  controls outbound request rate
        ▼
AsyncAPIClient (src/client.py)
        │  asyncio.Semaphore for bounded concurrency
        │  httpx.AsyncClient for connection pooling
        │  exponential-backoff retry via RetryPolicy
        ▼
retry.py
        │  configurable retry policy
        │  classifies transient vs. permanent errors
        │  exponential backoff with optional jitter
        ▼
External HTTP API
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/client.py` | `AsyncAPIClient` — connection pool, concurrency semaphore, request execution |
| `src/retry.py` | `RetryPolicy` — exponential backoff, transient failure classification, retry budget |
| `src/rate_limiter.py` | `AsyncRateLimiter` — token-bucket rate limiting, async-safe sleep |
| `src/config.py` | `ClientConfig` — typed configuration with environment-variable loading |
| `src/exceptions.py` | `APIClientError`, `APIResponseError` — domain exceptions |
| `src/models.py` | Typed response models (Pydantic) |
| `src/main.py` | Programmatic API for running the client workflow |
| `scripts/run_client.py` | CLI entry point — thin orchestration, exit codes |

---

## Project Structure

```text
02- Async API Client/
├── config/
│   └── settings.yaml       # Baseline configuration reference
├── scripts/
│   ├── .gitignore
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── README.md           # Scripts reference
│   └── run_client.py       # CLI entry point
├── src/
│   ├── __init__.py
│   ├── client.py
│   ├── config.py
│   ├── exceptions.py
│   ├── main.py
│   ├── models.py
│   ├── rate_limiter.py
│   └── retry.py
└── tests/
    ├── __init__.py
    ├── test_client.py
    ├── test_rate_limiter.py
    └── test_retry.py
```

---

## Key Concepts Demonstrated

### Connection Reuse (async context manager)

The `AsyncAPIClient` wraps `httpx.AsyncClient` and exposes it via an async context manager. This ensures the connection pool is opened once and closed reliably — even when exceptions occur:

```python
async with AsyncAPIClient(config) as client:
    response = await client.get("/users")
```

Creating a new HTTP client for every request defeats connection pooling. Failing to close the client leaks socket resources.

### Bounded Concurrency

`asyncio.Semaphore(config.max_concurrency)` limits how many concurrent HTTP requests can be in-flight at once:

```python
async with self._semaphore:
    response = await self._client.get(url)
```

Without a semaphore, spawning hundreds of asyncio tasks for hundreds of API calls would create hundreds of simultaneous connections — potentially overwhelming the upstream API and the local connection pool.

### Token-Bucket Rate Limiting

`AsyncRateLimiter` implements a token-bucket algorithm that controls how many requests per second leave the process. It uses `await asyncio.sleep()` (never `time.sleep()`, which blocks the event loop):

```python
async with rate_limiter:
    response = await client.get("/users")
```

> **Note:** This limiter is process-local. Multiple processes or containers each run an independent instance and can collectively exceed the upstream quota. Distributed rate limiting requires a shared backend (Redis, API gateway).

### Exponential Backoff Retry

`RetryPolicy` classifies failures and retries only transient ones — with configurable exponential backoff:

```text
Attempt 1 → wait 1s
Attempt 2 → wait 2s
Attempt 3 → wait 4s
Attempt 4 → fail permanently
```

Permanent failures (`401`, `403`, `404`) are not retried. Transient failures (`429`, `500`, `502`, `503`, `504`, timeouts, connection errors) are retried up to `max_retries`.

`asyncio.CancelledError` is never swallowed — it propagates to allow graceful cancellation by parent tasks and container shutdown signals.

### Typed Configuration

`ClientConfig` is loaded from environment variables — no configuration is embedded in source code:

```bash
export API_BASE_URL="https://api.example.com"
export API_TIMEOUT_SECONDS="10"
export API_MAX_RETRIES="3"
export API_MAX_CONCURRENCY="10"
export API_RATE_LIMIT_PER_SECOND="10"
export API_KEY="..."
```

### Process Exit Codes

The CLI script uses meaningful exit codes for CI/CD integration:

| Outcome | Exit code |
|---|---:|
| Success | `0` |
| API/client failure | `1` |
| Invalid configuration | `2` |
| User interruption (Ctrl+C) | `130` |

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `API_BASE_URL` | (required) | External API base URL |
| `API_KEY` | (unset) | Bearer token or API key |
| `API_TIMEOUT_SECONDS` | `10` | Per-request timeout |
| `API_MAX_RETRIES` | `3` | Maximum retry attempts |
| `API_MAX_CONCURRENCY` | `10` | Max simultaneous in-flight requests |
| `API_RATE_LIMIT_PER_SECOND` | `10` | Max outbound requests per second |

---

## Requirements

- Python ≥ 3.12
- httpx ≥ 0.28
- pydantic ≥ 2.10

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running the Client

```bash
export API_BASE_URL="https://api.example.com"
export API_KEY="your-token"

# Via script
python scripts/run_client.py

# Via installed entry point
run-client
```

---

## Running Tests

Tests use mocked HTTP transports — no real API credentials or network access required.

```bash
pytest
pytest --cov=src --cov-report=term-missing

ruff check src tests scripts
mypy src
```

---

## Production Considerations

| Concern | Approach |
|---|---|
| Secrets | `API_KEY` via env var or secret manager — never in YAML or source |
| Timeouts | Always finite — unbounded requests block indefinitely on unhealthy upstreams |
| Retries | Bounded, with exponential backoff; permanent errors not retried |
| Idempotency | Non-idempotent POST operations need explicit idempotency keys before blind retry |
| Rate limiting | Process-local; use Redis or API gateway for distributed quota enforcement |
| Cancellation | `asyncio.CancelledError` propagates cleanly — container shutdown works correctly |
| Logging | Never log `API_KEY`, authorization headers, or sensitive response bodies |

---

## Navigation

| # | Section |
|---|---|
| [01](../01-%20Fundamentals/README.md) | Fundamentals |
| [02](../02-%20Object%20Oriented%20Programming/README.md) | Object Oriented Programming |
| [03](../03-%20Intermediate%20Python/README.md) | Intermediate Python |
| [04](../04-%20Error%20Handling/README.md) | Error Handling |
| [05](../05-%20Files%20and%20Serialization/README.md) | Files and Serialization |
| [06](../06-%20Type%20System/README.md) | Type System |
| [07](../07-%20Dataclasses%20and%20Data%20Modeling/README.md) | Dataclasses and Data Modeling |
| [08](../08-%20Concurrency%20and%20Parallelism/README.md) | Concurrency and Parallelism |
| [09](../09-%20Memory%20and%20Performance/README.md) | Memory and Performance |
| [10](../10-%20Backend%20Python/README.md) | Backend Python |
| [11](../11-%20Testing/README.md) | Testing |
| [12](../12-%20Interview%20Preparation/README.md) | Interview Preparation |
| **13** | **Projects** |
| ↳ [01](../01-%20REST%20API%20Service/README.md) | REST API Service |
| ↳ [02](README.md) | Async API Client |
| ↳ [03](../03-%20Background%20Job%20System/README.md) | Background Job System |
| ↳ [04](../04-%20Concurrent%20Data%20Processor/README.md) | Concurrent Data Processor |
| ↳ [05](../05-%20Webhook%20Processing%20Service/README.md) | Webhook Processing Service |
