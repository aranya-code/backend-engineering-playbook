# 14- Dunder Methods

## Overview

Dunder methods, short for **double-underscore methods**, are special methods recognized by Python's data model. They use names such as `__init__`, `__repr__`, `__eq__`, `__hash__`, `__iter__`, `__enter__`, and `__call__`.

They allow user-defined classes to participate in Python's built-in language protocols and operators.

For example:

```python
class Money:
    def __init__(self, amount: int, currency: str) -> None:
        self.amount = amount
        self.currency = currency

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currencies must match")

        return Money(
            self.amount + other.amount,
            self.currency,
        )
```

Now Python can evaluate:

```python
total = Money(100, "USD") + Money(50, "USD")
```

The `+` operator is implemented through the class's special method:

```python
__add__
```

Dunder methods are therefore not merely syntactic conveniences. They are the mechanism through which custom objects integrate with Python's object model.

In backend engineering, they are particularly useful for:

- Domain models
- Value objects
- Collections
- Context managers
- Iterators
- Async resources
- Serialization
- Logging and debugging
- Equality and hashing
- Testing
- Framework integration

## What Are Dunder Methods?

A dunder method is a specially named method whose name begins and ends with two underscores:

```text
__name__
```

Examples:

| Dunder method | Python behavior |
|---|---|
| `__init__` | Object initialization |
| `__new__` | Object creation |
| `__repr__` | Developer-oriented representation |
| `__str__` | Human-readable representation |
| `__eq__` | Equality comparison |
| `__hash__` | Hash calculation |
| `__lt__` | Less-than comparison |
| `__len__` | `len(obj)` |
| `__bool__` | Truth-value testing |
| `__iter__` | Iteration |
| `__next__` | Next iterator item |
| `__contains__` | Membership testing |
| `__getitem__` | Subscription/indexing |
| `__setitem__` | Item assignment |
| `__delitem__` | Item deletion |
| `__call__` | Calling an object |
| `__enter__` | Synchronous context manager entry |
| `__exit__` | Synchronous context manager exit |
| `__aenter__` | Async context manager entry |
| `__aexit__` | Async context manager exit |
| `__await__` | Awaitable behavior |

Python invokes these methods through language operations.

For example:

```python
len(order)
```

conceptually delegates to:

```python
order.__len__()
```

The exact interpreter implementation is more specialized than a normal attribute lookup, but the data-model relationship is the important abstraction.

## Why Dunder Methods Exist

Without dunder methods, custom classes would remain largely disconnected from Python's built-in protocols.

Compare:

```python
if order.is_empty():
    ...
```

with:

```python
if not order:
    ...
```

The second form allows the object to participate naturally in Python's truth-value protocol through:

```python
__bool__
```

Similarly:

```python
len(batch)
```

uses:

```python
__len__
```

and:

```python
for item in batch:
    ...
```

uses the iteration protocol.

Dunder methods allow classes to expose **standard Python semantics** instead of inventing custom APIs for every operation.

## Dunder Methods and Python's Data Model

Python's data model defines protocols that objects can implement.

```text
                 Python Operation
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
      len(x)          x + y           x == y
        |               |               |
        v               v               v
    __len__          __add__         __eq__
        |
        v
     Custom Object
```

This protocol-oriented design is one of Python's most important object-oriented features.

Instead of asking:

```text
"What class is this?"
```

Python often asks:

```text
"Does this object support the operation I need?"
```

That principle is closely related to duck typing and protocols.

## Object Lifecycle Dunder Methods

The most important lifecycle methods are:

```python
__new__
__init__
__del__
```

They have very different responsibilities.

### `__new__`

`__new__` creates the object.

```python
class User:
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        return instance
```

It is a class-level creation hook.

### `__init__`

`__init__` initializes an already-created object.

```python
class User:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
```

The normal lifecycle is conceptually:

```text
Class(...)
   |
   v
__new__()
   |
   v
Object allocated
   |
   v
__init__()
   |
   v
Initialized object
```

`__new__` is primarily needed for advanced object creation patterns such as immutable subclasses, caching, or metaprogramming.

### `__del__`

`__del__` is a finalization hook.

It should generally not be used for critical resource management.

```python
class Resource:
    def __del__(self):
        ...
```

Garbage collection, interpreter shutdown, reference cycles, and exception behavior make deterministic cleanup inappropriate for important resources.

Prefer:

```python
with resource:
    ...
```

using `__enter__` and `__exit__`.

## `__repr__`

`__repr__` should provide a useful developer-oriented representation.

```python
class Order:
    def __init__(self, order_id: int, status: str) -> None:
        self.order_id = order_id
        self.status = status

    def __repr__(self) -> str:
        return (
            f"Order("
            f"order_id={self.order_id!r}, "
            f"status={self.status!r}"
            f")"
        )
```

Now:

```python
order = Order(123, "paid")
print(repr(order))
```

produces something like:

```text
Order(order_id=123, status='paid')
```

A good `__repr__` helps with:

- Debugging
- Logs
- Interactive development
- Test failures
- Tracebacks
- Operational diagnostics

### `__repr__` Production Considerations

Never expose secrets:

```python
class Credentials:
    def __repr__(self) -> str:
        return "Credentials(password=***)"
```

Avoid including:

- Passwords
- API keys
- Access tokens
- Session identifiers
- Sensitive personal information
- Large payloads

A useful representation should be informative without creating a data-leak vector.

## `__str__`

`__str__` provides a human-readable representation.

```python
class Order:
    def __init__(self, order_id: int, status: str) -> None:
        self.order_id = order_id
        self.status = status

    def __str__(self) -> str:
        return f"Order #{self.order_id} ({self.status})"
```

Python generally uses `__str__` for:

```python
str(order)
```

and:

```python
print(order)
```

If `__str__` is not implemented, Python can fall back to `__repr__`.

### `__repr__` vs `__str__`

| Method | Audience | Typical purpose |
|---|---|---|
| `__repr__` | Developers | Debugging and diagnostics |
| `__str__` | Users/operators | Human-readable output |

For backend domain objects, `__repr__` is usually more important than a highly customized `__str__`.

## `__eq__`

`__eq__` defines equality semantics.

```python
class UserId:
    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserId):
            return NotImplemented

        return self.value == other.value
```

Now:

```python
UserId(10) == UserId(10)
```

returns:

```python
True
```

### Return `NotImplemented` When Appropriate

Prefer:

```python
if not isinstance(other, UserId):
    return NotImplemented
```

instead of:

```python
return False
```

`NotImplemented` tells Python that this implementation does not know how to compare the operands, allowing Python to attempt the reflected comparison where appropriate.

This distinction matters when implementing interoperable types.

## Equality and Domain Modeling

Value objects commonly implement equality by value.

```python
class EmailAddress:
    def __init__(self, value: str) -> None:
        self.value = value.lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmailAddress):
            return NotImplemented

        return self.value == other.value
```

Then:

```python
EmailAddress("USER@example.com") == EmailAddress("user@example.com")
```

is true.

This can be useful for domain concepts such as:

- User IDs
- Currency amounts
- Coordinates
- Email addresses
- Version numbers
- Date ranges

The equality contract should reflect the domain rather than merely comparing all instance attributes.

## `__ne__`

`__ne__` defines `!=`.

```python
def __ne__(self, other: object) -> bool:
    result = self.__eq__(other)

    if result is NotImplemented:
        return NotImplemented

    return not result
```

Modern Python often does not require explicitly defining `__ne__` because the interpreter can derive inequality from equality.

Implement it only when the semantics genuinely differ.

## Ordering Comparisons

Python supports dunder methods for ordering:

```text
__lt__  <
__le__  <=
__gt__  >
__ge__  >=
```

Example:

```python
class Priority:
    def __init__(self, value: int) -> None:
        self.value = value

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Priority):
            return NotImplemented

        return self.value < other.value
```

Then:

```python
Priority(1) < Priority(5)
```

works naturally.

For related comparison methods, `functools.total_ordering` can reduce implementation effort, although explicit methods or dataclass ordering may be preferable when performance and exact semantics matter.

## `__hash__`

`__hash__` determines the hash used by hash-based collections such as:

```python
dict
set
```

Example:

```python
class UserId:
    def __init__(self, value: int) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserId):
            return NotImplemented

        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)
```

Now:

```python
user_ids = {UserId(10)}
```

works.

### Hash Contract

If:

```python
a == b
```

then:

```python
hash(a) == hash(b)
```

must be true.

The reverse is not required:

```python
hash(a) == hash(b)
```

does not imply:

```python
a == b
```

because hash collisions are possible.

### Mutable Hashable Objects

Avoid hashing objects whose equality-defining state can change.

Bad design:

```python
class User:
    def __hash__(self):
        return hash(self.email)
```

if:

```python
user.email
```

can change after insertion into a set.

This can make the object effectively unreachable in the hash table.

Immutable value objects are usually safer candidates for hashing.

## `__len__`

`__len__` enables:

```python
len(obj)
```

Example:

```python
class Batch:
    def __init__(self, items: list[str]) -> None:
        self.items = items

    def __len__(self) -> int:
        return len(self.items)
```

The return value must be a non-negative integer.

Python may also use `__len__` for truth-value testing when `__bool__` is not defined.

## `__bool__`

`__bool__` controls truth-value testing.

```python
class ResultSet:
    def __init__(self, items: list[str]) -> None:
        self.items = items

    def __bool__(self) -> bool:
        return bool(self.items)
```

Now:

```python
if result_set:
    ...
```

reflects whether the collection contains items.

Use this carefully for domain objects.

For example, an HTTP response object should not necessarily become false simply because its payload is empty. Truthiness should represent a clear and unsurprising semantic.

## `__iter__`

`__iter__` makes an object iterable.

```python
class OrderBatch:
    def __init__(self, orders: list[int]) -> None:
        self.orders = orders

    def __iter__(self):
        return iter(self.orders)
```

Now:

```python
for order_id in batch:
    ...
```

works naturally.

A container's `__iter__` should normally return an iterator.

## `__next__`

`__next__` implements the iterator protocol.

```python
class Counter:
    def __init__(self, limit: int) -> None:
        self.current = 0
        self.limit = limit

    def __iter__(self):
        return self

    def __next__(self) -> int:
        if self.current >= self.limit:
            raise StopIteration

        value = self.current
        self.current += 1
        return value
```

Then:

```python
for value in Counter(3):
    print(value)
```

produces:

```text
0
1
2
```

In production code, generators are often simpler when custom iterator state is not itself part of the design.

## `__contains__`

`__contains__` supports:

```python
item in container
```

Example:

```python
class AllowedRoles:
    def __init__(self, roles: set[str]) -> None:
        self.roles = roles

    def __contains__(self, role: str) -> bool:
        return role in self.roles
```

This allows:

```python
if "admin" in allowed_roles:
    ...
```

For security-sensitive membership checks, ensure the underlying comparison semantics are appropriate. Do not assume `__contains__` provides constant-time or side-channel-resistant comparison.

## `__getitem__`

`__getitem__` enables indexing and subscription.

```python
class OrderBatch:
    def __init__(self, orders: list[int]) -> None:
        self.orders = orders

    def __getitem__(self, index: int) -> int:
        return self.orders[index]
```

Now:

```python
batch[0]
```

works.

It can also support slices:

```python
def __getitem__(self, index):
    return self.orders[index]
```

Python passes either an integer or a `slice` object.

## `__setitem__` and `__delitem__`

These support:

```python
container[index] = value
del container[index]
```

Example:

```python
class Config:
    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def __getitem__(self, key: str) -> str:
        return self._values[key]

    def __setitem__(self, key: str, value: str) -> None:
        self._values[key] = value

    def __delitem__(self, key: str) -> None:
        del self._values[key]
```

This can make custom configuration or collection objects integrate naturally with Python syntax.

## `__call__`

`__call__` makes an instance callable.

```python
class RetryPolicy:
    def __init__(self, max_attempts: int) -> None:
        self.max_attempts = max_attempts

    def __call__(self, attempt: int) -> bool:
        return attempt < self.max_attempts
```

Now:

```python
policy = RetryPolicy(max_attempts=3)

if policy(2):
    ...
```

Callable objects are useful for:

- Strategies
- Validators
- Policies
- Dependency providers
- Adapters
- Stateful callbacks

They can be especially useful when behavior requires configuration or state.

## `__enter__` and `__exit__`

These implement synchronous context managers.

```python
class DatabaseTransaction:
    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

        return False
```

Usage:

```python
with DatabaseTransaction():
    create_order()
```

The lifecycle is conceptually:

```text
with resource:
    |
    v
__enter__()
    |
    v
Body executes
    |
    +---- success ----> __exit__(None, None, None)
    |
    +---- exception --> __exit__(exception details)
```

Returning `True` from `__exit__` suppresses the exception. This should be done only intentionally.

## `__aenter__` and `__aexit__`

Async context managers use:

```python
__aenter__
__aexit__
```

Example:

```python
class AsyncConnection:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
        return False
```

Usage:

```python
async with AsyncConnection() as connection:
    await connection.execute(...)
```

This pattern is common for:

- Async database connections
- HTTP clients
- Distributed locks
- Resource pools
- Async transactions

## `__await__`

An object can implement `__await__` to become awaitable.

```python
class DeferredResult:
    def __await__(self):
        return self._future.__await__()
```

Then:

```python
result = await deferred
```

works.

This is an advanced protocol. Most application code should use `async def` and standard awaitable objects rather than implementing `__await__` manually.

## `__aenter__` vs `__await__`

These protocols solve different problems.

| Protocol | Syntax | Purpose |
|---|---|---|
| `__await__` | `await obj` | Await a result |
| `__aenter__` | `async with obj` | Enter async resource scope |
| `__aexit__` | `async with obj` | Exit async resource scope |

Do not confuse an awaitable resource with an async context manager.

## Arithmetic Operators

Dunder methods can implement arithmetic operators:

```text
__add__       +
__sub__       -
__mul__       *
__truediv__   /
__floordiv__  //
__mod__       %
__pow__       **
```

Example:

```python
class Money:
    def __init__(self, amount: int, currency: str) -> None:
        self.amount = amount
        self.currency = currency

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")

        return Money(
            self.amount + other.amount,
            self.currency,
        )
```

For domain value objects, operator overloading should reflect obvious mathematical or domain semantics.

Do not overload operators merely because Python permits it.

## Reflected Operators

Python supports reflected arithmetic methods such as:

```text
__radd__
__rsub__
__rmul__
```

For example:

```python
class Score:
    def __init__(self, value: int) -> None:
        self.value = value

    def __radd__(self, other: int) -> int:
        return other + self.value
```

This can allow:

```python
10 + Score(5)
```

to work.

Operator interoperability should be designed carefully when custom types interact with built-in types.

## In-Place Operators

Methods such as:

```text
__iadd__
__isub__
__imul__
```

support augmented assignment:

```python
x += y
```

Example:

```python
class Counter:
    def __init__(self, value: int = 0) -> None:
        self.value = value

    def __iadd__(self, amount: int):
        self.value += amount
        return self
```

The semantics of in-place operations should be clear about whether the object is mutated or a new object is returned.

This distinction matters especially for immutable value objects.

## Attribute Access Dunder Methods

Python provides several hooks for attribute behavior:

```text
__getattr__
__getattribute__
__setattr__
__delattr__
```

### `__getattr__`

Called when normal attribute lookup fails.

```python
class Config:
    def __getattr__(self, name: str):
        raise AttributeError(
            f"Unknown configuration key: {name}"
        )
```

`__getattr__` is often useful for controlled fallback behavior.

### `__getattribute__`

Called for virtually every attribute access.

```python
class Traced:
    def __getattribute__(self, name):
        print(f"accessing {name}")
        return super().__getattribute__(name)
```

This is powerful but easy to break.

Avoid overriding it unless the use case genuinely requires interception of all attribute access.

### `__setattr__`

Intercepts assignment:

```python
class Validated:
    def __setattr__(self, name, value):
        if name == "age" and value < 0:
            raise ValueError("age cannot be negative")

        super().__setattr__(name, value)
```

For normal validation, properties or explicit validation methods are often clearer.

### `__delattr__`

Controls:

```python
del obj.attribute
```

It is less commonly required in application code.

## `__slots__`

`__slots__` is a class-level declaration that can restrict instance attributes and potentially reduce per-instance memory usage.

```python
class UserId:
    __slots__ = ("value",)

    def __init__(self, value: int) -> None:
        self.value = value
```

It is not itself a dunder method, but it interacts closely with Python's object model.

Use it deliberately, particularly for large numbers of lightweight objects.

Consider implications for:

- Inheritance
- Pickling
- Weak references
- Dynamic attributes
- Framework behavior

## Serialization-Related Dunder Methods

Objects can participate in serialization protocols through methods such as:

```text
__getstate__
__setstate__
__reduce__
__reduce_ex__
```

These are relevant to Python's pickle protocol.

Example:

```python
class Connection:
    def __getstate__(self):
        state = self.__dict__.copy()
        state.pop("socket", None)
        return state
```

This can prevent non-serializable resources from being included.

### Security Warning

Never unpickle untrusted data.

Python pickle is capable of executing arbitrary code during deserialization. Dunder methods such as `__reduce__` are one reason pickle is powerful and security-sensitive.

For external APIs, queues, files, and untrusted payloads, prefer explicit formats such as:

- JSON
- MessagePack with appropriate controls
- Protobuf
- Avro
- Validated application-specific schemas

## `__copy__` and `__deepcopy__`

Custom copy behavior can be implemented with:

```text
__copy__
__deepcopy__
```

These methods matter when objects contain resources or complex state.

For example, a database connection should generally not be duplicated simply because its owning object is copied.

Prefer explicit copy semantics for resource-owning objects.

## Dunder Methods and Dataclasses

Dataclasses generate several methods automatically.

```python
from dataclasses import dataclass


@dataclass
class UserId:
    value: int
```

Depending on configuration, Python can generate methods such as:

- `__init__`
- `__repr__`
- `__eq__`

For example:

```python
user_id = UserId(42)

print(user_id)
```

produces a useful representation automatically.

Configuration such as:

```python
@dataclass(
    frozen=True,
    slots=True,
)
class UserId:
    value: int
```

can create an immutable, slot-based value object with appropriate generated behavior.

Understand what the dataclass decorator generates before overriding individual dunder methods.

## Dunder Methods and Hashability

Dataclasses have important equality/hash interactions.

For example:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class UserId:
    value: int
```

A frozen dataclass can safely be hashable when its equality-defining fields are hashable.

By contrast, mutable equality-based objects should not generally be made hashable.

The rule is:

```text
Equality-defining state must remain stable while hashable.
```

## Dunder Methods and Backend Domain Models

Dunder methods are particularly valuable for value objects.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    amount: int
    currency: str

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")

        return Money(
            self.amount + other.amount,
            self.currency,
        )
```

Application code becomes:

```python
subtotal = Money(1000, "USD")
shipping = Money(150, "USD")

total = subtotal + shipping
```

This is often clearer than:

```python
total = Money(
    amount=subtotal.amount + shipping.amount,
    currency=subtotal.currency,
)
```

provided the operator semantics are obvious and domain-correct.

## Dunder Methods and ORM Models

ORM classes often already have framework-defined behavior.

For example, Django models have meaningful representations, equality semantics, and lifecycle behavior.

Before overriding a dunder method on a framework-managed object:

1. Read the framework contract.
2. Understand what the base implementation does.
3. Check whether `super()` is required.
4. Test interactions with persistence and identity.
5. Verify behavior across unsaved and persisted instances.

Do not override `__eq__` or `__hash__` on ORM entities casually. Persistence identity and domain equality are not always the same thing.

## Dunder Methods and REST APIs

Dunder methods should generally remain an internal Python concern.

For example:

```python
class Order:
    def __repr__(self) -> str:
        return f"Order(id={self.id!r})"
```

does not mean an API response should be generated from:

```python
repr(order)
```

REST serialization should use explicit schemas.

For FastAPI:

```python
from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: int
    status: str
```

This separates:

```text
Python object representation
```

from:

```text
External API contract
```

That separation is important for compatibility and security.

## Dunder Methods and Logging

Avoid using arbitrary `str()` or `repr()` output as a structured logging schema.

Prefer:

```python
logger.info(
    "order_processed",
    extra={
        "order_id": order.id,
        "status": order.status,
    },
)
```

rather than relying on:

```python
logger.info("order=%r", order)
```

for important operational fields.

`__repr__` is excellent for debugging but should not become an accidental API or observability contract.

## Dunder Methods and Testing

Dunder methods should be tested like any other public behavior.

For a value object:

```python
def test_money_addition():
    first = Money(100, "USD")
    second = Money(50, "USD")

    assert first + second == Money(150, "USD")
```

For equality:

```python
def test_user_id_equality():
    assert UserId(1) == UserId(1)
    assert UserId(1) != UserId(2)
```

For hashing:

```python
def test_user_id_hash_contract():
    first = UserId(1)
    second = UserId(1)

    assert first == second
    assert hash(first) == hash(second)
```

For context managers:

```python
def test_transaction_rolls_back_on_error():
    with pytest.raises(RuntimeError):
        with transaction():
            raise RuntimeError("failure")
```

Test the semantic contract rather than merely checking that a method exists.

## Performance Considerations

Dunder methods are part of Python's normal object protocol, so their execution occurs in application code and can appear on hot paths.

Potentially high-frequency operations include:

```python
__eq__
__hash__
__getitem__
__iter__
__len__
```

For large collections, expensive equality or hashing can materially affect performance.

For example:

```python
class UserId:
    def __hash__(self):
        return expensive_database_lookup(self.value)
```

would be a serious design error.

Hashing and equality should normally be:

- Deterministic
- Fast
- Side-effect free
- Independent of network I/O
- Independent of database I/O

## Dunder Methods Must Not Perform I/O

Avoid:

```python
class Order:
    def __repr__(self):
        customer = load_customer_from_database(self.customer_id)
        return f"Order(customer={customer.name})"
```

A simple debugging operation could unexpectedly trigger PostgreSQL traffic.

This becomes especially dangerous in:

- Logging
- Error handling
- Debuggers
- Test failures
- Admin interfaces
- Monitoring

Dunder methods should generally operate on already-available in-memory state.

## Avoid Hidden Side Effects

Operations such as:

```python
str(obj)
repr(obj)
len(obj)
obj == other
hash(obj)
```

should have predictable behavior.

Avoid side effects such as:

- Database writes
- Network calls
- Message publication
- Cache mutation
- Global state mutation
- Expensive computation
- Locks unless absolutely necessary

Python developers reasonably expect these operations to be lightweight and observational.

## Concurrency Considerations

Dunder methods may execute implicitly from many parts of an application.

For example:

```python
obj in collection
```

may invoke equality or membership logic without making the operation visually obvious.

If the implementation mutates shared state:

```python
def __eq__(self, other):
    self.comparison_count += 1
    ...
```

the object may require synchronization under concurrent use.

Prefer stateless implementations.

For async applications, do not perform blocking I/O from dunder methods called in an event-loop context.

## Security Considerations

Dunder methods can become security-sensitive when they influence:

- Serialization
- Authorization objects
- Logging
- Error reporting
- Configuration
- Dynamic attribute access

Important rules:

- Never deserialize untrusted pickle data.
- Never expose secrets through `__repr__` or `__str__`.
- Do not perform authorization checks implicitly through equality or truthiness.
- Avoid dynamic attribute hooks that bypass normal validation.
- Keep security-sensitive behavior explicit.

Security decisions should be visible in application code rather than hidden inside surprising Python protocols.

## Reliability and Observability

Dunder methods frequently run during failure handling.

For example:

```python
logger.exception("failed order=%r", order)
```

may invoke:

```python
order.__repr__()
```

If `__repr__` itself raises an exception, diagnostics become harder.

A production-safe `__repr__` should therefore be:

- Deterministic
- Cheap
- Side-effect free
- Defensive about optional state
- Safe for logging

Avoid representations that depend on resources that may already be unavailable during failure handling.

## Common Mistakes

### Implementing Every Possible Dunder Method

Do not implement methods simply because Python provides them.

Only implement protocols that improve the object's semantics.

### Confusing `__str__` and `__repr__`

Use:

```text
__repr__ -> developer diagnostics
__str__  -> human-readable presentation
```

### Returning the Wrong Type

For example, `__len__` must return a non-negative integer.

Protocol methods have specific contracts.

### Incorrect Equality

Comparing unrelated objects without a clear contract can create surprising behavior.

### Incorrect Hashing

If equality changes but hashing does not reflect the same identity semantics, dictionaries and sets can behave incorrectly.

### Hashing Mutable State

Never rely on mutable fields for the hash of an object that can change while inside a set or dictionary.

### Performing I/O

Dunder methods should not unexpectedly query PostgreSQL, Redis, Kafka, HTTP services, or files.

### Leaking Secrets

A password or access token accidentally included in `__repr__` can enter logs.

### Overriding `__getattribute__` Unnecessarily

It is powerful and easy to make recursive lookup bugs.

### Using `__del__` for Cleanup

Garbage collection is not a deterministic resource-management mechanism.

Use context managers or explicit lifecycle methods.

### Overloading Operators Unnaturally

Do not make:

```python
user_a + user_b
```

mean something arbitrary just because it is syntactically possible.

Operator semantics should be intuitive.

## Production Pitfalls

| Pitfall | Consequence | Better Approach |
|---|---|---|
| Secret data in `__repr__` | Credential leakage | Redact sensitive fields |
| Database access in `__str__` | Hidden latency/I/O | Use explicit queries |
| Mutable hash state | Broken sets/dicts | Use immutable identity |
| Incorrect `__eq__` | Unexpected comparisons | Define domain equality explicitly |
| Missing `NotImplemented` | Poor interoperability | Return `NotImplemented` for unsupported types |
| `__del__` for resources | Non-deterministic cleanup | Use context managers |
| Complex `__getattribute__` | Recursive lookup bugs | Prefer simpler hooks |
| Arbitrary operator overloads | Unclear APIs | Use intuitive semantics |
| Serialization through pickle | Remote code execution risk | Use explicit safe formats |
| Dunder methods with side effects | Surprising behavior | Keep them deterministic |
| Heavy `__repr__` | Slow logs/debugging | Keep representations cheap |

## Dunder Methods and Protocol Design

A senior Python design approach treats dunder methods as **protocol implementations**.

Instead of asking:

```text
"Which dunder methods should this class have?"
```

ask:

```text
"Which Python protocols should this object participate in?"
```

For example:

| Requirement | Protocol |
|---|---|
| Object has a meaningful size | `__len__` |
| Object can be iterated | `__iter__` |
| Object supports indexing | `__getitem__` |
| Object supports membership | `__contains__` |
| Object has domain equality | `__eq__` |
| Object is safely hashable | `__hash__` |
| Object represents a resource scope | `__enter__` / `__exit__` |
| Object is asynchronously scoped | `__aenter__` / `__aexit__` |
| Object acts like a strategy | `__call__` |
| Object supports arithmetic | Relevant arithmetic dunders |

This produces more deliberate designs.

## Dunder Methods vs Explicit Methods

Dunder methods should be preferred when the operation naturally maps to an existing Python protocol.

Use:

```python
len(batch)
```

rather than:

```python
batch.size()
```

when `batch` genuinely behaves like a collection.

Use an explicit method when the operation is domain-specific:

```python
order.cancel()
```

rather than trying to invent:

```python
order - cancellation
```

A useful rule is:

> Use dunder methods for language-level semantics and explicit methods for business-level commands.

## Dunder Methods and Immutability

Dunder methods work particularly well with immutable value objects.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrencyAmount:
    value: int
    currency: str

    def __add__(self, other: "CurrencyAmount"):
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")

        return CurrencyAmount(
            self.value + other.value,
            self.currency,
        )
```

Instead of mutating:

```python
amount.value += 10
```

the operator returns a new object.

This makes equality, hashing, caching, concurrency, and reasoning about state significantly easier.

## Dunder Methods and Distributed Systems

Dunder methods execute locally inside a Python process.

They should not be used to hide distributed-system operations.

Bad:

```python
def __eq__(self, other):
    return fetch_remote_order(self.id) == fetch_remote_order(other.id)
```

This creates:

```text
Python equality
      |
      v
Network call
      |
      v
Remote service
```

A simple:

```python
order_a == order_b
```

could now fail because of:

- Network latency
- Service outages
- Timeouts
- Authentication failures
- Retry behavior

Distributed operations should be explicit:

```python
await order_service.compare_orders(...)
```

## Dunder Methods and Microservices

Keep dunder methods local to the service process.

For example:

```python
class PaymentId:
    def __eq__(self, other):
        ...
```

is appropriate.

But:

```python
class Payment:
    def __eq__(self, other):
        # Calls payment service over gRPC
        ...
```

is not.

A service boundary should be explicit and observable.

## Dunder Methods and API Contracts

Do not expose Python's dunder semantics as external API contracts.

For example, this is fragile:

```python
return JSONResponse(content=order.__dict__)
```

because internal object structure becomes coupled to the API.

Prefer explicit schemas:

```python
class OrderResponse(BaseModel):
    id: int
    status: str
    total: int
```

Dunder methods integrate an object with Python. They should not replace API schema design.

## Interview Traps

### Is `__init__` the constructor?

Strictly speaking, no.

`__new__` creates the instance and `__init__` initializes it.

### Does `len(obj)` always call `obj.__len__()` directly?

Conceptually it invokes the length protocol, but special-method lookup is handled by Python's type machinery rather than ordinary instance attribute lookup.

This distinction matters because assigning:

```python
obj.__len__ = custom_function
```

does not generally change how:

```python
len(obj)
```

dispatches.

### Why does `__hash__` sometimes become `None`?

When a class overrides equality without providing a compatible hash implementation, Python can make the class unhashable to prevent unsafe use in sets and dictionaries.

### Why return `NotImplemented`?

It signals that the operation is unsupported for the given operand type and allows Python to try the reflected operation where applicable.

### Why should `__repr__` be cheap?

It is commonly invoked during logging, debugging, exceptions, and interactive inspection, including failure paths.

### Can `__del__` guarantee cleanup?

No. It is not a reliable replacement for deterministic resource management.

## Production Checklist

Before implementing or reviewing dunder methods:

- The method corresponds to a real Python protocol.
- The semantic behavior is intuitive.
- The protocol contract is understood.
- Equality and hashing are consistent.
- Hashable objects use stable equality-defining state.
- `NotImplemented` is returned for unsupported comparisons where appropriate.
- `__repr__` is concise and safe for logs.
- Sensitive information is redacted.
- Dunder methods do not perform unexpected I/O.
- Dunder methods avoid hidden side effects.
- Resource cleanup uses context managers rather than relying on `__del__`.
- Serialization hooks are treated as security-sensitive.
- Framework-managed classes are reviewed before overriding dunders.
- Performance is appropriate for potentially high-frequency operations.
- Tests cover the observable protocol behavior.
- Explicit domain methods are used when an operation is not naturally a Python language semantic.

## Key Takeaways

- Dunder methods implement Python's data-model protocols, allowing custom objects to participate naturally in operations such as comparison, iteration, indexing, context management, and arithmetic.
- Implement dunder methods when they express intuitive language-level semantics; use explicit methods for domain-specific business operations.
- Equality and hashing must remain consistent, and hashable objects should not derive their hash from mutable equality-defining state.
- Production dunder methods should be deterministic, lightweight, side-effect free, and safe for logging; avoid hidden database/network I/O and sensitive-data leakage.
- Advanced dunder methods such as `__getattribute__`, `__reduce__`, `__await__`, and `__del__` require particular care because they can affect correctness, security, lifecycle management, or runtime behavior.