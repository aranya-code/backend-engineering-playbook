# 19- Indexes for GROUP BY

## Overview

`GROUP BY` transforms multiple rows into groups and usually performs an aggregate operation such as `COUNT`, `SUM`, `AVG`, `MIN`, or `MAX`.

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total) AS revenue
FROM orders
GROUP BY customer_id;
```

The database must identify which rows belong to the same `customer_id` group and then compute the aggregates.

An index can sometimes make this work cheaper, particularly when the query also contains selective filtering:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

A candidate index might be:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

However, an important production principle is:

> **An index does not automatically make `GROUP BY` faster.**

Aggregation often requires scanning a substantial portion of the input, and a sequential scan followed by a hash or sort-based aggregation can be cheaper than traversing an index.

The correct index should therefore be derived from the complete query pattern and validated with the execution plan.

## How GROUP BY Works

Conceptually, a grouped query performs two major operations:

```text
Input rows
    ↓
Filter
    ↓
Group rows by key
    ↓
Compute aggregates
    ↓
Return grouped result
```

For:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

the database must transform:

```text
customer_id
------------
101
101
102
101
103
102
```

into logical groups:

```text
101 → 3 rows
102 → 2 rows
103 → 1 row
```

The database engine can use different aggregation strategies depending on the query and estimated cost.

Common strategies include:

- Hash aggregation.
- Sort-based aggregation.
- Group aggregation over already ordered input.
- Parallel aggregation.

## Hash Aggregation

Hash aggregation builds an in-memory hash table keyed by the grouping columns.

Conceptually:

```text
Rows
 ↓
Read row
 ↓
Hash GROUP BY key
 ↓
Lookup/create group
 ↓
Update aggregate
 ↓
Next row
```

For:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

the internal state may resemble:

```text
customer_id → count
-------------------
101         → 3
102         → 2
103         → 1
```

Hash aggregation is attractive when:

- The number of groups is manageable.
- Input does not need to be ordered.
- The hash table fits efficiently in memory.

An index is not necessarily useful here because the database can often read the table sequentially and build the hash table efficiently.

## Sort-Based Aggregation

Another approach is to sort rows by the grouping key:

```text
Input
 ↓
Sort by customer_id
 ↓
101
101
101
102
102
103
 ↓
Aggregate consecutive groups
```

If the input is already ordered by a suitable index, the database may be able to avoid or reduce the sorting work.

For example:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);
```

can provide rows ordered by `customer_id`.

A plan can potentially exploit that ordering for:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

But the optimizer may still prefer a sequential scan plus hash aggregation if that is cheaper.

## Group Aggregation Over Ordered Input

When rows arrive in grouping-key order, the database can process one group at a time:

```text
customer_id = 101
    ↓
aggregate
    ↓
customer_id = 102
    ↓
aggregate
    ↓
customer_id = 103
    ↓
aggregate
```

This can avoid maintaining a hash table for every group.

The advantage becomes more significant when:

- The grouping key is indexed.
- Input is already ordered.
- The number of groups is large.
- Memory pressure makes hashing expensive.

The database still decides whether this access path is beneficial.

## Indexes and GROUP BY

A B-tree index such as:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);
```

stores entries ordered by `customer_id`.

Conceptually:

```text
Index
────────────────────
101
101
101
102
102
103
103
104
...
```

That ordering can make grouped processing possible without independently sorting all input rows.

However, reading the entire index is not automatically cheaper than reading the table.

An index scan may require:

```text
Index page
   ↓
Heap/table page
   ↓
Index page
   ↓
Heap/table page
```

while a sequential scan can read table pages efficiently:

```text
Sequential table scan
        ↓
   contiguous I/O
        ↓
Aggregation
```

For large aggregations, sequential access is often highly competitive.

## GROUP BY With WHERE

The most useful index pattern is frequently:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

A candidate index is:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

This index provides:

```text
status
  ↓
customer_id
```

The database can potentially:

1. Locate rows for `status = 'completed'`.
2. Process those rows grouped by `customer_id`.
3. Compute the aggregates.

The index is therefore serving both filtering and grouping.

## Composite Index Column Order

Column order matters.

Compare:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

with:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

For:

```sql
WHERE status = 'completed'
GROUP BY customer_id
```

the first index is generally better aligned because it narrows the index using the equality predicate first and then provides ordering by the grouping column.

Conceptually:

```text
status = completed
        ↓
customer_id
        ↓
groups
```

The second index primarily organizes by `customer_id`:

```text
customer_id
        ↓
status
```

which may not provide the same efficient filtering behavior.

A useful starting heuristic is:

```text
Selective equality predicates
        ↓
Grouping/order requirements
        ↓
Additional payload columns
```

This is a design heuristic, not a guarantee. Always validate with real workload data.

## GROUP BY and Selectivity

Index usefulness depends heavily on how many rows survive the `WHERE` clause.

Consider:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

If:

```text
95% of orders are completed
```

then the index may not provide enough filtering benefit to justify an index scan.

If:

```text
2% of orders are completed
```

the index can potentially reduce the amount of data that needs to be processed substantially.

This is why cardinality and data distribution matter more than simply asking:

> "Is the GROUP BY column indexed?"

## GROUP BY With ORDER BY

A common query is:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
ORDER BY order_count DESC
LIMIT 20;
```

The grouping key is:

```text
customer_id
```

but the final ordering is:

```text
COUNT(*)
```

An index on:

```sql
customer_id
```

may help with the grouping stage but cannot generally provide the final ordering because `order_count` is computed during aggregation.

The execution conceptually becomes:

```text
orders
  ↓
GROUP BY customer_id
  ↓
COUNT(*)
  ↓
ORDER BY computed count
  ↓
LIMIT 20
```

This is an important distinction:

> **An index can help produce grouped input without necessarily eliminating a sort after aggregation.**

## GROUP BY Multiple Columns

Consider:

```sql
SELECT
    customer_id,
    status,
    COUNT(*)
FROM orders
GROUP BY customer_id, status;
```

A composite index:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

provides entries ordered by:

```text
customer_id
    ↓
status
```

This can potentially support grouping over both columns.

The order of grouping columns matters because:

```text
(customer_id, status)
```

and:

```text
(status, customer_id)
```

represent different index orderings.

If the query also filters by `status`, however, `(status, customer_id)` may be a better access path:

```sql
WHERE status = 'completed'
GROUP BY customer_id;
```

Index design should reflect the complete workload rather than the `GROUP BY` clause alone.

## GROUP BY and Covering Indexes

Suppose:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

An index containing:

```text
status
customer_id
```

may provide all columns required by the query.

In PostgreSQL:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

The database may be able to use an index-only scan when visibility information permits it.

For queries where additional non-grouping columns are required, PostgreSQL can use included columns:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id)
INCLUDE (total);
```

For example:

```sql
SELECT
    customer_id,
    COUNT(*),
    SUM(total)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

The additional column can potentially reduce heap access.

However, included columns increase index size and write overhead, so they should be justified by workload measurements.

## GROUP BY and COUNT

A common production query is:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id;
```

An index on:

```sql
customer_id
```

may help the database process groups in key order.

But there is no universal rule that this is faster than:

```text
Sequential Scan
      ↓
HashAggregate
```

For a large table with many rows, sequential reading plus hashing can be extremely efficient.

For a highly selective query:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY customer_id;
```

an index beginning with `created_at` may be more valuable because the index primarily reduces the input size.

## GROUP BY and SUM

Consider:

```sql
SELECT
    customer_id,
    SUM(total) AS revenue
FROM orders
GROUP BY customer_id;
```

An index on:

```sql
customer_id
```

provides grouping order but does not automatically eliminate access to `total`.

A PostgreSQL covering index could be:

```sql
CREATE INDEX idx_orders_customer_total
ON orders (customer_id)
INCLUDE (total);
```

This can potentially enable an index-only scan.

However, this is not automatically superior to a sequential scan.

For large analytical scans, the database may prefer reading the table directly because:

- Most rows are required.
- Sequential I/O is efficient.
- The index may be large.
- Heap access may dominate.
- Aggregation can be parallelized.

## GROUP BY and MIN/MAX

Some grouped queries can benefit significantly from appropriate indexes.

For example:

```sql
SELECT
    customer_id,
    MIN(created_at)
FROM orders
GROUP BY customer_id;
```

A composite index:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

orders records by:

```text
customer_id
    ↓
created_at
```

This gives the optimizer useful structure for grouped access.

However, whether the database can exploit the index to avoid processing most rows depends on the database engine, query shape, statistics, and available optimization strategies.

Do not assume that an index automatically turns every `MIN()` or `MAX()` aggregation into a constant-time lookup.

## GROUP BY and DISTINCT

`GROUP BY` and `DISTINCT` are related but have different semantics.

For:

```sql
SELECT DISTINCT customer_id
FROM orders;
```

an index on:

```sql
customer_id
```

can provide ordered values from which duplicates can be removed efficiently.

For:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

the database also needs to maintain aggregate state.

An index may help establish grouping order, but the aggregation itself remains necessary.

## Partial Indexes for GROUP BY Workloads

When the workload consistently targets a subset of rows, a partial index can be useful.

For example:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'pending'
GROUP BY customer_id;
```

PostgreSQL:

```sql
CREATE INDEX idx_orders_pending_customer
ON orders (customer_id)
WHERE status = 'pending';
```

This index contains only pending orders.

Advantages:

- Smaller index.
- Lower maintenance cost than a full equivalent index.
- Less storage.
- Potentially better cache efficiency.
- Faster access to the targeted subset.

The query predicate must be compatible with the index predicate for PostgreSQL to use the partial index.

## GROUP BY and Time Windows

Time-bounded aggregation is common in backend systems:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY customer_id;
```

A candidate index is:

```sql
CREATE INDEX idx_orders_created_customer
ON orders (created_at, customer_id);
```

Here the first column supports the time range.

However, because `created_at` is a range predicate rather than equality, the index's ability to directly provide global `customer_id` grouping order is limited.

This illustrates an important composite-index principle:

> **A range condition on an earlier index column can restrict how later columns can be exploited for ordering or grouping.**

The optimizer may still use the index because reducing the scanned rows is valuable.

## GROUP BY and Large Tables

For very large tables, aggregation can dominate query cost.

Consider:

```text
1 billion orders
        ↓
GROUP BY customer_id
        ↓
millions of groups
```

An index alone does not solve the fundamental amount of data that must be processed.

At this scale, consider:

- Partitioning.
- Pre-aggregation.
- Materialized views.
- Incremental aggregation.
- Data warehouses.
- Read replicas.
- Dedicated analytics systems.

For example, instead of repeatedly calculating:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

a system might maintain an aggregate table:

```text
customer_daily_metrics
----------------------
customer_id
date
order_count
revenue
```

The API can then aggregate a much smaller dataset.

Indexes remain useful, but architectural changes may provide a much larger improvement.

## Partitioning and GROUP BY

If data is partitioned by time:

```text
orders_2026_06
orders_2026_07
orders_2026_08
```

a query restricted to a recent period may allow partition pruning:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE created_at >= DATE '2026-08-01'
GROUP BY customer_id;
```

The database can potentially avoid scanning irrelevant partitions.

Within each partition, indexes may still be useful.

The optimization layers are therefore:

```text
Partition pruning
       ↓
Index filtering
       ↓
Aggregation
```

Do not treat partitioning and indexing as substitutes. They solve different problems.

## Execution Plans

Always inspect the execution plan before deciding that a `GROUP BY` index is necessary.

PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

Common plan nodes include:

| Plan node | Purpose |
|---|---|
| `Seq Scan` | Reads table sequentially |
| `Index Scan` | Traverses an index and fetches table rows |
| `Index Only Scan` | Reads required information from the index when possible |
| `Bitmap Index Scan` | Finds matching index entries |
| `Bitmap Heap Scan` | Fetches corresponding table pages |
| `HashAggregate` | Aggregates using a hash table |
| `GroupAggregate` | Aggregates ordered/grouped input |
| `Sort` | Orders input before grouping or final output |
| `Incremental Sort` | Sorts partially ordered input incrementally |
| `Gather` | Combines parallel worker results |
| `Partial HashAggregate` | Performs aggregation in parallel workers |

The important question is not:

> "Did PostgreSQL use my index?"

The better question is:

> "Did the selected plan reduce the total cost and latency for the production workload?"

## Memory and Spilling

Hash aggregation requires memory.

If the number of groups becomes large, the aggregation can exceed available working memory and spill intermediate data to disk.

For example:

```text
Large input
    ↓
HashAggregate
    ↓
Memory pressure
    ↓
Temporary I/O
    ↓
Higher latency
```

Monitoring temporary file activity and execution plans can reveal this class of problem.

Increasing memory settings can help in appropriate cases, but blindly increasing memory is not a complete solution. Query shape, indexes, data volume, concurrency, and aggregation cardinality must also be considered.

## Parallel Aggregation

Modern database engines can parallelize some aggregation workloads.

Conceptually:

```text
                 Table
                   ↓
        ┌──────────┼──────────┐
        ↓          ↓          ↓
     Worker 1   Worker 2   Worker 3
        ↓          ↓          ↓
     partial    partial    partial
     aggregate  aggregate  aggregate
        └──────────┼──────────┘
                   ↓
             Final aggregate
```

A sequential index traversal is not always preferable to a parallel table scan.

This is another reason not to assume that an index on the grouping column will always improve performance.

## Backend API Example

A reporting endpoint might execute:

```sql
SELECT
    status,
    COUNT(*) AS order_count,
    SUM(total) AS revenue
FROM orders
WHERE created_at >= $1
  AND created_at < $2
GROUP BY status;
```

A possible index is:

```sql
CREATE INDEX idx_orders_created_status
ON orders (created_at, status)
INCLUDE (total);
```

The index is primarily useful for the time-range filter.

The `status` column can also provide useful ordering information, but because `created_at` is a range predicate, the database may not be able to exploit the index as if `status` were the leading grouping key.

The correct plan should be verified with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    status,
    COUNT(*),
    SUM(total)
FROM orders
WHERE created_at >= TIMESTAMP '2026-08-01'
  AND created_at < TIMESTAMP '2026-09-01'
GROUP BY status;
```

## Django Example

Django can define an index for a common filtered aggregation:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.BigIntegerField()
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "customer_id"],
                name="idx_order_status_customer",
            ),
        ]
```

A query might be:

```python
from django.db.models import Count

results = (
    Order.objects
    .filter(status="completed")
    .values("customer_id")
    .annotate(order_count=Count("id"))
)
```

The ORM produces a grouped SQL query, but the database optimizer still decides whether the index is useful.

For performance-sensitive endpoints:

1. Inspect the generated SQL.
2. Run `EXPLAIN`.
3. Measure production-like data.
4. Validate after deployment.

## Common Mistakes and Pitfalls

### Assuming GROUP BY Automatically Benefits From an Index

An index on:

```sql
customer_id
```

does not guarantee a faster:

```sql
GROUP BY customer_id
```

A sequential scan plus hash aggregation may be cheaper.

**Avoid it:** compare execution plans and measured latency.

### Indexing Only the GROUP BY Column

For:

```sql
WHERE status = 'completed'
GROUP BY customer_id
```

an index only on:

```sql
customer_id
```

may not reduce the input set efficiently.

**Avoid it:** consider the filtering predicate and grouping requirement together.

### Ignoring Data Distribution

An index can look excellent on a small development database but become ineffective when the production distribution changes.

For example:

```text
Development:
status='completed' → 10%

Production:
status='completed' → 95%
```

The optimizer may reasonably choose completely different plans.

**Avoid it:** test with realistic cardinality and statistics.

### Creating Huge Covering Indexes

Adding every selected column to an index can make it unnecessarily large.

**Avoid it:** include only columns that provide a measurable benefit.

### Confusing GROUP BY With ORDER BY

An index that helps produce grouped input does not necessarily eliminate a later:

```sql
ORDER BY aggregate_value
```

For example:

```sql
GROUP BY customer_id
ORDER BY COUNT(*) DESC
```

requires ordering based on a computed aggregate.

### Ignoring Aggregation Cardinality

A query that produces:

```text
10 groups
```

is very different from one producing:

```text
10 million groups
```

Hash-table memory, sorting, and output volume can dominate performance.

### Assuming More Indexes Are Better

Every index adds:

- Storage.
- Write overhead.
- Maintenance work.
- Cache pressure.
- Backup and replication overhead.

**Avoid it:** maintain indexes based on observed workload value.

### Optimizing an Analytical Query With OLTP Indexes Alone

A query scanning hundreds of millions of rows is not necessarily fixable by adding another B-tree index.

**Avoid it:** consider partitioning, pre-aggregation, materialized views, or analytical storage when the workload requires large-scale aggregation.

## Production Considerations

### Measure Real Query Patterns

Start with the actual query:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

Capture:

- Execution time.
- Rows scanned.
- Rows returned.
- Buffer hits.
- Buffer reads.
- Temporary I/O.
- Aggregation strategy.
- Parallel workers.
- Memory usage where available.

### Watch Index Usage

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

An index with very low usage may be a candidate for removal, but usage statistics must be interpreted carefully.

An index might support an infrequent but business-critical query.

### Account for Write Costs

For a high-write `orders` table:

```text
INSERT
  ↓
table write
  +
index maintenance
  +
WAL
  +
replication
```

Adding several indexes solely to accelerate reporting can negatively affect transactional workloads.

Consider whether reporting should instead run against:

- Read replicas.
- Materialized views.
- Aggregation tables.
- Dedicated analytics infrastructure.

### Statistics Matter

The optimizer relies on statistics to estimate:

- Number of rows.
- Selectivity.
- Number of groups.
- Data distribution.

Outdated statistics can produce poor plans.

PostgreSQL maintenance operations such as `ANALYZE` help keep optimizer statistics current.

### High Availability

Indexes are part of the database state and therefore affect:

- Replication.
- Failover readiness.
- Backup size.
- Recovery time.
- Replica lag.

Large index creation or maintenance can create substantial I/O and WAL activity.

Treat major index changes as production migrations rather than harmless configuration changes.

## Security Considerations

Indexes do not enforce authorization.

For example, an API might execute:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE customer_id = $1
GROUP BY customer_id;
```

The index can make this query efficient, but the application must still verify that the authenticated caller is authorized to access that customer's data.

Use parameterized queries:

```sql
WHERE customer_id = $1
```

rather than dynamically concatenating user input into SQL.

Performance optimizations should never bypass:

- Tenant isolation.
- Authorization checks.
- Row-level security policies.
- Input validation.

## When to Use an Index for GROUP BY

An index is worth considering when one or more of these conditions apply:

| Situation | Index potential |
|---|---|
| `WHERE` greatly reduces input rows | High |
| `WHERE` + `GROUP BY` align with composite index | High |
| Query needs ordered grouped input | Potentially high |
| Query requires only indexed columns | Potentially high |
| Small `LIMIT` follows aggregation | Depends on query shape |
| Entire large table must be aggregated | Often limited |
| Very high-cardinality aggregation | Depends on memory and plan |
| Grouping without filtering | Often lower |
| Reporting scans most of a huge table | Consider analytical approaches |

The final decision should always come from execution plans and production measurements.

## Index Design Checklist

Before creating an index for a `GROUP BY` query, check:

- What columns appear in `WHERE`?
- Which predicates are equality predicates?
- Which predicates are ranges?
- Which columns are in `GROUP BY`?
- Is there an `ORDER BY` after aggregation?
- Is there a `LIMIT`?
- How many rows survive the filters?
- How many groups are expected?
- Can the query use an index-only scan?
- Would a partial index reduce index size?
- Is the table write-heavy?
- Could a sequential scan be cheaper?
- Could parallel aggregation be better?
- Are statistics current?
- Does the index benefit another important query?
- Has the change been tested with production-like data?

## Key Takeaways

- **An index does not automatically make `GROUP BY` faster; sequential scans with hash or parallel aggregation can be cheaper for large scans.**
- **Design composite indexes around the complete query, especially `WHERE` predicates followed by grouping requirements.**
- **Index ordering can provide grouped input, potentially avoiding sorting, but the optimizer decides whether that access path is actually cheaper.**
- **For large analytical aggregations, consider partitioning, pre-aggregation, materialized views, or dedicated analytics systems instead of relying solely on OLTP indexes.**
- **Validate every indexing decision with realistic data, `EXPLAIN (ANALYZE, BUFFERS)`, workload measurements, and the operational cost of maintaining the index.**