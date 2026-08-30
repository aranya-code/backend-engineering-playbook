# 06- CASE with Aggregation

## Overview

`CASE` and aggregate functions are frequently combined to turn row-level conditions into grouped metrics.

This pattern is fundamental to reporting, dashboards, analytics APIs, operational metrics, and backend queries where multiple business metrics must be calculated in a single database round trip.

The general pattern is:

```sql
SELECT
    SUM(CASE WHEN condition THEN value ELSE 0 END) AS metric
FROM orders;
```

The database evaluates the `CASE` expression for each qualifying row and then applies the aggregate to the resulting values.

For example:

```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
FROM orders;
```

This produces multiple metrics from one scan of the relevant rows.

The important distinction is:

- `CASE` performs **row-level classification or transformation**.
- Aggregation performs **set-level calculation**.
- Combining them creates **conditional aggregation**.

## Mental Model

Think of the query as a pipeline:

```text
Rows
  ↓
WHERE filters the input set
  ↓
CASE evaluates each remaining row
  ↓
Aggregate combines the resulting values
  ↓
GROUP BY optionally produces one result per group
```

For example:

```sql
SELECT
    tenant_id,
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders
GROUP BY tenant_id;
```

Conceptually:

```text
order rows
    ↓
filter input rows
    ↓
evaluate CASE per order
    ↓
0 / amount
    ↓
SUM per tenant
```

This distinction is useful when debugging incorrect metrics.

## Conditional COUNT

One of the most common uses is counting rows satisfying a condition.

### Using SUM with CASE

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN 1
            ELSE 0
        END
    ) AS completed_orders
FROM orders;
```

Each row becomes either:

```text
completed -> 1
other     -> 0
```

`SUM` then produces the count.

### Using COUNT with CASE

Another common form is:

```sql
SELECT
    COUNT(
        CASE
            WHEN status = 'completed' THEN order_id
        END
    ) AS completed_orders
FROM orders;
```

For non-matching rows, the `CASE` returns `NULL`, and `COUNT(expression)` ignores those `NULL` values.

Both patterns can be correct.

| Pattern | Typical behavior |
| --- | --- |
| `SUM(CASE WHEN ... THEN 1 ELSE 0 END)` | Explicit conditional count |
| `COUNT(CASE WHEN ... THEN id END)` | Counts non-NULL conditional results |
| `COUNT(*) FILTER (WHERE ...)` | PostgreSQL-style explicit conditional aggregate |

For PostgreSQL, the `FILTER` syntax is often particularly readable:

```sql
SELECT
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders
FROM orders;
```

Use the syntax supported by your target database and team conventions.

## Conditional SUM

Conditional revenue or amount calculations are another core pattern.

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders;
```

The expression effectively converts:

```text
completed order -> amount
other order     -> 0
```

before `SUM` is applied.

A PostgreSQL alternative is:

```sql
SELECT
    SUM(amount) FILTER (WHERE status = 'completed') AS completed_revenue
FROM orders;
```

The second form makes the aggregate condition explicit and avoids embedding the condition inside the value expression.

## Conditional AVG

Conditional averages require more care.

Suppose the requirement is:

> Calculate the average amount of completed orders.

A direct approach is:

```sql
SELECT
    AVG(
        CASE
            WHEN status = 'completed' THEN amount
        END
    ) AS average_completed_amount
FROM orders;
```

Non-completed rows produce `NULL`, and `AVG` ignores those rows.

This is different from:

```sql
AVG(
    CASE
        WHEN status = 'completed' THEN amount
        ELSE 0
    END
)
```

The second expression includes non-completed rows as zero-valued observations, which changes the denominator and therefore the result.

For conditional averages, **do not add `ELSE 0` mechanically**.

Prefer:

```sql
AVG(amount) FILTER (WHERE status = 'completed')
```

when supported.

## Conditional MIN and MAX

`CASE` can also conditionally select values for `MIN` and `MAX`.

```sql
SELECT
    MIN(
        CASE
            WHEN status = 'completed' THEN completed_at
        END
    ) AS first_completed_at,
    MAX(
        CASE
            WHEN status = 'completed' THEN completed_at
        END
    ) AS last_completed_at
FROM orders;
```

Non-matching rows become `NULL`, which the aggregate ignores.

This can be useful when multiple lifecycle states are stored in one table.

## Multiple Metrics in One Query

A major production benefit of conditional aggregation is calculating several related metrics in one query.

```sql
SELECT
    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,

    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders,

    SUM(amount) FILTER (
        WHERE status = 'completed'
    ) AS completed_revenue,

    AVG(amount) FILTER (
        WHERE status = 'completed'
    ) AS average_completed_order
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
```

Instead of issuing several independent queries from an API service, the database can calculate related metrics together.

This reduces:

- Network round trips
- Application-side aggregation
- Duplicate query logic
- Potential inconsistency between separately executed queries

However, a single query is not automatically faster. Always inspect execution plans for large workloads.

## Conditional Aggregation with GROUP BY

Conditional aggregation becomes especially useful with `GROUP BY`.

Suppose a multi-tenant application needs order metrics by tenant:

```sql
SELECT
    tenant_id,
    COUNT(*) AS total_orders,
    SUM(
        CASE
            WHEN status = 'completed' THEN 1
            ELSE 0
        END
    ) AS completed_orders,
    SUM(
        CASE
            WHEN status = 'cancelled' THEN 1
            ELSE 0
        END
    ) AS cancelled_orders
FROM orders
GROUP BY tenant_id;
```

The database produces one row per tenant.

Conceptually:

```text
Tenant A
  ├── total orders
  ├── completed orders
  └── cancelled orders

Tenant B
  ├── total orders
  ├── completed orders
  └── cancelled orders
```

This pattern is common in dashboards and administrative APIs.

## Conditional Aggregation by Time Period

A common reporting requirement is comparing metrics across time periods.

For example:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE created_at >= CURRENT_DATE
    ) AS today_orders,
    COUNT(*) FILTER (
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
    ) AS last_7_days_orders
FROM orders;
```

Be careful with overlapping conditions.

`today_orders` is also included in `last_7_days_orders`.

If the requirement is mutually exclusive periods, express that explicitly:

```sql
SELECT
    COUNT(*) FILTER (
        WHERE created_at >= CURRENT_DATE
    ) AS today_orders,

    COUNT(*) FILTER (
        WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
          AND created_at < CURRENT_DATE
    ) AS previous_6_days_orders;
```

Business reporting queries should make period boundaries explicit.

## Conditional Aggregation for Status Distributions

A dashboard might need the number of orders in each lifecycle state:

```sql
SELECT
    COUNT(*) FILTER (WHERE status = 'pending') AS pending,
    COUNT(*) FILTER (WHERE status = 'processing') AS processing,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed
FROM orders;
```

This is effectively a pivot-like transformation.

A portable `CASE` version is:

```sql
SELECT
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) AS processing,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
FROM orders;
```

This pattern is useful when the set of categories is known and relatively stable.

If statuses are highly dynamic, `GROUP BY status` may be a better design:

```sql
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY status;
```

## Conditional Aggregation for Revenue

Consider an e-commerce system with several payment outcomes:

```sql
SELECT
    SUM(amount) FILTER (
        WHERE payment_status = 'captured'
    ) AS captured_revenue,

    SUM(amount) FILTER (
        WHERE payment_status = 'refunded'
    ) AS refunded_amount,

    SUM(amount) FILTER (
        WHERE payment_status = 'failed'
    ) AS failed_amount
FROM payments;
```

This is useful for operational dashboards, but financial reporting requires additional domain controls.

For example, refunded transactions may need to be associated with:

- Refund timestamps
- Partial refunds
- Currency
- Settlement status
- Chargebacks
- Idempotency semantics

A simple `SUM(CASE...)` query should not be mistaken for a complete accounting model.

## NULL Semantics

`NULL` behavior is one of the most important details in conditional aggregation.

Consider:

```sql
SUM(
    CASE
        WHEN status = 'completed' THEN amount
    END
)
```

If there are no completed rows, the aggregate may return:

```text
NULL
```

If the application contract requires zero:

```sql
COALESCE(
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
        END
    ),
    0
) AS completed_revenue
```

With PostgreSQL's `FILTER`:

```sql
COALESCE(
    SUM(amount) FILTER (WHERE status = 'completed'),
    0
) AS completed_revenue
```

The correct choice depends on the semantics.

`NULL` can mean:

> There was no value to aggregate.

`0` can mean:

> The aggregate value is explicitly zero.

Do not collapse the distinction without considering the API and business contract.

## Empty Input Sets

Aggregate behavior for empty input sets differs from `COUNT`.

Typically:

```sql
COUNT(*)
```

returns:

```text
0
```

while:

```sql
SUM(...)
AVG(...)
MIN(...)
MAX(...)
```

return `NULL` when there are no input values.

For an API response such as:

```json
{
  "order_count": 0,
  "revenue": 0
}
```

the SQL may need:

```sql
SELECT
    COUNT(*) AS order_count,
    COALESCE(SUM(amount), 0) AS revenue
FROM orders
WHERE tenant_id = $1
  AND created_at >= $2
  AND created_at < $3;
```

This is a common production boundary: SQL semantics are converted into API semantics deliberately.

## Conditional Aggregation and NULL Values

Suppose:

```text
status    amount
--------  ------
completed 100
completed NULL
pending   50
```

Then:

```sql
SUM(
    CASE
        WHEN status = 'completed' THEN amount
        ELSE 0
    END
)
```

does not treat the `NULL` amount as `0` inside the completed branch. `SUM` ignores the `NULL` value.

The result is:

```text
100
```

This can be correct, but it may also conceal incomplete data.

If a completed order is expected to always have a non-NULL amount, the database should ideally enforce that invariant:

```sql
CHECK (status <> 'completed' OR amount IS NOT NULL)
```

The exact constraint depends on the lifecycle model.

## CASE Inside Aggregation vs Aggregation Inside CASE

These are not interchangeable.

### CASE Inside Aggregate

```sql
SUM(
    CASE
        WHEN status = 'completed' THEN amount
        ELSE 0
    END
)
```

This means:

> Transform each row conditionally, then aggregate the transformed values.

### Aggregate Inside CASE

```sql
CASE
    WHEN SUM(amount) > 100000 THEN 'high'
    ELSE 'normal'
END
```

This means:

> Aggregate the rows first, then classify the aggregate result.

This distinction is fundamental.

```text
CASE inside SUM
    row-level decision
          ↓
       SUM

SUM inside CASE
    SUM
     ↓
aggregate-level decision
```

## Conditional Aggregation with HAVING

`CASE` can be combined with aggregates and `HAVING`.

For example, find tenants with at least 100 completed orders:

```sql
SELECT
    tenant_id,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders
FROM orders
GROUP BY tenant_id
HAVING COUNT(*) FILTER (
    WHERE status = 'completed'
) >= 100;
```

The aggregate is calculated per group, and `HAVING` filters groups after aggregation.

Do not use `WHERE` when the condition depends on an aggregate result.

## Conditional Aggregation and WHERE

The distinction between `WHERE` and conditional aggregation is critical.

Consider:

```sql
SELECT
    COUNT(*) AS completed_orders
FROM orders
WHERE status = 'completed';
```

This filters the input rows before aggregation.

By contrast:

```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders
FROM orders;
```

preserves all rows so that multiple metrics can be calculated.

If you write:

```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders
FROM orders
WHERE status = 'completed';
```

then `total_orders` is no longer the total number of orders. The `WHERE` clause has already removed all non-completed orders.

Think carefully about the input set before writing conditional aggregates.

## Performance Considerations

Conditional aggregation often performs well because multiple metrics can be computed during the same aggregation pass.

However, performance depends on:

- Number of input rows
- Group cardinality
- Selectivity of `WHERE`
- Indexes
- Sort/hash requirements
- Aggregate strategy
- Query concurrency
- Database engine

For example:

```sql
SELECT
    tenant_id,
    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END)
FROM orders
WHERE created_at >= $1
GROUP BY tenant_id;
```

may require scanning a substantial portion of the table.

An index such as:

```sql
CREATE INDEX idx_orders_created_tenant
ON orders (created_at, tenant_id);
```

may help depending on the workload and database planner.

Do not index every column appearing in a `CASE`. An expression inside an aggregate is not automatically a reason for an expression index.

Use execution plans:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    tenant_id,
    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END)
FROM orders
WHERE created_at >= $1
GROUP BY tenant_id;
```

Optimize based on measured workload.

## Production Reporting Pattern

For an operational dashboard, a backend service might request:

```text
GET /api/dashboard/order-metrics
```

The service can issue one parameterized query:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_orders,
    COALESCE(
        SUM(amount) FILTER (WHERE status = 'completed'),
        0
    ) AS completed_revenue
FROM orders
WHERE tenant_id = $1
  AND created_at >= $2
  AND created_at < $3;
```

The application then maps the result to its response schema.

The important production characteristics are:

- Use bound parameters rather than string interpolation.
- Define the time range explicitly.
- Define how `NULL` maps to API values.
- Keep authorization predicates in the query.
- Avoid fetching every row into Python just to aggregate it.
- Measure query latency under realistic data volume.

## Multi-Tenant Systems

Conditional aggregation must respect tenant isolation.

A dangerous pattern is:

```sql
SELECT
    tenant_id,
    COUNT(*) FILTER (WHERE status = 'completed')
FROM orders
GROUP BY tenant_id;
```

when the endpoint should expose only one tenant's data.

Prefer a query constrained to the authorized tenant:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders
FROM orders
WHERE tenant_id = $1;
```

Authorization is not merely an application-layer concern when the query itself determines which rows are aggregated.

For systems using PostgreSQL Row-Level Security, conditional aggregation still operates only over rows visible under the active security policy.

## ORM Considerations

Django can express conditional aggregation using database functions and conditional filters.

For example:

```python
from django.db.models import Count, Q

metrics = Order.objects.filter(
    tenant_id=tenant_id,
).aggregate(
    total_orders=Count("id"),
    completed_orders=Count(
        "id",
        filter=Q(status="completed"),
    ),
)
```

This is preferable to loading all orders into Python:

```python
orders = list(Order.objects.filter(tenant_id=tenant_id))

completed_orders = [
    order for order in orders
    if order.status == "completed"
]
```

The latter moves work and data transfer into the application layer unnecessarily.

For performance-sensitive endpoints, inspect the generated SQL and execution plan rather than assuming ORM syntax is optimal.

## Common Mistakes

### Filtering Away Rows Needed by Another Metric

Incorrect:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders
FROM orders
WHERE status = 'completed';
```

`total_orders` is now the completed-order count.

Keep broad input filtering in `WHERE` and category-specific conditions inside the aggregate when multiple categories must be compared.

### Using ELSE 0 for AVG

Avoid:

```sql
AVG(
    CASE
        WHEN status = 'completed' THEN amount
        ELSE 0
    END
)
```

when you mean the average among completed orders.

Use:

```sql
AVG(
    CASE
        WHEN status = 'completed' THEN amount
    END
)
```

or:

```sql
AVG(amount) FILTER (WHERE status = 'completed')
```

### Forgetting NULL Aggregate Results

This:

```sql
SUM(amount)
```

can return `NULL` for an empty input set.

If the API contract requires numeric zero:

```sql
COALESCE(SUM(amount), 0)
```

### Counting a Nullable Column

This:

```sql
COUNT(
    CASE
        WHEN status = 'completed' THEN amount
    END
)
```

counts only completed rows whose `amount` is non-NULL.

If the requirement is to count completed orders regardless of amount, use a non-NULL identifier:

```sql
COUNT(
    CASE
        WHEN status = 'completed' THEN order_id
    END
)
```

or:

```sql
COUNT(*) FILTER (WHERE status = 'completed')
```

### Repeating Complex CASE Expressions

If the same large `CASE` appears in many aggregates, readability and maintenance degrade quickly.

Consider:

- A derived table
- A CTE when appropriate
- A generated classification column
- A normalized mapping table
- A materialized reporting model

Do not introduce a CTE solely for style if it makes the query harder to optimize or understand.

### Aggregating Before Applying Security Filters

Never calculate a broad aggregate and rely on the application to discard unauthorized data afterward.

The authorization boundary should constrain the rows participating in the aggregation.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| Why use `SUM(CASE...)`? | To conditionally convert rows into values and aggregate them |
| Why can `ELSE 0` be wrong for `AVG`? | It adds non-matching rows to the denominator |
| What does `COUNT(CASE WHEN ... THEN id END)` count? | Non-NULL IDs produced by matching rows |
| What happens to `NULL` values in `SUM`? | They are generally ignored |
| What does `SUM` return for no input values? | Typically `NULL`, unlike `COUNT(*)`, which returns `0` |
| What is the difference between `WHERE` and conditional aggregation? | `WHERE` removes rows from the aggregate input; conditional aggregation preserves them for selective metrics |
| What is `CASE` inside `SUM`? | Row-level transformation followed by aggregation |
| What is `SUM` inside `CASE`? | Aggregate first, then classify the aggregate result |
| Why is conditional aggregation useful for APIs? | Multiple related metrics can often be calculated in one database query |
| Should every conditional aggregate use `ELSE 0`? | No; the correct expression depends on whether unmatched rows should contribute zero or `NULL` |
| When should `GROUP BY` replace conditional aggregation? | When the category set is dynamic or the result should naturally contain one row per category |
| Does one query automatically mean better performance? | No; execution plans, data volume, indexes, and concurrency determine actual performance |

## Key Takeaways

- `CASE` performs row-level conditional transformation, while aggregate functions combine those transformed values into set-level metrics.
- `SUM(CASE...)`, conditional `COUNT`, and `FILTER` are core patterns for calculating multiple metrics without unnecessary application-side aggregation.
- Be deliberate with `ELSE 0`: it is appropriate for conditional counts and many sums, but can produce incorrect averages or hide meaningful `NULL` semantics.
- Keep broad row filtering in `WHERE` and category-specific conditions inside aggregates when multiple metrics must be calculated from the same input set.
- Production conditional aggregates must respect tenant/security boundaries, API `NULL` semantics, realistic indexes, and measured execution-plan performance.