# 13- Unpacking

## Overview

Unpacking is Python's mechanism for assigning elements from an iterable or mapping to multiple variables in a single operation.

It is used throughout modern Python code for:

- Tuple and sequence assignment
- Function arguments
- Returning multiple values
- Swapping values
- Iterating over structured records
- Dictionary merging
- Function argument forwarding
- API and configuration handling
- Pattern matching
- Data transformation pipelines

The core idea is simple:

```python
first, second = values
```

Python obtains an iterator from the right-hand side and assigns successive values to the targets on the left.

Unpacking becomes especially important at the intermediate and senior level because `*` and `**` are not merely syntactic conveniences. They interact with:

- The iterator protocol
- Function-call semantics
- Mapping semantics
- Memory allocation
- Type checking
- API design
- Backward compatibility
- Data transformation
- Python's argument-binding rules

## Why Unpacking Matters

Without unpacking:

```python
user = get_user()

user_id = user[0]
email = user[1]
status = user[2]
```

With unpacking:

```python
user_id, email, status = get_user()
```

The second version makes the expected structure explicit.

In backend systems, this is particularly useful when working with:

- Database rows
- API responses
- Configuration values
- Function return values
- Key-value pairs
- Structured event data

## Basic Sequence Unpacking

```python
coordinates = (40.7128, -74.0060)

latitude, longitude = coordinates
```

After assignment:

```text
latitude  -> 40.7128
longitude -> -74.0060
```

The source can be any iterable, not just a tuple:

```python
a, b = [10, 20]
```

```python
a, b = "XY"
```

```python
a, b = {10, 20}
```

The important requirement is that the right-hand side can produce the expected number of values.

## How Unpacking Works Internally

Conceptually:

```python
first, second, third = iterable
```

behaves approximately like:

```python
iterator = iter(iterable)

first = next(iterator)
second = next(iterator)
third = next(iterator)
```

Python also verifies that the iterable contains exactly the required number of values.

For:

```python
a, b = [1, 2, 3]
```

Python discovers an additional value and raises:

```text
ValueError: too many values to unpack
```

For:

```python
a, b = [1]
```

it raises:

```text
ValueError: not enough values to unpack
```

This connection to the iterator protocol is important: unpacking works with custom iterables and generators as well.

## Exact Unpacking

When the number of values is known:

```python
status, message = get_status()
```

The iterable must contain exactly two values.

This is useful when the function contract guarantees a fixed structure.

For example:

```python
def parse_response(response) -> tuple[int, str]:
    return response.status_code, response.reason
```

Usage:

```python
status_code, reason = parse_response(response)
```

## Unpacking Function Return Values

Python functions can return multiple values:

```python
def parse_port(value: str) -> tuple[int, bool]:
    try:
        port = int(value)
    except ValueError:
        return 0, False

    return port, True
```

Usage:

```python
port, valid = parse_port("8080")
```

Technically, Python returns one tuple:

```python
(port, valid)
```

The caller then unpacks it.

This is useful for small, tightly coupled result values.

For complex domain results, a dataclass or dedicated result type is often clearer:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ParseResult:
    port: int
    valid: bool
```

## Swapping Variables

Python supports direct swapping:

```python
left = 10
right = 20

left, right = right, left
```

This avoids a temporary variable:

```python
temporary = left
left = right
right = temporary
```

The right-hand side is evaluated before assignment.

Conceptually:

```text
right, left
   |
   v
temporary tuple
   |
   +--> left
   |
   +--> right
```

This is safe because both expressions are evaluated before the targets are assigned.

## Multiple Assignment

Unpacking can initialize multiple variables:

```python
host, port = "localhost", 5432
```

This is technically tuple packing followed by unpacking.

The right side represents multiple values:

```python
("localhost", 5432)
```

and the left side receives them.

## Nested Unpacking

Unpacking can mirror nested structures:

```python
user = (
    42,
    ("alice@example.com", True),
)

user_id, (email, verified) = user
```

Result:

```text
user_id  -> 42
email    -> alice@example.com
verified -> True
```

Nested unpacking is useful when the structure is stable.

Avoid excessive nesting when it makes the data model difficult to understand.

## Extended Unpacking

Python supports starred unpacking:

```python
first, *middle, last = [1, 2, 3, 4, 5]
```

Result:

```python
first  # 1
middle # [2, 3, 4]
last   # 5
```

The starred target collects zero or more remaining elements.

## Starred Unpacking Rules

A single starred target can appear in an assignment:

```python
first, *rest = values
```

```python
*prefix, last = values
```

```python
first, *middle, last = values
```

But this is invalid:

```python
*a, *b = values
```

Python cannot determine how the remaining values should be divided.

## Starred Target Always Produces a List

Consider:

```python
first, *rest = (1, 2, 3)
```

`rest` is:

```python
[2, 3]
```

not a tuple.

Similarly:

```python
first, *rest = generator()
```

produces a list for `rest`.

This matters for memory usage.

## Extended Unpacking and Memory

Consider:

```python
first, *rest = huge_iterator
```

Python must consume the remaining values to construct `rest`.

Therefore, unlike ordinary lazy iteration, this can materialize a large amount of data.

For a potentially large stream, prefer explicit iteration:

```python
iterator = iter(huge_iterator)

first = next(iterator)

for value in iterator:
    process(value)
```

Do not use starred unpacking casually on unbounded or very large iterables.

## Ignoring Values with `_`

A conventional pattern is:

```python
first, _, third = values
```

when the middle value is intentionally ignored.

For example:

```python
status_code, _, body = response_parts
```

The underscore is just a normal Python variable name. Python does not treat `_` as a special discard operator.

Its meaning comes from convention.

## Ignoring Multiple Values

Starred unpacking can discard an arbitrary middle section:

```python
first, *_, last = values
```

However, this still creates a list containing the middle values.

Therefore:

```python
first, *_, last = huge_iterable
```

can be memory-expensive.

If the middle values are not needed, explicit iteration or indexing may be more appropriate depending on the source.

## Unpacking in `for` Loops

Unpacking is particularly useful when iterating structured values.

```python
users = [
    ("alice", True),
    ("bob", False),
]

for name, active in users:
    if active:
        process_user(name)
```

This is clearer than:

```python
for user in users:
    name = user[0]
    active = user[1]
```

## Dictionary Iteration

Dictionary iteration normally produces keys:

```python
for key in mapping:
    ...
```

To unpack keys and values, use `.items()`:

```python
for key, value in mapping.items():
    process(key, value)
```

This is one of the most common practical uses of unpacking.

## `enumerate()` with Unpacking

```python
for index, user in enumerate(users):
    print(index, user)
```

`enumerate()` produces pairs:

```text
(index, value)
```

which are naturally unpacked.

This is preferable to manually maintaining an index:

```python
index = 0

for user in users:
    ...
    index += 1
```

## `zip()` with Unpacking

`zip()` produces tuples that can be unpacked:

```python
names = ["alice", "bob"]
ages = [30, 35]

for name, age in zip(names, ages):
    print(name, age)
```

The data flow is:

```text
names ----+
          |
          v
         zip()
          ^
          |
ages -----+
          |
          v
(name, age)
          |
          v
     unpacking
```

This is useful when processing corresponding values.

## `zip()` and Strictness

When inputs must have equal length, modern Python supports:

```python
for name, age in zip(
    names,
    ages,
    strict=True,
):
    ...
```

Without `strict=True`, `zip()` stops at the shortest iterable.

This can silently lose data if unequal lengths indicate a programming error.

Use strict mode when equal cardinality is part of the invariant.

## Unpacking Dictionary Items

```python
config = {
    "host": "localhost",
    "port": 5432,
}

for key, value in config.items():
    print(key, value)
```

The `.items()` iterator produces two-element tuples.

The loop target unpacks each tuple.

## Function Argument Unpacking

The `*` operator has another important use: unpacking positional arguments into a function call.

```python
def connect(host: str, port: int):
    ...


arguments = ("localhost", 5432)

connect(*arguments)
```

This is equivalent to:

```python
connect("localhost", 5432)
```

The difference is that the arguments originate from an iterable.

## `**` Argument Unpacking

`**` expands a mapping into keyword arguments.

```python
def create_user(
    name: str,
    email: str,
    active: bool,
):
    ...


payload = {
    "name": "alice",
    "email": "alice@example.com",
    "active": True,
}

create_user(**payload)
```

Conceptually:

```text
mapping
   |
   v
**payload
   |
   +--> name=...
   +--> email=...
   +--> active=...
```

The mapping keys must be valid keyword names and must match the function's accepted parameters unless the function accepts `**kwargs`.

## `*args`

A function can collect arbitrary positional arguments:

```python
def log_values(*values):
    for value in values:
        logger.info("value=%r", value)
```

Calling:

```python
log_values(1, 2, 3)
```

binds:

```python
values == (1, 2, 3)
```

`*args` is a parameter-collection mechanism.

`*values` in a function call is an argument-expansion mechanism.

The syntax is related but operates in opposite directions.

## `**kwargs`

A function can collect arbitrary keyword arguments:

```python
def configure(**options):
    timeout = options.get("timeout", 5)
    retries = options.get("retries", 3)

    return timeout, retries
```

Calling:

```python
configure(timeout=10, retries=5)
```

creates a dictionary-like mapping of keyword arguments.

## `*` in Function Signatures

A bare `*` makes following parameters keyword-only:

```python
def create_client(
    base_url: str,
    *,
    timeout: float = 5.0,
    retries: int = 3,
):
    ...
```

This means:

```python
create_client(
    "https://api.example.com",
    timeout=10,
    retries=5,
)
```

is valid.

But:

```python
create_client(
    "https://api.example.com",
    10,
    5,
)
```

raises a `TypeError`.

Keyword-only parameters are useful for API clarity and backward compatibility.

## `*args` and `**kwargs` in API Design

A common wrapper pattern is:

```python
def wrapper(*args, **kwargs):
    return function(*args, **kwargs)
```

This forwards arbitrary arguments.

Decorators frequently use this pattern.

However, blindly accepting arbitrary arguments can weaken type safety and API clarity.

Modern Python code should use precise signatures and `ParamSpec` where appropriate when writing reusable decorators.

## Combining Positional and Keyword Unpacking

Python allows:

```python
args = ("localhost",)
kwargs = {
    "port": 5432,
}

connect(*args, **kwargs)
```

This is useful for forwarding dynamically constructed arguments.

## Multiple `*` Expansions

Python allows multiple iterable expansions in contexts that support them:

```python
values = [
    *first_values,
    *second_values,
]
```

For example:

```python
combined = [
    *active_users,
    *pending_users,
]
```

Each iterable contributes its elements to the new list.

## List Unpacking

The syntax:

```python
combined = [
    *first,
    *second,
]
```

creates a new list.

It is different from:

```python
combined = first + second
```

in syntax and implementation details, although both create a combined list for ordinary lists.

The important point is that unpacking iterates the sources and inserts their elements into a new list.

## Tuple Unpacking

Tuple construction also supports unpacking:

```python
combined = (
    *first,
    *second,
)
```

This creates a new tuple containing the elements.

## Set Unpacking

Set displays support unpacking:

```python
combined = {
    *first_ids,
    *second_ids,
}
```

Duplicate values are removed because the resulting object is a set.

## Dictionary Unpacking

Mappings can be merged using `**`:

```python
defaults = {
    "timeout": 5,
    "retries": 3,
}

overrides = {
    "timeout": 10,
}

config = {
    **defaults,
    **overrides,
}
```

The later mapping wins:

```python
config == {
    "timeout": 10,
    "retries": 3,
}
```

This is useful for configuration composition.

## Dictionary Merge Operators

For dictionaries, Python also provides:

```python
config = defaults | overrides
```

and:

```python
defaults |= overrides
```

The choice depends on whether a new dictionary or in-place update is desired.

`**` unpacking remains useful when constructing a dictionary alongside explicit key-value entries:

```python
payload = {
    "request_id": request_id,
    **metadata,
}
```

## Duplicate Keyword Arguments

This is invalid:

```python
payload = {
    "name": "alice",
}

create_user(
    name="bob",
    **payload,
)
```

Python raises a `TypeError` because the same keyword argument is supplied more than once.

This differs from dictionary construction:

```python
payload = {
    **{"name": "alice"},
    "name": "bob",
}
```

where the later key replaces the earlier value.

## Mapping Requirements for `**`

For function calls:

```python
function(**mapping)
```

the object must provide appropriate mapping behavior.

Typical usage is:

```python
function(**dict_value)
```

The keys must be strings suitable for keyword argument names.

This is why arbitrary mappings such as:

```python
{1: "value"}
```

cannot simply be used as keyword arguments to ordinary Python functions.

## Unpacking and API Payloads

Suppose an API layer has validated data:

```python
payload = {
    "customer_id": 42,
    "currency": "USD",
    "amount": Decimal("100.00"),
}
```

A service function can receive it with:

```python
order = create_order(**payload)
```

This can be convenient, but the dictionary must match the function's public contract exactly.

For large systems, explicit arguments may be preferable:

```python
order = create_order(
    customer_id=payload["customer_id"],
    currency=payload["currency"],
    amount=payload["amount"],
)
```

Explicit mapping can make validation and API evolution easier to reason about.

## Unpacking and FastAPI

FastAPI commonly uses typed models rather than raw dictionary expansion.

For example:

```python
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class CreateUserRequest(BaseModel):
    name: str
    email: str
    active: bool = True


@app.post("/users")
def create_user(request: CreateUserRequest):
    return create_user(
        name=request.name,
        email=request.email,
        active=request.active,
    )
```

Blindly doing:

```python
create_user(**request.model_dump())
```

can be appropriate when the model and function contract are deliberately aligned.

It should not be used simply to avoid writing explicit arguments.

## Unpacking and Django

Django commonly returns structured tuples from operations such as:

```python
created, created_new = Model.objects.get_or_create(
    email=email,
)
```

The values can be unpacked directly:

```python
user, created = User.objects.get_or_create(
    email=email,
)
```

This improves readability when the API explicitly returns a fixed tuple-like structure.

## Unpacking Database Rows

Database libraries often return row-like objects.

If a query returns tuples:

```python
rows = cursor.fetchall()

for user_id, email, status in rows:
    process_user(
        user_id,
        email,
        status,
    )
```

This is concise when the column ordering is stable.

For larger queries, named rows or dataclasses may provide stronger readability.

Avoid relying on positional unpacking when SQL column order can change independently of the Python code.

## Unpacking Kafka Events

A structured event may contain:

```python
event = (
    "order.created",
    42,
    {"total": "100.00"},
)

event_type, order_id, payload = event
```

This is concise for stable internal event structures.

For externally versioned events, explicit schemas are generally safer than relying on positional order.

## Unpacking Configuration

Configuration can be represented as:

```python
database = (
    "postgresql.example.internal",
    5432,
)

host, port = database
```

For production configuration, typed models or named mappings are usually preferable when the number of fields grows.

Positional unpacking makes field order part of the contract.

## Starred Unpacking in Data Processing

Suppose records contain a leading identifier followed by arbitrary values:

```python
record = (
    42,
    "alice@example.com",
    "active",
    "premium",
)

user_id, *attributes = record
```

Result:

```python
user_id == 42
attributes == [
    "alice@example.com",
    "active",
    "premium",
]
```

This can be useful for flexible structures.

However, if the data has a defined schema, explicit named fields are usually better.

## Unpacking Generators

Unpacking consumes an iterable:

```python
def values():
    yield 10
    yield 20


a, b = values()
```

The generator is exhausted after successful unpacking.

This matters when the source represents:

- A file
- A database cursor
- A network stream
- A Kafka consumer
- A large generator

Exact unpacking consumes only enough values to verify the expected count, but starred unpacking may consume the remainder.

## Infinite Iterables

This is dangerous:

```python
first, *rest = infinite_generator()
```

The interpreter attempts to consume the remaining values forever.

The program will not complete.

For streaming systems, never use starred unpacking on potentially unbounded sources.

## Unpacking and Side Effects

The expressions on the right-hand side are evaluated before assignment.

Consider:

```python
a, b = get_a(), get_b()
```

Both function calls occur before the targets are updated.

If the second function fails:

```python
a, b = get_a(), get_b()
```

the assignment does not complete.

However, `get_a()` may already have performed its side effects.

Therefore, unpacking does not provide transactional semantics.

## Evaluation Order

Python evaluates the right-hand side from left to right:

```python
a, b = first(), second()
```

The effective sequence is:

```text
first()
   |
   v
second()
   |
   v
assignment
```

This is relevant when expressions perform I/O or mutate shared state.

Keep side effects out of complex assignment expressions when possible.

## Attribute and Subscript Targets

Unpacking targets do not have to be simple variable names.

For example:

```python
values = [10, 20]

result = {"value": None}

result["value"], result["other"] = values
```

Similarly:

```python
obj.x, obj.y = values
```

The right-hand side is evaluated before assignment to the targets.

Complex targets can be useful but may reduce readability.

## Assignment Expressions vs Unpacking

Unpacking:

```python
user_id, email = get_user()
```

assigns multiple values.

The walrus operator:

```python
if user := find_user():
    ...
```

assigns a single expression result.

They solve different problems and should not be confused.

## Structural Pattern Matching and Unpacking

Pattern matching uses related structural concepts:

```python
match event:
    case ("order.created", order_id):
        process_order(order_id)
    case ("order.cancelled", order_id):
        cancel_order(order_id)
```

Pattern matching can destructure values while also selecting based on structure.

Traditional unpacking is generally appropriate when the structure is already known.

Pattern matching is more useful when multiple shapes need to be handled.

## Type Hints and Unpacking

Typed tuples can document fixed positional structures:

```python
from typing import TypeAlias


UserRecord: TypeAlias = tuple[int, str, bool]


def load_user() -> UserRecord:
    return 42, "alice@example.com", True
```

Usage:

```python
user_id, email, active = load_user()
```

For larger structures, `TypedDict`, dataclasses, or dedicated classes may provide better semantics.

## Sequence vs Mapping Unpacking

These are fundamentally different.

Sequence unpacking:

```python
a, b = [10, 20]
```

depends on iteration order.

Mapping unpacking into variables:

```python
for key, value in mapping.items():
    ...
```

depends on the `.items()` pair structure.

Dictionary construction with:

```python
{
    **mapping,
}
```

merges mapping keys and values.

Do not confuse:

```python
a, b = mapping
```

with:

```python
a, b = mapping.items()
```

The first unpacks keys; the second attempts to unpack key-value pairs as an iterable.

## Unpacking vs Indexing

Prefer:

```python
user_id, email = user_record
```

when the record contract is a fixed two-element structure.

Prefer indexing when only one element is needed:

```python
user_id = user_record[0]
```

Unpacking communicates that the caller expects the complete structure.

## Unpacking vs Named Structures

Consider:

```python
user_id, email, active = row
```

This is compact but positional.

A dataclass makes the schema explicit:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    user_id: int
    email: str
    active: bool
```

Then:

```python
user.user_id
user.email
user.active
```

As the domain model becomes more complex, named attributes generally scale better than positional unpacking.

## Performance Considerations

Simple unpacking is generally inexpensive.

However, extended unpacking:

```python
first, *middle, last = values
```

requires collecting the middle values into a list.

For `n` remaining values, this requires approximately:

```text
Time:  O(n)
Space: O(n)
```

Normal exact unpacking requires consuming the source values but does not create a separate list for the entire source.

For performance-sensitive code, understand whether the operation is:

- Lazy
- Materializing
- Copying
- Iterating
- Allocating

## Unpacking and Memory

Consider:

```python
first, *rest = large_list
```

The starred portion creates a new list.

Therefore:

```text
original list
     |
     +--> first
     |
     +--> copied rest list
```

The original list remains in memory as well if still referenced.

For large datasets, this can temporarily increase peak memory significantly.

## Unpacking in High-Throughput Services

In a FastAPI or Django service, unpacking small request structures is generally negligible compared with:

- Network latency
- JSON parsing
- Database operations
- Serialization
- Business processing

Do not micro-optimize ordinary unpacking.

Focus on memory-heavy patterns such as:

```python
first, *rest = huge_dataset
```

or repeated dictionary/list expansion in hot loops.

## Dictionary Expansion and Copies

Consider:

```python
payload = {
    **defaults,
    **request_data,
}
```

A new dictionary is created.

For small request payloads this is normally appropriate.

For very large mappings or extremely hot code paths, unnecessary copying can increase memory allocation and CPU cost.

Measure before optimizing, but understand the allocation semantics.

## Concurrency Considerations

Unpacking itself does not provide synchronization.

This:

```python
current, previous = get_state()
```

does not make `get_state()` thread-safe.

Similarly:

```python
a, b = shared_state()
```

does not create an atomic snapshot unless the underlying function provides that guarantee.

In concurrent systems, the correctness of the data source and synchronization mechanism matters more than the unpacking syntax.

## Security Considerations

Unpacking should not be used as a substitute for input validation.

For example:

```python
user_id, role = request_data
```

does not guarantee that:

- `user_id` is valid
- `role` is authorized
- the structure came from a trusted source

Validate external input before using it.

For keyword expansion:

```python
create_user(**request_data)
```

be careful about accepting unexpected keys.

Prefer explicit schemas and typed validation at API boundaries.

## API Compatibility

Suppose a function initially returns:

```python
return user_id, email
```

and callers use:

```python
user_id, email = get_user()
```

Changing it to:

```python
return user_id, email, active
```

breaks existing callers.

Positional unpacking therefore makes the return structure part of the API contract.

For public or long-lived APIs, consider named result objects when evolution is expected.

## Backward-Compatible Function Signatures

Keyword-only parameters can make API evolution safer:

```python
def create_client(
    base_url: str,
    *,
    timeout: float = 5.0,
    retries: int = 3,
):
    ...
```

Adding another keyword-only parameter:

```python
def create_client(
    base_url: str,
    *,
    timeout: float = 5.0,
    retries: int = 3,
    verify_tls: bool = True,
):
    ...
```

does not change existing positional calls.

This is one reason modern Python APIs frequently use keyword-only arguments.

## Common Mistakes

### Expecting a List from `map()` or `filter()`

They return iterators.

### Using Starred Unpacking on Huge Data

```python
first, *rest = huge_iterable
```

can materialize a large list.

### Using Starred Unpacking on Infinite Iterators

It never finishes.

### Assuming `_` Discards a Value

It merely assigns to a conventional variable name.

### Unpacking an Unstable Positional Structure

If field order can change, positional unpacking can introduce subtle bugs.

### Blindly Using `**request_data`

Unexpected or renamed keys can break function calls.

### Using `*args` and `**kwargs` Everywhere

Generic argument forwarding can make APIs harder to understand and type-check.

### Ignoring `zip()` Length Mismatches

Default `zip()` silently stops at the shortest iterable.

Use:

```python
zip(a, b, strict=True)
```

when equal length is required.

### Overusing Nested Unpacking

This:

```python
a, (b, (c, d)) = value
```

can become difficult to maintain.

### Assuming Unpacking Is Transactional

Right-hand-side expressions can perform side effects before assignment completes.

### Using Positional Results for Complex Domain Models

A dataclass or named structure may be clearer.

## Production Pitfalls

| Pitfall | Impact | Better approach |
|---|---|---|
| `first, *rest = huge_data` | High memory usage | Iterate explicitly |
| Starred unpacking of infinite source | Non-terminating operation | Consume incrementally |
| Positional unpacking of unstable API response | Runtime failures | Use named structures/schema |
| `function(**raw_payload)` | Unexpected arguments | Validate schema first |
| Default `zip()` on required equal-length inputs | Silent data loss | Use `strict=True` |
| Excessive `*args/**kwargs` | Weak API contracts | Explicit typed parameters |
| Deep nested unpacking | Poor readability | Use named models |
| Unpacking database rows by fragile column order | Incorrect field mapping | Explicit column ordering/named rows |
| Dictionary expansion in hot loops | Extra allocations | Measure and optimize only if needed |
| Assuming unpacking provides atomicity | Concurrency bugs | Synchronize the underlying state |

## Best Practices

### Use Unpacking to Express Structure

Good:

```python
user_id, email = user_record
```

It communicates that the record contains two meaningful values.

### Use Named Variables

Prefer:

```python
user_id, email, active = row
```

over:

```python
a, b, c = row
```

Names preserve domain meaning.

### Use `strict=True` for Important `zip()` Invariants

```python
for user, profile in zip(
    users,
    profiles,
    strict=True,
):
    ...
```

### Avoid Materializing Large Iterables

Do not use starred unpacking when the remainder may be large.

### Validate External Mappings

Before:

```python
create_user(**payload)
```

ensure that the payload has the expected schema.

### Prefer Keyword Arguments for Important APIs

Instead of:

```python
create_client("db.example.com", 5432, 5, 3)
```

prefer:

```python
create_client(
    "db.example.com",
    port=5432,
    timeout=5,
    retries=3,
)
```

### Prefer Named Models as Structures Grow

Use:

- Dataclasses
- Pydantic models
- TypedDict
- Domain objects

when positional unpacking no longer communicates enough information.

## Practical Backend Example

Consider a service processing an order event:

```python
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderEvent:
    event_type: str
    order_id: int
    total: Decimal


def process_event(event: OrderEvent) -> None:
    event_type, order_id, total = (
        event.event_type,
        event.order_id,
        event.total,
    )

    if event_type == "order.created":
        process_created_order(
            order_id=order_id,
            total=total,
        )
```

The unpacking is appropriate because the values are already part of a typed domain model.

For a larger object, direct attributes may be clearer:

```python
def process_event(event: OrderEvent) -> None:
    if event.event_type == "order.created":
        process_created_order(
            order_id=event.order_id,
            total=event.total,
        )
```

The senior-level choice is not "always unpack"; it is to select the representation that communicates intent best.

## Practical API Forwarding Example

A service wrapper can use keyword expansion when the contract is deliberate:

```python
def create_order(
    *,
    customer_id: int,
    currency: str,
    amount: Decimal,
):
    ...


def create_order_from_payload(payload: dict):
    allowed = {
        "customer_id",
        "currency",
        "amount",
    }

    validated = {
        key: payload[key]
        for key in allowed
    }

    return create_order(**validated)
```

In production, a schema validator such as Pydantic is generally preferable to manually filtering arbitrary dictionaries.

## Unpacking in Data Pipelines

A streaming pipeline can combine unpacking with `enumerate()`:

```python
for index, record in enumerate(records):
    record_id, payload = record

    process_record(
        index=index,
        record_id=record_id,
        payload=payload,
    )
```

This is concise while preserving explicit variable names.

## Unpacking with `zip(strict=True)`

When synchronizing records:

```python
for user_id, email in zip(
    user_ids,
    emails,
    strict=True,
):
    persist_user(
        user_id=user_id,
        email=email,
    )
```

If the lengths differ, Python raises `ValueError` rather than silently dropping unmatched values.

This is often the safer behavior for ETL and backend processing.

## Unpacking Decision Guide

| Situation | Preferred approach |
|---|---|
| Fixed small tuple | Direct unpacking |
| Ignore one known value | `_` |
| Variable middle values | Starred unpacking |
| Huge iterable | Explicit iteration |
| Infinite iterable | Explicit incremental consumption |
| Dictionary key/value iteration | `.items()` + unpacking |
| Parallel iteration | `zip()` |
| Equal-length invariant | `zip(..., strict=True)` |
| Function argument forwarding | `*args` / `**kwargs` |
| Configuration merging | `**mapping` or `|` |
| Complex domain structure | Dataclass/model |
| External API payload | Validated model |
| Stable database tuple | Positional unpacking |
| Evolving public result | Named result type |

## Interview Traps

### What Is Unpacking?

Unpacking assigns values produced by an iterable or mapping structure to multiple targets.

### Does Unpacking Require a Tuple?

No.

Any iterable can generally be unpacked:

```python
a, b = [1, 2]
```

```python
a, b = iter([1, 2])
```

### What Happens if the Number of Values Does Not Match?

Without a starred target, Python raises `ValueError`.

### What Does `*rest` Do?

It collects the remaining values into a list.

### Is `*rest` Lazy?

No.

The remaining values must be consumed to construct the list.

### What Does `*` Mean in a Function Call?

It expands an iterable into positional arguments.

```python
function(*values)
```

### What Does `**` Mean in a Function Call?

It expands a mapping into keyword arguments.

```python
function(**values)
```

### What Does `*args` Mean in a Function Definition?

It collects extra positional arguments into a tuple.

### What Does `**kwargs` Mean?

It collects extra keyword arguments into a dictionary.

### Why Is `_` Used During Unpacking?

By convention, `_` indicates that the value is intentionally not needed.

It is still an ordinary variable.

### What Happens Here?

```python
a, *b, c = [1, 2, 3, 4]
```

The result is:

```python
a == 1
b == [2, 3]
c == 4
```

### What Happens Here?

```python
a, *b = [1]
```

The result is:

```python
a == 1
b == []
```

The starred target can receive zero values.

### Why Is This Dangerous?

```python
first, *rest = infinite_generator()
```

Because `rest` must contain all remaining values, the operation does not terminate.

### What Does `zip()` Produce?

It produces tuples containing corresponding values from its input iterables.

### Why Use `zip(..., strict=True)`?

It detects mismatched input lengths instead of silently stopping at the shortest iterable.

### Does Unpacking Create Copies?

It depends on the operation.

Normal assignment/unpacking binds references to produced objects. Starred unpacking creates a new list for the collected values. Container display unpacking creates a new container.

### Does Dictionary Unpacking Mutate the Original Dictionary?

No:

```python
merged = {**first, **second}
```

creates a new dictionary.

### What Happens with Duplicate Keys During Dictionary Construction?

Later values overwrite earlier values:

```python
result = {
    **{"x": 1},
    **{"x": 2},
}
```

produces:

```python
{"x": 2}
```

### Is `**mapping` in a Function Call the Same as Dictionary Merging?

No.

Dictionary unpacking creates/constructs a mapping:

```python
merged = {**a, **b}
```

Function keyword unpacking supplies named arguments:

```python
function(**mapping)
```

### Does Unpacking Provide Atomicity?

No.

Right-hand-side expressions can perform side effects before assignment completes.

### When Should You Prefer a Dataclass Over Unpacking?

When the data structure has multiple fields, domain meaning, validation requirements, or an API that is expected to evolve.

## Key Takeaways

- Python unpacking uses the iterable protocol to assign multiple values, while `*` and `**` additionally support positional and keyword argument expansion.
- Starred unpacking collects remaining values into a new list, so it can cause significant memory usage and must not be used casually with large or unbounded iterables.
- Use `enumerate()`, `zip()`, `.items()`, and structured return values with unpacking to make backend data-processing code concise and explicit; use `zip(..., strict=True)` when equal lengths are an invariant.
- Treat positional unpacking as part of an API contract; use dataclasses, Pydantic models, `TypedDict`, or other named structures when data is complex or expected to evolve.
- Unpacking is a language feature, not a concurrency, validation, or transactional mechanism; correctness still depends on the underlying data source, API contract, synchronization, and validation boundaries.