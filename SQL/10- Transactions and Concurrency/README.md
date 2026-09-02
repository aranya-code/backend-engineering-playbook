# README.md

## Overview

Transactions and concurrency are fundamental to building reliable backend systems. They determine how multiple database operations behave as one logical unit and how concurrent requests interact when they read or modify shared state.

This section focuses on the engineering decisions required to use transactions safely in production PostgreSQL-backed applications.

The progression is:

```text
Transaction Fundamentals
        │
        ├── Transaction lifecycle
        ├── BEGIN / COMMIT / ROLLBACK
        ├── SAVEPOINT
        └── Transaction boundaries
                │
                ▼
Isolation and Concurrency
        │
        ├── Autocommit
        ├── Isolation levels
        ├── Dirty reads
        ├── Non-repeatable reads
        ├── Phantom reads
        └── Lost updates
                │
                ▼
Locking and Concurrency Control
        │
        ├── Shared / exclusive locks
        ├── Row / table locks
        ├── Deadlocks
        ├── Optimistic concurrency
        └── Pessimistic concurrency
                │
                ▼
Production Transaction Design
        │
        ├── Retry strategies
        ├── Transaction design rules
        ├── Isolation-level selection
        ├── When to use transactions
        ├── Large transaction risks
        ├── Backend application integration
        └── Common mistakes
```

The primary database examples use PostgreSQL because transaction behavior is database-specific. Framework examples use Python, Django, and SQLAlchemy where they provide useful application-level context.

---

## Navigation

- [01- Transactions](./01-%20Transactions.md) — What transactions are and why they are essential for backend reliability
- [02- ACID Properties](./02-%20ACID%20Properties.md) — Atomicity, Consistency, Isolation, and Durability explained
- [03- BEGIN](./03-%20BEGIN.md) — Starting a transaction explicitly
- [04- COMMIT and ROLLBACK](./04-%20COMMIT%20and%20ROLLBACK.md) — Finalizing or reversing a transaction
- [05- SAVEPOINT](./05-%20SAVEPOINT.md) — Partial rollback with named savepoints
- [06- Transaction Boundaries](./06-%20Transaction%20Boundaries.md) — Defining where transactions begin and end in application code
- [07- Autocommit](./07-%20Autocommit.md) — Implicit transaction behavior and its implications
- [08- Isolation Levels](./08-%20Isolation%20Levels.md) — How databases control visibility of concurrent changes
- [09- Read Uncommitted](./09-%20Read%20Uncommitted.md) — The weakest isolation level and its risks
- [10- Read Committed](./10-%20Read%20Committed.md) — PostgreSQL default isolation and its concurrency behavior
- [11- Repeatable Read](./11-%20Repeatable%20Read.md) — Preventing non-repeatable reads within a transaction
- [12- Serializable](./12-%20Serializable.md) — Strongest isolation and serializable snapshot isolation
- [13- Snapshot Isolation](./13-%20Snapshot%20Isolation.md) — MVCC-based isolation and how PostgreSQL implements it
- [14- Dirty Reads](./14-%20Dirty%20Reads.md) — Reading uncommitted data and why it is dangerous
- [15- Non-Repeatable Reads](./15-%20Non-Repeatable%20Reads.md) — When the same row returns different values within one transaction
- [16- Phantom Reads](./16-%20Phantom%20Reads.md) — When repeated queries return different row sets
- [17- Lost Updates](./17-%20Lost%20Updates.md) — Concurrent overwrites and how to prevent them
- [18- Locks](./18-%20Locks.md) — How the database controls concurrent access to shared data
- [19- Shared and Exclusive Locks](./19-%20Shared%20and%20Exclusive%20Locks.md) — Lock types, compatibility, and acquisition rules
- [20- Row-Level and Table-Level Locks](./20-%20Row-Level%20and%20Table-Level%20Locks.md) — Lock granularity and its effect on concurrency
- [21- Deadlocks](./21-%20Deadlocks.md) — How deadlocks form, how to detect them, and how to avoid them
- [22- Optimistic vs Pessimistic Concurrency](./22-%20Optimistic%20vs%20Pessimistic%20Concurrency.md) — Choosing a concurrency strategy for the workload
- [23- Transaction Retry Strategies](./23-%20Transaction%20Retry%20Strategies.md) — Designing retry logic for serialization failures
- [24- Transaction Design Rules](./24-%20Transaction%20Design%20Rules.md) — Practical rules for correct and safe transaction design
- [25- Choosing an Isolation Level](./25-%20Choosing%20an%20Isolation%20Level.md) — Selecting the right isolation level for a workload
- [26- When to Use Transactions](./26-%20When%20to%20Use%20Transactions.md) — Identifying operations that require transactional guarantees
- [27- When Not to Use Large Transactions](./27-%20When%20Not%20to%20Use%20Large%20Transactions.md) — Risks of long-running transactions and how to avoid them
- [28- Transactions in Backend Applications](./28-%20Transactions%20in%20Backend%20Applications.md) — Django, SQLAlchemy, and application-level transaction management
- [29- Common Transaction Mistakes](./29-%20Common%20Transaction%20Mistakes.md) — Correctness, performance, isolation, and production pitfalls

---


## How to Read This Section

The files are designed to build progressively from transaction mechanics toward production-level concurrency design.

### Transaction Fundamentals

Start with the basic transaction lifecycle before studying concurrency.

| File | Focus |
|---|---|
| `01- Transactions.md` | Transaction fundamentals and database transaction semantics |
| `02- ACID Properties.md` | Atomicity, consistency, isolation, and durability |
| `03- BEGIN.md` | Starting explicit database transactions |
| `04- COMMIT and ROLLBACK.md` | Completing or reversing transactions |
| `05- SAVEPOINT.md` | Partial rollback and nested transaction semantics |
| `06- Transaction Boundaries.md` | Choosing transaction boundaries in applications |
| `07- Autocommit.md` | Statement-level transaction behavior and framework defaults |

The key objective at this stage is understanding that a transaction is a **business consistency boundary**, not simply a collection of SQL statements.

---

## Isolation and Concurrency

Once transaction fundamentals are understood, study how concurrent transactions interact.

| File | Focus |
|---|---|
| `08- Isolation Levels.md` | Isolation guarantees and concurrency trade-offs |
| `09- Read Uncommitted.md` | Weak isolation semantics |
| `10- Read Committed.md` | PostgreSQL's common default isolation level |
| `11- Repeatable Read.md` | Stable transaction snapshots |
| `12- Serializable.md` | Strong serializable execution guarantees |
| `13- Snapshot Isolation.md` | MVCC snapshot-based concurrency |
| `14- Dirty Reads.md` | Reading uncommitted changes |
| `15- Non-Repeatable Reads.md` | Seeing different committed values within a transaction |
| `16- Phantom Reads.md` | Changes to a matching row set during concurrent execution |
| `17- Lost Updates.md` | Concurrent read-modify-write conflicts |

A central principle is:

> Isolation level determines what concurrent transactions are allowed to observe; it does not eliminate every concurrency problem automatically.

PostgreSQL-specific behavior should be understood rather than assuming that SQL-standard terminology maps identically to every database engine.

---

## Locks and Concurrency Control

Locks provide explicit control when concurrent operations need coordination.

| File | Focus |
|---|---|
| `18- Locks.md` | Database locking fundamentals |
| `19- Shared and Exclusive Locks.md` | Shared and exclusive lock behavior |
| `20- Row-Level and Table-Level Locks.md` | Lock granularity and contention |
| `21- Deadlocks.md` | Circular lock dependencies and recovery |
| `22- Optimistic vs Pessimistic Concurrency.md` | Choosing concurrency-control strategies |
| `23- Transaction Retry Strategies.md` | Recovering from transient transaction failures |

Typical PostgreSQL patterns include:

```sql
SELECT *
FROM inventory
WHERE product_id = 42
FOR UPDATE;
```

and atomic conditional updates:

```sql
UPDATE inventory
SET available = available - 1
WHERE product_id = 42
  AND available > 0;
```

The correct approach depends on the invariant, contention level, access pattern, and workload.

---

## Production Transaction Design

The final group connects database transactions with real backend architecture.

| File | Focus |
|---|---|
| `24- Transaction Design Rules.md` | General production transaction principles |
| `25- Choosing an Isolation Level.md` | Selecting isolation based on business requirements |
| `26- When to Use Transactions.md` | Identifying operations that require transactions |
| `27- When Not to Use Large Transactions.md` | Transaction size, duration, and operational risks |
| `28- Transactions in Backend Applications.md` | Applying transactions to APIs, services, workers, and microservices |
| `29- Common Transaction Mistakes.md` | Common correctness, performance, and reliability failures |

This is where database knowledge becomes backend engineering.

A production transaction design should account for:

```text
Business invariant
      │
      ▼
Transaction boundary
      │
      ▼
Concurrency strategy
      │
      ▼
Database constraints
      │
      ▼
Failure / retry strategy
      │
      ▼
External side effects
      │
      ▼
Observability + operations
```

---

## Core Mental Model

When designing a transactional operation, reason in this order:

### Identify the invariant

Ask:

> What must always remain true?

Examples:

```text
Inventory cannot become negative.
Account balance cannot become negative.
Only one active subscription exists per user.
An order cannot be confirmed without successful payment.
```

### Identify the state transition

Determine which records change:

```text
Order: PENDING → CONFIRMED
Inventory: 10 → 9
Payment: AUTHORIZED → CAPTURED
```

### Identify concurrent actors

Consider:

```text
HTTP requests
Celery workers
Kafka consumers
Scheduled jobs
Administrative operations
Background migrations
```

### Choose the smallest sufficient mechanism

Possible mechanisms include:

- Atomic SQL
- Database constraints
- Row-level locking
- Optimistic concurrency
- Isolation-level changes
- Explicit transactions
- Idempotency
- Transactional outbox
- State machines

Do not default to the strongest or most complex mechanism without understanding the invariant.

---

## PostgreSQL Transaction Model

PostgreSQL uses MVCC and transaction snapshots to provide concurrency without requiring every read to block writers.

A simplified model is:

```text
Transaction A
     │
     ├── reads snapshot
     ├── modifies rows
     └── COMMIT
             │
             ▼
       visible to later
       transactions
```

Concurrent transactions can still conflict.

Depending on isolation and access patterns, PostgreSQL may:

- Block on locks
- Detect deadlocks
- Reject a transaction with serialization failure
- Allow concurrent operations
- Provide different snapshots to different statements

Therefore, application correctness must be designed around PostgreSQL's actual transaction semantics.

---

## Transaction Boundary in a Backend Service

A typical service-layer transaction looks like:

```text
HTTP / gRPC request
        │
        ▼
Controller
        │
        ▼
Application Service
        │
        ├── BEGIN
        │
        ├── Read state
        ├── Validate invariant
        ├── Lock or atomically update
        ├── Write business state
        ├── Write outbox event
        │
        └── COMMIT
                │
                ▼
             Response
```

External processing happens after durable database state exists:

```text
PostgreSQL
    │
    ├── business state
    └── outbox event
             │
             ▼
      asynchronous worker
             │
             ▼
           Kafka
             │
             ▼
      downstream services
```

This separation is especially important in microservice architectures.

---

## Framework Integration

### Django

Use `transaction.atomic()` around business operations:

```python
from django.db import transaction

@transaction.atomic
def reserve_inventory(product_id: int, quantity: int):
    inventory = (
        Inventory.objects
        .select_for_update()
        .get(product_id=product_id)
    )

    if inventory.available < quantity:
        raise InsufficientInventory()

    inventory.available -= quantity
    inventory.save(update_fields=["available"])
```

Use database constraints for invariants such as uniqueness and valid ranges.

### FastAPI / SQLAlchemy

Define the transaction boundary explicitly:

```python
def reserve_inventory(session, product_id: int, quantity: int):
    with session.begin():
        inventory = (
            session.query(Inventory)
            .filter(Inventory.product_id == product_id)
            .with_for_update()
            .one()
        )

        if inventory.available < quantity:
            raise InsufficientInventory()

        inventory.available -= quantity
```

FastAPI itself does not define transaction semantics. The database session and transaction management strategy do.

---

## Transactions and External Systems

A database transaction cannot automatically include:

- Kafka
- Redis
- HTTP APIs
- Email providers
- Payment gateways
- Object storage

For example:

```text
PostgreSQL transaction
        │
        ├── update order
        ├── publish Kafka event
        └── update Redis
```

creates failure combinations that cannot be atomically rolled back.

For important events, use a transactional outbox:

```text
┌────────────────────────┐
│      PostgreSQL        │
│                        │
│  business state        │
│  outbox_events         │
└───────────┬────────────┘
            │
          COMMIT
            │
            ▼
┌────────────────────────┐
│    Outbox Publisher    │
└───────────┬────────────┘
            │
            ▼
          Kafka
```

Consumers should generally be idempotent because the publisher may retry delivery.

---

## Production Concerns

Transaction design affects more than correctness.

### Performance

Monitor:

- Query duration
- Transaction duration
- Lock wait time
- Connection acquisition time
- Commit latency

A transaction can be slow even when its individual SQL statements are fast because it may spend time waiting for locks or external application work.

### Scalability

As concurrency increases:

```text
More requests
     ↓
More concurrent transactions
     ↓
More lock contention
     ↓
More waiting/retries
     ↓
Reduced throughput
```

Avoid unnecessary locking and keep critical sections short.

### Reliability

Design for:

- Deadlocks
- Serialization failures
- Connection failures
- Database failover
- Transaction timeouts
- Retry storms
- Uncertain commit outcomes

### High Availability

Transaction behavior should remain correct during:

- PostgreSQL failover
- Application restarts
- Kubernetes pod termination
- Network interruptions
- Connection pool failures

Retries should respect request deadlines and idempotency.

### Disaster Recovery

Transactions provide local atomicity, but recovery also depends on:

- Backups
- WAL
- Point-in-time recovery
- Replication
- Recovery procedures
- Data reconciliation

A transaction design should not assume that database availability and disaster recovery are the same problem.

---

## Common Transaction Anti-Patterns

Avoid these patterns:

```text
BEGIN
  │
  ├── database query
  ├── HTTP request
  ├── sleep
  ├── expensive computation
  ├── database query
  └── COMMIT
```

Avoid:

- Unbounded transaction duration
- Unnecessary row locks
- Application-only uniqueness checks
- Blind retries
- Unbounded retries
- Retrying only one statement
- Blind retry after uncertain commit
- Treating Kafka as part of a PostgreSQL transaction
- Treating Redis as transactional with PostgreSQL
- Huge all-or-nothing bulk operations when batching is acceptable
- Ignoring long-running `idle in transaction` sessions

---

## Operational Observability

Transaction-heavy services should expose database behavior through metrics and tracing.

Important metrics include:

| Metric | Purpose |
|---|---|
| Transaction duration | Detect long transactions |
| Lock wait duration | Detect contention |
| Deadlock count | Detect lock dependency problems |
| Serialization failures | Detect high concurrency conflicts |
| Retry count | Measure transient failures |
| Connection pool utilization | Detect capacity pressure |
| Transaction failure rate | Detect correctness/availability issues |
| Outbox backlog | Detect asynchronous delivery delays |
| Replication lag | Detect database propagation pressure |

PostgreSQL activity can be inspected with:

```sql
SELECT
    pid,
    state,
    xact_start,
    now() - xact_start AS transaction_age,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

Long-running and `idle in transaction` sessions deserve particular attention.

---

## Recommended Learning Sequence

For efficient progression, study the section in this order:

```text
Transactions
    ↓
ACID
    ↓
BEGIN / COMMIT / ROLLBACK
    ↓
SAVEPOINT
    ↓
Transaction Boundaries
    ↓
Autocommit
    ↓
Isolation Levels
    ↓
Isolation Anomalies
    ↓
Locks
    ↓
Deadlocks
    ↓
Optimistic vs Pessimistic Concurrency
    ↓
Retry Strategies
    ↓
Transaction Design Rules
    ↓
Isolation-Level Selection
    ↓
When to Use Transactions
    ↓
Large Transaction Risks
    ↓
Backend Application Integration
    ↓
Common Mistakes
```

Do not memorize isolation-level definitions in isolation. For each concept, reason about:

```text
Concurrent Request A
        +
Concurrent Request B
        +
Database behavior
        ↓
Possible outcome
        ↓
Required correctness mechanism
```

This produces stronger practical understanding than memorizing terminology.

---

## Interview Focus

For senior backend interviews, be prepared to explain transactions through real concurrency scenarios rather than definitions.

You should be able to reason about:

- ACID and its practical meaning
- Transaction boundaries
- Autocommit
- Isolation levels
- MVCC
- Dirty reads
- Non-repeatable reads
- Phantom reads
- Lost updates
- Row-level locking
- `SELECT ... FOR UPDATE`
- Optimistic concurrency
- Pessimistic concurrency
- Deadlock detection and retry
- Serialization failures
- Atomic conditional updates
- Database constraints
- Idempotency
- Transactional outbox
- Distributed transaction limitations
- Large transaction risks
- Connection pool interaction
- Long-running transactions
- Uncertain commit outcomes

A strong senior-level answer should explain **why** a particular mechanism is appropriate for a given workload.

---

## Practical Backend Scenarios

Use the following scenarios to connect the database concepts to real backend systems.

| Scenario | Primary Concern | Typical Mechanism |
|---|---|---|
| Inventory reservation | Prevent overselling | Atomic update or row lock |
| Bank transfer | Atomic multi-row update | Transaction + constraints |
| Unique username | Concurrent uniqueness | Unique constraint |
| Document editing | Stale writes | Optimistic concurrency |
| Job claiming | Concurrent workers | Row locking / atomic state transition |
| Payment creation | Duplicate requests | Idempotency |
| Order event publishing | DB/Kafka consistency | Transactional outbox |
| Large data migration | Lock and WAL pressure | Batching / online migration |
| High-contention counter | Concurrent increments | Atomic SQL |
| Multi-service workflow | Distributed consistency | Events + state machine |

These scenarios should be used to test whether you can select an appropriate concurrency mechanism instead of applying transactions mechanically.

---

## Engineering Principles

The section should reinforce the following principles:

```text
1. Start with the business invariant.
2. Define the smallest correct transaction boundary.
3. Prefer database constraints for enforceable invariants.
4. Prefer atomic SQL for simple conditional state changes.
5. Use locks only when they provide necessary coordination.
6. Use optimistic concurrency when stale writes are acceptable to reject.
7. Keep transactions short and deterministic.
8. Retry only known transient failures.
9. Retry the entire transaction.
10. Make retryable operations idempotent.
11. Do not pretend external systems participate in local DB transactions.
12. Use outbox/event patterns for reliable asynchronous integration.
13. Monitor transaction duration and contention.
14. Design for failure, failover, and uncertain outcomes.
```

---

## Key Takeaways

- Transactions are business consistency boundaries; design them around invariants rather than around arbitrary groups of SQL statements.
- Concurrency correctness requires more than `BEGIN`/`COMMIT`; use the appropriate combination of atomic SQL, constraints, isolation, locks, and optimistic concurrency.
- Keep transactions short and avoid unnecessary work or external calls inside them to protect database throughput and availability.
- Treat retries, idempotency, deadlocks, serialization failures, and distributed side effects as first-class production concerns.
- Senior-level transaction design means reasoning about correctness, contention, failure modes, observability, scalability, and operational behavior together.