# 06- Transaction Boundaries

## Overview

A **transaction boundary** defines the point at which a group of database operations begins and ends as one atomic unit of work.

For backend systems, transaction boundaries are primarily a **business correctness decision**, not merely a database configuration detail. A well-designed boundary ensures that all database changes required for one business operation either become committed together or are rolled back together.

```text
Business Operation
       │
       ▼
   BEGIN TRANSACTION
       │
       ├── Read required state
       ├── Validate business rules
       ├── Modify database state
       ├── Persist related changes
       │
       ▼
     COMMIT
       │
       ▼
   Business operation complete
```

A poorly chosen boundary can produce:

- Partial updates.
- Lost or inconsistent state.
- Excessive lock duration.
- Long-running transactions.
- Connection pool exhaustion.
- Deadlocks.
- Difficult retry behavior.
- Unnecessary contention between requests.

The senior-level goal is not to make every operation transactional. It is to identify **which state changes must be atomic, which can be independent, and where the database transaction should start and end**.

## What Is a Transaction Boundary?

A transaction boundary is the logical scope between transaction start and transaction completion.

In SQL:

```sql
BEGIN;

-- Transaction boundary starts here.

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

-- Transaction boundary ends here.
COMMIT;
```

Everything between `BEGIN` and `COMMIT` belongs to the same transaction.

If an unrecoverable error occurs:

```sql
ROLLBACK;
```

the database discards the transaction's changes.

The important design question is:

> Which operations must succeed or fail together to preserve the business invariant?

That question should determine the boundary.

## Why Transaction Boundaries Matter

Consider a money transfer:

```text
Account A                    Account B
   │                            │
   │ -$100                      │ +$100
   └──────────────┬─────────────┘
                  │
              Same transaction
```

The balance changes must be atomic.

This is unsafe:

```text
Transaction 1:
    Debit Account A
    COMMIT

Transaction 2:
    Credit Account B
    FAIL
```

The system can now have:

```text
Account A: -$100
Account B: unchanged
```

The transaction boundary must encompass both state changes:

```text
BEGIN
 │
 ├── Debit A
 ├── Credit B
 │
 └── COMMIT
```

The boundary therefore protects the business invariant:

```text
total balance before = total balance after
```

## Choosing the Boundary

A practical approach is to identify the **business unit of atomicity**.

Ask:

1. What business operation is being performed?
2. Which database records must change together?
3. What invariants must hold after the operation?
4. Can the operation safely be partially completed?
5. Which external side effects occur?
6. How long will the transaction remain open?
7. What concurrency or locking is required?

For example, placing an order might require:

```text
Create Order
    │
    ├── Create Order Items
    ├── Reserve Inventory
    ├── Calculate persisted totals
    └── Update Order Status
```

If all of these database changes must agree, they belong inside the same transaction.

## Transaction Boundary and Business Invariants

Transaction boundaries should protect invariants that must never be observed in an invalid committed state.

Example:

```text
Inventory quantity >= 0
```

Suppose an order consumes inventory:

```sql
BEGIN;

UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 100
  AND quantity > 0;

INSERT INTO order_items(order_id, product_id, quantity)
VALUES (5001, 100, 1);

COMMIT;
```

The inventory update and order-item insertion should be considered together if the application relies on their consistency.

A useful design principle is:

> Put all database mutations required to establish a business invariant inside the same transaction boundary.

## Request-Scoped Transactions

A common backend pattern is to associate a transaction with an HTTP request:

```text
HTTP Request
     │
     ▼
BEGIN
     │
     ├── Authentication
     ├── Business logic
     ├── Database writes
     │
     ▼
COMMIT / ROLLBACK
     │
     ▼
HTTP Response
```

This can be useful for simple CRUD-style applications, but it should not automatically be applied to every endpoint.

A request may perform:

- Read-only operations.
- Long-running computation.
- External HTTP calls.
- File processing.
- Message publishing.
- Multiple independent business operations.

Keeping the entire request inside one database transaction can unnecessarily increase transaction duration.

## Prefer Business-Operation Boundaries

For more complex systems, transaction boundaries should generally align with the **database portion of a business operation**, rather than the entire request lifecycle.

Instead of:

```text
HTTP Request
 │
 ├── BEGIN
 ├── Call external API
 ├── Process large file
 ├── Query database
 ├── Sleep/retry
 ├── Update database
 └── COMMIT
```

prefer:

```text
HTTP Request
 │
 ├── Validate request
 ├── External/non-transactional work
 │
 └── Short database transaction
       │
       ├── Read required state
       ├── Apply changes
       └── COMMIT
```

This reduces:

- Lock duration.
- Connection occupancy.
- Transaction lifetime.
- Deadlock exposure.
- Resource consumption.

## Transaction Boundary in Django

Django provides `transaction.atomic()` for defining transaction boundaries.

```python
from django.db import transaction

@transaction.atomic
def create_order(customer_id: int, product_id: int) -> Order:
    order = Order.objects.create(
        customer_id=customer_id,
        status="pending",
    )

    OrderItem.objects.create(
        order=order,
        product_id=product_id,
        quantity=1,
    )

    return order
```

Conceptually:

```text
create_order()
     │
     ▼
BEGIN
     │
     ├── INSERT order
     ├── INSERT order_item
     │
     ▼
COMMIT
```

If an exception escapes the atomic block, Django rolls back the transaction.

### Nested Atomic Blocks

Django supports nested `atomic()` blocks.

```python
from django.db import transaction

with transaction.atomic():
    update_required_state()

    try:
        with transaction.atomic():
            perform_optional_database_operation()
    except OptionalOperationError:
        handle_optional_failure()

    finalize_required_state()
```

The outer block represents the main transaction. The inner block can use a savepoint to isolate the optional operation.

This is different from creating an independent database transaction.

## Transaction Boundary in SQLAlchemy

SQLAlchemy provides explicit transaction management:

```python
from sqlalchemy.orm import Session

def create_order(session: Session, customer_id: int) -> None:
    order = Order(customer_id=customer_id, status="pending")
    session.add(order)

    session.flush()

    session.add(
        OrderItem(
            order_id=order.id,
            product_id=100,
            quantity=1,
        )
    )

    session.commit()
```

For service-layer designs, an explicit unit-of-work pattern can make transaction boundaries easier to reason about:

```python
def create_order(session: Session, customer_id: int) -> Order:
    order = build_order(session, customer_id)
    reserve_inventory(session, order)
    persist_order_items(session, order)
    return order
```

The caller owns the transaction:

```python
with session.begin():
    order = create_order(session, customer_id)
```

This separates:

- Business logic.
- Transaction ownership.
- Database session lifecycle.

That separation becomes valuable as applications grow.

## Transaction Boundary and Service Layers

A useful backend architecture is:

```text
Controller / API
       │
       ▼
Application Service
       │
       ▼
Transaction Boundary
       │
       ├── Repository
       ├── Repository
       └── Repository
       │
       ▼
    Database
```

For example:

```python
def place_order(command: PlaceOrderCommand) -> Order:
    with transaction.atomic():
        order = create_order(command)
        reserve_inventory(order)
        record_order_state(order)
        return order
```

Repositories should generally not independently commit unless there is a deliberate architectural reason.

This keeps the transaction boundary visible at the application-service level.

## Avoid Repository-Level Commits

A problematic design is:

```python
def create_order():
    order = ...
    db.commit()

def reserve_inventory():
    inventory = ...
    db.commit()
```

The service cannot guarantee atomicity:

```text
create_order()
    │
    └── COMMIT ✓

reserve_inventory()
    │
    └── FAIL ✗
```

A better design is:

```python
def create_order():
    ...

def reserve_inventory():
    ...

def place_order():
    with transaction.atomic():
        create_order()
        reserve_inventory()
```

The service owns the business transaction.

## Transaction Boundaries and External Calls

Database transactions should generally not remain open while waiting for external services.

Avoid:

```text
BEGIN
 │
 ├── UPDATE order
 ├── HTTP request → Payment Service
 │                   │
 │                   ├── network latency
 │                   ├── retry
 │                   └── timeout
 │
 └── COMMIT
```

The transaction may hold database locks while the external call takes hundreds of milliseconds or several seconds.

A safer architecture is often:

```text
Database Transaction
 │
 ├── Persist state
 ├── Persist outbox event
 └── COMMIT
          │
          ▼
     Outbox Publisher
          │
          ▼
   External Service / Kafka
```

This is the basis of the transactional outbox pattern.

## Transaction Boundary and Kafka

Suppose an order service needs to update PostgreSQL and publish an event to Kafka.

This is unsafe:

```text
BEGIN
 │
 ├── UPDATE orders
 ├── COMMIT
 │
 └── Publish Kafka event
        │
        └── FAIL
```

The database contains the new state but Kafka may not contain the corresponding event.

A transactional outbox provides a better boundary:

```text
BEGIN
 │
 ├── UPDATE orders
 ├── INSERT outbox_events
 │
 └── COMMIT
          │
          ▼
     Outbox Worker
          │
          ▼
        Kafka
```

The database transaction atomically establishes both:

- The business state.
- The fact that an event must eventually be published.

## Transaction Boundary and Celery

Background jobs require the same reasoning.

Avoid dispatching a Celery task before the database transaction commits:

```python
with transaction.atomic():
    order = create_order()

    send_order_task.delay(order.id)

    update_order(order)
```

The worker could consume the task before the transaction commits and observe incomplete state.

Django provides `transaction.on_commit()`:

```python
from django.db import transaction

with transaction.atomic():
    order = create_order()

    transaction.on_commit(
        lambda: send_order_task.delay(order.id)
    )
```

Now the task is scheduled only after the transaction successfully commits.

The broader principle is:

> External consumers should not be allowed to act on database state that has not yet committed.

## Long-Running Transactions

Long-running transactions are a common production problem.

```text
BEGIN
 │
 ├── Query
 ├── Application computation
 ├── HTTP request
 ├── Large loop
 ├── File processing
 └── COMMIT
```

Potential consequences include:

- Locks being held for too long.
- Increased contention.
- Increased MVCC storage pressure in systems such as PostgreSQL.
- Longer rollback time.
- Connection pool exhaustion.
- Increased deadlock probability.
- Reduced throughput.

A transaction should generally contain **database work that needs atomicity**, not arbitrary application processing.

## Transaction Boundary and Lock Duration

Consider:

```sql
BEGIN;

SELECT *
FROM accounts
WHERE id = 100
FOR UPDATE;

-- Expensive application processing here.

UPDATE accounts
SET balance = balance - 100
WHERE id = 100;

COMMIT;
```

The row lock can remain held during the application processing.

A better design minimizes the time between lock acquisition and commit:

```text
BEGIN
 │
 ├── SELECT ... FOR UPDATE
 ├── Validate current state
 ├── UPDATE
 └── COMMIT
```

This is especially important for high-contention resources such as:

- Inventory.
- Account balances.
- Counters.
- Reservations.
- Quotas.
- Job claims.

## Read-Only Operations

Not every database interaction requires an explicit write transaction.

For example:

```sql
SELECT id, name, status
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC;
```

A read-only request may not need an application-managed transaction.

However, multiple reads that must represent one consistent logical snapshot may require transactional semantics depending on the database's isolation model and application requirements.

The decision should be based on consistency requirements rather than a blanket rule.

## Transaction Boundary and Isolation

Transaction boundaries interact directly with isolation levels.

```text
Transaction Boundary
        │
        ▼
Isolation Level
        │
        ├── What can be observed?
        ├── Which anomalies are possible?
        └── How much concurrency is allowed?
```

For example:

```sql
BEGIN;

SELECT balance
FROM accounts
WHERE id = 100;

UPDATE accounts
SET balance = balance - 50
WHERE id = 100;

COMMIT;
```

The isolation level determines what concurrent transactions can observe while this transaction executes.

A larger transaction usually means:

- More state is held concurrently.
- More opportunities for contention.
- More potential interaction with concurrent transactions.

Therefore, transaction design and isolation design should be considered together.

## Transaction Boundary and Deadlocks

Deadlocks often arise when transactions acquire locks in inconsistent order.

Example:

```text
Transaction A                 Transaction B

Lock Account 1                Lock Account 2
      │                              │
      ▼                              ▼
Wait for Account 2           Wait for Account 1
      │                              │
      └──────────── DEADLOCK ────────┘
```

A common mitigation is consistent lock ordering:

```text
Always lock accounts by ascending ID:

Account 1
Account 2
```

Transaction boundaries matter because the longer locks remain held, the larger the window for conflicting transactions.

## Transaction Size

Transaction size should be measured in terms of both:

- Number of operations.
- Time the transaction remains open.

This is often more useful than simply counting SQL statements.

Compare:

```text
Small transaction:
BEGIN
  5 queries
COMMIT
  10 ms
```

with:

```text
Large transaction:
BEGIN
  20 queries
  external processing
  10,000-row loop
  lock contention
COMMIT
  8 seconds
```

The second transaction creates a much larger failure and contention domain.

## Batch Processing

Large batch jobs should rarely run as one enormous transaction.

Avoid:

```text
BEGIN
 │
 ├── Process 1
 ├── Process 2
 ├── ...
 ├── Process 1,000,000
 │
 └── COMMIT
```

Prefer bounded batches when business semantics permit:

```text
BEGIN
 ├── Process 1–1,000
 └── COMMIT

BEGIN
 ├── Process 1,001–2,000
 └── COMMIT

BEGIN
 ├── Process 2,001–3,000
 └── COMMIT
```

Benefits include:

- Smaller rollback scope.
- Shorter transactions.
- Lower lock duration.
- Better recovery.
- Better operational control.

The tradeoff is that the entire batch is no longer one atomic operation.

## Transaction Boundary and Retries

Transaction boundaries strongly influence retry behavior.

Suppose:

```text
BEGIN
 │
 ├── Update A
 ├── Update B
 ├── Update C
 │
 └── transient failure
```

The safest general retry model is:

```text
ROLLBACK
   │
   ▼
Reconstruct transaction
   │
   ▼
BEGIN
   │
   ├── Update A
   ├── Update B
   ├── Update C
   │
   └── COMMIT
```

Do not assume that retrying an individual SQL statement is equivalent to retrying the business transaction.

The database state may have changed between attempts.

## Idempotency and Transaction Boundaries

Retries become especially important for APIs.

Consider:

```text
POST /payments
```

If the request succeeds but the client times out:

```text
Client
  │
  ├── POST payment
  │
  ▼
Server
  │
  ├── BEGIN
  ├── Create payment
  └── COMMIT
  │
  X response lost
```

The client may retry.

A transaction alone does not guarantee that the second request will not create a duplicate payment.

The system may need:

- Idempotency keys.
- Unique constraints.
- Transactional state transitions.

Example:

```sql
CREATE UNIQUE INDEX payments_idempotency_key_uq
ON payments(idempotency_key);
```

Transaction boundaries protect atomicity; idempotency protects retry semantics.

## Transaction Boundary and Database Constraints

Application validation should not be the only protection for critical invariants.

For example:

```python
if not Payment.objects.filter(reference=reference).exists():
    Payment.objects.create(reference=reference)
```

Two concurrent requests can both observe that the reference does not exist.

A database constraint is stronger:

```sql
ALTER TABLE payments
ADD CONSTRAINT payments_reference_unique
UNIQUE (reference);
```

The transaction boundary and database constraint work together:

```text
Application
    │
    ▼
Transaction
    │
    ▼
Database constraint
    │
    ▼
Atomic state
```

## Transaction Boundaries Across Microservices

A database transaction normally cannot provide atomicity across independent services.

For example:

```text
Order Service → PostgreSQL
Payment Service → PostgreSQL
Inventory Service → PostgreSQL
```

A single local transaction cannot safely span all three.

Avoid designing:

```text
BEGIN
  Order update
  Payment update
  Inventory update
COMMIT
```

as if all databases shared one local transaction.

Instead, distributed workflows commonly use:

- Saga patterns.
- Transactional outbox.
- Idempotent consumers.
- Compensating actions.
- Event-driven workflows.

Example:

```text
Order Created
     │
     ▼
Reserve Inventory
     │
     ├── Success → Charge Payment
     │
     └── Failure → Cancel Order
```

Each service owns its local transaction boundary.

## Transaction Boundary and Connection Pools

A database connection is often occupied for the duration of a transaction.

If an application has:

```text
Connection pool = 20
```

and 20 requests hold database transactions open while waiting on external services, other requests may be unable to obtain connections.

This can create cascading latency:

```text
Long transaction
      │
      ▼
Connection held
      │
      ▼
Pool exhausted
      │
      ▼
Requests wait
      │
      ▼
Latency increases
```

Keeping transaction boundaries short is therefore also a connection-pool capacity concern.

## Transaction Boundary and Async Applications

In asynchronous Python applications such as FastAPI services, transaction ownership must be handled carefully.

Avoid holding a transaction across unrelated asynchronous work:

```text
BEGIN
 │
 ├── Database operation
 ├── await external API
 ├── await another service
 └── COMMIT
```

The database transaction remains open while the coroutine waits.

Prefer:

```text
External preparation
       │
       ▼
Short database transaction
       │
       ├── Read/validate current state
       ├── Write required changes
       └── COMMIT
```

The exact implementation depends on the database driver and ORM, but the underlying rule remains the same: **do not hold scarce database resources while waiting on unrelated work**.

## Production Transaction Boundary Checklist

When defining a transaction boundary, evaluate:

| Question | Good signal | Warning signal |
|---|---|---|
| Business atomicity | Related changes commit together | Partial state is possible |
| Duration | Milliseconds or bounded work | Seconds or unpredictable work |
| Lock scope | Locks held briefly | Locks held during external work |
| Query count | Necessary operations only | Large loops inside transaction |
| External calls | Outside transaction | HTTP/Kafka/S3 call inside transaction |
| Retry behavior | Whole unit can be retried | Partial retry changes semantics |
| Failure scope | Small and intentional | Huge rollback domain |
| Connection usage | Short-lived | Long connection occupancy |
| Concurrency | Explicit lock ordering | Inconsistent lock ordering |
| Observability | Duration and failures measured | Transaction behavior invisible |

## Common Mistakes

### Putting the Entire Request Inside a Transaction

A request can contain work that does not need transactional guarantees.

Wrapping everything in a transaction can increase lock duration and connection usage.

### Committing Inside Repository Methods

Repository-level commits prevent higher-level services from composing multiple operations atomically.

Keep transaction ownership at an appropriate application-service or unit-of-work boundary.

### Calling External Services Inside Transactions

Network latency is unpredictable.

A slow payment service, Kafka broker, HTTP API, or third-party dependency can unnecessarily extend the database transaction.

### Performing Large Loops Inside One Transaction

Processing millions of records in one transaction creates a large failure and resource domain.

Use bounded batches when the business operation permits partial progress.

### Assuming Transactions Solve Distributed Consistency

A PostgreSQL transaction cannot atomically commit a PostgreSQL update and a separate microservice's database mutation.

Use distributed workflow patterns instead.

### Ignoring Retry Semantics

A transaction can guarantee atomicity without guaranteeing idempotency.

A retried API request may still create duplicate business operations unless the application explicitly handles retries.

### Holding Locks While Doing Application Work

Acquiring `SELECT ... FOR UPDATE` and then performing expensive computation or network I/O keeps locks held unnecessarily.

Move non-database work outside the critical transaction path where correctness permits.

### Catching Exceptions at the Wrong Boundary

This can produce confusing behavior:

```python
with transaction.atomic():
    try:
        perform_database_operation()
    except Exception:
        pass
```

If a database operation fails, the transaction may no longer be usable in the expected way.

Use nested transaction boundaries or savepoints when a failure is intentionally recoverable.

## Production Considerations

### Keep Boundaries Explicit

A senior codebase should make transaction ownership easy to identify.

Prefer:

```python
def place_order(command):
    with transaction.atomic():
        ...
```

over having multiple lower-level functions independently decide when to commit.

### Measure Transaction Duration

Monitor:

- Transaction duration.
- Lock wait time.
- Deadlocks.
- Rollback rate.
- Database connection pool utilization.
- Long-running transactions.
- Query latency inside transactions.
- Transaction retries.

Transaction duration is often more operationally significant than raw query count.

### Keep Transactions Deterministic

Transactions are easier to reason about when they contain predictable database operations.

Avoid:

- Random delays.
- External network calls.
- User interaction.
- File processing.
- Unbounded loops.
- Long computations.

### Use Database Constraints

Critical invariants should be enforced as close to the data as practical:

```text
Application validation
        +
Transaction boundary
        +
Database constraints
```

This combination is substantially more robust than application checks alone.

## Security Considerations

Transaction boundaries do not replace authorization.

For example:

```python
with transaction.atomic():
    update_account(account_id)
```

does not establish that the caller is authorized to modify that account.

Authorization must be validated explicitly.

At the database layer, use:

- Least-privilege credentials.
- Parameterized queries.
- Appropriate row-level security where required.
- Database constraints.
- Auditing for sensitive mutations.

For financial or security-sensitive operations, transaction boundaries should be designed together with authorization and concurrency controls.

## High Availability and Disaster Recovery

Transactions provide atomicity and consistency within their database scope, but they do not eliminate operational failure.

Production systems should also consider:

- Database replication.
- Automated backups.
- Point-in-time recovery.
- Failover behavior.
- Connection retry behavior.
- Transaction retry behavior.
- Idempotent application operations.

A database failover can interrupt an in-flight transaction. The application should treat the transaction as failed and reconstruct the logical operation when retrying.

Do not assume:

```text
Connection failure
      │
      ▼
"Maybe COMMIT succeeded"
```

can be resolved safely by blindly repeating writes.

Design retry behavior around idempotency and durable business identifiers.

## Interview Traps

### Should Every API Request Use a Transaction?

No.

Use transactions when multiple operations require atomicity or a consistent transactional view.

### Where Should the Transaction Boundary Live?

Usually around the application-level business operation that requires atomic database changes, often in a service or unit-of-work layer.

### Why Avoid External Calls Inside Transactions?

Because unpredictable network latency increases transaction duration, lock duration, connection occupancy, and failure exposure.

### Can a Transaction Span Multiple Microservices?

A normal local database transaction cannot provide atomicity across independent service databases.

Use patterns such as Saga and transactional outbox for distributed workflows.

### Does a Transaction Make an API Idempotent?

No.

Transactions provide atomicity; idempotency prevents duplicate effects when an operation is retried.

### Is a Larger Transaction More Consistent?

Not automatically.

A larger transaction can provide a larger atomicity boundary, but it can also increase contention, lock duration, rollback cost, and resource consumption.

### Should Repositories Commit Their Own Changes?

Usually not when multiple repositories participate in one business operation. The higher-level transaction owner should control the commit.

### What Determines a Good Transaction Boundary?

The business invariant and required atomicity should determine the boundary, followed by concurrency, performance, failure, and operational considerations.

## Practical Design Pattern

A robust backend transaction often follows this structure:

```text
API Request
    │
    ▼
Validate Input
    │
    ▼
Application Service
    │
    ├── Non-database preparation
    │
    ▼
BEGIN TRANSACTION
    │
    ├── Read current state
    ├── Lock required resources
    ├── Validate concurrency-sensitive rules
    ├── Apply database mutations
    ├── Record outbox event if needed
    │
    ▼
COMMIT
    │
    ▼
Trigger post-commit work
    │
    ├── Celery
    ├── Kafka publisher
    └── Other asynchronous processing
```

The transaction is deliberately kept around the smallest set of operations that must be atomic.

## Decision Guide

| Scenario | Transaction strategy |
|---|---|
| Single independent write | Often rely on the database statement transaction |
| Multiple related writes | One explicit transaction |
| Financial transfer | One transaction covering both sides |
| Inventory reservation | Short transaction with appropriate concurrency control |
| Optional database subsection | Savepoint/nested transaction |
| Large independent batch | Bounded transactions |
| External HTTP dependency | Prefer outside transaction |
| Database + Kafka event | Transactional outbox |
| Database + Celery task | Schedule after commit |
| Multiple microservices | Local transactions + distributed workflow |
| Retried API mutation | Transaction + idempotency |
| Long computation | Outside database transaction where possible |

## Key Takeaways

- **A transaction boundary should represent the smallest business operation that must remain atomically consistent.**
- **Keep transactions short and avoid external calls, long computations, and unbounded loops while a transaction is open.**
- **Transaction ownership should normally live at the application-service or unit-of-work level rather than being scattered across repositories.**
- **Transactions provide atomicity, but they do not provide API idempotency or distributed atomicity across microservices.**
- **Good transaction boundaries reduce lock contention, connection-pool pressure, retry complexity, and production failure impact while preserving required business invariants.**