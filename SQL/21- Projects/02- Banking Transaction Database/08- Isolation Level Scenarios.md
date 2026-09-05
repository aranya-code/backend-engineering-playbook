# 08- Isolation Level Scenarios

## Overview

Transaction isolation controls how concurrent database transactions observe and interact with each other's changes.

In a banking transaction database, isolation is important because financial operations often involve:

```text
read current state
    ↓
validate business invariant
    ↓
modify shared state
    ↓
commit
```

Multiple requests can execute this workflow concurrently.

PostgreSQL provides transaction isolation levels that define which concurrent effects a transaction can observe and which anomalies the database prevents.

The commonly relevant levels are:

| Isolation level | PostgreSQL behavior | Typical banking use |
|---|---|---|
| `READ COMMITTED` | Default; each statement gets a fresh snapshot | Most OLTP operations |
| `REPEATABLE READ` | Transaction-level consistent snapshot | Consistent multi-query reads |
| `SERIALIZABLE` | Strongest isolation; conflicting transactions may be aborted | Operations requiring serializable execution semantics |

Isolation level is only one part of concurrency control.

A production banking system typically combines:

```text
Isolation level
+
row locking
+
atomic updates
+
constraints
+
idempotency
+
transaction boundaries
```

The key principle is:

> Choose isolation based on the business invariant and concurrency behavior that must be guaranteed, rather than automatically choosing the strongest available level.

---

## Isolation vs Locking

Isolation and locking are related but different.

### Isolation

Isolation determines how concurrent transactions observe database state.

### Locking

Locking explicitly coordinates access to particular rows or other database resources.

For example:

```sql
SELECT
    id,
    balance
FROM accounts
WHERE id = $1
FOR UPDATE;
```

uses row locking.

A transaction can also run at:

```sql
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
```

which changes the transaction's isolation semantics.

A common banking design may use:

```text
READ COMMITTED
+
FOR UPDATE
```

rather than:

```text
SERIALIZABLE for every operation
```

because the required invariant can often be enforced more directly.

---

## PostgreSQL Isolation Model

PostgreSQL's implementation is based heavily on MVCC.

MVCC allows transactions to work with snapshots of database state rather than requiring every read to block concurrent writes.

Conceptually:

```text
Transaction A
     │
     ├── snapshot
     │
     └── reads committed row versions

Transaction B
     │
     ├── modifies row
     │
     └── creates newer row version
```

PostgreSQL's MVCC behavior allows high levels of concurrent read/write activity while preserving transaction isolation rules.

---

## Read Committed

`READ COMMITTED` is PostgreSQL's default isolation level.

Each statement generally sees data committed before that statement began.

This means two statements in the same transaction can observe different committed states.

Example:

```sql
BEGIN;

SELECT balance
FROM accounts
WHERE id = 1001;

-- Another transaction commits a change.

SELECT balance
FROM accounts
WHERE id = 1001;

COMMIT;
```

The two statements may see different committed values.

This is often desirable for OLTP workloads because it provides good concurrency without requiring a stable transaction-wide snapshot.

---

## Why Read Committed Is Often Appropriate

Most banking operations do not need every statement in the transaction to see exactly the same snapshot.

For example:

```text
lock account
validate
update balance
insert ledger
commit
```

can often be safely implemented with:

```text
READ COMMITTED
+
row locking
+
atomic writes
```

The important requirement is that the financial invariant is protected.

---

## Read Committed Scenario: Concurrent Withdrawal

Initial:

```text
balance = 100
```

Two transactions attempt:

```text
withdraw 80
withdraw 80
```

Using:

```sql
UPDATE accounts
SET balance = balance - $1
WHERE id = $2
  AND balance >= $1
RETURNING balance;
```

PostgreSQL coordinates the concurrent row updates.

One operation can succeed:

```text
100 → 20
```

The other evaluates against the resulting row state and cannot satisfy:

```text
balance >= 80
```

Therefore:

```text
one withdrawal succeeds
one withdrawal fails
```

This is an example of using an atomic statement instead of relying on a stronger isolation level.

---

## Read Committed Scenario: Row Lock

A more complex operation can use:

```sql
BEGIN;

SELECT
    id,
    balance,
    currency,
    status
FROM accounts
WHERE id = $1
FOR UPDATE;

-- Perform validation.

UPDATE accounts
SET
    balance = balance - $2
WHERE id = $1;

COMMIT;
```

The row lock serializes concurrent operations that need conflicting access to the account.

This is often easier to reason about than increasing isolation globally.

---

## Read Committed Scenario: Non-Repeatable Read

A transaction can observe different committed values across statements.

Example:

```text
Transaction A:
    SELECT balance → 100

Transaction B:
    UPDATE balance → 150
    COMMIT

Transaction A:
    SELECT balance → 150
```

The transaction observed two different committed states.

This behavior is permitted under `READ COMMITTED`.

For most short OLTP workflows, this is acceptable when each critical mutation uses appropriate locking or atomic SQL.

---

## Read Committed Scenario: Transfer

Consider:

```text
Account A = 1000
Account B = 500
```

A transfer can use:

```sql
BEGIN;

SELECT
    id,
    balance,
    currency,
    status
FROM accounts
WHERE id IN ($1, $2)
ORDER BY id
FOR UPDATE;

-- Validate accounts.

-- Insert transaction.
-- Insert ledger entries.
-- Update both balances.

COMMIT;
```

The important guarantee comes from the combination of:

```text
transaction
+
ordered locks
+
validation
+
atomic writes
```

rather than the isolation level alone.

---

## Repeatable Read

`REPEATABLE READ` provides a transaction-level consistent snapshot.

A transaction generally continues to see the database state as of the start of its transaction, subject to PostgreSQL's concurrency rules.

Example:

```sql
BEGIN;

SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

SELECT balance
FROM accounts
WHERE id = $1;

-- Other transactions may commit changes.

SELECT balance
FROM accounts
WHERE id = $1;

COMMIT;
```

The transaction does not simply acquire a fresh snapshot for every statement as it does under `READ COMMITTED`.

---

## When Repeatable Read Helps

`REPEATABLE READ` can be useful when several reads must be internally consistent.

Examples:

- Generating a consistent statement.
- Reading multiple related records for one logical snapshot.
- Multi-query reporting within a transaction.
- Workflows where a stable snapshot is important.

However, it does not automatically replace row locking for mutable financial state.

---

## Repeatable Read and Updates

A common misconception is:

```text
REPEATABLE READ
=
no concurrency problems
```

That is incorrect.

If a transaction attempts to update a row that has changed incompatibly since its snapshot, PostgreSQL may abort the transaction rather than silently applying an unsafe update.

The application must therefore be prepared for transaction-level failures.

---

## Repeatable Read Scenario

Suppose:

```text
Initial balance = 100
```

Transaction A starts under `REPEATABLE READ`.

```text
A reads balance = 100
```

Transaction B then changes the account:

```text
B:
balance = 50
COMMIT
```

Transaction A continues using its transaction snapshot.

If A later attempts a conflicting modification, PostgreSQL's concurrency rules may cause the transaction to fail rather than allowing an inconsistent update.

The application should treat such failures as retryable only when the entire business operation is safely retryable.

---

## Serializable

`SERIALIZABLE` provides the strongest isolation level available in PostgreSQL.

The goal is to ensure that successfully committed concurrent transactions behave as though they were executed in some serial order.

This does not mean:

```text
all transactions execute one at a time
```

Instead, PostgreSQL detects conflicts that would make a serial execution impossible and aborts transactions when necessary.

---

## Serializable Scenario

Suppose two operations independently read state and then make decisions:

```text
Transaction A
    read account state
    perform operation A

Transaction B
    read related state
    perform operation B
```

If their combined behavior cannot be represented as a valid serial execution, PostgreSQL can abort one transaction.

The application receives a serialization failure such as:

```text
SQLSTATE 40001
```

---

## Serializable Requires Retry Logic

A serializable transaction can fail even though the SQL statements themselves are valid.

Typical flow:

```text
BEGIN
    ↓
execute statements
    ↓
serialization conflict
    ↓
ROLLBACK
    ↓
backoff
    ↓
retry entire transaction
```

Do not retry only the statement that happened to fail.

The entire transaction must be rerun because its earlier reads were part of the serialization decision.

---

## Read Committed vs Repeatable Read vs Serializable

| Property | `READ COMMITTED` | `REPEATABLE READ` | `SERIALIZABLE` |
|---|---|---|---|
| Default PostgreSQL level | Yes | No | No |
| Statement-level snapshots | Yes | No | No |
| Stable transaction snapshot | No | Yes | Yes |
| Strongest anomaly prevention | Lowest | Higher | Highest |
| Serialization failures | Possible in some cases | Possible | Expected possibility |
| Retry complexity | Lower | Moderate | Higher |
| Typical throughput | Highest | High | Potentially lower |
| Best use | OLTP | Consistent multi-query reads | Strong serial semantics |

The exact performance impact depends on workload, contention, query patterns, and transaction duration.

---

## Isolation and Business Invariants

The correct question is not:

```text
"Which isolation level is safest?"
```

Instead ask:

```text
"What invariant must remain true?"
```

Examples:

| Invariant | Possible protection |
|---|---|
| Balance cannot become negative | Atomic conditional update |
| Only one idempotent operation per key | Unique constraint |
| Two account rows must be updated together | Database transaction |
| Account must not change during complex validation | `FOR UPDATE` |
| Concurrent state transition must have one winner | Conditional update |
| Multiple reads require one consistent snapshot | `REPEATABLE READ` |
| Workflow must behave serially under complex conflicts | `SERIALIZABLE` |

---

## Scenario: Double Spending

The requirement is:

```text
balance >= withdrawal amount
```

A strong implementation is:

```sql
UPDATE accounts
SET
    balance = balance - $1
WHERE id = $2
  AND status = 'ACTIVE'
  AND balance >= $1
RETURNING id, balance;
```

This can be sufficient under normal `READ COMMITTED` semantics.

Increasing the entire database workload to `SERIALIZABLE` is not automatically a better solution.

---

## Scenario: Complex Account Validation

Suppose a transfer requires:

```text
account active
+
sufficient balance
+
currency valid
+
no prohibited state
+
account limits valid
```

A row lock may be appropriate:

```sql
BEGIN;

SELECT
    id,
    balance,
    currency,
    status
FROM accounts
WHERE id = $1
FOR UPDATE;

-- Validate multiple conditions.

UPDATE accounts
SET balance = balance - $2
WHERE id = $1;

COMMIT;
```

The lock protects the state being used by the multi-step decision.

---

## Scenario: Consistent Statement Generation

Suppose a statement requires multiple queries:

```text
opening balance
+
transactions
+
closing balance
```

If the queries execute at different snapshots, concurrent transactions can change the data between them.

A transaction-level consistent snapshot can be useful:

```sql
BEGIN;

SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Query opening balance.
-- Query ledger entries.
-- Query closing state.

COMMIT;
```

The exact statement-generation architecture should also consider long transaction duration and replica usage.

---

## Scenario: Reporting During OLTP

A reporting query might aggregate millions of transactions while transfers continue to execute.

Using a transaction with a stable snapshot can provide consistent reporting results.

However, holding a long-running transaction on the primary can create operational pressure.

Potential effects include:

```text
long-lived snapshots
+
vacuum cleanup delays
+
bloat
+
resource consumption
```

For large reports, consider:

- Read replicas.
- Materialized views.
- Summary tables.
- Analytics infrastructure.
- Bounded reporting windows.

---

## Scenario: Concurrent Transfer and Statement

Suppose:

```text
Transfer:
A → B : 100
```

runs concurrently with:

```text
Statement generation for A
```

The statement may see either the state before or after the committed transfer depending on its snapshot and transaction timing.

The application should define whether the statement requires:

```text
point-in-time consistency
```

rather than assuming the latest possible state is always required.

---

## Isolation and `SELECT ... FOR UPDATE`

These can be combined.

Example:

```sql
BEGIN;

SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

SELECT
    id,
    balance
FROM accounts
WHERE id = $1
FOR UPDATE;

-- mutate account

COMMIT;
```

There is no requirement to use `SERIALIZABLE` simply because row locks are being used.

In fact, many high-throughput OLTP systems use:

```text
READ COMMITTED
+
targeted locks
```

for predictable concurrency.

---

## Isolation and Conditional Updates

A conditional update can often eliminate the need for an explicit read.

```sql
UPDATE accounts
SET
    balance = balance - $1
WHERE id = $2
  AND balance >= $1
RETURNING balance;
```

This is an important senior-level optimization:

```text
avoid unnecessary read
+
express invariant in SQL
+
perform atomic mutation
```

It reduces both query count and the concurrency window.

---

## Isolation and Unique Constraints

Suppose two requests use:

```text
customer_id = 10
idempotency_key = abc
```

A unique constraint:

```sql
CREATE UNIQUE INDEX transactions_idempotency_idx
ON transactions (
    initiated_by_customer_id,
    idempotency_key
)
WHERE idempotency_key IS NOT NULL;
```

provides the concurrency guarantee.

Increasing isolation does not replace a unique constraint.

A business uniqueness invariant should be enforced declaratively.

---

## Isolation and Foreign Keys

Foreign keys also participate in PostgreSQL's concurrency behavior.

For example:

```text
transactions
    ↓
customers
```

A foreign key ensures that referenced data satisfies the relational constraint while concurrent modifications occur.

Do not replace relational constraints with application-level checks simply because the operation is concurrent.

---

## Isolation and Deadlocks

Higher isolation does not eliminate deadlocks.

Deadlocks can still occur because of lock ordering:

```text
Transaction A:
lock Account 1
wait Account 2

Transaction B:
lock Account 2
wait Account 1
```

Use:

```text
deterministic lock ordering
+
short transactions
+
bounded retries
```

regardless of the chosen isolation level.

---

## Isolation and Serialization Failures

Serialization failures are especially important under:

```text
SERIALIZABLE
```

but applications should also understand that stronger transaction semantics can introduce retry requirements.

A retryable transaction should be structured as:

```text
BEGIN
    ↓
all reads
    ↓
all validations
    ↓
all writes
    ↓
COMMIT
```

If the transaction fails due to serialization:

```text
ROLLBACK
    ↓
retry complete workflow
```

---

## Retry Pattern in Python

A service can use bounded retries:

```python
import time

MAX_ATTEMPTS = 3

for attempt in range(MAX_ATTEMPTS):
    try:
        with transaction.atomic():
            perform_transfer()
        break
    except SerializationFailure:
        if attempt == MAX_ATTEMPTS - 1:
            raise
        time.sleep(0.05 * (2 ** attempt))
```

In production, use an appropriate database exception mapping and add jitter rather than relying on a fixed deterministic delay.

The transaction function should be safe to execute again.

---

## Retry Pattern with Deadlocks

The same principle applies to PostgreSQL deadlocks:

```text
SQLSTATE 40P01
```

A safe retry strategy is:

```text
detect transient concurrency error
        ↓
rollback
        ↓
backoff
        ↓
retry complete transaction
```

Do not retry business validation failures such as:

```text
insufficient funds
account closed
invalid currency
```

---

## Isolation and Unknown Commit Outcome

A transaction can commit successfully while the application fails to receive the response.

Example:

```text
COMMIT
  ↓
database commits
  ↓
connection/network failure
  ↓
application sees error
```

Isolation level does not solve this problem.

The system still needs:

```text
idempotency
+
durable transaction identifiers
+
reconciliation
```

to determine whether the operation actually committed.

---

## Isolation and Read Replicas

Isolation applies within a database transaction.

It does not automatically solve distributed replica consistency.

Architecture:

```text
Application
    │
    ├── write → Primary
    │
    └── read  → Replica
```

A replica may lag behind the primary.

Therefore:

```text
transaction committed on primary
```

does not necessarily mean:

```text
immediately visible on replica
```

For read-after-write requirements, route to the appropriate consistency source.

---

## Isolation and Connection Pooling

Applications using Django, FastAPI, SQLAlchemy, or other frameworks often use connection pools.

Isolation level should be explicitly managed at the transaction boundary when a non-default level is required.

For example:

```sql
BEGIN;

SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- transaction work

COMMIT;
```

Do not accidentally leave a connection configured in an unexpected isolation state for subsequent requests.

Transaction-scoped configuration is preferable where supported.

---

## Isolation and Long Transactions

Higher consistency does not make long transactions free.

A long-running transaction can:

```text
retain snapshots
+
increase resource usage
+
delay cleanup
+
increase contention
```

This is particularly important for:

```text
REPEATABLE READ
SERIALIZABLE
```

where transaction-wide consistency is more significant.

Keep transactions as short as the business workflow permits.

---

## Isolation and Queue Workers

Queue-like workers can use:

```sql
SELECT
    id,
    transaction_id
FROM transactions
WHERE status = 'PENDING'
ORDER BY created_at, id
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

The worker does not necessarily need `SERIALIZABLE`.

A suitable queue design often combines:

```text
READ COMMITTED
+
row locks
+
SKIP LOCKED
+
durable status/claim
+
idempotent processing
```

This can provide high throughput.

---

## Isolation and Banking Ledger Queries

Ledger history is typically append-oriented.

A query such as:

```sql
SELECT
    id,
    transaction_id,
    direction,
    amount,
    currency,
    created_at
FROM ledger_entries
WHERE account_id = $1
ORDER BY created_at, id;
```

usually does not need row locks.

Historical reads should not unnecessarily block financial writes.

The required isolation depends on whether the query needs:

```text
current point-in-time view
```

or:

```text
transaction-wide consistent snapshot
```

---

## Scenario: Reconciliation

A reconciliation job may compare:

```text
transactions
+
ledger entries
+
account balances
```

For a bounded reconciliation window, a consistent snapshot can be valuable.

For example:

```sql
BEGIN;

SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Read transactions.
-- Read ledger.
-- Read balance projections.

COMMIT;
```

However, large reconciliation jobs should be designed carefully so that the snapshot does not remain open for excessive periods.

---

## Scenario: Serializable Financial Invariant

Consider a business rule that depends on multiple independent rows and cannot easily be expressed as:

```text
constraint
```

or:

```text
atomic update
```

or:

```text
targeted row lock
```

`SERIALIZABLE` may be appropriate if the application can tolerate and correctly retry serialization failures.

The trade-off is:

```text
stronger correctness semantics
        ↕
higher retry/contention complexity
```

---

## When to Choose Each Level

### Prefer `READ COMMITTED` When

Use it for most normal OLTP operations:

```text
point lookups
transaction creation
status transitions
atomic balance updates
ordinary transaction workflows
worker processing
```

Combine it with explicit locks or atomic statements when necessary.

---

### Consider `REPEATABLE READ` When

Use it when several reads need to observe a consistent transaction snapshot:

```text
statement generation
consistent reporting
multi-query reconciliation
snapshot-style workflows
```

Be cautious with long-running transactions.

---

### Consider `SERIALIZABLE` When

Use it when:

```text
the business invariant spans multiple reads/writes
+
lower-level locking/constraints are insufficient
+
serial execution semantics are desirable
+
the application can safely retry
```

Do not choose it simply because banking systems "need the strongest isolation."

---

## Decision Matrix

| Requirement | Recommended starting point |
|---|---|
| Simple balance decrement | `READ COMMITTED` + atomic `UPDATE` |
| Account validation + update | `READ COMMITTED` + `FOR UPDATE` |
| Multi-account transfer | `READ COMMITTED` + ordered row locks |
| Idempotency | Unique constraint |
| Transaction status transition | Conditional `UPDATE` |
| Parallel workers | `READ COMMITTED` + `SKIP LOCKED` |
| Consistent multi-query snapshot | `REPEATABLE READ` |
| Complex serializable invariant | `SERIALIZABLE` |
| Historical read | Usually no explicit row lock |
| Large analytics workload | Separate read/analytics architecture |

---

## Django Isolation Configuration

Django applications can configure database transaction behavior through PostgreSQL settings and explicit transaction handling.

A transaction-specific isolation level can be established at the database level or through an appropriate PostgreSQL connection configuration.

The important engineering principle is:

```text
do not change isolation casually
```

because the setting affects transaction behavior, retries, performance, and application assumptions.

For most Django OLTP workloads, the PostgreSQL default of `READ COMMITTED` is a reasonable starting point.

---

## FastAPI and SQLAlchemy

In a FastAPI service using SQLAlchemy, transaction boundaries should be explicit.

Conceptually:

```python
with session.begin():
    account = (
        session.query(Account)
        .filter(Account.id == account_id)
        .with_for_update()
        .one()
    )

    # Validate and modify financial state.
```

If `SERIALIZABLE` is required, configure it deliberately at the connection/transaction layer and ensure retry handling exists around the complete transaction.

---

## Security Implications

Isolation problems can become authorization and financial security problems.

For example:

```text
authorization check
       ↓
state changes concurrently
       ↓
operation proceeds using invalid assumptions
```

A secure financial operation should combine:

```text
authorization
+
transaction boundary
+
appropriate isolation
+
row locking/atomic update
+
database constraints
```

Isolation does not replace authorization.

---

## Performance Considerations

Increasing isolation can affect:

- Transaction abort rate.
- Retry frequency.
- Lock contention.
- CPU utilization.
- Transaction latency.
- Throughput.

The actual impact must be measured against realistic workloads.

A useful benchmark compares:

```text
READ COMMITTED
vs
REPEATABLE READ
vs
SERIALIZABLE
```

using:

- Production-like row counts.
- Realistic contention.
- Realistic transaction duration.
- Realistic concurrency.
- Realistic retry behavior.

---

## Monitoring Isolation Behavior

Monitor:

```text
serialization failures
deadlocks
transaction retries
lock wait duration
transaction latency
long-running transactions
connection pool saturation
```

A sudden increase in:

```text
SQLSTATE 40001
```

may indicate increased contention or a workload change.

Do not simply increase retry counts without understanding why conflicts increased.

---

## Production Configuration

Useful PostgreSQL controls include:

```text
statement_timeout
lock_timeout
idle_in_transaction_session_timeout
deadlock_timeout
```

These are complementary.

For example:

```text
lock_timeout
    ↓
limits lock waiting

statement_timeout
    ↓
limits statement execution

idle_in_transaction_session_timeout
    ↓
protects against idle open transactions

deadlock_timeout
    ↓
controls when PostgreSQL checks for deadlocks
```

Do not treat timeout configuration as a replacement for sound isolation and locking design.

---

## Common Mistakes

### Always Using `SERIALIZABLE`

Why it happens:

```text
banking = strict consistency
```

The reasoning is incomplete.

A targeted:

```text
atomic update
+
constraint
+
row lock
```

may provide the required invariant with less contention and fewer retries.

---

### Assuming `READ COMMITTED` Is Unsafe

`READ COMMITTED` is the PostgreSQL default and is appropriate for many production OLTP workloads.

It becomes unsafe when the application assumes stronger semantics without implementing the necessary locks or atomic operations.

---

### Assuming Isolation Replaces Constraints

`SERIALIZABLE` does not replace:

```text
UNIQUE
CHECK
FOREIGN KEY
```

Declarative invariants should still be enforced with database constraints.

---

### Retrying Only One Statement

For:

```text
40001
```

retrying only the failed statement is generally incorrect.

Retry the complete transaction.

---

### Ignoring Deadlocks

Stronger isolation does not eliminate deadlocks.

Use:

```text
deterministic lock ordering
+
short transactions
+
bounded retry
```

---

### Using Long Repeatable-Read Transactions

A stable snapshot can be useful, but keeping it open for minutes or hours can create operational pressure.

Use bounded reporting or dedicated analytics architectures for large workloads.

---

### Reading From a Replica After a Write

Isolation level does not guarantee read-after-write consistency across replicas.

A replica can lag.

---

### Changing Isolation Without Load Testing

Isolation affects concurrency behavior.

Changing:

```text
READ COMMITTED
→
SERIALIZABLE
```

should be treated as a workload-level design change, not merely a configuration tweak.

---

## Interview Traps

### "Is SERIALIZABLE the Only Correct Isolation Level for Banking?"

No.

Many banking operations can safely use:

```text
READ COMMITTED
+
atomic SQL
+
row locks
+
constraints
```

The correct choice depends on the invariant.

---

### "Does REPEATABLE READ Prevent All Concurrency Problems?"

No.

It provides a stable transaction snapshot but does not eliminate every concurrency conflict or replace explicit locking and constraints.

---

### "Does FOR UPDATE Require SERIALIZABLE?"

No.

`FOR UPDATE` can be used under `READ COMMITTED`, which is common for OLTP workflows.

---

### "Does READ COMMITTED Mean Reads Are Never Consistent?"

No.

Each statement gets a consistent snapshot according to PostgreSQL's rules.

What changes is that different statements in the same transaction can observe different committed states.

---

### "Does SERIALIZABLE Mean Transactions Execute One at a Time?"

No.

PostgreSQL permits concurrent execution and detects conflicts that would violate serializable semantics.

Some transactions may be aborted and must be retried.

---

### "Can I Retry a Serialization Failure Without Idempotency?"

Not safely for arbitrary financial operations.

The entire transaction must be retryable, and the surrounding business operation should have durable idempotency semantics where duplicate requests are possible.

---

## Production Checklist

### Isolation Selection

- [ ] Business invariants are explicitly documented.
- [ ] Default `READ COMMITTED` behavior is understood.
- [ ] Stronger isolation is used only when justified.
- [ ] Isolation changes are load-tested.

### Concurrency

- [ ] Atomic updates are used where appropriate.
- [ ] Row locks protect multi-step mutable workflows.
- [ ] Multi-row locks use deterministic ordering.
- [ ] Deadlocks are handled.
- [ ] Serialization failures are handled.

### Reliability

- [ ] Complete transactions are retried after retryable concurrency failures.
- [ ] Retries are bounded.
- [ ] Backoff/jitter is used.
- [ ] Idempotency protects repeated business operations.
- [ ] Unknown commit outcomes can be reconciled.

### Performance

- [ ] Transactions are short.
- [ ] Long-running snapshots are avoided where possible.
- [ ] Lock waits are monitored.
- [ ] Retry rates are monitored.
- [ ] Replica lag is considered for read-after-write workflows.

### Database Integrity

- [ ] Unique constraints enforce uniqueness.
- [ ] Check constraints enforce local invariants.
- [ ] Foreign keys enforce relationships.
- [ ] Isolation is not being used as a substitute for schema constraints.

### Operations

- [ ] `40001` serialization failures are observable.
- [ ] `40P01` deadlocks are observable.
- [ ] Long-running transactions are observable.
- [ ] Connection pool saturation is observable.
- [ ] Reconciliation exists for ambiguous financial outcomes.

---

## Senior Decision Framework

When choosing an isolation level, reason in this order:

```text
What business invariant must hold?
        ↓
Can a database constraint enforce it?
        ↓
Can one atomic SQL statement enforce it?
        ↓
Can targeted row locks enforce it?
        ↓
Do multiple reads require one stable snapshot?
        ↓
Would serializable execution semantics materially simplify correctness?
        ↓
Can the application safely retry the entire transaction?
        ↓
What is the expected contention?
        ↓
What is the operational cost of retries?
```

A strong design often looks like:

```text
Constraint
    ↓
Atomic statement
    ↓
Targeted row lock
    ↓
Transaction boundary
    ↓
Appropriate isolation level
    ↓
Retry + reconciliation
```

The isolation level is therefore one layer of the concurrency architecture, not the entire solution.

---

## Key Takeaways

- **PostgreSQL `READ COMMITTED` is a strong default for banking OLTP when combined with atomic updates, targeted row locks, and database constraints.**
- **Use `REPEATABLE READ` when a transaction requires a stable multi-query snapshot, while avoiding unnecessarily long-lived transactions.**
- **Use `SERIALIZABLE` when the business invariant genuinely requires serial execution semantics and the application can safely handle serialization failures and complete-transaction retries.**
- **Isolation does not replace constraints, idempotency, locking, authorization, or reconciliation; financial correctness depends on the combination of these mechanisms.**
- **Choose isolation from the invariant and workload backward, then validate the design under realistic contention, latency, retry, and failure conditions.**