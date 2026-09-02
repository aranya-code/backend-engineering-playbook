# 11- Repeatable Read

## Overview

**Repeatable Read** is a transaction isolation level that provides a consistent view of data throughout a transaction. Once the transaction establishes its snapshot, subsequent reads continue to operate against that same logical view rather than observing commits made by concurrent transactions.

It is stronger than `READ COMMITTED` because it prevents non-repeatable reads. In PostgreSQL, `REPEATABLE READ` uses a transaction-level MVCC snapshot and provides stronger guarantees than the SQL standard minimally requires for this isolation level.

The central distinction is:

```text
READ COMMITTED
----------------
Statement 1 → Snapshot A
Statement 2 → Snapshot B
               ↑
       May see new commits


REPEATABLE READ
----------------
Transaction begins
       │
       ▼
Snapshot A
       │
       ├── Statement 1 → Snapshot A
       ├── Statement 2 → Snapshot A
       └── Statement 3 → Snapshot A
```

Repeatable Read is useful when multiple queries must reason about the same database state. The tradeoff is that concurrent modifications can become harder to complete successfully, and applications may need retry handling.

## Why Repeatable Read Exists

`READ COMMITTED` provides a fresh view for each statement. That is often desirable for OLTP workloads, but it can be problematic when a transaction performs several reads that must be logically consistent with one another.

Consider a reporting or business operation:

```text
Read account balance
        ↓
Read account transactions
        ↓
Calculate derived result
        ↓
Make decision
```

If concurrent commits occur between these reads, the queries can describe different database states.

Repeatable Read provides a stable transaction-level view:

```text
Transaction
    │
    ├── Query A ──┐
    ├── Query B ──┼── Same logical snapshot
    ├── Query C ──┤
    └── Query D ──┘
```

This makes multi-query reasoning more predictable.

## What Repeatable Read Guarantees

At a high level, Repeatable Read provides these guarantees:

- Dirty reads are prevented.
- Previously visible rows do not change underneath the transaction's snapshot.
- Repeating a query produces results consistent with the transaction's snapshot.
- Concurrent changes may cause a transaction to fail rather than silently produce an unsafe result, depending on the database and operation.

For PostgreSQL specifically, `REPEATABLE READ` is implemented using MVCC snapshots.

## PostgreSQL Implementation

PostgreSQL's `REPEATABLE READ` isolation level establishes a transaction-level snapshot.

Conceptually:

```text
BEGIN
  │
  ▼
Create transaction snapshot
  │
  ├── SELECT → snapshot
  ├── SELECT → same snapshot
  ├── UPDATE → snapshot + locking/write rules
  └── SELECT → same snapshot
  │
  ▼
COMMIT
```

The actual PostgreSQL implementation involves transaction IDs, tuple visibility information, snapshots, and transaction status.

A simplified row history might look like:

```text
Row version history

balance = 100
     │
     │ Transaction A updates and commits
     ▼
balance = 500
```

If Transaction B established its Repeatable Read snapshot before A committed, B continues to see the version visible to its snapshot.

It does not simply switch to the newest committed version for every subsequent statement.

## Transaction-Level Snapshot

Consider:

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;

SELECT balance
FROM accounts
WHERE id = 42;
```

Suppose the result is:

```text
100
```

Another transaction then commits:

```sql
UPDATE accounts
SET balance = 500
WHERE id = 42;

COMMIT;
```

Transaction B executes:

```sql
SELECT balance
FROM accounts
WHERE id = 42;
```

Under PostgreSQL Repeatable Read, B continues to see the value consistent with its original snapshot:

```text
100
```

The second query does not automatically move to the newly committed state.

## Non-Repeatable Reads

A non-repeatable read occurs when the same transaction reads a row twice and gets different values because another transaction committed a modification between the reads.

Under PostgreSQL Repeatable Read:

```mermaid
sequenceDiagram
    participant A as Transaction A
    participant B as Transaction B
    participant DB as Database

    B->>DB: BEGIN REPEATABLE READ
    B->>DB: SELECT balance
    DB-->>B: 100

    A->>DB: UPDATE balance = 500
    A->>DB: COMMIT

    B->>DB: SELECT balance
    DB-->>B: 100
```

The transaction-level snapshot prevents the second read from observing A's later commit.

Therefore:

> PostgreSQL Repeatable Read prevents non-repeatable reads.

## Phantom Reads in PostgreSQL

A phantom read traditionally refers to seeing a different set of rows matching the same predicate because another transaction inserted or deleted matching rows.

For example:

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;

SELECT COUNT(*)
FROM orders
WHERE customer_id = 42
  AND status = 'pending';
```

Suppose the result is:

```text
5
```

Another transaction inserts a matching order and commits.

When the first transaction repeats:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = 42
  AND status = 'pending';
```

PostgreSQL's Repeatable Read snapshot continues to provide a consistent view, so the newly committed row is not visible to the transaction's snapshot.

This is an important PostgreSQL-specific point:

> PostgreSQL's Repeatable Read provides stronger behavior than the minimum commonly associated with the SQL-standard Repeatable Read definition.

## Repeatable Read vs Read Committed

The most important difference is snapshot scope.

| Property | Read Committed | Repeatable Read |
|---|---|---|
| Dirty reads | Prevented | Prevented |
| Snapshot scope in PostgreSQL | Per statement | Per transaction |
| Non-repeatable reads | Possible | Prevented |
| New committed rows visible during transaction | Can become visible to later statements | Not visible through the transaction snapshot |
| Concurrency | Generally higher | More restrictive |
| Retry complexity | Lower | Potentially higher |
| Typical use | General OLTP | Stable multi-query view |

The decision is therefore not simply:

```text
Repeatable Read = better
```

Instead:

```text
Need stable transaction-level view?
        │
       Yes
        ▼
Evaluate Repeatable Read
```

## Repeatable Read vs Serializable

Repeatable Read and Serializable solve different levels of concurrency-control requirements.

| Property | Repeatable Read | Serializable |
|---|---|---|
| Stable snapshot | Yes | Yes |
| Prevents dirty reads | Yes | Yes |
| Prevents non-repeatable reads | Yes | Yes |
| PostgreSQL phantom behavior | Prevented by snapshot semantics | Prevented |
| Allows all concurrent executions to appear serial | No | Yes |
| Serialization failures | Possible | Common design consideration |
| Concurrency | Higher than strict serialization in many workloads | More restrictive |
| Use case | Stable consistent view | Strongest transactional correctness |

Serializable is appropriate when correctness depends on preventing anomalies that cannot be safely handled through ordinary snapshot isolation, constraints, atomic operations, or explicit locks.

## When to Use Repeatable Read

Repeatable Read is useful when several operations must observe one consistent database state.

Typical scenarios include:

### Consistent Multi-Query Processing

Suppose a service calculates an account-level result using multiple queries:

```text
Account
   │
   ├── Current state
   ├── Transactions
   ├── Adjustments
   └── Limits
```

If these queries must describe the same point-in-time state, Repeatable Read can be appropriate.

### Long-Running Read Workflows

A transaction performing several related reads may benefit from a stable snapshot when consistency between those reads matters more than observing newly committed data.

However, long-running transactions should be treated carefully because they can increase database resource pressure.

### Financial or Reconciliation Workflows

A reconciliation process may need to inspect multiple related datasets without having its view shift while processing.

Repeatable Read can provide a stable starting point, but it does **not** automatically solve every financial consistency requirement. Business invariants may still require locking, constraints, or stronger transactional mechanisms.

## When Not to Use Repeatable Read

Do not choose Repeatable Read simply because it sounds safer.

For ordinary CRUD APIs, PostgreSQL's default `READ COMMITTED` is often sufficient.

Avoid unnecessary Repeatable Read when:

- Each statement is independent.
- Fresh committed data is desirable.
- Transactions are extremely short.
- High concurrency is more important than a stable snapshot.
- Business correctness is already enforced through atomic SQL and constraints.
- The application cannot reasonably retry transaction failures.

The stronger isolation level should solve an actual consistency requirement.

## Practical PostgreSQL Example

Start a transaction explicitly:

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;

SELECT id, balance
FROM accounts
WHERE id = 42;

SELECT id, amount, created_at
FROM account_transactions
WHERE account_id = 42
ORDER BY created_at;

COMMIT;
```

Both queries operate against the same transaction snapshot.

This can be valuable when the application needs to calculate a result based on a consistent view of both the account and its transaction history.

## Concurrent Update Behavior

Repeatable Read does not mean that every concurrent operation will quietly succeed.

Consider:

```text
Transaction A                 Transaction B
     │                              │
     ├── Read row                   ├── Read same row
     │                              │
     ├── UPDATE row                 │
     ├── COMMIT                     │
     │                              │
     │                              ├── UPDATE same row
     │                              │
     │                              └── May fail due to
     │                                  concurrent update
```

PostgreSQL may raise a serialization-related error when a transaction attempts to modify a row that changed after the transaction's snapshot was established.

The application must therefore be prepared to retry appropriate transactions.

## Handling Serialization Failures

A production service should not assume every transaction commits successfully.

Conceptually:

```python
for attempt in range(max_retries):
    try:
        run_transaction()
        break
    except RetryableTransactionError:
        if attempt == max_retries - 1:
            raise
        backoff()
```

The retry must restart the **entire transaction**, not merely repeat the failed SQL statement.

Why?

Because the transaction's snapshot and transactional state are part of the failed transaction.

The correct model is:

```text
Transaction attempt 1
       ↓
serialization failure
       ↓
ROLLBACK
       ↓
Transaction attempt 2
       ↓
new snapshot
       ↓
COMMIT
```

Do not retry indefinitely. Use bounded retries with appropriate backoff and observability.

## Application Frameworks

### Django

Django supports transaction management through `transaction.atomic()`.

A transaction can request a database-specific isolation level through the underlying database connection configuration or explicit SQL/session configuration.

For example:

```python
from django.db import connection, transaction

with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute(
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"
        )

    # All queries in this atomic block use Repeatable Read.
    ...
```

The isolation level must be configured before performing transactional queries that depend on it.

In production, prefer a consistent configuration strategy rather than scattering isolation-level SQL throughout application code.

### SQLAlchemy

With SQLAlchemy, isolation can be configured on the engine or connection depending on the desired scope.

For example:

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg://app:secret@db.example.com/app",
    isolation_level="REPEATABLE READ",
)
```

For production systems, credentials should come from a secret-management mechanism rather than being embedded directly in source code.

## Transaction Boundaries

Isolation level and transaction boundaries are tightly connected.

A Repeatable Read snapshot is useful only while the transaction remains active.

Consider:

```text
BEGIN
  │
  ├── Query A
  ├── Query B
  ├── Query C
  │
  ▼
COMMIT
```

If the application commits after Query A and starts a new transaction before Query B:

```text
Transaction 1
    └── Query A

Transaction 2
    ├── Query B
    └── Query C
```

the second transaction gets a new snapshot.

Therefore, Repeatable Read does not provide consistency across independent transactions.

## Long-Running Transactions

Repeatable Read becomes operationally significant when transactions remain open for a long time.

In PostgreSQL, a transaction snapshot can prevent cleanup of row versions that are still potentially visible to that snapshot.

Long-running transactions can contribute to:

- Table and index bloat.
- Delayed vacuum cleanup.
- Increased storage usage.
- Increased transaction ID pressure.
- Resource consumption.
- Connection pool exhaustion.

Monitor long-running and idle-in-transaction sessions.

A transaction performing a large report should not necessarily hold one database transaction open for hours. Depending on the requirement, alternatives include:

- Database snapshots.
- Read replicas.
- Materialized views.
- Incremental processing.
- Batch processing.
- Dedicated analytical workloads.

## Locking Still Matters

Repeatable Read does not eliminate locks.

For a read-modify-write workflow:

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;

SELECT balance
FROM accounts
WHERE id = 42
FOR UPDATE;

UPDATE accounts
SET balance = balance - 100
WHERE id = 42;

COMMIT;
```

`FOR UPDATE` provides explicit row-level coordination.

The isolation level determines snapshot semantics, while the lock determines how concurrent modifications to the selected row are coordinated.

Use locks when the business operation requires serialization around a particular resource.

## Constraints Still Matter

Isolation should not replace database constraints.

Suppose the system requires one active subscription per customer.

Use a database constraint:

```sql
CREATE UNIQUE INDEX uq_active_subscription
ON subscriptions (customer_id)
WHERE status = 'active';
```

Repeatable Read may provide a consistent view, but a constraint is a direct and durable mechanism for enforcing the invariant.

A senior design typically combines:

```text
Isolation
    +
Atomic SQL
    +
Locks where necessary
    +
Database constraints
    +
Retry handling
```

rather than attempting to solve all concurrency problems with isolation alone.

## Performance Considerations

Repeatable Read can have operational costs.

The main concerns include:

- Longer transaction lifetimes.
- More retained row versions.
- Increased vacuum pressure.
- More transaction failures under write contention.
- Additional retry workload.
- Reduced effective concurrency for conflicting operations.

The cost depends heavily on transaction duration and workload.

Do not assume:

```text
Higher isolation = slower queries
```

in a simple linear sense.

A query's execution plan may be identical while the transaction's overall concurrency behavior changes significantly.

Measure:

- Query latency.
- Transaction duration.
- Lock waits.
- Serialization failures.
- Retry rates.
- Connection pool utilization.
- PostgreSQL vacuum behavior.
- Table and index bloat.

## Monitoring

Production systems using Repeatable Read should monitor both database performance and transaction correctness.

| Signal | Why it matters |
|---|---|
| Transaction duration | Detects long-lived snapshots |
| Serialization failures | Indicates concurrency conflicts |
| Retry rate | Shows application-level recovery pressure |
| Lock waits | Indicates contention |
| Idle-in-transaction sessions | Can retain resources unexpectedly |
| Connection pool utilization | Detects transaction-induced connection pressure |
| Table/index bloat | Can indicate long-lived snapshots and cleanup pressure |
| Vacuum progress | Helps identify MVCC cleanup issues |

A sudden increase in serialization failures can indicate a workload pattern that requires architectural or query-level changes rather than simply increasing retry counts.

## High Availability and Read Replicas

Repeatable Read provides transaction snapshot semantics on the database connection executing the transaction.

It does not solve replication lag.

Consider:

```text
Application
    │
    ├── Primary
    │      └── COMMIT
    │
    └── Replica
           └── May still be behind
```

A read from a lagging replica can be stale regardless of the isolation level used on another connection.

For workflows requiring read-after-write consistency:

- Prefer the primary when appropriate.
- Use an explicit consistency strategy.
- Monitor replica lag.
- Do not assume transaction isolation implies replica synchronization.

## Security Considerations

Repeatable Read does not provide authorization or access control.

It protects transaction visibility and concurrency semantics.

Security still requires:

- Authentication.
- Authorization.
- Correct tenant filtering.
- Parameterized SQL.
- Database permissions.
- Row-level security where appropriate.
- Correct transaction boundaries.

For multi-tenant systems, a consistent snapshot does not help if the query itself can access another tenant's rows.

## Common Mistakes

### Assuming Repeatable Read Prevents Every Race Condition

It does not.

Business invariants may still require:

- Unique constraints.
- Atomic updates.
- Row locks.
- Serializable isolation.
- Optimistic concurrency control.

### Assuming Repeatable Read Always Means "No Errors"

A stronger isolation level can make concurrent operations fail instead of silently proceeding with an unsafe state.

Production code must handle retryable transaction failures.

### Retrying Only the Failed Query

This is incorrect:

```text
Transaction
  ├── Query A
  ├── Query B → failure
  └── retry Query B
```

Restart the entire transaction:

```text
Transaction attempt 1
  └── failure

ROLLBACK

Transaction attempt 2
  ├── Query A
  ├── Query B
  └── COMMIT
```

### Keeping Repeatable Read Transactions Open Too Long

Long-lived snapshots can create significant PostgreSQL maintenance pressure.

Keep transactions as short as the consistency requirement permits.

### Using Repeatable Read for Normal CRUD

If the application simply performs:

```text
request
  ↓
UPDATE
  ↓
COMMIT
```

Repeatable Read may provide no meaningful benefit.

Use the default isolation level unless a specific requirement justifies stronger semantics.

### Confusing Snapshot Consistency With Business Consistency

A transaction can have a perfectly consistent snapshot and still violate a business rule if the rule spans operations that the chosen isolation or locking strategy does not adequately coordinate.

## Interview Traps

### What Is the Main Difference Between Read Committed and Repeatable Read?

In PostgreSQL:

```text
Read Committed  → snapshot per statement
Repeatable Read → snapshot per transaction
```

### Does Repeatable Read Prevent Dirty Reads?

Yes.

### Does Repeatable Read Prevent Non-Repeatable Reads?

Yes.

### Can Concurrent Updates Still Cause Transaction Failures?

Yes.

PostgreSQL can raise serialization-related errors when concurrent changes conflict with the transaction's snapshot semantics.

### Should an Application Retry a Failed Repeatable Read Transaction?

When the error is retryable, yes.

The entire transaction should be retried with bounded attempts and appropriate backoff.

### Is Repeatable Read Equivalent to Serializable?

No.

Repeatable Read provides a stable transaction snapshot, while Serializable additionally guarantees that committed transactions behave as though they were executed in some serial order.

### Does Repeatable Read Guarantee Fresh Data?

No.

Its purpose is almost the opposite: it deliberately provides a stable view rather than continually exposing newly committed changes.

### Does Repeatable Read Eliminate Locks?

No.

Explicit locks and database write locks still exist.

## Production Decision Framework

Use the following reasoning when choosing between isolation levels:

```mermaid
flowchart TD
    A[Transactional workflow] --> B{Need only committed data?}

    B -->|No| C[Reconsider isolation requirements]
    B -->|Yes| D{Must multiple reads share one snapshot?}

    D -->|No| E[Read Committed]
    D -->|Yes| F{Can atomic SQL, constraints, or locks enforce correctness?}

    F -->|Yes| G[Read Committed + targeted coordination]
    F -->|No| H[Evaluate Repeatable Read]

    H --> I{Can conflicting transactions be retried?}

    I -->|Yes| J[Repeatable Read + bounded retries]
    I -->|No| K[Re-evaluate design and isolation requirements]

    H --> L{Must execution be equivalent to serial order?}
    L -->|Yes| M[Evaluate Serializable]
```

The engineering goal is not to maximize isolation. The goal is to achieve the required correctness with acceptable concurrency and operational complexity.

## Recommended Patterns

| Requirement | Recommended approach |
|---|---|
| Standard OLTP CRUD | Read Committed |
| Prevent dirty reads | Read Committed or stronger |
| Stable multi-query snapshot | Repeatable Read |
| Protect one row during read-modify-write | Row-level locking |
| Enforce uniqueness | Unique constraint/index |
| Atomic numeric/state update | Single SQL statement |
| Strong cross-transaction invariants | Evaluate Serializable |
| Repeatable Read conflicts | Bounded full-transaction retries |
| Long analytical queries | Prefer analytical/read-optimized architecture |
| Read-after-write from primary | Route critical reads appropriately |

## Key Takeaways

- **PostgreSQL Repeatable Read provides a transaction-level MVCC snapshot, so multiple statements observe a consistent logical view.**
- **It prevents dirty and non-repeatable reads and provides stronger snapshot behavior than Read Committed.**
- **Concurrent writes can still produce retryable transaction failures, so production applications must support bounded full-transaction retries.**
- **Repeatable Read does not replace atomic SQL, database constraints, or explicit locks when enforcing business invariants.**
- **Use Repeatable Read deliberately; long-lived snapshots can increase MVCC cleanup pressure, contention, and operational cost.**