# 03- GIL

## Overview

The **Global Interpreter Lock (GIL)** is a central implementation detail of CPython that affects how Python threads execute Python code.

The GIL matters because it influences the relationship between:

- threads
- CPU-bound workloads
- I/O-bound workloads
- multi-core execution
- native extensions
- `asyncio`
- multiprocessing
- web-server workers
- application scalability

The most important distinction is:

```text
Traditional GIL-enabled CPython

Multiple threads
      ↓
One interpreter
      ↓
One thread executes Python bytecode at a time
```

This does **not** mean Python cannot perform concurrent I/O or use multiple CPU cores.

Processes can execute independently:

```text
Process A → Core 1
Process B → Core 2
Process C → Core 3
Process D → Core 4
```

Modern CPython also supports **free-threaded builds** that can run without the GIL. Therefore, the GIL should be understood as an implementation characteristic of a particular CPython build rather than a universal definition of Python.

---

## What Is the GIL?

The GIL is a lock associated with CPython's interpreter execution model.

In a traditional GIL-enabled CPython interpreter, the GIL ensures that only one thread at a time executes Python bytecode within that interpreter.

Conceptually:

```text
                 CPython Process
                       │
                ┌──────┴──────┐
                │ Interpreter │
                └──────┬──────┘
                       │
                     GIL
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       Thread A     Thread B     Thread C
          │
       executing
       Python code
```

Other threads may exist and may be waiting for the GIL or blocked on I/O.

The GIL is not a Python language rule. It is an implementation mechanism of CPython.

---

## Why Does CPython Have a GIL?

The GIL historically simplified the implementation of CPython's runtime and its memory-management model.

Python objects are managed by the interpreter, including reference-counted object lifetimes and other interpreter-internal state.

A coarse-grained lock historically reduced the amount of fine-grained synchronization required throughout the runtime and helped maintain compatibility with a large ecosystem of native extensions.

The tradeoff is that traditional GIL-enabled CPython cannot execute Python bytecode simultaneously on multiple threads within one interpreter.

---

## The Core Problem

Suppose a machine has:

```text
CPU cores = 8
```

and a Python process has:

```text
Threads = 8
```

Under the traditional GIL model, pure Python bytecode does not execute simultaneously across all eight cores within that interpreter.

Conceptually:

```text
Core 1 → Thread A → Python bytecode
Core 2 → Thread B → waiting
Core 3 → Thread C → waiting
Core 4 → Thread D → waiting
...
```

The operating system can schedule threads across cores, but the GIL prevents multiple threads from simultaneously executing Python bytecode in that interpreter.

This is why adding threads is generally not an effective way to parallelize CPU-bound pure Python code.

---

## The GIL Does Not Mean "Only One Thread"

A process can still contain many threads.

```text
Python Process
├── Main Thread
├── Worker Thread A
├── Worker Thread B
├── Worker Thread C
└── Worker Thread D
```

The restriction is on simultaneous execution of Python bytecode under the traditional GIL model, not on the existence of threads.

Threads can still:

- wait for I/O
- perform network operations
- execute native code
- coordinate work
- overlap blocking operations

This distinction is critical for backend engineering.

---

## GIL and I/O-Bound Work

I/O-bound operations spend significant time waiting for external resources.

Examples include:

- PostgreSQL
- Redis
- HTTP APIs
- filesystem operations
- sockets
- DNS
- cloud services

During suitable blocking operations, the interpreter can release the GIL so another thread can execute.

Conceptually:

```text
Thread A
   │
   ├── Python code
   │
   ├── Network I/O
   │
   └── waiting
          │
          └──── GIL available
                    ↓
                 Thread B
                    │
                    └── Python code
```

Therefore, threads can provide substantial throughput improvements for I/O-bound workloads.

---

## Example: I/O-Bound Threading

```python
from concurrent.futures import ThreadPoolExecutor


def fetch_customer(customer_id: int) -> dict:
    return customer_client.get(customer_id)


def load_customers(customer_ids: list[int]) -> list[dict]:
    with ThreadPoolExecutor(max_workers=16) as executor:
        return list(
            executor.map(fetch_customer, customer_ids)
        )
```

If each request spends most of its time waiting on a network service, multiple threads can overlap those waits.

The performance benefit does not come from multiple threads executing Python bytecode simultaneously.

It comes from overlapping waiting periods.

---

## GIL and CPU-Bound Work

CPU-bound work spends most of its time executing computation.

Examples include:

- complex transformations
- pure Python numerical algorithms
- compression implemented in Python
- expensive parsing
- cryptographic calculations implemented in Python
- computational simulations

With traditional GIL-enabled CPython:

```text
Thread A → CPU-heavy Python code
Thread B → waiting for GIL
Thread C → waiting for GIL
Thread D → waiting for GIL
```

Adding more threads may provide little or no CPU-parallel speedup and can sometimes make performance worse because of scheduling and GIL contention.

---

## Why Threads Can Be Slower

Consider:

```python
import threading


def calculate() -> int:
    total = 0

    for value in range(10_000_000):
        total += value

    return total
```

Running several copies concurrently with threads does not necessarily reduce elapsed time.

The threads contend for the GIL:

```text
Thread A ── Python bytecode ──┐
                              │
Thread B ── waiting ──────────┤
                              │
Thread C ── waiting ──────────┤
                              ↓
                         GIL scheduling
```

Additional overhead can include:

- thread scheduling
- context switching
- synchronization
- cache effects
- GIL handoff

For CPU-bound pure Python work, processes are generally a better fit under GIL-enabled execution.

---

## Processes Avoid the Single-Interpreter GIL Bottleneck

Separate processes have separate interpreters.

```text
Process A
├── Interpreter
└── GIL

Process B
├── Interpreter
└── GIL

Process C
├── Interpreter
└── GIL

Process D
├── Interpreter
└── GIL
```

Each process can execute Python code independently.

On a multi-core machine:

```text
Process A → Core 1
Process B → Core 2
Process C → Core 3
Process D → Core 4
```

This enables parallel execution of CPU-bound Python workloads.

---

## Process-Based Parallelism

```python
from concurrent.futures import ProcessPoolExecutor


def transform(value: int) -> int:
    return expensive_cpu_operation(value)


def process_values(values: list[int]) -> list[int]:
    with ProcessPoolExecutor(max_workers=4) as executor:
        return list(executor.map(transform, values))
```

Each worker process has its own interpreter.

The tradeoff is additional:

- memory
- process startup
- serialization
- IPC
- lifecycle management

---

## GIL vs `asyncio`

`asyncio` is not a mechanism for bypassing the GIL.

Its primary benefit is cooperative concurrency for non-blocking I/O.

```text
Event Loop
   │
   ├── Task A → await network I/O
   ├── Task B → await database I/O
   └── Task C → await HTTP I/O
```

Only one task executes Python code at a time on the event loop thread, but tasks can make progress while other tasks are waiting.

Therefore:

```text
I/O-bound workload
→ asyncio can provide high concurrency
```

while:

```text
CPU-bound Python workload
→ asyncio does not create CPU parallelism
```

A CPU-heavy function executed directly in an event loop can block all other tasks.

---

## GIL vs Threads vs Processes

| Workload | Threads | Processes | `asyncio` |
|---|---:|---:|---:|
| HTTP I/O | Excellent | Good | Excellent |
| PostgreSQL I/O | Good | Good | Excellent with async driver |
| Redis I/O | Good | Good | Excellent with async client |
| Filesystem I/O | Good | Good | Depends on API |
| Pure Python CPU work | Poor for parallelism under traditional GIL | Excellent | Poor |
| Native code releasing GIL | Potentially excellent | Excellent | Depends on integration |
| Shared memory | Easy | Explicit IPC required | Shared event-loop state |
| Startup overhead | Low | Higher | Very low |
| Multi-core Python execution | Limited under traditional GIL | Yes | No |

---

## The GIL and Native Extensions

The GIL primarily constrains execution of Python bytecode.

Native extensions implemented in languages such as C or C++ can release the GIL while performing suitable operations.

Conceptually:

```text
Python Thread
     ↓
Native extension
     ↓
Release GIL
     ↓
CPU-intensive native operation
     ↓
Reacquire GIL
     ↓
Python code
```

This allows multiple threads to execute native operations concurrently.

This is one reason why the statement:

> "Python threads cannot run in parallel."

is too broad.

A more accurate statement is:

> Traditional GIL-enabled CPython does not allow multiple threads to execute Python bytecode simultaneously within one interpreter, but native code can execute concurrently when it releases the GIL.

---

## Numerical and Data Processing

Some libraries perform heavy computation in native code.

For example, an operation may conceptually look like:

```text
Python
  ↓
NumPy API
  ↓
Native implementation
  ↓
Multiple CPU cores
```

The actual threading behavior depends on the library, operation, build configuration, and underlying numerical libraries.

This is different from pure Python loops.

For backend and data-engineering workloads, measure the actual implementation rather than reasoning from the Python syntax alone.

---

## GIL and C Extensions

A native extension must coordinate correctly with Python's interpreter state.

When an extension releases the GIL, it must not access Python objects in ways that require interpreter protection unless the appropriate runtime mechanisms are used.

This creates a boundary:

```text
Python-managed state
       ↕
Interpreter synchronization
       ↕
Native computation
```

Poorly implemented native extensions can introduce memory corruption or race conditions.

The GIL is therefore not a substitute for correct synchronization in native code.

---

## GIL and Thread Safety

The GIL does not make application code thread-safe.

For example:

```python
shared_state = {}


def update() -> None:
    shared_state["count"] = (
        shared_state.get("count", 0) + 1
    )
```

The GIL should not be treated as an application-level synchronization mechanism.

Concurrent operations can still produce incorrect results when multiple steps must be coordinated atomically.

Use appropriate mechanisms such as:

- `threading.Lock`
- `Queue`
- immutable state
- database transactions
- atomic Redis operations
- other explicit synchronization

---

## The GIL Is Not a Database Lock

Consider:

```text
Thread A
   ↓
read order

Thread B
   ↓
read order

Thread A
   ↓
update order

Thread B
   ↓
update order
```

The GIL does not provide business-level transaction semantics.

For PostgreSQL-backed systems, correctness may require:

```sql
BEGIN;

SELECT ...
FOR UPDATE;

UPDATE ...;

COMMIT;
```

The appropriate synchronization boundary is the database transaction, not the Python interpreter lock.

---

## GIL and Multiple Web Workers

A production web application often uses multiple processes.

For example:

```text
Nginx / Load Balancer
        │
        ├── Worker Process 1
        ├── Worker Process 2
        ├── Worker Process 3
        └── Worker Process 4
```

Each process has its own interpreter.

This allows a traditional CPython deployment to use multiple CPU cores even when each process is GIL-enabled.

This is one reason production Python web servers commonly use multiple worker processes.

---

## FastAPI Example

A deployment might conceptually look like:

```text
Load Balancer
      ↓
FastAPI
├── Process 1
├── Process 2
├── Process 3
└── Process 4
      ↓
PostgreSQL / Redis / APIs
```

The processes provide CPU-level parallelism while asynchronous execution within each process can provide high I/O concurrency.

These mechanisms are complementary:

```text
Processes
→ parallelism across CPU cores

asyncio
→ concurrency within each process
```

---

## Django Example

Django deployments can similarly use multiple worker processes.

For example:

```text
Nginx
  ↓
Application Server
  ├── Worker 1
  ├── Worker 2
  ├── Worker 3
  └── Worker 4
```

Each worker process has independent interpreter state.

Therefore, application-level in-memory state is not automatically shared across workers.

This is important for:

- caches
- counters
- locks
- session state
- rate limits
- configuration
- background tasks

Use shared infrastructure such as Redis or PostgreSQL when state must be shared across workers.

---

## GIL and Containerized Deployment

In Docker or Kubernetes, CPU parallelism is determined by the available CPU resources and worker configuration.

For example:

```text
Pod CPU limit = 4 cores

Application
├── Process 1
├── Process 2
├── Process 3
└── Process 4
```

The correct number of workers depends on:

- workload
- CPU limit
- memory
- I/O behavior
- framework
- database capacity

Do not blindly configure one process per CPU without load testing.

---

## Kubernetes Concurrency Multiplication

Concurrency can multiply across deployment layers.

Example:

```text
6 Kubernetes pods
×
4 Python worker processes
×
8 threads
=
192 potential threads
```

That does not mean 192 threads are beneficial.

The resulting workload may overwhelm:

- PostgreSQL
- Redis
- external APIs
- network connections
- CPU
- memory

The GIL is only one part of the capacity model.

---

## GIL and Connection Pools

Suppose:

```text
4 processes
×
10 database connections
=
40 potential connections
```

Increasing process count to improve CPU utilization may unintentionally increase database connection usage.

Therefore, worker tuning must consider the entire system.

```text
Python workers
      ↓
Connection pools
      ↓
PostgreSQL capacity
```

---

## Free-Threaded CPython

CPython has introduced support for **free-threaded builds**, where the traditional GIL can be disabled.

This changes the execution model:

```text
Free-threaded build

Thread A → Python bytecode → Core 1
Thread B → Python bytecode → Core 2
Thread C → Python bytecode → Core 3
Thread D → Python bytecode → Core 4
```

This can enable genuine multi-core execution of Python code within one process.

However, free-threading does not mean:

```text
threads = automatically faster
```

Applications still encounter:

- lock contention
- memory contention
- cache contention
- synchronization overhead
- thread-unsafe code
- third-party dependency limitations

---

## Free-Threaded Builds and Compatibility

The free-threaded runtime changes assumptions that some native extensions or application components may have historically made.

Production adoption should verify:

- Python version support
- extension compatibility
- dependency support
- framework support
- thread-safety guarantees
- performance under realistic workloads

Do not switch interpreter modes solely because the application is CPU-bound.

Benchmark the complete application.

---

## GIL and CPU Scaling

For traditional GIL-enabled CPython:

```text
One process + many threads
→ limited Python-bytecode parallelism

Many processes
→ multi-core Python execution
```

For a free-threaded build:

```text
One process + many threads
→ potential multi-core Python execution
```

But in both cases:

```text
CPU capacity
≠
application throughput
```

The workload may still be limited by:

- memory bandwidth
- database access
- network latency
- synchronization
- algorithmic complexity
- downstream services

---

## GIL and Context Switching

Threads competing for the GIL can incur scheduling overhead.

A simplified execution pattern is:

```text
Thread A
  ↓
execute
  ↓
GIL handoff
  ↓
Thread B
  ↓
execute
  ↓
GIL handoff
  ↓
Thread C
```

Frequent switching can reduce efficiency for small CPU-bound tasks.

This is one reason a CPU-heavy workload may become slower when unnecessarily threaded.

---

## GIL and Latency

The GIL can affect latency as well as throughput.

If a thread performs long-running Python computation:

```text
Thread A
└── CPU-heavy Python execution
        ↓
Other threads receive limited execution opportunities
```

This can delay unrelated work.

In an async web service, CPU-heavy work can be even more disruptive because blocking the event loop can delay many requests.

Move substantial CPU work to:

- process workers
- dedicated services
- native implementations
- specialized compute infrastructure

as appropriate.

---

## GIL and Background Jobs

Long-running CPU-bound jobs should generally not execute directly inside a request handler.

Prefer:

```text
API
 ↓
Queue
 ↓
Worker
 ↓
Process-based CPU execution
 ↓
Result storage
```

Celery is one common architecture.

For large-scale systems, separate compute workers can be independently scaled.

---

## GIL and Kafka Consumers

Kafka consumers may benefit from multiple processes or consumer instances when CPU-heavy processing is required.

For example:

```text
Kafka Topic
    │
    ├── Partition 0 → Consumer Process A
    ├── Partition 1 → Consumer Process B
    ├── Partition 2 → Consumer Process C
    └── Partition 3 → Consumer Process D
```

Partitioning provides a natural way to distribute work.

The design must still consider:

- partition count
- ordering requirements
- consumer rebalancing
- processing latency
- offset management
- duplicate processing

---

## GIL and Redis

Redis operations are I/O-bound from the Python application's perspective.

A threaded or asynchronous client can overlap Redis operations.

The GIL is therefore usually not the primary bottleneck.

The actual bottleneck may instead be:

- Redis server capacity
- network latency
- connection pool size
- serialization
- command complexity
- contention

---

## GIL and PostgreSQL

Similarly, PostgreSQL queries are generally I/O-bound from the Python application's perspective.

The GIL does not prevent multiple requests from waiting on PostgreSQL concurrently.

However, database capacity may become the bottleneck.

```text
100 application tasks
        ↓
20 DB connections
        ↓
PostgreSQL
```

Increasing Python concurrency beyond database capacity may simply increase waiting.

---

## Measuring GIL Impact

Do not diagnose GIL contention solely from CPU utilization.

Useful measurements include:

- CPU utilization
- per-thread CPU usage
- request latency
- throughput
- context switching
- thread count
- process count
- event-loop latency
- profiling data

A workload profiler can reveal whether the application spends most of its time:

```text
Python bytecode
Native code
I/O
Synchronization
Database waiting
```

---

## Benchmarking Threads vs Processes

A benchmark should compare realistic workloads.

```python
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from time import perf_counter


def cpu_work(value: int) -> int:
    total = 0

    for number in range(value):
        total += number * number

    return total


values = [2_000_000] * 8


start = perf_counter()

with ThreadPoolExecutor(max_workers=8) as executor:
    list(executor.map(cpu_work, values))

thread_duration = perf_counter() - start


start = perf_counter()

with ProcessPoolExecutor(max_workers=8) as executor:
    list(executor.map(cpu_work, values))

process_duration = perf_counter() - start

print(f"threads:  {thread_duration:.2f}s")
print(f"processes: {process_duration:.2f}s")
```

A benchmark like this is useful for demonstrating behavior, but production decisions should use representative workloads, machine sizes, Python builds, and dependency versions.

---

## Benchmarking Principles

A useful benchmark should control:

- Python version
- interpreter build
- operating system
- CPU allocation
- workload size
- worker count
- input data
- warm-up behavior
- process startup cost
- serialization cost

Measure:

```text
Throughput
Latency
CPU
Memory
Context switches
Worker utilization
```

Do not benchmark only elapsed time.

---

## Common Misconceptions

### "The GIL Means Python Is Single-Threaded"

Incorrect.

Python programs can have many threads and perform concurrent I/O.

The traditional GIL limits simultaneous Python-bytecode execution within one interpreter.

### "The GIL Prevents Multi-Core Python"

Incorrect as a universal statement.

Multiple processes can use multiple cores, and free-threaded CPython builds can execute Python code across threads without the traditional GIL.

### "The GIL Makes Locks Unnecessary"

Incorrect.

The GIL is not a substitute for application-level synchronization.

### "Asyncio Removes the GIL"

Incorrect.

`asyncio` provides cooperative concurrency, not CPU parallelism.

### "More Threads Always Improve Performance"

Incorrect.

For CPU-bound Python code under the traditional GIL model, more threads can reduce performance.

### "The GIL Protects Database Operations"

Incorrect.

Database consistency is controlled by database transactions and constraints.

---

## Production Pitfalls

### Treating the GIL as an Architecture

The GIL is an implementation detail, not an application architecture.

Design around workload characteristics and system capacity.

### Increasing Thread Counts to Solve CPU Saturation

For traditional GIL-enabled CPython, this may increase contention without increasing CPU throughput.

### Increasing Process Counts Without Capacity Planning

More processes can increase:

- memory
- database connections
- network connections
- CPU contention

### Running CPU Work in an Async Endpoint

This can block the event loop and increase latency across unrelated requests.

### Assuming Native Libraries Behave Like Pure Python

Native libraries may release the GIL or use their own thread pools.

Their actual behavior must be measured.

### Ignoring Free-Threaded Compatibility

Applications adopting free-threaded builds must verify framework and extension compatibility.

---

## Security Considerations

The GIL provides no meaningful application-level security boundary.

Do not use it to protect:

- authorization state
- credentials
- tenant isolation
- financial transactions
- sensitive configuration
- security-sensitive counters

Security correctness requires explicit controls.

For example:

```text
Authorization
    ↓
Database transaction
    ↓
Atomic state transition
```

rather than:

```text
Authorization
    ↓
Python thread lock
```

---

## Reliability Considerations

Concurrency mechanisms must account for failure.

Threads and processes can terminate unexpectedly.

Production systems should use:

- bounded work
- timeouts
- retries where appropriate
- idempotency
- durable queues
- graceful shutdown
- health checks
- structured logging

For distributed workloads, assume that work can be:

- interrupted
- duplicated
- delayed
- retried
- reordered

---

## High Availability

A multi-process deployment can improve availability by isolating worker processes.

For example:

```text
Load Balancer
    │
    ├── Pod A
    │    ├── Worker 1
    │    └── Worker 2
    │
    ├── Pod B
    │    ├── Worker 1
    │    └── Worker 2
    │
    └── Pod C
         ├── Worker 1
         └── Worker 2
```

If one process fails, other processes may continue serving requests.

Kubernetes can restart failed containers and redistribute traffic.

However, high availability depends on the complete system, including databases, queues, caches, and external dependencies.

---

## Cost Considerations

Process-based parallelism can increase infrastructure cost because each worker requires resources.

Example:

```text
4 workers
×
300 MiB average memory
≈
1.2 GiB worker memory
```

Actual memory usage depends on:

- interpreter state
- imported modules
- workload
- copy-on-write behavior
- operating system
- process start method

For Kubernetes and AWS, worker count directly influences resource requests, limits, pod density, and cost.

---

## Disaster Recovery

The GIL has no direct role in disaster recovery.

Concurrent state should not be considered durable.

Persist important application state in durable systems such as:

- PostgreSQL
- Kafka
- SQS
- durable object storage
- Redis when appropriate for the state semantics

After process or pod failure, the application should be able to reconstruct required state.

---

## Recommended Decision Framework

Use the following decision process:

```text
Is the workload CPU-bound?
        │
        ├── No
        │    └── Is it non-blocking I/O?
        │          ├── Yes → asyncio
        │          └── No  → threads / worker
        │
        └── Yes
             │
             ├── Native code releases GIL?
             │       └── Threads may work
             │
             └── Pure Python
                     │
                     ├── GIL-enabled CPython
                     │       └── Processes
                     │
                     └── Free-threaded CPython
                             └── Benchmark threads
```

Then validate the choice against:

- memory
- database capacity
- downstream rate limits
- workload duration
- serialization cost
- deployment topology

---

## Best Practices

- Treat the GIL as a CPython implementation detail, not a Python language rule.
- Distinguish Python-bytecode execution from I/O and native-code execution.
- Use threads primarily for I/O-bound workloads under traditional GIL-enabled CPython.
- Use processes for CPU-bound pure Python workloads when parallel execution is required.
- Use `asyncio` for high-concurrency non-blocking I/O rather than as a CPU-parallelism mechanism.
- Do not use the GIL as an application-level synchronization mechanism.
- Minimize shared mutable state regardless of the interpreter locking model.
- Measure native-library behavior rather than assuming whether the GIL is released.
- Account for worker multiplication across Kubernetes replicas, processes, and threads.
- Tune concurrency against database and downstream capacity.
- Use queues and worker processes for substantial background CPU workloads.
- Benchmark free-threaded builds before adopting them for production workloads.
- Verify native extension and framework compatibility with free-threaded Python.
- Monitor CPU, memory, latency, worker utilization, and downstream resource usage.
- Use profiling and load testing to identify actual bottlenecks before changing concurrency configuration.

---

## Interview Traps

| Question | Correct Reasoning |
|---|---|
| Does the GIL prevent multiple threads from existing? | No |
| Can threads perform concurrent I/O? | Yes |
| Can traditional GIL-enabled threads execute Python bytecode simultaneously? | No, not within the same interpreter |
| Can Python use multiple CPU cores? | Yes, commonly through multiple processes and also through suitable native code or free-threaded builds |
| Does `asyncio` bypass the GIL? | No |
| Does the GIL make code thread-safe? | No |
| Are multiprocessing workers affected by one process's GIL? | No; each process has its own interpreter |
| Can native extensions run concurrently? | Yes, when they release the GIL appropriately |
| Does more threading always improve performance? | No |
| Is the GIL part of Python's language specification? | No |

---

## Production Checklist

Before choosing a concurrency strategy, verify:

- [ ] Workload has been classified as CPU-bound or I/O-bound.
- [ ] Actual CPython build and version are known.
- [ ] GIL-enabled vs free-threaded execution has been explicitly considered.
- [ ] Native dependencies have been evaluated for GIL behavior.
- [ ] Thread/process counts are bounded.
- [ ] Database connection requirements have been calculated.
- [ ] Redis and HTTP connection limits have been considered.
- [ ] CPU and memory limits are known.
- [ ] Kubernetes replica multiplication has been included in capacity planning.
- [ ] CPU-heavy work is not blocking an async event loop.
- [ ] Background CPU workloads have appropriate worker isolation.
- [ ] Shared state has explicit synchronization where required.
- [ ] Database-level consistency does not rely on the GIL.
- [ ] Timeouts and cancellation behavior are defined.
- [ ] Retry and idempotency semantics are defined.
- [ ] Worker shutdown behavior is graceful.
- [ ] CPU, memory, latency, and concurrency metrics are monitored.
- [ ] Load testing has been performed under realistic resource limits.
- [ ] Production configuration is based on measurements rather than generic worker-count rules.

## Key Takeaways

- **The GIL is a CPython implementation mechanism:** in traditional GIL-enabled builds, only one thread at a time executes Python bytecode within an interpreter.
- **The GIL does not eliminate concurrency:** threads remain effective for I/O-bound workloads, and suitable native code can execute concurrently when it releases the GIL.
- **Processes provide traditional multi-core Python parallelism:** each process has an independent interpreter and GIL, making processes a strong choice for CPU-bound pure Python workloads.
- **`asyncio` and the GIL solve different problems:** `asyncio` provides cooperative I/O concurrency, while CPU parallelism requires processes, suitable native implementations, or a free-threaded interpreter.
- **Modern Python changes the picture:** free-threaded CPython builds can remove the traditional GIL, but production adoption still requires compatibility testing, benchmarking, and careful synchronization design.