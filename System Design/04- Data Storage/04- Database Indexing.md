# 04- Database Indexing

## Overview

A database index is an auxiliary data structure that allows a database engine to locate rows without scanning the entire table.

Without an appropriate index, a query such as:

```sql
SELECT *
FROM users
WHERE email = 'alice@example.com';
```

may require a sequential scan:

```text
Users table
├── row 1   -> compare
├── row 2   -> compare
├── row 3   -> compare
├── ...
└── row N   -> compare
```

For a table containing millions of rows, this can become expensive.

With an index:

```text
                 Query
                   |
                   v
             Index lookup
                   |
                   v
             Row location
                   |
                   v
             Table access
```

The database can navigate the index to identify candidate rows and then retrieve only the required data.

Indexing is one of the most important database performance concepts in backend system design because database performance is frequently dominated by:

- How many rows are examined
- How much data is read from storage
- Whether sorting can be avoided
- Whether joins can efficiently locate matching rows
- Whether the query can be served directly from the index
- Whether the working set fits in memory
- Whether indexes introduce excessive write overhead

Indexes are not automatically beneficial. Every index consumes storage, increases write cost, can increase vacuum/maintenance work, and may be completely ignored by the query planner.

The goal is therefore not:

> "Create indexes on every frequently used column."

The goal is:

> **Create indexes that support the actual access patterns of the application while keeping write, storage, and maintenance costs under control.**

---

## Why Indexes Exist

A database table is optimized primarily for storing rows. An index provides an additional representation optimized for locating those rows according to a particular key or expression.

Consider:

```text
Table:

id    email                 status
1     alice@example.com     active
2     bob@example.com       active
3     carol@example.com     inactive
4     dave@example.com      active
```

An index on `email` conceptually provides:

```text
Index

alice@example.com  -> row 1
bob@example.com    -> row 2
carol@example.com  -> row 3
dave@example.com   -> row 4
```

The database can search the index rather than comparing the predicate against every table row.

Indexes are particularly valuable when:

- Tables are large.
- Queries return a small percentage of rows.
- Columns are used in selective predicates.
- Columns participate in joins.
- Queries frequently sort or group by particular keys.
- Uniqueness must be enforced.
- Range queries are common.
- Queries repeatedly access the same access path.

---

## How an Index Works

Most general-purpose relational databases use some form of **B-tree** as the default index structure.

A simplified representation is:

```text
                    Root
                  /      \
                 /        \
             Node A       Node B
            /    \        /    \
           /      \      /      \
         Leaf     Leaf  Leaf    Leaf
```

The tree remains balanced, allowing the database to navigate through a relatively small number of nodes.

For a lookup:

```sql
SELECT *
FROM users
WHERE id = 500000;
```

the database can navigate:

```text
Root
  |
  v
Intermediate node
  |
  v
Leaf node
  |
  v
Row location
```

This is substantially more efficient than examining every row when the table is large and the predicate is selective.

The exact implementation depends on the database engine and index type, but the high-level principle is consistent: indexes organize information so the engine can avoid unnecessary data access.

---

## Index Lookup vs Sequential Scan

Suppose a table contains 10 million rows.

### Sequential Scan

```text
10,000,000 rows
       |
       v
Evaluate predicate for each row
       |
       v
Return matching rows
```

This can be appropriate when a large percentage of the table matches.

### Index Scan

```text
Index
  |
  v
Locate matching key
  |
  v
Find row locations
  |
  v
Fetch matching rows
```

This is usually attractive when relatively few rows match.

The query planner decides which strategy is cheaper.

This is an important senior-level point:

> **Having an index does not mean the database must use it.**

---

## Selectivity

Index usefulness depends heavily on **selectivity**.

Selectivity describes how effectively a predicate narrows the candidate rows.

Suppose:

```text
users = 10,000,000 rows
```

A query:

```sql
WHERE id = 12345
```

may identify one row.

That is highly selective.

A query:

```sql
WHERE is_active = true
```

might identify:

```text
9,500,000 rows
```

if most users are active.

That predicate has poor selectivity.

An index on `is_active` may therefore provide little benefit for that query.

### High-Selectivity Examples

```text
email
user_id
order_id
UUID
phone_number
```

### Potentially Low-Selectivity Examples

```text
gender
boolean flags
status with only a few values
country_code in a highly concentrated dataset
```

Low cardinality does not automatically mean an index is useless. Composite indexes, partial indexes, data distribution, and query shape can change the decision.

---

## Cardinality

Cardinality refers to the number of distinct values in a column.

For example:

```text
user_id:
10,000,000 distinct values
```

has high cardinality.

Whereas:

```text
status:
active
inactive
```

has very low cardinality.

A rough intuition is:

```text
High cardinality
        |
        v
Usually more selective
        |
        v
Often useful for equality lookups
```

But cardinality alone is insufficient.

A senior engineer considers:

- Data distribution
- Query predicates
- Table size
- Expected result size
- Query frequency
- Composite indexes
- Correlation between columns
- Whether the optimizer can use the index efficiently

---

## Primary Key Indexes

Primary keys are commonly backed by indexes.

For example:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);
```

The database uses the primary key to enforce uniqueness and efficiently locate rows.

A primary key therefore serves two distinct purposes:

1. **Data integrity**
2. **Efficient lookup**

A primary key index should generally not be duplicated with another ordinary index containing exactly the same leading key unless there is a specific reason.

---

## Unique Indexes

A unique index enforces uniqueness while providing an access path.

```sql
CREATE UNIQUE INDEX users_email_unique_idx
ON users (email);
```

This supports:

```sql
SELECT *
FROM users
WHERE email = 'alice@example.com';
```

while also preventing duplicate emails.

For an application-level uniqueness requirement, database-enforced uniqueness is generally safer than relying only on application validation.

Bad:

```python
if not User.objects.filter(email=email).exists():
    User.objects.create(email=email)
```

Two concurrent requests can both pass the check.

Better:

```text
Application validation
        +
Database UNIQUE constraint
```

The application can provide a friendly error while the database provides the actual integrity guarantee.

---

## B-tree Index

B-tree indexes are the general-purpose choice for many relational workloads.

They are useful for:

- Equality
- Range queries
- Sorting
- Prefix-compatible operations
- Ordering
- Many join conditions

Examples:

```sql
CREATE INDEX orders_created_at_idx
ON orders (created_at);
```

Useful query:

```sql
SELECT *
FROM orders
WHERE created_at >= TIMESTAMP '2026-01-01 00:00:00'
  AND created_at < TIMESTAMP '2026-02-01 00:00:00';
```

The tree structure allows the database to locate the starting range and scan the relevant portion.

---

## Hash Indexes

Hash indexes organize values using hash functions.

Conceptually:

```text
hash(key) -> bucket -> matching entries
```

They are primarily useful for equality-style lookups.

```sql
WHERE user_id = 123
```

They are not a general replacement for B-tree indexes because they do not naturally support ordered operations such as:

```sql
WHERE amount > 1000
ORDER BY created_at
```

For most conventional PostgreSQL workloads, B-tree should be the default unless a specific workload justifies another index type.

---

## Composite Indexes

A composite index contains multiple columns.

```sql
CREATE INDEX orders_customer_status_idx
ON orders (customer_id, status);
```

This can support queries such as:

```sql
SELECT *
FROM orders
WHERE customer_id = 100
  AND status = 'pending';
```

The order of columns matters.

Conceptually:

```text
(customer_id, status)

100, cancelled
100, pending
100, shipped
101, cancelled
101, pending
102, shipped
```

The index is ordered first by `customer_id`, then by `status`.

---

## Leftmost Prefix Principle

For a composite B-tree index:

```sql
CREATE INDEX idx
ON orders (customer_id, status, created_at);
```

the leading column matters.

The index is naturally useful for access patterns beginning with:

```text
customer_id
```

or:

```text
customer_id + status
```

or:

```text
customer_id + status + created_at
```

But a query using only:

```sql
WHERE status = 'pending'
```

cannot generally exploit this index as efficiently as an index beginning with `status`.

A useful mental model is:

```text
(customer_id, status, created_at)
     ^
     |
Leading key
```

The database cannot arbitrarily treat the composite index as three independent indexes.

---

## Column Order in Composite Indexes

Choosing column order requires understanding the query workload.

Suppose the application frequently runs:

```sql
SELECT *
FROM orders
WHERE customer_id = ?
  AND status = ?
ORDER BY created_at DESC;
```

A possible index is:

```sql
CREATE INDEX orders_customer_status_created_idx
ON orders (customer_id, status, created_at DESC);
```

This can align the index with:

```text
Filtering
   |
customer_id
   |
status
   |
Ordering
   |
created_at
```

However, blindly applying "highest cardinality first" is not a universal rule.

The correct order depends on:

- Query predicates
- Equality vs range predicates
- Sort requirements
- Join conditions
- Data distribution
- Query frequency
- PostgreSQL optimizer behavior
- Whether the index can eliminate sorting

The workload should determine the index design.

---

## Equality, Range, and Sort Predicates

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = 123
  AND status = 'paid'
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY created_at DESC;
```

A common composite-index strategy is:

```text
Equality predicates
        |
        v
Range predicate
        |
        v
Ordering requirement
```

For example:

```sql
CREATE INDEX orders_customer_status_created_idx
ON orders (customer_id, status, created_at DESC);
```

The exact optimal index should be verified with `EXPLAIN ANALYZE`.

---

## Covering Indexes

A covering index contains enough information for the database to answer a query without fetching the full table row.

Suppose:

```sql
SELECT id, email
FROM users
WHERE email = 'alice@example.com';
```

An index containing the required columns may allow the engine to satisfy the query directly from the index.

In PostgreSQL, `INCLUDE` can add non-key columns:

```sql
CREATE INDEX users_email_covering_idx
ON users (email)
INCLUDE (id);
```

The distinction is important:

```text
Index key columns
    |
    +---- Used for index ordering/searching

Included columns
    |
    +---- Stored to help cover queries
```

Covering indexes can reduce heap/table access but increase index size.

---

## Partial Indexes

A partial index contains only rows satisfying a predicate.

For example, suppose only pending jobs need frequent lookup:

```sql
CREATE INDEX jobs_pending_idx
ON jobs (created_at)
WHERE status = 'pending';
```

The index contains only pending rows.

This can be significantly smaller than:

```sql
CREATE INDEX jobs_status_created_idx
ON jobs (status, created_at);
```

Partial indexes are useful when:

- Only a subset of rows is frequently queried.
- The predicate is stable and well-defined.
- The application has a highly skewed workload.

Examples:

```text
active records
pending jobs
unprocessed events
soft-deleted = false
tenant-specific states
```

---

## Expression Indexes

An expression index indexes the result of an expression rather than the raw column.

For example:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

This can support:

```sql
SELECT *
FROM users
WHERE LOWER(email) = LOWER('Alice@example.com');
```

Without an appropriate expression index, applying a function to the column may prevent the normal index from being used effectively.

Common examples include:

```sql
LOWER(email)
DATE(timestamp_column)
JSON expressions
computed values
```

Expression indexes should be created only when the expression matches real query patterns.

---

## Indexes and Functions

Consider:

```sql
SELECT *
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

A normal index:

```sql
CREATE INDEX users_email_idx
ON users (email);
```

may not provide the desired access path because the predicate operates on:

```text
LOWER(email)
```

rather than:

```text
email
```

An expression index can align the index with the query:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

The broader principle is:

> **The index must match the access expression the optimizer can use.**

---

## Indexes for Sorting

Indexes can sometimes eliminate explicit sorting.

Consider:

```sql
SELECT id, created_at
FROM orders
WHERE customer_id = 100
ORDER BY created_at DESC
LIMIT 50;
```

An index such as:

```sql
CREATE INDEX orders_customer_created_idx
ON orders (customer_id, created_at DESC);
```

can allow the database to traverse matching rows in the required order.

Without the appropriate index:

```text
Filter rows
     |
     v
Sort rows
     |
     v
Return first 50
```

With a suitable index:

```text
Index traversal
      |
      v
Already ordered
      |
      v
Return first 50
```

This can be especially valuable for pagination queries.

---

## Indexes and Pagination

Offset pagination:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 50 OFFSET 100000;
```

can become increasingly expensive because the database may need to walk past many rows.

Keyset pagination is often more scalable:

```sql
SELECT *
FROM orders
WHERE created_at < :last_seen_created_at
ORDER BY created_at DESC
LIMIT 50;
```

A supporting index:

```sql
CREATE INDEX orders_created_at_id_idx
ON orders (created_at DESC, id DESC);
```

can make the query efficient even at deep pagination positions.

For deterministic ordering, include a unique tie-breaker:

```sql
ORDER BY created_at DESC, id DESC
```

rather than relying on timestamps alone.

---

## Indexes and JOINs

Indexes are important for many join patterns.

Consider:

```sql
SELECT o.id, u.email
FROM orders o
JOIN users u
    ON u.id = o.user_id
WHERE o.status = 'pending';
```

Useful indexes may include:

```sql
CREATE INDEX orders_status_user_id_idx
ON orders (status, user_id);
```

while `users.id` is normally already indexed through the primary key.

For joins, think about both sides:

```text
Table A
   |
join key
   |
Table B
```

The optimizer can choose different join algorithms depending on:

- Index availability
- Table sizes
- Statistics
- Predicate selectivity
- Memory
- Estimated result size

An index does not automatically guarantee a nested-loop join or any particular join strategy.

---

## Indexes and Foreign Keys

Foreign keys enforce referential integrity, but a foreign-key column is not universally guaranteed to have a useful index automatically.

For example:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id)
);
```

If the application frequently queries:

```sql
SELECT *
FROM orders
WHERE customer_id = 123;
```

an index is appropriate:

```sql
CREATE INDEX orders_customer_id_idx
ON orders (customer_id);
```

Indexes on foreign-key columns can also improve operations involving parent-row updates/deletes because the database may need to efficiently locate referencing rows.

---

## Indexes and Constraints

Indexes frequently support constraints.

Common examples include:

```text
PRIMARY KEY
UNIQUE
```

Conceptually:

```text
Constraint
    |
    v
Index-backed enforcement
    |
    v
Fast lookup + integrity guarantee
```

Do not create redundant indexes simply because a constraint already created an equivalent index.

---

## Query Planner

The database query planner determines how a query should execute.

It considers:

- Available indexes
- Table statistics
- Estimated row counts
- Data distribution
- Predicate selectivity
- Join cardinality
- Sorting cost
- Memory
- I/O cost
- CPU cost

A simplified decision looks like:

```text
                    Query
                      |
                      v
                Query Planner
                 /          \
                v            v
         Sequential Scan   Index Scan
                |            |
                +-----+------+
                      |
                      v
                 Chosen Plan
```

The planner is cost-based.

Therefore, "the index exists" is not enough.

---

## EXPLAIN

Before optimizing a query, inspect its execution plan.

PostgreSQL:

```sql
EXPLAIN
SELECT *
FROM users
WHERE email = 'alice@example.com';
```

For actual execution metrics:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users
WHERE email = 'alice@example.com';
```

Important fields include:

- `Seq Scan`
- `Index Scan`
- `Index Only Scan`
- `Bitmap Index Scan`
- `Bitmap Heap Scan`
- `Rows Removed by Filter`
- `actual time`
- `actual rows`
- `loops`
- Buffer statistics

Do not optimize based solely on intuition.

Measure the actual query.

---

## Reading an Execution Plan

Consider:

```text
Index Scan using users_email_idx on users
  Index Cond: (email = 'alice@example.com')
  actual rows=1
```

This indicates that the index is being used as part of the access path.

Compare that with:

```text
Seq Scan on users
  Filter: (status = 'active')
  actual rows=9500000
```

A sequential scan may be entirely reasonable if most rows match.

The question is not:

> "Why didn't PostgreSQL use my index?"

The better question is:

> "Is the selected execution plan cheaper for this data distribution and workload?"

---

## Statistics and Index Decisions

Query planners depend on statistics.

Statistics may become inaccurate when data changes significantly.

For PostgreSQL, statistics can be updated through `ANALYZE`:

```sql
ANALYZE users;
```

Autovacuum and auto-analyze generally handle this automatically, but large data changes or unusual workloads may require operational attention.

If the planner estimates:

```text
Estimated rows: 10
Actual rows: 5,000,000
```

the chosen plan may be poor because the optimizer made a fundamentally incorrect assumption.

---

## Index Scan vs Bitmap Scan

PostgreSQL can use bitmap strategies for queries that match many rows.

Conceptually:

```text
Index
  |
  v
Bitmap of matching pages
  |
  v
Heap/table page access
  |
  v
Rows
```

Bitmap scans can be useful when the result set is too large for a traditional index scan to be optimal but still selective enough that a full table scan is unnecessary.

This is another reason not to force a specific scan type without examining the workload.

---

## Index-Only Scans

An index-only scan can satisfy a query using index data without fetching the table row for every result.

For example:

```sql
CREATE INDEX users_email_id_idx
ON users (email, id);
```

Potential query:

```sql
SELECT id
FROM users
WHERE email = 'alice@example.com';
```

If the required data is available in the index and PostgreSQL's visibility information permits it, an index-only scan can reduce heap access.

Index-only scans are particularly useful for:

- Read-heavy workloads
- Narrow queries
- Frequently accessed lookup paths
- Large tables

But they are not guaranteed merely because all selected columns appear in the index.

---

## Write Amplification

Indexes accelerate reads but make writes more expensive.

Consider:

```text
INSERT row
   |
   +---- update table
   |
   +---- update index A
   |
   +---- update index B
   |
   +---- update index C
```

If a table has many indexes, every insert may require maintaining multiple structures.

Updates can be even more expensive when indexed columns change.

Therefore:

```text
More indexes
    |
    +---- faster certain reads
    |
    +---- slower writes
    +---- more storage
    +---- more maintenance
```

Index design is always a trade-off.

---

## Index Storage Cost

Indexes can consume substantial storage.

A table:

```text
100 GB
```

may have several indexes that add significant additional storage.

This affects:

- Disk cost
- Backup size
- Replication traffic
- Cache pressure
- Maintenance time
- Restore time

Do not evaluate index performance without considering its storage footprint.

---

## Index and Memory Pressure

Frequently accessed indexes may remain in memory or cache.

A larger index can increase cache pressure:

```text
Memory
+--------------------------+
| Table pages              |
| Frequently used indexes  |
| Other working data       |
+--------------------------+
```

Adding a large index may push other useful data out of cache.

An index can therefore make one query faster while indirectly affecting unrelated workloads.

---

## Index Bloat and Maintenance

Indexes can accumulate unused or inefficient storage depending on database engine, workload, update patterns, and maintenance behavior.

PostgreSQL environments should monitor:

- Index size
- Index usage
- Table bloat
- Index bloat
- Vacuum behavior
- Autovacuum activity
- Dead tuples

Operational maintenance should be based on actual database behavior rather than periodically rebuilding every index.

---

## Concurrent Index Creation

For production PostgreSQL systems, creating an index on a large live table requires careful planning.

PostgreSQL supports:

```sql
CREATE INDEX CONCURRENTLY users_email_idx
ON users (email);
```

This reduces the blocking impact on normal writes compared with a regular index build, though it has operational trade-offs and can take longer.

It is not a universal "zero-impact" operation.

Teams should consider:

- Build duration
- Disk usage
- I/O load
- Lock behavior
- Failed builds
- Deployment coordination
- Replication implications

---

## Indexing in Django

Django supports indexes through model metadata.

Example:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.BigIntegerField()
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["customer_id", "status", "-created_at"],
                name="order_customer_status_created_idx",
            ),
        ]
```

Django migrations can then create the database index:

```bash
python manage.py makemigrations
python manage.py migrate
```

Django also supports database constraints:

```python
class User(models.Model):
    email = models.EmailField(unique=True)
```

For production systems, index design should still begin with SQL workload analysis rather than blindly adding indexes to Django models.

---

## Django Query Optimization

Suppose the application frequently executes:

```python
Order.objects.filter(
    customer_id=customer_id,
    status="pending",
).order_by("-created_at")[:50]
```

A supporting composite index may be appropriate:

```python
class Meta:
    indexes = [
        models.Index(
            fields=["customer_id", "status", "-created_at"],
            name="order_customer_status_created_idx",
        ),
    ]
```

The correct decision should be validated with the actual SQL and execution plan.

Django abstractions do not remove the need to understand database behavior.

---

## FastAPI and SQLAlchemy

FastAPI itself does not manage database indexes.

If SQLAlchemy is used, indexes are generally declared at the model/table layer:

```python
from sqlalchemy import Index, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index("users_email_idx", "email"),
    )
```

Database migrations should then be managed using a migration system such as Alembic.

---

## Multi-Tenant Indexing

Multi-tenant systems require careful index design.

Suppose every query includes:

```sql
WHERE tenant_id = ?
  AND status = ?
```

A useful index might be:

```sql
CREATE INDEX orders_tenant_status_idx
ON orders (tenant_id, status);
```

For tenant-isolated applications, the tenant key is often part of the primary access pattern.

A common architecture is:

```text
tenant_id
    |
    +---- primary filtering boundary
             |
             +---- status
             +---- created_at
             +---- resource_id
```

The exact order should follow real query patterns.

For very large tenants, however, indexing alone may not solve scale problems. Partitioning, sharding, workload isolation, or tenant-specific strategies may become necessary.

---

## Partitioning vs Indexing

Partitioning and indexing solve different problems.

| Technique | Primary Purpose |
|---|---|
| Index | Efficient row lookup within a data structure |
| Partitioning | Divide a large logical table into smaller physical pieces |
| Sharding | Distribute data across database nodes |
| Caching | Avoid database reads entirely |
| Denormalization | Reduce expensive joins/read computation |

They can be combined.

For example:

```text
Orders
   |
   +---- Partition by month
             |
             +---- Local indexes
```

Partitioning does not eliminate the need for appropriate indexes.

---

## Indexing Time-Series Data

For time-series workloads:

```sql
SELECT *
FROM events
WHERE created_at >= :start
  AND created_at < :end
ORDER BY created_at DESC
LIMIT 100;
```

an index such as:

```sql
CREATE INDEX events_created_at_idx
ON events (created_at DESC);
```

may be useful.

For very large datasets, consider:

- Partitioning by time
- Retention policies
- BRIN indexes in PostgreSQL for physically correlated large tables
- Data lifecycle management
- Cold storage
- Aggregation

The correct strategy depends on data volume and physical ordering.

---

## BRIN Indexes

PostgreSQL's **Block Range Index (BRIN)** summarizes value ranges for groups of table pages.

They can be extremely compact for large tables where physical row order correlates with the indexed value.

For example:

```sql
CREATE INDEX events_created_at_brin_idx
ON events
USING BRIN (created_at);
```

This can work well for append-heavy tables such as:

```text
events
logs
metrics
audit records
```

where `created_at` roughly follows insertion order.

BRIN is not a universal replacement for B-tree.

It is most effective when the physical layout has useful correlation with the indexed value.

---

## Full-Text and Specialized Indexes

Not all search problems should use ordinary B-tree indexes.

Depending on the database:

```text
B-tree
    -> equality/range/order

GIN
    -> arrays, JSONB, full-text-related workloads

GiST
    -> geometric/range and specialized operators

BRIN
    -> large correlated datasets
```

For example, PostgreSQL JSONB workloads may benefit from GIN:

```sql
CREATE INDEX products_metadata_gin_idx
ON products
USING GIN (metadata);
```

Index type should be selected according to the operators and access patterns actually used.

---

## Indexing JSON Data

Suppose:

```sql
products.metadata
```

contains:

```json
{
  "color": "black",
  "brand": "example"
}
```

A query might be:

```sql
SELECT *
FROM products
WHERE metadata @> '{"brand": "example"}';
```

A GIN index may be appropriate:

```sql
CREATE INDEX products_metadata_idx
ON products
USING GIN (metadata);
```

However, indexing every JSON field indiscriminately can create oversized indexes.

If a JSON attribute becomes a major query dimension, consider whether it should instead become a proper relational column.

---

## Indexing Anti-Patterns

### Indexing Every Column

This creates:

- Large storage usage
- Write overhead
- Maintenance cost
- More planner choices
- Potential cache pressure

### Duplicate Indexes

For example:

```sql
CREATE INDEX idx_a ON users(email);
CREATE INDEX idx_b ON users(email);
```

These usually provide no benefit and increase maintenance overhead.

### Redundant Composite Indexes

For example:

```text
(email)
(email, created_at)
```

may make the standalone `email` index unnecessary depending on workload and database behavior.

Do not assume redundancy without checking actual access patterns.

### Wrong Composite Column Order

```sql
INDEX(status, customer_id)
```

may be ineffective for an important workload dominated by:

```sql
WHERE customer_id = ?
```

when the desired access path should begin with `customer_id`.

### Indexing Low-Value Predicates

An index on a boolean column may not help when most rows have the same value.

### Ignoring Writes

A read optimization can become a write bottleneck if a high-throughput table accumulates too many indexes.

### Using Functions Without Matching Indexes

```sql
WHERE LOWER(email) = ?
```

with only:

```sql
INDEX(email)
```

may not provide the expected access path.

### Optimizing Without EXPLAIN

Guessing is not query optimization.

---

## Production Indexing Workflow

A practical workflow is:

```text
Identify slow query
       |
       v
Measure baseline
       |
       v
Inspect EXPLAIN ANALYZE
       |
       v
Understand access pattern
       |
       v
Design candidate index
       |
       v
Test against realistic data
       |
       v
Measure execution plan
       |
       v
Deploy carefully
       |
       v
Monitor
       |
       v
Remove index if unnecessary
```

### Identify

Use:

- Application APM
- Database slow-query logs
- PostgreSQL statistics
- Query monitoring
- Production traces

### Measure

Record:

- Latency
- Rows examined
- Rows returned
- CPU
- I/O
- Buffer hits
- Query frequency

### Design

Consider:

- Equality predicates
- Range predicates
- Ordering
- Joins
- Selectivity
- Covering requirements
- Partial conditions

### Validate

Test with:

- Production-like row counts
- Production-like data distribution
- Realistic concurrency
- Realistic parameter values

### Deploy

For large production tables:

- Consider concurrent index creation.
- Avoid unplanned lock contention.
- Monitor disk space.
- Monitor replication.
- Have a rollback/removal plan.

### Monitor

After deployment, verify:

- Query latency improved.
- Query plan changed as expected.
- Write latency did not regress.
- Storage growth is acceptable.
- Index is actually being used.

---

## Index Usage Monitoring

PostgreSQL exposes index usage statistics through system views such as:

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

Indexes with extremely low usage may be candidates for review.

Do not immediately delete an apparently unused index.

Consider:

- Rare but critical queries
- Constraint-backed indexes
- Future workloads
- Failover behavior
- Maintenance windows
- Statistics reset history

An index should be removed only after understanding its purpose and usage over an appropriate observation period.

---

## Zero-Downtime Index Changes

Production index migrations require the same engineering discipline as application deployments.

A typical approach is:

```text
Application version N
       |
       v
Create new index
       |
       v
Validate performance
       |
       v
Deploy application version N+1
       |
       v
Monitor
       |
       v
Remove obsolete index later
```

Avoid coupling a risky large index build directly to a critical application release unless the operational characteristics are understood.

For PostgreSQL:

```sql
CREATE INDEX CONCURRENTLY ...
```

can be appropriate for live systems, but teams should understand its limitations and migration tooling behavior.

---

## High Availability Considerations

Indexes affect more than a single database node.

In replicated environments:

```text
Primary
   |
   +---- WAL / replication
   |
   v
Replica
```

Creating or modifying large indexes can increase:

- I/O
- WAL generation
- Replication lag
- Storage utilization
- Recovery time

For large production databases, index operations should therefore be treated as operational events.

Monitor:

```text
Replication lag
Disk utilization
I/O latency
CPU
Lock activity
Query latency
```

---

## Disaster Recovery Considerations

Indexes are generally derived structures rather than independent business data.

The source table data remains the authoritative information.

However, indexes affect:

- Backup size
- Restore duration
- Recovery performance
- Database startup behavior
- Post-restore query performance

After restoring a database, verify that:

- Required indexes exist.
- Constraints are intact.
- Query plans remain reasonable.
- Statistics are refreshed when necessary.
- Application performance is acceptable.

A backup strategy should account for both data recovery and the operational time required to restore a performant database.

---

## Security Considerations

Indexes do not replace authorization.

For example:

```sql
CREATE INDEX orders_customer_id_idx
ON orders(customer_id);
```

does not enforce that a user may only access their own orders.

Authorization must remain an application or database security concern:

```text
Authentication
      |
      v
Authorization
      |
      v
Query
      |
      v
Index-assisted execution
```

In multi-tenant applications, ensure that tenant isolation is enforced independently of index design.

Indexes may also contain copies of sensitive values. Protect database files, backups, replicas, and operational access accordingly.

---

## Cost Considerations

Every index has a cost profile.

| Cost | Impact |
|---|---|
| Storage | Additional disk usage |
| Writes | Inserts/updates become more expensive |
| Maintenance | More structures to maintain |
| Replication | More database activity and potentially more WAL |
| Backups | Larger database footprint |
| Memory | Increased cache pressure |
| Operations | More objects to monitor and migrate |

A useful optimization metric is:

```text
Value of index
=
Read performance benefit
-
Write + storage + maintenance cost
```

An index that saves 500 ms on a query executed once per day may not justify significant write overhead.

An index that saves 500 ms on a query executed 10,000 times per second almost certainly deserves serious consideration.

---

## Interview Questions

### Why does an index improve query performance?

It provides an access path that allows the database to locate relevant rows without scanning the entire table.

### Why doesn't the database always use an index?

Because the query planner estimates whether an index-based plan is cheaper than alternatives such as sequential scans.

### What is a composite index?

An index containing multiple columns, such as:

```sql
CREATE INDEX idx
ON orders (customer_id, status, created_at);
```

The column order affects which query patterns can efficiently use the index.

### What is the leftmost prefix principle?

For many B-tree composite indexes, queries can efficiently use leading portions of the index, such as `(customer_id)` or `(customer_id, status)`, while a query filtering only on a later column may not obtain the same benefit.

### Why can too many indexes hurt performance?

Every insert, delete, and relevant update must maintain those indexes. This increases write cost, storage usage, maintenance work, and potentially replication overhead.

### What is a covering index?

An index that contains enough information for a query to avoid fetching the full table row, potentially enabling an index-only access path.

### What is a partial index?

An index containing only rows satisfying a predicate:

```sql
CREATE INDEX jobs_pending_idx
ON jobs(created_at)
WHERE status = 'pending';
```

### How do you decide whether an index is useful?

Analyze actual query patterns and execution plans using tools such as:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and validate against realistic data and workload.

### Should every foreign key be indexed?

Not automatically, but foreign-key columns frequently benefit from indexes because they are commonly used in joins, filtering, and parent-row modification checks.

### What is the difference between an index and partitioning?

An index provides an efficient lookup structure, while partitioning divides a logical table into separate physical partitions. They solve different problems and can be used together.

---

## Key Takeaways

- **Indexes provide optimized access paths to data**, but the database optimizer decides whether using an index is actually cheaper than alternatives such as sequential scans.
- **Index design must follow query patterns**: composite-column order, equality/range predicates, joins, sorting, pagination, and selectivity all influence whether an index is effective.
- **Indexes are not free**: they consume storage, increase write latency, add maintenance work, increase replication activity, and can create memory pressure.
- **Use execution plans and production-like data to validate indexing decisions**, especially with PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` rather than relying on intuition.
- **A production indexing strategy continuously balances read performance against operational cost**, including index usage monitoring, safe migrations, high availability, replication, backups, and periodic removal of genuinely unnecessary indexes.