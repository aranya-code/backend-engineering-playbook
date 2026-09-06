# 05- Callable

## Overview

`Callable` describes objects that can be invoked like functions.

In Python's type system, it is used to describe:

- function parameters
- callback functions
- handlers
- factories
- dependency providers
- middleware
- decorators
- strategy objects
- task functions
- plugin entry points

The simplest form is:

```python
from collections.abc import Callable


def execute(operation: Callable[[int], str], value: int) -> str:
    return operation(value)
```

This communicates a function contract:

```text
Callable[
    [argument types],
    return type
]
```

In this example:

```python
Callable[[int], str]
```

means:

```text
accepts an int
      │
      ▼
returns a str
```

`Callable` is more than a way to annotate functions. It is an important tool for expressing dependency inversion and behavior-oriented APIs.

---

## Why `Callable` Matters

Python treats functions as first-class objects.

A function can be:

- assigned to a variable
- passed to another function
- returned from a function
- stored in a collection
- attached to an object
- dynamically selected at runtime

This enables patterns such as:

```python
handlers = {
    "created": handle_created,
    "deleted": handle_deleted,
}
```

Typing that structure precisely is much easier with `Callable`.

Without typing:

```python
handlers: dict[str, object]
```

With typing:

```python
handlers: dict[str, Callable[[Event], None]]
```

The second version communicates the behavior expected from every handler.

---

## Basic Syntax

The modern import is:

```python
from collections.abc import Callable
```

Then:

```python
Callable[[int, str], bool]
```

means:

```text
arguments:
    int
    str

return:
    bool
```

Example:

```python
def validate_user(user_id: int, email: str) -> bool:
    ...


validator: Callable[[int, str], bool] = validate_user
```

The callable contract is explicit.

---

## Callable with No Arguments

A callable accepting no arguments can be expressed as:

```python
Callable[[], str]
```

Example:

```python
from collections.abc import Callable


def get_environment() -> str:
    return "production"


provider: Callable[[], str] = get_environment
```

This pattern is common for:

- configuration providers
- lazy initialization
- factories
- dependency injection
- test hooks

---

## Callable Returning `None`

A callback that performs an action without returning a meaningful result:

```python
Callable[[Event], None]
```

Example:

```python
from collections.abc import Callable


def publish_event(
    event: Event,
    callback: Callable[[Event], None],
) -> None:
    callback(event)
```

The callback's return value is intentionally ignored.

Be careful not to interpret `None` as "the callable does not return." It returns normally and its return value is `None`.

---

## Callable with Multiple Parameters

```python
Callable[[int, str, bool], User]
```

represents:

```text
int
str
bool
 │
 ▼
User
```

Example:

```python
def create_user(
    user_id: int,
    email: str,
    active: bool,
) -> User:
    ...


factory: Callable[[int, str, bool], User] = create_user
```

This is useful for explicit callback contracts.

---

## Callable with Variadic Arguments

A callable accepting arbitrary positional arguments can be described using:

```python
Callable[..., ReturnType]
```

Example:

```python
Callable[..., str]
```

means the callable returns `str`, while the parameter signature is not specified.

This is intentionally less precise.

Use it when the exact parameter signature genuinely cannot be expressed or is irrelevant.

Avoid using:

```python
Callable[..., Any]
```

as a general-purpose function type. It provides very little static safety.

---

## `Callable[..., T]` vs Precise Callable

Compare:

```python
Callable[[int], User]
```

with:

```python
Callable[..., User]
```

The first communicates:

```text
must accept exactly the intended argument shape
```

The second communicates:

```text
some callable that returns User
```

The precise form is preferable whenever the signature matters.

---

## Callable as a Parameter

A common use is dependency injection.

```python
from collections.abc import Callable


def load_user(
    user_id: int,
    repository: Callable[[int], User | None],
) -> User | None:
    return repository(user_id)
```

The function does not care whether `repository` is:

- a normal function
- a bound method
- a lambda
- a callable object

It only requires the specified callable behavior.

---

## Callable and Dependency Injection

This pattern supports dependency inversion.

```text
Service
   │
   ▼
Callable dependency
   │
   ├── PostgreSQL implementation
   ├── Redis implementation
   └── Test implementation
```

For example:

```python
from collections.abc import Callable


def build_service(
    user_loader: Callable[[int], User | None],
) -> UserService:
    return UserService(user_loader)
```

Tests can provide:

```python
lambda user_id: User(id=user_id)
```

without modifying the service.

For more complex dependencies, a `Protocol` may provide a clearer interface than `Callable`.

---

## Callable vs Protocol

Suppose the dependency is simply:

```python
user_loader(user_id)
```

`Callable` is appropriate.

If the dependency has multiple operations:

```python
repository.get(...)
repository.save(...)
repository.delete(...)
```

a protocol is usually clearer:

```python
from typing import Protocol


class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None:
        ...

    def save(self, user: User) -> None:
        ...
```

Use:

| Requirement | Preferred abstraction |
|---|---|
| One function-like operation | `Callable` |
| Multiple related operations | `Protocol` |
| Shared state + behavior | Class / protocol |
| Multiple domain variants | Union / protocol depending on semantics |

---

## Callable Objects

Python objects can implement `__call__()`.

```python
class UserLoader:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def __call__(self, user_id: int) -> User | None:
        return self.repository.get(user_id)
```

The instance is callable:

```python
loader = UserLoader(repository)

user = loader(1001)
```

It satisfies:

```python
Callable[[int], User | None]
```

This is useful when a callable needs state or configuration.

---

## Functions vs Callable Objects

| Characteristic | Function | Callable object |
|---|---|---|
| Simple behavior | Excellent | Usually unnecessary |
| Stateful behavior | Closure or object | Excellent |
| Configuration | Closure / partial | Excellent |
| Multiple methods | Limited | Excellent |
| Dependency injection | Good | Good |
| Testing | Good | Good |
| Complex lifecycle | Limited | Better |

Do not use a callable class simply to make a function look object-oriented.

Use one when state, configuration, or lifecycle matters.

---

## Lambdas

Lambdas are callable objects and can satisfy callable annotations.

```python
from collections.abc import Callable


transform: Callable[[int], int] = lambda value: value * 2
```

For production application logic, named functions are generally preferable when the behavior is non-trivial.

Avoid large lambdas that obscure business logic.

---

## Bound Methods

Methods can also satisfy callable contracts.

```python
class UserService:
    def get_user(self, user_id: int) -> User | None:
        ...


service = UserService()

loader: Callable[[int], User | None] = service.get_user
```

The bound method already contains its instance.

Therefore, the callable's exposed signature is:

```python
(int) -> User | None
```

not:

```python
(UserService, int) -> User | None
```

---

## Static Methods and Class Methods

A static method can be assigned to a callable:

```python
class Parser:
    @staticmethod
    def parse(value: str) -> int:
        return int(value)


parser: Callable[[str], int] = Parser.parse
```

A class method can also be callable:

```python
class User:
    @classmethod
    def from_id(cls, user_id: int) -> "User":
        ...
```

The bound class method exposes:

```python
Callable[[int], User]
```

to its caller.

---

## Partial Functions

`functools.partial` creates a callable with some arguments pre-bound.

```python
from functools import partial


def connect(host: str, port: int, timeout: float) -> Connection:
    ...


connect_to_database = partial(
    connect,
    host="postgres",
    port=5432,
)
```

The resulting callable can be used as a configured function.

Type inference around partial applications depends on the Python version and static type checker, so verify the inferred signature in the project's tooling.

---

## Callable and Decorators

Decorators are one of the most important advanced uses of `Callable`.

A decorator accepts a callable and returns another callable.

A basic form is:

```python
from collections.abc import Callable
from typing import Any


def log_calls(func: Callable[..., Any]) -> Callable[..., Any]:
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(func.__name__)
        return func(*args, **kwargs)

    return wrapper
```

This works but loses the original function's precise signature.

For production decorators, `ParamSpec` is usually the better solution.

---

## Callable with `ParamSpec`

`ParamSpec` preserves the parameter specification of another callable.

```python
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def log_calls(
    func: Callable[P, R],
) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper
```

This preserves:

```text
input signature → output type
```

instead of reducing everything to:

```python
Callable[..., Any]
```

This is an important distinction for production-quality decorators.

---

## Why `ParamSpec` Matters

Suppose:

```python
@log_calls
def create_order(
    customer_id: int,
    amount: Decimal,
) -> Order:
    ...
```

With a precise `ParamSpec` decorator, static tooling can preserve the effective signature:

```python
(int, Decimal) -> Order
```

A weak decorator type can instead cause the function to appear as:

```python
Callable[..., Any]
```

and degrade IDE support and static checking.

---

## Callable and `TypeVar`

A callable's return type can be represented generically.

```python
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def execute(factory: Callable[[], T]) -> T:
    return factory()
```

Then:

```python
user = execute(create_user)
```

can preserve the specific return type.

Conceptually:

```text
Callable[[], User]
        │
        ▼
execute()
        │
        ▼
User
```

---

## Callable and Higher-Order Functions

A higher-order function accepts or returns another callable.

Example:

```python
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")
R = TypeVar("R")


def transform(
    values: list[T],
    mapper: Callable[[T], R],
) -> list[R]:
    return [mapper(value) for value in values]
```

This expresses a generic relationship:

```text
T --mapper--> R
```

Example:

```python
names = transform(
    users,
    lambda user: user.name,
)
```

The return type becomes:

```python
list[str]
```

---

## Callable and Strategy Pattern

A callable can represent a strategy without requiring a class hierarchy.

```python
from collections.abc import Callable
from decimal import Decimal


PricingStrategy = Callable[[Order], Decimal]


def standard_pricing(order: Order) -> Decimal:
    ...


def premium_pricing(order: Order) -> Decimal:
    ...


def calculate_total(
    order: Order,
    strategy: PricingStrategy,
) -> Decimal:
    return strategy(order)
```

This can be simpler than defining separate strategy classes when behavior is stateless.

---

## Callable and Event Handlers

Event-driven applications frequently use callable handlers.

```python
from collections.abc import Callable


EventHandler = Callable[[OrderCreated], None]


handlers: list[EventHandler] = [
    send_confirmation_email,
    update_search_index,
    publish_metrics,
]
```

Processing:

```python
def dispatch(
    event: OrderCreated,
    handlers: list[EventHandler],
) -> None:
    for handler in handlers:
        handler(event)
```

In production, handler failures, retries, ordering, idempotency, and observability must still be designed explicitly.

The type annotation only describes the handler contract.

---

## Callable and Kafka Consumers

A consumer can dispatch events through typed handlers:

```python
from collections.abc import Callable


EventHandler = Callable[[DomainEvent], None]


def dispatch_event(
    event: DomainEvent,
    handler: EventHandler,
) -> None:
    handler(event)
```

The Kafka layer is responsible for:

```text
bytes
  │
  ▼
deserialization
  │
  ▼
validation
  │
  ▼
DomainEvent
  │
  ▼
Callable handler
```

`Callable` should normally operate after the event has been validated.

---

## Callable and Celery

Task functions are naturally callable:

```python
def process_order(order_id: int) -> None:
    ...
```

A higher-level dispatcher can type task functions:

```python
from collections.abc import Callable


OrderTask = Callable[[int], None]
```

However, Celery adds serialization and distributed execution semantics.

A callable annotation does not guarantee:

- serializability
- retry behavior
- idempotency
- worker availability
- delivery guarantees

Those are operational properties of the task system.

---

## Callable and FastAPI Dependencies

FastAPI dependency injection often uses callable objects or functions.

A dependency can be:

```python
def get_current_user() -> User:
    ...
```

or a configured callable object:

```python
class UserProvider:
    def __call__(self) -> User:
        ...


provider = UserProvider()
```

This illustrates an important Python design principle:

```text
Dependency
    ↓
required behavior
    ↓
Callable
```

Framework-specific dependency mechanisms may add metadata and lifecycle semantics beyond ordinary Python callability.

---

## Callable and Middleware

Middleware often behaves like a callable pipeline:

```text
Request
   │
   ▼
Middleware A
   │
   ▼
Middleware B
   │
   ▼
Application
   │
   ▼
Response
```

A middleware may accept another callable representing the next stage.

The exact signature depends on the framework.

Do not replace a framework-specific callable signature with `Callable[..., Any]` when the framework already provides a precise protocol or type.

---

## Callable and REST Client Abstractions

A service may inject an HTTP operation:

```python
from collections.abc import Callable


HttpGet = Callable[[str], Response]


def fetch_user(
    user_id: int,
    get: HttpGet,
) -> User:
    response = get(f"/users/{user_id}")
    return parse_user(response)
```

This can simplify unit testing.

A production implementation may use:

- `httpx`
- a generated client
- an internal HTTP abstraction

while tests provide a controlled callable.

---

## Callable and Database Transactions

Transaction wrappers are another common callable use.

```python
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def transaction(
    operation: Callable[[], T],
) -> T:
    begin_transaction()

    try:
        result = operation()
        commit_transaction()
        return result
    except Exception:
        rollback_transaction()
        raise
```

In a real Django or SQLAlchemy application, use the framework's transaction facilities rather than implementing transaction management manually.

The example illustrates the type relationship.

---

## Callable and Retry Logic

A retry helper can accept a callable:

```python
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def retry(
    operation: Callable[[], T],
    attempts: int,
) -> T:
    ...
```

This is useful for infrastructure operations such as:

- HTTP requests
- transient database operations
- AWS API calls
- queue operations

The callable abstraction does not automatically make an operation retry-safe.

Before retrying, evaluate:

- idempotency
- side effects
- timeout behavior
- exception classification
- backoff
- jitter

---

## Callable and Async Functions

Async functions require special attention.

An async function:

```python
async def fetch_user(user_id: int) -> User:
    ...
```

is called like a callable, but calling it produces a coroutine object.

The effective relationship is conceptually:

```text
fetch_user
    │
    ▼
Callable[[int], Coroutine[..., User]]
```

or, depending on the desired abstraction:

```python
Callable[[int], Awaitable[User]]
```

For general async dependencies, `Awaitable[T]` is often more useful than exposing a concrete coroutine implementation.

---

## `Callable` vs `Awaitable`

Synchronous:

```python
Callable[[int], User]
```

Asynchronous:

```python
Callable[[int], Awaitable[User]]
```

Example:

```python
from collections.abc import Awaitable, Callable


UserLoader = Callable[[int], Awaitable[User]]
```

Then:

```python
async def load(
    user_id: int,
    loader: UserLoader,
) -> User:
    return await loader(user_id)
```

This is useful for async services and FastAPI applications.

---

## Sync and Async Are Different Contracts

Do not treat:

```python
Callable[[int], User]
```

and:

```python
Callable[[int], Awaitable[User]]
```

as interchangeable.

A synchronous function returns a `User`.

An asynchronous function returns an awaitable that eventually produces a `User`.

This distinction matters for:

- event loops
- concurrency
- dependency injection
- middleware
- test doubles
- API clients

---

## Callable and `Coroutine`

You can type a concrete coroutine result:

```python
from collections.abc import Callable, Coroutine


AsyncLoader = Callable[
    [int],
    Coroutine[object, object, User],
]
```

However, when the caller only needs something awaitable, this is usually clearer:

```python
from collections.abc import Awaitable


AsyncLoader = Callable[[int], Awaitable[User]]
```

Use the narrowest useful abstraction.

---

## Callable and Variance

Callable types have special variance rules.

Conceptually:

```python
Callable[[Animal], None]
```

can accept a function capable of handling any `Animal`, while a function accepting only `Dog` cannot safely replace it.

For return values, covariance generally applies:

```text
Callable[..., Dog]
       │
       ▼
Callable[..., Animal]
```

can be safe because a `Dog` is an `Animal`.

For arguments, contravariance applies because the consumer must be capable of accepting every value promised by the callable contract.

Understanding this is important when designing generic callback APIs.

---

## Callable Argument Variance Example

Suppose:

```python
class Animal:
    ...


class Dog(Animal):
    ...


def handle_animal(animal: Animal) -> None:
    ...
```

A callback requiring:

```python
Callable[[Animal], None]
```

can use:

```python
handle_animal
```

because it can handle any animal, including dogs.

A callback that only accepts:

```python
Dog
```

cannot safely be substituted where arbitrary `Animal` objects may be passed.

This is one of the more advanced `Callable` interview topics.

---

## Callable and `Protocol`

A callable protocol can model a callable with additional structure.

```python
from typing import Protocol


class Validator(Protocol):
    def __call__(self, value: str) -> bool:
        ...
```

Now both functions and callable objects can satisfy the protocol.

This becomes useful when the callable itself has additional attributes or behavior that `Callable` alone cannot describe.

---

## Callable Protocol with State

For example:

```python
class ConfigurableValidator(Protocol):
    strict: bool

    def __call__(self, value: str) -> bool:
        ...
```

A plain:

```python
Callable[[str], bool]
```

cannot express the `strict` attribute.

Use a protocol when both invocation and additional interface structure matter.

---

## Callable and Decorator Metadata

Decorators can alter callable behavior.

Use:

```python
from functools import wraps
```

to preserve important runtime metadata:

```python
def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
```

`wraps` helps preserve attributes such as:

- `__name__`
- `__qualname__`
- `__doc__`
- `__wrapped__`

For production decorators, combine `wraps` with `ParamSpec` and `TypeVar` when appropriate.

---

## Callable and Testing

Callables make dependencies easy to substitute.

Production:

```python
service = UserService(repository.get)
```

Test:

```python
def fake_get(user_id: int) -> User | None:
    return User(id=user_id)
```

Then:

```python
service = UserService(fake_get)
```

This can be simpler than creating a full mock object for a single behavior.

For complex dependencies, use protocols and explicit fakes where that improves readability.

---

## Mocking Callables

`unittest.mock.Mock` and `MagicMock` are dynamically typed at runtime.

A mock can be configured:

```python
from unittest.mock import Mock


loader = Mock(spec=UserLoader)
loader.return_value = User(id=1001)
```

Static typing around mocks may require careful annotations or casts depending on the test framework and type checker.

Do not allow test-only `Any` patterns to dictate production interfaces.

---

## Security Considerations

A callable is executable behavior.

If an application accepts arbitrary callables from untrusted input, it has effectively accepted arbitrary code execution.

Never deserialize or dynamically load untrusted callable objects without a strong trust boundary.

Dangerous patterns include:

```python
# Do not treat untrusted input as a Python callable.
callback = untrusted_value
callback()
```

or dynamically importing arbitrary user-controlled module paths.

Production plugin systems should use:

- explicit allowlists
- trusted package boundaries
- controlled entry points
- authorization
- process isolation where appropriate

---

## Serialization Considerations

Function objects are not generally suitable as portable application data.

Avoid designing distributed messages around:

```python
Callable
```

For example, Kafka and Redis should carry data such as:

```text
event type
payload
version
metadata
```

rather than Python function objects.

Workers can then map event types to trusted handlers:

```python
handlers: dict[str, Callable[[Event], None]]
```

The callable registry stays local to the trusted process.

---

## Performance Considerations

Calling through a callable abstraction adds little conceptual overhead compared with ordinary Python function calls, but Python function calls themselves are not free.

Avoid creating deep callback chains in extremely hot paths without measuring them.

For backend systems, larger performance costs usually come from:

- database I/O
- network calls
- serialization
- synchronization
- excessive allocations

Do not optimize away a clear callable abstraction without profiling evidence.

---

## Scalability Considerations

Callable-based dependency injection works well within a process.

For distributed systems, the callable itself does not cross service boundaries.

Instead:

```text
Service A
   │
   │ serialized command/event
   ▼
Kafka / HTTP / gRPC
   │
   ▼
Service B
   │
   ▼
local callable handler
```

This distinction prevents confusing local Python behavior with distributed system contracts.

---

## Observability

Callable wrappers are often used for instrumentation:

```python
from collections.abc import Callable
from typing import ParamSpec, TypeVar


P = ParamSpec("P")
R = TypeVar("R")


def instrument(
    operation: Callable[P, R],
) -> Callable[P, R]:
    ...
```

The wrapper can record:

- latency
- invocation count
- errors
- trace context
- business metrics

Be careful not to log arbitrary callable arguments because they may contain:

- passwords
- tokens
- personal data
- payment information
- secrets

Instrumentation must respect data-minimization requirements.

---

## Reliability Considerations

When a callable represents an infrastructure operation, reliability belongs to the execution strategy.

For example:

```python
Callable[[], Response]
```

does not specify:

- timeout
- retry policy
- circuit breaker
- idempotency
- cancellation
- fallback behavior

Those properties should be expressed through the surrounding abstraction when they materially affect correctness.

For complex infrastructure dependencies, a protocol or dedicated service class may communicate these semantics better than a bare callable.

---

## Common Mistakes

### Using `Callable[..., Any]` Everywhere

This discards parameter and return information.

Prefer:

```python
Callable[[Order], Payment]
```

when the contract is known.

### Confusing Callable with Return Type

This:

```python
Callable[[int], User]
```

means "a function accepting `int` and returning `User."

It does not mean the value itself is a `User`.

### Forgetting Async Semantics

An async callable returns an awaitable.

Use:

```python
Callable[[int], Awaitable[User]]
```

when appropriate.

### Using Callable for Complex Interfaces

If a dependency has several operations, use a protocol or class.

### Using `cast()` to Hide an Incorrect Callable Signature

A cast does not fix runtime incompatibility.

### Assuming Callable Means Serializable

A Python function is not automatically suitable for Kafka, Redis, Celery, or persistent storage.

### Passing Untrusted Callables

A callable represents executable behavior and should never originate from untrusted data without a strong security model.

### Losing Decorator Signatures

Using:

```python
Callable[..., Any]
```

in decorators often destroys useful type information.

Use `ParamSpec` and `TypeVar` for signature-preserving decorators.

### Overusing Callable-Based Dependency Injection

If the dependency has meaningful domain behavior, a named protocol often provides a clearer architectural boundary.

---

## Production Design Pattern

A useful service design is:

```text
                 ┌──────────────────────┐
                 │     Application      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │   Typed dependency   │
                 │      Callable        │
                 └──────────┬───────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         PostgreSQL       Redis       HTTP client
```

The application depends on behavior rather than a concrete implementation.

When the dependency becomes more complex:

```text
Callable
   │
   │ complexity grows
   ▼
Protocol
   │
   ▼
Concrete implementation
```

This gives the codebase a natural progression from simple function injection to explicit interfaces.

---

## Example: Typed Repository Function

A simple service can accept a repository function:

```python
from collections.abc import Callable


UserLoader = Callable[[int], User | None]


class UserService:
    def __init__(self, load_user: UserLoader) -> None:
        self.load_user = load_user

    def get_user(self, user_id: int) -> User:
        user = self.load_user(user_id)

        if user is None:
            raise UserNotFound(user_id)

        return user
```

Production:

```python
service = UserService(repository.get_by_id)
```

Test:

```python
def fake_loader(user_id: int) -> User | None:
    return User(id=user_id)


service = UserService(fake_loader)
```

This is simple, explicit dependency injection without requiring a framework.

---

## Example: Generic Callable Pipeline

A reusable transformation pipeline can preserve types:

```python
from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")
R = TypeVar("R")


def apply(
    value: T,
    operation: Callable[[T], R],
) -> R:
    return operation(value)
```

Usage:

```python
user_name: str = apply(
    user,
    lambda current_user: current_user.name,
)
```

The callable defines the transformation:

```text
T
 │
 ▼
Callable[[T], R]
 │
 ▼
R
```

This pattern underlies many functional programming utilities.

---

## Example: Async Dependency

```python
from collections.abc import Awaitable, Callable


AsyncUserLoader = Callable[[int], Awaitable[User | None]]


async def require_user(
    user_id: int,
    load_user: AsyncUserLoader,
) -> User:
    user = await load_user(user_id)

    if user is None:
        raise UserNotFound(user_id)

    return user
```

This is suitable for an async service architecture where the repository or HTTP client performs asynchronous I/O.

---

## Choosing Between Callable, Protocol, and Class

| Design | Best when | Main advantage | Limitation |
|---|---|---|---|
| `Callable` | One operation | Minimal and direct | Limited interface description |
| Callable object | One operation + state | Stateful behavior | More ceremony |
| `Protocol` | Several operations or structural contract | Explicit interface | More code |
| Abstract class | Shared implementation/state | Reuse + contract | Stronger coupling |
| Concrete class | Complex domain behavior | Full encapsulation | More rigid dependency |

Start with the simplest abstraction that accurately represents the dependency.

---

## Interview Traps

### What does `Callable[[int], str]` mean?

A callable that accepts an integer argument and returns a string.

### Is every function a `Callable`?

Functions are callable objects, but `Callable` can also describe callable instances, bound methods, lambdas, and other objects implementing `__call__()`.

### What does `Callable[..., T]` mean?

A callable with an unspecified parameter signature that returns `T`.

### Why is `Callable[..., Any]` usually weak?

It removes useful information about both parameters and return values.

### What is the difference between `Callable[[int], User]` and `Callable[[int], Awaitable[User]]`?

The first returns a `User` synchronously. The second returns an awaitable that must be awaited to obtain a `User`.

### When should `Callable` be replaced with `Protocol`?

When the dependency has multiple related operations, requires additional attributes, or needs a richer structural interface.

### What is `ParamSpec` used for?

It preserves the parameter specification of another callable, especially in decorators and higher-order functions.

### Why use `TypeVar` with `Callable`?

It allows generic functions to preserve relationships between input and output types.

### Are callable objects serializable?

Not automatically. Python callability and serialization are separate concerns.

### Does `Callable` enforce runtime signatures?

No. It provides static type information. Python's runtime does not automatically enforce the annotation.

---

## Production Checklist

Before introducing `Callable`, verify:

- The callable's parameter types are explicit where practical.
- The return type is explicit.
- `Callable[..., Any]` is avoided unless the signature is genuinely dynamic.
- `collections.abc.Callable` is preferred for modern Python code.
- Async callables use `Awaitable[T]` or an appropriate coroutine type.
- `ParamSpec` is used for signature-preserving decorators.
- `TypeVar` is used when input/output relationships should be preserved.
- A `Protocol` is considered when the dependency has multiple operations.
- Callable objects are used when state or configuration belongs with the behavior.
- Callable dependencies are validated through normal application contracts.
- Untrusted input is never treated as executable callable behavior.
- Callable objects are not assumed to be serializable.
- Kafka, Redis, HTTP, and other distributed boundaries exchange data rather than Python callable objects.
- Retryable callables are evaluated for idempotency and side effects.
- Timeouts and cancellation are handled outside the type annotation where required.
- Instrumentation does not expose secrets or sensitive callable arguments.
- Callback failures are handled according to the application's reliability model.
- Dependency injection remains simple enough to understand and test.
- Static analysis verifies callable compatibility in CI/CD.
- Runtime tests cover important callback, decorator, and async execution paths.

## Key Takeaways

- `Callable[[Args...], ReturnType]` describes function-like behavior and is useful for callbacks, factories, handlers, dependency injection, and strategy functions.
- Prefer precise callable signatures over `Callable[..., Any]`; use `ParamSpec` and `TypeVar` when decorators or higher-order functions need to preserve type relationships.
- Use `Awaitable[T]` for asynchronous callable contracts when the caller needs an awaitable result rather than a synchronous `T`.
- Use `Protocol` instead of `Callable` when a dependency has multiple operations, additional attributes, or a richer structural contract.
- `Callable` describes static behavior, not serialization, security, retryability, idempotency, or runtime validation; those production properties must be designed separately.