# 02- INSERT Multiple Rows

## Overview

Multi-row `INSERT` allows multiple records to be written using a single SQL statement. It is primarily useful for reducing database round trips and improving write throughput when several rows belong to the same logical operation.

The basic pattern is:

```sql
INSERT INTO table_name (column_a, column_b, column_c)
VALUES
    (value_a1, value_b1, value_c1),
    (value_a2, value_b2, value_c2),
    (value_a3, value_b3, value_c3);
```

For backend systems, multi-row inserts sit between individual application-level writes and database-native bulk-loading mechanisms. The correct choice depends on the volume of data, transaction requirements, error semantics, indexing, and database engine.

This document uses PostgreSQL syntax where database-specific behavior matters.

## Why Use Multi-Row INSERT

An application that inserts 1,000 records individually may perform 1,000 client/server interactions:

```text
Application
    |
    +--> INSERT row 1 --> Database
    +--> INSERT row 2 --> Database
    +--> INSERT row 3 --> Database
    ...
    +--> INSERT row 1000 --> Database
```

A multi-row statement can reduce this to one request:

```text
Application
    |
    +--> INSERT 1000 rows --> Database
```

This can reduce:

- Network round trips.
- SQL parsing overhead.
- Driver overhead.
- Transaction management overhead.
- Per-statement protocol overhead.

The improvement is especially relevant for services running across a network from the database, such as applications deployed on Kubernetes, ECS, or EC2 while PostgreSQL runs on a managed database service.

## Basic Syntax

```sql
INSERT INTO products (
    sku,
    name,
    price
)
VALUES
    ('KB-001', 'Mechanical Keyboard', 129.99),
    ('MS-001', 'Wireless Mouse', 49.99),
    ('HS-001', 'USB Headset', 79.99);
```

Every row must provide values compatible with the same target column list.

```sql
INSERT INTO products (sku, name, price)
VALUES
    ('KB-001', 'Mechanical Keyboard', 129.99),
    ('MS-001', 'Wireless Mouse', 49.99),
    ('HS-001', 'USB Headset', 79.99);
```

The column list applies to every row.

## Explicit Column Lists

Always specify the target columns.

```sql
INSERT INTO orders (
    customer_id,
    status,
    total_amount
)
VALUES
    (101, 'pending', 150.00),
    (102, 'pending', 275.50),
    (103, 'pending', 89.99);
```

Avoid positional inserts:

```sql
-- Fragile and difficult to maintain.
INSERT INTO orders
VALUES
    (101, 'pending', 150.00),
    (102, 'pending', 275.50);
```

Explicit columns protect the SQL from assumptions about physical column order and make schema evolution safer.

## Multi-Row INSERT vs Individual INSERT

| Characteristic | Individual `INSERT` | Multi-row `INSERT` |
|---|---|---|
| Network round trips | High | Low |
| SQL statements | Many | One |
| Parsing/protocol overhead | Higher | Lower |
| Error boundary | Per statement | Entire statement |
| Transaction control | Fine-grained | Coarser |
| Suitable for small batches | Yes | Yes |
| Suitable for moderate batches | Sometimes | Usually |
| Suitable for very large ingestion | Usually inefficient | Can become inefficient |
| Maximum practical size | Small per request | Depends on workload/database |

Multi-row insertion is not automatically the best solution for every bulk workload.

For very large datasets, PostgreSQL's `COPY` protocol is often more appropriate.

## Multi-Row INSERT and Transactions

A multi-row `INSERT` is one SQL statement. If the statement fails, the statement's changes do not partially commit as successful independent statements.

For example:

```sql
INSERT INTO users (email, status)
VALUES
    ('alice@example.com', 'active'),
    ('bob@example.com', 'active'),
    ('alice@example.com', 'active');
```

If `email` has a `UNIQUE` constraint, the duplicate can cause the statement to fail.

This differs from executing three separate statements inside a transaction:

```sql
BEGIN;

INSERT INTO users (email, status)
VALUES ('alice@example.com', 'active');

INSERT INTO users (email, status)
VALUES ('bob@example.com', 'active');

INSERT INTO users (email, status)
VALUES ('alice@example.com', 'active');

COMMIT;
```

The transaction-level behavior is different from statement-level behavior because individual statements may succeed before a later statement fails. Unless the transaction is rolled back, those earlier changes can remain part of the transaction's eventual commit.

The key distinction is:

> **Statement atomicity and transaction atomicity are related but not the same thing.**

## Multi-Row INSERT Inside an Explicit Transaction

For multiple related operations:

```sql
BEGIN;

INSERT INTO orders (
    customer_id,
    status,
    total_amount
)
VALUES
    (101, 'pending', 150.00),
    (102, 'pending', 275.50);

INSERT INTO order_events (
    order_id,
    event_type
)
SELECT
    id,
    'created'
FROM orders
WHERE customer_id IN (101, 102);

COMMIT;
```

The transaction boundary should represent the required business consistency boundary, not simply the desired batch size.

Avoid unnecessarily large transactions when processing high-volume workloads.

## Generated IDs with RETURNING

PostgreSQL can return generated values from all inserted rows.

```sql
INSERT INTO users (
    email,
    display_name
)
VALUES
    ('alice@example.com', 'Alice'),
    ('bob@example.com', 'Bob'),
    ('charlie@example.com', 'Charlie')
RETURNING id, email;
```

A result might look like:

| id | email |
|---:|---|
| 1001 | alice@example.com |
| 1002 | bob@example.com |
| 1003 | charlie@example.com |

This is useful when the application needs generated primary keys for subsequent operations.

It avoids issuing a separate query for each inserted row.

## INSERT ... SELECT for Multiple Rows

Multi-row insertion does not require literal `VALUES`.

`INSERT ... SELECT` can create multiple target rows from an existing query:

```sql
INSERT INTO user_audit (
    user_id,
    event_type,
    created_at
)
SELECT
    id,
    'migration.imported',
    CURRENT_TIMESTAMP
FROM users
WHERE status = 'active';
```

This is often preferable to retrieving rows into application memory and then sending them back to the database.

The data path becomes:

```mermaid
flowchart LR
    A[Existing Rows] --> B[SELECT]
    B --> C[Transformation]
    C --> D[INSERT]
    D --> E[Target Table]
```

The database can perform filtering and transformation close to the data, avoiding unnecessary application-side data movement.

## Parameterized Multi-Row INSERT

Application code should never construct SQL using untrusted string interpolation.

A database driver may support parameterized multi-row statements directly.

For example, using PostgreSQL-style placeholders:

```python
rows = [
    ("KB-001", "Mechanical Keyboard", 129.99),
    ("MS-001", "Wireless Mouse", 49.99),
    ("HS-001", "USB Headset", 79.99),
]

values_sql = ", ".join(["(%s, %s, %s)"] * len(rows))

query = f"""
    INSERT INTO products (sku, name, price)
    VALUES {values_sql}
"""

parameters = [value for row in rows for value in row]

cursor.execute(query, parameters)
```

The SQL structure is generated by the application, while actual values remain parameterized.

For production applications, prefer the parameterization and bulk-insert facilities provided by the database driver or ORM when available rather than implementing SQL generation manually.

## Django Example

Django provides `bulk_create()` for inserting multiple model instances efficiently.

```python
Product.objects.bulk_create(
    [
        Product(sku="KB-001", name="Mechanical Keyboard", price=129.99),
        Product(sku="MS-001", name="Wireless Mouse", price=49.99),
        Product(sku="HS-001", name="USB Headset", price=79.99),
    ],
    batch_size=500,
)
```

`batch_size` can prevent an excessively large SQL statement and transaction.

Be aware that bulk operations have different semantics from saving objects individually. Depending on Django version, database backend, and options used, model-level hooks/signals and per-object behavior may differ.

Do not assume:

```python
bulk_create(...)
```

is semantically identical to:

```python
for product in products:
    product.save()
```

Choose based on both performance and required application behavior.

## FastAPI and SQLAlchemy Considerations

With SQLAlchemy, bulk insertion can be performed through Core or ORM APIs.

A Core-style example:

```python
from sqlalchemy import insert

stmt = insert(products_table)

connection.execute(
    stmt,
    [
        {"sku": "KB-001", "name": "Mechanical Keyboard", "price": 129.99},
        {"sku": "MS-001", "name": "Wireless Mouse", "price": 49.99},
        {"sku": "HS-001", "name": "USB Headset", "price": 79.99},
    ],
)
```

The exact behavior depends on the SQLAlchemy version, driver, dialect, and execution configuration.

For high-volume workloads, measure the actual generated SQL and database behavior instead of assuming that an ORM bulk API always maps to the most efficient database-native mechanism.

## Handling Defaults

Columns with defaults can be omitted from the column list.

```sql
CREATE TABLE jobs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Multiple rows can then be inserted with only business input:

```sql
INSERT INTO jobs (name)
VALUES
    ('generate-report'),
    ('send-email'),
    ('rebuild-index');
```

Each row receives the appropriate database defaults.

You can also explicitly use `DEFAULT`:

```sql
INSERT INTO jobs (name, status)
VALUES
    ('generate-report', DEFAULT),
    ('send-email', DEFAULT),
    ('rebuild-index', DEFAULT);
```

Do not confuse `DEFAULT` with `NULL`.

```sql
-- Uses the default
INSERT INTO jobs (name)
VALUES ('generate-report');

-- Attempts to store NULL
INSERT INTO jobs (name, status)
VALUES ('generate-report', NULL);
```

The second statement fails if `status` is `NOT NULL`.

## Constraints and Multi-Row INSERT

All inserted rows must satisfy the target table's constraints.

Consider:

```sql
CREATE TABLE user_roles (
    user_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (user_id, role)
);
```

This statement contains a duplicate:

```sql
INSERT INTO user_roles (user_id, role)
VALUES
    (1, 'admin'),
    (1, 'editor'),
    (1, 'admin');
```

The primary-key constraint is violated.

When duplicate data is expected as part of normal processing, PostgreSQL provides conflict handling:

```sql
INSERT INTO user_roles (user_id, role)
VALUES
    (1, 'admin'),
    (1, 'editor'),
    (1, 'admin')
ON CONFLICT (user_id, role)
DO NOTHING;
```

The correct conflict strategy depends on the business semantics. Do not use `DO NOTHING` simply to suppress errors if duplicate data indicates a real application defect.

## Multi-Row Upserts

PostgreSQL supports multiple-row upserts:

```sql
INSERT INTO inventory (sku, quantity)
VALUES
    ('KB-001', 10),
    ('MS-001', 20),
    ('HS-001', 15)
ON CONFLICT (sku)
DO UPDATE
SET quantity = inventory.quantity + EXCLUDED.quantity
RETURNING sku, quantity;
```

This can efficiently process batches while allowing existing rows to be updated.

The operation remains subject to:

- Unique constraints.
- Row-level concurrency.
- Index maintenance.
- Trigger execution.
- Transaction isolation.
- Lock contention.

Upserts should therefore be designed around the business invariant, not merely around convenient syntax.

## Batch Size

There is no universally optimal batch size.

A batch that is too small may cause:

- Excessive network overhead.
- More transaction commits.
- Lower throughput.

A batch that is too large may cause:

- Large SQL payloads.
- Higher memory usage.
- Longer transactions.
- More WAL generation.
- Longer lock durations.
- Increased replication lag.
- More expensive rollback/recovery.
- Greater impact when the batch fails.

A typical production pattern is:

```text
Incoming records
      |
      v
Batch records
      |
      +---- Batch 1 ----> INSERT ----> Commit
      |
      +---- Batch 2 ----> INSERT ----> Commit
      |
      +---- Batch 3 ----> INSERT ----> Commit
```

Choose batch size using load testing and production telemetry.

## Error Semantics

A major design question is whether a batch should behave atomically.

### All-or-Nothing

```sql
INSERT INTO payments (
    payment_id,
    amount
)
VALUES
    ('p-001', 100.00),
    ('p-002', 200.00),
    ('p-003', 300.00);
```

If one row violates a constraint, the statement fails rather than silently inserting only the valid rows.

This is useful when the rows form one logical operation.

### Partial Success

If individual rows have independent business outcomes, process them as separate units or use an ingestion architecture that explicitly supports partial failure.

Do not accidentally turn an all-or-nothing business operation into a partially applied workflow merely for throughput.

## Performance Considerations

Multi-row insertion improves throughput primarily by reducing overhead, but database write performance remains dependent on the physical work required for every row.

Each inserted row can require:

```text
Row
 |
 +--> Table storage
 |
 +--> Primary key index
 |
 +--> Unique indexes
 |
 +--> Secondary indexes
 |
 +--> Foreign-key checks
 |
 +--> Triggers
 |
 +--> WAL
```

An insert-heavy table with many indexes can experience substantial write amplification.

For high-write systems:

- Keep only necessary indexes.
- Measure transaction latency.
- Monitor lock waits.
- Monitor WAL generation.
- Monitor replication lag.
- Avoid unnecessarily large transactions.
- Consider partitioning when it addresses a real workload characteristic.
- Use database-native bulk-loading tools for very large ingestion workloads.

## Multi-Row INSERT vs COPY

For PostgreSQL, `COPY` is designed for efficient bulk data movement.

| Approach | Best suited for |
|---|---|
| Single `INSERT` | One business operation |
| Multi-row `INSERT` | Small to moderate batches |
| `INSERT ... SELECT` | Database-side data movement |
| `COPY` | Large-scale data ingestion |
| Queue + batch writer | Asynchronous high-volume ingestion |

`COPY` is generally not a replacement for normal transactional application writes. It is primarily a high-throughput data-loading mechanism.

For example, an operational data-import pipeline might look like:

```mermaid
flowchart LR
    A[CSV or Data Stream] --> B[Validation / Staging]
    B --> C[COPY]
    C --> D[PostgreSQL Staging Table]
    D --> E[SQL Transformation]
    E --> F[Production Tables]
```

Staging can be useful when imported data requires validation, deduplication, transformation, or reconciliation before becoming authoritative application data.

## Concurrency and Uniqueness

Do not implement uniqueness using:

```text
SELECT whether record exists
        |
        v
Application decides record is absent
        |
        v
INSERT
```

Concurrent requests can both observe the record as absent.

Instead, enforce the invariant in the database:

```sql
CREATE UNIQUE INDEX users_email_unique
ON users (email);
```

Then use conflict handling when appropriate:

```sql
INSERT INTO users (email, display_name)
VALUES
    ('alice@example.com', 'Alice'),
    ('bob@example.com', 'Bob')
ON CONFLICT (email)
DO NOTHING;
```

The database becomes the concurrency authority for the uniqueness rule.

## Monitoring

For high-volume multi-row inserts, monitor:

- Insert throughput.
- Statement latency.
- Rows inserted per batch.
- Transaction duration.
- Constraint violation rate.
- Deadlocks.
- Lock waits.
- Database CPU.
- Database I/O.
- WAL generation.
- Replication lag.
- Connection pool utilization.

A useful application metric is:

```text
rows_inserted / statement_execution_time
```

but throughput alone is insufficient. Also monitor failure rates and downstream effects such as replica lag.

Avoid logging every inserted value. Production logs should not become a second data store or expose sensitive information.

## Reliability and Recovery

Large insert batches can increase the amount of work that must be replayed or rolled back after failures.

Consider:

- Transaction size.
- WAL volume.
- Replication behavior.
- Database failover.
- Retry semantics.
- Idempotency.
- Duplicate handling.

Retries are particularly important.

Suppose an application sends a batch and the database connection breaks immediately after the server processes the transaction but before the client receives the response:

```text
Application
    |
    | INSERT batch
    v
Database
    |
    | Commit
    X
Network failure
    |
    v
Application sees timeout
```

The application cannot automatically assume that the operation failed.

Blindly retrying can create duplicates unless the operation is idempotent or protected by a unique constraint/upsert strategy.

## Security Considerations

Multi-row insertion does not change the fundamental SQL security requirements.

Use:

- Parameterized queries.
- Least-privilege database users.
- Database constraints.
- Input validation.
- Safe error handling.
- Appropriate audit logging.

Never construct values directly into SQL:

```python
# Unsafe
query = f"""
INSERT INTO users (email, name)
VALUES ('{email}', '{name}')
"""
```

Use parameter binding instead.

Also avoid granting broad write permissions to application roles that only require access to specific tables or operations.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Inserting rows individually in a loop | Excessive round trips | Batch inserts |
| One enormous batch | Large transactions and failure impact | Tune batch size |
| Omitting column lists | Schema-order coupling | Specify columns |
| String interpolation | SQL injection | Parameterize values |
| Ignoring constraints | Invalid data reaches the database | Enforce invariants |
| Using `DO NOTHING` everywhere | Can hide real data problems | Define explicit conflict semantics |
| Assuming ORM bulk APIs equal normal saves | Hooks/signals/semantics may differ | Understand ORM behavior |
| Retrying blindly after timeout | May duplicate successful writes | Design idempotent writes |
| Too many indexes | High write amplification | Index according to workload |
| Loading huge datasets through application memory | Memory pressure and unnecessary data movement | Use database-native bulk loading |
| One transaction for an entire import | Long locks and difficult recovery | Stage and batch where possible |

## Interview Traps

### Is multi-row INSERT always faster than individual INSERT statements?

Usually it reduces overhead, but performance depends on the driver, database, transaction boundaries, indexes, network latency, and batch size. Very large statements can become counterproductive.

### Does multi-row INSERT partially succeed when one row fails?

A normal SQL statement does not behave as a collection of independently committed inserts. If the statement fails, its statement-level effects are rolled back.

### Should you use `ON CONFLICT DO NOTHING` for every duplicate?

No. Suppressing conflicts can hide data-quality problems. Use it only when ignoring an existing row is valid business behavior.

### When should you use `COPY` instead?

For PostgreSQL workloads involving large-scale data ingestion, `COPY` is generally more appropriate than constructing extremely large `INSERT ... VALUES` statements.

### Is a bulk ORM operation always equivalent to calling `save()` repeatedly?

No. Bulk APIs are optimized for database writes and may bypass per-object behavior such as model hooks or signals, depending on the framework and operation.

### Why can a multi-row insert still be slow?

The database still has to maintain table storage, indexes, constraints, triggers, WAL, and potentially foreign-key relationships for every row.

## Production Checklist

- [ ] Explicit target columns are specified.
- [ ] Values are parameterized.
- [ ] Batch size has been benchmarked.
- [ ] Transaction boundaries match business requirements.
- [ ] Unique and foreign-key constraints are defined.
- [ ] Conflict behavior is explicit.
- [ ] Retry behavior is idempotent.
- [ ] Generated identifiers can be retrieved efficiently.
- [ ] Index write amplification has been considered.
- [ ] Large imports use appropriate bulk-loading mechanisms.
- [ ] Long-running transactions are monitored.
- [ ] Lock waits and deadlocks are observable.
- [ ] Replication lag is monitored for write-heavy workloads.
- [ ] ORM bulk-operation semantics are understood.
- [ ] Sensitive inserted values are not unnecessarily logged.

## Key Takeaways

- **Use multi-row `INSERT` to reduce round trips and statement overhead for small-to-moderate batches.**
- **Choose batch sizes deliberately; oversized batches can increase transaction duration, WAL pressure, lock contention, and recovery cost.**
- **Use database constraints and explicit `ON CONFLICT` behavior to make concurrent batch writes correct and predictable.**
- **Use `RETURNING` for generated values and `INSERT ... SELECT` when data can be transformed inside the database.**
- **For very large PostgreSQL ingestion workloads, prefer database-native bulk loading such as `COPY` over enormous `INSERT` statements.**