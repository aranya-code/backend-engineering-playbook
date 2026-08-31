# 02- SUM OVER

## Overview

`SUM() OVER` combines the arithmetic behavior of `SUM()` with the row-preserving behavior of a window function.

A regular aggregate:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

produces one row per customer.

A windowed aggregate:

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

keeps every order while attaching the customer's total to each row.

This distinction makes `SUM() OVER` useful for backend reporting, running balances, contribution percentages, cumulative metrics, and time-series analytics.

## Basic Syntax

The general form is:

```sql
SUM(expression) OVER (
    PARTITION BY partition_expression
    ORDER BY ordering_expression
    frame_clause
)
```

Each part has a different responsibility:

| Component | Purpose |
|---|---|
| `SUM(expression)` | Defines what is accumulated |
| `OVER` | Converts the aggregate into a window calculation |
| `PARTITION BY` | Separates rows into independent calculation groups |
| `ORDER BY` | Defines logical order within each partition |
| Frame clause | Defines which rows contribute to the current calculation |

The `PARTITION BY` and `ORDER BY` clauses are optional, depending on the required semantics.

## Why `SUM() OVER` Exists

Traditional aggregation answers questions such as:

> What is the total revenue for each customer?

Window aggregation answers questions such as:

> What is the customer's total revenue while still returning every order?

That second requirement is common in production APIs and reporting systems.

For example, an order-detail response might need:

```text
order amount
customer lifetime total
customer running total
customer percentage contribution
```

A window function can calculate these values without collapsing the order-level result set.

## `SUM()` Without a Window

Before looking at windowed sums, distinguish the ordinary aggregate:

```sql
SELECT SUM(amount) AS total_revenue
FROM orders;
```

This returns a single aggregate row.

With grouping:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

the result has one row per customer.

The aggregation changes the result's grain.

## `SUM() OVER ()`

An empty window applies the sum to the entire input set:

```sql
SELECT
    order_id,
    amount,
    SUM(amount) OVER () AS total_revenue
FROM orders;
```

Every row receives the same total.

For:

| order_id | amount |
|---:|---:|
| 101 | 100 |
| 102 | 250 |
| 103 | 150 |

the result is conceptually:

| order_id | amount | total_revenue |
|---:|---:|---:|
| 101 | 100 | 500 |
| 102 | 250 | 500 |
| 103 | 150 | 500 |

This is particularly useful for percentage-of-total calculations.

## `PARTITION BY`

`PARTITION BY` divides the input rows into independent windows.

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

Conceptually:

```text
orders
   │
   ├── customer 1 ── SUM ── customer 1 total
   │
   ├── customer 2 ── SUM ── customer 2 total
   │
   └── customer 3 ── SUM ── customer 3 total
```

Rows are not physically grouped into separate result sets. The database evaluates the window over each logical partition and returns the original rows with the calculated value.

## Partition-Level Totals

Consider:

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

Input:

| order_id | customer_id | amount |
|---:|---:|---:|
| 101 | 1 | 100 |
| 102 | 1 | 200 |
| 103 | 2 | 75 |
| 104 | 2 | 125 |

Output:

| order_id | customer_id | amount | customer_total |
|---:|---:|---:|---:|
| 101 | 1 | 100 | 300 |
| 102 | 1 | 200 | 300 |
| 103 | 2 | 75 | 200 |
| 104 | 2 | 125 | 200 |

The calculation scope is customer-specific, but the result remains order-specific.

## Running Totals

Adding an `ORDER BY` makes the calculation order-sensitive.

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

For customer `1`:

```text
Order 1: 100       → 100
Order 2: 200       → 300
Order 3: 150       → 450
```

The frame:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

means:

> Start at the first row in the partition and accumulate through the current row.

For production financial or operational calculations, explicitly specifying this frame makes the intended semantics easier to review.

## Why Deterministic Ordering Matters

Avoid relying on:

```sql
ORDER BY created_at
```

when multiple records can have the same timestamp.

Prefer:

```sql
ORDER BY created_at, order_id
```

The unique identifier provides a deterministic tie-breaker.

This matters for:

- Running balances.
- Cumulative revenue.
- Event processing.
- Audit reports.
- Reproducible tests.
- Pagination-related analytics.

A timestamp often represents when something happened, but does not necessarily uniquely identify the sequence of events.

## `ROWS` vs `RANGE`

For running totals, `ROWS` and `RANGE` can produce different results when ordering values are duplicated.

Consider:

```sql
SUM(amount) OVER (
    ORDER BY created_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

versus:

```sql
SUM(amount) OVER (
    ORDER BY created_at
    RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

`ROWS` operates on physical/logical row positions.

`RANGE` groups rows with equivalent ordering values according to the window's ordering semantics.

For example, if two transactions share the same `created_at`, a `RANGE` frame can include both peer rows at the same ordering value, while a `ROWS` frame can advance one row at a time.

When the requirement is specifically:

> Add one row at a time in deterministic order.

use a deterministic `ORDER BY` with an explicit `ROWS` frame.

## Moving Sums

A bounded frame creates a rolling sum.

```sql
SELECT
    recorded_at,
    revenue,
    SUM(revenue) OVER (
        ORDER BY recorded_at
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_row_revenue
FROM daily_revenue;
```

The current row plus the six preceding rows are included.

This is useful for:

- Rolling revenue.
- Recent event counts.
- Operational metrics.
- Moving workload calculations.
- Time-series analysis.

Important distinction:

> `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` means seven rows, not necessarily seven calendar days.

If records are missing or timestamps are irregular, row count and elapsed time are different concepts.

## Partitioned Running Totals

Running totals become more useful when combined with partitions.

```sql
SELECT
    account_id,
    transaction_id,
    occurred_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY occurred_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS balance
FROM account_transactions;
```

Each account starts its own running calculation.

Conceptually:

```text
Account A
├── transaction 1 → balance 100
├── transaction 2 → balance 250
└── transaction 3 → balance 180

Account B
├── transaction 1 → balance 500
├── transaction 2 → balance 420
└── transaction 3 → balance 700
```

The partition boundary resets the cumulative calculation.

## Percentage of Total

A common production use case is calculating each row's contribution to the complete result set.

```sql
SELECT
    product_id,
    revenue,
    100.0 * revenue / NULLIF(SUM(revenue) OVER (), 0) AS revenue_percentage
FROM product_revenue;
```

The denominator is the total revenue across all returned rows.

`NULLIF` prevents division-by-zero errors.

For example:

```text
Product A = 200
Product B = 300
Product C = 500

Total = 1000

A = 20%
B = 30%
C = 50%
```

## Percentage Within a Partition

The same pattern works for group-level percentages:

```sql
SELECT
    customer_id,
    product_id,
    revenue,
    100.0 * revenue
        / NULLIF(
            SUM(revenue) OVER (
                PARTITION BY customer_id
            ),
            0
        ) AS customer_revenue_percentage
FROM customer_product_revenue;
```

Now the denominator is the customer's total rather than the global total.

This is useful for:

- Product mix.
- Customer spending distribution.
- Department budget allocation.
- Regional revenue composition.

## Combining `GROUP BY` and `SUM() OVER`

A window function can operate on rows produced by aggregation.

```sql
SELECT
    department_id,
    SUM(salary) AS department_salary,
    SUM(SUM(salary)) OVER () AS company_salary
FROM employees
GROUP BY department_id;
```

The conceptual processing is:

```text
employee rows
     ↓
GROUP BY department
     ↓
department salary rows
     ↓
window SUM across departments
     ↓
department + company totals
```

This is an important senior-level SQL pattern.

The inner `SUM(salary)` performs ordinary aggregation. The outer `SUM(...) OVER ()` performs window aggregation over the resulting department rows.

## Aggregation at the Correct Grain

Window functions operate over the rows available to their query block.

Suppose the requirement is:

> Calculate each customer's average monthly revenue.

Start by establishing the monthly grain:

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
    SUM(revenue) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM monthly_revenue;
```

The window operates on customer-month rows instead of individual order rows.

This separation makes complex analytical queries easier to reason about and test.

## Filtering and `SUM() OVER`

Filtering occurs before the window function in the same query block.

```sql
SELECT
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE status = 'completed';
```

Only completed orders participate in `customer_total`.

If the requirement is:

> Show completed orders, but calculate the total across all orders.

use a query boundary:

```sql
WITH order_metrics AS (
    SELECT
        order_id,
        customer_id,
        amount,
        status,
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
FROM order_metrics
WHERE status = 'completed';
```

This distinction is critical when building reporting queries.

## `SUM() OVER` vs `GROUP BY`

| Requirement | `GROUP BY` | `SUM() OVER` |
|---|---:|---:|
| One row per group | Excellent | No |
| Preserve detail rows | No | Excellent |
| Group total beside detail | Requires join/subquery | Excellent |
| Running total | No | Excellent |
| Percentage of total | Possible with additional query structure | Excellent |
| Rolling sum | No | Excellent |
| Aggregated reporting | Excellent | Sometimes |
| Row-level analytics | Limited | Excellent |

Use `GROUP BY` when aggregation changes the required result grain.

Use `SUM() OVER` when the aggregate is analytical context attached to existing rows.

## Real-World Backend Example

Suppose an API returns a customer's completed orders along with:

- Order amount.
- Customer lifetime completed revenue.
- Running revenue.
- Percentage contributed by each order.

A PostgreSQL query could be:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,

    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS lifetime_revenue,

    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_revenue,

    100.0 * amount
        / NULLIF(
            SUM(amount) OVER (
                PARTITION BY customer_id
            ),
            0
        ) AS revenue_percentage

FROM orders
WHERE
    customer_id = :customer_id
    AND status = 'completed'
ORDER BY
    created_at,
    order_id;
```

A Django or FastAPI service can execute this query and serialize the resulting rows directly into an API response.

The important architectural consideration is that the query is calculating analytics over the rows selected for that query. If "lifetime" means all historical orders but the API only retrieves a subset of rows, calculate the lifetime metric in a separate query layer or CTE.

## Financial Systems

`SUM() OVER` is particularly useful for transaction-ledger calculations:

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
    ) AS running_balance
FROM account_transactions
WHERE account_id = :account_id
ORDER BY
    occurred_at,
    transaction_id;
```

Production systems should explicitly define:

- Which transactions participate.
- Whether reversals are separate transactions.
- Which timestamp controls ordering.
- How equal timestamps are resolved.
- Whether pending transactions are included.
- How corrections are represented.

Do not rely on accidental database ordering for financial calculations.

## Multi-Tenant Applications

Tenant boundaries should be established before calculating tenant-scoped metrics.

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

The tenant filter prevents rows from other tenants from entering the query's window.

In multi-tenant Django or FastAPI systems, tenant isolation should be enforced consistently through the data-access and authorization layers rather than relying on individual developers to remember every filter.

## NULL Behavior

`SUM()` ignores `NULL` values.

For example:

```sql
SELECT
    SUM(amount)
FROM orders;
```

does not treat a `NULL` amount as zero; it excludes it from the aggregation.

If all values are `NULL`, the aggregate result is generally `NULL`, not `0`.

If application semantics require zero:

```sql
COALESCE(SUM(amount), 0)
```

For a windowed calculation:

```sql
COALESCE(
    SUM(amount) OVER (
        PARTITION BY customer_id
    ),
    0
) AS customer_total
```

Do not blindly use `COALESCE` without understanding whether `NULL` represents missing data or a legitimate business state.

## Data Types and Monetary Values

For monetary calculations, use an exact numeric type supported by the database, such as PostgreSQL `numeric`, rather than floating-point storage.

Example:

```sql
CREATE TABLE payments (
    payment_id BIGINT PRIMARY KEY,
    amount NUMERIC(12, 2) NOT NULL
);
```

Then:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

preserves exact decimal semantics appropriate for financial values.

Application code should also map the database value to an appropriate decimal representation rather than converting monetary amounts to binary floating-point values unnecessarily.

## Performance Considerations

Window calculations can require significant database work, especially when partitions are large or ordering is required.

Potential costs include:

- Sorting.
- Memory consumption.
- Temporary disk usage.
- CPU usage.
- Processing large partitions.
- Increased query latency.

For PostgreSQL, inspect the actual execution plan:

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

Pay particular attention to:

- Sort nodes.
- Actual row counts.
- Temporary file usage.
- Buffer reads.
- Execution time.
- Memory-intensive operations.

An index can help with filtering and may help the planner with ordering, but it does not guarantee that the window operation will avoid sorting.

## Large-Scale Production Systems

A window query can be logically correct while still being architecturally inappropriate for a high-throughput API.

Avoid repeatedly calculating expensive lifetime or historical windows over very large tables during synchronous requests.

Possible strategies include:

- Restricting the input time range.
- Pre-aggregating historical data.
- Maintaining summary tables.
- Materialized views.
- Read replicas.
- Background computation.
- Caching stable analytical results.
- Moving heavy analytics to an analytical database.

For example:

```text
Django / FastAPI
       │
       ▼
Application database
       │
       ├── transactional queries
       │
       └── pre-aggregated metrics
                    │
                    ▼
              analytical query
```

The correct choice depends on freshness requirements, workload size, query frequency, and operational complexity.

## Security Considerations

Window functions themselves do not create a security boundary.

The security boundary comes from the rows supplied to the query.

For multi-tenant or authorization-sensitive systems:

- Apply tenant filters correctly.
- Apply authorization constraints before calculating sensitive aggregates.
- Avoid exposing global totals to users who should only see scoped totals.
- Parameterize user-provided values.
- Review CTEs and subqueries for accidental scope expansion.

For example, a global:

```sql
SUM(amount) OVER ()
```

may expose information about other customers if the query was intended to be customer-scoped.

## Common Mistakes

### Mistaking `SUM() OVER` for `GROUP BY`

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

does not return one row per customer.

It returns one calculated value for every input row.

### Forgetting the Calculation Grain

If the window receives order-level rows, it calculates over order-level rows.

Aggregate first when the desired metric is based on monthly, daily, or product-level data.

### Omitting a Tie-Breaker

Avoid:

```sql
ORDER BY created_at
```

when timestamps are not unique.

Prefer:

```sql
ORDER BY created_at, order_id
```

for deterministic row ordering.

### Confusing `ROWS` With Time

This:

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

means seven rows, not seven days.

### Filtering Before the Wrong Calculation

This:

```sql
WHERE status = 'completed'
```

removes other rows before the window calculation.

If the aggregate must include those rows, move the filter outside the window-producing query.

### Assuming `SUM()` Returns Zero for No Values

`SUM()` can return `NULL`.

Use `COALESCE` only when the application's semantics require a zero value.

### Running Expensive Windows in API Requests

A window calculation over millions of rows can become a latency bottleneck.

Measure the query under realistic production data volumes.

### Relying on Implicit Ordering

Without an explicit `ORDER BY`, SQL does not guarantee row order.

Never build running balances or cumulative business logic around accidental physical row order.

## Interview Traps

| Question | Correct answer |
|---|---|
| Does `SUM() OVER` collapse rows? | No. It preserves the input rows. |
| What does `PARTITION BY` do? | It creates independent calculation scopes within the result. |
| What does `ORDER BY` do inside `OVER`? | It defines logical order for order-sensitive window calculations. |
| Does window `ORDER BY` determine final output order? | No. Use the query-level `ORDER BY` for final result ordering. |
| How do you calculate a running total? | Use `SUM(...) OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`. |
| How do you calculate a partition total? | Use `SUM(...) OVER (PARTITION BY ...)`. |
| How do you calculate a global total beside every row? | Use `SUM(...) OVER ()`. |
| Why use `ROWS` for a running total? | It makes row-by-row frame semantics explicit. |
| Does `WHERE` affect a window aggregate? | Yes. Filtering in the same query block occurs before the window calculation. |
| Can `GROUP BY` and window aggregation be combined? | Yes. A window function can operate over the grouped result. |
| What happens to `NULL` values in `SUM()`? | They are ignored; an all-`NULL` input can produce `NULL`. |

## Best Practices

- Treat `SUM() OVER` as an analytical operation that preserves row-level results.
- Define the required result grain before choosing the window.
- Use `PARTITION BY` for independent group-level calculations.
- Use deterministic `ORDER BY` expressions for cumulative calculations.
- Prefer explicit `ROWS` frames when row-by-row semantics matter.
- Use `COALESCE` only when `NULL` and zero have equivalent business meaning.
- Use CTEs or derived tables to establish the correct aggregation grain.
- Apply filters at the correct query stage.
- Parameterize application inputs rather than interpolating SQL strings.
- Inspect PostgreSQL execution plans for large window queries.
- Pre-aggregate or move analytical workloads when synchronous window calculations become expensive.
- Test duplicate timestamps, empty datasets, `NULL` values, and boundary conditions.

## Key Takeaways

- **`SUM() OVER` calculates totals without collapsing the underlying rows, making it ideal for row-level analytical context.**
- **`PARTITION BY` controls calculation scope, while `ORDER BY` and the frame control cumulative and rolling behavior.**
- **Running totals should use deterministic ordering and explicit `ROWS` semantics when row-by-row correctness matters.**
- **Filtering and aggregation boundaries determine which rows participate in the window, so query structure directly affects correctness.**
- **For large production datasets, measure window-query cost and consider pre-aggregation or dedicated analytical infrastructure when necessary.**