# 05- Decorators

## Overview

A decorator is a callable that takes another callable, extends or modifies its behavior, and returns a callable.

Python provides decorator syntax as a convenient way to apply this transformation:

```python
@decorator
def function():
    ...
```

Conceptually:

```python
def function():
    ...


function = decorator(function)
```

Decorators are built on Python's first-class functions and closures. They are therefore an important intermediate-to-advanced Python concept and appear extensively in backend frameworks and libraries.

Common production uses include:

- Logging and tracing
- Metrics
- Authentication and authorization
- Caching
- Retry policies
- Rate limiting
- Transaction boundaries
- Validation
- Feature flags
- Authorization checks
- Request instrumentation
- Framework registration
- Resource management

The important engineering principle is:

> A decorator should add a well-defined cross-cutting behavior without obscuring the decorated operation's core responsibility.

## Why Decorators Exist

Many backend operations require the same behavior around otherwise unrelated functions.

For example:

```text
                 +------------------+
                 |   Business Call  |
                 +------------------+
                          |
              +-----------+-----------+
              |           |           |
           Logging      Metrics    Tracing
              |           |           |
              +-----------+-----------+
                          |
                    Actual function
```

Without decorators, cross-cutting logic tends to be duplicated:

```python
def create_user(data):
    start_timer()
    log_request()

    try:
        return service.create_user(data)
    finally:
        record_metrics()
```

A decorator can centralize the infrastructure concern:

```python
@observed
def create_user(data):
    return service.create_user(data)
```

This separates the business operation from reusable infrastructure behavior.

## Decorator Fundamentals

A basic decorator looks like this:

```python
from collections.abc import Callable
from typing import Any


def log_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)

    return wrapper
```

Applying it:

```python
@log_calls
def create_user(user_id: int) -> str:
    return f"user:{user_id}"
```

The syntax:

```python
@log_calls
def create_user(user_id: int) -> str:
    return f"user:{user_id}"
```

is equivalent to:

```python
def create_user(user_id: int) -> str:
    return f"user:{user_id}"


create_user = log_calls(create_user)
```

The original function object is passed to `log_calls`, and the returned wrapper becomes the new value bound to `create_user`.

## How Decorators Work

The decorator process has two distinct stages.

### Decoration Time

The decorator executes when the `def` statement is executed.

```python
@log_calls
def create_user():
    ...
```

Conceptually:

```text
Define function
      |
      v
Create function object
      |
      v
Call decorator(function)
      |
      v
Receive wrapper
      |
      v
Bind name to wrapper
```

### Call Time

Later, when:

```python
create_user()
```

is executed, the wrapper runs.

```text
Caller
   |
   v
wrapper()
   |
   +--> pre-processing
   |
   +--> original function
   |
   +--> post-processing
   |
   v
result
```

Understanding this distinction is important when decorators perform setup, registration, validation, or configuration at import time.

## A Production-Oriented Decorator

A basic logging decorator should preserve metadata and avoid changing the original callable's interface unnecessarily.

```python
from collections.abc import Callable
from functools import wraps
from typing import Any


def log_calls(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)

    return wrapper
```

The `@wraps(func)` decorator is important for preserving function metadata.

## `functools.wraps`

Without `wraps`, the wrapper replaces important metadata:

```python
def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
```

Then:

```python
@decorator
def process_order():
    """Process an order."""
    ...
```

may report:

```python
process_order.__name__ == "wrapper"
```

and:

```python
process_order.__doc__ == None
```

Using:

```python
from functools import wraps


def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
```

preserves important metadata such as:

- `__name__`
- `__qualname__`
- `__doc__`
- `__module__`
- `__annotations__`

It also sets `__wrapped__`, which many introspection tools and frameworks use.

> Production decorators should generally use `functools.wraps`.

## Decorators with Arguments

A decorator that accepts configuration requires another function layer.

For example:

```python
from collections.abc import Callable
from functools import wraps
from typing import Any


def retry(
    attempts: int,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(
        func: Callable[..., Any],
    ) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: Exception | None = None

            for _ in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_error = exc

            raise last_error

        return wrapper

    return decorator
```

Usage:

```python
@retry(attempts=3)
def call_external_service() -> str:
    ...
```

The evaluation is:

```text
retry(attempts=3)
        |
        v
    decorator
        |
        v
decorator(function)
        |
        v
     wrapper
```

This is why decorators with arguments often appear to have three nested functions.

## Decorator Factory

The outer function in:

```python
@retry(attempts=3)
```

is a **decorator factory**.

Its job is to capture configuration and return the actual decorator.

```text
configuration
     |
     v
decorator factory
     |
     v
configured decorator
     |
     v
target function
     |
     v
wrapped function
```

This pattern is common for:

- Retry configuration
- Cache configuration
- Rate limits
- Authorization policies
- Feature flags
- Metrics labels
- Timeout configuration

## Decorator Execution Order

Multiple decorators are applied from the bottom upward.

```python
@outer
@middle
@inner
def process():
    ...
```

is equivalent to:

```python
process = outer(middle(inner(process)))
```

The call path is therefore:

```text
process()
   |
   v
outer wrapper
   |
   v
middle wrapper
   |
   v
inner wrapper
   |
   v
original process()
```

The order matters when decorators perform operations such as:

- Authentication
- Transactions
- Retries
- Caching
- Logging
- Metrics

For example:

```python
@transactional
@retry(attempts=3)
def update_order():
    ...
```

has different semantics from:

```python
@retry(attempts=3)
@transactional
def update_order():
    ...
```

The transaction boundary and retry boundary are different.

## Decorator Ordering in Backend Systems

Consider:

```python
@authenticate
@rate_limit
@trace
def get_account():
    ...
```

The effective structure is:

```text
authenticate
    |
    v
rate_limit
    |
    v
trace
    |
    v
get_account
```

A senior engineer should explicitly reason about:

- Which checks execute first.
- Which failures are visible to which decorator.
- Which operations are retried.
- Whether metrics include rejected requests.
- Whether tracing covers authentication.
- Whether transactions include retry attempts.

Decorator order is part of application behavior.

## Preserving Return Values

A wrapper should normally return the original result.

```python
from functools import wraps


def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("before")
        result = func(*args, **kwargs)
        print("after")
        return result

    return wrapper
```

Incorrect:

```python
def wrapper(*args, **kwargs):
    func(*args, **kwargs)
```

The original return value is lost.

Decorators should preserve the decorated callable's expected contract unless changing that contract is intentional.

## Preserving Exceptions

A transparent decorator should normally allow exceptions to propagate.

```python
from functools import wraps


def log_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            print("operation failed")
            raise

    return wrapper
```

The bare `raise` preserves the original exception and traceback.

Avoid:

```python
except Exception as exc:
    raise Exception(str(exc))
```

unless there is a deliberate exception translation boundary.

## Decorators and Closures

Decorators rely heavily on closures.

```python
def prefix(prefix_value: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(prefix_value)
            return func(*args, **kwargs)

        return wrapper

    return decorator
```

The wrapper retains access to `prefix_value` even after `prefix()` has returned.

This allows decorators to capture configuration without storing it globally.

## Decorators and Stateful Closures

A decorator can maintain state:

```python
from functools import wraps


def count_calls(func):
    count = 0

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal count
        count += 1
        return func(*args, **kwargs)

    return wrapper
```

However, the state is typically process-local and shared by all calls through that wrapper.

This matters in production deployments.

If a service has:

```text
Kubernetes
   |
   +--> Pod A --> decorator state = 100
   |
   +--> Pod B --> decorator state = 75
   |
   +--> Pod C --> decorator state = 120
```

the values are not globally consistent.

Do not use process-local decorator state as a distributed counter or coordination mechanism.

For distributed state, use an appropriate external system such as:

- Redis
- PostgreSQL
- Kafka
- Cloud-managed metrics

## Async Decorators

Synchronous and asynchronous functions require different wrapper behavior.

This decorator is for synchronous callables:

```python
def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("calling")
        return func(*args, **kwargs)

    return wrapper
```

It should not blindly wrap an `async def` function.

For asynchronous functions:

```python
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar


T = TypeVar("T")


def async_log_calls(
    func: Callable[..., Awaitable[T]],
) -> Callable[..., Awaitable[T]]:
    @wraps(func)
    async def wrapper(
        *args: Any,
        **kwargs: Any,
    ) -> T:
        print(f"calling {func.__name__}")
        return await func(*args, **kwargs)

    return wrapper
```

Usage:

```python
@async_log_calls
async def get_user(user_id: int) -> User:
    ...
```

The wrapper must `await` the original coroutine.

## Detecting Sync vs Async Functions

A decorator intended to support both synchronous and asynchronous functions can inspect the target:

```python
import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any


def log_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            print(f"calling {func.__name__}")
            return await func(*args, **kwargs)

        return async_wrapper

    @wraps(func)
    def sync_wrapper(
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)

    return sync_wrapper
```

This pattern can be useful for generic infrastructure utilities, but it increases complexity. If a decorator only needs to support one execution model, keep it specialized.

## Decorators in FastAPI

Frameworks frequently use decorators to register application behavior.

For example:

```python
from fastapi import FastAPI


app = FastAPI()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
```

The decorator is not merely wrapping the function in the usual cross-cutting-concern sense. Framework decorators can also perform **registration**.

Conceptually:

```text
@app.get("/health")
       |
       v
FastAPI route registration
       |
       v
health_check function
       |
       v
Application routing table
```

The framework stores metadata describing:

- HTTP method
- Path
- Handler
- Dependencies
- Response behavior
- OpenAPI metadata

The same distinction appears in many Python frameworks: decorators can either wrap behavior, register behavior, or do both.

## Decorators in Django

Django uses decorators for common request-level concerns.

Examples include:

- Authentication requirements
- HTTP method restrictions
- CSRF-related behavior
- Caching
- Permission checks

For example:

```python
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    ...
```

The decorator adds an access-control policy around the view.

This is a useful example of a cross-cutting concern being separated from business logic.

## Authentication and Authorization

A decorator can enforce authorization:

```python
from collections.abc import Callable
from functools import wraps
from typing import Any


def require_admin(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(
        user: User,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not user.is_admin:
            raise PermissionError("admin access required")

        return func(user, *args, **kwargs)

    return wrapper
```

Usage:

```python
@require_admin
def delete_user(
    user: User,
    user_id: int,
) -> None:
    ...
```

However, authorization decorators should not be used as the sole security boundary in a complex system.

A robust system should also enforce authorization at appropriate service and data-access boundaries.

The decorator should provide a clear application-level policy, not create a false assumption that every execution path must pass through one wrapper.

## Logging Decorators

A logging decorator can centralize basic invocation logging:

```python
import logging
from functools import wraps
from typing import Any


logger = logging.getLogger(__name__)


def log_calls(func):
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info(
            "calling function",
            extra={"function": func.__qualname__},
        )
        return func(*args, **kwargs)

    return wrapper
```

Avoid logging:

- Passwords
- Access tokens
- Session cookies
- API keys
- Full payment data
- Sensitive personal information

Decorators sit at a boundary where careless argument logging can become a security incident.

## Metrics Decorators

A decorator can measure operation latency:

```python
import time
from functools import wraps
from typing import Any


def measure_time(func):
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - started
            record_latency(func.__qualname__, elapsed)

    return wrapper
```

The `finally` block ensures the measurement occurs even when the function raises an exception.

In production, prefer established observability libraries and metrics backends rather than implementing a complete metrics system inside a decorator.

## Tracing Decorators

Distributed tracing is another common cross-cutting concern.

Conceptually:

```text
HTTP Request
     |
     v
Trace decorator
     |
     v
Service method
     |
     v
Repository
     |
     v
PostgreSQL
```

A decorator can create or annotate a span around a service operation.

However, tracing context must be propagated correctly across:

- Async tasks
- Threads
- Processes
- Kafka messages
- Celery tasks
- HTTP calls
- gRPC calls

A simple wrapper does not automatically solve distributed context propagation.

## Retry Decorators

Retries are a common decorator use case, but they are easy to implement incorrectly.

A naive implementation:

```python
def retry(attempts):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    pass

            return func(*args, **kwargs)

        return wrapper

    return decorator
```

has serious problems:

- Retries every exception.
- Does not use backoff.
- Can amplify traffic.
- Can retry non-idempotent operations.
- Can hide the original exception.
- Has no jitter.
- Has no maximum delay.
- Can make an outage worse.

Production retries should be explicit about:

- Retryable exceptions.
- Maximum attempts.
- Exponential backoff.
- Jitter.
- Deadlines.
- Idempotency.
- Maximum elapsed time.

For example:

```text
Request
   |
   v
Attempt 1
   |
 failure
   |
   v
Backoff + jitter
   |
   v
Attempt 2
   |
 failure
   |
   v
Attempt 3
   |
   v
Success / final failure
```

Retry decorators are appropriate only when the retry semantics are well-defined.

## Caching Decorators

Python provides `functools.cache` and `functools.lru_cache` for appropriate function-level caching.

Example:

```python
from functools import lru_cache


@lru_cache(maxsize=1024)
def get_country_code(country: str) -> str:
    ...
```

This can be useful for deterministic, relatively stable computations.

However, an in-process cache is not equivalent to Redis.

```text
Pod A --> local cache
Pod B --> local cache
Pod C --> local cache
```

Each process has independent state.

For distributed application caching:

```text
Application
     |
     v
Redis
     |
     v
Shared cache
```

Consider:

- Cache invalidation.
- TTL.
- Memory limits.
- Eviction policy.
- Serialization.
- Stale data.
- Cache stampedes.
- Process-local vs distributed scope.

## Transaction Decorators

A transaction decorator can define a transaction boundary:

```python
@transactional
def create_order(...):
    ...
```

This can be convenient, but transaction boundaries should remain explicit enough that engineers understand:

- What operations participate.
- How exceptions trigger rollback.
- How nested transactions behave.
- What isolation level applies.
- How retries interact with transactions.
- Whether external side effects occur inside the transaction.

A transaction should not span an unnecessarily long operation such as a network call to an unrelated external service.

## Decorator Composition

Decorators can be composed to create reusable policies:

```python
@authenticated
@rate_limited
@traced
@validated
def create_order(...):
    ...
```

This can be powerful, but excessive composition creates invisible control flow.

When reviewing such code, mentally expand it:

```text
authenticated(
    rate_limited(
        traced(
            validated(
                create_order
            )
        )
    )
)
```

If the resulting execution path becomes difficult to reason about, use explicit middleware, dependency injection, service objects, or framework-native mechanisms instead.

## Decorators vs Middleware

Decorators and middleware solve related but different problems.

| Concern | Decorator | Middleware |
|---|---|---|
| Function-specific policy | Excellent | Poor fit |
| Whole HTTP application | Poor fit | Excellent |
| Route-specific behavior | Excellent | Possible |
| Request lifecycle | Possible | Excellent |
| Logging | Good | Excellent globally |
| Authentication | Good for local policy | Excellent globally |
| Transaction boundary | Good | Sometimes |
| Cross-service infrastructure | Limited | Better at framework boundary |

Use decorators when behavior belongs to a specific callable.

Use middleware when behavior belongs to an entire request or application lifecycle.

## Decorators vs Dependency Injection

Consider authentication.

A decorator:

```python
@require_admin
def delete_user(...):
    ...
```

implicitly adds behavior around the function.

Dependency injection makes dependencies more explicit:

```python
def delete_user(
    user: User,
    authorization: AuthorizationService,
) -> None:
    authorization.require_admin(user)
    ...
```

Neither is universally superior.

A useful distinction is:

```text
Cross-cutting policy
        |
        v
Decorator / middleware

Required collaborator
        |
        v
Dependency injection

Business operation
        |
        v
Explicit function/service method
```

Do not use decorators to hide dependencies that callers need to understand.

## Decorators and Method Binding

Decorators also work with methods.

```python
def log_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(func.__qualname__)
        return func(*args, **kwargs)

    return wrapper


class OrderService:
    @log_calls
    def create_order(self, order_id: int) -> None:
        ...
```

The wrapper becomes a function descriptor and participates in normal method binding.

When called:

```python
service.create_order(100)
```

the instance is passed through the wrapper to the original method.

This is one reason decorators should normally preserve callable behavior carefully.

## Decorators and `classmethod` / `staticmethod`

Decorator order matters with descriptors such as `classmethod`.

Correct:

```python
class User:
    @classmethod
    @validate_input
    def from_email(cls, email: str):
        ...
```

Here:

```python
from_email = classmethod(validate_input(from_email))
```

versus:

```python
class User:
    @validate_input
    @classmethod
    def from_email(cls, email: str):
        ...
```

These are not generally equivalent because the inner `classmethod` changes the object being passed to the outer decorator.

The same principle applies to:

- `staticmethod`
- `property`
- Custom descriptors

When decorating methods involving descriptors, understand which decorator executes first and what object it receives.

## Decorators and Type Safety

Generic decorators often use:

```python
Callable[..., Any]
```

because they must accept arbitrary signatures.

This is convenient but weakens static type precision.

Modern Python typing can preserve a function's parameter and return types with `ParamSpec` and `TypeVar`.

```python
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def log_calls(
    func: Callable[P, R],
) -> Callable[P, R]:
    @wraps(func)
    def wrapper(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        print(func.__qualname__)
        return func(*args, **kwargs)

    return wrapper
```

This communicates that:

```text
input signature
      |
      v
decorated function
      |
      v
same input signature
      |
      v
same return type
```

`ParamSpec` is particularly valuable for reusable decorator libraries and strongly typed backend code.

## Decorators and `functools.wraps`

`wraps()` is itself implemented using `functools.update_wrapper()`.

Conceptually:

```python
wrapper = update_wrapper(
    wrapper,
    wrapped=func,
)
```

This copies selected metadata and establishes the `__wrapped__` reference.

That reference is useful for introspection:

```python
original = decorated_function.__wrapped__
```

Frameworks and tools may use this metadata for:

- Signature inspection
- Documentation
- Dependency discovery
- Testing
- Debugging
- Instrumentation

Do not casually remove or overwrite `__wrapped__`.

## Decorators and Introspection

Decorators can interfere with introspection if metadata is not preserved.

For example:

```python
import inspect


signature = inspect.signature(decorated_function)
```

A properly implemented decorator using `@wraps` allows Python tooling to follow the wrapped function through `__wrapped__`.

This matters for frameworks such as FastAPI, which inspect callable signatures and annotations as part of dependency and request handling.

## Import-Time Behavior

Decorators execute when their containing module's definitions are evaluated.

For example:

```python
@register_handler("user.created")
def handle_user_created(event):
    ...
```

may register the handler during module import.

This means importing a module can have side effects.

In production systems, be cautious with decorators that:

- Open network connections.
- Query databases.
- Register external resources.
- Perform expensive computation.
- Mutate global state.
- Depend on application startup order.

Prefer lightweight registration during import and explicit resource initialization during application startup.

## Decorators and Testing

Decorated functions should be tested at two levels.

### Test the Decorator Behavior

```python
def test_log_calls_preserves_result():
    @log_calls
    def operation() -> str:
        return "ok"

    assert operation() == "ok"
```

Also verify important semantics:

- Return value.
- Exceptions.
- Metadata.
- Invocation count.
- Arguments.
- Async behavior.
- Configuration.

### Test the Decorated Operation

Test the business behavior normally:

```python
def test_create_order():
    result = create_order(...)
    assert result.status == "created"
```

Do not over-test implementation details such as the exact number of nested wrappers unless that behavior is part of the contract.

## Testing Decorated Functions Directly

Because `@wraps` establishes `__wrapped__`, tests can sometimes access the underlying function:

```python
original = decorated_function.__wrapped__
```

This can be useful when testing business logic independently of infrastructure behavior.

However, do not routinely bypass decorators in application-level tests. The production callable includes the decorators, and integration behavior may depend on them.

Use direct access selectively.

## Security Considerations

Decorators frequently sit at security-sensitive boundaries.

Be careful with:

### Authorization

Ensure authorization decisions are based on trusted identity and permissions.

### Logging

Do not log secrets or sensitive payloads.

### Authentication

Do not assume a decorator is the only path to a function.

### Token Handling

Never place credentials into decorator configuration or source code.

### Dynamic Decorator Selection

Avoid selecting executable callables directly from untrusted input.

Prefer:

```python
handlers = {
    "create": create_handler,
    "delete": delete_handler,
}
```

with explicit validation.

## Reliability Considerations

Decorators can improve reliability when they provide well-defined policies, but they can also hide failure behavior.

For example:

```python
@retry(attempts=5)
def charge_card():
    ...
```

can be dangerous if `charge_card()` is not idempotent.

A retry can create:

```text
Attempt 1 --> payment succeeds
               |
               v
          response lost
               |
               v
Attempt 2 --> payment executed again
```

Use idempotency keys and provider-supported idempotency mechanisms for operations where duplicate execution has financial or stateful consequences.

Decorators should not conceal reliability semantics.

## Performance Considerations

Every decorator wrapper adds at least another Python-level call layer.

For example:

```text
caller
  |
  v
wrapper A
  |
  v
wrapper B
  |
  v
wrapper C
  |
  v
function
```

For normal backend operations dominated by database or network latency, this overhead is usually negligible.

For extremely hot CPU-bound paths, many wrapper layers can matter.

Potential costs include:

- Additional Python calls.
- Argument packing into `*args` and `**kwargs`.
- Logging.
- Metrics.
- Tracing.
- Locking.
- Cache lookups.

Measure before optimizing.

Avoid decorating tiny numerical operations with many expensive infrastructure wrappers if profiling shows they dominate runtime.

## Memory Considerations

Each decorated function creates additional callable objects and closure references.

A decorator can also retain references to:

- Configuration.
- Services.
- Clients.
- Caches.
- Large objects.

For long-lived application processes, inspect closure state when memory usage grows unexpectedly.

A particularly risky pattern is capturing request-scoped objects inside a decorator closure that lives for the lifetime of the application.

## Concurrency Considerations

Decorator state must be treated according to its execution scope.

This:

```python
def counter(func):
    count = 0

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal count
        count += 1
        return func(*args, **kwargs)

    return wrapper
```

is shared mutable state within the process.

In threaded code, updates may require synchronization depending on the required correctness guarantees.

In async code, shared state can still race across tasks when operations yield control.

Across multiple processes or Kubernetes pods, each process has its own state.

For distributed coordination, use an external system rather than decorator-local state.

## Scalability and Deployment

Decorator state is normally local to one Python process.

In a Kubernetes deployment:

```text
                Load Balancer
                      |
          +-----------+-----------+
          |           |           |
        Pod A       Pod B       Pod C
          |           |           |
       wrapper      wrapper      wrapper
       state A      state B      state C
```

Do not assume a decorator-created cache, counter, lock, or registry is shared across replicas.

For globally consistent behavior use appropriate shared infrastructure:

| Requirement | Typical Mechanism |
|---|---|
| Local memoization | `lru_cache` |
| Distributed cache | Redis |
| Distributed lock | Redis / database / specialized service |
| Durable state | PostgreSQL |
| Event coordination | Kafka |
| Background execution | Celery / queue |
| Metrics | Prometheus / CloudWatch-compatible telemetry |
| Distributed tracing | OpenTelemetry-compatible tooling |

## Decorators and Microservices

Decorators are local Python constructs.

They do not automatically propagate behavior across service boundaries.

For example:

```text
Service A
  |
  +--> @retry
  |
  +--> HTTP request
          |
          v
       Service B
          |
          +--> independent retry policy
```

If both services retry the same operation, retry amplification can occur.

Distributed retry policy should therefore be designed at the system level, not merely implemented independently through decorators.

## Decorators and Celery

Celery provides task abstractions that already include retry and execution lifecycle mechanisms.

Avoid duplicating task-level retry semantics with an unrelated generic decorator without understanding the interaction.

For example:

```python
@app.task(bind=True, autoretry_for=(ConnectionError,))
def process_event(self, event_id: int):
    ...
```

is generally clearer than layering an unrelated retry decorator on top of the task.

Framework-native lifecycle features should generally be preferred when they already express the required semantics.

## Decorators and Resource Management

A decorator can manage resource setup and cleanup:

```python
from functools import wraps


def with_resource(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        resource = acquire_resource()

        try:
            return func(resource, *args, **kwargs)
        finally:
            resource.close()

    return wrapper
```

This can work, but context managers are usually a more explicit abstraction for resource lifetime:

```python
with acquire_resource() as resource:
    process(resource)
```

Prefer the abstraction that makes ownership and cleanup easiest to understand.

## Common Mistakes

### Forgetting `@wraps`

This loses useful metadata and can interfere with frameworks and debugging.

### Swallowing Exceptions

Avoid:

```python
except Exception:
    return None
```

unless failure suppression is an explicit contract.

### Changing Return Semantics Accidentally

A wrapper should normally return the decorated function's result.

### Breaking Async Functions

A synchronous wrapper around an async function can return a coroutine instead of executing it correctly.

### Retrying Everything

Not every exception is transient, and not every operation is safe to retry.

### Logging Arguments Blindly

Arguments may contain credentials or sensitive data.

### Creating Hidden Global State

Decorator closures can introduce process-local state that is difficult to discover.

### Excessive Decoration

Many layers can make control flow difficult to understand.

### Performing Heavy Work at Import Time

Decorator execution happens during module initialization.

### Using Decorators to Hide Dependencies

Important collaborators should generally remain explicit through function arguments, constructors, or dependency injection.

## Production Pitfalls

| Pitfall | Why It Happens | Better Approach |
|---|---|---|
| `<lambda>`-like metadata issues | Wrapper metadata not preserved | Use `functools.wraps` |
| Broken framework introspection | Signature hidden by wrapper | Preserve metadata and signature |
| Retry storm | Unbounded or synchronized retries | Backoff, jitter, deadlines |
| Duplicate writes | Non-idempotent operation retried | Use idempotency |
| Secret leakage | Raw arguments logged | Structured, redacted logging |
| Inconsistent counters | Process-local closure state | Shared metrics/state system |
| Async failures | Sync wrapper around coroutine | Use async-aware wrapper |
| Import-time side effects | Decorator performs heavy work | Keep decoration lightweight |
| Hidden control flow | Many stacked decorators | Use middleware or explicit composition |
| Memory retention | Closure captures large objects | Review captured references |
| Transaction surprises | Decorator order changes boundary | Define transaction semantics explicitly |
| Cross-service retry amplification | Multiple independent retry layers | Design retry policy system-wide |

## When to Use Decorators

Decorators are a good fit when:

- The behavior is cross-cutting.
- The behavior applies consistently to selected callables.
- The wrapped function's contract remains understandable.
- The policy is reusable.
- The behavior is orthogonal to the function's core responsibility.

Examples:

```text
                    Decorator
                       |
        +--------------+--------------+
        |              |              |
      Logging       Metrics        Authorization
        |              |              |
        +--------------+--------------+
                       |
                  Business Logic
```

## When Not to Use Decorators

Prefer explicit code, middleware, dependency injection, or another abstraction when:

- The behavior is core business logic.
- The decorator hides important dependencies.
- The execution order becomes difficult to understand.
- The wrapper changes the function's contract substantially.
- State management becomes complex.
- Resource ownership is unclear.
- The operation requires explicit transaction boundaries.
- The decorator introduces significant hidden I/O.
- Framework-native lifecycle features already exist.

## Decorators vs Other Abstractions

| Problem | Good Default |
|---|---|
| Function-specific cross-cutting policy | Decorator |
| Entire HTTP request lifecycle | Middleware |
| Explicit service dependency | Dependency injection |
| Resource lifetime | Context manager |
| Reusable stateful behavior | Class / callable object |
| Data transformation | Function / composition |
| Distributed retry policy | Explicit resilience mechanism |
| Framework route registration | Framework decorator |
| Global application lifecycle | Framework lifecycle hooks |

## Senior Engineering Heuristic

A decorator is most valuable when it makes a policy **more reusable without making control flow less visible**.

Before adding one, ask:

1. Is this behavior cross-cutting?
2. Does it belong at the function boundary?
3. Is the behavior reusable?
4. Does it preserve the callable's contract?
5. Does it preserve metadata?
6. Does it work correctly for sync or async execution?
7. Does decorator ordering matter?
8. Does it introduce state?
9. Does that state need to be distributed?
10. Does the framework already provide a better mechanism?

If several answers indicate complexity, prefer a more explicit architecture.

## Interview Traps

### What Is a Decorator?

A decorator is a callable that receives another callable and returns a callable with modified or extended behavior.

### What Does `@decorator` Mean?

This:

```python
@decorator
def operation():
    ...
```

is approximately:

```python
operation = decorator(operation)
```

### When Does a Decorator Execute?

The decorator expression is evaluated when the function definition is executed, normally during module import.

The wrapper executes later when the decorated function is called.

### Why Is `functools.wraps` Important?

It preserves useful metadata and exposes `__wrapped__`, improving introspection, debugging, documentation, and framework compatibility.

### Why Do Decorators Often Have Three Nested Functions?

A parameterized decorator commonly has:

```text
factory(configuration)
    |
    v
decorator(function)
    |
    v
wrapper(*args, **kwargs)
```

The outer layer captures configuration, the middle layer receives the target function, and the inner layer executes when the function is called.

### What Is the Order of Multiple Decorators?

Given:

```python
@a
@b
def f():
    ...
```

the result is:

```python
f = a(b(f))
```

### Can Decorators Be Used with Async Functions?

Yes, but the wrapper must preserve async semantics and await the original coroutine.

### Are Decorators Global?

No. A decorator's closure state is normally local to the Python process containing the decorated function.

### Why Can Decorators Cause Memory Issues?

Closures can retain references to objects for as long as the decorated callable remains alive.

### Can Decorators Affect Performance?

Yes. Each wrapper adds execution overhead, and infrastructure behavior such as logging, metrics, tracing, locking, or cache access can add substantially more overhead.

## Production Checklist

Before introducing a decorator into production code, verify:

- The decorator represents a genuine cross-cutting concern.
- The function's primary responsibility remains clear.
- `functools.wraps` is used where appropriate.
- Return values are preserved.
- Exceptions are preserved or intentionally translated.
- Sync and async behavior are handled correctly.
- Decorator ordering has been reviewed.
- Function signatures remain discoverable where frameworks depend on introspection.
- Sensitive arguments are not logged.
- Retry behavior is limited to appropriate transient failures.
- Retried operations are safe or idempotent.
- Backoff, jitter, and deadlines are considered for retries.
- Process-local state is not mistaken for distributed state.
- Long-lived closures do not retain unnecessary resources.
- Import-time side effects are lightweight and intentional.
- Framework-native mechanisms are preferred when they already provide the required lifecycle.
- Decorator composition does not make control flow opaque.
- Tests cover wrapper behavior and the decorated operation.
- Performance overhead has been measured when the decorator is used on hot paths.

## Key Takeaways

- Decorators are callable transformations built on first-class functions and closures; `@decorator` is syntactic sugar for rebinding a function through a decorator.
- Use decorators primarily for reusable cross-cutting concerns such as logging, metrics, tracing, authorization, caching, and carefully designed resilience policies.
- Production decorators should preserve metadata with `functools.wraps`, preserve callable contracts, handle synchronous and asynchronous execution correctly, and make decorator ordering explicit.
- Decorator-local state is normally process-local, so it must not be treated as distributed state across threads, processes, Kubernetes pods, or microservices.
- Prefer middleware, dependency injection, context managers, framework lifecycle mechanisms, or explicit code when decorators would hide important dependencies, resource ownership, business logic, or execution flow.