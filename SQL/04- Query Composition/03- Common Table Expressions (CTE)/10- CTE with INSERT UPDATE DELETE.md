# 10- CTE with INSERT UPDATE DELETE

## Overview

Common Table Expressions (CTEs) are not limited to `SELECT` queries. In databases that support data-modifying statements with CTEs, they can be used to structure complex `INSERT`, `UPDATE`, and `DELETE` workflows as a single SQL statement.

This is particularly useful when a write operation depends on another relational operation:

- Insert rows derived from existing data.
- Update rows based on an intermediate result.
- Delete rows identified by a CTE.
- Move data between tables.
- Archive and remove records as one database operation.
- Capture affected rows with `RETURNING`.
- Compose multi-stage data transformations while preserving transactional atomicity.

The important distinction is that **CTE syntax and data-modifying CTE semantics are database-specific**. PostgreSQL provides powerful support for data-modifying statements inside `WITH`; other databases may support only some forms of CTE-based writes.

For production systems, always verify the exact behavior supported by the target database rather than assuming that CTE behavior is portable.

## Basic Structure

A CTE is introduced with `WITH` and followed by the statement that consumes it:

```sql
WITH eligible_customers AS (
    SELECT
        id
    FROM customers
    WHERE status = 'active'
)
UPDATE customers
SET last_reviewed_at = CURRENT_TIMESTAMP
WHERE id IN (
    SELECT id
    FROM eligible_customers
);
```

The CTE creates a named intermediate relation:

```text
customers
   ↓
eligible_customers
   ↓
UPDATE customers
   ↓
changed rows
```

The CTE itself does not necessarily modify data. It can simply define the rows that the final write operation should target.

## CTE with `INSERT`

### Insert Rows Selected from Another Table

A common pattern is inserting transformed or filtered data into another table.

```sql
WITH eligible_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
INSERT INTO order_audit (
    order_id,
    customer_id,
    amount,
    recorded_at
)
SELECT
    id,
    customer_id,
    total_amount,
    CURRENT_TIMESTAMP
FROM eligible_orders;
```

This is useful when the source data needs preprocessing before insertion.

Typical use cases include:

- Creating audit records.
- Populating reporting tables.
- Migrating data.
- Creating derived records.
- Backfilling new columns or tables.
- Building summary tables.

### Insert with Aggregation

A CTE can aggregate data before inserting it.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
INSERT INTO customer_revenue_snapshot (
    customer_id,
    total_revenue,
    snapshot_at
)
SELECT
    customer_id,
    total_revenue,
    CURRENT_TIMESTAMP
FROM customer_revenue;
```

The CTE establishes the required grain:

```text
orders
  ↓
GROUP BY customer_id
  ↓
customer_revenue
  ↓
INSERT snapshot
```

This keeps aggregation inside the database rather than transferring raw rows to application code.

## `INSERT ... SELECT` vs CTE

A CTE is not automatically required for an insert-from-select operation.

This may be sufficient:

```sql
INSERT INTO customer_revenue_snapshot (
    customer_id,
    total_revenue
)
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

A CTE becomes useful when the source relation represents a meaningful intermediate stage:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
INSERT INTO customer_revenue_snapshot (
    customer_id,
    total_revenue
)
SELECT
    customer_id,
    total_revenue
FROM customer_revenue;
```

Prefer the simpler query when the additional abstraction provides no meaningful clarity.

## CTE with `UPDATE`

A CTE can identify the rows that need updating.

```sql
WITH inactive_customers AS (
    SELECT
        id
    FROM customers
    WHERE last_login_at < CURRENT_TIMESTAMP - INTERVAL '365 days'
      AND status = 'active'
)
UPDATE customers AS c
SET status = 'inactive'
FROM inactive_customers AS i
WHERE c.id = i.id;
```

This pattern separates:

1. Determining which rows qualify.
2. Applying the mutation.

That separation is useful when eligibility logic is complex.

## Updating from Aggregated Data

Suppose customer records contain a cached order count:

```text
customers
---------
id
order_count
```

and the authoritative count comes from `orders`.

A CTE can calculate the count first:

```sql
WITH order_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS total_orders
    FROM orders
    GROUP BY customer_id
)
UPDATE customers AS c
SET order_count = oc.total_orders
FROM order_counts AS oc
WHERE c.id = oc.customer_id;
```

This is useful for:

- Data correction.
- Backfills.
- Reconciliation.
- Derived-value maintenance.
- Batch maintenance jobs.

For fields that can be computed cheaply at read time, however, storing redundant counters may introduce consistency concerns. Cached aggregates should have a clear ownership and reconciliation strategy.

## Updating with a Window Function

CTEs can combine window functions with updates.

For example, assign a sequence number to each customer's orders:

```sql
WITH ranked_orders AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at, id
        ) AS sequence_number
    FROM orders
)
UPDATE orders AS o
SET sequence_number = r.sequence_number
FROM ranked_orders AS r
WHERE o.id = r.id;
```

This is useful for controlled backfills and data migrations.

The important pattern is:

```text
source rows
   ↓
window calculation
   ↓
CTE result
   ↓
UPDATE target rows
```

When performing large migrations, execute this in controlled batches if the table size and lock behavior make one large transaction operationally unsafe.

## CTE with `DELETE`

A CTE can identify rows for deletion.

```sql
WITH expired_sessions AS (
    SELECT
        id
    FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP
)
DELETE FROM sessions AS s
USING expired_sessions AS e
WHERE s.id = e.id;
```

This separates selection logic from deletion logic.

For a simple predicate, however, the CTE may be unnecessary:

```sql
DELETE FROM sessions
WHERE expires_at < CURRENT_TIMESTAMP;
```

Use a CTE when the target set requires meaningful relational processing.

## Delete Based on Aggregation

For example, delete customers who have no orders:

```sql
WITH customers_without_orders AS (
    SELECT
        c.id
    FROM customers AS c
    LEFT JOIN orders AS o
        ON o.customer_id = c.id
    WHERE o.id IS NULL
)
DELETE FROM customers AS c
USING customers_without_orders AS x
WHERE c.id = x.id;
```

Before executing destructive queries in production, verify:

- Foreign-key dependencies.
- Cascading behavior.
- Application references.
- Audit requirements.
- Retention requirements.
- Transaction size.
- Lock duration.
- Recovery procedures.

## Data-Modifying CTEs in PostgreSQL

PostgreSQL supports data-modifying statements inside a `WITH` clause.

For example:

```sql
WITH deleted_orders AS (
    DELETE FROM orders
    WHERE status = 'cancelled'
      AND created_at < CURRENT_TIMESTAMP - INTERVAL '2 years'
    RETURNING id, customer_id
)
INSERT INTO deleted_order_archive (
    order_id,
    customer_id,
    archived_at
)
SELECT
    id,
    customer_id,
    CURRENT_TIMESTAMP
FROM deleted_orders;
```

This creates a database-side workflow:

```text
DELETE orders
      │
      │ RETURNING
      ▼
deleted_orders CTE
      │
      ▼
INSERT archive
```

This pattern can be substantially safer than:

1. Selecting IDs into application memory.
2. Deleting the source rows.
3. Inserting archive records separately.

The single SQL statement provides a single transactional unit.

## `RETURNING` and CTEs

`RETURNING` is particularly powerful with data-modifying CTEs in PostgreSQL.

Consider:

```sql
WITH moved_orders AS (
    DELETE FROM orders
    WHERE status = 'cancelled'
    RETURNING
        id,
        customer_id,
        total_amount
)
INSERT INTO archived_orders (
    order_id,
    customer_id,
    total_amount,
    archived_at
)
SELECT
    id,
    customer_id,
    total_amount,
    CURRENT_TIMESTAMP
FROM moved_orders;
```

The `DELETE` produces rows through `RETURNING`.

The CTE exposes those rows to the subsequent `INSERT`.

This avoids querying the source table again after deletion.

## Atomic Data Movement

A useful production pattern is:

```text
Source table
     │
     │ DELETE ... RETURNING
     ▼
CTE result
     │
     │ INSERT
     ▼
Archive table
```

The operation can execute within one transaction.

If the statement fails, the transaction can be rolled back rather than leaving the system in a partially completed state.

This is especially useful for:

- Archival jobs.
- Data migrations.
- State transitions.
- Cleanup workflows.
- Retention enforcement.

Atomicity does not eliminate operational concerns. A large statement can still generate significant WAL, locks, replication traffic, and transaction duration.

## Multiple Data-Modifying CTEs

PostgreSQL allows multiple data-modifying CTEs in a single statement.

For example:

```sql
WITH archived_orders AS (
    DELETE FROM orders
    WHERE status = 'cancelled'
      AND created_at < CURRENT_TIMESTAMP - INTERVAL '2 years'
    RETURNING id, customer_id, total_amount
),
archived_rows AS (
    INSERT INTO order_archive (
        order_id,
        customer_id,
        total_amount,
        archived_at
    )
    SELECT
        id,
        customer_id,
        total_amount,
        CURRENT_TIMESTAMP
    FROM archived_orders
    RETURNING order_id
)
SELECT COUNT(*) AS archived_count
FROM archived_rows;
```

This can express an entire database-side workflow.

However, complexity increases quickly. A senior engineer should prefer this pattern when the atomic relationship between stages is valuable, not merely because SQL permits it.

## Important PostgreSQL Execution Semantics

Data-modifying statements inside a PostgreSQL `WITH` are executed exactly once and are executed to completion independently of whether the outer query consumes all rows from their `RETURNING` output.

A crucial implication is that sibling data-modifying CTEs should not be designed around a procedural assumption such as:

```text
CTE A finishes
    ↓
CTE B sees all physical changes from CTE A
    ↓
CTE C sees B
```

Instead, think of each data-modifying CTE as part of one statement-level operation whose interactions are primarily expressed through `RETURNING`.

For example, this is the useful dependency:

```sql
WITH deleted_rows AS (
    DELETE FROM orders
    WHERE status = 'cancelled'
    RETURNING id
)
INSERT INTO order_archive (order_id)
SELECT id
FROM deleted_rows;
```

The second stage consumes the rows returned by the first stage.

Do not rely on repeatedly querying the same target table within sibling data-modifying CTEs as though they were sequential procedural statements.

## Visibility and Snapshot Semantics

PostgreSQL data-modifying statements in a single `WITH` execute with the same statement snapshot.

This means that multiple modifying sub-statements should generally be viewed as operating from the same snapshot, while their effects are communicated explicitly through `RETURNING`.

This is a major interview and production consideration.

A CTE containing a `DELETE` is not equivalent to writing:

```text
DELETE
then
SELECT
then
UPDATE
```

as separate application statements.

The database optimizer and execution model determine how the statement is executed.

When correctness depends on a particular mutation sequence, prefer explicit transactional statements or communicate data between modifying stages through `RETURNING`.

## Transaction Boundaries

A CTE containing writes still participates in the surrounding transaction.

For example:

```sql
BEGIN;

WITH deleted_rows AS (
    DELETE FROM orders
    WHERE customer_id = 42
    RETURNING id
)
INSERT INTO order_deletion_audit (
    order_id,
    deleted_at
)
SELECT
    id,
    CURRENT_TIMESTAMP
FROM deleted_rows;

COMMIT;
```

If the statement fails, the transaction can be rolled back.

In application code, transaction management should normally be explicit.

For Django:

```python
from django.db import transaction

with transaction.atomic():
    # Execute the write query.
    ...
```

For SQLAlchemy or other Python database libraries, use the framework's transaction/session facilities rather than manually mixing transaction boundaries without understanding connection pooling.

## CTE Writes vs Application-Level Workflows

Consider a workflow that moves expired records to an archive.

### Application-driven approach

```text
API / worker
    ↓
SELECT expired rows
    ↓
application memory
    ↓
INSERT archive rows
    ↓
DELETE source rows
```

This introduces multiple database round trips and creates a larger failure surface.

### Database-side approach

```text
Database
    ↓
DELETE ... RETURNING
    ↓
CTE
    ↓
INSERT archive
```

The second approach can provide:

- Fewer network round trips.
- Atomicity.
- Less application memory usage.
- Less opportunity for concurrent application logic to interfere.
- Better locality of data processing.

It can also create:

- Larger transactions.
- More database CPU.
- More WAL.
- Longer locks.
- More difficult query debugging.

The database is not automatically the right place for every workflow. Use the database for relational operations and use application workers for orchestration, external APIs, long-running workflows, and operations that cannot be expressed safely as one transaction.

## Production Example: Archive and Delete

A retention job may need to archive old cancelled orders before deleting them.

```sql
WITH rows_to_archive AS (
    DELETE FROM orders
    WHERE status = 'cancelled'
      AND created_at < CURRENT_TIMESTAMP - INTERVAL '2 years'
    RETURNING
        id,
        customer_id,
        total_amount,
        created_at
)
INSERT INTO order_archive (
    order_id,
    customer_id,
    total_amount,
    original_created_at,
    archived_at
)
SELECT
    id,
    customer_id,
    total_amount,
    created_at,
    CURRENT_TIMESTAMP
FROM rows_to_archive;
```

A Celery worker could execute this periodically:

```text
Celery
   ↓
Database connection
   ↓
single transactional SQL statement
   ↓
archive + delete
   ↓
metrics / logs
```

For very large datasets, avoid attempting to archive millions of rows in one transaction. Process bounded batches.

## Batching Large Writes

A large CTE-based write can create excessive transaction pressure.

Potential effects include:

- Long-running transactions.
- Increased WAL generation.
- Replication lag.
- Large undo/MVCC cleanup requirements.
- Lock contention.
- Increased database CPU.
- Higher storage pressure.
- Difficult rollback behavior.

Instead of:

```sql
DELETE FROM orders
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '5 years';
```

for a massive table, use controlled batches where the database supports an appropriate strategy.

For PostgreSQL, one pattern is to identify a bounded set first:

```sql
WITH rows_to_delete AS (
    SELECT id
    FROM orders
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '5 years'
    ORDER BY id
    LIMIT 5000
),
deleted_rows AS (
    DELETE FROM orders AS o
    USING rows_to_delete AS r
    WHERE o.id = r.id
    RETURNING o.id
)
SELECT COUNT(*)
FROM deleted_rows;
```

Repeat the operation from a worker until no rows remain.

The exact batching strategy should account for indexes, foreign keys, partitioning, replication, and concurrent writes.

## Concurrency Considerations

Write-oriented CTEs do not eliminate race conditions automatically.

For example, a worker that identifies rows and later processes them must consider concurrent workers.

PostgreSQL row locking can be useful in job-queue patterns:

```sql
WITH next_jobs AS (
    SELECT id
    FROM jobs
    WHERE status = 'pending'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 100
)
UPDATE jobs AS j
SET
    status = 'processing',
    started_at = CURRENT_TIMESTAMP
FROM next_jobs AS n
WHERE j.id = n.id
RETURNING j.id;
```

This allows multiple workers to claim different rows without waiting on already-locked rows.

This pattern is useful for database-backed job queues, although dedicated systems such as Kafka, SQS, or other queue infrastructure may be more appropriate at higher scale or for more complex delivery semantics.

## Referential Integrity

Before using a CTE to delete or update rows, understand foreign-key relationships.

For example:

```text
customers
    │
    ├── orders
    │      │
    │      └── order_items
    │
    └── payments
```

Deleting a customer may fail because dependent records exist, or may cascade depending on the schema.

Inspect constraints before destructive migrations.

PostgreSQL can show table definitions with:

```sql
\d+ customers
```

and foreign-key relationships can be inspected through the catalog or database administration tooling.

Do not rely on an application-level assumption that deleting a parent row will behave safely.

## Performance Considerations

A CTE does not inherently improve write performance.

Performance depends on:

- Rows affected.
- Filtering selectivity.
- Indexes.
- Join strategy.
- Lock contention.
- Transaction size.
- WAL volume.
- Foreign-key checks.
- Triggers.
- Replication.
- Table bloat.
- Database configuration.

Use:

```sql
EXPLAIN
```

to inspect the planned operation and:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

when measuring an operation safely in an appropriate environment.

Be especially careful with `EXPLAIN ANALYZE` for destructive statements because it actually executes the statement.

Never run destructive `EXPLAIN ANALYZE` casually against production data.

## Indexing for CTE-Based Writes

The filtering and join predicates still need appropriate indexes.

For:

```sql
WITH expired_sessions AS (
    SELECT id
    FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP
)
DELETE FROM sessions AS s
USING expired_sessions AS e
WHERE s.id = e.id;
```

an index on:

```sql
expires_at
```

may help identify eligible sessions efficiently.

The primary key on `id` supports the subsequent target lookup.

Indexes should be designed around the actual query workload, not simply added because a column appears in a CTE.

## Security Considerations

Write-oriented CTEs require the same security discipline as any other SQL mutation.

### Use Parameterized Queries

Do not construct dynamic SQL from request data:

```python
# Avoid interpolating user-controlled values into SQL.
query = f"DELETE FROM orders WHERE customer_id = {customer_id}"
```

Use parameters:

```python
cursor.execute(
    """
    WITH rows_to_delete AS (
        SELECT id
        FROM orders
        WHERE customer_id = %s
    )
    DELETE FROM orders AS o
    USING rows_to_delete AS r
    WHERE o.id = r.id
    """,
    [customer_id],
)
```

### Apply Authorization at the Database Operation

For multi-tenant systems, constrain the mutation by tenant where appropriate:

```sql
DELETE FROM orders
WHERE id = %s
  AND tenant_id = %s;
```

Do not rely exclusively on the application having previously loaded an authorized row.

The final mutation should enforce the authorization boundary whenever practical.

### Minimize Database Privileges

A service account that only needs to update selected tables should not automatically receive unrestricted schema modification privileges.

Use least privilege for:

- API services.
- Background workers.
- Migration processes.
- Administrative jobs.

## CTE Writes and ORMs

Most ORMs support basic `INSERT`, `UPDATE`, and `DELETE` operations but may not expose advanced data-modifying CTE features directly.

For example, Django's ORM can express many operations:

```python
Order.objects.filter(
    status="cancelled",
    created_at__lt=cutoff,
).delete()
```

But complex PostgreSQL-specific workflows involving:

```sql
DELETE ... RETURNING
```

feeding:

```sql
INSERT
```

through a data-modifying CTE may require carefully managed raw SQL or a specialized query-building library.

When using raw SQL:

- Keep SQL close to the domain operation.
- Parameterize values.
- Add integration tests.
- Document database-specific assumptions.
- Monitor execution plans.
- Avoid hiding complex SQL behind generic helper functions.

## Common Mistakes

### Assuming CTEs Are Universally Writable

CTE capabilities differ between databases.

A query that works in PostgreSQL may not work unchanged in MySQL, SQL Server, SQLite, or another engine.

Check the target database documentation before using data-modifying CTEs.

### Treating a CTE Like a Temporary Table

A CTE is a query construct, not automatically a durable temporary table.

Do not assume:

```text
CTE = physical table
```

or that every CTE creates an independently stored intermediate dataset.

### Assuming CTEs Guarantee Sequential Execution

Do not assume sibling data-modifying CTEs behave like procedural statements.

For PostgreSQL, communicate rows between modifying stages through `RETURNING` when that relationship matters.

### Archiving and Deleting in Separate Statements

This pattern creates a failure window:

```text
INSERT archive
    ↓
application failure
    ↓
DELETE never happens
```

or:

```text
DELETE
    ↓
archive operation fails
    ↓
data lost
```

When the operation truly needs atomic archive-and-delete semantics, a data-modifying CTE can be appropriate.

### Running Huge Mutations in One Transaction

A logically elegant query can still be operationally dangerous.

Large mutations can cause:

- Lock contention.
- Replication lag.
- WAL spikes.
- Long transaction lifetimes.
- Vacuum pressure.
- Difficult rollback.

Use batching or partition-level operations when appropriate.

### Forgetting `RETURNING`

When a mutation's affected rows are needed by another stage, querying the table again is often unnecessary.

Prefer:

```sql
DELETE ...
RETURNING ...
```

when the database supports it and the workflow benefits from the returned relation.

### Ignoring Foreign Keys

A CTE can identify the correct rows but still fail because another table references them.

Always understand referential actions before production deletes.

### Testing Only with Small Data

A mutation that takes 50 ms on 10,000 rows may become an operational incident at 500 million rows.

Test realistic cardinalities and concurrency.

### Using Raw SQL Without Integration Tests

Complex CTE-based writes are easy to get subtly wrong.

Test:

- Rows affected.
- Duplicate behavior.
- Transaction rollback.
- Concurrent execution.
- Foreign-key behavior.
- `NULL` handling.
- Retry behavior.
- Idempotency where applicable.

## Interview Traps

### Can a CTE Perform `INSERT`, `UPDATE`, or `DELETE`?

It depends on the database.

PostgreSQL supports data-modifying statements in `WITH`. Other databases have different capabilities.

### What Is the Main Benefit of a Data-Modifying CTE?

It can compose relational reads and writes into a single database statement, reducing round trips and enabling atomic database-side workflows.

### Why Is `RETURNING` Important?

It exposes affected rows from a data-modifying statement so another stage can consume those rows without querying the mutated table again.

### Is a CTE Automatically Faster?

No.

CTEs primarily provide query composition and structure. Performance depends on the database optimizer, query shape, cardinality, indexes, locks, and transaction behavior.

### Are Data-Modifying CTEs Equivalent to Stored Procedures?

No.

A CTE is part of a SQL statement. A stored procedure is a persistent database-side program with its own procedural semantics.

### Should Every Multi-Step Write Use a CTE?

No.

Use a CTE when the operations have a strong relational relationship and benefit from being executed as one database operation.

Use application-level orchestration when the workflow involves external services, long-running work, asynchronous retries, or multiple independent transactions.

## CTE Write Pattern Selection

| Requirement | Suitable pattern |
|---|---|
| Insert from filtered data | `INSERT ... SELECT` |
| Insert from complex intermediate result | CTE + `INSERT ... SELECT` |
| Update based on another relation | CTE + `UPDATE ... FROM` |
| Delete based on another relation | CTE + `DELETE ... USING` |
| Calculate values before update | CTE + window/aggregation + `UPDATE` |
| Archive deleted rows | Data-modifying CTE + `RETURNING` + `INSERT` |
| Atomic database-side transformation | Data-modifying CTE |
| Very large cleanup | Batched mutations or partitioning |
| External workflow | Application/worker orchestration |
| High-throughput asynchronous processing | Queue/stream infrastructure |

## Production Checklist

Before deploying a CTE-based write:

- [ ] Confirm the target database supports the required CTE semantics.
- [ ] Understand the grain and exact rows being modified.
- [ ] Verify foreign-key and cascading behavior.
- [ ] Use parameterized SQL.
- [ ] Enforce tenant and authorization boundaries.
- [ ] Confirm transaction boundaries.
- [ ] Check whether the operation needs atomicity.
- [ ] Use `RETURNING` where affected rows need to feed another stage.
- [ ] Add deterministic ordering for batched operations where required.
- [ ] Check indexes supporting filters and joins.
- [ ] Test with production-scale cardinalities.
- [ ] Measure lock duration and transaction size.
- [ ] Monitor WAL and replication impact.
- [ ] Consider batching for large mutations.
- [ ] Test rollback behavior.
- [ ] Test concurrent execution.
- [ ] Verify retry and idempotency behavior.
- [ ] Add integration tests around the complete SQL statement.
- [ ] Document database-specific behavior when raw SQL is used.

## Key Takeaways

- **CTEs can structure `INSERT`, `UPDATE`, and `DELETE` workflows, but writable-CTE capabilities are database-specific.**
- **PostgreSQL data-modifying CTEs combined with `RETURNING` are especially useful for atomic database-side workflows such as archive-and-delete operations.**
- **Do not treat CTEs as temporary tables or assume that sibling write CTEs execute like sequential procedural statements; use explicit data flow through `RETURNING` when stages depend on one another.**
- **Large CTE-based mutations can create substantial lock, WAL, replication, and transaction pressure, so batch high-volume operations when appropriate.**
- **Use CTE-based writes when they simplify a tightly coupled relational operation; use application-level orchestration for long-running, asynchronous, or cross-service workflows.**