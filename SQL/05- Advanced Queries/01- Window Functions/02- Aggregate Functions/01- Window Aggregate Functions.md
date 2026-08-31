# 01- Window Aggregate Functions

## Overview

Window aggregate functions apply standard aggregate functions such as `SUM`, `AVG`, `COUNT`, `MIN`, and `MAX` across a window of rows while preserving the individual rows in the result.

The key distinction from ordinary aggregation is **row preservation**:

```text
GROUP BY

orders
   ↓
group rows
   ↓
one result row per group


Window aggregate

orders
   ↓
define window
   ↓
calculate aggregate for each row
   ↓
original rows remain
```

This makes window aggregates useful for production analytics such as:

- Running account balances.
- Customer lifetime revenue.
- Per-customer averages.
- Percentage-of-total calculations.
- Running counts.
- Moving averages.
- Minimum/maximum values within a group.
- Time-series metrics.
- Ranking inputs and reporting datasets.

## Basic Syntax

The general form is:

```sql
aggregate_function(expression) OVER (
    PARTITION BY partition_expression
    ORDER BY ordering_expression
    frame_clause
)
```

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

Every order remains in the result, but each order receives the total revenue for its customer.

## Aggregate Functions as Window Functions

Many familiar aggregate functions can be used with `OVER`.

| Function | Window use |
|---|---|
| `SUM()` | Running or partition-level totals |
| `AVG()` | Per-group or moving averages |
| `COUNT()` | Per-group or running counts |
| `MIN()` | Lowest value within a window |
| `MAX()` | Highest value within a window |

The function itself does not define the window. The `OVER` clause does.

## `SUM()` as a Window Function

### Partition-Level Total

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

For data such as:

| order_id | customer_id | amount |
|---:|---:|---:|
| 101 | 1 | 100 |
| 102 | 1 | 250 |
| 103 | 2 | 80 |
| 104 | 2 | 120 |

the result conceptually becomes:

| order_id | customer_id | amount | customer_total |
|---:|---:|---:|---:|
| 101 | 1 | 100 | 350 |
| 102 | 1 | 250 | 350 |
| 103 | 2 | 80 | 200 |
| 104 | 2 | 120 | 200 |

The partition is the customer, but the rows are not collapsed.

### Running Total

Add ordering and an explicit frame:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

For each customer:

```text
first order       → amount
second order      → first + second
third order       → first + second + third
...
```

The explicit `ROWS` frame makes the intended row-by-row cumulative behavior clear.

## `AVG()` as a Window Function

A common backend use case is comparing an individual value with its group average:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS department_average
FROM employees;
```

The result can then be used by an outer query:

```sql
WITH employee_metrics AS (
    SELECT
        employee_id,
        department_id,
        salary,
        AVG(salary) OVER (
            PARTITION BY department_id
        ) AS department_average
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary,
    department_average,
    salary - department_average AS difference_from_average
FROM employee_metrics;
```

This pattern is useful for detecting values significantly above or below their peer group.

## `COUNT()` as a Window Function

A windowed `COUNT()` can attach group cardinality to every row:

```sql
SELECT
    order_id,
    customer_id,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS customer_order_count
FROM orders;
```

Unlike:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id;
```

the window version keeps the order-level rows.

This is useful when a row-level API response needs both the individual record and metadata about its group.

## `MIN()` and `MAX()` as Window Functions

Windowed `MIN()` and `MAX()` can compare each row with the boundaries of its partition.

```sql
SELECT
    order_id,
    customer_id,
    amount,
    MIN(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_min_order,
    MAX(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_max_order
FROM orders;
```

This avoids joining the original table against a separate aggregate query when the result needs both row-level and group-level information.

## `PARTITION BY` Without `ORDER BY`

When only a partition-level aggregate is required, `ORDER BY` is unnecessary:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

Conceptually:

```text
Customer 1
├── Order A ──┐
├── Order B ──┼── SUM = customer total
└── Order C ──┘

Customer 2
├── Order D ──┐
└── Order E ──┴── SUM = customer total
```

Adding an `ORDER BY` changes the semantics because the calculation can become order-sensitive.

## `ORDER BY` and Running Aggregates

Consider:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at
)
```

The ordering determines how the window progresses.

For production queries, prefer deterministic ordering:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

If `created_at` is not unique, `order_id` provides a stable tie-breaker.

This matters for:

- Financial calculations.
- Pagination.
- Reproducible reports.
- Auditing.
- Automated tests.

## Window Frames

A frame defines which rows within the ordered partition are considered for the current calculation.

Example:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
)
```

The calculation uses:

```text
previous 2 rows
      +
current row
```

This is a three-row rolling total.

A frame is particularly important for:

- Running totals.
- Moving averages.
- Rolling sums.
- `FIRST_VALUE`.
- `LAST_VALUE`.
- Time-series calculations.

Do not treat `ORDER BY` and the frame as interchangeable concepts.

## Running Total

The canonical running-total pattern is:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

The frame means:

```text
UNBOUNDED PRECEDING
        ↓
[ row ][ row ][ row ][ current row ]
                                  ↑
                              current row
```

For an account balance, this pattern can be extended to signed transactions:

```sql
SELECT
    transaction_id,
    account_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY created_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS balance
FROM account_transactions;
```

For financial systems, the transaction ordering must be based on a business-defined sequence or immutable timestamp plus a unique tie-breaker.

## Moving Average

A moving average can be implemented with a bounded frame:

```sql
SELECT
    recorded_at,
    temperature,
    AVG(temperature) OVER (
        ORDER BY recorded_at
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_reading_average
FROM sensor_readings;
```

This calculates an average across the current row and six preceding rows.

Important distinction:

> Seven rows is not necessarily seven time units.

If readings are irregular, seven rows might represent minutes, hours, or days.

For time-based business requirements, use an appropriate time-aware strategy supported by the target database rather than assuming row count equals elapsed time.

## Percentage of Total

Window aggregates are useful for contribution calculations.

```sql
SELECT
    product_id,
    revenue,
    SUM(revenue) OVER () AS total_revenue,
    revenue / NULLIF(SUM(revenue) OVER (), 0) AS revenue_share
FROM product_revenue;
```

If percentage output is required:

```sql
SELECT
    product_id,
    revenue,
    100.0 * revenue / NULLIF(SUM(revenue) OVER (), 0) AS revenue_percentage
FROM product_revenue;
```

`NULLIF` protects against division by zero.

A common production pattern is to first establish the correct aggregation grain:

```sql
WITH product_revenue AS (
    SELECT
        product_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY product_id
)
SELECT
    product_id,
    revenue,
    100.0 * revenue / NULLIF(SUM(revenue) OVER (), 0) AS revenue_percentage
FROM product_revenue;
```

## Multiple Window Aggregates

Multiple window aggregates can be calculated in the same query:

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
    MIN(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_min,
    MAX(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_max,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS customer_order_count
FROM orders;
```

This can be significantly cleaner than repeatedly joining separate aggregate subqueries.

However, do not assume that fewer SQL expressions automatically means a cheaper query. Inspect the execution plan for large workloads.

## Multiple Window Definitions

Different calculations can use different windows:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,

    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total,

    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS customer_running_total,

    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS recent_average

FROM orders;
```

The first calculation is partition-wide, while the latter two are order-sensitive.

The database optimizer may share work between compatible window operations, but query performance depends on the specific engine and plan.

## Named Windows

SQL allows a named window definition in databases that support the relevant syntax:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER customer_window AS customer_total,
    AVG(amount) OVER customer_window AS customer_average
FROM orders
WINDOW customer_window AS (
    PARTITION BY customer_id
);
```

Named windows reduce repetition and make complex queries easier to review.

They are especially useful when multiple calculations intentionally share the same partition and ordering semantics.

## Aggregate Window vs `GROUP BY`

The difference is fundamental:

```sql
SELECT
    customer_id,
    SUM(amount) AS total
FROM orders
GROUP BY customer_id;
```

produces:

```text
one row per customer
```

while:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS total
FROM orders;
```

produces:

```text
one row per order
+ customer-level total
```

| Requirement | Better tool |
|---|---|
| One result per customer | `GROUP BY` |
| Order rows plus customer total | Window aggregate |
| Customer ranking | Window function |
| Running customer revenue | Window aggregate + `ORDER BY` |
| Dashboard-level summary | Often `GROUP BY` |
| Row-level analytical context | Window function |

## Aggregation Before Window Calculation

Window functions operate on the rows available to the query block.

Therefore, aggregation can establish the input grain:

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

The window function now operates over:

```text
customer + month
```

rather than individual orders.

This staged approach is usually easier to reason about than trying to perform all transformations at one query level.

## Interaction With `WHERE`

`WHERE` filters the rows before the window calculation.

```sql
SELECT
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE status = 'completed';
```

Only completed orders participate in `customer_total`.

If the requirement is instead:

> Calculate the customer's total across all orders, but return only completed orders.

then the filter must occur after the window calculation:

```sql
WITH metrics AS (
    SELECT
        customer_id,
        created_at,
        amount,
        status,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
)
SELECT
    customer_id,
    created_at,
    amount,
    customer_total
FROM metrics
WHERE status = 'completed';
```

The query boundary changes the semantics.

## Interaction With `GROUP BY`

Aggregates can be calculated first and then used as input to window aggregates:

```sql
SELECT
    department_id,
    SUM(salary) AS department_salary,
    SUM(SUM(salary)) OVER () AS company_salary
FROM employees
GROUP BY department_id;
```

Conceptually:

```text
employee rows
     ↓
GROUP BY department
     ↓
department salary
     ↓
window SUM over departments
     ↓
company salary attached to each department
```

This is a powerful pattern for percentage-of-total and hierarchical reporting.

## Production Use Cases

### Customer Analytics

```sql
SELECT
    customer_id,
    order_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS lifetime_order_value
FROM orders
WHERE status = 'completed';
```

### Account Balances

```sql
SELECT
    transaction_id,
    account_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY created_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance
FROM account_transactions;
```

### Operational Metrics

```sql
SELECT
    service,
    recorded_at,
    latency_ms,
    AVG(latency_ms) OVER (
        PARTITION BY service
        ORDER BY recorded_at
        ROWS BETWEEN 99 PRECEDING AND CURRENT ROW
    ) AS rolling_average_latency
FROM service_metrics;
```

For high-volume observability data, this type of query may be better suited to an analytical workload than a transactional PostgreSQL database.

## Performance Considerations

Window aggregates can require sorting and substantial intermediate processing.

Potential costs include:

- Sorting by partition and ordering keys.
- Large memory requirements.
- Temporary file usage.
- Large partition processing.
- CPU consumption.
- Increased latency for large analytical queries.

Use PostgreSQL execution plans when diagnosing performance:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders
WHERE tenant_id = 42;
```

Look for:

- Actual row counts.
- Sort operations.
- Sort methods.
- Temporary disk activity.
- Buffer reads.
- Scan strategy.
- Execution time.

Indexes can help reduce the cost of filtering and may provide useful ordering to the planner, but an index does not guarantee that a window operation will avoid sorting.

## Large-Scale Systems

For large production datasets, avoid putting expensive analytical windows directly on latency-sensitive API paths without measurement.

Possible strategies include:

- Restricting the time range.
- Pre-aggregating historical data.
- Materialized views.
- Read replicas.
- Background computation with Celery.
- Cached report results.
- Dedicated analytical databases.
- Periodic aggregation tables.

A useful architectural rule is:

> If the metric is expensive and requested frequently, consider computing it once rather than recomputing it for every API request.

For example:

```text
Django / FastAPI API
        ↓
PostgreSQL
        ↓
Pre-aggregated customer metrics
        ↓
Window calculation for small result set
        ↓
API response
```

rather than repeatedly scanning a multi-billion-row transaction table.

## Financial and Correctness Considerations

Window aggregates are often used for financial data, where ordering and filtering mistakes can create incorrect balances or reports.

For running financial totals:

- Use a deterministic ordering.
- Define whether canceled or reversed transactions participate.
- Define the business timestamp semantics.
- Handle corrections explicitly.
- Avoid floating-point representations for monetary values when exact decimal semantics are required.
- Test boundary conditions such as duplicate timestamps and zero-value transactions.

Example:

```sql
SUM(amount) OVER (
    PARTITION BY account_id
    ORDER BY effective_at, transaction_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

The unique transaction identifier ensures deterministic ordering when timestamps collide.

## Multi-Tenant Applications

Tenant isolation must be established before calculating tenant-scoped metrics.

Prefer:

```sql
SELECT
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE tenant_id = :tenant_id;
```

rather than calculating a global metric and attempting to filter it afterward.

This is both a correctness and security concern.

For Django or FastAPI applications, tenant filters should be applied consistently through the application's authorization/data-access layer.

## Common Mistakes

### Using `GROUP BY` When Rows Must Be Preserved

If the API needs order-level rows plus customer totals, `GROUP BY` alone cannot provide that shape.

Use a window aggregate.

### Using a Window Aggregate Without Understanding the Grain

This:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

calculates over all rows in the partition.

If the input contains order-level rows, the total is repeated for every order.

Aggregate first when the required grain is customer-month, customer-product, or another higher-level entity.

### Omitting a Deterministic Tie-Breaker

Avoid relying only on:

```sql
ORDER BY created_at
```

when multiple rows can share the same timestamp.

Prefer:

```sql
ORDER BY created_at, order_id
```

### Confusing `ROWS` and `RANGE`

Duplicate ordering values can cause different results.

Use an explicit frame when the business requirement depends on row-by-row behavior.

### Filtering at the Wrong Stage

A `WHERE` filter changes which rows participate in the window calculation.

Use a CTE or derived table when the calculation must include rows that are later filtered from the output.

### Assuming Seven Rows Means Seven Days

A frame such as:

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

means seven rows, not seven calendar days.

### Running Expensive Analytics on Every API Request

A correct query can still be a poor architecture if it scans a huge transactional dataset on every request.

Measure workload characteristics and consider precomputation or analytical infrastructure.

## Interview Traps

| Question | Correct answer |
|---|---|
| Does a window aggregate collapse rows? | No. It preserves the rows in its input set. |
| What does `PARTITION BY` do? | It creates independent groups for the window calculation. |
| What does window `ORDER BY` do? | It establishes the logical order used by order-sensitive window calculations. |
| Does window `ORDER BY` sort the final result? | No. Use the query's outer `ORDER BY` for final result ordering. |
| What does a frame control? | The subset of the window considered for the current row. |
| Why explicitly specify `ROWS` for running totals? | It makes row-by-row cumulative semantics explicit, particularly around duplicate ordering values. |
| Can `SUM()` be used as a window function? | Yes, by using `SUM(...) OVER (...)`. |
| How is `COUNT(*) OVER (...)` different from `GROUP BY`? | The window version preserves the original rows. |
| Why can a CTE be useful before a window aggregate? | It establishes a clean input grain or query boundary. |
| Does `WHERE` affect window aggregates? | Yes. Rows filtered by `WHERE` are unavailable to the window calculation in that query block. |

## Best Practices

- Define the required result grain before writing the window expression.
- Use `PARTITION BY` only when the calculation is logically group-scoped.
- Add deterministic tie-breakers to ordered windows.
- Explicitly specify frames for running and moving calculations when semantics matter.
- Use `NULLIF` or appropriate safeguards for percentage calculations.
- Filter as early as correctness permits to reduce the window's input size.
- Use CTEs or derived tables to separate aggregation stages.
- Inspect `EXPLAIN (ANALYZE, BUFFERS)` for expensive PostgreSQL queries.
- Avoid large analytical windows in synchronous API paths without load testing.
- Consider pre-aggregation or dedicated analytical systems for high-volume reporting.

## Key Takeaways

- **Window aggregate functions calculate `SUM`, `AVG`, `COUNT`, `MIN`, and `MAX` across related rows without collapsing the result set.**
- **`PARTITION BY` defines the calculation scope, while `ORDER BY` and the frame determine how order-sensitive aggregates operate.**
- **Correct data grain is critical: aggregate first when the window should operate on customers, months, products, or another higher-level entity.**
- **Running totals and moving calculations should use deterministic ordering and explicit frame semantics when correctness matters.**
- **For production workloads, measure sort and memory costs and consider pre-aggregation or analytical infrastructure when window calculations become expensive.**