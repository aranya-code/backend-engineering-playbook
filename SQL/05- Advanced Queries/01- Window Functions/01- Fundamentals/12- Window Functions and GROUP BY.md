# 12- Window Functions and GROUP BY

## Overview

`GROUP BY` and window functions both perform analytical operations over sets of rows, but they preserve fundamentally different result shapes.

`GROUP BY` **collapses multiple input rows into one output row per group**. Window functions calculate values across related rows while **preserving the individual rows**.

This distinction is critical when building backend queries such as:

- Revenue reports with transaction-level details.
- Department-level metrics alongside individual employees.
- Customer orders with customer totals.
- Ranked results within aggregated groups.
- Pagination-friendly API responses containing both row-level and group-level metrics.

A useful mental model is:

```text
GROUP BY
many rows ──► one row per group

Window function
many rows ──► same rows + derived analytical columns
```

## The Fundamental Difference

Consider an `orders` table:

```text
order_id   customer_id   amount
--------   -----------   ------
101        10            100
102        10            250
103        20            150
104        20            300
105        20            200
```

A `GROUP BY` query:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

produces:

```text
customer_id   customer_total
-----------   --------------
10            350
20            650
```

The five source rows become two result rows.

A window function:

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

produces:

```text
order_id   customer_id   amount   customer_total
--------   -----------   ------   --------------
101        10            100      350
102        10            250      350
103        20            150      650
104        20            300      650
105        20            200      650
```

The original rows remain available.

## Result Shape

This is the most important distinction.

| Property | `GROUP BY` | Window Function |
|---|---|---|
| Collapses rows | Yes | No |
| Preserves row-level detail | No | Yes |
| Produces one row per group | Usually | No |
| Can calculate aggregates | Yes | Yes |
| Can calculate ranking | No | Yes |
| Can calculate running totals | Not directly | Yes |
| Can compare a row with neighboring rows | No | Yes |
| Can use `PARTITION BY` | No | Yes |
| Typical use | Aggregation | Analytics over rows |

A practical rule:

> If you need to **change the grain of the result**, think `GROUP BY`. If you need to **keep the grain and add context**, think window function.

## SQL Logical Processing Order

Understanding SQL's logical processing order explains many `GROUP BY` and window-function errors.

A simplified model is:

```text
FROM
  ↓
WHERE
  ↓
GROUP BY
  ↓
HAVING
  ↓
Window functions
  ↓
SELECT / ORDER BY
```

The exact implementation performed by a database optimizer can differ, but this logical model is useful for reasoning about query validity.

Window functions operate on the rows produced after earlier relational operations such as filtering and grouping.

Consider:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total,
    AVG(SUM(amount)) OVER () AS average_customer_total
FROM orders
GROUP BY customer_id;
```

This is valid because:

1. `orders` are grouped by `customer_id`.
2. `SUM(amount)` produces one row per customer.
3. The window function then operates over those grouped rows.
4. `AVG(SUM(amount)) OVER ()` calculates the average customer total.

The window function is therefore operating on the **result of the aggregation**, not directly on every original order row.

## `GROUP BY` Changes the Grain

Suppose the original grain is:

```text
one row = one order
```

After:

```sql
GROUP BY customer_id
```

the grain becomes:

```text
one row = one customer
```

This is a major data-modeling concept.

Once rows have been collapsed, columns that are not grouped or aggregated generally cannot be selected directly.

For example:

```sql
SELECT
    customer_id,
    order_id,
    SUM(amount)
FROM orders
GROUP BY customer_id;
```

is invalid in standard SQL because `order_id` is not determined by the grouping operation.

There may be database-specific functional-dependency rules, but relying on them without understanding the schema and database behavior can make queries difficult to reason about.

## Window Functions Preserve the Grain

The equivalent analytical query can retain the order grain:

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

The grain remains:

```text
one row = one order
```

The query simply adds:

```text
customer_total
```

to every order belonging to the same customer.

This is why window functions are useful when API responses need both:

- The individual entity.
- A metric calculated across related entities.

## Aggregating First, Then Applying a Window

A powerful pattern is:

```text
raw rows
   ↓
GROUP BY
   ↓
aggregated rows
   ↓
window function
   ↓
analytical result
```

Example:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS customer_rank
FROM orders
GROUP BY customer_id;
```

Result:

```text
customer_id   customer_total   customer_rank
-----------   --------------   -------------
20            650              1
10            350              2
```

Here, `GROUP BY` establishes the customer-level result set.

The window function then ranks those customer-level rows.

This pattern is extremely common in reporting and analytics.

## Windowing Over Aggregated Results

The previous query can be understood as if SQL had produced an intermediate relation:

```text
customer_id   customer_total
-----------   --------------
10            350
20            650
```

and then applied:

```sql
RANK() OVER (ORDER BY customer_total DESC)
```

Conceptually:

```text
Orders
  │
  ▼
GROUP BY customer_id
  │
  ▼
Customer totals
  │
  ▼
RANK() OVER (...)
  │
  ▼
Ranked customers
```

This is often easier to reason about than thinking of the entire query as one operation.

## Practical Pattern: Rank Groups

Suppose an e-commerce system needs the top-performing products by revenue.

```sql
SELECT
    product_id,
    SUM(quantity * unit_price) AS revenue,
    RANK() OVER (
        ORDER BY SUM(quantity * unit_price) DESC
    ) AS revenue_rank
FROM order_items
GROUP BY product_id;
```

`GROUP BY` creates one row per product.

`RANK()` then operates over those product-level rows.

This avoids attempting to rank individual order items when the actual business requirement is ranking products.

## Practical Pattern: Group Metrics With Row Detail

Sometimes the requirement is:

> Return every order, but also show the customer's total spending.

A window function is appropriate:

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

Using only `GROUP BY` would lose the individual order rows.

A common workaround is to aggregate separately and join:

```sql
SELECT
    o.order_id,
    o.customer_id,
    o.amount,
    totals.customer_total
FROM orders AS o
JOIN (
    SELECT
        customer_id,
        SUM(amount) AS customer_total
    FROM orders
    GROUP BY customer_id
) AS totals
    ON totals.customer_id = o.customer_id;
```

The window-function version is usually more direct when the database can express the calculation naturally.

## Practical Pattern: Aggregate and Compare Against the Overall Total

Suppose the API needs:

- Each customer's total.
- The percentage of all revenue represented by that customer.

A window over grouped results works well:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total,
    ROUND(
        100.0 * SUM(amount)
        / SUM(SUM(amount)) OVER (),
        2
    ) AS revenue_percentage
FROM orders
GROUP BY customer_id;
```

The inner `SUM(amount)` produces customer totals.

The window expression:

```sql
SUM(SUM(amount)) OVER ()
```

then sums those customer totals.

Conceptually:

```text
orders
  ↓
customer aggregation
  ↓
customer totals
  ↓
window over customer totals
  ↓
percentage of overall revenue
```

This is a useful example of combining aggregation and windowing without an additional application-side calculation.

## `WHERE` and Window Functions

A filter in the same query block happens before the window calculation.

Consider:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE order_date >= DATE '2026-01-01';
```

The window sees only orders from 2026 onward.

It does **not** calculate the customer's lifetime total.

If the requirement is:

> Show 2026 orders, but display each customer's lifetime total.

Use separate query layers:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(amount) AS lifetime_total
    FROM orders
    GROUP BY customer_id
)
SELECT
    o.order_id,
    o.customer_id,
    o.amount,
    ct.lifetime_total
FROM orders AS o
JOIN customer_totals AS ct
    ON ct.customer_id = o.customer_id
WHERE o.order_date >= DATE '2026-01-01';
```

The CTE establishes the lifetime aggregation before the final filter.

This distinction is particularly important for reporting APIs.

## `HAVING` and Window Functions

`HAVING` filters grouped results before the window operation.

For example:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS customer_rank
FROM orders
GROUP BY customer_id
HAVING SUM(amount) >= 1000;
```

The ranking is performed over customers whose total is at least `1000`.

Therefore, a customer with a total of `900` is not merely ranked lower; it is absent from the window input entirely.

If the requirement is:

> Rank all customers, but return only customers whose rank is within the top 10.

you generally need another query layer:

```sql
WITH ranked_customers AS (
    SELECT
        customer_id,
        SUM(amount) AS customer_total,
        RANK() OVER (
            ORDER BY SUM(amount) DESC
        ) AS customer_rank
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    customer_total,
    customer_rank
FROM ranked_customers
WHERE customer_rank <= 10;
```

This preserves the correct ranking population.

## Why You Cannot Filter a Window Directly With `WHERE`

This is generally invalid:

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS customer_rank
FROM orders
GROUP BY customer_id
WHERE customer_rank <= 10;
```

The `WHERE` clause cannot directly reference the window result because the window calculation has not logically been produced at that stage.

Use a CTE or derived table:

```sql
WITH ranked_customers AS (
    SELECT
        customer_id,
        SUM(amount) AS customer_total,
        RANK() OVER (
            ORDER BY SUM(amount) DESC
        ) AS customer_rank
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM ranked_customers
WHERE customer_rank <= 10;
```

This creates a relational boundary around the window result.

## `GROUP BY` vs `PARTITION BY`

These clauses are often confused because both organize rows into groups.

### `GROUP BY`

```sql
GROUP BY customer_id
```

changes the result grain.

### `PARTITION BY`

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

defines the window's independent calculation groups while preserving the rows.

Compare:

```sql
SELECT
    customer_id,
    SUM(amount) AS total
FROM orders
GROUP BY customer_id;
```

with:

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

The first returns one row per customer.

The second returns one row per order.

## Combining `GROUP BY` and `PARTITION BY`

The two can be used together.

Suppose a company needs monthly revenue by product category and wants each category ranked within its month.

First aggregate:

```sql
SELECT
    DATE_TRUNC('month', order_date) AS month,
    category_id,
    SUM(amount) AS revenue,
    RANK() OVER (
        PARTITION BY DATE_TRUNC('month', order_date)
        ORDER BY SUM(amount) DESC
    ) AS category_rank
FROM orders
GROUP BY
    DATE_TRUNC('month', order_date),
    category_id;
```

The logical flow is:

```text
orders
  │
  ▼
GROUP BY month + category
  │
  ▼
one row per month/category
  │
  ▼
PARTITION BY month
  │
  ▼
rank categories within each month
```

This pattern is common in business intelligence and backend reporting systems.

## CTEs for Complex Query Pipelines

When the distinction between aggregation and windowing becomes difficult to reason about, use a CTE to make the stages explicit.

```sql
WITH monthly_product_revenue AS (
    SELECT
        DATE_TRUNC('month', order_date) AS month,
        product_id,
        SUM(quantity * unit_price) AS revenue
    FROM order_items
    GROUP BY
        DATE_TRUNC('month', order_date),
        product_id
),
ranked_products AS (
    SELECT
        month,
        product_id,
        revenue,
        RANK() OVER (
            PARTITION BY month
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM monthly_product_revenue
)
SELECT
    month,
    product_id,
    revenue,
    revenue_rank
FROM ranked_products
WHERE revenue_rank <= 10
ORDER BY
    month,
    revenue_rank,
    product_id;
```

The stages now have explicit responsibilities:

| Stage | Responsibility |
|---|---|
| `monthly_product_revenue` | Change grain to month/product |
| `ranked_products` | Add ranking without changing grain |
| Final query | Filter ranked results |

This is easier to test and maintain than one deeply nested expression.

## Backend API Example

Suppose a FastAPI endpoint returns a customer's recent orders together with lifetime spending.

A naive query:

```sql
SELECT
    order_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE customer_id = :customer_id
  AND order_date >= :start_date
ORDER BY order_date DESC;
```

has an important semantic issue: the window sees only the filtered recent orders.

If `customer_total` is intended to mean lifetime spending, the query is incorrect.

A safer design separates the two populations:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(amount) AS lifetime_total
    FROM orders
    WHERE customer_id = :customer_id
    GROUP BY customer_id
)
SELECT
    o.order_id,
    o.amount,
    o.order_date,
    ct.lifetime_total
FROM orders AS o
JOIN customer_totals AS ct
    ON ct.customer_id = o.customer_id
WHERE o.customer_id = :customer_id
  AND o.order_date >= :start_date
ORDER BY
    o.order_date DESC,
    o.order_id DESC;
```

The database now computes the metric over the intended population.

This matters in Django ORM, SQLAlchemy, and FastAPI applications because moving filters between query layers can silently change analytical semantics.

## Performance Considerations

Both `GROUP BY` and window functions can require substantial database work.

Common operations include:

```text
Scan
  ↓
Filter
  ↓
Aggregate
  ↓
Sort / Window processing
  ↓
Final result
```

The exact execution plan is database-specific.

For PostgreSQL, inspect expensive analytical queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    SUM(amount) AS customer_total,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS customer_rank
FROM orders
GROUP BY customer_id;
```

Look for:

- Large sequential scans.
- Expensive sorts.
- External sorts spilling to disk.
- High memory consumption.
- Large intermediate result sets.
- Unexpected row multiplication from joins.

### Indexing

Indexes can help filtering, joins, and sometimes reduce the cost of obtaining ordered data, but they do not automatically make every window query fast.

For example, a query frequently partitioned and ordered by:

```sql
PARTITION BY customer_id
ORDER BY order_date, order_id
```

may benefit from an index such as:

```sql
CREATE INDEX idx_orders_customer_date_id
ON orders (customer_id, order_date, order_id);
```

Whether the optimizer actually uses it depends on:

- Selectivity.
- Table size.
- Query predicates.
- Statistics.
- Required ordering.
- Cost estimates.
- Database version and execution strategy.

Always validate with the execution plan.

## Large-Scale Reporting

For high-volume transactional systems, avoid putting unrestricted analytical queries directly on the primary database behind latency-sensitive API endpoints.

Potential approaches include:

- Read replicas.
- Pre-aggregated reporting tables.
- Materialized views.
- Data warehouses.
- Scheduled aggregation jobs with Celery.
- Separate analytical workloads.
- Partitioned tables where appropriate.

For example:

```text
REST API
   │
   ▼
Application
   │
   ├── OLTP query ──► PostgreSQL primary
   │
   └── reporting query ──► read replica / analytics store
```

Window functions are powerful, but query sophistication does not eliminate the underlying cost of scanning, sorting, grouping, and processing large datasets.

## Common Mistakes

### Using `GROUP BY` When Row Detail Is Required

Incorrect mental model:

> "I need the total per customer, so I should always use `GROUP BY`."

If the response also needs every order, `GROUP BY` alone changes the result grain and loses order-level detail.

Use a window function or an explicit aggregation-and-join strategy.

### Using a Window Function When the Result Should Be One Row Per Group

The opposite mistake is also common.

If the API requires:

```text
one row per customer
```

there is usually no reason to retain every order through a window function.

Use:

```sql
GROUP BY customer_id
```

and produce the intended customer-level relation.

### Filtering Before Calculating a Lifetime Metric

This is one of the most dangerous semantic mistakes:

```sql
FROM orders
WHERE order_date >= :start_date
```

followed by:

```sql
SUM(amount) OVER (PARTITION BY customer_id)
```

The window calculates over the filtered population.

If the requirement is lifetime spending, calculate the lifetime metric in a separate query layer.

### Filtering a Ranking Population Too Early

If you rank after filtering, the ranking population changes.

For example:

```sql
WHERE region = 'APAC'
```

before:

```sql
RANK() OVER (...)
```

means the ranking is among APAC rows only.

That may be correct or incorrect depending on whether the business requirement is:

- Rank globally, then show APAC.
- Rank only within APAC.

The query must make that distinction explicit.

### Assuming CTEs Always Materialize

A CTE is primarily a query-structuring mechanism in modern SQL systems.

Do not assume:

```sql
WITH x AS (...)
SELECT ...
```

always means:

```text
execute x
store its result
then execute the outer query
```

Database optimizers may inline or otherwise transform CTEs depending on the engine and query.

Use `EXPLAIN` to understand actual execution behavior.

## Interview Traps

| Question | Correct answer |
|---|---|
| What is the main difference between `GROUP BY` and a window function? | `GROUP BY` changes the result grain; a window function preserves rows while adding analytical values. |
| Is `PARTITION BY` equivalent to `GROUP BY`? | No. `PARTITION BY` defines calculation groups inside a window without collapsing rows. |
| Can window functions operate after `GROUP BY`? | Yes. They can operate over the grouped result. |
| Why can't a window result normally be used directly in `WHERE`? | The window result is produced after the filtering stage in the logical query-processing model. |
| How do you filter rows based on a window result? | Use a CTE or derived table, then filter in an outer query. |
| Does `WHERE` affect a window function? | Yes. Rows filtered by the same query block are not available to the window. |
| Can `GROUP BY` and window functions be used in one query? | Yes, and this is common for ranking or analyzing aggregated groups. |
| Why use a CTE between aggregation and windowing? | It makes result grain and analytical stages explicit and easier to reason about. |
| Does a CTE guarantee a temporary stored result? | No. The optimizer may inline or transform it depending on the database and query. |

## Practical Decision Guide

Use this decision process when designing a query:

```text
Do I need one row per group?
        │
      Yes ──► GROUP BY
        │
       No
        │
        ▼
Do I need a metric calculated across related rows?
        │
      Yes ──► Window function
        │
       No
        │
        ▼
Do I need both?
        │
      Yes ──► GROUP BY + window function
```

For more complex requirements:

```text
Raw data
   │
   ▼
Filter the correct population
   │
   ▼
GROUP BY if the result grain must change
   │
   ▼
Window function if analytical context is required
   │
   ▼
Outer query if filtering on the window result
```

## Production Checklist

Before shipping a query combining `GROUP BY` and window functions, verify:

- [ ] What is the input grain?
- [ ] What should the final result grain be?
- [ ] Does `GROUP BY` intentionally change that grain?
- [ ] Should the analytical calculation operate before or after aggregation?
- [ ] Does `WHERE` remove rows that the window should see?
- [ ] Does `HAVING` change the intended ranking population?
- [ ] Does the window need `PARTITION BY`?
- [ ] Is the `ORDER BY` deterministic where required?
- [ ] Should ranking happen before or after the final filtering?
- [ ] Should a CTE or derived table separate query stages?
- [ ] Has the execution plan been checked against realistic data volume?
- [ ] Could the workload belong on a read replica or analytical system instead of the OLTP primary?

## Key Takeaways

- **`GROUP BY` changes result grain by collapsing rows, while window functions preserve rows and add analytical context.**
- **`PARTITION BY` groups rows for a window calculation but does not collapse them like `GROUP BY`.**
- **Window functions can operate over grouped results, making `GROUP BY` + window functions a powerful pattern for ranking and analyzing aggregates.**
- **`WHERE` and `HAVING` can change the population visible to a window function, so query-layer placement is part of the metric's correctness.**
- **For production analytical queries, make result grain explicit, separate complex stages with CTEs when useful, and validate performance with realistic execution plans.**