# 16- Transaction Exercises

## Overview

Transactions are the boundary at which a backend system turns multiple database operations into one logical unit of work.

The exercises in this document focus on transaction reasoning rather than transaction syntax alone. The goal is to practice:

- Defining correct transaction boundaries.
- Understanding atomicity and rollback.
- Choosing isolation levels.
- Handling concurrent requests.
- Preventing lost updates and race conditions.
- Designing retry-safe transactions.
- Handling deadlocks and serialization failures.
- Keeping transactions short.
- Coordinating database work with Redis, Kafka, Celery, and external APIs.
- Designing reliable production workflows around failures.

The examples use PostgreSQL and assume a backend application such as Django, FastAPI, or another Python service.

---

## Practice Schema

Use the following schema for the exercises:

```sql
CREATE TABLE accounts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL,
    balance numeric(12, 2) NOT NULL CHECK (balance >= 0),
    version bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL,
    status text NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    total_amount numeric(12, 2) NOT NULL CHECK (total_amount >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    status text NOT NULL
        CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    amount numeric(12, 2) NOT NULL,
    idempotency_key text UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE inventory (
    product_id bigint PRIMARY KEY,
    available_quantity integer NOT NULL CHECK (available_quantity >= 0),
    reserved_quantity integer NOT NULL DEFAULT 0
        CHECK (reserved_quantity >= 0)
);

CREATE TABLE outbox_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aggregate_type text NOT NULL,
    aggregate_id bigint NOT NULL,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);
```

---

## Transaction Mental Model

Use this lifecycle when analyzing every exercise:

```text
BEGIN
  ↓
Read / validate
  ↓
Mutate state
  ↓
Check invariants
  ↓
COMMIT
  │
  ├── success → durable state
  │
  └── failure → ROLLBACK
```

For concurrent workloads:

```text
Request A ──┐
            ├── PostgreSQL
Request B ──┤
            │
Request C ──┘
```

The database must coordinate these operations according to isolation, locking, constraints, and transaction semantics.

A transaction boundary should normally correspond to a business operation that must succeed or fail as one unit.

---

## Exercise: Basic Atomicity

Suppose an order creation workflow performs:

```text
1. Insert order
2. Insert payment
3. Reserve inventory
```

The third operation fails because inventory is unavailable.

### Tasks

Determine what happens if each operation executes without a transaction.

Then redesign the workflow so that:

```text
Order insert
+
Payment insert
+
Inventory reservation
```

either all succeed or all roll back.

Explain why atomicity belongs in the database transaction rather than being simulated with application-level flags.

---

## Exercise: Transaction Boundary

Consider:

```text
POST /orders
```

The application performs:

```text
Validate request
Create order
Reserve inventory
Create payment record
Send confirmation email
Publish Kafka event
```

### Tasks

Determine which operations should belong inside the database transaction.

Evaluate:

| Operation | Inside DB transaction? | Reason |
|---|---|---|
| Validate request | Usually no | Pure application work |
| Create order | Yes | Durable state |
| Reserve inventory | Yes | Business invariant |
| Create payment record | Yes | Transactional state |
| Send email | No | External side effect |
| Publish Kafka event | Usually no direct dependency | Use outbox pattern |

Design the transaction boundary.

---

## Exercise: External API Inside Transaction

Consider:

```python
with transaction.atomic():
    order = create_order()
    response = payment_provider.charge(order)
    mark_order_paid(order)
```

### Tasks

Identify the problems with this design.

Consider:

- Network latency.
- External timeout.
- Connection occupancy.
- Database locks.
- Payment provider retries.
- Transaction rollback.
- Ambiguous external result.

Redesign the workflow so that the database transaction remains short.

---

## Exercise: Lost Update

Two requests execute simultaneously:

```text
Initial balance = 100
```

Request A:

```text
Read balance = 100
Set balance = 80
```

Request B:

```text
Read balance = 100
Set balance = 70
```

The final balance becomes:

```text
70
```

instead of:

```text
10
```

### Tasks

Explain the lost-update problem.

Compare these solutions:

- Row locking.
- Atomic SQL update.
- Optimistic concurrency.
- Serializable isolation.

Identify the simplest safe solution for a debit operation.

---

## Exercise: Atomic Update

Instead of:

```sql
SELECT balance
FROM accounts
WHERE id = $1;
```

followed by application-side arithmetic, design:

```sql
UPDATE accounts
SET balance = balance - $2,
    version = version + 1,
    updated_at = now()
WHERE id = $1
  AND balance >= $2;
```

### Tasks

Determine how to detect insufficient funds.

Determine why this approach can avoid a read-modify-write race.

Explain why the database expression:

```sql
balance = balance - $2
```

is safer than:

```text
read balance
→ calculate in Python
→ write balance
```

for this operation.

---

## Exercise: Pessimistic Locking

Implement an account transfer using:

```sql
SELECT id, balance
FROM accounts
WHERE id = $1
FOR UPDATE;
```

### Tasks

Design a transaction that:

1. Locks the source account.
2. Locks the destination account.
3. Validates the source balance.
4. Decreases the source balance.
5. Increases the destination balance.
6. Commits atomically.

Explain:

- What `FOR UPDATE` protects.
- When the lock is released.
- What happens when another transaction tries to update the same row.
- Why transaction duration matters.

---

## Exercise: Deadlock

Consider two transactions:

```text
Transaction A:
lock account 1
lock account 2

Transaction B:
lock account 2
lock account 1
```

### Tasks

Explain how a deadlock occurs.

Design a consistent lock ordering:

```text
Always lock lower account ID first.
```

For example:

```python
first_id, second_id = sorted([source_id, destination_id])
```

Then acquire locks in that order.

Explain why deterministic ordering reduces deadlocks.

---

## Exercise: Deadlock Retry

PostgreSQL can terminate a transaction because of a deadlock.

The SQLSTATE is:

```text
40P01
```

### Tasks

Design retry behavior.

Your retry strategy should include:

- Whole-transaction retry.
- Bounded attempts.
- Exponential backoff.
- Jitter.
- Idempotency.
- Logging.
- Metrics.

Explain why retrying only the failed SQL statement is generally insufficient after PostgreSQL has aborted the transaction.

---

## Exercise: Serialization Failure

Use:

```text
SERIALIZABLE
```

for a transaction involving two concurrent requests.

### Tasks

Construct a workload that can produce:

```text
serialization_failure
```

PostgreSQL SQLSTATE:

```text
40001
```

Design a retry strategy.

Explain why serialization failures are expected behavior under serializable concurrency rather than necessarily an infrastructure failure.

---

## Exercise: Isolation Levels

Compare:

| Isolation level | Exercise |
|---|---|
| Read Committed | Default PostgreSQL behavior |
| Repeatable Read | Stable transaction snapshot |
| Serializable | Strongest transactional isolation |

### Tasks

For each level, investigate:

- Visibility.
- Concurrent updates.
- Serialization failures.
- Performance.
- Locking behavior.
- Suitable workloads.

Explain why stronger isolation can increase retry requirements and reduce concurrency.

---

## Exercise: Non-Repeatable Read

Create two concurrent transactions.

Transaction A:

```text
BEGIN
SELECT balance FROM accounts WHERE id = 1;
```

Transaction B:

```text
BEGIN
UPDATE accounts
SET balance = 500
WHERE id = 1;
COMMIT;
```

Transaction A then reads the account again.

### Tasks

Test the behavior under PostgreSQL's default isolation level.

Then repeat under:

```text
REPEATABLE READ
```

Explain the difference in visibility.

---

## Exercise: Phantom-Style Behavior

Construct a transaction that counts:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = $1
  AND status = 'pending';
```

Then have another transaction insert a matching order.

### Tasks

Repeat the experiment under different isolation levels.

Determine whether the original transaction observes the new row.

Explain the difference between:

```text
statement snapshot
```

and:

```text
transaction snapshot
```

in PostgreSQL.

---

## Exercise: `SELECT FOR UPDATE`

Consider:

```sql
SELECT id, available_quantity
FROM inventory
WHERE product_id = $1
FOR UPDATE;
```

### Tasks

Design a stock reservation transaction.

Determine:

- Which row is locked.
- How long the lock remains.
- What concurrent reservations experience.
- What happens when inventory reaches zero.
- How high contention affects throughput.

Explain why row-level locking can protect correctness but become a scalability bottleneck for extremely hot products.

---

## Exercise: `NOWAIT`

Use:

```sql
SELECT id, available_quantity
FROM inventory
WHERE product_id = $1
FOR UPDATE NOWAIT;
```

### Tasks

Design an API behavior when the row is already locked.

Consider:

```text
HTTP 409
HTTP 429
retry
queue
```

Determine which response is appropriate based on the business semantics.

Explain why `NOWAIT` is useful when waiting for a lock would exceed the request's latency budget.

---

## Exercise: `SKIP LOCKED`

Design a database-backed job queue:

```sql
SELECT id
FROM jobs
WHERE status = 'pending'
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 10;
```

### Tasks

Design multiple workers that claim jobs concurrently.

Determine:

- Why workers do not block each other.
- How jobs transition to `processing`.
- How failures are recovered.
- Whether starvation is possible.
- How visibility timeouts or leases might be implemented.

Explain why `SKIP LOCKED` is useful for queue-like workloads but is not a general concurrency solution.

---

## Exercise: Django Transaction

Implement an order workflow using:

```python
from django.db import transaction

with transaction.atomic():
    order = create_order()
    reserve_inventory(order)
    create_payment(order)
```

### Tasks

Determine:

- What happens when `reserve_inventory()` raises an exception.
- What happens to `order`.
- How nested `atomic()` blocks behave.
- When database changes become durable.

Then add:

```python
transaction.on_commit(...)
```

for an external notification.

Explain why `on_commit()` is safer than publishing the notification before commit.

---

## Exercise: Django `select_for_update`

Implement:

```python
from django.db import transaction

with transaction.atomic():
    account = (
        Account.objects
        .select_for_update()
        .get(id=account_id)
    )

    account.balance -= amount
    account.save(update_fields=["balance"])
```

### Tasks

Determine:

- Which row is locked.
- How long it remains locked.
- What happens under concurrent requests.
- What happens if the transaction raises an exception.

Compare this with an atomic `UPDATE`.

---

## Exercise: SQLAlchemy Transaction

Design a FastAPI transaction using SQLAlchemy.

Example:

```python
with session.begin():
    order = Order(...)
    session.add(order)

    reserve_inventory(session, product_id, quantity)
    create_payment(session, order)
```

### Tasks

Determine:

- When the transaction begins.
- When it commits.
- What causes rollback.
- How exceptions propagate.
- What happens to the SQLAlchemy session after rollback.

Explain why transaction ownership should be clear in service-layer code.

---

## Exercise: Savepoints

Consider:

```sql
BEGIN;

INSERT INTO orders (...);

SAVEPOINT payment_attempt;

INSERT INTO payments (...);

ROLLBACK TO SAVEPOINT payment_attempt;

COMMIT;
```

### Tasks

Determine which changes survive.

Explain:

- Savepoint creation.
- Partial rollback.
- Nested transaction abstractions.
- When savepoints are useful.
- Why savepoints do not create independent durable transactions.

---

## Exercise: Constraint Failure

Create:

```sql
INSERT INTO accounts (
    customer_id,
    balance
)
VALUES (1, -100);
```

The check constraint fails.

### Tasks

Determine the PostgreSQL transaction state after the error.

Try another statement before rollback.

Explain why the transaction is considered failed and why a rollback is required before continuing with the transaction.

---

## Exercise: Transaction State

Construct:

```sql
BEGIN;

INSERT INTO orders (...);

-- Force an error

SELECT * FROM orders;

ROLLBACK;
```

### Tasks

Observe the behavior after the error.

Document these states:

```text
Idle
Transaction started
Active
Failed transaction
Committed
Rolled back
```

Explain why application code must not assume that a transaction remains usable after an SQL error.

---

## Exercise: Idempotent Payment Creation

Suppose:

```text
POST /payments
```

can be retried because of network failures.

The request contains:

```text
Idempotency-Key: payment-abc-123
```

### Tasks

Design a transaction that ensures the payment is not created twice.

Consider:

```sql
UNIQUE (idempotency_key)
```

Determine how the application handles:

```text
first request succeeds
database commits
response is lost
client retries
```

Explain why database uniqueness is stronger than relying only on application memory.

---

## Exercise: Commit Uncertainty

Consider:

```text
Application
   ↓
COMMIT
   ↓
PostgreSQL commits
   ↓
Network failure
   ↓
Application receives timeout
```

The application does not know whether the transaction committed.

### Tasks

Design a recovery strategy.

Consider:

- Idempotency keys.
- Unique constraints.
- Querying transaction state through a business identifier.
- Safe retry.
- Avoiding duplicate side effects.

Explain why:

```text
timeout ≠ rollback
```

---

## Exercise: Transactional Outbox

An order must be stored and an event must eventually be published.

Design:

```text
orders
outbox_events
```

inside the same transaction.

Example:

```sql
BEGIN;

INSERT INTO orders (
    customer_id,
    status,
    total_amount
)
VALUES ($1, 'pending', $2)
RETURNING id;

INSERT INTO outbox_events (
    aggregate_type,
    aggregate_id,
    event_type,
    payload
)
VALUES (
    'order',
    $3,
    'OrderCreated',
    $4
);

COMMIT;
```

### Tasks

Design a worker that publishes unpublished events.

Explain why this avoids:

```text
database committed
Kafka publish failed
```

without requiring a distributed transaction between PostgreSQL and Kafka.

---

## Exercise: Outbox Idempotency

Suppose the outbox worker:

```text
publishes event
↓
crashes before marking published
```

The same event may be published again.

### Tasks

Design consumers that tolerate duplicates.

Consider:

- Event IDs.
- Consumer deduplication.
- Idempotent state transitions.
- Unique constraints.
- Kafka delivery semantics.

Explain why an outbox pattern does not automatically guarantee exactly-once business effects.

---

## Exercise: Redis and Transactions

Consider:

```text
PostgreSQL transaction
+
Redis cache update
```

### Tasks

Determine why this is unsafe:

```text
BEGIN
update PostgreSQL
update Redis
COMMIT
```

If PostgreSQL later rolls back, Redis may already contain the new value.

Design safer alternatives:

- Invalidate cache after commit.
- `transaction.on_commit()`.
- Versioned cache entries.
- Event-driven invalidation.

Explain why Redis should generally not be treated as part of the PostgreSQL transaction.

---

## Exercise: Kafka and Database Transactions

Consider:

```text
BEGIN
INSERT order
COMMIT
publish Kafka event
```

Kafka publishing fails.

### Tasks

Determine the resulting system state.

Then consider:

```text
publish Kafka event
BEGIN
INSERT order
COMMIT
```

Determine the failure modes.

Compare both with the transactional outbox pattern.

---

## Exercise: Celery and Transactions

A Django request creates an order and immediately schedules:

```python
send_order_confirmation.delay(order.id)
```

inside the transaction.

### Tasks

Construct a failure where Celery consumes the task before the order transaction commits.

Determine what the worker sees.

Redesign using:

```python
transaction.on_commit(
    lambda: send_order_confirmation.delay(order.id)
)
```

Explain why workers should not assume database state is visible before the creating transaction commits.

---

## Exercise: Long Transaction

Consider:

```python
with transaction.atomic():
    orders = load_large_dataset()

    for order in orders:
        process(order)

    call_external_service()
```

### Tasks

Identify:

- Lock duration.
- Connection occupancy.
- Snapshot lifetime.
- MVCC cleanup implications.
- Rollback cost.
- Failure impact.

Redesign the workflow so that expensive processing happens outside the database transaction whenever possible.

---

## Exercise: Idle in Transaction

Find sessions using:

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

### Tasks

Determine:

- How long each transaction has been open.
- Whether locks may still be held.
- Whether old snapshots may delay cleanup.
- Whether application connection handling is responsible.

Design monitoring and timeout controls for idle transactions.

---

## Exercise: Lock Timeout

Configure:

```sql
SET LOCAL lock_timeout = '2s';
```

### Tasks

Construct a lock conflict.

Determine what happens when the transaction waits longer than two seconds.

Compare:

```text
lock_timeout
statement_timeout
```

Explain why they solve different problems.

---

## Exercise: Statement Timeout

Use:

```sql
SET LOCAL statement_timeout = '5s';
```

### Tasks

Construct an expensive query.

Determine:

- When PostgreSQL cancels it.
- What happens to the transaction.
- What application behavior should follow.
- Whether retries are safe.

Explain why statement timeout should be designed together with API and connection-pool timeout budgets.

---

## Exercise: Retry Storm

Suppose a service retries a failed transaction three times.

The database becomes slow.

Model:

```text
100 requests
   ↓
100 DB attempts

timeouts
   ↓
300 retries

timeouts
   ↓
900 additional attempts
```

### Tasks

Determine how retries amplify load.

Design:

- Maximum attempts.
- Backoff.
- Jitter.
- Timeout budgets.
- Idempotency.
- Retry classification.

Explain why retry behavior is part of transaction architecture.

---

## Exercise: Transaction Retry Boundary

Suppose this operation fails with a serialization error:

```text
BEGIN
read
update
commit
```

### Tasks

Determine whether the application should retry:

```text
only UPDATE
```

or:

```text
entire transaction
```

Explain why the transaction's complete read/write decision must normally be repeated.

---

## Exercise: Deadlock vs Lock Contention

Construct:

```text
Transaction A waits for B
```

without creating a cycle.

Then construct:

```text
A waits for B
B waits for A
```

### Tasks

Explain the difference:

| Condition | Description |
|---|---|
| Lock contention | Transaction waits for another transaction |
| Deadlock | Transactions form a cycle and cannot proceed |

Determine the appropriate operational response for each.

---

## Exercise: Transaction and Connection Pool

Suppose:

```text
20 application workers
10 DB connections
```

A transaction lasts:

```text
2 seconds
```

### Tasks

Estimate how long requests may wait under sustained load.

Then reduce transaction duration to:

```text
200 ms
```

Explain the impact on:

- Connection utilization.
- Throughput.
- Queueing.
- Tail latency.
- Lock duration.

Relate transaction duration to connection-pool sizing.

---

## Exercise: Multi-Row Lock Ordering

Suppose an operation updates:

```text
10 inventory rows
```

Another operation updates the same rows in a different order.

### Tasks

Design a deterministic ordering strategy.

For example:

```sql
SELECT product_id
FROM inventory
WHERE product_id = ANY($1)
ORDER BY product_id
FOR UPDATE;
```

Then perform updates in the same order.

Explain why multi-row operations are a common source of deadlocks.

---

## Exercise: Hot Row

A product has:

```text
available_quantity = 1,000,000
```

and receives:

```text
50,000 reservation requests/sec
```

All transactions execute:

```sql
UPDATE inventory
SET available_quantity = available_quantity - 1
WHERE product_id = $1
  AND available_quantity > 0;
```

### Tasks

Determine the correctness properties.

Then analyze the scalability bottleneck.

Evaluate:

- Row locking.
- Queue serialization.
- Partitioned inventory.
- Sharded counters.
- Redis coordination.
- Kafka-based serialization.

Explain why atomic SQL can be correct but still insufficient for extreme contention.

---

## Exercise: Optimistic Concurrency

Use:

```sql
UPDATE accounts
SET balance = $1,
    version = version + 1
WHERE id = $2
  AND version = $3;
```

### Tasks

Determine how the application detects a conflict.

Explain:

```text
UPDATE count = 0
```

versus:

```text
UPDATE count = 1
```

Design retry or conflict behavior.

Compare optimistic concurrency with `SELECT FOR UPDATE`.

---

## Exercise: Version-Based API Updates

A REST API receives:

```json
{
  "balance": 500,
  "version": 7
}
```

The database currently contains:

```text
version = 8
```

### Tasks

Determine whether the update should succeed.

Design an optimistic-concurrency API response.

Consider:

```text
409 Conflict
```

Explain why silently overwriting the newer value is dangerous.

---

## Exercise: Constraint vs Application Validation

Suppose application code performs:

```text
if balance >= amount:
    UPDATE balance
```

### Tasks

Explain why another concurrent request can invalidate the assumption between the check and update.

Replace the logic with a database-enforced operation.

Determine why database constraints and atomic statements should enforce critical invariants.

---

## Exercise: Foreign Key Concurrency

Create a parent/child relationship:

```text
orders
payments
```

### Tasks

Investigate the locks involved when:

```text
Parent row is modified
Child row is inserted
```

Determine how foreign keys can introduce lock interactions.

Explain why seemingly unrelated statements can participate in deadlocks through constraints.

---

## Exercise: DDL and Transactions

Consider:

```sql
ALTER TABLE orders
ADD COLUMN processed_at timestamptz;
```

### Tasks

Determine how DDL can interact with concurrent transactions.

Investigate:

- Table locks.
- Long-running transactions.
- Lock waits.
- Deployment traffic.

Then design a safer production migration strategy.

---

## Exercise: `CREATE INDEX CONCURRENTLY`

Create an index on a large table:

```sql
CREATE INDEX CONCURRENTLY orders_customer_created_idx
ON orders (customer_id, created_at DESC);
```

### Tasks

Determine:

- Why concurrent index creation reduces blocking.
- Why it has operational trade-offs.
- Why it cannot run inside a transaction block.
- How failures can leave an invalid index.
- How to monitor the operation.

Explain why migration design and transaction design intersect.

---

## Exercise: Transaction and Read Replica

A write transaction commits on the primary.

Immediately afterward:

```text
GET /orders/{id}
```

is routed to a read replica.

### Tasks

Explain how replica lag can cause stale reads.

Design:

- Primary routing after write.
- Read-your-writes handling.
- LSN-aware strategies where appropriate.
- Fallback behavior.

Explain why transaction commit and replica visibility are separate concerns.

---

## Exercise: Transaction and Cache Consistency

An order changes:

```text
pending → completed
```

The database commits, but Redis still contains:

```text
pending
```

### Tasks

Design a cache invalidation strategy.

Compare:

```text
update DB
commit
invalidate cache
```

with:

```text
update DB
update cache
commit
```

Explain why the first approach is generally safer for database-backed cache consistency.

---

## Exercise: Transaction and Search Index

An order is stored in PostgreSQL and indexed in a search system.

### Tasks

Design behavior when:

```text
PostgreSQL commit succeeds
search indexing fails
```

Determine whether the search index should be treated as part of the database transaction.

Design an asynchronous recovery mechanism.

---

## Exercise: Distributed Transaction

Two microservices own:

```text
Order Service
Payment Service
```

The workflow is:

```text
Create order
↓
Charge payment
↓
Mark order completed
```

### Tasks

Explain why a single PostgreSQL transaction cannot normally cover both services.

Evaluate:

- Two-phase commit.
- Saga.
- Orchestration.
- Choreography.
- Compensation.
- Idempotency.

Design a practical Saga for the workflow.

---

## Exercise: Saga Compensation

Suppose:

```text
Order created
Payment charged
Inventory reservation fails
```

### Tasks

Design the compensation:

```text
Refund payment
Cancel order
```

Determine:

- Which operations are reversible.
- Which operations are not.
- How retries are handled.
- How duplicate events are handled.
- How workflow state is persisted.

Explain why compensation is not equivalent to rollback.

---

## Exercise: Transactional State Machine

An order has states:

```text
pending
processing
completed
cancelled
```

### Tasks

Define legal transitions.

For example:

```text
pending → processing
processing → completed
pending → cancelled
processing → cancelled
```

Reject:

```text
completed → pending
```

Design a transaction that validates state transitions atomically.

Explain why state transitions are business invariants rather than simple field assignments.

---

## Exercise: Concurrent State Transition

Two workers simultaneously execute:

```text
pending → processing
```

### Tasks

Design an atomic transition:

```sql
UPDATE orders
SET status = 'processing',
    updated_at = now()
WHERE id = $1
  AND status = 'pending';
```

Determine how the application detects whether it won the transition.

Explain why checking status in Python before issuing the update creates a race window.

---

## Exercise: Queue Claiming

Design a worker query:

```sql
SELECT id
FROM orders
WHERE status = 'pending'
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

### Tasks

Design the transaction that changes the rows to:

```text
processing
```

Determine how to avoid:

- Duplicate claims.
- Long transactions.
- Worker crashes.
- Permanent stuck states.

Evaluate leases or recovery timestamps.

---

## Exercise: Batch Transaction

Process:

```text
1,000,000 rows
```

using transactions.

Compare:

```text
one transaction for 1,000,000 rows
```

with:

```text
1,000 transactions × 1,000 rows
```

### Tasks

Evaluate:

- Lock duration.
- WAL.
- Rollback cost.
- Replica lag.
- Vacuum pressure.
- Connection occupancy.
- Failure recovery.

Explain why batching often improves operational safety even though it changes transactional semantics.

---

## Exercise: Large Backfill

A new column must be populated for:

```text
500 million rows
```

### Tasks

Design a migration workflow:

```text
Add nullable column
        ↓
Deploy compatible application
        ↓
Batch backfill
        ↓
Validate
        ↓
Enable required constraint
        ↓
Deploy final application
```

Consider:

- Batch size.
- Keyset pagination.
- Progress tracking.
- Throttling.
- Lock contention.
- Replica lag.
- WAL.
- Retry safety.

Explain why schema migration and data migration should often be separate operational steps.

---

## Exercise: Transaction and Backfill Failure

A backfill processes:

```text
rows 1–5,000
```

and then crashes.

### Tasks

Design restart behavior.

Determine whether the job should:

- Restart from zero.
- Resume from a checkpoint.
- Recalculate processed state.
- Use idempotent updates.

Explain why durable progress should not rely only on an in-memory worker variable.

---

## Exercise: Transaction and Idempotent Backfill

Design:

```sql
UPDATE customers
SET normalized_email = lower(email)
WHERE id > $1
  AND id <= $2;
```

### Tasks

Determine whether rerunning the same batch is safe.

Compare with a non-idempotent operation.

Explain why idempotency simplifies:

- Worker retries.
- Crash recovery.
- Deployment interruptions.
- Manual reruns.

---

## Exercise: Read-Only Transaction

Execute:

```sql
BEGIN READ ONLY;

SELECT ...
SELECT ...

COMMIT;
```

### Tasks

Determine when read-only transactions are useful.

Consider:

- Reporting.
- Consistency across multiple reads.
- Preventing accidental writes.
- Replica workloads.

Explain why read-only does not automatically mean inexpensive.

---

## Exercise: Transaction Snapshot

Start:

```sql
BEGIN;
```

Then perform multiple reads while another transaction changes data.

### Tasks

Compare PostgreSQL behavior under:

```text
READ COMMITTED
REPEATABLE READ
```

Determine when the same transaction can observe different committed states.

Explain why snapshot semantics matter for reports and multi-query business decisions.

---

## Exercise: Transaction Isolation vs Locks

A developer proposes:

> "We can use SERIALIZABLE everywhere instead of row locks."

### Tasks

Evaluate the statement.

Compare:

```text
Serializable isolation
Pessimistic row locking
Optimistic concurrency
Atomic SQL
```

Determine when each is appropriate.

Explain why isolation level and explicit locking are complementary tools rather than interchangeable solutions.

---

## Exercise: Nested Transactions

Consider application code:

```python
with transaction.atomic():
    create_order()

    with transaction.atomic():
        create_payment()
```

### Tasks

Determine how Django implements nested atomic blocks.

Explain the role of savepoints.

Determine what happens if the inner block fails and is handled.

Explain why nested `atomic()` does not normally create an independent database transaction.

---

## Exercise: Exception Handling

Consider:

```python
try:
    with transaction.atomic():
        create_order()
        create_payment()
except Exception:
    pass
```

### Tasks

Determine whether swallowing the exception is safe.

Then consider:

```python
with transaction.atomic():
    try:
        create_order()
        create_payment()
    except Exception:
        pass
```

Explain why exception handling placement matters for transaction state and rollback semantics.

---

## Exercise: Transaction Logging

Design structured transaction logs containing:

```text
request_id
transaction_id
database
operation
duration
rows_affected
retry_attempt
error_code
```

### Tasks

Determine which information is useful for diagnosing:

- Deadlocks.
- Serialization failures.
- Long transactions.
- Rollbacks.
- Retry storms.
- Connection-pool pressure.

Avoid logging sensitive data such as passwords, tokens, or unnecessary customer information.

---

## Exercise: Transaction Metrics

Design metrics for:

```text
transaction_duration
transaction_commit_count
transaction_rollback_count
deadlock_count
serialization_failure_count
lock_wait_duration
idle_transaction_duration
retry_count
```

### Tasks

Determine which metrics should have:

- Count.
- Rate.
- Histogram.
- Percentiles.
- Labels.

Avoid high-cardinality labels such as raw user IDs or arbitrary SQL text.

---

## Exercise: Production Incident

A production service reports:

```text
p99 latency ↑
DB connections ↑
lock waits ↑
deadlocks ↑
retry count ↑
```

### Tasks

Construct a hypothesis tree.

Investigate:

1. Recent deployment.
2. Transaction duration.
3. Lock ordering.
4. Hot rows.
5. Connection-pool utilization.
6. Query latency.
7. Retry behavior.
8. Background workers.
9. Long-running transactions.
10. Recent migration activity.

Determine whether increasing the connection pool is likely to help or worsen the incident.

---

## Exercise: Transaction Failure Matrix

Create a failure matrix:

| Failure | Transaction result | Retry? | Required protection |
|---|---|---|---|
| Constraint violation | Rollback/error | Usually no | Correct input |
| Deadlock | Aborted | Usually yes | Idempotency + backoff |
| Serialization failure | Aborted | Usually yes | Whole-transaction retry |
| Lock timeout | Statement/transaction error depending context | Sometimes | Retry classification |
| Statement timeout | Statement cancelled | Sometimes | Idempotency + timeout budget |
| Network timeout before commit outcome known | Unknown | Carefully | Idempotency |
| Application exception | Rollback if propagated | Depends | Correct transaction boundary |

Expand this matrix with additional failure modes.

---

## Exercise: Transaction Design Review

Review this workflow:

```text
BEGIN

validate customer
call payment provider
update Redis
insert order
publish Kafka event
send email
update inventory
run expensive calculation

COMMIT
```

### Tasks

Identify every design problem.

Redesign it into:

```text
Application validation
        ↓
Short DB transaction
        ↓
Durable database state
        ↓
Outbox/event processing
        ↓
External side effects
        ↓
Asynchronous work
```

Justify every boundary.

---

## Exercise: Senior Transaction Architecture

Design a production order workflow with:

```text
POST /orders
```

Requirements:

- Inventory must not become negative.
- Duplicate requests must not create duplicate orders.
- Payment state must be durable.
- Kafka event must eventually be published.
- Redis cache must remain consistent enough for reads.
- Email must not block the database transaction.
- Celery workers may retry.
- Database deadlocks may occur.
- PostgreSQL may fail over.
- Requests may time out after commit.
- Read replicas may lag.

### Tasks

Produce:

1. Transaction boundary.
2. SQL constraints.
3. Locking strategy.
4. Idempotency strategy.
5. Outbox design.
6. Retry strategy.
7. Cache invalidation strategy.
8. Worker strategy.
9. Replica-read strategy.
10. Monitoring strategy.
11. Failure recovery strategy.

---

## Common Transaction Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Huge transaction | Treating atomicity as unlimited scope | Keep transactions short |
| External API inside transaction | Convenient control flow | Use state machines/outbox |
| Publishing before commit | Assuming DB state already exists | Publish after commit/outbox |
| Updating Redis inside transaction | Treating cache as transactional | Invalidate/update after commit |
| Assuming timeout means rollback | Confusing network failure with transaction result | Use idempotency and reconciliation |
| Retrying only failed statement | Ignoring transaction abort state | Retry whole transaction |
| Retrying everything | Treating all errors as transient | Classify failures |
| No lock ordering | Independent code paths acquire locks differently | Establish deterministic order |
| Increasing pool size during lock incident | Treating waiting as lack of capacity | Fix contention |
| One huge backfill transaction | Optimizing for simplicity | Use bounded batches |
| Application-only validation | Race conditions | Enforce invariants in SQL |
| Ignoring constraints | Assuming code is enough | Use database constraints |
| Swallowing exceptions | Avoiding error propagation | Preserve transaction semantics |
| Assuming nested transactions are independent | Misunderstanding savepoints | Understand transaction scope |
| Using SERIALIZABLE everywhere | Assuming strongest is always best | Choose isolation deliberately |
| Ignoring idempotency | Assuming requests execute once | Design for retries |
| Holding locks during external work | Convenient workflow | Move external calls outside transaction |
| Treating outbox as exactly-once | Confusing delivery with business effects | Make consumers idempotent |
| Ignoring replica lag | Assuming commit means every replica sees it | Design read consistency |
| Logging sensitive transaction data | Over-debugging production | Redact and minimize |

---

## Production Transaction Checklist

### Transaction Boundary

- [ ] Transaction represents a meaningful business operation.
- [ ] External network calls are outside the transaction.
- [ ] Expensive CPU work is outside the transaction where possible.
- [ ] Transactions are short.
- [ ] Connection occupancy is understood.
- [ ] Lock duration is understood.

### Correctness

- [ ] Critical invariants are enforced by the database.
- [ ] Atomic SQL is used for atomic state changes.
- [ ] Race conditions have been analyzed.
- [ ] Locking strategy is explicit where required.
- [ ] State transitions are validated atomically.
- [ ] Multi-row operations have deterministic lock ordering.

### Reliability

- [ ] Deadlock retries are bounded.
- [ ] Serialization retries cover the whole transaction.
- [ ] Retry backoff includes jitter.
- [ ] Idempotency exists for retryable operations.
- [ ] Commit uncertainty is handled.
- [ ] External side effects have recovery mechanisms.

### Integration

- [ ] Kafka publication does not depend on an unsafe dual-write.
- [ ] Transactional outbox is used where appropriate.
- [ ] Celery tasks do not run before required database state commits.
- [ ] Redis invalidation occurs after commit.
- [ ] Read-after-write behavior is defined.
- [ ] Replica lag is considered.

### Operations

- [ ] Transaction duration is monitored.
- [ ] Lock waits are monitored.
- [ ] Deadlocks are monitored.
- [ ] Serialization failures are monitored.
- [ ] Rollback rates are monitored.
- [ ] Retry rates are monitored.
- [ ] Idle transactions are monitored.
- [ ] Connection-pool utilization is monitored.

### Deployment

- [ ] Migrations do not unexpectedly hold long locks.
- [ ] Backfills are incremental.
- [ ] Large writes are throttled.
- [ ] Replica impact is understood.
- [ ] WAL impact is understood.
- [ ] Rollback/forward-recovery strategy exists.

---

## Interview Traps

### Does a transaction guarantee that external APIs roll back?

No. PostgreSQL transactions control PostgreSQL state. External systems require separate reliability patterns such as idempotency, state machines, outbox, and compensation.

### Does `COMMIT` guarantee that every replica immediately sees the data?

No. With asynchronous replication, replicas may lag.

### Should every database operation be wrapped in a transaction?

Not necessarily. Transaction scope should match business atomicity and consistency requirements.

### Is a longer transaction safer?

Usually not. Longer transactions increase lock duration, connection occupancy, rollback cost, and MVCC cleanup pressure.

### Does `SELECT FOR UPDATE` prevent every race condition?

No. It protects selected rows against conflicting concurrent operations, but correctness still depends on transaction scope, access patterns, constraints, and consistent locking.

### Is `SERIALIZABLE` always the safest production choice?

It provides strong isolation but can increase serialization failures and retries. The correct isolation level depends on workload and business requirements.

### Does retrying a deadlocked statement fix the transaction?

Usually no. PostgreSQL aborts the transaction, so the complete transaction should generally be retried.

### Does a database timeout mean the transaction did not commit?

Not necessarily. A network failure can occur after the database has committed but before the client receives the result.

### Does a transactional outbox provide exactly-once delivery?

No. It makes the database state and outbox record atomic, but event publication can be retried. Consumers should be idempotent.

### Are nested transactions independent transactions?

Normally no. PostgreSQL savepoints provide partial rollback within the surrounding transaction.

### Why are database constraints important if application code validates everything?

Because concurrent requests, alternate code paths, background workers, migrations, and bugs can bypass application assumptions. Database constraints provide durable enforcement.

---

## Senior-Level Transaction Questions

For every production transaction, ask:

1. What business invariant requires atomicity?
2. What is the exact transaction boundary?
3. Which operations can safely occur outside the transaction?
4. What locks are acquired?
5. In what order are locks acquired?
6. How long are locks held?
7. What isolation level is required?
8. Can two concurrent requests make conflicting decisions?
9. Can the operation use atomic SQL instead of read-modify-write?
10. Which constraints enforce correctness?
11. What happens after a constraint error?
12. What happens after a deadlock?
13. What happens after a serialization failure?
14. What happens after a lock timeout?
15. What happens if the client times out after commit?
16. Can the operation be retried safely?
17. Is an idempotency key required?
18. Are external side effects involved?
19. Should the outbox pattern be used?
20. Can Redis become stale?
21. Can Kafka events be duplicated?
22. Can Celery tasks execute more than once?
23. Can a read replica be stale?
24. What happens during primary failover?
25. How does the design behave under hot-row contention?
26. What happens when connection pools are exhausted?
27. How does the transaction behave at 10x traffic?
28. How is transaction duration monitored?
29. How are failures correlated with application requests?
30. How is recovery tested?

---

## Final Practice Set

Complete these exercises without consulting reference material:

1. Design a basic atomic transaction.
2. Define a business transaction boundary.
3. Remove external calls from a transaction.
4. Reproduce a lost update.
5. Implement an atomic update.
6. Implement pessimistic locking.
7. Reproduce a deadlock.
8. Design deadlock retries.
9. Reproduce a serialization failure.
10. Compare PostgreSQL isolation levels.
11. Demonstrate non-repeatable reads.
12. Investigate snapshot behavior.
13. Implement `SELECT FOR UPDATE`.
14. Implement `NOWAIT`.
15. Implement `SKIP LOCKED`.
16. Use Django `transaction.atomic()`.
17. Use Django `select_for_update()`.
18. Implement a SQLAlchemy transaction.
19. Use savepoints.
20. Investigate failed transaction state.
21. Design idempotent payment creation.
22. Handle commit uncertainty.
23. Implement a transactional outbox.
24. Design an idempotent outbox consumer.
25. Coordinate database changes with Redis.
26. Coordinate database state with Kafka.
27. Safely enqueue Celery work after commit.
28. Diagnose long transactions.
29. Diagnose idle-in-transaction sessions.
30. Configure lock timeouts.
31. Configure statement timeouts.
32. Design bounded transaction retries.
33. Define the correct retry boundary.
34. Compare lock contention with deadlocks.
35. Analyze pool pressure caused by long transactions.
36. Design deterministic multi-row lock ordering.
37. Analyze a hot-row bottleneck.
38. Implement optimistic concurrency.
39. Design version-based API updates.
40. Enforce invariants with database constraints.
41. Investigate foreign-key lock interactions.
42. Analyze DDL transaction interactions.
43. Deploy a large index safely.
44. Handle transactions with read replicas.
45. Design cache consistency after commit.
46. Design asynchronous search indexing.
47. Design a distributed Saga.
48. Implement compensation logic.
49. Design a transactional state machine.
50. Implement concurrent state transitions.
51. Build a database-backed queue.
52. Compare large single transactions with batches.
53. Design a large-table backfill.
54. Design restartable backfill progress.
55. Implement an idempotent backfill.
56. Use read-only transactions appropriately.
57. Compare transaction snapshots.
58. Compare isolation and explicit locks.
59. Analyze nested transaction behavior.
60. Design safe exception handling around transactions.
61. Design transaction observability.
62. Diagnose a production lock/retry incident.
63. Build a transaction failure matrix.
64. Review a production transaction boundary.
65. Design a complete order workflow with PostgreSQL, Redis, Kafka, Celery, and read replicas.

## Key Takeaways

- **Transactions should represent business atomicity:** keep the boundary focused, short, and independent of slow external operations whenever possible.
- **Concurrency requires explicit reasoning:** use atomic SQL, constraints, optimistic concurrency, or deterministic locking based on the actual invariant rather than relying on application-side checks.
- **Retries must be transaction-aware:** deadlocks and serialization failures generally require retrying the whole transaction with bounded backoff, jitter, and idempotency.
- **Database transactions do not extend automatically to other systems:** use outbox, idempotency, state machines, and compensation for Redis, Kafka, Celery, external APIs, and distributed workflows.
- **Production transaction design is operational design:** monitor duration, lock waits, rollbacks, deadlocks, retries, connection pressure, replica lag, and recovery behavior under failure.