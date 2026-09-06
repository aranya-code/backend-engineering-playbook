# 04- Class Attributes and Methods

## Overview

Class attributes and class methods operate at the **class level** rather than representing state or behavior tied exclusively to one instance.

Python provides several mechanisms for class-level behavior:

- Class attributes
- `@classmethod`
- `@staticmethod`
- Class-level constants
- Class factories
- Alternative constructors
- Class registries
- Class configuration
- Metaclass-driven behavior

These mechanisms are useful when information or behavior belongs to the type itself rather than to an individual object.

A useful mental model is:

```text
                    Class
                      |
          +-----------+-----------+
          |                       |
          v                       v
   Class Attributes        Class Methods
          |                       |
          v                       v
   Shared class-level       Receives cls
       state/metadata        as first argument
          |
          +-----------------------+
                                  |
                                  v
                              Instances
                         +--------+--------+
                         |                 |
                         v                 v
                      Object A          Object B
```

The distinction between **class-level** and **instance-level** state is particularly important in backend systems because class-level mutable state is process-local and can accidentally become shared across requests, threads, and objects.

## Class Attributes

A class attribute is an attribute defined on the class rather than created specifically on each instance.

```python
class Order:
    resource_name = "orders"

    def __init__(self, order_id: int) -> None:
        self.order_id = order_id
```

Here:

```text
Order.resource_name
```

is a class-level value, while:

```text
order.order_id
```

is instance state.

Conceptually:

```text
Order
├── resource_name = "orders"
├── methods
│
├── order_a
│   └── order_id = 1001
│
└── order_b
    └── order_id = 1002
```

## Why Class Attributes Exist

Class attributes are useful for information shared by instances or metadata describing the class itself.

Common uses include:

- Constants
- Default configuration
- Type metadata
- Feature configuration
- Registry structures
- Framework metadata
- Shared immutable values

Example:

```python
class HttpClient:
    default_timeout_seconds = 10
```

Every instance can access:

```python
client.default_timeout_seconds
```

without each instance needing its own copy of the value.

## Class Attribute Lookup

When evaluating:

```python
client.default_timeout_seconds
```

Python performs attribute lookup.

A simplified model is:

```text
client.default_timeout_seconds
             |
             v
       Instance lookup
             |
             v
       Class lookup
             |
             v
      Base class lookup
```

If the attribute does not exist on the instance, Python can find it on the class or its base classes.

For example:

```python
class Client:
    timeout = 10


client = Client()

assert client.timeout == 10
assert Client.timeout == 10
```

The instance can access the class attribute without containing an independent instance copy.

## Instance Attributes Can Shadow Class Attributes

An instance can create an attribute with the same name:

```python
class Client:
    timeout = 10


client = Client()
client.timeout = 30
```

Now:

```python
client.timeout
```

returns:

```text
30
```

while:

```python
Client.timeout
```

remains:

```text
10
```

Conceptually:

```text
Client
└── timeout = 10

client
└── timeout = 30
```

The instance-level value shadows the class-level value in ordinary lookup.

## Class Attributes as Defaults

A class attribute can provide a default that instances may override.

```python
class ApiClient:
    timeout_seconds = 10
    retry_count = 3

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
```

A specialized client can override the defaults:

```python
class PaymentClient(ApiClient):
    timeout_seconds = 20
```

This can be useful for stable configuration defaults.

However, for environment-specific production configuration, explicit configuration objects are usually preferable to mutable class-level settings.

## Immutable Class Attributes

Class-level constants are one of the safest uses of class attributes.

```python
class Order:
    MAX_ITEMS = 100
    DEFAULT_CURRENCY = "USD"
```

These values are conventionally treated as constants.

Python does not enforce immutability:

```python
Order.MAX_ITEMS = 200
```

is technically possible.

The uppercase naming convention communicates intended usage.

For values that must never change at runtime, enforce that requirement through architecture rather than relying on naming conventions alone.

## Mutable Class Attributes

Mutable class attributes require special care.

Bad:

```python
class RequestContext:
    headers: dict[str, str] = {}
```

All instances can access the same dictionary.

```text
RequestContext
       |
       v
   headers {}
      ^
      |
  +---+---+
  |       |
ctx_a   ctx_b
```

A mutation through one instance can therefore be observed through another.

Prefer per-instance state:

```python
class RequestContext:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {}
```

Now:

```text
ctx_a --> headers {}
ctx_b --> headers {}
```

The dictionaries are independent.

## When Shared Mutable State Is Intentional

Shared mutable state is not inherently invalid.

Sometimes a class-level registry is deliberate:

```python
class SerializerRegistry:
    serializers: dict[str, type] = {}
```

The engineering question is whether the shared state is:

- Intentional
- Process-local
- Thread-safe
- Lifecycle-managed
- Bounded
- Observable
- Safe to mutate

If shared state is important to application correctness, consider whether it belongs in an external system such as:

- Redis
- PostgreSQL
- Kafka
- Object storage

rather than in a Python class.

## Class State Is Process-Local

Class attributes exist inside a Python process.

With multiple workers:

```text
Worker A
└── Order.registry

Worker B
└── Order.registry

Worker C
└── Order.registry
```

These registries are separate.

Updating:

```python
Order.registry["x"] = handler
```

in Worker A does not automatically update Worker B.

This is critical when deploying through:

- Gunicorn
- Uvicorn workers
- Docker
- Kubernetes
- AWS ECS
- AWS Lambda execution environments

Do not use class-level state as a distributed coordination mechanism.

## Class Attributes and Threads

Threads within the same process can access the same class attribute.

Therefore:

```python
class Metrics:
    counters: dict[str, int] = {}
```

can become shared mutable state across concurrent threads.

If multiple threads mutate the same structure, synchronization may be required.

However, locks do not make class-level architecture automatically correct.

Before introducing shared mutable class state, ask:

- Is the state truly shared?
- Can it be immutable?
- Does each request need isolation?
- Does each worker need its own state?
- Does the state need to survive process restarts?
- Does the state need to be shared across replicas?

## Class Methods

A class method is defined using `@classmethod`.

```python
class User:
    @classmethod
    def from_email(cls, email: str) -> "User":
        return cls(email=email)
```

The first argument is the class, conventionally named `cls`.

Conceptually:

```text
User.from_email(...)
        |
        v
      cls
        |
        v
      User
```

Unlike an instance method:

```python
def method(self):
    ...
```

a class method receives:

```python
def method(cls):
    ...
```

## Why Class Methods Exist

Class methods are useful when behavior:

- Operates on class-level state
- Creates instances
- Acts as an alternative constructor
- Needs to respect subclasses
- Provides type-specific factories
- Encapsulates class-level configuration

A common production use is an alternative constructor.

```python
class User:
    def __init__(self, user_id: int, email: str) -> None:
        self.user_id = user_id
        self.email = email

    @classmethod
    def from_email(cls, email: str) -> "User":
        return cls(
            user_id=0,
            email=email.strip().lower(),
        )
```

Usage:

```python
user = User.from_email("USER@example.com")
```

## `cls` vs `self`

| Feature | Instance Method | Class Method |
|---|---|---|
| Decorator | None | `@classmethod` |
| First argument | `self` | `cls` |
| Receives | Instance | Class |
| Typical purpose | Instance behavior | Class-level behavior/factory |
| Can access instance state | Yes | No specific instance exists |
| Can access class state | Yes | Yes |
| Supports subclass-aware construction | Indirectly | Naturally |

Example:

```python
class User:
    default_role = "user"

    def __init__(self, email: str) -> None:
        self.email = email

    def activate(self) -> None:
        self.active = True

    @classmethod
    def default(cls) -> "User":
        return cls(email="unknown@example.com")
```

`activate()` operates on one user.

`default()` creates an instance through the class.

## Class Methods as Alternative Constructors

Alternative constructors are one of the strongest uses of `@classmethod`.

```python
from datetime import datetime


class ApiToken:
    def __init__(
        self,
        value: str,
        expires_at: datetime,
    ) -> None:
        self.value = value
        self.expires_at = expires_at

    @classmethod
    def from_raw_token(
        cls,
        token: str,
        expires_at: datetime,
    ) -> "ApiToken":
        return cls(
            value=token.strip(),
            expires_at=expires_at,
        )
```

This keeps construction logic close to the type while providing multiple valid input representations.

Other examples include:

```python
User.from_database_row(...)
User.from_json(...)
User.from_headers(...)
Config.from_environment(...)
Money.from_decimal(...)
```

## Subclass-Aware Class Methods

One important advantage of `cls` over explicitly naming the class is subclass support.

```python
class Payment:
    @classmethod
    def create_default(cls) -> "Payment":
        return cls()
```

A subclass inherits the method:

```python
class CardPayment(Payment):
    pass
```

Calling:

```python
payment = CardPayment.create_default()
```

uses:

```text
cls == CardPayment
```

Therefore the result is a `CardPayment`.

If the method instead used:

```python
return Payment()
```

it would always construct `Payment`, breaking subclass-aware factory behavior.

## Class Methods and Inheritance

Class methods participate in normal inheritance.

```python
class BaseParser:
    format_name = "base"

    @classmethod
    def format(cls) -> str:
        return cls.format_name
```

A subclass can change the class-level configuration:

```python
class JsonParser(BaseParser):
    format_name = "json"
```

Then:

```python
assert JsonParser.format() == "json"
```

This pattern is useful for carefully designed class hierarchies.

It can become difficult to reason about when inheritance becomes deep or class-level configuration is heavily mutable.

## Static Methods

A static method is defined using `@staticmethod`.

```python
class EmailValidator:
    @staticmethod
    def is_valid_domain(domain: str) -> bool:
        return "." in domain
```

A static method receives neither:

- `self`
- `cls`

automatically.

It behaves essentially like a function stored on the class namespace.

```python
EmailValidator.is_valid_domain("example.com")
```

## Why Static Methods Exist

Static methods are appropriate when a function is conceptually associated with a class but does not need:

- Instance state
- Class state
- Polymorphic construction

Example:

```python
class Money:
    @staticmethod
    def validate_currency(currency: str) -> None:
        if len(currency) != 3:
            raise ValueError("Currency must use a 3-letter code")
```

However, the existence of `@staticmethod` does not automatically make the design better.

If the function has no meaningful relationship to the class, a module-level function may be clearer.

## `staticmethod` vs Module-Level Function

Consider:

```python
class UrlBuilder:
    @staticmethod
    def normalize_path(path: str) -> str:
        return path.strip("/")
```

If the function is not conceptually part of `UrlBuilder`, prefer:

```python
def normalize_path(path: str) -> str:
    return path.strip("/")
```

A module-level function has:

- Less indirection
- Simpler testing
- Clearer namespace ownership
- No artificial class dependency

Use `staticmethod` when the class namespace genuinely improves discoverability or API organization.

## Instance, Class, and Static Methods

A single class can contain all three:

```python
class User:
    default_role = "user"

    def __init__(self, email: str) -> None:
        self.email = email

    def activate(self) -> None:
        self.active = True

    @classmethod
    def guest(cls) -> "User":
        return cls(email="guest@example.com")

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()
```

Their responsibilities are different:

```text
Instance method
    |
    +--> operates on object state

Class method
    |
    +--> operates on class/type
    +--> often constructs objects

Static method
    |
    +--> utility logically associated with class
```

## Class Method Binding

Python implements `classmethod` using descriptor machinery.

Conceptually:

```text
Class method definition
        |
        v
classmethod descriptor
        |
        v
Attribute access
        |
        v
Bound method with cls
```

For:

```python
User.guest()
```

the class is bound as the first argument.

For:

```python
AdminUser.guest()
```

the subclass is bound as `cls` when inherited normally.

This behavior is different from a plain function stored on the class.

## Static Method Binding

A static method does not bind an instance or class.

```python
class MathTools:
    @staticmethod
    def add(a: int, b: int) -> int:
        return a + b
```

Calling:

```python
MathTools.add(1, 2)
```

does not automatically provide an additional first argument.

The descriptor returns the underlying function without binding `self` or `cls`.

## Class Attributes and Descriptors

Class attributes can participate in descriptor-based attribute access.

Examples include:

- `property`
- `classmethod`
- `staticmethod`
- ORM fields
- Framework-managed attributes

For example:

```python
class User:
    @property
    def email(self) -> str:
        return self._email
```

The property object resides on the class and controls access through instances.

This is why class-level objects can fundamentally change how:

```python
user.email
```

behaves.

Descriptors are covered separately in the OOP section because they form an important part of Python's attribute access model.

## Class-Level Registries

A registry can be implemented with class-level state:

```python
class EventHandlers:
    handlers: dict[str, type] = {}

    @classmethod
    def register(cls, event_name: str, handler: type) -> None:
        cls.handlers[event_name] = handler
```

This can be useful for:

- Plugin registration
- Serialization handlers
- Command dispatch
- Framework extensions

However, production registries need careful consideration around:

- Import order
- Initialization
- Test isolation
- Thread safety
- Process boundaries
- Memory growth

A global registry can become hidden global state if not designed carefully.

## Class Methods and Registries

A class method can encapsulate registry mutation:

```python
class SerializerRegistry:
    _serializers: dict[str, type] = {}

    @classmethod
    def register(cls, name: str, serializer: type) -> None:
        if name in cls._serializers:
            raise ValueError(f"Serializer already registered: {name}")

        cls._serializers[name] = serializer

    @classmethod
    def get(cls, name: str) -> type:
        try:
            return cls._serializers[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown serializer: {name}"
            ) from exc
```

The class now controls the registry API rather than exposing unrestricted mutation.

Even so, the registry remains process-local.

## Class Attributes for Configuration

Class attributes can represent static metadata:

```python
class PaymentProvider:
    provider_name = "base"
    supports_refunds = False
```

A subclass can specialize it:

```python
class StripeProvider(PaymentProvider):
    provider_name = "stripe"
    supports_refunds = True
```

This can be effective when the values are stable characteristics of the type.

It is less appropriate for runtime configuration such as:

```text
DATABASE_URL
REDIS_URL
API_KEY
TIMEOUT
RETRY_POLICY
```

Those values usually belong in explicit configuration objects or dependency injection.

## Environment Configuration

Avoid:

```python
class Settings:
    DATABASE_URL = os.environ["DATABASE_URL"]
```

when the class becomes an implicit global configuration singleton throughout the application.

Prefer explicit configuration:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
```

Then inject the settings into components that require them.

This makes configuration:

- Testable
- Explicit
- Replaceable
- Easier to validate
- Easier to reason about

## Class Methods and Factory Design

Class methods can provide a lightweight factory without requiring a separate factory class.

```python
class DatabaseClient:
    def __init__(
        self,
        host: str,
        port: int,
    ) -> None:
        self.host = host
        self.port = port

    @classmethod
    def from_url(cls, url: str) -> "DatabaseClient":
        host, port = parse_database_url(url)
        return cls(host=host, port=port)
```

This is appropriate when construction logic is closely related to the class.

If construction requires complex dependency graphs or application-wide configuration, a separate composition/factory layer may be clearer.

## Class Attributes and Dataclasses

Dataclasses distinguish between class-level metadata and per-instance fields.

Use:

```python
from dataclasses import dataclass, field


@dataclass
class Request:
    method: str
    headers: dict[str, str] = field(default_factory=dict)
```

rather than:

```python
@dataclass
class Request:
    method: str
    headers: dict[str, str] = {}
```

`default_factory` ensures each instance receives its own dictionary.

For genuine class-level metadata, `ClassVar` makes the intent explicit:

```python
from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Order:
    order_id: int
    table_name: ClassVar[str] = "orders"
```

`ClassVar` communicates to static type checkers that `table_name` is not an instance field.

## Class Variables and Type Hints

Use `ClassVar` when a variable is intentionally class-level.

```python
from typing import ClassVar


class Service:
    service_name: ClassVar[str] = "orders"
```

This improves static analysis and communicates design intent.

Without `ClassVar`, type checkers may interpret the annotation differently depending on the surrounding context.

For production code, explicit type intent is valuable.

## Class Attributes and Memory

A class attribute is shared rather than duplicated across every instance.

For immutable values:

```python
class Client:
    DEFAULT_TIMEOUT = 10
```

this can be conceptually more efficient than storing:

```python
self.timeout = 10
```

on every instance when the value truly never varies.

However, the memory difference is usually insignificant compared with larger architectural concerns.

Do not use class attributes primarily as a micro-optimization.

## Class-Level Caches

Class-level caches can be tempting:

```python
class CurrencyConverter:
    _rates: dict[str, Decimal] = {}
```

But this creates process-local shared mutable state.

Questions that must be answered include:

- How large can the cache become?
- When does it expire?
- Is it thread-safe?
- Is it safe across workers?
- What happens after a deployment?
- What happens when the data becomes stale?
- Is Redis a better fit?

For distributed services, Redis is often more appropriate for shared caching.

## Class-Level State and Kubernetes

Consider three Kubernetes replicas:

```text
                 Load Balancer
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
        Pod A       Pod B       Pod C
          |           |           |
       Class X      Class X      Class X
       cache={}     cache={}     cache={}
```

Each pod has its own Python process and therefore its own class state.

This means class-level caching can cause inconsistent views:

```text
Pod A -> cache contains key
Pod B -> cache does not contain key
Pod C -> stale value
```

For shared caching or coordination, use infrastructure designed for it.

## Class Methods in Frameworks

Frameworks frequently use class-level behavior.

### Django

Django models expose class-level managers:

```python
User.objects.filter(...)
```

The manager is associated with the model class and provides query behavior.

Django also uses class attributes and descriptors extensively for model metadata and fields.

### FastAPI

FastAPI does not require service classes, but classes can be used for:

- Service objects
- Dependency containers
- Clients
- Application components

The important concern remains lifecycle and scope.

### Celery

Task systems can use classes or registries for organization, but task execution happens across worker processes.

Therefore, class-level state should not be assumed to be shared between Celery workers.

## Class Attributes and Microservices

A class attribute is an internal implementation detail of one service process.

It should never be treated as a cross-service contract.

For example:

```text
Order Service
    |
    +--> Python class state

Payment Service
    |
    +--> Separate process/class state
```

Services communicate through:

- REST
- gRPC
- Kafka
- Other explicit network contracts

Python class attributes remain local to the process.

## Testing Class Attributes

Class-level mutable state can make tests interfere with each other.

Bad pattern:

```python
class Registry:
    handlers: dict[str, type] = {}
```

Test A mutates:

```python
Registry.handlers["order.created"] = HandlerA
```

Test B may unexpectedly observe that registration.

Mitigations include:

- Resetting state explicitly
- Using fixtures
- Avoiding global mutable registries
- Creating registry instances instead
- Isolating process-level state

For pytest, fixtures can manage controlled lifecycle:

```python
import pytest


@pytest.fixture
def registry():
    return SerializerRegistry()
```

Instance-based registries are often easier to test than globally shared class state.

## Class Methods and Testing

Class methods are generally straightforward to test:

```python
def test_user_from_email() -> None:
    user = User.from_email("USER@example.com")

    assert user.email == "user@example.com"
```

For subclass-aware factories:

```python
def test_factory_preserves_subclass() -> None:
    user = AdminUser.guest()

    assert isinstance(user, AdminUser)
```

Testing should verify intended semantics rather than implementation details.

## Security Considerations

Class-level state can accidentally retain sensitive information across requests.

Avoid:

```python
class RequestState:
    current_user = None
```

in a web application.

This is especially dangerous because:

- Requests can be concurrent
- Workers can serve many users
- State can leak between requests
- Async execution can interleave operations

Request-specific state should use request-scoped mechanisms provided by the framework or explicit context propagation.

Never use class attributes as a substitute for authenticated request context.

## Reliability Considerations

Class-level mutable state can disappear during:

- Process restart
- Pod replacement
- Deployment
- Autoscaling
- Crash recovery

Therefore, it should not be the authoritative source for durable business state.

Avoid storing critical state such as:

```text
Order status
Payment status
User permissions
Inventory quantity
Financial balances
```

only in class attributes.

Persist authoritative business state in durable systems such as PostgreSQL.

## Observability

Class-level caches and registries should be observable when they materially affect system behavior.

Useful metrics may include:

```text
cache_hits_total
cache_misses_total
cache_entries
registry_entries
class_cache_evictions_total
```

Avoid silently accumulating unbounded class-level state.

For production services, memory growth should be measurable.

## Performance Considerations

Class attributes can avoid redundant per-instance storage for genuinely shared immutable values.

Class methods introduce normal Python method-binding and function-call overhead, which is typically negligible in backend workloads.

The larger performance risks usually come from:

- Unbounded class-level caches
- Lock contention around shared state
- Repeated initialization
- Import-time registration
- Memory retention
- Hidden database/network work inside class methods

Do not optimize class-vs-instance storage without profiling.

## Production Decision Framework

Use a class attribute when:

```text
The value describes the class
        OR
The value is intentionally shared
        OR
The value is immutable class metadata
```

Use an instance attribute when:

```text
The value belongs to one object
        OR
The value varies per request/object
        OR
The value must be isolated
```

Use a class method when:

```text
The operation needs cls
        OR
The operation constructs an instance
        OR
The operation manages class-level behavior
```

Use a static method when:

```text
The function belongs conceptually to the class
but requires neither self nor cls
```

Use a module-level function when:

```text
There is no meaningful class relationship.
```

## Common Mistakes

### Treating Class Attributes as Per-Instance Defaults

A mutable class attribute is shared.

Use instance initialization for mutable per-object state.

### Using Class State as a Distributed Cache

Class state exists inside one process.

Use Redis or another shared system when state must be shared across replicas.

### Storing Request State on a Class

This can cause cross-request data leakage.

Use request-scoped state.

### Overusing `staticmethod`

A static method can simply become an unnecessarily indirect module function.

Use it only when class namespace association provides real value.

### Hard-Coding the Class Inside a Class Method

Avoid:

```python
class User:
    @classmethod
    def guest(cls):
        return User(...)
```

Prefer:

```python
class User:
    @classmethod
    def guest(cls):
        return cls(...)
```

when subclass-aware construction is intended.

### Unbounded Class-Level Caches

A class-level dictionary can grow for the lifetime of the process.

Use bounded caches, expiration, explicit eviction, or external cache infrastructure where appropriate.

### Hidden Global State

Class-level registries can become effectively global state.

Make ownership, lifecycle, mutation, and reset behavior explicit.

### Using Class Configuration for Runtime Configuration

Environment-specific configuration is generally better represented by explicit configuration objects and dependency injection.

## Production Pitfalls

| Pattern | Risk | Better Approach |
|---|---|---|
| Mutable class attribute | Shared state bugs | Initialize per instance |
| Request data on class | Cross-request leakage | Request-scoped state |
| Class-level cache | Stale/unbounded data | Bounded cache or Redis |
| Class registry | Test/process coupling | Explicit registry object where possible |
| Runtime config on class | Hidden dependencies | Configuration object + DI |
| Hard-coded class in factory | Breaks subclassing | Use `cls` when appropriate |
| Static methods everywhere | Artificial abstractions | Prefer module functions when independent |
| Durable state in class | Data loss on restart | PostgreSQL or durable storage |
| Unsynchronized shared state | Race conditions | Immutable state or synchronization |

## Interview Traps

### What Is a Class Attribute?

An attribute stored or resolved through the class rather than being uniquely stored on an instance.

### Are Class Attributes Shared?

Class attributes can be shared by instances through class-level lookup. Mutable class attributes therefore require particular care.

### What Does `@classmethod` Do?

It creates a method that receives the class as its first argument, conventionally named `cls`.

### What Does `@staticmethod` Do?

It prevents automatic binding of either an instance or class. The function receives only the arguments explicitly passed by the caller.

### When Should You Use `classmethod`?

Common uses include alternative constructors, subclass-aware factories, and class-level operations.

### When Should You Use `staticmethod`?

When behavior logically belongs to a class but requires neither instance state nor class state. Otherwise, consider a module-level function.

### Why Use `cls` Instead of the Class Name?

`cls` allows inherited class methods to construct or operate on the actual subclass.

### Are Class Attributes Process-Global?

No. They are local to the Python process. Multiple workers or Kubernetes replicas have separate class state.

### Can Class Attributes Be Modified Through an Instance?

Yes, depending on the attribute and lookup mechanism. Assigning through an instance typically creates or changes instance state rather than modifying the class attribute.

For example:

```python
class Config:
    timeout = 10


config = Config()
config.timeout = 30

assert Config.timeout == 10
assert config.timeout == 30
```

### Is a Class Attribute the Same as a Global Variable?

No. A class attribute is associated with a class namespace and participates in Python's attribute lookup rules. However, mutable class state can create many of the same architectural problems as global mutable state.

## Production Checklist

Before introducing class-level state or behavior, verify:

- The state genuinely belongs to the class.
- Mutable state is intentional.
- Request-specific data is not stored on the class.
- Cross-process sharing is not incorrectly assumed.
- Thread-safety requirements are understood.
- Cache size and lifecycle are bounded.
- Durable business state is stored externally.
- Tests can isolate or reset class-level state.
- Class methods use `cls` when subclass-aware behavior is intended.
- Static methods are genuinely associated with the class.
- Runtime configuration is explicit and injectable.
- Sensitive information cannot leak through shared state or representations.
- Observability exists for important caches or registries.
- Composition has been considered before introducing class-level global state.

## Key Takeaways

- Class attributes represent class-level state or metadata and are resolved through Python's attribute lookup machinery; mutable class attributes can unintentionally become shared state across instances.
- `@classmethod` receives `cls` and is particularly useful for alternative constructors, subclass-aware factories, and operations that genuinely belong to the class.
- `@staticmethod` receives neither `self` nor `cls`; use it selectively, and prefer a module-level function when there is no meaningful class relationship.
- Class-level state is process-local, so it must not be treated as durable storage, request state, distributed coordination, or a cache shared across Kubernetes replicas.
- Production Python code should keep class-level state intentional, bounded, observable, testable, and thread-safe where necessary, while preferring explicit instance state and dependency injection for request-scoped behavior.