# 20- Indexes for Range Queries

## Overview

Range queries retrieve rows whose indexed value falls within an interval rather than matching a single value.

Common examples include:

```sql
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01'
```

```sql
WHERE price BETWEEN 100 AND 500
```

```sql
WHERE id > 100000
```

```sql
WHERE created_at >= NOW() - INTERVAL '24 hours'
```

Range queries are fundamental in backend systems because they appear in time-based APIs, pagination, reporting, event processing, billing, audit logs, and data retention workflows.

B-tree indexes are particularly well suited to ordered range predicates. The database can locate the beginning of the range and then traverse adjacent index entries instead of scanning every row in the table.

The important production question is not simply whether an index exists. It is whether the index reduces enough work to justify its lookup and maintenance cost.

## What Is a Range Query?

A range predicate selects values according to an ordering relationship:

| Predicate | Meaning |
|---|---|
| `column >= value` | Greater than or equal |
| `column > value` | Greater than |
| `column <= value` | Less than or equal |
| `column < value` | Less than |
| `BETWEEN a AND b` | Inclusive range |
| `column >= a AND column < b` | Half-open range |

For example:

```sql
SELECT id, customer_id, created_at
FROM orders
WHERE created_at >= TIMESTAMP '2026-08-01 00:00:00'
  AND created_at < TIMESTAMP '2026-09-01 00:00:00';
```

A B-tree index on `created_at` maintains values in sorted order:

```text
Index
────────────────────────────────────────────
2026-07-30
2026-07-31
2026-08-01  ← range begins
2026-08-01
2026-08-02
...
2026-08-31
2026-09-01  ← range ends
2026-09-02
```

The database can seek to the lower boundary and scan forward until the upper boundary.

## Why B-Tree Indexes Work Well for Ranges

A B-tree maintains keys in sorted order and provides logarithmic navigation to a particular key range.

Conceptually:

```text
                    Root
                     │
              ┌──────┴──────┐
              ↓             ↓
          Internal       Internal
           nodes           nodes
              │             │
              └──────┬──────┘
                     ↓
                  Leaf pages
                     │
         ┌───────────┼───────────┐
         ↓           ↓           ↓
       100         200          300
         →           →           →
```

For:

```sql
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01'
```

the database can approximately perform:

```text
Find first key >= 2026-08-01
             ↓
Traverse leaf pages
             ↓
Read matching entries
             ↓
Stop at 2026-09-01
```

This is fundamentally different from scanning every table row and evaluating the predicate individually.

## Basic Range Index

For a table such as:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    total NUMERIC(12, 2) NOT NULL
);
```

create:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

A query such as:

```sql
SELECT id, customer_id, total
FROM orders
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

can potentially use the index to restrict the scanned range.

## Selectivity Determines Whether the Index Helps

The most important factor is often how much of the table the range covers.

Suppose a table contains:

```text
100 million rows
```

A query for:

```text
one hour
```

might match:

```text
0.01% of rows
```

An index is highly attractive because it can avoid reading almost the entire table.

A query for:

```text
five years
```

might match:

```text
95% of rows
```

The index may no longer be the best access path.

The database could prefer:

```text
Sequential Scan
      ↓
Filter
```

rather than:

```text
Index Scan
      ↓
Many index entries
      ↓
Many table fetches
```

Therefore:

> **A range predicate does not imply an index scan. The optimizer chooses based on estimated total cost.**

## Index Scan vs Sequential Scan

Consider:

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-01-01';
```

If almost every row satisfies the condition, an index may provide little benefit.

The database has two broad choices:

```text
Index Scan
──────────
Index → matching row locations → table pages
```

or:

```text
Sequential Scan
───────────────
Table pages → evaluate predicate
```

The sequential scan may be faster because table pages can be read efficiently in physical order.

This is especially relevant when the query selects many columns and therefore needs frequent heap/table access.

## Range Queries With Additional Filters

Production queries commonly combine ranges with equality predicates.

For example:

```sql
SELECT id, customer_id, total
FROM orders
WHERE customer_id = 12345
  AND created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

A composite index is often appropriate:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

The index is organized conceptually as:

```text
customer_id
    ↓
created_at
```

The database can first locate:

```text
customer_id = 12345
```

and then scan only the relevant `created_at` range.

This is generally more targeted than an index only on `created_at` when customer-specific range queries are frequent.

## Equality Before Range

A common composite-index design principle is:

```text
Equality columns
        ↓
Range column
        ↓
Optional included/payload columns
```

For:

```sql
WHERE customer_id = ?
  AND created_at >= ?
  AND created_at < ?
```

a strong candidate is:

```sql
(customer_id, created_at)
```

because the index can narrow to a specific customer and then traverse the requested time interval.

Compare this with:

```sql
(created_at, customer_id)
```

The latter primarily narrows by time and then encounters customers within that time range.

Neither index is universally superior. The correct choice depends on query patterns, selectivity, workload, and whether other queries benefit from the same ordering.

## The Range Column and Later Index Columns

Consider:

```sql
CREATE INDEX idx_events_tenant_time_type
ON events (tenant_id, created_at, event_type);
```

and:

```sql
SELECT *
FROM events
WHERE tenant_id = 42
  AND created_at >= '2026-08-01'
  AND created_at < '2026-09-01'
  AND event_type = 'payment';
```

The index can efficiently narrow by:

```text
tenant_id = 42
        ↓
created_at range
```

But the presence of a range on `created_at` limits how effectively the later `event_type` key can be used for further ordered navigation.

This is one reason column order matters.

If `event_type` is highly selective and equality-filtered, an alternative may be:

```sql
CREATE INDEX idx_events_tenant_type_time
ON events (tenant_id, event_type, created_at);
```

Now the logical traversal is:

```text
tenant_id
    ↓
event_type
    ↓
created_at range
```

For this particular query pattern, this can provide a narrower range of index entries.

## Half-Open Time Ranges

For timestamp queries, prefer half-open intervals:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

rather than:

```sql
WHERE created_at BETWEEN $1 AND $2
```

when representing adjacent time windows.

For example:

```text
[2026-08-01 00:00, 2026-09-01 00:00)
```

contains everything from the start of August up to, but excluding, September.

This avoids ambiguity around fractional seconds and makes adjacent ranges naturally composable:

```text
[Aug 1, Sep 1)
[Sep 1, Oct 1)
```

There is no overlap and no missing boundary value.

## Range Queries and ORDER BY

A range index can often help with both filtering and ordering.

For:

```sql
SELECT id, created_at
FROM orders
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01'
ORDER BY created_at ASC;
```

an index on:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

matches both:

```text
WHERE created_at range
ORDER BY created_at
```

The database may therefore avoid a separate sort.

This becomes especially valuable when the query also uses:

```sql
LIMIT 100;
```

For example:

```sql
SELECT id, created_at
FROM orders
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01'
ORDER BY created_at ASC
LIMIT 100;
```

The database can potentially:

```text
Seek to range start
        ↓
Read ordered entries
        ↓
Return first 100 matches
        ↓
Stop
```

This is one of the strongest practical use cases for an ordered range index.

## Range Queries and Keyset Pagination

Range indexes are particularly useful for keyset pagination.

Instead of:

```sql
SELECT id, created_at
FROM orders
ORDER BY created_at, id
LIMIT 100 OFFSET 1000000;
```

use a cursor:

```sql
SELECT id, created_at
FROM orders
WHERE (created_at, id) > ($1, $2)
ORDER BY created_at, id
LIMIT 100;
```

with:

```sql
CREATE INDEX idx_orders_created_id
ON orders (created_at, id);
```

The database can seek directly to the cursor position.

Conceptually:

```text
Index
──────────────────────────────────
created_at + id
       ↓
cursor position
       ↓
next 100 rows
```

This avoids progressively larger `OFFSET` scans.

### Why the Tie-Breaker Matters

`created_at` may not be unique.

Suppose:

```text
created_at
----------------
10:00:00
10:00:00
10:00:00
10:01:00
```

Ordering only by `created_at` makes cursor pagination ambiguous.

Use:

```sql
ORDER BY created_at, id
```

and:

```sql
WHERE (created_at, id) > ($1, $2)
```

where `id` provides deterministic ordering.

## Descending Range Queries

For recent-first APIs:

```sql
SELECT id, created_at
FROM orders
WHERE created_at >= $1
  AND created_at < $2
ORDER BY created_at DESC
LIMIT 100;
```

A B-tree can generally be traversed in either direction.

The index:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

can potentially support both ascending and descending traversal.

An explicitly descending index can still be useful in some composite ordering patterns:

```sql
CREATE INDEX idx_orders_customer_created_desc
ON orders (customer_id, created_at DESC);
```

The important consideration is the complete ordering requirement rather than assuming that every descending query requires a separate descending index.

## Range Queries on Numeric Values

Ranges are not limited to timestamps.

For:

```sql
SELECT *
FROM products
WHERE price >= 100
  AND price < 500;
```

a B-tree index can be appropriate:

```sql
CREATE INDEX idx_products_price
ON products (price);
```

Other common numeric ranges include:

- IDs.
- Sequence numbers.
- Account balances.
- Scores.
- Quantities.
- Version numbers.
- Geographic coordinates in limited use cases.

The same selectivity and cost considerations apply.

## Range Queries on IDs

Sequential identifiers are frequently queried using ranges:

```sql
SELECT *
FROM events
WHERE id > 90000000
ORDER BY id
LIMIT 1000;
```

If `id` is a primary key backed by a B-tree index, the index already provides the required ordering.

The database can seek to:

```text
id = 90,000,001
```

and read forward.

This pattern is useful for:

- Batch processing.
- Data migration.
- Backfills.
- Event consumers.
- Administrative tooling.
- Incremental exports.

For high-volume batch processing, range-based iteration is often preferable to repeatedly using large offsets.

## Sargable Range Predicates

A predicate is **sargable** when the database can use the indexed column directly to constrain an index scan.

Good:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

Potentially problematic:

```sql
WHERE DATE(created_at) = $1
```

The function transforms the indexed value before comparison.

Instead, rewrite the query as a range:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

For example, to retrieve one day:

```text
[2026-08-31 00:00:00, 2026-09-01 00:00:00)
```

This allows a normal B-tree index on `created_at` to be used naturally.

## Expressions and Functional Indexes

Sometimes a function is unavoidable.

For:

```sql
WHERE lower(email) = 'user@example.com'
```

an ordinary index on:

```sql
email
```

may not directly support the transformed expression.

A functional index can address that:

```sql
CREATE INDEX idx_users_lower_email
ON users (lower(email));
```

For range queries, the same principle applies.

If a query consistently uses a deterministic expression, an expression index may be appropriate, but it should be introduced based on actual workload requirements.

## Date Range Queries

For backend reporting:

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(total) AS revenue
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

an index on:

```sql
created_at
```

is a natural candidate.

However, if the report scans 80% of the table, the optimizer may still choose a sequential scan.

For very large time-series tables, consider combining indexes with:

- Partitioning by time.
- Partition pruning.
- Retention policies.
- Pre-aggregation.
- Materialized views.
- BRIN indexes in PostgreSQL when physical row order correlates strongly with time.

## B-Tree vs BRIN for Large Time-Series Tables

PostgreSQL provides BRIN indexes that summarize ranges of physical table pages.

For append-heavy tables such as:

```text
events
created_at
```

where rows are physically correlated with insertion time, a BRIN index can be dramatically smaller than a B-tree.

Conceptually:

```text
Table pages
──────────────────────────────
Pages 1–128    → Jan
Pages 129–256  → Feb
Pages 257–384  → Mar
```

A BRIN index stores summaries for page ranges rather than every row.

For:

```sql
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01'
```

it can identify relevant page ranges.

BRIN is attractive when:

- Tables are very large.
- Values correlate with physical row order.
- Queries commonly use broad ranges.
- A tiny index footprint is valuable.

B-tree is generally better for highly selective random lookups and precise range access.

## Range Queries and Partitioning

For extremely large time-based tables, partitioning can reduce the amount of data considered before indexing.

Example:

```text
orders
├── orders_2026_06
├── orders_2026_07
├── orders_2026_08
└── orders_2026_09
```

A query for August:

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01';
```

can potentially benefit from partition pruning.

The optimization layers become:

```text
Query
  ↓
Partition pruning
  ↓
Relevant partition(s)
  ↓
Index range scan or sequential scan
  ↓
Rows
```

Partitioning does not replace indexing. It reduces the amount of data that needs to be considered, while an index can reduce work within the selected partition.

## Covering Indexes for Range Queries

Consider:

```sql
SELECT id, customer_id, total
FROM orders
WHERE created_at >= $1
  AND created_at < $2
ORDER BY created_at
LIMIT 100;
```

A PostgreSQL index might be:

```sql
CREATE INDEX idx_orders_created_covering
ON orders (created_at)
INCLUDE (customer_id, total);
```

This can potentially support an index-only scan.

Advantages include:

- Less heap access.
- Reduced random I/O.
- Efficient retrieval for frequently executed endpoints.

Limitations include:

- Larger index size.
- Higher write overhead.
- Additional vacuum/visibility considerations in PostgreSQL.
- More expensive index maintenance.

Do not add columns merely because they appear in `SELECT`. Confirm that avoiding heap access provides a measurable benefit.

## Partial Indexes for Range Workloads

Suppose an application frequently retrieves active records:

```sql
SELECT id, customer_id, created_at
FROM jobs
WHERE status = 'pending'
  AND created_at < NOW();
```

A PostgreSQL partial index can reduce index size:

```sql
CREATE INDEX idx_jobs_pending_created
ON jobs (created_at)
WHERE status = 'pending';
```

The index contains only rows satisfying the predicate.

This can be effective when:

- The indexed subset is small.
- The predicate is stable and common.
- The query pattern is well understood.

Be careful with predicates involving changing expressions such as `NOW()`. Index predicates have database-specific rules and should not be designed as though the index dynamically re-evaluates every row's membership on every query.

## NULL Values and Ranges

Range predicates interact with `NULL` through SQL's three-valued logic.

For:

```sql
WHERE created_at >= $1
```

rows where:

```text
created_at IS NULL
```

do not satisfy the predicate.

If `NULL` has semantic significance, explicitly model the required behavior.

For example:

```sql
WHERE created_at IS NULL
   OR created_at >= $1
```

The resulting access path can be different from a simple range scan.

Do not assume that adding `IS NULL` to a range query preserves the same execution plan.

## Range Queries and Data Types

Use appropriate data types for indexed values.

For timestamps:

```sql
TIMESTAMPTZ
```

is often appropriate for event times in distributed systems because it represents an absolute point in time while PostgreSQL handles timezone conversion semantics.

Avoid storing timestamps as strings such as:

```text
"2026-08-31T14:00:00Z"
```

when the database needs to perform temporal filtering and ordering.

Proper types provide:

- Correct comparison semantics.
- Appropriate operator behavior.
- Better optimizer statistics.
- More reliable index usage.

## Time Zones and Range Boundaries

Application code should define time boundaries consistently.

A common backend pattern is:

```text
API request
   ↓
Parse client time zone
   ↓
Resolve calendar boundary
   ↓
Convert to UTC/absolute timestamps
   ↓
Query database using half-open range
```

For example:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

The application should calculate `$1` and `$2` correctly rather than applying timezone conversion functions to the indexed column for every row.

Avoid:

```sql
WHERE DATE(created_at AT TIME ZONE 'Asia/Kolkata') = $1
```

for a high-volume indexed query when the same requirement can be expressed as precomputed UTC boundaries.

## Range Queries in Django

A Django query:

```python
orders = (
    Order.objects
    .filter(
        created_at__gte=start,
        created_at__lt=end,
    )
    .order_by("created_at", "id")[:100]
)
```

can map naturally to a range predicate.

A matching index might be:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(
                fields=["created_at", "id"],
                name="idx_order_created_id",
            ),
        ]
```

For customer-specific pagination:

```python
orders = (
    Order.objects
    .filter(
        customer_id=customer_id,
        created_at__gte=start,
        created_at__lt=end,
    )
    .order_by("created_at", "id")[:100]
)
```

a composite index beginning with `customer_id` may be more appropriate:

```python
models.Index(
    fields=["customer_id", "created_at", "id"],
    name="idx_order_customer_created_id",
)
```

The actual index should be chosen from the application's query workload rather than from ORM syntax alone.

## Execution Plan Analysis

Use the database's execution plan to validate the index.

PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, customer_id, total
FROM orders
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01'
ORDER BY created_at
LIMIT 100;
```

Look for:

- `Index Scan`.
- `Index Only Scan`.
- Estimated versus actual rows.
- `Rows Removed by Filter`.
- Buffer hits and reads.
- Sort operations.
- Execution time.
- Whether the index is scanning a large fraction of the table.

A plan such as:

```text
Limit
  -> Index Scan using idx_orders_created_at
```

can be excellent for a selective range with a small `LIMIT`.

A plan such as:

```text
Seq Scan
  -> Sort
```

is not automatically bad. It may be cheaper for a broad range.

## Statistics and Cardinality

The optimizer needs accurate statistics to estimate how many rows satisfy a range.

Suppose the database estimates:

```text
1,000 matching rows
```

but reality is:

```text
10,000,000 matching rows
```

The optimizer might select an index scan expecting a small number of table fetches, only to discover that the range is enormous.

This can produce severe performance regressions.

Keep statistics current and investigate plans where:

```text
estimated rows ≠ actual rows
```

especially for columns with:

- Skewed distributions.
- Rapidly changing values.
- Correlated columns.
- Time-dependent workloads.

## Common Mistakes and Pitfalls

### Wrapping the Indexed Column in a Function

Avoid:

```sql
WHERE DATE(created_at) = $1
```

when a range can express the same condition.

Prefer:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

This preserves direct use of the indexed column.

### Using `BETWEEN` Carelessly With Timestamps

Avoid ambiguous adjacent boundaries such as:

```sql
BETWEEN '2026-08-01' AND '2026-08-31'
```

when timestamps include times and fractional seconds.

Prefer:

```sql
created_at >= '2026-08-01'
AND created_at < '2026-09-01'
```

### Assuming Every Range Uses an Index

A range covering most of the table may be cheaper with a sequential scan.

### Putting the Range Column Too Early

For:

```sql
WHERE tenant_id = ?
  AND status = ?
  AND created_at >= ?
```

blindly creating:

```sql
(created_at, tenant_id, status)
```

may not be the best design.

A common candidate is:

```sql
(tenant_id, status, created_at)
```

because equality predicates narrow the index before the range.

The correct order still depends on the broader workload.

### Ignoring ORDER BY

An index can provide both filtering and ordering.

Failing to consider the `ORDER BY` can result in unnecessary sorting or an index design that misses an important optimization.

### Using OFFSET for Deep Pagination

Avoid:

```sql
LIMIT 100 OFFSET 10000000
```

for high-volume APIs.

Prefer keyset pagination using an indexed cursor.

### Building a Giant Covering Index

Including many columns increases:

- Storage.
- Write cost.
- Cache pressure.
- Vacuum/maintenance work.
- Backup and replication overhead.

### Ignoring Data Distribution

A query selecting 1% of rows may strongly benefit from an index while the same query pattern selecting 80% may not.

### Ignoring Physical Correlation

For huge append-only time-series tables, a BRIN index may be more appropriate than a large B-tree when indexed values correlate strongly with physical row order.

### Forgetting Operational Costs

Indexes must be maintained during:

```text
INSERT
UPDATE
DELETE
```

A range-query optimization can therefore increase write latency and storage requirements.

## Production Considerations

### Design Indexes Around Query Shapes

Start with real queries:

```text
WHERE
GROUP BY
ORDER BY
LIMIT
JOIN
```

rather than creating indexes independently for individual columns.

For example:

```sql
WHERE tenant_id = ?
  AND created_at >= ?
  AND created_at < ?
ORDER BY created_at, id
LIMIT 100
```

suggests evaluating:

```sql
(tenant_id, created_at, id)
```

as a candidate index.

### Monitor Query Latency

Track:

- P50 latency.
- P95 latency.
- P99 latency.
- Rows scanned.
- Rows returned.
- Buffer reads.
- Temporary I/O.
- Query frequency.

A query executed 100,000 times per minute deserves different optimization priorities than an administrative report executed once per day.

### Monitor Index Usage

PostgreSQL:

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY idx_scan DESC;
```

Low usage does not automatically mean an index should be removed. An infrequent but critical query can justify an otherwise rarely used index.

### Consider Write Amplification

For a high-throughput event table:

```text
INSERT
  ↓
Heap/table write
  +
B-tree maintenance
  +
WAL
  +
Replication
```

Every additional index can increase the cost of writes.

### Large Index Creation

Creating an index on a large production table can consume substantial:

- CPU.
- Memory.
- Disk I/O.
- Storage.
- WAL.
- Replication bandwidth.

PostgreSQL provides:

```sql
CREATE INDEX CONCURRENTLY idx_orders_created_at
ON orders (created_at);
```

which is designed to reduce blocking of normal writes compared with a standard index build, but it still consumes significant resources and has operational trade-offs.

Test index migrations against production-scale data and plan for monitoring.

### Read Replicas and Reporting

If broad range queries are primarily analytical:

```text
Application
    ↓
Primary DB
    ↓
Replication
    ↓
Read replica
    ↓
Reporting workload
```

moving reporting traffic to a replica can protect transactional workloads.

A replica does not eliminate the need for appropriate indexes, but it can isolate resource contention.

### Partitioning

For very large time-based datasets, partitioning can reduce the amount of data considered by a query.

Use:

```text
partition pruning
+
appropriate local indexes
```

rather than treating partitioning as a replacement for indexing.

## Interview Traps

### "B-Tree Is O(log n), So Range Queries Are O(log n)"

This is incomplete.

Finding the beginning of a range can be approximately logarithmic, but retrieving `k` matching entries requires additional work.

A more useful model is:

```text
Seek to range start: O(log n)
+
Read matching entries: O(k)
```

So a broad range can still be expensive.

### "An Index Makes Any WHERE Clause Fast"

False.

Index usefulness depends on:

- Selectivity.
- Data distribution.
- Predicate shape.
- Table size.
- Required columns.
- Query ordering.
- Cache state.
- Optimizer estimates.

### "Put the Most Selective Column First"

This is an oversimplification.

For composite indexes, equality predicates, range predicates, ordering requirements, join patterns, and workload frequency all matter.

"Most selective first" is not a universal indexing rule.

### "Every Timestamp Column Needs an Index"

False.

An index should exist because a workload benefits from it, not because the column contains timestamps.

### "OFFSET and Range Pagination Are Equivalent"

They are not.

Deep `OFFSET` pagination may require scanning and discarding a large number of rows.

Keyset pagination can seek directly to an indexed cursor position.

## Practical Design Checklist

Before adding an index for a range query, verify:

- Is the predicate sargable?
- How selective is the range?
- How many rows are expected to match?
- Is there an equality predicate that should precede the range column?
- Is there an `ORDER BY`?
- Is there a `LIMIT`?
- Can the same index support keyset pagination?
- Are multiple columns involved in the cursor?
- Could a covering index eliminate heap access?
- Would a partial index reduce the index size?
- Would BRIN be more appropriate for a very large time-series table?
- Would partition pruning reduce the data volume?
- Is the table write-heavy?
- Is the query latency-sensitive?
- Are optimizer statistics current?
- What does `EXPLAIN (ANALYZE, BUFFERS)` show?
- What is the index's storage and maintenance cost?

## Key Takeaways

- **B-tree indexes are well suited to ordered range predicates because the database can seek to a range boundary and traverse adjacent index entries.**
- **Composite indexes commonly place equality predicates before range columns, but the complete `WHERE`, `ORDER BY`, pagination, and workload pattern must determine column order.**
- **A range query can still be expensive when it matches a large fraction of the table; the optimizer may correctly prefer a sequential scan.**
- **Use sargable half-open timestamp ranges and keyset pagination to preserve efficient index access and predictable performance.**
- **For very large time-series workloads, combine indexing with partitioning, BRIN indexes, pre-aggregation, or other architectural techniques when a B-tree alone is insufficient.**