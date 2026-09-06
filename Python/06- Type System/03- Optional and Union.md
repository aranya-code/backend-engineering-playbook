# 03- Optional and Union

## Overview

`Union` types express that a value may belong to more than one type. `Optional` is the common case where a value may either contain a specific type or be `None`.

Modern Python expresses these relationships primarily with the `|` operator:

```python
str | None
int | str
list[str] | None
```

Older code commonly uses:

```python
from typing import Optional, Union

Optional[str]
Union[int, str]
```

The modern syntax is generally preferred for new Python code.

Optional and union types are important because production systems frequently deal with values that are:

- absent
- nullable
- conditionally available
- represented differently at different stages
- returned in multiple valid forms
- dependent on external systems

The critical engineering distinction is that **a type being optional is different from a value merely having a default**.

```python
def find_user(user_id: int) -> User | None:
    ...
```

means the function may return either a `User` or `None`.

It does not mean that `user_id` itself is optional.

---

## Why Union Types Exist

A union represents a value that can legally have one of several types.

```python
def parse_identifier(value: int | str) -> int:
    if isinstance(value, int):
        return value

    return int(value)
```

The parameter contract is:

```text
value
 ├── int
 └── str
```

This is useful when multiple representations are genuinely supported.

Typical backend examples include:

- an ID accepted as `int | str`
- a configuration value represented as `str | None`
- an API field represented as `str | None`
- a function returning `User | None`
- a parser returning one of several result types
- a value transitioning from raw to validated representation

A union should represent a real domain or API contract, not simply hide unclear design.

---

## Modern Union Syntax

For modern Python, prefer:

```python
int | str
```

over:

```python
Union[int, str]
```

For optional values:

```python
str | None
```

over:

```python
Optional[str]
```

Example:

```python
def get_username(user_id: int) -> str | None:
    ...
```

This syntax is concise and directly communicates the runtime alternatives.

---

## `Optional[T]`

Historically:

```python
Optional[str]
```

means:

```python
str | None
```

It does **not** mean:

```text
the parameter is optional
```

Consider:

```python
def get_user(user_id: int, nickname: str | None) -> User:
    ...
```

`nickname` is nullable, but the caller is still required to provide it.

This is different:

```python
def get_user(
    user_id: int,
    nickname: str | None = None,
) -> User:
    ...
```

Now the argument itself has a default and can be omitted.

These are separate concepts:

| Concept | Example | Meaning |
|---|---|---|
| Nullable type | `str | None` | Value may be `None` |
| Optional argument | `x: str = "default"` | Argument can be omitted |
| Optional nullable argument | `x: str | None = None` | Argument can be omitted and can explicitly be `None` |

---

## `None` Is a Value

`None` represents the singleton object used to indicate the absence of a value.

```python
result: User | None = None
```

It is not the same as:

- `0`
- `False`
- `""`
- `[]`
- missing dictionary key

For example:

```python
if result is None:
    ...
```

is preferable to:

```python
if not result:
    ...
```

because the latter also treats valid falsey values as absent.

---

## Checking for `None`

Use identity comparison:

```python
if value is None:
    ...
```

and:

```python
if value is not None:
    ...
```

Avoid:

```python
if value == None:
    ...
```

Identity expresses the intended semantic operation and is the standard Python convention.

---

## Type Narrowing

Static type checkers can narrow a union after an appropriate runtime check.

```python
def normalize(value: str | int) -> str:
    if isinstance(value, int):
        return str(value)

    return value.upper()
```

Before the check:

```text
value: str | int
```

Inside the first branch:

```text
value: int
```

After the branch:

```text
value: str
```

This process is called **type narrowing**.

It allows code to remain type-safe while still supporting multiple runtime representations.

---

## Narrowing `None`

The same principle applies to optional values.

```python
def send_email(user: User | None) -> None:
    if user is None:
        return

    deliver_message(user.email)
```

After the check, the type checker understands that:

```python
user
```

is a `User`.

This is one reason precise union types are useful: they force application code to explicitly handle absence.

---

## Truthiness Is Not Always Narrowing

Consider:

```python
def process(value: str | None) -> None:
    if value:
        send(value)
```

This may narrow the value sufficiently for many type checkers, but it also changes the semantic condition.

An empty string is not `None`.

If absence specifically matters:

```python
if value is not None:
    send(value)
```

Use explicit conditions when business semantics distinguish:

- missing
- empty
- zero
- false
- invalid

---

## Union of Multiple Types

A union can contain more than two alternatives.

```python
str | int | bytes
```

Example:

```python
def decode_identifier(value: str | bytes | int) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")

    if isinstance(value, int):
        return str(value)

    return value
```

However, large unions can indicate that an abstraction is missing.

This:

```python
A | B | C | D | E
```

may be difficult to reason about.

When alternatives represent distinct domain states, consider a dedicated model or protocol.

---

## Union Types Are Not Overloading

A union:

```python
def process(value: int | str) -> Result:
    ...
```

means one function accepts either representation.

Overloading expresses different type-level relationships between inputs and outputs.

For example:

```python
from typing import overload


@overload
def parse(value: int) -> int: ...


@overload
def parse(value: str) -> str: ...


def parse(value: int | str) -> int | str:
    return value
```

Overloads become useful when the return type depends on the input type.

---

## Union and Return Types

Return unions are common at application boundaries.

```python
def find_order(order_id: int) -> Order | None:
    ...
```

This is clearer than:

```python
def find_order(order_id: int) -> object:
    ...
```

because callers know exactly what states must be handled.

For example:

```python
order = repository.find_order(order_id)

if order is None:
    raise OrderNotFound(order_id)

process_order(order)
```

The type contract drives explicit error handling.

---

## Union and Exceptions

Do not use a union as a substitute for exceptions when failure represents an exceptional condition.

For example:

```python
def parse_config(value: str) -> Config | None:
    ...
```

may be appropriate when absence is a valid result.

But:

```python
def charge_payment(...) -> Payment | None:
    ...
```

may be ambiguous if `None` means a payment failure.

A clearer design may be:

```python
def charge_payment(...) -> Payment:
    ...
```

with explicit domain exceptions for failure.

Use unions for **valid states**, not merely to avoid designing error handling.

---

## Optional Return Values in Repositories

A repository lookup often naturally returns an optional entity:

```python
def get_by_id(user_id: int) -> User | None:
    ...
```

Typical flow:

```text
HTTP request
    │
    ▼
Service
    │
    ▼
Repository
    │
    ├── User
    │
    └── None
         │
         ▼
      404 response
```

The service layer converts the repository's absence semantics into the API's domain semantics.

---

## Optional Values and HTTP APIs

An optional database field may become a nullable JSON field:

```json
{
  "id": 1001,
  "display_name": null
}
```

The Python representation may be:

```python
display_name: str | None
```

But these API states are not necessarily equivalent:

```json
{}
```

and:

```json
{
  "display_name": null
}
```

The first can mean "field not supplied."

The second can mean "field explicitly set to null."

This distinction becomes particularly important for PATCH APIs.

---

## PATCH Semantics

Consider:

```python
class UpdateUser:
    display_name: str | None
```

This alone may not distinguish:

```text
field omitted
field explicitly set to null
field set to a string
```

For PATCH operations, these states may have different meanings.

A robust API model may need a representation where:

```text
UNSET
NULL
VALUE
```

are distinct states.

This is one reason frameworks such as Pydantic provide mechanisms for distinguishing missing fields from fields explicitly supplied as `None`.

---

## Optional Fields in Pydantic

A nullable field can be represented as:

```python
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    nickname: str | None
```

If the field should also have a default:

```python
class UserRequest(BaseModel):
    nickname: str | None = None
```

The distinction between:

```python
nickname: str | None
```

and:

```python
nickname: str | None = None
```

is important.

The first declares a nullable field; the second also supplies a default.

Exact required/optional behavior should be verified against the Pydantic version and model configuration used by the project.

---

## Optional Values and Django

Django applications commonly encounter nullable database fields.

For example:

```python
class UserProfile(models.Model):
    nickname = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
```

Application-layer typing may represent the resulting value as:

```python
str | None
```

However, Django's `null` and `blank` have different meanings:

- `null` concerns database storage
- `blank` concerns validation/forms

Do not assume database nullability and API optionality are automatically equivalent.

---

## Optional vs Empty

These are distinct:

```python
None
""
[]
{}
```

For example:

```python
nickname: str | None
```

may mean:

```text
None → no nickname
""   → nickname is explicitly empty
```

Whether both states should be allowed is a domain decision.

Production APIs should define this explicitly rather than allowing accidental ambiguity.

---

## Union Types and Database Values

Database systems often contain nullable columns.

Conceptually:

```text
PostgreSQL
    │
    ▼
NULL
    │
    ▼
Python
    │
    ▼
None
```

Application code may therefore use:

```python
email_verified_at: datetime | None
```

A query result containing `NULL` should not be treated as an ordinary `datetime`.

The service layer should preserve or explicitly transform the nullable state.

---

## Union Types and Configuration

Configuration values frequently have multiple representations.

For example, an internal configuration API might accept:

```python
timeout: int | float
```

or:

```python
endpoint: str | None
```

However, external configuration commonly arrives as strings:

```text
TIMEOUT="30"
```

Runtime validation and conversion should normalize the value:

```text
environment variable
        │
        ▼
string
        │
        ▼
validation / parsing
        │
        ▼
int
```

Do not spread `str | int` throughout the application merely because environment variables are strings.

Normalize once at the configuration boundary.

---

## Normalize Unions at Boundaries

Suppose an API accepts:

```python
user_id: int | str
```

It is usually better to normalize immediately:

```python
def normalize_user_id(value: int | str) -> int:
    if isinstance(value, int):
        return value

    return int(value)
```

Then downstream code can use:

```python
user_id: int
```

instead of carrying:

```python
int | str
```

through every service and repository.

This is a strong production pattern:

> **Accept flexible representations at boundaries, normalize them early, and keep the core domain model precise.**

---

## Union Types Across Microservices

Suppose service A sends:

```json
{
  "user_id": "1001"
}
```

while service B expects:

```python
user_id: int
```

Adding:

```python
int | str
```

everywhere may appear convenient, but it hides a contract mismatch.

A better architecture is:

```text
External representation
        │
        ▼
Deserialize
        │
        ▼
Validate
        │
        ▼
Normalize
        │
        ▼
Domain model
```

The internal service contract should remain stable.

---

## Union Types and gRPC

gRPC and Protocol Buffers typically represent alternatives through explicit schema mechanisms such as `oneof`.

Conceptually:

```text
oneof identifier:
    user_id
    external_id
```

In Python, this may result in generated types and runtime accessors rather than simply relying on:

```python
int | str
```

For strongly defined service-to-service contracts, explicit wire-level schemas are usually preferable to unconstrained unions.

---

## Union Types and Kafka

Kafka messages may evolve over time.

A consumer might temporarily support:

```python
OrderCreatedV1 | OrderCreatedV2
```

during a migration.

This can be useful during controlled schema evolution, but the consumer should usually normalize both versions into a common internal model:

```text
Kafka event
   │
   ├── V1 ──┐
   │        │
   └── V2 ──┤
            ▼
       normalization
            │
            ▼
     OrderCreated
```

Do not let protocol-version unions leak throughout the domain layer.

---

## Union Types and Redis

Redis stores serialized values rather than Python's static type information.

A cache may contain:

```text
User
or
legacy User representation
```

A consumer may temporarily use:

```python
UserV1 | UserV2
```

while migrating cached data.

However, explicit versioning and controlled cache invalidation are usually safer than allowing arbitrary runtime unions indefinitely.

---

## Type Aliases for Domain Unions

Repeated unions can be given meaningful names.

```python
type UserIdentifier = int | str
```

Then:

```python
def get_user(identifier: UserIdentifier) -> User | None:
    ...
```

This is clearer when the union represents a real domain concept.

A type alias should explain semantics rather than merely shorten syntax.

---

## Discriminated Unions

When alternatives have different structures, use an explicit discriminator.

Conceptually:

```json
{
  "type": "email",
  "address": "user@example.com"
}
```

or:

```json
{
  "type": "sms",
  "phone": "+15551234567"
}
```

The model becomes:

```text
Notification
   │
   ├── EmailNotification
   │
   └── SMSNotification
```

A discriminator such as `type` makes the union explicit and easier to validate, serialize, log, and evolve.

This is generally safer than attempting to infer the variant from arbitrary fields.

---

## Structural vs Nominal Alternatives

A union can combine classes:

```python
User | Admin
```

but sometimes the real requirement is a shared capability.

If both types support:

```python
send_notification()
```

a protocol may be more appropriate than a union:

```python
from typing import Protocol


class Notifiable(Protocol):
    def send_notification(self) -> None:
        ...
```

Then:

```python
def notify(target: Notifiable) -> None:
    target.send_notification()
```

This avoids enumerating every implementation.

A useful design rule is:

```text
Known finite alternatives
    → Union

Shared capability
    → Protocol

Common domain state
    → Base model / domain abstraction
```

---

## Union Types and Generics

Unions can appear inside generic containers:

```python
list[int | str]
```

This means each element may independently be an integer or string.

It differs from:

```python
list[int] | list[str]
```

The first means:

```text
list
 ├── int
 ├── str
 ├── int
 └── ...
```

The second means:

```text
either:
    list[int]

or:
    list[str]
```

This distinction matters for type checking and API contracts.

---

## `list[int | str]` vs `list[int] | list[str]`

| Type | Meaning |
|---|---|
| `list[int | str]` | One list can contain both `int` and `str` |
| `list[int] \| list[str]` | The entire list is either all `int` or all `str` |
| `tuple[int \| str, ...]` | Any-length tuple containing either type |
| `(int \| str) \| None` | `int`, `str`, or `None` |

The distinction can materially affect downstream assumptions.

---

## Optional Generic Types

Generic containers can themselves be optional:

```python
list[User] | None
```

This means:

```text
None
or
list[User]
```

It is different from:

```python
list[User | None]
```

which means:

```text
list containing User and/or None
```

For example:

```python
users: list[User] | None
```

versus:

```python
users: list[User | None]
```

These represent completely different contracts.

---

## Prefer Empty Collections When Appropriate

Sometimes an API does not need:

```python
list[User] | None
```

If "no users" can naturally be represented by an empty list, prefer:

```python
list[User]
```

with:

```python
[]
```

This reduces branching:

```python
for user in users:
    process(user)
```

instead of:

```python
if users is not None:
    for user in users:
        process(user)
```

Use `None` when absence has different semantics from an empty collection.

For example:

```text
None → query was not performed
[]   → query was performed and found nothing
```

That distinction can be meaningful.

---

## Optional Values and Caching

A cache lookup commonly returns:

```python
User | None
```

because a cache miss is a valid state.

```python
user = cache.get(user_id)

if user is None:
    user = repository.get_by_id(user_id)
```

Be careful when cached values themselves may legitimately be `None`.

In those cases, a simple nullable return value may not distinguish:

```text
cache miss
cached None
```

Use an explicit result abstraction if those states matter.

---

## Optional Values and Concurrency

Optional values can become stale between checks and use.

For example:

```python
user = repository.get_by_id(user_id)

if user is not None:
    repository.update(user)
```

Another transaction may modify the database between the read and update.

Type narrowing guarantees only the type relationship, not transactional consistency.

Production correctness may require:

- transactions
- optimistic locking
- database constraints
- atomic updates
- appropriate isolation levels

Static typing cannot replace concurrency control.

---

## Security Considerations

Union types should not be used to bypass validation of untrusted input.

This:

```python
payload: dict[str, int | str]
```

does not make incoming JSON trustworthy.

External input should follow:

```text
Untrusted input
      │
      ▼
Parsing
      │
      ▼
Schema validation
      │
      ▼
Normalization
      │
      ▼
Typed application model
```

Be especially careful with unions involving:

- URLs
- file paths
- SQL fragments
- authentication data
- serialized objects
- command arguments

A static annotation does not establish trust.

---

## Performance Considerations

Union annotations normally have negligible runtime performance impact.

The important performance consideration is the runtime logic used to discriminate between variants.

For example:

```python
if isinstance(value, int):
    ...
elif isinstance(value, str):
    ...
```

is inexpensive.

The larger concern is carrying broad unions deep into an application and repeatedly checking them.

Prefer:

```text
parse once
   ↓
normalize once
   ↓
use precise domain type
```

over repeated:

```text
isinstance(...)
isinstance(...)
isinstance(...)
```

throughout business logic.

---

## Static Analysis

Type checkers such as mypy and Pyright can identify invalid union handling.

For example:

```python
def uppercase(value: str | None) -> str:
    return value.upper()
```

A strict type checker should flag this because `value` may be `None`.

Correct:

```python
def uppercase(value: str | None) -> str:
    if value is None:
        return ""

    return value.upper()
```

This is one of the practical benefits of strict typing: nullable states become visible during development rather than only through runtime failures.

---

## Assertions and Type Narrowing

An assertion can narrow a type:

```python
def process(user: User | None) -> None:
    assert user is not None
    send_email(user.email)
```

However, assertions should not generally replace production validation.

Python can run with optimizations that remove assertions, and assertions are better suited to expressing programmer invariants than handling expected external conditions.

Prefer explicit application logic:

```python
if user is None:
    raise UserNotFound(...)
```

when absence is an expected business state.

---

## `cast()` and Union Types

`cast()` tells a static type checker to treat an expression as another type.

```python
from typing import cast


user = cast(User, value)
```

It does not perform runtime conversion or validation.

Therefore:

```python
cast(User, value)
```

does not make `value` a `User`.

Use `cast()` sparingly and only when the programmer has stronger information than the type checker.

If casts appear frequently around unions, the underlying API may need redesign.

---

## `TypeGuard` and Complex Unions

Custom predicates can communicate narrowing information.

```python
from typing import TypeGuard


def is_user(value: object) -> TypeGuard[User]:
    return isinstance(value, User)
```

Then:

```python
value: object

if is_user(value):
    value.email
```

This is useful when runtime discrimination is more complex than a simple `isinstance()` check.

Type guards should be truthful. An incorrect type guard can undermine static safety.

---

## Common Mistakes

### Treating `Optional` as "Argument May Be Omitted"

Incorrect assumption:

```python
def send(name: str | None):
    ...
```

This does not make the argument optional.

Use a default when omission is intended:

```python
def send(name: str | None = None):
    ...
```

### Using `if not value` for `None`

This can incorrectly treat valid falsey values as absent.

Prefer:

```python
if value is None:
    ...
```

when checking nullability.

### Confusing Nullable Collections

These are different:

```python
list[User] | None
```

and:

```python
list[User | None]
```

### Carrying Unions Through the Entire Application

Normalize flexible input at the boundary.

### Using Huge Unions

A large union may indicate a missing abstraction.

### Using `Any` Instead

Replacing a meaningful union with:

```python
Any
```

throws away useful information.

### Using `cast()` to Hide Design Problems

Repeated casts often indicate that the type model does not match the architecture.

### Assuming Type Hints Validate API Input

They do not.

### Treating `None` and Empty as Equivalent

This can introduce subtle API and business-logic bugs.

### Using `None` for Every Failure

A union with `None` is appropriate when absence is a valid state. Expected business failures often deserve explicit result types or exceptions instead.

---

## Production Design Patterns

### Normalize at Boundaries

```python
def normalize_id(value: int | str) -> int:
    if isinstance(value, int):
        return value

    return int(value)
```

After normalization:

```python
user_id: int
```

### Use `None` for Genuine Absence

```python
def find_user(user_id: int) -> User | None:
    ...
```

### Prefer Empty Collections for Natural Emptiness

```python
def list_users() -> list[User]:
    ...
```

Return:

```python
[]
```

rather than `None` when there is no meaningful distinction.

### Use Protocols for Capabilities

If multiple types satisfy the same behavior, use a protocol rather than a growing union.

### Use Explicit Models for Variant Structures

Use discriminators for message or API variants.

### Keep Wire Types Separate from Domain Types

Normalize external unions into stable internal representations.

---

## Architecture Example

A production API may process an identifier accepted in multiple forms:

```text
HTTP request
     │
     ▼
FastAPI validation
     │
     ▼
str | int
     │
     ▼
Normalization
     │
     ▼
int
     │
     ▼
Service
     │
     ▼
Repository
     │
     ▼
PostgreSQL
```

The union exists at the boundary because the external representation is flexible.

The domain layer should not need to care whether the caller originally supplied `"1001"` or `1001`.

---

## Testing Union-Based Code

Each meaningful variant should have test coverage.

For:

```python
def normalize_id(value: int | str) -> int:
    ...
```

test at least:

```text
int input
valid string input
invalid string input
boundary values
unexpected runtime values
```

For nullable return values:

```text
entity found
entity absent
database error
```

For discriminated unions:

```text
each supported variant
missing discriminator
unknown discriminator
invalid variant payload
```

Static type checking and runtime testing complement each other.

---

## CI/CD Recommendations

Run static analysis as part of CI:

```text
Pull Request
     │
     ├── Unit tests
     ├── Integration tests
     ├── Ruff
     ├── mypy / Pyright
     └── Build
```

Use strictness appropriate to the maturity of the codebase.

New services should generally avoid allowing nullable and union-heavy code to grow without review.

Type-checking failures should normally be treated as development failures rather than production warnings.

---

## Decision Guide

| Requirement | Recommended approach |
|---|---|
| Value may be `T` or `None` | `T \| None` |
| Value may be one of several types | `A \| B` |
| Argument can be omitted | Default value |
| Argument can be omitted and null | `T \| None = None` |
| Empty collection means "none" | Prefer `list[T]`, `set[T]`, etc. |
| Missing and null have different meanings | Explicit model/state representation |
| Input has multiple external representations | Union at boundary + normalization |
| Multiple types share a capability | `Protocol` |
| Different structured variants | Discriminated union |
| Return depends on input type | `@overload` |
| Complex runtime narrowing | `TypeGuard` |
| Static checker lacks known information | Limited `cast()` use |
| Failure is exceptional | Exception or explicit result model |
| Multiple protocol versions temporarily supported | Version union + normalization |

---

## Interview Traps

### Is `Optional[str]` the same as an optional function argument?

No. `Optional[str]` means the value can be `str` or `None`. An argument is optional to supply only when it has a default or the function otherwise permits omission.

### What is the modern equivalent of `Optional[str]`?

```python
str | None
```

### What is the difference between `list[int | str]` and `list[int] | list[str]`?

The first permits mixed element types in one list. The second says the entire list is either an integer list or a string list.

### Does `int | str` automatically convert strings to integers?

No. A union describes accepted types; it does not perform conversion.

### Does a union perform runtime validation?

No.

### When should a union become a protocol?

When the alternatives are not fundamentally different states but merely different implementations providing the same behavior.

### Why is `None` different from an empty list?

`None` can represent absence or "not available," while `[]` can represent a successfully evaluated operation with zero results.

### Why should unions often be normalized at boundaries?

It prevents representation complexity from propagating through the service and domain layers.

### Can `cast()` validate a union value?

No. `cast()` only changes the static type assumption.

### Why are large unions often a design smell?

They can indicate that the domain lacks a clearer abstraction, discriminator, protocol, or normalization boundary.

---

## Production Checklist

Before using optional or union types, verify:

- `T | None` is used when nullability is intentional.
- Argument omission is not being confused with nullable values.
- Defaults are used when parameters are genuinely optional to supply.
- `None` checks use identity comparison.
- Empty collections are preferred when they adequately represent "no results."
- `None` and empty values are distinguished when their business semantics differ.
- Union members represent legitimate supported states.
- Flexible external representations are normalized at system boundaries.
- Domain logic does not unnecessarily carry raw wire-format unions.
- Complex structured alternatives use explicit discriminators or models.
- Protocols are considered when alternatives share behavior rather than state.
- Overloads are considered when output types depend on input types.
- `TypeGuard` is used only when its runtime predicate is accurate.
- `cast()` is not being used to suppress unresolved design or validation problems.
- Static type checking runs in CI/CD.
- Runtime validation protects all untrusted external input.
- Database nullability is not assumed to equal API optionality.
- PATCH APIs distinguish omitted fields from explicit `null` when required.
- Cache misses are not confused with cached `None` values when both are possible.
- Concurrency and transaction guarantees are handled separately from type narrowing.
- Union-heavy interfaces are reviewed for maintainability and domain clarity.

## Key Takeaways

- `T | None` expresses nullability; it does not by itself mean that a function argument can be omitted.
- Use unions for genuine alternative representations or states, then normalize flexible external input into precise internal types.
- Distinguish `None`, empty collections, omitted fields, and explicit nulls because they can represent different business semantics.
- Prefer protocols for shared capabilities and explicit models or discriminated unions for structured variants instead of allowing large unions to spread through the application.
- Static type narrowing improves correctness but does not perform runtime validation, enforce transactional consistency, or replace proper error and security handling.