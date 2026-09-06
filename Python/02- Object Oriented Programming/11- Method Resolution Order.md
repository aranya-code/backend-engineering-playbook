# 11- Method Resolution Order

## Overview

Method Resolution Order (MRO) defines the order Python uses to search classes when resolving attributes and methods, especially in inheritance hierarchies and multiple inheritance.

For a simple hierarchy:

```text
Child
  |
  v
Parent
  |
  v
object
```

Python searches:

```text
Child -> Parent -> object
```

For multiple inheritance, the order becomes more important:

```python
class Child(ParentA, ParentB):
    ...
```

Python does not simply search `ParentA` completely and then `ParentB`. It calculates a consistent linear ordering using the **C3 linearization algorithm**.

Understanding MRO is essential when working with:

- Multiple inheritance
- Mixins
- `super()`
- Framework extension points
- Abstract base classes
- Cooperative inheritance
- Complex class hierarchies
- Method overriding

For production backend engineering, the key principle is:

> MRO determines which implementation Python reaches when an attribute or method is not found earlier in the lookup chain.

## Why MRO Exists

Python needs a deterministic way to resolve methods when a class has multiple parents.

Consider:

```python
class A:
    def process(self) -> str:
        return "A"


class B(A):
    def process(self) -> str:
        return "B"


class C(A):
    def process(self) -> str:
        return "C"


class D(B, C):
    pass
```

`D` inherits from both `B` and `C`.

When executing:

```python
D().process()
```

Python needs to decide whether the implementation comes from:

```text
B
```

or:

```text
C
```

The MRO provides the answer.

```python
print(D.__mro__)
```

Conceptually:

```text
D -> B -> C -> A -> object
```

Therefore:

```python
D().process()
```

returns:

```text
B
```

## Inspecting MRO

Python provides multiple ways to inspect MRO.

### `__mro__`

```python
print(D.__mro__)
```

Example output:

```text
(<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

### `mro()`

```python
print(D.mro())
```

This returns the same resolution sequence as a list.

### `help()`

```python
help(D)
```

The class documentation includes the method resolution order.

For debugging inheritance problems, `ClassName.__mro__` is usually the clearest option.

## Basic Single Inheritance

With single inheritance, MRO is straightforward.

```python
class Base:
    def process(self) -> str:
        return "base"


class Service(Base):
    pass
```

The MRO is:

```python
print(Service.__mro__)
```

```text
Service -> Base -> object
```

When calling:

```python
Service().process()
```

Python searches:

1. `Service`
2. `Base`
3. `object`

`process()` is found in `Base`.

## Attribute Lookup and MRO

MRO is relevant to attributes as well as methods.

```python
class Base:
    timeout = 30


class Service(Base):
    pass
```

Then:

```python
service = Service()

print(service.timeout)
```

Python searches through the relevant lookup mechanisms and inheritance hierarchy to find the attribute.

At a high level:

```text
instance
   |
   v
class
   |
   v
MRO
   |
   +--> Service
   +--> Base
   +--> object
```

The exact attribute lookup rules also involve descriptors and instance dictionaries, so MRO should not be confused with the entire Python attribute-access algorithm.

## MRO and Method Overriding

Consider:

```python
class Repository:
    def save(self) -> None:
        print("repository")


class UserRepository(Repository):
    def save(self) -> None:
        print("user repository")
```

The MRO is:

```text
UserRepository -> Repository -> object
```

Calling:

```python
UserRepository().save()
```

finds `save()` immediately in `UserRepository`.

The parent implementation is not automatically called.

To explicitly continue through the inheritance chain, use `super()`.

## MRO and `super()`

`super()` is tightly connected to MRO.

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

Calling:

```python
C().process()
```

produces:

```text
CBA
```

The resolution path is:

```text
C.process()
    |
    v
super() -> B.process()
    |
    v
super() -> A.process()
```

`super()` does not simply mean "call my parent."

It means:

> Continue attribute lookup after the current class in the MRO.

This distinction becomes critical with multiple inheritance.

## The MRO of Multiple Inheritance

Consider:

```python
class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass
```

The hierarchy is:

```text
      A
     / \
    B   C
     \ /
      D
```

The MRO is:

```text
D -> B -> C -> A -> object
```

This ordering avoids visiting `A` twice.

Python therefore produces a single linear sequence from a potentially complex inheritance graph.

## C3 Linearization

Python uses **C3 linearization** to calculate MRO.

The algorithm produces an ordering that preserves important constraints:

- The child appears before its parents.
- Parent ordering declared in the class definition is respected.
- The local precedence order is preserved.
- A class does not appear before one of its subclasses.
- A consistent monotonic ordering is maintained.

For:

```python
class D(B, C):
    pass
```

Python must preserve:

```text
B before C
```

because the declaration says:

```python
(B, C)
```

It must also preserve:

```text
B before A
C before A
```

when both inherit from `A`.

The resulting ordering is:

```text
D -> B -> C -> A -> object
```

## Why Python Uses C3

A naive depth-first search can produce surprising or inconsistent results in diamond inheritance.

C3 provides a deterministic and monotonic method resolution order.

This is particularly important for cooperative multiple inheritance.

Without a consistent MRO, `super()` chains could become unpredictable.

## Diamond Inheritance

A diamond hierarchy looks like:

```text
       Base
      /    \
     A      B
      \    /
       Child
```

Example:

```python
class Base:
    def process(self) -> None:
        print("base")


class A(Base):
    def process(self) -> None:
        print("A")
        super().process()


class B(Base):
    def process(self) -> None:
        print("B")
        super().process()


class Child(A, B):
    def process(self) -> None:
        print("child")
        super().process()
```

The MRO is:

```text
Child -> A -> B -> Base -> object
```

Calling:

```python
Child().process()
```

produces:

```text
child
A
B
base
```

Notice that `Base.process()` runs exactly once.

This is one of the major benefits of cooperative multiple inheritance.

## Cooperative Multiple Inheritance

Cooperative inheritance means each class participates in the inheritance chain by calling `super()`.

```python
class Base:
    def process(self) -> None:
        print("base")


class LoggingMixin:
    def process(self) -> None:
        print("logging")
        super().process()


class MetricsMixin:
    def process(self) -> None:
        print("metrics")
        super().process()


class Service(LoggingMixin, MetricsMixin, Base):
    def process(self) -> None:
        print("service")
        super().process()
```

MRO:

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

Execution:

```text
service
logging
metrics
base
```

Each class contributes behavior and delegates to the next class in the MRO.

## Why `super()` Is Better Than Explicit Parent Calls

Avoid:

```python
class Service(Base):
    def process(self) -> None:
        Base.process(self)
```

Prefer:

```python
class Service(Base):
    def process(self) -> None:
        super().process()
```

Explicit parent calls:

- Hard-code a specific parent.
- Do not cooperate naturally with multiple inheritance.
- Can cause duplicated execution.
- Make refactoring more difficult.

`super()` follows the MRO instead.

## `super()` in Multiple Inheritance

Consider:

```python
class A:
    def process(self) -> None:
        print("A")


class B(A):
    def process(self) -> None:
        print("B")
        super().process()


class C(A):
    def process(self) -> None:
        print("C")
        super().process()


class D(B, C):
    def process(self) -> None:
        print("D")
        super().process()
```

The MRO is:

```text
D -> B -> C -> A -> object
```

The call:

```python
D().process()
```

follows:

```text
D
 |
 v
B
 |
 v
C
 |
 v
A
```

This is why `super()` must be understood as MRO traversal rather than parent invocation.

## `super()` With Explicit Arguments

The zero-argument form is normally preferred:

```python
super().process()
```

Python can infer:

- The current class
- The current instance

Conceptually, this is related to:

```python
super(CurrentClass, self)
```

but the explicit form is rarely necessary in modern Python.

## MRO Conflicts

Not every multiple-inheritance hierarchy has a valid MRO.

Consider:

```python
class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass
```

This hierarchy is valid.

But conflicting parent ordering can make an MRO impossible.

For example:

```python
class A:
    pass


class B(A):
    pass


class C(A):
    pass


class X(B, C):
    pass


class Y(C, B):
    pass


class Z(X, Y):
    pass
```

Python cannot create a consistent ordering for `Z`.

The class definition raises:

```text
TypeError: Cannot create a consistent method resolution
order (MRO) for bases ...
```

The important point is that Python rejects an inconsistent hierarchy rather than silently choosing an arbitrary order.

## MRO and Local Precedence

Consider:

```python
class A:
    pass


class B:
    pass


class C(A, B):
    pass
```

The local precedence order is:

```text
A before B
```

Therefore:

```python
C.__mro__
```

begins with:

```text
C -> A -> B
```

Changing the declaration:

```python
class C(B, A):
    pass
```

changes the MRO:

```text
C -> B -> A
```

The parent order in the class definition is therefore significant.

## MRO and Method Selection

Suppose:

```python
class Base:
    def execute(self) -> str:
        return "base"


class LoggingMixin:
    def execute(self) -> str:
        return "logging"


class Service(LoggingMixin, Base):
    pass
```

MRO:

```text
Service -> LoggingMixin -> Base -> object
```

Calling:

```python
Service().execute()
```

returns:

```text
logging
```

because `LoggingMixin` is encountered before `Base`.

The method does not need to be copied into `Service`.

## MRO and Attribute Shadowing

The same inheritance order influences inherited attributes.

```python
class Base:
    timeout = 30


class FastMixin:
    timeout = 5


class Service(FastMixin, Base):
    pass
```

Then:

```python
Service.timeout
```

resolves to:

```text
5
```

because `FastMixin` occurs first in the MRO.

This can become dangerous when multiple mixins define the same configuration attributes.

## MRO and Descriptors

Python attribute lookup is more sophisticated than simply iterating through `__mro__`.

Descriptors can participate in attribute resolution:

```python
class Descriptor:
    def __get__(self, instance, owner):
        return "value"


class Base:
    field = Descriptor()
```

Frameworks such as Django rely heavily on descriptors and class-level metadata.

Therefore, when debugging attribute resolution, remember:

```text
MRO
  +
descriptor protocol
  +
instance/class namespaces
  =
attribute access behavior
```

MRO is a major part of resolution, but not the entire mechanism.

## MRO in Django

Django uses multiple inheritance in several framework components.

Class-based views are a common example:

```python
from django.views.generic import ListView


class UserListView(ListView):
    ...
```

More complex views may combine mixins:

```python
class AuthenticatedUserListView(
    LoginRequiredMixin,
    ListView,
):
    ...
```

The MRO determines how methods inherited from:

- `LoginRequiredMixin`
- `ListView`
- Their parent classes

are resolved.

Framework mixins often depend on cooperative inheritance and `super()`.

Incorrectly overriding a framework method without calling `super()` can bypass important framework behavior.

## MRO in FastAPI and Starlette

FastAPI and Starlette also expose class-based extension points and middleware abstractions where inheritance may appear.

When extending framework classes, verify:

- Which method is being overridden.
- Whether the framework expects `super()`.
- The actual MRO.
- Whether a mixin participates cooperatively.

Do not assume that overriding a method and omitting `super()` is harmless.

## MRO and Mixins

Mixins are classes designed to provide focused behavior rather than represent complete domain entities.

Example:

```python
class AuditMixin:
    def audit(self, event: str) -> None:
        ...
```

A service can combine:

```python
class AuditedService(AuditMixin, BaseService):
    ...
```

Mixins work best when they are:

- Small
- Focused
- Stateless or carefully stateful
- Cooperative with `super()` when overriding methods
- Independent of unrelated implementation details

## Mixin Ordering

Mixin order matters.

```python
class Service(
    LoggingMixin,
    MetricsMixin,
    BaseService,
):
    ...
```

is not necessarily equivalent to:

```python
class Service(
    MetricsMixin,
    LoggingMixin,
    BaseService,
):
    ...
```

The MRO changes.

For behavior-changing mixins, ordering should therefore be intentional and documented when necessary.

## MRO and Framework Hooks

Frameworks frequently implement hook methods.

For example:

```python
class BaseHandler:
    def handle(self, request):
        ...


class LoggingHandler(BaseHandler):
    def handle(self, request):
        self.log(request)
        return super().handle(request)
```

If another mixin participates:

```python
class MetricsHandler(BaseHandler):
    def handle(self, request):
        self.record(request)
        return super().handle(request)
```

the MRO determines which hook executes first.

This pattern is useful for:

- Logging
- Metrics
- Authorization
- Validation
- Caching
- Request preprocessing

But it should be used carefully because behavior can become distributed across the MRO.

## MRO and `__init__`

Constructors also participate in the MRO.

```python
class Base:
    def __init__(self) -> None:
        print("base")


class LoggingMixin:
    def __init__(self) -> None:
        print("logging")
        super().__init__()


class Service(LoggingMixin, Base):
    def __init__(self) -> None:
        print("service")
        super().__init__()
```

The MRO is:

```text
Service -> LoggingMixin -> Base -> object
```

Construction produces:

```text
service
logging
base
```

For cooperative initialization, each participating class should generally call `super().__init__()`.

## Cooperative `__init__` With Arguments

Multiple inheritance becomes more difficult when constructors require different arguments.

A common cooperative pattern uses keyword arguments:

```python
class Base:
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class LoggingMixin:
    def __init__(self, *, logger, **kwargs) -> None:
        self.logger = logger
        super().__init__(**kwargs)


class Service(LoggingMixin, Base):
    def __init__(self, *, logger, **kwargs) -> None:
        super().__init__(logger=logger, **kwargs)
```

This can work, but it also increases complexity.

In application code, composition is often clearer when initialization requirements become complicated.

## MRO and Abstract Base Classes

ABCs participate in MRO like normal classes.

```python
from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    async def get(self, item_id: int):
        ...


class CachedRepositoryMixin:
    async def get_cached(self, item_id: int):
        ...


class UserRepository(CachedRepositoryMixin, Repository):
    async def get(self, item_id: int):
        ...
```

The MRO determines how inherited behavior and methods are found.

ABCs can also participate in more complex hierarchies, but excessive combinations can make the class graph difficult to reason about.

## Virtual Subclasses

ABCs support registration of virtual subclasses.

```python
from abc import ABC


class Repository(ABC):
    pass


class ExternalRepository:
    pass


Repository.register(ExternalRepository)
```

Now:

```python
isinstance(ExternalRepository(), Repository)
```

can return:

```text
True
```

even though `ExternalRepository` does not explicitly inherit from `Repository`.

This affects `issubclass()` and `isinstance()` behavior but does not mean methods from the ABC are physically inherited.

Virtual subclassing is a specialized feature and should not be used casually.

## MRO and `__mro_entries__`

Python also allows objects used in a class bases list to customize how bases are resolved through `__mro_entries__`.

This is an advanced mechanism used by parts of the Python ecosystem.

For most backend application code, direct inheritance, protocols, and composition are preferable.

Understanding that Python's class creation machinery can transform bases helps explain why the actual MRO may involve mechanisms beyond the literal class declaration.

## Internal Class Creation Flow

At a high level, class creation involves:

```text
class definition
      |
      v
evaluate bases
      |
      v
resolve MRO
      |
      v
create class namespace
      |
      v
metaclass creates class
      |
      v
class object
```

For multiple inheritance, Python must establish a valid MRO before the class can be created.

If no consistent MRO exists, class creation fails.

## Runtime Method Lookup

A simplified conceptual model for:

```python
obj.process()
```

is:

```text
obj
 |
 v
attribute lookup
 |
 v
type(obj)
 |
 v
MRO traversal
 |
 +--> Class 1
 +--> Class 2
 +--> Class 3
 +--> object
 |
 v
descriptor / method binding
 |
 v
call
```

The actual implementation is optimized in CPython and includes descriptor handling and attribute caches, but the MRO provides the class-ordering foundation.

## Performance Considerations

MRO traversal is normally not a meaningful performance bottleneck in backend applications.

Python implementations optimize attribute access heavily.

The expensive operations in a typical backend are more likely to be:

- PostgreSQL queries
- Network requests
- Serialization
- Redis operations
- Kafka communication
- Disk I/O

Do not flatten a useful class hierarchy solely because of theoretical MRO lookup cost.

However, deeply complicated inheritance hierarchies can increase:

- Debugging time
- Cognitive complexity
- Maintenance cost
- Risk of accidental behavior changes

Architectural complexity is usually the larger concern.

## Memory Considerations

MRO itself does not duplicate inherited method implementations into every subclass.

The class maintains references to its inheritance metadata and method resolution structures.

However, complex inheritance can increase the number of classes, mixins, descriptors, and objects in the system.

The main production concern is generally maintainability rather than raw memory usage.

## MRO and Concurrency

MRO itself is not a concurrency mechanism.

Class definitions and method resolution metadata are generally shared by all instances in a process.

The danger comes from mutable state stored in classes or inherited components:

```python
class MetricsMixin:
    counters = {}
```

All instances may share that class-level state.

When such objects are used concurrently, synchronization or a different state-management design may be required.

Prefer instance-level state or dedicated concurrency-safe components where appropriate.

## MRO Across Processes

In a Kubernetes deployment:

```text
Pod A
    |
    +--> Python process
    +--> MRO metadata

Pod B
    |
    +--> Python process
    +--> MRO metadata
```

Each Python process has its own class objects and MRO metadata.

MRO does not provide shared state across:

- Processes
- Containers
- Pods
- Machines

Distributed coordination must use appropriate infrastructure such as PostgreSQL, Redis, Kafka, or another shared system.

## Security Considerations

MRO can affect which security-sensitive implementation is executed.

For example, if an authorization mixin is expected to run before a handler:

```python
class SecureHandler(AuthMixin, BaseHandler):
    ...
```

changing the order:

```python
class SecureHandler(BaseHandler, AuthMixin):
    ...
```

may alter method resolution and potentially bypass intended behavior.

Security-sensitive inheritance should therefore be:

- Explicit
- Tested
- Easy to inspect
- Resistant to accidental reordering

For critical authorization boundaries, explicit composition can sometimes be easier to audit than complex multiple inheritance.

## Reliability Considerations

Inheritance chains can create hidden dependencies.

A method may appear local:

```python
class PaymentService(BaseService):
    def process(self):
        ...
```

but behavior can depend on:

```text
PaymentService
   |
   v
AuditMixin
   |
   v
RetryMixin
   |
   v
BaseService
```

Changing one parent or mixin can therefore affect runtime behavior far away from the modification.

For production reliability:

- Keep hierarchies shallow.
- Keep mixins focused.
- Use `super()` consistently in cooperative hierarchies.
- Add tests for important MRO-dependent behavior.
- Inspect MRO when debugging inheritance issues.

## Observability

MRO problems often appear as unexpected behavior rather than obvious errors.

Useful debugging techniques include:

```python
logger.debug(
    "handler_mro=%s",
    [cls.__name__ for cls in Handler.__mro__],
)
```

Do not normally log MRO information on every request.

Instead, inspect it during:

- Debugging
- Startup diagnostics
- Development
- Targeted troubleshooting

Avoid exposing unnecessary internal implementation details through production APIs.

## Testing MRO-Dependent Behavior

If behavior depends on inheritance ordering, test the actual contract.

For example:

```python
def test_handler_mro():
    names = [
        cls.__name__
        for cls in Handler.__mro__
    ]

    assert names[:3] == [
        "Handler",
        "LoggingMixin",
        "BaseHandler",
    ]
```

More importantly, test behavior:

```python
def test_logging_runs_before_handler():
    ...
```

Testing only the exact MRO can make tests unnecessarily coupled to implementation.

Use MRO assertions when the ordering itself is a meaningful architectural requirement.

## Common Mistakes

### Thinking `super()` Means "Parent"

`super()` follows the MRO after the current class. It does not simply select the direct parent.

### Forgetting `super()`

In cooperative multiple inheritance, omitting `super()` can terminate the chain.

```python
class LoggingMixin:
    def process(self):
        log()
        # Chain stops here.
```

### Calling a Parent Explicitly

Avoid:

```python
Base.process(self)
```

when cooperative inheritance is intended.

Prefer:

```python
super().process()
```

### Ignoring Parent Order

These are different:

```python
class Service(A, B):
    ...
```

and:

```python
class Service(B, A):
    ...
```

Their MROs differ.

### Using Multiple Inheritance Without Understanding the MRO

Multiple inheritance can work well, but only when the hierarchy is intentionally designed.

### Creating Deep Hierarchies

Deep inheritance increases the amount of code that must be understood before changing a method.

### Sharing Mutable State Through Mixins

A class-level mutable object can unexpectedly be shared across instances.

### Overriding Framework Hooks Without `super()`

This can silently bypass framework behavior.

## Production Pitfalls

| Pitfall | Impact | Better Approach |
|---|---|---|
| Incorrect mixin order | Unexpected behavior | Design and test MRO |
| Missing `super()` | Broken cooperative chain | Call `super()` consistently |
| Explicit parent calls | Multiple-inheritance bugs | Use cooperative `super()` |
| Deep hierarchy | High maintenance cost | Prefer shallow hierarchies |
| Giant mixins | Hidden dependencies | Keep mixins focused |
| Mutable class state | Concurrency bugs | Use instance or dedicated state |
| Framework override without `super()` | Missing framework behavior | Check extension contract |
| MRO-only testing | Brittle tests | Prefer behavioral tests |
| Security mixin ordering ignored | Authorization risk | Make security boundaries explicit |
| Assuming identical parent APIs | Runtime surprises | Define clear contracts |

## Senior-Level Design Guidance

MRO is most valuable when you deliberately use multiple inheritance.

A practical hierarchy should be easy to visualize:

```text
Concrete Service
   |
   +--> LoggingMixin
   |
   +--> MetricsMixin
   |
   +--> BaseService
```

If understanding the behavior requires tracing ten classes across several modules, the inheritance model is probably too complex.

For application services, repositories, clients, and infrastructure components, composition is frequently clearer:

```text
OrderService
   |
   +--> OrderRepository
   +--> PaymentGateway
   +--> EventPublisher
```

Use inheritance when the subtype relationship and method-resolution behavior are genuinely useful.

Use composition when components primarily collaborate.

## When to Use Multiple Inheritance

Multiple inheritance can be appropriate for:

- Small, orthogonal mixins
- Framework extension points
- Shared cross-cutting behavior
- Cooperative framework classes
- Well-defined reusable interfaces

Avoid it when:

- Classes contain significant independent state.
- Constructor requirements become complicated.
- Parent ordering is difficult to understand.
- Methods frequently collide.
- `super()` behavior is unclear.
- Composition would be simpler.

## Debugging an MRO Problem

When a method behaves unexpectedly:

1. Inspect the actual class.
2. Print its MRO.
3. Identify where the method first appears.
4. Check whether the method calls `super()`.
5. Trace the remaining MRO chain.
6. Check descriptors if attribute lookup is involved.
7. Check mixin ordering.
8. Check framework documentation for cooperative inheritance expectations.
9. Add a behavioral regression test.

Useful commands:

```python
print(MyClass.__mro__)

print(
    [cls.__name__ for cls in MyClass.mro()]
)
```

For deeper inspection:

```python
import inspect

print(inspect.getmro(MyClass))
```

## MRO Decision Checklist

Before introducing or modifying multiple inheritance:

- Is inheritance actually the right relationship?
- Is the MRO easy to understand?
- Are parent classes ordered intentionally?
- Are mixins small and orthogonal?
- Does each cooperative method call `super()`?
- Are constructor arguments compatible?
- Could composition provide a clearer design?
- Are framework hooks being overridden correctly?
- Are important MRO-dependent behaviors tested?
- Are security-sensitive behaviors protected from accidental ordering changes?
- Is the hierarchy shallow enough for future maintainers to understand?

## Interview Reference

| Question | Answer |
|---|---|
| What is MRO? | The order Python uses to search classes for inherited attributes and methods. |
| What algorithm does Python use? | C3 linearization. |
| How do you inspect MRO? | `Class.__mro__` or `Class.mro()`. |
| What does `super()` do? | Continues lookup according to the MRO after the current class. |
| Does `super()` always call the parent? | No. It follows the next class in the MRO. |
| Why is MRO important with multiple inheritance? | It provides deterministic method and attribute resolution. |
| What is diamond inheritance? | A hierarchy where two branches share a common ancestor. |
| What is cooperative inheritance? | Classes use `super()` so each class can participate in the MRO chain. |
| Can Python reject a class definition because of MRO? | Yes, if no consistent MRO can be created. |
| Why is composition often preferred in backend systems? | It avoids complex inheritance coupling and makes dependencies explicit. |

## Key Takeaways

- Python's MRO defines the deterministic class search order for inherited methods and attributes; multiple inheritance uses C3 linearization to produce a consistent order.
- `super()` means "continue according to the MRO," not simply "call my parent," which is why it is essential for cooperative multiple inheritance.
- Mixins and framework extension points can use MRO effectively, but parent ordering, constructor behavior, and `super()` participation must be intentional.
- Deep or complicated MRO chains increase maintenance and reliability risk; for most backend services and infrastructure components, composition is often clearer than multiple inheritance.
- When debugging inheritance behavior, inspect `Class.__mro__`, trace the first matching implementation and `super()` chain, and validate the resulting behavior with focused tests.