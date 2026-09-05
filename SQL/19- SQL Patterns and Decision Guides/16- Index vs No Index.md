# 16- Index vs No Index

## Overview

An index is a database data structure that helps the query planner locate rows without scanning the entire table.

The decision is not:

> "Should every frequently queried column have an index?"

The real question is:

> "Does the performance benefit of this access path justify the storage, write, maintenance, and operational cost of the index?"

For a PostgreSQL backend, an index can dramatically improve a selective query:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

with:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

But indexes are not free.

Every additional index can increase:

- Disk usage.
- `INSERT` cost.
- `UPDATE` cost when indexed columns change.
- `DELETE` cost.
- WAL generation.
- Vacuum work.
- Backup size.
- Replication traffic.
- Write latency.
- Schema migration time.

The senior engineering decision is therefore a workload optimization problem rather than an indexing checklist.

---

## What an Index Does

Without a suitable index, a query may need to inspect a large portion of the table:

```text
Query
  ↓
Sequential scan
  ↓
Rows examined
  ↓
Rows matching predicate
```

With a suitable index:

```text
Query
  ↓
Index lookup
  ↓
Candidate row locations
  ↓
Table/index access
  ↓
Rows returned
```

The exact execution strategy is chosen by the query planner.

An index does not force the database to use it.

---

## Sequential Scan

A sequential scan reads the table's pages in sequence.

For example:

```sql
SELECT *
FROM customers
WHERE country = 'IN';
```

If most customers are in India, a sequential scan may be cheaper than using an index.

Conceptually:

```text
Table
 ├── page 1
 ├── page 2
 ├── page 3
 ├── ...
 └── page N

Read pages
    ↓
Evaluate predicate
    ↓
Return matches
```

A sequential scan is not inherently bad.

For large portions of a table, sequential access can be more efficient than random index-driven access.

---

## Index Scan

With an appropriate index:

```sql
CREATE INDEX idx_customers_country
ON customers (country);
```

the planner may choose an index-based plan:

```text
Index
  ↓
Find matching keys
  ↓
Locate table rows
  ↓
Fetch required columns
```

For highly selective queries, this can avoid reading most table pages.

For example:

```sql
SELECT *
FROM customers
WHERE id = $1;
```

A primary-key index is highly effective because a single ID usually identifies one row.

---

## Bitmap Index Access

PostgreSQL can also use a bitmap strategy.

Conceptually:

```text
Index
  ↓
Collect matching row locations
  ↓
Build bitmap
  ↓
Read table pages efficiently
  ↓
Return matching rows
```

This can be useful when:

- Many rows match.
- Multiple pages are involved.
- An index scan would cause excessive random heap access.
- Multiple indexes can be combined.

For example, PostgreSQL may use bitmap operations for predicates involving multiple indexed columns.

The planner decides among sequential scans, index scans, bitmap scans, and other strategies based on estimated cost.

---

## Index-Only Scan

Sometimes PostgreSQL can answer a query primarily from the index without fetching the heap row for every result.

For example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

A query that only needs indexed columns may be eligible:

```sql
SELECT
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

However, an index-only scan is not guaranteed.

PostgreSQL also uses visibility information to determine whether heap access can be avoided.

Therefore:

> "The index contains all requested columns" does not automatically mean "index-only scan."

---

## Why Indexes Improve Performance

Indexes reduce the amount of data the database needs to inspect.

For a selective query:

```text
10,000,000 table rows
        ↓
Index lookup
        ↓
50 matching rows
```

instead of potentially evaluating millions of rows.

The benefit depends heavily on:

- Selectivity.
- Data distribution.
- Query shape.
- Index structure.
- Table size.
- Cache state.
- Statistics.
- Returned columns.
- Ordering requirements.

An index is useful when its access path is cheaper than the alternatives.

---

## Index Selectivity

Selectivity describes how narrowly a predicate identifies rows.

Consider:

```text
status = 'cancelled'
```

If:

```text
1% of rows are cancelled
```

the predicate is highly selective.

If:

```text
95% of rows are active
```

then:

```sql
WHERE status = 'active'
```

is not very selective.

An index on a low-cardinality column is not automatically useless, but its usefulness depends on the complete query.

For example:

```sql
SELECT *
FROM orders
WHERE status = 'cancelled'
  AND created_at >= $1;
```

may benefit from a composite or partial index even if `status` alone has low selectivity.

---

## Indexes and `ORDER BY`

Indexes can also help avoid sorting.

Consider:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

An index such as:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

aligns with:

```text
WHERE customer_id = ?
ORDER BY created_at DESC
```

This can allow PostgreSQL to retrieve rows in the required order.

The index is therefore serving both:

```text
filtering
+
ordering
```

This is often particularly valuable for paginated APIs.

---

## Composite Indexes

A composite index contains multiple columns:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (
    customer_id,
    status,
    created_at DESC
);
```

Column order matters.

The index is physically organized according to the specified key order.

Do not treat:

```text
(a, b, c)
```

as equivalent to:

```text
(b, a, c)
```

for every workload.

Index design should follow actual query predicates and ordering requirements.

---

## The Leftmost Prefix Principle

For a B-tree index:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (
    customer_id,
    status,
    created_at DESC
);
```

the leading columns matter.

A query such as:

```sql
WHERE customer_id = $1
  AND status = $2
ORDER BY created_at DESC;
```

aligns well with the index.

A query only on:

```sql
WHERE status = $1;
```

does not have the same direct access pattern because `status` is not the leading index column.

Modern PostgreSQL can sometimes use an index in less obvious ways, including skip-scan behavior in suitable cases, but the general design rule remains:

> Put columns in the index based on the actual workload, not simply by listing every frequently queried column.

---

## Index vs No Index

| Factor | No Index | With Index |
|---|---|---|
| Read latency for selective queries | Can be high | Often much lower |
| Full-table scans | Natural | Still possible |
| Insert cost | Lower | Higher |
| Update cost | Lower | Higher when indexed values change |
| Delete cost | Lower | Higher |
| Storage | Lower | Higher |
| WAL/maintenance | Lower | Higher |
| Schema complexity | Lower | Higher |
| Deep pagination | Often poor | Can be much better |
| Point lookups | Poor at scale | Excellent |
| Low-selectivity queries | May be better | May not help |
| Operational overhead | Lower | Higher |

---

## When No Index Is Better

Not every column deserves an index.

A table may be better without an index when:

- It is very small.
- The query is rarely executed.
- The indexed predicate has poor selectivity.
- The table is write-heavy.
- The index is not used.
- The index duplicates another index.
- The query is expected to scan most of the table anyway.
- The index provides negligible benefit relative to its maintenance cost.

For a small table:

```text
100 rows
```

a sequential scan may be cheaper than navigating an index.

Do not optimize based on theoretical index usage alone.

---

## Write Cost of Indexes

Suppose:

```sql
CREATE TABLE events (
    id bigint PRIMARY KEY,
    customer_id bigint NOT NULL,
    event_type text NOT NULL,
    created_at timestamptz NOT NULL
);
```

Adding:

```sql
CREATE INDEX idx_events_customer
ON events (customer_id);
```

means an insert must maintain both:

```text
events table
+
customer_id index
```

If there are five indexes:

```text
INSERT
  ├── table write
  ├── index 1
  ├── index 2
  ├── index 3
  ├── index 4
  └── index 5
```

Indexes therefore increase write amplification.

This matters significantly for:

- High-ingest event tables.
- Kafka consumers.
- Audit logs.
- Metrics tables.
- Bulk imports.
- Write-heavy OLTP systems.

---

## Update Cost

Updating an indexed column can require index maintenance.

For example:

```sql
UPDATE customers
SET email = $1
WHERE id = $2;
```

If `email` is indexed, the database must maintain the corresponding index entry.

Even updating a non-indexed column can have index implications because PostgreSQL's MVCC model creates new row versions and may affect whether index-only scans remain efficient.

The cost of indexes therefore cannot be evaluated solely by counting indexed-column updates.

---

## Delete Cost

Deleting rows also requires maintaining indexes.

For:

```sql
DELETE FROM orders
WHERE created_at < $1;
```

the database must maintain:

```text
table state
+
all affected indexes
```

Large deletes can therefore be expensive in heavily indexed tables.

Combined with PostgreSQL MVCC, large deletes can also create dead tuples and increase vacuum work.

---

## Index Storage Cost

Every index consumes disk space.

For large tables:

```text
orders table       → 500 GB
indexes            → additional hundreds of GB
```

is entirely possible depending on schema and index definitions.

Index storage affects:

- Database volume requirements.
- Backups.
- Restore time.
- Replication.
- Cache pressure.
- Storage costs.

A redundant index is not free simply because disk space is relatively inexpensive.

---

## Cache and Memory Effects

Indexes compete for memory with table data.

A workload with many large indexes can increase:

```text
buffer cache pressure
```

and reduce the amount of frequently accessed table data that fits in memory.

A smaller number of well-designed indexes can sometimes outperform a large collection of partially useful indexes.

Index design is therefore also a memory-management concern.

---

## Redundant Indexes

Consider:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);

CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

The second index may make the first unnecessary for some workloads.

But do not automatically drop the first index.

Check:

- Actual query patterns.
- Index usage.
- Index size.
- Planner behavior.
- Write overhead.
- PostgreSQL version.
- Special query cases.

Use production evidence before removing indexes.

---

## Detecting Unused Indexes

PostgreSQL exposes index statistics through:

```sql
SELECT
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan, pg_relation_size(indexrelid) DESC;
```

An index with zero scans may be suspicious.

But "unused" does not automatically mean "safe to drop."

Reasons include:

- Statistics reset.
- Rare but critical queries.
- Reporting workloads.
- Failover paths.
- Seasonal workloads.
- Recent deployment.
- Planner preference for another equivalent index.

Index removal should be treated as a measured production change.

---

## Duplicate and Overlapping Indexes

Review indexes periodically.

For example:

```text
(customer_id)
(customer_id, created_at)
(customer_id, status, created_at)
```

may represent legitimate distinct workloads or unnecessary overlap.

The correct decision requires query workload analysis.

Do not blindly keep every index created by different application teams over several years.

Index debt is a real operational problem.

---

## Partial Indexes

A partial index covers only rows satisfying a predicate.

Example:

```sql
CREATE INDEX idx_orders_pending_created
ON orders (created_at DESC)
WHERE status = 'pending';
```

This is useful when queries frequently access:

```sql
SELECT *
FROM orders
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 100;
```

and pending orders represent only a subset of the table.

Benefits include:

- Smaller index.
- Lower maintenance cost.
- Potentially better cache behavior.
- Efficient access to a hot subset.

The query predicate must align with the index predicate for PostgreSQL to use the index appropriately.

---

## Expression Indexes

An expression index indexes a computed expression.

Example:

```sql
CREATE INDEX idx_customers_lower_email
ON customers (lower(email));
```

This can support:

```sql
SELECT *
FROM customers
WHERE lower(email) = lower($1);
```

Expression indexes are useful when the expression is part of a stable, repeated query pattern.

But they add:

- Storage.
- Write cost.
- Schema complexity.

Prefer data normalization or appropriate data types when that solves the problem more cleanly.

---

## Unique Indexes

A unique index can enforce a business invariant:

```sql
CREATE UNIQUE INDEX users_email_unique
ON users (lower(email));
```

This provides both:

```text
lookup capability
+
uniqueness enforcement
```

For business-critical uniqueness, database enforcement is stronger than relying only on application checks.

For example, two concurrent requests can both pass:

```python
if not user_exists(email):
    create_user(...)
```

without a database constraint.

The unique index closes that race.

---

## Foreign Keys and Indexes

A foreign key does not automatically mean the referencing column has an index in every database system.

In PostgreSQL, consider indexing frequently joined or filtered foreign-key columns.

For example:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

This can help:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;
```

and can also help certain parent-row updates/deletes because the database needs to check referencing rows.

The correct index should be based on workload and referential-integrity behavior.

---

## Pagination

Indexes are particularly important for large pagination workloads.

Offset:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 100000;
```

can still require traversing many rows even with an index.

Keyset:

```sql
SELECT *
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

can seek directly from the cursor boundary when supported by an appropriate index:

```sql
CREATE INDEX idx_orders_created_id
ON orders (created_at DESC, id DESC);
```

For large APIs, keyset pagination plus aligned indexes is often a strong combination.

---

## Indexes and Joins

Consider:

```sql
SELECT
    o.id,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.customer_id = $1;
```

Indexes can support:

```text
orders.customer_id
customers.id
```

`customers.id` is typically covered by the primary key.

The referencing side may need an explicit index:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

The planner can then choose an efficient join strategy based on estimated cardinalities and costs.

---

## Indexes and `EXISTS`

For:

```sql
SELECT c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

an index on:

```sql
orders(customer_id)
```

can provide an efficient access path.

However, do not assume:

```text
EXISTS → index required
```

The planner may choose another strategy depending on table sizes and selectivity.

Always inspect the plan.

---

## Indexes and Aggregation

An index does not automatically make aggregation cheap.

For:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

the database may still need to process a large portion of the table.

An index on:

```sql
(customer_id)
```

may or may not improve the query.

The best strategy depends on:

- Table size.
- Number of distinct customers.
- Query shape.
- Visibility.
- Statistics.
- Whether only indexed columns are required.
- Aggregation strategy.

Do not create an index simply because a column appears in `GROUP BY`.

---

## Indexes and Sorting

An index can help with:

```sql
ORDER BY created_at DESC
```

but only if its ordering and query predicates make the access path useful.

For example:

```sql
CREATE INDEX idx_orders_created_id
ON orders (created_at DESC, id DESC);
```

aligns with:

```sql
ORDER BY created_at DESC, id DESC;
```

If the query returns most of the table, the planner may still prefer a sequential scan followed by a sort.

Again:

> An index provides an option; the optimizer decides whether that option is cheaper.

---

## Indexes and `LIKE`

A normal B-tree index is not universally effective for text search.

For:

```sql
WHERE email LIKE 'alice%'
```

a B-tree may be useful under appropriate conditions.

For:

```sql
WHERE email LIKE '%alice%'
```

a normal B-tree generally cannot efficiently seek to the middle of the string.

PostgreSQL-specific options such as:

- `pg_trgm`
- GIN/GiST indexes
- Full-text search

may be more appropriate depending on the search requirement.

Do not add a normal B-tree index expecting it to solve arbitrary substring search.

---

## Indexes and NULL

PostgreSQL B-tree indexes can contain `NULL` values.

For:

```sql
SELECT *
FROM customers
WHERE phone IS NULL;
```

an index can potentially be useful.

The planner still evaluates the cost.

For workloads focused on a small subset of null rows, a partial index may be attractive:

```sql
CREATE INDEX idx_customers_phone_null
ON customers (id)
WHERE phone IS NULL;
```

---

## Indexes and Soft Deletes

A common SaaS pattern is:

```sql
WHERE tenant_id = $1
  AND deleted_at IS NULL
```

A partial index can be effective:

```sql
CREATE INDEX idx_orders_active_tenant_created
ON orders (
    tenant_id,
    created_at DESC
)
WHERE deleted_at IS NULL;
```

This keeps deleted rows out of the index.

It can be particularly useful when:

```text
active rows = 95%
deleted rows = 5%
```

or the reverse, depending on the workload and query patterns.

Do not blindly index every soft-delete predicate; measure the actual workload.

---

## Multi-Tenant Indexing

For a multi-tenant application:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 50;
```

a candidate index is:

```sql
CREATE INDEX idx_orders_tenant_status_created
ON orders (
    tenant_id,
    status,
    created_at DESC
);
```

The leading tenant key can be especially important when many tenants share a large table.

But tenant distributions matter.

If one tenant owns 80% of the table, its access pattern may behave very differently from a tenant owning 0.01%.

Index design should account for skew.

---

## Indexes and Query Planner Statistics

The PostgreSQL planner relies on statistics to estimate:

```text
row counts
selectivity
data distribution
join cardinality
```

If statistics are stale or inadequate, the planner can choose a poor plan even when a good index exists.

`ANALYZE` updates statistics:

```sql
ANALYZE orders;
```

Autovacuum normally performs automatic analyze operations, but large data changes or unusual distributions may require closer attention.

For skewed columns, PostgreSQL statistics targets can sometimes be adjusted.

Do not assume:

```text
index exists → optimal plan
```

The optimizer needs accurate information to make that decision.

---

## Execution Plan Verification

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

Inspect:

- `Seq Scan`.
- `Index Scan`.
- `Index Only Scan`.
- `Bitmap Heap Scan`.
- `Bitmap Index Scan`.
- Actual rows.
- Estimated rows.
- Buffers.
- Sort operations.
- Execution time.

For example:

```text
estimated rows = 50
actual rows    = 500,000
```

is a major warning sign.

The problem may be statistics, data distribution, or query structure rather than merely a missing index.

---

## Indexes Are Not Guarantees

An index may exist and still not be used.

Possible reasons include:

- Low selectivity.
- Small table.
- Query returns many rows.
- Sequential scan is cheaper.
- Type mismatch.
- Expression mismatch.
- Statistics are inaccurate.
- Ordering does not align.
- The query uses a different predicate.
- The planner estimates a different cardinality.

This is why the following reasoning is weak:

> "The query is slow because there is no index."

A stronger process is:

```text
Observe
  ↓
EXPLAIN
  ↓
Understand workload
  ↓
Design index
  ↓
Test
  ↓
Measure
```

---

## Type Matching and Index Usage

Avoid implicit conversions that prevent efficient access paths.

For example, if:

```sql
customer_id bigint
```

the application should bind a compatible parameter type.

Do not rely on converting indexed columns inside predicates unnecessarily:

```sql
WHERE customer_id::text = $1;
```

when the actual query can use:

```sql
WHERE customer_id = $1;
```

If a transformation is genuinely required, consider whether an expression index is appropriate.

---

## Index Deployment in PostgreSQL

Creating an index on a large production table requires planning.

Standard:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);
```

can take locks that affect concurrent operations depending on the operation and PostgreSQL behavior.

For production workloads where minimizing blocking is important:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer
ON orders (customer_id);
```

`CREATE INDEX CONCURRENTLY` reduces blocking of ordinary writes, but it has trade-offs:

- Takes longer.
- Performs more work.
- Cannot run inside a transaction block.
- Can leave an invalid index if the operation fails.
- Requires operational monitoring.

Migration tooling must support the required transaction behavior.

---

## Failed Concurrent Index Creation

After a failed concurrent index creation, inspect indexes:

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisvalid,
    indisready
FROM pg_index
WHERE NOT indisvalid
   OR NOT indisready;
```

An invalid index may require cleanup before retrying.

Do not assume a failed migration always leaves the database exactly as it was before the operation.

---

## Index Lifecycle

Treat indexes as production artifacts.

A healthy lifecycle is:

```text
Query requirement
      ↓
Index design
      ↓
Migration
      ↓
Production validation
      ↓
Usage monitoring
      ↓
Periodic review
      ↓
Retain / modify / remove
```

Indexes should evolve with application behavior.

A query that justified an index two years ago may no longer exist.

---

## Django Indexes

Django supports indexes at the model level.

For example:

```python
from django.db import models


class Order(models.Model):
    tenant_id = models.BigIntegerField()
    created_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(
                fields=["tenant_id", "-created_at"],
                name="orders_tenant_created_idx",
            ),
        ]
```

For more advanced PostgreSQL indexes, Django migrations can use database-specific features and operations.

Index definitions should remain part of version-controlled schema migrations.

Do not create production indexes manually and forget to encode them in CI/CD migrations.

---

## FastAPI and SQLAlchemy

With SQLAlchemy:

```python
from sqlalchemy import Index

Index(
    "orders_tenant_created_idx",
    Order.tenant_id,
    Order.created_at.desc(),
)
```

The important principle is independent of ORM:

```text
ORM model
    ↓
Generated SQL
    ↓
Execution plan
    ↓
Index access path
```

Always inspect actual SQL and production query behavior.

An ORM abstraction does not eliminate database optimization responsibilities.

---

## Indexes in Microservices

A service should generally own the indexes for the data it owns.

Avoid cross-service assumptions such as:

```text
Service A
    ↓
expects Service B's database index
```

Microservices should not directly depend on another service's database schema or tuning decisions.

If a service requires a specialized query model, consider:

```text
service-owned read model
```

rather than cross-service database coupling.

---

## Indexes and Kubernetes

Kubernetes does not change database index semantics, but it changes operational considerations.

For example:

```text
Kubernetes deployment
      ↓
new application version
      ↓
migration job
      ↓
CREATE INDEX CONCURRENTLY
      ↓
application rollout
```

Index creation should not be casually coupled to every application pod startup.

Use controlled migration workflows through CI/CD.

Avoid:

```text
every pod starts
    ↓
attempts database schema change
```

Schema changes should normally be executed once through a controlled migration process.

---

## Indexes and Read Replicas

Index creation and maintenance affect replication because index changes generate WAL.

Large index builds can therefore contribute to:

- Replica lag.
- I/O pressure.
- Storage growth.
- Recovery workload.

Before creating a large production index, consider:

- Primary load.
- Replica capacity.
- Replication lag.
- Backup systems.
- Maintenance windows.
- Storage headroom.

An index that improves read latency can temporarily increase system-wide replication pressure during deployment.

---

## High Availability

Indexes are part of the database schema and therefore need to be present on failover targets.

For streaming replication:

```text
Primary
  ↓ WAL
Replica
```

index changes are replicated through WAL.

A failover should therefore preserve the index state.

However, large index operations can increase replication pressure and should be included in HA capacity planning.

---

## Backup and Disaster Recovery

Indexes increase:

- Database size.
- Backup volume.
- Restore workload.

But indexes are usually reconstructable from table data.

The critical distinction is:

```text
Business data
    ↓
authoritative

Indexes
    ↓
derived access structures
```

For disaster recovery, indexes still matter because a restored database without expected indexes may have unacceptable performance.

A recovery plan should validate:

- Schema version.
- Required indexes.
- Invalid indexes.
- Query performance.
- Statistics behavior.
- Application compatibility.

---

## Cost Considerations

The cost of an index includes more than disk space.

Consider:

```text
Storage
+
Write amplification
+
WAL
+
Replication
+
Backup
+
Vacuum/maintenance
+
Migration time
+
Operational complexity
```

An index is justified when its workload benefit outweighs these costs.

For a high-volume write system, an index that saves:

```text
10 ms on a query executed 100 times/day
```

may not justify significant write overhead.

An index saving:

```text
2 seconds on a query executed 100,000 times/hour
```

may easily be worthwhile.

Think in workload economics, not isolated query latency.

---

## Security Considerations

Indexes are not an authorization mechanism.

Do not assume that because a query uses:

```sql
tenant_id
```

in an index, tenant isolation is enforced.

Authorization must still be expressed through:

- Query predicates.
- Application authorization.
- PostgreSQL Row-Level Security where appropriate.
- Database roles and privileges.

Indexes may also contain copies of sensitive indexed values.

Consider this when indexing:

```text
email
phone
national identifiers
tokens
other sensitive attributes
```

Indexes should be covered by the same database access, encryption, backup, and retention controls as the underlying database.

---

## Reliability Considerations

Indexes can become operational failure points when:

- An index is invalid.
- A migration fails.
- Index bloat becomes significant.
- Storage is exhausted.
- A critical query unexpectedly loses its access path.
- An index is dropped prematurely.

Production database monitoring should include schema health and storage headroom, not only query latency.

A failed index deployment should have a recovery procedure.

---

## Common Mistakes

### Indexing Every Column

More indexes do not mean a faster database.

They increase write and maintenance cost.

### Assuming Every Query Uses an Index

The optimizer may correctly choose a sequential scan.

### Creating an Index Without Examining the Query

Index the access pattern, not the column name.

### Ignoring Column Order

For composite indexes:

```text
(a, b)
```

and:

```text
(b, a)
```

are different access structures.

### Indexing Low-Cardinality Columns Blindly

A boolean or status column may not benefit from a standalone index.

Evaluate the complete workload.

### Ignoring Write Amplification

Every additional index affects writes and maintenance.

### Keeping Redundant Indexes Forever

Index duplication increases cost without necessarily improving reads.

### Dropping "Unused" Indexes Immediately

Statistics can be incomplete or reset, and rare critical queries may not appear in usage metrics.

### Assuming `CREATE INDEX CONCURRENTLY` Is Free

It reduces blocking but can take longer, consume resources, and complicate migrations.

### Building Large Indexes During Peak Traffic

Large index operations can compete for CPU, memory, I/O, and replication bandwidth.

### Forgetting ORM Migrations

A manually created index can disappear from a reproducible environment or drift from schema definitions.

### Using an Index as a Security Control

Indexes improve access paths; they do not enforce authorization.

### Optimizing Without `EXPLAIN (ANALYZE, BUFFERS)`

Without execution-plan evidence, index changes are often guesswork.

---

## Production Troubleshooting

When a query is slow despite an index:

```text
Slow query
   ↓
EXPLAIN (ANALYZE, BUFFERS)
   ↓
Is index used?
   ├── Yes
   │    ↓
   │  Is it actually selective?
   │    ↓
   │  Are estimates accurate?
   │    ↓
   │  Are joins/sorts/aggregation expensive?
   │
   └── No
        ↓
      Why?
        ├── Low selectivity
        ├── Small table
        ├── Wrong index shape
        ├── Predicate mismatch
        ├── Type/expression mismatch
        ├── Stale statistics
        └── Sequential scan is cheaper
```

Do not respond by immediately creating another index.

---

## Senior Index Design Framework

For every proposed index, answer:

1. Which production query requires it?
2. What predicate does it support?
3. What ordering does it support?
4. How selective is the predicate?
5. How large is the table?
6. How frequently does the query execute?
7. How frequently is the table written?
8. Which existing indexes overlap with it?
9. What storage will it consume?
10. What write amplification will it introduce?
11. Will it affect replication or backups?
12. How will it be deployed safely?
13. How will usage be measured?
14. When should it be reconsidered or removed?

A strong index proposal can be expressed as:

```text
Query
  ↓
Access pattern
  ↓
Candidate index
  ↓
EXPLAIN
  ↓
Benchmark
  ↓
Production rollout
  ↓
Monitor
```

---

## Practical Decision Matrix

| Situation | Likely choice |
|---|---|
| Primary-key lookup | Index |
| Highly selective equality filter | Usually index |
| Large-table keyset pagination | Usually index |
| Frequent tenant + time-range query | Often composite index |
| Rare query on tiny table | Often no index |
| Full-table reporting scan | Often no additional index |
| High-volume insert-only event table | Minimize indexes |
| Frequent prefix search | Consider B-tree |
| Arbitrary substring search | Consider trigram/full-text approach |
| Small active subset | Consider partial index |
| Case-insensitive lookup | Consider normalized value/expression index |
| Business uniqueness | Unique constraint/index |
| Repeated expensive query | Measure before indexing |
| Existing overlapping index | Review before adding another |

---

## Production Example

Suppose an API serves:

```http
GET /api/orders?tenant_id=42&limit=50
```

The query is:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

A candidate index is:

```sql
CREATE INDEX CONCURRENTLY idx_orders_tenant_created_id
ON orders (
    tenant_id,
    created_at DESC,
    id DESC
);
```

The reasoning is:

```text
tenant_id
    ↓
equality filter

created_at + id
    ↓
deterministic ordering

LIMIT 50
    ↓
small result set
```

For keyset pagination:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

the same index can support the cursor-based access pattern.

The index should still be validated with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

and production workload measurements.

---

## The No-Index Decision Is Also an Engineering Decision

Choosing not to create an index can be correct.

For example:

```text
events
10 billion rows
```

with:

```text
99% of workload = sequential ingestion
1% of workload = occasional full export
```

may not justify several indexes that slow every insert.

Likewise:

```text
configuration
200 rows
```

may not need an index on every column.

The correct decision considers the dominant workload.

---

## Indexes and the Read/Write Trade-Off

A useful mental model is:

```text
More indexes
    ↓
Faster selected reads
    +
More expensive writes
    +
More storage
    +
More maintenance

Fewer indexes
    ↓
Cheaper writes
    +
Less storage
    -
Potentially slower reads
```

The optimal point depends on:

```text
read/write ratio
+
query frequency
+
data size
+
latency requirements
+
availability requirements
+
infrastructure cost
```

---

## Key Takeaways

- **An index is an access path, not a guarantee of faster execution; PostgreSQL chooses between sequential, index, bitmap, and other plans based on estimated cost.**
- **Create indexes around real query patterns—filters, joins, ordering, pagination, and uniqueness—not simply because a column is frequently referenced.**
- **Indexes improve selected reads but increase storage, write amplification, WAL, replication, backup, and maintenance costs, making excessive indexing harmful for write-heavy systems.**
- **Use `EXPLAIN (ANALYZE, BUFFERS)`, production statistics, and workload measurements to validate indexes; do not assume an unused or missing index is automatically the root cause.**
- **Treat indexes as production schema components: deploy them safely, monitor their usage and health, review overlap periodically, and remove obsolete indexes only with evidence.**