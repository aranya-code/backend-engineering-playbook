# Distributed Locking

## Overview

In a single-threaded application, preventing multiple processes from modifying the same resource is relatively straightforward. However, in distributed systems where multiple application instances, containers, or microservices are running simultaneously, coordinating access to shared resources becomes significantly more challenging.

Redis provides an efficient mechanism for implementing **distributed locks**, allowing applications running on different machines to coordinate access to shared resources.

Distributed locking is commonly used for:

- Preventing duplicate job execution
- Scheduled tasks
- Inventory reservation
- Payment processing
- Resource synchronization
- Leader election
- File processing
- Distributed cron jobs

Without proper locking, multiple services may process the same resource simultaneously, leading to inconsistent data and race conditions.

---

# Why Distributed Locking?

Imagine an e-commerce application.

Only one item remains in inventory.

```
Inventory

↓

Laptop

↓

Stock = 1
```

Two customers purchase it at exactly the same time.

```
Customer A

↓

Buy
```

```
Customer B

↓

Buy
```

Without synchronization:

```
Both Orders

↓

Accepted

↓

Inventory = -1
```

This is a classic race condition.

---

# What is a Distributed Lock?

A distributed lock allows only one application instance to access a shared resource at a time.

```
Application A

↓

Acquire Lock

↓

Success
```

```
Application B

↓

Acquire Lock

↓

Wait
```

Only one application proceeds.

---

# Conceptual Architecture

```
               Redis
                  │
        +---------+---------+
        │                   │
+-------v------+    +-------v------+
| Application A|    | Application B|
+--------------+    +--------------+
        │                   │
        │ Acquire Lock      │ Acquire Lock
        │                   │
        ▼                   ▼
      Granted            Denied
```

Redis acts as the central coordination service.

---

# Lock Lifecycle

A typical distributed lock follows this lifecycle.

```
Acquire Lock

↓

Process Resource

↓

Release Lock
```

If another application attempts to acquire the same lock:

```
Lock Exists

↓

Wait

or

Retry
```

---

# Basic Lock Workflow

```
Worker

↓

Request Lock

↓

Redis

↓

Lock Created

↓

Execute Task

↓

Release Lock
```

Only one worker performs the task.

---

# Why Redis?

Redis is well suited for distributed locking because it offers:

- Extremely fast operations
- Atomic commands
- Automatic expiration
- High throughput
- Low latency

Acquiring a lock typically takes only microseconds.

---

# Lock Expiration

A lock should never exist forever.

Suppose an application crashes.

```
Acquire Lock

↓

Crash

↓

Lock Never Released
```

Other applications become permanently blocked.

To prevent this:

```
Acquire Lock

↓

TTL = 30 Seconds
```

If the owner crashes:

```
TTL Expires

↓

Redis Removes Lock
```

The resource becomes available again.

---

# Lock Ownership

Every lock should contain an owner identifier.

Conceptually:

```
Lock

↓

job:invoice

↓

Owner

↓

Application A
```

Only the owner should be allowed to release the lock.

This prevents accidental deletion by another application.

---

# Race Condition Example

Without locking:

```
Application A

↓

Read Counter = 10
```

```
Application B

↓

Read Counter = 10
```

Both increment:

```
11

↓

11
```

Expected:

```
12
```

One update is lost.

With a distributed lock:

```
Application A

↓

Acquire Lock

↓

Increment

↓

Release
```

Then:

```
Application B

↓

Acquire Lock

↓

Increment

↓

Release
```

Final value:

```
12
```

---

# Inventory Reservation

One of the most common production use cases.

```
Customer

↓

Acquire Product Lock

↓

Check Inventory

↓

Reserve Product

↓

Release Lock
```

This prevents overselling.

---

# Payment Processing

Duplicate payments are expensive.

```
Payment Request

↓

Acquire Lock

↓

Charge Customer

↓

Store Result

↓

Release Lock
```

Even if duplicate requests arrive, only one proceeds.

---

# Scheduled Jobs

Consider multiple application servers.

```
Server A

↓

Daily Cleanup
```

```
Server B

↓

Daily Cleanup
```

Without locking:

```
Cleanup Executes Twice
```

With Redis locking:

```
Acquire Lock

↓

Only One Server Executes
```

---

# Background Workers

Suppose multiple workers process invoices.

```
Invoice Queue

↓

Worker A

↓

Worker B

↓

Worker C
```

Workers acquire locks before processing.

Each invoice is handled once.

---

# File Processing

Large files should not be processed simultaneously.

```
CSV File

↓

Acquire Lock

↓

Parse

↓

Import

↓

Release Lock
```

---

# Leader Election

Distributed systems often need a leader.

```
Node A

↓

Acquire Leadership Lock

↓

Leader
```

Other nodes remain followers.

If the leader crashes:

```
TTL Expires

↓

Another Node Becomes Leader
```

---

# Lock Timeout

Applications should not wait forever.

```
Acquire Lock

↓

Unavailable

↓

Retry

↓

Timeout
```

Eventually the application returns an error or retries later.

---

# Deadlocks

Without expiration:

```
Worker

↓

Acquire Lock

↓

Crash

↓

Permanent Lock
```

Other workers remain blocked indefinitely.

TTL prevents this.

---

# Distributed Lock vs Database Lock

| Feature | Database Lock | Redis Lock |
|----------|---------------|------------|
| Scope | Database | Distributed System |
| Speed | Moderate | Very Fast |
| Cross-Service | Limited | Excellent |
| TTL Support | Usually No | Yes |
| Cloud Native | Limited | Excellent |

Database locks protect database rows.

Redis locks coordinate entire distributed applications.

---

# Distributed Lock vs Mutex

| Feature | Mutex | Redis Lock |
|----------|-------|------------|
| Single Process | Yes | No |
| Multiple Machines | No | Yes |
| Shared Memory | Yes | No |
| Network Aware | No | Yes |

Mutexes work inside one application.

Redis locks work across many servers.

---

# Redlock Algorithm

For higher availability, Redis introduced the **Redlock Algorithm**.

Instead of relying on one Redis server:

```
Redis A

Redis B

Redis C

Redis D

Redis E
```

A lock is considered valid only if a majority of Redis nodes agree.

```
Acquire Lock

↓

3 of 5 Servers

↓

Success
```

Benefits:

- Fault tolerance
- Better availability
- Reduced single point of failure

### When is Redlock Needed?

Most applications **do not require Redlock**.

A single Redis instance with replication is sufficient for:

- API rate limiting
- Scheduled jobs
- Cache synchronization
- Background workers

Redlock becomes useful when:

- Distributed locks protect critical financial operations.
- Infrastructure spans multiple availability zones.
- Lock correctness is more important than performance.
- A single Redis failure cannot be tolerated.

---

# Common Production Use Cases

Distributed locking is widely used for:

- Inventory reservation
- Payment processing
- Distributed cron jobs
- Scheduled tasks
- Background workers
- Leader election
- Report generation
- File imports
- Email campaigns
- Cache rebuilding

---

# Common Mistakes

## No Expiration

```
Lock

↓

Never Expires
```

A crashed application permanently blocks others.

---

## Deleting Another Application's Lock

```
Worker A

↓

Owns Lock
```

```
Worker B

↓

Deletes Lock
```

This can introduce severe race conditions.

Always verify ownership before releasing a lock.

---

## Holding Locks Too Long

```
Acquire Lock

↓

30 Second Task

↓

Other Workers Wait
```

Keep lock duration as short as possible.

---

## Locking Too Much

Avoid locking entire workflows if only a small critical section requires synchronization.

---

# Best Practices

- Always use lock expiration (TTL).
- Store a unique owner identifier with every lock.
- Release locks immediately after work completes.
- Keep critical sections short.
- Handle lock acquisition failures gracefully.
- Monitor lock contention in production.
- Use distributed locks only when synchronization is genuinely required.

---

# Production Considerations

Before implementing distributed locks, consider:

- Maximum task duration
- Appropriate TTL values
- Retry strategy
- Failure handling
- Network partitions
- Redis availability
- Monitoring and alerting

Distributed locking should be carefully tested under failure scenarios to ensure correctness.

---

# Distributed Locking in Microservices

A common production architecture:

```
                API Gateway
                     │
          +----------+----------+
          │                     │
+---------v---------+  +--------v--------+
| Order Service     |  | Payment Service |
+---------+---------+  +--------+--------+
          │                     │
          +----------+----------+
                     │
               Redis Lock
                     │
              Shared Resource
```

Each service attempts to acquire a lock before modifying the shared resource, ensuring consistent behavior across the system.

---

# Summary

Distributed locking enables multiple application instances to coordinate access to shared resources in a distributed environment. Redis provides an efficient implementation through atomic operations and key expiration, making it ideal for preventing race conditions, duplicate processing, and concurrent updates. Proper lock ownership, expiration, and monitoring are essential for building reliable distributed systems. While advanced algorithms such as Redlock improve fault tolerance, most production applications achieve excellent results with a well-designed single Redis deployment using TTL-based locks.

---

# Key Takeaways

- Distributed locks prevent multiple applications from modifying the same resource simultaneously.
- Redis is an excellent choice for distributed locking because of its atomic operations and low latency.
- Every lock should have a TTL to prevent deadlocks.
- Lock ownership must be verified before releasing a lock.
- Distributed locks are commonly used for payments, inventory, scheduled jobs, and leader election.
- Redlock provides additional fault tolerance but is unnecessary for most applications.
- Keep lock durations short and monitor contention in production environments.