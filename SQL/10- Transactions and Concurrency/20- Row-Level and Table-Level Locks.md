# 20- Row-Level and Table-Level Locks

## Overview

Database locks coordinate concurrent transactions that access shared database resources. The most important distinction for application developers is **lock granularity**:

- **Row-level locks** protect individual rows or small sets of rows.
- **Table-level locks** protect a table as a broader resource.

Lock granularity directly affects concurrency. A narrow row-level lock can allow unrelated requests to continue, while a broad table-level lock can serialize large portions of an application's workload.

In production systems, locking is not simply a correctness mechanism. It is also a **latency, throughput, availability, and scalability concern**.

A useful mental model is:

```text
Transaction
    │
    ├── identifies resource
    │
    ├── requests lock
    │
    ├── database checks lock compatibility
    │
    ├── granted ─────────► access resource
    │
    └── conflicting ─────► wait / fail
                              │
                              ▼
                       lock released
```

The correct locking strategy depends on the database engine, isolation level, transaction boundary, workload, and business invariant being protected.

## Why Lock Granularity Matters

Suppose an API processes a single account:

```sql
UPDATE accounts
SET balance = balance - 100
WHERE id = 42;
```

Ideally, concurrent work against account `43` should not need to wait for work against account `42`.

A row-level locking strategy provides this isolation:

```text
Account 42 ── locked ──► Request A

Account 43 ── available ──► Request B

Account 44 ── available ──► Request C
```

A table-level lock can instead create much broader contention:

```text
Accounts table
      │
      ├── Account 42
      ├── Account 43
      ├── Account 44
      └── Account 45

        ▲
        │
   broad table lock
        │
        ▼
many operations affected
```

The narrower the resource being protected, the greater the potential concurrency—provided the narrower scope still protects the required invariant.

## Row-Level Locks

### What They Are

A row-level lock coordinates concurrent access to specific rows.

For example, PostgreSQL supports explicit row-locking clauses such as:

```sql
SELECT *
FROM accounts
WHERE id = 42
FOR UPDATE;
```

The transaction is requesting a row-level lock appropriate for a transaction that intends to modify the selected row.

A concurrent transaction attempting a conflicting operation may have to wait.

### Why They Exist

Row-level locks allow transactions to serialize operations on the same logical resource without unnecessarily blocking unrelated rows.

This is particularly useful for:

- Account balances.
- Inventory quantities.
- Order state transitions.
- Resource allocation.
- Job claiming.
- Seat or capacity allocation.
- Other read-modify-write workflows.

### When to Use Them

Use explicit row-level locking when an operation needs to:

1. Read current state.
2. Make a decision based on that state.
3. Prevent a conflicting transaction from changing that state.
4. Perform a related modification.
5. Commit the entire operation atomically.

Example:

```sql
BEGIN;

SELECT quantity
FROM inventory
WHERE product_id = 42
FOR UPDATE;

-- Validate quantity in the application or transaction.

UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 42;

COMMIT;
```

### Advantages

- High concurrency for independent rows.
- Narrow contention scope.
- Suitable for transactional business invariants.
- Works naturally with database transactions.
- Avoids serializing an entire table unnecessarily.

### Limitations

- Many concurrent requests can still contend on the same row.
- Locks consume database resources.
- Long transactions can hold locks for long periods.
- Multiple row locks can participate in deadlocks.
- Exact semantics differ across database engines.

## Table-Level Locks

### What They Are

A table-level lock coordinates access against a table as a whole rather than a particular row.

PostgreSQL, for example, supports explicit table locking:

```sql
LOCK TABLE accounts IN ACCESS EXCLUSIVE MODE;
```

This is substantially broader than:

```sql
SELECT *
FROM accounts
WHERE id = 42
FOR UPDATE;
```

Table locks are appropriate only when the operation genuinely requires table-wide coordination.

### Why They Exist

Some operations cannot be safely modeled as a single-row operation.

Table-level locks can be useful for:

- Certain schema or maintenance operations.
- Explicit administrative coordination.
- Operations requiring broad table protection.
- Specialized batch or migration workflows.

They should not be used merely because they are simpler to reason about.

### Advantages

- Strong and straightforward coordination.
- Useful when an operation genuinely affects the table as a whole.
- Can simplify specialized maintenance operations.

### Limitations

- Significantly reduces concurrency.
- Can block unrelated application operations.
- Can create large lock queues.
- Can cause severe latency spikes.
- Can contribute to connection pool exhaustion.
- Incorrect use can turn a highly concurrent service into a serialized workload.

## Row-Level vs Table-Level Locks

| Property | Row-Level Lock | Table-Level Lock |
|---|---|---|
| Scope | Individual rows | Entire table/resource |
| Concurrency | Higher | Lower |
| Contention | Usually narrower | Potentially broad |
| Typical application use | Common | Relatively uncommon |
| Hotspot risk | Specific rows | Entire table |
| Deadlock risk | Possible | Possible |
| Latency impact | Usually localized | Potentially system-wide |
| Best suited for | Business resource coordination | Broad maintenance/administrative operations |
| Scalability | Generally better | Generally worse |

## PostgreSQL Row-Level Locking

PostgreSQL provides several row-level locking modes:

```sql
FOR UPDATE
FOR NO KEY UPDATE
FOR SHARE
FOR KEY SHARE
```

These are not interchangeable.

A simplified view:

| Clause | Typical purpose |
|---|---|
| `FOR UPDATE` | Strong row lock for a transaction that may update the row |
| `FOR NO KEY UPDATE` | Protect against stronger row modifications while allowing some compatible operations |
| `FOR SHARE` | Shared row-level protection |
| `FOR KEY SHARE` | Protect key-related aspects of a row |

For most backend application workflows involving a read-modify-write operation, `FOR UPDATE` is the most commonly encountered explicit row lock.

The exact conflict relationships should be understood from the database's lock matrix rather than inferred from the clause names alone.

## PostgreSQL Table Locking

PostgreSQL has multiple table-level lock modes rather than one generic table lock.

Examples include:

```sql
LOCK TABLE accounts IN SHARE MODE;
```

and:

```sql
LOCK TABLE accounts IN ACCESS EXCLUSIVE MODE;
```

The lock mode determines which other operations can proceed concurrently.

`ACCESS EXCLUSIVE` is particularly restrictive and should be used carefully.

A production engineer should therefore ask:

```text
What resource is being locked?
        ↓
What lock mode is requested?
        ↓
Which operations conflict with it?
        ↓
How long will it be held?
        ↓
How many requests can be affected?
```

## Explicit Row Locking with `FOR UPDATE`

A typical transactional workflow is:

```sql
BEGIN;

SELECT id, balance
FROM accounts
WHERE id = 42
FOR UPDATE;

UPDATE accounts
SET balance = balance - 100
WHERE id = 42;

COMMIT;
```

The important part is not the SQL clause by itself. The lock must be held within the appropriate transaction boundary.

```text
BEGIN
  │
  ▼
SELECT ... FOR UPDATE
  │
  ▼
Row locked
  │
  ├── validate business rules
  │
  ├── perform mutation
  │
  ▼
COMMIT / ROLLBACK
  │
  ▼
Lock released
```

A lock that is acquired outside the intended transaction boundary does not provide the same protection.

## Locking Multiple Rows

Many production operations need to lock multiple rows.

Consider transferring funds:

```sql
BEGIN;

SELECT id, balance
FROM accounts
WHERE id IN (10, 20)
ORDER BY id
FOR UPDATE;

UPDATE accounts
SET balance = balance - 100
WHERE id = 10;

UPDATE accounts
SET balance = balance + 100
WHERE id = 20;

COMMIT;
```

The `ORDER BY id` establishes a deterministic acquisition order.

Without a consistent ordering, different transactions can acquire locks in different sequences:

```text
Transaction A:
  lock Account 10
  wait for Account 20

Transaction B:
  lock Account 20
  wait for Account 10
```

This creates a deadlock cycle.

## Row Locks and MVCC

Row-level locking should not be confused with ordinary reads.

Modern relational databases commonly use **Multi-Version Concurrency Control (MVCC)**.

For example:

```sql
SELECT *
FROM accounts
WHERE id = 42;
```

does not simply mean:

```text
Acquire a shared lock
Block all writers
Read the row
```

In PostgreSQL, ordinary reads generally use MVCC visibility rules rather than acquiring a conflicting row-level lock.

An explicit locking read is different:

```sql
SELECT *
FROM accounts
WHERE id = 42
FOR UPDATE;
```

This requests row-level coordination in addition to reading the row.

This distinction is important:

| Operation | General purpose |
|---|---|
| Normal `SELECT` | Read a transactionally visible version |
| `SELECT ... FOR UPDATE` | Read and lock rows for protected transactional work |
| `UPDATE` | Modify rows and acquire required write locks |
| Table `LOCK` | Coordinate access at table level |

The exact behavior depends on the database engine and isolation level.

## Atomic SQL vs Row Locks

A common mistake is introducing explicit locks when the database can perform the operation atomically.

Consider inventory:

```sql
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 42
  AND quantity > 0;
```

The application can inspect the affected-row count:

```text
1 row affected → reservation succeeded
0 rows affected → no inventory available
```

This may be preferable to:

```text
SELECT quantity FOR UPDATE
        ↓
application checks quantity
        ↓
UPDATE
```

The general rule is:

> Prefer a single atomic database operation when it can directly enforce the invariant.

Use explicit locking when the business operation genuinely requires a multi-step transactional decision.

## Locking in Django

Django exposes row-level locking through `select_for_update()`.

```python
from django.db import transaction

with transaction.atomic():
    account = (
        Account.objects
        .select_for_update()
        .get(pk=account_id)
    )

    if account.balance < amount:
        raise InsufficientFundsError

    account.balance -= amount
    account.save(update_fields=["balance"])
```

The critical combination is:

```text
transaction.atomic()
        +
select_for_update()
        ↓
transaction-scoped row protection
```

Django also supports options such as:

```python
.select_for_update(nowait=True)
```

and:

```python
.select_for_update(skip_locked=True)
```

when supported by the configured database backend.

## Locking in SQLAlchemy and FastAPI

FastAPI itself does not provide database locking.

A SQLAlchemy application can request row-level locking through:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

statement = (
    select(Account)
    .where(Account.id == account_id)
    .with_for_update()
)

account = session.execute(statement).scalar_one()
```

The surrounding transaction must remain active while the protected operation is performed.

The architecture is:

```text
FastAPI
   │
   ▼
SQLAlchemy
   │
   ▼
Database driver
   │
   ▼
PostgreSQL
   │
   ├── MVCC
   └── Lock manager
```

## `NOWAIT`

Sometimes waiting for a lock is worse than immediately reporting a conflict.

PostgreSQL supports:

```sql
SELECT *
FROM accounts
WHERE id = 42
FOR UPDATE NOWAIT;
```

If a conflicting lock already exists, the statement fails instead of waiting.

This is useful when:

- The API has strict latency requirements.
- The caller can retry or choose another resource.
- Waiting for the resource is not acceptable.
- The application wants explicit conflict semantics.

Example workflow:

```text
Request
  ↓
Try row lock
  ↓
Available? ── Yes ──► Process
  │
  No
  ↓
Return conflict / retry
```

The application should handle the database error deliberately rather than exposing an unhandled database exception to clients.

## `SKIP LOCKED`

`SKIP LOCKED` is useful when multiple workers compete for independent work items.

Example:

```sql
SELECT id
FROM jobs
WHERE status = 'pending'
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 10;
```

Suppose:

```text
Job 1 → Worker A
Job 2 → Worker B
Job 3 → already locked
Job 4 → Worker A
Job 5 → Worker B
```

Worker A or B can skip Job 3 rather than waiting.

This is particularly useful for database-backed job claiming.

However, `SKIP LOCKED` changes the semantics from:

```text
"Wait until the next resource becomes available"
```

to:

```text
"Use currently available resources and skip locked ones"
```

That trade-off must be intentional.

## Lock Contention

Lock contention occurs when multiple transactions need conflicting locks on the same resource.

For example:

```text
Request A ─┐
Request B ─┤
Request C ─┼──► Account 42
Request D ─┘
             │
             ▼
       exclusive lock
             │
             ▼
        serialization
```

The database may have plenty of CPU available while throughput still degrades because requests are waiting for the same resource.

Common symptoms include:

- Increasing database latency.
- Increasing API latency.
- Growing connection pool utilization.
- Lock wait events.
- Request timeouts.
- Deadlocks.
- Reduced throughput.

## Hot Rows

A **hot row** is a row that receives unusually high concurrent access.

Examples:

- A global counter.
- A popular inventory item.
- A frequently modified account.
- A single job coordination record.
- A global configuration record.

For example:

```sql
UPDATE counters
SET value = value + 1
WHERE id = 1;
```

Thousands of concurrent operations against the same row can effectively serialize around that resource.

Possible architectural solutions include:

- Atomic updates.
- Batching.
- Sharded counters.
- Append-only event recording.
- Asynchronous aggregation.
- Redis counters where appropriate.
- Redesigning the data model.

The right solution depends on the consistency requirement.

## Table Locks and Migrations

Table-level locks are particularly important during schema changes and maintenance.

A migration that requires a strong table lock can interact badly with production traffic:

```text
Application traffic
       │
       ▼
Production table
       │
       ├── Request A
       ├── Request B
       ├── Request C
       └── Request D
              │
              ▼
        migration requests
        strong table lock
              │
              ▼
          requests wait
```

Before running potentially blocking DDL in production, consider:

- Table size.
- Current traffic.
- Lock requirements.
- Migration duration.
- Existing long-running transactions.
- Deployment strategy.
- Rollback strategy.
- Database observability.

For large production tables, prefer online or low-lock migration techniques supported by the specific database engine.

## Deadlocks

Both row-level and table-level locks can participate in deadlocks.

Example:

```text
Transaction A
    │
    ├── holds Row 1
    └── waits for Row 2
                  ▲
                  │
Transaction B     │
    │             │
    ├── holds Row 2
    └── waits for Row 1
```

The database can detect the cycle and abort one transaction.

### Preventing Deadlocks

Use:

- Consistent lock ordering.
- Short transactions.
- Narrow lock scope.
- Minimal unnecessary locking.
- Predictable query ordering.
- Appropriate timeout configuration.

For example:

```sql
SELECT id
FROM accounts
WHERE id IN (10, 20)
ORDER BY id
FOR UPDATE;
```

Both transactions now attempt to acquire locks in the same order.

## Lock Duration

Lock granularity and lock duration are separate design dimensions.

A row-level lock can still be dangerous if held for a long time:

```text
BEGIN
  ↓
Lock row
  ↓
Call external API
  ↓
Wait 2 seconds
  ↓
Process data
  ↓
Call another service
  ↓
COMMIT
```

The row is narrow, but the duration is long.

Prefer:

```text
Validate inputs
    ↓
Perform required external work
    ↓
BEGIN
    ↓
Acquire lock
    ↓
Validate current database state
    ↓
Mutate
    ↓
COMMIT
```

External network calls should generally not occur while holding database locks.

## Monitoring Lock Problems

For PostgreSQL, `pg_stat_activity` can reveal active sessions and wait events:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    query_start,
    query
FROM pg_stat_activity
WHERE state <> 'idle';
```

`pg_locks` can be used to investigate lock state and relationships.

Production monitoring should track:

| Metric | Why it matters |
|---|---|
| Lock wait duration | Detects contention |
| Blocked sessions | Identifies concurrency pressure |
| Deadlocks | Indicates conflicting transaction design |
| Transaction duration | Long transactions hold resources |
| Query latency | Shows user-facing impact |
| Connection pool usage | Waiting requests can consume connections |
| Lock timeout errors | Detects excessive contention |
| Idle transactions | May retain snapshots or locks/resources |

A useful debugging sequence is:

```text
API latency increases
        ↓
Database latency increases
        ↓
Check wait events
        ↓
Lock contention detected
        ↓
Identify blocked session
        ↓
Identify blocking transaction
        ↓
Inspect transaction duration/query
        ↓
Reduce contention or redesign workflow
```

## Scalability Considerations

The scalability impact of locks is primarily determined by **contention**, not simply the number of locks.

This can scale relatively well:

```text
Request A → Row 1
Request B → Row 2
Request C → Row 3
Request D → Row 4
```

This does not:

```text
Request A ─┐
Request B ─┤
Request C ─┼──► Row 1
Request D ─┘
```

Senior-level database design therefore asks:

> Which resources become serialized under peak concurrency?

A database with millions of rows can still have excellent concurrency if requests operate on independent rows. A single hot row can become a bottleneck even in an otherwise lightly loaded database.

## Reliability Considerations

Database locks are tied to transaction/session state.

If an application process crashes or a database connection terminates, the database can clean up transactional state associated with that connection.

Applications should therefore avoid implementing correctness around manual "unlock" calls.

Prefer:

```text
BEGIN
  ↓
Acquire lock
  ↓
Perform operation
  ↓
COMMIT / ROLLBACK
  ↓
Database releases transactional locks
```

This makes lock ownership part of the database transaction lifecycle.

## Security and Availability

Locking problems can become availability problems.

A faulty endpoint that keeps transactions open can hold locks and consume database connections:

```text
Bad request
   ↓
BEGIN
   ↓
Lock row/table
   ↓
Slow processing
   ↓
Transaction remains open
   ↓
Other requests wait
   ↓
Connection pool fills
   ↓
API latency increases
```

Mitigations include:

- Authentication and authorization before entering critical sections.
- Transaction timeouts.
- Lock timeouts.
- Statement timeouts.
- Connection pool limits.
- Monitoring long-running transactions.
- Avoiding external calls while holding locks.
- Keeping critical sections small.

Do not use table locks as an application-level security mechanism.

## Common Mistakes

### Locking the Entire Table for a Single-Row Operation

If the invariant concerns one account, locking the entire accounts table unnecessarily reduces concurrency.

Prefer the smallest resource that correctly protects the invariant.

### Assuming `SELECT` Automatically Means Shared Row Lock

In MVCC databases such as PostgreSQL, ordinary reads do not simply behave as traditional shared row locks.

Explicit locking syntax has different semantics.

### Using `FOR UPDATE` Everywhere

Explicit locks have a cost.

If an atomic statement can safely enforce the invariant, it may be better:

```sql
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 42
  AND quantity > 0;
```

### Holding a Row Lock During a Network Call

Never casually hold a database lock while waiting for:

- Payment providers.
- HTTP APIs.
- Kafka acknowledgements.
- Object storage.
- Another microservice.
- Human interaction.

External dependencies can be slow or unavailable.

### Acquiring Multiple Locks in Different Orders

Inconsistent ordering is a common source of deadlocks.

Use a deterministic order whenever multiple resources must be locked.

### Ignoring Hot Rows

A row-level lock does not guarantee scalability.

If every request needs the same row, the workload can still serialize.

### Assuming All Databases Implement Locks the Same Way

PostgreSQL, MySQL/InnoDB, SQL Server, and Oracle differ in:

- Lock modes.
- MVCC behavior.
- Isolation semantics.
- DDL locking.
- Row-lock behavior.
- Deadlock detection.
- Locking syntax.

Always validate concurrency assumptions against the actual production database.

### Using Application-Level Mutexes

This is insufficient in a distributed deployment:

```python
from threading import Lock

lock = Lock()
```

With multiple Kubernetes pods:

```text
Pod A → Lock A
Pod B → Lock B
Pod C → Lock C
```

These locks do not coordinate database access across pods.

Use database-level coordination or an appropriate distributed coordination mechanism when shared state crosses process boundaries.

## Production Best Practices

1. Use row-level locking for row-scoped transactional invariants.
2. Use table-level locking only when broad coordination is genuinely required.
3. Prefer atomic SQL when a business invariant can be expressed in one database statement.
4. Keep transactions short.
5. Acquire multiple locks in a deterministic order.
6. Avoid external calls while holding database locks.
7. Use `NOWAIT` when waiting is not acceptable.
8. Use `SKIP LOCKED` for appropriate concurrent worker-claiming workloads.
9. Monitor lock waits, blocking sessions, deadlocks, and long-running transactions.
10. Configure appropriate statement and lock timeouts.
11. Treat hot rows as potential scalability bottlenecks.
12. Test concurrency behavior under realistic load rather than relying only on sequential tests.
13. Use database constraints alongside locks for hard invariants such as uniqueness.
14. Make deadlock and transient transaction failures safely retryable where appropriate.

## Practical Decision Guide

| Requirement | Recommended approach |
|---|---|
| Read data normally | Ordinary `SELECT` |
| Update one row atomically | Atomic `UPDATE` |
| Read-modify-write one row | Row-level locking |
| Protect multiple related rows | Lock rows in deterministic order |
| Concurrent job claiming | `FOR UPDATE SKIP LOCKED` where appropriate |
| Do not wait for locked resource | `NOWAIT` where supported |
| Coordinate entire table | Table-level lock only when required |
| Large production schema change | Prefer database-specific online/low-lock migration strategies |
| Very hot row | Redesign or reduce contention |
| Cross-process coordination | Database/distributed coordination |
| External API interaction | Avoid holding DB locks across the call |

## Interview Traps

### Is Row-Level Locking Always Better Than Table-Level Locking?

No.

Row-level locking usually provides better concurrency, but the correct granularity depends on the operation. If an operation genuinely requires table-wide coordination, a table-level lock may be appropriate.

### Does a Row-Level Lock Prevent All Reads?

Not necessarily.

MVCC databases can allow ordinary readers to access transactionally visible row versions while another transaction holds a write-related row lock.

### Does `SELECT FOR UPDATE` Lock the Entire Table?

No. It requests row-level locking for the selected rows, subject to the database engine's semantics.

### Can Row-Level Locks Cause Deadlocks?

Yes.

Deadlocks can occur when transactions acquire multiple locks in conflicting orders.

### Why Is `ORDER BY` Important When Locking Multiple Rows?

It can establish deterministic lock acquisition order, reducing the chance that concurrent transactions acquire the same resources in different orders.

### Why Can Row-Level Locking Still Hurt Performance?

Because many transactions can contend for the same row.

```text
N requests
   ↓
same hot row
   ↓
one conflicting operation at a time
   ↓
serialization
```

Lock granularity does not eliminate contention; it limits its scope.

### Should You Use Locks Instead of Database Constraints?

No.

Locks coordinate concurrent transactions, while constraints enforce database invariants.

For example:

```sql
CREATE UNIQUE INDEX users_email_unique
ON users (email);
```

The uniqueness guarantee should belong to the database rather than relying solely on application-level locking.

### How Do You Choose Between Row and Table Locks?

Start with the invariant:

```text
What must be protected?
        ↓
One row?
        │
        ├── Yes → row-level coordination
        │
        └── No
             ↓
      Multiple rows?
             │
             ├── Yes → lock required rows consistently
             │
             └── Table-wide operation?
                    ↓
              consider table lock
```

Then evaluate transaction duration, contention, workload, and database-specific semantics.

## Key Takeaways

- **Row-level locks provide narrow transactional coordination and generally preserve much more concurrency than table-level locks.**
- **Table-level locks should be reserved for operations that genuinely require broad coordination because they can block otherwise unrelated application work.**
- **Lock granularity alone does not guarantee scalability; hot rows and long-held locks can still serialize high-volume workloads.**
- **Use deterministic lock ordering, short transactions, atomic SQL, and appropriate timeout strategies to reduce contention and deadlocks.**
- **Lock behavior is database-specific, so production concurrency designs must account for the actual engine's MVCC, isolation, lock modes, and DDL semantics.**