# 25- Choosing an Isolation Level

## Overview

Transaction isolation determines how concurrently executing transactions are allowed to observe and affect each other's changes.

It is one of the primary controls for balancing:

- Data correctness.
- Concurrency.
- Lock contention.
- Transaction throughput.
- Latency.
- Retry frequency.

Choosing an isolation level is not simply a matter of selecting the strongest available option. Stronger isolation can increase serialization failures, waiting, or application complexity. Weaker isolation can improve concurrency but allow anomalies that violate business requirements.

A practical engineering approach is:

```text
Business invariant
       ↓
Concurrency behavior required
       ↓
Possible anomalies
       ↓
Isolation level / locking / atomic SQL
       ↓
Performance and retry characteristics
```

The correct question is:

> What consistency guarantee does this business operation actually require?

## Isolation Levels

The commonly discussed SQL isolation levels are:

| Isolation level | Dirty reads | Non-repeatable reads | Phantoms | Typical concurrency |
|---|---:|---:|---:|---|
| Read Uncommitted | Possible by standard definition | Possible | Possible | Highest |
| Read Committed | Prevented | Possible | Possible | High |
| Repeatable Read | Prevented | Prevented | Depends on implementation | Medium–high |
| Serializable | Prevented | Prevented | Prevented | Lowest logical concurrency |

These are conceptual SQL guarantees. Actual behavior is database-specific.

For PostgreSQL specifically:

- `READ UNCOMMITTED` behaves like `READ COMMITTED`.
- `READ COMMITTED` uses a fresh snapshot for each statement.
- `REPEATABLE READ` uses a transaction-level snapshot and provides stronger behavior than the SQL standard minimum.
- `SERIALIZABLE` provides serializable execution semantics using PostgreSQL's Serializable Snapshot Isolation (SSI).

Therefore, isolation-level names should never be interpreted without considering the database engine.

## The Main Trade-Off

Isolation can be viewed as a spectrum:

```text
More concurrency
      │
      ▼
Read Committed
      │
      ▼
Repeatable Read
      │
      ▼
Serializable
      │
      ▼
Stronger consistency guarantees
```

As consistency requirements increase, the database may need to:

- Maintain stronger visibility guarantees.
- Detect more conflicts.
- Abort more transactions.
- Cause applications to retry work.
- Reduce effective concurrency for conflicting operations.

The goal is not maximum isolation.

The goal is **sufficient isolation for the business invariant**.

## Read Committed

`READ COMMITTED` is the default isolation level in PostgreSQL.

Each SQL statement sees a snapshot containing data committed before that statement began.

Consider:

```text
Transaction A

BEGIN;

SELECT balance FROM accounts WHERE id = 1;
-- 100
```

Meanwhile:

```text
Transaction B

UPDATE accounts
SET balance = 50
WHERE id = 1;

COMMIT;
```

If Transaction A executes the same `SELECT` again as a new statement under PostgreSQL `READ COMMITTED`, it can observe the newly committed value.

```text
Statement 1 → balance = 100
Statement 2 → balance = 50
```

This is a **non-repeatable read**.

### When to Use Read Committed

It is a strong default for:

- Typical REST APIs.
- CRUD operations.
- Short service transactions.
- Most Django applications.
- Standard OLTP workloads.
- Operations that do not require a stable transaction-wide snapshot.

### Advantages

- Good concurrency.
- Low overhead for typical workloads.
- PostgreSQL's default.
- Suitable for most backend CRUD operations.

### Limitations

A transaction may observe different committed states across statements.

Therefore, code that assumes all reads within a transaction represent one consistent snapshot may be incorrect.

## Repeatable Read

`REPEATABLE READ` provides a stable transaction-level snapshot in PostgreSQL.

Conceptually:

```text
BEGIN
  ↓
Snapshot created
  ↓
Statement A → snapshot
  ↓
Statement B → same snapshot
  ↓
Statement C → same snapshot
  ↓
COMMIT
```

A transaction does not normally observe changes committed after its snapshot was established.

PostgreSQL's implementation can also abort transactions when concurrent updates conflict with the transaction's snapshot.

### When to Use Repeatable Read

Consider it when:

- Multiple statements need a consistent view of the same data.
- A transaction performs a complex read operation.
- Business logic depends on a stable snapshot.
- You want stronger semantics than `READ COMMITTED` without requiring full serializable execution.

### Limitations

- Longer-lived transactions can increase resource pressure.
- Concurrent modifications can cause transaction failures.
- Applications may need retry handling.
- It does not automatically solve every application-level concurrency problem.

## Serializable

`SERIALIZABLE` provides the strongest standard isolation guarantee.

The result should be equivalent to some serial ordering of committed transactions.

For example:

```text
Concurrent execution:

T1 ────────────────┐
                   │
T2 ────────────────┤
                   │
T3 ────────────────┘

Database ensures the result is equivalent to:

T1 → T2 → T3
```

The database may detect conflicts and abort one transaction rather than allow a result that cannot correspond to a serial execution.

In PostgreSQL, serializable isolation is implemented using **Serializable Snapshot Isolation (SSI)** rather than simply executing all transactions using traditional strict two-phase locking.

### When to Use Serializable

Use it when the business invariant genuinely requires serializable behavior and cannot be safely expressed using:

- Constraints.
- Atomic SQL.
- Explicit row locking.
- Optimistic concurrency.
- Lower isolation levels.

Examples can include:

- Complex financial invariants.
- Highly sensitive allocation logic.
- Multi-row invariants that are difficult to protect otherwise.
- Operations where incorrect concurrent interleavings are unacceptable.

### Cost

Serializable transactions can experience:

```text
serialization failure
       ↓
rollback
       ↓
retry
```

Therefore, applications using serializable isolation should have bounded transaction retry handling.

## Read Uncommitted

The SQL standard describes `READ UNCOMMITTED` as allowing dirty reads.

A dirty read means:

```text
T1:
UPDATE balance = 50
-- not committed

T2:
SELECT balance
-- sees 50
```

If T1 subsequently rolls back, T2 observed data that never became committed.

PostgreSQL does not provide this behavior. Setting `READ UNCOMMITTED` effectively behaves like `READ COMMITTED`.

Therefore, do not choose PostgreSQL `READ UNCOMMITTED` expecting dirty reads or meaningful additional concurrency.

## Choosing Isolation by Business Requirement

Isolation should follow the invariant.

| Business requirement | Typical starting point |
|---|---|
| Standard CRUD | Read Committed |
| Independent reads/writes | Read Committed |
| Consistent multi-statement snapshot | Repeatable Read |
| Complex cross-row invariant | Repeatable Read, locking, or Serializable |
| Strict serializable semantics | Serializable |
| Inventory decrement | Atomic conditional `UPDATE` |
| Account transfer | Short transaction + deterministic row locks |
| Concurrent document editing | Optimistic concurrency |
| Duplicate prevention | Unique constraint |
| Long-running workflow | Explicit state machine rather than long transaction |

This table is a starting point, not a universal rule.

## Isolation vs Locking

Isolation level and explicit locking are related but different mechanisms.

Isolation controls **visibility and concurrency semantics**.

Locks explicitly control **access to resources**.

For example:

```sql
SELECT *
FROM accounts
WHERE id = $1
FOR UPDATE;
```

can protect a row from concurrent modifications regardless of whether the application uses the strongest possible isolation level.

A common production design is:

```text
Read Committed
+
short transaction
+
SELECT ... FOR UPDATE
+
database constraints
```

rather than:

```text
Serializable everywhere
```

The first approach can provide sufficient correctness with better control over contention.

## Isolation vs Atomic SQL

Many concurrency problems can be solved without increasing isolation.

Consider inventory:

```sql
UPDATE inventory
SET available_quantity = available_quantity - $2
WHERE product_id = $1
  AND available_quantity >= $2;
```

The database evaluates the condition and update atomically.

This can be preferable to:

```text
SELECT quantity
      ↓
application calculation
      ↓
UPDATE quantity
```

The key principle is:

> Before increasing isolation, determine whether the invariant can be expressed directly as an atomic database operation.

## Isolation vs Optimistic Concurrency

Optimistic concurrency detects conflicting changes rather than preventing them.

Example:

```sql
UPDATE documents
SET content = $1,
    version = version + 1
WHERE id = $2
  AND version = $3;
```

If zero rows are affected:

```text
version mismatch
      ↓
concurrent modification detected
```

This is often more appropriate for low-contention user edits than using long transactions or strong isolation.

Isolation level controls database transaction behavior; optimistic concurrency is an application/data-model technique.

They can be used together.

## Isolation vs Pessimistic Locking

Pessimistic concurrency assumes conflicts are possible and acquires locks before modifying shared state.

```sql
BEGIN;

SELECT balance
FROM accounts
WHERE id = $1
FOR UPDATE;

UPDATE accounts
SET balance = balance - $2
WHERE id = $1;

COMMIT;
```

This can be appropriate for highly contended resources where conflict resolution would be expensive.

The transaction should remain short because the lock is typically held until transaction completion.

## A Practical Decision Framework

Use the following decision process.

### Identify the Invariant

Ask:

```text
What must remain true?
```

Examples:

```text
balance >= 0

inventory >= 0

email is unique

order cannot move from SHIPPED back to PENDING

two accounts must be updated together
```

### Identify the Race

Ask:

```text
What can happen if two requests execute concurrently?
```

Examples:

```text
lost update
double reservation
duplicate creation
inconsistent reads
write skew
```

### Find the Narrowest Mechanism

Try, in roughly this order:

```text
Database constraint
        ↓
Atomic SQL
        ↓
Optimistic concurrency
        ↓
Explicit row locking
        ↓
Higher isolation
```

This is not a strict universal ordering, but it encourages solving the specific correctness problem rather than globally increasing isolation.

### Evaluate Contention

Ask:

- How frequently do concurrent operations touch the same rows?
- How long does each transaction run?
- How expensive is a conflict?
- Can transactions be retried?
- How many application instances are running?
- What happens during traffic spikes?

### Evaluate Failure Behavior

Ask:

```text
Can the transaction be retried safely?
```

If using `SERIALIZABLE`, this question becomes particularly important.

## PostgreSQL Configuration

You can inspect the current transaction isolation level:

```sql
SHOW transaction_isolation;
```

Example output:

```text
read committed
```

Set isolation for a transaction:

```sql
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;

SELECT ...
UPDATE ...

COMMIT;
```

Or:

```sql
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;

SELECT ...
UPDATE ...

COMMIT;
```

Keep isolation configuration explicit when an operation has stronger requirements than the application's normal default.

## Django

Django normally operates with PostgreSQL's default `READ COMMITTED` isolation unless the database configuration or transaction explicitly changes it.

For normal operations:

```python
from django.db import transaction


def update_order(order_id: int) -> None:
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)

        order.status = Order.Status.PAID
        order.save(update_fields=["status"])
```

Here, explicit row locking may be more targeted than changing the entire database isolation policy.

For stronger isolation requirements, configure the database connection appropriately and ensure the application understands the resulting concurrency failures.

Do not assume that wrapping code in `transaction.atomic()` automatically makes it serializable.

## FastAPI and SQLAlchemy

With SQLAlchemy, transaction and isolation configuration should be deliberate.

For example, an engine can be configured with a specific isolation level:

```python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    isolation_level="SERIALIZABLE",
)
```

Do not configure every service transaction this way without understanding the workload.

For a targeted operation, transaction-level or connection-level configuration can be preferable depending on the SQLAlchemy version and architecture.

The important design principle is to keep stronger isolation scoped to operations that actually require it.

## Serializable Retry Pattern

A serializable transaction should be prepared for serialization failures.

```text
BEGIN SERIALIZABLE
        ↓
execute business operation
        ↓
       COMMIT
        │
   ┌────┴────┐
   │         │
success    failure
   │         │
   ▼         ▼
return   serialization failure
             │
             ▼
          rollback
             │
             ▼
      backoff + jitter
             │
             ▼
       new transaction
```

The retry must start with fresh reads.

Do not cache values from the failed transaction and reuse them in the retry.

## Example: Account Transfer

A transfer requires:

```text
debit account A
credit account B
```

Both updates must commit atomically.

A practical PostgreSQL implementation is:

```sql
BEGIN;

SELECT id, balance
FROM accounts
WHERE id IN ($1, $2)
ORDER BY id
FOR UPDATE;

UPDATE accounts
SET balance = balance - $3
WHERE id = $1
  AND balance >= $3;

-- Verify the debit succeeded.

UPDATE accounts
SET balance = balance + $3
WHERE id = $2;

COMMIT;
```

Important design properties:

- Both accounts are updated in one transaction.
- Rows are locked before dependent updates.
- Rows are locked in deterministic order.
- The balance invariant is checked against current database state.
- The transaction remains short.
- Deadlock probability is reduced through consistent lock ordering.

Serializable isolation may still be appropriate if the overall business invariant is more complex than the example.

## Example: Inventory Reservation

For a simple inventory invariant:

```text
available_quantity >= requested_quantity
```

an atomic update can often be sufficient:

```sql
UPDATE inventory
SET available_quantity = available_quantity - $2
WHERE product_id = $1
  AND available_quantity >= $2;
```

Then:

```text
affected rows = 1
    → reservation succeeded

affected rows = 0
    → reservation failed
```

This can provide excellent concurrency without requiring serializable isolation.

If reservation involves multiple inventory records or a more complex cross-row invariant, explicit locking or stronger isolation may become necessary.

## Example: Preventing Duplicate Orders

Suppose an API accepts an idempotency key:

```text
POST /orders
Idempotency-Key: abc123
```

A unique constraint can enforce uniqueness:

```sql
CREATE UNIQUE INDEX orders_idempotency_key_unique
ON orders (idempotency_key);
```

The application transaction can then safely create or retrieve the operation.

The constraint is more reliable than:

```text
SELECT idempotency_key
IF NOT EXISTS
    INSERT
```

because concurrent requests can race between the two statements.

## Production Considerations

### Default Isolation Should Be Boring

For most PostgreSQL OLTP applications, `READ COMMITTED` is a reasonable default.

Individual operations should use stronger techniques only when their correctness requirements demand them.

This keeps system behavior understandable.

### Avoid Global Serializable by Default

Making every transaction serializable can introduce:

- More serialization failures.
- More retries.
- Increased application complexity.
- Potential throughput reduction under contention.

Use it when its guarantees provide meaningful business value.

### Measure Before Changing Isolation

Monitor:

- Transaction latency.
- Lock wait time.
- Deadlocks.
- Serialization failures.
- Rollback rate.
- Database CPU.
- Connection pool usage.

Changing isolation without measurements can trade one production problem for another.

### Keep Transactions Short

Isolation interacts with transaction duration.

A stronger isolation level on a 20 ms transaction may be manageable.

The same design on a 30-second transaction can create severe operational problems.

### Test Under Concurrency

Unit tests that execute one transaction at a time do not prove concurrency correctness.

Test scenarios such as:

```text
10 workers
    ↓
same inventory row
    ↓
concurrent updates
```

and:

```text
multiple workers
    ↓
same account pair
    ↓
lock contention
```

Observe:

- Final database state.
- Error rates.
- Retry counts.
- Lock waits.
- Transaction duration.

## Monitoring and Observability

Track isolation-sensitive behavior separately.

Useful metrics include:

```text
transaction_duration_seconds
transaction_rollbacks_total
deadlocks_total
serialization_failures_total
lock_wait_seconds
```

For PostgreSQL, inspect active transactions:

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
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

Long-running transactions should be investigated because they can affect concurrency and MVCC maintenance.

## Security Considerations

Isolation does not replace authorization.

For example:

```sql
UPDATE documents
SET status = 'APPROVED'
WHERE id = $1
  AND owner_id = $2
  AND status = 'PENDING';
```

The transaction may guarantee atomicity, but the `owner_id` predicate is still necessary to enforce ownership.

Security-sensitive state transitions should combine:

- Authorization checks.
- Database constraints.
- Correct transaction boundaries.
- Current database state.
- Appropriate locking or atomic updates.

Never assume a stronger isolation level makes an unauthorized operation safe.

## Scalability Considerations

At high scale, contention often matters more than theoretical isolation strength.

Consider:

```text
1,000 requests/sec
       ↓
same database row
       ↓
serialized access
       ↓
lock contention
       ↓
latency increases
```

Increasing application replicas does not necessarily increase throughput for a single highly contended database resource.

Solutions may include:

- Reducing contention.
- Partitioning hot data.
- Atomic updates.
- Queue-based serialization.
- Sharding where justified.
- Optimistic concurrency.
- Better transaction boundaries.
- Reducing unnecessary writes.

Isolation should be considered alongside the data-access architecture.

## Common Mistakes

### Choosing Serializable Because It Is "Safest"

Serializable provides strong guarantees, but it is not automatically the best choice.

**Better:** identify the invariant and use the narrowest mechanism that safely protects it.

### Assuming Repeatable Read Means No Concurrent Conflicts

Repeatable Read provides stable visibility, but concurrent writes can still conflict.

**Better:** understand the database implementation and design for possible transaction failures.

### Treating Isolation and Locking as the Same Thing

They solve different problems.

**Better:** use isolation for visibility/execution guarantees and explicit locks when specific resources require controlled concurrent access.

### Using Read Committed for Every Complex Workflow Without Analysis

Read Committed is an excellent default, but multi-statement business logic can still suffer from race conditions.

**Better:** analyze each invariant and use atomic SQL, constraints, locks, optimistic concurrency, or stronger isolation as required.

### Increasing Isolation Instead of Fixing a Race

Sometimes the problem is simply:

```text
read
calculate
write
```

when a single atomic SQL statement would solve it.

**Better:** simplify the operation before increasing isolation.

### Ignoring Serialization Failures

Serializable transactions can legitimately fail due to concurrency.

**Better:** implement bounded retries with exponential backoff and jitter.

### Keeping Long Transactions at High Isolation

This increases the operational impact of contention and transaction conflicts.

**Better:** minimize transaction duration and avoid user/network interaction inside transactions.

## Interview Traps

### What Isolation Level Does PostgreSQL Use by Default?

`READ COMMITTED`.

### Does PostgreSQL Support Dirty Reads?

No. PostgreSQL's `READ UNCOMMITTED` behaves like `READ COMMITTED`.

### What Is the Difference Between Read Committed and Repeatable Read in PostgreSQL?

`READ COMMITTED` takes a new snapshot for each statement, while `REPEATABLE READ` uses a transaction-level snapshot.

### When Would You Choose Serializable?

When the business operation requires serializable execution semantics and weaker isolation plus targeted concurrency mechanisms cannot safely enforce the invariant.

### Does Serializable Mean Transactions Never Fail?

No. Serializable transactions may be aborted with serialization failures. Applications must be prepared to retry the complete transaction.

### Is Serializable Always Slower?

Not necessarily in every workload, but it can produce more conflict detection and transaction aborts under contention. The important cost is workload-dependent.

### Can `SELECT FOR UPDATE` Replace Serializable?

Sometimes a targeted lock can provide exactly the required protection, but it is not semantically equivalent to serializable isolation.

### How Do You Choose an Isolation Level?

Start with the business invariant, identify possible concurrent anomalies, determine whether constraints/atomic SQL/locking/optimistic concurrency can solve them, and choose the weakest isolation that still provides the required correctness.

## Quick Decision Guide

```text
Do I need multiple operations to be atomic?
        │
       Yes
        ↓
Use a transaction
        │
        ▼
Can the invariant be enforced with a constraint?
        │
       Yes ──→ Use the constraint
        │
       No
        ↓
Can one atomic SQL statement enforce it?
        │
       Yes ──→ Prefer atomic SQL
        │
       No
        ↓
Is there a specific resource to protect?
        │
       Yes ──→ Consider row-level locking
        │
       No
        ↓
Are conflicts infrequent?
        │
       Yes ──→ Consider optimistic concurrency
        │
       No
        ↓
Does the invariant require serializable execution?
        │
       Yes ──→ Consider Serializable + retries
        │
       No
        ↓
Use the normal application isolation level
```

## Key Takeaways

- **Choose isolation from the business invariant and concurrency requirements, not from the assumption that stronger isolation is always better.**
- **For PostgreSQL OLTP systems, `READ COMMITTED` is a strong general default; use stronger isolation only when the operation requires stronger guarantees.**
- **Before increasing isolation, consider database constraints, atomic SQL, optimistic concurrency, and targeted row locking because they can solve specific races with less contention.**
- **`REPEATABLE READ` and `SERIALIZABLE` can produce transaction failures under concurrency, so production applications must handle retries correctly.**
- **Isolation level, transaction duration, lock scope, query design, and workload contention must be considered together when designing scalable transactional systems.**