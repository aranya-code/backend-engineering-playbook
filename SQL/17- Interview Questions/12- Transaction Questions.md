# 12- Transaction Questions

## Overview

Transactions are a core SQL interview topic because they connect database correctness with concurrency, failure handling, application architecture, and production reliability.

A transaction groups database operations into a unit of work with defined consistency and durability semantics.

For backend engineers, transaction questions usually go beyond:

> "What is ACID?"

Senior interviews often test whether you can reason about:

- Transaction boundaries
- Atomicity
- Isolation levels
- Concurrency anomalies
- Locking
- Deadlocks
- Rollbacks
- Constraints
- Retries
- Idempotency
- Connection pooling
- External service calls
- Transactional outbox
- Message processing
- Long-running transactions
- Database failures
- High availability
- Django and SQLAlchemy transaction behavior

A useful production mental model is:

```text
API request
    ↓
application transaction boundary
    ↓
database connection
    ↓
BEGIN
    ↓
SQL statements
    ↓
locks / MVCC / constraints
    ↓
COMMIT
    ↓
durable database state
```

The most important principle is:

> **A transaction should represent a coherent business unit of work, not simply a convenient wrapper around multiple SQL statements.**

---

## What Is a Transaction?

A transaction is a logical unit of database work whose changes are committed or rolled back according to the database's transaction semantics.

Example:

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

COMMIT;
```

The intent is:

```text
debit account 1
+
credit account 2
=
one atomic business operation
```

If the transaction fails before commit, the changes can be rolled back.

---

## Why Transactions Exist

Without transactions, related operations can partially succeed.

For example:

```text
Debit account
    ↓ success

Credit account
    ↓ failure
```

The system could end with money removed from one account without being added to the other.

Transactions provide atomicity around operations that must change together.

---

## ACID

The traditional transaction model is described using ACID:

| Property | Meaning |
|---|---|
| Atomicity | The transaction's changes are committed as a unit |
| Consistency | Database invariants remain valid after successful transactions |
| Isolation | Concurrent transactions interact according to the configured isolation semantics |
| Durability | Committed changes survive according to the database's durability guarantees |

ACID is useful as an interview framework, but senior answers should explain the mechanisms behind each property.

---

## Atomicity

Atomicity means a transaction's database changes are committed as one unit.

Example:

```sql
BEGIN;

INSERT INTO orders (
    customer_id,
    total_amount
)
VALUES ($1, $2);

INSERT INTO order_items (
    order_id,
    product_id,
    quantity
)
VALUES ($3, $4, $5);

COMMIT;
```

If an error occurs before commit, the transaction can be rolled back.

Atomicity is especially important for:

- Financial operations
- Inventory changes
- Order creation
- State transitions
- Referential data changes

---

## Consistency

Consistency means successful transactions preserve the database's defined invariants.

These invariants can be enforced through:

- `PRIMARY KEY`
- `UNIQUE`
- `FOREIGN KEY`
- `CHECK`
- `NOT NULL`
- Exclusion constraints
- Triggers where appropriate
- Application-level business rules

Example:

```sql
CREATE TABLE accounts (
    id bigint PRIMARY KEY,
    balance numeric(19, 2) NOT NULL CHECK (balance >= 0)
);
```

The database can prevent a committed state with a negative balance.

A transaction does not magically guarantee business correctness.

The system must define the invariants that need protection.

---

## Isolation

Isolation determines how concurrent transactions can observe and interact with each other's changes.

Typical phenomena include:

- Dirty reads
- Non-repeatable reads
- Phantom reads
- Serialization anomalies
- Write conflicts

Isolation is closely related to:

- MVCC
- Locks
- Snapshots
- Transaction visibility
- Serialization failures

---

## Durability

Durability means committed changes are persisted according to the database's durability configuration.

PostgreSQL uses mechanisms including:

```text
transaction changes
      ↓
WAL
      ↓
durable storage
      ↓
checkpoint / recovery
```

Durability is not simply:

> "The COMMIT statement returned."

Production durability also depends on:

- Storage reliability
- WAL configuration
- Synchronous replication settings
- Backup strategy
- Failure domain
- Recovery procedures

---

## Transaction Lifecycle

A typical lifecycle is:

```text
Idle
 ↓
BEGIN
 ↓
Active
 ↓
SQL statements
 ↓
 ┌───────────────┐
 │               │
success        failure
 │               │
 ↓               ↓
COMMIT         ROLLBACK
 ↓               ↓
Durable       Aborted
state
```

After an error inside a PostgreSQL transaction, the transaction normally enters an aborted state and must be rolled back before further commands can succeed.

---

## BEGIN and COMMIT

Explicit transaction:

```sql
BEGIN;

UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = $1
  AND quantity > 0;

INSERT INTO orders (
    customer_id,
    product_id
)
VALUES ($2, $1);

COMMIT;
```

Use explicit transaction boundaries when multiple statements must succeed or fail together.

---

## ROLLBACK

A rollback discards changes made by the current transaction that have not been committed.

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

ROLLBACK;
```

The update does not become part of the committed database state.

---

## SAVEPOINT

Savepoints provide partial rollback inside a transaction.

```sql
BEGIN;

INSERT INTO orders (
    customer_id
)
VALUES ($1);

SAVEPOINT optional_step;

INSERT INTO order_metadata (
    order_id,
    metadata
)
VALUES ($2, $3);

ROLLBACK TO SAVEPOINT optional_step;

COMMIT;
```

The outer transaction remains active.

Savepoints are useful when:

- A sub-operation is optional
- Multiple independent operations occur in one transaction
- Frameworks need nested transaction semantics

They should not be used to make enormous transactions easier to tolerate.

---

## Nested Transactions

Many application frameworks expose nested transaction-like APIs.

In PostgreSQL, nested `BEGIN` statements do not create independently commit-able nested transactions.

Frameworks typically implement nested transaction behavior using savepoints.

For example, Django:

```python
from django.db import transaction

with transaction.atomic():
    create_order()

    try:
        with transaction.atomic():
            optional_operation()
    except Exception:
        pass
```

The inner `atomic()` can correspond to a savepoint.

---

## Transaction Boundaries in Backend Applications

A typical API operation:

```text
HTTP request
   ↓
validate request
   ↓
begin transaction
   ↓
database changes
   ↓
commit
   ↓
response
```

The transaction should usually cover the database operations that must be atomic.

Avoid holding a database transaction while performing unrelated slow work.

---

## External API Calls Inside Transactions

Avoid:

```text
BEGIN
 ↓
UPDATE database
 ↓
call payment provider
 ↓
wait 5 seconds
 ↓
COMMIT
```

The database connection and locks may remain occupied during the external call.

Prefer:

```text
transaction
    ↓
record local state
    ↓
COMMIT
    ↓
external interaction
    ↓
state update / event
```

When atomic coordination is required between local database state and asynchronous processing, consider the transactional outbox pattern.

---

## Transactional Outbox

A common architecture is:

```text
BEGIN
 ├── update business data
 └── insert outbox event
COMMIT
       ↓
outbox publisher
       ↓
Kafka / message broker
       ↓
consumer
```

Example:

```sql
BEGIN;

UPDATE orders
SET status = 'confirmed'
WHERE id = $1;

INSERT INTO outbox_events (
    event_type,
    aggregate_id,
    payload
)
VALUES (
    'order.confirmed',
    $1,
    $2
);

COMMIT;
```

The business state and outbox event are committed atomically.

This avoids the failure window where the database commits but event publication fails.

---

## Database Transaction vs Distributed Transaction

A local database transaction can guarantee atomicity within one database.

It does not automatically provide atomicity across:

```text
PostgreSQL
+
Redis
+
Kafka
+
External API
```

For example:

```text
PostgreSQL COMMIT
        ↓
Kafka publish fails
```

A database transaction cannot roll back the already committed PostgreSQL transaction because Kafka failed.

Distributed workflows require explicit patterns such as:

- Transactional outbox
- Saga
- Compensation
- Idempotency
- Retry
- Reconciliation

---

## Isolation Levels

Common SQL isolation levels include:

| Isolation Level | General Behavior |
|---|---|
| Read Uncommitted | Permits the weakest visibility semantics; PostgreSQL effectively treats it as Read Committed |
| Read Committed | Statements generally see a snapshot of committed data at statement start |
| Repeatable Read | Transaction-level snapshot semantics with stronger consistency |
| Serializable | Provides the strongest standard isolation semantics, potentially requiring retries |

The exact implementation differs between database engines.

The examples here focus primarily on PostgreSQL.

---

## PostgreSQL Read Committed

PostgreSQL's default isolation level is `READ COMMITTED`.

A statement generally sees data committed before that statement's snapshot was taken.

Two statements in the same transaction can therefore observe different committed database states.

Example:

```text
Transaction A
    SELECT
       ↓
Transaction B commits update
       ↓
Transaction A
    SELECT again
```

The second statement can see the newly committed value.

This is an important distinction from transaction-level snapshot semantics.

---

## PostgreSQL Repeatable Read

Under PostgreSQL's `REPEATABLE READ`, the transaction uses a stable snapshot for ordinary reads.

This provides stronger consistency across statements.

However, concurrent updates can cause serialization failures.

Applications must be prepared to retry appropriate transactions.

---

## Serializable

`SERIALIZABLE` provides the strongest isolation level supported by PostgreSQL's standard transaction isolation model.

The database detects execution patterns that cannot be serialized safely and may abort a transaction.

The application may receive:

```text
SQLSTATE 40001
```

The correct response is generally:

```text
retry the entire transaction
```

with bounded backoff and jitter where appropriate.

---

## Serialization Failure

A serialization failure is not necessarily a database bug.

It means the database could not safely allow the transaction's concurrent execution under the requested isolation semantics.

Example:

```text
Transaction A ──┐
                ├── conflicting serialization
Transaction B ──┘
```

The database aborts one transaction.

The application should retry the complete transaction if the operation is safely retryable.

---

## Retry the Whole Transaction

Incorrect:

```python
try:
    update_row()
except SerializationFailure:
    update_row()
```

The retry must respect the transaction boundary.

Conceptually:

```python
for attempt in range(max_attempts):
    try:
        with transaction.atomic():
            perform_business_operation()
        break
    except SerializationFailure:
        backoff()
```

The exact exception handling depends on the framework and driver.

---

## Retry Safety

Retries can duplicate effects if operations are not idempotent.

Example:

```text
request
 ↓
database commit succeeds
 ↓
network failure
 ↓
client retries
 ↓
operation executes again
```

Use:

- Idempotency keys
- Unique constraints
- Deterministic state transitions
- Upserts
- Safe retry boundaries

Transactions and idempotency solve different parts of the problem.

---

## Atomic SQL

Prefer atomic database operations when possible.

Instead of:

```text
SELECT balance
application calculates balance - 100
UPDATE balance
```

prefer:

```sql
UPDATE accounts
SET balance = balance - 100
WHERE id = $1
  AND balance >= 100;
```

Then verify the affected row count.

This reduces race conditions and often reduces round trips.

---

## Read-Modify-Write Race

Unsafe pattern:

```text
Transaction A:
SELECT quantity = 1

Transaction B:
SELECT quantity = 1

A:
UPDATE quantity = 0

B:
UPDATE quantity = 0
```

The application may have intended two decrements but only one may be represented.

Better:

```sql
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = $1
  AND quantity > 0;
```

The database performs the conditional update atomically.

---

## Optimistic Concurrency

Optimistic concurrency assumes conflicts are relatively uncommon.

A version column can be used:

```sql
UPDATE orders
SET
    status = $1,
    version = version + 1
WHERE id = $2
  AND version = $3;
```

If zero rows are updated:

```text
another transaction changed the record
```

The application can retry or return a conflict.

This avoids holding locks for long periods.

---

## Pessimistic Concurrency

Pessimistic concurrency explicitly locks rows.

PostgreSQL:

```sql
SELECT
    id,
    balance
FROM accounts
WHERE id = $1
FOR UPDATE;
```

This is useful when:

- The row must be protected during a transaction
- Contention is expected
- A read-then-write workflow requires serialization

Keep the transaction short.

---

## SELECT FOR UPDATE

Example:

```sql
BEGIN;

SELECT balance
FROM accounts
WHERE id = $1
FOR UPDATE;

UPDATE accounts
SET balance = balance - 100
WHERE id = $1;

COMMIT;
```

The selected row is locked until the transaction ends.

Do not hold the lock while performing external network calls.

---

## NOWAIT

`NOWAIT` fails immediately instead of waiting for a conflicting lock.

```sql
SELECT *
FROM inventory
WHERE product_id = $1
FOR UPDATE NOWAIT;
```

This is useful when the application prefers:

```text
fail fast
```

instead of:

```text
wait indefinitely
```

---

## SKIP LOCKED

`SKIP LOCKED` skips rows currently locked by another transaction.

Example queue pattern:

```sql
SELECT id
FROM jobs
WHERE status = 'pending'
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

This is useful for worker queues.

It is not a general-purpose consistency mechanism.

Rows can be temporarily skipped, and fairness/starvation considerations remain.

---

## Lock Contention

Lock contention occurs when transactions compete for conflicting resources.

Example:

```text
Transaction A
    locks row
       ↓
Transaction B
    waits
       ↓
connection occupied
       ↓
pool pressure
       ↓
API latency
```

The root cause may be:

- Long transactions
- Hot rows
- Large batches
- Excessive concurrency
- Poor lock ordering

---

## Deadlocks

A deadlock occurs when transactions wait on each other cyclically.

Example:

```text
Transaction A
locks Row 1
    ↓
waits for Row 2

Transaction B
locks Row 2
    ↓
waits for Row 1
```

PostgreSQL detects the deadlock and aborts one transaction.

The SQLSTATE is:

```text
40P01
```

---

## Preventing Deadlocks

Use consistent lock ordering.

Bad:

```text
Transaction A: Row 1 → Row 2
Transaction B: Row 2 → Row 1
```

Better:

```text
Transaction A: Row 1 → Row 2
Transaction B: Row 1 → Row 2
```

Other techniques:

- Keep transactions short
- Lock only required rows
- Avoid external calls inside transactions
- Batch work
- Use deterministic ordering
- Retry deadlock-aborted transactions safely

---

## Lock Timeout vs Statement Timeout

These settings solve different problems.

### lock_timeout

Limits how long a statement waits to acquire a lock.

### statement_timeout

Limits the total execution time of a statement.

Conceptually:

```text
statement
 ├── lock wait
 └── execution
```

`lock_timeout` concerns the waiting portion.

`statement_timeout` concerns statement execution as a whole.

Do not treat them as interchangeable.

---

## Long-Running Transactions

Long transactions can cause:

- Lock retention
- MVCC cleanup delays
- Table/index bloat
- Vacuum pressure
- Connection pool exhaustion
- Replica conflicts

Avoid:

```text
BEGIN
 ↓
large computation
 ↓
HTTP request
 ↓
user interaction
 ↓
COMMIT
```

Keep transaction scope focused.

---

## Idle in Transaction

A particularly dangerous state is:

```text
BEGIN
 ↓
query
 ↓
application waits
 ↓
transaction remains open
```

PostgreSQL can report:

```text
idle in transaction
```

Such transactions can retain snapshots and locks and interfere with cleanup.

Monitor them in production.

---

## Transaction Duration

A useful production metric is transaction duration.

Short transactions generally reduce:

- Lock wait duration
- Connection occupancy
- MVCC retention
- Failure surface

Do not optimize only statement latency.

A 50 ms query inside a 30-second transaction can still create severe operational problems.

---

## Connection Pool Interaction

Transactions occupy connections.

Suppose:

```text
pool = 20 connections
```

and 20 transactions spend most of their time waiting on external services.

The application has effectively lost its database capacity.

Therefore:

```text
transaction duration
+
pool size
+
application concurrency
```

must be considered together.

---

## Django Transactions

Django provides:

```python
from django.db import transaction

with transaction.atomic():
    order = create_order()
    create_order_items(order)
```

The `atomic()` block defines the transaction boundary.

Use it when operations must succeed or fail together.

---

## Django on_commit

When an external side effect must happen only after successful commit:

```python
from django.db import transaction

with transaction.atomic():
    order = create_order()

    transaction.on_commit(
        lambda: publish_order_created(order.id)
    )
```

This prevents the callback from executing when the transaction rolls back.

For reliable message delivery, a transactional outbox is generally stronger than relying only on an in-process callback.

---

## FastAPI and SQLAlchemy

A common service-layer pattern is:

```python
with Session(engine) as session:
    try:
        with session.begin():
            create_order(session)
            create_order_items(session)
    except Exception:
        raise
```

The exact transaction lifecycle depends on the SQLAlchemy version and session configuration, but the architectural principle remains:

> Define transaction ownership explicitly at the service/use-case boundary.

---

## Transaction Boundary in Service Architecture

A useful layering model:

```text
HTTP / gRPC handler
        ↓
service / use-case
        ↓
transaction boundary
        ↓
repository / SQL
        ↓
PostgreSQL
```

The service layer can define:

```text
one business operation
=
one transaction
```

where appropriate.

Avoid scattering transaction control across unrelated repository methods unless the architecture explicitly requires it.

---

## Transactions and REST APIs

A REST request may perform:

```text
POST /orders
```

with operations:

```text
create order
create items
reserve inventory
create outbox event
```

If all database changes belong to one consistency boundary:

```text
BEGIN
 ├── order
 ├── items
 ├── inventory reservation
 └── outbox
COMMIT
```

External payment processing should generally be modeled separately rather than held inside the database transaction.

---

## Transactions and gRPC

The same principle applies to gRPC.

A gRPC method can represent a business operation that owns one transaction:

```text
gRPC request
    ↓
service method
    ↓
transaction
    ↓
database changes
    ↓
commit
    ↓
response
```

Do not assume a distributed transaction exists simply because services communicate synchronously.

---

## Transactions and Celery

Background workers often need their own transaction boundaries.

Example:

```text
Celery task
    ↓
BEGIN
    ↓
process batch
    ↓
COMMIT
```

Avoid processing an enormous job in one transaction.

Prefer bounded batches:

```text
batch 1 → commit
batch 2 → commit
batch 3 → commit
```

This reduces lock duration and recovery cost.

---

## Transactions and Kafka Consumers

A Kafka consumer may process:

```text
message
 ↓
database update
 ↓
commit database transaction
 ↓
acknowledge Kafka message
```

If the database commits but the consumer crashes before acknowledging the Kafka message, the message may be processed again.

Therefore consumers should be idempotent.

A unique event ID can help:

```sql
CREATE UNIQUE INDEX idx_processed_events_event_id
ON processed_events (event_id);
```

---

## Transaction Idempotency

For retried operations, use a unique business or request identifier.

Example:

```sql
CREATE TABLE payment_requests (
    idempotency_key text PRIMARY KEY,
    payment_id bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

A retry with the same key can safely resolve to the existing operation instead of creating a duplicate.

---

## Transactions and Redis

Redis does not automatically participate in a PostgreSQL transaction.

Bad assumption:

```text
PostgreSQL COMMIT
+
Redis update
=
atomic
```

These are separate systems.

For cache consistency:

```text
database commit
    ↓
cache invalidation/update
```

must be designed explicitly.

A common pattern is:

```text
DB transaction
    ↓
COMMIT
    ↓
invalidate cache
```

or use an outbox/event-driven approach.

---

## Transactions and Cache Consistency

Suppose:

```text
DB transaction updates order
Redis still contains old order
```

The cache must eventually be invalidated or refreshed.

Do not update Redis before the database commit and assume the database transaction can roll back the cache change.

---

## Transactional Constraints

Database constraints are part of transaction correctness.

Example:

```sql
ALTER TABLE orders
ADD CONSTRAINT orders_total_positive
CHECK (total_amount > 0);
```

If the transaction violates the constraint:

```text
statement fails
→ transaction enters failed state
→ rollback required
```

Constraints should be used to protect invariants that belong at the database boundary.

---

## Constraint Violations and Application Handling

Applications should distinguish expected business conflicts from unexpected failures.

Examples:

```text
unique violation
foreign-key violation
check violation
serialization failure
deadlock
```

Each may require a different response.

Do not catch every database exception and silently retry it.

---

## Transaction Errors

After many PostgreSQL statement errors:

```text
statement fails
     ↓
transaction becomes aborted
```

Subsequent statements fail until:

```sql
ROLLBACK;
```

or the framework performs equivalent transaction cleanup.

This is a common source of application bugs when using low-level database drivers.

---

## Transaction Retry Categories

Not every failure should be retried.

Potentially retryable:

- Serialization failure
- Deadlock
- Some transient connection failures

Usually not blindly retryable:

- Unique constraint violation
- Invalid input
- Foreign-key violation
- Permission failure
- Syntax error

Retries should be based on error semantics.

---

## Retry Storms

Suppose:

```text
100 workers
 ↓
database temporarily fails
 ↓
100 retries
 ↓
database becomes overloaded
 ↓
more failures
 ↓
more retries
```

This creates a retry storm.

Use:

- Bounded retry counts
- Exponential backoff
- Jitter
- Concurrency limits
- Circuit breaking where appropriate
- Idempotency

---

## Transaction Timeouts

Use timeouts to prevent runaway transactions.

Relevant layers can include:

```text
HTTP timeout
connection acquisition timeout
lock timeout
statement timeout
transaction/application deadline
```

The timeout hierarchy should be intentional.

A database timeout should not unexpectedly exceed the API's maximum request duration by a large margin.

---

## Large Transactions

A large transaction can generate:

- Significant WAL
- Large numbers of row versions
- Long lock duration
- Long rollback time
- Replication pressure
- Vacuum delays

For large data operations, prefer:

```text
small batch
→ commit
→ next batch
```

while preserving the required business semantics.

---

## Transaction vs Batch

These are different concepts.

A batch can be:

```text
1000 rows
```

while each batch executes in its own transaction.

Do not assume:

```text
one job
=
one transaction
```

For large workloads, smaller transactions are often operationally safer.

---

## Migrations and Transactions

Schema changes can have transaction semantics of their own.

Production migrations should consider:

- Lock acquisition
- Transaction duration
- Backward compatibility
- Replication
- Application version overlap
- Rollback strategy

For large data migrations:

```text
schema expansion
→ compatible application
→ batched backfill
→ validation
→ cutover
→ cleanup
```

is generally safer than one enormous transaction.

---

## Zero-Downtime Transactions

A deployment should not assume every application instance has the same schema version.

During rolling deployments:

```text
old application
+
new application
+
database
```

may coexist.

Schema changes should therefore support both versions during the transition.

This is why expand-and-contract migration patterns are important.

---

## Transaction and Schema Compatibility

Example:

```text
Phase 1:
add nullable column

Phase 2:
deploy application that writes both columns

Phase 3:
backfill

Phase 4:
switch reads

Phase 5:
enforce constraint

Phase 6:
remove old column
```

Each phase can preserve transaction correctness while allowing rolling deployment.

---

## Transactions and High Availability

In a primary/replica architecture:

```text
Application
    ↓
Primary
    ↓ WAL
Replica
```

A transaction committed on the primary may not immediately be visible on an asynchronous replica.

Therefore:

```text
COMMIT succeeded
+
read from replica
```

does not necessarily mean the new data is immediately visible.

This is the read-after-write consistency problem.

---

## Read-After-Write

Suppose:

```text
POST /orders
    ↓
primary
    ↓
COMMIT
```

Then:

```text
GET /orders/123
    ↓
read replica
```

The replica may still be behind.

Solutions include:

- Read from primary after writes
- Session/request stickiness
- LSN-aware routing
- Bounded replica lag policies
- Accepting eventual consistency

---

## Uncertain Commit

A particularly difficult failure is:

```text
application
    ↓
COMMIT
    ↓
database commits
    ↓
network failure
    ↓
application does not receive response
```

The application cannot always know whether the transaction committed.

Blindly retrying may duplicate the operation.

Use:

- Idempotency keys
- Unique constraints
- Deterministic operation IDs
- Reconciliation

This is a senior-level transaction interview topic.

---

## Transaction and Failover

During database failover:

```text
primary
   ↓ failure
standby promoted
   ↓
application reconnects
```

A transaction that was in progress may be lost.

A commit response already received by the application is different from a transaction whose outcome is uncertain due to a connection failure.

Application retry behavior must account for this distinction.

---

## Transaction Monitoring

Monitor:

- Transaction duration
- Active transactions
- Idle-in-transaction sessions
- Lock waits
- Deadlocks
- Serialization failures
- Rollbacks
- Commit rate
- Connection utilization
- Long-running queries
- Replica lag

Useful PostgreSQL query:

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

---

## Finding Idle Transactions

```sql
SELECT
    pid,
    usename,
    xact_start,
    state,
    query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
ORDER BY xact_start;
```

Long-lived entries should be investigated.

---

## Finding Blocking Transactions

A useful starting point:

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

This helps identify whether transaction latency is caused by lock contention.

---

## Transaction Metrics

Useful application-level metrics include:

```text
transaction_duration
transaction_commit_count
transaction_rollback_count
serialization_failure_count
deadlock_count
lock_wait_duration
idle_in_transaction_count
```

Correlate these with:

```text
endpoint
request ID
service
database
pod
worker
```

This makes transaction incidents much easier to diagnose.

---

## Security Considerations

Transactions do not replace authorization.

For example:

```sql
BEGIN;

UPDATE orders
SET status = 'cancelled'
WHERE id = $1;

COMMIT;
```

may be atomic but still insecure if the application fails to verify that the caller is authorized to modify that order.

Security requirements include:

- Authentication
- Authorization
- Tenant isolation
- Parameterized queries
- Least-privilege roles
- RLS where appropriate
- Auditability

Atomicity and authorization are separate concerns.

---

## Transaction Isolation and Security

Isolation can prevent certain users from observing inconsistent database states, but it is not an access-control mechanism.

Do not use:

```text
transaction isolation
```

as a substitute for:

```text
authorization
```

---

## Transaction Cost

Transactions consume database resources through:

- Connections
- Memory
- Locks
- WAL
- MVCC state
- CPU
- I/O

Higher transaction concurrency does not always mean higher throughput.

At some point:

```text
more concurrency
→ more contention
→ more waiting
→ lower throughput
```

This is why connection-pool and worker sizing matter.

---

## Production Transaction Decision Framework

Before defining a transaction boundary, ask:

1. Which database changes must be atomic?
2. Which invariants must hold after commit?
3. Can the operation be safely retried?
4. Does it involve external services?
5. Could it hold locks for a long time?
6. What isolation level is required?
7. Could concurrent operations conflict?
8. What happens if the client disconnects?
9. What happens if commit succeeds but the response is lost?
10. Does the operation need an idempotency key?
11. Will it run synchronously or asynchronously?
12. What happens during database failover?

---

## Common Transaction Mistakes

### Making Every Function Open Its Own Transaction

This can create fragmented transaction boundaries.

Prefer transaction ownership at the business-operation/service layer.

### Calling External Services Inside Transactions

This increases lock and connection duration.

### Creating Huge Transactions

Large transactions increase WAL, lock, rollback, and replication pressure.

### Retrying Every Exception

Not every error is transient.

### Retrying Only One Statement

Serialization failures and deadlocks generally require retrying the whole transaction.

### Ignoring Idempotency

Retries can create duplicate business effects.

### Assuming COMMIT Always Has a Known Outcome

Network failures can make commit outcomes uncertain.

### Treating Redis as Transactionally Consistent With PostgreSQL

They are separate systems.

### Using Isolation as Authorization

Isolation controls concurrency visibility, not access control.

### Ignoring Idle-in-Transaction Sessions

They can retain snapshots and locks and interfere with database maintenance.

### Using `SELECT FOR UPDATE` Everywhere

Pessimistic locking can become a scalability bottleneck.

### Using `SKIP LOCKED` Without Understanding Its Semantics

Skipped rows may be processed later, and fairness is not guaranteed.

### Ignoring Replica Lag

A successful primary commit does not imply immediate visibility on an asynchronous replica.

---

## Interview Traps

### What Are ACID Properties?

Atomicity, Consistency, Isolation, and Durability.

A senior answer should explain the mechanisms and trade-offs behind them.

---

### What Is the Default PostgreSQL Isolation Level?

`READ COMMITTED`.

---

### What Is the Difference Between Read Committed and Repeatable Read?

Under PostgreSQL:

- `READ COMMITTED` generally uses a new snapshot for each statement.
- `REPEATABLE READ` uses a stable transaction snapshot for ordinary reads.

This affects what concurrent commits become visible during a transaction.

---

### What Is Serializable?

An isolation level that provides the strongest standard isolation semantics by preventing executions that cannot be safely serialized, potentially through transaction aborts that require retries.

---

### What Is SQLSTATE 40001?

A serialization failure.

Appropriate transactions may need to be retried from the beginning.

---

### What Is SQLSTATE 40P01?

A PostgreSQL deadlock detected error.

The transaction should generally be retried as a whole if the operation is safely retryable.

---

### Why Retry the Whole Transaction?

Because the database transaction's snapshot, locks, and state are no longer valid after the serialization/deadlock failure.

Retrying only one statement does not recreate the original transaction semantics.

---

### What Is a Deadlock?

A cycle of transactions waiting for resources held by each other.

---

### How Do You Prevent Deadlocks?

Use:

- Consistent lock ordering
- Short transactions
- Small batches
- Minimal lock scope
- Avoidance of external calls inside transactions

---

### What Is `SELECT FOR UPDATE`?

A row-locking mechanism that prevents conflicting concurrent modifications until the transaction ends.

---

### What Is the Difference Between `NOWAIT` and `SKIP LOCKED`?

`NOWAIT` fails immediately if the lock cannot be acquired.

`SKIP LOCKED` ignores currently locked rows and continues with other eligible rows.

---

### When Should You Use Optimistic Concurrency?

When conflicts are relatively uncommon and holding locks would be undesirable.

A version column or conditional update can detect concurrent modifications.

---

### When Should You Use Pessimistic Locking?

When a business operation needs to serialize access to a resource and the transaction can safely hold the lock for a short period.

---

### Why Should External Calls Usually Be Outside Transactions?

They can be slow or unpredictable and can hold database connections and locks unnecessarily.

Use durable state transitions and patterns such as transactional outbox when coordination is required.

---

### Can a PostgreSQL Transaction Include Redis?

Not as one atomic PostgreSQL transaction.

Redis and PostgreSQL have independent transactional systems.

---

### What Is a Transactional Outbox?

A pattern where business state and an event/outbox record are committed in the same database transaction, after which a separate publisher delivers the event.

---

### What Happens if the Application Loses the Connection During COMMIT?

The transaction outcome may be uncertain.

The database may have committed even though the application did not receive the response.

Use idempotency and reconciliation to make retries safe.

---

### Why Are Long Transactions Dangerous?

They can:

- Hold locks
- Retain snapshots
- Delay vacuum cleanup
- Increase bloat
- Occupy connections
- Increase rollback cost
- Increase replication pressure

---

### Does a Transaction Guarantee Business Correctness?

No.

Transactions provide atomicity and isolation semantics, but business invariants must still be correctly modeled and enforced.

---

## Practical Interview Problems

### Transfer Money Between Accounts

A strong solution:

```sql
BEGIN;

UPDATE accounts
SET balance = balance - $1
WHERE id = $2
  AND balance >= $1;

UPDATE accounts
SET balance = balance + $1
WHERE id = $3;

COMMIT;
```

Production considerations:

- Verify affected row counts
- Validate account ownership
- Lock/order accounts consistently if explicit row locking is required
- Use appropriate constraints
- Make the operation idempotent
- Handle deadlocks
- Handle uncertain commit outcomes

---

### Prevent Overselling Inventory

Instead of:

```text
SELECT quantity
UPDATE quantity
```

use an atomic conditional update:

```sql
UPDATE inventory
SET quantity = quantity - $1
WHERE product_id = $2
  AND quantity >= $1;
```

Then verify:

```text
rows affected = 1
```

If zero:

```text
insufficient inventory
```

This can avoid unnecessary read-modify-write races.

---

### Implement Optimistic Locking

```sql
UPDATE orders
SET
    status = $1,
    version = version + 1
WHERE id = $2
  AND version = $3;
```

If zero rows are affected:

```text
concurrent modification detected
```

Return an appropriate conflict or retry according to business requirements.

---

### Process Jobs Concurrently

```sql
WITH batch AS (
    SELECT id
    FROM jobs
    WHERE status = 'pending'
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 100
)
UPDATE jobs AS j
SET status = 'processing'
FROM batch
WHERE j.id = batch.id
RETURNING j.id;
```

This can allow multiple workers to claim different jobs without waiting on one another.

---

### Create an Order and Outbox Event

```sql
BEGIN;

INSERT INTO orders (
    customer_id,
    total_amount
)
VALUES ($1, $2)
RETURNING id;

INSERT INTO outbox_events (
    event_type,
    aggregate_id,
    payload
)
VALUES (
    'order.created',
    $3,
    $4
);

COMMIT;
```

The application must ensure the returned order ID is correctly associated with the outbox row.

---

## Senior-Level Transaction Scenario

### Scenario

An API creates an order and then publishes:

```text
order.created
```

to Kafka.

Naive implementation:

```text
BEGIN
 ↓
INSERT order
 ↓
COMMIT
 ↓
publish Kafka event
```

Failure:

```text
COMMIT succeeds
 ↓
Kafka publish fails
```

The database contains the order but consumers never receive the event.

Better:

```text
BEGIN
 ├── INSERT order
 └── INSERT outbox event
COMMIT
      ↓
outbox publisher
      ↓
Kafka
```

This separates:

```text
database atomicity
```

from:

```text
message delivery
```

while preserving a durable connection between them.

---

## Transaction Design Checklist

- [ ] Transaction represents a coherent business operation.
- [ ] All required atomic changes are inside the boundary.
- [ ] Unrelated work is outside the transaction.
- [ ] External network calls are not unnecessarily inside the transaction.
- [ ] Isolation level matches the consistency requirement.
- [ ] Database constraints protect important invariants.
- [ ] Read-modify-write races have been considered.
- [ ] Optimistic or pessimistic concurrency is chosen intentionally.
- [ ] Lock ordering is deterministic.
- [ ] Deadlocks are handled appropriately.
- [ ] Serialization failures are retryable where appropriate.
- [ ] Retries are bounded and use backoff/jitter.
- [ ] Business operations are idempotent when retries are possible.
- [ ] Long-running transactions are monitored.
- [ ] Idle-in-transaction sessions are monitored.
- [ ] Connection pool impact is understood.
- [ ] Replica lag is considered for read-after-write behavior.
- [ ] Uncertain commit outcomes are handled.
- [ ] External events use an appropriate reliability pattern.
- [ ] Large workloads are processed in bounded batches.
- [ ] Transaction metrics and failures are observable.
- [ ] Failover and recovery behavior are understood.

---

## Key Takeaways

- **Transactions define atomic business boundaries:** keep all database changes that must succeed together inside one focused transaction and avoid unrelated or slow external work inside it.
- **Isolation is a concurrency decision:** PostgreSQL's `READ COMMITTED`, `REPEATABLE READ`, and `SERIALIZABLE` provide different semantics, and stronger isolation can require application retries.
- **Concurrency requires deliberate design:** atomic SQL, optimistic concurrency, row locking, deterministic lock ordering, and idempotency are often more important than simply wrapping statements in `BEGIN` and `COMMIT`.
- **Retries and failures must be designed together:** serialization failures, deadlocks, connection failures, and uncertain commits require bounded retries, idempotency, and sometimes reconciliation rather than blind repetition.
- **Senior transaction design crosses system boundaries:** PostgreSQL transactions, connection pools, replicas, Redis, Kafka, Celery, external APIs, migrations, and failover all affect the reliability of a real backend operation.