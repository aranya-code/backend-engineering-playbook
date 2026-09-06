# 09- Async and Await

## Overview

`async` and `await` are Python language constructs used to define and consume asynchronous operations.

They are the syntax layer that makes `asyncio` programs readable and composable:

```python
async def fetch_customer(customer_id: int) -> dict:
    return await client.get_customer(customer_id)
```

The important distinction is:

- `async def` defines a coroutine function.
- Calling an `async def` function creates a coroutine object.
- `await` suspends the current coroutine until an awaitable completes.
- The event loop decides which runnable coroutine executes next.
- `asyncio.create_task()` schedules a coroutine for concurrent execution.

The syntax itself does not make blocking code asynchronous.

```text
async def
   ↓
Coroutine object
   ↓
Task / await
   ↓
Event loop
   ↓
Non-blocking I/O
   ↓
Coroutine resumes
```

Understanding `async` and `await` requires understanding the execution model behind them. In production backend systems, incorrect use can lead to event-loop blocking, excessive concurrency, connection-pool exhaustion, cancellation bugs, and misleading performance expectations.

---

## `async def`

An asynchronous function is declared with `async def`.

```python
async def fetch_customer(customer_id: int) -> dict:
    response = await client.get(
        f"/customers/{customer_id}"
    )
    return response.json()
```

Calling it does not immediately execute the function body.

```python
coroutine = fetch_customer(42)
```

At this point:

```text
fetch_customer(42)
        ↓
Coroutine object
        ↓
Not yet executing
```

Execution starts when the coroutine is:

- awaited
- scheduled as a task
- driven by an event loop

---

## Coroutine Function vs Coroutine Object

These are different concepts.

```python
async def fetch_customer(customer_id: int):
    ...
```

is a **coroutine function**.

This:

```python
coroutine = fetch_customer(42)
```

is a **coroutine object**.

A useful mental model is:

```text
Coroutine function
    ↓ call
Coroutine object
    ↓ await / task
Execution
```

This distinction is important when debugging warnings such as:

```text
RuntimeWarning: coroutine 'fetch_customer' was never awaited
```

---

## What Happens When `async def` Is Called

Consider:

```python
async def calculate() -> int:
    print("running")
    return 42


coroutine = calculate()
```

The body does not execute merely because `calculate()` was called.

Conceptually:

```text
calculate()
    ↓
Create coroutine object
    ↓
Return control to caller
```

The body begins when the coroutine is driven by an event loop.

For example:

```python
result = await calculate()
```

---

## `await`

`await` waits for an awaitable to complete.

```python
async def load_customer(customer_id: int) -> dict:
    customer = await repository.get_customer(
        customer_id
    )
    return customer
```

The key behavior is not simply "wait."

It is:

```text
Current coroutine
       ↓
await operation
       ↓
Suspend current coroutine
       ↓
Event loop can run other tasks
       ↓
Operation becomes ready
       ↓
Resume current coroutine
```

This is cooperative concurrency.

---

## What Can Be Awaited

`await` works with **awaitable objects**.

Common awaitables include:

- coroutine objects
- `asyncio.Task`
- `asyncio.Future`
- objects implementing the asynchronous protocol required by Python

For example:

```python
result = await fetch_customer(42)
```

where `fetch_customer()` returns a coroutine object.

---

## `await` Does Not Mean Blocking the Thread

Compare:

```python
result = await async_operation()
```

with:

```python
result = blocking_operation()
```

The first can suspend the coroutine while allowing the event loop to run other tasks.

The second occupies the executing thread until it returns.

```text
await async I/O
    ↓
Task suspended
    ↓
Event loop continues

blocking call
    ↓
Thread blocked
    ↓
Event loop cannot progress
```

This distinction is fundamental.

---

## Sequential Await

Multiple awaits can still execute sequentially.

```python
async def build_dashboard() -> dict:
    profile = await fetch_profile()
    orders = await fetch_orders()

    return {
        "profile": profile,
        "orders": orders,
    }
```

Execution:

```text
fetch_profile
     ↓
wait
     ↓
fetch_orders
     ↓
wait
     ↓
build response
```

If the two operations are independent, this may leave performance on the table.

---

## Concurrent Await

Independent operations can be scheduled concurrently.

```python
import asyncio


async def build_dashboard() -> dict:
    profile_task = asyncio.create_task(
        fetch_profile()
    )
    orders_task = asyncio.create_task(
        fetch_orders()
    )

    profile = await profile_task
    orders = await orders_task

    return {
        "profile": profile,
        "orders": orders,
    }
```

Now:

```text
              Event Loop
                  │
        ┌─────────┴─────────┐
        ↓                   ↓
   Profile Task        Orders Task
        ↓                   ↓
     await I/O           await I/O
        └─────────┬─────────┘
                  ↓
             Build response
```

The concurrency comes from task scheduling, not from `await` alone.

---

## `await` vs `create_task()`

This distinction is important:

```python
result = await operation()
```

means:

```text
Run this coroutine as part of the current coroutine's flow.
```

Whereas:

```python
task = asyncio.create_task(operation())
```

means:

```text
Schedule this coroutine independently on the current event loop.
```

Then:

```python
result = await task
```

collects the result.

---

## `await` vs `asyncio.gather()`

For simple fan-out/fan-in operations:

```python
import asyncio


async def load_dashboard() -> dict:
    profile, orders = await asyncio.gather(
        fetch_profile(),
        fetch_orders(),
    )

    return {
        "profile": profile,
        "orders": orders,
    }
```

The operations are scheduled concurrently.

Results preserve the input ordering:

```python
results = await asyncio.gather(
    operation_a(),
    operation_b(),
)
```

means:

```text
results[0] → operation_a()
results[1] → operation_b()
```

even if `operation_b()` finishes first.

---

## `asyncio.gather()` vs Explicit Tasks

Both can express concurrency:

```python
await asyncio.gather(
    fetch_profile(),
    fetch_orders(),
)
```

and:

```python
profile_task = asyncio.create_task(fetch_profile())
orders_task = asyncio.create_task(fetch_orders())

profile = await profile_task
orders = await orders_task
```

Use `gather()` when the operations are straightforward concurrent work.

Use explicit tasks when you need:

- individual task references
- cancellation
- status inspection
- different sequencing
- explicit task ownership

---

## `TaskGroup`

Modern Python provides structured concurrency through `asyncio.TaskGroup`.

```python
import asyncio


async def load_dashboard() -> dict:
    async with asyncio.TaskGroup() as group:
        profile_task = group.create_task(
            fetch_profile()
        )
        orders_task = group.create_task(
            fetch_orders()
        )

    return {
        "profile": profile_task.result(),
        "orders": orders_task.result(),
    }
```

A `TaskGroup` makes task lifetime explicit:

```text
TaskGroup scope
├── Profile task
└── Orders task

Scope exits
    ↓
Children completed or coordinated cancellation occurs
```

This is generally preferable for structured application-level concurrency where child tasks belong to one logical operation.

---

## `asyncio.run()`

A normal synchronous entry point can start the asynchronous application:

```python
import asyncio


async def main() -> None:
    customer = await fetch_customer(42)
    print(customer)


if __name__ == "__main__":
    asyncio.run(main())
```

`asyncio.run()` manages the event loop for the top-level coroutine.

It should normally be used at the boundary between synchronous application startup and asynchronous execution.

---

## Running `asyncio.run()` Inside Async Code

Do not do this:

```python
async def service():
    asyncio.run(other_operation())
```

An event loop is already running in this context.

Use:

```python
async def service():
    await other_operation()
```

The rule is:

```text
Synchronous boundary
    ↓
asyncio.run()

Inside async code
    ↓
await
```

---

## Event Loop Relationship

`async` and `await` do not execute tasks by themselves.

The event loop drives them.

```text
async def
    ↓
coroutine
    ↓
Task
    ↓
Event loop
    ↓
await
    ↓
I/O readiness
    ↓
resume coroutine
```

The event loop is responsible for advancing suspended asynchronous operations when their awaited dependencies become ready.

---

## Coroutine State

A coroutine can conceptually be:

```text
Created
   ↓
Suspended at await
   ↓
Runnable
   ↓
Running
   ↓
Suspended again
   ↓
Completed
```

It may also terminate because of:

```text
Exception
Cancellation
```

This lifecycle explains why asynchronous code can have many suspended operations without requiring one operating-system thread for every operation.

---

## Suspension Points

Every `await` is a potential suspension point.

```python
async def process() -> None:
    first = await operation_a()
    second = await operation_b()
```

The coroutine can suspend at:

```text
await operation_a()
```

and later:

```text
await operation_b()
```

This has important concurrency implications.

If shared state is accessed before and after an await, another task may execute between those points.

---

## Race Conditions in Async Code

Asyncio does not eliminate race conditions.

Consider:

```python
balance = 100


async def withdraw(amount: int) -> None:
    global balance

    current = balance

    await asyncio.sleep(0)

    balance = current - amount
```

Two tasks can interleave:

```text
Task A → read 100
Task B → read 100
Task A → write 50
Task B → write 20
```

One update is lost.

The absence of preemptive thread scheduling does not make shared mutable state automatically safe.

---

## Asyncio Locks

Protect shared state when necessary:

```python
import asyncio


balance = 100
balance_lock = asyncio.Lock()


async def withdraw(amount: int) -> None:
    global balance

    async with balance_lock:
        balance -= amount
```

The lock is designed for tasks running within the same event loop.

It does not coordinate across:

- processes
- containers
- Kubernetes pods
- separate machines

Distributed state requires a distributed coordination mechanism or, preferably, a transactional data store.

---

## Asyncio and Transactions

Application-level async locks are not substitutes for database transactions.

For financial or consistency-sensitive state:

```text
Application
    ↓
PostgreSQL transaction
    ↓
Row-level locking / constraints
    ↓
Commit
```

Use database guarantees for shared persistent state.

---

## Asyncio Is Cooperative

A coroutine must reach an appropriate suspension point before another task gets a chance to run.

This code can block the event loop:

```python
async def process():
    for _ in range(10_000_000):
        expensive_python_operation()
```

Even though the function is declared `async`, it contains no useful suspension point.

```text
Event loop
    ↓
process()
    ↓
CPU-heavy loop
    ↓
Other tasks wait
```

---

## Blocking Calls Inside `async def`

This is one of the most common mistakes:

```python
import requests


async def fetch():
    response = requests.get(
        "https://example.com"
    )

    return response.json()
```

The function is syntactically asynchronous but operationally blocking.

The `requests` call occupies the event-loop thread.

---

## Correct Async HTTP

Use an async-compatible client:

```python
async def fetch():
    response = await http_client.get(
        "https://example.com"
    )

    return response.json()
```

The actual client must implement non-blocking asynchronous I/O.

Simply adding `await` around a blocking library does not make the library asynchronous.

---

## Offloading Blocking Work

If a synchronous dependency cannot be replaced immediately:

```python
import asyncio


async def fetch():
    return await asyncio.to_thread(
        synchronous_client.get,
        "https://example.com",
    )
```

This moves the blocking operation to a thread.

Conceptually:

```text
Event Loop
    ↓
await to_thread()
    ↓
Worker Thread
    ↓
Blocking I/O
```

This is useful for integrating legacy synchronous libraries.

---

## CPU-Bound Work

Do not put expensive CPU work directly in the event loop:

```python
async def calculate():
    return expensive_cpu_computation()
```

For CPU-heavy Python code, use process-based execution:

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor


async def calculate(
    executor: ProcessPoolExecutor,
) -> int:
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
        executor,
        expensive_cpu_computation,
    )
```

This combines async request handling with process-based CPU parallelism.

---

## `asyncio.to_thread()` vs Process Pool

| Workload | Recommended approach |
|---|---|
| Async HTTP | Direct `await` |
| Async database | Direct `await` |
| Blocking HTTP library | `asyncio.to_thread()` |
| Blocking file/library operation | Often `asyncio.to_thread()` |
| CPU-heavy Python | Process pool |
| Durable background job | Celery / SQS / Kafka |
| High-volume I/O | Native asyncio |

The key question is what resource the operation spends most of its time waiting for.

---

## Async Context Managers

Asynchronous resources can use:

```python
async with resource:
    await operation()
```

For example:

```python
async with http_client:
    response = await http_client.get(url)
```

This provides asynchronous setup and cleanup.

Common applications include:

- HTTP clients
- database transactions
- async locks
- connection resources
- streaming resources

---

## Async Iteration

Use `async for` when values arrive asynchronously.

```python
async for event in event_stream:
    await process_event(event)
```

This is useful for:

- WebSockets
- streaming HTTP
- asynchronous database cursors
- event consumers
- long-running streams

---

## Async Generators

An async generator combines lazy production with asynchronous waiting:

```python
async def stream_events():
    while True:
        event = await read_event()
        yield event
```

Consumer:

```python
async for event in stream_events():
    await process_event(event)
```

This avoids loading an entire stream into memory.

---

## Async Comprehensions

Python supports asynchronous comprehensions:

```python
results = [
    transform(event)
    async for event in event_stream()
]
```

Use them when the resulting collection is intentionally bounded.

For large or unbounded streams, materializing all values into a list defeats streaming and can exhaust memory.

---

## Async With and Async For

The asynchronous syntax family is:

| Syntax | Purpose |
|---|---|
| `async def` | Define coroutine function |
| `await` | Await an awaitable |
| `async with` | Manage asynchronous resources |
| `async for` | Iterate asynchronously |
| `asyncio.create_task()` | Schedule coroutine concurrently |
| `TaskGroup` | Structure related concurrent tasks |

These constructs form the core language-level interface to asynchronous programming.

---

## Async Properties and Methods

An asynchronous method can be defined normally:

```python
class CustomerRepository:
    async def get(
        self,
        customer_id: int,
    ) -> dict:
        return await self.client.fetch(
            customer_id
        )
```

Callers must await it:

```python
customer = await repository.get(42)
```

Do not expose asynchronous APIs unless their underlying work actually benefits from asynchronous execution.

---

## Type Hints

Modern type annotations can describe asynchronous callables.

For example:

```python
from collections.abc import Awaitable, Callable


Handler = Callable[[dict], Awaitable[dict]]
```

This communicates:

```text
Callable
   ↓
accepts dict
   ↓
returns Awaitable[dict]
```

This is useful for middleware, dependency injection, callbacks, and framework abstractions.

---

## Awaitable Return Types

Compare:

```python
def get_customer() -> dict:
    ...
```

with:

```python
async def get_customer() -> dict:
    ...
```

The latter is a coroutine function whose invocation produces an awaitable coroutine object.

At API boundaries, the type signature should communicate whether callers must await the operation.

---

## Async API Design

Prefer clear async boundaries:

```python
class CustomerService:
    async def get_customer(
        self,
        customer_id: int,
    ) -> Customer:
        return await self.repository.get(
            customer_id
        )
```

Avoid mixing synchronous and asynchronous behavior unpredictably.

For example, a method named `get_customer()` that sometimes blocks and sometimes awaits depending on configuration creates difficult operational behavior.

---

## FastAPI

An async FastAPI endpoint:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/customers/{customer_id}")
async def get_customer(
    customer_id: int,
) -> dict:
    return await customer_service.get_customer(
        customer_id
    )
```

The request handler can suspend while waiting for:

- PostgreSQL
- Redis
- HTTP services
- gRPC services

The event loop can process other requests during those waits.

---

## FastAPI Request Lifecycle

```mermaid
sequenceDiagram
    participant Client
    participant Server as FastAPI/Uvicorn
    participant Loop as Event Loop
    participant DB as PostgreSQL

    Client->>Server: HTTP request
    Server->>Loop: Schedule endpoint
    Loop->>DB: Async query
    Loop->>Loop: Suspend endpoint
    Note over Loop: Handle other requests
    DB-->>Loop: Query result
    Loop->>Loop: Resume endpoint
    Loop-->>Server: Response data
    Server-->>Client: HTTP response
```

The benefit depends on the database driver and surrounding stack being genuinely asynchronous.

---

## Django

Django supports asynchronous views:

```python
async def customer_view(request):
    customer = await load_customer()
    return JsonResponse(customer)
```

However, individual framework operations and dependencies must be evaluated for their actual async behavior.

Do not assume that every Django API becomes non-blocking merely because the view is `async def`.

---

## REST API Fan-Out

A service aggregator is a strong use case:

```text
Client
  ↓
API Gateway / FastAPI
  ↓
Async service
  ├── Profile Service
  ├── Orders Service
  └── Billing Service
```

The service can issue independent requests concurrently:

```python
profile, orders, billing = await asyncio.gather(
    profile_client.get(customer_id),
    order_client.list(customer_id),
    billing_client.get(customer_id),
)
```

This can reduce total latency from approximately:

```text
T_profile + T_orders + T_billing
```

to approximately:

```text
max(T_profile, T_orders, T_billing)
```

plus application overhead.

---

## Timeouts

Async operations should have explicit timeouts.

```python
async with asyncio.timeout(2.0):
    customer = await customer_client.get(
        customer_id
    )
```

A timeout should reflect the service's latency budget and dependency behavior.

Avoid allowing requests to remain indefinitely suspended.

---

## Timeout Hierarchy

A production request may have multiple timeout layers:

```text
Client timeout
    ↓
Load balancer timeout
    ↓
Application request timeout
    ↓
Dependency timeout
    ↓
Database timeout
```

These should be designed coherently.

An inner dependency timeout should generally leave enough budget for the application to produce a response or fallback.

---

## Cancellation

Async operations are cancellable.

```python
task = asyncio.create_task(
    process_request()
)

task.cancel()
```

Cancellation is delivered to the task and should normally propagate through the coroutine stack.

---

## Handling `CancelledError`

Use cleanup and re-raise:

```python
async def worker() -> None:
    try:
        await process()
    except asyncio.CancelledError:
        await cleanup()
        raise
```

Do not casually convert cancellation into a normal success or failure state.

Cancellation is often part of:

- request disconnects
- timeout handling
- application shutdown
- task-group failure

---

## Cancellation-Safe Resource Handling

Prefer:

```python
async def operation():
    connection = await acquire_connection()

    try:
        await do_work(connection)
    finally:
        await connection.close()
```

Better still, use the resource's async context manager:

```python
async with acquire_connection() as connection:
    await do_work(connection)
```

This makes cleanup behavior more explicit.

---

## `asyncio.timeout()`

Modern Python provides:

```python
async with asyncio.timeout(5):
    await operation()
```

This establishes a timeout scope.

For older code or specific compatibility requirements, `asyncio.wait_for()` may also be used:

```python
await asyncio.wait_for(
    operation(),
    timeout=5,
)
```

The two APIs have different semantics and should not be treated as interchangeable in every advanced cancellation scenario.

---

## Asyncio Semaphore

Use a semaphore to bound concurrent operations:

```python
import asyncio


partner_limit = asyncio.Semaphore(20)


async def call_partner(request: dict) -> dict:
    async with partner_limit:
        return await partner_client.send(request)
```

Without a limit:

```text
5000 tasks
   ↓
5000 outbound requests
   ↓
Partner overloaded
```

With a semaphore:

```text
5000 tasks
   ↓
20 concurrent calls
   ↓
Controlled dependency pressure
```

---

## Asyncio Queue

A bounded queue can provide backpressure:

```python
queue: asyncio.Queue[dict] = asyncio.Queue(
    maxsize=500,
)
```

Producer:

```python
await queue.put(event)
```

Consumer:

```python
event = await queue.get()

try:
    await process(event)
finally:
    queue.task_done()
```

A bounded queue prevents producers from accumulating unlimited in-memory work.

---

## Asyncio and Database Pools

A large number of async tasks does not mean a large number of database connections.

A good architecture may look like:

```text
10,000 concurrent requests
          ↓
Async application
          ↓
Database connection pool
          ↓
100 PostgreSQL connections
```

Tasks wait asynchronously for connection availability.

This separates application concurrency from database connection capacity.

---

## Asyncio and Redis

Use an asynchronous Redis client when the application is asynchronous:

```python
value = await redis.get(
    f"customer:{customer_id}"
)
```

The client should be application-scoped where appropriate so connections can be reused.

---

## Asyncio and HTTP Connection Pools

A long-lived async HTTP client should generally be reused.

```text
Application
    ↓
Async HTTP Client
    ↓
Connection Pool
    ├── Connection 1
    ├── Connection 2
    └── Connection N
```

Creating a new client for every request can cause unnecessary connection establishment and TLS overhead.

---

## Asyncio and gRPC

Async gRPC clients can fit naturally into an async service:

```python
response = await grpc_client.get_customer(
    customer_id
)
```

This allows outbound RPC operations to overlap while the event loop handles other tasks.

---

## Asyncio and Kafka

An asynchronous Kafka consumer can process records without blocking the event loop:

```text
Kafka
  ↓
Async Consumer
  ↓
await message
  ↓
Process
  ↓
Commit offset
```

However, Kafka's delivery and offset semantics remain independent of asyncio.

Async execution does not automatically provide:

- durability
- exactly-once business semantics
- reliable retries
- distributed coordination

Those require system-level design.

---

## Asyncio and Celery

An in-process coroutine is not a replacement for durable task infrastructure.

```text
asyncio.create_task()
→ process-local, ephemeral

Celery
→ distributed, durable background execution model
```

If a task must survive:

```text
pod restart
process crash
deployment
machine failure
```

store the work in durable infrastructure.

---

## Background Tasks

This pattern:

```python
asyncio.create_task(send_email())
```

can be appropriate for truly ephemeral work.

It is dangerous for critical business operations because the process may terminate before the task completes.

For important work:

```text
HTTP Request
   ↓
Durable Queue
   ↓
Worker
   ↓
Email Service
```

Use Celery, SQS, Kafka, or another appropriate durable mechanism.

---

## Asyncio and Nginx

A common production stack is:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
Uvicorn
  ↓
FastAPI
  ↓
Event Loop
  ↓
Async dependencies
```

Nginx handles connection and proxy concerns while the application event loop handles coroutine scheduling.

---

## Asyncio and Kubernetes

Each worker process has its own event loop.

```text
Kubernetes
 ├── Pod 1
 │    ├── Process
 │    │    └── Event Loop
 │    └── ...
 ├── Pod 2
 │    └── Event Loop
 └── Pod 3
      └── Event Loop
```

Horizontal scaling increases total asynchronous capacity.

But downstream systems must also support the resulting concurrency.

---

## Concurrency Multiplication

Suppose:

```text
6 pods
×
2 Uvicorn workers
×
1000 concurrent requests
```

Potential application-level concurrency can become substantial.

If each request performs:

```text
3 outbound service calls
```

the downstream request pressure can multiply again.

Always calculate concurrency across the entire topology.

---

## Event-Loop Blocking

Monitor for operations that take unusually long on the event-loop thread.

Potential causes include:

- CPU-heavy Python
- synchronous HTTP clients
- blocking database drivers
- filesystem operations
- expensive serialization
- large JSON transformations
- synchronous logging handlers

One blocking operation can affect unrelated requests sharing the same event loop.

---

## Serialization

Async does not eliminate serialization costs.

For example:

```python
payload = huge_python_object
json_payload = json.dumps(payload)
```

If serialization is CPU-intensive, it executes synchronously unless explicitly offloaded.

Large response serialization can therefore become an event-loop bottleneck.

---

## Memory

Async tasks are generally lighter than operating-system threads, but thousands of tasks still consume memory.

Each task may retain:

- coroutine state
- local variables
- awaited objects
- request data
- buffers
- exceptions
- response objects

Therefore:

```text
High concurrency
≠
Unlimited concurrency
```

Bound concurrency based on memory and downstream capacity.

---

## File Descriptors

Async networking still consumes operating-system file descriptors.

High connection counts require appropriate:

- container limits
- operating-system limits
- HTTP connection limits
- database pool limits

An application can fail despite having available CPU if it exhausts file descriptors.

---

## Retry Storms

Async concurrency can amplify failures.

```text
Dependency outage
      ↓
1000 requests fail
      ↓
1000 retries
      ↓
Dependency receives more traffic
      ↓
Failure worsens
```

Use:

- bounded retries
- exponential backoff
- jitter
- concurrency limits
- circuit breakers where appropriate
- idempotency

---

## Security

Async applications can be particularly susceptible to resource-exhaustion attacks.

Examples:

- opening many concurrent connections
- triggering expensive fan-out
- abusing streaming endpoints
- causing cache stampedes
- forcing large request bodies
- creating many expensive tasks

Mitigate with:

- authentication
- authorization
- rate limiting
- request-size limits
- concurrency limits
- timeouts
- per-tenant quotas
- bounded queues

---

## Common Mistakes

### Calling a Coroutine Without Awaiting It

Bad:

```python
customer = fetch_customer(42)
```

If the result is never awaited or scheduled, the coroutine does not execute correctly.

Correct:

```python
customer = await fetch_customer(42)
```

### Assuming `await` Means Parallelism

This:

```python
await operation_a()
await operation_b()
```

is sequential.

Use task scheduling or `gather()` when concurrency is required.

### Blocking Inside `async def`

Bad:

```python
time.sleep(2)
```

Correct:

```python
await asyncio.sleep(2)
```

for an asynchronous delay.

### Using Synchronous HTTP Clients

Bad:

```python
requests.get(url)
```

inside the event loop.

Use an async HTTP client or explicitly offload the blocking call.

### CPU Work on the Event Loop

CPU-heavy functions can block every task sharing the loop.

### Creating Unlimited Tasks

Bad:

```python
for item in items:
    asyncio.create_task(process(item))
```

for an unbounded or very large collection.

Use bounded concurrency.

### Swallowing Cancellation

Bad:

```python
except asyncio.CancelledError:
    return
```

This can break shutdown and cancellation semantics.

### Using Asyncio Locks for Distributed State

An `asyncio.Lock` only coordinates tasks within the appropriate local process/event-loop context.

It cannot coordinate Kubernetes replicas.

---

## Production Pitfalls

### Async API, Blocking Implementation

The most dangerous misconception is:

```text
async def
    ≠
non-blocking implementation
```

Every important dependency must be examined.

### Excessive Fan-Out

A single incoming request may trigger dozens of downstream requests.

Bound concurrency and define a maximum fan-out.

### Connection Pool Exhaustion

Thousands of tasks may compete for a small database or HTTP connection pool.

### Event-Loop Starvation

CPU-heavy code can cause high latency across unrelated requests.

### Memory Amplification

Each concurrent request retains its own state.

### Retry Amplification

Highly concurrent retries can turn dependency failures into cascading outages.

### Detached Tasks

Unowned background tasks can survive beyond request scope and fail without proper observation.

---

## Performance Engineering

Measure:

```text
Throughput
p50 latency
p95 latency
p99 latency
Event-loop latency
CPU utilization
Memory
Connection-pool utilization
Queue depth
Dependency latency
Error rate
```

Do not evaluate asyncio solely by requests per second.

An async service can achieve high throughput while producing unacceptable p99 latency if the event loop is periodically blocked.

---

## Benchmarking

Compare realistic implementations:

```text
Sequential synchronous
Async sequential
Async concurrent
Thread-based
Process-based
```

Measure the actual workload.

For I/O-heavy systems, concurrency often improves throughput.

For CPU-heavy systems, asyncio alone generally does not.

---

## Async Testing

Async functions should be tested using an async-capable test environment.

Example:

```python
import pytest


@pytest.mark.asyncio
async def test_get_customer():
    customer = await service.get_customer(42)

    assert customer["id"] == 42
```

Test:

- successful awaits
- dependency failures
- timeouts
- cancellations
- concurrent execution
- resource cleanup
- backpressure
- retry behavior

---

## Deterministic Concurrency Tests

Avoid arbitrary sleeps:

```python
await asyncio.sleep(0.1)
```

as a synchronization mechanism.

Prefer explicit primitives:

```python
event = asyncio.Event()

await event.wait()
```

This makes tests less sensitive to machine speed and scheduler timing.

---

## Observability

Production async systems should expose:

```text
Request metrics
Task metrics
Event-loop metrics
Connection-pool metrics
Queue metrics
Dependency metrics
Timeout metrics
Cancellation metrics
Retry metrics
```

Useful application-level measurements include:

- active tasks
- task duration
- queue wait time
- dependency latency
- pool wait time
- event-loop lag

---

## Graceful Shutdown

A robust shutdown flow is:

```text
SIGTERM
   ↓
Stop accepting new requests
   ↓
Stop creating new work
   ↓
Cancel appropriate tasks
   ↓
Allow bounded cleanup
   ↓
Close clients and pools
   ↓
Exit process
```

Kubernetes termination grace periods should be long enough for the application's shutdown behavior.

---

## Resource Lifecycle

Prefer application-scoped ownership for expensive clients.

```text
Application Startup
    ↓
Create HTTP client
Create DB pool
Create Redis client
    ↓
Serve requests
    ↓
Application Shutdown
    ↓
Close HTTP client
Close DB pool
Close Redis client
```

Avoid repeatedly constructing expensive resources inside request handlers.

---

## Decision Framework

Use the following reasoning:

```text
Is the operation I/O-bound?
        │
        ├── No → ProcessPool / optimized native code
        │
        └── Yes
             ↓
Does the library support async I/O?
             │
             ├── Yes → await directly
             │
             └── No
                  ↓
             Can it be safely offloaded?
                  │
                  └── Yes → asyncio.to_thread()
```

Then evaluate:

```text
Concurrency limit
Connection pool
Timeout
Retry policy
Cancellation
Backpressure
Observability
Failure semantics
```

---

## Practical Backend Pattern

A production request handler might look like:

```python
import asyncio


partner_limit = asyncio.Semaphore(20)


async def build_customer_dashboard(
    customer_id: int,
) -> dict:
    async with asyncio.TaskGroup() as group:
        profile_task = group.create_task(
            customer_service.get_profile(customer_id)
        )
        orders_task = group.create_task(
            order_service.list_orders(customer_id)
        )

        async def load_recommendations():
            async with partner_limit:
                return await recommendation_service.get(
                    customer_id
                )

        recommendations_task = group.create_task(
            load_recommendations()
        )

    return {
        "profile": profile_task.result(),
        "orders": orders_task.result(),
        "recommendations": recommendations_task.result(),
    }
```

This combines:

- structured concurrency
- async I/O
- bounded dependency concurrency
- explicit task ownership
- predictable result collection

---

## Asyncio Execution Model

The complete mental model is:

```text
                    Application
                         │
                    async def
                         │
                    Coroutine
                         │
                  create_task()
                         │
                       Task
                         │
                    Event Loop
                         │
               ┌─────────┴─────────┐
               ↓                   ↓
          Task A awaits        Task B runs
               │                   │
           I/O pending          await I/O
               │                   │
               └─────────┬─────────┘
                         ↓
                  I/O becomes ready
                         │
                         ↓
                    Task resumes
```

The event loop is productive because suspended tasks give other ready tasks opportunities to execute.

---

## Production Checklist

- [ ] `async def` is used only where asynchronous execution provides value.
- [ ] Every coroutine is either awaited or intentionally scheduled.
- [ ] Blocking libraries are not called directly on the event loop.
- [ ] CPU-heavy work is moved out of the event loop.
- [ ] Async-compatible HTTP, database, Redis, and gRPC clients are used where appropriate.
- [ ] HTTP and database clients use connection pooling.
- [ ] Concurrency is bounded with semaphores, queues, pools, or framework controls.
- [ ] Request fan-out is explicitly limited.
- [ ] Timeouts exist at dependency and request levels.
- [ ] Retry policies are bounded and use backoff and jitter.
- [ ] Cancellation propagates correctly.
- [ ] `CancelledError` is not accidentally swallowed.
- [ ] Resources are cleaned up during cancellation and shutdown.
- [ ] `TaskGroup` is considered for structured concurrent work.
- [ ] Detached background tasks are not used for durable business operations.
- [ ] Durable jobs use appropriate infrastructure such as Celery, SQS, or Kafka.
- [ ] Database transactions provide consistency guarantees rather than local asyncio locks.
- [ ] Queue sizes and connection pools provide backpressure.
- [ ] Event-loop latency is monitored.
- [ ] Memory usage under high concurrency has been measured.
- [ ] File-descriptor limits have been evaluated.
- [ ] Kubernetes worker and replica multiplication has been considered.
- [ ] Graceful shutdown has been tested.
- [ ] Async tests avoid arbitrary timing assumptions.
- [ ] Load tests measure p95/p99 latency and downstream saturation.
- [ ] Security controls account for high-concurrency resource exhaustion.
- [ ] Performance decisions are based on benchmarks rather than the presence of `async` syntax alone.

## Key Takeaways

- **`async def` defines coroutine functions and `await` provides suspension points:** the event loop can run other tasks while the current coroutine waits for an asynchronous operation.
- **`await` does not automatically create concurrency:** sequential awaits remain sequential; use task scheduling, `gather()`, or `TaskGroup` when independent operations should execute concurrently.
- **Asynchronous syntax does not make blocking code non-blocking:** synchronous HTTP, database, filesystem, CPU-heavy, and serialization operations can still block the event loop and must be replaced or explicitly offloaded.
- **Production asyncio requires bounded concurrency and lifecycle control:** connection pools, semaphores, queues, timeouts, cancellation, retries, backpressure, and graceful shutdown are part of the design.
- **Asyncio provides process-local I/O concurrency, not CPU parallelism or durable execution:** use process-based execution for CPU-heavy Python workloads and durable queues or worker systems for business-critical background work.