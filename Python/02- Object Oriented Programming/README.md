# README

## Overview

This folder covers Python Object-Oriented Programming (OOP) from core object semantics through production-oriented design techniques.

The goal is not to make every Python application class-heavy. Python supports multiple programming styles, and effective backend engineering combines:

- Functions
- Modules
- Classes
- Composition
- Inheritance
- Protocols
- Abstract Base Classes
- Dataclasses
- Dependency Injection
- Encapsulation
- Polymorphism
- Abstraction
- Design principles

The emphasis in this section is on understanding **when object-oriented techniques improve a system and when they introduce unnecessary complexity**.

A production backend commonly uses OOP at boundaries such as:

```text
HTTP/API
   |
   v
Application Services
   |
   +--> Domain Models
   |
   +--> Repositories
   |
   +--> External API Clients
   |
   +--> Cache
   |
   +--> Message Publishers
```

The important engineering skill is being able to design these relationships deliberately.

## What This Folder Covers

The material progresses from Python's object model to increasingly advanced design concepts:

```text
Object Model
    |
    v
Classes and Objects
    |
    v
Instance/Class State
    |
    v
Initialization
    |
    v
Encapsulation
    |
    +--> Inheritance
    |       |
    |       +--> MRO
    |       +--> Multiple Inheritance
    |       +--> super()
    |
    +--> Composition
    |
    +--> Polymorphism
    |
    +--> Abstraction
    |       |
    |       +--> ABCs
    |       +--> Protocols
    |
    +--> Descriptors
    |       |
    |       +--> Properties
    |
    +--> Dependency Injection
            |
            v
      OOP Design Principles
```

## Learning Path

### Fundamentals of Python OOP

Start by understanding how Python represents objects and how classes provide structure around state and behavior.

| # | File | Topic | Primary Focus |
|---|---|---|---|
| 01 | [OOP Fundamentals](01-%20OOP%20Fundamentals.md) | OOP Fundamentals | Python's object model and OOP concepts |
| 02 | [Classes and Objects](02-%20Classes%20and%20Objects.md) | Classes and Objects | Class definitions, instances, identity, namespaces |
| 03 | [Instance Attributes and Methods](03-%20Instance%20Attributes%20and%20Methods.md) | Instance Attributes and Methods | Object state and instance behavior |
| 04 | [Class Attributes and Methods](04-%20Class%20Attributes%20and%20Methods.md) | Class Attributes and Methods | Class-level state and behavior |
| 05 | [Constructors and Initialization](05-%20Constructors%20and%20Initialization.md) | Constructors and Initialization | `__new__`, `__init__`, object lifecycle |

These concepts establish the mechanics required for understanding more advanced object-oriented design.

### Encapsulation and Relationships

The next group focuses on controlling state and expressing relationships between objects.

| # | File | Topic | Primary Focus |
|---|---|---|---|
| 06 | [Encapsulation](06-%20Encapsulation.md) | Encapsulation | Controlling state and implementation details |
| 07 | [Inheritance](07-%20Inheritance.md) | Inheritance | Reusing and specializing behavior |
| 08 | [Composition](08-%20Composition.md) | Composition | Building behavior from collaborating objects |
| 09 | [Polymorphism](09-%20Polymorphism.md) | Polymorphism | Interchangeable implementations and runtime behavior |
| 10 | [Abstraction](10-%20Abstraction.md) | Abstraction | Stable behavioral boundaries |

A key engineering principle is:

```text
Inheritance models "is-a".
Composition models "has-a" or "uses-a".
```

In backend systems, composition is frequently the better default.

### Advanced Python Object Model

These topics explain mechanisms that are important for understanding Python's runtime behavior.

| # | File | Topic | Primary Focus |
|---|---|---|---|
| 11 | [Method Resolution Order](11-%20Method%20Resolution%20Order.md) | Method Resolution Order | MRO and C3 linearization |
| 12 | [Multiple Inheritance](12-%20Multiple%20Inheritance.md) | Multiple Inheritance | Multiple parent classes and cooperative inheritance |
| 13 | [Super](13-%20Super.md) | `super()` | MRO-aware delegation |
| 14 | [Dunder Methods](14-%20Dunder%20Methods.md) | Dunder Methods | Python data model and special methods |
| 15 | [Properties](15-%20Properties.md) | Properties | Managed attribute access |
| 16 | [Descriptors](16-%20Descriptors.md) | Descriptors | Attribute-level runtime customization |

These mechanisms appear directly or indirectly in major Python frameworks.

For example:

```text
Python descriptors
       |
       +--> property
       +--> methods
       +--> classmethod
       +--> staticmethod
       |
       v
Framework behavior
       |
       +--> Django ORM
       +--> Python object model
```

Understanding these mechanisms makes framework behavior easier to debug rather than treating it as magic.

## Abstractions and Dependency Management

The final concepts focus on designing boundaries between business logic and implementation details.

| # | File | Topic | Primary Focus |
|---|---|---|---|
| 17 | [Abstract Base Classes](17-%20Abstract%20Base%20Classes.md) | Abstract Base Classes | Nominal contracts and runtime abstraction |
| 18 | [Protocols](18-%20Protocols.md) | Protocols | Structural typing and behavioral contracts |
| 19 | [Dependency Injection](19-%20Dependency%20Injection.md) | Dependency Injection | Explicit dependency composition |
| 20 | [OOP Design Principles](20-%20OOP%20Design%20Principles.md) | OOP Design Principles | SOLID and practical object-oriented design |

These concepts are particularly relevant to backend architecture.

A typical dependency graph might look like:

```text
                    Composition Root
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    PostgreSQL          Redis           HTTP Client
          |                |                |
          v                v                v
     Repository          Cache        External Adapter
          \                |                /
           \               |               /
            +--------------+--------------+
                           |
                           v
                   Application Service
                           |
                           v
                       API Layer
```

## Core Concepts

### Classes and Objects

A class defines behavior and structure.

An object is an instance with its own identity and state.

```python
class Order:
    def __init__(self, order_id: int) -> None:
        self.order_id = order_id


order = Order(order_id=1001)
```

Important concepts include:

- Identity
- Type
- State
- Behavior
- Attribute lookup
- Instance namespace
- Class namespace

### Encapsulation

Encapsulation protects invariants and implementation details.

Instead of allowing arbitrary state mutation:

```python
order.status = "paid"
```

a domain model may expose:

```python
order.mark_paid()
```

The latter allows the object to enforce valid state transitions.

### Inheritance

Inheritance allows one class to derive behavior from another.

```python
class AdminUser(User):
    ...
```

It should generally represent a genuine subtype relationship rather than merely being a mechanism for code reuse.

### Composition

Composition assembles behavior from independent collaborators.

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        payment_gateway: PaymentGateway,
    ) -> None:
        self.repository = repository
        self.payment_gateway = payment_gateway
```

This pattern is especially useful for backend infrastructure.

### Polymorphism

Polymorphism allows application code to operate against a stable contract while implementations vary.

```text
PaymentGateway
    |
    +--> Stripe
    +--> Adyen
    +--> Fake/Test implementation
```

The application service should not need to know which implementation is active.

### Abstraction

Abstraction exposes required behavior while hiding implementation details.

A useful abstraction should represent a meaningful boundary rather than simply wrapping an existing class.

### Protocols

Python protocols provide structural typing.

```python
from typing import Protocol


class Cache(Protocol):
    async def get(self, key: str) -> bytes | None:
        ...
```

An implementation does not need to inherit from `Cache` if it satisfies the required structure.

Protocols are particularly useful for dependency boundaries.

### Abstract Base Classes

ABCs provide nominal abstraction and runtime enforcement.

They are useful when:

- A class hierarchy is intentional.
- Shared implementation exists.
- Runtime abstractness matters.
- Framework extension points require inheritance.

Protocols are often preferable when structural typing is sufficient.

### Dependency Injection

Dependency injection supplies collaborators from outside an object.

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
        payment_gateway: PaymentGateway,
    ) -> None:
        self.repository = repository
        self.payment_gateway = payment_gateway
```

This improves:

- Testability
- Dependency visibility
- Configuration
- Separation of concerns
- Implementation substitution

## Python's Object Model

Python uses a unified object model in which classes themselves are objects.

Important relationships include:

```text
object
  ^
  |
Base classes
  ^
  |
User-defined classes
  ^
  |
Instances
```

A class has its own namespace and participates in Python's attribute lookup rules.

For example:

```python
class User:
    role = "user"

    def __init__(self, name: str) -> None:
        self.name = name
```

Here:

```text
User
 ├── role
 └── __dict__ / class namespace

user = User("Alice")
 └── name
```

Understanding attribute lookup is important for:

- Inheritance
- Properties
- Descriptors
- Class attributes
- Method binding
- MRO

## Attribute Lookup

A simplified model is:

```text
instance.attribute
       |
       v
Data descriptors on class/MRO
       |
       v
Instance namespace
       |
       v
Non-data descriptors / class attributes
       |
       v
Base classes following MRO
```

This explains why Python features such as properties and methods can control attribute behavior.

For advanced work, understanding descriptor precedence and MRO is more valuable than memorizing isolated rules.

## Object Lifecycle

Object creation generally involves:

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
Initialized instance
```

`__new__` controls object creation.

`__init__` initializes an already-created instance.

Most application classes only need `__init__`.

## Instance vs Class State

Instance state belongs to a specific object:

```python
class User:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
```

Class state is shared through the class:

```python
class User:
    default_role = "user"
```

Be careful with mutable class attributes:

```python
class Registry:
    items = []
```

All instances may share the same list.

This can create unexpected state leakage.

## Inheritance and MRO

Python supports multiple inheritance.

```python
class ServiceMixin:
    ...


class AuditedService:
    ...


class OrderService(ServiceMixin, AuditedService):
    ...
```

Python determines method lookup using the Method Resolution Order.

```python
OrderService.__mro__
```

C3 linearization produces a deterministic order.

`super()` follows that MRO rather than simply calling "the parent."

This matters for cooperative multiple inheritance and mixins.

## Composition vs Inheritance

A practical decision rule:

| Situation | Preferred Design |
|---|---|
| Genuine subtype relationship | Inheritance |
| Shared infrastructure collaborator | Composition |
| Replaceable implementation | Composition + Protocol |
| Framework extension point | Often inheritance |
| Optional behavior | Composition |
| Independent services | Composition |
| Small reusable cross-cutting behavior | Composition or mixin |
| Deep hierarchy | Usually avoid |
| Provider integration | Adapter + composition |

Prefer composition unless inheritance provides a clear semantic advantage.

## Dunder Methods

Dunder methods implement Python protocols.

Examples:

```python
__init__
__repr__
__str__
__eq__
__hash__
__iter__
__next__
__enter__
__exit__
__call__
```

They allow user-defined objects to participate naturally in Python operations.

Use dunder methods for language-level semantics.

Use explicit methods for business operations.

Good:

```python
invoice.total()
```

Less appropriate:

```python
invoice.__calculate_total__()
```

## Properties

Properties allow attribute syntax to invoke controlled behavior.

```python
class User:
    @property
    def display_name(self) -> str:
        return self.first_name + " " + self.last_name
```

Properties work well for:

- Derived state
- Validation
- Encapsulated attributes
- Cheap computed values

Avoid properties for expensive I/O or surprising side effects.

Prefer:

```python
await repository.load_profile()
```

over a property that silently performs network I/O.

## Descriptors

Descriptors define attribute access behavior through:

```python
__get__
__set__
__delete__
```

Python's `property` is implemented using the descriptor protocol.

Descriptors are also heavily used by frameworks.

Django's ORM uses descriptors to provide Python-level access to related and model-managed data.

This is one reason understanding descriptors helps when debugging ORM behavior.

## Abstract Base Classes vs Protocols

| Concern | ABC | Protocol |
|---|---|---|
| Typing model | Nominal | Structural |
| Inheritance required | Usually | No |
| Runtime abstract enforcement | Yes | No equivalent by default |
| Shared implementation | Natural | Less central |
| Framework hierarchy | Strong fit | Sometimes |
| Loose coupling | Good | Excellent |
| Duck typing | Limited | Strong |
| Backend dependency boundary | Sometimes | Often preferred |

A protocol is frequently a good default for application-level behavioral dependencies.

## Dependency Injection

Dependency injection separates object construction from object behavior.

Without DI:

```python
class ReportService:
    def __init__(self) -> None:
        self.repository = PostgresReportRepository()
```

With DI:

```python
class ReportService:
    def __init__(
        self,
        repository: ReportRepository,
    ) -> None:
        self.repository = repository
```

The composition layer decides:

```text
Production -> PostgreSQL repository
Testing    -> Fake repository
```

DI does not require a DI framework.

Explicit constructor injection is often enough.

## SOLID Principles

The folder concludes with practical OOP design principles.

```text
S -> Single Responsibility
O -> Open/Closed
L -> Liskov Substitution
I -> Interface Segregation
D -> Dependency Inversion
```

These principles help reason about:

- Responsibility
- Coupling
- Abstraction
- Substitution
- Dependency direction
- Change isolation

They should not be applied mechanically.

## SOLID in Python

Python's dynamic and structural nature changes how SOLID should be applied.

For example, Interface Segregation can be implemented naturally using protocols:

```python
class Reader(Protocol):
    async def read(self, key: str) -> bytes:
        ...
```

There is no need to create a large Java-style interface hierarchy.

Similarly, Dependency Inversion can often be implemented using:

```text
Protocol
    +
Dependency Injection
    +
Composition
```

without abstract base classes.

## Backend Architecture Application

OOP design principles become useful when building backend services.

A practical structure might be:

```text
src/
├── api/
│   └── routes/
├── application/
│   └── services/
├── domain/
│   ├── models/
│   └── policies/
├── infrastructure/
│   ├── database/
│   ├── cache/
│   ├── messaging/
│   └── external/
└── config/
```

The exact structure should match project complexity.

The architectural principle is more important than the directory names:

```text
Transport
   |
   v
Application
   |
   v
Domain
   |
   v
Infrastructure
```

## FastAPI Integration

FastAPI's dependency system can support explicit application composition.

Typical flow:

```text
HTTP Request
    |
    v
FastAPI
    |
    v
Dependency Resolution
    |
    v
Application Service
    |
    v
Repository / Gateway / Cache
    |
    v
Response
```

Avoid placing all business logic inside route functions.

Keep endpoint responsibilities focused on transport concerns.

## Django Integration

Django provides strong framework abstractions around:

- Models
- QuerySets
- Views
- Forms
- Middleware
- Management commands

Do not introduce additional OOP layers merely because the playbook teaches them.

For complex workflows, a service layer can be useful:

```text
Django View
    |
    v
Application Service
    |
    +--> ORM
    +--> External API
    +--> Event Publisher
```

For straightforward CRUD, Django's existing abstractions may already be sufficient.

## OOP and REST APIs

REST endpoints should generally separate transport representation from domain behavior.

For example:

```text
HTTP JSON
   |
   v
Request DTO / Validation
   |
   v
Application Service
   |
   v
Domain Model
   |
   v
Repository
```

Do not make domain models responsible for parsing arbitrary HTTP requests.

Likewise, avoid coupling core business logic directly to HTTP response formats unless that is an intentional design decision.

## OOP and gRPC

The same principle applies to gRPC:

```text
gRPC Handler
    |
    v
Application Service
    |
    v
Domain
```

Protocol buffers define the network contract.

Python classes should represent application behavior rather than simply mirroring every protobuf message.

## OOP and Microservices

OOP principles primarily structure code inside a service.

They do not replace distributed-system architecture.

A microservice may use:

```text
Application Service
   |
   +--> PostgreSQL
   +--> Redis
   +--> Kafka
   +--> External REST/gRPC services
```

Each external interaction should have clearly defined:

- Contract
- Timeout
- Retry semantics
- Error behavior
- Idempotency
- Observability

## Testing OOP Designs

Good OOP boundaries improve testability.

A service depending on protocols can be tested with fakes:

```python
class FakeRepository:
    async def get(self, order_id: int):
        ...


class FakePaymentGateway:
    async def charge(self, amount: int, currency: str) -> str:
        return "test-payment"
```

Testing should include multiple levels:

```text
Unit Tests
    |
    v
Component Tests
    |
    v
Integration Tests
    |
    v
Contract Tests
    |
    v
End-to-End Tests
```

Do not replace all real dependencies with mocks.

Database behavior, network behavior, serialization, transactions, and provider integrations still require integration-level validation.

## Concurrency Considerations

Object lifetime and sharing become important in concurrent systems.

Ask:

- Is this object shared across requests?
- Is it shared across async tasks?
- Is it shared across threads?
- Is it shared across worker processes?
- Does it contain mutable state?
- Is the underlying client concurrency-safe?

A Python singleton is normally:

```text
singleton per process
```

not:

```text
singleton across all Kubernetes pods
```

Distributed state requires appropriate infrastructure.

## Performance Considerations

OOP abstractions have some runtime cost through:

- Object allocation
- Attribute lookup
- Method dispatch
- Wrapper objects
- Indirection

In typical backend systems, these costs are usually smaller than:

- Database latency
- Network latency
- Serialization
- External API calls
- Disk I/O

Do not remove useful abstractions based on assumptions.

Measure with:

- `timeit`
- `cProfile`
- `py-spy`
- `tracemalloc`
- Application metrics
- Distributed tracing

Optimize after identifying actual bottlenecks.

## Memory Considerations

Large object graphs can increase memory usage.

Important factors include:

- Instance dictionaries
- Object references
- Dependency graphs
- Cached objects
- Long-lived clients
- Large collections

For memory-sensitive workloads, consider:

```python
from dataclasses import dataclass


@dataclass(slots=True)
class UserRecord:
    user_id: int
    email: str
```

Use slots and other memory optimizations based on measured requirements.

## Security Considerations

OOP design can improve security by isolating sensitive operations.

Examples include:

```text
Application
    |
    v
Credential-aware adapter
    |
    v
AWS / External Provider
```

Business logic should not need direct access to:

- API keys
- Database credentials
- Secret tokens
- Private encryption material

Use proper secrets-management mechanisms and avoid exposing secrets through object representations, logs, traces, or exceptions.

## Reliability Considerations

Well-defined object boundaries make failure handling easier to isolate.

For infrastructure dependencies, define:

- Timeout behavior
- Retryability
- Idempotency
- Error translation
- Resource ownership
- Circuit-breaking behavior where appropriate

For example:

```text
Application Service
       |
       v
PaymentGateway
       |
       +--> timeout
       +--> provider error translation
       +--> retry policy
       +--> idempotency
```

The abstraction should not hide operational semantics that the application needs to reason about.

## Scalability Considerations

OOP does not directly make a system horizontally scalable.

Scalability depends on architecture and infrastructure:

```text
Load Balancer / Nginx
        |
        v
Multiple Python Workers
        |
        +--> PostgreSQL
        +--> Redis
        +--> Kafka
        +--> External APIs
```

OOP contributes by keeping application responsibilities modular and dependencies explicit.

Resource lifetimes must be considered across:

```text
Process
Worker
Pod
Service
Region
```

## High Availability

Replaceable dependencies can support failover architectures, but the abstraction alone does not provide HA.

For example:

```text
PaymentGateway
    |
    +--> Primary Provider
    |
    +--> Secondary Provider
```

A production implementation also needs:

- Timeouts
- Health detection
- Retry limits
- Idempotency
- Failure classification
- Monitoring
- Alerting

## Deployment Considerations

OOP designs should remain compatible with modern deployment environments.

A typical lifecycle is:

```text
Container Startup
      |
      v
Load Configuration
      |
      v
Initialize Resources
      |
      v
Compose Dependencies
      |
      v
Start API
      |
      v
Serve Requests
      |
      v
Graceful Shutdown
```

Kubernetes termination and readiness behavior should be considered when application-scoped resources are involved.

## Observability

Good abstractions should not destroy useful operational information.

Useful telemetry may include:

```text
service=orders
dependency=postgres
operation=get_order
duration_ms=18
result=success
```

For external providers:

```text
provider=stripe
operation=charge
duration_ms=120
result=timeout
```

Do not log:

```text
API keys
access tokens
passwords
credential-bearing URLs
```

## Cost Considerations

Dependency lifecycle can have direct infrastructure costs.

For example:

```text
10 pods
× 4 workers
× 10 database connections
= 400 potential connections
```

The OOP design should make resource ownership clear, but capacity planning must consider the entire deployment.

The same applies to:

- Redis connections
- HTTP connection pools
- Kafka producers
- AWS clients
- Memory-heavy caches

## Common Mistakes

### Overusing Classes

Not every piece of business logic needs a class.

Prefer a function for simple pure transformations.

### Inheritance for Code Reuse

Code reuse alone does not justify inheritance.

Use composition when the relationship is not genuinely substitutable.

### Giant Service Classes

A service containing dozens of unrelated operations usually indicates poor boundaries.

### Excessive Abstraction

Avoid introducing:

```text
ABC
Protocol
Factory
Adapter
Repository
DI Container
```

when a concrete class would be clearer.

### Huge Interfaces

Large interfaces increase coupling.

Prefer focused behavioral contracts.

### Hidden Dependencies

Avoid:

```python
class OrderService:
    def process(self):
        client = create_client_from_environment()
        ...
```

Prefer explicit dependency injection.

### Global Mutable State

Global registries and caches can create:

- Test leakage
- Concurrency problems
- Process-local inconsistencies

### Ignoring Object Lifetime

A database pool or HTTP client should have a deliberate owner and shutdown lifecycle.

### Over-Mocking

Tests can pass against mocks while real integrations fail.

### Confusing Python Objects with Distributed Objects

An object in one Python process cannot directly coordinate state across Kubernetes replicas.

Use shared infrastructure for distributed state.

## Production Pitfalls

| Problem | Typical Cause | Better Approach |
|---|---|---|
| Deep inheritance hierarchy | Reuse-driven inheritance | Prefer composition |
| Giant service | Too many responsibilities | Split cohesive workflows |
| Huge protocol | Interface designed around implementation | Model consumer needs |
| Hidden dependencies | Global/container lookup | Constructor injection |
| Resource exhaustion | Incorrect object lifetime | Centralize expensive resources |
| Cross-request state leakage | Mutable singleton | Explicit scope and ownership |
| Broken substitution | Weak behavioral contract | Contract tests |
| Slow application startup | Excessive eager construction | Initialize only required resources |
| Excessive abstraction | Applying SOLID mechanically | Optimize for actual complexity |
| Difficult debugging | Too much indirection | Keep boundaries purposeful |
| Integration failures | Mock-only testing | Add integration and contract tests |

## Senior Design Heuristics

Use these principles when evaluating an OOP design:

### Prefer Composition by Default

Use inheritance when the subtype relationship is clear and behaviorally valid.

### Depend on Behavior

Protocols are often preferable to concrete infrastructure dependencies.

### Keep Dependencies Explicit

Constructor injection makes architecture visible.

### Protect Invariants

Objects should control important state transitions.

### Separate Policy from Mechanism

Business rules should not depend unnecessarily on:

```text
PostgreSQL
Redis
Kafka
AWS SDKs
HTTP libraries
```

### Keep Abstractions Small

An abstraction should expose what its consumer needs, not everything the implementation can do.

### Design for Actual Change

Abstract stable variation that is likely to change.

Do not build speculative extension points everywhere.

### Optimize for Understandability

The best design is not the one with the most patterns.

It is the one that makes ownership, behavior, dependencies, and failure boundaries obvious.

## Recommended Backend OOP Pattern

A practical Python backend can use:

```text
                    API Layer
                       |
                       v
                Application Service
                       |
          +------------+------------+
          |            |            |
          v            v            v
     Repository     Gateway       Publisher
       Protocol     Protocol       Protocol
          ^            ^            ^
          |            |            |
          v            v            v
    PostgreSQL       External       Kafka
                     Provider
```

This combines:

- Encapsulation
- Composition
- Polymorphism
- Protocols
- Dependency Injection
- Dependency Inversion

without requiring a large inheritance hierarchy.

## Recommended Study Order

Study the files sequentially when building foundational understanding:

```text
01 -> OOP Fundamentals
02 -> Classes and Objects
03 -> Instance Attributes and Methods
04 -> Class Attributes and Methods
05 -> Constructors and Initialization

06 -> Encapsulation
07 -> Inheritance
08 -> Composition
09 -> Polymorphism
10 -> Abstraction

11 -> Method Resolution Order
12 -> Multiple Inheritance
13 -> super()
14 -> Dunder Methods
15 -> Properties
16 -> Descriptors

17 -> Abstract Base Classes
18 -> Protocols
19 -> Dependency Injection
20 -> OOP Design Principles
```

The sequence deliberately moves from Python mechanics toward architectural reasoning.

## Interview Focus

For backend interviews, prioritize understanding over memorization.

Be prepared to explain:

- Python's object model.
- Class vs instance attributes.
- `__new__` vs `__init__`.
- Attribute lookup.
- Encapsulation in Python.
- Inheritance and composition.
- MRO and C3 linearization.
- `super()`.
- Multiple inheritance and mixins.
- Dunder methods.
- Properties and descriptors.
- ABCs vs protocols.
- Duck typing and structural typing.
- Dependency injection.
- Dependency inversion.
- SOLID principles.
- Composition over inheritance.
- Liskov substitution.
- Resource lifecycle.
- Object lifetime under concurrency.
- Testing replaceable dependencies.
- How these concepts apply to FastAPI and Django.

The strongest interview answers connect language semantics to engineering trade-offs.

## Production Checklist

Before applying an OOP design in a production Python backend, verify:

- Responsibilities are cohesive.
- Dependencies are explicit.
- Business logic is separated from infrastructure where useful.
- Composition is preferred over unnecessary inheritance.
- Inheritance relationships are behaviorally valid.
- Protocols and ABCs have meaningful contracts.
- Interfaces are focused.
- Object lifetimes are intentional.
- Resource ownership is explicit.
- Shared mutable state is safe under the application's concurrency model.
- Database connection pools are sized against total workers and replicas.
- External clients use appropriate timeouts and retry policies.
- Transaction boundaries are explicit.
- Idempotency is defined for retryable side effects.
- Unit tests can substitute appropriate dependencies.
- Integration tests validate real infrastructure behavior.
- Contract tests validate interchangeable implementations.
- Security-sensitive state is not exposed through logs or representations.
- Observability preserves dependency and operation context.
- Startup validates required configuration and dependencies.
- Graceful shutdown releases owned resources.
- Abstractions are not introduced merely to satisfy design patterns.
- The architecture remains understandable to engineers who did not create it.

## Key Takeaways

- Python OOP is a set of language mechanisms and design techniques, not a requirement to make every component a class.
- Composition, protocols, dependency injection, encapsulation, and focused abstractions are particularly valuable for production backend systems.
- Inheritance, multiple inheritance, descriptors, and other advanced mechanisms should be used deliberately when their runtime and architectural semantics provide real value.
- SOLID principles are heuristics for managing responsibility, coupling, change, and behavioral contracts; applying them mechanically often creates unnecessary complexity.
- Strong OOP design makes ownership, dependencies, behavior, lifecycle, and failure boundaries explicit while keeping the overall system simple enough to maintain.