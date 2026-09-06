# 03- Try Except

## Overview

Python's `try`/`except` statement is the primary mechanism for handling exceptional conditions.

In production backend systems, `try`/`except` is not simply a way to prevent application crashes. It defines where failures are interpreted, recovered, translated, logged, retried, or allowed to propagate.

A useful model is:

```text
Operation
    │
    ▼
   try
    │
    ├── success ──────────────► continue
    │
    └── exception
           │
           ▼
       except
           │
           ├── recover
           ├── translate
           ├── retry
           ├── log
           └── propagate
```

The key engineering principle is:

> Catch an exception only when the current layer can make a correct decision about that failure.

Catching an exception without a recovery strategy often makes a system less reliable because it hides the original failure.

---

## Basic Syntax

The fundamental structure is:

```python
try:
    operation()
except SomeException:
    handle_failure()
```

For example:

```python
try:
    user_id = int(raw_user_id)
except ValueError:
    user_id = None
```

Python executes the `try` block first. If an exception occurs, Python searches the associated `except` clauses for a compatible handler.

If no matching handler exists, the exception continues propagating to the caller.

---

## Runtime Flow

Conceptually:

```text
Enter try block
      │
      ▼
Execute statement
      │
      ▼
Exception raised?
   ┌──┴──┐
   │     │
  No    Yes
   │     │
   ▼     ▼
Continue Find matching except
             │
             ├── Found → execute handler
             │
             └── Not found → propagate
```

An exception interrupts normal sequential execution.

For example:

```python
def process():
    print("A")
    raise ValueError("invalid")
    print("B")


process()
```

Output:

```text
A
```

`B` is never executed because the exception transfers control away from the remaining statements in the function.

---

## Exception Matching

An `except` clause matches an exception according to its class hierarchy.

```python
try:
    raise ValueError("invalid value")
except ValueError:
    print("handled")
```

A superclass can also match:

```python
try:
    raise ValueError("invalid value")
except Exception:
    print("handled")
```

because `ValueError` inherits from `Exception`.

This is why exception hierarchy knowledge matters when writing handlers.

---

## Multiple Exception Types

A single handler can catch multiple related exception types:

```python
try:
    process_input()
except (ValueError, TypeError):
    handle_invalid_input()
```

This is appropriate when the recovery behavior is genuinely identical.

If different failures require different actions, separate handlers are clearer:

```python
try:
    process_input()
except ValueError:
    handle_value_error()
except TypeError:
    handle_type_error()
```

Avoid grouping unrelated failures merely to reduce lines of code.

---

## Exception Handler Ordering

More specific handlers should appear before broader handlers.

Correct:

```python
try:
    operation()
except ValueError:
    handle_value_error()
except Exception:
    handle_unexpected_error()
```

Incorrect:

```python
try:
    operation()
except Exception:
    handle_generic_error()
except ValueError:
    handle_value_error()
```

The second `except` is unreachable for `ValueError` because `Exception` already matches it.

A useful rule is:

```text
Most specific
     │
     ▼
Specific
     │
     ▼
General
```

---

## Catching Exception Objects

Use `as` when the exception object provides information needed for handling or logging.

```python
try:
    payload = parse_payload(raw_data)
except ValueError as exc:
    logger.warning(
        "invalid payload: %s",
        exc,
    )
```

The variable `exc` refers to the exception object.

Avoid keeping exception objects alive unnecessarily, particularly in long-lived data structures, because tracebacks can retain references to stack frames and local objects.

---

## Bare except

Python permits:

```python
try:
    operation()
except:
    handle_failure()
```

This catches exceptions derived from `BaseException`, including control-flow exceptions such as:

- `KeyboardInterrupt`
- `SystemExit`
- `GeneratorExit`

Bare `except` should almost never be used in application code.

Prefer:

```python
except Exception:
    ...
```

when a broad application-level boundary genuinely requires it.

Even then, broad catching should have a clear purpose.

---

## `Exception` vs `BaseException`

The hierarchy is approximately:

```text
BaseException
├── KeyboardInterrupt
├── SystemExit
├── GeneratorExit
└── Exception
    ├── ValueError
    ├── TypeError
    ├── RuntimeError
    ├── OSError
    ├── LookupError
    └── ...
```

Most application exceptions inherit from `Exception`.

Therefore:

```python
except Exception:
```

normally excludes process/control-flow exceptions.

Do not use:

```python
except BaseException:
```

as a general error handler.

---

## Catching Too Broadly

This pattern is dangerous:

```python
try:
    process_order(order)
except Exception:
    return None
```

It can hide:

- programming bugs
- database failures
- network failures
- invalid assumptions
- resource exhaustion
- configuration errors

The application may appear healthy while silently losing work.

A better approach is to catch known failures:

```python
try:
    process_order(order)
except InventoryUnavailable:
    return retry_later()
```

Unexpected failures should usually propagate.

---

## Handling vs Propagating

Not every exception should be handled at the point where it occurs.

Consider:

```text
PostgreSQL
    │
    ▼
Repository
    │
    ▼
Service
    │
    ▼
API
```

The repository may detect a database exception but not know whether the API should return `409`, `404`, `503`, or `500`.

The service or API boundary may have more context.

A useful principle is:

> The layer closest to the failure understands its technical cause; the higher layer may understand its business consequence.

---

## Re-Raising Exceptions

An exception can be re-raised from inside its handler:

```python
try:
    process()
except DatabaseError:
    logger.exception("database operation failed")
    raise
```

A bare:

```python
raise
```

re-raises the currently handled exception while preserving its traceback.

This is generally preferable to:

```python
raise exc
```

when the intention is simply to propagate the same exception.

---

## `raise` vs `raise exc`

Compare:

```python
try:
    operation()
except ValueError:
    raise
```

with:

```python
try:
    operation()
except ValueError as exc:
    raise exc
```

Both propagate the exception, but bare `raise` is the idiomatic mechanism for re-raising the currently handled exception and preserves the original traceback context more directly.

Use:

```python
raise
```

when no translation is needed.

Use:

```python
raise NewError(...) from exc
```

when changing the abstraction.

---

## Translating Exceptions

A lower-level exception can be translated into an application-specific exception.

```python
try:
    repository.save(order)
except DatabaseError as exc:
    raise OrderPersistenceError(
        "Unable to persist order"
    ) from exc
```

The flow becomes:

```text
DatabaseError
     │
     ▼
Repository
     │
     ▼
OrderPersistenceError
     │
     ▼
Service
```

This reduces coupling between business logic and infrastructure-specific exception classes.

---

## Recovery

An exception handler should normally have a defined recovery action.

```python
try:
    cache.get(key)
except CacheUnavailable:
    return load_from_database()
```

This is meaningful because the handler knows what to do.

Compare with:

```python
try:
    cache.get(key)
except Exception:
    pass
```

This does not define meaningful recovery and can hide serious failures.

---

## Default Values

Exceptions can sometimes be used to fall back to a safe default.

```python
try:
    timeout = int(config["TIMEOUT"])
except (KeyError, ValueError):
    timeout = 5
```

This is appropriate only when a default is genuinely valid.

For configuration that is required for safe operation, failing fast is often better:

```python
try:
    timeout = int(config["TIMEOUT"])
except (KeyError, ValueError) as exc:
    raise ConfigurationError(
        "TIMEOUT must be configured as an integer"
    ) from exc
```

Configuration errors should generally be detected during startup rather than after serving traffic.

---

## Validation

`try`/`except` is useful when an operation naturally reports invalid input through exceptions.

```python
def parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("PORT must be an integer") from exc

    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535")

    return port
```

The distinction is important:

```text
Parsing failure
    │
    ▼
Exception


Business validation
    │
    ▼
Explicit condition
```

Not every validation rule needs exceptions internally.

---

## File Handling

Exceptions are common when interacting with the filesystem.

```python
from pathlib import Path


def load_config(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"Configuration file not found: {path}"
        ) from exc
```

The application translates an OS-level failure into a domain-level configuration failure.

For sensitive systems, avoid exposing filesystem paths to external clients.

---

## Database Operations

Database operations commonly raise driver or ORM-specific exceptions.

```python
try:
    repository.create_order(order)
except UniqueConstraintError as exc:
    raise OrderAlreadyExists(
        order.id
    ) from exc
```

The service layer should normally depend on application semantics rather than a specific database driver's exception hierarchy.

```text
PostgreSQL / driver
        │
        ▼
Repository
        │
        ▼
Application exception
        │
        ▼
Service
```

This improves portability and testability.

---

## Transaction Boundaries

Exception handling and transactions must be designed together.

```python
def create_order(order):
    with transaction():
        repository.insert(order)
        inventory.reserve(order)
        audit.record(order)
```

If an exception occurs:

```text
BEGIN
  │
  ├── Insert order
  ├── Reserve inventory
  ├── Record audit
  │
  └── exception
        │
        ▼
     ROLLBACK
```

Do not catch an exception inside a transaction merely to continue if the transaction can no longer safely continue.

The exact transaction semantics depend on the database and framework.

---

## Network Failures

Network calls can fail because of:

- connection timeout
- DNS failure
- connection reset
- TLS failure
- remote service error
- rate limiting
- malformed response

A handler should distinguish transient failures from permanent failures.

```python
try:
    response = payment_client.charge(payment)
except PaymentTimeout as exc:
    raise PaymentTemporarilyUnavailable(
        "Payment provider timed out"
    ) from exc
```

Whether the caller retries depends on:

- idempotency
- timeout budget
- provider semantics
- retry policy
- operation state

---

## Retry with try/except

A simple retry loop can be implemented with `try`/`except`:

```python
import time


def call_with_retry(operation, attempts: int = 3):
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except TemporaryError:
            if attempt == attempts:
                raise

            time.sleep(2 ** (attempt - 1))
```

Production retry mechanisms should additionally consider:

- jitter
- total time budget
- cancellation
- idempotency
- rate limits
- circuit breakers
- observability

Do not place arbitrary retry loops around every `try` block.

---

## HTTP API Handling

FastAPI applications commonly translate exceptions at the API boundary.

Conceptually:

```text
Service
   │
   ▼
Application exception
   │
   ▼
FastAPI exception handler
   │
   ▼
HTTP response
```

For example:

```python
from fastapi import HTTPException


def get_order(order_id: int):
    try:
        return service.get_order(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        ) from exc
```

In larger applications, centralized exception handlers are often preferable to repeating this mapping in every endpoint.

---

## Django Error Handling

Django applications may use exceptions across:

- views
- services
- ORM operations
- middleware
- management commands
- background tasks

The same principle applies:

```text
Low-level exception
       │
       ▼
Application/domain exception
       │
       ▼
Django boundary
       │
       ▼
HTTP response / logging
```

Django's built-in exception handling should generally be extended through established framework mechanisms rather than bypassed with arbitrary global `try`/`except` blocks.

---

## Async Exception Handling

`try`/`except` works inside `async def` functions:

```python
async def process_order():
    try:
        await payment_client.charge()
    except PaymentTimeout:
        await schedule_retry()
```

The important difference is that asynchronous operations can also be cancelled.

Do not accidentally suppress cancellation with an overly broad handler.

Prefer handling known application failures and allowing unrelated exceptions to propagate.

---

## Exceptions in Tasks

When using `asyncio` tasks:

```python
task = asyncio.create_task(process_order())
```

the task may fail independently of the code that created it.

The application must ensure that task exceptions are observed and handled appropriately.

For concurrent operations:

```python
results = await asyncio.gather(
    operation_a(),
    operation_b(),
)
```

an exception can affect the overall gathering operation.

Failure behavior should therefore be designed together with task lifecycle and cancellation behavior.

---

## Background Jobs

For Celery or similar systems:

```python
try:
    process_message(message)
except TemporaryDependencyError:
    raise
```

Allowing the worker/task system to observe the exception may be necessary for its configured retry behavior.

Swallowing the exception:

```python
try:
    process_message(message)
except Exception:
    pass
```

can incorrectly make the task appear successful.

This may cause:

- lost work
- incorrect acknowledgements
- missing retries
- silent data inconsistencies

---

## Kafka Consumers

Kafka consumers require similar care.

```python
try:
    process_event(event)
except TemporaryDatabaseError:
    raise
```

Whether the message is retried or the offset is committed depends on the consumer architecture.

A broad handler that logs and continues can cause the system to move past an event that was never successfully processed.

Error handling must therefore align with offset-management semantics.

---

## Logging Exceptions

Use `logger.exception()` when logging a currently handled exception and its traceback:

```python
try:
    process_order(order)
except OrderError:
    logger.exception(
        "order processing failed",
        extra={"order_id": order.id},
    )
    raise
```

Avoid:

```python
except Exception as exc:
    logger.error(str(exc))
```

when the traceback is needed.

Also avoid logging the same exception at every layer. A useful approach is:

```text
Lower layer
    └── translate/enrich

Boundary
    └── log + observe

External response
    └── safe error contract
```

---

## Security Considerations

Exception messages can contain sensitive information.

Avoid returning raw exception text:

```python
return {"error": str(exc)}
```

when the exception may contain:

- SQL
- database URLs
- filesystem paths
- credentials
- internal hostnames
- stack information

Instead, expose a controlled error:

```python
return {
    "error": {
        "code": "DEPENDENCY_UNAVAILABLE",
        "message": "The service is temporarily unavailable",
    }
}
```

Keep detailed diagnostics in protected observability systems.

---

## Exception Handling and Secrets

Never log secrets merely because an exception occurred.

Bad:

```python
logger.exception(
    "request failed: headers=%s",
    request.headers,
)
```

The headers may contain:

```text
Authorization
Cookie
API-Key
```

Exception logging should follow the same data-classification and redaction policies as ordinary application logging.

---

## Performance

Exception handling itself is not generally expensive when no exception occurs because Python does not execute the handler body.

Actual exception paths can be more expensive due to:

- exception object creation
- traceback construction
- stack unwinding
- logging
- serialization
- monitoring/reporting

Therefore, avoid designing high-frequency ordinary outcomes around exceptions unnecessarily.

Prefer:

```python
value = mapping.get(key)
```

over using `KeyError` as the normal lookup mechanism when absence is expected and `.get()` expresses the desired semantics.

---

## Exception Frequency

A useful distinction is:

```text
Expected business outcome
        │
        └── explicit return/result


Unexpected or exceptional condition
        │
        └── exception
```

For example:

```python
user = repository.find(user_id)

if user is None:
    return None
```

may be more appropriate than using an exception for every normal "not found" lookup, depending on the repository contract.

However, a domain operation where absence is inherently invalid may reasonably raise a domain exception.

The correct choice is semantic, not merely performance-driven.

---

## Memory and Tracebacks

Exceptions can carry tracebacks containing frame references.

A traceback may indirectly retain local variables:

```text
Exception
   │
   ▼
Traceback
   │
   ▼
Frame
   │
   └── local variables
```

Retaining exceptions in long-lived structures can therefore retain more memory than expected.

Avoid storing full exception objects indefinitely unless there is a deliberate diagnostic requirement.

---

## Nested try/except

Nested handlers can be appropriate when different operations have different recovery policies:

```python
try:
    try:
        payload = load_payload()
    except PayloadError:
        payload = recover_payload()

    save(payload)
except DatabaseError:
    rollback()
    raise
```

However, deeply nested exception handling often indicates that the function is performing too many responsibilities.

Prefer extracting operations into smaller functions when error boundaries become difficult to understand.

---

## `try` Scope

Keep the `try` block as small as practical.

Prefer:

```python
try:
    result = repository.save(order)
except DatabaseError as exc:
    raise OrderPersistenceError from exc

publish_event(result)
```

over:

```python
try:
    result = repository.save(order)
    publish_event(result)
    send_notification(result)
    update_metrics(result)
except Exception:
    ...
```

The larger the `try` block, the greater the chance of accidentally handling an exception from unrelated code.

A narrow `try` block makes the intended failure boundary explicit.

---

## Avoiding Accidental Exception Capture

Consider:

```python
try:
    result = calculate()
    audit(result)
except ValueError:
    fallback()
```

If both `calculate()` and `audit()` can raise `ValueError`, the handler cannot distinguish the source.

A narrower design is:

```python
try:
    result = calculate()
except ValueError:
    result = fallback()

audit(result)
```

This improves correctness because the exception handler corresponds to a specific operation.

---

## Cleanup with finally

When cleanup must happen regardless of success:

```python
resource = acquire()

try:
    use(resource)
except ResourceError:
    recover()
finally:
    resource.close()
```

For reusable resource management, prefer a context manager:

```python
with acquire_resource() as resource:
    use(resource)
```

`try`/`except` and context managers complement each other rather than competing.

---

## `try` and `else`

The `else` block runs only when the `try` block completes successfully.

```python
try:
    result = parse_request()
except ValueError:
    reject_request()
else:
    persist(result)
```

This can be useful when the operation that may fail should remain separate from code that should execute only after success.

It also prevents unrelated exceptions from accidentally being caught.

---

## Handling Multiple Failure Domains

Consider an API request:

```text
HTTP request
     │
     ▼
Parse input
     │
     ▼
Validate domain
     │
     ▼
Database
     │
     ▼
Publish event
```

Each operation can have a different failure policy.

```python
try:
    payload = parse_payload(raw_body)
except ValueError as exc:
    raise InvalidRequest("Malformed payload") from exc

try:
    order = repository.create(payload)
except UniqueConstraintError as exc:
    raise OrderAlreadyExists from exc

publish_order_created(order)
```

This is usually preferable to one broad handler covering the entire request.

---

## Exception Boundaries in Microservices

A microservice should generally establish clear boundaries:

```text
External dependency
        │
        ▼
Infrastructure exception
        │
        ▼
Adapter / repository
        │
        ▼
Application exception
        │
        ▼
API / worker boundary
        │
        ▼
External contract
```

This prevents infrastructure-specific errors from leaking throughout the application.

For example, the service should not need to know every exception class emitted by a PostgreSQL driver, Redis client, or HTTP library.

---

## Reliability Considerations

Reliable exception handling should answer:

- What happens when the operation fails?
- Is the failure retryable?
- Is the operation idempotent?
- Has a partial side effect occurred?
- Does the transaction roll back?
- Can the request safely be repeated?
- Will the worker acknowledge the message?
- Is the failure observable?
- Does the client receive a stable response?
- What happens after process restart?

Exception handling is therefore tightly connected to system reliability.

---

## High Availability

In a highly available backend:

```text
Load Balancer
     │
 ┌───┼────┐
 ▼   ▼    ▼
Pod Pod  Pod
 │   │    │
 └───┼────┘
     ▼
 Shared infrastructure
```

Each process can fail independently.

Exception handling should therefore avoid relying on:

- process-local state
- local caches for durable decisions
- local queues for critical work
- in-memory retry state for durable workflows

Critical state should be stored in appropriate durable infrastructure.

---

## Kubernetes and Process Lifecycle

Kubernetes may terminate application processes during deployments or scaling.

Exception handling should not interfere with graceful shutdown.

The application should distinguish between:

```text
Application error
      │
      ▼
Recover / propagate


Process termination
      │
      ▼
Graceful shutdown
```

Do not use broad exception handling to suppress shutdown signals or lifecycle-related control flow.

---

## Common Mistakes

| Mistake | Problem | Better Practice |
|---|---|---|
| `except:` | Catches control-flow exceptions | Catch specific exceptions |
| `except Exception` everywhere | Hides defects | Catch narrowly |
| Empty handler | Silent failure | Handle or propagate intentionally |
| Huge `try` block | Captures unrelated failures | Keep scope narrow |
| Re-raising with generic error | Loses semantic clarity | Translate deliberately |
| Logging only `str(exc)` | Loses traceback | Use appropriate traceback logging |
| Returning raw exception text | Information leakage | Stable external error contract |
| Retrying every exception | Outage amplification | Retry only safe transient failures |
| Swallowing worker exceptions | Lost jobs | Align with worker semantics |
| Catching `BaseException` | Breaks control flow | Usually catch `Exception` |
| Retaining exceptions | Potential memory retention | Release transient exception state |

---

## Production Pitfalls

### Catching Too Early

A repository should not necessarily decide the HTTP response.

### Catching Too Late

An API boundary that allows infrastructure-specific exceptions to escape may expose unstable implementation details.

### Logging at Every Layer

This can produce duplicate alerts and noisy logs.

### Converting Everything to `500`

Known validation, conflict, authentication, and dependency failures should have appropriate semantics.

### Retrying Inside Generic Handlers

This can accidentally retry permanent errors.

### Ignoring Partial Success

A timeout after an external side effect creates an ambiguous state.

### Hiding Programming Bugs

A broad handler can make broken code appear operationally healthy.

---

## Testing Exception Paths

Exception paths should be tested explicitly.

With pytest:

```python
import pytest


def test_invalid_order_raises():
    with pytest.raises(InvalidOrderStateError):
        service.cancel(order)
```

Test the application contract, including:

- exception type
- meaningful attributes
- chained cause
- rollback
- cleanup
- retry behavior
- logging where appropriate
- API response mapping

Do not over-test Python's built-in exception implementation.

---

## Testing Exception Chaining

When translation is part of the contract:

```python
def test_repository_error_preserves_cause():
    with pytest.raises(OrderPersistenceError) as exc_info:
        service.create_order(order)

    assert isinstance(
        exc_info.value.__cause__,
        DatabaseError,
    )
```

This verifies that the higher-level error preserves the original failure.

---

## Testing Cleanup

Resource cleanup should be verified under both success and failure.

```python
def test_resource_is_closed_after_failure():
    resource = FakeResource()

    with pytest.raises(ValueError):
        use_resource(resource)

    assert resource.closed
```

Context managers often simplify these tests by centralizing lifecycle behavior.

---

## Interview Traps

### Does `except Exception` Catch Everything?

No.

It does not normally catch exceptions directly derived from `BaseException`, such as `KeyboardInterrupt` and `SystemExit`.

### What Happens When No Handler Matches?

The exception continues propagating up the call stack.

### Which `except` Runs?

The first matching handler is selected.

### Why Keep `try` Blocks Small?

To prevent unrelated exceptions from being accidentally handled.

### What Does Bare `raise` Do?

It re-raises the currently handled exception.

### Should Every Exception Be Caught?

No. Unhandled exceptions can be the correct behavior when the current layer cannot recover.

### Why Use Custom Exceptions?

To establish meaningful application-level contracts and reduce coupling to implementation-specific failures.

### Why Is `except Exception: pass` Dangerous?

It hides failures and can make data loss or service degradation invisible.

### Are Exceptions Expensive?

The exceptional path has non-trivial cost because Python creates exception state and traceback information, but the larger concern is usually incorrect control-flow design rather than micro-optimizing exception syntax.

---

## Senior Engineering Heuristics

When reviewing a `try`/`except` block, ask:

1. What exact operation can fail?
2. Is the `try` block unnecessarily large?
3. Which exception types are actually expected?
4. Can the current layer recover correctly?
5. Should the exception propagate?
6. Should it be translated into a domain exception?
7. Should the original cause be preserved?
8. Is retry safe?
9. Could the operation have partially succeeded?
10. What happens to the database transaction?
11. What happens to external side effects?
12. Will a worker acknowledge the failed operation?
13. Is the error observable?
14. Could the handler expose sensitive information?
15. Could broad handling hide programming defects?
16. Does the exception path behave correctly under asyncio, threads, processes, and container restarts?
17. Is the resulting external API or event contract stable?

A high-quality exception handler is usually small, explicit, and semantically justified.

---

## Production Checklist

Before merging exception-handling code, verify:

- The `try` block is as narrow as practical.
- Exceptions are caught by type rather than broadly by default.
- `BaseException` is not being caught unnecessarily.
- Expected failures have defined recovery behavior.
- Unexpected failures are allowed to propagate.
- Translated exceptions preserve the original cause when useful.
- Retry behavior is explicit and bounded.
- Retried operations are safe or idempotent.
- Transaction boundaries are correct.
- Resources are cleaned up through `finally` or context managers.
- Background-worker behavior matches acknowledgement and retry semantics.
- API responses do not expose internal exception details.
- Logs include useful context without secrets.
- Tracebacks are retained where needed for diagnosis.
- Tests cover important exception paths.
- Error metrics and alerts distinguish meaningful failure categories.
- Shutdown and cancellation behavior are not accidentally suppressed.
- Exception handling does not hide programming defects.

## Key Takeaways

- `try`/`except` defines an exception boundary; keep the `try` block narrow and catch only failures the current layer can meaningfully handle.
- Prefer specific exception types and deliberate handling, translation, retry, or propagation over broad handlers such as `except Exception: pass`.
- Use bare `raise` to propagate the current exception and `raise ... from exc` when translating an infrastructure failure into a higher-level application error.
- Exception handling must align with transactions, retries, idempotency, async tasks, Celery/Kafka delivery semantics, API contracts, and resource cleanup.
- Production-grade `try`/`except` code preserves failure visibility: detailed internal diagnostics, safe external responses, explicit recovery behavior, and no accidental suppression of programming or lifecycle errors.