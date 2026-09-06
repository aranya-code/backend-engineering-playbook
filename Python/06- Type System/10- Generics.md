# 10- Generics

## Overview

Generics allow Python code to operate over multiple types while preserving precise relationships between those types.

A generic abstraction is not simply "code that accepts anything." The important property is that the abstraction can express how its input, output, attributes, and operations relate to one another.

For example:

```python
def first[T](items: list[T]) -> T:
    return items[0]
```

The same function works for:

```python
first([1, 2, 3])          # int
first(["a", "b", "c"])     # str
first([User(...)])         # User
```

The generic parameter `T` preserves the element type through the operation.

Generics are useful for building reusable infrastructure without falling back to `Any`, while still allowing application-specific types to flow through the abstraction.

In backend engineering, common generic abstractions include:

- repositories
- pagination
- API response wrappers
- caches
- event envelopes
- result types
- serializers
- collections
- dependency providers
- middleware
- adapters

The core principle is:

```text
Generic abstraction
        │
        ▼
Reusable implementation
        │
        ├── User
        ├── Order
        ├── Payment
        └── Other concrete types
                │
                ▼
       Type relationship preserved
```

---

## Why Generics Matter

Without generics, reusable code often becomes overly broad:

```python
def get_first(items: list[Any]) -> Any:
    return items[0]
```

The implementation works, but the type checker cannot preserve the relationship between the collection and the returned value.

A generic version:

```python
def get_first[T](items: list[T]) -> T:
    return items[0]
```

communicates:

> The returned value has the same type as the elements in the input list.

This improves:

- static correctness
- IDE support
- refactoring safety
- API readability
- reusable infrastructure
- documentation
- maintainability

Generics are most valuable when the same implementation genuinely applies to multiple types.

---

## Generic Thinking

A useful mental model is:

```text
Concrete implementation

Repository[User]
Repository[Order]
Repository[Payment]

        │

One abstraction

Repository[T]
```

`T` represents a placeholder for a concrete type selected by the caller or specialization.

For example:

```python
class Repository[T]:
    ...
```

can represent:

```python
Repository[User]
Repository[Order]
```

The implementation remains reusable while the type system preserves what the repository contains.

---

## Generic Function

A generic function introduces a type parameter.

Modern Python syntax:

```python
def identity[T](value: T) -> T:
    return value
```

Equivalent older syntax:

```python
from typing import TypeVar


T = TypeVar("T")


def identity(value: T) -> T:
    return value
```

The generic relationship is:

```text
input:  T
          │
          ▼
      identity()
          │
          ▼
output: T
```

If the input is `User`, the output is `User`.

---

## Generic Class

A class can also be parameterized:

```python
class Repository[T]:
    def __init__(self, items: list[T]) -> None:
        self._items = items

    def get(self, index: int) -> T:
        return self._items[index]
```

Usage:

```python
users: Repository[User]
orders: Repository[Order]
```

The class implementation is shared while its concrete type parameter differs.

---

## Generic Type Parameters

Python 3.12 introduced dedicated type parameter syntax.

Generic function:

```python
def first[T](items: list[T]) -> T:
    return items[0]
```

Generic class:

```python
class Repository[T]:
    ...
```

Generic alias:

```python
type Page[T] = list[T]
```

This syntax is more localized than the traditional:

```python
T = TypeVar("T")
```

style.

For Python versions before 3.12, use `TypeVar` and `Generic`.

---

## TypeVar-Based Generics

The traditional approach remains important for existing systems:

```python
from typing import Generic, TypeVar


T = TypeVar("T")


class Repository(Generic[T]):
    def get(self, entity_id: int) -> T | None:
        raise NotImplementedError
```

Then:

```python
class UserRepository(Repository[User]):
    ...
```

This is the primary pattern for Python versions that predate the type-parameter syntax.

---

## Generic Collections

Built-in collections support generic parameters:

```python
list[int]
dict[str, User]
set[str]
tuple[int, str]
```

These are generic types.

For example:

```python
users: list[User]
users_by_id: dict[int, User]
```

This is simpler than defining a custom generic class when the built-in collection already expresses the required abstraction.

---

## Generic Interfaces

Generic interfaces allow the caller's concrete type to flow through an abstraction.

For example:

```python
from collections.abc import Iterable


class Repository[T]:
    def find_all(self) -> Iterable[T]:
        ...
```

Then:

```python
user_repository: Repository[User]
```

means:

```python
find_all() -> Iterable[User]
```

The same interface can be used for another entity:

```python
order_repository: Repository[Order]
```

which gives:

```python
find_all() -> Iterable[Order]
```

---

## Generic Pagination

Pagination is a strong backend use case.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    next_cursor: str | None
```

Now:

```python
Page[User]
Page[Order]
Page[Payment]
```

all use the same pagination abstraction.

The important relationship is:

```text
Page[T]
   │
   ├── items: list[T]
   │
   └── next_cursor: str | None
```

The pagination mechanism does not need to know anything about the concrete item type.

---

## Generic API Response

A response envelope can also be generic:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiResponse[T]:
    data: T
    request_id: str
```

Then:

```python
ApiResponse[User]
ApiResponse[list[User]]
ApiResponse[Order]
```

This is useful for internal service layers.

For public REST APIs, avoid automatically wrapping every response in a generic envelope if the API contract does not benefit from it.

---

## Generic Result Types

A result abstraction can preserve the successful value type:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Success[T]:
    value: T


@dataclass(frozen=True)
class Failure:
    message: str


type Result[T] = Success[T] | Failure
```

Then:

```python
Result[User]
Result[Order]
Result[Payment]
```

The successful branch retains its concrete type.

This can be useful when explicit success/failure values are part of the application's design.

Do not introduce result wrappers everywhere if Python exceptions already provide a clearer error model.

---

## Generic Type Aliases

Generic aliases package reusable type relationships.

```python
type HandlerMap[T] = dict[
    str,
    Callable[[T], None],
]
```

Then:

```python
HandlerMap[UserCreated]
HandlerMap[OrderCreated]
```

A generic alias is appropriate when the underlying structure is sufficient and no runtime behavior is required.

If the abstraction needs state or methods, a generic class may be better.

---

## Generic Classes vs Generic Type Aliases

Consider:

```python
type Cache[T] = dict[str, T]
```

versus:

```python
class Cache[T]:
    def get(self, key: str) -> T | None:
        ...
```

Use the alias when the dictionary itself is the abstraction.

Use the class when the abstraction needs:

- methods
- validation
- TTL behavior
- metrics
- synchronization
- serialization
- eviction
- lifecycle management

Do not create a generic class merely to rename a built-in collection.

---

## Generic Methods

A class can be generic while methods introduce their own relationships.

For example:

```python
class Converter:
    def convert[T](self, value: T) -> T:
        return value
```

The method-level `T` is independent of any class-level type parameter.

This distinction matters in larger APIs:

```text
Class type parameter
    → relationship shared by the instance

Method type parameter
    → relationship specific to one method
```

Avoid accidentally coupling unrelated types by placing a type variable at the wrong scope.

---

## Multiple Type Parameters

Generics can represent multiple independent relationships.

```python
class Pair[K, V]:
    def __init__(self, key: K, value: V) -> None:
        self.key = key
        self.value = value
```

This can represent:

```python
Pair[str, int]
Pair[int, User]
Pair[UUID, Order]
```

The relationship is:

```text
K → key type
V → value type
```

This is useful when two or more type dimensions are genuinely independent.

---

## Generic Mapping

Generic mappings are a common example:

```python
from collections.abc import Mapping


def get_value[K, V](
    mapping: Mapping[K, V],
    key: K,
) -> V:
    return mapping[key]
```

The type relationships are:

```text
mapping: Mapping[K, V]
key:     K
result:  V
```

This is more precise than:

```python
def get_value(
    mapping: Mapping[object, object],
    key: object,
) -> object:
    ...
```

---

## Generic Protocols

Protocols can themselves be generic.

```python
from typing import Protocol


class Serializer[T](Protocol):
    def serialize(self, value: T) -> bytes:
        ...
```

Implementations can then specialize the contract:

```text
Serializer[User]
Serializer[Order]
Serializer[Event]
```

This is powerful for dependency inversion because the application depends on a behavioral contract rather than a concrete serializer implementation.

---

## Generic Repository Pattern

A generic repository might look like:

```python
from abc import ABC, abstractmethod


class Repository[T](ABC):
    @abstractmethod
    def get(self, entity_id: int) -> T | None:
        ...

    @abstractmethod
    def save(self, entity: T) -> T:
        ...
```

A specialized repository:

```python
class UserRepository(Repository[User]):
    ...
```

This communicates:

```text
UserRepository
       │
       ▼
Repository[User]
       │
       ├── get() → User | None
       └── save(User) → User
```

The generic abstraction is useful when the operations and semantics genuinely apply across multiple entities.

---

## Generic Repository Limitations

A generic repository can become an architectural smell if every database operation is forced through a generic CRUD abstraction.

Real entities often have different query requirements:

```text
User
    → find_by_email()

Order
    → find_open_orders()

Payment
    → find_pending_payments()
```

A generic:

```python
Repository[T]
```

does not automatically model these domain-specific operations.

A senior design should use generics for common infrastructure while keeping domain-specific behavior explicit.

---

## Generic Dependency Injection

Generic providers can preserve the dependency type:

```python
class Provider[T]:
    def get(self) -> T:
        raise NotImplementedError
```

Then:

```python
class UserProvider(Provider[User]):
    ...
```

This can improve static checking in dependency injection infrastructure.

FastAPI already provides dependency injection mechanisms, so custom generic providers should be introduced only when they solve a real architectural problem.

---

## Generic Event Envelopes

Distributed systems can use generic event envelopes:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Event[T]:
    event_type: str
    version: int
    payload: T
```

Then:

```python
Event[UserCreated]
Event[OrderCreated]
```

The event envelope remains generic while the payload is strongly typed.

However, Kafka consumers still receive runtime bytes.

The actual pipeline remains:

```text
Kafka bytes
    │
    ▼
Deserializer
    │
    ▼
Schema validation
    │
    ▼
Event[T]
    │
    ▼
Business logic
```

Generic typing does not replace schema validation.

---

## Generic Caching

A generic cache abstraction can preserve value types:

```python
class Cache[T]:
    def get(self, key: str) -> T | None:
        ...

    def set(self, key: str, value: T) -> None:
        ...
```

Usage:

```python
user_cache: Cache[User]
order_cache: Cache[Order]
```

In a Redis-backed implementation, the generic parameter exists only at the application typing layer.

The Redis boundary still requires:

- serialization
- deserialization
- validation
- schema versioning
- TTL management
- invalidation
- failure handling

---

## Generic Serialization

A serializer can preserve the model type:

```python
from collections.abc import Callable


class Serializer[T]:
    def __init__(
        self,
        encode: Callable[[T], bytes],
        decode: Callable[[bytes], T],
    ) -> None:
        self.encode = encode
        self.decode = decode
```

Then:

```python
Serializer[User]
Serializer[Order]
```

The type relationship ensures:

```text
encode: T → bytes
decode: bytes → T
```

The implementation still needs to ensure the serialized representation is actually compatible with the expected model.

---

## Generic Pydantic Adapters

Generic infrastructure can preserve Pydantic model types:

```python
from pydantic import BaseModel


class ModelLoader[T: BaseModel]:
    def __init__(self, model_type: type[T]) -> None:
        self.model_type = model_type

    def load(self, payload: object) -> T:
        return self.model_type.model_validate(payload)
```

Then:

```python
loader = ModelLoader(UserResponse)
```

can produce:

```python
UserResponse
```

This combines:

```text
Generic typing
    +
Runtime validation
```

which is often appropriate at backend boundaries.

---

## Generic HTTP Clients

An internal HTTP client can model response payloads generically:

```python
class ApiResponse[T]:
    def __init__(
        self,
        data: T,
        status_code: int,
    ) -> None:
        self.data = data
        self.status_code = status_code
```

Then:

```python
ApiResponse[User]
ApiResponse[list[Order]]
```

can preserve application-level response types.

The HTTP client must still validate the actual response body.

---

## Generic Database Results

Database adapters can represent typed rows:

```python
class QueryResult[T]:
    def __init__(self, rows: list[T]) -> None:
        self.rows = rows
```

Then:

```python
QueryResult[UserRow]
QueryResult[OrderRow]
```

This is useful when a repository converts raw database records into validated application representations.

Do not assume a generic annotation automatically validates a database row.

---

## Generic Celery Results

Background-job abstractions can preserve result types:

```python
class TaskResult[T]:
    def __init__(self, value: T) -> None:
        self.value = value
```

For example:

```python
TaskResult[Report]
TaskResult[User]
```

However, Celery serializes actual task results.

Generic parameters are not transmitted through the message broker as runtime type guarantees.

Use explicit schemas when task payloads cross process or service boundaries.

---

## Generic Async APIs

Generics work with asynchronous functions:

```python
async def fetch[T](loader: Callable[[], Awaitable[T]]) -> T:
    return await loader()
```

The generic relationship remains the same:

```text
loader → Awaitable[T]
           │
           ▼
        await
           │
           ▼
           T
```

The type parameter describes the eventual value, not the coroutine machinery itself.

---

## Generic Iterators and Generators

Generic iterator abstractions preserve element types:

```python
from collections.abc import Iterator


def batches[T](
    items: list[T],
    size: int,
) -> Iterator[list[T]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]
```

For:

```python
batches(users, 100)
```

the result is:

```python
Iterator[list[User]]
```

This is particularly useful in ETL and large-file processing because the generic contract can remain precise while the implementation remains lazy.

---

## Generics and Streaming

Generics combine naturally with streaming:

```python
from collections.abc import Iterable, Iterator


def transform[T, R](
    values: Iterable[T],
    function: Callable[[T], R],
) -> Iterator[R]:
    for value in values:
        yield function(value)
```

The relationship is:

```text
Iterable[T]
    │
    ▼
transform()
    │
    ▼
Iterator[R]

T → input element
R → transformed element
```

This allows reusable streaming pipelines without materializing entire data sets.

---

## Generic Data Flow

A backend processing pipeline can use generics to preserve data relationships:

```mermaid
flowchart LR
    A[External Data] --> B[Validation]
    B --> C[Repository[T]]
    C --> D[Page[T]]
    D --> E[Service]
    E --> F[ApiResponse[T]]
    F --> G[HTTP Response]

    H[Kafka] --> I[Event[T]]
    I --> E
```

The type parameter does not alter the runtime data flow.

It describes the relationship between the stages to static analysis tools and developers.

---

## Generics and Type Bounds

A generic parameter can be restricted by a bound.

```python
class Model:
    ...


class Repository[T: Model]:
    ...
```

This means the generic parameter must satisfy the bound.

A bounded generic can then use operations guaranteed by the bound.

For example:

```python
class Entity:
    id: int


class Repository[T: Entity]:
    def get_id(self, entity: T) -> int:
        return entity.id
```

The repository can safely use `id` because every valid `T` satisfies the bound.

---

## Generic Constraints

Generic parameters can also be constrained to a finite set of types.

Traditional syntax:

```python
T = TypeVar("T", int, str)
```

Modern type parameter syntax supports equivalent constraints:

```python
def normalize[T: (int, str)](value: T) -> T:
    return value
```

Constraints and bounds have different semantics.

Use:

```text
Bound
→ any compatible subtype of a common abstraction

Constraint
→ one of a finite set of supported types
```

---

## Generic Variance

Variance describes how generic types behave when their type parameters have subtype relationships.

There are three concepts:

```text
Covariance
Contravariance
Invariance
```

### Covariance

A producer can be covariant.

```text
Producer[Dog]
      │
      ▼
Producer[Animal]
```

when the abstraction only produces values.

### Contravariance

A consumer can be contravariant.

```text
Consumer[Animal]
      │
      ▼
Consumer[Dog]
```

because a consumer that accepts every `Animal` can consume a `Dog`.

### Invariance

A type that both consumes and produces a value is generally invariant.

This prevents unsafe substitutions.

---

## Variance in Backend Design

Consider:

```python
class EventConsumer[T]:
    def handle(self, event: T) -> None:
        ...
```

This is fundamentally a consumer.

A read-only repository:

```python
class Reader[T]:
    def get(self, id: int) -> T:
        ...
```

is primarily a producer.

A mutable repository:

```python
class Repository[T]:
    def get(self, id: int) -> T:
        ...

    def save(self, value: T) -> None:
        ...
```

both consumes and produces `T`.

Understanding the data-flow direction helps determine appropriate variance.

---

## Generic Protocols and Variance

A protocol can express variance explicitly:

```python
from typing import Protocol, TypeVar


T_co = TypeVar("T_co", covariant=True)


class Producer(Protocol[T_co]):
    def get(self) -> T_co:
        ...
```

A consumer:

```python
T_contra = TypeVar("T_contra", contravariant=True)


class Consumer(Protocol[T_contra]):
    def consume(self, value: T_contra) -> None:
        ...
```

This is advanced type-system design and should be introduced only when the abstraction genuinely benefits from substitutability across subtypes.

---

## Generic Functions With `Callable`

A generic higher-order function can connect input and output types:

```python
from collections.abc import Callable


def apply[T, R](
    function: Callable[[T], R],
    value: T,
) -> R:
    return function(value)
```

The relationship is:

```text
T → function → R
```

For example:

```python
apply(str.upper, "hello")
```

produces a `str`.

This pattern appears in:

- transformation pipelines
- middleware
- adapters
- callbacks
- event handlers
- functional utilities

---

## Generics and Decorators

Decorators frequently need to preserve generic relationships.

A simple decorator can preserve a return type:

```python
from collections.abc import Callable
from functools import wraps


def log_result[T](
    function: Callable[..., T],
) -> Callable[..., T]:
    @wraps(function)
    def wrapper(*args: object, **kwargs: object) -> T:
        result = function(*args, **kwargs)
        return result

    return wrapper
```

For production decorators that need to preserve arbitrary parameter signatures, use `ParamSpec`:

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def log_call(
    function: Callable[P, R],
) -> Callable[P, R]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return function(*args, **kwargs)

    return wrapper
```

Here:

```text
P → parameters
R → return type
```

This is more precise than `TypeVar` alone.

---

## Generics and `Self`

When an API returns the same concrete instance subtype, use `Self`:

```python
from typing import Self


class QueryBuilder:
    def where(self, condition: str) -> Self:
        return self
```

A subclass can retain its concrete type through chained operations.

Use:

```text
Self
→ same concrete instance type

TypeVar
→ general type relationship
```

Do not introduce a generic type parameter when `Self` directly expresses the intent.

---

## Generics and `TypedDict`

Generics can operate over typed dictionaries when the generic function does not need to know the exact fields.

For example, a generic collection helper can work with:

```python
class UserPayload(TypedDict):
    id: int
    email: str
```

and:

```python
class OrderPayload(TypedDict):
    id: int
    total: Decimal
```

while preserving the payload type.

If the generic implementation requires specific fields, the generic constraint must express those requirements through an appropriate protocol, model, or other static contract.

An unconstrained `T` does not magically provide dictionary keys.

---

## Generics and `Protocol`

A generic protocol is often more flexible than inheritance.

For example:

```python
from typing import Protocol


class Identifiable(Protocol):
    id: int


class Repository[T: Identifiable]:
    def save(self, entity: T) -> T:
        ...
```

Now any compatible object with an `id` can satisfy the bound without inheriting from a specific base class.

This supports structural typing and reduces coupling.

---

## Generics and Pydantic

Generic Pydantic models can model reusable validated structures:

```python
from pydantic import BaseModel


class ApiResponse[T](BaseModel):
    data: T
    request_id: str
```

Then:

```python
ApiResponse[User]
ApiResponse[list[User]]
```

can represent parameterized validated response structures.

This combines:

```text
Generics
    +
Runtime validation
    +
Schema generation
```

which is useful for structured API contracts.

---

## Generics and FastAPI

FastAPI can use generic Pydantic models for reusable response structures.

For example:

```python
class Page[T](BaseModel):
    items: list[T]
    next_cursor: str | None
```

A route can conceptually expose:

```text
Page[User]
```

or:

```text
Page[Order]
```

while retaining the same pagination structure.

The exact API schema behavior depends on the framework and Pydantic version, so generated OpenAPI schemas should be tested as part of the API contract.

---

## Generics and Django

Django applications can use generics in:

- repository abstractions
- service layers
- serializers
- query helpers
- pagination
- adapters
- domain services

Avoid wrapping Django's ORM in generic abstractions merely to reproduce existing ORM behavior.

Use generics when the abstraction creates a stable application-level interface.

---

## Generics and PostgreSQL

A generic repository can preserve model types:

```python
class Repository[T]:
    def get(self, entity_id: int) -> T | None:
        ...
```

The database remains responsible for:

- schema integrity
- constraints
- transactions
- locking
- indexes

The generic type provides application-level static guarantees.

It does not affect PostgreSQL execution plans or query performance.

---

## Generics and Redis

Generic cache abstractions can preserve value types:

```python
class Cache[T]:
    def get(self, key: str) -> T | None:
        ...
```

But Redis only stores serialized data.

The production implementation needs:

```text
T
│
├── encode
│     ↓
│   bytes
│
├── Redis
│     ↓
│   bytes
│
└── decode + validate
      ↓
      T
```

The generic parameter documents the intended result type; it does not verify the cache contents.

---

## Generics and Kafka

Generic event envelopes can make event handling clearer:

```python
class Event[T]:
    event_type: str
    version: int
    payload: T
```

However:

```text
Python generic
    ≠
Kafka schema
```

Schema compatibility must still be managed through:

- versioning
- schema validation
- backward compatibility
- consumer compatibility
- dead-letter handling

Generics improve application code; they do not replace distributed schema management.

---

## Generics and Docker/Kubernetes

Generics do not directly affect container scheduling or orchestration.

Their operational value is indirect:

- fewer type-related defects
- safer refactoring
- clearer service interfaces
- more predictable infrastructure code

A container image should still run:

```bash
mypy app/
pytest
```

or equivalent checks during CI rather than relying on Kubernetes to detect application type errors.

---

## Generics and AWS

Generic abstractions can simplify reusable AWS adapters.

For example:

```python
class ObjectStore[T]:
    def get(self, key: str) -> T:
        ...
```

A specialized implementation could represent:

```text
ObjectStore[UserDocument]
ObjectStore[Report]
ObjectStore[Event]
```

The adapter must still handle:

- serialization
- object versioning
- checksums
- encryption
- IAM authorization
- retries
- timeouts
- eventual consistency considerations where applicable

Generic typing does not provide any AWS security guarantee.

---

## Generic Architecture

A mature backend can use generics selectively:

```mermaid
flowchart TD
    A[External Request] --> B[Runtime Validation]
    B --> C[API Model]
    C --> D[Service[T]]
    D --> E[Repository[T]]
    E --> F[(PostgreSQL)]

    D --> G[Cache[T]]
    G --> H[(Redis)]

    D --> I[Event[T]]
    I --> J[(Kafka)]

    D --> K[Task[T]]
    K --> L[Celery Workers]
```

The generic parameter is an internal static relationship.

External boundaries still require explicit schemas and runtime validation.

---

## Runtime Semantics

Generics do not cause Python to generate a separate runtime implementation for every concrete type.

For:

```python
Page[User]
Page[Order]
```

Python does not normally compile two different versions of the `Page` implementation.

The generic information is primarily used by:

- static type checkers
- IDEs
- runtime typing metadata where applicable
- documentation/tooling

The actual runtime object still contains normal Python values.

---

## Performance

Generics generally have negligible runtime performance impact.

They do not automatically introduce:

- dynamic dispatch
- serialization
- network calls
- database queries
- object copies

The runtime cost comes from the actual implementation.

However, generic abstractions can indirectly affect performance if they introduce unnecessary wrapper objects or layers.

For example:

```text
Too many abstraction layers
    ↓
more objects
    ↓
more allocations
    ↓
more function calls
```

Do not sacrifice a simple hot path merely to make its type structure more abstract.

---

## Memory

Generic annotations do not change the memory representation of values.

For:

```python
list[User]
```

the runtime memory behavior is still determined by the list and the `User` objects.

A generic wrapper such as:

```python
Page[User]
```

may introduce an additional object if implemented as a class or dataclass.

For large data processing systems, evaluate whether that abstraction is worthwhile.

Streaming and bounded batches are often more important for memory efficiency than generic typing.

---

## Concurrency

Generics do not provide thread safety or synchronization.

This:

```python
class Cache[T]:
    ...
```

can still contain unsafe shared mutable state.

Concurrency concerns must be designed separately:

- thread ownership
- locks
- atomic operations
- async coordination
- process isolation
- distributed locks
- transactional storage

Generic type correctness and concurrency correctness are independent properties.

---

## Security

Generic types are not security controls.

For example:

```python
ApiResponse[AdminUser]
```

does not prove that the caller is authorized to receive an admin user.

Security remains a runtime concern:

```text
Authentication
      │
      ▼
Authorization
      │
      ▼
Validation
      │
      ▼
Business logic
      │
      ▼
Generic application abstractions
```

Do not use generic types as substitutes for access-control checks.

---

## Reliability

Generics can reduce bugs caused by accidental type mismatches.

For example:

```python
Page[User]
```

is more precise than:

```python
Page[Any]
```

This helps prevent incorrect assumptions during refactoring.

For production reliability, combine generics with:

- static analysis
- runtime validation
- tests
- schema compatibility
- database constraints
- idempotency
- retries
- observability

Generics address only the static portion of correctness.

---

## Observability

Generic parameters should not be exposed directly as runtime metrics dimensions.

Instead, record bounded concrete categories:

```text
entity=user
entity=order
entity=payment
```

Generic infrastructure can standardize instrumentation APIs, but runtime observability should use actual bounded values.

Avoid high-cardinality labels such as:

```text
entity_type=<arbitrary Python class name>
```

when that can create excessive metric cardinality.

---

## Testing Generic Code

Generic implementations should be tested against representative concrete types.

For example:

```python
def test_page_supports_users() -> None:
    page = Page[User](
        items=[user],
        next_cursor=None,
    )

    assert page.items[0] is user
```

More importantly, run static analysis:

```bash
mypy app/
```

or:

```bash
pyright
```

Tests verify runtime behavior.

Static analysis verifies type relationships.

Both provide different forms of confidence.

---

## Property-Based Testing

Generic utilities often benefit from property-based tests because the implementation is intended to work across many concrete values.

For example, a generic transformation:

```python
def transform[T, R](
    values: Iterable[T],
    function: Callable[[T], R],
) -> Iterator[R]:
    ...
```

can be tested across different value domains.

This is especially useful for reusable infrastructure where correctness should not depend on one particular model type.

---

## Static Analysis in CI/CD

A production Python project should run static analysis automatically.

Example pipeline:

```text
Pull Request
      │
      ├── Ruff / formatting
      ├── mypy / Pyright
      ├── Unit tests
      ├── Integration tests
      ├── API tests
      └── Build
             │
             ▼
          Deploy
```

Generic abstractions should not be merged based solely on successful runtime tests.

Incorrect generic relationships may never be exercised by the runtime test suite.

---

## Common Mistakes

### Using Generics Without a Relationship

Bad:

```python
def log[T](value: T) -> str:
    return str(value)
```

`T` adds little useful information.

Prefer:

```python
def log(value: object) -> str:
    return str(value)
```

### Replacing Everything With `Any`

Bad:

```python
class Repository:
    def get(self, id: int) -> Any:
        ...
```

Better:

```python
class Repository[T]:
    def get(self, id: int) -> T:
        ...
```

when the repository genuinely preserves the entity type.

### Over-Generalizing Repositories

A generic CRUD abstraction may hide important domain-specific queries.

### Ignoring Variance

Variance mistakes can create unsound substitutions or confusing type errors.

### Creating Deep Generic Nesting

Types such as:

```python
Result[Page[ApiResponse[list[User]]]]
```

may be technically valid but difficult to maintain.

Simplify the architecture when the type structure becomes harder to understand than the business logic.

### Using Generics for Runtime Dispatch

Generics do not automatically choose implementations based on runtime types.

### Confusing Generic Types With Runtime Validation

`Repository[User]` does not verify that runtime values are actually valid `User` objects.

### Generic Abstraction Everywhere

Not every repeated function needs a generic framework.

Duplication is sometimes cheaper than premature abstraction.

---

## Production Pitfalls

### Generic Repository Becomes a Leaky Abstraction

If every entity requires special-case behavior:

```python
Repository[T]
```

may stop being a useful abstraction.

Prefer explicit domain interfaces when semantics diverge.

### Generic Type Hides Serialization Boundaries

A:

```python
Cache[User]
```

does not mean Redis contains a Python `User`.

It means the application expects the cache adapter to produce a `User`.

### Generic Event Without Schema Versioning

`Event[UserCreated]` does not solve Kafka compatibility.

Use explicit schema versions and compatibility policies.

### Excessive Type Complexity

A type signature should make the contract clearer.

If it requires a long explanation before a developer can understand it, reconsider the abstraction.

### Runtime and Static Models Diverge

If a generic annotation says:

```python
ApiResponse[User]
```

but runtime validation produces arbitrary dictionaries, the type system is lying about the actual application state.

Keep runtime and static contracts aligned.

---

## Decision Guide

| Requirement | Recommended approach |
|---|---|
| Preserve input type in output | Generic function |
| Generic collection | Built-in generic type |
| Generic reusable class | Generic class |
| Generic reusable type expression | Generic alias |
| Common behavior across unrelated implementations | Generic `Protocol` |
| Restrict generic to compatible base/interface | Bound |
| Restrict generic to finite types | Constraints |
| Preserve callable parameters | `ParamSpec` |
| Preserve callable return type | `TypeVar` |
| Preserve concrete instance type | `Self` |
| Specific finite values | `Literal` |
| Fixed dictionary shape | `TypedDict` |
| Runtime validation | Pydantic / runtime model |
| Static distinction between primitive values | `NewType` |
| No meaningful type relationship | Simpler concrete annotation |

---

## Production Best Practices

Use generics when:

- one implementation genuinely supports multiple types
- the type relationship is meaningful
- the relationship improves caller safety
- the abstraction is reused across application boundaries
- the generic parameter remains understandable

Prefer modern syntax for Python 3.12+:

```python
def first[T](items: Iterable[T]) -> T:
    ...
```

```python
class Repository[T]:
    ...
```

```python
type Page[T] = list[T]
```

For older Python versions, use `TypeVar`, `Generic`, and compatible typing constructs.

In production:

- keep generic abstractions narrow
- use bounds when a common capability is required
- understand variance before explicitly configuring it
- use `ParamSpec` for decorators
- use `Self` for subtype-preserving methods
- use protocols for behavioral contracts
- validate external data independently
- keep Kafka, Redis, REST, and database schemas explicit
- run static analysis in CI/CD
- test generic implementations with multiple concrete types
- avoid generic abstractions whose complexity exceeds their value
- prefer domain-specific interfaces when generic CRUD semantics become restrictive

---

## Interview Traps

### What are generics?

Generics allow reusable code to operate across multiple types while preserving relationships between those types.

### Is a generic type the same as Any?

No. `Any` weakens static checking, while generics preserve specific type relationships.

### What does `T` mean?

It is a type parameter representing a type selected by the caller or specialization.

### Why use `list[T]` instead of `list[Any]`?

`list[T]` preserves the element type and enables precise static checking.

### What is a bounded generic?

A generic parameter restricted to a base type or protocol:

```python
class Repository[T: Entity]:
    ...
```

### Bound vs constraint?

A bound allows compatible subtypes of a common abstraction. Constraints specify a finite set of supported types.

### What is variance?

Variance defines how generic types relate when their parameter types have subtype relationships.

### Are generic classes invariant by default?

Yes, user-defined generic classes are generally invariant unless their type parameters are designed with appropriate variance.

### What is the difference between TypeVar and ParamSpec?

`TypeVar` represents types of values. `ParamSpec` preserves callable parameter signatures.

### What is the difference between TypeVar and Self?

`TypeVar` expresses general type relationships. `Self` specifically represents the concrete type of the current instance.

### Do generics exist at runtime?

Python retains some typing metadata at runtime, but generic parameters primarily support static analysis. They do not cause separate runtime implementations to be generated for each type.

### Do generics validate HTTP or Kafka data?

No. Runtime validation is still required.

### Should every repository be generic?

No. Generics are useful when a real common relationship exists. Domain-specific query semantics often require explicit interfaces.

### Do generics improve runtime performance?

Not inherently. Their primary value is static correctness, reuse, and maintainability.

---

## Production Checklist

Before introducing a generic abstraction, verify:

- The abstraction genuinely supports multiple types.
- There is a meaningful relationship between its type parameters.
- `Any` is not being used where a precise generic relationship is possible.
- A concrete type is not actually clearer.
- The generic API remains understandable to the team.
- Generic parameters are scoped correctly.
- Multiple type parameters represent genuinely independent relationships.
- Bounds are used when a common interface is required.
- Constraints are used only for finite supported type sets.
- Variance is understood before being explicitly configured.
- Mutable abstractions are not incorrectly made covariant.
- `ParamSpec` is used when callable parameter preservation is required.
- `Self` is considered when methods return the same concrete instance type.
- Protocols are considered for behavioral abstractions.
- Runtime validation exists at external boundaries.
- Generic types are not treated as serialization or security guarantees.
- Redis and Kafka boundaries perform explicit serialization and validation.
- Database constraints remain authoritative for persistent integrity.
- Generic repositories do not hide domain-specific behavior.
- Type complexity does not exceed the value of the abstraction.
- Static analysis runs in CI/CD.
- Tests exercise generic implementations with representative concrete types.
- Schema evolution is handled independently for distributed systems.
- The abstraction does not introduce unnecessary runtime wrappers or allocation overhead.

## Key Takeaways

- Generics make reusable Python code type-safe by preserving meaningful relationships between inputs, outputs, attributes, and operations across concrete types.
- Use generic functions, classes, aliases, and protocols when one implementation genuinely applies to multiple types; do not introduce generics merely to avoid duplication.
- Bounds, constraints, variance, `ParamSpec`, and `Self` solve different problems and should be selected based on the actual type relationship being modeled.
- Generics provide static guarantees only; HTTP, Kafka, Redis, database, and other external boundaries still require runtime validation, schema management, and security controls.
- Production-quality generic design favors small, understandable abstractions that improve backend infrastructure without hiding domain-specific behavior behind excessive type complexity.