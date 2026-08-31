# README

## Overview

Window aggregate functions extend ordinary SQL aggregates such as `SUM()`, `AVG()`, `COUNT()`, `MIN()`, and `MAX()` so they can calculate aggregate metrics **without collapsing the result set**.

This section focuses on practical aggregate-window patterns used in backend systems and analytical queries:

- Group-level totals and averages.
- Running and cumulative aggregations.
- Moving averages.
- Partitioned metrics.
- Per-row counts and boundaries.
- Combining `GROUP BY` with window aggregates.
- Using CTEs and subqueries to stage window calculations.
- Filtering on calculated window values.
- Production performance considerations.

The core distinction is:

```text
GROUP BY
    Many rows ──► Fewer rows

Window aggregate
    Many rows ──► Same rows + aggregate context
```

Window aggregates are particularly useful when an API, report, or operational query needs both **individual records** and **context about the records they belong to**.

## Navigation

- [01- Window Aggregate Functions](./01-%20Window%20Aggregate%20Functions.md) — Fundamentals of aggregate functions used with OVER()
- [02- SUM OVER](./02-%20SUM%20OVER.md) — SUM() OVER() for group totals and ordered accumulation
- [03- AVG OVER](./03-%20AVG%20OVER.md) — AVG() OVER() for group and contextual averages
- [04- COUNT OVER](./04-%20COUNT%20OVER.md) — COUNT() OVER() for row and partition-level counts
- [05- MIN and MAX OVER](./05-%20MIN%20and%20MAX%20OVER.md) — Minimum and maximum values within windows
- [06- Running Totals](./06-%20Running%20Totals.md) — Running totals using ordered window frames
- [07- Moving Averages](./07-%20Moving%20Averages.md) — Rolling and moving averages
- [08- Cumulative Aggregations](./08-%20Cumulative%20Aggregations.md) — Cumulative metrics across ordered data
- [09- Partitioned Aggregations](./09-%20Partitioned%20Aggregations.md) — Aggregations scoped to independent partitions
- [10- Window Aggregate Selection Rules](./10-%20Window%20Aggregate%20Selection%20Rules.md) — Choosing the correct aggregate and window definition
- [11- Practical Window Aggregate Patterns](./11-%20Practical%20Window%20Aggregate%20Patterns.md) — Production-oriented patterns combining aggregate windows

## Aggregate Window Functions

The primary aggregate functions in this section are:

| Function | Typical use |
|---|---|
| `SUM()` | Totals, running totals, cumulative values |
| `AVG()` | Group averages, moving averages, deviations |
| `COUNT()` | Rows per group, event counts, occurrence counts |
| `MIN()` | Group minimums and lower boundaries |
| `MAX()` | Group maximums and upper boundaries |

The common syntax is:

```sql
aggregate_function(expression) OVER (
    PARTITION BY partition_columns
    ORDER BY ordering_columns
    frame_definition
)
```

Each component has a different responsibility:

| Component | Responsibility |
|---|---|
| Aggregate function | Defines what is calculated |
| `PARTITION BY` | Defines independent calculation groups |
| `ORDER BY` | Defines row sequence within each window |
| Frame | Defines the rows included relative to the current row |

For example:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

Every order remains in the result while `customer_total` provides customer-level context.

## `GROUP BY` vs Window Aggregates

The most important conceptual distinction is **result-set granularity**.

### `GROUP BY`

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

The result contains one row per customer.

### Window Aggregate

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

The result contains one row per order.

This distinction determines which technique should be used.

| Requirement | Technique |
|---|---|
| One result row per customer | `GROUP BY` |
| Every order plus customer total | `SUM() OVER()` |
| Every order plus customer average | `AVG() OVER()` |
| Running total | `SUM() OVER()` with ordering/frame |
| Moving average | `AVG() OVER()` with frame |
| Count records in each partition | `COUNT() OVER()` |
| Filter using a window result | CTE or subquery |
| Aggregate first, then calculate over aggregates | `GROUP BY` followed by a window |

## Partitioning

`PARTITION BY` divides the input rows into independent logical windows.

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

Each customer's total is calculated independently.

Multiple columns can define a business partition:

```sql
SUM(amount) OVER (
    PARTITION BY tenant_id, customer_id
)
```

This is important in multi-tenant systems where a customer identifier may only be unique within a tenant.

### Partitioning Is Not Authorization

A window partition does not protect data.

This:

```sql
PARTITION BY tenant_id
```

does not replace:

```sql
WHERE tenant_id = :tenant_id
```

Authorization and tenant filtering must be enforced separately.

## Ordering and Window Frames

Adding `ORDER BY` changes the nature of many aggregate windows.

A partition total:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

calculates across the partition.

A running total:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

calculates progressively through the ordered rows.

For production queries, deterministic ordering matters. If timestamps can collide, use a stable tie-breaker such as a unique ID:

```sql
ORDER BY created_at, order_id
```

## Running and Cumulative Aggregations

A running total accumulates values from the beginning of the window through the current row.

```sql
SELECT
    transaction_id,
    account_id,
    occurred_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY occurred_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM transactions;
```

The same pattern applies to:

- Revenue.
- Transaction amounts.
- Inventory changes.
- Usage.
- Request counts.
- Job processing metrics.

For higher-level reporting, aggregate first:

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', paid_at) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE status = 'succeeded'
    GROUP BY DATE_TRUNC('month', paid_at)
)
SELECT
    month,
    revenue,
    SUM(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM monthly_revenue
ORDER BY month;
```

This avoids performing the cumulative calculation across every underlying payment when the required output is monthly.

## Moving Averages

Moving averages use a bounded frame around the current row.

```sql
AVG(value) OVER (
    ORDER BY measured_at
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
)
```

This calculates an average over the current row and up to six preceding rows.

A critical distinction is that `ROWS` counts rows rather than elapsed time.

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

does not inherently mean seven days.

If measurements are irregular, seven rows may cover a much larger or smaller time interval.

## CTEs and Subqueries

Window results generally cannot be filtered directly in the same query level's `WHERE` clause.

Instead:

```sql
WITH customer_metrics AS (
    SELECT
        order_id,
        customer_id,
        amount,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
)
SELECT
    order_id,
    customer_id,
    amount,
    customer_total
FROM customer_metrics
WHERE customer_total >= 10000;
```

The CTE creates a new relational query level.

The same approach works with a derived table:

```sql
SELECT *
FROM (
    SELECT
        order_id,
        customer_id,
        amount,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
) AS customer_metrics
WHERE customer_total >= 10000;
```

CTEs are often preferable when a query has multiple logical stages because they make the data flow easier to review.

## Aggregation Followed by Window Aggregation

One of the most useful advanced patterns is:

```text
Raw rows
   │
   ▼
WHERE
   │
   ▼
GROUP BY
   │
   ▼
Aggregated rows
   │
   ▼
Window aggregate
   │
   ▼
Final result
```

Example:

```sql
WITH monthly_customer_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', paid_at) AS month,
        SUM(amount) AS monthly_revenue
    FROM payments
    WHERE status = 'succeeded'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', paid_at)
)
SELECT
    customer_id,
    month,
    monthly_revenue,
    AVG(monthly_revenue) OVER (
        PARTITION BY customer_id
    ) AS average_monthly_revenue,
    SUM(monthly_revenue) OVER (
        PARTITION BY customer_id
    ) AS total_revenue
FROM monthly_customer_revenue;
```

This pattern is valuable because the window function operates at the **business reporting granularity**, rather than unnecessarily processing every transactional row.

## Practical Backend Patterns

### Order API With Customer Context

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS customer_order_count
FROM orders
WHERE tenant_id = :tenant_id
  AND status = 'completed';
```

This can provide an API with row-level order data and customer-level metrics in one query.

### Revenue Dashboard

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', paid_at) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE tenant_id = :tenant_id
      AND status = 'succeeded'
    GROUP BY DATE_TRUNC('month', paid_at)
)
SELECT
    month,
    revenue,
    SUM(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue,
    AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS three_month_average
FROM monthly_revenue
ORDER BY month;
```

### Event-Level Session Metrics

```sql
SELECT
    event_id,
    user_id,
    session_id,
    event_type,
    COUNT(*) OVER (
        PARTITION BY session_id
    ) AS session_event_count,
    AVG(duration_ms) OVER (
        PARTITION BY session_id
    ) AS session_avg_duration_ms
FROM events
WHERE tenant_id = :tenant_id;
```

This keeps individual events while attaching session-level context.

## Performance and Production Considerations

Window aggregates can require substantial database work, particularly when partitions are large or ordering is required.

Use PostgreSQL execution plans when evaluating production queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    order_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders
WHERE tenant_id = 42;
```

Pay attention to:

- Large sort operations.
- Temporary disk usage.
- High buffer reads.
- Unexpected row counts.
- Large partitions.
- Query execution time.

### Large Partitions

A query can appear efficient for normal customers but become expensive for a tenant containing millions of records.

Mitigation strategies include:

- Restricting the date range.
- Pre-aggregating historical data.
- Materialized views.
- Reporting tables.
- Incremental aggregation.
- Read replicas for suitable workloads.
- Dedicated analytical stores.

For frequently requested dashboards, recomputing large windows over raw transactional data on every API request is often the wrong architecture.

## Application Integration

Window queries work well with Python web backends such as Django and FastAPI when the database is responsible for relational aggregation.

Django provides window expressions through `Window()`:

```python
from django.db.models import F, Sum, Window

orders = Order.objects.annotate(
    customer_total=Window(
        expression=Sum("amount"),
        partition_by=[F("customer_id")],
    )
)
```

Production recommendations:

- Inspect generated SQL.
- Test against realistic data volumes.
- Use bound parameters rather than string interpolation.
- Return only required columns.
- Measure database latency independently from application latency.
- Review execution plans for expensive queries.
- Prefer database computation when it reduces application-side round trips without creating an unmanageable query.

## Common Mistakes

| Mistake | Why it is a problem |
|---|---|
| Using `GROUP BY` when row-level records are required | It collapses the result set |
| Treating `PARTITION BY` as a security boundary | It organizes rows but does not authorize access |
| Filtering before the wrong calculation | `WHERE` changes the rows visible to the window |
| Filtering a window result directly in `WHERE` | A separate query level is normally required |
| Assuming `ROWS` means a time interval | `ROWS` counts records |
| Omitting a tie-breaker in ordered calculations | Ordering may be nondeterministic when keys tie |
| Using `MIN()`/`MAX()` to identify a related row | They return values, not the associated row |
| Running huge windows over raw event data repeatedly | Can overload the transactional database |
| Assuming a CTE always materializes | PostgreSQL may inline eligible CTEs |
| Assuming one SQL query is always faster | A consolidated query can still be computationally expensive |

## Interview Reference

| Concept | Key point |
|---|---|
| Window aggregate | Adds aggregate context without collapsing rows |
| `PARTITION BY` | Defines independent logical windows |
| `ORDER BY` | Defines sequence for ordered calculations |
| Frame | Defines which rows participate relative to the current row |
| `GROUP BY` + window | Useful when calculations should happen at different granularities |
| CTE/subquery | Provides a new query level for filtering or further processing |
| `ROWS` | Specifies a row-count-based frame |
| Deterministic ordering | Use stable tie-breakers when ordering keys can collide |
| Large partitions | Can create substantial sort and memory costs |
| Pre-aggregation | Reduces the input size before expensive window processing |

## Key Takeaways

- **Window aggregate functions add aggregate context while preserving row-level granularity.**
- **`PARTITION BY`, `ORDER BY`, and the window frame define the calculation scope and must match the business requirement.**
- **Combine `GROUP BY` with window functions when the calculation should progress from transactional data to a higher reporting granularity.**
- **Use CTEs or subqueries when a window result must be filtered or consumed by another query stage.**
- **For production-scale analytics, validate execution plans and consider pre-aggregation or dedicated analytical storage for large workloads.**