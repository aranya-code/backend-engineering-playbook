# 03- AVG OVER

## Overview

`AVG() OVER` applies an average calculation as a window function while preserving the individual rows in the result set.

A regular aggregate:

```sql
SELECT
    customer_id,
    AVG(amount) AS average_order_value
FROM orders
GROUP BY customer_id;
```

returns one row per customer.

A windowed average:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS average_order_value
FROM orders;
```

returns every order while attaching the customer's average order value to each row.

This makes `AVG() OVER` useful for comparing individual records against group averages, calculating rolling averages, measuring deviations from baselines, and building analytical API responses.

## Basic Syntax

The general form is:

```sql
AVG(expression) OVER (
    PARTITION BY partition_expression
    ORDER BY ordering_expression
    frame_clause
)
```

| Component | Purpose |
|---|---|
| `AVG(expression)` | Calculates the arithmetic mean |
| `OVER` | Converts the aggregate into a window calculation |
| `PARTITION BY` | Defines independent calculation groups |
| `ORDER BY` | Defines logical order for order-sensitive averages |
| Frame clause | Defines which rows participate in the current calculation |

`PARTITION BY` and `ORDER BY` are optional. Their presence changes the scope and semantics of the average.

## Regular `AVG()` vs `AVG() OVER`

A regular aggregate changes the result grain:

```sql
SELECT
    customer_id,
    AVG(amount) AS avg_order_value
FROM orders
GROUP BY customer_id;
```

The result contains one row per customer.

A windowed aggregate preserves the input grain:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS avg_order_value
FROM orders;
```

The result remains one row per order.

| Requirement | Regular `AVG()` | `AVG() OVER` |
|---|---:|---:|
| One row per group | Yes | No |
| Preserve detail rows | No | Yes |
| Group average beside each row | Requires join/subquery | Yes |
| Running average | No | Yes |
| Rolling average | No | Yes |
| Compare row to group baseline | Requires additional query structure | Yes |

The key distinction is **result-set grain**.

## Global Average

An empty window applies the average to the entire input set:

```sql
SELECT
    order_id,
    amount,
    AVG(amount) OVER () AS overall_average
FROM orders;
```

Every row receives the same average.

For:

| order_id | amount |
|---:|---:|
| 101 | 100 |
| 102 | 200 |
| 103 | 300 |

the average is `200`, so the result is conceptually:

| order_id | amount | overall_average |
|---:|---:|---:|
| 101 | 100 | 200 |
| 102 | 200 | 200 |
| 103 | 300 | 200 |

This pattern is useful when each record needs to be compared with a global baseline.

## Partitioned Average

`PARTITION BY` creates independent average calculations.

```sql
SELECT
    order_id,
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_avg_order_value
FROM orders;
```

For:

| order_id | customer_id | amount |
|---:|---:|---:|
| 101 | 1 | 100 |
| 102 | 1 | 300 |
| 103 | 2 | 200 |
| 104 | 2 | 400 |

the result is:

| order_id | customer_id | amount | customer_avg_order_value |
|---:|---:|---:|---:|
| 101 | 1 | 100 | 200 |
| 102 | 1 | 300 | 200 |
| 103 | 2 | 200 | 300 |
| 104 | 2 | 400 | 300 |

Each order remains visible while the average is calculated independently for each customer.

## Comparing a Row Against Its Group Average

One of the most useful patterns is comparing a value with its partition's average.

```sql
SELECT
    order_id,
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average,
    amount - AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS difference_from_average
FROM orders;
```

The result identifies whether each order is above or below the customer's normal order value.

A percentage comparison can be calculated as:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average,
    100.0 * (
        amount - AVG(amount) OVER (
            PARTITION BY customer_id
        )
    ) / NULLIF(
        AVG(amount) OVER (
            PARTITION BY customer_id
        ),
        0
    ) AS percentage_difference
FROM orders;
```

`NULLIF` prevents division by zero when the baseline average is zero.

## Running Average

Adding `ORDER BY` makes the average depend on row position.

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_average
FROM orders;
```

For one customer:

```text
Order 1: 100 → 100
Order 2: 200 → 150
Order 3: 300 → 200
```

The frame grows from the first row through the current row.

This is useful for:

- Customer spending trends.
- Average processing time.
- Average transaction value.
- Operational performance.
- Incremental KPI analysis.

For production queries, explicitly defining the frame avoids ambiguity and documents the intended calculation.

## Rolling Average

A bounded frame creates a moving average.

```sql
SELECT
    recorded_at,
    revenue,
    AVG(revenue) OVER (
        ORDER BY recorded_at
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_row_average
FROM daily_revenue;
```

The current row plus six preceding rows participate in the average.

This produces a seven-row moving average once enough rows are available.

### Rows Are Not Calendar Periods

The expression:

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

means seven rows.

It does **not** necessarily mean seven calendar days.

If a daily metrics table has missing dates:

```text
Monday
Tuesday
Friday
Saturday
```

a seven-row frame can cover more than seven calendar days.

When the business requirement is explicitly time-based, first establish a regular time series or use an appropriate time-based frame/query strategy supported by the target database.

## `ROWS` vs `RANGE`

Consider:

```sql
AVG(amount) OVER (
    ORDER BY created_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

and:

```sql
AVG(amount) OVER (
    ORDER BY created_at
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

`ROWS` is based on row positions.

`RANGE` uses ordering values and peer groups.

If multiple rows have the same ordering value, the two can produce different results.

For deterministic row-by-row running averages, prefer a unique ordering:

```sql
ORDER BY created_at, order_id
```

and use an explicit `ROWS` frame when row-based semantics are intended.

## Deterministic Ordering

Avoid relying on:

```sql
ORDER BY created_at
```

if multiple records can have the same timestamp.

Prefer:

```sql
ORDER BY created_at, order_id
```

where `order_id` uniquely identifies the row.

This matters for:

- Running averages.
- Cumulative metrics.
- Event processing.
- Financial reporting.
- Reproducible tests.
- Debugging production discrepancies.

The `ORDER BY` inside `OVER` controls the window calculation. It does **not** guarantee the final output order.

If the API requires a particular output order, specify a query-level `ORDER BY` as well:

```sql
SELECT
    order_id,
    created_at,
    amount,
    AVG(amount) OVER (
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_average
FROM orders
ORDER BY created_at, order_id;
```

## `NULL` Behavior

`AVG()` ignores `NULL` values.

For example:

```sql
SELECT AVG(amount)
FROM orders;
```

does not treat a `NULL` amount as zero.

Conceptually:

```text
100
200
NULL
300
```

produces:

```text
AVG = (100 + 200 + 300) / 3
    = 200
```

not:

```text
(100 + 200 + 0 + 300) / 4
```

This distinction matters when `NULL` means "unknown" rather than "zero".

For windowed averages:

```sql
AVG(amount) OVER (
    PARTITION BY customer_id
)
```

the same `NULL` handling applies within each partition.

## Empty and All-NULL Inputs

`AVG()` can return `NULL` when there are no non-`NULL` values.

If the application requires a zero fallback:

```sql
COALESCE(
    AVG(amount) OVER (
        PARTITION BY customer_id
    ),
    0
) AS customer_average
```

However, zero and "no measurable average" often have different business meanings.

For example:

- `0` may mean the measured average is genuinely zero.
- `NULL` may mean there were no qualifying records.

Do not convert `NULL` to zero automatically without checking the domain semantics.

## Integer and Decimal Data Types

Average calculations require attention to data types.

For example, when calculating averages for monetary values, use an exact numeric database type rather than floating-point storage.

In PostgreSQL:

```sql
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL
);
```

Then:

```sql
AVG(amount) OVER (
    PARTITION BY customer_id
)
```

produces an exact numeric result appropriate for financial calculations.

Application code should preserve the database's decimal semantics when serializing financial values rather than unnecessarily converting them to binary floating-point numbers.

## Average of Averages Is Usually Wrong

A common analytical mistake is averaging already-aggregated averages.

Suppose two customers have:

```text
Customer A: 2 orders, average = 100
Customer B: 100 orders, average = 200
```

The expression:

```text
(100 + 200) / 2 = 150
```

is not the overall order-level average.

The correct overall average must account for the number of observations:

```text
(2 × 100 + 100 × 200) / 102
```

When working with grouped data, preserve the underlying count and sum when an overall weighted metric is required.

For example:

```sql
WITH customer_stats AS (
    SELECT
        customer_id,
        SUM(amount) AS total_amount,
        COUNT(amount) AS order_count
    FROM orders
    GROUP BY customer_id
)
SELECT
    SUM(total_amount) / NULLIF(SUM(order_count), 0) AS overall_average
FROM customer_stats;
```

This distinction is important in analytics systems and technical interviews.

## Weighted Averages

`AVG()` calculates an arithmetic mean where each participating row has equal weight.

If records have different weights, calculate a weighted average explicitly.

For example:

```sql
SELECT
    SUM(price * quantity)
        / NULLIF(SUM(quantity), 0) AS weighted_average_price
FROM order_items;
```

The window equivalent is:

```sql
SELECT
    product_id,
    price,
    quantity,
    SUM(price * quantity) OVER (
        PARTITION BY product_id
    )
    / NULLIF(
        SUM(quantity) OVER (
            PARTITION BY product_id
        ),
        0
    ) AS weighted_average_price
FROM product_prices;
```

Do not use `AVG(price)` when the business requirement is quantity-weighted pricing.

## Combining `GROUP BY` and `AVG() OVER`

Window functions operate on the result produced by the query block in which they appear.

This allows grouped averages to become input to another window calculation.

For example:

```sql
SELECT
    department_id,
    AVG(salary) AS department_avg_salary,
    AVG(AVG(salary)) OVER () AS average_department_salary
FROM employees
GROUP BY department_id;
```

Conceptually:

```text
employee rows
     ↓
GROUP BY department
     ↓
department average rows
     ↓
window AVG across departments
     ↓
department + overall department-average
```

The outer window average is averaging **department averages**, not individual employee salaries.

That distinction is intentional here, but it can also be a source of analytical bugs.

## Correct Aggregation Grain

Always establish the required analytical grain before applying `AVG() OVER`.

Suppose the requirement is:

> Show monthly revenue and the customer's average monthly revenue.

First aggregate orders to customer-month:

```sql
WITH monthly_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
)
SELECT
    customer_id,
    month,
    revenue,
    AVG(revenue) OVER (
        PARTITION BY customer_id
    ) AS average_monthly_revenue
FROM monthly_revenue;
```

The window operates on customer-month rows.

Applying `AVG()` directly to order-level rows would answer a different question.

## Filtering and Window Averages

Filtering in the same query block occurs before the window calculation.

```sql
SELECT
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average
FROM orders
WHERE status = 'completed';
```

The average contains only completed orders.

If the requirement is:

> Display completed orders but compare them against the average of all orders.

create a query boundary:

```sql
WITH order_metrics AS (
    SELECT
        order_id,
        customer_id,
        amount,
        status,
        AVG(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_average
    FROM orders
)
SELECT
    order_id,
    customer_id,
    amount,
    customer_average
FROM order_metrics
WHERE status = 'completed';
```

This pattern is essential when separating **calculation scope** from **display scope**.

## API and Backend Example

A backend API may need to return orders together with a customer's average order value:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average
FROM orders
WHERE
    customer_id = :customer_id
    AND status = 'completed'
ORDER BY
    created_at,
    order_id;
```

A Django or FastAPI service can map each result row directly into an API representation.

Example response shape:

```json
{
  "order_id": 1001,
  "amount": 125.00,
  "customer_average": 180.50
}
```

The important design question is not simply whether the SQL is valid. Verify that the rows entering the window represent the intended business population.

If `customer_average` means lifetime average, but the query only contains the last 30 days, the calculation is not a lifetime average.

## Operational Metrics Example

Windowed averages are useful for service and infrastructure metrics.

Suppose a table stores request latency:

```sql
CREATE TABLE api_latency (
    recorded_at TIMESTAMPTZ NOT NULL,
    endpoint TEXT NOT NULL,
    latency_ms NUMERIC(10, 2) NOT NULL
);
```

A rolling seven-observation average can be calculated as:

```sql
SELECT
    recorded_at,
    endpoint,
    latency_ms,
    AVG(latency_ms) OVER (
        PARTITION BY endpoint
        ORDER BY recorded_at
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_average_latency_ms
FROM api_latency
WHERE recorded_at >= NOW() - INTERVAL '24 hours';
```

This can support dashboards and operational analysis, but high-volume observability workloads are often better handled by dedicated metrics systems rather than repeatedly scanning transactional tables.

## Performance Considerations

Windowed averages can require:

- Sorting.
- Partition processing.
- Memory.
- CPU.
- Temporary storage.
- Scanning large numbers of rows.

For PostgreSQL, inspect the actual execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    created_at,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_average
FROM orders
WHERE tenant_id = 42;
```

Look for:

- Large sort operations.
- Unexpected row counts.
- Temporary file usage.
- Excessive buffer reads.
- Long execution times.
- Large partitions.

Indexes can help reduce the cost of filtering and may help the optimizer with ordering, but an index does not guarantee that a window operation will avoid sorting.

## Large-Scale Production Workloads

A correct window query can still be the wrong implementation for a high-throughput API.

Avoid repeatedly calculating historical averages over very large transactional tables when the value changes infrequently.

Depending on freshness requirements, consider:

- Summary tables.
- Materialized views.
- Pre-aggregated metrics.
- Read replicas.
- Background jobs.
- Cached analytical results.
- Dedicated analytical databases.

For example:

```text
Application API
      │
      ▼
Transactional PostgreSQL
      │
      ├── current transactional data
      │
      └── pre-aggregated customer metrics
                    │
                    ▼
              API analytics
```

The architectural goal is to avoid turning expensive historical scans into a synchronous request-path dependency.

## Security Considerations

`AVG() OVER` does not provide authorization or tenant isolation.

The rows entering the window determine what information contributes to the calculation.

For multi-tenant systems:

```sql
SELECT
    customer_id,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average
FROM orders
WHERE tenant_id = :tenant_id;
```

The tenant boundary must be enforced before calculating tenant-scoped analytics.

Be careful with global windows:

```sql
AVG(amount) OVER ()
```

A global average can unintentionally disclose information about records outside the user's authorized scope.

Use:

- Parameterized queries.
- Consistent tenant filtering.
- Authorization-aware data-access layers.
- Tests for cross-tenant leakage.
- Explicit definitions of the population represented by an aggregate.

## Common Mistakes

### Treating `AVG() OVER` Like `GROUP BY`

```sql
AVG(amount) OVER (
    PARTITION BY customer_id
)
```

does not produce one row per customer.

It preserves every input row.

### Averaging the Wrong Grain

If the business metric is average monthly revenue, do not average order-level amounts.

First establish customer-month rows, then apply the window average.

### Ignoring `NULL`

`AVG()` ignores `NULL`.

If `NULL` means missing data, treating it as zero changes the metric.

### Using `AVG()` for Weighted Data

If one record represents 1 unit and another represents 1,000 units, a simple average may not represent the business metric.

Use an explicit weighted formula when required.

### Averaging Averages

A simple average of group averages can be mathematically incorrect when groups contain different numbers of observations.

Retain counts and sums when a weighted overall metric is required.

### Assuming `ROWS` Means Days

A seven-row frame is not automatically a seven-day window.

The distinction becomes important when timestamps are sparse or irregular.

### Omitting a Tie-Breaker

For cumulative calculations, avoid relying on non-unique timestamps.

Prefer:

```sql
ORDER BY created_at, order_id
```

### Filtering the Wrong Query Layer

A `WHERE` clause in the same query block changes which rows participate in the window.

Use a CTE or derived table when calculation scope and display scope must differ.

### Running Historical Windows on Every API Request

Large analytical windows can create unpredictable API latency.

Measure the query and consider precomputation when the workload grows.

## Interview Traps

| Question | Correct answer |
|---|---|
| Does `AVG() OVER` collapse rows? | No. It preserves the input rows. |
| What does `PARTITION BY` control? | The independent scope of each average calculation. |
| What does `ORDER BY` inside `OVER` control? | Logical ordering for order-sensitive window calculations. |
| Does window `ORDER BY` guarantee final result order? | No. Use the query-level `ORDER BY`. |
| Does `AVG()` include `NULL` values? | No. `NULL` values are ignored. |
| What does `AVG() OVER ()` calculate? | The average across the rows visible to that query block. |
| How do you calculate a running average? | Use `AVG(...) OVER (...)` with deterministic ordering and an appropriate frame. |
| Does `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` mean seven days? | No. It means seven rows. |
| Can `GROUP BY` and window averages be combined? | Yes. The window can operate over the grouped result. |
| Is the average of group averages always the overall average? | No. It is only equivalent when group weighting makes it valid. |
| How do you calculate a weighted average? | Use `SUM(value × weight) / SUM(weight)` rather than `AVG(value)`. |
| Can filtering change a window average? | Yes. Rows filtered in the same query block are excluded before the window calculation. |

## Best Practices

- Treat `AVG() OVER` as an analytical calculation that preserves result-set grain.
- Define the desired business grain before writing the window expression.
- Use `PARTITION BY` for group-specific baselines.
- Use deterministic ordering for running averages.
- Prefer explicit `ROWS` frames when row-based semantics are intended.
- Distinguish row-based windows from time-based business requirements.
- Understand `NULL` semantics before replacing `NULL` with zero.
- Avoid averaging averages when group sizes differ.
- Use weighted-average formulas when observations have different weights.
- Keep calculation scope separate from presentation filtering when necessary.
- Use exact numeric types for monetary calculations.
- Inspect PostgreSQL execution plans for large window queries.
- Pre-aggregate or move expensive analytics away from synchronous API paths when necessary.
- Test duplicate timestamps, `NULL` values, empty inputs, different partition sizes, and boundary conditions.

## Key Takeaways

- **`AVG() OVER` calculates averages while preserving individual rows, making it ideal for row-level analytical comparisons.**
- **`PARTITION BY` defines the population being averaged, while `ORDER BY` and the frame determine running or rolling behavior.**
- **`AVG()` ignores `NULL` values, and simple averages are not interchangeable with weighted averages or averages of averages.**
- **The rows entering the window determine the metric, so query grain and filtering boundaries are critical for correctness.**
- **Large historical window calculations should be measured and, when necessary, replaced with pre-aggregation or dedicated analytical infrastructure.**