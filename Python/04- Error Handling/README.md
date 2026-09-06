# README

## Overview

The `04- Error Handling` section covers how Python applications detect, classify, propagate, translate, recover from, and expose failures.

Production backend systems cannot treat exceptions as isolated language features. Failures cross architectural boundaries:

```text
HTTP Request
     │
     ▼
API Layer
     │
     ▼
Service Layer
     │
     ▼
Repository / Adapter
     │
     ▼
PostgreSQL / Redis / Kafka / External API
```

An error originating in PostgreSQL may become a repository exception, then an application-level exception, and finally an HTTP `409`, `503`, or `500` response.

The goal of this section is to build a consistent failure model across those boundaries.

---

## What This Section Covers

The section progresses from Python exception semantics to production resilience patterns:

```text
Exception Fundamentals
        │
        ▼
Exception Hierarchy
        │
        ▼
try / except
        │
        ▼
else / finally
        │
        ▼
raise
        │
        ▼
Custom Exceptions
        │
        ▼
Exception Chaining
        │
        ▼
Exception Handling Patterns
        │
        ▼
Retry and Recovery
        │
        ▼
Error Handling in APIs
```

| # | File | Focus |
|---|---|---|
| 01 | [Exception Fundamentals](01-%20Exception%20Fundamentals.md) | Exception semantics, failure vs normal control flow, and basic exception behavior |
| 02 | [Exception Hierarchy](02-%20Exception%20Hierarchy.md) | Built-in exception hierarchy, inheritance, and selecting appropriate exception types |
| 03 | [Try Except](03-%20Try%20Except.md) | `try`, `except`, matching rules, propagation, and practical handling |
| 04 | [Else and Finally](04-%20Else%20and%20Finally.md) | Successful execution paths, cleanup, and `finally` semantics |
| 05 | [Raising Exceptions](05-%20Raising%20Exceptions.md) | `raise`, re-raising, explicit exceptions, and failure contracts |
| 06 | [Custom Exceptions](06-%20Custom%20Exceptions.md) | Application/domain exceptions and structured failure models |
| 07 | [Exception Chaining](07-%20Exception%20Chaining.md) | `__cause__`, `__context__`, translation, and preserving failure causality |
| 08 | [Exception Handling Patterns](08-%20Exception%20Handling%20Patterns.md) | Reusable handling, translation, recovery, fallback, and boundary patterns |
| 09 | [Retry and Recovery](09-%20Retry%20and%20Recovery.md) | Transient failures, retries, backoff, idempotency, recovery, and resilience |
| 10 | [Error Handling in APIs](10-%20Error%20Handling%20in%20APIs.md) | HTTP error contracts, status codes, error mapping, security, and observability |

---

## Core Mental Model

Exception handling should answer five questions:

```text
1. What failed?
2. Is the failure expected?
3. Can this layer recover?
4. Should the failure be translated?
5. Who owns the final response or recovery decision?
```

A useful architectural model is:

```text
Infrastructure Failure
        │
        ▼
Technical Exception
        │
        ▼
Repository / Adapter
        │
        ├── propagate
        └── translate
                │
                ▼
        Application Exception
                │
                ▼
           Service Layer
                │
                ├── recover
                ├── retry
                └── propagate
                        │
                        ▼
                  API Boundary
                        │
                        ▼
                HTTP / gRPC Error
```

The most important principle is:

> Catch an exception only when the current layer has enough context to make a correct decision.

---

## Exception Categories

Backend applications commonly encounter several categories of failure.

| Category | Example | Typical handling |
|---|---|---|
| Input failure | Invalid JSON | Reject |
| Validation failure | Invalid quantity | Return validation error |
| Domain failure | Invalid state transition | Raise domain exception |
| Resource failure | Order not found | Translate to application error |
| Infrastructure failure | Database unavailable | Translate or propagate |
| Transient failure | Network timeout | Retry when safe |
| Authentication failure | Invalid credentials | Fail immediately |
| Authorization failure | Permission denied | Fail safely |
| Programming error | `AttributeError` | Fail, diagnose, fix |
| Data corruption | Invalid persisted state | Fail fast + alert |
| Ambiguous outcome | Payment timeout | Reconcile |
| Distributed failure | Kafka processing failure | Retry/DLQ/compensate |

This classification determines recovery behavior.

---

## Exception Hierarchy

Python exceptions are objects organized through inheritance.

A simplified structure is:

```text
BaseException
├── SystemExit
├── KeyboardInterrupt
├── GeneratorExit
└── Exception
    ├── ValueError
    ├── TypeError
    ├── LookupError
    ├── OSError
    │   ├── ConnectionError
    │   └── TimeoutError
    └── RuntimeError
```

Application exceptions normally inherit from `Exception`:

```python
class OrderError(Exception):
    """Base exception for order-related failures."""
```

A meaningful hierarchy allows callers to handle failures at different levels of specificity.

---

## Catch Specific Exceptions

Prefer:

```python
try:
    repository.get(order_id)
except OrderNotFoundError:
    return None
```

over:

```python
try:
    repository.get(order_id)
except Exception:
    return None
```

Broad handlers can hide:

- programming bugs
- infrastructure outages
- invalid configuration
- serialization errors
- security failures
- unexpected application state

The narrower the handler, the easier it is to reason about the recovery behavior.

---

## Propagation

An exception does not need to be handled where it occurs.

```text
Repository
    │
    ▼
Exception
    │
    ▼
Service
    │
    ▼
API boundary
```

For example:

```python
def get_order(order_id: int):
    return repository.get(order_id)
```

If the service cannot recover from the failure, allowing the exception to propagate is often correct.

The API layer may have enough context to map it to a protocol response.

---

## Exception Translation

Infrastructure exceptions should not unnecessarily leak through application boundaries.

```python
try:
    database.insert(order)
except DatabaseError as exc:
    raise OrderPersistenceError(order.id) from exc
```

This creates:

```text
DatabaseError
      │
      ▼
OrderPersistenceError
      │
      ▼
Service
```

The service now depends on application semantics rather than a particular database driver.

Translate when the abstraction or semantic meaning changes.

---

## Exception Chaining

When translating an exception, preserve the cause:

```python
try:
    repository.save(order)
except DatabaseError as exc:
    raise OrderPersistenceError(order.id) from exc
```

This gives both:

```text
application-level meaning
```

and:

```text
underlying diagnostic cause
```

Exception chaining is especially valuable for:

- debugging
- logging
- observability
- infrastructure abstraction
- incident analysis

---

## Recovery

Recovery means restoring useful behavior after failure.

Examples:

```text
Redis unavailable
      │
      ▼
PostgreSQL fallback
```

or:

```text
Email provider unavailable
      │
      ▼
Queue email for later
```

Recovery is appropriate only when the alternative path preserves acceptable correctness, latency, and capacity.

---

## Retry

Retry repeats an operation after a potentially transient failure.

```text
Attempt 1
   │
   └── failure
          │
          ▼
      backoff
          │
          ▼
Attempt 2
   │
   └── success
```

Production retry policies should consider:

- failure classification
- idempotency
- timeout
- maximum attempts
- maximum elapsed time
- backoff
- jitter
- dependency capacity

Never use retries as a generic response to every exception.

---

## Idempotency

Retries can duplicate side effects.

For example:

```text
POST /payments
      │
      ▼
Payment succeeds
      │
      ▼
Response lost
      │
      ▼
Client retries
```

The payment may already have been processed.

Idempotency keys allow the server to recognize repeated requests:

```http
Idempotency-Key: payment-123
```

This is essential for safely retrying many side-effecting operations.

---

## API Error Handling

Internal exceptions should be mapped to stable external contracts.

```text
OrderNotFoundError
       │
       ▼
HTTP 404
```

Example:

```json
{
  "error": {
    "code": "ORDER_NOT_FOUND",
    "message": "Order not found",
    "request_id": "req_123"
  }
}
```

Clients should depend on:

- HTTP status
- stable error codes
- documented response schemas

They should not depend on Python exception names or human-readable messages.

---

## HTTP Error Mapping

A typical mapping is:

| Internal condition | HTTP status |
|---|---:|
| Malformed request | `400` |
| Validation failure | `400` / `422` |
| Authentication failure | `401` |
| Authorization failure | `403` |
| Resource missing | `404` |
| Conflict | `409` |
| Rate limit | `429` |
| Dependency unavailable | `502` / `503` |
| Upstream timeout | `504` |
| Unexpected application failure | `500` |

The application-specific error code provides more precise semantics.

For example:

```text
409
├── ORDER_ALREADY_EXISTS
├── ORDER_STATE_CONFLICT
└── VERSION_CONFLICT
```

---

## Error Handling Boundaries

A mature Python backend typically has several deliberate error boundaries.

### Repository Boundary

Handles technical persistence failures.

```text
PostgreSQL
    │
    ▼
Database exception
    │
    ▼
Repository exception
```

### Service Boundary

Handles domain semantics.

```text
Repository
    │
    ▼
Domain rule
    │
    ▼
Business exception
```

### API Boundary

Handles protocol translation.

```text
Application exception
    │
    ▼
HTTP / gRPC response
```

### Worker Boundary

Handles asynchronous execution semantics.

```text
Task failure
    │
    ├── retry
    ├── permanent failure
    └── dead-letter
```

---

## Failure Handling and Transactions

Exceptions and transactions must be designed together.

A database transaction should not remain in an invalid state after a failure.

Conceptually:

```text
BEGIN
  │
  ├── operation A
  ├── operation B
  └── operation C
       │
       └── failure
             │
             ▼
          ROLLBACK
```

When a transaction is retryable, retry the transaction as a unit rather than arbitrary individual statements.

This is particularly important for PostgreSQL serialization failures and deadlocks.

---

## Failure Handling in Redis

Redis may be used for:

- caching
- sessions
- distributed locks
- rate limiting
- queues
- application state

The correct failure strategy depends on the role.

For an optional cache:

```text
Redis unavailable
      │
      ▼
Database fallback
```

For critical state:

```text
Redis unavailable
      │
      ▼
Controlled failure
```

Never assume that every Redis failure can safely be treated as a cache miss.

---

## Failure Handling in Kafka

Kafka consumers require explicit failure semantics:

```text
Message
   │
   ▼
Consumer
   │
   ├── success → commit
   │
   ├── transient → retry
   │
   └── permanent → DLQ
```

Important concerns include:

- offset commits
- duplicate delivery
- idempotency
- retry topics
- dead-letter topics
- poison messages
- partition ordering

An exception handler must not accidentally acknowledge an event that failed processing.

---

## Failure Handling in Celery

Background tasks have different retry requirements from HTTP requests.

```text
Celery Task
    │
    ├── transient dependency failure
    │       └── retry
    │
    ├── permanent business failure
    │       └── record failure
    │
    └── unexpected exception
            └── fail + alert
```

Retries must account for duplicate execution because a worker can fail after performing a side effect but before acknowledging the task.

---

## Distributed Systems

Distributed failures are often ambiguous.

A timeout can mean:

```text
Operation definitely failed
```

or:

```text
Operation succeeded but response was lost
```

Therefore:

```text
timeout
   │
   ▼
unknown state
   │
   ├── query status
   ├── use idempotency key
   ├── reconcile
   └── compensate if necessary
```

This is more important than simply catching `TimeoutError`.

---

## Observability

Exception handling should integrate with:

- structured logging
- metrics
- distributed tracing
- request IDs
- alerts

A useful failure event might contain:

```json
{
  "event": "request_failed",
  "request_id": "req_123",
  "error_code": "DEPENDENCY_UNAVAILABLE",
  "status_code": 503,
  "route": "/orders/{order_id}",
  "dependency": "inventory-service"
}
```

Do not log sensitive request data by default.

---

## Security

Error responses are part of the application's security boundary.

Never expose:

- stack traces
- SQL statements
- credentials
- tokens
- filesystem paths
- internal hostnames
- database connection details
- sensitive user data

Use:

```text
Detailed exception
    → controlled logs/traces

Safe error contract
    → client
```

Authentication and authorization failures should also avoid unnecessarily revealing protected information.

---

## Performance

Exception handling has several performance implications.

The major operational costs usually come from:

- retries
- fallback requests
- excessive logging
- database recovery traffic
- large error payloads
- repeated serialization
- excessive traceback retention

A retry policy should therefore be evaluated as a load-management mechanism, not merely as an availability feature.

---

## Scalability and Reliability

At scale, one failed dependency can affect thousands of requests.

Consider:

```text
Cache outage
     │
     ▼
Database fallback
     │
     ▼
Database overload
     │
     ▼
Database timeout
     │
     ▼
API error spike
```

Resilience mechanisms should therefore work together:

```text
Timeouts
   +
Bounded retries
   +
Backoff + jitter
   +
Circuit breakers
   +
Bulkheads
   +
Fallbacks
   +
Idempotency
```

Each mechanism addresses a different failure mode.

---

## Common Mistakes

### Catching `Exception` Everywhere

Broad exception handling can hide defects.

### Returning Success After Logging an Error

Logging a failure does not make the operation successful.

### Retrying Non-Idempotent Operations

A retry can duplicate external side effects.

### Retrying at Every Layer

Nested retries can multiply dependency traffic dramatically.

### Returning Raw Exception Messages

This leaks implementation details and can create security vulnerabilities.

### Logging Every Exception at Every Layer

This creates duplicate logs and noisy alerts.

### Treating Timeout as Failure Certainty

The remote operation may have succeeded.

### Using Fallbacks Without Capacity Planning

A fallback can overload the secondary dependency.

### Treating DLQs as Permanent Storage

DLQs require ownership, monitoring, retention, and replay procedures.

---

## Engineering Decision Framework

When an exception occurs, reason through the following sequence:

```text
Exception occurs
      │
      ▼
Is it expected?
      │
      ├── No ──► Propagate / fail
      │
      ▼
Can this layer recover?
      │
      ├── Yes ──► Recover / fallback
      │
      ▼
Does the abstraction change?
      │
      ├── Yes ──► Translate + chain
      │
      ▼
Is it transient?
      │
      ├── Yes ──► Check retry safety
      │
      ▼
Is the operation idempotent?
      │
      ├── Yes ──► Retry within budget
      │
      └── No ──► Reconcile / fail safely
```

This framework is more useful than memorizing individual exception classes.

---

## Recommended Architecture

A production Python backend should generally follow:

```text
                    ┌─────────────────────┐
                    │      Client         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ API / gRPC Boundary │
                    │ Error Mapping       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Service Layer     │
                    │ Domain Decisions    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Repository / Client │
                    │ Technical Errors    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
         PostgreSQL          Redis           External API
```

The architecture should make failure ownership explicit.

---

## Production Checklist

Before considering error handling production-ready, verify:

- Exceptions are classified according to meaningful failure semantics.
- Handlers catch specific exception types.
- `try` blocks are kept narrow.
- Exceptions are propagated when the current layer cannot recover.
- Infrastructure exceptions are translated at appropriate boundaries.
- Exception causes are preserved when translating.
- Domain exceptions remain transport-neutral.
- Retries are bounded by attempts and deadlines.
- Backoff and jitter are used where appropriate.
- Retry ownership is explicit.
- Side-effecting operations are idempotent or reconciled.
- Database transactions roll back correctly.
- Fallback paths have capacity limits.
- Circuit breakers and bulkheads are considered for unstable dependencies.
- API errors use stable HTTP and application-level semantics.
- Raw exceptions and tracebacks are never exposed externally.
- Request IDs and traces connect failures across services.
- Logs do not contain secrets or unnecessary sensitive data.
- Kafka failures have retry/DLQ semantics.
- Celery tasks account for duplicate execution.
- Async cancellation is not accidentally swallowed.
- Exception behavior is covered by automated tests.
- Operational metrics distinguish expected errors from service failures.

## Key Takeaways

- Exception handling is an architectural concern: classify failures, handle them where there is enough context, and propagate them when recovery is not the current layer's responsibility.
- Keep domain and application exceptions separate from transport and infrastructure details, translating failures at deliberate boundaries while preserving their causes.
- Retries require transient failures, bounded deadlines, backoff, and safe/idempotent operations; ambiguous outcomes require reconciliation rather than blind repetition.
- API error contracts should expose stable status codes and application error codes while keeping internal diagnostics, stack traces, and sensitive information private.
- Reliable Python backends combine exception handling with transactions, retries, idempotency, fallbacks, observability, concurrency controls, queues, and distributed-system recovery strategies.