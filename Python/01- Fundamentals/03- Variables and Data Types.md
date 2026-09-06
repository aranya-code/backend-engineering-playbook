# 03- Variables and Data Types

## Overview

Python variables are names bound to objects. Unlike statically typed languages where a variable is typically associated with a declared type and storage location, Python names do not have a permanent type. The object referenced by a name has a type.

This distinction is fundamental to understanding Python behavior around assignment, mutability, function arguments, copying, equality, memory management, type hints, and concurrency.

Python's built-in data types provide the basic building blocks for application state, API payloads, configuration, database results, cache values, and messages flowing through backend systems.

A production engineer should understand not only which type to use, but also:

- How names bind to objects
- How assignment behaves
- The difference between identity and equality
- Mutable versus immutable objects
- Hashability and dictionary/set behavior
- Numeric and string semantics
- Collection characteristics
- `None` and absence of values
- Type conversion and validation
- Memory and performance implications
- Type hints versus runtime types
- Serialization boundaries
- Shared state across requests and workers

## Variables Are Name Bindings

Python variables are better understood as **names bound to objects** rather than containers that permanently hold values.

```python
user_id = 1001
```

Conceptually:

```text
user_id
   |
   v
+-----------+
| int       |
| 1001      |
+-----------+
```

The name `user_id` refers to an integer object.

Reassignment changes the binding:

```python
user_id = 1001
user_id = 2002
```

Conceptually:

```text
Before:

user_id ---> int(1001)


After:

user_id ---> int(2002)
```

The name itself does not have a fixed runtime type.

```python
value = 1001
value = "1001"
value = None
```

The same name can refer to objects of different types during execution.

## Names, Objects, and References

Consider:

```python
users = ["alice", "bob"]
```

The name `users` refers to a list object.

If another name is assigned from it:

```python
active_users = users
```

both names refer to the same object.

```text
users --------\
               \
                ---> ["alice", "bob"]
               /
active_users -/
```

Mutating through either name affects the same list:

```python
active_users.append("charlie")

print(users)
# ['alice', 'bob', 'charlie']
```

This is **aliasing**.

Aliasing is normal Python behavior, but unintended aliasing can cause difficult bugs when mutable objects are shared between application layers.

## Assignment Semantics

Python assignment generally performs name binding.

```python
a = 10
b = a
```

The assignment to `b` does not create a conceptual copy of the integer. Both names refer to an integer object representing the same value.

With immutable objects, this distinction is often invisible.

With mutable objects, it becomes significant:

```python
a = []
b = a

b.append(1)

print(a)
# [1]
```

If an independent collection is required, explicitly copy it:

```python
a = []
b = a.copy()

b.append(1)

print(a)
# []
```

For nested mutable structures, `copy()` performs a shallow copy. Deep copying is a separate operation and should be used carefully.

## Variable Scope

A name's visibility depends on its scope.

Python uses the LEGB resolution model:

```text
Local
  ↓
Enclosing
  ↓
Global
  ↓
Built-in
```

Example:

```python
timeout = 5


def create_client():
    timeout = 10

    def connect():
        return timeout

    return connect()
```

`connect()` resolves `timeout` from its enclosing function scope.

Scope affects:

- Name resolution
- Closures
- Configuration
- Dependency injection
- Global state
- Testing
- Concurrency

In backend services, minimizing mutable global state generally makes applications easier to test and reason about.

## Naming Conventions

Python follows established naming conventions.

| Element | Convention | Example |
|---|---|---|
| Variable | `snake_case` | `user_id` |
| Function | `snake_case` | `get_user()` |
| Constant | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| Class | `PascalCase` | `UserService` |
| Module | `snake_case` | `database.py` |
| Private/internal name | Leading underscore | `_connection` |

Examples:

```python
DEFAULT_TIMEOUT_SECONDS = 5
MAX_RETRY_ATTEMPTS = 3


def fetch_user(user_id: int):
    ...
```

Naming should communicate intent rather than implementation details.

Prefer:

```python
request_timeout = 5
```

over:

```python
x = 5
```

when the value has meaningful domain semantics.

## Dynamic Typing

Python is dynamically typed.

The runtime type belongs to the object:

```python
value = 42

print(type(value))
# <class 'int'>
```

A name can later reference another type:

```python
value = "42"

print(type(value))
# <class 'str'>
```

This provides flexibility but means incorrect values can reach runtime code unless they are validated.

Dynamic typing does not mean Python has no type system. Python has a well-defined runtime type system; it simply does not require most variable types to be declared statically.

## Type Hints

Modern Python supports type annotations:

```python
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity
```

Type hints improve:

- IDE support
- Static analysis
- Refactoring
- Documentation
- Code review
- API contracts

However, annotations generally do not enforce runtime behavior.

```python
def calculate_total(price: float, quantity: int) -> float:
    return price * quantity


result = calculate_total("100", 2)
```

Whether this fails depends on the operation performed. Python does not automatically reject the call merely because `price` was annotated as `float`.

For external boundaries such as REST APIs, runtime validation is still required.

## Runtime Type Checking

Python provides several mechanisms for runtime inspection.

```python
value = 42

if isinstance(value, int):
    print("integer")
```

Prefer `isinstance()` over comparing `type()` directly when subclass compatibility matters.

```python
if isinstance(value, int):
    ...
```

Instead of:

```python
if type(value) is int:
    ...
```

The latter requires the exact runtime type to be `int`.

Runtime checks are useful at boundaries, but excessive type checking inside well-typed internal code can make the design unnecessarily defensive.

## Built-in Data Types

Python's core built-in types can be grouped into several categories.

| Category | Types | Key Property |
|---|---|---|
| Boolean | `bool` | Logical values |
| Integer | `int` | Arbitrary-precision integers |
| Floating point | `float` | IEEE-style floating-point arithmetic |
| Complex | `complex` | Complex numbers |
| Text | `str` | Unicode text |
| Binary | `bytes`, `bytearray` | Binary data |
| Null | `NoneType` | Absence of a value |
| Sequence | `list`, `tuple`, `range` | Ordered data |
| Mapping | `dict` | Key-value associations |
| Set | `set`, `frozenset` | Unique elements |

The correct type depends on the required semantics rather than simply the data's apparent shape.

## `None`

`None` represents the absence of a value.

```python
middle_name = None
```

Its runtime type is `NoneType`:

```python
print(type(None))
# <class 'NoneType'>
```

Use identity comparison:

```python
if middle_name is None:
    ...
```

not:

```python
if middle_name == None:
    ...
```

`None` commonly appears in backend systems for:

- Optional database columns
- Missing configuration
- Absent HTTP fields
- Optional function parameters
- Cache misses
- Uninitialized application state

Do not automatically treat `None` as equivalent to every form of "empty".

These values have different semantics:

```python
None
""
[]
{}
0
False
```

A production API should distinguish between "missing", "empty", and "false" when those states have different business meanings.

## Boolean Type

Python's Boolean type has two values:

```python
True
False
```

Example:

```python
is_active = True
```

Booleans are commonly used for state and conditions.

Python also defines truth-value testing for many objects.

```python
if users:
    process(users)
```

An empty list is falsey:

```python
bool([])
# False
```

A non-empty list is truthy:

```python
bool(["alice"])
# True
```

Other common falsey values include:

- `None`
- `False`
- `0`
- `0.0`
- `""`
- Empty collections

Be careful when business logic distinguishes `None` from `False` or `0`.

For example:

```python
if retry_count:
    ...
```

does not distinguish zero from absence.

When that distinction matters, use explicit checks.

## Integers

Python's `int` represents integers with arbitrary precision.

```python
count = 1_000_000
```

Python does not expose the fixed-width integer overflow behavior commonly found in languages such as Java or C for ordinary `int` operations.

```python
value = 10**100

print(type(value))
# <class 'int'>
```

This is convenient but does not make arbitrarily large integers free.

Larger integers require more memory and computation.

For backend systems, integers are commonly used for:

- Database identifiers
- Counters
- Pagination offsets
- Quantities
- Unix timestamps
- Retry counts

Database-specific integer limits still apply when values cross a persistence boundary.

## Floating-Point Numbers

Python's `float` is typically a double-precision binary floating-point value in CPython.

Floating-point arithmetic can introduce representation errors.

```python
result = 0.1 + 0.2

print(result)
# 0.30000000000000004
```

Do not use binary floating-point for financial calculations where exact decimal semantics are required.

For monetary values, use `decimal.Decimal` when appropriate:

```python
from decimal import Decimal

price = Decimal("19.99")
quantity = Decimal("3")

total = price * quantity
```

For systems using PostgreSQL, database-level `NUMERIC`/`DECIMAL` types are often appropriate for exact monetary values, with consistent conversion rules at the application boundary.

## Decimal Values

`decimal.Decimal` provides decimal arithmetic with configurable precision.

```python
from decimal import Decimal

tax_rate = Decimal("0.18")
amount = Decimal("100.00")

tax = amount * tax_rate
```

Use it when decimal arithmetic matters.

Typical cases include:

- Financial amounts
- Tax calculations
- Accounting
- Currency-sensitive business logic

Do not convert through a binary float unnecessarily:

```python
from decimal import Decimal

# Avoid when exact decimal semantics are required.
value = Decimal(0.1)
```

Prefer:

```python
value = Decimal("0.1")
```

The string representation preserves the intended decimal value.

## Strings

`str` represents Unicode text.

```python
username = "aranya"
```

Strings are immutable.

```python
name = "alice"
name += " smith"
```

The operation creates a new string rather than modifying the original string object in place.

Strings are used extensively in backend applications:

- HTTP headers
- URLs
- JSON fields
- User input
- Database text
- Log messages
- Configuration values

When handling external text, encoding boundaries should be explicit where appropriate.

## Unicode and Encoding

Python `str` represents Unicode text, while `bytes` represents raw byte sequences.

```python
text = "café"
data = text.encode("utf-8")

print(type(text))
# <class 'str'>

print(type(data))
# <class 'bytes'>
```

The reverse operation is decoding:

```python
decoded = data.decode("utf-8")
```

The distinction matters at system boundaries such as:

```text
HTTP
  |
  v
Bytes
  |
  v
Decode
  |
  v
Python str
  |
  v
Application Logic
```

Incorrect encoding assumptions can produce corrupted text or decoding failures.

Modern backend applications should normally use UTF-8 consistently unless an external protocol specifies another encoding.

## Bytes

`bytes` represents immutable binary data.

```python
payload = b"hello"
```

Bytes are commonly used for:

- Network protocols
- File contents
- Cryptographic operations
- Encoded payloads
- Compression
- Binary serialization

Do not treat bytes and strings as interchangeable.

```python
text = "hello"
payload = b"hello"

print(text == payload)
# False
```

Explicit encoding and decoding makes boundaries clear.

## Bytearray

`bytearray` provides mutable binary data.

```python
buffer = bytearray(b"hello")
buffer[0] = ord("H")
```

It is useful when binary data needs in-place modification.

It is less commonly required in high-level backend application code than `bytes`.

## Lists

Lists are ordered, mutable sequences.

```python
orders = ["order-1", "order-2"]
orders.append("order-3")
```

Common operations include:

```python
orders.append(order)
orders.extend(more_orders)
orders.remove(order)
first = orders[0]
```

Lists are appropriate when:

- Order matters
- Duplicates are allowed
- Mutation is useful
- Index-based access is needed

List membership is generally linear:

```python
if order_id in order_ids:
    ...
```

For large collections where membership checks dominate, a `set` may be more appropriate.

## Tuples

Tuples are ordered sequences that are immutable.

```python
coordinates = (12.5, 42.7)
```

They are useful when:

- Values represent a fixed grouping
- Immutability is desirable
- A hashable composite value is needed
- Data should not be modified after construction

A tuple can still contain mutable objects:

```python
value = ([1, 2], 3)
```

The tuple itself cannot be modified, but the list inside it can.

This is an important distinction when discussing immutability.

## Sets

Sets store unique hashable elements.

```python
permissions = {"read", "write", "delete"}
```

Membership testing is generally efficient:

```python
if "write" in permissions:
    ...
```

Sets are useful for:

- Deduplication
- Membership tests
- Set operations
- Permission checks
- Tracking unique identifiers

Example:

```python
requested_permissions = {"read", "write"}
allowed_permissions = {"read", "write", "admin"}

if requested_permissions <= allowed_permissions:
    authorize()
```

Sets do not provide an API contract around meaningful positional ordering.

Do not use a set when deterministic sequence order is part of the business requirement.

## Dictionaries

Dictionaries map hashable keys to values.

```python
user = {
    "id": 1001,
    "name": "Alice",
    "active": True,
}
```

Dictionary lookup is generally expected to be efficient.

Dictionaries are heavily used for:

- JSON-like data
- Configuration
- Lookup tables
- Request metadata
- Cache entries
- Serialization boundaries

Python dictionaries preserve insertion order as part of the language specification in modern Python.

However, ordering should only be relied upon when it is semantically appropriate.

## Hashability

Dictionary keys and set elements must be hashable.

Common hashable types include:

- `int`
- `str`
- `float`
- `bytes`
- `tuple` containing hashable elements
- `frozenset`

Lists and dictionaries are not hashable.

```python
lookup = {}

lookup["user-1001"] = "Alice"
```

This works because strings are hashable.

The following does not:

```python
lookup = {}

lookup[["user", "1001"]] = "Alice"
```

because lists are mutable and unhashable.

Hashability matters because dictionaries and sets rely on hash-based lookup.

## Equality and Identity

Python provides two different concepts:

- `==` tests equality
- `is` tests identity

Example:

```python
a = [1, 2, 3]
b = [1, 2, 3]

print(a == b)
# True

print(a is b)
# False
```

Use `is` for singleton identity checks such as `None`:

```python
if value is None:
    ...
```

Use `==` when comparing values:

```python
if status == "active":
    ...
```

Confusing the two can produce subtle production bugs.

## Mutable vs Immutable Types

| Type | Mutable | Hashable |
|---|---:|---:|
| `int` | No | Yes |
| `float` | No | Yes |
| `str` | No | Yes |
| `bytes` | No | Yes |
| `tuple` | No* | Yes* |
| `frozenset` | No | Yes |
| `list` | Yes | No |
| `dict` | Yes | No |
| `set` | Yes | No |
| `bytearray` | Yes | No |

\* A tuple or frozenset is hashable only when all required contained elements are hashable.

Immutability provides useful guarantees but does not automatically make an application thread-safe or free from shared-state problems.

## Mutable Default Arguments

A classic Python mistake involves mutable default arguments.

Avoid:

```python
def add_tag(tag: str, tags: list[str] = []) -> list[str]:
    tags.append(tag)
    return tags
```

The default list is created once when the function is defined, not once per function call.

Prefer:

```python
def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []

    tags.append(tag)
    return tags
```

This ensures each call without an explicit list gets a new list.

## Type Conversion

Python provides explicit conversion functions:

```python
user_id = int("1001")
price = float("19.99")
name = str(1001)
```

Conversion can fail:

```python
int("abc")
```

raises `ValueError`.

External data should be validated rather than blindly converted.

For example, API input should be processed through a validation layer before entering business logic.

Frameworks such as FastAPI can use type annotations and validation models to enforce API contracts at the boundary.

## Truthiness

Python objects have truth-value semantics.

Examples:

```python
bool(None)      # False
bool(False)     # False
bool(0)         # False
bool("")        # False
bool([])        # False
bool({})        # False
bool([1])       # True
```

This is useful for concise conditions:

```python
if not orders:
    return
```

However, truthiness can hide semantic differences.

Avoid:

```python
if not user_id:
    ...
```

if `0` could be a valid identifier but `None` means missing.

Prefer:

```python
if user_id is None:
    ...
```

when absence is the actual condition.

## Collection Selection

Choosing the right collection is a design decision.

| Requirement | Recommended Type |
|---|---|
| Ordered mutable collection | `list` |
| Fixed immutable sequence | `tuple` |
| Unique values | `set` |
| Immutable unique values | `frozenset` |
| Key-value lookup | `dict` |
| Lazy numeric sequence | `range` |
| Text | `str` |
| Binary data | `bytes` |
| Mutable binary buffer | `bytearray` |

Do not automatically use lists for every collection.

For example:

```python
allowed_roles = {"admin", "operator", "viewer"}
```

is more appropriate than:

```python
allowed_roles = ["admin", "operator", "viewer"]
```

when the primary operation is membership testing and duplicates are meaningless.

## Data Types at Backend Boundaries

Python types frequently represent data crossing system boundaries.

A typical API request might follow:

```text
HTTP JSON
   |
   v
Raw Request Data
   |
   v
Validation
   |
   v
Python Types
   |
   v
Domain Logic
   |
   v
Database / Queue
```

For example:

```json
{
  "user_id": 1001,
  "active": true,
  "roles": ["admin", "operator"]
}
```

can be represented internally as:

```python
user_id: int
active: bool
roles: list[str]
```

The application should validate incoming data before trusting these assumptions.

## Database Type Mapping

Python types often map to database types, but the mapping is not always one-to-one.

| Python | PostgreSQL Example |
|---|---|
| `int` | `INTEGER`, `BIGINT` |
| `float` | `DOUBLE PRECISION` |
| `Decimal` | `NUMERIC` |
| `str` | `TEXT`, `VARCHAR` |
| `bool` | `BOOLEAN` |
| `datetime` | `TIMESTAMP`, `TIMESTAMPTZ` |
| `date` | `DATE` |
| `bytes` | `BYTEA` |
| `None` | `NULL` |
| `list` / `dict` | `JSONB` when modeled as JSON |

Database schema semantics remain authoritative at the persistence boundary.

For example, a Python `int` does not imply that every possible Python integer can fit into a PostgreSQL `INTEGER`.

## JSON Serialization

JSON has a much smaller type system than Python.

JSON supports:

```text
object
array
string
number
boolean
null
```

Python has additional types such as:

- `set`
- `bytes`
- `Decimal`
- `datetime`
- Custom classes

These require explicit serialization strategies.

For example:

```python
import json

payload = {
    "user_id": 1001,
    "active": True,
    "roles": ["admin"],
}

encoded = json.dumps(payload)
```

The Python-to-JSON boundary should be explicit in production systems.

Do not assume every Python object can be serialized directly.

## Datetimes and Time Zones

Date and time handling deserves special care in backend systems.

Python provides:

```python
from datetime import datetime
```

For timezone-aware timestamps, prefer aware datetimes:

```python
from datetime import datetime, timezone

created_at = datetime.now(timezone.utc)
```

Avoid treating naive local timestamps as globally meaningful.

Distributed systems commonly operate across:

- Multiple regions
- Multiple containers
- Multiple time zones
- Different client locales

Persisting and communicating timestamps in UTC is generally a robust backend convention, while converting to user-local time at presentation boundaries.

## Type Aliasing and Domain Meaning

Two values may have the same Python type but different business meaning.

```python
user_id: int
order_id: int
```

Both are integers, but they represent different domain concepts.

Type hints can improve readability:

```python
UserId = int
OrderId = int
```

For stronger domain modeling, dedicated value objects or typing constructs can provide additional separation.

This becomes particularly useful in large systems where accidental interchange of identifiers can produce valid but incorrect database queries.

## Memory Considerations

Every Python object carries runtime overhead beyond its logical value.

A simple value:

```python
user_id = 1001
```

is represented by a Python object managed by the runtime.

A large collection can therefore consume substantially more memory than the equivalent packed binary representation.

This matters when processing:

- Millions of database rows
- Large CSV files
- Kafka messages
- Large API payloads
- Batch workloads

Avoid unnecessary materialization:

```python
records = list(load_records())
```

when streaming is sufficient.

Prefer bounded processing:

```python
for record in load_records():
    process(record)
```

For data-intensive workloads, specialized structures such as NumPy arrays may provide substantially better memory efficiency for homogeneous numerical data.

## Performance Considerations

Different data types have different operational costs.

Typical characteristics:

| Operation | `list` | `set` | `dict` |
|---|---:|---:|---:|
| Index access | Fast | N/A | N/A |
| Membership | O(n) typical | O(1) average | O(1) average |
| Key lookup | N/A | N/A | O(1) average |
| Append | O(1) amortized | N/A | N/A |
| Insert at front | O(n) | N/A | N/A |

These are general complexity characteristics, not latency guarantees.

For high-volume services, data structure selection can have a much larger impact than micro-optimizing individual Python statements.

## Copying Objects

Assignment does not copy objects.

For mutable structures, use explicit copying when independent state is required.

### Shallow Copy

```python
original = {
    "roles": ["admin"]
}

copy = original.copy()
```

The outer dictionary is copied, but nested objects remain shared.

```text
original ----\
              ---> roles list
copy --------/
```

### Deep Copy

`copy.deepcopy()` recursively copies supported nested objects.

```python
from copy import deepcopy

copy = deepcopy(original)
```

Deep copying can be expensive and can have surprising behavior for complex object graphs.

In production code, prefer explicit construction of the required data structure when practical rather than using deep copying as a general state-management strategy.

## Variables in Concurrent Applications

Mutable objects can become shared state.

With threads:

```text
Thread A ----\
              ---> Shared Object
Thread B ----/
```

Concurrent mutation can create race conditions.

This is especially relevant for:

- In-memory caches
- Counters
- Shared dictionaries
- Connection state
- Worker coordination

Process-based deployments are different:

```text
Process A ---> Memory A
Process B ---> Memory B
Process C ---> Memory C
```

The memory is separate.

Therefore, a variable stored in one worker is not automatically visible to another worker.

For distributed state, use appropriate external systems such as Redis or PostgreSQL.

## Production Example

Consider an order-processing service:

```python
from decimal import Decimal
from datetime import datetime, timezone


order = {
    "id": 1001,
    "customer_id": 5001,
    "total": Decimal("149.99"),
    "currency": "USD",
    "paid": True,
    "created_at": datetime.now(timezone.utc),
    "items": [
        {
            "product_id": 9001,
            "quantity": 2,
        }
    ],
}
```

Different Python types communicate different semantics:

| Field | Type | Reason |
|---|---|---|
| `id` | `int` | Identifier |
| `customer_id` | `int` | Identifier |
| `total` | `Decimal` | Exact monetary arithmetic |
| `currency` | `str` | Text/code |
| `paid` | `bool` | State |
| `created_at` | `datetime` | Timestamp |
| `items` | `list` | Ordered collection |
| Item fields | `dict` | Structured data |

In a larger application, this raw dictionary would often be replaced with a typed model or domain object.

## Security Considerations

Type handling can become a security boundary.

Never assume that external data has the expected type.

Potential sources include:

- HTTP requests
- Query parameters
- Headers
- JSON payloads
- Environment variables
- Message queues
- Files
- Database records
- User-controlled configuration

Validate external input before using it in sensitive operations.

Examples include validating:

- Identifier types
- Numeric ranges
- String lengths
- Enum values
- Timestamp formats
- Collection sizes
- Nested object structure

Type hints alone are not sufficient input validation.

## Common Mistakes

### Confusing Names With Objects

Incorrect mental model:

> `user` is the object.

More accurately:

> `user` is a name bound to an object.

This distinction explains aliasing and assignment behavior.

### Using `is` for Value Comparison

Avoid:

```python
if status is "active":
    ...
```

Use:

```python
if status == "active":
    ...
```

Use `is` primarily for identity checks such as:

```python
if value is None:
    ...
```

### Using Floating Point for Money

Avoid:

```python
total = 0.1 + 0.2
```

for exact monetary calculations.

Prefer `Decimal` or an integer representation of the smallest currency unit where appropriate.

### Using Lists for Large Membership Checks

Avoid repeatedly performing:

```python
if user_id in user_ids:
    ...
```

when `user_ids` is a large list and membership testing dominates the workload.

Use a set when uniqueness and membership are the actual requirements.

### Treating `None` and Falsey Values as Equivalent

Avoid:

```python
if not value:
    handle_missing()
```

when `0`, `False`, or `""` are legitimate values.

Use explicit checks when semantics matter.

### Assuming `.copy()` Is Deep

This:

```python
copy = original.copy()
```

does not recursively copy nested objects.

Understand the object graph before choosing a copying strategy.

### Using Mutable Defaults

Mutable default arguments persist across calls.

Use `None` as the default and initialize the mutable object inside the function.

### Ignoring Memory Costs

A Python list of millions of objects can consume significant memory.

Use streaming, batching, database-side processing, or specialized data structures when the workload requires it.

### Trusting Type Hints at Runtime

Annotations do not automatically validate external input.

Use runtime validation at system boundaries.

## Interview Traps

### Is Python Pass-by-Value or Pass-by-Reference?

Neither description is sufficiently precise.

Python uses object-reference semantics commonly described as **call-by-sharing**.

A function receives references to objects, and rebinding a parameter does not rebind the caller's variable.

```python
def replace(items):
    items = ["new"]


values = ["old"]

replace(values)

print(values)
# ['old']
```

But mutation of the referenced object is visible:

```python
def mutate(items):
    items.append("new")


values = ["old"]

mutate(values)

print(values)
# ['old', 'new']
```

The distinction between rebinding and mutation is the key concept.

### Why Is a Tuple Immutable If It Contains a List?

The tuple's structure is immutable, but the objects referenced by its elements may be mutable.

```python
value = ([1, 2], 3)

value[0].append(4)
```

This is valid because the tuple still references the same list object.

### Why Can a Dictionary Use a Tuple as a Key but Not a List?

Dictionary keys must be hashable.

A tuple is hashable when all of its elements are hashable.

A list is mutable and therefore unhashable.

### Why Does `0.1 + 0.2` Not Equal Exactly `0.3`?

Binary floating-point cannot represent many decimal fractions exactly.

The resulting value is therefore an approximation.

Use decimal arithmetic when exact decimal semantics are required.

## Best Practices

For production Python applications:

- Use descriptive `snake_case` names.
- Treat variables as names bound to objects.
- Understand whether objects are mutable before sharing them.
- Use `is None` for `None` checks.
- Use `==` for value comparison.
- Choose collections according to access patterns and semantics.
- Use `set` for efficient membership and uniqueness.
- Use `dict` for key-based lookup.
- Use `Decimal` or integer minor units for exact monetary calculations.
- Use timezone-aware datetimes for distributed applications.
- Validate external input at system boundaries.
- Use type hints and static analysis for maintainability.
- Avoid mutable default arguments.
- Avoid unnecessary deep copies.
- Stream large datasets instead of materializing everything in memory.
- Avoid process-local state when state must be shared across workers.
- Measure performance before changing data structures solely for optimization.

## Key Takeaways

- Python variables are names bound to objects; assignment normally changes bindings rather than copying objects.
- Mutability, identity, equality, and hashability determine how Python objects behave when shared, copied, stored in dictionaries, or used across application boundaries.
- Choose built-in data types according to semantics and access patterns: `list` for ordered collections, `set` for uniqueness and membership, `dict` for key-based lookup, and immutable types when appropriate.
- Type hints improve maintainability and static analysis but do not replace runtime validation of external API, database, queue, or configuration data.
- Backend reliability and performance depend on correct type selection, explicit handling of `None`, memory-aware collection usage, precise numeric semantics, and disciplined management of shared mutable state.