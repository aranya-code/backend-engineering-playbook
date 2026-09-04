# 16- Lock Contention

## Overview

**Lock contention** occurs when concurrent transactions need conflicting database locks and one or more transactions must wait.

Unlike a deadlock, contention does not require a circular dependency.

```text
Transaction A
    │
    ├── holds lock on row 101
    │
    └── performs work
            │
            ▼
Transaction B
    │
    └── requests row 101
            │
            ▼
         WAITING
```

When Transaction A commits, Transaction B can continue.

Lock contention is therefore a normal consequence of concurrency, but excessive contention becomes a production performance problem.

Typical symptoms include:

- Increasing query latency.
- High p95/p99 request latency.
- Transactions waiting on locks.
- Connection pools becoming exhausted.
- Reduced throughput.
- Increased timeout rates.
- Deadlocks when contention patterns form cycles.
- Replication or background-worker delays.

The senior engineering goal is not to eliminate all locking. It is to **keep necessary locking short, predictable, and appropriately scoped**.

---

## Lock Contention vs Deadlocks

| Property | Lock contention | Deadlock |
|---|---|---|
| Dependency | One transaction waits for another | Transactions wait in a cycle |
| Progress possible | Yes | No without aborting a transaction |
| Typical outcome | Waiter eventually acquires lock | PostgreSQL aborts one transaction |
| SQLSTATE | Usually no immediate error | `40P01` |
| Primary mitigation | Reduce wait duration/conflicts | Prevent cyclic lock ordering |
| Monitoring | Lock wait duration/rate | Deadlock count/rate |

A system can have severe lock contention without having a single deadlock.

---

## Why Locks Exist

Locks coordinate concurrent operations that cannot safely proceed independently.

For example, two requests attempting to allocate the final unit of inventory may need serialization.

```sql
SELECT id, available_quantity
FROM app.inventory
WHERE product_id = $1
FOR UPDATE;
```

The first transaction acquires the row lock.

The second transaction waits until the first transaction releases it.

This provides correctness at the cost of concurrency.

The engineering problem is therefore:

```text
Correctness
    ↕
Concurrency
    ↕
Lock duration
```

Good database design minimizes unnecessary trade-offs.

---

## PostgreSQL MVCC and Locking

PostgreSQL uses **MVCC (Multi-Version Concurrency Control)** for transaction visibility.

MVCC allows many reads to proceed without blocking ordinary writes in the same way traditional lock-based systems might.

However, PostgreSQL still uses locks for operations such as:

- Row-level updates.
- Explicit `FOR UPDATE` locking.
- Deletes.
- DDL.
- Certain constraint operations.
- Advisory locking.
- Transaction coordination.

Therefore:

```text
MVCC
≠
no locks
```

MVCC reduces unnecessary reader/writer blocking, but it does not eliminate lock contention.

---

## Row-Level Contention

A common production pattern is a hot row.

Example:

```sql
UPDATE app.accounts
SET balance = balance + $1
WHERE id = $2;
```

If thousands of requests continuously update the same account:

```text
Request 1 ──► account 42 ──► lock
Request 2 ──► account 42 ──► wait
Request 3 ──► account 42 ──► wait
Request 4 ──► account 42 ──► wait
...
```

Even if the SQL statement is fast, serialization around the same row limits throughput.

This is a **contention bottleneck**, not necessarily a query-performance problem.

---

## Hot Rows

A hot row is a database row that receives disproportionately high concurrent access.

Common examples include:

- Global counters.
- Inventory records.
- Popular account balances.
- Job scheduler state.
- Shared configuration records.
- Rate-limit counters.
- Frequently updated status records.

A single hot row can become a scalability ceiling.

For example:

```text
10,000 requests/second
        ↓
same database row
        ↓
serialized updates
        ↓
throughput limited by lock acquisition
```

Adding more application instances does not solve this.

It may increase contention.

---

## Hot Row Mitigation

Possible strategies include:

| Strategy | When useful | Trade-off |
|---|---|---|
| Atomic update | Simple numeric/state operation | Still serializes same row |
| Sharded counters | High-frequency counters | Requires aggregation |
| Queue serialization | Work naturally ordered | Adds latency |
| Partitioned ownership | Work can be divided | More complex routing |
| Redis counter | Very high-frequency ephemeral data | Requires durability strategy |
| Event aggregation | Append-heavy workloads | Eventually consistent totals |
| Database partitioning | Large data volume | Does not automatically solve same-row contention |

Choose based on correctness requirements.

---

## Atomic Updates

Prefer atomic SQL when possible.

Instead of:

```text
SELECT balance
UPDATE balance
```

use:

```sql
UPDATE app.accounts
SET balance = balance - $1
WHERE id = $2
  AND balance >= $1;
```

Then check the affected row count.

This avoids unnecessary application-level read-modify-write windows.

However, the update still requires serialization when multiple transactions modify the same row.

Atomic SQL reduces race conditions and transaction work; it does not make a hot row infinitely scalable.

---

## Explicit Row Locks

Use:

```sql
SELECT *
FROM app.orders
WHERE id = $1
FOR UPDATE;
```

when a transaction needs to inspect a row and then modify it while preventing conflicting concurrent changes.

Example:

```sql
BEGIN;

SELECT status
FROM app.orders
WHERE id = $1
FOR UPDATE;

UPDATE app.orders
SET status = 'processing'
WHERE id = $1;

COMMIT;
```

The lock remains relevant for the transaction's lifetime.

Therefore the surrounding transaction should be as short as practical.

---

## Lock Duration Is Critical

Consider:

```text
BEGIN
  ↓
acquire row lock
  ↓
HTTP request
  ↓
process response
  ↓
additional SQL
  ↓
COMMIT
```

The external request may take several seconds.

Every transaction waiting for that row is affected.

Prefer:

```text
BEGIN
  ↓
small database operation
  ↓
COMMIT
  ↓
external processing
```

when business semantics allow it.

Short transactions generally reduce both contention and failure amplification.

---

## Transaction Scope

A transaction should contain the operations that must be atomic.

It should not automatically contain every operation associated with a request.

Bad:

```python
with transaction.atomic():
    create_order()
    call_payment_provider()
    send_email()
    generate_report()
    update_search_index()
```

Better:

```text
Database transaction
    ├── create order
    ├── record payment intent
    └── create outbox event
            ↓
          COMMIT
            ↓
      asynchronous workers
            ├── payment provider
            ├── email
            └── search indexing
```

This separates database atomicity from external workflow execution.

---

## `NOWAIT`

When waiting itself is undesirable:

```sql
SELECT *
FROM app.orders
WHERE id = $1
FOR UPDATE NOWAIT;
```

The query fails immediately if the required lock cannot be acquired.

Useful for workflows where the application prefers:

```text
resource busy
    ↓
return conflict
```

rather than:

```text
wait several seconds
    ↓
request timeout
```

`NOWAIT` should be used when the business semantics support a conflict response.

---

## `SKIP LOCKED`

For suitable worker queues:

```sql
SELECT id
FROM app.jobs
WHERE status = 'pending'
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

Workers skip rows already locked by other workers.

This can significantly reduce worker contention.

However, it changes selection semantics.

A locked job may temporarily be skipped, so this pattern is appropriate only when the workload can tolerate that behavior.

---

## Advisory Locks

PostgreSQL advisory locks coordinate application-defined resources.

Example:

```sql
SELECT pg_advisory_xact_lock($1);
```

Transaction-level advisory locks are released when the transaction ends.

They can be useful for:

- Per-resource serialization.
- Rare administrative coordination.
- Preventing duplicate concurrent workflows.

However, advisory locks are still locks.

A system can create contention or deadlocks if application code acquires them unnecessarily or in inconsistent order.

Document advisory-lock ownership and ordering rules just as you would for row locks.

---

## Table-Level Contention

Not all contention is row-level.

Operations such as:

```sql
ALTER TABLE ...
```

can require table-level locks that conflict with concurrent activity.

This is particularly important during migrations.

A migration can appear simple:

```text
ALTER TABLE
```

but operationally become:

```text
migration
    ↓
waits for long transaction
    ↓
application transactions accumulate
    ↓
latency increases
    ↓
connection pools fill
```

Production DDL should therefore be evaluated for lock requirements and expected duration.

---

## Lock Contention During Migrations

Before applying a migration to a large production table, consider:

- Lock mode.
- Existing transaction duration.
- Table size.
- Concurrent traffic.
- Index creation behavior.
- Replica impact.
- `lock_timeout`.
- Deployment ordering.

For indexes, PostgreSQL supports:

```sql
CREATE INDEX CONCURRENTLY ...
```

for cases where avoiding the stronger blocking behavior of a regular index build is important.

It has operational trade-offs and cannot simply be substituted everywhere.

---

## Lock Timeout

PostgreSQL supports:

```sql
SET lock_timeout = '2s';
```

This limits how long a statement waits to acquire a lock.

Compare it with:

```sql
SET statement_timeout = '5s';
```

which limits total statement execution time.

| Setting | Protects against |
|---|---|
| `lock_timeout` | Excessive lock acquisition waits |
| `statement_timeout` | Excessive total statement execution |
| Connection timeout | Failure to establish a connection |

A timeout should be treated as a safety boundary, not a substitute for fixing contention.

---

## Lock Wait vs Query Execution

Suppose an API reports:

```text
database latency = 3 seconds
```

The query itself may take only:

```text
10 ms
```

while waiting for a lock for:

```text
2.99 seconds
```

Conceptually:

```text
Total latency
    =
lock wait
+
query execution
+
other database overhead
```

This is why `EXPLAIN ANALYZE` alone may not explain every production latency spike.

You must also inspect lock waits and transaction activity.

---

## Diagnosing Waiting Transactions

Start with:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    xact_start,
    query_start,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock'
ORDER BY xact_start NULLS LAST;
```

A session with:

```text
wait_event_type = Lock
```

is waiting on a lock-related event.

The next question is:

> Who is blocking it?

---

## Finding Blocking Sessions

PostgreSQL provides:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

This helps identify the immediate blocker.

Then inspect the blocker:

```sql
SELECT
    pid,
    usename,
    state,
    xact_start,
    query_start,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE pid = $1;
```

The blocker may itself be:

- Executing a query.
- Idle in a transaction.
- Waiting on another resource.
- Holding locks because of an unexpectedly long transaction.

---

## Inspecting Locks

Use:

```sql
SELECT
    pid,
    locktype,
    mode,
    granted,
    relation::regclass AS relation,
    transactionid,
    virtualxid
FROM pg_locks
ORDER BY pid, granted;
```

Important fields include:

- `pid`
- `locktype`
- `mode`
- `granted`
- `relation`
- `transactionid`
- `virtualxid`

A lock investigation should correlate `pg_locks` with `pg_stat_activity`.

---

## Idle in Transaction

One of the most dangerous contention patterns is:

```text
BEGIN
  ↓
UPDATE
  ↓
application does nothing
  ↓
connection remains open
```

PostgreSQL may continue to hold transaction-related resources while the transaction remains open.

Find such sessions with:

```sql
SELECT
    pid,
    usename,
    state,
    xact_start,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY xact_start;
```

Long-lived `idle in transaction` sessions deserve immediate investigation.

---

## Transaction Duration

A transaction that takes 10 seconds may be problematic even when its SQL statements are individually fast.

Track:

```text
transaction duration
lock wait duration
query execution duration
```

Separately.

This allows you to distinguish:

```text
slow query
```

from:

```text
fast query + long lock wait
```

and:

```text
fast queries + oversized transaction
```

---

## Connection Pool Amplification

Lock contention can propagate into the application connection pool.

Example:

```text
DB row locked
    ↓
20 requests wait
    ↓
20 connections occupied
    ↓
pool capacity decreases
    ↓
new requests wait for connections
    ↓
API latency increases
```

Eventually:

```text
connection pool exhaustion
```

can occur even though PostgreSQL itself has not reached its maximum connection count.

This is why application pool metrics and database lock metrics should be examined together.

---

## Queueing Effect

Lock contention creates queueing.

Conceptually:

```text
Incoming requests
       ↓
   ┌───────┐
   │ lock  │
   └───┬───┘
       ↓
 ┌───────────┐
 │ waiters   │
 └─────┬─────┘
       ↓
  lock released
       ↓
transactions proceed
```

As concurrency increases, wait time can grow non-linearly.

This often appears first in p95/p99 latency rather than average latency.

---

## Little's Law and Contention

A useful capacity relationship is:

```text
L = λ × W
```

where:

- `L` = average work in the system.
- `λ` = throughput.
- `W` = average time in the system.

If lock contention increases transaction time, `W` increases.

For a fixed request rate, the number of concurrent connections required also increases.

This explains why lock contention can indirectly exhaust connection pools.

---

## Hot Counter Example

Suppose an application maintains:

```sql
UPDATE app.statistics
SET request_count = request_count + 1
WHERE id = 1;
```

At low traffic this is simple and reliable.

At very high traffic, every request targets the same row.

Possible alternatives include:

```text
Per-worker counters
        ↓
periodic aggregation
```

or:

```text
sharded counter rows
        ↓
aggregate on read
```

The correct design depends on whether the count must be immediately exact.

Do not introduce distributed complexity unless the hot row has actually become a bottleneck.

---

## Queue Serialization

Sometimes contention is a consequence of a business rule that inherently requires ordering.

For example:

```text
account 42
    ↓
operation A
    ↓
operation B
    ↓
operation C
```

Instead of allowing hundreds of database transactions to compete for the same row, work can be serialized through a queue keyed by the resource.

Kafka partitioning, SQS FIFO-style designs, or application-level scheduling can sometimes move serialization out of the database.

The trade-off is increased architectural complexity and potentially greater processing latency.

---

## Redis and Lock Contention

Redis is sometimes used to reduce database contention for counters, rate limits, or ephemeral coordination.

For example:

```text
Request
   ↓
Redis atomic operation
   ↓
periodic durable aggregation
   ↓
PostgreSQL
```

This can improve throughput for suitable workloads.

However, Redis does not replace transactional database correctness.

If a value represents a durable business invariant, the database may still need to enforce it.

Avoid moving a consistency requirement to Redis merely to avoid a database lock.

---

## Optimistic Concurrency

Not every contention problem requires pessimistic locking.

A version column can detect concurrent modifications:

```sql
UPDATE app.documents
SET
    content = $1,
    version = version + 1
WHERE id = $2
  AND version = $3;
```

If zero rows are affected:

```text
concurrent modification detected
```

The application can return a conflict or reload state.

Optimistic concurrency is useful when conflicts are relatively rare and transactions would otherwise remain open for long periods.

---

## Pessimistic vs Optimistic Concurrency

| Approach | Mechanism | Best for |
|---|---|---|
| Pessimistic | Lock before modifying | High-value serialized workflows |
| Optimistic | Detect conflicting versions | Low/moderate conflict editing |
| Atomic SQL | Encode invariant in one statement | Simple state changes |
| Queue serialization | Serialize outside DB | Naturally ordered workloads |

A senior design chooses based on conflict frequency, correctness requirements, and workload characteristics.

---

## Django and Lock Contention

Django exposes PostgreSQL row locking through:

```python
select_for_update()
```

Example:

```python
from django.db import transaction

with transaction.atomic():
    order = (
        Order.objects
        .select_for_update()
        .get(pk=order_id)
    )

    order.status = "processing"
    order.save(update_fields=["status"])
```

The transaction should do only the work required for the state transition.

Avoid:

```python
with transaction.atomic():
    order = Order.objects.select_for_update().get(pk=order_id)
    call_external_api()
    generate_large_report()
    order.status = "processing"
    order.save()
```

The lock lifetime becomes coupled to unrelated work.

---

## FastAPI and SQLAlchemy

The same principles apply with SQLAlchemy.

```python
with Session(engine) as session:
    with session.begin():
        order = (
            session.query(Order)
            .filter(Order.id == order_id)
            .with_for_update()
            .one()
        )

        order.status = "processing"
```

The service layer should make transaction ownership explicit.

Repository abstractions should not hide expensive or long-lived locking behavior.

---

## Microservices and Shared Databases

Lock contention can become difficult to diagnose when multiple services share one PostgreSQL database.

For example:

```text
Order Service ──┐
                ├── PostgreSQL
Billing Service ┘
```

Both services may independently modify the same tables.

A change in one service can therefore increase contention in another.

Database ownership boundaries reduce this coupling:

```text
Order Service   → Order DB
Billing Service → Billing DB
```

with events or APIs for cross-service coordination.

---

## Background Worker Contention

Celery workers can create significant database contention.

Example:

```text
100 workers
    ↓
same table
    ↓
same hot rows
    ↓
lock queue
```

Increasing worker concurrency can make throughput worse.

Tune:

- Worker concurrency.
- Batch size.
- Transaction size.
- Lock scope.
- Queue partitioning.
- Database connection pool size.

Measure throughput and lock waits together.

---

## Read Workloads and Lock Contention

PostgreSQL's MVCC allows many ordinary reads to coexist with writes, but some read operations can still participate in locking.

Explicit locking reads such as:

```sql
SELECT ...
FOR UPDATE;
```

are fundamentally different from ordinary:

```sql
SELECT ...
```

Do not add `FOR UPDATE` by default.

Use it when the business operation requires pessimistic coordination.

---

## Large Queries and Lock Contention

A transaction can hold locks while executing unrelated expensive work.

For example:

```sql
BEGIN;

UPDATE app.orders
SET status = 'processing'
WHERE id = $1;

SELECT ...
FROM large_table
JOIN another_large_table ...
;

COMMIT;
```

The expensive query extends the transaction lifetime.

Better:

```text
prepare expensive read
    ↓
short transaction
    ↓
update state
    ↓
commit
```

when the consistency model permits it.

---

## Large Batch Updates

This can create extensive lock duration:

```sql
UPDATE app.orders
SET status = 'archived'
WHERE created_at < $1;
```

on a very large table.

If the operation does not need to be atomic across every row, bounded batches can reduce contention:

```text
batch 1 → commit
batch 2 → commit
batch 3 → commit
```

But batching changes transaction semantics.

It should not be used when the business invariant requires all rows to change atomically.

---

## Partitioning and Contention

Partitioning can help when contention is distributed across partitions.

For example:

```text
tenant A → partition A
tenant B → partition B
tenant C → partition C
```

However, partitioning does not automatically solve contention if every transaction still targets:

```text
same partition
same row
```

Partitioning is primarily a data-management and query-routing technique, not a universal locking solution.

---

## Monitoring Lock Contention

Useful metrics include:

```text
lock_wait_count
lock_wait_duration
p95_transaction_duration
p99_transaction_duration
deadlock_count
lock_timeout_count
connection_pool_wait_time
database_connections
idle_in_transaction_sessions
```

Monitor these alongside:

```text
CPU
I/O
query latency
transaction rate
application request latency
worker concurrency
```

A lock problem often appears as a cross-layer latency problem.

---

## PostgreSQL Observability

Useful catalog and activity views include:

| View | Purpose |
|---|---|
| `pg_stat_activity` | Sessions, transaction state, waits, queries |
| `pg_locks` | Current lock requests and ownership |
| `pg_blocking_pids()` | Identify blocking sessions |
| `pg_stat_database` | Database-level activity |
| `pg_stat_statements` | Query execution statistics |

A practical investigation combines them instead of relying on one view.

---

## Logging Lock Waits

PostgreSQL provides:

```text
log_lock_waits
deadlock_timeout
```

These can help surface significant lock waits.

Be careful with aggressive logging in high-volume systems.

A good production observability strategy should balance:

```text
diagnostic value
+
log volume
+
storage cost
```

Use centralized logging and appropriate retention.

---

## Application-Level Observability

Capture:

```text
request_id
service
endpoint
database
transaction duration
query duration
retry count
SQLSTATE
```

Do not log sensitive query values unnecessarily.

Correlating:

```text
API request
    ↓
service log
    ↓
database session
    ↓
blocking transaction
```

can dramatically reduce incident investigation time.

---

## Security Considerations

Lock diagnostics often require access to database activity information.

Production access should follow least privilege.

Avoid giving application users:

- Superuser privileges.
- Unrestricted diagnostic access.
- DDL permissions.

Protect logs because query text and session metadata can contain sensitive information.

Also ensure that lock-management endpoints cannot be abused to intentionally create resource exhaustion.

---

## High Availability Considerations

Lock contention is usually a primary-database workload concern.

Read replicas can reduce read workload:

```text
writes → primary
reads  → replicas
```

but they do not solve contention caused by writes to the same primary row.

During failover:

- Connections may reset.
- Transactions may fail.
- Retry traffic may increase.
- Lock state from the failed primary does not simply carry over as application state.

Applications should combine HA handling with idempotent transaction retries.

---

## Cost Considerations

Lock contention can increase infrastructure cost indirectly.

For example:

```text
lock waits
    ↓
more concurrent connections
    ↓
larger application fleet
    ↓
higher database capacity
```

Scaling vertically may temporarily reduce pressure, but it does not remove serialization around a hot resource.

The cheapest long-term optimization is often to reduce unnecessary contention rather than adding more compute.

---

## Production Troubleshooting Workflow

When lock contention is suspected:

1. Confirm elevated latency or timeout rates.
2. Inspect `pg_stat_activity`.
3. Find sessions waiting on locks.
4. Identify blocking PIDs with `pg_blocking_pids()`.
5. Inspect the blocking transaction.
6. Check transaction start time.
7. Determine which table/resource is involved.
8. Check whether the blocker is `idle in transaction`.
9. Inspect recent deployments and migrations.
10. Check application transaction boundaries.
11. Check worker concurrency and batch size.
12. Determine whether a hot row is involved.
13. Check for explicit `FOR UPDATE` or advisory locks.
14. Reduce unnecessary lock duration.
15. Add or improve concurrency tests.
16. Monitor the change after deployment.

---

## Incident Example

Suppose an API normally responds in:

```text
p95 = 100 ms
```

After a deployment:

```text
p95 = 4 seconds
p99 = 10 seconds
```

Database CPU is only:

```text
35%
```

A query inspection shows normal execution times.

`pg_stat_activity` reveals:

```text
wait_event_type = Lock
```

The blocking transaction has:

```text
xact_start = 45 seconds ago
```

Investigation finds:

```text
new code
    ↓
SELECT FOR UPDATE
    ↓
external API call
    ↓
COMMIT
```

The root cause is not insufficient database CPU.

It is **lock lifetime coupled to external network latency**.

The correct fix is to redesign the transaction boundary rather than simply increasing database capacity.

---

## Common Mistakes

### Confusing Contention With Deadlocks

A waiting transaction is not necessarily part of a deadlock.

**Fix:** inspect the wait graph and determine whether a cycle exists.

### Adding More Application Instances

More workers can increase the number of transactions competing for the same resource.

**Fix:** identify the bottleneck before increasing concurrency.

### Increasing the Connection Pool

A larger pool can increase database concurrency and make hot-row contention worse.

**Fix:** size pools based on database capacity and workload characteristics.

### Using `FOR UPDATE` Everywhere

Explicit locking is sometimes added defensively without a clear correctness requirement.

**Fix:** use pessimistic locking only when the business workflow needs it.

### Holding Locks During External Calls

Network latency becomes lock duration.

**Fix:** separate durable database state transitions from external workflows.

### Ignoring `idle in transaction`

An application can hold transaction resources while doing no database work.

**Fix:** detect long-lived idle transactions and enforce appropriate transaction lifecycle controls.

### Using Timeouts as the Primary Fix

A lower `lock_timeout` may reduce waiting but can increase application failures.

**Fix:** use timeouts as guardrails while addressing the contention source.

### Using `SKIP LOCKED` Without Understanding Semantics

Skipping locked work may cause temporary starvation or ordering differences.

**Fix:** use it only when the workload explicitly supports those semantics.

### Moving Everything to Redis

Redis can reduce database load for some workloads but cannot automatically replace transactional guarantees.

**Fix:** identify whether the state is ephemeral or a durable business invariant.

### Increasing Celery Concurrency

More workers can increase contention against the same database resources.

**Fix:** benchmark worker concurrency against database lock and connection metrics.

### Ignoring Migrations

DDL can create unexpected production lock waits.

**Fix:** test migration behavior against production-sized tables and realistic concurrency.

---

## Prevention Checklist

- [ ] Keep transactions short.
- [ ] Acquire locks as late as practical.
- [ ] Release locks as early as practical.
- [ ] Avoid network calls inside transactions.
- [ ] Avoid unnecessary `FOR UPDATE`.
- [ ] Use atomic SQL for simple invariants.
- [ ] Establish deterministic lock ordering.
- [ ] Control hot-row access.
- [ ] Use `NOWAIT` when immediate conflict is preferable.
- [ ] Use `SKIP LOCKED` only for suitable queue semantics.
- [ ] Review advisory lock usage.
- [ ] Monitor `idle in transaction`.
- [ ] Monitor lock wait duration.
- [ ] Monitor transaction duration.
- [ ] Monitor connection-pool wait time.
- [ ] Test concurrent workflows.
- [ ] Test migrations under load.
- [ ] Bound transaction sizes for batch work when semantics permit.
- [ ] Correlate database waits with application requests.
- [ ] Treat recurring contention as an architecture problem.

---

## Interview Traps

### What Is Lock Contention?

Lock contention occurs when concurrent transactions need conflicting locks and one or more must wait.

### Is Lock Contention a Database Error?

Not necessarily. Waiting for a lock is normal database behavior. It becomes a problem when waits are long or frequent enough to affect throughput and latency.

### What Is the Difference Between Contention and Deadlock?

Contention can eventually resolve when the lock holder commits. A deadlock contains a circular dependency and requires PostgreSQL to abort one transaction.

### Does PostgreSQL MVCC Eliminate Locking?

No. MVCC improves concurrent visibility and reduces many reader/writer conflicts, but PostgreSQL still uses locks for writes, explicit row locking, DDL, advisory locks, and other coordination.

### Why Can a Fast Query Cause High Latency?

The query may spend most of its time waiting for a lock rather than executing.

### Why Can Increasing the Connection Pool Make Contention Worse?

More connections allow more concurrent transactions to compete for the same database resources, increasing queue depth around hot rows.

### How Do You Find the Blocking Transaction?

Use `pg_stat_activity` together with:

```sql
pg_blocking_pids(pid)
```

and inspect the corresponding session.

### How Do You Reduce Lock Contention?

Reduce transaction duration, minimize lock scope, avoid unnecessary pessimistic locking, use atomic SQL, control hot resources, and serialize work at an appropriate architectural layer.

### Can Read Replicas Fix Write Lock Contention?

No. Replicas can offload suitable reads, but writes still contend on the primary.

### Can Partitioning Fix Lock Contention?

Sometimes, if it distributes independent workloads across different physical partitions. It does not solve contention when many transactions still target the same row or resource.

### Why Is `idle in transaction` Dangerous?

The application may have stopped doing database work while leaving the transaction open, allowing transaction resources and locks to remain active longer than intended.

### What Is the Senior-Level Way to Think About Lock Contention?

Treat it as a queueing and architecture problem:

```text
concurrency
    ↓
resource conflicts
    ↓
lock acquisition
    ↓
wait time
    ↓
connection utilization
    ↓
tail latency
    ↓
system throughput
```

The best solution is usually to reduce unnecessary serialization rather than simply adding more infrastructure.

## Key Takeaways

- **Lock contention is waiting, not necessarily deadlock:** contention occurs when transactions compete for conflicting resources; it becomes harmful when wait time degrades throughput and tail latency.
- **Transaction duration determines lock impact:** short, focused transactions reduce the time other requests spend waiting and prevent database contention from spreading into connection pools.
- **Hot rows are scalability bottlenecks:** atomic SQL improves correctness, but heavily contended single resources may require sharded counters, queue serialization, workload partitioning, or other architectural changes.
- **Diagnose the blocker, not just the waiter:** combine `pg_stat_activity`, `pg_locks`, `pg_blocking_pids()`, transaction duration, and application logs to reconstruct the contention path.
- **Treat contention as a system-design problem:** more workers, larger connection pools, and more application instances can amplify contention; optimize concurrency and resource ownership before scaling out.