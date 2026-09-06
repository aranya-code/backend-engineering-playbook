# 13- Super

## Overview

`super()` provides a controlled way to continue method and attribute lookup through a class's **Method Resolution Order (MRO)**.

The most common misconception is:

> "`super()` calls my parent class."

More accurately:

> `super()` creates a proxy that performs attribute lookup starting after a specified class in the MRO.

In simple single inheritance, these descriptions often appear equivalent:

```python
class Base:
    def process(self) -> str:
        return "base"


class Service(Base):
    def process(self) -> str:
        return "service:" + super().process()
```

But in multiple inheritance, the distinction becomes critical:

```text
Child
  |
  v
MixinA
  |
  v
MixinB
  |
  v
Base
```

A call to `super()` means:

```text
Continue from the next class in the MRO
```

rather than:

```text
Call the class I visually consider to be my parent
```

Understanding `super()` is essential for:

- Method overriding
- Multiple inheritance
- Mixins
- Cooperative inheritance
- Framework extension points
- Django class-based views
- Abstract base classes
- Constructor chaining
- Correct MRO-based design

## Basic Usage

The modern form is:

```python
super().method()
```

Example:

```python
class BaseService:
    def process(self) -> str:
        return "base"


class OrderService(BaseService):
    def process(self) -> str:
        return "order:" + super().process()
```

Calling:

```python
OrderService().process()
```

returns:

```text
order:base
```

Here `super()` continues lookup after `OrderService` in the MRO.

## Why `super()` Exists

Without `super()`, subclasses often call parent implementations directly:

```python
class OrderService(BaseService):
    def process(self) -> str:
        return "order:" + BaseService.process(self)
```

This creates an explicit dependency on `BaseService`.

Using:

```python
class OrderService(BaseService):
    def process(self) -> str:
        return "order:" + super().process()
```

delegates according to the MRO.

This matters when the inheritance hierarchy evolves.

## `super()` Is an MRO Proxy

Consider:

```python
class A:
    def process(self) -> str:
        return "A"


class B(A):
    def process(self) -> str:
        return "B" + super().process()


class C(B):
    def process(self) -> str:
        return "C" + super().process()
```

The MRO is:

```text
C -> B -> A -> object
```

When `C.process()` executes:

```python
super().process()
```

means:

```text
Start lookup after C
        |
        v
B.process()
```

Then inside `B.process()`:

```python
super().process()
```

means:

```text
Start lookup after B
        |
        v
A.process()
```

Therefore:

```python
C().process()
```

returns:

```text
CBA
```

## Inspecting the MRO

When working with `super()`, inspect the MRO directly:

```python
print(MyClass.__mro__)
```

or:

```python
print(MyClass.mro())
```

A readable form:

```python
print(
    " -> ".join(
        cls.__name__
        for cls in MyClass.__mro__
    )
)
```

Example:

```text
Service -> LoggingMixin -> MetricsMixin -> BaseService -> object
```

This often explains unexpected `super()` behavior immediately.

## `super()` in Single Inheritance

Single inheritance is the simplest case.

```python
class Repository:
    def save(self, value: str) -> str:
        return f"saved:{value}"


class UserRepository(Repository):
    def save(self, value: str) -> str:
        return "user:" + super().save(value)
```

MRO:

```text
UserRepository -> Repository -> object
```

Therefore:

```python
UserRepository().save("123")
```

returns:

```text
user:saved:123
```

In this simple hierarchy, `super()` behaves like a parent delegation mechanism.

## `super()` Is Not a Parent Reference

Consider:

```python
class A:
    ...


class B(A):
    ...


class C(B):
    ...
```

Inside `C`, this:

```python
super()
```

does not mean:

```text
B
```

as a fixed parent object.

It represents a proxy whose lookup starts after `C` in the MRO.

If the hierarchy changes, the next class selected by `super()` can change.

This is precisely what makes cooperative multiple inheritance possible.

## Explicit `super()` Arguments

Python also supports:

```python
super(CurrentClass, instance)
```

For example:

```python
class Base:
    def process(self):
        return "base"


class Service(Base):
    def process(self):
        return super(Service, self).process()
```

In modern Python, prefer:

```python
super().process()
```

The zero-argument form is clearer and less error-prone.

Explicit arguments remain useful in advanced introspection, unusual metaprogramming situations, or when understanding how `super()` works internally.

## `super()` and Multiple Inheritance

This is where `super()` becomes especially important.

```python
class Base:
    def process(self) -> str:
        return "base"


class LoggingMixin(Base):
    def process(self) -> str:
        return "logging:" + super().process()


class MetricsMixin(Base):
    def process(self) -> str:
        return "metrics:" + super().process()


class Service(LoggingMixin, MetricsMixin):
    def process(self) -> str:
        return "service:" + super().process()
```

The MRO is:

```text
Service
   |
LoggingMixin
   |
MetricsMixin
   |
Base
   |
object
```

Calling:

```python
Service().process()
```

returns:

```text
service:logging:metrics:base
```

Each `super()` call advances through the MRO.

## Cooperative Multiple Inheritance

A hierarchy is cooperative when each class performs its responsibility and delegates to the next class using `super()`.

```python
class BaseHandler:
    def handle(self, request):
        return request


class LoggingMixin:
    def handle(self, request):
        print("logging")
        return super().handle(request)


class MetricsMixin:
    def handle(self, request):
        print("metrics")
        return super().handle(request)


class Handler(
    LoggingMixin,
    MetricsMixin,
    BaseHandler,
):
    def handle(self, request):
        print("handler")
        return super().handle(request)
```

Execution order:

```text
Handler
   |
   v
LoggingMixin
   |
   v
MetricsMixin
   |
   v
BaseHandler
```

The classes do not explicitly know each other's identities.

They cooperate through the MRO.

## Why Explicit Parent Calls Break Cooperation

Consider:

```python
class LoggingMixin:
    def handle(self, request):
        print("logging")
        return BaseHandler.handle(self, request)
```

If the hierarchy becomes:

```python
class Handler(
    LoggingMixin,
    MetricsMixin,
    BaseHandler,
):
    ...
```

`MetricsMixin` may be skipped completely.

The explicit call:

```python
BaseHandler.handle(self, request)
```

jumps directly to a specific class.

By contrast:

```python
super().handle(request)
```

continues through the MRO:

```text
LoggingMixin
      |
      v
MetricsMixin
      |
      v
BaseHandler
```

## The MRO Is the Real Contract

Suppose:

```python
class Service(
    LoggingMixin,
    MetricsMixin,
    BaseService,
):
    ...
```

The behavior of:

```python
super().process()
```

depends on:

```text
Service.__mro__
```

Therefore, changing parent order can change runtime behavior.

```python
class Service(
    MetricsMixin,
    LoggingMixin,
    BaseService,
):
    ...
```

produces a different MRO.

This means parent ordering is not cosmetic.

## `super()` and Constructors

`super()` is commonly used to chain `__init__()` methods.

```python
class BaseService:
    def __init__(self) -> None:
        self.started = True


class LoggingMixin:
    def __init__(self, logger) -> None:
        self.logger = logger
        super().__init__()


class OrderService(LoggingMixin, BaseService):
    pass
```

Construction:

```python
service = OrderService(logger)
```

flows through:

```text
OrderService
   |
LoggingMixin.__init__()
   |
BaseService.__init__()
```

Each constructor gets an opportunity to initialize its state.

## Cooperative Constructors

With multiple inheritance, cooperative constructors often use keyword arguments.

```python
class Base:
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class LoggingMixin:
    def __init__(
        self,
        *,
        logger,
        **kwargs,
    ) -> None:
        self.logger = logger
        super().__init__(**kwargs)


class MetricsMixin:
    def __init__(
        self,
        *,
        metrics,
        **kwargs,
    ) -> None:
        self.metrics = metrics
        super().__init__(**kwargs)


class Service(
    LoggingMixin,
    MetricsMixin,
    Base,
):
    pass
```

Instantiation:

```python
service = Service(
    logger=logger,
    metrics=metrics,
)
```

can propagate arguments through the cooperative chain.

This pattern is powerful but should not be introduced casually.

## Constructor Pitfalls

A cooperative constructor can fail if a class consumes an argument incorrectly.

For example:

```python
class LoggingMixin:
    def __init__(self, logger, **kwargs):
        self.logger = logger
        super().__init__(**kwargs)
```

If another class also requires positional arguments, composition may be simpler.

Constructor-heavy multiple inheritance often indicates that dependencies should be explicit collaborators rather than base classes.

## `super()` and Return Values

When chaining methods, the return value should be handled deliberately.

Good:

```python
class Handler:
    def process(self, request):
        result = super().process(request)
        return transform(result)
```

Potentially problematic:

```python
class Handler:
    def process(self, request):
        super().process(request)
```

If the parent contract returns a meaningful value, dropping it can break the chain.

In cooperative hierarchies, classes should agree on:

- Arguments
- Return values
- Exceptions
- Side effects
- State transitions

## `super()` and Method Arguments

Cooperative methods should generally maintain compatible signatures.

For example:

```python
class BaseHandler:
    def handle(self, request, **kwargs):
        ...


class LoggingMixin:
    def handle(self, request, **kwargs):
        self.log(request)
        return super().handle(
            request,
            **kwargs,
        )
```

Using keyword arguments can make cooperative hierarchies easier to extend.

However, excessively flexible `**kwargs` can also hide errors. Use it when the inheritance design genuinely requires cooperative argument propagation.

## `super()` and `staticmethod`

`super()` can resolve attributes that are not ordinary instance methods.

For example:

```python
class Base:
    @staticmethod
    def normalize(value: str) -> str:
        return value.strip()


class Service(Base):
    @staticmethod
    def normalize(value: str) -> str:
        return super().normalize(value)
```

However, zero-argument `super()` is designed around a class/instance context. For static methods, explicit parent references or alternative design approaches may be clearer.

In practice, use `super()` most naturally in instance methods, class methods, and cooperative constructors.

## `super()` and `classmethod`

`super()` works naturally with class methods.

```python
class Base:
    @classmethod
    def create(cls):
        return cls()


class Service(Base):
    @classmethod
    def create(cls):
        instance = super().create()
        instance.initialized = True
        return instance
```

Here:

```python
super().create()
```

continues class-level method lookup according to the MRO.

## `super()` and Properties

`super()` can also access properties.

```python
class Base:
    @property
    def status(self) -> str:
        return "base"


class Service(Base):
    @property
    def status(self) -> str:
        return "service:" + super().status
```

The property descriptor is resolved through the MRO.

This can be useful when extending framework properties, but it should be done only when the parent contract is stable.

## `super()` and Descriptors

`super()` performs attribute lookup and therefore interacts with Python's descriptor protocol.

A method accessed through:

```python
super().process
```

can become a bound method.

Likewise, properties and other descriptors can participate in lookup.

Conceptually:

```text
super()
  |
  v
MRO-based attribute lookup
  |
  v
descriptor handling
  |
  v
bound attribute
```

This is one reason `super()` is more accurately described as a proxy rather than a parent object.

## `super()` and Abstract Base Classes

ABCs can use `super()` for shared behavior.

```python
from abc import ABC, abstractmethod


class Repository(ABC):
    def __init__(self) -> None:
        self.initialized = True

    @abstractmethod
    async def get(self, item_id: int):
        ...
```

A concrete class can explicitly continue initialization:

```python
class PostgresRepository(Repository):
    def __init__(self, pool) -> None:
        super().__init__()
        self.pool = pool
```

This is useful when the base class has real initialization responsibilities.

Do not call `super().__init__()` automatically in every class without understanding whether the parent constructor has meaningful behavior.

## `super()` in Django

Django relies heavily on inheritance and framework extension points.

Class-based views often use `super()` when overriding lifecycle methods.

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView


class UserListView(
    LoginRequiredMixin,
    ListView,
):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(
            request,
            *args,
            **kwargs,
        )
```

The framework's parent implementation may perform important work such as:

- Authentication checks
- Method dispatch
- Context preparation
- Rendering
- Object lookup

Skipping `super()` can silently bypass framework behavior.

Always verify whether a Django extension point is intended to be cooperative before overriding it.

## `super()` and Django Mixins

Django mixins are a practical example of cooperative inheritance.

Consider:

```text
CustomView
   |
LoginRequiredMixin
   |
PermissionMixin
   |
ListView
```

A method override may need to call:

```python
super().dispatch(...)
```

so that each layer gets an opportunity to participate.

The exact MRO should be inspected when combining several mixins.

## `super()` in FastAPI Ecosystems

FastAPI applications more commonly use composition and dependency injection than deep application-service inheritance.

However, FastAPI depends on Starlette and other framework components that use class-based extension mechanisms.

When extending framework classes:

- Inspect the parent implementation.
- Check whether `super()` is required.
- Preserve method signatures.
- Preserve return semantics.
- Avoid bypassing middleware or lifecycle behavior.

For application services, prefer:

```python
class OrderService:
    def __init__(
        self,
        repository: OrderRepository,
    ) -> None:
        self._repository = repository
```

rather than building large inheritance chains.

## `super()` and Dependency Injection

`super()` and dependency injection solve different problems.

`super()` manages behavior within an inheritance hierarchy.

Dependency injection supplies independent collaborators.

Prefer:

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

over:

```python
class OrderService(
    RepositoryMixin,
    PublisherMixin,
):
    ...
```

when the components have independent responsibilities and lifecycles.

## `super()` and Composition

Composition removes the need for many inheritance chains.

Instead of:

```text
OrderService
    |
    +--> LoggingMixin
    +--> MetricsMixin
    +--> RepositoryMixin
    +--> KafkaMixin
```

prefer:

```text
OrderService
    |
    +--> Logger
    +--> Metrics
    +--> Repository
    +--> EventPublisher
```

`super()` is valuable inside a genuine inheritance hierarchy, but it should not be used to force independent system components into one.

## `super()` and Request Lifecycle

Consider a framework handler:

```text
HTTP Request
     |
     v
Framework Handler
     |
     v
Authentication Layer
     |
     v
Logging Layer
     |
     v
Application Handler
     |
     v
Response
```

If each layer is implemented as a cooperative mixin, `super()` controls progression through the chain.

A missing `super()` can therefore change request behavior:

```text
Request
   |
Authentication
   |
   X
Logging/Application handler skipped
```

This is why framework method overrides must be treated as part of the request lifecycle.

## `super()` and Middleware-Like Behavior

A cooperative inheritance chain can resemble middleware:

```python
class LoggingHandler:
    def handle(self, request):
        log_request(request)
        response = super().handle(request)
        log_response(response)
        return response
```

Another layer can wrap it:

```python
class MetricsHandler:
    def handle(self, request):
        start_timer()
        response = super().handle(request)
        record_duration()
        return response
```

This provides before-and-after behavior around downstream handlers.

However, explicit middleware or composition is often clearer when the chain becomes large.

## Error Propagation

A cooperative chain must have a defined error model.

```python
class LoggingMixin:
    def process(self, request):
        try:
            return super().process(request)
        except Exception:
            logger.exception("request failed")
            raise
```

The exception is re-raised so upstream layers can still handle it.

Be careful not to convert or suppress exceptions accidentally:

```python
except Exception:
    return None
```

This can violate the contract expected by downstream or upstream layers.

## Transactions and `super()`

Avoid putting transaction boundaries into arbitrary mixins unless the lifecycle is very well defined.

For example:

```python
class TransactionMixin:
    def process(self, request):
        with transaction():
            return super().process(request)
```

This can be valid in a framework-specific design, but transaction ownership must be explicit.

A transaction spanning:

```text
API
 -> Service
 -> Repository
 -> Kafka
```

has very different semantics from a transaction limited to:

```text
Service
 -> PostgreSQL
```

`super()` does not solve transaction design.

## Resource Management

Similarly, resource acquisition through `super()` requires explicit ownership.

Potentially complex:

```text
Mixin A -> opens database
Mixin B -> opens Kafka producer
Mixin C -> opens HTTP client
Base    -> shutdown
```

It can become unclear which layer owns cleanup.

For production infrastructure, explicit composition and lifecycle management are usually easier to reason about.

## Concurrency Considerations

`super()` itself is not a synchronization mechanism.

If a cooperative method mutates shared state:

```python
class MetricsMixin:
    def process(self, request):
        self.count += 1
        return super().process(request)
```

threading or asyncio safety must be considered independently.

The inheritance mechanism does not make state mutation safe.

## Performance Considerations

`super()` introduces normal Python attribute lookup and method dispatch.

For typical backend applications, this cost is negligible compared with:

- PostgreSQL queries
- Redis requests
- HTTP calls
- Kafka operations
- Serialization
- Disk I/O

Do not replace a clean cooperative design based on speculative performance concerns.

If the code is on a proven hot path:

1. Profile it.
2. Measure method dispatch cost.
3. Compare alternatives.
4. Optimize only if the data supports the change.

## Memory Considerations

`super()` does not copy parent methods into child instances.

The main memory implications come from the inheritance hierarchy itself and state created by participating classes.

Be especially careful with mixins that define class-level mutable state:

```python
class MetricsMixin:
    counters = {}
```

All instances may share that dictionary.

Prefer explicit instance state where appropriate.

## Security Considerations

Skipping `super()` can have security consequences if parent classes implement security-sensitive behavior.

For example:

```python
class AuthorizationMixin:
    def dispatch(self, request, *args, **kwargs):
        self.check_permission(request)
        return super().dispatch(
            request,
            *args,
            **kwargs,
        )
```

If a subclass bypasses the chain:

```python
class Handler(AuthorizationMixin):
    def dispatch(self, request, *args, **kwargs):
        return self.handle(request)
```

the authorization layer may never execute.

Security-sensitive inheritance should therefore be tested at the behavior level.

## Reliability Considerations

A cooperative chain introduces hidden control flow.

For example:

```text
Service
  |
  v
LoggingMixin
  |
  v
RetryMixin
  |
  v
AuthorizationMixin
  |
  v
BaseService
```

A change in any layer can affect the entire chain.

For production reliability:

- Keep inheritance chains shallow.
- Keep mixins focused.
- Preserve `super()` contracts.
- Test important ordering.
- Avoid side effects that are difficult to reason about.
- Document non-obvious ordering requirements.

## Observability

When debugging a complex inheritance hierarchy, inspect the MRO.

```python
logger.debug(
    "handler_mro=%s",
    [
        cls.__name__
        for cls in Handler.__mro__
    ],
)
```

Do not emit this on every production request unless it is specifically required.

More useful operational metrics usually measure business operations:

```text
http_request_duration_seconds
payment_request_duration_seconds
repository_operation_duration_seconds
```

rather than individual `super()` calls.

## Testing `super()` Behavior

Test the resulting behavior rather than implementation details whenever possible.

```python
def test_handler_runs_all_layers():
    handler = Handler()

    result = handler.handle(request)

    assert result is not None
```

If ordering is itself part of the contract:

```python
def test_handler_mro():
    names = [
        cls.__name__
        for cls in Handler.__mro__
    ]

    assert names[:4] == [
        "Handler",
        "LoggingMixin",
        "MetricsMixin",
        "BaseHandler",
    ]
```

Behavioral tests are usually more resilient than hard-coding the entire MRO.

## Common Mistakes

### Thinking `super()` Means Direct Parent

This is the most common misconception.

`super()` follows the MRO.

### Calling a Specific Parent

Avoid:

```python
Base.process(self)
```

when cooperative inheritance is intended.

Prefer:

```python
super().process()
```

### Forgetting `super()`

A missing call can terminate a cooperative chain.

### Calling `super()` Multiple Times

Do not blindly call:

```python
super().process()
super().process()
```

unless the method contract explicitly requires it.

A cooperative chain normally advances once.

### Dropping Return Values

If the parent returns a value, preserve or intentionally transform it.

### Swallowing Exceptions

Do not accidentally hide errors while extending a parent implementation.

### Breaking Constructor Cooperation

A constructor that fails to call `super().__init__()` can leave base-class state uninitialized.

### Assuming `super()` Has No Side Effects

The next implementation may:

- Validate
- Authorize
- Persist data
- Emit events
- Acquire resources
- Transform state

Understand the parent contract before calling it.

### Using `super()` to Justify Complex Inheritance

If the hierarchy exists primarily because `super()` can chain behavior, reconsider whether composition or explicit middleware would be clearer.

## Production Pitfalls

| Pitfall | Impact | Better Approach |
|---|---|---|
| Treating `super()` as direct parent | Incorrect mental model | Think in terms of MRO |
| Explicit parent calls | Breaks cooperative inheritance | Use `super()` |
| Missing `super()` | Skipped behavior | Preserve cooperative chain |
| Wrong mixin order | Different runtime behavior | Design MRO intentionally |
| Dropped return values | Broken contracts | Preserve return semantics |
| Swallowed exceptions | Hidden failures | Re-raise or normalize intentionally |
| Broken constructor chain | Uninitialized state | Cooperate through `super()` |
| Security check skipped | Authorization vulnerability | Test security behavior |
| Deep hierarchy | Hard-to-debug control flow | Prefer shallow hierarchies |
| Infrastructure mixins | Hidden dependencies | Prefer composition |
| Excessive `**kwargs` | Hidden argument errors | Use only when justified |

## Senior-Level Design Guidance

Use `super()` when the inheritance hierarchy is intentional and cooperative.

A good example is:

```text
Framework Base
     ^
     |
AuthenticationMixin
     ^
     |
LoggingMixin
     ^
     |
Custom Handler
```

Each class contributes a focused behavior.

A poor example is:

```text
OrderService
   |
   +--> DatabaseMixin
   +--> RedisMixin
   +--> KafkaMixin
   +--> HTTPMixin
```

These are independent infrastructure dependencies.

They should usually be represented as:

```text
OrderService
   |
   +--> Repository
   +--> Cache
   +--> EventPublisher
   +--> HTTPClient
```

Use `super()` to cooperate within an inheritance hierarchy, not to simulate dependency injection.

## When to Use `super()`

Use `super()` when:

- Overriding a parent method.
- Extending framework behavior.
- Building cooperative mixins.
- Supporting multiple inheritance.
- Chaining compatible constructors.
- Extending class methods or properties.
- Preserving framework lifecycle behavior.

## When Not to Use `super()`

Do not introduce inheritance solely so that `super()` can be used.

Prefer composition when:

- Dependencies are independent components.
- Runtime replacement is required.
- Resources have independent lifecycles.
- Infrastructure clients are involved.
- State ownership needs to be explicit.
- The inheritance hierarchy is becoming difficult to understand.

## Debugging `super()` Problems

When `super()` behaves unexpectedly:

1. Inspect `Class.__mro__`.
2. Identify the current class.
3. Identify the next class in the MRO.
4. Locate the method implementation there.
5. Check whether that implementation calls `super()`.
6. Trace the remaining chain.
7. Check method signatures and return values.
8. Check exception handling.
9. Check constructor cooperation if `__init__()` is involved.
10. Add a behavioral regression test.

Useful diagnostic code:

```python
def describe_mro(cls: type) -> str:
    return " -> ".join(
        base.__name__
        for base in cls.__mro__
    )


print(describe_mro(MyHandler))
```

## `super()` Decision Framework

Before using `super()`, ask:

1. Is this a genuine inheritance relationship?
2. Is the parent behavior something I want to extend?
3. Is the hierarchy cooperative?
4. What is the actual MRO?
5. Does the parent expect `super()` to be called?
6. Are method signatures compatible?
7. Are return values preserved?
8. Are exceptions preserved or intentionally transformed?
9. Is constructor cooperation required?
10. Could composition express the relationship more clearly?

If the answer to the final question is yes, composition is often the better design.

## Interview Reference

| Question | Answer |
|---|---|
| What does `super()` do? | It provides a proxy for attribute lookup continuing from a specific point in the MRO. |
| Does `super()` call the parent? | Not necessarily. It resolves the next implementation according to the MRO. |
| Why is `super()` important in multiple inheritance? | It enables cooperative traversal of the MRO. |
| What algorithm determines MRO? | C3 linearization. |
| Why use `super()` instead of `Base.method(self)`? | It avoids hard-coding a parent and supports cooperative inheritance. |
| What happens if a mixin does not call `super()`? | The cooperative chain may terminate before later classes execute. |
| Can `super()` be used in `__init__()`? | Yes, and it is common in cooperative constructors. |
| Is `super()` a class object? | No. It returns a proxy object that performs MRO-based lookup. |
| Is `super()` always required? | No. It should be used when extending behavior or participating in a cooperative hierarchy. |
| Why is composition often preferable in backend services? | It makes independent dependencies explicit and avoids complex inheritance chains. |

## Production Checklist

Before using or reviewing `super()`:

- The inheritance relationship is intentional.
- The actual MRO is understood.
- Parent ordering is deliberate.
- The hierarchy is cooperative where required.
- Overridden methods preserve compatible signatures.
- Return values are preserved or intentionally transformed.
- Exceptions are propagated or transformed deliberately.
- Constructors cooperate when necessary.
- Framework lifecycle methods call `super()` where required.
- Security-sensitive parent behavior cannot be accidentally bypassed.
- Resource ownership is clear.
- Concurrency assumptions are understood.
- Tests cover important cooperative behavior.
- Composition has been considered as an alternative.
- The inheritance chain remains shallow and understandable.

## Key Takeaways

- `super()` does not simply mean "call my parent"; it provides MRO-aware lookup that continues from the current class through the inheritance chain.
- `super()` is essential for cooperative multiple inheritance because each class can contribute behavior and delegate to the next implementation without hard-coding a parent.
- Always understand the MRO, method signatures, return values, exception behavior, and constructor contracts before relying on `super()`.
- In frameworks such as Django, omitting `super()` from lifecycle methods can bypass important framework behavior, including authentication, dispatch, validation, or rendering.
- Use `super()` within intentional inheritance hierarchies; use composition and dependency injection for independent backend dependencies such as repositories, caches, message publishers, and external clients.