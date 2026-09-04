# 17- Concurrency Exercises

## Overview

Concurrency is the behavior of multiple requests, workers, transactions, or services operating on shared state at overlapping times.

For backend engineers, concurrency problems rarely appear as obvious database errors. They usually appear as:

- Lost updates.
- Duplicate operations.
- Negative inventory.
- Incorrect counters.
- Conflicting state transitions.
- Deadlocks.
- Lock contention.
- Serialization failures.
- Duplicate background jobs.
- Stale reads.
- Inconsistent cache state.
- Retry storms.

These exercises focus on reasoning about concurrent execution using PostgreSQL and common backend technologies such as Django, FastAPI, Celery, Redis, Kafka, and microservices.

The core question for every exercise is:

> What happens when two or more actors execute this operation at the same time?

---

## Practice Schema

Use the following PostgreSQL schema throughout the exercises.

```sql
CREATE TABLE accounts (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL,
    balance numeric(12, 2) NOT NULL CHECK (balance >= 0),
    version bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    stock integer NOT NULL CHECK (stock >= 0),
    version bigint NOT NULL DEFAULT 0,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL,
    status text NOT NULL
        CHECK (status IN (
            'pending',
            'processing',
            'completed',
            'cancelled'
        )),
    total_amount numeric(12, 2) NOT NULL CHECK (total_amount >= 0),
    version bigint NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    status text NOT NULL
        CHECK (status IN (
            'pending',
            'paid',
            'failed',
            'refunded'
        )),
    amount numeric(12, 2) NOT NULL,
    idempotency_key text UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE inventory_reservations (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id bigint NOT NULL REFERENCES products(id),
    order_id bigint NOT NULL REFERENCES orders(id),
    quantity integer NOT NULL CHECK (quantity > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (product_id, order_id)
);
```

---

## Concurrency Mental Model

Start every concurrency problem by identifying:

```text
Shared state
    ↓
Concurrent actors
    ↓
Read/write sequence
    ↓
Interleaving
    ↓
Race condition?
    ↓
Required invariant
    ↓
Concurrency control
```

A useful representation is:

```text
Transaction A                 Transaction B

BEGIN                         BEGIN
  │                             │
  ├─ read X                     ├─ read X
  │                             │
  ├─ calculate                  ├─ calculate
  │                             │
  ├─ write X                    ├─ write X
  │                             │
  └─ COMMIT                     └─ COMMIT
```

The important question is not merely whether each transaction is individually correct.

The question is whether **every valid interleaving of concurrent transactions preserves the business invariant**.

---

## Exercise: Identify Shared State

For each operation, identify the shared resource:

| Operation | Shared state |
|---|---|
| Debit account | Account balance |
| Reserve inventory | Product stock |
| Increment counter | Counter row |
| Claim job | Job status |
| Change order state | Order status |
| Create payment | Payment/idempotency key |
| Generate username | Username uniqueness |
| Transfer money | Two account balances |

### Tasks

For each operation:

1. Identify the concurrent actors.
2. Identify the shared state.
3. Define the invariant.
4. Describe a possible race condition.
5. Choose a concurrency-control mechanism.

---

## Exercise: Lost Update

Initial state:

```text
balance = 100
```

Two requests concurrently execute:

```text
Request A:
read balance = 100
calculate 100 - 30
write 70

Request B:
read balance = 100
calculate 100 - 50
write 50
```

### Tasks

Determine the final balance.

Explain why:

```text
100 - 30 - 50 = 20
```

is not guaranteed.

Compare:

- Application-side read/modify/write.
- Atomic SQL.
- `SELECT FOR UPDATE`.
- Optimistic concurrency.
- Serializable isolation.

---

## Exercise: Atomic Counter

Two workers need to increment:

```text
counter = counter + 1
```

A developer proposes:

```sql
SELECT counter
FROM counters
WHERE id = $1;
```

followed by:

```sql
UPDATE counters
SET counter = $value
WHERE id = $1;
```

### Tasks

Explain the race.

Replace it with:

```sql
UPDATE counters
SET counter = counter + 1
WHERE id = $1;
```

Determine why the database-side expression is safer.

Explain why atomic SQL does not necessarily mean the entire surrounding business operation is atomic.

---

## Exercise: Concurrent Inventory Reservation

Initial state:

```text
stock = 10
```

Twenty concurrent requests each attempt to reserve:

```text
quantity = 1
```

### Tasks

Design a safe operation using:

```sql
UPDATE products
SET stock = stock - $2,
    version = version + 1,
    updated_at = now()
WHERE id = $1
  AND stock >= $2;
```

Determine how the application detects failure.

Explain why the final stock cannot become negative.

Then analyze the performance impact when the same product becomes extremely hot.

---

## Exercise: Negative Inventory Race

Consider:

```python
product = Product.objects.get(id=product_id)

if product.stock >= quantity:
    product.stock -= quantity
    product.save()
```

### Tasks

Construct an interleaving that causes overselling.

Explain why the check and update are not atomic.

Redesign the operation using:

- Atomic SQL.
- `select_for_update()`.
- Optimistic concurrency.

Compare the three approaches.

---

## Exercise: Pessimistic Locking

Implement an inventory reservation using:

```sql
BEGIN;

SELECT stock
FROM products
WHERE id = $1
FOR UPDATE;

UPDATE products
SET stock = stock - $2
WHERE id = $1;

COMMIT;
```

### Tasks

Determine:

- Which row is locked.
- When the lock is acquired.
- When the lock is released.
- What concurrent transactions experience.
- What happens if the transaction rolls back.

Explain why locks protect correctness but can reduce throughput under contention.

---

## Exercise: Django Row Locking

Implement:

```python
from django.db import transaction

with transaction.atomic():
    product = (
        Product.objects
        .select_for_update()
        .get(id=product_id)
    )

    if product.stock < quantity:
        raise ValueError("Insufficient stock")

    product.stock -= quantity
    product.save(update_fields=["stock"])
```

### Tasks

Explain the concurrency guarantees.

Determine what happens when two requests execute simultaneously.

Explain why `select_for_update()` must be used inside a transaction.

---

## Exercise: Optimistic Concurrency

Use:

```sql
UPDATE products
SET stock = $new_stock,
    version = version + 1,
    updated_at = now()
WHERE id = $product_id
  AND version = $expected_version;
```

### Tasks

Determine how the application detects a conflict.

Explain the difference between:

```text
UPDATE count = 0
```

and:

```text
UPDATE count = 1
```

Determine when optimistic concurrency is preferable to pessimistic locking.

---

## Exercise: Optimistic Inventory Reservation

Two workers read:

```text
stock = 10
version = 7
```

Worker A reserves 3.

Worker B reserves 4.

Both attempt to update version 7.

### Tasks

Determine which worker succeeds.

Determine what the second worker should do.

Design:

```text
retry
re-read
recalculate
```

Explain why blindly retrying the original write is incorrect.

---

## Exercise: Compare Concurrency Strategies

Compare:

| Strategy | Best suited for | Main cost |
|---|---|---|
| Atomic SQL | Simple state transitions | Limited to operation semantics |
| Row locking | High-conflict critical rows | Lock waits |
| Optimistic concurrency | Low/moderate conflict | Retries/conflicts |
| Serializable | Complex invariants | Serialization failures |
| Queue serialization | Extremely hot resources | Added latency/architecture |

### Tasks

Choose the appropriate mechanism for:

- Account debit.
- Product stock.
- User profile update.
- Hot counter.
- Order state transition.
- Financial transfer.

---

## Exercise: Concurrent Order State Transition

Two workers attempt:

```text
pending → processing
```

Use:

```sql
UPDATE orders
SET status = 'processing',
    version = version + 1,
    updated_at = now()
WHERE id = $1
  AND status = 'pending';
```

### Tasks

Determine what happens when both workers execute concurrently.

Explain why exactly one worker should observe:

```text
rows_affected = 1
```

and the other:

```text
rows_affected = 0
```

Design worker behavior for both cases.

---

## Exercise: Invalid State Transition

An order is:

```text
completed
```

A delayed worker attempts:

```text
completed → processing
```

### Tasks

Design a database operation that rejects the transition.

Explain why:

```python
if order.status == "completed":
    return
```

is not sufficient under concurrency.

Design an atomic state transition.

---

## Exercise: State Machine Concurrency

Valid transitions:

```text
pending → processing
processing → completed
processing → cancelled
pending → cancelled
```

Invalid transitions:

```text
completed → pending
completed → processing
cancelled → processing
```

### Tasks

Design a concurrency-safe state machine.

Consider:

- Conditional `UPDATE`.
- Version numbers.
- Row locks.
- Database constraints.
- Event publication.

Explain why a state transition should be treated as a business invariant.

---

## Exercise: Double Payment

A client submits:

```text
POST /payments
```

twice because of a timeout.

Both requests attempt to charge:

```text
$100
```

### Tasks

Design protection against duplicate payment records.

Use:

```text
Idempotency-Key
```

and:

```sql
UNIQUE (idempotency_key)
```

Determine what happens when two identical requests arrive simultaneously.

Explain why application-level duplicate detection alone is insufficient.

---

## Exercise: Concurrent Username Creation

Two users simultaneously request:

```text
username = "alex"
```

Both applications execute:

```text
SELECT 1
FROM users
WHERE username = 'alex';
```

No row exists.

Both then insert.

### Tasks

Explain the race.

Design a database-level solution using:

```sql
UNIQUE (username)
```

Determine how the application handles the uniqueness violation.

Explain why:

```text
check → insert
```

is not atomic without database enforcement.

---

## Exercise: Duplicate Job Creation

Two API requests concurrently create the same background job.

Example:

```text
Generate monthly report for customer 42
```

### Tasks

Design a uniqueness strategy.

Possible key:

```text
(customer_id, report_month)
```

Create an appropriate unique constraint.

Explain how the constraint prevents duplicate work.

Then discuss whether preventing duplicate job records guarantees the report itself is generated exactly once.

---

## Exercise: Race Condition with `COUNT`

A developer checks:

```sql
SELECT COUNT(*)
FROM active_sessions
WHERE user_id = $1;
```

If the result is below 5, the application inserts another session.

### Tasks

Construct a race where six sessions are created.

Explain why:

```text
COUNT → decision → INSERT
```

is unsafe.

Design alternatives using:

- Database constraints.
- Row locking.
- Advisory locks.
- Atomic allocation.
- Serializable isolation.

---

## Exercise: Unique Constraint as Concurrency Control

Suppose only one active subscription is allowed per customer.

### Tasks

Design a PostgreSQL constraint or unique partial index that enforces:

```text
one active subscription per customer
```

Then analyze two concurrent subscription requests.

Explain why database uniqueness is a concurrency-control mechanism, not merely a data-quality feature.

---

## Exercise: Account Transfer

Transfer:

```text
$50
```

from:

```text
Account A
```

to:

```text
Account B
```

### Tasks

Design a transaction that:

1. Locks both accounts.
2. Validates the source balance.
3. Debits the source.
4. Credits the destination.
5. Commits atomically.

Determine how to prevent deadlocks when another transfer operates in the opposite direction.

---

## Exercise: Transfer Deadlock

Transaction A:

```text
lock account 1
lock account 2
```

Transaction B:

```text
lock account 2
lock account 1
```

### Tasks

Explain the wait cycle.

Redesign both transactions to acquire locks in ascending account ID order.

Explain why deterministic ordering is one of the simplest deadlock-prevention techniques.

---

## Exercise: Multi-Row Concurrency

A bulk operation updates:

```text
products 10, 20, 30
```

Another operation updates:

```text
products 30, 20, 10
```

### Tasks

Determine whether a deadlock is possible.

Redesign both workflows so that rows are always locked in the same order.

Explain why concurrency bugs often emerge only after a system becomes sufficiently parallel.

---

## Exercise: Deadlock Detection

Construct a deadlock in PostgreSQL.

Investigate:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

Then:

```sql
SELECT
    pid,
    locktype,
    relation::regclass,
    transactionid,
    mode,
    granted
FROM pg_locks;
```

### Tasks

Identify:

- Waiting transaction.
- Blocking transaction.
- Locked resource.
- Lock mode.

Explain how PostgreSQL detects and resolves deadlocks.

---

## Exercise: Deadlock Retry

PostgreSQL can abort a transaction with:

```text
SQLSTATE 40P01
```

### Tasks

Design retry behavior using:

```text
attempt 1
↓
failure
↓
backoff + jitter
↓
attempt 2
↓
failure
↓
attempt 3
```

Explain why the whole transaction should normally be retried.

Define a maximum retry budget.

---

## Exercise: Lock Contention

Two transactions access the same product row.

Transaction A holds the lock for:

```text
5 seconds
```

Transaction B waits.

### Tasks

Determine the impact on:

- Request latency.
- Connection pools.
- Throughput.
- p99 latency.
- Worker utilization.

Explain why lock contention can become a system-wide capacity problem.

---

## Exercise: Hot Row

A global counter receives:

```text
50,000 updates/sec
```

All requests update one row.

### Tasks

Determine why the row becomes a bottleneck.

Evaluate:

- Atomic SQL.
- Row locking.
- Sharded counters.
- Redis counters.
- Kafka serialization.
- Periodic aggregation.
- Partitioned counters.

Explain the difference between **correctness** and **scalability**.

---

## Exercise: Redis Counter Race

Multiple workers increment a Redis counter.

Compare:

```text
GET
calculate
SET
```

with:

```text
INCR
```

### Tasks

Explain why `INCR` is safer for the counter operation.

Then discuss whether Redis atomicity automatically provides transactional consistency with PostgreSQL.

---

## Exercise: Redis Lock

A developer proposes:

```text
SET lock_key value NX EX 30
```

to coordinate a critical operation.

### Tasks

Analyze:

- Lock ownership.
- Expiration.
- Worker crash.
- Lock expiration while work continues.
- Duplicate execution.
- Network partitions.
- Fencing tokens.

Explain when Redis-based coordination is appropriate and when a PostgreSQL transaction is the better primitive.

---

## Exercise: Advisory Locks

Use PostgreSQL advisory locks to serialize operations for a logical resource.

Example:

```sql
SELECT pg_advisory_xact_lock($1);
```

### Tasks

Determine:

- What resource is being represented by the key.
- How the lock lifetime differs from session-level advisory locks.
- What happens on transaction rollback.
- How deadlocks can still occur.

Design a lock-key strategy that avoids collisions between unrelated resources.

---

## Exercise: Advisory Lock Ordering

Two workflows acquire:

```text
customer lock
account lock
```

in opposite orders.

### Tasks

Determine whether advisory locks can deadlock.

Design deterministic lock ordering.

Explain why advisory locks do not eliminate the need for concurrency design.

---

## Exercise: `NOWAIT`

Use:

```sql
SELECT *
FROM products
WHERE id = $1
FOR UPDATE NOWAIT;
```

### Tasks

Determine the behavior when another transaction already owns the lock.

Design application behavior for:

```text
lock immediately available
lock unavailable
```

Compare `NOWAIT` with waiting normally.

---

## Exercise: `SKIP LOCKED`

Design a concurrent worker queue using:

```sql
SELECT id
FROM orders
WHERE status = 'pending'
ORDER BY id
FOR UPDATE SKIP LOCKED
LIMIT 20;
```

### Tasks

Design the complete claim operation.

Consider:

- Worker concurrency.
- Atomic claiming.
- Worker crashes.
- Stuck jobs.
- Leases.
- Retries.
- Starvation.
- Monitoring.

Explain why `SKIP LOCKED` is particularly useful for queue-like workloads.

---

## Exercise: Queue Claim Race

A worker performs:

```text
SELECT pending job
UPDATE job → processing
```

without locking.

### Tasks

Construct an interleaving where two workers claim the same job.

Redesign using:

```text
FOR UPDATE SKIP LOCKED
```

or an atomic conditional update.

Explain why claiming and state transition should be treated as one concurrency operation.

---

## Exercise: Worker Crash

A worker successfully changes:

```text
pending → processing
```

and then crashes.

### Tasks

Determine how the job could become permanently stuck.

Design a lease:

```text
processing_started_at
lease_expires_at
```

Explain how another worker can safely recover expired jobs.

Consider the possibility that the original worker resumes after the lease expires.

---

## Exercise: Fencing Tokens

A worker receives:

```text
lease token = 10
```

Another worker later receives:

```text
lease token = 11
```

The old worker continues running.

### Tasks

Design a database update that accepts only the latest token.

Explain how fencing prevents an old worker from overwriting newer work.

---

## Exercise: Compare Queue Semantics

Compare:

| Mechanism | Main use |
|---|---|
| PostgreSQL `SKIP LOCKED` | DB-backed work queue |
| Redis queue | Fast ephemeral/distributed work |
| Kafka | Durable event streaming |
| Celery | Task execution abstraction |
| SQS | Managed durable queue |

### Tasks

For each mechanism, analyze:

- Ordering.
- Delivery semantics.
- Duplicate execution.
- Retry behavior.
- Persistence.
- Concurrency.
- Failure recovery.

---

## Exercise: Concurrent Cache Population

Two requests miss the same Redis cache key:

```text
GET product:42
```

Both query PostgreSQL and both populate Redis.

### Tasks

Determine whether this is a correctness problem.

Then analyze:

- Cache stampede.
- Duplicate database queries.
- Locking.
- Request coalescing.
- TTL jitter.

Explain why not every race condition requires a lock.

---

## Exercise: Cache Invalidation Race

Consider:

```text
Request A:
update DB
invalidate cache

Request B:
read DB
populate cache
```

### Tasks

Construct an interleaving where stale data becomes cached.

Design safer approaches using:

- Versioned cache values.
- Post-commit invalidation.
- Events.
- Write timestamps.
- Short TTLs.

---

## Exercise: Database and Redis Consistency

Two concurrent requests execute:

```text
Request A:
update PostgreSQL
update Redis

Request B:
read Redis
```

### Tasks

Identify possible stale states.

Explain why Redis should usually be treated as a cache rather than the transactional source of truth.

Design a safer:

```text
database commit
→ cache invalidation/update
```

workflow.

---

## Exercise: Transaction and Celery Race

A request executes:

```python
with transaction.atomic():
    order = create_order()
    send_order_confirmation.delay(order.id)
```

### Tasks

Construct a race where the Celery worker executes before the transaction commits.

Determine what the worker can observe.

Redesign using:

```python
transaction.on_commit(
    lambda: send_order_confirmation.delay(order.id)
)
```

---

## Exercise: Duplicate Celery Execution

A Celery task:

```text
charge_payment(payment_id)
```

times out.

The broker retries it.

The first execution may have succeeded.

### Tasks

Design the task to be idempotent.

Consider:

- Payment state.
- Idempotency key.
- Unique constraints.
- Provider idempotency.
- Database transactions.
- Retry classification.

Explain why task delivery and task execution are different concerns.

---

## Exercise: Kafka Duplicate Event

A Kafka consumer receives:

```text
OrderCompleted
```

and updates PostgreSQL.

The transaction commits, but the consumer crashes before acknowledging the Kafka message.

### Tasks

Determine what happens when Kafka redelivers the event.

Design an idempotent consumer using:

- Event ID.
- Unique constraint.
- Processed-event table.
- Idempotent state transition.

---

## Exercise: Event Ordering

Events arrive:

```text
OrderCompleted
OrderProcessing
```

instead of:

```text
OrderProcessing
OrderCompleted
```

### Tasks

Determine how an order-state consumer can avoid moving:

```text
completed → processing
```

Design protection using:

- State transition validation.
- Event version.
- Sequence number.
- Optimistic concurrency.

Explain why distributed event delivery should not be assumed to preserve business ordering unless explicitly designed.

---

## Exercise: Concurrent REST Requests

Two clients simultaneously call:

```text
PATCH /orders/42
```

Client A changes:

```json
{
  "status": "completed"
}
```

Client B changes:

```json
{
  "status": "cancelled"
}
```

### Tasks

Determine possible outcomes.

Design an optimistic concurrency mechanism using:

```text
version
```

or:

```text
ETag / If-Match
```

Explain why last-write-wins can silently lose business decisions.

---

## Exercise: HTTP Idempotency

Classify these operations:

| Operation | Naturally idempotent? |
|---|---|
| `GET /orders/42` | Yes |
| `PUT /orders/42` with complete representation | Usually |
| `DELETE /orders/42` | Semantically often |
| `POST /payments` | No, unless designed |
| `POST /orders` | No, unless designed |

### Tasks

Explain why HTTP method semantics alone do not solve business-level duplicate execution.

Design an idempotency mechanism for a payment endpoint.

---

## Exercise: Read-After-Write Race

A client executes:

```text
POST /orders
GET /orders/{id}
```

The write goes to the primary.

The read goes to a replica.

### Tasks

Construct a stale-read scenario.

Design:

- Primary routing.
- Session-level consistency.
- LSN-aware routing.
- Temporary primary reads.

Explain why a successful transaction commit does not imply immediate replica visibility.

---

## Exercise: Concurrent Read and Update

Transaction A reads an account.

Transaction B updates the account and commits.

Transaction A then makes a decision based on its earlier read.

### Tasks

Analyze the behavior under:

```text
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

Determine when explicit locking is necessary.

---

## Exercise: Write Skew

Consider a business rule:

```text
At least one doctor must remain on call.
```

Two doctors are currently on call.

Two concurrent transactions each attempt to remove one doctor after observing that two are available.

### Tasks

Construct the write-skew scenario.

Determine whether row-level locks on each individual doctor automatically prevent the anomaly.

Evaluate:

- Serializable isolation.
- Explicit coordination row.
- Advisory lock.
- Database design changes.

---

## Exercise: Serializable Isolation

Construct a workload where two concurrent transactions make individually valid decisions but cannot both be committed safely.

Run them under:

```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
```

### Tasks

Observe serialization failures.

Explain:

- Why PostgreSQL aborts one transaction.
- Why retry is required.
- Why serializable isolation does not mean operations execute physically one at a time.

---

## Exercise: Serialization Retry

Design a Python transaction wrapper that retries:

```text
SQLSTATE 40001
```

with:

```text
maximum attempts = 3
exponential backoff
random jitter
```

### Tasks

Ensure the retry encompasses the complete transaction.

Determine which exceptions should not be retried.

Explain why unlimited retries can become a production failure amplifier.

---

## Exercise: Lock Timeout

Use:

```sql
SET LOCAL lock_timeout = '2s';
```

### Tasks

Construct a transaction that waits for a lock longer than two seconds.

Determine the resulting behavior.

Compare:

```text
lock_timeout
statement_timeout
```

Explain why they should be configured as separate parts of a latency budget.

---

## Exercise: Connection Pool Amplification

Suppose:

```text
10 Kubernetes pods
20 connections per pod
```

A lock incident causes each connection to wait.

### Tasks

Calculate the maximum potential database connections.

Explain how increasing pool size can worsen:

- Lock contention.
- Memory consumption.
- CPU scheduling.
- Queue depth.
- Tail latency.

Design a connection budget for the fleet.

---

## Exercise: Concurrency and Little's Law

Suppose:

```text
throughput = 500 requests/sec
average transaction duration = 200 ms
```

Use:

```text
L = λW
```

to estimate average concurrent requests.

Then change transaction duration to:

```text
1 second
```

### Tasks

Calculate the approximate concurrency.

Explain why reducing transaction duration can improve capacity without adding database hardware.

---

## Exercise: Long Transaction

A transaction:

```text
BEGIN
lock row
perform expensive calculation
call external API
update row
COMMIT
```

runs for 10 seconds.

### Tasks

Identify the concurrency impact.

Consider:

- Lock duration.
- Connection occupancy.
- MVCC.
- Dead tuples.
- Rollback cost.
- Pool exhaustion.

Redesign the workflow.

---

## Exercise: Idle in Transaction

A service opens a transaction and then waits for external work.

Investigate:

```sql
SELECT
    pid,
    state,
    xact_start,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE state = 'idle in transaction';
```

### Tasks

Determine why this state is dangerous.

Design monitoring and timeout controls.

Explain how long-lived transactions can interfere with PostgreSQL cleanup.

---

## Exercise: Concurrent Delete and Update

Transaction A:

```sql
UPDATE orders
SET status = 'completed'
WHERE id = 42;
```

Transaction B:

```sql
DELETE FROM orders
WHERE id = 42;
```

### Tasks

Investigate the lock interaction.

Determine which transaction waits.

Explain why row-level concurrency still requires understanding transaction ordering.

---

## Exercise: Concurrent Parent and Child Operations

Consider:

```text
orders
payments
```

with:

```sql
FOREIGN KEY (order_id) REFERENCES orders(id)
```

### Tasks

Investigate the locking behavior of:

```text
INSERT payment
DELETE order
```

when executed concurrently.

Explain why foreign-key enforcement can participate in unexpected lock relationships.

---

## Exercise: Concurrent Schema Change

A deployment performs:

```sql
ALTER TABLE orders
ADD COLUMN processed_at timestamptz;
```

while production traffic continuously updates orders.

### Tasks

Investigate:

- Required locks.
- Lock waiting.
- Long transactions.
- Deployment ordering.
- Application compatibility.

Design a safer migration strategy.

---

## Exercise: Concurrent Index Deployment

A large index is created:

```sql
CREATE INDEX CONCURRENTLY orders_customer_created_idx
ON orders (customer_id, created_at DESC);
```

### Tasks

Determine:

- Why concurrent creation is safer for availability.
- What resources it consumes.
- Why it cannot run inside a transaction block.
- What happens if creation fails.
- How to detect invalid indexes.

Explain why concurrency is relevant to schema deployment as well as application code.

---

## Exercise: Migration Backfill Concurrency

A worker backfills:

```text
500 million rows
```

while API traffic updates the same records.

### Tasks

Analyze:

- Write-write conflicts.
- Lock contention.
- WAL growth.
- Replica lag.
- Autovacuum pressure.
- Connection-pool usage.

Design:

```text
batching
+
keyset pagination
+
throttling
+
idempotency
```

Explain why migration workers are part of the production concurrency model.

---

## Exercise: Concurrent Backfill Workers

Five workers process the same table.

Each worker uses:

```text
WHERE id > last_processed_id
ORDER BY id
LIMIT 5000
```

### Tasks

Determine whether workers can process overlapping rows.

Redesign the work allocation using:

- Partitioned ID ranges.
- `SKIP LOCKED`.
- Explicit work queue.
- Deterministic ownership.

Explain why independently maintained checkpoints are insufficient for shared work without coordination.

---

## Exercise: Duplicate Background Processing

Two Kubernetes deployments temporarily run simultaneously during a rolling deployment.

Both execute the same scheduled job.

### Tasks

Determine how duplicate processing can occur.

Design protection using:

- Database uniqueness.
- Leader election.
- Advisory locks.
- Distributed scheduler.
- Idempotent jobs.

Explain why application deployment strategy can create concurrency problems even when individual workers are correct.

---

## Exercise: Microservice Concurrency

Two services independently update the same business entity:

```text
Order Service
Inventory Service
```

### Tasks

Determine the risks of shared database writes.

Compare:

```text
shared database
```

with:

```text
database ownership + events
```

Explain why microservices do not automatically eliminate concurrency problems.

---

## Exercise: Distributed Saga Race

Workflow:

```text
Create order
↓
Reserve inventory
↓
Charge payment
```

At the same time, a cancellation request arrives.

### Tasks

Construct a race between:

```text
complete order workflow
```

and:

```text
cancel order
```

Design coordination using:

- State machine.
- Version checks.
- Event ordering.
- Idempotent commands.
- Compensation.

Determine how to prevent an invalid final state.

---

## Exercise: Concurrent Saga Compensation

Suppose:

```text
Payment charged
Inventory reservation failed
```

The system starts a refund.

Meanwhile another worker retries the payment workflow.

### Tasks

Identify possible duplicate refunds or inconsistent payment state.

Design idempotent compensation.

Explain why compensation workflows need concurrency control just like forward workflows.

---

## Exercise: Duplicate Event Processing

Two consumers process the same logical event concurrently.

Both execute:

```sql
UPDATE orders
SET status = 'completed'
WHERE id = $1;
```

### Tasks

Determine whether duplicate execution is harmful.

Then modify the operation to enforce valid state transitions:

```sql
UPDATE orders
SET status = 'completed',
    version = version + 1
WHERE id = $1
  AND status = 'processing';
```

Explain how conditional updates can provide lightweight concurrency control.

---

## Exercise: Event Versioning

Events contain:

```json
{
  "order_id": 42,
  "version": 8,
  "status": "completed"
}
```

The database currently has:

```text
version = 9
```

### Tasks

Determine whether the event should be applied.

Design an update that rejects stale events.

Explain how version numbers can protect distributed consumers from out-of-order messages.

---

## Exercise: Concurrent API and Worker

An API request changes:

```text
pending → cancelled
```

while a background worker attempts:

```text
pending → processing
```

### Tasks

Construct possible interleavings.

Design atomic state transitions so that exactly one valid transition wins.

Determine how the losing actor should behave.

---

## Exercise: Concurrency Failure Classification

Classify each event:

| Event | Category |
|---|---|
| Two requests overwrite each other | Lost update |
| Two transactions wait forever | Deadlock |
| Transaction waits for another | Lock contention |
| Serializable transaction is aborted | Serialization failure |
| Same task executes twice | Duplicate execution |
| Replica returns older data | Stale read |
| Old worker overwrites newer worker | Lease/fencing failure |

### Tasks

For each category, identify the correct primary mitigation.

Avoid using a generic "add a lock" solution for every problem.

---

## Exercise: Production Incident

A production service suddenly reports:

```text
p99 latency ↑
DB lock waits ↑
connections ↑
deadlocks ↑
CPU ↑
retry count ↑
```

### Tasks

Build a concurrency-focused investigation.

Inspect:

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
FROM pg_stat_activity;
```

Then inspect:

```sql
SELECT
    pid,
    locktype,
    relation::regclass,
    mode,
    granted
FROM pg_locks;
```

Investigate:

- Recent deployment.
- Transaction duration.
- Lock ordering.
- Hot rows.
- Pool size.
- Worker concurrency.
- Retry behavior.
- Background migrations.
- Long-running transactions.

Determine why blindly increasing database connections may worsen the incident.

---

## Exercise: Concurrency Load Test

Create a test that executes the same business operation concurrently from:

```text
10 workers
100 workers
1,000 workers
```

### Tasks

Measure:

- Successful operations.
- Failed operations.
- Duplicate operations.
- Lock waits.
- Deadlocks.
- Transaction latency.
- p50/p95/p99.
- Database CPU.
- Connection utilization.

Determine whether correctness remains intact as concurrency increases.

---

## Exercise: Concurrency Test with Python

Design a Python concurrency test using multiple workers that execute a database operation simultaneously.

### Tasks

Ensure the test can detect:

```text
lost updates
duplicate records
incorrect counters
negative stock
invalid state transitions
```

Explain why concurrency bugs may not reproduce reliably in sequential unit tests.

---

## Exercise: Django Concurrency Test

Use Django's testing framework to create concurrent transactions.

### Tasks

Design a test around:

```python
select_for_update()
```

and another around:

```text
conditional UPDATE
```

Determine how to verify that only one concurrent worker succeeds.

Consider database isolation and test-database behavior when interpreting results.

---

## Exercise: Concurrency Observability

Design metrics for:

```text
lock_wait_duration
deadlock_count
serialization_failure_count
transaction_duration
retry_count
conflict_count
queue_depth
worker_execution_duration
```

### Tasks

Determine which should be:

- Counter.
- Histogram.
- Gauge.

Choose labels carefully.

Avoid high-cardinality dimensions such as:

```text
user_id
request_id
raw SQL
```

for general-purpose metrics.

---

## Exercise: Concurrency Logging

Design structured logs containing:

```text
request_id
transaction_id
operation
resource_type
resource_id
retry_attempt
error_code
duration
```

### Tasks

Determine how these fields help correlate:

```text
API request
→ database transaction
→ lock wait
→ retry
→ worker execution
```

Avoid logging sensitive customer information or credentials.

---

## Exercise: Concurrency and Security

A multi-tenant API receives:

```text
tenant_id
resource_id
```

from the client.

### Tasks

Determine why concurrent operations must preserve tenant authorization.

Analyze a race where:

```text
authorization check
→ transaction
→ resource update
```

uses inconsistent tenant context.

Design protection using:

- Database ownership.
- Tenant-aware queries.
- Row-level security.
- Transaction-scoped context.
- Constraints.

Explain why concurrency correctness and authorization correctness can interact.

---

## Exercise: Concurrency and RLS

A PostgreSQL database uses row-level security.

The application sets:

```sql
SET LOCAL app.tenant_id = 'tenant-42';
```

inside a transaction.

### Tasks

Determine why transaction-scoped context is preferable with pooled connections.

Analyze what could happen if tenant context leaks between requests.

Explain why pooling makes session state an important concurrency concern.

---

## Exercise: Concurrency Decision Matrix

For each scenario, choose a primary mechanism:

| Scenario | Candidate |
|---|---|
| Increment numeric counter | Atomic SQL |
| Protect hot inventory row | Row lock / atomic update |
| Low-conflict profile edits | Optimistic concurrency |
| Complex cross-row invariant | Serializable / explicit coordination |
| Account transfer | Ordered row locks |
| Background queue claiming | `SKIP LOCKED` |
| Duplicate HTTP request | Idempotency key + uniqueness |
| Distributed workflow | State machine + idempotency |
| Hot global counter | Sharded/partitioned aggregation |
| Cache stampede | Coalescing/locking where justified |

### Tasks

For every choice, explain:

- Why it fits.
- What it protects.
- What it does not protect.
- Its scalability limitation.
- Its failure behavior.

---

## Exercise: Design a Concurrency-Safe Order API

Design:

```text
POST /orders
```

Requirements:

- Duplicate requests must not create duplicate orders.
- Inventory cannot become negative.
- Only valid state transitions are allowed.
- Payment creation must be idempotent.
- Kafka events must tolerate duplicate publication.
- Celery tasks may execute more than once.
- Redis is used as a cache.
- Read replicas may lag.
- Database deadlocks may occur.

### Tasks

Design:

1. Database constraints.
2. Transaction boundary.
3. Inventory concurrency strategy.
4. Idempotency mechanism.
5. Order state machine.
6. Payment strategy.
7. Outbox strategy.
8. Consumer idempotency.
9. Cache invalidation.
10. Retry behavior.
11. Replica-read strategy.
12. Monitoring.

---

## Exercise: Senior Concurrency Architecture

Design a production architecture for:

```text
10,000 API requests/sec
```

with:

```text
1,000 worker processes
```

and:

```text
shared PostgreSQL primary
```

The system contains:

- Orders.
- Inventory.
- Payments.
- Redis.
- Kafka.
- Celery.
- Read replicas.
- Kubernetes.

### Tasks

Determine:

- Which resources can become hot.
- Where locks are appropriate.
- Where optimistic concurrency is appropriate.
- Where queues should serialize work.
- Which state belongs in PostgreSQL.
- Which operations can be asynchronous.
- Where idempotency is mandatory.
- How retries are bounded.
- How connection pools are sized.
- How replica lag affects correctness.
- How concurrency metrics should be designed.

Produce an architecture that preserves correctness without assuming unlimited database concurrency.

---

## Common Concurrency Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Read-modify-write without protection | Sequential thinking | Atomic SQL or concurrency control |
| Check then insert | Assuming no competing request | Unique constraint |
| Check then update | Race window | Conditional update |
| Locking everything | Treating locks as universal protection | Lock only required resources |
| Holding locks during API calls | Convenient control flow | External work outside transaction |
| Inconsistent lock order | Independent code paths | Deterministic ordering |
| Unlimited retries | Assuming transient errors are harmless | Bounded retries + backoff |
| Retrying failed statements only | Ignoring transaction state | Retry whole transaction |
| Increasing pool size during contention | Mistaking waits for capacity shortage | Reduce contention |
| Treating Redis locks as magic | Ignoring expiration/fencing | Explicit ownership and fencing |
| Assuming Kafka executes once | Confusing delivery with business effect | Idempotent consumers |
| Assuming Celery executes once | Ignoring task retries | Idempotent tasks |
| Assuming replicas are current | Ignoring replication lag | Consistency-aware routing |
| Using `SERIALIZABLE` everywhere | Strong isolation seems universally safer | Choose isolation intentionally |
| Ignoring hot rows | Scaling application workers blindly | Sharding/serialization/aggregation |
| Using only application validation | Alternate paths bypass checks | Database constraints |
| Ignoring migration workers | Treating migrations separately from traffic | Include them in concurrency planning |
| Logging raw identifiers everywhere | Over-instrumentation | Structured, low-cardinality observability |
| Testing only sequentially | Race conditions remain hidden | Controlled concurrent tests |

---

## Production Concurrency Checklist

### Correctness

- [ ] Shared mutable state is identified.
- [ ] Business invariants are explicitly defined.
- [ ] Race windows have been analyzed.
- [ ] Critical invariants are enforced by PostgreSQL.
- [ ] Conditional updates are used where appropriate.
- [ ] Unique constraints protect uniqueness.
- [ ] State transitions are atomic.
- [ ] Multi-row operations have deterministic ordering.

### Transactions

- [ ] Transactions are short.
- [ ] External calls are outside database transactions.
- [ ] Expensive computation is outside transactions where possible.
- [ ] Transaction ownership is explicit.
- [ ] Isolation level is deliberate.
- [ ] Failed transaction behavior is understood.
- [ ] Commit uncertainty is handled.

### Locks

- [ ] Required locks are understood.
- [ ] Lock duration is measured.
- [ ] Lock ordering is deterministic.
- [ ] Hot rows are identified.
- [ ] `NOWAIT` is used where appropriate.
- [ ] `SKIP LOCKED` is used only for appropriate queue-like workloads.
- [ ] Advisory locks have documented ownership and keying.

### Retries

- [ ] Deadlocks are classified.
- [ ] Serialization failures are classified.
- [ ] Retryable errors are explicitly defined.
- [ ] Retries are bounded.
- [ ] Exponential backoff is used.
- [ ] Jitter is used.
- [ ] Retry operations are idempotent.
- [ ] Retry storms are monitored.

### Distributed Systems

- [ ] HTTP operations have appropriate idempotency semantics.
- [ ] Kafka consumers tolerate duplicates.
- [ ] Celery tasks tolerate retries.
- [ ] Outbox events are durable.
- [ ] Compensation operations are idempotent.
- [ ] Distributed state transitions are versioned where necessary.
- [ ] Old workers cannot overwrite newer work when leases are used.

### Caching

- [ ] PostgreSQL remains the source of truth where appropriate.
- [ ] Cache invalidation occurs safely relative to commit.
- [ ] Cache stampedes are considered.
- [ ] Versioned cache values are considered for highly concurrent data.
- [ ] Session state does not leak through pooled connections.

### Scaling

- [ ] Connection budgets are calculated across the entire fleet.
- [ ] Worker concurrency is bounded.
- [ ] Hot resources are identified.
- [ ] Background jobs are included in capacity planning.
- [ ] Large backfills are throttled.
- [ ] Read replicas are not treated as a write-concurrency solution.
- [ ] Sharding or serialization is considered for extreme hotspots.

### Observability

- [ ] Lock waits are monitored.
- [ ] Deadlocks are monitored.
- [ ] Serialization failures are monitored.
- [ ] Transaction duration is monitored.
- [ ] Retry rates are monitored.
- [ ] Queue depth is monitored.
- [ ] Connection utilization is monitored.
- [ ] p95/p99 latency is monitored.
- [ ] Concurrency incidents can be correlated with deployments.

---

## Interview Traps

### Is concurrency the same as parallelism?

No. Concurrency describes overlapping progress or execution of multiple activities. Parallelism means activities execute simultaneously on multiple execution resources.

### Does a transaction automatically prevent race conditions?

No. Transactions provide atomicity and isolation semantics, but correctness still depends on isolation level, locking, constraints, and transaction design.

### Is `SELECT FOR UPDATE` always better than optimistic concurrency?

No. It can be appropriate for high-conflict resources, but it introduces waiting and can reduce throughput. Optimistic concurrency can be better when conflicts are uncommon.

### Does an atomic SQL statement solve every concurrency problem?

No. It is excellent for simple state changes such as counters or conditional inventory updates, but complex multi-step invariants may require transactions, locks, serializable isolation, or other coordination.

### Does a unique constraint prevent all duplicate business effects?

No. It can prevent duplicate database records, but external side effects such as payment charges, emails, or API calls require their own idempotency mechanisms.

### Does `SERIALIZABLE` execute transactions one at a time?

No. PostgreSQL can execute transactions concurrently and abort transactions whose concurrent execution cannot be serialized safely.

### Should deadlocks be impossible in production?

Ideally the application minimizes them through consistent lock ordering and short transactions, but robust systems still classify and safely retry deadlocks.

### Does increasing the connection pool improve concurrency?

Only up to the database's useful capacity. Beyond that, more connections can increase CPU, memory, lock contention, and queueing.

### Does Redis locking guarantee correctness?

Not automatically. Expiration, crashes, network failures, ownership, fencing, and stale lock holders must be considered.

### Does Kafka guarantee exactly-once business effects?

No. Even when infrastructure provides strong delivery guarantees, business operations must still be designed to tolerate retries and duplicate processing.

### Does a read replica provide read-your-writes consistency?

Not automatically. Asynchronous replication can leave the replica behind the primary.

### Can database constraints replace application validation?

They should not replace useful application validation, but critical invariants should also be enforced at the database layer because concurrent requests and alternate execution paths can bypass application checks.

---

## Senior-Level Concurrency Questions

For every shared resource, ask:

1. What state is shared?
2. What invariant must always hold?
3. Which actors can modify it?
4. Can two actors read the same old value?
5. Can two actors write conflicting values?
6. Is the operation atomic?
7. Is a database constraint sufficient?
8. Is an atomic SQL statement sufficient?
9. Is pessimistic locking required?
10. Is optimistic concurrency preferable?
11. What isolation level is required?
12. Which rows or resources are locked?
13. Can locks be acquired in different orders?
14. Can a deadlock occur?
15. What happens when a lock is unavailable?
16. Should the operation wait, fail fast, or skip?
17. Can the operation be retried?
18. Is retrying the entire transaction necessary?
19. Is the operation idempotent?
20. Can a timeout occur after the database commits?
21. Can a worker execute the operation twice?
22. Can an old worker continue after lease expiration?
23. Can events arrive out of order?
24. Can replicas return stale data?
25. Can cache state become stale?
26. Can connection pooling amplify contention?
27. Can background jobs compete with API traffic?
28. Can migrations compete with production traffic?
29. What happens at 10x concurrency?
30. How will the concurrency failure be detected in production?

---

## Final Practice Set

Complete these exercises without reference material:

1. Identify shared state and invariants.
2. Reproduce a lost update.
3. Implement an atomic counter.
4. Implement concurrent inventory reservation.
5. Reproduce negative inventory.
6. Implement pessimistic locking.
7. Implement Django `select_for_update()`.
8. Implement optimistic concurrency.
9. Resolve an optimistic concurrency conflict.
10. Compare pessimistic and optimistic strategies.
11. Implement an atomic order state transition.
12. Reject invalid state transitions.
13. Design a concurrent state machine.
14. Prevent duplicate payments.
15. Protect concurrent username creation.
16. Prevent duplicate background jobs.
17. Analyze a `COUNT`-then-insert race.
18. Enforce uniqueness with a database constraint.
19. Implement an account transfer.
20. Prevent transfer deadlocks.
21. Design deterministic multi-row lock ordering.
22. Diagnose a PostgreSQL deadlock.
23. Implement deadlock retries.
24. Measure lock contention.
25. Analyze a hot-row bottleneck.
26. Compare Redis `GET`/`SET` with `INCR`.
27. Design a Redis lock safely.
28. Implement a PostgreSQL advisory lock.
29. Design advisory lock ordering.
30. Use `NOWAIT`.
31. Build a `SKIP LOCKED` worker queue.
32. Prevent duplicate queue claims.
33. Recover crashed workers.
34. Design lease expiration.
35. Implement fencing tokens.
36. Compare PostgreSQL queues, Redis, Kafka, Celery, and SQS.
37. Analyze cache stampedes.
38. Prevent cache invalidation races.
39. Design PostgreSQL/Redis consistency.
40. Prevent Celery transaction races.
41. Design idempotent Celery tasks.
42. Design idempotent Kafka consumers.
43. Handle out-of-order events.
44. Design optimistic REST updates.
45. Implement HTTP idempotency.
46. Handle read-after-write consistency.
47. Analyze concurrent snapshots.
48. Reproduce write skew.
49. Use serializable isolation.
50. Implement serialization retries.
51. Configure lock timeouts.
52. Analyze connection-pool amplification.
53. Apply Little's Law to transaction concurrency.
54. Diagnose long transactions.
55. Diagnose idle-in-transaction sessions.
56. Analyze concurrent deletes and updates.
57. Investigate foreign-key concurrency.
58. Design concurrent schema changes.
59. Deploy indexes safely under traffic.
60. Design concurrent large-table backfills.
61. Coordinate multiple migration workers.
62. Prevent duplicate scheduled jobs.
63. Analyze microservice shared-state concurrency.
64. Design a concurrent Saga.
65. Design idempotent compensation.
66. Protect against duplicate event processing.
67. Use event versions to reject stale updates.
68. Coordinate API and worker state transitions.
69. Classify concurrency failures.
70. Diagnose a production concurrency incident.
71. Build a concurrent load test.
72. Write Python concurrency tests.
73. Write Django concurrency tests.
74. Design concurrency metrics.
75. Design structured concurrency logs.
76. Analyze tenant isolation under concurrency.
77. Combine RLS with pooled connections.
78. Build a concurrency decision matrix.
79. Design a concurrency-safe order API.
80. Design a production concurrency architecture at scale.

## Key Takeaways

- **Concurrency correctness starts with invariants:** identify shared state, define what must remain true, and choose atomic SQL, constraints, locks, or optimistic concurrency accordingly.
- **Atomicity and scalability are different problems:** a row-level lock or atomic update can be perfectly correct while becoming a bottleneck under extreme contention.
- **Retries are part of concurrency design:** deadlocks and serialization failures require bounded, idempotent, transaction-aware retries rather than indiscriminate repetition.
- **Distributed concurrency extends beyond PostgreSQL:** Redis, Kafka, Celery, replicas, leases, caches, and microservices introduce duplicate execution, stale state, ordering, and ownership problems.
- **Production concurrency must be observable and bounded:** monitor lock waits, deadlocks, transaction duration, retries, queue depth, connection usage, and tail latency while controlling application and worker concurrency.