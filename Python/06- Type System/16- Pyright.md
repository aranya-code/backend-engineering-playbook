# 16- Pyright

## Overview

[Pyright](https://microsoft.github.io/pyright/) is a static type checker for Python. It analyzes Python source code, type annotations, inferred types, imports, generics, protocols, control flow, and function contracts without executing the application.

Pyright is commonly used through:

- The `pyright` command-line tool.
- VS Code through the Pylance language server.
- CI/CD pipelines.
- Editor-integrated diagnostics and autocomplete.

Python remains dynamically typed at runtime. Pyright does not add runtime type enforcement; it provides compile-time-like feedback during development and static analysis during CI.

For backend systems, Pyright is most valuable where multiple components must agree on contracts:

```text
HTTP Request
     │
     ▼
API / DTO
     │
     ▼
Service
     │
     ▼
Repository Protocol
     │
     ▼
PostgreSQL
```

The goal is not to annotate every line of Python. The goal is to make important contracts explicit, discoverable, and mechanically verifiable.

---

## Why Pyright Matters

Dynamic Python is productive, but implicit contracts become difficult to maintain as applications grow.

Consider:

```python
def calculate_total(price, quantity):
    return price * quantity
```

The function does not communicate:

- what `price` represents
- what `quantity` represents
- what the return value represents
- whether `None` is allowed
- whether subclasses are supported

A typed interface provides stronger information:

```python
def calculate_total(
    price: float,
    quantity: int,
) -> float:
    return price * quantity
```

Pyright can then analyze callers and implementations against that contract.

This becomes particularly valuable during:

- large refactors
- API changes
- dependency upgrades
- repository changes
- domain model changes
- shared-library development
- microservice development

---

## What Pyright Does

A simplified analysis flow is:

```text
Python source
      │
      ▼
Parse source
      │
      ▼
Read annotations
      │
      ▼
Infer types
      │
      ▼
Analyze control flow
      │
      ▼
Resolve imports and symbols
      │
      ▼
Check type relationships
      │
      ▼
Report diagnostics
```

Pyright can identify problems such as:

- incompatible assignments
- invalid function arguments
- incorrect return types
- missing attributes
- incompatible overrides
- invalid generic usage
- protocol mismatches
- unsafe optional handling
- unreachable or inconsistent code in some situations
- invalid overload definitions
- unknown or partially unknown types

---

## What Pyright Does Not Do

Pyright does not:

- Execute application logic.
- Validate HTTP payloads at runtime.
- Validate arbitrary JSON.
- Verify database contents.
- Verify authentication.
- Verify authorization.
- Replace tests.
- Detect every business logic error.
- Guarantee thread safety.
- Guarantee network reliability.
- Guarantee runtime type correctness.

For example:

```python
def get_user(user_id: int) -> User:
    ...
```

does not cause the Python interpreter to reject:

```python
get_user("123")
```

Pyright can report the incorrect call statically, but Python itself does not enforce the annotation.

---

## Installation

Install Pyright as a development dependency:

```bash
python -m pip install pyright
```

Then:

```bash
pyright
```

You can also invoke it through Python:

```bash
python -m pyright
```

Depending on the environment and installation method, the executable may be exposed directly as `pyright`.

For reproducible CI, pin the version through the project's dependency-management system.

---

## Editor Integration

Pyright provides strong editor feedback, and Microsoft's Pylance uses Pyright's type-analysis technology for Python language intelligence in VS Code.

Typical editor capabilities include:

- autocomplete
- type information
- diagnostics
- symbol navigation
- references
- rename support
- inferred type inspection
- import diagnostics

This makes type errors visible while code is being written rather than only after running CI.

---

## Basic Example

Consider:

```python
def get_user_name(user_id: int) -> str:
    return 123
```

Pyright can report that the returned `int` is incompatible with `str`.

Correct:

```python
def get_user_name(user_id: int) -> str:
    return "alice"
```

The checker verifies the relationship between the implementation and the declared contract.

---

## Type Inference

Pyright performs extensive type inference.

```python
name = "alice"
count = 10
enabled = True
```

The inferred types are:

```text
name    → str
count   → int
enabled → bool
```

Inference also works through collections:

```python
users = ["alice", "bob"]

for user in users:
    print(user.upper())
```

Pyright understands that `user` is a `str`.

Good typing does not require manually annotating every local variable.

---

## Explicit Types at Boundaries

Use explicit annotations where they communicate architectural contracts.

```python
def create_order(
    request: CreateOrderRequest,
    repository: OrderRepository,
) -> Order:
    ...
```

This makes the service interface obvious:

```text
CreateOrderRequest
       │
       ▼
    Service
       │
       ▼
OrderRepository
       │
       ▼
     Order
```

Local implementation details can usually rely on inference.

---

## Configuration

Pyright supports project configuration through `pyrightconfig.json` or configuration in `pyproject.toml`.

Example:

```json
{
  "include": [
    "src",
    "tests"
  ],
  "exclude": [
    "**/__pycache__",
    ".venv",
    "build",
    "dist"
  ],
  "typeCheckingMode": "strict"
}
```

The configuration should be committed to version control.

This ensures developers and CI use the same type-checking policy.

---

## `pyrightconfig.json`

A dedicated configuration file can be useful when the project wants Pyright-specific settings:

```json
{
  "include": ["src", "tests"],
  "exclude": ["build", "dist", ".venv"],
  "typeCheckingMode": "strict",
  "reportMissingImports": true,
  "reportMissingTypeStubs": false
}
```

Avoid copying configuration options without understanding their impact.

A smaller, explicit configuration is easier to maintain.

---

## `pyproject.toml`

Pyright can also be configured in `pyproject.toml`:

```toml
[tool.pyright]
include = ["src", "tests"]
exclude = [
    "**/__pycache__",
    ".venv",
    "build",
    "dist",
]
typeCheckingMode = "strict"
```

Choose one primary configuration location for the repository rather than maintaining conflicting configurations.

---

## Type Checking Modes

Pyright supports several checking modes:

| Mode | Purpose |
|---|---|
| `off` | Disable type checking |
| `basic` | Basic type analysis |
| `standard` | Stronger default analysis |
| `strict` | Aggressive type checking |

For production backend systems, `standard` or `strict` is generally preferable once the codebase has sufficient typing coverage.

Legacy applications may begin with a less strict mode and migrate incrementally.

---

## Strict Mode

Strict mode catches more potential defects.

Example:

```json
{
  "typeCheckingMode": "strict"
}
```

Strict checking can expose:

- missing annotations
- unknown types
- unsafe operations
- incompatible overrides
- incomplete generic declarations
- invalid optional handling
- partially typed dependencies

Do not confuse strictness with quality by itself.

The important objective is consistent, useful type guarantees.

---

## Strictness Migration

A legacy codebase may not be ready for strict mode immediately.

A practical strategy:

```text
Legacy codebase
      │
      ▼
Run Pyright
      │
      ▼
Measure errors
      │
      ▼
Type critical boundaries
      │
      ▼
Prevent new errors
      │
      ▼
Increase strictness
      │
      ▼
Reduce type debt
```

This allows type safety to improve without requiring an immediate rewrite.

---

## Type Inference vs Annotation

Prefer:

```python
users = load_users()
```

when `load_users()` already has a precise return type.

Avoid unnecessary duplication:

```python
users: list[User] = load_users()
```

unless the annotation improves readability, constrains inference intentionally, or documents an important boundary.

Use explicit annotations for:

- public functions
- complex callbacks
- important class attributes
- protocol interfaces
- ambiguous values
- reusable library APIs

---

## `Any`

`Any` weakens static checking.

```python
from typing import Any

value: Any = external_library()
```

Once a value becomes `Any`, many operations are allowed without normal type verification.

For example:

```python
value: Any = "hello"

value.unknown_method()
value.not_a_real_attribute
```

This can hide real defects.

---

## Unknown Types

Pyright distinguishes unknown or incompletely understood values from known types.

This is an important difference when compared with simply allowing everything to become `Any`.

For example, a value returned from a poorly typed dependency may be effectively unknown.

The desired workflow is:

```text
Unknown external value
        │
        ▼
Validate / narrow
        │
        ▼
Precise application type
```

This is safer than allowing dynamic values to spread through core services.

---

## `Any` vs `Unknown`

A useful mental model is:

```text
Any
→ "Assume this is safe."

Unknown
→ "We do not know what this is yet."
```

With an unknown value, Pyright encourages explicit narrowing or validation.

For example:

```python
value = load_external_value()

if isinstance(value, str):
    print(value.upper())
```

The type becomes known after the runtime check.

---

## `object` vs `Any`

`object` is useful when the code genuinely accepts arbitrary Python objects.

```python
def process(value: object) -> None:
    ...
```

You cannot safely call arbitrary methods:

```python
def process(value: object) -> None:
    value.upper()
```

Instead:

```python
def process(value: object) -> None:
    if isinstance(value, str):
        print(value.upper())
```

The distinction is:

```text
Any
→ disables many checks

object
→ permits only operations guaranteed by object
```

---

## Optional Values

Pyright can identify unsafe use of nullable values.

```python
def find_user(user_id: int) -> User | None:
    ...
```

Correct:

```python
user = find_user(user_id)

if user is None:
    raise UserNotFoundError(user_id)

return user.email
```

Unsafe:

```python
user = find_user(user_id)

return user.email
```

Strict checking makes nullable contracts visible to callers.

---

## Type Narrowing

Pyright performs control-flow-based narrowing.

```python
def normalize(value: str | int) -> str:
    if isinstance(value, str):
        return value.upper()

    return str(value)
```

Conceptually:

```text
Before:
str | int

True branch:
str

Else branch:
int
```

This is one of the most useful features of a static analyzer because it allows dynamic Python operations to remain precise.

---

## User-Defined Type Guards

Use `TypeGuard` for reusable predicates:

```python
from typing import TypeGuard


def is_user(value: object) -> TypeGuard[User]:
    return isinstance(value, User)
```

Then:

```python
value: object = load_value()

if is_user(value):
    value.send_email()
```

The predicate communicates the intended narrowing relationship to Pyright.

The implementation must still be logically correct. Static analysis cannot prove arbitrary custom predicate correctness.

---

## `TypeIs`

Modern Python typing also provides `TypeIs`.

```python
from typing import TypeIs


def is_string(value: object) -> TypeIs[str]:
    return isinstance(value, str)
```

`TypeIs` is useful when the predicate expresses a type relationship compatible with intersection-style narrowing and provides stronger information about both branches than a `TypeGuard` in appropriate cases.

Choose between `TypeGuard` and `TypeIs` according to the semantics of the predicate.

---

## Generics

Pyright supports modern generic syntax:

```python
def first[T](items: list[T]) -> T:
    return items[0]
```

Usage:

```python
name = first(["alice", "bob"])
user_id = first([100, 200])
```

Pyright can infer:

```text
name    → str
user_id → int
```

Generics are useful when an operation preserves relationships between types.

---

## TypeVar

Traditional generic syntax uses `TypeVar`:

```python
from typing import TypeVar


T = TypeVar("T")


def first(items: list[T]) -> T:
    return items[0]
```

`TypeVar` expresses relationships between types.

It is static metadata and does not create a runtime wrapper.

---

## Bounds and Constraints

Bounded type variables:

```python
from typing import TypeVar


T = TypeVar("T", bound=User)


def refresh(user: T) -> T:
    user.reload()
    return user
```

Constrained type variables:

```python
Number = TypeVar("Number", int, float)
```

Use bounds when a generic type must satisfy a common capability or hierarchy.

Use constraints when the valid alternatives are intentionally restricted to a known set.

---

## Variance

Generic APIs can involve:

- covariance
- contravariance
- invariance

For example, a producer may safely expose a subtype where a base type is expected, while a consumer may have the opposite relationship.

This becomes important when designing:

- repositories
- event consumers
- callback interfaces
- generic protocols
- reusable libraries

Do not introduce variance annotations simply because they are available.

Use them when the API's producer/consumer semantics require them.

---

## Protocols

Pyright supports structural typing through `Protocol`.

```python
from typing import Protocol


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None:
        ...
```

A concrete implementation does not need to inherit from the protocol:

```python
class PostgresUserRepository:
    def get(self, user_id: int) -> User | None:
        ...
```

Pyright can determine whether the implementation structurally satisfies the protocol.

---

## Protocol-Based Dependency Injection

A service can depend on the protocol:

```python
class UserService:
    def __init__(
        self,
        repository: UserRepository,
    ) -> None:
        self.repository = repository
```

Implementations can include:

```text
UserRepository
      │
      ├── PostgreSQL implementation
      ├── In-memory implementation
      └── Test fake
```

This supports dependency inversion without requiring inheritance.

---

## TypedDict

Pyright understands dictionary-shaped contracts:

```python
from typing import TypedDict


class UserPayload(TypedDict):
    id: int
    email: str
```

It can detect incorrect key usage and incompatible values.

However:

```python
payload: UserPayload
```

does not validate an arbitrary dictionary at runtime.

For external JSON:

```text
JSON
 │
 ▼
Parse
 │
 ▼
Runtime validation
 │
 ▼
Typed object
 │
 ▼
Application logic
```

---

## Required and Optional TypedDict Fields

Modern typing allows more precise dictionary contracts:

```python
from typing import NotRequired, TypedDict


class UserPatch(TypedDict):
    email: NotRequired[str]
    display_name: NotRequired[str]
```

This is useful for PATCH-style APIs where field absence has semantic meaning.

Remember:

```text
field absent
≠
field present with None
```

Model these states explicitly when the API requires the distinction.

---

## `Literal`

Pyright can narrow finite values:

```python
from typing import Literal


def set_mode(
    mode: Literal["sync", "async"],
) -> None:
    ...
```

Invalid values can be detected statically:

```python
set_mode("invalid")
```

`Literal` is useful for:

- configuration modes
- state values
- protocol flags
- feature switches
- overload discrimination
- finite command variants

---

## Overloads

Pyright supports overloads:

```python
from typing import Literal, overload


@overload
def fetch(
    resource: Literal["user"],
) -> User:
    ...


@overload
def fetch(
    resource: Literal["order"],
) -> Order:
    ...


def fetch(
    resource: Literal["user", "order"],
) -> User | Order:
    ...
```

Pyright uses the overload signatures when analyzing callers.

Only the final implementation executes at runtime.

---

## Overload Ordering

Overload definitions should be carefully ordered and should not overlap unnecessarily.

Badly designed overloads can produce:

- ambiguous calls
- unreachable overloads
- confusing inferred return types
- maintenance problems

Use overloads when return types genuinely depend on argument combinations.

Prefer a union when the return type is simply one of several alternatives regardless of the input.

---

## `Callable`

Pyright understands callable contracts:

```python
from collections.abc import Callable


def execute(
    operation: Callable[[Order], PaymentResult],
    order: Order,
) -> PaymentResult:
    return operation(order)
```

This is useful for:

- callbacks
- strategy functions
- dependency injection
- middleware
- event handlers
- task handlers

---

## `ParamSpec`

For decorators and higher-order functions:

```python
from collections.abc import Callable
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def traced(
    function: Callable[P, R],
) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return function(*args, **kwargs)

    return wrapper
```

`ParamSpec` preserves the wrapped callable's parameter structure.

This is substantially more precise than:

```python
Callable[..., Any]
```

---

## `Self`

Pyright supports `Self` for subtype-preserving APIs:

```python
from typing import Self


class Query:
    def filter(self, **conditions: object) -> Self:
        return self
```

This is useful for:

- fluent APIs
- builders
- query objects
- chainable configuration APIs

---

## Dataclasses

Pyright understands standard dataclasses:

```python
from dataclasses import dataclass


@dataclass
class User:
    id: int
    email: str
```

It can infer constructor requirements and detect invalid construction:

```python
User(id="abc", email=123)
```

This is useful for domain objects and DTOs.

Runtime validation is still a separate responsibility.

---

## Pydantic and Pyright

Pydantic and Pyright solve different problems.

```text
External JSON
      │
      ▼
Pydantic
      │
      ├── Runtime validation
      └── Parsed model
              │
              ▼
       Application logic
              │
              ▼
          Pyright
      static verification
```

Pydantic verifies actual runtime data.

Pyright verifies source-code type relationships.

A FastAPI application benefits from both.

---

## FastAPI

FastAPI makes extensive use of Python annotations.

```python
from fastapi import FastAPI


app = FastAPI()


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int) -> UserResponse:
    ...
```

Pyright helps verify application code around:

- route handlers
- dependencies
- service calls
- response construction
- repository interfaces
- client integrations

FastAPI's runtime validation remains necessary.

---

## Django

Django applications can use Pyright for:

- service functions
- domain models
- repository interfaces
- serializers
- management commands
- background tasks
- integrations

Django's dynamic ORM and framework behavior can require additional typing support or explicit abstractions.

A useful strategy is:

```text
Dynamic Django behavior
        │
        ▼
Typed application boundary
        │
        ▼
Typed domain/service layer
```

---

## PostgreSQL

Pyright can verify application-level repository contracts:

```python
class UserRepository(Protocol):
    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        ...
```

It cannot verify:

- SQL correctness in every runtime case
- database availability
- transaction isolation behavior
- migration safety
- data integrity
- query performance

Those require database-level testing and operational controls.

---

## Redis

A typed cache interface can hide serialization details:

```python
class UserCache(Protocol):
    async def get(self, user_id: int) -> User | None:
        ...

    async def set(
        self,
        user: User,
        ttl_seconds: int,
    ) -> None:
        ...
```

The implementation still needs:

```text
User
 ↓
Serialize
 ↓
Redis
 ↓
Deserialize
 ↓
User
```

Pyright checks the Python interface, not Redis's actual bytes.

---

## Kafka

Kafka processing should validate external data before passing it into strongly typed application logic.

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
Typed event
    │
    ▼
Pyright-checked handler
    │
    ▼
Business logic
```

Static typing begins to provide strong guarantees after the dynamic boundary has been converted into a known representation.

---

## Celery

Background task functions benefit from explicit types:

```python
@app.task
def generate_report(report_id: int) -> str:
    ...
```

Pyright can verify Python callers and implementations.

Celery's actual transport still involves serialization and worker processes.

Production systems therefore need:

- task schema compatibility
- idempotency
- retries
- timeouts
- failure handling
- versioning where required

---

## REST API Contracts

A useful application architecture is:

```text
HTTP JSON
    │
    ▼
Runtime validation
    │
    ▼
Request DTO
    │
    ▼
Typed service
    │
    ▼
Domain object
    │
    ▼
Typed repository
    │
    ▼
Database
```

Pyright verifies the Python-side contracts.

OpenAPI remains the external API contract.

---

## gRPC

gRPC already provides explicit protobuf contracts.

A useful flow is:

```text
.proto schema
      │
      ▼
Code generation
      │
      ▼
Python client/server types
      │
      ▼
Pyright
      │
      ▼
Application logic
```

Do not treat Python annotations as a replacement for protobuf schemas.

---

## Dynamic Python

Python supports highly dynamic behavior:

```python
getattr(obj, name)
setattr(obj, name, value)
```

It also supports:

- metaclasses
- dynamic attributes
- decorators
- descriptors
- monkey patching
- runtime registration

Static analysis cannot always infer these behaviors precisely.

The preferred architecture is:

```text
Dynamic implementation
        │
        ▼
Explicit typed adapter
        │
        ▼
Typed application
```

This keeps dynamic behavior isolated.

---

## Third-Party Dependencies

A dependency may provide:

- inline annotations
- stub files
- incomplete typing
- incorrect typing
- no useful typing

When a library is poorly typed, isolate it behind an adapter:

```text
Application
    │
    ▼
Typed Adapter
    │
    ▼
Third-party Library
```

This prevents unknown or dynamic values from spreading through core business logic.

---

## Stub Files

A `.pyi` file describes an API without implementation.

Example:

```python
class PaymentClient:
    def charge(
        self,
        customer_id: str,
        amount_cents: int,
    ) -> PaymentResult:
        ...
```

Stubs can be useful for:

- third-party packages
- C extensions
- generated libraries
- runtime-heavy APIs

Prefer official typing information when available.

---

## Type-Only Imports

Some imports exist only for static analysis:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.payment import PaymentClient
```

This can prevent runtime circular imports.

However, type-only imports should not become a permanent workaround for poor package architecture.

Use them deliberately.

---

## Forward References

Types can refer to classes that are defined later.

```python
from __future__ import annotations


class User:
    def create_manager(self) -> UserManager:
        ...


class UserManager:
    ...
```

Using postponed annotation evaluation can simplify forward references and reduce some runtime annotation concerns.

Configure the checker and runtime version consistently.

---

## Type Aliases

Pyright supports modern type aliases:

```python
type UserId = int
type UserMap = dict[UserId, User]
```

For semantically distinct values, `NewType` may be more appropriate:

```python
from typing import NewType


UserId = NewType("UserId", int)
```

The distinction matters because a plain alias does not create a distinct static type.

---

## `NewType`

Use `NewType` when two values share the same runtime representation but should not be freely interchangeable.

```python
from typing import NewType


UserId = NewType("UserId", int)
OrderId = NewType("OrderId", int)
```

Then:

```python
def get_user(user_id: UserId) -> User:
    ...
```

Pyright can detect accidental mixing of these domain identifiers.

---

## `Final`

Pyright can enforce non-reassignment of values:

```python
from typing import Final


MAX_RETRIES: Final = 5
```

Useful examples include:

- constants
- protocol identifiers
- immutable configuration references
- application-level limits

`Final` does not make referenced mutable objects deeply immutable.

---

## `ClassVar`

Class-level fields can be explicitly represented:

```python
from typing import ClassVar


class ConnectionPool:
    active_connections: ClassVar[int] = 0
```

This helps static analysis distinguish class state from instance state.

---

## `Annotated`

`Annotated` can attach metadata to a type:

```python
from typing import Annotated


UserId = Annotated[int, "positive user identifier"]
```

Frameworks can use this metadata for runtime behavior, while Pyright can still analyze the underlying type.

Do not assume arbitrary metadata automatically produces validation.

---

## Mypy vs Pyright

Both tools provide Python static type checking, but they differ in implementation, configuration, diagnostics, and inference behavior.

| Area | Pyright | Mypy |
|---|---|---|
| Static type checking | Yes | Yes |
| Type inference | Strong | Strong |
| Strict checking | Yes | Yes |
| CLI | `pyright` | `mypy` |
| Project configuration | `pyrightconfig.json` / `pyproject.toml` | `pyproject.toml` / `mypy.ini` / others |
| VS Code integration | Excellent through Pylance | Available through extensions |
| Language-server ecosystem | Strong | Strong |
| Behavior compatibility | High, but not identical | High, but not identical |
| Best choice | Project-dependent | Project-dependent |

Do not assume that code accepted by one checker will always produce identical diagnostics in the other.

---

## Choosing Pyright vs Mypy

Choose based on project needs rather than popularity.

Pyright is particularly attractive when:

- VS Code is the primary development environment.
- Fast interactive feedback matters.
- Strong inference is valuable.
- The team prefers Pyright's diagnostic model.
- Pylance is already standardized.

Mypy is particularly attractive when:

- The existing Python ecosystem is already standardized around it.
- The team has established mypy configuration and CI.
- Existing plugins or tooling depend on mypy.
- The repository already has extensive mypy type infrastructure.

For most teams, one primary checker is preferable to running both without a specific reason.

---

## CI/CD Integration

A production CI pipeline might contain:

```yaml
steps:
  - name: Install dependencies
    run: python -m pip install -e ".[dev]"

  - name: Lint
    run: ruff check .

  - name: Type check
    run: pyright

  - name: Tests
    run: pytest
```

The exact tooling can differ.

The important principle is:

```text
Type checking
      ↓
Required CI gate
      ↓
Tests
      ↓
Build
      ↓
Deploy
```

Do not rely entirely on developers remembering to run Pyright locally.

---

## GitHub Actions

A minimal example:

```yaml
name: Python CI

on:
  pull_request:
  push:

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: python -m pip install -e ".[dev]"
      - run: pyright
      - run: pytest
```

Pin the relevant development dependencies through the project's dependency management strategy.

---

## Docker

Static analysis should happen before the production image is published.

```text
Git push
   │
   ▼
CI
 ├── Lint
 ├── Pyright
 ├── Tests
 └── Security scans
   │
   ▼
Docker build
   │
   ▼
Container registry
   │
   ▼
ECS / EKS / Kubernetes
```

This avoids discovering obvious type defects only after producing a deployment artifact.

---

## Kubernetes

For Kubernetes workloads, Pyright belongs in CI rather than the application startup path.

Do not make a pod start command perform a full type check:

```text
Bad:
Pod startup → Pyright → Application

Good:
CI → Pyright → Build → Deploy → Application
```

Static analysis is a build-time quality gate, not a runtime health check.

---

## AWS

Pyright can be integrated into CI pipelines deploying to:

- ECS
- EKS
- Lambda
- AWS Batch
- containerized workers

For example:

```text
Developer
   │
   ▼
Git
   │
   ▼
CI
   ├── Pyright
   ├── Tests
   └── Security checks
   │
   ▼
Artifact
   │
   ▼
AWS deployment
```

Runtime services still require their own validation and operational controls.

---

## Performance

Pyright affects development and CI performance rather than normal application runtime performance.

For large repositories, analysis cost can increase with:

- large dependency graphs
- generated code
- extensive generic usage
- complex protocols
- large monorepos
- poorly isolated packages

Optimize the development workflow rather than weakening type safety unnecessarily.

---

## Large Repositories

A monorepo might look like:

```text
repository/
├── services/
│   ├── users/
│   ├── orders/
│   └── payments/
├── libraries/
│   ├── auth/
│   └── messaging/
└── infrastructure/
```

Use explicit source boundaries:

```json
{
  "include": [
    "services",
    "libraries"
  ],
  "exclude": [
    "build",
    "dist",
    "generated"
  ]
}
```

The exact structure should match the repository.

Generated or vendor code should be excluded only when doing so does not hide important compatibility problems.

---

## Incremental Analysis

Large codebases benefit from fast feedback.

A useful workflow is:

```text
Developer edit
      │
      ▼
Editor diagnostics
      │
      ▼
Fast local Pyright
      │
      ▼
Commit
      │
      ▼
Full CI analysis
```

The editor should provide immediate feedback while CI remains authoritative.

---

## Type Checking and Refactoring

One of Pyright's strongest benefits is refactoring safety.

Suppose:

```python
def get_user(user_id: int) -> User:
    ...
```

changes to:

```python
def get_user(user_id: UserId) -> User:
    ...
```

Pyright can identify incompatible callers.

This becomes especially valuable in:

- large monoliths
- monorepos
- shared libraries
- backend platforms
- domain-heavy applications

---

## Type Checking and Architecture

Static types can encode architectural boundaries.

For example:

```text
API DTO
  │
  ▼
Application Command
  │
  ▼
Domain Model
  │
  ▼
Repository Protocol
  │
  ▼
Infrastructure Adapter
```

Pyright can verify the Python-level relationships between these components.

Types therefore provide architectural value beyond autocomplete.

---

## Dependency Inversion

Instead of:

```text
Service
   │
   ▼
PostgreSQLRepository
```

prefer:

```text
Service
   │
   ▼
Repository Protocol
   ▲
   │
PostgreSQLRepository
```

Pyright verifies that the concrete repository satisfies the protocol.

This supports dependency inversion and makes testing easier.

---

## Runtime Validation Boundaries

A robust backend separates static contracts from runtime validation:

```text
External input
      │
      ▼
Runtime validation
      │
      ▼
Typed model
      │
      ▼
Application logic
      │
      ▼
Static verification
```

For FastAPI:

```text
HTTP JSON
    │
    ▼
Pydantic
    │
    ▼
Request model
    │
    ▼
Typed service
    │
    ▼
Repository protocol
```

Pyright verifies the application code.

Pydantic validates actual runtime input.

---

## Security Considerations

Pyright is not a security boundary.

This:

```python
user_id: int = request.json["user_id"]
```

does not prove that:

- the value is actually an integer
- the user is authenticated
- the user is authorized
- the resource belongs to the user

Security still requires:

- authentication
- authorization
- runtime validation
- SQL parameterization
- secret management
- rate limiting
- dependency scanning
- audit logging

Static typing reduces implementation risk but does not establish trust.

---

## Reliability

Pyright improves reliability by catching type-related defects before deployment.

It is especially valuable during:

- refactoring
- dependency upgrades
- API changes
- schema changes
- repository replacements
- event model changes

It does not protect against:

- network failures
- database outages
- corrupted data
- race conditions
- incorrect business requirements
- infrastructure failures

Combine static analysis with runtime reliability mechanisms.

---

## Testing

Pyright and tests provide different guarantees.

| Problem | Pyright | Tests |
|---|---:|---:|
| Incorrect argument type | Yes | Sometimes |
| Incorrect return type | Yes | Sometimes |
| Missing attribute | Yes | Sometimes |
| Runtime JSON validation | No | Yes |
| Business logic defect | Usually no | Yes |
| Database failure | No | Yes |
| Authentication bug | No | Yes |
| Race condition | No | Sometimes |
| Network timeout | No | Yes |
| API contract behavior | Partially | Yes |

A production system should use both.

---

## Type Checking and Contract Tests

Static typing verifies Python-side contracts.

Contract tests verify runtime contracts between systems.

For example:

```text
OpenAPI / protobuf
       │
       ├── Static application contracts
       │
       └── Runtime contract tests
```

This distinction is especially important for microservices.

---

## Type Checking and Serialization

Static types describe Python objects.

Serialization converts objects to external representations:

```text
User
 │
 ▼
JSON / Protobuf / Avro
 │
 ▼
Network / Kafka / Redis
 │
 ▼
Deserializer
 │
 ▼
User
```

Pyright does not validate serialized bytes.

Schema validation and compatibility testing remain necessary.

---

## Async Code

Pyright understands asynchronous functions:

```python
async def get_user(user_id: int) -> User:
    ...
```

For callback-based asynchronous APIs:

```python
from collections.abc import Awaitable, Callable


Handler = Callable[[Request], Awaitable[Response]]
```

This is useful for:

- FastAPI
- async database clients
- async message consumers
- asynchronous middleware
- async service clients

---

## Concurrency

Pyright can identify type mismatches in concurrent code:

```python
from concurrent.futures import ThreadPoolExecutor


def fetch_user(user_id: int) -> User:
    ...


with ThreadPoolExecutor(max_workers=8) as executor:
    users = list(
        executor.map(fetch_user, [1, 2, 3])
    )
```

It cannot prove that shared state is race-free.

Concurrency correctness still requires:

- synchronization design
- isolation
- testing
- transaction analysis
- runtime monitoring

---

## Observability

Pyright does not provide runtime observability.

Production systems still need:

- structured logging
- metrics
- tracing
- error tracking
- health checks
- alerting

Typed models can improve the consistency of telemetry structures.

For example:

```python
class RequestContext(TypedDict):
    request_id: str
    route: str
    user_id: str | None
```

This reduces accidental inconsistencies in application metadata.

---

## High Availability

Static checking contributes indirectly to availability by preventing some deployment defects.

A production delivery pipeline might be:

```text
Code
 │
 ├── Pyright
 ├── Unit tests
 ├── Integration tests
 ├── Security checks
 └── Build validation
       │
       ▼
Deployment
       │
       ├── Health checks
       ├── Readiness checks
       ├── Rolling deployment
       └── Rollback
```

Pyright itself does not provide high availability.

---

## Disaster Recovery

Pyright does not protect against:

- data loss
- backup corruption
- infrastructure failure
- region failure
- unsafe migrations

Use:

- automated backups
- restore testing
- multi-AZ architecture
- replication
- infrastructure-as-code
- documented recovery procedures

Static analysis is a development-time control.

---

## Cost Considerations

Pyright introduces development and CI compute costs.

For most applications, these costs are small relative to:

- production debugging
- failed deployments
- engineering rework
- regressions
- maintenance overhead

For large repositories, improve performance using:

- incremental analysis
- explicit project boundaries
- exclusion of irrelevant generated artifacts
- controlled dependency graphs
- efficient CI pipelines

---

## Common Mistakes

### Treating Pyright as Runtime Validation

Annotations do not validate incoming HTTP or Kafka data.

### Overusing `Any`

`Any` removes valuable static guarantees.

### Ignoring Unknown Values

Unknown values should generally be narrowed or validated before entering core business logic.

### Using `cast()` to Silence Errors

A cast changes static assumptions; it does not validate runtime data.

### Annotating Every Local Variable

Unnecessary annotations create noise without increasing meaningful safety.

### Running Pyright Only in the Editor

CI should enforce the repository's type policy.

### Mixing Pyright and Mypy Without a Reason

Running both can produce inconsistent diagnostics and additional maintenance burden.

### Ignoring Third-Party Typing

Dynamic dependencies can introduce weakly typed values throughout the application.

### Overengineering Protocols

Use protocols when they clarify real behavioral boundaries, not merely because structural typing exists.

---

## Production Pitfalls

### Version Drift

Different Pyright versions can produce different diagnostics.

Pin the version used by CI.

### Configuration Drift

If developers and CI use different configurations, local success does not guarantee CI success.

### Python Version Drift

Configure Pyright for the Python version actually supported in production.

### Generated Code

Large generated directories can significantly increase analysis cost.

### Excessive Suppression

Large numbers of casts and ignores indicate type debt.

### False Confidence

A clean Pyright run does not prove that the application is correct.

### Framework Mismatch

Dynamic framework behavior may require adapters or additional typing support.

---

## Suppressions

Static analysis occasionally encounters valid runtime behavior that cannot be represented conveniently.

Suppressions should be:

- rare
- local
- documented
- reviewed

Do not use broad suppressions simply to achieve a clean CI run.

A healthy repository should make it possible to identify where static guarantees have been intentionally bypassed.

---

## Mypy and Pyright Interoperability

A project may use both tools in special circumstances, such as:

- library compatibility testing
- migration from one checker to another
- validating third-party typing
- investigating checker-specific behavior

However, running both as mandatory gates increases maintenance cost.

If both are required:

```text
Source
 │
 ├── Pyright
 │
 └── Mypy
      │
      ▼
Potentially different diagnostics
```

Document which tool is authoritative for which purpose.

---

## Recommended Project Structure

A backend repository can organize typing configuration like:

```text
project/
├── pyproject.toml
├── pyrightconfig.json
├── src/
│   └── application/
│       ├── api/
│       ├── domain/
│       ├── services/
│       ├── repositories/
│       └── infrastructure/
├── tests/
└── ...
```

Avoid maintaining duplicate configuration unless the project has a specific reason to do so.

---

## Recommended Workflow

A production-oriented workflow is:

1. Define the supported Python version.
2. Install and pin Pyright.
3. Create version-controlled configuration.
4. Start with an appropriate checking mode.
5. Type public APIs and architectural boundaries.
6. Reduce `Any` and unknown values.
7. Use generics and protocols where they express real relationships.
8. Keep external data runtime-validated.
9. Run Pyright in the editor for immediate feedback.
10. Run Pyright in CI as an enforcement gate.
11. Track type debt in legacy systems.
12. Increase strictness progressively.

---

## Decision Guide

| Problem | Recommended Approach |
|---|---|
| Obvious local type | Let Pyright infer |
| Public function | Explicit annotation |
| Unknown external value | Validate and narrow |
| Arbitrary Python object | `object` |
| Dictionary structure | `TypedDict` |
| Generic relationship | `TypeVar` / generic syntax |
| Behavioral abstraction | `Protocol` |
| Runtime narrowing predicate | `TypeGuard` / `TypeIs` |
| Multiple call signatures | `@overload` |
| Decorator | `ParamSpec` + `TypeVar` |
| Fluent API | `Self` |
| Domain-specific primitive | `NewType` |
| Constant | `Final` |
| Third-party dynamic API | Typed adapter |
| Legacy application | Incremental typing |
| New service | Prefer strict checking |
| Runtime request validation | Pydantic / explicit validation |
| Distributed schema | OpenAPI / protobuf / event schema |

---

## Interview Traps

### Is Pyright part of Python?

No. Pyright is an external static type checker.

### Does Pyright execute Python code?

No. It statically analyzes Python source.

### Does Pyright make Python statically typed at runtime?

No. Python remains dynamically typed during execution.

### What is Pylance?

Pylance is Microsoft's Python language server for VS Code and uses Pyright's type-analysis technology.

### Is Pyright the same as mypy?

They solve the same broad problem but are separate tools with differences in inference, diagnostics, configuration, and ecosystem integration.

### Why use Pyright?

It provides strong static analysis, fast editor feedback, and integrates closely with modern Python development workflows, particularly through Pylance.

### What is `Any`?

`Any` permits operations without normal static type guarantees.

### What is an unknown type?

It represents a value whose precise type is not sufficiently known to the analyzer. It should generally be narrowed or validated before use.

### Does `cast()` validate data?

No. A cast changes the static assumption only.

### Does `TypedDict` validate JSON?

No. Runtime validation is still required.

### Can Pyright prove thread safety?

No. It can verify types but cannot generally prove synchronization correctness.

### Can Pyright detect database failures?

No.

### Should every variable be annotated?

No. Pyright's inference can handle many local values.

### Why use Protocol?

Protocol provides structural typing and allows code to depend on behavior rather than concrete inheritance.

### Why use ParamSpec?

ParamSpec preserves callable parameter information, particularly for decorators and higher-order functions.

### Why use overloads?

Overloads describe different static call signatures when the resulting type depends on the arguments.

---

## Production Checklist

Before adopting Pyright for a production backend:

- [ ] Define the supported Python version.
- [ ] Pin the Pyright version.
- [ ] Store configuration in version control.
- [ ] Define explicit source directories.
- [ ] Exclude only intentionally irrelevant generated or vendor code.
- [ ] Choose an appropriate type-checking mode.
- [ ] Use strict checking for new code where practical.
- [ ] Type public functions and important interfaces.
- [ ] Type service and repository boundaries.
- [ ] Use protocols for meaningful behavioral abstractions.
- [ ] Use generics where they preserve important type relationships.
- [ ] Use `ParamSpec` for decorators where necessary.
- [ ] Use `Self` for subtype-preserving APIs where appropriate.
- [ ] Minimize `Any`.
- [ ] Treat unknown values carefully.
- [ ] Prefer narrowing over unsafe casts.
- [ ] Keep runtime validation at external boundaries.
- [ ] Keep `TypedDict` separate from runtime schema validation.
- [ ] Isolate poorly typed third-party dependencies.
- [ ] Review suppressions as technical debt.
- [ ] Run Pyright during local development.
- [ ] Run Pyright in CI.
- [ ] Make type errors fail the appropriate CI stage.
- [ ] Keep runtime tests mandatory.
- [ ] Keep integration and contract tests mandatory.
- [ ] Monitor CI analysis time for large repositories.
- [ ] Avoid unnecessary plugins or duplicated type-checking infrastructure.
- [ ] Document any intentional differences if both Pyright and mypy are used.
- [ ] Increase strictness incrementally in legacy applications.
- [ ] Treat static typing as a correctness aid, not a security or runtime-validation boundary.

## Key Takeaways

- **Pyright is a static type checker, not a runtime type-enforcement system**; it analyzes annotations, inferred types, control flow, imports, and contracts without executing application logic.
- **Pyright's strongest production value is at architectural boundaries** such as API handlers, services, protocols, repositories, event handlers, and infrastructure adapters.
- **`Any`, unknown values, unsafe casts, and broad suppressions weaken static guarantees**; mature codebases narrow dynamic values and isolate poorly typed dependencies.
- **Pyright complements runtime validation and testing rather than replacing them**; Pydantic, database constraints, authentication, integration tests, contract tests, and observability remain necessary.
- **A production Pyright strategy requires consistency**: pin versions, centralize configuration, enforce checking in CI, use appropriate strictness, manage type debt, and choose Pyright or mypy deliberately rather than introducing redundant tooling without a clear purpose.