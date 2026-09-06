# 18- Functools

## Overview

Python's `functools` module provides higher-order utilities for working with callable objects, function composition, caching, dispatch, comparison, and wrapper metadata.

The module is particularly relevant to backend engineering because many production concerns can be expressed as transformations around functions:

```text
Function
   │
   ├── Cache results ───────────► cache / lru_cache
   ├── Bind arguments ──────────► partial / partialmethod
   ├── Preserve metadata ───────► wraps / update_wrapper
   ├── Dispatch by type ────────► singledispatch
   ├── Adapt comparisons ──────► cmp_to_key
   ├── Generate ordering ───────► total_ordering
   └── Reduce a sequence ───────► reduce
```

`functools` builds on Python's first-class functions, closures, decorators, iterators, and callable objects. Understanding those concepts makes the module much easier to reason about.

The most important production-oriented utilities are:

| Utility | Primary Purpose |
|---|---|
| `partial()` | Pre-bind function arguments |
| `partialmethod()` | Pre-bind arguments for methods |
| `wraps()` | Preserve metadata in decorators |
| `update_wrapper()` | Explicit wrapper metadata control |
| `cache()` | Unbounded memoization |
| `lru_cache()` | Bounded or unbounded memoization |
| `cached_property()` | Lazy per-instance property caching |
| `reduce()` | Fold an iterable into one value |
| `singledispatch()` | Dispatch based on first argument type |
| `singledispatchmethod()` | Type-based dispatch for methods |
| `cmp_to_key()` | Adapt legacy comparison functions |
| `total_ordering()` | Generate missing ordering methods |

The central engineering principle is:

> `functools` should simplify function composition and reusable behavior without hiding important lifecycle, memory, concurrency, or correctness semantics.

---

## Why functools Matters

Functions are objects in Python. They can be:

- assigned
- passed as arguments
- returned from functions
- stored in collections
- wrapped
- cached
- partially applied
- dynamically dispatched

`functools` provides standardized implementations for common patterns that would otherwise require custom closures or decorators.

For example, instead of writing a custom closure to bind an argument:

```python
def create_user_handler(client):
    def handler(user_id):
        return client.get_user(user_id)

    return handler
```

you can use:

```python
from functools import partial

handler = partial(client.get_user)
```

Or bind explicit arguments:

```python
handler = partial(client.get_user, timeout=2.0)
```

The standard library implementation is clearer about the intent.

---

## Core API

A useful mental model is:

```text
                    functools
                        │
        ┌───────────────┼────────────────┐
        │               │                │
     Function         State           Metadata
        │               │                │
    partial          cache            wraps
    reduce           lru_cache         update_wrapper
    dispatch         cached_property
```

The functions solve different problems and should not be treated as interchangeable abstractions.

---

## partial

`functools.partial()` creates a new callable with some arguments of another callable pre-filled.

```python
from functools import partial


def create_connection(host: str, port: int, timeout: float) -> None:
    ...


connect_to_primary = partial(
    create_connection,
    host="db-primary.internal",
    port=5432,
    timeout=2.0,
)

connect_to_primary()
```

Conceptually:

```text
Original function
create_connection(host, port, timeout)

             │
             ▼
partial(... host=..., port=..., timeout=...)

             │
             ▼
New callable
connect_to_primary()
```

`partial` is useful when a function already has the desired behavior but a subset of its configuration should be fixed.

---

## Why partial Exists

Without `partial`, developers often create trivial wrapper functions:

```python
def connect_to_primary():
    return create_connection(
        host="db-primary.internal",
        port=5432,
        timeout=2.0,
    )
```

This is perfectly valid, but `partial` is useful when the wrapper adds no additional behavior.

Use `partial` when you need:

- argument binding
- callback configuration
- strategy configuration
- reusable function variants
- adapting a function to another callable interface

---

## partial Semantics

Given:

```python
from functools import partial


def request(
    client,
    path,
    timeout,
):
    ...


request_api = partial(
    request,
    client=client,
    timeout=2.0,
)
```

the resulting callable still accepts:

```python
request_api(path="/users")
```

A `partial` object exposes useful attributes:

```python
print(request_api.func)
print(request_api.args)
print(request_api.keywords)
```

These represent:

- original callable
- pre-bound positional arguments
- pre-bound keyword arguments

A `partial` is therefore an actual callable object rather than a special function syntax.

---

## partial and Argument Binding

Positional arguments are bound from the left.

```python
from functools import partial


def multiply(a: int, b: int, c: int) -> int:
    return a * b * c


multiply_by_10 = partial(multiply, 10)

print(multiply_by_10(2, 3))
```

This is equivalent to:

```python
multiply(10, 2, 3)
```

Keyword arguments can also be bound:

```python
multiply_with_a = partial(multiply, a=10)
```

The remaining arguments are supplied when the partial is called.

---

## partial and Backend Callbacks

`partial` is useful when APIs expect a callback with a particular shape.

```python
from functools import partial


def publish_event(producer, topic, event):
    producer.publish(topic, event)


publish_order_event = partial(
    publish_event,
    producer,
    "orders",
)
```

Now:

```python
publish_order_event(order_created_event)
```

This can simplify:

- event handlers
- task callbacks
- retry callbacks
- CLI command handlers
- test fixtures
- dependency configuration

---

## partial in FastAPI and Django

`partial` can adapt application behavior without creating unnecessary wrappers.

For example:

```python
from functools import partial


def build_response(serializer, data):
    return serializer(data)


json_response = partial(
    build_response,
    json_serializer,
)
```

However, do not use `partial` merely to make application code shorter. If a callable represents an important domain operation, a named function or class can be more readable and easier to type and document.

---

## partial and Python 3.14 Placeholder

Python 3.14 adds `functools.Placeholder`, which allows positional arguments to be reserved for later filling rather than only binding arguments from the left.

Conceptually:

```python
from functools import Placeholder, partial


def connect(host, port, timeout):
    ...


connect_with_defaults = partial(
    connect,
    Placeholder,
    5432,
    2.0,
)
```

The placeholder allows the first positional argument to remain open.

This is useful when partial application requires binding later positional parameters while leaving earlier positions available.

Production projects should verify their supported Python version before relying on `Placeholder`.

---

## partialmethod

`partialmethod()` is designed for methods defined on classes.

```python
from functools import partialmethod


class Client:
    def request(self, method: str, path: str):
        ...

    get = partialmethod(request, "GET")
    post = partialmethod(request, "POST")
```

Then:

```python
client = Client()

client.get("/users")
client.post("/users")
```

The instance is still correctly supplied as the method receiver.

This is useful for defining families of related methods that differ only by fixed arguments.

---

## partial vs Wrapper Function

| Requirement | `partial` | Wrapper Function |
|---|---|---|
| Bind arguments | Excellent | Excellent |
| Add logic | No | Yes |
| Custom error handling | Limited | Excellent |
| Logging | Not directly | Excellent |
| Rich type signature | Sometimes less explicit | Often clearer |
| Simple callback adaptation | Excellent | Good |
| Domain semantics | Sometimes weak | Often stronger |

Use `partial` when the operation is fundamentally:

> "Call this function with these arguments already fixed."

Use a named wrapper when additional behavior or domain meaning exists.

---

## wraps

`functools.wraps()` is essential when writing decorators.

Consider:

```python
def logging_decorator(func):
    def wrapper(*args, **kwargs):
        print("calling function")
        return func(*args, **kwargs)

    return wrapper
```

The wrapper does not automatically preserve metadata such as:

```python
__name__
__doc__
```

Using `wraps()`:

```python
from functools import wraps


def logging_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("calling function")
        return func(*args, **kwargs)

    return wrapper
```

Now the wrapper presents metadata associated with the original function.

---

## Why wraps Matters

Metadata is used by:

- debuggers
- documentation generators
- tracing systems
- testing tools
- framework introspection
- API frameworks
- dependency injection systems
- developer tooling

For example, FastAPI relies heavily on callable inspection.

A poorly implemented decorator can interfere with framework behavior if it fails to preserve the expected metadata or callable signature semantics.

The standard pattern is:

```python
from functools import wraps


def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
```

---

## How wraps Works

`wraps()` is essentially a convenience around `update_wrapper()`.

Conceptually:

```text
original function
      │
      ▼
wrapper function
      │
      └── metadata copied from original
```

The wrapper also receives:

```python
__wrapped__
```

which points to the wrapped callable.

This allows introspection tools such as `inspect.unwrap()` to recover the underlying function.

---

## update_wrapper

`update_wrapper()` provides explicit control over wrapper metadata.

```python
from functools import update_wrapper


def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    update_wrapper(wrapper, func)
    return wrapper
```

`wraps()` is generally more readable:

```python
@wraps(func)
def wrapper(...):
    ...
```

Use `update_wrapper()` when custom wrapper construction requires explicit metadata handling.

---

## Decorator Metadata and Signatures

`wraps()` preserves important metadata but does not magically make arbitrary wrapper behavior type-safe.

For typed decorators, use `ParamSpec` and `TypeVar`:

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def traced(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper
```

This allows static type checkers to preserve the original callable's parameter and return types.

---

## cache

`functools.cache()` provides unbounded memoization.

```python
from functools import cache


@cache
def calculate_rate(currency: str) -> float:
    return load_rate_from_source(currency)
```

Repeated calls with the same arguments can reuse the cached result.

Conceptually:

```text
calculate_rate("USD")
        │
        ▼
   cache lookup
      /     \
   hit       miss
    │          │
    ▼          ▼
 return     calculate
               │
               ▼
             cache
```

`cache()` is effectively an unbounded form of `lru_cache()`.

---

## cache vs lru_cache

| Feature | `cache()` | `lru_cache()` |
|---|---|---|
| Memoization | Yes | Yes |
| Maximum size | Unlimited | Configurable |
| Eviction | None | Least-recently-used |
| Simplicity | Higher | Higher control |
| Memory bounded | No | Yes with `maxsize` |
| Best for | Small stable domains | Potentially large key spaces |

Use `cache()` only when the key space and lifecycle are known to be safe.

---

## lru_cache

`lru_cache()` provides memoization with optional size limits.

```python
from functools import lru_cache


@lru_cache(maxsize=1_024)
def get_exchange_rate(currency: str) -> float:
    return load_rate_from_source(currency)
```

When the cache reaches its limit, less-recently-used entries are evicted.

This makes it safer than unbounded memoization when the input domain may grow.

---

## How lru_cache Works

Conceptually:

```text
             Function call
                  │
                  ▼
             Build cache key
                  │
                  ▼
             Cache lookup
             /          \
          hit            miss
           │               │
           ▼               ▼
      return value     execute function
                           │
                           ▼
                     store result
                           │
                           ▼
                       return
```

The cache stores function results based on the function's arguments.

This means cache correctness depends on argument identity and value semantics.

---

## lru_cache Key Requirements

Arguments used by the cache must be hashable.

This works:

```python
@lru_cache(maxsize=128)
def get_user(user_id: int):
    ...
```

This does not:

```python
@lru_cache(maxsize=128)
def process_users(user_ids: list[int]):
    ...
```

because lists are unhashable.

A tuple may work:

```python
@lru_cache(maxsize=128)
def process_users(user_ids: tuple[int, ...]):
    ...
```

But converting a mutable list to a tuple does not automatically make the underlying business operation safe to cache.

---

## Cache Key Semantics

Caching is based on function arguments.

These may represent distinct cache keys:

```python
@lru_cache
def calculate(value, scale=1):
    return value * scale
```

Calls involving different argument forms can have different cache-key representations depending on how the arguments are passed.

Do not assume every semantically equivalent call is necessarily the same cache entry.

For production systems, design stable, canonical arguments when cache efficiency matters.

---

## lru_cache with Methods

Caching instance methods can unintentionally retain instances.

```python
from functools import lru_cache


class Service:
    @lru_cache(maxsize=128)
    def calculate(self, value: int) -> int:
        return expensive_calculation(value)
```

The instance (`self`) participates in the cache key.

Therefore, cached entries can retain references to instances until those entries are evicted or the cache is cleared.

This can matter when:

- instances are created frequently
- instances contain large object graphs
- the cache has a large `maxsize`
- objects are expected to be garbage-collected

Do not casually apply `lru_cache` to instance methods in high-churn object lifecycles.

---

## Cache Lifecycle

`lru_cache()` provides:

```python
get_value.cache_info()
```

and:

```python
get_value.cache_clear()
```

Example:

```python
info = get_value.cache_info()

print(info.hits)
print(info.misses)
print(info.maxsize)
print(info.currsize)
```

This is useful for operational diagnostics.

A cache should have an intentional lifecycle.

Consider:

- startup state
- deployment behavior
- invalidation
- configuration changes
- memory limits
- worker restarts
- cache warming
- stale data

---

## Cache Invalidation

Function-level caching is easy to add and difficult to invalidate correctly when the underlying data changes.

Consider:

```python
@lru_cache(maxsize=1024)
def get_user(user_id: int):
    return database.load_user(user_id)
```

If the user changes in PostgreSQL:

```text
PostgreSQL
   │
   ├── user updated
   │
   ▼
Application cache
   │
   └── old value
```

The cached value may remain stale.

Possible strategies include:

```python
get_user.cache_clear()
```

or using a more appropriate cache architecture with explicit invalidation.

For distributed systems, Redis or another shared caching layer may be more appropriate.

---

## Function Cache vs Distributed Cache

| Requirement | `lru_cache` | Redis |
|---|---|---|
| Process-local | Excellent | Yes |
| Cross-process | No | Yes |
| Cross-pod | No | Yes |
| Persistent | No | Configurable |
| TTL support | No native TTL | Yes |
| Simple memoization | Excellent | More infrastructure |
| Shared invalidation | Limited | Supported |
| Network overhead | None | Yes |

A Python function cache is ideal for local deterministic computation or stable process-local data.

It is not a replacement for a distributed cache.

---

## Cache Threading Semantics

The standard caching decorators use internal locking to keep the underlying cache structure coherent.

However, this does not guarantee that the wrapped function executes only once when multiple threads miss the same key concurrently.

Conceptually:

```text
Thread A ── cache miss ──► compute
Thread B ── cache miss ──► compute
```

Both may perform the underlying computation before one result is stored.

Therefore, if the function has expensive side effects, `lru_cache` is not a general-purpose single-flight mechanism.

---

## Cache and Side Effects

Caching is generally appropriate for deterministic or safely repeatable computations.

Avoid caching functions whose result depends on hidden mutable state:

```python
@lru_cache(maxsize=128)
def get_current_user():
    return request_context.user
```

The cache key contains no representation of the request context.

The first result can therefore incorrectly become the result for later calls.

Likewise, avoid caching functions that:

- mutate state
- perform non-idempotent operations
- depend on current time
- depend on authentication context
- depend on request-local state
- depend on random values
- depend on mutable external resources without explicit invalidation

---

## cached_property

`cached_property` provides lazy attribute computation that is cached on an instance.

```python
from functools import cached_property


class UserProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id

    @cached_property
    def permissions(self) -> set[str]:
        return load_permissions(self.user_id)
```

The first access computes the value:

```python
profile.permissions
```

Subsequent access normally reads the cached instance attribute.

---

## cached_property Lifecycle

Conceptually:

```text
profile.permissions
        │
        ▼
attribute exists?
     /       \
   yes        no
   │           │
   ▼           ▼
return      compute
              │
              ▼
        store on instance
              │
              ▼
            return
```

This differs from `lru_cache`:

```text
lru_cache
    └── cache associated with callable arguments

cached_property
    └── cache associated with an instance attribute
```

---

## cached_property Invalidation

The cached value can be removed:

```python
del profile.permissions
```

The next access recomputes it.

This is useful when the underlying state changes:

```python
profile.refresh()
del profile.permissions
```

The exact invalidation policy should be part of the object's lifecycle design.

---

## cached_property and Memory

`cached_property` stores the computed value on the instance.

This means:

```python
instance
   │
   └── cached property value
```

The value remains as long as that instance retains the attribute.

If the value is large and many instances are long-lived, memory usage can grow significantly.

Use it for:

- expensive derived instance state
- stable per-instance calculations
- lazily loaded local metadata

Be cautious with:

- large datasets
- high-cardinality objects
- long-lived caches
- values that change frequently

---

## cached_property and Slots

`cached_property` requires an instance dictionary for its normal caching behavior.

A class using:

```python
__slots__ = (...)
```

without a `__dict__` generally cannot use `cached_property` in the standard way.

This matters when optimizing object memory with slots.

The choice becomes:

```text
Need cached_property?
        │
        ▼
Instance must support attribute storage
        │
        └── __dict__ generally required
```

If memory optimization requires slots without a dictionary, use an alternative caching strategy.

---

## reduce

`reduce()` repeatedly combines iterable elements into a single result.

```python
from functools import reduce
from operator import add

values = [1, 2, 3, 4]

result = reduce(add, values)

print(result)
```

Result:

```text
10
```

Conceptually:

```text
(((1 + 2) + 3) + 4)
```

The function receives:

```text
accumulator, current_value
```

and returns the next accumulator.

---

## reduce with Initial Value

An initializer can define the starting accumulator:

```python
from functools import reduce
from operator import mul

values = [2, 3, 4]

result = reduce(mul, values, 1)

print(result)
```

Result:

```text
24
```

The initial value is especially important for empty inputs.

```python
reduce(add, [], 0)
```

returns:

```text
0
```

Without an initializer, reducing an empty iterable raises `TypeError`.

---

## reduce vs Specialized Built-ins

Do not use `reduce()` automatically.

Prefer specialized operations when they express the intent more directly:

```python
sum(values)
```

instead of:

```python
reduce(add, values)
```

Similarly:

```python
any(values)
all(values)
max(values)
min(values)
```

are usually clearer than equivalent reductions.

Use `reduce()` when the operation genuinely represents a fold that does not have a clearer specialized primitive.

---

## reduce and Readability

This can be difficult to understand:

```python
result = reduce(
    lambda acc, item: acc.merge(item),
    items,
)
```

If the operation represents meaningful domain logic, a normal loop may be clearer:

```python
result = initial_state

for item in items:
    result = result.merge(item)
```

A senior engineer optimizes for:

- correctness
- readability
- maintainability
- testability

not merely functional style.

---

## reduce and Associativity

For some operations, order matters.

For:

```python
reduce(operator.add, values)
```

addition is associative for mathematical integers:

```text
(a + b) + c = a + (b + c)
```

But arbitrary business operations may not be.

For example:

```python
reduce(subtract, [100, 20, 10])
```

produces:

```text
70
```

but changing evaluation order can produce a different result.

This matters when considering parallel or distributed aggregation.

A reduction that is not associative and compatible with the required identity cannot generally be safely reordered.

---

## singledispatch

`singledispatch` implements generic functions whose implementation is selected according to the type of the first argument.

```python
from functools import singledispatch


@singledispatch
def serialize(value):
    raise TypeError(f"Unsupported type: {type(value).__name__}")


@serialize.register
def _(value: str) -> str:
    return value


@serialize.register
def _(value: int) -> str:
    return str(value)
```

Then:

```python
serialize("hello")
serialize(42)
```

dispatches to different implementations.

---

## Why singledispatch Exists

Without `singledispatch`, developers often write large conditional blocks:

```python
def serialize(value):
    if isinstance(value, str):
        ...
    elif isinstance(value, int):
        ...
    elif isinstance(value, User):
        ...
    else:
        ...
```

`singledispatch` separates implementations by type.

This can be useful for:

- serialization
- formatting
- adapters
- plugin-style behavior
- command handling
- domain transformations

---

## singledispatch Registration

Types can be registered explicitly:

```python
@serialize.register(int)
def _(value: int) -> str:
    return str(value)
```

Annotations can also provide the registered type:

```python
@serialize.register
def _(value: float) -> str:
    return f"{value:.2f}"
```

Multiple types can be registered independently.

---

## singledispatch Inheritance

Dispatch considers the first argument's type and follows method-resolution rules through its type hierarchy.

Therefore:

```python
class Animal:
    ...


class Dog(Animal):
    ...
```

A handler registered for `Animal` can act as a fallback for `Dog` if a more specific handler is not registered.

This makes `singledispatch` more flexible than a simple dictionary of exact types.

---

## singledispatch Does Not Dispatch on All Arguments

The name is important:

```text
single dispatch
```

Dispatch is based on the first argument after the function's binding semantics.

It does not natively implement arbitrary multiple-dispatch behavior.

For example:

```python
serialize(value, format)
```

does not automatically dispatch based on both `value` and `format`.

If behavior depends on multiple dimensions, consider:

- explicit strategy objects
- dictionaries of handlers
- protocols
- class-based polymorphism
- another dispatch design

---

## singledispatchmethod

`singledispatchmethod` provides similar behavior for methods.

```python
from functools import singledispatchmethod


class EventHandler:
    @singledispatchmethod
    def handle(self, event) -> None:
        raise TypeError(
            f"Unsupported event: {type(event).__name__}"
        )

    @handle.register
    def _(self, event: str) -> None:
        print(f"String event: {event}")

    @handle.register
    def _(self, event: int) -> None:
        print(f"Integer event: {event}")
```

The instance is not the dispatch target; dispatch is based on the appropriate method argument.

This can be useful for type-oriented handlers.

---

## singledispatch vs Polymorphism

| Approach | Best Fit |
|---|---|
| `singledispatch` | External generic operation over many types |
| Class polymorphism | Behavior naturally belongs to objects |
| Protocol | Behavior-based structural interface |
| Dictionary dispatch | Explicit finite command mapping |
| Pattern matching | Shape/value-based branching |

A useful architectural question is:

> Does the operation belong to the data type, or does the application need an external operation over many independent types?

`singledispatch` is often strongest for the second case.

---

## cmp_to_key

`cmp_to_key()` converts an old-style comparison function into a key function suitable for sorting.

A comparison function traditionally returns:

```text
negative → a < b
zero     → a == b
positive → a > b
```

Example:

```python
from functools import cmp_to_key


def compare_versions(left: str, right: str) -> int:
    ...


versions.sort(key=cmp_to_key(compare_versions))
```

Modern Python sorting prefers key functions directly:

```python
items.sort(key=lambda item: item.priority)
```

Use `cmp_to_key()` mainly when the comparison cannot be naturally expressed as a key or when adapting existing comparison logic.

---

## cmp_to_key and Performance

A key function is generally preferable because Python's sorting implementation can compute keys and reuse them during comparisons.

With:

```python
sorted(items, key=extract_key)
```

the key is computed for each element.

A comparison function adapted with:

```python
cmp_to_key(compare)
```

may perform comparison logic repeatedly.

Therefore, if the ordering can be represented as a key, prefer the key-based approach.

---

## total_ordering

`total_ordering` is a class decorator that fills in missing ordering methods when a class defines some ordering operations.

```python
from functools import total_ordering


@total_ordering
class Version:
    def __init__(self, value: int):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.value == other.value

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented
        return self.value < other.value
```

The decorator supplies other ordering operations based on the defined methods.

---

## total_ordering Trade-offs

`total_ordering` reduces boilerplate but can add complexity to generated comparison methods.

For performance-sensitive comparison-heavy code, explicitly implementing all required methods can be preferable.

Use it when:

- the class has meaningful ordering semantics
- reducing repetitive comparison methods improves maintainability
- comparison performance is not the dominant concern

Avoid using it automatically for every value object.

---

## Comparison Semantics

Comparison methods should return `NotImplemented` for unsupported types rather than incorrectly returning `False`.

```python
def __eq__(self, other):
    if not isinstance(other, Version):
        return NotImplemented
    return self.value == other.value
```

This allows Python's comparison machinery to try appropriate reflected behavior and ultimately produce the correct result.

This is more robust than:

```python
return False
```

for every unrelated type.

---

## partial, cache, and Decorators Together

These utilities can be composed.

For example:

```python
from functools import lru_cache, partial


@lru_cache(maxsize=512)
def get_feature_flag(
    config_service,
    feature_name: str,
) -> bool:
    return config_service.is_enabled(feature_name)


get_checkout_enabled = partial(
    get_feature_flag,
    config_service,
    "checkout-v2",
)
```

The resulting flow is:

```text
get_checkout_enabled()
        │
        ▼
partial
        │
        ▼
get_feature_flag(...)
        │
        ▼
lru_cache
        │
   ┌────┴────┐
   │         │
  hit       miss
   │         │
   ▼         ▼
 return   service call
```

This is powerful, but the cache lifecycle and invalidation requirements still apply.

---

## Decorator Composition

Multiple `functools` utilities can appear in backend code:

```python
from functools import lru_cache, wraps


def traced(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("calling %s", func.__name__)
        return func(*args, **kwargs)

    return wrapper


@traced
@lru_cache(maxsize=256)
def get_config(key: str) -> str:
    return load_config(key)
```

Decorator order matters.

The decoration process is conceptually:

```text
get_config
   │
   ▼
lru_cache
   │
   ▼
traced
   │
   ▼
final callable
```

Changing the order can change:

- what gets cached
- what gets logged
- what metadata is visible
- what arguments are observed
- how exceptions are handled

Always reason about decorator order explicitly.

---

## Caching and Backend Requests

A common temptation is to cache database or API calls:

```python
@lru_cache(maxsize=1024)
def get_user(user_id: int):
    return repository.get_user(user_id)
```

This can be valid for stable data, but production correctness requires answers to:

- How stale can the result be?
- When is it invalidated?
- Is the repository call deterministic?
- Is the returned object mutable?
- Can authorization affect the result?
- Is the cache process-local?
- What happens after deployment?
- What is the maximum memory usage?

A cache is not merely a performance optimization. It changes the consistency model.

---

## Cached Objects and Mutation

Caching mutable objects can introduce subtle bugs.

Consider:

```python
@lru_cache(maxsize=128)
def get_settings() -> dict:
    return load_settings()
```

Then:

```python
settings = get_settings()
settings["timeout"] = 1
```

The cached object has now been mutated.

Future callers can observe the modified value.

Safer alternatives include:

- immutable return values
- defensive copies
- immutable dataclasses
- explicit cache boundaries

For example:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    timeout: int
```

Immutable cached values are easier to reason about.

---

## Cache Security

Caching can create security vulnerabilities when security-sensitive context is omitted from the cache key.

Dangerous pattern:

```python
@lru_cache(maxsize=1024)
def get_account(account_id: int):
    return load_account_for_current_user(account_id)
```

The authenticated identity is not part of the key.

Potentially:

```text
User A
   │
   ▼
get_account(42)
   │
   ▼
cache stores A's result


User B
   │
   ▼
get_account(42)
   │
   ▼
receives cached A result
```

Never cache authorization-sensitive results unless the cache key incorporates every relevant security dimension and the lifecycle is correct.

For many request-scoped authorization decisions, avoiding global function caching is safer.

---

## Memory and Cache Sizing

A cache with:

```python
@lru_cache(maxsize=100_000)
```

may retain a large amount of memory.

Actual memory usage depends on:

- number of entries
- key size
- value size
- object graph size
- Python object overhead
- references retained by values

Do not choose `maxsize` arbitrarily.

A practical process is:

1. Estimate expected cardinality.
2. Estimate typical key/value size.
3. Measure cache hit rate.
4. Measure process RSS/heap behavior.
5. Tune `maxsize`.
6. Monitor eviction and memory impact.

Caching is useful only when the saved work justifies the retained memory.

---

## Observability

Function-level caches should be observable when they affect production behavior.

For `lru_cache`:

```python
info = get_user.cache_info()

logger.info(
    "user cache statistics",
    extra={
        "hits": info.hits,
        "misses": info.misses,
        "current_size": info.currsize,
        "max_size": info.maxsize,
    },
)
```

Useful metrics include:

- hit rate
- miss rate
- cache size
- eviction rate
- computation latency
- stale-result rate
- memory usage

A high cache hit rate is not automatically good if cached values are stale or security-sensitive.

---

## Testing functools-Based Code

Test behavior rather than implementation details.

### Testing Cached Functions

```python
from functools import lru_cache


calls = 0


@lru_cache(maxsize=16)
def calculate(value: int) -> int:
    global calls
    calls += 1
    return value * 2
```

A test can verify repeated calls reuse the cached result:

```python
def test_cache_reuses_result():
    calculate.cache_clear()

    assert calculate(10) == 20
    assert calculate(10) == 20
    assert calls == 1
```

Reset cache state between tests.

Otherwise, one test can influence another through retained cache entries.

---

## Testing Decorators

Use `wraps()` and test both behavior and metadata:

```python
def test_decorator_preserves_metadata():
    @traced
    def calculate(value: int) -> int:
        """Calculate a value."""
        return value * 2

    assert calculate.__name__ == "calculate"
    assert calculate.__doc__ == "Calculate a value."
```

Also test:

- return values
- exceptions
- positional arguments
- keyword arguments
- async functions when applicable
- decorator ordering

---

## functools and Async Code

Most `functools` utilities are synchronous abstractions.

`lru_cache` can technically wrap an `async def`, but this generally caches the coroutine object rather than the awaited result:

```python
@lru_cache
async def get_data():
    ...
```

This is usually not the desired async caching behavior.

Do not assume:

```python
@lru_cache
async def ...
```

creates an async result cache.

For asynchronous backend applications, use an async-aware caching strategy when the cached value represents awaited I/O.

Similarly, `partial()` can wrap an async function, but it does not make execution asynchronous by itself.

---

## functools and FastAPI

FastAPI uses callable inspection extensively, making decorator correctness important.

A decorator should preserve metadata:

```python
from functools import wraps


def audit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.info("calling endpoint", extra={"endpoint": func.__name__})
        return await func(*args, **kwargs)

    return wrapper
```

For framework-managed dependencies and route handlers, avoid decorators that:

- change signatures unexpectedly
- swallow exceptions
- alter return values
- hide metadata
- mix synchronous and asynchronous execution incorrectly

Framework integration should be tested using the actual framework request lifecycle.

---

## functools and Django

`functools` is commonly useful for:

- decorators around views
- cached computations
- callback binding
- reusable service configuration
- ordering helpers

However, Django's own caching framework should generally be used for application-level shared caching rather than `lru_cache` when the requirement includes:

- cross-process caching
- TTL
- shared invalidation
- distributed deployment

The appropriate layer depends on the scope of the state.

---

## functools and PostgreSQL

Do not use Python-level caching or reduction as a substitute for efficient database operations.

For example, instead of:

```python
total = reduce(
    lambda acc, row: acc + row.amount,
    rows,
    0,
)
```

a large dataset may be better aggregated in PostgreSQL:

```sql
SELECT SUM(amount)
FROM orders;
```

The database can often:

- scan indexed data efficiently
- aggregate close to the data
- reduce network transfer
- avoid loading all rows into Python

`functools` is most useful for application-level behavior that genuinely belongs in Python.

---

## functools and Redis

A local:

```python
@lru_cache(maxsize=1024)
```

is appropriate when the cache is:

```text
Pod-local
```

Redis is more appropriate when the cache must be:

```text
shared across replicas
        │
        ├── Pod A
        ├── Pod B
        └── Pod C
```

A common architecture is:

```text
Request
   │
   ▼
Application
   │
   ├── local cache
   │
   └── Redis
          │
          ▼
      PostgreSQL
```

The local cache can reduce repeated Redis/database access, while Redis provides shared state.

This introduces additional invalidation and consistency considerations and should be justified by measured performance requirements.

---

## functools and Celery

Be careful when using cached functions in Celery workers.

Each worker process may have its own cache:

```text
Celery
 ├── Worker A ── local cache
 ├── Worker B ── local cache
 └── Worker C ── local cache
```

A cache update in Worker A does not automatically affect Worker B.

Worker restarts also clear process-local caches.

Therefore, `lru_cache` should not be relied upon for distributed task coordination or shared task state.

---

## Process and Deployment Semantics

Function caches exist inside a Python process.

When the process terminates:

```text
process memory
     │
     ▼
destroyed
```

This happens during:

- Kubernetes pod replacement
- application deployment
- worker restart
- crash recovery
- autoscaling

This can be desirable because the cache naturally resets, but it means the application should not depend on cache contents for correctness.

The cache should normally be an optimization rather than the authoritative state.

---

## Reliability Considerations

Caching can improve reliability by reducing load on dependencies, but stale or incorrect cache behavior can also amplify failures.

Consider:

```text
Application
    │
    ▼
Cache hit
    │
    └── dependency unavailable
         │
         └── request still succeeds
```

This can be useful.

But:

```text
Application
    │
    ▼
stale cache
    │
    ▼
incorrect business decision
```

may be worse than a failed request.

Therefore, define whether cached data is:

- advisory
- eventually consistent
- authoritative
- security-sensitive
- acceptable when stale

---

## High Availability

Local `functools` caches are not highly available state.

They can improve service availability by reducing dependency traffic, but they do not replicate automatically.

For high-availability systems:

```text
                    Load Balancer
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            Pod A      Pod B      Pod C
              │          │          │
           local       local       local
           cache       cache       cache
              │          │          │
              └──────────┼──────────┘
                         ▼
                       Redis
                         │
                         ▼
                    PostgreSQL
```

The shared cache or database should remain the authoritative source where required.

---

## Maintainability Guidelines

Use `functools` when it makes the abstraction clearer.

Good:

```python
from functools import partial

send_to_orders = partial(
    send_event,
    topic="orders",
)
```

Less useful:

```python
do_this = partial(
    very_complex_function,
    a,
    b,
    c,
    d,
)
```

where the resulting callable obscures what the operation means.

Likewise, avoid excessive decorator stacking:

```python
@a
@b
@c
@d
@e
def process():
    ...
```

If behavior becomes difficult to reason about, move cross-cutting concerns into clearer middleware, service abstractions, or explicit composition.

---

## Common Mistakes

### Forgetting wraps

Bad:

```python
def decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
```

Better:

```python
from functools import wraps


def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
```

### Unbounded cache

```python
@cache
def process(user_input):
    ...
```

If `user_input` has unbounded cardinality, memory can grow continuously.

### Caching mutable results

```python
@lru_cache
def get_config():
    return {}
```

Callers can mutate the cached object.

### Caching request-specific state

```python
@lru_cache
def get_current_user():
    ...
```

This can leak one request's result into another request.

### Caching side effects

```python
@lru_cache
def send_payment():
    ...
```

Caching can prevent expected execution entirely.

### Assuming cache means distributed

Each process has its own cache.

### Using reduce when sum is clearer

```python
reduce(add, values)
```

is usually less clear than:

```python
sum(values)
```

### Assuming lru_cache prevents duplicate concurrent computation

Concurrent misses can still execute the wrapped function more than once.

---

## Production Pitfalls

| Pitfall | Impact | Better Approach |
|---|---|---|
| Unbounded `cache()` | Memory growth | Use bounded cache or external cache |
| Caching mutable objects | Shared accidental mutation | Cache immutable values |
| Missing security context in key | Data leakage | Include all relevant identity dimensions or avoid cache |
| Caching request-local state | Cross-request contamination | Keep request state outside global caches |
| Stale database results | Incorrect behavior | Define invalidation/TTL strategy |
| Caching async functions with `lru_cache` | Coroutine-object caching | Use async-aware caching |
| Caching instance methods | Retains instances | Review lifecycle and cache scope |
| Excessive decorator stacking | Difficult control flow | Consolidate or use middleware |
| `reduce()` everywhere | Reduced readability | Prefer specialized built-ins |
| Local cache as shared state | Inconsistent replicas | Use Redis/database |
| Ignoring cache metrics | Invisible memory/performance issues | Monitor hits, misses, size, latency |
| Treating cache as source of truth | Reliability problems | Keep authoritative state elsewhere |

---

## Performance Considerations

`functools` can improve performance by:

- avoiding repeated computation
- reducing object construction
- reducing dependency calls
- reusing bound callables
- simplifying callback dispatch

But it also introduces overhead and retained state.

For caching, the effective value is roughly:

```text
benefit
=
avoided computation/dependency cost
-
cache lookup cost
-
memory cost
-
staleness/invalidation cost
```

A cache that has a very low hit rate may add complexity without meaningful benefit.

Measure:

- hit rate
- miss latency
- cache lookup latency
- memory consumption
- dependency load
- end-to-end request latency

---

## Memory Considerations

The most important memory-related utilities are:

```text
cache
lru_cache
cached_property
tee-like retained state elsewhere
```

For `cache()`:

```text
entries
   │
   └── grow without eviction
```

For `lru_cache(maxsize=N)`:

```text
entries
   │
   └── bounded by configured cache size
```

For `cached_property`:

```text
instance
   │
   └── cached value
```

The correct choice depends on lifecycle and cardinality.

---

## Security Considerations

When using `functools` in production, explicitly evaluate:

- whether cache keys contain authorization context
- whether cached values contain secrets
- whether mutable cached objects can be modified
- whether user-controlled inputs can create unlimited cache entries
- whether cache contents can survive longer than expected
- whether wrappers accidentally expose sensitive arguments in logs
- whether decorator ordering bypasses authorization or validation

A particularly dangerous design is placing caching outside an authorization boundary:

```text
Request
   │
   ▼
Cache
   │
   ▼
Authorization
```

If the cached result bypasses authorization, the cache can become a security boundary accidentally.

Prefer:

```text
Request
   │
   ▼
Authentication
   │
   ▼
Authorization
   │
   ▼
Cache / Data access
```

when the cached value depends on authorization context.

---

## Interview Traps

### What is partial application?

It creates a callable with some arguments of another callable already bound.

### What is the difference between partial and a closure?

Both can capture configuration, but `partial` directly represents argument binding while a closure can implement arbitrary behavior and state.

### Why should decorators use wraps?

To preserve important metadata such as `__name__`, `__doc__`, and the `__wrapped__` relationship used by introspection tools.

### What does lru_cache cache?

It caches function results keyed by the function's arguments, subject to the configured cache size and cache-key semantics.

### Is lru_cache a distributed cache?

No. It is process-local.

### Does lru_cache guarantee one computation per key?

No. The cache structure is protected for coherent operation, but concurrent misses can still cause multiple underlying executions.

### Why can caching an instance method retain objects?

`self` participates in the cache key, so cached entries can retain references to instances.

### What is the difference between cache and lru_cache?

`cache()` is unbounded memoization. `lru_cache()` supports configurable maximum size and LRU eviction.

### What happens when reduce receives an empty iterable?

Without an initializer, it raises `TypeError`. With an initializer, the initializer becomes the result for an empty input.

### When should reduce be avoided?

When a specialized operation such as `sum()`, `any()`, `all()`, `max()`, or a normal loop communicates the intent more clearly.

### What does singledispatch dispatch on?

The type of the first argument to the generic function.

### Is singledispatch multiple dispatch?

No. It dispatches on one argument.

### Why is cmp_to_key less preferred than a key function?

Key functions usually express sorting intent more directly and avoid repeatedly invoking comparison logic.

### What does total_ordering provide?

It generates missing ordering methods from a smaller set of explicitly implemented comparison methods.

### Can lru_cache safely cache async functions?

Not as a general async result cache. Applying it directly to an `async def` caches coroutine objects rather than providing the expected awaited-result caching semantics.

---

## Senior-Level Design Heuristics

When using `functools`, ask:

1. Is this callable transformation making the code clearer?
2. Is the function deterministic enough to cache?
3. What defines the cache key?
4. What is the maximum key cardinality?
5. How large are cached values?
6. When does cached data become stale?
7. How is cache invalidation performed?
8. Does the cache need to be shared between processes?
9. Could cached values contain authorization-sensitive information?
10. Does a decorator preserve metadata and type information?
11. Does decorator order change security or reliability behavior?
12. Does `reduce()` make the algorithm clearer than a normal loop?
13. Does dispatch belong to the data type or to an external operation?
14. Would a protocol or polymorphic object provide a stronger abstraction?
15. What happens to the behavior during deployment, restart, or horizontal scaling?

The strongest use of `functools` is not clever functional programming.

It is reducing repeated implementation while keeping runtime behavior explicit and predictable.

---

## Decision Guide

```text
Need to adapt a callable?
          │
          ├── Bind arguments ───────────► partial
          │
          ├── Bind method arguments ────► partialmethod
          │
          ├── Decorate function
          │       │
          │       └── Preserve metadata ► wraps
          │
          ├── Cache computation
          │       │
          │       ├── Small bounded cache ─► lru_cache
          │       ├── Stable tiny domain ──► cache
          │       └── Per-instance value ──► cached_property
          │
          ├── Fold iterable ─────────────► reduce
          │
          ├── Dispatch by type
          │       │
          │       ├── Function ───────────► singledispatch
          │       └── Method ─────────────► singledispatchmethod
          │
          ├── Adapt comparator ───────────► cmp_to_key
          │
          └── Generate ordering methods ──► total_ordering
```

Then evaluate the system boundary:

```text
Is the state process-local?
       │
       ├── Yes ──► functools may be appropriate
       │
       └── No ───► consider Redis / PostgreSQL /
                    Kafka / dedicated infrastructure
```

---

## Production Checklist

Before using a `functools` utility in production, verify:

- `partial()` is used for genuine argument binding rather than hiding domain logic.
- `partialmethod()` is appropriate for method-level argument binding.
- Decorators use `wraps()` unless there is a deliberate reason not to.
- Typed decorators preserve callable signatures with `ParamSpec` where appropriate.
- Cache keys contain every input that materially affects the result.
- Cached functions are deterministic or have explicitly controlled invalidation.
- Mutable cached values cannot be accidentally modified by callers.
- Cache cardinality is bounded or demonstrably safe.
- Cache memory usage is understood.
- `cache()` is not used for unbounded user-controlled input.
- Instance-method caching does not unintentionally retain large object graphs.
- Cache invalidation behavior is defined.
- Process-local caches are not treated as shared or durable state.
- Async functions are not incorrectly cached with synchronous memoization semantics.
- Security-sensitive results are not reused across incompatible authorization contexts.
- `reduce()` is used only when it improves the expression of the algorithm.
- `singledispatch` is used where type-based external operations are appropriate.
- `cmp_to_key()` is used only when a key function is insufficient.
- `total_ordering` is avoided in performance-critical comparison paths when explicit methods are preferable.
- Cache metrics and relevant performance signals are observable.
- Tests clear global caches where required to maintain test isolation.
- Deployment, restart, scaling, and failure behavior remains correct without cached state.

## Key Takeaways

- `functools` provides standard building blocks for argument binding, decorators, caching, reduction, dispatch, and comparison; use them to express reusable behavior rather than to make code merely more functional.
- `partial()` simplifies argument binding, while `wraps()` is essential for preserving decorator metadata and framework introspection behavior.
- `cache()`, `lru_cache()`, and `cached_property` introduce retained state, so cache cardinality, memory usage, invalidation, staleness, mutability, and process lifecycle must be designed explicitly.
- Function-level caching is process-local and is not a replacement for Redis or other shared infrastructure; never assume local cache state is durable or synchronized across Kubernetes replicas or workers.
- At senior level, evaluate `functools` abstractions against correctness, security, concurrency, observability, and lifecycle requirements—not just readability or micro-performance.