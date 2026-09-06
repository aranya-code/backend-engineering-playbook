# 04- Else and Finally

## Overview

Python's `else` and `finally` clauses extend `try`/`except` by separating successful execution from cleanup that must happen regardless of the outcome.

The three clauses have distinct responsibilities:

| Clause | Executes when | Primary purpose |
|---|---|---|
| `try` | Always attempted | Code that may raise |
| `except` | A matching exception occurs | Handle or translate failure |
| `else` | `try` completes without an exception | Successful-path logic |
| `finally` | Almost always, regardless of outcome | Cleanup and lifecycle management |

A production-oriented mental model is:

```text
                try
                 │
          ┌──────┴──────┐
          │             │
       success        failure
          │             │
          ▼             ▼
        else          except
          │             │
          └──────┬──────┘
                 │
                 ▼
              finally
                 │
                 ▼
              continue
              or propagate
```

The important distinction is that `else` describes **successful completion of the `try` block**, while `finally` describes **mandatory cleanup or finalization**.

---

## `else` with `try`

The basic structure is:

```python
try:
    result = operation()
except OperationError:
    handle_error()
else:
    process_success(result)
```

The `else` block executes only if the `try` block completes without raising an exception.

It does not execute when:

- the `try` block raises a matching exception
- the `try` block raises an unmatched exception
- control leaves the `try` block through `return`, `break`, or `continue`

For normal successful execution:

```text
try succeeds
    │
    ▼
else executes
    │
    ▼
continue
```

For a handled failure:

```text
try raises
    │
    ▼
except executes
    │
    ▼
else is skipped
```

---

## Why `else` Exists

Without `else`, successful-path code often gets placed inside the `try` block:

```python
try:
    result = repository.get_order(order_id)
    validate_order(result)
    publish_event(result)
except DatabaseError:
    handle_database_error()
```

This can accidentally catch exceptions raised by `validate_order()` or `publish_event()` if they happen to use the same exception type.

Using `else` narrows the exception boundary:

```python
try:
    result = repository.get_order(order_id)
except DatabaseError:
    handle_database_error()
else:
    validate_order(result)
    publish_event(result)
```

Now the `DatabaseError` handler applies specifically to the database operation.

This improves both readability and correctness.

---

## `else` as a Success Boundary

A useful interpretation is:

```text
try
└── operation whose failure you intend to catch

except
└── failure handling

else
└── operation that should happen only after successful completion

finally
└── cleanup
```

This makes the control flow explicit.

For example:

```python
try:
    user = repository.create_user(data)
except DatabaseError as exc:
    raise UserPersistenceError from exc
else:
    audit_user_created(user)
```

The audit operation is not part of the database exception boundary.

---

## `else` and Exception Scope

Consider:

```python
try:
    data = load_data()
    result = transform(data)
except ValueError:
    recover()
```

Both `load_data()` and `transform()` can potentially raise `ValueError`.

If only `load_data()` should trigger the recovery logic:

```python
try:
    data = load_data()
except ValueError:
    recover()
else:
    result = transform(data)
```

This creates a more precise failure boundary.

The same principle applies to backend operations involving:

- PostgreSQL
- Redis
- HTTP clients
- Kafka producers
- filesystem operations
- configuration parsing
- message processing

---

## `else` with `finally`

All four clauses can be used together:

```python
try:
    result = operation()
except OperationError:
    handle_error()
else:
    process_success(result)
finally:
    release_resource()
```

The semantic flow is:

```text
                 try
                  │
          ┌───────┴────────┐
          │                │
       success           failure
          │                │
          ▼                ▼
        else             except
          │                │
          └───────┬────────┘
                  ▼
               finally
                  │
                  ▼
              next step
```

The `finally` block executes after the applicable `try`, `except`, or `else` path.

---

## `finally`

`finally` is used for cleanup or actions that should execute regardless of whether the operation succeeds or fails.

```python
resource = acquire_resource()

try:
    use(resource)
finally:
    resource.close()
```

If `use()` succeeds, `close()` executes.

If `use()` raises an exception, `close()` still executes before the exception continues propagating.

---

## Why `finally` Exists

Resources often have lifecycle requirements:

```text
Acquire
   │
   ▼
Use
   │
   ├── success ──┐
   │             │
   └── failure ──┤
                 ▼
               Cleanup
```

Examples include:

- file handles
- locks
- sockets
- database resources
- temporary files
- tracing spans
- external resources
- transaction state

Without reliable cleanup, failures can produce resource leaks.

---

## `finally` Execution Semantics

For:

```python
try:
    operation()
finally:
    cleanup()
```

Python attempts to execute `cleanup()` after the `try` block completes, including when:

- the `try` block succeeds
- the `try` block raises an exception
- the exception is not handled locally
- the `try` block executes `return`
- the `try` block executes `break`
- the `try` block executes `continue`

For example:

```python
def process():
    try:
        return "success"
    finally:
        logger.info("cleanup")
```

The cleanup runs before the function returns.

---

## `finally` and Exceptions

Consider:

```python
def process():
    try:
        raise ValueError("invalid")
    finally:
        cleanup()
```

The execution is:

```text
raise ValueError
      │
      ▼
finally executes
      │
      ▼
ValueError propagates
```

`finally` does not automatically suppress the exception.

---

## `finally` and `return`

A `return` inside `try` does not prevent `finally` from running:

```python
def process():
    try:
        return "success"
    finally:
        cleanup()
```

Conceptually:

```text
evaluate return value
       │
       ▼
execute finally
       │
       ▼
perform return
```

However, a `return` inside `finally` is dangerous:

```python
def process():
    try:
        return "success"
    finally:
        return "cleanup"
```

The result is:

```python
"cleanup"
```

The `finally` return overrides the pending return.

This can also suppress an exception:

```python
def process():
    try:
        raise RuntimeError("failure")
    finally:
        return "ignored"
```

The exception is suppressed.

Avoid returning from `finally` in normal application code.

---

## `finally` and `break`

The same cleanup semantics apply to loops:

```python
while True:
    try:
        process_batch()
    finally:
        release_batch_resources()

    break
```

The `finally` block runs before the `break` takes effect.

---

## `finally` and `continue`

`finally` also executes before a `continue` transfers control to the next loop iteration:

```python
for item in items:
    try:
        process(item)
    finally:
        release(item)

    continue
```

This matters when resource ownership exists inside loops.

---

## `finally` with Unhandled Exceptions

A `finally` block does not require an `except` block:

```python
try:
    process_request()
finally:
    cleanup_request()
```

This is useful when the caller should receive the exception unchanged but cleanup is mandatory.

It is often preferable to:

```python
try:
    process_request()
except Exception:
    cleanup_request()
    raise
```

because `finally` directly expresses the cleanup requirement.

---

## `try` / `except` / `else` / `finally`

The complete form is:

```python
try:
    operation()
except SpecificError:
    handle_error()
else:
    handle_success()
finally:
    cleanup()
```

Execution rules:

| `try` outcome | `except` | `else` | `finally` |
|---|---|---|---|
| Success | No | Yes | Yes |
| Matching exception | Yes | No | Yes |
| Unmatched exception | No | No | Yes |
| `return` | No | No | Yes |
| `break` | No | No | Yes |
| `continue` | No | No | Yes |

The exact control-flow interaction becomes more nuanced when `return`, `break`, `continue`, or another exception occurs inside `except`, `else`, or `finally`, because later control flow can replace earlier pending control flow.

---

## Execution Order

Consider:

```python
try:
    operation()
except OperationError:
    recover()
else:
    succeed()
finally:
    cleanup()
```

On success:

```text
try → else → finally
```

On a matching exception:

```text
try → except → finally
```

On an unmatched exception:

```text
try → finally → propagate
```

This ordering is fundamental when designing resource lifecycle behavior.

---

## Example: File Processing

A low-level implementation can use `finally`:

```python
file = open("orders.json", encoding="utf-8")

try:
    data = file.read()
except OSError:
    logger.exception("failed to read orders")
    raise
finally:
    file.close()
```

However, Python's context-manager protocol is preferable:

```python
with open("orders.json", encoding="utf-8") as file:
    data = file.read()
```

The context manager provides the same lifecycle guarantee with less error-prone code.

`finally` remains important for understanding how cleanup works underneath context-manager abstractions.

---

## Example: Database Resource

A manually managed resource might look like:

```python
connection = create_connection()

try:
    result = connection.execute(query)
except DatabaseError:
    connection.rollback()
    raise
else:
    connection.commit()
finally:
    connection.close()
```

This demonstrates a useful separation:

- `try`: operation that may fail
- `except`: rollback on failure
- `else`: commit after successful operation
- `finally`: release connection

The exact implementation should normally use the transaction and connection-management facilities provided by the database driver or framework.

---

## Why Commit Belongs in `else`

Consider:

```python
try:
    connection.execute(query)
    connection.commit()
except DatabaseError:
    connection.rollback()
```

If `commit()` itself raises `DatabaseError`, the exception is caught by the same handler.

That may be correct, but the transaction semantics can become difficult to reason about.

A clearer structure is:

```python
try:
    connection.execute(query)
except DatabaseError:
    connection.rollback()
    raise
else:
    connection.commit()
finally:
    connection.close()
```

The `else` clause makes it explicit that the commit occurs only after the protected database operation completes successfully.

In production, prefer the transaction abstraction supplied by your PostgreSQL driver, Django, SQLAlchemy, or equivalent framework rather than implementing transaction state manually unless there is a specific reason.

---

## Context Managers vs `finally`

A context manager is generally preferred for reusable resource lifecycle management.

Manual approach:

```python
resource = acquire()

try:
    use(resource)
finally:
    release(resource)
```

Context-manager approach:

```python
with resource_manager() as resource:
    use(resource)
```

Comparison:

| Approach | Strength | Typical use |
|---|---|---|
| `finally` | Explicit cleanup control | One-off cleanup logic |
| Context manager | Encapsulated lifecycle | Files, locks, transactions, sessions |
| `contextlib` | Reusable Python abstraction | Custom resource management |

A context manager itself commonly implements cleanup using `try`/`finally`.

---

## `finally` and Context Manager Internals

Conceptually, a context manager:

```python
with manager() as resource:
    use(resource)
```

provides lifecycle behavior equivalent to a structure involving:

```python
manager = manager()
resource = manager.__enter__()

try:
    use(resource)
finally:
    manager.__exit__(...)
```

The actual language semantics include exception information being passed to `__exit__`, and `__exit__` can suppress an exception by returning a truthy value.

The important engineering point is that `finally` is one of the fundamental mechanisms behind reliable cleanup.

---

## Exception Handling with `else`

A strong pattern for application code is:

```python
try:
    raw = client.fetch()
except ClientError as exc:
    raise DependencyUnavailable from exc
else:
    return parse_response(raw)
```

This separates:

```text
External I/O failure
        │
        ▼
     except
        │
        ▼
Application error


Successful I/O
        │
        ▼
      else
        │
        ▼
Parsing / processing
```

This is especially useful when parsing can raise exceptions that should not be confused with network failures.

---

## Backend Request Lifecycle

A FastAPI request may conceptually look like:

```text
HTTP request
     │
     ▼
Endpoint
     │
     ▼
Service
     │
     ▼
Repository / HTTP client
     │
     ├── failure → except → translate
     │
     └── success → else → continue
                       │
                       ▼
                    finally
                 release resources
```

For example:

```python
async def create_order(payload):
    client = PaymentClient()

    try:
        payment = await client.authorize(payload.payment)
    except PaymentTimeout as exc:
        raise PaymentUnavailable from exc
    else:
        return await order_service.create(
            payload,
            payment,
        )
    finally:
        await client.close()
```

In production, the HTTP client would typically be managed at an application or dependency-injection lifecycle boundary rather than instantiated per request.

---

## `finally` and Locks

Locks are another common cleanup use case.

Manual pattern:

```python
lock.acquire()

try:
    update_shared_state()
finally:
    lock.release()
```

If `update_shared_state()` raises an exception, the lock is still released.

A context manager is generally preferable:

```python
with lock:
    update_shared_state()
```

Failing to release locks can cause:

- blocked threads
- stuck workers
- request timeouts
- deadlocks
- degraded availability

---

## `finally` and Async Code

The same pattern applies to asynchronous resources:

```python
connection = await acquire_connection()

try:
    await process(connection)
finally:
    await connection.close()
```

Cancellation makes cleanup particularly important in asynchronous systems.

For example, an `asyncio` task can be cancelled while waiting on an operation. Cleanup code should therefore be designed to execute correctly when control flow is interrupted.

Async context managers are often preferable:

```python
async with connection_manager() as connection:
    await process(connection)
```

---

## Cleanup Must Not Accidentally Fail

A dangerous pattern is:

```python
try:
    process()
finally:
    cleanup()
```

when `cleanup()` itself can raise an exception.

If both the operation and cleanup fail, the cleanup exception can replace the original failure.

This can obscure the root cause.

For critical cleanup, consider whether cleanup failures should:

- propagate
- be logged and suppressed
- be retried
- trigger an operational alert

The correct decision depends on the resource.

---

## Cleanup Error Policy

Not every cleanup failure should be ignored.

For example:

```text
Temporary metrics flush failure
        └── may be logged

Database rollback failure
        └── potentially critical

Lock release failure
        └── potentially severe

Security-sensitive cleanup failure
        └── may require escalation
```

The cleanup policy must match the resource's importance.

Avoid blindly writing:

```python
finally:
    try:
        cleanup()
    except Exception:
        pass
```

because this can hide infrastructure failures.

---

## `finally` and Exception Replacement

Consider:

```python
try:
    raise RuntimeError("original")
finally:
    raise ValueError("cleanup failed")
```

The resulting exception is the `ValueError`.

The cleanup exception replaces the original exception as the active failure.

This is why cleanup code should generally be simple, deterministic, and carefully designed.

---

## `finally` and `return`

Avoid:

```python
def process():
    try:
        return calculate()
    finally:
        return default_value()
```

The original return is overridden.

Likewise:

```python
def process():
    try:
        raise RuntimeError("failure")
    finally:
        return None
```

The exception is suppressed.

A robust rule is:

> Do not use `return`, `break`, or `continue` in `finally` unless deliberately implementing unusual control flow and fully understanding the consequences.

---

## Nested `finally` Blocks

Nested cleanup is executed from the innermost scope outward.

```python
try:
    acquire_outer()

    try:
        acquire_inner()
        process()
    finally:
        release_inner()
finally:
    release_outer()
```

The order is:

```text
acquire_outer
    │
    ▼
acquire_inner
    │
    ▼
process
    │
    ▼
release_inner
    │
    ▼
release_outer
```

This mirrors resource ownership and is useful when resources have dependencies.

---

## Multiple Resources

Instead of manually nesting `try`/`finally` blocks:

```python
resource_a = acquire_a()

try:
    resource_b = acquire_b()

    try:
        process(resource_a, resource_b)
    finally:
        release_b(resource_b)
finally:
    release_a(resource_a)
```

prefer context managers when available:

```python
with acquire_a() as resource_a, acquire_b() as resource_b:
    process(resource_a, resource_b)
```

Multiple context managers enter from left to right and exit from right to left.

---

## Reliability Considerations

Reliable cleanup should preserve resource invariants:

```text
Acquire resource
      │
      ▼
Perform operation
      │
      ├── success ──► finalize
      │
      └── failure ──► rollback/recover
                          │
                          ▼
                     release resource
```

This matters for:

- database connections
- connection pools
- file descriptors
- locks
- HTTP sessions
- temporary files
- tracing spans
- transactions
- worker resources

Resource leakage can eventually become an availability incident even when individual requests appear correct.

---

## Scalability Considerations

A `finally` block runs for every execution of the associated `try` statement.

Therefore cleanup operations should not introduce unnecessary latency.

Avoid expensive operations such as:

```python
finally:
    rebuild_cache()
```

when the cleanup runs on every request.

For high-throughput services, resource cleanup should generally:

- release local resources quickly
- avoid unnecessary network calls
- avoid blocking the event loop
- use connection pools
- use centralized lifecycle management
- avoid repeated resource initialization

---

## Kubernetes and Deployment

In Kubernetes, pods can be terminated during:

- rolling deployments
- scaling
- node maintenance
- eviction
- application failures

Application-level `finally` blocks can help clean up resources when Python code exits through normal exception/control-flow paths, but they are not a substitute for proper process signal handling and graceful shutdown.

For example:

```text
SIGTERM
   │
   ▼
Graceful shutdown
   │
   ├── stop accepting work
   ├── finish/cancel active work
   ├── release resources
   └── exit
```

Shutdown architecture should use application lifecycle hooks and context managers where appropriate.

---

## Observability

Exception handling and cleanup should remain observable.

Useful signals include:

- exception counts
- error rates
- retry counts
- rollback counts
- cleanup failures
- request latency
- resource-pool exhaustion
- task cancellation
- connection leaks

For example:

```python
try:
    process()
except ProcessingError:
    logger.exception("processing failed")
    raise
finally:
    metrics.increment("processing.cleanup")
```

Avoid logging every normal cleanup operation at high severity because this can create excessive log volume and cost.

---

## Security Considerations

Cleanup code can operate on sensitive resources.

Examples include:

- temporary credential files
- authentication sessions
- database connections
- security tokens
- temporary decrypted data

A `finally` block should not accidentally log secrets:

```python
finally:
    logger.info("closing session token=%s", token)
```

Instead, log safe identifiers:

```python
finally:
    logger.info("closing authentication session")
```

Security-sensitive cleanup should be treated as part of the application's security boundary.

---

## Testing `else`

Test that `else` runs only after successful execution.

```python
def test_success_path_runs():
    result = process()

    assert result.status == "success"
```

For more explicit behavior, mock the successful-path operation and verify it is not invoked after failure.

```python
def test_success_handler_not_called_on_failure(mocker):
    success_handler = mocker.Mock()

    with pytest.raises(DatabaseError):
        execute(success_handler)

    success_handler.assert_not_called()
```

---

## Testing `finally`

A cleanup assertion should cover failure paths:

```python
def test_resource_released_on_failure():
    resource = FakeResource()

    with pytest.raises(RuntimeError):
        process(resource)

    assert resource.closed
```

Also test successful execution:

```python
def test_resource_released_on_success():
    resource = FakeResource()

    process(resource)

    assert resource.closed
```

The important invariant is:

```text
success → cleanup
failure → cleanup
```

---

## Testing Cleanup Failures

If cleanup failures are meaningful to the application's contract, test them separately.

```python
def test_cleanup_failure_is_observable():
    resource = FailingResource()

    with pytest.raises(CleanupError):
        process(resource)
```

Do not automatically suppress cleanup failures merely to make tests pass.

---

## Common Mistakes

| Mistake | Why it is dangerous | Better approach |
|---|---|---|
| Putting all code in `try` | Catches unrelated exceptions | Keep `try` narrow |
| Ignoring `else` | Successful-path boundary becomes unclear | Use `else` when it improves exception scope |
| Returning from `finally` | Overrides returns and can suppress exceptions | Avoid control-flow statements in `finally` |
| Raising in `finally` carelessly | Can replace the original exception | Keep cleanup simple |
| Swallowing cleanup errors | Hides resource failures | Define cleanup error policy |
| Manually closing every resource | Easy to forget cleanup | Prefer context managers |
| Blocking in async `finally` | Can stall the event loop | Use async cleanup |
| Expensive cleanup on every request | Adds latency and cost | Keep cleanup lightweight |
| Assuming `finally` handles process termination | Incomplete shutdown model | Implement graceful lifecycle handling |
| Logging sensitive values in cleanup | Information leakage | Redact sensitive data |

---

## Production Patterns

### Narrow `try`, Explicit `else`

```python
try:
    response = client.fetch()
except TimeoutError as exc:
    raise DependencyUnavailable from exc
else:
    return parse_response(response)
```

Use when successful processing should not belong to the I/O exception boundary.

### Cleanup with `finally`

```python
resource = acquire()

try:
    process(resource)
finally:
    release(resource)
```

Use when the resource does not have a context-manager abstraction.

### Context Manager for Reusable Lifecycle

```python
with resource_manager() as resource:
    process(resource)
```

Prefer this when lifecycle semantics are reusable.

### Transactional Flow

```python
try:
    persist()
except DatabaseError:
    rollback()
    raise
else:
    commit()
finally:
    release_connection()
```

Use the database framework's transaction abstraction when possible.

---

## Design Decision Guide

| Situation | Preferred construct |
|---|---|
| Handle a known failure | `try` + `except` |
| Execute logic only after success | `try` + `else` |
| Guarantee cleanup | `try` + `finally` |
| Handle failure and guarantee cleanup | `try` + `except` + `finally` |
| Handle failure, successful path, and cleanup | `try` + `except` + `else` + `finally` |
| Reusable resource lifecycle | Context manager |
| Async resource lifecycle | Async context manager |
| Dynamic resource collection | `ExitStack` / `AsyncExitStack` |

---

## Senior Engineering Perspective

`else` and `finally` are most valuable when they make failure boundaries and resource ownership explicit.

A strong design separates four concerns:

```text
try
└── Operation that may fail

except
└── Failure interpretation/recovery

else
└── Logic that is valid only after success

finally
└── Resource lifecycle / mandatory finalization
```

This separation becomes increasingly important as systems become more complex.

In a backend service, one request may involve:

```text
HTTP request
    │
    ▼
Validation
    │
    ▼
PostgreSQL transaction
    │
    ▼
Redis operation
    │
    ▼
External HTTP call
    │
    ▼
Kafka publication
```

Each boundary may have different failure and cleanup semantics.

The goal is not to use all four clauses everywhere. The goal is to express the actual lifecycle and failure model precisely.

---

## Key Takeaways

- `else` runs only when the `try` block completes successfully and is useful for keeping successful-path logic outside the exception boundary.
- `finally` is the cleanup mechanism that runs across success, handled exceptions, unhandled exceptions, and normal control-flow exits.
- Keep `try` blocks narrow; use `else` when code should execute after a specific operation succeeds without accidentally catching unrelated exceptions.
- Avoid `return`, `break`, `continue`, or careless exception raising inside `finally` because they can override pending returns or replace and suppress original exceptions.
- Prefer context managers for reusable resource lifecycle management, while understanding that `try`/`finally` provides the fundamental cleanup semantics underneath them.