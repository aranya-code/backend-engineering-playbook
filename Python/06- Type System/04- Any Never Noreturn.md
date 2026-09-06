# 04- Any Never Noreturn

## Overview

`Any`, `Never`, and `NoReturn` represent very different concepts in Python's type system:

| Type | Core meaning |
|---|---|
| `Any` | Opt out of static type checking for a value |
| `Never` | A value/state that can never exist |
| `NoReturn` | A function that does not return normally |

They solve opposite problems.

```text
Any
 │
 └── "The type checker should not constrain this value."

Never
 │
 └── "There is no possible value of this type."

NoReturn
 │
 └── "This function does not return normally."
```

These types become particularly important in large Python systems because type safety is not simply about adding annotations. Senior-level typing requires knowing where static guarantees should be strict, where dynamic behavior is unavoidable, and how unreachable states should be represented.

`Any` is especially powerful and therefore especially dangerous. Excessive use can cause type information to disappear across an entire application.

`Never` is useful for expressing impossible states and exhaustive control flow.

`NoReturn` is historically used for functions that never return, while modern Python typing generally uses `Never` for the return annotation of such functions.

---

## `Any`

`Any` means that the type checker should permit essentially any operation on the value.

```python
from typing import Any


value: Any = get_external_value()

value.some_method()
value["key"]
value + 10
```

Static type checking does not meaningfully constrain those operations.

This makes `Any` useful at genuinely dynamic boundaries, but dangerous as a general-purpose escape hatch.

---

## Why `Any` Exists

Python interacts with systems whose structure may not be statically known:

- dynamic JSON
- third-party libraries without complete type information
- plugin systems
- dynamically loaded modules
- legacy code
- reflection-heavy frameworks
- runtime-generated data
- loosely typed external integrations

`Any` provides an explicit escape hatch for these cases.

Without it, some dynamic Python patterns would be difficult or impossible to model precisely.

The engineering goal is not:

```text
Never use Any
```

but:

```text
Keep Any contained.
```

---

## `Any` Disables Type Safety

Consider:

```python
from typing import Any


value: Any = "hello"

result = value.nonexistent_method()
```

A static type checker generally cannot report the invalid attribute access because `Any` permits it.

Compare this with:

```python
value: str = "hello"

result = value.nonexistent_method()
```

A type checker can identify the invalid operation.

This makes `Any` fundamentally different from `object`.

---

## `Any` vs `object`

`Any` and `object` are often confused.

### `Any`

```python
value: Any

value.foo()
value["key"]
value + 1
```

The type checker permits arbitrary operations.

### `object`

```python
value: object

value.foo()
```

The type checker rejects the operation because `object` does not guarantee that `foo` exists.

You must narrow the value:

```python
if isinstance(value, str):
    print(value.upper())
```

The distinction is:

| Type | Static behavior |
|---|---|
| `Any` | Operations are generally permitted |
| `object` | Operations require narrowing |
| `Never` | No value can exist |

For unknown data, `object` is often safer than `Any`.

---

## `Any` and Implicit Type Leakage

One of the most dangerous properties of `Any` is that it can spread.

Consider:

```python
def load_payload() -> Any:
    ...


payload = load_payload()

user_id = payload["user_id"]
```

Because `payload` is `Any`, the resulting expression may also become `Any`.

Now:

```python
user_id.upper()
```

may pass static analysis even if the runtime value is an integer.

The original `Any` at the boundary has weakened type safety downstream.

```text
Untyped boundary
      │
      ▼
     Any
      │
      ├── Any
      ├── Any
      └── Any
            │
            ▼
     Type safety degraded
```

This is why `Any` should generally be isolated near the dynamic boundary.

---

## Containing `Any`

A better design is:

```python
from typing import Any


def load_payload() -> Any:
    ...


def parse_user_id(payload: Any) -> int:
    raw_value = payload["user_id"]

    if not isinstance(raw_value, int):
        raise ValueError("user_id must be an integer")

    return raw_value
```

After validation:

```python
user_id: int
```

The dynamic region is small.

```text
External data
     │
     ▼
 Any / unknown
     │
     ▼
Validation
     │
     ▼
Precise domain type
```

This pattern is valuable for REST APIs, configuration, plugins, and legacy integrations.

---

## `Any` at API Boundaries

Avoid making an entire API layer dynamically typed:

```python
def create_user(payload: Any) -> Any:
    ...
```

This removes most of the contract.

Prefer:

```python
from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    email: str
    display_name: str


def create_user(payload: CreateUserRequest) -> User:
    ...
```

The framework performs runtime validation while static typing describes the validated application state.

---

## `Any` and JSON

Raw JSON is naturally dynamic.

A low-level parser may produce structures such as:

```python
dict[str, Any]
```

This can be reasonable at the parsing boundary.

But avoid carrying that representation through business logic:

```python
def calculate_price(payload: dict[str, Any]) -> Any:
    ...
```

Prefer converting it into a validated model.

```text
JSON bytes
    │
    ▼
Parser
    │
    ▼
Dynamic representation
    │
    ▼
Validation
    │
    ▼
Typed request model
    │
    ▼
Business logic
```

---

## `Any` and FastAPI

FastAPI works particularly well when runtime validation and static typing reinforce each other.

Prefer:

```python
from fastapi import FastAPI
from pydantic import BaseModel


class CreateOrderRequest(BaseModel):
    product_id: int
    quantity: int


app = FastAPI()


@app.post("/orders")
def create_order(request: CreateOrderRequest) -> OrderResponse:
    ...
```

Avoid:

```python
@app.post("/orders")
def create_order(request: Any) -> Any:
    ...
```

The latter loses both documentation quality and static guarantees.

---

## `Any` and Django

Django's dynamic ORM and framework APIs sometimes expose values whose precise types are difficult for static analyzers to infer.

Using `Any` temporarily can be practical when integrating with:

- legacy models
- dynamic query APIs
- framework internals
- third-party packages

However, application-facing functions should still expose precise contracts.

```python
def get_active_users() -> list[User]:
    ...
```

is substantially better than:

```python
def get_active_users() -> Any:
    ...
```

---

## `Any` and Third-Party Libraries

A dependency without usable type information may introduce `Any`.

For example:

```python
result = untyped_library.fetch()
```

may effectively become dynamically typed.

Instead of allowing that uncertainty to spread, create a typed adapter:

```python
class PaymentGateway:
    def charge(self, request: ChargeRequest) -> Payment:
        ...
```

The adapter isolates the untyped dependency.

```text
Application
     │
     ▼
Typed adapter
     │
     ▼
Untyped third-party library
```

This is often preferable to sprinkling `Any` throughout application code.

---

## `Any` and `cast()`

`cast()` and `Any` are different mechanisms.

```python
from typing import Any, cast


value: Any = get_value()

user = cast(User, value)
```

`cast()` does not validate the value.

The runtime object remains unchanged.

Similarly:

```python
value: Any
```

does not convert the value into a particular runtime type.

Use validation when correctness matters.

---

## Explicit vs Implicit `Any`

`Any` can be introduced explicitly:

```python
value: Any
```

or implicitly through incomplete annotations or untyped APIs, depending on the type checker configuration.

For example:

```python
def process(value):
    ...
```

may result in reduced type checking.

Strict configurations help identify these gaps.

For production codebases, make the type-checking policy explicit rather than allowing accidental dynamic typing.

---

## `Never`

`Never` represents a type with no possible values.

It is useful for expressing:

- unreachable states
- impossible branches
- functions that never return normally
- exhaustive pattern matching
- impossible generic states

Conceptually:

```text
Never
  │
  └── contains no possible runtime value
```

No object can legitimately have the runtime type represented by `Never`.

---

## `Never` as the Bottom Type

In type theory, `Never` is commonly described as the bottom type.

It is a subtype of every type because a value of `Never` can never actually exist.

Conceptually:

```text
        object
       /      \
     str      int
       \      /
        Never
```

The practical consequence is that code reaching a `Never` state is considered unreachable.

---

## `Never` for Unreachable Code

Consider:

```python
from typing import Never


def unreachable() -> Never:
    raise AssertionError("Unreachable")
```

The function cannot return a value.

The type checker can use that information when analyzing control flow.

---

## `Never` for Functions That Always Raise

A function that always raises can use:

```python
from typing import Never


def fail(message: str) -> Never:
    raise RuntimeError(message)
```

Callers do not need to handle a normal return value:

```python
def get_user(user_id: int) -> User:
    user = repository.find(user_id)

    if user is None:
        fail("User not found")

    return user
```

The type checker understands that the branch calling `fail()` does not continue normally.

---

## `Never` vs `NoReturn`

`NoReturn` predates `Never` and historically described functions that never return normally.

```python
from typing import NoReturn


def fail(message: str) -> NoReturn:
    raise RuntimeError(message)
```

Modern typing generally uses:

```python
from typing import Never


def fail(message: str) -> Never:
    raise RuntimeError(message)
```

For a function's return annotation, `Never` is the modern representation of the "no possible return value" concept.

`NoReturn` remains relevant for compatibility and existing codebases.

---

## Why `NoReturn` Still Matters

You will encounter:

```python
from typing import NoReturn
```

in:

- older Python code
- older type annotations
- existing libraries
- documentation
- interview questions

The semantic intent is:

```text
This function never returns normally.
```

When maintaining an existing project, do not blindly rewrite annotations without considering the project's supported Python and typing versions.

---

## `Never` and Exhaustive Matching

One of the most useful applications of `Never` is exhaustive handling of finite variants.

Suppose:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Created:
    ...


@dataclass(frozen=True)
class Deleted:
    ...
```

A handler might process all supported variants.

```python
from typing import Never


def assert_never(value: Never) -> Never:
    raise AssertionError(f"Unhandled value: {value!r}")
```

Then:

```python
def handle_event(event: Created | Deleted) -> str:
    if isinstance(event, Created):
        return "created"

    if isinstance(event, Deleted):
        return "deleted"

    return assert_never(event)
```

If a new event type is added to the union but not handled, a strict type checker can identify the remaining branch.

---

## Exhaustiveness as a Safety Mechanism

This pattern is valuable when a domain has a finite set of states:

```text
OrderStatus
   │
   ├── pending
   ├── paid
   ├── shipped
   └── cancelled
```

Code handling the state should account for all valid cases.

A `Never`-based assertion makes future changes visible to static analysis.

This is especially useful for:

- state machines
- protocol variants
- event types
- command types
- finite domain states
- pattern matching

---

## `Never` and Pattern Matching

Python structural pattern matching can benefit from exhaustive reasoning.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Success:
    value: int


@dataclass(frozen=True)
class Failure:
    message: str


Result = Success | Failure
```

A handler can explicitly account for every known variant:

```python
def render(result: Result) -> str:
    match result:
        case Success(value=value):
            return f"success: {value}"
        case Failure(message=message):
            return f"failure: {message}"
```

When exhaustive checking matters, project-specific typing conventions can add an explicit unreachable branch using `Never`.

---

## `Never` in Conditional Logic

Consider:

```python
def process(value: str | int) -> str:
    if isinstance(value, str):
        return value.upper()

    if isinstance(value, int):
        return str(value)

    raise AssertionError("unreachable")
```

A type checker can reason that after both supported cases, there should be no remaining valid type.

Using an explicit `Never` helper can make that invariant clearer.

---

## `Never` in Generic APIs

`Never` can also appear in generic type expressions.

For example, a type parameter may represent an operation that accepts no valid input:

```python
list[Never]
```

Conceptually, such a list cannot contain any actual value.

This is primarily useful for type-level reasoning rather than ordinary runtime programming.

Most application code should not introduce `Never` into generic types unless the type relationship provides a real benefit.

---

## `Never` vs `None`

These are completely different.

```python
None
```

is an actual runtime value.

```python
Never
```

represents a type with no possible values.

Compare:

```python
def find_user() -> User | None:
    ...
```

with:

```python
def fail() -> Never:
    ...
```

The first function can return `None`.

The second cannot return normally.

---

## `Never` vs `NoReturn` vs `None`

| Type | Runtime value possible? | Normal function return? | Typical use |
|---|---:|---:|---|
| `None` | Yes | Yes | Absence / no meaningful value |
| `NoReturn` | No | No | Legacy annotation for non-returning functions |
| `Never` | No | No | Impossible values and modern non-returning annotations |

A function returning `None` completes normally.

A function returning `Never` does not.

---

## Non-Returning Functions

Typical examples include:

```python
from typing import Never


def terminate_process(exit_code: int) -> Never:
    raise SystemExit(exit_code)
```

and:

```python
def authentication_required() -> Never:
    raise AuthenticationError
```

In a web application, the latter might be used internally by a framework abstraction that always raises an exception or otherwise terminates the current control path.

---

## Exception-Raising Functions

A function that always raises is not equivalent to a function that returns `None`.

```python
def reject_request(message: str) -> Never:
    raise ValueError(message)
```

The caller:

```python
reject_request("invalid request")
print("unreachable")
```

does not normally reach the `print()` statement.

This information can improve control-flow analysis.

---

## `Never` and Async Functions

An async function can also be non-returning:

```python
from typing import Never


async def wait_forever() -> Never:
    while True:
        await asyncio.sleep(3600)
```

The coroutine never completes normally.

The distinction remains between:

```python
async def run() -> None:
    ...
```

which completes with a `None` result, and:

```python
async def run() -> Never:
    ...
```

which never completes normally.

---

## `Any` and Async Code

Be especially careful with `Any` in asynchronous applications.

```python
async def fetch() -> Any:
    ...
```

can cause the result of the coroutine to become dynamically typed:

```python
result = await fetch()
```

This can weaken static checking throughout request handlers and service code.

Prefer:

```python
async def fetch() -> User:
    ...
```

or:

```python
async def fetch() -> User | None:
    ...
```

when the contract is known.

---

## Backend API Example

A service may have:

```python
from typing import Never


def require_user(user: User | None) -> User:
    if user is None:
        raise AuthenticationError

    return user
```

If the helper is explicitly modeled as non-returning:

```python
def authentication_error() -> Never:
    raise AuthenticationError
```

then:

```python
def require_user(user: User | None) -> User:
    if user is None:
        authentication_error()

    return user
```

The type checker can infer that execution continues only when `user` is a `User`.

---

## FastAPI Error Handling

In FastAPI, endpoint code commonly raises HTTP exceptions:

```python
from fastapi import HTTPException


def require_admin(user: User) -> None:
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )
```

The function returns `None` on success and raises on failure.

If an internal helper always raises, `Never` can communicate that behavior more precisely.

Do not annotate every exception-raising function as `Never` merely because one branch raises. The annotation should describe the complete function behavior.

---

## Django Error Handling

The same principle applies to Django services:

```python
from typing import Never


def raise_permission_denied() -> Never:
    raise PermissionError("permission denied")
```

This can be useful in application-level authorization helpers when the helper's contract is explicitly non-returning.

Framework exception handling remains a runtime concern; `Never` only describes the control-flow contract to static tooling.

---

## `Any` in ORM Code

Dynamic ORM APIs sometimes make static typing difficult.

Avoid this pattern:

```python
def get_user(user_id: int) -> Any:
    return User.objects.get(id=user_id)
```

Prefer:

```python
def get_user(user_id: int) -> User:
    return User.objects.get(id=user_id)
```

If a third-party integration genuinely returns `Any`, isolate it at the boundary and convert it to a precise type.

---

## `Any` in Kafka Consumers

A consumer that starts with:

```python
message: Any
```

should validate and normalize quickly.

```python
def handle_message(message: Any) -> None:
    event = parse_event(message)
    process(event)
```

Better:

```python
def handle_message(message: bytes) -> None:
    event = deserialize_event(message)
    process(event)
```

The boundary should reflect what the transport actually provides.

After deserialization:

```python
event: OrderCreated
```

should replace the dynamic representation.

---

## `Any` in Redis Clients

Redis values are commonly bytes or strings depending on client configuration.

Avoid allowing an untyped cache abstraction to expose:

```python
def get(key: str) -> Any:
    ...
```

throughout the application.

Instead, use typed serialization boundaries:

```python
def get_user(key: str) -> User | None:
    ...
```

The cache adapter handles:

```text
Redis bytes
    │
    ▼
Deserialize
    │
    ▼
Validate
    │
    ▼
User | None
```

---

## `Any` in Celery Tasks

Celery tasks often cross a serialization boundary.

Avoid:

```python
def process_order(payload: Any) -> None:
    ...
```

when the message schema is known.

Prefer:

```python
def process_order(order_id: int) -> None:
    ...
```

or a validated task DTO.

The queue transport does not preserve Python static types, so runtime validation remains necessary at the worker boundary.

---

## `Any` and Serialization

Serialization can naturally introduce dynamic data.

For example:

```python
import json
from typing import Any


def parse_json(payload: str) -> Any:
    return json.loads(payload)
```

This can be appropriate as a low-level parser.

A higher-level API should immediately transform the result:

```python
def parse_user(payload: str) -> User:
    raw: Any = json.loads(payload)
    return validate_user(raw)
```

This keeps `Any` local.

---

## Security Implications

`Any` is not a security boundary.

This:

```python
payload: Any
```

does not mean the payload is trusted or valid.

Never interpret static typing as input sanitization.

For untrusted data:

1. Parse the input.
2. Validate its structure.
3. Validate values and constraints.
4. Normalize representations.
5. Apply authorization.
6. Convert to a trusted domain model.

This is especially important for:

- HTTP requests
- Kafka messages
- Redis cache values
- uploaded files
- environment variables
- configuration
- webhooks
- third-party API responses

---

## Performance Considerations

`Any`, `Never`, and `NoReturn` generally have little to no direct runtime performance impact.

The important performance consequences are architectural.

Poor use of `Any` can lead to:

- weaker static analysis
- more runtime validation scattered throughout the application
- more defensive branching
- harder refactoring
- increased debugging cost

`Never` can improve maintainability by making impossible control-flow paths explicit, but it should not be introduced for theoretical type purity at the expense of readability.

---

## Testing Considerations

Static typing does not replace runtime tests.

For `Any` boundaries, test:

- malformed input
- unexpected types
- missing fields
- invalid values
- schema changes
- third-party failures

For `Never` paths, test the actual runtime behavior:

```python
with pytest.raises(AuthenticationError):
    authentication_error()
```

Static analysis verifies the declared control-flow contract; tests verify the runtime behavior.

---

## Static Analysis Configuration

A production Python project should configure a type checker such as mypy or Pyright.

A strict configuration should identify accidental dynamic typing.

For example, mypy can be configured to make untyped definitions and expressions more visible.

The exact configuration should reflect the project's migration strategy, but mature codebases should aim to minimize unexplained `Any`.

Useful practices include:

- strict type checking for new modules
- CI enforcement
- explicit suppression comments
- tracking remaining dynamic areas
- typed wrappers around untyped dependencies
- reviewing new `Any` usage

---

## When `Any` Is Appropriate

Legitimate uses include:

- genuinely dynamic plugin APIs
- untyped third-party libraries
- legacy integration boundaries
- raw JSON before validation
- reflection-heavy framework internals
- generic serialization infrastructure

Even then:

```text
Any should be a boundary,
not an architecture.
```

Document why the dynamic boundary exists when it is not obvious.

---

## When `Any` Is a Design Smell

Be suspicious when `Any` appears in:

```python
def service(...) -> Any:
    ...
```

or:

```python
class Repository:
    def get(...) -> Any:
        ...
```

or throughout domain models.

Frequent `Any` usage can indicate:

- unclear contracts
- missing domain models
- poor third-party integration boundaries
- insufficient validation
- weak static-analysis configuration
- legacy code requiring refactoring

A useful engineering metric is not "zero `Any`" but **controlled and explainable dynamic typing**.

---

## When to Use `Never`

Use `Never` when it improves a meaningful type relationship:

- non-returning functions
- impossible branches
- exhaustive union handling
- unreachable states
- type-level APIs that intentionally have no valid values

Avoid using it merely because a branch "should never happen" without considering whether that invariant is actually enforced.

---

## When to Use `NoReturn`

Use `NoReturn` primarily when:

- maintaining existing code
- supporting older typing conventions
- working with APIs already documented using `NoReturn`
- compatibility with a project's established type annotations matters

For modern Python typing, prefer `Never` for new non-returning function annotations when the project's supported tooling handles it correctly.

---

## Decision Guide

| Situation | Recommended type |
|---|---|
| Completely dynamic value | `Any`, preferably at a narrow boundary |
| Unknown but should require narrowing | `object` |
| Value can never exist | `Never` |
| Function never returns normally | `Never` for modern code |
| Existing code uses legacy non-returning annotation | `NoReturn` |
| Nullable result | `T \| None` |
| Multiple legitimate alternatives | `A \| B` |
| Raw external JSON | Dynamic boundary, then validate |
| Untyped third-party dependency | Typed adapter |
| Exhaustive union handling | `Never` helper |
| Programmer assertion of impossible state | `Never` helper or explicit exception |

---

## Production Pitfalls

### Using `Any` Everywhere

```python
def create_order(data: Any) -> Any:
    ...
```

This makes the type system almost irrelevant.

**Better:** validate input and expose a precise model.

### Using `Any` Instead of `object`

If a value is genuinely unknown but should be narrowed before use:

```python
value: object
```

is safer than:

```python
value: Any
```

### Assuming `cast()` Validates `Any`

It does not.

### Treating `Never` as a Runtime Value

`Never` is a type-level concept representing an impossible value.

### Returning `None` from a `Never` Function

This violates the declared contract.

```python
def fail() -> Never:
    return None
```

is incorrect.

### Marking Partially Returning Functions as `Never`

This is incorrect:

```python
def process(value: bool) -> Never:
    if value:
        raise RuntimeError()

    return
```

The function can return normally, so `Never` is not an accurate return type.

### Using `Never` Without Exhaustive Reasoning

A `Never` assertion should represent a genuinely impossible state according to the type model.

### Assuming Static Types Provide Security

They do not validate untrusted data.

### Letting Dynamic Data Cross Domain Boundaries

Keep `Any` close to the parser or adapter and convert to a validated domain type.

---

## Architecture Pattern

A robust backend architecture keeps dynamic typing near external boundaries:

```mermaid
flowchart LR
    A[External Input] --> B[Dynamic Boundary]
    B --> C[Parsing]
    C --> D[Runtime Validation]
    D --> E[Typed Domain Model]
    E --> F[Service Layer]
    F --> G[Repository / Client]
    G --> H[Database / Kafka / Redis]

    B -. "Any / unknown" .-> C
    E -. "Precise types" .-> F
```

The design objective is:

```text
Dynamic outside
      ↓
Validated boundary
      ↓
Strongly typed core
      ↓
Predictable infrastructure interfaces
```

This reduces the blast radius of untyped data.

---

## Senior-Level Mental Model

Think about these types as different levels of certainty.

```text
Any
 │
 │  "I do not know or do not want to enforce the type."
 ▼
object
 │
 │  "I know it is an object, but I need to inspect it."
 ▼
Specific type / Union
 │
 │  "I know the valid alternatives."
 ▼
Never
 │
 │  "There is no valid value here."
```

`NoReturn` sits on the control-flow side:

```text
Function
   │
   ├── returns normally → T / None
   │
   └── never returns normally → Never
```

This mental model is useful when reviewing application boundaries and type contracts.

---

## Interview Traps

### What is the difference between `Any` and `object`?

`Any` disables most static checking for the value. `object` is the universal runtime base type, but operations require type narrowing.

### What is `Never`?

`Never` represents a type with no possible values and is useful for impossible states, unreachable branches, exhaustive checking, and non-returning functions.

### What is `NoReturn`?

`NoReturn` is the older typing construct used to indicate that a function never returns normally. Modern Python typing generally uses `Never` for this purpose.

### Does a function returning `None` never return?

No. It returns normally and its return value is the `None` singleton.

### Does `Never` exist as a runtime object?

No. It is a type-system construct, not a value that application code should produce.

### Why is `Any` dangerous?

Because it can allow invalid operations and propagate loss of type information into downstream code.

### Why can `object` be safer than `Any`?

`object` forces the caller to narrow the value before using type-specific operations.

### When should `Never` be used for exhaustive checking?

When the type system says all valid variants have already been handled and the remaining branch is genuinely impossible.

### Does `cast()` convert an `Any` value into another type?

No. It changes only the static type assumption.

### Should every exception-raising function return `Never`?

No. Only functions that cannot return normally on any execution path should be annotated that way.

---

## Production Checklist

Before using `Any`, `Never`, or `NoReturn`, verify:

- `Any` is confined to genuinely dynamic boundaries.
- Dynamic external data is validated before entering domain logic.
- `object` is preferred when a value is unknown but should be narrowed.
- Typed adapters isolate untyped third-party libraries.
- Public service and repository APIs expose precise types.
- `Any` is not being used merely to silence type-checking errors.
- `cast()` is not being mistaken for runtime validation.
- `Never` is used only for genuinely impossible values or non-returning control flow.
- Functions annotated with `Never` cannot complete normally.
- `None` is not confused with `Never`.
- `NoReturn` is understood as the legacy equivalent for non-returning function annotations.
- New code uses `Never` where the project's Python and typing tooling support it.
- Exhaustive union handling is checked by static analysis.
- Impossible branches fail loudly at runtime if invariants are violated.
- Static type checking runs in CI/CD.
- New or unexplained `Any` usage is reviewed.
- Runtime validation remains in place for HTTP, Kafka, Redis, configuration, and other external boundaries.
- Type annotations are not treated as security controls.
- Dynamic typing does not leak into core business logic.
- Generic abstractions remain precise after crossing serialization boundaries.
- The type model reflects actual runtime behavior rather than desired behavior.

## Key Takeaways

- `Any` is an intentional escape hatch from static typing; keep it narrow, explainable, and close to genuinely dynamic boundaries.
- `object` is safer than `Any` when a value is unknown because it forces explicit type narrowing before type-specific operations.
- `Never` represents an impossible value and is useful for exhaustive union handling, unreachable branches, and functions that cannot return normally.
- `NoReturn` is the older spelling for non-returning functions; modern Python typing generally uses `Never` for new annotations.
- Static types describe contracts but do not validate untrusted data, enforce security, or guarantee runtime behavior; production systems still need validation, testing, and explicit failure handling.