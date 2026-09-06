# 03- Identity Equality Hashing

## Overview

Python provides three related but distinct concepts for reasoning about objects:

- **Identity** — whether two references point to the same object.
- **Equality** — whether two objects represent equivalent values.
- **Hashing** — whether an object can produce a stable hash value suitable for hash-based collections such as `dict` and `set`.

These concepts are closely connected but are not interchangeable.

```python
a = [1, 2, 3]
b = [1, 2, 3]
c = a

assert a == b
assert a is not b

assert a is c
assert a == c
```

Here:

```text
a ───────┐
         ├────► list [1, 2, 3]
c ───────┘

b ─────────────► list [1, 2, 3]
```

`a` and `b` are equal but have different identities. `a` and `c` are the same object.

Hashing adds another layer:

```python
lookup = {"user-42": "Alice"}
```

Dictionary lookup depends on hashing and equality to locate keys efficiently.

Understanding these semantics is essential for:

- dictionaries and sets;
- caching;
- deduplication;
- database identity;
- ORM entities;
- immutable value objects;
- dataclasses;
- memoization;
- API and domain modeling;
- performance;
- concurrent systems.

---

## Identity

### What Identity Means

Object identity answers:

> Are these two references pointing to the exact same object?

Python exposes identity comparison through `is`.

```python
a = []
b = a
c = []

assert a is b
assert a is not c
```

Identity is about the object's existence as a particular runtime object, not its contents.

---

## `is` vs `==`

The distinction is fundamental:

| Expression | Meaning |
|---|---|
| `a is b` | Same object |
| `a == b` | Equal according to equality semantics |
| `hash(a)` | Hash value, if the object is hashable |

Example:

```python
a = {"id": 42}
b = {"id": 42}

print(a is b)  # False
print(a == b)  # True
```

The objects have equivalent contents but are different objects.

---

## When Identity Matters

Identity is useful when the distinction between "this exact object" and "an equivalent value" matters.

Typical examples include:

- checking for `None`;
- sentinel objects;
- object lifecycle management;
- certain caching or interning mechanisms;
- detecting aliases;
- identity-based registries.

Canonical Python usage:

```python
if value is None:
    return
```

Avoid:

```python
if value == None:
    return
```

`is None` expresses the intended singleton identity check directly.

---

## Sentinel Objects

A unique sentinel can distinguish "not supplied" from a legitimate value such as `None`.

```python
_MISSING = object()


def get_value(value: object = _MISSING) -> object:
    if value is _MISSING:
        return "default"

    return value
```

Because each `object()` creates a unique object:

```python
_MISSING is object()
```

is always false.

This pattern is useful in APIs where:

```text
argument omitted
        ≠
argument explicitly set to None
```

---

## `id()`

Python exposes an object's identity through `id()`:

```python
user = {"id": 42}

print(id(user))
```

For CPython, `id()` is typically related to the object's memory address, but Python only guarantees that it is a unique integer identifying the object during its lifetime.

Do not write production logic that assumes `id()` is a physical memory address.

Also note that object IDs can be reused after an object is destroyed.

---

## Identity Lifetime

An object's identity is stable for the object's lifetime.

```python
value = []

first = id(value)
second = id(value)

assert first == second
```

After the object is destroyed, its identity value may eventually be reused by another object.

Therefore:

```python
id(a) == id(b)
```

should not be treated as a permanent globally unique identifier.

For application-level identity, use explicit identifiers such as:

- UUIDs;
- database primary keys;
- domain IDs.

---

## Equality

Equality answers:

> Should these two objects be considered equivalent in value or meaning?

Python uses `==` for equality.

```python
a = [1, 2, 3]
b = [1, 2, 3]

assert a == b
```

Lists compare their elements.

Dictionaries compare their key-value contents.

Strings compare their character sequences.

Custom classes can define their own equality semantics.

---

## Equality Is Type-Specific

Different types implement equality differently.

```python
[1, 2] == [1, 2]
```

is true because lists compare their elements.

```python
{"id": 1} == {"id": 1}
```

is true because dictionaries compare their mappings.

Custom domain objects require explicit design decisions about what constitutes equality.

---

## Defining Equality in Custom Classes

A class can implement `__eq__()`:

```python
class User:
    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.user_id == other.user_id
```

Now:

```python
a = User(42, "alice@example.com")
b = User(42, "different@example.com")

assert a == b
```

This design says that `user_id` defines equality.

Whether that is correct depends on the domain.

---

## `NotImplemented`

When implementing rich comparison methods, returning `NotImplemented` is generally preferable when the other operand is not a supported type.

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, User):
        return NotImplemented

    return self.user_id == other.user_id
```

`NotImplemented` tells Python that this implementation does not know how to compare the operands.

It is different from returning:

```python
False
```

because Python may attempt the reflected comparison behavior of the other operand.

---

## Equality Contracts

Well-designed equality should behave predictably.

Important properties include:

### Reflexivity

For normal equality semantics:

```text
a == a
```

should generally be true.

### Symmetry

Ideally:

```text
a == b
```

and:

```text
b == a
```

should agree.

### Transitivity

If:

```text
a == b
b == c
```

then normally:

```text
a == c
```

should also hold.

Poorly designed custom equality can violate these expectations and produce difficult collection and caching bugs.

---

## Equality and Mutability

Mutable objects can change their equality relationship over time.

```python
user = User(42, "alice@example.com")
```

If equality depends on mutable fields and those fields change, the object's relationship to other objects can change.

This becomes especially dangerous when hashing is involved.

---

## Hashing

A hash is an integer derived from an object:

```python
value = hash("alice")
```

Hashing exists primarily to support efficient hash-based collections:

- `dict`;
- `set`;
- `frozenset`.

Conceptually:

```text
key
 ↓
hash(key)
 ↓
hash-table location
 ↓
candidate entries
 ↓
equality comparison
```

Hashing narrows the search space. Equality ultimately determines whether a candidate key is actually the requested key.

---

## Hashable Objects

An object is hashable when it has a hash value that remains stable during its lifetime and can participate correctly in equality comparisons.

Typical hashable types include:

- `int`;
- `str`;
- `bytes`;
- `frozenset` when its elements are hashable;
- tuples containing only hashable elements;
- many immutable user-defined objects.

Typical unhashable types include:

- `list`;
- `dict`;
- `set`.

For example:

```python
hash("user-42")
```

works.

But:

```python
hash(["user-42"])
```

raises:

```text
TypeError: unhashable type: 'list'
```

---

## Why Lists Are Unhashable

A list is mutable:

```python
values = [1, 2]
```

If lists were safely usable as dictionary keys, mutating the list after insertion could change its logical identity while the dictionary still stores it in its original hash bucket.

Python therefore prevents ordinary mutable containers such as lists and dictionaries from being hashable.

---

## Hash Contract

The most important hashing rule is:

> If `a == b`, then `hash(a) == hash(b)` must be true.

The reverse is not required.

Two different objects may have the same hash:

```text
a ──► hash 123
b ──► hash 123

a != b
```

This is a **hash collision**.

Hash tables handle collisions through additional lookup logic, including equality comparisons.

---

## Hash Collisions

A collision occurs when:

```python
hash(a) == hash(b)
```

but:

```python
a != b
```

Collisions are expected and must be handled correctly by hash-based collections.

Therefore, hashing is not a replacement for equality.

Conceptually:

```text
dictionary lookup
       │
       ▼
    hash(key)
       │
       ▼
candidate bucket
       │
       ▼
 equality checks
       │
       ▼
matching key
```

---

## Dictionary Lookup

Consider:

```python
users = {
    "user-42": "Alice",
}
```

A lookup:

```python
users["user-42"]
```

conceptually involves:

```text
"user-42"
    │
    ▼
hash("user-42")
    │
    ▼
hash-table lookup
    │
    ▼
candidate key
    │
    ▼
equality verification
    │
    ▼
"Alice"
```

This is why dictionary lookup is typically approximately O(1) on average.

It is not a mathematical guarantee that every lookup is constant time under all conditions.

---

## Set Membership

Sets use the same fundamental model.

```python
allowed_roles = {"reader", "writer", "admin"}

if role in allowed_roles:
    ...
```

The set hashes the candidate value and uses equality as necessary to determine membership.

For large collections of hashable values, this is generally much more efficient than scanning a list.

```python
role in roles_list
```

is typically O(n), while:

```python
role in roles_set
```

is typically O(1) on average.

---

## Hashing and Performance

Hash-based collections provide fast average-case lookup, but performance depends on:

- hash quality;
- collision behavior;
- table size;
- resizing;
- object creation;
- equality comparison cost.

A pathological hash function can degrade lookup performance.

Custom classes should therefore avoid simplistic or low-quality hash implementations.

---

## Defining `__hash__`

A class can define a hash function:

```python
class User:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.user_id == other.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)
```

Now:

```python
a = User(42)
b = User(42)

assert a == b
assert hash(a) == hash(b)
```

This is valid only if `user_id` remains stable while the object is used as a hash key.

---

## Mutable Hash Keys

This is a critical production pitfall.

Consider:

```python
class User:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def __hash__(self) -> int:
        return hash(self.user_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.user_id == other.user_id
```

Now:

```python
user = User(42)
users = {user}

user.user_id = 99
```

The object has changed its hash.

The set still contains the object in the location determined by the old hash.

This can cause:

```python
user in users
```

to produce unexpected results.

The object can effectively become difficult to find inside the collection.

---

## Rule for Hashable Objects

A practical rule is:

> Any state participating in equality and hashing must remain stable while the object is stored in a `dict` or `set`.

The safest design is usually:

```text
immutable equality fields
        +
stable hash
        =
safe hashable object
```

This is why immutable value objects are strong candidates for dictionary keys and set members.

---

## Equality and Hashing Must Agree

Bad design:

```python
class User:
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.user_id == other.user_id

    def __hash__(self) -> int:
        return hash(self.email)
```

Two objects can compare equal through `user_id` but produce different hashes through `email`.

That violates the hash contract.

The implementation should derive both from the same logical identity:

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, User):
        return NotImplemented

    return self.user_id == other.user_id

def __hash__(self) -> int:
    return hash(self.user_id)
```

---

## `__eq__()` and Automatic Hash Behavior

Python protects against a common mistake.

If a class defines `__eq__()` but does not provide a compatible `__hash__()`, Python commonly makes instances unhashable by setting:

```python
__hash__ = None
```

For example:

```python
class User:
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.user_id == other.user_id
```

Then:

```python
hash(User())
```

will generally fail.

This behavior prevents accidentally using mutable equality-based objects as dictionary keys or set members.

---

## `object.__hash__`

A normal user-defined class that does not override equality inherits identity-based hashing from `object`.

Conceptually:

```text
identity-based equality
        +
identity-based hash
```

This is appropriate when object identity, rather than value, defines equality.

Once value-based equality is introduced, hash behavior must be reconsidered.

---

## Dataclasses

Dataclasses make equality and hashing behavior configurable.

For example:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class UserId:
    value: int
```

A frozen dataclass is a natural candidate for a value object.

```python
a = UserId(42)
b = UserId(42)

assert a == b
assert hash(a) == hash(b)
```

The immutability helps keep the hash stable.

---

## Dataclass Hashing Matrix

The exact behavior depends on `eq`, `frozen`, and `unsafe_hash`.

A useful high-level model is:

| `eq` | `frozen` | Typical generated hash behavior |
|---:|---:|---|
| `False` | `False` | Preserve inherited hashing behavior |
| `True` | `False` | Generally unhashable |
| `True` | `True` | Generate a hash |
| `False` | `True` | Preserve inherited hashing behavior |

`unsafe_hash=True` can explicitly request hash generation, but it should be used only when the equality/hash contract is genuinely safe.

---

## Frozen Does Not Mean Deeply Immutable

This is still dangerous:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    roles: list[str]
```

The attribute cannot normally be rebound:

```python
user.roles = []
```

but the nested list can still mutate:

```python
user.roles.append("admin")
```

If `roles` participates in equality or hashing, this can create serious correctness problems.

Prefer immutable fields when the object is intended to be hashable:

```python
@dataclass(frozen=True)
class User:
    roles: tuple[str, ...]
```

---

## Value Objects

Value objects are particularly well suited to equality-based semantics.

Examples:

- `UserId`;
- `Money`;
- `EmailAddress`;
- `Coordinates`;
- `DateRange`;
- `Currency`;
- `Pagination`.

For example:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class UserId:
    value: int
```

Two instances with the same value represent the same logical value:

```python
UserId(42) == UserId(42)
```

They can also safely participate in sets and dictionaries.

---

## Entity Identity vs Value Equality

Backend systems often distinguish **entities** from **value objects**.

An entity usually has stable domain identity:

```text
User ID = 42
```

while a value object is defined by its value:

```text
Money(100, "USD")
```

Two users with the same name are not necessarily the same user.

Two `Money(100, "USD")` values generally represent equivalent values.

This distinction should influence `__eq__()` and `__hash__()` design.

---

## ORM Identity

Django ORM objects represent database entities.

```python
user = User.objects.get(pk=42)
```

Application-level identity should generally be based on the primary key or domain identity rather than Python's `is`.

Two separately loaded objects can represent the same database row:

```text
Python object A ──► database row 42
Python object B ──► database row 42
```

They may not be the same Python object.

Do not use:

```python
user_a is user_b
```

to determine whether two ORM objects represent the same database entity.

Use explicit domain/database identity.

---

## Database Identity vs Python Equality

A Python object's equality semantics do not automatically correspond to database identity.

For example, a domain object might define:

```python
user_a == user_b
```

based on `user_id`.

Another model might define equality based on a combination of business attributes.

Therefore, establish the identity rules explicitly rather than assuming that Python's default behavior matches the database.

---

## Caching

Identity, equality, and hashing are directly relevant to application caches.

A dictionary-based cache:

```python
cache: dict[UserId, bytes] = {}
```

requires `UserId` to be hashable.

```python
cache[UserId(42)] = b"..."
```

Later:

```python
payload = cache.get(UserId(42))
```

works because the newly created `UserId(42)` is equal to the original key and has the same hash.

This is one of the major benefits of value-object semantics.

---

## Memoization

Caching decorators such as `functools.lru_cache` rely on arguments being suitable as cache keys.

For example:

```python
from functools import lru_cache


@lru_cache(maxsize=1024)
def calculate_discount(user_id: int) -> float:
    ...
```

`user_id` is hashable, so it can participate in the cache key.

Using mutable, unhashable arguments directly is not possible.

This means API and service method design can affect whether memoization is practical.

---

## Security Considerations

Hash-based collections are performance-critical infrastructure.

Poor hashing behavior can create excessive collisions and degrade performance.

Python protects string and bytes hashing against certain adversarial collision attacks through hash randomization.

The value of:

```python
hash("example")
```

may therefore differ between Python processes.

Do not persist Python hash values as durable identifiers.

Do not use:

```python
hash(value)
```

as a cryptographic digest or security token.

Use dedicated cryptographic primitives such as SHA-256 when cryptographic hashing is actually required.

---

## Python Hash Randomization

For certain built-in types, especially strings and bytes, Python uses a per-process randomized hash seed.

This means:

```bash
python -c "print(hash('user-42'))"
```

and another process may produce different values.

This is intentional.

Therefore:

- do not persist `hash()` values in databases;
- do not use them as cache keys shared between processes;
- do not use them as stable partition identifiers;
- do not use them for cryptographic purposes.

For stable application hashing, define an explicit serialization and hashing scheme.

---

## Distributed Systems

Python's built-in `hash()` is not appropriate for distributed partitioning when stable results are required across processes or deployments.

For example, this is unsafe as a Kafka partitioning scheme if stable cross-process behavior is required:

```python
partition = hash(user_id) % partition_count
```

Instead, use a deterministic hash algorithm over a canonical representation.

For example:

```python
import hashlib


def stable_hash(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")
```

The exact partitioning strategy should also account for partition-count changes and compatibility requirements.

---

## Equality and Serialization

Serialization does not preserve Python identity.

```text
Python object
    ↓
JSON / protobuf / message
    ↓
network
    ↓
new object
```

After deserialization:

```python
original is restored
```

is normally false.

Value equality may still hold:

```python
original == restored
```

depending on the model.

This distinction is important in REST, gRPC, Kafka, Redis, and Celery workflows.

---

## Equality Across API Boundaries

Suppose a REST API returns:

```json
{
  "id": 42,
  "name": "Alice"
}
```

The client reconstructs its own object.

The client object and server object have separate identities.

A distributed system should therefore use explicit identifiers and serialized values rather than relying on runtime object identity.

---

## Performance Considerations

Hashing is normally efficient, but custom objects can make hashing expensive.

Avoid unnecessarily complex hash computations such as repeatedly hashing large nested structures during high-frequency lookups.

Prefer stable compact identity fields when they correctly represent the object's equality semantics:

```python
def __hash__(self) -> int:
    return hash(self.user_id)
```

rather than hashing an entire large object graph.

However, correctness always takes precedence over micro-optimizing hash computation.

---

## Equality Performance

Equality checks can become expensive when objects contain large structures.

For example:

```python
large_a == large_b
```

may require comparing many elements.

Hash tables usually avoid unnecessary equality comparisons by first comparing hashes, but collisions and hash-table behavior can still require equality checks.

Design domain objects so equality reflects meaningful identity or value semantics rather than blindly comparing large mutable structures.

---

## Hashability Decision Framework

Before making a custom object hashable, ask:

1. What defines equality?
2. Is that state immutable while the object is used as a key?
3. Can two equal objects produce the same hash?
4. Can the object safely participate in sets and dictionaries?
5. Does the object represent a value or an entity?
6. Is identity-based hashing actually sufficient?
7. Would a dedicated immutable value object be clearer?

If these questions cannot be answered confidently, do not add `__hash__()` merely to make `set()` or `dict` accept the object.

---

## Identity, Equality, and Hashing Comparison

| Property | Identity | Equality | Hashing |
|---|---|---|---|
| Operator/API | `is` | `==` | `hash()` |
| Question | Same object? | Same value/meaning? | Hash representation? |
| Customizable | Generally no | `__eq__()` | `__hash__()` |
| Used by `dict` | Indirectly | Yes | Yes |
| Used by `set` | Indirectly | Yes | Yes |
| Requires immutability | No | No | For participating state, effectively yes |
| Suitable for DB identity | Usually no | Sometimes | No |
| Suitable for cryptography | No | No | No |

---

## Practical Example: Domain Key

A production-oriented domain identifier can be modeled as an immutable value object:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserId:
    value: int


user_id = UserId(42)

permissions = {
    user_id: {"read", "write"},
}

assert permissions[UserId(42)] == {"read", "write"}
```

The important properties are:

- value-based equality;
- stable hashing;
- immutable identity;
- compact representation;
- explicit domain semantics.

This is generally preferable to using arbitrary mutable objects as dictionary keys.

---

## Practical Example: Avoid Mutable Hash Identity

Avoid:

```python
class User:
    def __init__(self, email: str) -> None:
        self.email = email

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.email == other.email

    def __hash__(self) -> int:
        return hash(self.email)
```

if `email` can change after insertion into a set or dictionary.

Prefer an immutable identifier:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserKey:
    user_id: int
```

Use mutable entities as mutable entities and immutable keys as keys.

---

## Common Mistakes

### Using `is` for Strings

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

String interning can make incorrect identity comparisons appear to work in some situations.

### Implementing `__eq__()` Without Considering Hashing

If equality changes from identity-based to value-based, hashing semantics must be reconsidered.

### Hashing Mutable Fields

A hash must remain stable while the object is used as a dictionary key or set member.

### Using `hash()` as a Persistent ID

Python hash values are not designed to be stable across processes or versions.

### Using `hash()` for Cryptography

Python's built-in hash is not a cryptographic hash function.

### Confusing Database Identity with Python Identity

Two ORM instances can represent the same database row without being the same Python object.

### Making Every Domain Object Hashable

Hashability is a semantic contract, not a convenience feature.

### Returning Inconsistent Hashes

If:

```python
a == b
```

then:

```python
hash(a) == hash(b)
```

must hold.

### Using Large Mutable Structures as Equality Identity

This can make equality expensive and unstable.

Prefer explicit domain identity where appropriate.

---

## Production Pitfalls

### Mutable Dictionary Keys

This can create keys that become effectively unreachable.

```python
mapping[key] = value

key.mutable_field = new_value
```

If the field participates in hashing, the dictionary may no longer locate the key correctly.

### Unstable Cache Keys

Using objects whose equality or hashing semantics change over time can corrupt logical cache behavior.

### Cross-Process Hash Assumptions

A Python hash value may differ between processes.

Do not use it as a distributed identifier without a deliberate deterministic hashing strategy.

### Incorrect ORM Comparisons

Checking:

```python
obj_a is obj_b
```

is generally the wrong way to compare database entities.

### Equality With Side Effects

`__eq__()` should normally be deterministic and free of external side effects.

Do not perform database calls, network requests, logging-heavy operations, or mutable global state changes inside equality logic.

---

## Testing Equality and Hashing

Custom value objects should have explicit tests.

```python
def test_user_id_equality_and_hash() -> None:
    first = UserId(42)
    second = UserId(42)
    third = UserId(99)

    assert first == second
    assert first != third
    assert hash(first) == hash(second)

    values = {first}
    assert second in values
    assert third not in values
```

Also test immutability when required:

```python
def test_user_id_is_immutable() -> None:
    user_id = UserId(42)

    try:
        user_id.value = 99
    except AttributeError:
        pass
    else:
        raise AssertionError("UserId must be immutable")
```

For dataclasses, pytest-based tests should normally be preferred in a modern testing stack.

---

## Property-Based Testing

For complex equality and hashing implementations, property-based testing can verify invariants over many generated values.

Important properties include:

```text
a == b  →  hash(a) == hash(b)

a == a

equality is symmetric

equality is transitive
```

Property-based testing can be particularly useful for:

- composite value objects;
- normalized identifiers;
- custom collection keys;
- parsing and serialization models.

---

## Concurrency Considerations

Hashability does not automatically make an object thread-safe.

An immutable hashable object can be safely shared more easily:

```text
Thread A ───┐
            ├──► immutable value
Thread B ───┘
```

A mutable hashable object is dangerous because concurrent mutation can invalidate assumptions about equality and hashing.

Therefore:

> Hash stability and thread safety are separate concerns.

Even immutable Python objects do not automatically make an entire application operation thread-safe.

---

## Reliability and High Availability

Hash-based in-memory structures are local process state.

For example:

```python
cache: dict[UserId, bytes] = {}
```

exists independently in each application worker.

With:

```text
Kubernetes
├── Pod A → local dict
├── Pod B → local dict
└── Pod C → local dict
```

each process has its own objects, identities, and in-memory hash tables.

Do not assume a Python dictionary provides distributed consistency.

For shared state, use an appropriate external system such as:

- PostgreSQL;
- Redis;
- Kafka;
- another durable or distributed service.

---

## Memory Considerations

Every dictionary and set maintains internal hash-table structures in addition to the Python objects themselves.

Large in-memory dictionaries can therefore consume substantial memory.

Consider:

- key object size;
- value object size;
- dictionary table overhead;
- resizing;
- object references;
- cache eviction;
- worker multiplication.

For example, a dictionary containing millions of Python objects can consume significantly more memory than an equivalent compact serialized representation.

This matters when deploying multiple FastAPI or Django workers across Kubernetes nodes.

---

## Observability

Identity and hashing issues are rarely solved through normal application metrics alone.

Useful diagnostic information includes:

- cache hit/miss rates;
- dictionary/set sizes;
- object counts;
- memory usage;
- request latency;
- allocation profiles;
- cache eviction rates.

For memory investigations, tools such as:

```python
import tracemalloc

tracemalloc.start()
```

can help identify allocation hotspots.

Avoid logging `id()` values as durable identifiers. They are useful for short-lived debugging but have no business meaning.

---

## Security Considerations

Treat object equality and hashing as application semantics, not security boundaries.

Do not use:

```python
hash(password)
```

for password storage.

Do not use:

```python
hash(token)
```

as a security primitive.

Use purpose-built cryptographic mechanisms for:

- password hashing;
- authentication tokens;
- signatures;
- integrity checks;
- cryptographic digests.

For user-controlled keys in high-volume hash-based structures, also consider resource-exhaustion risks and appropriate limits.

---

## Senior-Level Design Principles

### Separate Entity Identity From Value Equality

Use explicit domain identifiers for entities.

Use structural/value equality for value objects.

### Keep Hash Inputs Stable

Any state used by `__hash__()` must remain stable while the object is stored in a hash-based collection.

### Prefer Immutable Keys

Immutable value objects are safer dictionary and set keys.

### Do Not Persist Python Hashes

Use deterministic application hashing when stable cross-process behavior is required.

### Keep Equality Cheap and Deterministic

Avoid I/O, external state, and expensive computation in `__eq__()`.

### Treat Hashability as a Contract

Do not implement `__hash__()` merely to suppress:

```text
TypeError: unhashable type
```

The implementation must reflect correct domain semantics.

---

## Decision Framework

| Requirement | Recommended approach |
|---|---|
| Check whether value is absent | `is None` |
| Compare ordinary values | `==` |
| Detect same runtime object | `is` |
| Dictionary key | Immutable, correctly hashable value |
| Set member | Immutable/stable hash semantics |
| Domain identifier | Immutable value object |
| Database entity comparison | Explicit primary/domain identity |
| Cross-process stable hash | Deterministic hashing algorithm |
| Cryptographic hashing | `hashlib` or appropriate cryptographic library |
| Mutable aggregate | Usually do not make directly hashable |
| Cache key | Stable, explicit, preferably immutable representation |

---

## Key Takeaways

- **Identity, equality, and hashing solve different problems:** `is` checks object identity, `==` checks semantic equality, and `hash()` supports efficient hash-based collections.
- **Hashing must agree with equality:** whenever `a == b`, Python requires `hash(a) == hash(b)` for hashable objects; equal hashes alone do not imply equality.
- **Hashable objects require stable hash-relevant state:** mutable fields used by `__eq__()` or `__hash__()` can make dictionary and set membership incorrect after mutation.
- **Immutable value objects are strong hash-key candidates:** dataclasses with stable immutable fields are useful for domain identifiers, cache keys, and set membership.
- **Python hashes are not durable or cryptographic identifiers:** built-in hash values may vary between processes, so distributed systems need deterministic hashing and security-sensitive applications need dedicated cryptographic primitives.