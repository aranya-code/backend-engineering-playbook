# 13- Overloads

## Overview

`@overload` allows Python type annotations to describe multiple valid call signatures for a single function or method.

It is primarily a **static typing feature**. Python still executes exactly one implementation at runtime.

This distinction is fundamental:

```text
Multiple overload signatures
          │
          ▼
     Type checker
          │
          ▼
Determines return type from arguments

                Runtime
                   │
                   ▼
          One implementation
```

For example:

```python
from typing import overload


@overload
def get_value(key: int) -> User | None:
    ...


@overload
def get_value(key: str) -> Order | None:
    ...


def get_value(
    key: int | str,
) -> User | Order | None:
    ...
```

A caller using an `int` gets the static return type:

```python
user = get_value(42)
```

while a caller using a `str` gets:

```python
order = get_value("ORD-123")
```

The implementation still handles both cases at runtime.

Overloads are most useful when the **return type or accepted argument relationship depends on the input signature** and a single union annotation cannot express that relationship precisely.

---

## Why Overloads Matter

Without overloads, developers often write:

```python
def get_value(
    key: int | str,
) -> User | Order | None:
    ...
```

This is correct but loses information.

The caller now sees:

```text
int → User | Order | None
str → User | Order | None
```

even if the implementation guarantees:

```text
int → User | None
str → Order | None
```

Overloads preserve this relationship:

```text
                 get_value()
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
       int key               str key
          │                     │
          ▼                     ▼
     User | None          Order | None
```

This improves:

- static correctness
- IDE autocomplete
- API discoverability
- refactoring safety
- caller ergonomics
- library design

---

## Basic Syntax

An overloaded function contains:

1. one or more overload declarations
2. one concrete implementation

```python
from typing import overload


@overload
def parse(value: str) -> int:
    ...


@overload
def parse(value: bytes) -> int:
    ...


def parse(value: str | bytes) -> int:
    if isinstance(value, bytes):
        return int(value.decode())

    return int(value)
```

The overload declarations contain no runtime implementation.

The final function is the actual implementation executed by Python.

---

## Runtime Behavior

This is important:

```python
@overload
def parse(value: str) -> int:
    ...
```

does not create a runtime overload mechanism similar to Java or C++.

At runtime, the final definition wins.

Conceptually:

```python
@overload
def parse(value: str) -> int:
    ...


def parse(value: str | bytes) -> int:
    ...
```

becomes one callable implementation for runtime purposes.

The overloads exist primarily for static type checkers.

---

## Overloads Are Not Runtime Dispatch

Do not expect this:

```python
@overload
def process(value: int) -> User:
    ...


@overload
def process(value: str) -> Order:
    ...
```

to automatically select a different implementation at runtime.

Python executes:

```python
def process(value: int | str) -> User | Order:
    ...
```

The implementation must perform the dispatch:

```python
def process(value: int | str) -> User | Order:
    if isinstance(value, int):
        return get_user(value)

    return get_order(value)
```

The overloads document and statically model the dispatch relationship.

---

## Overload vs Union

This is the most important comparison.

Without overloads:

```python
def lookup(
    key: int | str,
) -> User | Order:
    ...
```

With overloads:

```python
@overload
def lookup(key: int) -> User:
    ...


@overload
def lookup(key: str) -> Order:
    ...


def lookup(key: int | str) -> User | Order:
    ...
```

The difference is:

| Approach | Input | Static output |
|---|---|---|
| Union | `int \| str` | `User \| Order` |
| Overload | `int` | `User` |
| Overload | `str` | `Order` |

Use overloads when the input determines the output type.

---

## When a Union Is Better

Do not use overloads merely because a function accepts multiple types.

This is usually sufficient:

```python
def normalize(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode()

    return value
```

The return type does not depend on which input type was supplied.

Therefore, overloads add unnecessary complexity.

A useful rule:

```text
Multiple accepted inputs
        │
        ├── Same return relationship → Union
        │
        └── Different return relationship → overload
```

---

## Overloads With Literal Values

`Literal` and overloads work particularly well together.

```python
from typing import Literal, overload


@overload
def fetch(
    resource: Literal["user"],
    identifier: int,
) -> User | None:
    ...


@overload
def fetch(
    resource: Literal["order"],
    identifier: int,
) -> Order | None:
    ...


def fetch(
    resource: Literal["user", "order"],
    identifier: int,
) -> User | Order | None:
    if resource == "user":
        return get_user(identifier)

    return get_order(identifier)
```

The caller gets a precise type:

```python
user = fetch("user", 42)
order = fetch("order", 42)
```

This is useful for finite dispatch APIs.

However, if the set of resource types becomes large, a dedicated service or registry may be cleaner.

---

## Overloads With `None`

Overloads can model APIs where `None` changes the return type.

For example:

```python
@overload
def get_user(
    user_id: int,
    *,
    required: Literal[True],
) -> User:
    ...


@overload
def get_user(
    user_id: int,
    *,
    required: Literal[False],
) -> User | None:
    ...


def get_user(
    user_id: int,
    *,
    required: bool,
) -> User | None:
    user = repository.get(user_id)

    if user is None and required:
        raise UserNotFoundError(user_id)

    return user
```

This lets static analysis distinguish:

```python
user = get_user(42, required=True)
```

from:

```python
user = get_user(42, required=False)
```

This pattern is useful when a Boolean option genuinely changes the return contract.

---

## Boolean Overloads

Boolean-dependent overloads are common:

```python
@overload
def load(
    path: str,
    *,
    binary: Literal[True],
) -> bytes:
    ...


@overload
def load(
    path: str,
    *,
    binary: Literal[False],
) -> str:
    ...


def load(
    path: str,
    *,
    binary: bool,
) -> bytes | str:
    ...
```

The overload tells the type checker:

```text
binary=True
    → bytes

binary=False
    → str
```

Avoid using overloads when the Boolean flag does not materially change the type contract.

---

## Handling a Non-Literal Boolean

A caller may have:

```python
binary: bool = get_configuration()
```

Then:

```python
value = load("data", binary=binary)
```

The type checker cannot know whether `binary` is `True` or `False`.

The result may therefore be inferred as:

```python
bytes | str
```

This is correct.

Overloads can provide precise types when the argument value is statically known, but they cannot predict arbitrary runtime configuration.

---

## Overloads With Generic Types

Overloads and generics can express sophisticated relationships.

For example:

```python
from collections.abc import Sequence
from typing import overload


@overload
def first(value: tuple[T, ...]) -> T:
    ...


@overload
def first(value: Sequence[T]) -> T:
    ...


def first[T](value: Sequence[T]) -> T:
    return value[0]
```

Often the generic relationship alone is enough:

```python
def first[T](value: Sequence[T]) -> T:
    return value[0]
```

Use overloads only when the generic signature cannot adequately express the distinction.

---

## Overloads With `TypeVar`

A common pattern is an input-dependent return relationship.

```python
from typing import TypeVar, overload


T = TypeVar("T")


@overload
def identity(value: T) -> T:
    ...


def identity(value: T) -> T:
    return value
```

Here an overload is unnecessary because `TypeVar` already expresses the relationship.

Prefer:

```python
def identity[T](value: T) -> T:
    return value
```

Use overloads when there are genuinely different signatures rather than using them to restate generic behavior.

---

## Overloads vs Generics

| Requirement | Prefer |
|---|---|
| Input and output have the same generic relationship | `TypeVar` / generics |
| Different input forms produce different return types | `@overload` |
| Finite value selects return type | `Literal` + overload |
| Callable parameter preservation | `ParamSpec` |
| Same concrete instance returned | `Self` |
| Runtime subtype predicate | `TypeGuard` |
| Simple multiple accepted types | Union |

For example:

```python
def identity[T](value: T) -> T:
    ...
```

is better than creating many overloads for every possible type.

---

## Overload Implementation Signature

The implementation signature must be broad enough to handle all overload variants.

Correct:

```python
@overload
def get(key: int) -> User:
    ...


@overload
def get(key: str) -> Order:
    ...


def get(key: int | str) -> User | Order:
    ...
```

Incorrect:

```python
@overload
def get(key: int) -> User:
    ...


@overload
def get(key: str) -> Order:
    ...


def get(key: int) -> User:
    ...
```

The implementation cannot correctly handle the `str` overload.

A type checker should flag incompatible overload implementation signatures.

---

## Implementation Return Type

The implementation return type should generally cover the outputs of the overloads.

```python
@overload
def get(key: int) -> User:
    ...


@overload
def get(key: str) -> Order:
    ...


def get(key: int | str) -> User | Order:
    ...
```

The implementation must account for both possibilities.

The overload declarations provide the precise caller-facing contract.

The implementation signature represents what the function actually handles internally.

---

## Implementation Arguments Can Be Broader

The implementation can generally use broader parameter types than individual overloads.

For example:

```python
@overload
def open_resource(name: str) -> TextResource:
    ...


@overload
def open_resource(name: bytes) -> BinaryResource:
    ...


def open_resource(
    name: str | bytes,
) -> TextResource | BinaryResource:
    ...
```

This reflects the runtime dispatch.

The implementation should not expose a narrower signature that excludes valid overload calls.

---

## Overload Ordering

Overload order can matter to static type checkers.

Consider overlapping signatures:

```python
@overload
def process(value: object) -> str:
    ...


@overload
def process(value: str) -> int:
    ...
```

The broad `object` overload can capture `str` calls before the more specific overload is considered, depending on the type checker's overload resolution rules.

Prefer:

```python
@overload
def process(value: str) -> int:
    ...


@overload
def process(value: object) -> str:
    ...
```

More generally:

```text
Specific overloads
       ↓
More general overloads
```

Avoid overlapping overloads whenever possible.

---

## Overlapping Overloads

Overloads should represent distinct, understandable call contracts.

Problematic:

```python
@overload
def process(value: int | str) -> object:
    ...


@overload
def process(value: int) -> int:
    ...
```

The signatures overlap.

This can make type inference difficult and may produce unreachable or shadowed overload warnings.

Prefer designing overloads with clearly distinguishable inputs.

---

## Overload Resolution

Static type checkers inspect the call site.

For:

```python
value = get(42)
```

the checker matches:

```python
get(key: int) -> User
```

and infers:

```python
value: User
```

For:

```python
key: int | str = get_key()

value = get(key)
```

no single overload may be sufficient.

The result may become:

```python
User | Order
```

or the checker may report an overload mismatch depending on the signatures.

The type checker cannot always resolve dynamic unions into one specific overload.

---

## Overloads and Union Arguments

Suppose:

```python
@overload
def get(key: int) -> User:
    ...


@overload
def get(key: str) -> Order:
    ...


def get(key: int | str) -> User | Order:
    ...
```

Then:

```python
key: int | str
result = get(key)
```

The static type is generally a union of possible results if the checker can correlate the union with the overloads.

If the function has more complex relationships, redesigning the API may be clearer than adding many overload variants.

---

## Overloads With Optional Arguments

Overloads can model optional parameters when their presence changes the return type.

```python
@overload
def find_user(
    user_id: int,
) -> User | None:
    ...


@overload
def find_user(
    user_id: int,
    default: User,
) -> User:
    ...


def find_user(
    user_id: int,
    default: User | None = None,
) -> User | None:
    user = repository.get(user_id)

    if user is None:
        return default

    return user
```

This allows:

```python
user = find_user(42)
```

to be:

```python
User | None
```

while:

```python
user = find_user(42, default_user)
```

can be:

```python
User
```

---

## Overloads With Keyword Arguments

Overloads can distinguish keyword-only options:

```python
@overload
def request(
    method: Literal["GET"],
    *,
    response_model: type[User],
) -> User:
    ...


@overload
def request(
    method: Literal["GET"],
    *,
    response_model: type[Order],
) -> Order:
    ...
```

The implementation:

```python
def request(
    method: Literal["GET"],
    *,
    response_model: type[User] | type[Order],
) -> User | Order:
    ...
```

This can be useful for typed HTTP clients.

However, generic type parameters may provide a cleaner design when the response model is simply a type parameter.

---

## Generic HTTP Client Example

A generic client is often preferable:

```python
from collections.abc import Mapping
from typing import Any


class HttpClient:
    def request[T](
        self,
        method: str,
        path: str,
        response_model: type[T],
        *,
        params: Mapping[str, str] | None = None,
    ) -> T:
        payload: Any = self._send(
            method,
            path,
            params=params,
        )

        return response_model.model_validate(payload)
```

This expresses:

```text
response_model: type[T]
        │
        ▼
runtime validation
        │
        ▼
return: T
```

Overloads would be unnecessary unless particular argument combinations produce fundamentally different contracts.

---

## Overloads in Standard Library Design

Overloads are useful for APIs whose runtime behavior varies based on arguments.

Python's typing ecosystem uses overloads extensively to model APIs that cannot be represented cleanly with one signature.

Common patterns include:

- optional parameters affecting return types
- literal values selecting return types
- synchronous vs asynchronous behavior
- different accepted container forms
- mode flags
- mapping access patterns

This is why understanding overloads is useful when reading type stubs and standard-library annotations.

---

## Overloads and Type Stubs

Overloads are especially common in `.pyi` stub files.

For example:

```text
library/
├── client.py
└── client.pyi
```

A stub can expose multiple overload signatures while the runtime implementation remains hidden.

This allows library authors to provide precise static typing without changing runtime behavior.

Overloads are therefore an important part of Python library API design.

---

## Overloads and Third-Party Libraries

Suppose a third-party client has a dynamic API:

```python
client.get("user", 42)
client.get("order", 100)
```

A stub or wrapper can model it:

```python
@overload
def get(
    resource: Literal["user"],
    identifier: int,
) -> User:
    ...


@overload
def get(
    resource: Literal["order"],
    identifier: int,
) -> Order:
    ...
```

This gives application developers precise IDE and type-checker behavior without modifying the external package.

---

## Overloads and FastAPI

Overloads can be useful in internal FastAPI service libraries, especially where helper APIs have multiple return contracts.

However, FastAPI route handlers should normally have a clear runtime response model.

For public API schemas, use:

- Pydantic models
- explicit response models
- OpenAPI

rather than relying on Python overloads to define the external contract.

Overloads primarily improve developer tooling inside the Python codebase.

---

## Overloads and Django

Django applications may use overloads for:

- service helpers
- query utilities
- model managers
- typed wrappers
- configuration APIs

For example, an internal helper might expose different return types depending on a mode parameter.

Avoid adding overloads merely to make Django's dynamic APIs appear statically typed if the resulting API becomes difficult to understand.

---

## Overloads and PostgreSQL

Overloads can describe application-level repository methods:

```python
@overload
def find_user(
    key: int,
) -> User | None:
    ...


@overload
def find_user(
    key: UUID,
) -> User | None:
    ...
```

But if both inputs return the same type, a union is usually simpler:

```python
def find_user(
    key: int | UUID,
) -> User | None:
    ...
```

Use overloads only when the type relationship actually differs.

---

## Overloads and Redis

Suppose a cache client supports two modes:

```python
@overload
def get(
    key: str,
    *,
    decode: Literal[True],
) -> str | None:
    ...


@overload
def get(
    key: str,
    *,
    decode: Literal[False],
) -> bytes | None:
    ...
```

This models the static contract of the wrapper.

The Redis implementation still performs runtime decoding.

The overload does not change Redis behavior.

---

## Overloads and Kafka

Kafka consumers often deal with different event types.

Instead of making one function return a large union:

```python
def decode(event_type: str) -> UserEvent | OrderEvent | PaymentEvent:
    ...
```

a literal-based overload can provide precise results:

```python
@overload
def decode(
    event_type: Literal["user.created"],
    payload: bytes,
) -> UserCreated:
    ...


@overload
def decode(
    event_type: Literal["order.created"],
    payload: bytes,
) -> OrderCreated:
    ...
```

For large event taxonomies, explicit schema registries and generated types may be more maintainable than manually maintaining dozens of overloads.

---

## Overloads and Celery

Overloads can model task helpers when different task names produce different result types:

```python
@overload
def dispatch(
    task: Literal["generate_report"],
) -> ReportTaskResult:
    ...


@overload
def dispatch(
    task: Literal["send_email"],
) -> EmailTaskResult:
    ...
```

As the number of tasks grows, this can become difficult to maintain.

Prefer generic task abstractions or explicit task objects when the domain becomes large.

---

## Overloads and gRPC

Generated gRPC clients generally already have explicit method signatures.

Overloads may be useful in an application-level wrapper where a single helper dispatches to different typed operations.

The `.proto` definition remains the distributed contract.

Python overloads only improve local static typing.

---

## Overloads and Microservices

In a microservice:

```text
HTTP/gRPC/Kafka boundary
          │
          ▼
Runtime schema validation
          │
          ▼
Typed application model
          │
          ▼
Python helper / service
          │
          ▼
Overloaded API where useful
```

Overloads belong inside the application.

They should not be treated as a replacement for:

- OpenAPI
- protobuf
- JSON Schema
- Avro
- database schemas

---

## Overloads and Runtime Validation

Overloads do not validate arguments.

This:

```python
@overload
def get(value: int) -> User:
    ...
```

does not guarantee that runtime callers pass an `int`.

Python still allows:

```python
get("unexpected")
```

unless the implementation validates or otherwise handles the value.

For external inputs:

```text
Runtime validation
      +
Static overloads
```

provide complementary guarantees.

---

## Overloads and Security

Overloads do not provide security guarantees.

For example:

```python
@overload
def get_user(
    user_id: int,
    *,
    include_private: Literal[True],
) -> PrivateUser:
    ...
```

does not authorize access to private information.

Authorization must still be enforced at runtime.

Static types should never be treated as evidence of:

- identity
- authorization
- trust
- data ownership

---

## Overloads and Performance

Overload declarations generally have negligible runtime cost.

They do not create multiple runtime implementations.

The performance impact comes from the implementation itself.

However, an overly complicated overloaded API can indirectly increase engineering cost:

- more implementation branches
- more tests
- more documentation
- slower type checking
- harder maintenance

Optimize the API for clarity, not for maximum type-level expressiveness.

---

## Overloads and Memory

Overloads do not meaningfully alter runtime object memory usage.

The annotations may contribute to function metadata, but they do not create separate function implementations for each overload.

The primary cost is development and static-analysis complexity.

---

## Overloads and Concurrency

Overloads do not provide concurrency guarantees.

For example:

```python
@overload
def acquire(
    resource: Literal["sync"],
) -> SyncLock:
    ...


@overload
def acquire(
    resource: Literal["async"],
) -> AsyncLock:
    ...
```

The types describe the returned interface.

They do not guarantee:

- thread safety
- lock fairness
- deadlock prevention
- cancellation safety
- distributed synchronization

Those properties belong to the runtime implementation and operational design.

---

## Overloads and Testing

Each overload represents a public type-level contract.

Test representative runtime paths:

```python
def test_get_user_by_id() -> None:
    result = get(42)

    assert isinstance(result, User)


def test_get_order_by_reference() -> None:
    result = get("ORD-123")

    assert isinstance(result, Order)
```

Also run static analysis.

```bash
mypy .
```

or:

```bash
pyright
```

A runtime implementation can work correctly while its overload declarations are wrong.

Both layers need verification.

---

## Static Type Testing

For complex overloads, maintain small type-checking examples.

For example:

```python
user = get(42)
reveal_type(user)

order = get("ORD-123")
reveal_type(order)
```

A type checker should report:

```text
User
Order
```

respectively.

These checks are useful when changing overloaded APIs because runtime tests cannot detect incorrect static return inference.

---

## Overloads in CI/CD

A production Python pipeline should include:

```text
Pull Request
      │
      ├── Formatting
      ├── Linting
      ├── Static Type Checking
      ├── Unit Tests
      ├── Integration Tests
      └── Build
             │
             ▼
          Deploy
```

Overload changes should be reviewed as API changes because they affect developer-facing type contracts.

---

## API Evolution

Changing:

```python
@overload
def get(key: int) -> User:
    ...
```

to:

```python
@overload
def get(key: int) -> User | None:
    ...
```

can break callers that relied on the previous static guarantee.

Similarly, removing an overload can cause previously valid code to fail type checking.

Treat overload signatures as part of the public API when the function is consumed outside a small internal module.

---

## Overload Design for Maintainability

Prefer a small number of meaningful overloads.

Good:

```text
2–4 clearly distinct signatures
```

Potentially problematic:

```text
15+ overlapping overloads
```

When overloads become numerous, consider:

- generics
- `Literal`
- a tagged object model
- a dedicated class
- separate methods
- a registry
- a protocol
- explicit result types

A complicated overload list is often evidence that the runtime API itself needs redesign.

---

## Overloads vs Separate Methods

Suppose an API has:

```python
client.fetch("user", 1)
client.fetch("order", 2)
client.fetch("payment", 3)
```

You could model it with many overloads.

Alternatively:

```python
client.fetch_user(1)
client.fetch_order(2)
client.fetch_payment(3)
```

Separate methods may be clearer when the operations have substantially different semantics.

Use overloads when the runtime API is naturally one operation with multiple type-specific forms.

Do not distort the API solely to demonstrate advanced typing.

---

## Overloads vs Tagged Results

Instead of:

```python
@overload
def execute(command: CreateUser) -> User:
    ...


@overload
def execute(command: DeleteUser) -> DeleteResult:
    ...
```

a command-dispatch system may benefit from explicit command/result types.

The appropriate choice depends on scale.

Overloads work well for small, stable sets of relationships.

Large dynamic registries generally need a different abstraction.

---

## Overloads and Protocols

Protocols define behavior.

Overloads define multiple call signatures.

They can be combined:

```python
class Client(Protocol):
    @overload
    def get(self, key: int) -> User:
        ...

    @overload
    def get(self, key: str) -> Order:
        ...
```

An implementation can satisfy the protocol if its public behavior is compatible with the declared overloads.

This is useful for typed client interfaces.

---

## Overloads and `ParamSpec`

`ParamSpec` preserves arbitrary callable parameters.

For example:

```python
P = ParamSpec("P")
R = TypeVar("R")


def decorator(
    function: Callable[P, R],
) -> Callable[P, R]:
    ...
```

Use `ParamSpec` for decorators and higher-order functions.

Use overloads when the API genuinely has multiple discrete signatures.

Do not replace generic callable typing with dozens of overloads.

---

## Overloads and `TypeGuard`

These solve different problems.

```text
TypeGuard
    → narrows a value after a runtime predicate

overload
    → selects a static signature based on call arguments
```

Example:

```python
@overload
def parse(value: str) -> User:
    ...


@overload
def parse(value: bytes) -> User:
    ...


def parse(value: str | bytes) -> User:
    ...
```

versus:

```python
def is_user(value: object) -> TypeGuard[User]:
    ...
```

One describes call signatures.

The other describes runtime narrowing.

---

## Overloads and `Any`

Using `Any` can bypass the benefits of overloads.

For example:

```python
key: Any = get_dynamic_key()
result = get(key)
```

Static analysis may lose precision because `Any` disables many checks.

Prefer precise types at application boundaries:

```python
key: int | str
```

and validate dynamic data before it reaches overloaded APIs.

---

## Overloads and `object`

`object` is safer than `Any`, but it does not automatically satisfy a specific overload.

For example:

```python
value: object
get(value)
```

cannot safely select:

```python
get(int)
```

or:

```python
get(str)
```

without narrowing first:

```python
if isinstance(value, int):
    user = get(value)
elif isinstance(value, str):
    order = get(value)
```

This is an important interaction between overload resolution and control-flow narrowing.

---

## Common Mistakes

### Implementing Multiple Runtime Functions

Python does not provide runtime function overloading through repeated definitions.

The final implementation is what executes.

### Using Overloads Instead of Generics

Bad:

```python
@overload
def identity(value: int) -> int:
    ...


@overload
def identity(value: str) -> str:
    ...
```

Prefer:

```python
def identity[T](value: T) -> T:
    return value
```

### Overloading When a Union Is Enough

If all inputs produce the same return type, use a union.

### Overlapping Signatures

Overlapping overloads make resolution ambiguous and can produce unreachable overloads.

### Incorrect Implementation Signature

The concrete implementation must support all declared overloads.

### Forgetting Runtime Validation

Overload annotations do not validate arguments.

### Excessive Overloads

A large overload matrix often indicates that the runtime API is too complicated.

### Treating Overloads as API Contracts Across Services

Overloads are Python-level static contracts, not distributed protocol definitions.

---

## Production Pitfalls

### Static Contract Drift

The implementation can evolve while overload signatures remain outdated.

Run static checks and runtime tests together.

### Incorrect Return Annotation

If an overload promises:

```python
User
```

but the implementation can return `None`, the static contract is unsound.

### Literal Explosion

Using one overload per literal value can become unmaintainable:

```text
"user.created"
"order.created"
"payment.created"
...
```

Use generated schemas, registries, or domain models when the set becomes large.

### Dynamic Inputs

Highly dynamic data can make overload resolution ineffective.

Validate and narrow values before invoking overloaded APIs.

### Framework Leakage

Do not create large overload layers simply to hide every dynamic behavior of Django, FastAPI, or a third-party SDK.

---

## Production Decision Guide

| Requirement | Preferred approach |
|---|---|
| Same type relationship across arbitrary types | Generic / `TypeVar` |
| Different return type for distinct input signatures | `@overload` |
| Finite values determine return type | `Literal` + overload |
| Input must be narrowed after runtime check | `TypeGuard` / `TypeIs` |
| Callback signature preservation | `ParamSpec` |
| Concrete instance preservation | `Self` |
| Simple multiple accepted inputs | Union |
| Behavioral dependency | Protocol |
| Runtime schema validation | Pydantic / validation library |
| External service contract | OpenAPI / protobuf / schema |

---

## Production Best Practices

Use overloads when the caller's arguments determine a more precise return type than a union can express.

Keep overloads:

- minimal
- non-overlapping
- ordered from specific to general where relevant
- consistent with the runtime implementation
- covered by static analysis
- covered by runtime tests

Prefer generics when the relationship is parametric:

```python
def identity[T](value: T) -> T:
    ...
```

Prefer unions when the return type does not depend on the input variant:

```python
def normalize(value: str | bytes) -> str:
    ...
```

Use `Literal` when finite values control the result:

```python
Literal["user"]
Literal["order"]
```

Use `ParamSpec` for callable parameter preservation.

Keep runtime validation separate from static overload declarations.

Treat public overload signatures as part of the API contract.

When overload lists become large or difficult to understand, reconsider the runtime API rather than continuing to add type-level complexity.

---

## Interview Traps

### What is `@overload` in Python?

`@overload` allows multiple static call signatures to be declared for one runtime implementation.

### Does Python support runtime function overloading?

Not through `typing.overload`. The final implementation is the runtime function.

### Why use overloads instead of a union?

Use overloads when different input signatures produce different return types.

### When should I use a generic instead?

Use a generic when the relationship is parametric, such as:

```python
def identity[T](value: T) -> T:
    ...
```

### Can overloads change runtime behavior?

No. They affect static analysis and developer tooling.

### What is the implementation signature?

It is the actual runtime function that implements all overload cases.

### Can overloads have different return types?

Yes. That is one of their primary purposes.

### Can overloads use `Literal`?

Yes. This is a common way to model APIs where a finite argument value determines the result type.

### What happens with a runtime `bool`?

If the type checker cannot determine whether it is `True` or `False`, it generally cannot select one literal overload and must use a broader result.

### Can overloads be generic?

Yes. Overloads and generic type parameters can be combined when both concepts are needed.

### Are overloads useful for FastAPI?

They can improve typing of internal helpers and clients, but public API contracts should use runtime schemas such as Pydantic and OpenAPI.

### Are overloads runtime validation?

No.

### Can overloads replace Protocols?

No. Protocols describe behavioral interfaces; overloads describe alternative call signatures.

### Can overloads replace OpenAPI or protobuf?

No. They are local Python typing constructs.

### When should I avoid overloads?

Avoid them when a generic, union, separate method, or simpler API expresses the contract more clearly.

---

## Production Checklist

Before introducing overloads, verify:

- The function has genuinely distinct call signatures.
- The return type depends meaningfully on the input signature.
- A generic type parameter cannot express the relationship more simply.
- A union is not sufficient.
- `Literal` is used when finite values determine the return type.
- Overloads are small and understandable.
- Overloads do not unnecessarily overlap.
- More specific signatures appear before broader overlapping signatures where required.
- The implementation signature accepts all valid overload inputs.
- The implementation return type covers all overload results.
- The runtime implementation actually satisfies every declared overload.
- Dynamic inputs are narrowed or validated before calling the overloaded API.
- External data is not trusted merely because it matches an overload statically.
- Runtime validation remains separate from static typing.
- Security decisions do not depend on overload resolution.
- Concurrency guarantees are not implied by type signatures.
- Public overloads are treated as API contracts.
- Runtime tests cover every important overload branch.
- Static type checking verifies overload resolution.
- Type-checking examples are maintained for complex APIs.
- The number of overloads remains manageable.
- A dedicated method or domain object is considered when overload complexity grows.
- Distributed contracts remain defined through OpenAPI, protobuf, JSON Schema, Avro, or equivalent mechanisms.
- CI/CD runs static analysis and runtime tests before deployment.

## Key Takeaways

- `@overload` describes multiple valid call signatures for one runtime implementation and is primarily a static typing mechanism.
- Use overloads when the input signature determines a more precise return type; use generics for parametric relationships and unions when the return type does not depend on the input variant.
- `Literal` values, optional arguments, and mode flags are common overload use cases, but overlapping or excessive overloads usually indicate unnecessary API complexity.
- Overload declarations do not perform runtime validation, authorization, concurrency control, or distributed schema enforcement; those guarantees must be implemented separately.
- Production overloads should remain minimal, non-overlapping, consistent with the runtime implementation, covered by static analysis and tests, and treated as part of the API contract when publicly consumed.