# 21- Deadlocks

## Overview

A **deadlock** occurs when two or more concurrent transactions permanently wait for one another because each transaction holds a resource required by another transaction.

The classic pattern is:

```text
Transaction A                    Transaction B
     │                                │
     ├── locks Row 1                 │
     │                                ├── locks Row 2
     │                                │
     ├── waits for Row 2 ────────────┤
     │                                ├── waits for Row 1
     │                                │
     └──────────── DEADLOCK ──────────┘
```

Deadlocks are a normal possibility in transactional databases. A production system should therefore be designed to **minimize deadlocks, detect them, handle aborted transactions safely, and retry appropriate operations**.

Deadlocks are different from ordinary lock contention:

| Situation | Description |
|---|---|
| Lock contention | A transaction waits because another transaction currently holds a conflicting lock |
| Deadlock | Transactions form a circular dependency and cannot make progress |
| Long-running transaction | A transaction holds locks or snapshots for an unnecessarily long time |
| Timeout | A wait exceeds a configured limit; this does not necessarily imply a deadlock |

A senior backend engineer should treat deadlocks as a concurrency-design problem rather than simply a database error.

## Why Deadlocks Exist

Deadlocks arise because transactions need to maintain atomicity while concurrently accessing shared resources.

Consider two accounts:

```text
Account A
Account B
```

Transaction 1 transfers from A to B:

```text
lock A
lock B
update A
update B
```

Transaction 2 transfers from B to A:

```text
lock B
lock A
update B
update A
```

If both transactions execute concurrently:

```text
T1                          T2
│                           │
├── lock A                  │
│                           ├── lock B
│                           │
├── request B ──────────────┤
│                           ├── request A
│                           │
└────── waiting ◄───────────┘
```

Neither transaction can proceed.

The important insight is:

> Deadlocks are usually caused by **inconsistent resource acquisition order**.

## Conditions for a Deadlock

Deadlocks are traditionally described using four necessary conditions:

| Condition | Meaning |
|---|---|
| Mutual exclusion | A resource can be held exclusively |
| Hold and wait | A transaction holds one resource while waiting for another |
| No preemption | A resource cannot simply be taken away from the transaction |
| Circular wait | Transactions form a cycle of dependencies |

For database transactions, the circular wait is usually the most useful condition to reason about operationally.

For example:

```text
T1 holds A → waits for B
T2 holds B → waits for A
```

This creates:

```text
T1 → T2 → T1
```

which is a cycle.

## Deadlock vs Lock Contention

These concepts are frequently confused.

### Lock Contention

```text
T1:
  holds Row A

T2:
  waits for Row A

T1:
  commits

T2:
  continues
```

There is waiting, but progress is possible.

### Deadlock

```text
T1:
  holds Row A
  waits for Row B

T2:
  holds Row B
  waits for Row A
```

Neither transaction can make progress without another transaction releasing a resource.

The database must break the cycle by aborting one transaction.

## A Practical Deadlock Example

Suppose an application transfers money between accounts.

Transaction A:

```sql
BEGIN;

SELECT id, balance
FROM accounts
WHERE id = 10
FOR UPDATE;

SELECT id, balance
FROM accounts
WHERE id = 20
FOR UPDATE;

-- perform transfer

COMMIT;
```

Transaction B does the reverse:

```sql
BEGIN;

SELECT id, balance
FROM accounts
WHERE id = 20
FOR UPDATE;

SELECT id, balance
FROM accounts
WHERE id = 10
FOR UPDATE;

-- perform transfer

COMMIT;
```

The sequence can become:

```text
T1                          T2
│                           │
├─ lock account 10         │
│                           ├─ lock account 20
│                           │
├─ wait for 20             │
│                           ├─ wait for 10
│                           │
└──────── DEADLOCK ─────────┘
```

The database detects the cycle and aborts one transaction.

## Preventing Deadlocks with Consistent Ordering

The most important prevention technique is to acquire multiple locks in a consistent order.

Instead of:

```sql
-- Transaction A
SELECT *
FROM accounts
WHERE id = 10
FOR UPDATE;

SELECT *
FROM accounts
WHERE id = 20
FOR UPDATE;
```

and:

```sql
-- Transaction B
SELECT *
FROM accounts
WHERE id = 20
FOR UPDATE;

SELECT *
FROM accounts
WHERE id = 10
FOR UPDATE;
```

both transactions should lock the smaller ID first:

```sql
SELECT id, balance
FROM accounts
WHERE id IN (10, 20)
ORDER BY id
FOR UPDATE;
```

Now both transactions follow:

```text
10 → 20
```

rather than:

```text
T1: 10 → 20
T2: 20 → 10
```

This removes the circular dependency in this class of workload.

## Lock Ordering as a System-Wide Rule

Consistent ordering should not be limited to one function.

For example, if the application works with:

```text
users
orders
inventory
payments
```

establish a documented ordering convention when transactions need multiple resources:

```text
users → orders → inventory → payments
```

Every transaction touching multiple resources should follow the same order whenever possible.

This is particularly important in large codebases because two independent service methods can otherwise introduce incompatible lock sequences.

## Deadlocks with Different Resources

Deadlocks are not limited to two rows.

Consider:

```text
T1:
  lock A
  lock B
  wait for C

T2:
  lock C
  wait for A
```

The dependency graph becomes:

```text
T1 ──waits for──► T2
 ▲                │
 │                │
 └────waits───────┘
```

More transactions can participate:

```text
T1 → T2 → T3 → T1
```

The database must detect the cycle regardless of its size.

## Deadlocks and Table Locks

Table-level locks can also participate in deadlocks.

For example:

```text
T1:
  lock Table A
  request Table B

T2:
  lock Table B
  request Table A
```

Result:

```text
T1 → Table B
      ▲
      │
      │
Table A
      │
      ▼
     T2
```

Using broader locks increases the number of operations that can conflict, making careful lock design even more important.

## Deadlocks and Foreign Keys

Foreign-key relationships can introduce locking dependencies that are not obvious from application code.

For example:

```text
Parent row
    ▲
    │ foreign key
    │
Child row
```

Updates, deletes, inserts, and referential-integrity checks can require internal locking.

Therefore, a transaction that appears to update only one logical object may interact with other rows through:

- Foreign keys.
- Unique constraints.
- Indexes.
- Triggers.
- Cascading operations.
- Database-specific implementation details.

This is one reason production deadlocks should be diagnosed from database lock information rather than inferred solely from application source code.

## Deadlocks and Indexes

Indexes do not automatically prevent deadlocks.

However, indexes can significantly affect:

- Which rows are scanned.
- How many rows are touched.
- Query duration.
- Lock duration.
- The amount of contention.

A poorly indexed query can scan many rows before modifying the target rows, increasing the period during which locks and transactional resources are involved.

For example:

```sql
UPDATE orders
SET status = 'processing'
WHERE customer_id = 42
  AND status = 'pending';
```

If this query is performance-critical, an appropriate index may reduce the amount of work required.

The exact index design depends on workload and query patterns.

## Transaction Duration and Deadlocks

Long transactions increase the window during which a deadlock can form.

Avoid:

```text
BEGIN
  ↓
lock row
  ↓
HTTP request
  ↓
wait for remote service
  ↓
large computation
  ↓
another database query
  ↓
COMMIT
```

Prefer:

```text
Validate
  ↓
Perform external work if possible
  ↓
BEGIN
  ↓
Acquire required locks
  ↓
Perform short critical section
  ↓
COMMIT
```

A shorter transaction does not mathematically eliminate deadlocks, but it reduces lock lifetime and therefore reduces contention and the probability of problematic interactions.

## Deadlocks in Web Applications

Consider a REST API:

```text
Client
  │
  ▼
Nginx / Load Balancer
  │
  ▼
FastAPI / Django
  │
  ▼
Database connection pool
  │
  ▼
PostgreSQL
```

Suppose two API requests concurrently modify related resources.

```text
Request A ──► Transaction A
                 │
                 ├── Lock X
                 └── Wait Y

Request B ──► Transaction B
                 │
                 ├── Lock Y
                 └── Wait X
```

The database eventually aborts one transaction.

The application must recognize that the transaction failed and decide whether the operation is safely retryable.

## Deadlocks in Django

Django's transaction management makes it straightforward to define transaction boundaries:

```python
from django.db import transaction

with transaction.atomic():
    account_ids = sorted([source_id, destination_id])

    accounts = {
        account.id: account
        for account in (
            Account.objects
            .select_for_update()
            .filter(id__in=account_ids)
        )
    }

    source = accounts[source_id]
    destination = accounts[destination_id]

    if source.balance < amount:
        raise InsufficientFundsError

    source.balance -= amount
    destination.balance += amount

    source.save(update_fields=["balance"])
    destination.save(update_fields=["balance"])
```

The important design properties are:

- One transaction.
- Deterministic lock ordering.
- Short critical section.
- No external network calls while locks are held.

## Deadlock Handling in Django

A deadlock can cause the database transaction to fail.

Retrying the **entire transaction** is generally safer than trying to continue executing inside a transaction that has already failed.

Conceptually:

```python
import time

from django.db import OperationalError, transaction


def transfer_with_retry(source_id, destination_id, amount, retries=3):
    for attempt in range(retries):
        try:
            with transaction.atomic():
                # Acquire all required locks in deterministic order.
                ids = sorted([source_id, destination_id])

                accounts = {
                    account.id: account
                    for account in (
                        Account.objects
                        .select_for_update()
                        .filter(id__in=ids)
                    )
                }

                source = accounts[source_id]
                destination = accounts[destination_id]

                if source.balance < amount:
                    raise InsufficientFundsError

                source.balance -= amount
                destination.balance += amount

                source.save(update_fields=["balance"])
                destination.save(update_fields=["balance"])

            return

        except OperationalError:
            if attempt == retries - 1:
                raise

            time.sleep(0.05 * (2 ** attempt))
```

In production, do not blindly catch every `OperationalError` and retry it. Retry logic should be based on the database driver's/database backend's specific transient error classification.

A retry should also be:

- Bounded.
- Observable.
- Idempotency-aware.
- Applied to the whole transaction.
- Used only where repeating the business operation is safe.

## Deadlocks and Retry Safety

Retrying a database transaction is not automatically safe.

Consider an API:

```text
POST /payments
```

If the first attempt performs an external side effect before the database deadlock occurs:

```text
Payment provider charged card
        ↓
Database transaction deadlocks
        ↓
Application retries
        ↓
Payment provider charged again
```

The database transaction may be retryable while the **overall business operation is not**.

Use appropriate patterns such as:

- Idempotency keys.
- Unique business-operation identifiers.
- Transactional outbox patterns.
- Provider-side idempotency where available.
- Explicit state machines.

Database transaction retries should not be confused with end-to-end request retries.

## PostgreSQL Deadlock Detection

PostgreSQL detects deadlocks automatically rather than allowing transactions to wait forever.

A deadlock can produce an error similar to:

```text
ERROR: deadlock detected
DETAIL: Process ... waits for ...
Process ... waits for ...
HINT: See server log for query details.
```

The exact diagnostic output depends on PostgreSQL version and configuration.

The database resolves the deadlock by aborting one transaction, allowing the remaining transaction to proceed.

This means:

> A deadlock is expected to terminate at least one transaction involved in the cycle.

The application should therefore treat deadlock errors as transaction failures.

## Investigating PostgreSQL Deadlocks

Start with active sessions:

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
WHERE state <> 'idle'
ORDER BY xact_start;
```

Inspect lock information:

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
ORDER BY pid;
```

For a more complete investigation, correlate:

```text
pg_stat_activity
       +
pg_locks
       +
database logs
       +
application logs
       +
request trace IDs
```

This allows you to reconstruct:

```text
HTTP request
    ↓
application transaction
    ↓
SQL statement
    ↓
lock acquisition
    ↓
blocking relationship
    ↓
deadlock
    ↓
aborted transaction
```

## Monitoring Deadlocks

Deadlocks should be observable as a production signal.

Monitor:

| Signal | Why it matters |
|---|---|
| Deadlock count | Measures concurrency failures |
| Transaction retry count | Shows how often applications recover |
| Lock wait duration | Detects increasing contention |
| Transaction duration | Long transactions increase risk |
| Database errors | Detects failed transactions |
| Request latency | Shows user-facing impact |
| Connection pool utilization | Retries and waits can consume connections |

A useful alerting strategy distinguishes:

```text
Occasional deadlock
        ↓
expected transient condition
        ↓
bounded retry
```

from:

```text
Deadlocks increasing rapidly
        ↓
systemic concurrency problem
        ↓
investigate lock ordering / query / schema design
```

## Deadlock Logging

Production database logs should retain enough information to investigate deadlocks.

For PostgreSQL, appropriate logging configuration can help expose:

- Deadlock reports.
- Slow statements.
- Transaction behavior.
- Relevant session information.

Avoid enabling extremely verbose database logging indiscriminately in high-volume production environments because logging itself can introduce storage and performance costs.

Correlate database events with application request IDs or trace IDs where possible.

## Performance Impact

Deadlocks affect performance in several ways.

### Direct Cost

The aborted transaction has already consumed resources:

```text
CPU
I/O
locks
connection
application work
```

All work that must be retried is additional work.

### Indirect Cost

Retries can amplify load:

```text
High contention
    ↓
Deadlocks
    ↓
Retries
    ↓
More database operations
    ↓
Higher contention
    ↓
More deadlocks
```

This can create a feedback loop.

Therefore, retry policies should be bounded and use appropriate backoff.

## Exponential Backoff

When retries are appropriate, avoid immediately retrying all failed transactions simultaneously.

Prefer bounded exponential backoff with jitter:

```text
Attempt 1 → immediate
Attempt 2 → small delay
Attempt 3 → larger delay
Attempt 4 → larger bounded delay
```

Conceptually:

```text
delay = min(base × 2^attempt + jitter, max_delay)
```

Jitter prevents many clients from retrying at exactly the same moment.

## Deadlocks in Distributed Systems

Database deadlocks should not be confused with distributed-system deadlocks.

A database deadlock might be:

```text
Transaction A → Row B
Transaction B → Row A
```

A distributed workflow might instead involve:

```text
Service A → waits for Service B
Service B → waits for Service C
Service C → waits for Service A
```

The latter is a distributed dependency cycle and requires different mechanisms.

In microservice architectures, avoid holding a database transaction open while synchronously waiting on another service:

```text
BEGIN
  ↓
lock database resource
  ↓
call Service B
  ↓
Service B calls Service C
  ↓
Service C waits for Service A
```

This can combine database contention with distributed dependency problems.

Prefer patterns such as:

- Transactional outbox.
- Asynchronous messaging.
- Explicit workflow/state machines.
- Idempotent consumers.
- Saga-style coordination where appropriate.

## Common Mistakes

### Acquiring Locks in Arbitrary Order

Bad:

```text
Function A: lock 10 → 20
Function B: lock 20 → 10
```

Better:

```text
All functions: lock 10 → 20
```

### Catching the Error but Continuing the Transaction

Once the database transaction has failed, application code should not assume the transaction remains usable.

Retry the complete transaction when retry is appropriate.

### Retrying Indefinitely

Bad:

```text
deadlock → retry
deadlock → retry
deadlock → retry
...
```

This can create a retry storm.

Use bounded retries and backoff.

### Retrying Non-Idempotent Operations

A database transaction may be safe to retry while an external side effect is not.

Design business operations with explicit idempotency where necessary.

### Holding Locks During External Calls

Bad:

```text
BEGIN
SELECT ... FOR UPDATE
HTTP request
wait
COMMIT
```

The HTTP request can hold database resources hostage.

### Locking More Rows Than Necessary

Overly broad locking increases the conflict graph.

Prefer the smallest resource set that protects the invariant.

### Ignoring Database Constraints

Locks are not a replacement for:

- Unique constraints.
- Foreign keys.
- Check constraints.
- Exclusion constraints where appropriate.

Use database constraints to enforce invariants whenever possible.

### Assuming Deadlocks Are Always Bugs

Some deadlocks are an unavoidable consequence of complex concurrent workloads.

The engineering goal is not necessarily zero deadlocks.

The goal is:

```text
minimize
    +
detect
    +
handle safely
    +
observe
    +
eliminate systemic causes
```

## Production Best Practices

1. Establish a deterministic lock acquisition order.
2. Keep transactions as short as practical.
3. Avoid external network calls while holding database locks.
4. Lock only the rows or resources required by the invariant.
5. Prefer atomic SQL when it eliminates unnecessary read-modify-write locking.
6. Use database constraints for hard data invariants.
7. Configure appropriate statement and lock timeouts.
8. Detect and classify deadlock errors explicitly.
9. Retry the complete transaction when the operation is safely retryable.
10. Use bounded exponential backoff with jitter.
11. Make externally visible operations idempotent when retries are possible.
12. Monitor deadlocks, lock waits, transaction duration, and retry rates.
13. Investigate recurring deadlocks rather than masking them with retries.
14. Test concurrent transaction paths under realistic load.
15. Document lock ordering conventions for shared domain resources.

## Concurrency Testing

Sequential tests rarely expose deadlocks.

A useful concurrency test intentionally executes conflicting transactions in parallel.

Conceptually:

```text
Worker A                       Worker B
   │                              │
   ├── begin                      ├── begin
   ├── lock resource A            ├── lock resource B
   ├── request resource B         ├── request resource A
   │                              │
   └──────────── deadlock ────────┘
```

Production-like testing should cover:

- Concurrent updates.
- Opposite resource ordering.
- Multiple workers.
- Lock contention.
- Transaction retries.
- Timeout behavior.
- Connection pool pressure.
- Failure during transaction execution.

For backend services using Kubernetes, test with multiple application replicas. A single-process test using an in-memory mutex does not reproduce distributed application behavior.

## Deadlock Prevention Checklist

Before deploying a transactional workflow, ask:

- Does it modify multiple rows?
- Does it lock multiple resources?
- Is the lock order deterministic?
- Can another code path acquire those resources in a different order?
- Are external calls made while the transaction is open?
- Can the transaction become long-running?
- Is the operation safely retryable?
- Are retries bounded?
- Is jitter used?
- Are database constraints enforcing the invariant?
- Are deadlocks and retries observable?
- Has the workflow been tested under concurrent load?

## Interview Traps

### Is a Deadlock the Same as Lock Contention?

No. Lock contention is ordinary waiting for a conflicting lock. A deadlock is a circular dependency in which transactions wait on one another and cannot make progress.

### How Does a Database Resolve a Deadlock?

The database detects the cycle and aborts one of the participating transactions. The remaining transaction can then continue.

### What Is the Most Common Way to Prevent Deadlocks?

Acquire multiple resources in a **consistent deterministic order**.

### Should You Always Retry a Deadlock?

No. Retry only when the operation is safely retryable and the failure is classified as transient. The retry should generally encompass the entire transaction.

### Why Use Exponential Backoff?

Immediate retries can cause many competing transactions to retry simultaneously, increasing contention. Backoff and jitter reduce synchronized retry pressure.

### Does `SELECT FOR UPDATE` Eliminate Deadlocks?

No. It can actually participate in deadlocks if multiple transactions acquire locks in inconsistent orders.

### Can Database Indexes Prevent Deadlocks?

Not directly. Indexes can reduce query work and lock duration, which may reduce contention, but they do not guarantee deadlock prevention.

### Why Is Lock Ordering So Important?

Because inconsistent ordering creates circular waits:

```text
T1: A → B
T2: B → A
```

Consistent ordering changes both transactions to:

```text
T1: A → B
T2: A → B
```

so one transaction waits for the other rather than creating a cycle.

## Key Takeaways

- **Deadlocks occur when concurrent transactions form a circular dependency over conflicting resources.**
- **The strongest general prevention technique is deterministic, consistent lock acquisition order across all relevant code paths.**
- **Deadlocks should be treated as transaction failures and retried only when the complete business operation is safely retryable.**
- **Short transactions, narrow lock scope, appropriate indexing, and avoiding external calls while holding locks reduce contention and deadlock risk.**
- **Recurring deadlocks require investigation using database lock information, logs, traces, and application-level transaction behavior rather than being hidden by retries.**