# 07- Inheritance

## Overview

Inheritance allows a Python class to derive behavior and structure from another class.

A derived class, or subclass, can:

- Reuse implementation from a base class.
- Add new behavior.
- Override inherited behavior.
- Extend initialization.
- Participate in polymorphism.
- Customize framework behavior.

Basic inheritance looks like:

```python
class PaymentGateway:
    def charge(self, amount: Decimal) -> None:
        raise NotImplementedError


class StripePaymentGateway(PaymentGateway):
    def charge(self, amount: Decimal) -> None:
        ...
```

The relationship can be represented as:

```text
PaymentGateway
      |
      | inherits from
      v
StripePaymentGateway
```

Inheritance is powerful, but it creates a relatively strong coupling between parent and child classes. In production backend systems, inheritance should therefore be used when there is a genuine substitutable relationship or a framework-defined extension point.

For many application designs, composition and dependency injection provide a more flexible alternative.

## Why Inheritance Exists

Inheritance provides a mechanism for sharing behavior across related types.

Without inheritance:

```python
class StripePaymentGateway:
    def charge(self, amount: Decimal) -> None:
        ...


class AdyenPaymentGateway:
    def charge(self, amount: Decimal) -> None:
        ...
```

With a common abstraction:

```python
class PaymentGateway:
    def charge(self, amount: Decimal) -> None:
        raise NotImplementedError


class StripePaymentGateway(PaymentGateway):
    def charge(self, amount: Decimal) -> None:
        ...


class AdyenPaymentGateway(PaymentGateway):
    def charge(self, amount: Decimal) -> None:
        ...
```

The common type communicates that both implementations provide the same conceptual capability.

The important benefit is not merely code reuse. It is the ability to reason about related types through a shared interface.

## Basic Inheritance

```python
class Animal:
    def speak(self) -> str:
        return "sound"


class Dog(Animal):
    def speak(self) -> str:
        return "bark"
```

Now:

```python
dog = Dog()

print(dog.speak())
```

The subclass inherits the base class's methods unless it overrides them.

If a method is not found on `Dog`, Python searches its inheritance hierarchy.

## Attribute Lookup

Consider:

```python
class Base:
    base_value = 10


class Child(Base):
    child_value = 20
```

When evaluating:

```python
child.base_value
```

Python performs attribute lookup through the object's type and its method resolution order.

Conceptually:

```text
child
  |
  v
Child
  |
  v
Base
  |
  v
object
```

This lookup process is central to understanding inheritance.

The actual lookup rules also involve descriptors, instance dictionaries, class dictionaries, and the method resolution order.

## Method Resolution Order

Every Python class has a method resolution order, commonly called the MRO.

```python
class Base:
    pass


class Child(Base):
    pass


print(Child.mro())
```

Conceptually:

```text
Child
  |
Base
  |
object
```

For multiple inheritance, the MRO becomes more important because Python must determine which implementation should be used.

The MRO is computed using the C3 linearization algorithm.

## `__mro__`

The MRO can also be inspected through:

```python
print(Child.__mro__)
```

Example:

```python
class Repository:
    pass


class CachedRepository(Repository):
    pass


print(CachedRepository.__mro__)
```

The result includes:

```text
CachedRepository
Repository
object
```

Understanding the MRO is essential when debugging:

- Multiple inheritance
- Mixins
- Framework base classes
- Cooperative `super()`
- Method overrides

## Method Overriding

A subclass can replace inherited behavior.

```python
class NotificationSender:
    def send(self, message: str) -> None:
        raise NotImplementedError


class EmailSender(NotificationSender):
    def send(self, message: str) -> None:
        print(f"Sending email: {message}")
```

The subclass's method takes precedence over the inherited implementation.

This enables polymorphism:

```python
def notify(sender: NotificationSender, message: str) -> None:
    sender.send(message)
```

The caller does not need to know which concrete implementation it received.

## Extending Inherited Behavior

A subclass does not always need to completely replace a parent method.

It can extend it:

```python
class BaseHandler:
    def handle(self, request: Request) -> Response:
        return self.process(request)


class AuditedHandler(BaseHandler):
    def handle(self, request: Request) -> Response:
        audit_start(request)

        response = super().handle(request)

        audit_complete(request, response)
        return response
```

This pattern is useful when the parent behavior remains valid and the child adds behavior around it.

However, extensive override chains can become difficult to reason about.

## `super()`

`super()` provides access to the next implementation in the MRO.

```python
class BaseService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


class OrderService(BaseService):
    def __init__(
        self,
        repository: Repository,
        publisher: EventPublisher,
    ) -> None:
        super().__init__(repository)
        self.publisher = publisher
```

`super()` is particularly important for cooperative multiple inheritance.

It should not be understood simply as:

> Call my direct parent.

More accurately, it means:

> Continue method lookup from the next class in the MRO.

## Inheritance and Constructors

If a subclass defines `__init__()`, Python does not automatically call the parent's initializer.

```python
class BaseClient:
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout


class ApiClient(BaseClient):
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
```

Here `timeout` is never initialized.

If the base initialization is required:

```python
class ApiClient(BaseClient):
    def __init__(
        self,
        base_url: str,
        timeout: float,
    ) -> None:
        super().__init__(timeout)
        self.base_url = base_url
```

For complex inheritance hierarchies, constructor cooperation becomes a major design consideration.

## Inheritance and State

Inheritance can create implicit assumptions about parent state.

```python
class BaseRepository:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool


class OrderRepository(BaseRepository):
    async def get(self, order_id: int) -> Order | None:
        async with self._pool.connection() as connection:
            ...
```

`OrderRepository` depends on the base class establishing `_pool`.

This coupling is acceptable when the relationship is intentional and stable.

It becomes problematic when subclasses depend on many undocumented implementation details of the base class.

## Protected-by-Convention Members

Python commonly uses a single underscore for inherited implementation details:

```python
class BaseRepository:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool
```

A subclass can access:

```python
self._pool
```

This is useful when the base class intentionally provides an implementation mechanism to subclasses.

However, a large number of `_internal` attributes accessed by subclasses can indicate excessive coupling.

## Public vs Protected vs Private

| Member | Typical Meaning |
|---|---|
| `value` | Public API |
| `_value` | Internal/protected-by-convention |
| `__value` | Name-mangled implementation detail |
| `__value__` | Special Python protocol name |

Inheritance often makes `_value` more appropriate than `__value` because subclasses may intentionally need access to protected implementation state.

## Inheritance for Shared Implementation

A common use is a stable base implementation with specialized behavior.

```python
class BaseEventPublisher:
    def __init__(self, serializer: EventSerializer) -> None:
        self._serializer = serializer

    def publish(self, event: DomainEvent) -> None:
        payload = self._serializer.serialize(event)
        self._send(payload)

    def _send(self, payload: bytes) -> None:
        raise NotImplementedError


class KafkaEventPublisher(BaseEventPublisher):
    def __init__(
        self,
        serializer: EventSerializer,
        producer: KafkaProducer,
    ) -> None:
        super().__init__(serializer)
        self._producer = producer

    def _send(self, payload: bytes) -> None:
        self._producer.send(payload)
```

The base class owns serialization behavior while the subclass supplies the transport-specific operation.

This can be useful when the algorithm is stable but one or more implementation steps vary.

## Template Method Pattern

The previous design resembles the Template Method pattern.

```text
Base implementation
       |
       +--> common validation
       |
       +--> common serialization
       |
       +--> subclass-specific operation
       |
       +--> common metrics
```

Example:

```python
class ImportJob:
    def run(self) -> None:
        data = self.extract()
        records = self.transform(data)
        self.load(records)

    def extract(self) -> list[dict[str, object]]:
        raise NotImplementedError

    def transform(
        self,
        data: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        return data

    def load(self, records: list[dict[str, object]]) -> None:
        raise NotImplementedError
```

A subclass supplies selected steps.

This pattern is useful when the workflow itself is stable and extension points are well-defined.

## Inheritance for Framework Extension

Inheritance is common in frameworks.

Django provides class-based views:

```python
from django.views import View


class HealthCheckView(View):
    def get(self, request):
        ...
```

The framework supplies common behavior while subclasses customize extension points.

Similar patterns appear in:

- Django models
- Django forms
- Django middleware-related abstractions
- Exception classes
- Test classes
- Framework-specific base classes

In these cases, inheritance is part of the framework's extension model and is often appropriate.

## FastAPI and Inheritance

FastAPI generally relies more heavily on dependency injection, composition, and type-oriented interfaces than deep inheritance hierarchies.

For example, a service may receive a protocol-compatible dependency:

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
    ) -> None:
        self._repository = repository
```

This can be preferable to:

```python
class OrderService(PostgresOrderRepository):
    ...
```

The first design separates business behavior from persistence implementation.

## Inheritance and REST APIs

Inheritance usually belongs inside the implementation rather than in the HTTP resource model.

For example:

```text
POST /orders
GET  /orders/{id}
```

should expose a stable API contract regardless of whether the implementation uses:

```text
OrderService
   |
   +--> BaseRepository
          |
          +--> PostgresRepository
```

Clients should not need to know the class hierarchy.

## Inheritance and gRPC

gRPC service implementations may use framework-provided base classes.

Conceptually:

```python
class OrderService(OrderServiceServicer):
    async def GetOrder(self, request, context):
        ...
```

The framework base class establishes the integration contract.

This is a strong use case for inheritance because the framework explicitly defines the extension mechanism.

## Inheritance vs Composition

Composition means building an object from other objects rather than deriving behavior from a parent class.

Inheritance:

```text
OrderService
    |
    +--> BaseService
```

Composition:

```text
OrderService
    |
    +--> OrderRepository
    +--> EventPublisher
    +--> Clock
```

Composition usually creates weaker coupling.

A useful engineering heuristic is:

> Prefer composition when the relationship is "has a" rather than "is a."

Examples:

| Relationship | Better fit |
|---|---|
| `Dog` is an `Animal` | Inheritance may fit |
| `OrderService` has a repository | Composition |
| `PaymentService` has a gateway | Composition |
| `ReportGenerator` has a formatter | Composition |
| `DjangoView` is a framework view | Inheritance |
| `KafkaPublisher` is a publisher implementation | Interface/protocol or inheritance |

## Why Composition Is Often Preferred

Suppose:

```python
class OrderService(PostgresOrderRepository):
    ...
```

Now `OrderService` inherits database behavior.

This creates an undesirable relationship:

```text
OrderService IS-A PostgresOrderRepository
```

The service is not actually a repository.

Composition is clearer:

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
    ) -> None:
        self._repository = repository
```

Now:

```text
OrderService HAS-A OrderRepository
```

The dependency can be replaced without changing the service's type hierarchy.

## Liskov Substitution Principle

Inheritance is appropriate when a subclass can genuinely substitute for its base type.

If code expects:

```python
def process(gateway: PaymentGateway) -> None:
    gateway.charge(Decimal("100.00"))
```

every valid `PaymentGateway` implementation should satisfy the expected behavioral contract.

A subclass that violates those assumptions is not a good substitute.

For example, this is problematic:

```python
class ReadOnlyPaymentGateway(PaymentGateway):
    def charge(self, amount: Decimal) -> None:
        raise RuntimeError("Charging is unsupported")
```

If callers reasonably expect every `PaymentGateway` to support charging, the hierarchy is poorly modeled.

## Behavioral Subtyping

The important inheritance relationship is behavioral, not merely structural.

A subclass should preserve expectations about:

- Valid inputs
- Return values
- Exceptions
- Side effects
- State transitions
- Performance characteristics where contractually relevant

Changing implementation is fine.

Changing the meaning of the interface is not.

## Fragile Base Class Problem

A base class can become a hidden dependency for many subclasses.

```text
                 BaseService
                /     |      \
               /      |       \
              A       B        C
```

Changing `BaseService` can unexpectedly break:

```text
A
B
C
```

This is the fragile base class problem.

For example, changing:

```python
def process(self) -> Response:
    ...
```

to:

```python
def process(self, timeout: float) -> Response:
    ...
```

may break every subclass and consumer.

A base class should therefore have a carefully designed contract.

## Deep Inheritance Hierarchies

Deep hierarchies are difficult to reason about.

```text
Base
 |
A
 |
B
 |
C
 |
D
 |
E
```

A developer working on `E` may need to inspect five classes to understand:

- Initialization
- Attribute definitions
- Method overrides
- Side effects
- Error handling
- `super()` calls

Prefer shallow hierarchies where possible.

A small hierarchy such as:

```text
PaymentGateway
   |
   +--> StripePaymentGateway
   +--> AdyenPaymentGateway
```

is generally easier to maintain.

## Multiple Inheritance

Python supports multiple inheritance:

```python
class A:
    ...


class B:
    ...


class C(A, B):
    ...
```

The MRO determines method lookup:

```python
print(C.mro())
```

Multiple inheritance is powerful but should be used deliberately.

Common use cases include:

- Mixins
- Framework classes
- Cooperative class hierarchies
- Cross-cutting reusable behavior

It is usually a poor choice for combining unrelated business components.

## Mixins

A mixin provides focused reusable behavior rather than representing a complete domain type.

```python
class AuditMixin:
    def audit(self, message: str) -> None:
        ...


class OrderService(AuditMixin):
    ...
```

A good mixin is generally:

- Small
- Focused
- Stateless or minimally stateful
- Designed for composition through inheritance
- Explicit about its assumptions

Avoid mixins that require many undocumented attributes.

## Cooperative Multiple Inheritance

Multiple inheritance works best when classes cooperate through `super()`.

```python
class LoggingMixin:
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.logger = create_logger()


class MetricsMixin:
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.metrics = create_metrics()


class Service(LoggingMixin, MetricsMixin):
    def __init__(self, repository: Repository, **kwargs) -> None:
        super().__init__(**kwargs)
        self.repository = repository
```

The exact constructor contracts matter greatly here.

A class that bypasses `super()` can break cooperative initialization.

## Why `super()` Matters in Multiple Inheritance

Consider:

```text
Service
  |
  +--> LoggingMixin
  |
  +--> MetricsMixin
  |
  +--> BaseService
```

Python follows the MRO:

```text
Service
  -> LoggingMixin
  -> MetricsMixin
  -> BaseService
  -> object
```

Each class calling:

```python
super()
```

allows the next class in the MRO to participate.

Calling a specific parent directly:

```python
BaseService.__init__(self)
```

can bypass other classes in the hierarchy.

## Diamond Inheritance

A classic structure is:

```text
       A
      / \
     B   C
      \ /
       D
```

Python's C3 MRO helps ensure that shared ancestors are handled consistently.

Example:

```python
class A:
    def run(self) -> None:
        print("A")


class B(A):
    def run(self) -> None:
        print("B")
        super().run()


class C(A):
    def run(self) -> None:
        print("C")
        super().run()


class D(B, C):
    def run(self) -> None:
        print("D")
        super().run()
```

The MRO is approximately:

```text
D -> B -> C -> A -> object
```

Calling:

```python
D().run()
```

follows that cooperative chain.

## Inheritance and Abstract Base Classes

Inheritance can define explicit contracts through `abc`.

```python
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    async def charge(
        self,
        amount: Decimal,
    ) -> PaymentResult:
        ...
```

Concrete implementations must provide the abstract method:

```python
class StripePaymentGateway(PaymentGateway):
    async def charge(
        self,
        amount: Decimal,
    ) -> PaymentResult:
        ...
```

This provides runtime enforcement that a concrete class implements the required abstraction.

Protocols can provide an alternative when structural typing is preferable.

## Inheritance vs Protocols

A protocol does not require implementation inheritance.

```python
from typing import Protocol


class PaymentGateway(Protocol):
    async def charge(
        self,
        amount: Decimal,
    ) -> PaymentResult:
        ...
```

A class can satisfy the protocol simply by providing compatible behavior.

```python
class StripePaymentGateway:
    async def charge(
        self,
        amount: Decimal,
    ) -> PaymentResult:
        ...
```

This reduces coupling because `StripePaymentGateway` does not need to inherit from `PaymentGateway`.

For backend dependency boundaries, protocols are often a strong alternative to inheritance.

## Inheritance and Type Checking

Static type checkers such as mypy and Pyright understand inheritance relationships.

```python
class BaseRepository:
    async def get(self, item_id: int) -> Item | None:
        ...


class OrderRepository(BaseRepository):
    async def get(self, item_id: int) -> Order | None:
        ...
```

Override compatibility matters.

The subclass should maintain a compatible method signature and behavior.

Type checking can catch many accidental violations before deployment.

## Inheritance and Exceptions

Exception hierarchies are an especially useful application of inheritance.

```python
class ApplicationError(Exception):
    pass


class OrderError(ApplicationError):
    pass


class OrderNotFound(OrderError):
    pass


class InvalidOrderState(OrderError):
    pass
```

Consumers can catch at the appropriate level:

```python
try:
    await service.submit(order_id)
except OrderNotFound:
    ...
except OrderError:
    ...
```

This allows precise handling while preserving a common category.

## Inheritance and Serialization

Inheritance can complicate serialization.

Consider:

```python
class Event:
    ...


class OrderCreated(Event):
    ...
```

Serialization must determine:

- Concrete type
- Schema
- Version
- Required fields
- Compatibility rules

For Kafka or REST payloads, explicit schemas are generally safer than relying on Python's class hierarchy.

Do not assume Python inheritance automatically translates into a stable wire-level schema.

## Inheritance and Database Models

ORM inheritance can have significant database implications.

For example, Django supports model inheritance, but different inheritance strategies can affect:

- Table structure
- Joins
- Query performance
- Migration complexity
- Serialization
- Operational behavior

Use ORM inheritance because the domain and persistence model justify it, not merely because Python inheritance is available.

## Inheritance and Concurrency

Inheritance does not provide thread safety.

If a base class contains mutable shared state:

```python
class BaseCache:
    def __init__(self) -> None:
        self._cache: dict[str, object] = {}
```

every subclass may inherit the same concurrency risks.

The hierarchy must explicitly define:

- Ownership
- Synchronization
- Thread safety
- Async safety
- Process scope

In a Kubernetes deployment, each process or pod has its own object instances.

Inheritance does not make state distributed.

## Inheritance and Performance

Method lookup through inheritance has runtime costs, but ordinary inheritance overhead is rarely a backend bottleneck.

Typical backend costs such as:

- Database queries
- Network requests
- Serialization
- TLS
- Disk I/O

are usually orders of magnitude more significant.

Do not avoid a clean inheritance relationship because of unmeasured micro-optimization concerns.

Performance problems become more relevant when inheritance interacts with:

- Extremely hot loops
- Dynamic attribute lookup
- Complex descriptors
- Deep method override chains
- Large object populations

Measure before optimizing.

## Inheritance and Memory

Each instance still contains its instance state regardless of whether that state originates from a base or subclass.

```python
class Base:
    def __init__(self) -> None:
        self.base_state = ...


class Child(Base):
    def __init__(self) -> None:
        super().__init__()
        self.child_state = ...
```

The resulting object contains both states.

Inheritance itself should not be treated as a memory optimization.

For large numbers of objects, consider:

- `__slots__`
- Object lifecycle
- Data structure choice
- Lazy state
- Object count

## Security Considerations

Inheritance can unintentionally expose or override security-sensitive behavior.

For example:

```python
class AuthenticatedClient(BaseClient):
    def request(self, request: Request) -> Response:
        ...
```

A subclass overriding authentication or authorization logic must preserve the security contract.

Risks include:

- Accidentally bypassing authorization
- Disabling validation
- Removing audit logging
- Weakening TLS configuration
- Overriding security hooks incorrectly

Security-sensitive base classes should have explicit contracts and strong tests around security invariants.

## Reliability Considerations

Base classes should avoid hidden side effects that subclasses cannot reasonably predict.

For example:

```python
class BaseHandler:
    def handle(self, request: Request) -> Response:
        result = self.process(request)
        publish_event(result)
        return result
```

A subclass may override `process()` without realizing that publishing occurs afterward.

Framework-style hooks should be documented clearly.

For critical workflows, explicit orchestration may be easier to reason about than deep inheritance.

## Observability

Inheritance hierarchies should preserve observability behavior.

If a base service records metrics:

```python
class BaseService:
    def process(self) -> None:
        start = time.monotonic()

        try:
            self._process()
        finally:
            duration = time.monotonic() - start
            metrics.observe(duration)
```

subclasses should not accidentally bypass the instrumentation.

If subclasses must override lifecycle methods, define clear extension points.

Observability can include:

- Metrics
- Structured logs
- Traces
- Error counters
- Latency measurements

## Inheritance and Dependency Injection

Dependency injection often reduces the need for inheritance.

Instead of:

```python
class CachedOrderService(PostgresOrderService):
    ...
```

prefer:

```python
class CachedOrderService:
    def __init__(
        self,
        repository: OrderRepository,
        cache: OrderCache,
    ) -> None:
        self._repository = repository
        self._cache = cache
```

Now caching is a dependency rather than a permanent type relationship.

This makes behavior easier to replace and test.

## Production Architecture Example

Consider an order-processing service:

```text
                   OrderService
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
   OrderRepository   OrderCache   EventPublisher
          |             |             |
          v             v             v
      PostgreSQL       Redis         Kafka
```

There may still be inheritance inside each boundary:

```text
OrderRepository
      |
      +--> PostgresOrderRepository

EventPublisher
      |
      +--> KafkaEventPublisher
```

This is often preferable to one large inheritance tree spanning the entire application.

## Common Mistakes

### Using Inheritance Only for Code Reuse

Shared code does not automatically imply an "is-a" relationship.

If the relationship is primarily reuse, composition or a helper abstraction may be clearer.

### Deep Inheritance Hierarchies

Deep trees make behavior difficult to trace and increase the blast radius of base-class changes.

### Forgetting `super().__init__()`

Required base state may never be initialized.

### Calling a Specific Parent Instead of `super()`

This can break cooperative multiple inheritance.

### Overriding Methods Without Preserving Contracts

A subclass may technically override a method while violating behavioral expectations.

### Accessing Too Many Base-Class Internals

If subclasses depend on numerous undocumented `_internal` fields, the base class becomes difficult to evolve.

### Using Inheritance for Dependency Injection

A service should usually have a repository rather than inherit from one.

### Ignoring the MRO

Multiple inheritance without understanding the MRO can produce surprising method resolution and initialization behavior.

### Assuming Inheritance Provides Encapsulation

Inherited members are still part of the same object and can expose implementation coupling.

### Treating Inheritance as a Security Boundary

Subclass behavior can override parent methods. Security must be enforced through explicit controls and tested contracts.

## Production Pitfalls

| Pitfall | Impact | Better Approach |
|---|---|---|
| Deep inheritance | Hard-to-trace behavior | Prefer shallow hierarchies |
| Base class with many responsibilities | Fragile subclasses | Narrow base contracts |
| Hidden parent state | Tight coupling | Explicit interfaces |
| Missing `super()` | Broken initialization | Cooperative initialization |
| Direct parent calls | Broken MRO | Use `super()` when cooperation is intended |
| Inheritance for reuse only | Wrong domain relationship | Prefer composition |
| Generic base service | Excessive coupling | Focused abstractions |
| Security logic in overridable methods | Potential bypass | Explicit security boundaries |
| ORM inheritance without analysis | Query/schema complexity | Evaluate persistence strategy |
| Multiple inheritance without MRO knowledge | Unexpected behavior | Keep mixins small and cooperative |

## When to Use Inheritance

Inheritance is a good candidate when most of the following are true:

- The subclass genuinely represents a specialized form of the base type.
- The subclass can satisfy the base type's behavioral contract.
- The base class provides meaningful shared behavior or a framework-defined extension point.
- The hierarchy is shallow.
- The base contract is stable.
- Subclasses do not depend heavily on implementation details.
- `super()` behavior is well understood.
- Testing the hierarchy remains straightforward.

Examples:

```text
Exception
   |
   +--> OrderError
          |
          +--> OrderNotFound
          +--> InvalidOrderState
```

and:

```text
Django View
   |
   +--> HealthCheckView
```

## When to Prefer Composition

Composition is usually preferable when:

- The relationship is "has-a".
- Dependencies may change independently.
- Different combinations of behavior are needed.
- You want easy dependency injection.
- The component is infrastructure rather than a domain subtype.
- The hierarchy would become deep.
- Runtime configuration determines behavior.

Example:

```python
class ReportService:
    def __init__(
        self,
        repository: ReportRepository,
        formatter: ReportFormatter,
        publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._formatter = formatter
        self._publisher = publisher
```

This gives the service several replaceable behaviors without creating a large inheritance hierarchy.

## Inheritance Design Checklist

Before introducing inheritance, ask:

- Is the child genuinely substitutable for the parent?
- Is this an "is-a" relationship?
- Does the parent define a stable behavioral contract?
- Is shared behavior actually meaningful?
- Would composition be simpler?
- Does the subclass need access to parent implementation details?
- Is the hierarchy shallow?
- Are constructor responsibilities clear?
- Is `super()` behavior understood?
- Could a protocol provide the required abstraction?
- Will the hierarchy remain manageable as the system grows?
- Does framework behavior explicitly require inheritance?

## Senior Engineering Heuristic

A useful decision model is:

```text
Need shared behavior?
       |
       +-- No --> Composition / Protocol
       |
       +-- Yes
            |
            v
Is there a genuine "is-a" relationship?
            |
       +----+----+
       |         |
      No        Yes
       |         |
       v         v
 Composition   Is substitution valid?
                  |
             +----+----+
             |         |
            No        Yes
             |         |
             v         v
        Composition  Inheritance
```

The strongest reason to use inheritance is not code reuse.

It is a stable subtype relationship with a meaningful behavioral contract.

## Key Takeaways

- Python inheritance enables specialization, method overriding, shared behavior, and polymorphism, but it creates strong coupling between base classes and subclasses.
- A valid inheritance relationship should satisfy behavioral substitutability; a subclass must preserve the expectations established by its base type.
- `super()` follows the method resolution order rather than simply meaning "call my parent," making it essential for cooperative inheritance and multiple-inheritance designs.
- In backend systems, composition, dependency injection, and protocols are often preferable for services and infrastructure because they reduce coupling and make components easier to replace and test.
- Use inheritance deliberately for genuine subtype relationships, framework extension points, focused mixins, and stable contracts; avoid deep hierarchies and inheritance used solely for code reuse.