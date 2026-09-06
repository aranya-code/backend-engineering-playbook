# 01- First Class Functions

## Overview

Python treats functions as **first-class objects**. A function can be assigned to a variable, stored in a collection, passed as an argument, returned from another function, and attached to objects just like other values.

This capability is fundamental to several advanced Python features:

- Higher-order functions
- Closures
- Decorators
- Callbacks
- Functional programming
- Strategy patterns
- Dependency injection
- Middleware
- Event handlers
- Framework extension points

In backend engineering, first-class functions are particularly useful for composing behavior without creating unnecessary classes or inheritance hierarchies.

```python
def normalize_email(email: str) -> str:
    return email.strip().lower()


processor = normalize_email

result = processor("  User@Example.COM  ")
```

Here, `processor` references the same function object as `normalize_email`.

The important distinction is:

```text
Function definition
        |
        v
Function object
        |
        +--> assign to variable
        +--> pass as argument
        +--> return from function
        +--> store in collection
        +--> attach to object
```

## What First-Class Functions Mean

A language treats functions as first-class values when functions can participate in ordinary value-oriented operations.

In Python, functions can:

| Operation | Supported |
|---|---|
| Assign to a variable | Yes |
| Pass as an argument | Yes |
| Return from another function | Yes |
| Store in a list/dict/set | Yes |
| Store as object attributes | Yes |
| Create dynamically | Yes |
| Have attributes | Yes |
| Be inspected at runtime | Yes |

This does not mean functions are special syntax only. A Python function is an object with identity, type, metadata, and behavior.

```python
def process_order(order_id: int) -> str:
    return f"processed:{order_id}"


print(type(process_order))
print(process_order.__name__)
print(process_order.__doc__)
```

The function itself can be inspected and manipulated at runtime.

## Function Objects

When Python executes:

```python
def calculate_total(amount: int, tax: int) -> int:
    return amount + tax
```

Python creates a function object and binds the name `calculate_total` to it.

Conceptually:

```text
Name                         Object

calculate_total  ----------> function object
                               |
                               +--> code
                               +--> globals
                               +--> defaults
                               +--> annotations
                               +--> metadata
```

The variable name is not the function itself.

This distinction matters because multiple names can reference the same function:

```python
def calculate_total(amount: int, tax: int) -> int:
    return amount + tax


calculate = calculate_total
```

Now:

```python
calculate is calculate_total
```

evaluates to `True`.

Both names reference the same function object.

## Assigning Functions to Variables

A function can be assigned to another variable:

```python
def send_email(address: str) -> None:
    print(f"Sending email to {address}")


send = send_email

send("user@example.com")
```

No new function is created by the assignment.

```text
send_email ─────┐
                ├──> function object
send ───────────┘
```

This is useful when selecting behavior dynamically.

```python
def create_user():
    ...


def create_admin():
    ...


handler = create_admin
handler()
```

The selection of behavior can now be separated from the execution of that behavior.

## Passing Functions as Arguments

Functions can be passed to other functions.

```python
from collections.abc import Callable


def execute(
    operation: Callable[[int], int],
    value: int,
) -> int:
    return operation(value)


def double(value: int) -> int:
    return value * 2


result = execute(double, 10)
```

This is the foundation of higher-order functions.

The receiving function does not need to know the implementation of `operation`.

```text
execute()
   |
   v
Callable
   |
   +--> double()
   +--> validate()
   +--> transform()
   +--> calculate()
```

This is particularly useful when behavior varies while the execution framework remains stable.

## Returning Functions

A function can return another function.

```python
from collections.abc import Callable


def make_multiplier(factor: int) -> Callable[[int], int]:
    def multiply(value: int) -> int:
        return value * factor

    return multiply


double = make_multiplier(2)

print(double(10))
```

The returned function retains access to `factor`.

This leads directly to closures, which are covered in a later document.

## Storing Functions in Collections

Functions can be stored in dictionaries to implement behavior dispatch.

```python
from collections.abc import Callable


def create_user() -> str:
    return "create"


def delete_user() -> str:
    return "delete"


handlers: dict[str, Callable[[], str]] = {
    "create": create_user,
    "delete": delete_user,
}


action = "create"
result = handlers[action]()
```

This is often cleaner than a large conditional chain.

```text
Request
   |
   v
action = "create"
   |
   v
handlers["create"]
   |
   v
create_user()
```

This pattern is useful for:

- Command dispatch
- Event handlers
- CLI commands
- Message consumers
- Protocol handlers
- Strategy selection

## Functions as Attributes

Functions can also be assigned to object attributes.

```python
class Processor:
    pass


processor = Processor()
processor.handle = lambda value: value.upper()

print(processor.handle("hello"))
```

However, dynamically attaching behavior to instances should be used carefully.

A function assigned directly to an instance is not automatically transformed into a bound method in the same way as a function stored on a class.

For production code, explicit class methods, callable objects, or dependency injection are often clearer.

## Functions Have Attributes

Function objects can have custom attributes.

```python
def process() -> None:
    ...


process.requires_authentication = True
```

This capability can be useful for metadata-driven systems, although decorators and explicit metadata structures are usually preferable for maintainability.

Frameworks commonly attach metadata to callables.

For example, routing systems can associate a function with:

```text
HTTP method
URL path
authentication requirements
response metadata
dependency information
```

## Higher-Order Functions

A higher-order function is a function that either:

- Accepts a function as an argument.
- Returns a function.
- Both.

Examples include:

```python
sorted(...)
map(...)
filter(...)
```

For example:

```python
users = [
    {"name": "Alice", "age": 32},
    {"name": "Bob", "age": 25},
]


users_sorted = sorted(
    users,
    key=lambda user: user["age"],
)
```

`sorted()` accepts a callable that determines how elements should be ordered.

The caller supplies the behavior without modifying `sorted()`.

## Callable Type Hints

Modern Python code should use `collections.abc.Callable` for callable type annotations.

```python
from collections.abc import Callable


def apply(
    operation: Callable[[int], int],
    value: int,
) -> int:
    return operation(value)
```

The signature:

```text
Callable[[int], int]
```

means:

```text
input:  int
output: int
```

For multiple parameters:

```python
Callable[[str, int], bool]
```

means:

```text
(str, int) -> bool
```

For a callable that accepts arbitrary arguments and returns nothing:

```python
Callable[..., None]
```

Use precise callable types whenever practical.

## Function Signatures and Contracts

A first-class function is still governed by its callable contract.

For example:

```python
from collections.abc import Callable


def execute(
    callback: Callable[[str], bool],
    value: str,
) -> bool:
    return callback(value)
```

The callback is expected to accept a string and return a boolean.

This provides an explicit contract even though Python does not enforce it at runtime.

Static type checkers such as mypy and Pyright can validate these relationships.

## Callbacks

A callback is a function supplied to another component to be invoked later.

Example:

```python
from collections.abc import Callable


def process_items(
    items: list[str],
    on_processed: Callable[[str], None],
) -> None:
    for item in items:
        on_processed(item)
```

Usage:

```python
def log_processed(item: str) -> None:
    print(f"Processed {item}")


process_items(
    ["a", "b", "c"],
    log_processed,
)
```

Callbacks are useful for:

- Event handling
- Background processing
- Retry hooks
- Metrics hooks
- Validation
- Lifecycle callbacks

They should have clear ownership and failure semantics.

## Backend Event Handling

A message consumer can dispatch events using functions:

```python
from collections.abc import Callable, Awaitable


EventHandler = Callable[[dict[str, object]], Awaitable[None]]

handlers: dict[str, EventHandler] = {}


async def handle_order_created(event: dict[str, object]) -> None:
    ...


handlers["order.created"] = handle_order_created
```

The consumer can then resolve the appropriate handler.

```text
Kafka
  |
  v
Consumer
  |
  v
Event Type
  |
  v
Handler Registry
  |
  v
Async Function
  |
  v
Business Logic
```

This allows the message transport mechanism to remain independent of individual event implementations.

## FastAPI and Function-Based Handlers

FastAPI makes extensive use of functions as application-level handlers.

Conceptually:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

The framework stores and invokes the handler according to its routing and dependency mechanisms.

The route function is therefore not merely a block of code. It is a callable registered with the framework.

## Middleware and Callables

Middleware commonly relies on callable composition.

Conceptually:

```text
Request
   |
   v
Middleware A
   |
   v
Middleware B
   |
   v
Handler
   |
   v
Response
```

Each layer can receive a callable representing the next stage.

This is a direct application of first-class functions.

## Strategy Pattern with Functions

Traditional object-oriented Strategy implementations may use classes:

```python
class PricingStrategy:
    def calculate(self, amount: int) -> int:
        ...
```

For simple stateless strategies, functions may be enough:

```python
from collections.abc import Callable


PricingStrategy = Callable[[int], int]


def standard_price(amount: int) -> int:
    return amount


def discounted_price(amount: int) -> int:
    return amount * 90 // 100
```

Then:

```python
def calculate_price(
    amount: int,
    strategy: PricingStrategy,
) -> int:
    return strategy(amount)
```

This avoids creating classes when the behavior has no meaningful state.

## Functions vs Callable Objects

Functions are not always the best abstraction.

A callable object is useful when behavior requires state:

```python
class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.count = 0

    def __call__(self) -> bool:
        if self.count >= self.limit:
            return False

        self.count += 1
        return True
```

Now:

```python
limiter = RateLimiter(limit=100)

if limiter():
    ...
```

The choice can be summarized as:

| Requirement | Prefer |
|---|---|
| Stateless behavior | Function |
| Stateful behavior | Callable object |
| Complex domain behavior | Class |
| Simple transformation | Function |
| Reusable metadata/decorator behavior | Function + decorator |
| Dependency boundary | Function or Protocol |
| Lifecycle management | Class/context manager |

## Function References vs Function Calls

One of the most common mistakes is confusing:

```python
handler
```

with:

```python
handler()
```

The first references the function.

The second invokes it.

For example:

```python
handlers = {
    "create": create_user,
}
```

is correct.

This is incorrect:

```python
handlers = {
    "create": create_user(),
}
```

The latter executes `create_user()` immediately and stores its result.

This distinction is critical when registering callbacks, routes, tasks, and handlers.

## Default Arguments and Function Objects

Default argument values belong to the function object.

```python
def connect(
    host: str,
    timeout: float = 5.0,
) -> None:
    ...
```

Conceptually, Python stores the default value with the function.

It can be inspected through:

```python
connect.__defaults__
```

For mutable defaults, the object can persist across calls:

```python
def append_item(
    item: str,
    items: list[str] = [],
) -> list[str]:
    items.append(item)
    return items
```

This is usually a bug.

Prefer:

```python
def append_item(
    item: str,
    items: list[str] | None = None,
) -> list[str]:
    if items is None:
        items = []

    items.append(item)
    return items
```

## Function Metadata

Function objects expose useful metadata:

```python
def calculate_total(amount: int) -> int:
    """Calculate the order total."""
    return amount


print(calculate_total.__name__)
print(calculate_total.__doc__)
print(calculate_total.__annotations__)
```

Important attributes include:

| Attribute | Purpose |
|---|---|
| `__name__` | Function name |
| `__qualname__` | Qualified name |
| `__doc__` | Documentation string |
| `__annotations__` | Type annotations |
| `__defaults__` | Positional default values |
| `__kwdefaults__` | Keyword-only defaults |
| `__module__` | Defining module |
| `__dict__` | Custom function attributes |

These attributes are frequently used by Python frameworks and introspection tools.

## Closures and Function State

Functions defined inside other functions can retain references to variables from their enclosing scope.

```python
from collections.abc import Callable


def make_prefixer(prefix: str) -> Callable[[str], str]:
    def prefix(value: str) -> str:
        return f"{prefix}{value}"

    return prefix
```

The returned function retains access to `prefix`.

This is a closure.

Closures become particularly important for:

- Decorators
- Factories
- Configuration binding
- Callbacks
- Lightweight state

Closures are covered in depth in the dedicated closures document.

## Late Binding in Closures

Loop variables can cause surprising closure behavior.

```python
handlers = []

for name in ["a", "b", "c"]:
    handlers.append(lambda: name)
```

All functions may resolve `name` to its final value when called.

A common fix is binding the current value as a default:

```python
handlers = []

for name in ["a", "b", "c"]:
    handlers.append(lambda name=name: name)
```

This is a common interview and production debugging scenario.

## First-Class Functions and Dependency Injection

Functions can be dependencies just like objects.

```python
from collections.abc import Callable


def create_service(
    clock: Callable[[], float],
) -> Callable[[], float]:
    return clock
```

In testing, a deterministic function can be supplied:

```python
def fake_clock() -> float:
    return 1_700_000_000.0
```

This can be simpler than creating a class solely to provide one operation.

The same principle applies to:

- UUID generation
- Time providers
- Feature checks
- Authorization decisions
- Serialization
- External adapters

## Function-Based Dependency Injection

A function can accept behavior as a dependency:

```python
from collections.abc import Callable


def authorize(
    user_id: int,
    permission_checker: Callable[[int, str], bool],
) -> bool:
    return permission_checker(user_id, "orders:read")
```

The business function does not need to know how permissions are stored.

The caller can provide:

```text
Production -> database/cache-backed implementation
Testing    -> deterministic fake function
```

## Performance Characteristics

Passing a function reference is inexpensive compared with most backend I/O operations, but function calls still have runtime overhead.

For CPU-heavy tight loops:

```python
for item in items:
    transform(item)
```

may be slower than specialized inlined logic because each call introduces dispatch overhead.

However, in backend applications:

```text
Python function call
       vs
PostgreSQL query
       vs
HTTP request
       vs
Kafka operation
```

network and I/O latency usually dominate.

Do not sacrifice useful abstraction for hypothetical micro-optimizations.

Measure before optimizing.

## Memory Considerations

A function object contains references to metadata and executable code information.

Closures can additionally retain references to values from enclosing scopes.

This can accidentally extend object lifetimes.

For example:

```python
def create_handler(large_object):
    def handler():
        return large_object.process()

    return handler
```

The returned handler keeps `large_object` reachable.

If the object is large, this can increase memory retention.

This matters for:

- Long-lived workers
- Callback registries
- Application-wide caches
- Event handlers
- Background tasks

## Concurrency Considerations

Function references themselves are generally safe to pass between concurrent tasks, but the state captured or accessed by the function may not be safe.

Consider:

```python
counter = 0


def increment() -> None:
    global counter
    counter += 1
```

The problem is not that the function is first-class.

The problem is shared mutable state.

For concurrent systems, consider:

- Immutable data
- Locks
- Queues
- Atomic operations where applicable
- Process-safe storage
- Database transactions
- Redis or other shared coordination mechanisms

A function abstraction does not automatically make its implementation concurrency-safe.

## Async Functions as First-Class Objects

Async functions are also first-class objects.

```python
async def fetch_user(user_id: int) -> dict[str, object]:
    ...
```

Referencing the function does not execute it:

```python
handler = fetch_user
```

Calling it creates a coroutine object:

```python
coroutine = fetch_user(42)
```

The coroutine must then be awaited or scheduled.

```python
user = await fetch_user(42)
```

This distinction is important in asynchronous backend systems.

```text
async function
     |
     | call
     v
coroutine object
     |
     | await / create_task
     v
execution
```

## Async Callback Contracts

Async callbacks should be typed explicitly.

```python
from collections.abc import Awaitable, Callable


AsyncHandler = Callable[
    [dict[str, object]],
    Awaitable[None],
]
```

This communicates that the callback returns an awaitable rather than an immediate result.

When dispatching:

```python
async def dispatch(
    handler: AsyncHandler,
    event: dict[str, object],
) -> None:
    await handler(event)
```

This avoids accidentally treating coroutine-producing functions as synchronous callbacks.

## Error Handling

Exceptions raised inside callbacks must have clearly defined ownership.

For example:

```python
def execute(
    callback: Callable[[], None],
) -> None:
    try:
        callback()
    except ValueError:
        ...
```

The caller should know:

- Which exceptions can escape?
- Should the callback be retried?
- Does failure abort the operation?
- Is failure logged?
- Is failure converted to a domain exception?

For infrastructure callbacks, retrying indiscriminately can cause duplicate side effects.

## Reliability and Idempotency

First-class callbacks are often used in:

- Event consumers
- Background workers
- Webhooks
- Retry handlers

These environments may execute work more than once.

For side-effecting callbacks:

```text
Message
   |
   v
Handler
   |
   +--> Database write
   +--> External API
   +--> Event publication
```

The handler should have appropriate idempotency guarantees.

Do not assume that a callback is invoked exactly once.

## Security Considerations

Passing a function as a dependency does not automatically make the dependency trusted.

Avoid dynamically executing arbitrary user-controlled callables.

For example, a registry should be controlled by application code:

```python
handlers: dict[str, Handler] = {
    "order.created": handle_order_created,
}
```

Do not allow arbitrary strings from external users to resolve into arbitrary Python objects or executable code.

Function references should be treated as executable capabilities.

## Testing

First-class functions simplify focused testing.

```python
def calculate_discount(
    amount: int,
    discount: callable,
) -> int:
    return discount(amount)
```

A test can supply deterministic behavior.

Prefer precise typing:

```python
from collections.abc import Callable


def calculate_discount(
    amount: int,
    discount: Callable[[int], int],
) -> int:
    return discount(amount)
```

This avoids requiring a full class hierarchy when the dependency is simply behavior.

## Mocking and Patching

Function references can complicate mocking when references are imported into another module.

For example:

```python
from payments import charge
```

If another module uses:

```python
charge(order)
```

tests should generally patch the name where it is looked up rather than assuming the original module reference is used.

The broader principle is:

```text
Patch the dependency at its point of use.
```

This becomes particularly important when designing testable dependency boundaries.

## Functional Composition

Functions can be combined to create processing pipelines.

```python
def strip_value(value: str) -> str:
    return value.strip()


def normalize_value(value: str) -> str:
    return value.lower()


def validate_value(value: str) -> str:
    if not value:
        raise ValueError("Value cannot be empty")
    return value
```

A pipeline can then compose these operations:

```python
def normalize_input(value: str) -> str:
    value = strip_value(value)
    value = normalize_value(value)
    return validate_value(value)
```

This style is useful for deterministic transformations.

Avoid creating elaborate functional pipelines when they make control flow harder to debug.

## Function Registries

Registries are a practical backend pattern.

```python
from collections.abc import Callable


Command = Callable[[dict[str, object]], None]

commands: dict[str, Command] = {}


def register(name: str, command: Command) -> None:
    commands[name] = command
```

Possible applications include:

- CLI command registration
- Event handlers
- Plugin systems
- Serialization handlers
- Factory dispatch
- Protocol-specific handlers

Registries should have clear ownership and initialization behavior.

Avoid global mutable registries unless their lifecycle is intentionally process-wide.

## Plugin Architecture

First-class functions can support lightweight plugin systems.

```text
Application
    |
    v
Plugin Registry
    |
    +--> Plugin A
    +--> Plugin B
    +--> Plugin C
```

A plugin may expose a callable:

```python
def register(registry: Registry) -> None:
    ...
```

For larger plugin architectures, explicit interfaces, entry points, protocols, lifecycle management, and isolation become more appropriate.

## When to Use First-Class Functions

Use first-class functions when:

- Behavior is small and focused.
- The behavior is stateless.
- A callback is required.
- A strategy has a simple signature.
- A transformation needs to be injected.
- A handler needs dynamic registration.
- A framework expects a callable.
- A function-based dependency is clearer than a class.

Examples:

```text
Validation function
Transformation function
Retry callback
Event handler
Authorization predicate
Sorting key
Serialization function
CLI command
```

## When Not to Use Them

Prefer a class or explicit object when:

- Significant mutable state is required.
- Multiple related operations share state.
- Resource ownership matters.
- Lifecycle management matters.
- The abstraction represents a domain entity.
- The behavior has a complex contract.
- The object requires multiple collaborators.
- Configuration is substantial.

For example, a database connection pool should not normally be represented as a closure containing hidden mutable state.

An explicit resource-owning class is easier to manage and observe.

## Functions vs Methods vs Classes

| Requirement | Function | Method | Class |
|---|---:|---:|---:|
| Stateless transformation | Excellent | Sometimes | Usually unnecessary |
| Operates on object state | No | Excellent | Excellent |
| Simple callback | Excellent | Sometimes | Often unnecessary |
| Shared mutable state | Limited | Good | Excellent |
| Resource lifecycle | Limited | Good | Excellent |
| Dependency injection | Excellent | Excellent | Excellent |
| Domain entity | Sometimes | Good | Excellent |
| Strategy without state | Excellent | Sometimes | Often unnecessary |
| Complex strategy with state | Limited | Good | Excellent |
| Framework handler | Excellent | Sometimes | Depends on framework |

The goal is not to choose functions over classes universally. Choose the smallest abstraction that clearly represents the behavior.

## Common Mistakes

### Calling Instead of Passing

Incorrect:

```python
register(handler())
```

Correct:

```python
register(handler)
```

unless registration explicitly requires the handler's return value.

### Using Lambda Everywhere

Lambdas are useful for short expressions:

```python
sorted(users, key=lambda user: user["name"])
```

They become difficult to maintain when they contain complex logic.

Use named functions for non-trivial behavior.

### Hiding Important Business Logic

Avoid deeply nested higher-order functions when a named function or class would make the business flow clearer.

### Capturing Large Objects Accidentally

Closures can retain objects longer than expected.

Be aware of what a long-lived callback captures.

### Mutable Global Registries

Process-wide registries can create test contamination and startup-order problems.

### Ignoring Async Semantics

An async function returns a coroutine when called.

It does not execute synchronously.

### Assuming Callbacks Are Reliable

Callbacks may fail, execute multiple times, or run concurrently.

Design their failure and idempotency semantics explicitly.

## Production Pitfalls

| Pitfall | Why It Happens | Better Approach |
|---|---|---|
| Handler executes during registration | `handler()` used instead of `handler` | Pass the callable |
| Callback retains memory | Closure captures large object | Review captured state and lifecycle |
| Difficult debugging | Excessive function composition | Prefer named stages |
| Runtime callback errors | Weak callable contract | Use type hints and tests |
| Duplicate side effects | Retry/event redelivery | Design idempotent handlers |
| Shared-state races | Callback mutates global state | Explicit synchronization/state ownership |
| Test leakage | Global function registry | Control lifecycle and isolate tests |
| Coroutine not awaited | Async callback treated as sync | Type and await `Awaitable` callbacks |
| Over-engineering | Classes created for tiny behavior | Use functions where appropriate |
| Under-engineering | Complex state hidden in closure | Use explicit objects |

## Senior Engineering Guidance

First-class functions are most valuable when they make **behavior explicit and replaceable**.

A good backend design might look like:

```text
Application Service
       |
       +--> validation function
       |
       +--> authorization function
       |
       +--> repository object
       |
       +--> event handler
       |
       +--> serializer function
```

Not every dependency needs to be a class.

The important questions are:

- What behavior is being supplied?
- Who owns it?
- What is its callable contract?
- Is it synchronous or asynchronous?
- Does it contain state?
- What exceptions can it raise?
- Can it be retried?
- Is it idempotent?
- What is its lifecycle?
- How is it tested?

This leads to a useful rule:

> Use a function when the primary abstraction is behavior; use an object when the primary abstraction is state plus behavior.

## Key Takeaways

- Python functions are first-class objects, so they can be assigned, passed, returned, stored, inspected, and composed like other values.
- First-class functions enable callbacks, strategy selection, event dispatch, dependency injection, middleware, and lightweight functional composition.
- Use functions for focused, preferably stateless behavior; use callable objects or classes when state, lifecycle, or complex contracts become important.
- In production systems, callable contracts, async semantics, exception ownership, concurrency, idempotency, and object lifetime matter as much as the function itself.
- First-class functions are a foundation for higher-order functions, closures, decorators, generators, and many of Python's advanced programming patterns.