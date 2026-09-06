# 05- Functions

## Overview

Functions are the primary unit of reusable behavior in Python. They provide a boundary for encapsulating logic, controlling dependencies, defining contracts, managing scope, and composing application behavior.

In backend systems, functions appear at almost every layer:

```text
HTTP Request
    |
    v
Route Handler
    |
    v
Validation
    |
    v
Service Function
    |
    v
Repository Function
    |
    v
Database
```

A function is therefore more than a syntax construct. Its signature, return value, side effects, dependencies, error behavior, and execution model form part of the application's design.

Production-quality functions should generally be:

- Focused on one coherent responsibility
- Explicit about inputs and outputs
- Predictable in their side effects
- Easy to test
- Type-annotated where useful
- Independent of unnecessary global state
- Appropriate in granularity
- Composable with other application components

Python functions also have important runtime semantics involving first-class objects, argument binding, closures, decorators, generators, recursion, and asynchronous execution. These become increasingly important as Python code moves from basic scripting to production backend systems.

## Defining a Function

A function is defined with `def`.

```python
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity
```

Calling the function:

```python
total = calculate_total(19.99, 3)
```

The function has:

- A name: `calculate_total`
- Parameters: `price`, `quantity`
- A return annotation: `float`
- A body
- A return value

Function definitions create function objects at runtime and bind them to names.

## Why Functions Matter

Functions provide several engineering benefits.

### Encapsulation

Implementation details can be hidden behind a meaningful interface.

```python
def get_active_users(repository):
    return repository.find_active_users()
```

Callers do not need to know how the repository retrieves the records.

### Reuse

The same behavior can be invoked from multiple application paths.

```python
users = get_active_users(repository)
```

### Testability

Focused functions are easier to test independently.

```python
def calculate_discount(price: float, percentage: float) -> float:
    return price * (1 - percentage)
```

The function can be tested without a database, HTTP server, or external service.

### Composition

Functions can be combined into larger workflows.

```text
validate()
   |
   v
authorize()
   |
   v
calculate()
   |
   v
persist()
   |
   v
publish()
```

This is fundamental to layered backend architecture.

## Function Parameters

Parameters define the function's input contract.

```python
def create_user(email: str, display_name: str) -> User:
    ...
```

Parameters can be:

- Positional
- Positional-or-keyword
- Keyword-only
- Positional-only
- Variadic positional
- Variadic keyword

Python provides syntax for controlling how arguments may be supplied.

## Positional Arguments

```python
def create_user(email: str, name: str) -> User:
    ...
```

The function can be called:

```python
create_user("user@example.com", "Alice")
```

Arguments are bound to parameters by position.

Positional arguments are concise but can become error-prone when many parameters have the same type.

## Keyword Arguments

Arguments can be supplied by name:

```python
create_user(
    email="user@example.com",
    name="Alice",
)
```

Keyword arguments improve readability and reduce ambiguity.

They are particularly useful when:

- A function has several parameters
- Parameters have similar types
- Some arguments are optional
- Configuration is being passed explicitly

## Default Arguments

Functions can define default values:

```python
def connect(timeout: float = 5.0) -> Connection:
    ...
```

The caller can use the default:

```python
connect()
```

or override it:

```python
connect(timeout=10.0)
```

Defaults should represent sensible and stable behavior.

## Mutable Default Arguments

A mutable default argument is evaluated once when the function is defined.

Avoid:

```python
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items
```

The same list can be reused across calls.

Prefer:

```python
def add_item(
    item: str,
    items: list[str] | None = None,
) -> list[str]:
    if items is None:
        items = []

    items.append(item)
    return items
```

This creates a new list when the caller does not provide one.

This behavior is a classic Python interview topic because it demonstrates that default arguments are evaluated at function definition time.

## Positional-Only Parameters

Python supports positional-only parameters using `/`.

```python
def calculate_total(price: float, quantity: int, /) -> float:
    return price * quantity
```

The caller must provide these parameters positionally:

```python
calculate_total(10.0, 2)
```

This is invalid:

```python
calculate_total(price=10.0, quantity=2)
```

Positional-only parameters can be useful when:

- Parameter names should not become part of the public API
- Compatibility constraints matter
- A function mirrors a low-level API
- Argument names could be confusing

They are less common in ordinary application-level service functions.

## Keyword-Only Parameters

Keyword-only parameters appear after `*`.

```python
def fetch_users(
    limit: int,
    *,
    offset: int = 0,
    include_inactive: bool = False,
) -> list[User]:
    ...
```

These must be supplied by keyword:

```python
fetch_users(
    100,
    offset=200,
    include_inactive=True,
)
```

Keyword-only parameters are particularly useful for configuration-like options.

They make call sites self-documenting and reduce positional argument mistakes.

## Variadic Positional Arguments

`*args` collects additional positional arguments.

```python
def log_values(*values: object) -> None:
    for value in values:
        print(value)
```

Example:

```python
log_values("user-1", "user-2", "user-3")
```

The parameter receives a tuple.

```python
def inspect_values(*values: object) -> tuple[object, ...]:
    return values
```

Use `*args` when the API genuinely supports a variable number of positional values.

Do not use it simply to avoid designing a clear function signature.

## Variadic Keyword Arguments

`**kwargs` collects additional keyword arguments.

```python
def configure(**options: object) -> dict[str, object]:
    return options
```

Example:

```python
configure(
    timeout=5,
    retries=3,
    cache=True,
)
```

The function receives a dictionary.

In application code, unrestricted `**kwargs` can make contracts difficult to discover and validate. Prefer explicit parameters when the supported options are known.

## Argument Unpacking

A sequence can be unpacked into positional arguments:

```python
values = (10.0, 3)

calculate_total(*values)
```

A mapping can be unpacked into keyword arguments:

```python
options = {
    "offset": 100,
    "include_inactive": True,
}

fetch_users(50, **options)
```

Unpacking is useful when data already exists in the appropriate structure.

## Argument Binding

When a function is called, Python binds supplied arguments to parameters according to its signature.

Consider:

```python
def create_user(email, name, active=True):
    ...
```

A call such as:

```python
create_user("a@example.com", name="Alice")
```

binds:

```text
email  -> "a@example.com"
name   -> "Alice"
active -> True
```

Understanding argument binding is important for debugging:

- Missing arguments
- Duplicate arguments
- Unexpected keyword arguments
- Positional/keyword conflicts
- `*args`
- `**kwargs`

Python raises `TypeError` when argument binding cannot satisfy the function signature.

## Return Values

A function can return a value:

```python
def get_user_count(users: list[User]) -> int:
    return len(users)
```

A function without an explicit `return` returns `None`.

```python
def log_event(event: Event) -> None:
    logger.info("event=%s", event.id)
```

A `return` immediately terminates the function.

```python
def find_user(users, user_id):
    for user in users:
        if user.id == user_id:
            return user

    return None
```

## Multiple Return Values

Python can return multiple values through tuple packing.

```python
def parse_response() -> tuple[int, str]:
    return 200, "OK"
```

The caller can unpack them:

```python
status_code, message = parse_response()
```

This is convenient for small, tightly related result sets.

For complex domain results, a named model or dataclass is often clearer.

Prefer:

```python
return UserLookupResult(
    user=user,
    source="cache",
)
```

when multiple returned values have meaningful domain semantics.

## Explicit Return Contracts

Functions should have predictable return behavior.

Avoid:

```python
def get_user(user_id):
    if user_id:
        return repository.get(user_id)
```

because the function implicitly returns `None` when `user_id` is falsey.

Prefer an explicit contract:

```python
def get_user(user_id: int) -> User | None:
    if user_id <= 0:
        return None

    return repository.get(user_id)
```

For application APIs, distinguish carefully between:

- Successful value
- Missing value
- Invalid input
- Operational failure

Do not use `None` for every possible failure mode.

## Type Annotations

Type annotations communicate intended contracts.

```python
def get_user(
    user_id: int,
    repository: UserRepository,
) -> User | None:
    return repository.get(user_id)
```

Annotations improve:

- IDE support
- Static analysis
- Refactoring
- Code review
- Documentation
- Maintenance

They generally do not enforce runtime types.

For externally supplied data, validation is still required.

## Pure Functions

A pure function:

- Depends only on its inputs
- Produces a deterministic result
- Does not modify external state

Example:

```python
def calculate_total(
    unit_price: Decimal,
    quantity: int,
) -> Decimal:
    return unit_price * quantity
```

Pure functions are easy to:

- Test
- Cache
- Reason about
- Reuse
- Parallelize

Not every backend function should be pure. Database writes, HTTP calls, logging, and message publishing necessarily involve side effects.

The goal is to isolate side effects rather than pretending they do not exist.

## Side Effects

A side effect occurs when a function changes or interacts with state outside its local computation.

Examples:

```python
repository.save(user)
```

```python
redis.set(cache_key, value)
```

```python
await payment_service.charge(order)
```

```python
logger.info("user_created")
```

Side effects should be intentional and visible from the function's design.

A function named:

```python
calculate_total()
```

should generally not unexpectedly modify a database.

## Function Granularity

Functions should be neither artificially tiny nor excessively large.

A function is often at a good abstraction level when it represents one coherent operation.

Prefer:

```python
def create_order(request, user):
    validate_order(request)
    authorize_order(user)
    order = build_order(request, user)
    save_order(order)
    publish_order_created(order)
    return order
```

over a 300-line function containing every implementation detail.

However, extracting every two-line operation into a separate function can also create unnecessary indirection.

The correct granularity is determined by:

- Cohesion
- Reuse
- Testability
- Complexity
- Domain boundaries
- Error handling
- Side effects

## Function Composition

Complex workflows can be composed from smaller functions.

```python
def create_order(request, user):
    data = validate_order(request)
    authorize_order(user, data)

    order = build_order(data, user)
    persist_order(order)
    publish_order_created(order)

    return order
```

This makes the high-level workflow visible while implementation details remain in dedicated functions.

## Functions as First-Class Objects

Functions are objects in Python.

They can be:

- Assigned to variables
- Passed as arguments
- Returned from functions
- Stored in collections
- Attached to objects

Example:

```python
def send_email(message):
    ...


handler = send_email
handler(message)
```

This property enables:

- Callbacks
- Dependency injection
- Decorators
- Higher-order functions
- Strategy patterns
- Function registries

## Passing Functions as Dependencies

A function can accept another function as an argument.

```python
def process_users(
    users: list[User],
    processor,
) -> None:
    for user in users:
        processor(user)
```

Callers can provide different implementations:

```python
process_users(users, send_notification)
```

This is a simple form of dependency injection.

For larger systems, explicit protocols or interfaces can make these contracts more maintainable.

## Returning Functions

Functions can return other functions.

```python
def make_multiplier(factor: int):
    def multiply(value: int) -> int:
        return value * factor

    return multiply
```

Example:

```python
double = make_multiplier(2)

double(10)
# 20
```

This behavior is the foundation for closures and decorators.

## Closures

A closure occurs when an inner function retains access to variables from its enclosing scope.

```python
def make_prefixer(prefix: str):
    def add_prefix(value: str) -> str:
        return f"{prefix}{value}"

    return add_prefix
```

The returned function retains `prefix`.

Closures are useful for:

- Configuration
- Callbacks
- Decorators
- Small stateful behaviors

They should not replace clear object-oriented designs when substantial state or behavior is involved.

## Inspecting Function Metadata

Functions expose metadata.

```python
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity

print(calculate_total.__name__)
print(calculate_total.__annotations__)
```

The `inspect` module can provide richer information:

```python
import inspect

signature = inspect.signature(calculate_total)
print(signature)
```

This can be useful for:

- Framework internals
- Dependency injection
- Testing utilities
- Debugging
- Introspection tools

Application code should generally not depend heavily on runtime introspection when a simpler explicit design is possible.

## Docstrings

Functions can document their behavior using docstrings.

```python
def calculate_total(
    unit_price: Decimal,
    quantity: int,
) -> Decimal:
    """Calculate the total price for an order item."""
    return unit_price * quantity
```

Docstrings are especially valuable for:

- Public libraries
- Complex domain functions
- Non-obvious invariants
- Integration boundaries

Avoid writing docstrings that merely restate obvious syntax.

## Recursive Functions

A recursive function calls itself.

```python
def factorial(value: int) -> int:
    if value <= 1:
        return 1

    return value * factorial(value - 1)
```

Recursion can be appropriate for inherently recursive structures such as trees.

However, Python does not optimize tail recursion, and recursive depth is limited.

For large or unbounded data structures, iterative approaches are often safer.

## Function Calls and the Call Stack

Each active function call creates a new execution frame.

Conceptually:

```text
main()
  |
  +--> handle_request()
          |
          +--> create_order()
                  |
                  +--> save_order()
```

The call stack grows as functions call other functions and unwinds as they return.

An unbounded recursive function can therefore eventually raise `RecursionError`.

This model is also important when debugging stack traces.

## Exceptions and Function Boundaries

Functions should either handle an error they can meaningfully recover from or allow it to propagate.

```python
def get_user(user_id: int) -> User:
    try:
        return repository.get(user_id)
    except DatabaseTimeoutError:
        raise UserLookupUnavailable(user_id) from None
```

A lower-level function should not necessarily convert every error into a generic exception.

Exception translation is useful when crossing architectural boundaries.

For example:

```text
Database Error
      |
      v
Repository Exception
      |
      v
Service Exception
      |
      v
HTTP Error Response
```

Each layer should preserve enough information for appropriate handling and observability.

## Functions and Transactions

Transaction boundaries should be deliberate.

Avoid hiding transaction behavior inside unrelated low-level utility functions.

For example, a service-level operation may define the transaction boundary:

```python
def create_order(data, repository, transaction_manager):
    with transaction_manager.transaction():
        order = repository.create_order(data)
        repository.reserve_inventory(order)
        return order
```

The exact implementation depends on the database and framework, but the architectural principle remains:

> The layer responsible for the business operation should usually control the transaction boundary.

This prevents individual repository calls from unintentionally creating inconsistent transaction scopes.

## Functions and Dependency Injection

Explicit dependencies are generally preferable to hidden globals.

Avoid:

```python
def create_order(data):
    database.save(data)
```

when `database` is an implicit global dependency.

Prefer:

```python
def create_order(data, repository):
    repository.save(data)
```

This makes the dependency:

- Visible
- Replaceable
- Testable
- Configurable

A dependency-injection framework can automate this at larger scales, but explicit function parameters are often sufficient.

## Functions in FastAPI

FastAPI commonly uses functions as request handlers.

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/users/{user_id}")
async def get_user(user_id: int) -> dict[str, int]:
    return {"user_id": user_id}
```

The framework inspects the function signature to understand:

- Route parameters
- Query parameters
- Type annotations
- Dependencies
- Return behavior

This makes function signatures part of the API implementation contract.

For production applications, keep route handlers thin and delegate business logic to services.

```python
@app.post("/orders")
async def create_order(request: CreateOrderRequest):
    order = await order_service.create(request)
    return order
```

## Functions in Django

Django uses functions in multiple roles:

- Views
- Middleware
- Management commands
- Signals
- Utility functions
- Service-layer code

A view should generally coordinate HTTP concerns rather than contain the entire business workflow.

```python
def create_order_view(request):
    data = parse_request(request)
    order = order_service.create(data)
    return JsonResponse(order.to_dict())
```

The exact architectural pattern varies by Django project, but keeping HTTP concerns separate from domain logic improves maintainability.

## Synchronous vs Asynchronous Functions

A normal function:

```python
def get_user(user_id: int) -> User:
    return repository.get(user_id)
```

executes synchronously.

An asynchronous function:

```python
async def get_user(user_id: int) -> User:
    return await repository.get(user_id)
```

returns a coroutine when called.

```python
result = get_user(1001)
```

does not execute the coroutine to completion.

It must be awaited from an appropriate asynchronous context:

```python
result = await get_user(1001)
```

This distinction is fundamental to asyncio-based applications.

## Async Functions and Blocking Operations

An asynchronous function can still contain blocking code.

Avoid:

```python
async def process():
    time.sleep(5)
```

because the event loop can be blocked.

Prefer an asynchronous API:

```python
async def process():
    await asyncio.sleep(5)
```

or explicitly offload appropriate blocking work.

The important principle is:

> `async def` does not automatically make every operation inside the function non-blocking.

## Generator Functions

A function containing `yield` becomes a generator function.

```python
def read_orders(source):
    for order in source:
        yield order
```

Calling it returns a generator rather than immediately producing all results.

Generators are useful for:

- Streaming
- Large files
- ETL pipelines
- Lazy computation
- Memory-efficient processing

Example:

```python
def process_orders(source):
    for order in source:
        yield transform_order(order)
```

This avoids materializing the entire transformed dataset at once.

Generators are covered in greater depth in the Intermediate Python section.

## Function Performance

Every function call has some runtime overhead, but function abstraction should not normally be avoided solely for this reason.

Prefer clear boundaries first.

Performance concerns become significant when:

- A function is called millions of times
- It is inside a hot loop
- It performs expensive allocations
- It repeatedly invokes external services
- It introduces unnecessary serialization
- It creates excessive intermediate objects

The first optimization target should generally be the algorithm and external operations, not arbitrary function extraction.

For example:

```python
for user_id in user_ids:
    repository.get(user_id)
```

is more likely to be problematic because of database calls than because of the function call itself.

## Avoiding Hidden Work

A function's name should accurately communicate its cost.

Avoid:

```python
def get_user(user_id):
    # Also performs three HTTP requests and refreshes a cache.
    ...
```

A caller reasonably expects `get_user()` to represent a user lookup, not an entire distributed workflow.

For expensive operations, names should communicate intent:

```python
refresh_user_from_identity_provider()
```

Clear naming helps engineers reason about latency and side effects.

## Function Design for Testability

A function with explicit dependencies is easier to test.

```python
def calculate_order_total(
    items: list[OrderItem],
    tax_rate: Decimal,
) -> Decimal:
    ...
```

This can be tested without infrastructure.

For side-effecting functions:

```python
def create_order(
    data: CreateOrderData,
    repository: OrderRepository,
    publisher: EventPublisher,
) -> Order:
    ...
```

Tests can supply controlled implementations or mocks.

This is one reason dependency injection and separation of concerns matter in backend systems.

## Security Considerations

Function boundaries should not accidentally bypass security checks.

For example, if a low-level repository function is callable from many places:

```python
repository.delete_user(user_id)
```

the application should ensure authorization occurs at the appropriate service or policy boundary.

Do not assume:

> "This function is only called internally."

Internal functions can become externally reachable through future routes, background jobs, administrative interfaces, or tests.

Security-sensitive functions should have clear contracts and appropriate authorization at the layer responsible for the decision.

## Reliability Considerations

Production functions that interact with external systems should explicitly account for:

- Timeouts
- Retries
- Idempotency
- Error propagation
- Resource cleanup
- Cancellation
- Logging
- Metrics

For example:

```python
async def charge_payment(order: Order) -> PaymentResult:
    try:
        return await payment_client.charge(
            order_id=order.id,
            amount=order.total,
            timeout=5,
        )
    except PaymentTimeoutError as exc:
        logger.warning(
            "payment_timeout order_id=%s",
            order.id,
        )
        raise PaymentUnavailable(order.id) from exc
```

The function should not silently swallow failures.

## Observability

Functions that represent important business operations are useful observability boundaries.

Examples:

```text
create_order()
charge_payment()
reserve_inventory()
publish_event()
```

These operations can be instrumented with:

- Duration
- Success/failure counts
- Error types
- External dependency latency
- Correlation/request IDs

Avoid logging sensitive input values indiscriminately.

For example, do not log:

- Passwords
- Authentication tokens
- Full payment information
- Secrets
- Sensitive personal data

Observability should improve diagnosis without creating a data-security problem.

## Common Mistakes

### Functions With Too Many Responsibilities

A function that validates input, authenticates users, performs database queries, calls external APIs, formats HTTP responses, and publishes events is difficult to maintain.

Split responsibilities according to meaningful architectural boundaries.

### Too Many Parameters

This:

```python
def create_order(
    user_id,
    product_id,
    quantity,
    currency,
    tax_rate,
    discount,
    shipping_address,
    metadata,
):
    ...
```

can become difficult to use and test.

Consider a domain model:

```python
def create_order(command: CreateOrderCommand):
    ...
```

when the data represents a coherent domain operation.

### Hidden Global Dependencies

Avoid relying on mutable global state for database clients, configuration, or business state when explicit dependency injection is practical.

### Mutable Default Arguments

Never use mutable defaults unintentionally.

### Overusing `**kwargs`

Unrestricted keyword arguments can hide invalid configuration and make static analysis weaker.

Prefer explicit parameters when the contract is known.

### Ignoring Return Semantics

A function that sometimes returns a value, sometimes returns `None`, and sometimes raises unrelated exceptions creates an ambiguous API.

Define predictable behavior.

### Excessive Function Extraction

Creating dozens of trivial wrapper functions can make control flow difficult to follow.

Extract functions when they provide meaningful:

- Abstraction
- Reuse
- Testability
- Separation of responsibility
- Domain vocabulary

### Hidden External Calls

A function that appears computational but performs network or database operations can create unexpected latency.

Name and document expensive behavior clearly.

### Catching Exceptions Too Broadly

Avoid:

```python
def process():
    try:
        ...
    except Exception:
        return None
```

This can hide real application failures.

## Interview Traps

### Are Functions Objects in Python?

Yes.

They can be assigned, passed, returned, stored, and inspected like other objects.

### When Are Default Arguments Evaluated?

Default argument expressions are evaluated when the function definition executes, not every time the function is called.

This explains the mutable-default-argument behavior.

### What Does `*args` Contain?

`*args` collects additional positional arguments into a tuple.

```python
def example(*args):
    print(type(args))
```

The result is:

```text
<class 'tuple'>
```

### What Does `**kwargs` Contain?

`**kwargs` collects additional keyword arguments into a dictionary.

```python
def example(**kwargs):
    print(type(kwargs))
```

The result is:

```text
<class 'dict'>
```

### What Is the Difference Between `return` and `yield`?

`return` terminates a function and provides a final result.

`yield` pauses a generator function and produces values incrementally.

### What Happens When an `async def` Function Is Called?

Calling an async function normally creates a coroutine object.

The coroutine must be awaited or scheduled for execution.

```python
async def get_data():
    return 42


result = get_data()
```

`result` is not `42`; it is a coroutine object.

### Does Python Pass Arguments by Reference?

The most precise description is **call-by-sharing**.

The function receives references to objects. Rebinding the local parameter does not rebind the caller's name, while mutation of a shared mutable object can be visible to the caller.

```python
def rebind(items):
    items = []


def mutate(items):
    items.clear()
```

These two functions have fundamentally different effects on a caller's object.

## Production Function Checklist

Before introducing or modifying an important function, consider:

| Question | Engineering Concern |
|---|---|
| What does this function do? | Responsibility |
| What are its inputs? | Contract |
| What does it return? | Output semantics |
| What can it raise? | Failure behavior |
| Does it mutate anything? | Side effects |
| Does it access external systems? | Latency/reliability |
| Can it be tested independently? | Testability |
| Are dependencies explicit? | Maintainability |
| Is it synchronous or asynchronous? | Execution model |
| Can it be called concurrently? | Thread/task safety |
| Does it process large data? | Memory usage |
| Does it enforce security boundaries? | Authorization |
| Does it need observability? | Operations |

## Best Practices

For production Python functions:

- Give each function a clear and coherent responsibility.
- Use descriptive names that communicate intent.
- Use type annotations for meaningful contracts.
- Prefer explicit dependencies over hidden global state.
- Prefer keyword-only parameters for optional configuration-heavy arguments.
- Avoid mutable default arguments.
- Keep return behavior predictable.
- Use guard clauses to reduce unnecessary nesting.
- Keep side effects explicit.
- Separate pure business calculations from infrastructure operations where practical.
- Keep transaction boundaries deliberate.
- Catch exceptions only where meaningful recovery or translation is possible.
- Avoid broad `except Exception` handlers in lower layers.
- Use generators for appropriate streaming workloads.
- Do not perform blocking operations inside asynchronous functions.
- Consider database and network calls when evaluating function performance.
- Design functions so important business operations can be observed and tested.
- Keep security and authorization decisions explicit.
- Extract functions when they improve abstraction, cohesion, reuse, or testability rather than simply reducing line count.

## Key Takeaways

- Python functions are first-class objects and form the fundamental abstraction boundary for reusable behavior, dependency injection, callbacks, decorators, and application composition.
- Function signatures define important contracts around argument binding, defaults, positional and keyword arguments, return values, and type annotations.
- Production functions should have clear responsibilities, explicit dependencies, predictable return and error behavior, and intentional side effects.
- Backend function design must account for database and network I/O, transactions, retries, async execution, concurrency, security, observability, and testability.
- Senior-level Python design focuses less on writing smaller functions and more on creating meaningful boundaries that make business logic, infrastructure dependencies, and failure behavior explicit.