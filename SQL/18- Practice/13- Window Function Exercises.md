# 13- Window Function Exercises

## Overview

Window functions perform calculations across a related set of rows while preserving the individual rows in the result. They are one of the most important SQL tools for solving ranking, running-total, latest-record, comparison, and time-series problems without collapsing data through `GROUP BY`.

The core mental model is:

```text
GROUP BY
    → many rows become one row per group

WINDOW FUNCTION
    → rows remain visible while calculations use related rows
```

Window functions are especially useful in backend systems for:

- Latest record per entity.
- Top-N records per group.
- Ranking and leaderboards.
- Running totals.
- Moving averages.
- Month-over-month comparisons.
- Change detection.
- Pagination and reporting.
- Deduplication.
- Data-quality analysis.
- Operational analytics.

These exercises use PostgreSQL syntax and progressively move from basic window expressions to production-oriented query design.

---

## Practice Schema

Use the following schema for the exercises:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status text NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    total_amount numeric(12, 2) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    price numeric(12, 2) NOT NULL,
    active boolean NOT NULL DEFAULT true
);

CREATE TABLE order_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    product_id bigint NOT NULL REFERENCES products(id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL
);

CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    amount numeric(12, 2) NOT NULL,
    status text NOT NULL
        CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    paid_at timestamptz
);
```

Useful indexes:

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC, id DESC);

CREATE INDEX orders_status_created_idx
    ON orders (status, created_at DESC);

CREATE INDEX payments_order_paid_idx
    ON payments (order_id, paid_at DESC, id DESC);

CREATE INDEX order_items_product_idx
    ON order_items (product_id);
```

---

## Window Function Mental Model

A window function has the general structure:

```sql
function_name(...) OVER (
    PARTITION BY ...
    ORDER BY ...
    ROWS BETWEEN ...
)
```

The major components are:

| Component | Purpose |
|---|---|
| `PARTITION BY` | Defines independent groups |
| `ORDER BY` | Defines row ordering within each group |
| Frame | Defines which rows are visible to the calculation |
| Function | Performs ranking, aggregation, navigation, or comparison |

Example:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

Every order remains visible, but each row also contains the total for its customer.

---

## Basic Window Aggregation

Start with a simple aggregate window.

```sql
SELECT
    id,
    customer_id,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM orders;
```

### Exercises

Write queries to calculate:

1. Total revenue per customer while preserving every order.
2. Average order value per customer.
3. Maximum order value per customer.
4. Minimum order value per customer.
5. Number of orders per customer.
6. Number of completed orders per customer.

Compare these results with equivalent `GROUP BY` queries.

---

## `PARTITION BY`

`PARTITION BY` divides rows into independent windows.

```sql
SELECT
    id,
    customer_id,
    status,
    total_amount,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS customer_order_count
FROM orders;
```

### Exercises

Create window calculations partitioned by:

1. Customer.
2. Order status.
3. Customer and order status.
4. Month of order creation.
5. Payment status.

For each query, explain exactly which rows belong to each partition.

---

## `ORDER BY` Inside a Window

Window ordering determines the logical sequence used by the function.

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS order_number
FROM orders;
```

The `id` tie-breaker makes ordering deterministic when timestamps are equal.

### Exercises

For each customer, calculate:

1. Oldest order number.
2. Newest order number.
3. Chronological order number.
4. Reverse chronological order number.
5. Ranking by order amount.
6. Ranking by completion time.

---

## `ROW_NUMBER()`

`ROW_NUMBER()` assigns a unique sequential number within each window.

```sql
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS row_number
FROM orders;
```

Unlike ranking functions, every row receives a different number.

### Exercises

Use `ROW_NUMBER()` to:

1. Find the latest order per customer.
2. Find the earliest order per customer.
3. Find the latest completed order per customer.
4. Find the highest-value order per customer.
5. Find the second-highest order per customer.
6. Find the third-most-recent order per customer.

---

## Filtering Window Function Results

Window functions cannot normally be referenced directly in the same `WHERE` clause in which they are calculated.

Use a CTE or derived table:

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE row_number = 1;
```

### Exercises

Use this pattern to:

1. Return one latest order per customer.
2. Return the latest three orders per customer.
3. Return the top five orders by value per customer.
4. Return the second-most-recent order per customer.
5. Return customers whose latest order is completed.

---

## `RANK()`

`RANK()` gives tied rows the same rank and leaves gaps after ties.

Example:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    RANK() OVER (
        PARTITION BY customer_id
        ORDER BY total_amount DESC
    ) AS amount_rank
FROM orders;
```

If amounts are:

```text
1000
1000
800
500
```

the ranks are:

```text
1
1
3
4
```

### Exercises

Use `RANK()` to:

1. Rank orders by value within each customer.
2. Rank customers by total revenue.
3. Rank products by total quantity sold.
4. Rank monthly revenue.
5. Rank employees by compensation if an employee table is added.

---

## `DENSE_RANK()`

`DENSE_RANK()` also assigns the same rank to ties but does not leave gaps.

For:

```text
1000
1000
800
500
```

the ranks are:

```text
1
1
2
3
```

### Exercises

Compare `RANK()` and `DENSE_RANK()` for:

1. Customer revenue.
2. Product sales.
3. Order values.
4. Monthly revenue.
5. API leaderboard data.

Explain when gaps in ranking are meaningful and when they are undesirable.

---

## `ROW_NUMBER()` vs `RANK()` vs `DENSE_RANK()`

| Function | Ties share rank? | Gaps after ties? | Unique row number? |
|---|---:|---:|---:|
| `ROW_NUMBER()` | No | No | Yes |
| `RANK()` | Yes | Yes | No |
| `DENSE_RANK()` | Yes | No | No |

### Exercise

Given:

```text
customer_id | revenue
-------------+--------
1            | 1000
2            | 1000
3            | 800
4            | 500
```

Produce the output using all three functions and explain the difference.

---

## Top-N Per Group

One of the most common real-world window-function problems is:

> Return the top N records for every group.

Example:

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS row_number
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE row_number <= 3;
```

### Exercises

Find:

1. Top three orders per customer.
2. Top five completed orders per customer.
3. Top three products by quantity sold per month.
4. Top two payments by amount per order.
5. Top five customers per month by revenue.

For each query, define whether ties should increase the number of returned rows.

---

## Latest Row Per Group

This pattern appears frequently in backend APIs.

```sql
WITH latest_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM orders AS o
)
SELECT *
FROM latest_orders
WHERE row_number = 1;
```

### Exercises

Find:

1. Latest order per customer.
2. Latest completed order per customer.
3. Latest payment per order.
4. Latest failed payment per order.
5. Latest order status record if a status-history table is introduced.
6. Latest record for every tenant if `tenant_id` is added.

---

## Deterministic Ordering

This is dangerous:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

If multiple rows have the same timestamp, their relative ordering may not be deterministic.

Prefer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, id DESC
)
```

### Exercise

Create test data where two orders have exactly the same `created_at`.

Verify that:

1. Ordering without a tie-breaker can be ambiguous.
2. Ordering with `id DESC` is deterministic.
3. Your latest-record API returns the same record consistently.

---

## Running Totals

Window functions are ideal for cumulative calculations.

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_revenue
FROM orders;
```

### Exercises

Calculate:

1. Running revenue per customer.
2. Running order count per customer.
3. Running completed revenue.
4. Running quantity sold per product.
5. Running monthly revenue.
6. Running payment amount per order.

---

## Window Frames

The window frame determines which ordered rows participate in the calculation.

Common frame syntax:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

This means:

```text
first row
   ↓
all previous rows
   ↓
current row
```

### Exercises

Write queries using:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

to calculate:

1. Running customer revenue.
2. Running order count.
3. Running product quantity.
4. Running monthly revenue.

Then test:

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

for a three-row moving calculation.

---

## Moving Average

A moving average uses a limited window frame.

```sql
SELECT
    id,
    created_at,
    total_amount,
    AVG(total_amount) OVER (
        ORDER BY created_at, id
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_average
FROM orders;
```

### Exercises

Calculate:

1. Three-order moving average.
2. Seven-order moving average.
3. Three-month moving revenue average.
4. Seven-day average order value.
5. Customer-specific moving average.

Clearly define whether the frame represents rows or actual time intervals.

---

## `LAG()`

`LAG()` accesses a previous row without requiring a self-join.

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount,
    LAG(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_order_amount
FROM orders;
```

### Exercises

Use `LAG()` to calculate:

1. Previous order amount.
2. Previous order timestamp.
3. Time since previous order.
4. Difference between current and previous order amount.
5. Percentage change from the previous order.
6. Previous month's revenue.

---

## `LEAD()`

`LEAD()` accesses a later row.

```sql
SELECT
    id,
    customer_id,
    created_at,
    LEAD(created_at) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS next_order_at
FROM orders;
```

### Exercises

Use `LEAD()` to find:

1. Next order date.
2. Next payment date.
3. Next event in a status history.
4. Time until the next customer order.
5. The next monthly revenue value.

---

## `LAG()` and `LEAD()` for Change Detection

Suppose a status-history table contains:

```text
entity_id | status      | changed_at
----------+-------------+-----------
10        | pending     | ...
10        | processing  | ...
10        | completed   | ...
```

Use:

```sql
LAG(status) OVER (
    PARTITION BY entity_id
    ORDER BY changed_at
)
```

to inspect the previous state.

### Exercises

Create a status-history table:

```sql
CREATE TABLE order_status_history (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    status text NOT NULL,
    changed_at timestamptz NOT NULL DEFAULT now()
);
```

Then:

1. Find every status transition.
2. Show previous status.
3. Show next status.
4. Calculate time spent in each status.
5. Find orders that transitioned directly from `pending` to `completed`.
6. Find orders that never entered `processing`.

---

## `FIRST_VALUE()`

`FIRST_VALUE()` returns the first value according to the window ordering.

```sql
SELECT
    id,
    customer_id,
    total_amount,
    FIRST_VALUE(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS first_order_amount
FROM orders;
```

### Exercises

Calculate:

1. First order amount per customer.
2. First order timestamp per customer.
3. First completed order amount.
4. First payment amount per order.
5. First product purchase quantity per customer.

---

## `LAST_VALUE()`

`LAST_VALUE()` requires careful frame handling.

A common mistake is:

```sql
LAST_VALUE(total_amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, id
)
```

The default frame may end at the current row, meaning the result can be the current row rather than the final row in the partition.

Use an explicit frame when you need the entire partition:

```sql
LAST_VALUE(total_amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, id
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
) AS last_order_amount
```

### Exercises

Use `LAST_VALUE()` to calculate:

1. Last order amount per customer.
2. Last order timestamp.
3. Last completed order.
4. Final payment amount per order.
5. Final status in a status-history table.

Compare the behavior with and without the explicit frame.

---

## `NTH_VALUE()`

`NTH_VALUE()` retrieves a value from a specified position in the window.

Example:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    NTH_VALUE(total_amount, 2) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS second_order_amount
FROM orders;
```

### Exercises

Calculate:

1. Second order amount.
2. Third order amount.
3. Second-highest order value.
4. Third payment amount per order.
5. Fifth event in a customer activity stream.

Explain why explicit frame boundaries may matter.

---

## Percentage of Group Total

Window aggregates can calculate percentages without a separate aggregation query.

```sql
SELECT
    id,
    customer_id,
    total_amount,
    total_amount / NULLIF(
        SUM(total_amount) OVER (
            PARTITION BY customer_id
        ),
        0
    ) AS percentage_of_customer_revenue
FROM orders;
```

### Exercises

Calculate:

1. Each order's percentage of customer revenue.
2. Each product's percentage of total sales.
3. Each month's percentage of annual revenue.
4. Each payment's percentage of order value.
5. Each customer's percentage of total company revenue.

---

## Customer Revenue Ranking

Build the revenue first, then rank it.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_revenue,
    RANK() OVER (
        ORDER BY total_revenue DESC
    ) AS revenue_rank
FROM customer_revenue;
```

### Exercises

Return:

1. Customer revenue rank.
2. Dense revenue rank.
3. Revenue percentage of total.
4. Top 10 customers.
5. Customers in the top 10% by revenue.

---

## Ranking Within Each Month

Combine aggregation, date bucketing, partitioning, and ranking.

```sql
WITH monthly_customer_revenue AS (
    SELECT
        date_trunc('month', created_at) AS month,
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY
        date_trunc('month', created_at),
        customer_id
)
SELECT
    month,
    customer_id,
    revenue,
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank
FROM monthly_customer_revenue;
```

### Exercises

Calculate:

1. Top 3 customers each month.
2. Top 5 products each month.
3. Monthly customer revenue rank.
4. Monthly order-count rank.
5. Monthly revenue percentile.

---

## Month-over-Month Comparison

Use `LAG()` after producing monthly aggregates.

```sql
WITH monthly_revenue AS (
    SELECT
        date_trunc('month', created_at) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY date_trunc('month', created_at)
),
with_previous AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (
            ORDER BY month
        ) AS previous_revenue
    FROM monthly_revenue
)
SELECT
    month,
    revenue,
    previous_revenue,
    revenue - previous_revenue AS revenue_change
FROM with_previous
ORDER BY month;
```

### Exercises

Calculate:

1. Month-over-month revenue change.
2. Month-over-month percentage change.
3. Month-over-month order-count change.
4. Customer-level monthly revenue change.
5. Product-level monthly sales change.

Handle the first month explicitly.

---

## Detecting Changes in Customer Behavior

Use `LAG()` to compare consecutive orders.

### Exercise

Find customers whose order value:

1. Increased from the previous order.
2. Decreased from the previous order.
3. Increased by more than 50%.
4. Decreased by more than 50%.
5. Changed from below `100` to above `1000`.

Return:

- Customer ID.
- Current order.
- Previous order.
- Current value.
- Previous value.
- Percentage change.

---

## Time Between Events

Use `LAG()` to compare timestamps.

```sql
SELECT
    customer_id,
    id,
    created_at,
    created_at
        - LAG(created_at) OVER (
            PARTITION BY customer_id
            ORDER BY created_at, id
        ) AS time_since_previous_order
FROM orders;
```

### Exercises

Find:

1. Average time between customer orders.
2. Customers whose next order took more than 30 days.
3. Customers with orders less than one hour apart.
4. Longest customer inactivity period.
5. Median-like percentile distribution of order intervals.

---

## `NTILE()`

`NTILE()` divides ordered rows into approximately equal buckets.

```sql
SELECT
    customer_id,
    total_revenue,
    NTILE(10) OVER (
        ORDER BY total_revenue DESC
    ) AS revenue_decile
FROM customer_revenue;
```

### Exercises

Use `NTILE()` to divide customers into:

1. Two revenue groups.
2. Four quartiles.
3. Five quintiles.
4. Ten deciles.
5. One hundred percentile-style buckets.

Explain why `NTILE()` does not necessarily produce equal revenue amounts per bucket.

---

## Percentiles

PostgreSQL provides ordered-set aggregates such as `percentile_cont()` and `percentile_disc()`.

These are aggregates rather than ordinary window functions, but they are useful when combined with window-oriented reporting.

### Exercises

Calculate:

1. Median order value.
2. 90th percentile order value.
3. 95th percentile order value.
4. Median order value per customer.
5. 95th percentile order value per month.

Compare percentile results with `NTILE()`.

---

## Window Function with `FILTER`

Window aggregates can use filtered aggregation.

Example:

```sql
SELECT
    customer_id,
    id,
    total_amount,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) OVER (
        PARTITION BY customer_id
    ) AS completed_orders
FROM orders;
```

### Exercises

Calculate per customer:

1. Total orders.
2. Completed orders.
3. Cancelled orders.
4. Pending orders.
5. Completed revenue.
6. Cancelled revenue.

Preserve every individual order in the output.

---

## Window Functions and `GROUP BY`

A common production pattern is:

```text
Raw rows
   ↓
GROUP BY
   ↓
One row per business entity
   ↓
Window function
   ↓
Ranking/comparison
```

Example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_revenue;
```

### Exercises

Use this pattern for:

1. Customer revenue ranking.
2. Product quantity ranking.
3. Monthly revenue ranking.
4. Monthly top customers.
5. Customer order-count ranking.

---

## Window Functions and `DISTINCT`

Be careful when combining `DISTINCT` and windows.

A window function can cause rows that otherwise appear identical to become different because the calculated window value differs.

### Exercise

Create a query using:

```sql
SELECT DISTINCT ...
```

and a window function.

Determine:

1. Whether duplicates are actually removed.
2. Whether the window value changes row identity.
3. Whether `GROUP BY` would express the intent more clearly.

---

## Window Functions for Deduplication

A standard deduplication technique is:

```sql
WITH ranked_rows AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY email
            ORDER BY created_at, id
        ) AS row_number
    FROM staging_customers
)
SELECT *
FROM ranked_rows
WHERE row_number = 1;
```

### Exercises

Using a staging table:

```sql
CREATE TABLE staging_customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

1. Identify duplicate emails.
2. Select the canonical row.
3. Identify duplicate rows for deletion.
4. Keep the newest row instead of the oldest.
5. Keep the row with the most complete data.
6. Produce a reconciliation report.

Never delete duplicates without first validating the target set and dependent relationships.

---

## Window Functions for Pagination

Window functions can support some reporting-style pagination, but they are not automatically better than keyset pagination.

Example:

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE row_number BETWEEN 101 AND 120;
```

### Exercise

Compare this approach with:

```sql
SELECT *
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

Evaluate:

- Execution plan.
- Rows processed.
- Memory.
- Latency at deep pages.
- Index usage.
- Suitability for high-volume APIs.

For large APIs, keyset pagination is often preferable when the ordering requirements permit it.

---

## Window Functions and API Design

Consider:

```text
GET /customers/{id}/orders
```

The endpoint may need:

- Latest order.
- Previous order.
- Running revenue.
- Order rank.
- Percentage contribution.

A single SQL query can sometimes produce all of these values.

### Exercise

Design an API query that returns:

```json
{
  "order_id": 123,
  "amount": "450.00",
  "order_rank": 3,
  "previous_order_amount": "300.00",
  "running_revenue": "2450.00"
}
```

Requirements:

- One database query.
- Deterministic ordering.
- No N+1 queries.
- Appropriate indexes.
- Bounded result set.
- Correct behavior under concurrent inserts.

---

## Window Functions and Concurrency

Window calculations operate on the rows visible to the query according to the transaction's isolation and snapshot semantics.

They do not automatically lock rows.

For example:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS row_number
FROM orders;
```

This is a read operation. Another transaction can insert or update data independently.

### Exercises

Analyze what happens when:

1. A new order is inserted during a report.
2. An order changes status during a report.
3. The query runs against a read replica.
4. Multiple workers generate rankings simultaneously.
5. A transaction uses a stronger isolation level.

Explain whether the application needs a consistent snapshot, locking, or merely an eventually consistent report.

---

## Window Functions and Read Replicas

Window-heavy analytical queries can be expensive.

For example:

```text
API
 ↓
Read replica
 ↓
Sort / partition / window calculation
 ↓
Response
```

This may reduce load on the primary, but it does not eliminate the query cost.

### Exercises

For a large ranking query:

1. Determine whether it can run safely on a replica.
2. Measure replica lag.
3. Determine whether the query can interfere with replica replay.
4. Decide whether the query belongs on an OLAP system.
5. Compare a precomputed materialized view with live calculation.

---

## Window Function Performance

Window functions often require PostgreSQL to organize rows according to the window's partition and ordering requirements.

Potential costs include:

- Sorting.
- Large intermediate result sets.
- Memory consumption.
- Temporary disk I/O.
- Multiple window passes.
- Large partitions.
- High CPU usage.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS row_number
FROM orders;
```

### Exercises

Investigate:

1. A query with one window function.
2. A query with multiple windows.
3. A query with a large partition.
4. A query with an outer filter.
5. A query where an index supports the desired ordering.

Compare:

- Planning time.
- Execution time.
- Buffer usage.
- Sort behavior.
- Temporary I/O.
- Rows processed.

---

## Multiple Window Definitions

You may need several calculations using the same partition and ordering.

Example:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS row_number,
    LAG(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

### Exercise

Build one query that calculates:

- Row number.
- Previous amount.
- Next amount.
- Running revenue.
- Customer total.
- First order amount.
- Last order amount.

Ensure that ordering and frame definitions are intentional.

---

## Named Windows

PostgreSQL allows a named window specification.

Example:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount,
    ROW_NUMBER() OVER customer_window AS row_number,
    LAG(total_amount) OVER customer_window AS previous_amount
FROM orders
WINDOW customer_window AS (
    PARTITION BY customer_id
    ORDER BY created_at, id
);
```

### Exercise

Rewrite a query containing three or more identical window definitions using a named window.

Evaluate whether the resulting SQL is easier to maintain.

---

## Window Functions with Joins

Joining before applying a window function can change row cardinality.

For example, joining:

```text
orders
    ↓
order_items
```

can create multiple rows per order.

A window calculation intended to operate once per order may then operate over duplicated order rows.

### Exercise

Build a query that:

1. Joins orders to order items.
2. Calculates order-level revenue.
3. Applies a window function.
4. Detects whether the join changes the expected grain.
5. Corrects the query using a pre-aggregation CTE.

Explicitly document the grain before and after each stage.

---

## Window Functions and Aggregation Errors

Consider:

```sql
SELECT
    o.customer_id,
    oi.product_id,
    SUM(oi.quantity) AS quantity,
    SUM(oi.quantity) OVER (
        PARTITION BY o.customer_id
    ) AS customer_quantity
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
GROUP BY
    o.customer_id,
    oi.product_id;
```

The result may not represent the intended business grain.

### Exercise

Rewrite the query so that:

1. Product quantity is calculated correctly.
2. Customer total quantity is calculated correctly.
3. Product percentage of customer quantity is calculated.
4. No join multiplication occurs.

---

## Advanced Exercise: Customer Order Lifecycle

Build a single query that returns every order with:

- Customer ID.
- Order ID.
- Order amount.
- Order timestamp.
- Previous order amount.
- Next order amount.
- Running customer revenue.
- Total customer revenue.
- Order number.
- Percentage of customer revenue.
- Difference from previous order.
- Time since previous order.

Use:

- `ROW_NUMBER()`
- `LAG()`
- `LEAD()`
- `SUM() OVER`
- `NULLIF()`

---

## Advanced Exercise: Customer Leaderboard

Build a customer leaderboard containing:

- Customer ID.
- Customer name.
- Completed order count.
- Completed revenue.
- Revenue rank.
- Dense revenue rank.
- Revenue percentage of total.
- Revenue quartile.
- Previous customer's revenue.

Requirements:

- Exclude customers without completed orders.
- Define deterministic ordering.
- Handle revenue ties correctly.
- Use appropriate window functions.

---

## Advanced Exercise: Monthly Business Dashboard

Create a monthly dashboard containing:

- Month.
- Order count.
- Completed order count.
- Revenue.
- Completed revenue.
- Average order value.
- Previous month's revenue.
- Revenue change.
- Revenue percentage change.
- Running annual revenue.
- Monthly revenue rank.

Consider how to handle months with no orders.

---

## Advanced Exercise: Top Products Per Month

Using `order_items`, build a report containing:

- Month.
- Product ID.
- Quantity sold.
- Revenue.
- Product rank within month.
- Percentage of monthly quantity.
- Percentage of monthly revenue.

Requirements:

- Completed orders only.
- Deterministic ranking.
- Correct aggregation grain.
- No double counting.
- Appropriate indexes.

---

## Advanced Exercise: Order Status Duration

Using `order_status_history`, calculate:

- Order ID.
- Status.
- Status start time.
- Status end time.
- Duration in status.
- Previous status.
- Next status.
- Sequence number.

Use:

```sql
LAG()
LEAD()
```

to construct the lifecycle.

Then answer:

1. Which status has the longest average duration?
2. Which orders stayed pending for more than 24 hours?
3. Which orders skipped a required state?
4. Which transitions occur most frequently?

---

## Advanced Exercise: Detect Suspicious Ordering Patterns

Use window functions to identify:

1. Multiple orders from the same customer within five minutes.
2. Large increases in order amount.
3. Repeated failed payments.
4. Rapid changes in order status.
5. Multiple high-value orders shortly after account creation.

Explain how these queries could support fraud detection or operational alerting without becoming the sole authorization mechanism.

---

## Advanced Exercise: Customer Retention Cohorts

Create a cohort analysis using:

- Customer first order month.
- Subsequent order months.
- Months since first order.
- Number of active customers.
- Revenue by cohort.

Useful techniques include:

```text
MIN()
DATE_TRUNC()
LAG()
SUM() OVER
```

### Exercise

Produce:

```text
cohort_month
activity_month
months_since_signup
active_customers
revenue
```

Then calculate retention percentages.

---

## Advanced Exercise: Running Inventory

Assume an inventory movement table:

```sql
CREATE TABLE inventory_movements (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id bigint NOT NULL REFERENCES products(id),
    quantity_change integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

Calculate:

- Running inventory quantity.
- Previous inventory quantity.
- Inventory changes.
- First movement.
- Latest movement.
- Products that reached zero.
- Products that became negative.

Discuss why a calculated running balance may differ from a transactional inventory system that maintains explicit stock state.

---

## Advanced Exercise: Data Quality Detection

Use window functions to find:

1. Duplicate business keys.
2. Repeated events.
3. Out-of-order timestamps.
4. Unexpected status transitions.
5. Multiple records that should be unique.
6. Customers with suspiciously rapid activity.

For every detection query, distinguish:

```text
Detection
    ≠
Correction
    ≠
Authorization
```

A diagnostic query should not silently mutate production data.

---

## Advanced Exercise: SQL vs Application Code

For each problem, decide whether the calculation belongs in SQL or Python:

| Problem | SQL | Python | Decision |
|---|---:|---:|---|
| Rank millions of rows | ✓ | Possible but expensive | ? |
| Format API response | Possible | ✓ | ? |
| Running database total | ✓ | Possible but risky | ? |
| Complex ML scoring | Usually not | ✓ | ? |
| Latest record per group | ✓ | Possible but inefficient | ? |
| Small result transformation | Possible | ✓ | ? |

Explain your decision based on:

- Data volume.
- Network transfer.
- Database CPU.
- Application CPU.
- Query frequency.
- Consistency.
- Operational complexity.

---

## Django Exercise

Design a Django endpoint:

```text
GET /customers/{id}/orders/analytics
```

Return:

- Order number.
- Running revenue.
- Previous order amount.
- Next order amount.
- Customer total revenue.

Determine:

1. Whether the ORM can express the query cleanly.
2. Whether `Window`, `RowNumber`, `Lag`, `Lead`, and `Sum` expressions are appropriate.
3. Whether raw SQL is justified.
4. How to avoid N+1 queries.
5. How to test generated SQL.
6. How to inspect the execution plan.

Do not move millions of rows into Python merely to perform a calculation that PostgreSQL can efficiently execute.

---

## FastAPI and SQLAlchemy Exercise

Implement the same analytics endpoint using SQLAlchemy.

Requirements:

- One database query.
- Parameterized SQL.
- Explicit ordering.
- Appropriate indexes.
- Bounded pagination.
- Typed response model.
- Execution-plan validation.

Compare the generated SQL with the handwritten PostgreSQL version.

---

## Production API Exercise

Design:

```text
GET /customers/top
```

Requirements:

- Top 100 customers.
- Completed orders only.
- Revenue ranking.
- Dense ranking.
- Revenue percentage.
- Stable ordering.
- Tenant isolation.
- No N+1 queries.
- Read replica support if consistency permits.
- Timeout protection.

Decide whether the calculation should happen live or through:

- Materialized view.
- Cached result.
- Precomputed read model.
- OLAP query.

Justify the choice based on workload and freshness requirements.

---

## Security Exercise

Design a multi-tenant window query.

Requirements:

```text
Tenant A
    ↓
Only Tenant A rows
    ↓
Window calculation
    ↓
Tenant A result
```

Test for:

1. Missing tenant predicates.
2. Cross-tenant joins.
3. RLS interaction.
4. Application authorization.
5. Read-replica routing.
6. Cached leaderboard isolation.

Ensure that window functions never accidentally calculate across tenants.

---

## Performance Exercise

Create a dataset with at least:

```text
1 million orders
100,000 customers
```

Benchmark:

1. `ROW_NUMBER()` by customer.
2. `RANK()` by customer.
3. Running revenue.
4. `LAG()` by customer.
5. Multiple window functions.
6. Top-N per customer.
7. Equivalent correlated subquery.
8. Equivalent self-join.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

Record:

- Execution time.
- Planning time.
- Rows processed.
- Sort operations.
- Buffer reads/hits.
- Temporary I/O.
- CPU utilization.

---

## Production Troubleshooting Workflow

When a window-function query is slow:

1. Define the expected result grain.
2. Verify row counts before the window stage.
3. Check whether joins multiplied rows.
4. Inspect `PARTITION BY`.
5. Inspect `ORDER BY`.
6. Inspect frame definitions.
7. Run `EXPLAIN (ANALYZE, BUFFERS)`.
8. Check sorting and temporary I/O.
9. Check cardinality estimates.
10. Check index usefulness.
11. Check query frequency using `pg_stat_statements`.
12. Check database CPU and memory.
13. Check lock and transaction behavior.
14. Check whether a replica or OLAP system is more appropriate.
15. Test with production-scale data.

A window function may be perfectly correct while still being the wrong architecture for a frequently executed large analytical workload.

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Using `GROUP BY` when rows must remain visible | Confusing aggregation with windowing | Use window functions |
| Using a window function without `PARTITION BY` | Forgetting grouping scope | Define the business partition |
| Non-deterministic ordering | Timestamp ties | Add a stable tie-breaker |
| Filtering directly on a window result | SQL evaluation-order misunderstanding | Use CTE/derived table |
| Using `RANK()` when unique rows are required | Misunderstanding ties | Use `ROW_NUMBER()` |
| Using `ROW_NUMBER()` when ties should share rank | Wrong ranking semantics | Use `RANK()` or `DENSE_RANK()` |
| Misusing `LAST_VALUE()` | Ignoring window frame | Specify the required frame |
| Ignoring join multiplication | Window operates on duplicated rows | Pre-aggregate at the correct grain |
| Using windows for deep pagination | Expensive intermediate processing | Prefer keyset pagination |
| Moving millions of rows to Python | Avoiding SQL complexity | Perform relational computation in PostgreSQL |
| Running expensive windows on OLTP primary | Reporting workload mixed with transactions | Use replicas, read models, or OLAP |
| Ignoring tenant scope | Partition spans multiple tenants | Include tenant isolation in query design |
| Assuming an index guarantees fast windows | Window may still require sorting | Validate the execution plan |
| Ignoring temporary I/O | Large windows spill to disk | Inspect memory and sort behavior |
| Assuming concurrent reads are locked | Window functions are analytical reads | Add locking only when business semantics require it |

---

## Production Design Checklist

### Correctness

- [ ] Result grain is explicitly defined.
- [ ] `PARTITION BY` matches business grouping.
- [ ] `ORDER BY` is deterministic.
- [ ] Window frame is intentional.
- [ ] Ties have defined semantics.
- [ ] `NULL` behavior is understood.
- [ ] Join cardinality is validated.
- [ ] First/last-row behavior is tested.

### Performance

- [ ] Query plan has been inspected.
- [ ] Large sorts are understood.
- [ ] Temporary I/O is monitored.
- [ ] Intermediate result size is bounded.
- [ ] Query frequency is known.
- [ ] Required indexes have been evaluated.
- [ ] Large partitions are identified.
- [ ] OLTP versus OLAP workload placement is intentional.

### API Integration

- [ ] No N+1 queries.
- [ ] Result size is bounded.
- [ ] Pagination strategy is appropriate.
- [ ] Database timeout is configured.
- [ ] Application timeout is configured.
- [ ] Replica consistency requirements are understood.
- [ ] Generated SQL is observable.

### Security

- [ ] Tenant scope is enforced.
- [ ] Authorization is independent of ranking logic.
- [ ] RLS behavior is understood where applicable.
- [ ] Dynamic SQL is parameterized.
- [ ] Sensitive analytical results are access-controlled.
- [ ] Cached results cannot cross tenant boundaries.

### Reliability

- [ ] Long-running reports do not threaten OLTP availability.
- [ ] Read replicas have sufficient capacity.
- [ ] Expensive workloads have appropriate isolation.
- [ ] Failover behavior is understood.
- [ ] Query cancellation is supported.
- [ ] Recovery and reporting dependencies are documented.

---

## Interview Traps

### `ROW_NUMBER()` vs `RANK()`

**Question:** Why does `ROW_NUMBER()` not preserve ties?

Because it assigns a unique sequence position to every row. If ties must share a rank, use `RANK()` or `DENSE_RANK()`.

### Latest Record Per Group

**Question:** How would you find the latest order for every customer?

A common solution is:

```sql
WITH ranked AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked
WHERE rn = 1;
```

### Why Not `MAX(created_at)`?

Because:

```sql
SELECT
    customer_id,
    MAX(created_at)
FROM orders
GROUP BY customer_id;
```

returns the timestamp, not necessarily the complete order row associated with that timestamp.

### `LAST_VALUE()` Trap

**Question:** Why can `LAST_VALUE()` unexpectedly return the current row?

Because the default window frame can end at the current row. When the final row of the entire partition is required, define the frame explicitly.

### Window Function vs `GROUP BY`

**Question:** When should you use a window function?

Use it when you need calculations across related rows while retaining individual rows in the result.

### Performance Trap

**Question:** Does a window function automatically make a query efficient?

No. Large partitions and ordering can require substantial sorting, memory, CPU, and temporary I/O.

---

## Senior-Level Design Questions

For each window-function solution, answer:

1. What is the result grain?
2. What defines the partition?
3. Is ordering deterministic?
4. What happens when values tie?
5. What is the window frame?
6. How many rows are processed?
7. Can joins multiply rows before the window?
8. What indexes support filtering and ordering?
9. Could the query spill to disk?
10. How frequently does the query execute?
11. Does the query belong on the OLTP database?
12. Can a materialized view or read model solve the problem better?
13. Does the query require primary consistency?
14. Can a replica serve it?
15. Is tenant isolation preserved?
16. What happens as the dataset grows by 10x?
17. How is query latency monitored?
18. What is the failure behavior if the database becomes overloaded?

---

## Final Practice Set

Complete the following without consulting reference solutions:

1. Calculate total customer revenue using a window aggregate.
2. Calculate customer order counts without `GROUP BY`.
3. Number orders chronologically per customer.
4. Number orders in reverse chronological order.
5. Find the latest order per customer.
6. Find the earliest order per customer.
7. Find the second order per customer.
8. Find the top three orders per customer.
9. Rank orders using `RANK()`.
10. Rank orders using `DENSE_RANK()`.
11. Compare all three ranking functions.
12. Calculate running revenue per customer.
13. Calculate a three-order moving average.
14. Retrieve the previous order using `LAG()`.
15. Retrieve the next order using `LEAD()`.
16. Calculate the difference from the previous order.
17. Calculate time since the previous order.
18. Calculate the first order amount.
19. Calculate the last order amount correctly using an explicit frame.
20. Retrieve the second order amount with `NTH_VALUE()`.
21. Calculate each order's percentage of customer revenue.
22. Rank customers by completed revenue.
23. Calculate revenue quartiles.
24. Calculate month-over-month revenue change.
25. Calculate month-over-month percentage change.
26. Rank customers within each month.
27. Find the top five products per month.
28. Detect duplicate business keys.
29. Build a status-transition report.
30. Calculate time spent in each order status.
31. Detect suspiciously rapid customer activity.
32. Build a customer retention cohort query.
33. Calculate running inventory quantity.
34. Compare window-function pagination with keyset pagination.
35. Compare a window query with an equivalent correlated subquery.
36. Compare a window query with an equivalent self-join.
37. Build a multi-tenant-safe leaderboard.
38. Build a Django analytics endpoint.
39. Build the equivalent SQLAlchemy query.
40. Benchmark the query at production-scale data volume.
41. Inspect the execution plan.
42. Identify sorting and temporary I/O costs.
43. Determine whether the workload belongs on OLTP, a replica, or OLAP.
44. Define monitoring metrics for the query.
45. Explain every design decision as if defending the query in a production architecture review.

## Key Takeaways

- **Window functions preserve row-level detail:** unlike `GROUP BY`, they calculate across related rows without collapsing the result set.
- **Partitioning, ordering, and frames define correctness:** `PARTITION BY`, deterministic `ORDER BY`, and explicit frames must match the business semantics of the calculation.
- **Choose ranking functions intentionally:** `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()` have different tie behavior and should not be treated as interchangeable.
- **Window queries can be expensive at scale:** large partitions, sorting, temporary I/O, and repeated analytical workloads require execution-plan analysis and appropriate workload isolation.
- **Senior SQL design connects windows to architecture:** result grain, joins, pagination, tenant isolation, replicas, OLAP, ORM behavior, observability, and data growth all influence whether a window-function solution is production-ready.