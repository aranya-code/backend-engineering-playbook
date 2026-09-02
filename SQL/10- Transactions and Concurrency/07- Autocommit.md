# 07- Autocommit

## Overview

**Autocommit** is the database connection behavior where each individual SQL statement is automatically committed as its own transaction unless an explicit transaction is started.

For example, with autocommit enabled:

```sql
INSERT INTO users (email)
VALUES ('alice@example.com');
```

The statement executes as a transaction and is committed automatically when it succeeds.

Conceptually:

```text
SQL Statement
     │
     ▼
BEGIN
     │
     ▼
Execute Statement
     │
     ├── Success ──► COMMIT
     │
     └── Failure ──► ROLLBACK
```

Autocommit is convenient for independent database operations, but it becomes dangerous when several statements must succeed or fail together.

```text
Autocommit
──────────

INSERT A ── COMMIT
INSERT B ── COMMIT
INSERT C ── COMMIT
```

versus an explicit transaction:

```text
Explicit Transaction
────────────────────

BEGIN
 │
 ├── INSERT A
 ├── INSERT B
 ├── INSERT C
 │
 └── COMMIT
```

The key engineering decision is knowing **when autocommit is sufficient and when an explicit transaction boundary is required**.

## What Autocommit Means

When a connection operates in autocommit mode, a statement that is not already inside an explicit transaction is committed automatically after successful execution.

For a single statement:

```sql
INSERT INTO orders (customer_id, status)
VALUES (42, 'pending');
```

the database effectively treats the operation as:

```text
BEGIN
  INSERT ...
COMMIT
```

The exact implementation is database- and driver-specific, but the application-level behavior is that the statement becomes durable without an explicit `COMMIT`.

A multi-statement sequence does **not** automatically become one atomic transaction merely because the statements execute on the same connection.

```sql
INSERT INTO orders (...);

INSERT INTO order_items (...);

UPDATE inventory ...;
```

With autocommit enabled, these may represent three separate transactions.

If the third statement fails, the first two can remain committed.

## Why Autocommit Exists

Autocommit is useful because most simple database operations do not require a multi-statement transaction.

Examples include:

```sql
SELECT id, email
FROM users
WHERE id = 42;
```

or:

```sql
UPDATE users
SET last_login_at = CURRENT_TIMESTAMP
WHERE id = 42;
```

For independent operations, automatically committing each statement:

- Reduces transaction-management code.
- Provides straightforward durability semantics.
- Prevents accidental long-lived transactions.
- Works naturally with request/response CRUD operations.
- Makes simple database interactions easier to use.

Autocommit is therefore a useful **default**, not a replacement for explicit transaction design.

## Autocommit vs Explicit Transactions

| Aspect | Autocommit | Explicit transaction |
|---|---|---|
| Transaction scope | Usually one statement | Multiple statements |
| Atomicity across statements | No | Yes |
| Application complexity | Low | Higher |
| Lock duration | Usually short | Depends on transaction duration |
| Failure isolation | Per statement | Entire transaction |
| Best for | Independent operations | Related business operations |
| Rollback control | Limited to statement | Explicit `ROLLBACK` |
| Risk | Partial multi-step updates | Long transactions if poorly designed |

A senior engineer should not ask:

> Should autocommit always be enabled?

The better question is:

> What transaction boundary does this business operation require?

## Autocommit and Explicit `BEGIN`

Autocommit does not prevent explicit transactions.

A connection can normally operate like this:

```text
Autocommit mode
     │
     ├── Statement → automatically committed
     │
     ▼
BEGIN
     │
     ├── Statement
     ├── Statement
     ├── Statement
     │
     ▼
COMMIT
     │
     ▼
Autocommit behavior resumes
```

For example:

```sql
UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;

COMMIT;
```

The first update is independent. The two updates inside `BEGIN` form one transaction.

## The Important Difference: One Statement vs Multiple Statements

Consider creating an order:

```sql
INSERT INTO orders (customer_id, status)
VALUES (42, 'pending');

INSERT INTO order_items (order_id, product_id, quantity)
VALUES (1001, 500, 2);

UPDATE inventory
SET quantity = quantity - 2
WHERE product_id = 500;
```

With autocommit, a failure in the inventory update does not necessarily undo the earlier inserts.

This can produce:

```text
orders       ✓ committed
order_items  ✓ committed
inventory    ✗ failed
```

If these changes represent one business operation, the correct design is:

```sql
BEGIN;

INSERT INTO orders (customer_id, status)
VALUES (42, 'pending');

INSERT INTO order_items (order_id, product_id, quantity)
VALUES (1001, 500, 2);

UPDATE inventory
SET quantity = quantity - 2
WHERE product_id = 500;

COMMIT;
```

Now failure before `COMMIT` allows the transaction to be rolled back as one unit.

## Autocommit and Transaction Boundaries

Autocommit effectively creates very small transaction boundaries.

```text
Statement A
   │
   └── COMMIT

Statement B
   │
   └── COMMIT

Statement C
   │
   └── COMMIT
```

Explicit transaction management allows the application to enlarge that boundary intentionally:

```text
BEGIN
 │
 ├── Statement A
 ├── Statement B
 ├── Statement C
 │
 └── COMMIT
```

This is why autocommit should be understood as a **transaction-boundary policy** rather than simply a convenience setting.

## PostgreSQL Behavior

PostgreSQL normally operates in a mode where each statement is executed within a transaction when the client has not explicitly started one.

For example:

```sql
INSERT INTO users (email)
VALUES ('alice@example.com');
```

is committed after successful execution when no explicit transaction is active.

An explicit transaction changes the behavior:

```sql
BEGIN;

INSERT INTO users (email)
VALUES ('alice@example.com');

UPDATE users
SET status = 'active'
WHERE email = 'alice@example.com';

COMMIT;
```

The two statements now belong to the same transaction.

PostgreSQL also provides transaction control through:

```sql
BEGIN;
COMMIT;
ROLLBACK;
SAVEPOINT;
ROLLBACK TO SAVEPOINT;
```

## Autocommit in Python Database Drivers

Python database drivers commonly expose an `autocommit` connection setting, although the exact API differs by driver.

For example, with `psycopg`:

```python
import psycopg

with psycopg.connect(
    "postgresql://app_user:password@localhost/app"
) as conn:
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET last_login_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (42,),
        )
```

For multi-statement atomic work:

```python
import psycopg

with psycopg.connect(
    "postgresql://app_user:password@localhost/app"
) as conn:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE accounts
                SET balance = balance - %s
                WHERE id = %s
                """,
                (100, 1),
            )

            cur.execute(
                """
                UPDATE accounts
                SET balance = balance + %s
                WHERE id = %s
                """,
                (100, 2),
            )
```

The important principle is to make the transaction boundary explicit around the business operation.

## Autocommit in Django

Django operates in autocommit mode by default.

This means individual ORM queries are committed automatically unless code explicitly enters a transaction.

For example:

```python
user = User.objects.create(
    email="alice@example.com",
)
```

does not require an explicit `commit()` in normal Django application code.

For multiple related changes:

```python
from django.db import transaction

with transaction.atomic():
    order = Order.objects.create(
        customer_id=42,
        status="pending",
    )

    OrderItem.objects.create(
        order=order,
        product_id=500,
        quantity=2,
    )
```

`transaction.atomic()` creates the required transaction boundary.

This model is useful because developers get safe behavior for simple operations without having to manually commit every query, while explicit business transactions remain available when needed.

## Autocommit and Django Request Handling

A common misconception is:

> Django's autocommit means every HTTP request is one transaction.

That is incorrect.

By default, Django does not make the entire request one transaction merely because autocommit is enabled.

A view such as:

```python
def create_user(request):
    User.objects.create(email="alice@example.com")
    return JsonResponse({"status": "created"})
```

performs the database write under normal autocommit behavior.

If the view contains multiple operations that must be atomic, use:

```python
from django.db import transaction

@transaction.atomic
def create_order(request):
    ...
```

or:

```python
with transaction.atomic():
    ...
```

## `ATOMIC_REQUESTS`

Django can be configured with:

```python
DATABASES = {
    "default": {
        # ...
        "ATOMIC_REQUESTS": True,
    }
}
```

This wraps each request in a transaction.

Conceptually:

```text
HTTP Request
     │
     ▼
BEGIN
     │
     ├── View
     ├── Database operations
     │
     ▼
COMMIT / ROLLBACK
```

This can simplify transactional behavior for applications where most requests require request-wide atomicity.

However, it can also keep transactions open longer than necessary.

Potential consequences include:

- Longer lock duration.
- Higher database connection occupancy.
- More contention.
- Increased latency under load.
- Greater rollback scope.
- Transactions spanning work that does not need atomicity.

For high-throughput services, explicit `transaction.atomic()` blocks around business-critical operations are often easier to reason about.

## Autocommit and SQLAlchemy

SQLAlchemy's transaction model is intentionally different from simply treating every application operation as an independent autocommit statement.

Modern SQLAlchemy encourages explicit transaction management:

```python
with Session(engine) as session:
    with session.begin():
        session.add(order)
        session.add(order_item)
```

The context manager commits on successful completion and rolls back when an exception escapes the block.

For database-level operations that genuinely require autocommit semantics, SQLAlchemy also provides execution options for statements or connections where supported.

The important engineering rule is to understand the ORM's transaction model rather than assuming that the database's autocommit setting maps directly to ORM behavior.

## When Autocommit Is Appropriate

Autocommit is generally appropriate for operations that are logically independent.

Examples include:

### Independent Updates

```sql
UPDATE users
SET last_seen_at = CURRENT_TIMESTAMP
WHERE id = 42;
```

If this single mutation succeeds, there is no related database mutation that must also succeed atomically.

### Simple Inserts

```sql
INSERT INTO audit_events(event_type, created_at)
VALUES ('login', CURRENT_TIMESTAMP);
```

When the insert is intentionally independent from another operation, autocommit can be appropriate.

### Administrative Statements

Some database administrative or schema operations may require special transaction behavior depending on the database.

Always verify the specific database's transactional restrictions before enabling autocommit for administrative operations.

### Health Checks

A simple health check can execute a read:

```sql
SELECT 1;
```

No application-managed transaction is normally required.

## When Autocommit Is Not Appropriate

Autocommit is insufficient when several statements represent one atomic business operation.

Examples:

- Money transfers.
- Order creation plus inventory reservation.
- Updating a parent and required child records.
- Maintaining related counters.
- State transitions involving multiple tables.
- Recording a business mutation and its outbox event.
- Multi-step uniqueness or allocation logic.
- Concurrency-sensitive resource reservation.

The rule is:

> If failure between two statements would leave an invalid committed state, those statements should normally share an explicit transaction boundary.

## Autocommit and Constraints

Database constraints remain effective under autocommit.

For example:

```sql
CREATE UNIQUE INDEX users_email_uq
ON users(email);
```

With autocommit:

```sql
INSERT INTO users(email)
VALUES ('alice@example.com');
```

the unique constraint is still enforced.

Autocommit does not weaken database constraints. It changes **how statements are grouped into transactions**.

## Autocommit and Concurrency

Autocommit can reduce lock duration because independent statements generally finish their transactions quickly.

For example:

```text
Request A
  │
  ├── UPDATE
  └── COMMIT

Request B
  │
  ├── UPDATE
  └── COMMIT
```

However, autocommit does not eliminate race conditions.

This is unsafe regardless of autocommit:

```python
if not user_exists(email):
    create_user(email)
```

Two concurrent requests can both observe the absence of the user.

A database uniqueness constraint is required:

```sql
CREATE UNIQUE INDEX users_email_uq
ON users(email);
```

Concurrency correctness comes from the combination of:

- Transaction boundaries.
- Isolation.
- Locks where necessary.
- Database constraints.
- Correct application logic.

## Autocommit and Isolation

Autocommit does not define the isolation level.

These are separate concepts:

```text
Autocommit
    │
    └── How statements are grouped into transactions

Isolation level
    │
    └── What concurrent transactions can observe
```

For example, a database can use a particular isolation level while each statement executes in its own transaction.

Changing autocommit does not automatically change:

- Read phenomena.
- Locking behavior.
- Isolation guarantees.
- Visibility rules.

## Autocommit and Performance

Autocommit can be beneficial for short independent operations because transactions complete quickly.

However, using autocommit for a large number of related writes can introduce unnecessary commit overhead.

For example:

```text
10,000 inserts

Autocommit:
INSERT → COMMIT
INSERT → COMMIT
INSERT → COMMIT
...
```

versus:

```text
BEGIN
  INSERT
  INSERT
  INSERT
  ...
COMMIT
```

The second approach can be significantly more efficient when atomicity and batch semantics permit it.

The tradeoff is that larger transactions consume more resources and may increase lock contention.

Therefore:

> Optimize transaction boundaries based on both correctness and workload characteristics.

## Bulk Operations

For large data imports, blindly using autocommit can create excessive transaction overhead.

A bounded transaction strategy is often better:

```text
BEGIN
  Insert rows 1–1,000
COMMIT

BEGIN
  Insert rows 1,001–2,000
COMMIT

BEGIN
  Insert rows 2,001–3,000
COMMIT
```

This balances:

- Commit overhead.
- Rollback cost.
- Lock duration.
- Recovery time.
- Memory/resource usage.

The appropriate batch size depends on workload, database configuration, row size, indexes, constraints, and latency requirements.

## Autocommit and Connection Pools

Connection pooling makes transaction state especially important.

A pooled connection can be reused by another request after the current request completes.

If application code leaves a transaction open:

```text
Request A
   │
   ├── BEGIN
   ├── UPDATE
   └── Connection returned incorrectly
              │
              ▼
        Connection Pool
              │
              ▼
Request B receives connection
```

Request B may inherit unexpected transaction state.

Production applications should ensure that connections are returned to the pool in a clean state.

Frameworks and mature database drivers generally provide mechanisms to manage this, but application code must still avoid manually bypassing those lifecycle guarantees.

## Autocommit and Error Handling

Consider:

```sql
UPDATE accounts
SET balance = balance - 100
WHERE id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE id = 2;
```

With autocommit, the first statement may already be committed before the second fails.

Calling:

```sql
ROLLBACK;
```

after the second failure does not undo a transaction that was already committed.

This is one of the most important autocommit pitfalls.

If both operations are atomic:

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

then:

```sql
ROLLBACK;
```

can undo both before commit.

## Autocommit and DDL

Transactional behavior for DDL differs across database engines and specific statements.

PostgreSQL supports transactional DDL for many operations, while some database systems or particular administrative operations have different restrictions.

Do not assume:

```text
DDL + autocommit
```

has identical semantics across all SQL databases.

For production migrations, follow the database's documented transactional behavior and your migration framework's conventions.

## Autocommit and the Transactional Outbox

Suppose an order service executes:

```text
UPDATE orders
INSERT outbox_event
```

With autocommit, these can commit independently.

That can create:

```text
orders       ✓
outbox       ✗
```

The order exists, but no event is recorded.

Instead:

```sql
BEGIN;

UPDATE orders
SET status = 'confirmed'
WHERE id = 1001;

INSERT INTO outbox_events(event_type, aggregate_id)
VALUES ('order.confirmed', 1001);

COMMIT;
```

Both changes now share one transaction.

The outbox publisher can later deliver the event to Kafka or another messaging system.

## Autocommit and Celery

The same issue occurs when scheduling background work.

This can be problematic:

```python
order = Order.objects.create(status="pending")
send_order_task.delay(order.id)
```

If the task executes before the surrounding business operation has completed, it may observe incomplete state.

For a multi-step transaction:

```python
from django.db import transaction

with transaction.atomic():
    order = Order.objects.create(status="pending")
    update_related_state(order)

    transaction.on_commit(
        lambda: send_order_task.delay(order.id)
    )
```

The task is scheduled only after the transaction commits successfully.

## Production Best Practices

### Treat Autocommit as the Default for Independent Work

Autocommit is convenient and efficient for operations that do not need to share an atomic boundary.

### Use Explicit Transactions for Business Operations

If multiple database mutations form one business operation, make the transaction boundary explicit.

```python
with transaction.atomic():
    create_order()
    reserve_inventory()
    record_outbox_event()
```

### Keep Explicit Transactions Short

Avoid:

```text
BEGIN
 │
 ├── Database work
 ├── HTTP request
 ├── Large computation
 ├── File processing
 └── COMMIT
```

Prefer:

```text
Preparation
   │
   ▼
BEGIN
   │
   ├── Required database reads/writes
   └── COMMIT
```

### Never Rely on Rollback After an Autocommitted Statement

Once a statement has committed, a later rollback cannot undo it.

### Understand Your Framework's Transaction Model

Django, SQLAlchemy, and individual database drivers expose different abstractions.

Do not mix assumptions between:

- Database autocommit.
- Driver transaction behavior.
- ORM session behavior.
- Framework request transactions.

### Use Constraints for Concurrency Safety

Autocommit does not protect check-then-act application logic.

Use:

- Unique constraints.
- Foreign keys.
- Check constraints.
- Appropriate locking.
- Explicit transactions.

### Test Failure Paths

Transaction behavior should be tested under failures, not only successful execution.

Verify:

- Mid-transaction exceptions.
- Constraint violations.
- Deadlocks.
- Connection failures.
- Retry behavior.
- Duplicate requests.
- Background jobs triggered after commit.

## Common Mistakes

### Assuming Autocommit Means Every Operation Is Safe

Autocommit makes individual statements independent. It does not make a multi-step business workflow atomic.

### Calling `ROLLBACK` After Every Error

With autocommit, the failed statement's transaction may already have been rolled back, while previous statements may already be committed.

The correct response depends on the transaction boundary.

### Disabling Autocommit Globally Without a Plan

Turning autocommit off can create long-lived transactions if developers forget to commit or roll back.

This can cause:

- Open transactions.
- Locks remaining held.
- Connection pool exhaustion.
- MVCC cleanup pressure.
- Unexpected visibility behavior.

### Committing Inside Repositories

A repository that commits every write prevents higher-level services from composing multiple operations into one transaction.

### Treating Autocommit as an Isolation Mechanism

Autocommit and isolation are separate concepts.

### Using Autocommit for Large Batch Writes

Thousands of individual transactions can create unnecessary overhead.

Use appropriately sized explicit transactions when the workload permits.

### Forgetting Pooled Connection State

Leaving transaction state or session-level settings behind can affect subsequent users of a pooled connection.

## Interview Traps

### Is Autocommit the Same as No Transactions?

No.

Each statement still executes transactionally; autocommit simply causes the transaction to be completed automatically.

### Does Autocommit Make Multiple SQL Statements Atomic?

No.

Separate statements can be separate transactions.

### Does `ROLLBACK` Undo the Previous Autocommitted Statement?

No.

Once the statement's transaction has committed, a later rollback cannot undo it.

### Is Autocommit Faster?

Not universally.

It can be efficient for independent short operations, but repeated commits can make large batches slower than appropriately sized explicit transactions.

### Does Autocommit Change Isolation Level?

No.

Autocommit determines transaction grouping; isolation determines concurrency visibility and behavior.

### Does Django Use Autocommit?

Yes. Django uses autocommit by default unless code or configuration establishes an explicit transaction.

### Should Autocommit Be Disabled in Production?

Not as a blanket rule.

The appropriate configuration depends on the driver, ORM, workload, and transaction-management architecture. Explicit transactions should be used where business atomicity requires them.

## Decision Guide

| Situation | Recommended approach |
|---|---|
| Single independent `INSERT` | Autocommit is usually appropriate |
| Single independent `UPDATE` | Autocommit is usually appropriate |
| Simple `SELECT` | Autocommit/default driver behavior is usually sufficient |
| Money transfer | Explicit transaction |
| Order + order items | Explicit transaction |
| Inventory reservation + order mutation | Explicit transaction |
| Database + outbox record | Explicit transaction |
| Database + Celery dispatch | Transaction + post-commit dispatch |
| Large import | Bounded explicit transactions |
| Independent audit write | Often autocommit |
| Multiple microservices | Local transactions + distributed workflow |
| Concurrency-sensitive check-then-act | Explicit transaction and/or database constraints |
| DDL/migrations | Follow database and migration-tool transaction semantics |

## Practical Mental Model

Think of autocommit as creating this default:

```text
Statement
    │
    ▼
Transaction
    │
    ▼
Commit
```

An explicit transaction deliberately changes the grouping:

```text
Business Operation
       │
       ▼
BEGIN
       │
       ├── Statement
       ├── Statement
       ├── Statement
       │
       ▼
     COMMIT
```

The application should move from the default model to the explicit model whenever business correctness requires multiple operations to succeed or fail together.

## Key Takeaways

- **Autocommit normally makes each independent SQL statement its own transaction, automatically committing successful statements.**
- **Autocommit does not make multiple statements atomic; related business mutations require an explicit transaction boundary.**
- **Autocommit and isolation level are separate concerns: one controls transaction grouping, while the other controls concurrent visibility and behavior.**
- **Autocommit is useful for independent operations, but explicit transactions are essential for workflows such as transfers, inventory updates, and transactional outbox writes.**
- **Do not disable autocommit blindly; transaction behavior should be deliberate, short-lived, framework-aware, and validated under failure and concurrency scenarios.**