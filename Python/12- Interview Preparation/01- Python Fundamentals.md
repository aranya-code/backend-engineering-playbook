# README

## Overview

The `12- Interview Preparation` section consolidates the Python knowledge required for backend engineering interviews, coding assessments, debugging exercises, data-engineering scenarios, AWS-oriented problems, and Python-based system design discussions.

The goal is not to memorize isolated Python facts. The goal is to develop the ability to:

- explain Python runtime behavior precisely;
- write correct and idiomatic code under time constraints;
- reason about complexity, memory, and concurrency;
- debug unfamiliar code;
- identify production failure modes;
- choose appropriate Python abstractions;
- solve backend-oriented coding problems;
- connect language behavior to system design decisions.

This section builds on the concepts developed throughout the Python Forge Playbook.

```text
Python Fundamentals
        │
        ▼
Object Model + Intermediate Python
        │
        ▼
Errors + Types + Data Modeling
        │
        ▼
Concurrency + Memory + Performance
        │
        ▼
Backend Python + Testing
        │
        ▼
Interview Preparation
        │
        ├── Conceptual Questions
        ├── Coding Problems
        ├── Debugging
        ├── Backend Scenarios
        ├── Data Engineering
        ├── AWS
        └── System Design
```

---

## Section Structure

```text
12- Interview Preparation/
│
├── 01- Python Fundamentals.md
└── README.md
```

The interview-preparation section is intentionally organized around **interview-oriented synthesis** rather than duplicating every Python concept from the earlier sections.

---

## Interview Preparation Philosophy

A strong Python interview answer should usually operate at three levels:

```text
Level 1: What
    │
    ▼
Define the concept accurately

Level 2: How
    │
    ▼
Explain Python's behavior and implementation

Level 3: Why
    │
    ▼
Explain engineering tradeoffs and production impact
```

For example, when asked about Python dictionaries:

```text
What:
    Hash-based mapping

How:
    Keys are hashed and used for lookup

Why:
    Average-case O(1) lookup supports efficient indexing,
    caching, routing, and application state
```

Senior-level interviews frequently evaluate the third level.

---

## Interview Categories

Python interviews commonly span several dimensions.

| Category | What to demonstrate |
|---|---|
| Language fundamentals | Correct Python semantics |
| Data structures | Appropriate structure and complexity |
| OOP | Object-model understanding and design |
| Intermediate Python | Functions, decorators, generators, contexts |
| Exceptions | Failure handling and recovery |
| Type system | Maintainable typed Python |
| Concurrency | Threads, processes, asyncio |
| Memory | References, mutability, GC |
| Performance | Complexity and measurement |
| Testing | Isolation, mocks, integration |
| Backend | APIs, databases, queues, caching |
| Data engineering | ETL, files, SQL, Pandas/NumPy |
| AWS | Cloud-oriented Python scenarios |
| System design | Architecture and tradeoffs |
| Debugging | Root-cause analysis |

---

## Python Fundamentals

**`01- Python Fundamentals.md`** focuses on the core language concepts most frequently used as interview foundations.

Topics should include:

- Python execution model;
- variables and object references;
- built-in data types;
- mutability and immutability;
- equality and identity;
- truthiness;
- control flow;
- functions;
- argument passing;
- default arguments;
- positional and keyword arguments;
- `*args` and `**kwargs`;
- comprehensions;
- iterables and iterators;
- generators;
- modules and imports;
- packages;
- built-in functions;
- exceptions;
- basic complexity reasoning.

These concepts form the vocabulary required for more advanced interview questions.

---

## Object References

One of the most important Python interview concepts is that variables are names bound to objects.

```python
items = [1, 2, 3]
alias = items

alias.append(4)

print(items)
```

Both names refer to the same list.

```text
items ──────┐
            ▼
        [1, 2, 3, 4]
            ▲
            │
alias ──────┘
```

This explains many interview questions involving:

- mutation;
- function arguments;
- shallow copies;
- default arguments;
- aliasing.

---

## `is` vs `==`

Use:

```python
a == b
```

to test equality.

Use:

```python
a is b
```

to test object identity.

The canonical `None` check is:

```python
if value is None:
    ...
```

Do not rely on identity for arbitrary value comparisons.

---

## Mutable vs Immutable Objects

Common mutable objects include:

- `list`;
- `dict`;
- `set`;
- most user-defined mutable objects.

Common immutable objects include:

- `int`;
- `float`;
- `bool`;
- `str`;
- `tuple` when its elements are immutable;
- `frozenset`.

Interview questions often test whether you understand that immutability is a property of the object, not the variable name.

---

## Function Arguments

Python uses object references in argument passing.

Consider:

```python
def add_item(items):
    items.append("x")


values = []
add_item(values)

print(values)
```

The function receives a reference to the same list object.

Rebinding the parameter is different:

```python
def replace(items):
    items = ["new"]
```

The caller's variable is not rebound.

This distinction is fundamental when reasoning about mutation and side effects.

---

## Default Arguments

Default arguments are evaluated when the function is defined.

Avoid:

```python
def add_item(item, items=[]):
    items.append(item)
    return items
```

The list is shared across calls.

Prefer:

```python
def add_item(item, items=None):
    if items is None:
        items = []

    items.append(item)
    return items
```

This is a common interview question because it tests understanding of function-definition time versus function-call time.

---

## Late Binding

Closures capture variables, not necessarily their values at the moment a function is created.

For example:

```python
functions = [
    lambda: i
    for i in range(3)
]
```

Calling the functions later can produce the same final value of `i`.

A common technique for binding the current value is:

```python
functions = [
    lambda i=i: i
    for i in range(3)
]
```

The important interview concept is the difference between **late binding** and explicit value capture.

---

## Comprehensions

Comprehensions provide concise collection construction.

```python
active_ids = [
    customer.id
    for customer in customers
    if customer.status == "active"
]
```

They are generally preferable to verbose loops when the transformation is simple.

Avoid deeply nested comprehensions that become harder to read than an explicit loop.

---

## Iterables and Iterators

An iterable can produce an iterator.

```python
iterator = iter(items)
value = next(iterator)
```

An iterator implements the iterator protocol, including `__iter__()` and `__next__()`.

This distinction matters for:

- generators;
- streaming;
- lazy processing;
- file handling;
- large datasets.

---

## Generators

Generators produce values lazily.

```python
def read_ids(rows):
    for row in rows:
        yield row["id"]
```

Instead of materializing everything:

```text
Database
   │
   ▼
All rows in memory
```

a generator can support:

```text
Database
   │
   ▼
One item
   │
   ▼
Process
   │
   ▼
Next item
```

This is important for memory-efficient backend and data-processing workflows.

---

## Modules and Imports

Understand the distinction between:

```python
import module
```

and:

```python
from module import function
```

Imports bind names in the importing module.

This is especially important for testing:

```text
module_a.py
    │
    └── from module_b import function

test
    │
    └── patch module_a.function
```

The general testing rule is:

> Patch where the code under test looks up the dependency.

---

## Built-in Data Structures

Interview questions frequently compare:

| Structure | Typical strengths |
|---|---|
| `list` | Ordered sequence, indexed access |
| `tuple` | Immutable sequence |
| `dict` | Key/value lookup |
| `set` | Membership and uniqueness |
| `deque` | Efficient operations at both ends |
| `heapq` | Priority queue behavior |

Selection should follow the required operations rather than habit.

---

## Complexity Reasoning

Interview solutions should identify algorithmic complexity.

Typical expectations:

| Operation | Typical complexity |
|---|---:|
| List indexing | O(1) |
| List append | Amortized O(1) |
| List membership | O(n) |
| Dict lookup | Average O(1) |
| Set membership | Average O(1) |
| Sorting | O(n log n) |
| Deque append/pop at ends | O(1) |

These are typical complexity characteristics, not guarantees that every operation has identical runtime across all implementations or workloads.

---

## OOP Interview Topics

Important areas include:

- classes and objects;
- instance attributes;
- class attributes;
- inheritance;
- composition;
- polymorphism;
- abstraction;
- method resolution order;
- multiple inheritance;
- `super()`;
- descriptors;
- properties;
- abstract base classes;
- protocols;
- dependency injection.

A senior-level answer should explain when composition is preferable to inheritance.

---

## Composition vs Inheritance

Inheritance expresses an **is-a** relationship.

Composition expresses a **has-a/uses-a** relationship.

For backend systems, composition is often easier to evolve:

```text
OrderService
    │
    ├── PaymentClient
    ├── OrderRepository
    └── EventPublisher
```

instead of creating a deep inheritance hierarchy.

This also improves dependency injection and testability.

---

## Python Protocols

Protocols support structural typing.

```python
from typing import Protocol


class Repository(Protocol):
    async def get(self, customer_id: str) -> Customer | None:
        ...
```

Any compatible implementation can satisfy the protocol without explicitly inheriting from it.

This is useful for:

- dependency injection;
- testing;
- loose coupling;
- architectural boundaries.

---

## Decorators

Decorators modify or wrap callable behavior.

Common backend uses include:

- authentication;
- logging;
- tracing;
- retries;
- caching;
- metrics;
- authorization.

Example:

```python
from functools import wraps


def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Calling %s", func.__name__)
        return func(*args, **kwargs)

    return wrapper
```

Interview discussions should include:

- closures;
- wrapper functions;
- `functools.wraps`;
- decorator order;
- async decorators.

---

## Context Managers

Context managers define resource lifecycle.

```python
with database.transaction():
    create_order()
    create_payment()
```

Conceptually:

```text
Enter
  │
  ▼
Acquire resource
  │
  ▼
Execute operation
  │
  ▼
Cleanup / exit
```

They are particularly important for:

- files;
- locks;
- transactions;
- database sessions;
- tracing spans;
- temporary resources.

---

## Exception Handling

Senior-level exception discussions should cover:

- exception hierarchy;
- custom exceptions;
- exception chaining;
- retryability;
- cleanup;
- error translation;
- API error mapping.

Prefer:

```python
try:
    result = repository.get(customer_id)
except CustomerNotFoundError as exc:
    raise CustomerAPIError("Customer not found") from exc
```

The `from exc` preserves the causal relationship.

---

## Retryability

Not every exception should be retried.

A useful classification:

```text
Error
 │
 ├── Transient → potentially retry
 │
 └── Permanent → fail immediately
```

Examples of potentially transient failures:

- connection timeout;
- temporary service unavailability;
- network interruption.

Examples of generally non-retryable failures:

- invalid input;
- authorization failure;
- malformed request;
- violated business rule.

Retries must also consider idempotency.

---

## Type System Interview Topics

Know:

- type hints;
- `Optional` / `| None`;
- `Union` / `|`;
- `Any`;
- `Never`;
- `NoReturn`;
- `Callable`;
- `TypeVar`;
- generics;
- `TypedDict`;
- `Literal`;
- protocols;
- type guards;
- overloads;
- static type checking;
- mypy;
- Pyright.

The senior-level concern is how typing improves maintainability without pretending that Python becomes statically enforced at runtime.

---

## Dataclasses

Dataclasses reduce boilerplate for data-oriented classes.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str
```

Interview discussions may include:

- generated methods;
- equality;
- mutability;
- `frozen=True`;
- `slots=True`;
- inheritance;
- `default_factory`;
- serialization considerations.

---

## Concurrency

Python concurrency questions commonly involve:

```text
Concurrency
   │
   ├── Threads
   ├── Processes
   └── asyncio
```

Choose based on workload.

| Workload | Typical approach |
|---|---|
| I/O-bound synchronous code | Threads |
| CPU-bound parallel work | Processes |
| High-volume async I/O | asyncio |
| Independent worker jobs | Processes / task queue |

The Global Interpreter Lock is important for understanding CPython threading behavior, but it is not the entire concurrency model.

---

## Asyncio

`asyncio` is designed primarily for cooperative asynchronous I/O.

```python
async def fetch_customer(client, customer_id):
    response = await client.get(
        f"/customers/{customer_id}"
    )

    return response.json()
```

The event loop schedules tasks while operations are awaiting.

A critical interview point:

> `async def` does not automatically make blocking code non-blocking.

Calling blocking database, filesystem, or CPU-heavy operations directly inside an event-loop task can stall unrelated requests.

---

## Event Loop

Conceptually:

```text
Event Loop
    │
    ├── Task A → await I/O
    ├── Task B → run
    ├── Task C → await I/O
    └── Task D → run
```

The loop can execute other ready tasks while one task awaits an asynchronous operation.

This is why asyncio can efficiently handle many concurrent I/O operations without creating one thread per request.

---

## Async Task Ownership

Tasks created with:

```python
asyncio.create_task(...)
```

need clear ownership.

A production system should know:

- who owns the task;
- who waits for it;
- who cancels it;
- how exceptions are observed;
- how shutdown cleans it up.

Structured concurrency through mechanisms such as `TaskGroup` can make these relationships clearer.

---

## GIL

In CPython, the Global Interpreter Lock affects execution of Python bytecode across threads.

This means threads generally do not provide straightforward parallel execution of CPU-bound Python bytecode.

However, threads remain highly useful for I/O-bound workloads, and native extensions may release the GIL.

A strong interview answer should avoid saying:

> Python cannot do parallelism.

Python supports parallelism through processes and other mechanisms.

---

## Memory Model

Important concepts include:

- object references;
- reference counting in CPython;
- cyclic garbage collection;
- weak references;
- object identity;
- mutability;
- shallow and deep copying;
- `__slots__`.

Example:

```text
name
 │
 ▼
Python object
 │
 ├── type
 ├── value/state
 └── references to other objects
```

Understanding references explains many apparent memory and mutation problems.

---

## Garbage Collection

CPython primarily uses reference counting and also has cyclic garbage collection.

A critical distinction:

> Garbage collection only reclaims objects that are no longer reachable.

It does not fix memory retention caused by reachable objects stored in:

- global caches;
- long-lived collections;
- session state;
- queues;
- application registries.

---

## Performance Interview Topics

Performance discussions should start with measurement.

Useful tools include:

- `timeit`;
- `cProfile`;
- `tracemalloc`;
- application profilers;
- database query analysis;
- distributed tracing.

Do not optimize based solely on intuition.

A production performance investigation should consider:

```text
Request
  │
  ├── Python CPU
  ├── Database
  ├── Network
  ├── Cache
  ├── Serialization
  └── External services
```

---

## Testing Interview Topics

Testing discussions should cover:

- unit testing;
- integration testing;
- API testing;
- database testing;
- fixtures;
- factories;
- mocking;
- test isolation;
- async testing;
- coverage;
- testing strategy.

A senior answer should explain why:

```text
Unit tests
+
Integration tests
+
API/contract tests
+
Limited E2E tests
```

provide stronger confidence than any single test category.

---

## Backend Python Interview Topics

Backend-oriented Python interviews commonly cover:

- HTTP;
- REST APIs;
- FastAPI;
- Django;
- authentication;
- authorization;
- PostgreSQL;
- Redis;
- Kafka;
- Celery;
- background processing;
- caching;
- transactions;
- connection pools;
- configuration;
- logging;
- observability;
- graceful shutdown.

The expected answer should connect Python language behavior to system behavior.

---

## API Request Lifecycle

A useful mental model:

```text
Client
  │
  ▼
Nginx / Load Balancer
  │
  ▼
FastAPI / Django
  │
  ├── Authentication
  ├── Authorization
  ├── Validation
  │
  ▼
Service Layer
  │
  ├── PostgreSQL
  ├── Redis
  └── Kafka
  │
  ▼
Response
```

Interview questions often test where a responsibility belongs.

For example:

> Should validation happen in the API handler, service layer, or database?

The correct answer depends on the type of invariant.

---

## Database Interview Topics

Know:

- transactions;
- isolation levels;
- connection pooling;
- indexes;
- query complexity;
- N+1 queries;
- constraints;
- optimistic locking;
- pessimistic locking;
- pagination;
- migrations;
- consistency.

Python ORM knowledge should not replace understanding of the underlying database.

---

## Caching

A common backend caching model is cache-aside:

```text
Request
  │
  ▼
Redis
  │
  ├── Hit ──► Return
  │
  └── Miss
        │
        ▼
    PostgreSQL
        │
        ▼
      Redis
        │
        ▼
      Return
```

Interview discussions should include:

- TTL;
- invalidation;
- stale data;
- cache stampede;
- cache penetration;
- distributed locks;
- consistency tradeoffs.

---

## Messaging

Kafka and task queues introduce asynchronous processing.

```text
API
 │
 ▼
Database
 │
 ▼
Event / Task
 │
 ▼
Kafka / Celery
 │
 ▼
Worker
 │
 ▼
External Effect
```

Interview answers should consider:

- retries;
- duplicate delivery;
- idempotency;
- ordering;
- acknowledgment;
- dead-letter queues;
- backpressure.

---

## Idempotency

Idempotency is critical for operations that may be retried.

Examples:

- payments;
- order creation;
- webhook processing;
- message consumers.

The important question is:

> What happens if the same operation is delivered twice?

A strong design ensures duplicate delivery does not create an unintended duplicate side effect.

---

## Data Engineering Interview Topics

Python backend interviews may overlap with data engineering.

Relevant areas include:

- CSV;
- JSON;
- Parquet;
- Pandas;
- NumPy;
- SQL;
- ETL;
- streaming;
- batching;
- memory efficiency;
- data validation.

For large datasets:

```text
Bad:
Load entire dataset
        │
        ▼
Process in memory

Better:
Read batch
   │
   ▼
Transform
   │
   ▼
Write
   │
   ▼
Read next batch
```

Memory constraints should influence the design.

---

## Pandas Interview Topics

Important Pandas concepts include:

- `Series`;
- `DataFrame`;
- indexing;
- filtering;
- joins;
- grouping;
- aggregation;
- missing data;
- datetime handling;
- string operations;
- CSV/JSON/Parquet;
- database integration.

Interview answers should include performance considerations.

For example, avoid unnecessary Python-level row loops when vectorized operations or efficient DataFrame methods are appropriate.

---

## NumPy Interview Topics

Important NumPy concepts include:

- `ndarray`;
- shape;
- dimensions;
- dtype;
- slicing;
- reshaping;
- broadcasting;
- vectorization;
- aggregation;
- memory layout.

A senior-level answer should understand why vectorized operations can outperform Python loops by moving work into optimized native implementations.

---

## AWS-Oriented Python Questions

Python backend interviews may include AWS scenarios involving:

- Lambda;
- ECS;
- EKS;
- S3;
- RDS;
- ElastiCache;
- SQS;
- SNS;
- MSK;
- CloudWatch;
- IAM.

The important skill is connecting application behavior to infrastructure.

Example:

```text
FastAPI
   │
   ▼
ECS / EKS
   │
   ├── RDS PostgreSQL
   ├── ElastiCache Redis
   ├── SQS / Kafka
   └── S3
```

Questions should be answered in terms of:

- scalability;
- availability;
- security;
- cost;
- failure recovery;
- observability.

---

## Coding Problem Strategy

For coding challenges, use a consistent process:

```text
Understand requirements
        │
        ▼
Clarify edge cases
        │
        ▼
Choose data structure
        │
        ▼
Design algorithm
        │
        ▼
State complexity
        │
        ▼
Implement
        │
        ▼
Test boundaries
        │
        ▼
Review tradeoffs
```

Do not start coding before understanding the problem.

---

## Coding Interview Checklist

Before submitting a solution, check:

- [ ] Empty input
- [ ] Single element
- [ ] Duplicate values
- [ ] Negative values where relevant
- [ ] Very large input
- [ ] Already sorted input where relevant
- [ ] Boundary values
- [ ] Invalid input if specified
- [ ] Time complexity
- [ ] Space complexity
- [ ] Mutation/side effects
- [ ] Readability

---

## Debugging Strategy

When given broken Python code:

```text
Observe symptom
      │
      ▼
Reproduce
      │
      ▼
Reduce scope
      │
      ▼
Inspect state
      │
      ▼
Identify invariant violation
      │
      ▼
Fix root cause
      │
      ▼
Add regression test
```

Avoid making multiple unrelated changes before identifying the failure mechanism.

---

## Common Python Interview Traps

### Mutable Default Arguments

```python
def f(value=[]):
    ...
```

The default object is created once at function definition time.

### `is` vs `==`

Identity and equality are different operations.

### Late Binding

Closures capture variables and may observe their later values.

### Shallow Copy

A shallow copy does not recursively duplicate nested mutable objects.

### Generator Exhaustion

Generators are typically single-pass iterators.

### Dictionary Key Requirements

Dictionary keys must be hashable.

### Hash Contract

Equal objects must have equal hashes when used as hashable objects.

### `finally`

`finally` executes during normal exception-handling control flow even when `try` or `except` returns, though control flow can be complicated by a return or exception raised from `finally`.

### Async Blocking

`async def` does not make synchronous blocking operations non-blocking.

### GIL

The GIL does not mean Python cannot perform parallel computation.

### Mocking

Patch the name where the dependency is looked up.

### Assertions

`assert` is not a substitute for runtime validation in production code.

---

## Senior-Level Interview Expectations

At senior level, interviewers often evaluate whether you can connect a Python feature to engineering consequences.

For example:

```text
Question:
"Would you use a generator?"

Weak answer:
"It saves memory."

Stronger answer:
"It provides lazy iteration and can reduce peak memory
for large streams, but it also makes the data single-pass
and can extend the lifetime of underlying resources if those
resources are embedded in the generator's lifecycle."
```

The second answer demonstrates engineering judgment.

---

## Tradeoff-Oriented Answers

Avoid absolute statements.

Instead of:

> Redis is faster than PostgreSQL.

Explain:

> Redis is typically much faster for simple in-memory access, but it introduces another consistency boundary, memory cost, eviction behavior, and operational complexity.

Instead of:

> Asyncio is faster.

Explain:

> Asyncio can efficiently handle many concurrent I/O operations with relatively low per-task overhead, but blocking operations can stall the event loop and CPU-bound work generally requires a different execution strategy.

Interviewers generally value tradeoff awareness.

---

## Production Scenario Questions

For production scenarios, structure the answer around:

```text
Correctness
    │
    ▼
Reliability
    │
    ▼
Scalability
    │
    ▼
Security
    │
    ▼
Observability
    │
    ▼
Cost
    │
    ▼
Disaster Recovery
```

For example, when designing a payment API, discuss:

- idempotency;
- transactions;
- retries;
- duplicate requests;
- authorization;
- auditability;
- timeouts;
- external provider failures;
- observability;
- reconciliation.

---

## System Design Preparation

Python system-design questions should move beyond Python syntax.

A typical flow:

```text
Requirements
     │
     ▼
Capacity estimation
     │
     ▼
API design
     │
     ▼
Data model
     │
     ▼
Storage
     │
     ▼
Caching
     │
     ▼
Messaging
     │
     ▼
Concurrency
     │
     ▼
Failure handling
     │
     ▼
Observability
     │
     ▼
Security
     │
     ▼
Scaling / HA / DR
```

Python is one implementation component inside the larger system.

---

## Interview Answer Framework

For conceptual questions:

```text
Definition
   ↓
How it works
   ↓
Example
   ↓
Tradeoffs
   ↓
Production relevance
```

For coding problems:

```text
Clarify
   ↓
Approach
   ↓
Complexity
   ↓
Implementation
   ↓
Edge cases
```

For backend scenarios:

```text
Requirements
   ↓
Architecture
   ↓
Data flow
   ↓
Failure modes
   ↓
Scalability
   ↓
Security
   ↓
Observability
```

This structure keeps answers organized under interview pressure.

---

## Interview Preparation Checklist

### Python Language

- [ ] Object references
- [ ] Mutability
- [ ] Equality vs identity
- [ ] Function arguments
- [ ] Default arguments
- [ ] Closures
- [ ] Comprehensions
- [ ] Iterators
- [ ] Generators
- [ ] Imports
- [ ] Exceptions
- [ ] Built-in collections
- [ ] Complexity

### OOP

- [ ] Classes
- [ ] Inheritance
- [ ] Composition
- [ ] Polymorphism
- [ ] MRO
- [ ] `super()`
- [ ] Properties
- [ ] Descriptors
- [ ] ABCs
- [ ] Protocols
- [ ] Dependency injection

### Advanced Python

- [ ] Decorators
- [ ] Context managers
- [ ] Asyncio
- [ ] Threads
- [ ] Processes
- [ ] GIL
- [ ] Memory model
- [ ] Garbage collection
- [ ] Profiling
- [ ] Performance optimization

### Backend

- [ ] FastAPI
- [ ] Django
- [ ] REST
- [ ] gRPC
- [ ] PostgreSQL
- [ ] Redis
- [ ] Kafka
- [ ] Celery
- [ ] Transactions
- [ ] Caching
- [ ] Authentication
- [ ] Authorization
- [ ] Idempotency
- [ ] Retries
- [ ] Observability
- [ ] Graceful shutdown

### Testing

- [ ] pytest
- [ ] unittest
- [ ] Fixtures
- [ ] Factories
- [ ] Parametrization
- [ ] Mocking
- [ ] Async tests
- [ ] Integration tests
- [ ] API tests
- [ ] Database tests
- [ ] Isolation
- [ ] Coverage
- [ ] Testing strategy

### Data Engineering

- [ ] SQL
- [ ] Pandas
- [ ] NumPy
- [ ] ETL
- [ ] Batch processing
- [ ] Streaming
- [ ] File formats
- [ ] Memory-efficient processing
- [ ] Data validation

### AWS

- [ ] IAM
- [ ] S3
- [ ] RDS
- [ ] ElastiCache
- [ ] SQS
- [ ] SNS
- [ ] MSK
- [ ] Lambda
- [ ] ECS
- [ ] EKS
- [ ] CloudWatch
- [ ] HA / DR
- [ ] Cost considerations

---

## Final Interview Preparation Model

The complete Python interview preparation path should connect language knowledge to engineering decisions:

```text
                         Python
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Language          Runtime          Tools
          │                │                │
          ▼                ▼                ▼
        OOP             Memory          Testing
        Types          Concurrency       Profiling
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                      Backend Python
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       APIs            Databases         Messaging
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                   System Design
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Scalability       Reliability      Security
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Senior Engineering
```

The strongest preparation combines **Python correctness, algorithmic reasoning, runtime understanding, backend architecture, testing discipline, and production tradeoff analysis**.

## Key Takeaways

- **Interview preparation should connect Python semantics to engineering decisions:** explain not only what Python does, but why its behavior matters for performance, memory, concurrency, testing, and backend architecture.
- **Master fundamentals before optimizing for advanced questions:** object references, mutability, functions, collections, iterators, exceptions, and complexity form the foundation for senior-level reasoning.
- **Backend interviews require system thinking:** APIs, PostgreSQL, Redis, Kafka, Celery, authentication, transactions, retries, idempotency, observability, scalability, and failure recovery should be considered together.
- **Use structured reasoning under pressure:** clarify requirements, identify edge cases, choose an appropriate approach, state complexity, implement, test, and discuss tradeoffs.
- **Senior-level answers are tradeoff-oriented:** avoid absolute claims and explain correctness, reliability, scalability, security, operational complexity, performance, and cost where they materially affect the design.