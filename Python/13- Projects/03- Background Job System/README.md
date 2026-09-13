# Background Job System

A production-oriented Python background job system built entirely with `asyncio` and no external message broker. Demonstrates an in-memory job queue, concurrent async worker pool, cron-style scheduler with heap-based scheduling, persistent job store, metrics collection, and graceful shutdown.

---

## Overview

This project implements the core patterns of a background job system from scratch in Python: job definition, queuing, concurrent execution, retry logic, scheduling, persistence, and observability. It is intentionally built without Celery, Redis, or any external dependency so the mechanics of each component are fully visible.

The same architecture decisions — worker pools, visibility timeouts, retry budgets, graceful shutdown — apply when working with real message brokers (SQS, RabbitMQ, Redis) or job frameworks (Celery, ARQ, Dramatiq).

---

## Architecture

```text
Scheduler (src/scheduler/scheduler.py)
    │  heap-based scheduled job queue
    │  one-shot and recurring jobs
    │  enqueues jobs when run_at time arrives
    ▼
JobQueue (src/queue/worker.py)
    │  InMemoryJobQueue (bounded asyncio.Queue)
    │  receive / acknowledge / reject interface
    ▼
Worker Pool (src/queue/worker.py)
    │  configurable concurrency via asyncio.Semaphore
    │  dispatches jobs to registered handlers
    │  retry with exponential backoff
    │  visibility timeout (re-queues unacknowledged jobs)
    ▼
Job Handlers (src/jobs/tasks.py)
    │  per-job-type async handler functions
    │  registered by job name
    ▼
Job Store (src/storage/job_store.py)
    │  persists job state, attempts, and history
    │  in-memory implementation (swappable for DB-backed)
    ▼
Monitoring (src/monitoring/)
    │  metrics: enqueued, processed, failed, retry counts
    │  health-check reporting
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/jobs/base.py` | `Job`, `JobStatus`, `JobContext` dataclasses |
| `src/jobs/tasks.py` | Job handler registry — maps job names to async handler functions |
| `src/queue/worker.py` | `JobQueue` protocol, `InMemoryJobQueue`, `Worker`, worker pool |
| `src/scheduler/scheduler.py` | `Scheduler` — heap-based scheduling, one-shot and recurring jobs |
| `src/storage/job_store.py` | `JobStore` — persists job state and execution history |
| `src/monitoring/metrics.py` | Counter-based metrics collection |
| `src/monitoring/main.py` | Monitoring server and health-check reporting |
| `src/config.py` | `JobSystemConfig` — typed runtime configuration |

---

## Project Structure

```text
03- Background Job System/
├── config/
│   ├── .gitignore
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── settings.yaml       # Baseline configuration reference
│   └── README.md           # Configuration reference
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── tasks.py
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── metrics.py
│   ├── queue/
│   │   ├── __init__.py
│   │   └── worker.py
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── scheduler.py
│   └── storage/
│       ├── __init__.py
│       └── job_store.py
└── tests/
    ├── __init__.py
    ├── test_jobs.py
    ├── test_job_store.py
    ├── test_scheduler.py
    └── test_worker.py
```

---

## Key Concepts Demonstrated

### Job Definition

A `Job` is a dataclass carrying a name, payload, status, attempt count, and execution metadata. `JobStatus` tracks the job's lifecycle:

```text
PENDING → IN_PROGRESS → COMPLETED
                     ↘ FAILED
                     ↘ RETRYING → IN_PROGRESS
```

### Queue Protocol

`JobQueue` is a minimal async protocol with three operations:

```python
async def receive(self) -> Job | None: ...
async def acknowledge(self, job: Job) -> None: ...
async def reject(self, job: Job, *, requeue: bool) -> None: ...
```

`InMemoryJobQueue` is a bounded `asyncio.Queue`-backed implementation. The same interface can back a Redis, SQS, or RabbitMQ adapter without changing the worker.

### Concurrent Worker Pool

The worker pool runs multiple coroutines concurrently, bounded by `asyncio.Semaphore(worker_concurrency)`. Each coroutine polls the queue, dispatches the job to the registered handler, and acknowledges or rejects based on the outcome:

```text
Worker 1 ─── get job ─── run handler ─── ack
Worker 2 ─── get job ─── run handler ─── ack
Worker 3 ─── get job ─── run handler ─── reject (requeue)
Worker 4 ─── waiting for job
```

### Retry with Exponential Backoff

Failed jobs are re-queued after an exponentially increasing delay up to `max_retries`. After exhausting retries, the job moves to `FAILED` status and is not re-queued.

```text
Attempt 1: immediate
Attempt 2: wait 2s
Attempt 3: wait 4s
Attempt 4: FAILED permanently
```

### Heap-Based Scheduler

The `Scheduler` uses a min-heap to efficiently find the next job to run. One-shot and recurring jobs are both supported:

```python
# One-shot job
scheduler.schedule(
    "send_report",
    payload={"user_id": "..."},
    run_at=datetime.now(UTC) + timedelta(minutes=5),
)

# Recurring job
scheduler.schedule(
    "cleanup",
    payload={},
    run_at=datetime.now(UTC),
    interval=timedelta(hours=1),
)
```

Recurring jobs automatically schedule their next occurrence after each execution.

### Visibility Timeout

Like SQS, jobs that are dequeued but not acknowledged within a timeout window are made visible again. This protects against worker crashes dropping jobs silently.

### Job Store

`JobStore` persists job state, attempt counts, and execution history. The current implementation is in-memory. The same interface maps cleanly to a database-backed implementation (SQLite, PostgreSQL) without changing the worker or scheduler.

### Graceful Shutdown

The system handles `SIGTERM` / `SIGINT` by draining in-progress jobs before stopping, rather than killing them mid-execution.

---

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `environment` | `development` | Deployment environment name |
| `queue_url` | `memory://jobs` | Queue implementation selector |
| `worker_concurrency` | `4` | Max concurrent job executions |
| `max_retries` | `3` | Max retry attempts per job |
| `visibility_timeout_seconds` | `30` | Re-queue timeout for in-progress jobs |
| `poll_interval_seconds` | `1.0` | Worker polling frequency |
| `job_timeout_seconds` | `60` | Max execution time per job |
| `shutdown_timeout_seconds` | `30` | Max drain time during shutdown |

See [`config/README.md`](config/README.md) for the full configuration reference.

---

## Requirements

- Python ≥ 3.12
- No external dependencies (stdlib only)

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running Tests

```bash
pytest
pytest --cov=src --cov-report=term-missing

ruff check src tests
mypy src
```

---

## What This Teaches

| Pattern | Where it appears |
|---|---|
| Async worker pool | `worker.py` — `asyncio.Semaphore` bounds concurrency |
| Protocol-based queue abstraction | `JobQueue` interface separates workers from queue implementation |
| Heap-based priority scheduling | `scheduler.py` — `heapq` for efficient next-job lookup |
| Retry with exponential backoff | Worker retry loop in `worker.py` |
| Visibility timeout | Re-queue logic for unacknowledged jobs |
| Job lifecycle state machine | `JobStatus` transitions in `base.py` |
| Graceful shutdown | Signal handling and drain loop |
| In-memory persistence | `JobStore` with swappable backend interface |

---

## Production Considerations

| Concern | Approach |
|---|---|
| Persistence | Replace `InMemoryJobQueue` with SQS, Redis, or RabbitMQ adapter |
| Durability | Replace `JobStore` with a database-backed implementation |
| Dead-letter queue | Route permanently failed jobs to a separate store for inspection |
| Distributed workers | Multiple processes can consume from the same external queue |
| Idempotency | Handlers should be idempotent — visibility timeouts can cause re-delivery |
| Observability | Expose metrics from `src/monitoring/` to Prometheus, CloudWatch, or Datadog |

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
| ↳ [02](../02-%20Async%20API%20Client/README.md) | Async API Client |
| ↳ [03](README.md) | Background Job System |
| ↳ [04](../04-%20Concurrent%20Data%20Processor/README.md) | Concurrent Data Processor |
| ↳ [05](../05-%20Webhook%20Processing%20Service/README.md) | Webhook Processing Service |
