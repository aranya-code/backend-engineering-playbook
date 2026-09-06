# 16- Descriptors

## Overview

Descriptors are one of Python's most powerful object-model mechanisms. They allow an object stored on a class to control how another object's attributes are accessed, assigned, or deleted.

The descriptor protocol is based primarily on:

```python
__get__
__set__
__delete__
```

A descriptor becomes useful when normal attribute access needs custom behavior.

The built-in `property` type is itself a descriptor:

```python
class User:
    def __init__(self, email: str) -> None:
        self._email = email

    @property
    def email(self) -> str:
        return self._email
```

Understanding descriptors explains several Python features that otherwise appear magical:

- Properties
- Bound methods
- Class methods
- Static methods
- ORM fields
- Validation frameworks
- Dependency injection frameworks
- Lazy attributes
- Attribute interception
- Many Python metaprogramming patterns

For backend engineers, descriptors are important less because every application should implement them and more because frameworks such as Django rely heavily on descriptor behavior.

## What Is a Descriptor?

A descriptor is an object that defines one or more of:

```python
__get__
__set__
__delete__
```

and is typically stored as a **class attribute**.

Example:

```python
class Field:
    def __get__(self, instance, owner):
        ...

    def __set__(self, instance, value):
        ...


class User:
    email = Field()
```

Here:

```python
User.email
```

and:

```python
user.email
```

can trigger descriptor logic.

The important relationship is:

```text
Class
  |
  +--> descriptor object
          |
          +--> controls access to
                  |
                  v
               instance
```

## Why Descriptors Exist

Without descriptors, Python would have limited support for reusable attribute behavior.

Suppose ten classes need validated fields:

```text
User.email
User.phone
Order.amount
Payment.currency
Product.price
...
```

Without descriptors, validation logic could be duplicated across properties.

A reusable descriptor can centralize the behavior:

```python
class PositiveInt:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("value must be a positive integer")

        instance.__dict__[self.name] = value
```

Then:

```python
class Product:
    quantity = PositiveInt()
    price = PositiveInt()
```

The validation behavior is reusable.

## Descriptor Protocol

The core protocol is:

```python
class Descriptor:
    def __get__(self, instance, owner):
        ...

    def __set__(self, instance, value):
        ...

    def __delete__(self, instance):
        ...
```

Not every descriptor needs all three methods.

| Method | Trigger |
|---|---|
| `__get__` | Attribute read |
| `__set__` | Attribute assignment |
| `__delete__` | Attribute deletion |
| `__set_name__` | Class creation/name assignment |

`__set_name__` is not one of the core descriptor access methods, but it is an important descriptor-related hook introduced in modern Python.

## Descriptor Example

A simple validating descriptor:

```python
class PositiveInt:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if not isinstance(value, int):
            raise TypeError("value must be an integer")

        if value <= 0:
            raise ValueError("value must be positive")

        instance.__dict__[self.name] = value


class Product:
    quantity = PositiveInt()
    price = PositiveInt()
```

Usage:

```python
product = Product()

product.quantity = 10
product.price = 500
```

Invalid values are rejected:

```python
product.quantity = -1
```

raises:

```text
ValueError
```

## How Descriptor Lookup Works

Attribute lookup is more complex than:

```python
obj.__dict__[name]
```

A simplified model is:

```text
obj.name
  |
  v
Search type(obj) and its MRO
  |
  v
Descriptor found?
  |
  +---- data descriptor ----> __get__(obj, type(obj))
  |
  +---- no data descriptor
  |
  v
Search obj.__dict__
  |
  v
Non-data descriptor?
  |
  +---- yes ----> __get__(obj, type(obj))
  |
  v
Class attribute
```

The distinction between **data descriptors** and **non-data descriptors** is fundamental.

## Data Descriptors

A descriptor implementing `__set__` or `__delete__` is a data descriptor.

For example:

```python
class ManagedAttribute:
    def __get__(self, instance, owner):
        ...

    def __set__(self, instance, value):
        ...
```

Data descriptors take precedence over an instance's `__dict__`.

This makes them suitable for:

- Validation
- Managed state
- Properties
- ORM fields
- Access control

## Non-Data Descriptors

A descriptor implementing only `__get__` is a non-data descriptor.

Example:

```python
class ReadOnlyDescriptor:
    def __get__(self, instance, owner):
        return "value"
```

Because it has no `__set__` or `__delete__`, an instance attribute can generally shadow it.

This distinction is important when implementing custom descriptors.

## Data vs Non-Data Descriptors

| Descriptor type | Implements | Priority |
|---|---|---|
| Data descriptor | `__set__` and/or `__delete__` plus `__get__` | Before instance `__dict__` |
| Non-data descriptor | `__get__` only | After instance `__dict__` |
| Normal class attribute | No descriptor protocol | Lower priority than instance attributes |

This explains behavior such as:

```python
obj.method
```

being resolved differently from a normal stored function.

## `__get__`

`__get__` controls attribute retrieval.

Its common signature is:

```python
def __get__(self, instance, owner):
    ...
```

For:

```python
obj.field
```

Python conceptually passes:

```text
instance = obj
owner = type(obj)
```

For:

```python
Class.field
```

the descriptor may receive:

```text
instance = None
owner = Class
```

A common implementation therefore starts with:

```python
if instance is None:
    return self
```

This allows the descriptor to be inspected through the class.

## `__set__`

`__set__` controls assignment.

```python
obj.field = value
```

can invoke:

```python
descriptor.__set__(obj, value)
```

This is useful for:

- Validation
- Normalization
- Change tracking
- Lazy persistence
- Type enforcement

However, descriptors should not hide expensive infrastructure operations without a strong framework-level reason.

## `__delete__`

`__delete__` controls:

```python
del obj.field
```

Example:

```python
class RequiredField:
    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__["value"]

    def __set__(self, instance, value):
        instance.__dict__["value"] = value

    def __delete__(self, instance):
        raise AttributeError("field cannot be deleted")
```

Deletion semantics should be explicit because silently deleting required state can violate object invariants.

## `__set_name__`

`__set_name__` lets a descriptor discover the attribute name assigned to it.

Example:

```python
class Field:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
```

Now:

```python
class User:
    email = Field()
    phone = Field()
```

causes Python to effectively tell the descriptor:

```text
Field instance -> "email"
Field instance -> "phone"
```

This eliminates the need to manually repeat field names.

## Descriptor Storage

A descriptor itself is normally stored on the class:

```python
class User:
    email = Field()
```

The descriptor object is therefore shared by instances.

Instance-specific values should usually be stored on the instance:

```python
instance.__dict__[self.name] = value
```

Conceptually:

```text
User class
   |
   +--> Field descriptor
            |
            +--> name = "email"

User instance A
   |
   +--> __dict__["email"] = "a@example.com"

User instance B
   |
   +--> __dict__["email"] = "b@example.com"
```

This separation is essential.

## Avoid Storing Mutable Instance State in the Descriptor

Because descriptors are class attributes, this is dangerous:

```python
class BadField:
    values = {}

    def __set__(self, instance, value):
        self.values[instance] = value
```

The descriptor is shared by all instances.

That may be intentional for a registry, but it is usually wrong for per-instance state.

Prefer:

```python
instance.__dict__[self.name] = value
```

or another explicit per-instance storage mechanism.

## Descriptor and Instance Lifetime

A descriptor can outlive individual instances because it belongs to the class.

Therefore, storing instances inside a descriptor can accidentally create strong references:

```python
class BadDescriptor:
    values = {}

    def __set__(self, instance, value):
        self.values[instance] = value
```

This can retain instances and cause memory growth.

If external per-instance storage is genuinely required, use an appropriate weak-reference strategy such as `weakref.WeakKeyDictionary`, while understanding its constraints.

## Property Is a Descriptor

Python's `property` is one of the most important built-in descriptors.

```python
class User:
    @property
    def email(self) -> str:
        return self._email
```

Conceptually:

```text
User.email
    |
    v
property descriptor
    |
    v
__get__(user, User)
    |
    v
getter function
```

A property with a setter also implements assignment behavior through the descriptor protocol.

This is why descriptors are the foundation underneath the previous topic on properties.

## Methods Are Descriptors

Functions defined inside classes implement descriptor behavior.

Consider:

```python
class User:
    def greet(self) -> str:
        return "hello"
```

When:

```python
user.greet
```

is accessed, Python binds the function to the instance.

Conceptually:

```text
User.greet
    |
    v
function descriptor
    |
    v
user.greet
    |
    v
bound method
```

The function's descriptor behavior is provided by its `__get__` implementation.

This is why:

```python
user.greet()
```

automatically supplies:

```python
self
```

## Function Binding

Consider:

```python
class User:
    def greet(self) -> str:
        return "hello"
```

Accessing:

```python
User.greet
```

returns the function.

Accessing:

```python
user.greet
```

returns a bound method.

Conceptually:

```python
User.greet
```

is similar to:

```text
function
```

while:

```python
user.greet
```

is similar to:

```python
function.__get__(user, User)
```

The descriptor protocol explains method binding without requiring special-case conceptual rules.

## `staticmethod` Is Descriptor-Based

`staticmethod` is also implemented using descriptor machinery.

```python
class Math:
    @staticmethod
    def add(a: int, b: int) -> int:
        return a + b
```

The method does not receive an automatically bound `self`.

Conceptually:

```text
Class attribute
     |
     v
staticmethod descriptor
     |
     v
underlying function
```

## `classmethod` Is Descriptor-Based

`classmethod` binds the class rather than the instance.

```python
class User:
    @classmethod
    def create(cls, user_id: int):
        return cls(user_id)
```

Conceptually:

```text
User.create
    |
    v
classmethod descriptor
    |
    v
function bound to User
```

This is another example of descriptors powering ordinary Python syntax.

## Descriptor Lookup and MRO

Descriptors participate in inheritance.

```python
class Base:
    name = SomeDescriptor()


class Child(Base):
    pass
```

Accessing:

```python
Child().name
```

requires Python to search the MRO for `name`.

The lookup path is approximately:

```text
Child
  |
  v
Base
  |
  v
descriptor
  |
  v
__get__(instance, Child)
```

The `owner` argument can be the actual type of the instance even when the descriptor is defined on a base class.

This matters when descriptors need subclass-aware behavior.

## Descriptor Example: Type Validation

A reusable descriptor can enforce types.

```python
class TypedField:
    def __init__(self, expected_type: type) -> None:
        self.expected_type = expected_type
        self.name = ""

    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value) -> None:
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} must be "
                f"{self.expected_type.__name__}"
            )

        instance.__dict__[self.name] = value
```

Usage:

```python
class User:
    user_id = TypedField(int)
    email = TypedField(str)
```

Now:

```python
user.user_id = 42
user.email = "user@example.com"
```

are valid.

But:

```python
user.user_id = "42"
```

raises `TypeError`.

## Descriptor Example: Normalization

Descriptors can centralize normalization.

```python
class NormalizedString:
    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("value must be a string")

        instance.__dict__[self.name] = value.strip().lower()
```

This can be useful for domain-level normalization.

However, validation frameworks or dedicated value objects may be more appropriate when the rules become complex.

## Descriptor Example: Lazy Loading

A descriptor can implement lazy evaluation:

```python
class LazyValue:
    def __init__(self, factory):
        self.factory = factory

    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = self.factory(instance)

        return instance.__dict__[self.name]
```

Usage:

```python
class Report:
    parsed = LazyValue(lambda report: parse_report(report.raw))
```

This is effectively a reusable lazy-property pattern.

For expensive or I/O-bound operations, however, explicit methods are often clearer.

## Descriptor Example: Cached Computation

Descriptors can implement cached values:

```python
class CachedValue:
    def __init__(self, factory):
        self.factory = factory

    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = self.factory(instance)

        return instance.__dict__[self.name]
```

This resembles:

```python
functools.cached_property
```

The standard library implementation should normally be preferred over maintaining a custom equivalent unless specialized behavior is required.

## Descriptor Example: Backend Configuration

Descriptors can validate configuration values.

```python
class EnvironmentValue:
    def __init__(
        self,
        env_name: str,
        *,
        default: str | None = None,
    ) -> None:
        self.env_name = env_name
        self.default = default

    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner) -> str | None:
        if instance is None:
            return self

        return os.getenv(
            self.env_name,
            self.default,
        )
```

However, repeatedly reading environment variables through descriptors can make configuration behavior less explicit.

For production systems, load and validate configuration once during application startup, then inject the configuration object.

## Descriptor Example: Access Control

A descriptor can control attribute access:

```python
class ReadOnly:
    def __set_name__(self, owner, name: str) -> None:
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        raise AttributeError(
            f"{self.name} is read-only"
        )
```

This can enforce a simple invariant.

For authorization, however, descriptors are usually the wrong abstraction. Security decisions should generally remain explicit and auditable.

## Django and Descriptors

Django is one of the clearest real-world examples of descriptor-heavy Python design.

Django model fields are declared on classes:

```python
class Order(models.Model):
    total = models.DecimalField(...)
```

But accessing:

```python
order.total
```

does not simply read a normal class variable.

Django's ORM machinery uses descriptors and related infrastructure to provide behavior around model attributes.

This enables:

- Field conversion
- Deferred loading
- Relationship access
- Related-object managers
- Validation integration
- Database-backed state

The descriptor effectively forms part of the bridge between:

```text
Python object model
```

and:

```text
Relational database
```

## Django Relationship Descriptors

Relationship fields demonstrate the pattern even more clearly.

For example:

```python
class Order(models.Model):
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
    )
```

Accessing:

```python
order.customer
```

can trigger ORM behavior to retrieve the related object.

This is an important distinction from ordinary properties.

A Django descriptor may intentionally perform database I/O.

That behavior is framework-defined and should not be generalized to application-level descriptors.

## Django and N+1 Queries

Descriptor-backed relationships can make database access look like ordinary attribute access.

For example:

```python
for order in orders:
    print(order.customer.name)
```

may generate an N+1 query pattern if relationships are not loaded appropriately.

Use explicit ORM loading strategies such as:

```python
orders = Order.objects.select_related(
    "customer"
)
```

when appropriate.

The broader lesson is:

> Attribute syntax does not guarantee in-memory access.

Framework descriptors can hide significant work, so engineers must understand the framework's descriptor semantics.

## FastAPI and Descriptors

FastAPI application code generally relies more heavily on:

- Dependency injection
- Pydantic models
- Function-based endpoints
- Explicit service composition

than custom descriptors.

Descriptors can still appear indirectly through libraries used by FastAPI applications.

When designing application code, do not introduce descriptors simply because they are powerful.

Use them when the problem is genuinely about reusable attribute semantics.

## ORM Descriptors and Transactions

Descriptor-backed ORM access can interact with transaction boundaries.

For example:

```python
order.customer
```

might require a database query.

If that access occurs:

```text
outside expected transaction scope
```

or:

```text
inside a high-volume loop
```

it can produce unexpected consistency or performance behavior.

For database-heavy paths, prefer explicit query planning:

```text
Query requirements
      |
      v
ORM loading strategy
      |
      v
Fetched object graph
      |
      v
In-memory attribute access
```

Do not rely on implicit descriptor behavior to design database access patterns.

## Descriptors and Lazy Loading

Lazy loading is convenient:

```python
order.customer
```

but has trade-offs.

Advantages:

- Lower initial query cost
- Load data only when needed
- Convenient object model

Limitations:

- Hidden I/O
- N+1 queries
- Unpredictable latency
- Transaction-scope problems
- Harder performance reasoning

For production APIs, query planning should usually make data access intentional.

## Descriptors and Dependency Injection

A descriptor can technically implement dependency lookup:

```python
class Injected:
    def __get__(self, instance, owner):
        return container.resolve(...)
```

This creates:

```text
service.repository
       |
       v
descriptor
       |
       v
dependency container
       |
       v
Repository instance
```

Although technically possible, this can hide dependencies.

Prefer constructor injection:

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
    ) -> None:
        self.repository = repository
```

The dependency is now explicit, testable, and visible in the class contract.

## Descriptors and Dataclasses

Dataclasses and descriptors can coexist, but interaction details matter.

For example:

```python
from dataclasses import dataclass


class PositiveInt:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("must be positive")

        instance.__dict__[self.name] = value


@dataclass
class Product:
    quantity: int = PositiveInt()
```

This design requires careful understanding of how the dataclass decorator processes class attributes.

For straightforward data validation, modern dataclass patterns or dedicated validation models are often easier to maintain.

Do not combine metaprogramming mechanisms without a concrete need.

## Descriptors and Type Hints

A descriptor's runtime behavior and static typing behavior are separate concerns.

For reusable descriptors, advanced typing may be required to accurately communicate:

```text
descriptor type
        |
        +--> value returned from instance access
        |
        +--> descriptor returned from class access
```

Simple application descriptors can often rely on ordinary annotations, while reusable libraries may require generic descriptors and overloads.

For example:

```python
from typing import Generic, TypeVar

T = TypeVar("T")


class Field(Generic[T]):
    ...
```

Library-quality descriptors often need more sophisticated typing than application-specific ones.

## Descriptors and `__slots__`

Descriptors become particularly important when classes use `__slots__`.

A slotted class may not have a normal `__dict__`:

```python
class User:
    __slots__ = ("user_id",)
```

A descriptor can provide managed attribute behavior without relying on instance dictionaries.

For example, a descriptor can store data externally or use a slot-backed mechanism.

However, custom descriptor storage must be designed carefully because:

- Instances may not have `__dict__`.
- Memory layout changes.
- Weak references may require explicit support.
- Inheritance interactions become more complex.

## Descriptors and Memory

A descriptor is usually one object stored on the class and shared across instances.

This can be memory-efficient when behavior is reusable.

For example:

```text
10,000 User instances
        |
        v
one shared descriptor
```

rather than:

```text
10,000 separate property-management objects
```

However, descriptor-managed external state can increase memory usage if it retains references to instances.

Always consider ownership and lifetime.

## Descriptors and Performance

Descriptor access introduces Python-level dispatch.

For a normal attribute:

```python
user.name
```

the runtime may retrieve a value directly from the instance dictionary.

For a descriptor:

```python
user.name
```

Python may invoke:

```python
descriptor.__get__(user, User)
```

If the descriptor performs additional computation, validation, locking, or I/O, the cost can become significant.

For hot paths:

- Keep descriptor operations small.
- Avoid database/network calls.
- Avoid unnecessary allocations.
- Avoid complex reflection.
- Profile before optimizing.

## Descriptors and Concurrency

Descriptors themselves do not provide synchronization.

If a descriptor modifies shared state:

```python
class CounterDescriptor:
    count = 0

    def __set__(self, instance, value):
        self.count += 1
```

multiple threads can interact with the shared descriptor object.

Remember:

```text
descriptor belongs to class
```

not:

```text
descriptor belongs to each instance
```

For shared mutable state, use appropriate synchronization or redesign the state ownership.

In async applications, avoid blocking operations in descriptor access paths.

## Descriptors and Security

Descriptors can enforce local access rules, but they should not become an invisible authorization system.

Avoid designs where:

```python
user.secret_data
```

implicitly performs complex permission checks based on global context.

Prefer explicit authorization:

```python
authorize(
    actor=current_user,
    resource=resource,
)
```

followed by access.

Security behavior should be visible at the application boundary.

Descriptors are better suited to:

- Type validation
- State validation
- Encapsulation
- Controlled attribute access

than authorization policy orchestration.

## Descriptors and Serialization

Descriptors can affect serialization behavior.

A serializer may inspect:

```python
obj.__dict__
```

and therefore bypass descriptor-defined computed behavior.

Conversely, a serializer may intentionally use:

```python
getattr(obj, field_name)
```

which invokes descriptors.

This means serialization libraries can interact with descriptors in different ways.

For external APIs, use explicit schemas rather than relying on arbitrary object introspection.

## Descriptors and Pickle

Descriptors themselves normally live on the class rather than inside each instance's serialized state.

However, descriptor-managed values may participate in serialization depending on how state is stored.

If a descriptor stores state externally, serialization can become complicated.

Before using descriptors with pickling or distributed object transport, define explicitly:

- What state is persisted?
- Where is it stored?
- How is it reconstructed?
- Is the descriptor itself serializable?
- Are external resources involved?

Avoid using Python object serialization as a substitute for a stable service contract.

## Descriptors and Microservices

Descriptors are process-local Python behavior.

They should not hide service-to-service communication.

Bad:

```python
class User:
    profile = RemoteProfileDescriptor()
```

where:

```python
user.profile
```

performs a gRPC request.

This makes a local-looking operation depend on:

- Network latency
- Remote availability
- Authentication
- Timeouts
- Retries
- Circuit breakers

Prefer:

```python
profile = await profile_client.get(user.id)
```

The distributed operation is then explicit.

## Descriptors and Caching

A descriptor can implement caching:

```python
class Cached:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name not in instance.__dict__:
            instance.__dict__[self.name] = compute(instance)

        return instance.__dict__[self.name]
```

This is appropriate for local, deterministic computations.

For distributed caches such as Redis, use explicit cache operations rather than hiding network access behind a descriptor.

```text
Application
    |
    v
Explicit cache operation
    |
    v
Redis
```

is easier to observe and reason about than:

```text
obj.value
    |
    v
Descriptor
    |
    v
Redis
```

## Descriptor Design Principles

Good descriptors usually have these properties:

- Single responsibility
- Clear lifecycle
- Explicit state ownership
- Predictable access semantics
- Minimal hidden work
- Well-defined type behavior
- No accidental global state
- Good testability

Avoid descriptors that combine:

```text
validation
+
database access
+
caching
+
authorization
+
logging
+
network calls
```

A descriptor should not become an entire application framework.

## When to Use Descriptors

Descriptors are appropriate when:

- Attribute access itself is the abstraction.
- The behavior is reusable across many classes.
- You need controlled attribute semantics.
- You are implementing a framework/library.
- You need custom validation or conversion.
- You are implementing a Python protocol.
- You need a reusable lazy or computed attribute mechanism.
- You are integrating deeply with Python's object model.

## When Not to Use Descriptors

Prefer simpler mechanisms when:

- A property is sufficient.
- A normal method is clearer.
- Constructor validation is sufficient.
- A dataclass provides the required behavior.
- Dependency injection is the real requirement.
- The behavior requires network or database I/O.
- The descriptor would hide important business operations.
- The mechanism would be difficult for normal application developers to understand.

A descriptor is a powerful abstraction, but power is not the same as appropriateness.

## Property vs Descriptor vs Method

| Requirement | Preferred mechanism |
|---|---|
| Simple stored state | Normal attribute |
| Cheap computed state | `@property` |
| Reusable attribute behavior across classes | Descriptor |
| Business operation | Method |
| Database operation | Repository/service method |
| External API call | Explicit client method |
| Dependency injection | Constructor injection |
| Cached local computation | `cached_property` |
| Framework-level attribute machinery | Descriptor when justified |

The simplest mechanism that correctly represents the semantics is usually the best choice.

## Descriptors and Testing

Descriptors should be tested through observable behavior.

```python
def test_positive_integer_field():
    product = Product()

    product.quantity = 10

    assert product.quantity == 10
```

Invalid input:

```python
def test_positive_integer_field_rejects_negative():
    product = Product()

    with pytest.raises(ValueError):
        product.quantity = -1
```

Class-level behavior:

```python
def test_descriptor_is_available_on_class():
    assert isinstance(Product.quantity, PositiveInt)
```

If a descriptor participates in inheritance, test the relevant MRO behavior as well.

## Descriptor Testing Matrix

For production descriptors, consider testing:

| Behavior | Test |
|---|---|
| Instance read | `obj.field` |
| Instance assignment | `obj.field = value` |
| Invalid assignment | Expected exception |
| Instance deletion | `del obj.field` |
| Class access | `Class.field` |
| Multiple instances | State isolation |
| Inheritance | Subclass behavior |
| Missing value | Defined failure semantics |
| Serialization | State preservation |
| Concurrency | Shared-state safety where relevant |

## Common Mistakes

### Confusing Descriptor and Property

A property is one specific descriptor implementation.

Descriptors are the broader mechanism.

### Storing Instance State on the Descriptor

Because descriptors live on classes, their state is shared.

### Forgetting `instance is None`

Class-level access often requires:

```python
if instance is None:
    return self
```

### Using `__getattribute__` Instead

`__getattribute__` intercepts virtually all attribute access on an instance and can be much more invasive than a targeted descriptor.

### Hiding I/O

Do not make:

```python
obj.customer
```

unexpectedly perform a network request unless a framework explicitly defines that behavior.

### Overusing Metaprogramming

A descriptor can make a design harder to understand than a normal property or method.

### Breaking `__dict__` Assumptions

Descriptors combined with `__slots__` may not have normal instance-dictionary storage.

### Ignoring Thread Safety

A shared descriptor can contain shared mutable state.

### Returning Incorrect Types

Descriptor contracts should be explicit and type-safe.

### Retaining Instances

External descriptor state that strongly references instances can create memory leaks.

## Production Pitfalls

| Pitfall | Impact | Better Approach |
|---|---|---|
| Shared mutable descriptor state | Cross-instance contamination | Store state on instances |
| Hidden database access | Latency/N+1 queries | Explicit repository/ORM loading |
| Hidden network access | Unpredictable failures | Explicit client calls |
| Complex descriptor logic | Difficult maintenance | Prefer property/method where possible |
| Missing class-access handling | Broken introspection | Handle `instance is None` |
| Strong instance references | Memory leaks | Use appropriate ownership/weak references |
| Ignoring MRO | Unexpected behavior | Understand descriptor lookup |
| Unclear typing | Static-analysis failures | Add appropriate annotations |
| Security hidden in descriptor | Hard-to-audit authorization | Explicit security checks |
| Descriptor used everywhere | Over-engineering | Reserve for reusable attribute semantics |

## Senior-Level Descriptor Reasoning

Descriptors are best understood as **attribute-level extension points in Python's object model**.

At an intermediate level:

```text
descriptor -> __get__ / __set__
```

At a senior level:

```text
attribute access
    |
    v
type/MRO lookup
    |
    v
data descriptor precedence
    |
    v
descriptor invocation
    |
    v
instance/class state
```

This knowledge becomes particularly valuable when debugging frameworks.

For example, if:

```python
order.customer
```

unexpectedly triggers a query, the correct question is not:

```text
"Why did Python randomly query the database?"
```

It is:

```text
"Which descriptor is managing this attribute, and what does its __get__ implementation do?"
```

That mental model scales from ordinary Python objects to ORM internals.

## Descriptor Debugging Workflow

When descriptor behavior is unexpected:

1. Inspect the class attribute.
2. Determine whether it implements `__get__`, `__set__`, or `__delete__`.
3. Check whether it is a data or non-data descriptor.
4. Inspect the class MRO.
5. Inspect the instance `__dict__`.
6. Determine which lookup rule wins.
7. Trace the descriptor implementation.
8. Check for hidden I/O or shared state.
9. Verify behavior under inheritance.
10. Add a focused regression test.

Useful inspection:

```python
descriptor = User.__dict__["email"]

print(type(descriptor))
print(hasattr(descriptor, "__get__"))
print(hasattr(descriptor, "__set__"))
print(hasattr(descriptor, "__delete__"))
```

For inherited descriptors:

```python
for cls in User.__mro__:
    if "email" in cls.__dict__:
        print(cls, cls.__dict__["email"])
```

## Descriptor Decision Framework

Before creating a custom descriptor, ask:

1. Is attribute access genuinely the right API?
2. Is the behavior reusable across multiple classes?
3. Is a normal attribute insufficient?
4. Is `@property` insufficient?
5. Is the behavior independent of infrastructure I/O?
6. Is state ownership explicit?
7. Does the descriptor need to be shared by all instances?
8. Are data-descriptor precedence rules understood?
9. Does inheritance affect behavior?
10. Is static typing manageable?
11. Can the behavior be tested independently?
12. Will a future maintainer understand the abstraction?

If a normal property solves the problem, prefer the property.

If a method makes the operation clearer, use the method.

Reserve custom descriptors for cases where the descriptor protocol itself provides meaningful architectural value.

## Production Checklist

Before shipping a custom descriptor:

- The descriptor solves a real reusable attribute-level problem.
- A normal attribute, property, or method was considered first.
- `__get__`, `__set__`, and `__delete__` semantics are explicit.
- Data vs non-data descriptor behavior is understood.
- `instance is None` is handled correctly where required.
- `__set_name__` is used when the descriptor needs its assigned attribute name.
- Per-instance state is not accidentally stored globally on the descriptor.
- Descriptor lifetime and ownership are understood.
- `__slots__` compatibility is verified where relevant.
- Inheritance and MRO behavior are tested.
- No unexpected database or network I/O occurs.
- No security-sensitive decisions are hidden inside attribute access.
- Concurrency behavior is safe.
- Memory retention has been considered.
- Serialization behavior is understood.
- Type annotations are appropriate.
- Tests cover instance, class, invalid, and inheritance behavior.
- The abstraction is simpler than the problem it solves.

## Key Takeaways

- Descriptors are Python's attribute-level protocol, primarily implemented through `__get__`, `__set__`, and `__delete__`, and they control how class-managed attributes behave.
- `property`, bound methods, `classmethod`, and `staticmethod` rely on descriptor machinery, making descriptors fundamental to understanding Python's object model.
- Data descriptors take precedence over instance attributes, while non-data descriptors can generally be shadowed by instance state; this distinction is critical when implementing custom descriptors.
- Django uses descriptors extensively to bridge Python objects and database-backed ORM behavior, which explains why seemingly simple attribute access can trigger queries and contribute to N+1 problems.
- Custom descriptors should be reserved for genuinely reusable attribute-level behavior; prefer normal attributes, properties, methods, or explicit dependency/repository operations when they provide a clearer design.