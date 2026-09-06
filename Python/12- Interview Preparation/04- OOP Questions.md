# 04- OOP Questions

## Overview

Object-oriented programming questions in Python test whether you understand both Python's object model and the design tradeoffs involved in building maintainable software.

Interviewers commonly move through three levels:

```text
Syntax
  │
  ▼
Python Object Model
  │
  ▼
Design Reasoning
```

A strong answer should therefore cover:

- what the feature does;
- how Python implements or resolves it;
- when it is appropriate;
- what tradeoffs it introduces;
- how it affects testing and maintainability;
- how it behaves in production systems.

Python OOP differs from class-based languages such as Java or C++ in important ways. Python supports inheritance and encapsulation, but also emphasizes:

- dynamic typing;
- duck typing;
- protocols;
- composition;
- first-class functions;
- descriptors;
- multiple inheritance;
- runtime introspection.

---

## Python Object Model

In Python, classes and instances are objects.

```text
object
  │
  ├── instance
  │
  ├── class
  │
  └── metaclass
```

A simplified relationship is:

```python
class Customer:
    pass


customer = Customer()
```

Conceptually:

```text
Customer
   │
   │ creates
   ▼
customer
```

`customer` is an instance of `Customer`, while `Customer` itself is an instance of its metaclass, normally `type`.

---

## Class vs Instance

A class defines behavior and can provide class-level attributes.

An instance represents a particular object created from that class.

```python
class Customer:
    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id


customer = Customer("cust-123")
```

Here:

```text
Customer
  │
  └── class definition

customer
  │
  └── instance
       └── customer_id = "cust-123"
```

---

## Instance Attributes

Instance attributes belong to individual objects.

```python
class Connection:
    def __init__(self, host: str) -> None:
        self.host = host


primary = Connection("db-primary")
replica = Connection("db-replica")
```

The instances have independent `host` attributes.

Instance state is commonly stored in the instance's `__dict__` unless the class uses mechanisms such as `__slots__`.

---

## Class Attributes

Class attributes belong to the class and can be accessed through instances when lookup finds them there.

```python
class Connection:
    default_timeout = 5.0
```

Both:

```python
Connection.default_timeout
```

and:

```python
connection.default_timeout
```

can access the class attribute.

However, assigning:

```python
connection.default_timeout = 10.0
```

normally creates an instance attribute rather than modifying the class attribute.

---

## Attribute Lookup

Python's attribute lookup is more sophisticated than simply checking `obj.__dict__`.

A simplified model involves:

```text
obj.attribute
     │
     ▼
Descriptor rules
     │
     ▼
Instance attributes
     │
     ▼
Class / MRO attributes
     │
     ▼
__getattr__ fallback
```

The exact behavior depends on descriptors, inheritance, and whether the attribute is being read, written, or deleted.

This is an important foundation for understanding:

- properties;
- methods;
- `classmethod`;
- `staticmethod`;
- ORM fields;
- framework dependency injection.

---

## Methods

Functions defined in a class become methods when accessed through an instance.

```python
class CustomerService:
    def get_customer(self, customer_id: str) -> Customer:
        ...
```

Calling:

```python
service.get_customer("cust-123")
```

implicitly supplies the instance as the first argument.

Conceptually:

```python
CustomerService.get_customer(
    service,
    "cust-123",
)
```

This binding behavior is enabled by Python's descriptor machinery.

---

## `self`

`self` is a conventional parameter name representing the instance.

It is not a language keyword.

```python
class Customer:
    def __init__(self, customer_id: str) -> None:
        self.customer_id = customer_id
```

Using another name would technically work, but `self` is the established Python convention and should always be preferred.

---

## `__init__` vs `__new__`

A common interview question is the difference between `__new__` and `__init__`.

```text
Class call
    │
    ▼
__new__()
    │
    ▼
Create / return instance
    │
    ▼
__init__()
    │
    ▼
Initialize instance
```

`__new__` controls instance creation.

`__init__` initializes an already-created instance.

Most application code only needs `__init__`.

`__new__` is relevant for advanced cases such as:

- immutable types;
- metaprogramming;
- custom object creation;
- singleton-like mechanisms.

---

## Encapsulation

Python does not enforce traditional private fields in the same way as languages with access modifiers.

Convention:

```python
class Account:
    def __init__(self, balance: Decimal) -> None:
        self._balance = balance
```

A single leading underscore means:

> Internal implementation detail; do not treat this as public API.

Double leading underscores trigger name mangling:

```python
class Account:
    def __init__(self) -> None:
        self.__balance = Decimal("0")
```

This becomes approximately:

```text
_Account__balance
```

Name mangling is primarily intended to avoid accidental name collisions in inheritance hierarchies, not to provide true security.

---

## Properties

Properties expose method-backed behavior through attribute syntax.

```python
class Account:
    def __init__(self, balance: Decimal) -> None:
        self._balance = balance

    @property
    def balance(self) -> Decimal:
        return self._balance
```

Usage:

```python
account.balance
```

instead of:

```python
account.balance()
```

Properties are useful when:

- validation is required;
- derived values are calculated;
- the implementation may evolve;
- an attribute-like API is appropriate.

Avoid expensive I/O inside properties because attribute access conventionally appears cheap.

---

## Inheritance

Inheritance allows a class to derive behavior from another class.

```python
class PaymentProcessor:
    def process(self, payment: Payment) -> None:
        ...


class CardPaymentProcessor(PaymentProcessor):
    def process(self, payment: Payment) -> None:
        ...
```

Inheritance can express an "is-a" relationship, but it introduces coupling between the base class and subclasses.

---

## Composition

Composition builds objects from other objects.

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        publisher: EventPublisher,
    ) -> None:
        self.repository = repository
        self.publisher = publisher
```

The service **uses** a repository and publisher rather than inheriting from them.

For backend systems, composition is often preferable because it supports:

- dependency injection;
- testing;
- replacement of implementations;
- smaller abstractions;
- clearer ownership.

---

## Composition vs Inheritance

| Concern | Inheritance | Composition |
|---|---|---|
| Relationship | Is-a | Has-a / uses-a |
| Coupling | Usually higher | Usually lower |
| Runtime replacement | Less flexible | Easier |
| Testing | Can be more coupled | Usually easier |
| Reuse | Via hierarchy | Via delegation |
| Best use | Genuine subtype relationship | Collaborating components |

Do not treat composition as universally superior. Inheritance is appropriate when substitutability and shared semantics are real.

---

## Polymorphism

Polymorphism allows code to operate against a common interface while implementations vary.

```python
class PaymentProcessor(Protocol):
    def process(self, payment: Payment) -> None:
        ...


def checkout(
    processor: PaymentProcessor,
    payment: Payment,
) -> None:
    processor.process(payment)
```

The caller does not need to know whether the implementation uses:

- Stripe;
- an internal processor;
- a test fake;
- another payment provider.

This is especially valuable at infrastructure boundaries.

---

## Duck Typing

Python often uses duck typing:

> If an object provides the required behavior, its concrete class does not necessarily matter.

```python
def publish(publisher) -> None:
    publisher.publish("order.created")
```

Any compatible object can work.

Duck typing is flexible but can make interfaces less explicit.

Protocols and type checking can provide stronger contracts without requiring inheritance.

---

## Abstract Base Classes

The `abc` module supports explicit abstract interfaces.

```python
from abc import ABC, abstractmethod


class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, payment: Payment) -> None:
        ...
```

Subclasses must implement the abstract method before they can be instantiated.

ABCs are useful when:

- a formal nominal hierarchy is appropriate;
- shared behavior exists;
- abstract contracts should be explicit.

They are not required merely to define an interface in Python.

---

## Protocols vs ABCs

| Feature | Protocol | ABC |
|---|---|---|
| Typing model | Structural | Nominal |
| Explicit inheritance required | No | Usually |
| Runtime enforcement | Limited by default | Abstract methods affect instantiation |
| Static typing | Excellent | Excellent |
| Duck-typed implementations | Natural | Less direct |
| Typical use | Loose boundaries / DI | Explicit class hierarchy |

For backend dependency boundaries, protocols are often an excellent fit.

---

## Method Resolution Order

Python uses Method Resolution Order, or MRO, to determine where attributes and methods are found through inheritance.

```python
class A:
    ...


class B(A):
    ...


class C(B):
    ...
```

The MRO can be inspected:

```python
print(C.mro())
```

Conceptually:

```text
C → B → A → object
```

Python uses the C3 linearization algorithm for MRO.

---

## Multiple Inheritance

Python supports multiple inheritance.

```python
class Auditable:
    ...


class Serializable:
    ...


class Order(Auditable, Serializable):
    ...
```

The MRO determines how methods are resolved.

Multiple inheritance can be useful for carefully designed mixins, but large inheritance graphs can become difficult to reason about.

---

## Mixins

A mixin provides reusable behavior rather than representing a complete domain entity.

```python
class AuditMixin:
    def audit(self, action: str) -> None:
        logger.info("action=%s", action)


class Order(AuditMixin):
    ...
```

Mixins should generally be:

- small;
- focused;
- minimally stateful;
- explicit about dependencies.

Avoid deep or heavily stateful mixin hierarchies.

---

## `super()`

`super()` delegates to the next implementation according to the MRO.

```python
class BaseService:
    def process(self) -> None:
        ...


class OrderService(BaseService):
    def process(self) -> None:
        super().process()
        ...
```

An important interview point:

> `super()` does not simply mean "call my parent."

It means to continue method lookup according to the MRO.

This distinction becomes important with multiple inheritance.

---

## Cooperative Multiple Inheritance

Well-designed multiple inheritance can use cooperative `super()` calls.

```python
class LoggingMixin:
    def process(self) -> None:
        logger.info("processing")
        super().process()


class ValidationMixin:
    def process(self) -> None:
        validate()
        super().process()


class BaseService:
    def process(self) -> None:
        execute()


class Service(LoggingMixin, ValidationMixin, BaseService):
    pass
```

The MRO determines the execution chain.

Every participating class must cooperate correctly.

If one class directly invokes a specific parent instead of `super()`, it can break the cooperative chain.

---

## Method Overriding

A subclass can replace inherited behavior.

```python
class BaseRepository:
    def save(self, entity: Entity) -> None:
        ...


class PostgresRepository(BaseRepository):
    def save(self, entity: Entity) -> None:
        ...
```

Overriding should preserve the conceptual contract of the parent when substitutability is expected.

Changing:

- accepted input assumptions;
- return semantics;
- exception behavior;

can violate that contract.

---

## Liskov Substitution Principle

The Liskov Substitution Principle means that a subtype should be usable wherever the base abstraction is expected without breaking correctness.

A common violation is a subclass that accepts less input or provides substantially different semantics than the base contract.

Before using inheritance, ask:

> Is this genuinely a substitutable subtype?

If not, composition may be more appropriate.

---

## Dependency Injection

Dependency injection supplies collaborators from outside the class.

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        publisher: EventPublisher,
    ) -> None:
        self.repository = repository
        self.publisher = publisher
```

This avoids hard-coding:

```python
self.repository = PostgresOrderRepository()
```

inside the service.

Benefits include:

- easier testing;
- loose coupling;
- configuration flexibility;
- clearer ownership.

---

## Dependency Injection in FastAPI

FastAPI can provide dependencies through function parameters.

```python
@router.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    order = await service.create(request)
    return OrderResponse.from_domain(order)
```

The framework manages dependency construction and request-level lifecycle where configured.

The underlying architectural principle remains ordinary dependency injection.

---

## Encapsulation and Domain Logic

Avoid creating classes that merely wrap data without meaningful behavior when a dataclass or simpler structure would be clearer.

Prefer domain-oriented behavior:

```python
class Order:
    def cancel(self) -> None:
        if self.status == OrderStatus.SHIPPED:
            raise InvalidOrderState("Shipped orders cannot be cancelled.")

        self.status = OrderStatus.CANCELLED
```

The invariant is kept close to the state it protects.

---

## Anemic Domain Models

An anemic model contains data while business behavior exists elsewhere.

This is not automatically wrong.

For CRUD-heavy systems, simple models plus service-layer logic can be appropriate.

The important question is:

> Where should business invariants live so they cannot be bypassed accidentally?

Complex domain invariants may justify richer domain objects.

---

## Dataclasses and OOP

Dataclasses are useful when the primary purpose of a class is representing data.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerId:
    value: str
```

Use ordinary classes when substantial custom behavior or lifecycle management is needed.

Do not create elaborate class hierarchies when a dataclass and a few functions would express the domain more clearly.

---

## `__slots__`

`__slots__` can restrict instance attributes and reduce per-instance memory overhead in suitable cases.

```python
class Customer:
    __slots__ = ("customer_id", "status")

    def __init__(self, customer_id: str, status: str) -> None:
        self.customer_id = customer_id
        self.status = status
```

Tradeoffs include:

- no normal instance `__dict__` unless explicitly included;
- restrictions on dynamically adding attributes;
- inheritance considerations;
- compatibility concerns with some frameworks and tooling.

Use it based on measured memory requirements, not as a default optimization.

---

## Dunder Methods

Dunder methods define protocol behavior.

Examples:

| Method | Purpose |
|---|---|
| `__init__` | Initialization |
| `__new__` | Instance creation |
| `__repr__` | Developer-oriented representation |
| `__str__` | User-oriented string representation |
| `__eq__` | Equality |
| `__hash__` | Hashing |
| `__len__` | Length |
| `__iter__` | Iteration |
| `__getitem__` | Subscription |
| `__enter__` | Context manager entry |
| `__exit__` | Context manager exit |
| `__call__` | Callable instance |

Implement protocols when they make the object naturally integrate with Python.

Avoid implementing magic methods merely to appear sophisticated.

---

## `__repr__` vs `__str__`

`__repr__` should generally provide a useful developer-facing representation.

```python
class Customer:
    def __repr__(self) -> str:
        return f"Customer(id={self.customer_id!r})"
```

`__str__` is intended for a more user-oriented representation.

Avoid including secrets or sensitive information in either.

For example, never expose:

- passwords;
- access tokens;
- session credentials;
- private keys.

This is a production security concern because objects frequently appear in logs and error messages.

---

## Equality

Implementing `__eq__` changes object comparison semantics.

```python
class CustomerId:
    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CustomerId):
            return NotImplemented

        return self.value == other.value
```

Returning `NotImplemented` for unsupported operand types allows Python to try the appropriate reflected comparison behavior.

---

## Hashing

Objects used as dictionary keys or set members need compatible hashing behavior.

The contract is:

```text
a == b
    ⇒
hash(a) == hash(b)
```

If equality depends on mutable state, using the object as a hash key can be dangerous.

Immutable value objects are often a better fit for hash-based identity.

---

## `__call__`

Objects can be made callable.

```python
class RateLimiter:
    def __init__(self, limit: int) -> None:
        self.limit = limit

    def __call__(self, request: Request) -> bool:
        return check_limit(request, self.limit)
```

Usage:

```python
limiter(request)
```

Callable objects are useful when behavior requires persistent state or configuration.

---

## Descriptors

Descriptors customize attribute access through methods such as:

- `__get__`;
- `__set__`;
- `__delete__`.

Properties are implemented using descriptor machinery.

Descriptors underpin important Python features and frameworks, including:

- methods;
- properties;
- ORM fields;
- validation systems;
- class-level managed attributes.

A simplified descriptor:

```python
class Positive:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("Value must be positive")

        instance.__dict__[self.name] = value
```

Descriptors are powerful but should be introduced only when the abstraction genuinely requires them.

---

## Class Methods

`@classmethod` receives the class as its first argument.

```python
class Customer:
    @classmethod
    def from_dict(
        cls,
        data: dict[str, str],
    ) -> "Customer":
        return cls(data["id"])
```

Common uses include:

- alternate constructors;
- factory methods;
- class-level configuration.

---

## Static Methods

`@staticmethod` does not receive an implicit instance or class.

```python
class CustomerValidator:
    @staticmethod
    def validate_id(customer_id: str) -> bool:
        return customer_id.startswith("cust-")
```

However, if a function has no meaningful relationship to the class, a module-level function may be clearer.

Do not use `staticmethod` simply because a function happens to be located inside a class.

---

## Class Method vs Static Method

| Feature | Instance method | Class method | Static method |
|---|---|---|---|
| Implicit first argument | `self` | `cls` | None |
| Access instance state | Yes | No | No |
| Access class state | Yes | Yes | Only explicitly |
| Typical use | Object behavior | Alternate constructors | Class-related utility |

---

## Properties vs Methods

Prefer a property when access conceptually represents an attribute:

```python
order.total
```

Prefer a method when the operation:

- performs meaningful work;
- has side effects;
- accepts significant parameters;
- may be expensive.

Avoid hiding database queries behind properties:

```python
order.customer
```

if accessing it unexpectedly performs network or database I/O.

---

## Multiple Inheritance Interview Trap

Consider:

```python
class A:
    def process(self):
        print("A")


class B(A):
    def process(self):
        print("B")
        super().process()


class C(A):
    def process(self):
        print("C")
        super().process()


class D(B, C):
    def process(self):
        print("D")
        super().process()
```

The MRO is:

```text
D → B → C → A → object
```

Calling:

```python
D().process()
```

produces:

```text
D
B
C
A
```

The key point is that `super()` follows the MRO rather than simply jumping to one named parent.

---

## OOP and Testing

Good OOP design can improve testability when dependencies are explicit.

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
    ) -> None:
        self.repository = repository
```

A test can supply a fake:

```python
class FakeOrderRepository:
    async def save(self, order: Order) -> None:
        self.orders.append(order)
```

This avoids patching global constructors throughout the test suite.

However, abstraction should not be added solely for mocking. Integration tests are still required to verify real PostgreSQL, Redis, Kafka, or HTTP behavior.

---

## OOP and Concurrency

Instance state can become shared mutable state.

```python
class Counter:
    def __init__(self) -> None:
        self.value = 0
```

If one instance is accessed concurrently by multiple threads or tasks, synchronization may be required.

In a web application, carefully distinguish:

```text
Request-scoped object
        vs
Process-wide singleton
        vs
Distributed state
```

A class being instantiated once does not automatically make it thread-safe.

---

## OOP and Dependency Lifetimes

Backend applications often contain objects with different lifetimes:

```text
Application lifetime
    │
    ├── Configuration
    └── Connection pool
          │
          ▼
Request lifetime
    │
    ├── Request context
    └── Service dependencies
          │
          ▼
Operation lifetime
    │
    └── Transaction
```

A common production mistake is allowing a long-lived object to retain short-lived state.

This can cause:

- memory leaks;
- stale data;
- request cross-contamination;
- security issues;
- connection misuse.

---

## OOP and Serialization

Not every Python object should be serialized directly.

Domain objects often need explicit transformation:

```text
Domain object
     │
     ▼
DTO / response model
     │
     ▼
JSON
```

This protects API contracts from accidental exposure of:

- internal fields;
- database implementation details;
- secrets;
- mutable internal state.

---

## OOP and ORMs

Django and SQLAlchemy use rich object models around database records.

An ORM model can provide:

- fields;
- validation hooks;
- relationships;
- query interfaces;
- lifecycle behavior.

But ORM models should not automatically become the application's entire domain model.

For complex systems, separating:

```text
Persistence model
        │
        ▼
Domain model
        │
        ▼
API DTO
```

can reduce coupling.

---

## OOP Design Principles

Important principles include:

- Single Responsibility Principle;
- Open/Closed Principle;
- Liskov Substitution Principle;
- Interface Segregation Principle;
- Dependency Inversion Principle.

These are useful as design heuristics rather than rigid rules.

---

## Single Responsibility Principle

A class should have a focused responsibility.

Avoid:

```text
OrderService
 ├── validate request
 ├── calculate tax
 ├── query database
 ├── send email
 ├── publish Kafka event
 ├── generate PDF
 └── format HTTP response
```

This makes testing and change management difficult.

Prefer clear boundaries where responsibilities are genuinely distinct.

---

## Open/Closed Principle

Code should generally be open to extension without requiring repeated modification of stable behavior.

Protocols and dependency injection can help:

```python
class NotificationSender(Protocol):
    def send(self, message: Message) -> None:
        ...
```

Different implementations can be introduced without rewriting the business logic that depends on the protocol.

---

## Interface Segregation

Avoid forcing consumers to depend on methods they do not need.

Instead of:

```python
class HugeRepository(Protocol):
    def create(...): ...
    def delete(...): ...
    def export(...): ...
    def rebuild_index(...): ...
    def archive(...): ...
```

prefer smaller interfaces when consumers require only a subset.

Small protocols are particularly useful for dependency injection.

---

## Dependency Inversion

High-level business logic should depend on abstractions rather than concrete infrastructure where that separation provides value.

```text
OrderService
     │
     ▼
OrderRepository protocol
     ▲
     │
 ┌───┴─────────────┐
 │                 │
PostgreSQL       Fake
```

This makes infrastructure replaceable and business logic easier to test.

---

## When Not to Use OOP

Not every problem requires classes.

A small transformation may be clearer as:

```python
def normalize_email(email: str) -> str:
    return email.strip().lower()
```

Use classes when they provide meaningful:

- state;
- lifecycle;
- identity;
- polymorphism;
- encapsulated invariants;
- collaboration boundaries.

Avoid creating classes solely because "everything should be an object."

---

## Common OOP Mistakes

### Deep Inheritance Trees

Deep hierarchies make behavior difficult to trace.

Prefer composition when inheritance does not provide genuine substitutability.

### God Classes

A class responsible for everything becomes difficult to test and evolve.

### Excessive Abstraction

Do not create interfaces for every class without a real variation point.

### Hidden Dependencies

Constructing infrastructure directly inside domain services increases coupling.

### Mutable Class Attributes

```python
class Service:
    cache = {}
```

This creates shared state across instances.

### Overusing `staticmethod`

A function without meaningful class semantics may belong at module level.

### Misusing `super()`

`super()` follows the MRO; it is not simply a direct parent call.

### Treating `_name` as Security

Underscore conventions provide no access-control security.

### Exposing Internal State

Returning mutable internal collections can allow callers to modify object state unexpectedly.

---

## Production OOP Checklist

When reviewing a class, ask:

- [ ] Does the class have a clear responsibility?
- [ ] Is its public API minimal?
- [ ] Are dependencies explicit?
- [ ] Is inheritance actually required?
- [ ] Would composition be clearer?
- [ ] Is shared mutable state intentional?
- [ ] Is object lifetime appropriate?
- [ ] Is the class safe under concurrent access?
- [ ] Are invariants enforced?
- [ ] Are sensitive fields protected from logs and serialization?
- [ ] Is the class easy to test?
- [ ] Does it depend on concrete infrastructure unnecessarily?
- [ ] Are abstractions justified by actual variation?
- [ ] Could a function or dataclass express the design more clearly?

---

## Interview Question Matrix

| Question | Core concept | Senior-level angle |
|---|---|---|
| What is `self`? | Instance reference | Method binding |
| Class vs instance attribute? | Attribute lookup | Shared vs per-instance state |
| `__new__` vs `__init__`? | Object creation | Immutable/custom creation |
| What is inheritance? | Reuse/subtyping | Coupling and substitutability |
| Composition vs inheritance? | Design | Maintainability and DI |
| What is MRO? | Method resolution | C3 linearization |
| What does `super()` do? | Cooperative inheritance | MRO-aware delegation |
| What is polymorphism? | Common interface | Decoupled architecture |
| ABC vs Protocol? | Interfaces | Nominal vs structural typing |
| What is a descriptor? | Attribute protocol | Properties and framework internals |
| `classmethod` vs `staticmethod`? | Method binding | API design |
| What is encapsulation in Python? | State boundaries | Convention vs enforcement |
| What are dunder methods? | Python protocols | Natural language integration |
| When should you avoid OOP? | Design judgment | Simplicity and maintainability |

---

## Senior-Level OOP Scenario

Suppose an application processes payments through multiple providers.

A tightly coupled design might be:

```python
class PaymentService:
    def __init__(self) -> None:
        self.client = StripeClient()
```

This couples the service directly to one implementation.

A more flexible design is:

```python
from typing import Protocol


class PaymentProvider(Protocol):
    async def charge(
        self,
        payment: Payment,
    ) -> PaymentResult:
        ...


class PaymentService:
    def __init__(
        self,
        provider: PaymentProvider,
    ) -> None:
        self.provider = provider

    async def charge(
        self,
        payment: Payment,
    ) -> PaymentResult:
        return await self.provider.charge(payment)
```

The architecture becomes:

```text
                 PaymentProvider
                       ▲
                       │
              ┌────────┴────────┐
              │                 │
        StripeProvider     InternalProvider
              │                 │
              └────────┬────────┘
                       │
                       ▼
                 PaymentService
                       │
                       ▼
                  API Handler
```

The service is now easier to test and less coupled to a specific provider.

---

## Interview Answer Framework

For OOP questions, structure answers as:

```text
What is it?
    │
    ▼
How does Python implement it?
    │
    ▼
When would you use it?
    │
    ▼
What are the tradeoffs?
    │
    ▼
How does it affect testing and production?
```

For design questions:

```text
Requirements
    │
    ▼
Identify responsibilities
    │
    ▼
Define boundaries
    │
    ▼
Choose composition / inheritance
    │
    ▼
Define interfaces
    │
    ▼
Inject dependencies
    │
    ▼
Consider concurrency + failure
```

---

## Key Takeaways

- **Python OOP is built on a dynamic object model:** classes, instances, methods, descriptors, inheritance, and MRO all participate in runtime behavior.
- **Prefer composition when relationships are collaborative rather than genuinely substitutive:** explicit dependencies improve testing, maintainability, and infrastructure flexibility.
- **Understand Python-specific OOP mechanisms:** `super()` follows the MRO, protocols provide structural interfaces, descriptors power attribute behavior, and `_name` conventions are not security boundaries.
- **Use abstractions where they solve real design problems:** protocols, ABCs, mixins, dataclasses, and dependency injection should reduce coupling or express meaningful domain behavior rather than add ceremony.
- **Senior-level OOP reasoning includes production concerns:** object lifetime, shared mutable state, concurrency, serialization, sensitive data exposure, testing, scalability, and infrastructure boundaries matter as much as class syntax.