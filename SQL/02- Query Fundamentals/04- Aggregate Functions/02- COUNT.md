# 02- COUNT

## Overview

`COUNT` is an aggregate function used to determine how many rows or non-NULL values exist in a result set. It is one of the most frequently used SQL aggregates in backend systems because counts drive pagination metadata, dashboards, reporting, validation, monitoring, billing, and business metrics.

The most important distinction is between:

```sql
COUNT(*)
COUNT(column)
COUNT(DISTINCT column)
```

They answer different questions:

| Expression | Counts | NULL behavior |
|---|---|---|
| `COUNT(*)` | Rows in the input result | Counts every qualifying row |
| `COUNT(column)` | Non-NULL values in a column | Ignores NULL |
| `COUNT(DISTINCT column)` | Unique non-NULL values | Ignores NULL |

Understanding this distinction is essential because an incorrect `COUNT` can produce silently incorrect application metrics.

## Basic Syntax

```sql
COUNT(*)
COUNT(column_name)
COUNT(DISTINCT column_name)
```

It is normally used together with `SELECT`:

```sql
SELECT COUNT(*) AS order_count
FROM orders;
```

The result is a single row containing the calculated count.

## COUNT(*) — Count Rows

`COUNT(*)` counts every row that qualifies for the query.

```sql
SELECT COUNT(*) AS order_count
FROM orders;
```

With filtering:

```sql
SELECT COUNT(*) AS paid_orders
FROM orders
WHERE status = 'paid';
```

The `WHERE` clause determines which rows enter the aggregation. `COUNT(*)` then counts those rows.

For example:

```text
orders
+----+--------+
| id | status |
+----+--------+
| 1  | paid   |
| 2  | paid   |
| 3  | failed |
| 4  | paid   |
+----+--------+
```

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'paid';
```

Result:

```text
3
```

### Why `COUNT(*)` Is Usually the Correct Row Count

When the requirement is:

> How many rows satisfy this query?

use:

```sql
COUNT(*)
```

Do not use an arbitrary nullable column as a proxy for row count:

```sql
COUNT(customer_id)
```

unless the requirement specifically means:

> How many qualifying rows have a non-NULL `customer_id`?

This distinction becomes particularly important in production schemas where nullable columns are common.

## COUNT(column) — Count Non-NULL Values

`COUNT(column)` counts only rows where the specified expression evaluates to a non-NULL value.

Consider:

```text
orders
+----+-------------+
| id | customer_id |
+----+-------------+
| 1  | 101         |
| 2  | NULL        |
| 3  | 102         |
| 4  | NULL        |
+----+-------------+
```

Then:

```sql
SELECT COUNT(*) AS rows,
       COUNT(customer_id) AS customers_present
FROM orders;
```

Result:

```text
rows | customers_present
-----+------------------
4    | 2
```

`COUNT(customer_id)` therefore measures populated values, not rows.

### When COUNT(column) Is Useful

It is appropriate when NULL has business meaning.

For example:

```sql
SELECT COUNT(shipped_at) AS shipped_orders
FROM orders;
```

If `shipped_at` is NULL until an order is shipped, this counts orders that have actually been shipped.

The query is effectively asking:

> How many qualifying rows have a shipping timestamp?

That is different from counting all orders.

## COUNT(DISTINCT column)

`COUNT(DISTINCT column)` counts unique non-NULL values.

```sql
SELECT COUNT(DISTINCT customer_id) AS unique_customers
FROM orders;
```

If a customer has placed multiple orders, that customer contributes only once.

Example:

```text
customer_id
-----------
101
101
102
103
103
NULL
```

```sql
COUNT(*)                  → 6
COUNT(customer_id)       → 5
COUNT(DISTINCT customer_id) → 3
```

This distinction is critical for metrics such as:

- Unique customers
- Unique users
- Unique devices
- Unique tenants
- Unique IP addresses
- Unique sessions

## COUNT with GROUP BY

`COUNT` becomes particularly useful with `GROUP BY`.

```sql
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY status;
```

Example result:

```text
status      | order_count
------------+------------
pending     | 120
paid        | 850
shipped     | 730
cancelled   | 45
```

Each group produces its own count.

### Grouping by Multiple Dimensions

```sql
SELECT
    tenant_id,
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY tenant_id, status;
```

The result contains one count for each unique `(tenant_id, status)` combination.

This pattern is common in multi-tenant systems where metrics must be isolated by tenant.

## COUNT with WHERE

`WHERE` filters rows before aggregation.

```sql
SELECT COUNT(*) AS recent_orders
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

The half-open interval:

```text
[start_time, end_time)
```

is generally preferable for time-based queries because adjacent windows do not overlap.

For example:

```text
2026-08-01 00:00:00 <= created_at < 2026-09-01 00:00:00
```

This avoids ambiguity around the final timestamp of a month.

## COUNT with HAVING

`HAVING` filters groups after aggregation.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

This means:

> Return customers who have at least 10 orders.

The distinction is:

```text
WHERE
  ↓
filter rows
  ↓
GROUP BY
  ↓
COUNT
  ↓
HAVING
  ↓
filter groups
```

Do not replace a row-level filter with `HAVING` unnecessarily.

## COUNT and NULL

NULL behavior is one of the most common `COUNT` interview and production traps.

Consider:

```text
value
-----
10
20
NULL
30
NULL
```

Then:

```sql
COUNT(*)       → 5
COUNT(value)   → 3
```

For distinct values:

```sql
COUNT(DISTINCT value) → 3
```

The NULL value is not counted by `COUNT(column)` or `COUNT(DISTINCT column)`.

### COUNT of an Expression

`COUNT` can also operate on expressions:

```sql
SELECT COUNT(email) AS users_with_email
FROM users;
```

Or:

```sql
SELECT COUNT(NULLIF(status, 'inactive')) AS active_or_non_inactive
FROM users;
```

The important rule is that `COUNT(expression)` counts rows for which the expression evaluates to non-NULL.

This makes expressions useful for conditional counting, although modern SQL also provides clearer constructs such as `FILTER` in PostgreSQL.

## Conditional Counting

A common backend requirement is to calculate several counts in one query.

In PostgreSQL, a clear approach is:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'paid') AS paid_orders,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders
FROM orders;
```

This returns multiple metrics from the same input relation.

For databases without `FILTER`, conditional aggregation can commonly be expressed with `CASE`:

```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_orders,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_orders
FROM orders;
```

The exact syntax and optimizer behavior depend on the database engine.

## COUNT and JOINs

`COUNT` becomes dangerous when joins change row cardinality.

Consider:

```sql
SELECT
    c.id,
    COUNT(*) AS order_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Here, each matching order contributes one joined row.

However, joining another one-to-many relation can multiply rows:

```text
customer
   │
   ├── orders
   │
   └── payments
```

If a customer has:

```text
3 orders
2 payments
```

a naive join can produce:

```text
3 × 2 = 6 joined rows
```

Then:

```sql
COUNT(*)
```

may return `6` instead of the intended `3`.

### COUNT(DISTINCT) as a Correctness Tool

If the business question is:

> How many distinct orders are associated with this customer?

you may need:

```sql
COUNT(DISTINCT o.id)
```

For example:

```sql
SELECT
    c.id,
    COUNT(DISTINCT o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN payments AS p
    ON p.order_id = o.id
GROUP BY c.id;
```

However, `COUNT(DISTINCT ...)` should not automatically be used to hide an incorrect join.

A better design may be to aggregate each one-to-many relationship separately before joining.

## COUNT and LEFT JOIN

`LEFT JOIN` is important when you need to include entities with zero related rows.

For example:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Using:

```sql
COUNT(o.id)
```

allows customers with no orders to produce:

```text
order_count = 0
```

This is different from:

```sql
COUNT(*)
```

because the `LEFT JOIN` still produces one result row for a customer even when no order exists.

For a customer with no matching order:

```text
COUNT(*)   → 1
COUNT(o.id) → 0
```

This is a classic SQL interview trap.

## COUNT and DISTINCT Performance

`COUNT(DISTINCT ...)` can be substantially more expensive than `COUNT(*)`.

The database may need to:

- Sort values
- Build a hash structure
- Deduplicate values
- Consume significant memory
- Spill intermediate data to disk
- Process a large number of rows

For example:

```sql
SELECT COUNT(DISTINCT user_id)
FROM events
WHERE created_at >= :start_time;
```

can become expensive on a high-volume events table.

Before optimizing, inspect the execution plan and measure the actual workload.

In PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(DISTINCT user_id)
FROM events
WHERE created_at >= :start_time;
```

Use `EXPLAIN ANALYZE` carefully on production systems because it executes the query.

## Indexes and COUNT

Indexes can help count queries, but there is no universal rule that an index makes `COUNT` fast.

For a selective predicate:

```sql
SELECT COUNT(*)
FROM orders
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time;
```

an index beginning with the filtering columns may reduce the amount of data that must be processed.

For example:

```sql
CREATE INDEX idx_orders_tenant_created_at
ON orders (tenant_id, created_at);
```

Whether this index is beneficial depends on:

- Table size
- Predicate selectivity
- Data distribution
- Visibility requirements
- Existing indexes
- Query frequency
- Write workload
- Database engine

Always validate index changes against real execution plans.

## COUNT(*) and Database Implementation

At the SQL semantic level, `COUNT(*)` means:

> Count every row in the input relation.

It does not mean:

> Read one particular column.

A database optimizer may choose different physical strategies depending on the query and engine. For example, an engine can potentially use an index, sequential scan, parallel execution, or other optimized mechanisms.

Do not assume that:

```sql
COUNT(id)
```

is faster than:

```sql
COUNT(*)
```

merely because `id` is indexed.

For ordinary row counting, `COUNT(*)` communicates the intent more accurately.

## COUNT and Pagination

Pagination APIs frequently need both the current page and the total number of matching records.

For example:

```sql
SELECT COUNT(*) AS total
FROM orders
WHERE tenant_id = :tenant_id
  AND status = 'paid';
```

The API might return:

```json
{
  "items": [],
  "total": 12500
}
```

This is straightforward with offset pagination but can become expensive for very large datasets because the database must calculate the total.

For keyset or cursor pagination, a total count is often unnecessary. The API can instead expose:

```json
{
  "items": [],
  "next_cursor": "..."
}
```

This avoids making total-count calculation a mandatory part of every page request.

## COUNT in Django

Django exposes database counting through `count()`:

```python
order_count = Order.objects.filter(
    tenant_id=tenant_id,
    status="paid",
).count()
```

For grouped counts:

```python
from django.db.models import Count

orders_by_status = (
    Order.objects
    .filter(tenant_id=tenant_id)
    .values("status")
    .annotate(order_count=Count("id"))
)
```

When using Django ORM, understand whether `count()` is counting rows, joined rows, or distinct values based on the generated SQL.

For complex queries, inspect the generated SQL and execution plan rather than assuming ORM abstractions preserve the intended cardinality.

## COUNT in API Design

A count endpoint might be implemented in a service layer:

```python
def count_paid_orders(tenant_id: int) -> int:
    return (
        Order.objects
        .filter(
            tenant_id=tenant_id,
            status="paid",
        )
        .count()
    )
```

Production considerations include:

- Ensure tenant filters cannot be bypassed.
- Avoid counting an unbounded historical dataset on every request.
- Cache only when stale results are acceptable.
- Avoid exposing counts that reveal information across authorization boundaries.
- Define whether soft-deleted records are included.
- Define whether cancelled or refunded records count toward the metric.

## COUNT and Transaction Consistency

Counts are evaluated against the database state visible to the statement or transaction according to the database's isolation semantics.

This matters when the application performs:

```text
COUNT matching rows
        ↓
fetch matching rows
```

as separate queries.

Another transaction may insert or delete rows between the two operations.

Therefore, a response containing:

```json
{
  "total": 100,
  "items": [...]
}
```

does not automatically mean that `items` represent exactly the same snapshot as the count.

For APIs where exact snapshot consistency matters, consider the database transaction and isolation requirements explicitly.

## Large-Scale Systems

Exact counts can become expensive on very large tables.

For example:

```sql
SELECT COUNT(*)
FROM events;
```

may require substantial work because the database must determine the exact number of qualifying rows.

At scale, alternatives may include:

- Maintaining summary tables
- Incremental counters
- Materialized views
- Read replicas
- Analytical databases
- Approximate cardinality algorithms where exactness is unnecessary

Do not replace exact counts with approximate values unless the business requirement explicitly permits approximation.

For example:

```text
"Exactly 1,842,311 users"
```

has different requirements from:

```text
"Approximately 1.8M users"
```

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Using `COUNT(column)` to count rows | NULL values are excluded | Use `COUNT(*)` |
| Using `COUNT(*)` after a `LEFT JOIN` | The outer row itself is counted | Count a nullable child key such as `COUNT(o.id)` |
| Assuming `COUNT(DISTINCT)` is always necessary | It can add significant computation | Use it only when uniqueness is part of the requirement |
| Using `DISTINCT` to hide bad joins | Incorrect cardinality remains | Fix the join relationship |
| Forgetting NULL behavior | Metrics become incorrect | Explicitly define NULL semantics |
| Counting joined rows without checking cardinality | One-to-many joins can multiply rows | Validate the relationship before aggregating |
| Running exact counts on huge datasets for every request | High database load | Cache, pre-aggregate, or redesign the API where appropriate |
| Assuming an index guarantees fast `COUNT` | The optimizer may choose another plan | Validate with `EXPLAIN` |
| Treating count and page results as one snapshot | Separate queries can observe different states | Use appropriate transaction semantics |
| Exposing counts across tenant boundaries | Can leak protected information | Apply authorization and tenant filters consistently |

## Interview Traps

### `COUNT(*)` vs `COUNT(column)`

```sql
SELECT COUNT(*), COUNT(email)
FROM users;
```

If three users exist and one has a NULL email:

```text
COUNT(*)      → 3
COUNT(email)  → 2
```

### LEFT JOIN Counting

Given:

```sql
SELECT
    c.id,
    COUNT(*)
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

A customer with no orders still produces one joined row, so `COUNT(*)` returns `1`.

To count orders:

```sql
COUNT(o.id)
```

returns `0`.

### COUNT(DISTINCT)

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

counts customers, not orders.

The business noun being counted should always be clear before choosing the expression.

## Production Checklist

Before shipping a `COUNT` query, verify:

- [ ] Am I counting rows, populated values, or unique values?
- [ ] Is NULL behavior intentional?
- [ ] Can a JOIN multiply rows?
- [ ] Should `COUNT(*)` or `COUNT(child.id)` be used?
- [ ] Is `DISTINCT` actually required?
- [ ] Is the filter selective enough for the expected workload?
- [ ] Has the query been tested with production-scale data?
- [ ] Does the execution plan match expectations?
- [ ] Is an exact count actually required by the API?
- [ ] Could repeated counting become a database bottleneck?
- [ ] Are tenant and authorization filters applied?
- [ ] Is count consistency with the returned data important?

## Key Takeaways

- `COUNT(*)` counts qualifying rows, while `COUNT(column)` counts only non-NULL values and `COUNT(DISTINCT column)` counts unique non-NULL values.
- `LEFT JOIN` cardinality makes `COUNT(*)` particularly error-prone; count a nullable child key when the requirement is to count related records.
- `COUNT(DISTINCT ...)` is a correctness tool when uniqueness is required, but it can be significantly more expensive than ordinary row counting.
- Aggregation correctness depends on join cardinality, NULL semantics, filtering, transaction consistency, and the exact business entity being counted.
- At large scale, exact counts can become expensive; use execution plans, appropriate indexes, pre-aggregation, caching, or alternative API designs based on actual requirements.