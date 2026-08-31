# 14- Window Functions and HAVING

## Overview

`HAVING` and window functions operate at different stages of SQL query processing. Understanding their relationship is essential when building analytical queries that combine aggregation, grouping, filtering, and ranking.

The key rule is:

> `HAVING` filters grouped rows before window functions are evaluated.

This means a window function can operate on the result of a `GROUP BY` query after `HAVING` has removed groups. Consequently, moving a condition between `WHERE`, `HAVING`, and an outer query can change the population being ranked, counted, or analyzed.

This distinction is particularly important for queries such as:

- Rank customers by total revenue.
- Find the top-performing departments after applying a minimum revenue threshold.
- Rank products within categories after excluding low-volume categories.
- Calculate percentages or cumulative metrics over aggregated data.
- Select the top N groups after aggregation.

## Logical Query Processing Order

A useful mental model is:

```text
FROM / JOIN
      ↓
WHERE
      ↓
GROUP BY
      ↓
HAVING
      ↓
Window functions
      ↓
SELECT
      ↓
ORDER BY
```

This is a **logical** processing model. A database optimizer may physically execute operations in a different order when it can do so without changing the result.

The important relationship is:

```text
WHERE
  ↓
GROUP BY
  ↓
HAVING
  ↓
Window Function
```

Therefore, a window function sees only the rows or groups that survive the earlier stages of the query block.

## Why `HAVING` Matters to Window Functions

`GROUP BY` collapses multiple base rows into groups.

For example:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue
FROM orders
GROUP BY customer_id;
```

The result contains one row per customer.

`HAVING` can then remove groups:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue
FROM orders
GROUP BY customer_id
HAVING SUM(amount) >= 1000;
```

Only customers with at least `1000` in revenue remain.

A window function applied to this query operates over those remaining grouped rows.

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS revenue_rank
FROM orders
GROUP BY customer_id
HAVING SUM(amount) >= 1000;
```

Conceptually:

```text
orders
  │
  ▼
GROUP BY customer_id
  │
  ▼
calculate customer totals
  │
  ▼
HAVING total >= 1000
  │
  ▼
rank remaining customers
```

The ranking does not include customers whose totals are below `1000`.

## `HAVING` vs Outer Filtering

This is one of the most important distinctions to understand.

Consider:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS revenue_rank
FROM orders
GROUP BY customer_id
HAVING SUM(amount) >= 1000;
```

The rank is calculated **after** low-revenue customers are removed.

Now consider:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        total_revenue,
        RANK() OVER (
            ORDER BY total_revenue DESC
        ) AS revenue_rank
    FROM customer_revenue
)
SELECT
    customer_id,
    total_revenue,
    revenue_rank
FROM ranked_customers
WHERE total_revenue >= 1000;
```

Here the ranking occurs before the revenue filter.

The difference is subtle but critical.

### `HAVING` Before Ranking

```text
all customers
      ↓
remove customers < 1000
      ↓
rank remaining customers
```

### Outer `WHERE` After Ranking

```text
all customers
      ↓
rank all customers
      ↓
remove customers < 1000
```

These queries can produce different rank values.

## Example

Suppose customer revenue is:

| Customer | Revenue |
|---|---:|
| A | 5000 |
| B | 4000 |
| C | 3000 |
| D | 2000 |
| E | 500 |

Using:

```sql
HAVING SUM(amount) >= 2000
```

the ranking population becomes:

| Customer | Revenue | Rank |
|---|---:|---:|
| A | 5000 | 1 |
| B | 4000 | 2 |
| C | 3000 | 3 |
| D | 2000 | 4 |

Customer E never participates in the ranking.

With an inner ranking followed by an outer filter:

```sql
WITH ranked_customers AS (
    SELECT
        customer_id,
        SUM(amount) AS total_revenue,
        RANK() OVER (
            ORDER BY SUM(amount) DESC
        ) AS revenue_rank
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM ranked_customers
WHERE total_revenue >= 2000;
```

Customer E receives rank `5` before being removed.

The visible rows may look similar, but their ranking values are different.

## When to Use `HAVING`

Use `HAVING` when the condition determines **which groups should participate in subsequent query processing**.

For example:

> Rank customers whose lifetime revenue is at least $10,000.

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS revenue_rank
FROM orders
GROUP BY customer_id
HAVING SUM(amount) >= 10000;
```

This produces a ranking among qualifying customers only.

`HAVING` is appropriate because the threshold is a condition on an aggregate group:

```sql
SUM(amount) >= 10000
```

## When to Filter in the Outer Query

Use an outer query when the window calculation should consider **all groups**, but the final result should display only a subset.

For example:

> Rank every customer, but display only customers whose revenue is at least $10,000.

```sql
WITH ranked_customers AS (
    SELECT
        customer_id,
        SUM(amount) AS total_revenue,
        RANK() OVER (
            ORDER BY SUM(amount) DESC
        ) AS revenue_rank
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_revenue,
    revenue_rank
FROM ranked_customers
WHERE total_revenue >= 10000;
```

The outer `WHERE` does not affect the ranking population.

## `WHERE`, `HAVING`, and Outer `WHERE`

These three filters can operate on different populations.

| Filter | Operates on | Effect on window population |
|---|---|---|
| `WHERE` | Base rows | Removes base rows before grouping and windows |
| `HAVING` | Groups | Removes groups before windows |
| Outer `WHERE` | Window result | Filters after the inner window calculation |

A useful mental model is:

```text
Base rows
   │
   ├── WHERE removes rows
   │
   ▼
Groups
   │
   ├── HAVING removes groups
   │
   ▼
Window calculation
   │
   ├── Outer WHERE removes calculated rows
   │
   ▼
Final result
```

## Aggregates Inside Window Functions

A window function can operate on an aggregate expression from the grouped result.

For example:

```sql
SELECT
    department_id,
    SUM(salary) AS department_payroll,
    RANK() OVER (
        ORDER BY SUM(salary) DESC
    ) AS payroll_rank
FROM employees
GROUP BY department_id;
```

The conceptual stages are:

```text
employees
    ↓
GROUP BY department_id
    ↓
SUM(salary)
    ↓
department-level rows
    ↓
RANK() over department rows
```

This is not the same as calculating a window over individual employees.

The aggregate first creates department-level rows; the window then operates over those rows.

## Filtering Aggregates Before Ranking

Suppose the requirement is:

> Rank departments whose payroll exceeds $1 million.

```sql
SELECT
    department_id,
    SUM(salary) AS payroll,
    RANK() OVER (
        ORDER BY SUM(salary) DESC
    ) AS payroll_rank
FROM employees
GROUP BY department_id
HAVING SUM(salary) > 1000000;
```

Only qualifying departments participate in the ranking.

This is usually preferable when the business definition of the ranking population is:

> Departments with payroll greater than $1 million.

## Ranking First, Filtering Later

If the requirement instead is:

> Rank every department, then show departments whose payroll exceeds $1 million.

use:

```sql
WITH department_payroll AS (
    SELECT
        department_id,
        SUM(salary) AS payroll
    FROM employees
    GROUP BY department_id
),
ranked_departments AS (
    SELECT
        department_id,
        payroll,
        RANK() OVER (
            ORDER BY payroll DESC
        ) AS payroll_rank
    FROM department_payroll
)
SELECT
    department_id,
    payroll,
    payroll_rank
FROM ranked_departments
WHERE payroll > 1000000;
```

The extra query boundary makes the intended evaluation order explicit.

## Combining `HAVING` with Partitioned Windows

The same principle applies when the window contains `PARTITION BY`.

Consider product sales:

```sql
SELECT
    category_id,
    product_id,
    SUM(quantity) AS units_sold,
    RANK() OVER (
        PARTITION BY category_id
        ORDER BY SUM(quantity) DESC
    ) AS category_rank
FROM order_items
GROUP BY
    category_id,
    product_id
HAVING SUM(quantity) >= 100;
```

The query means:

> Within each category, rank products whose aggregated sales are at least 100 units.

Products below the threshold are removed before the category ranking is calculated.

This differs from ranking all products and filtering afterward.

## Top-N Groups After `HAVING`

A common production pattern is:

> Find the top five customers by revenue, but only among customers with at least 100 completed orders.

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
    HAVING COUNT(*) >= 100
),
ranked_customers AS (
    SELECT
        customer_id,
        order_count,
        total_revenue,
        ROW_NUMBER() OVER (
            ORDER BY total_revenue DESC, customer_id
        ) AS row_num
    FROM customer_metrics
)
SELECT
    customer_id,
    order_count,
    total_revenue
FROM ranked_customers
WHERE row_num <= 5;
```

The stages are:

```text
completed orders
       ↓
GROUP BY customer
       ↓
HAVING order_count >= 100
       ↓
rank qualifying customers
       ↓
take top 5
```

This is often easier to reason about than trying to combine all conditions into one query block.

## `HAVING` Does Not Replace `WHERE`

A common mistake is to use `HAVING` for conditions that could be applied to base rows.

Instead of:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue
FROM orders
GROUP BY customer_id
HAVING status = 'completed';
```

use:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

`WHERE` filters individual rows before aggregation.

`HAVING` filters the resulting groups.

For large tables, pushing row-level predicates into `WHERE` can also reduce the amount of data that needs to be grouped and windowed.

## Predicate Placement and Performance

Correct predicate placement is primarily a semantic concern, but it can also have major performance consequences.

Consider:

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC, order_id DESC
        ) AS row_num
    FROM orders
)
SELECT *
FROM ranked_orders
WHERE customer_id = :customer_id
  AND row_num <= 10;
```

If the query only needs one customer, filtering that customer in the inner query may reduce the window population:

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC, order_id DESC
        ) AS row_num
    FROM orders
    WHERE customer_id = :customer_id
)
SELECT *
FROM ranked_orders
WHERE row_num <= 10;
```

However, the rewrite is valid only when the desired ranking is customer-local.

Do not move predicates solely for performance without first checking whether they change the intended population.

## Query Planning

For production analytical queries, validate the actual execution plan.

PostgreSQL example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    department_id,
    SUM(salary) AS payroll,
    RANK() OVER (
        ORDER BY SUM(salary) DESC
    ) AS payroll_rank
FROM employees
GROUP BY department_id
HAVING SUM(salary) > 1000000;
```

Look for:

- Large scans of base tables.
- Expensive aggregation.
- Sort operations required by the window.
- Memory-intensive intermediate results.
- Temporary-file spills.
- Incorrect row-count estimates.
- Unnecessary joins.
- Filters that could reduce the input earlier without changing semantics.

Window functions frequently require ordering, so large intermediate result sets can become expensive.

## Backend API Example

Suppose a FastAPI endpoint exposes:

```text
GET /customers/top
```

and the business requirement is:

> Return the top 10 customers among customers with at least 50 completed orders.

The SQL should encode the business population explicitly:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
    HAVING COUNT(*) >= 50
),
ranked AS (
    SELECT
        customer_id,
        order_count,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS position
    FROM customer_metrics
)
SELECT
    customer_id,
    order_count,
    revenue,
    position
FROM ranked
WHERE position <= 10
ORDER BY position;
```

The query has a clean semantic pipeline:

```text
API request
    ↓
completed orders
    ↓
customer aggregation
    ↓
minimum order-count eligibility
    ↓
ranking
    ↓
top 10
    ↓
JSON response
```

This separation makes the query easier to review against the business requirement.

## Security Considerations

`HAVING` and window functions do not provide authorization.

In a multi-tenant application, tenant filtering must be applied to the appropriate relational input:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = :tenant_id
      AND status = 'completed'
    GROUP BY customer_id
    HAVING COUNT(*) >= 50
)
SELECT ...
```

Do not rely on a later filter to hide unauthorized rows after an analytical calculation has already included them.

Use parameterized queries for request-derived values:

```python
cursor.execute(
    """
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = %s
    GROUP BY customer_id
    HAVING SUM(amount) >= %s
    """,
    [tenant_id, minimum_revenue],
)
```

## Common Mistakes

### Assuming `HAVING` Filters After the Window

Incorrect mental model:

```text
GROUP BY
  ↓
window
  ↓
HAVING
```

The logical relationship is:

```text
GROUP BY
  ↓
HAVING
  ↓
window
```

Therefore, `HAVING` changes the population available to the window function.

### Using `HAVING` When `WHERE` Is More Appropriate

Avoid:

```sql
GROUP BY customer_id
HAVING status = 'completed'
```

when `status` is a base-row predicate.

Prefer:

```sql
WHERE status = 'completed'
GROUP BY customer_id
```

This expresses the intent more clearly and can reduce the aggregation input.

### Assuming Outer Filtering Preserves the Same Rank

These are not equivalent:

```sql
HAVING SUM(amount) >= 1000
```

and:

```sql
WITH ranked AS (...)
SELECT *
FROM ranked
WHERE total_revenue >= 1000;
```

The first removes groups before ranking.

The second ranks all groups and removes some afterward.

### Confusing Group-Level and Row-Level Filtering

`WHERE` answers:

> Which base rows should participate?

`HAVING` answers:

> Which groups should participate?

An outer `WHERE` answers:

> Which already-computed rows should be returned?

Keeping these questions separate prevents many analytical SQL bugs.

### Ignoring Tie Semantics

If the query uses:

```sql
RANK() OVER (ORDER BY revenue DESC)
```

then:

```sql
WHERE revenue_rank <= 10
```

can return more than ten rows because tied values share ranks.

Use `ROW_NUMBER()` with a deterministic tie-breaker when the requirement is exactly ten rows.

## Production Checklist

Before shipping a query that combines `HAVING` and window functions:

- [ ] Is the ranking population explicitly defined?
- [ ] Are base-row filters in `WHERE`?
- [ ] Are aggregate/group filters in `HAVING`?
- [ ] Should the window include groups excluded by `HAVING`?
- [ ] If so, has the window been moved into an inner query?
- [ ] Is the correct window function being used?
- [ ] Are ties handled according to business requirements?
- [ ] Is window ordering deterministic?
- [ ] Are tenant and authorization predicates applied before unauthorized data enters the calculation?
- [ ] Has the query been tested with groups both above and below the `HAVING` threshold?
- [ ] Has the query been tested with tied aggregate values?
- [ ] Has the execution plan been inspected for large scans, sorts, and intermediate results?

## Interview Traps

| Question | Correct reasoning |
|---|---|
| Does `HAVING` execute before or after window functions? | Logically before window functions. |
| Does `HAVING` affect the rows available to a window function? | Yes. Groups removed by `HAVING` are not part of the window population. |
| Why use an outer query after a window function? | To filter the calculated window result without changing the population used by the window. |
| What is the difference between `HAVING SUM(x) > 100` and an outer `WHERE total > 100`? | The former filters before the window; the latter can filter after the window. |
| Should row-level predicates normally go in `WHERE` or `HAVING`? | `WHERE`, because they filter base rows before grouping. |
| Can an aggregate expression be used inside a window `ORDER BY` after `GROUP BY`? | Yes; the window operates on the grouped result. |
| Can `HAVING` be used to implement top-N ranking? | Not directly; calculate the window rank first, then filter the rank in an outer query or with `QUALIFY` where supported. |
| Why might two seemingly equivalent queries return different rank values? | They may define different populations for the window calculation because filtering occurs at different stages. |

## Key Takeaways

- **`HAVING` filters groups before window functions are logically evaluated, so it directly affects the population being ranked or analyzed.**
- **Use `WHERE` for base-row predicates, `HAVING` for aggregate/group predicates, and an outer filter when the window calculation must see the unfiltered grouped result.**
- **Filtering with `HAVING` before ranking and filtering after ranking are not interchangeable; they can produce different rank values even when the visible rows are similar.**
- **For top-N analytical queries, make the population, aggregation threshold, ranking function, and tie behavior explicit through separate query stages when necessary.**
- **Treat predicate placement as both a correctness and performance decision, and validate production queries with realistic data and execution plans.**
```
```

```
Markdown



```
# 15- Window Functions and CTEs

## Overview

Common Table Expressions (CTEs) and window functions solve different problems but work extremely well together.

A **CTE** creates a named intermediate query result that can be consumed by subsequent query logic. A **window function** performs calculations across related rows while preserving the individual rows in the result.

Combining them allows complex analytical queries to be decomposed into explicit stages:

```text
Base data
    ↓
Filter / Join
    ↓
CTE: prepare dataset
    ↓
CTE: aggregate metrics
    ↓
CTE: apply window calculations
    ↓
Outer query: filter / format result
```

This pattern is common in backend systems for:

- Top-N queries.
- Ranking and leaderboards.
- Latest-record selection.
- Running totals.
- Customer analytics.
- Time-series analysis.
- Deduplication.
- Cohort calculations.
- Percent-of-total metrics.
- Multi-stage reporting queries.

The important engineering principle is:

> Use CTEs to make query stages explicit; use window functions when the calculation needs access to related rows without collapsing them.

## Why Combine CTEs and Window Functions

A window function cannot normally be referenced directly in the `WHERE` clause of the same query block because window functions are evaluated after filtering in the logical query-processing order.

For example, this is invalid in PostgreSQL:

```sql
SELECT
    employee_id,
    salary,
    ROW_NUMBER() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees
WHERE salary_rank <= 3;
```

The solution is to introduce a query boundary:

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC, employee_id
        ) AS salary_rank
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary
FROM ranked_employees
WHERE salary_rank <= 3;
```

The CTE exposes the window result as a regular column to the outer query.

## CTE Mental Model

Think of a CTE as a named query stage:

```sql
WITH stage_name AS (
    SELECT ...
)
SELECT ...
FROM stage_name;
```

For example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT *
FROM customer_revenue;
```

The CTE establishes an intermediate relational result named `customer_revenue`.

A more complex query can have multiple stages:

```sql
WITH customer_revenue AS (
    SELECT ...
),
ranked_customers AS (
    SELECT ...
    FROM customer_revenue
)
SELECT ...
FROM ranked_customers;
```

Each stage can build on the previous one.

## Window Function Mental Model

A window function calculates a value across a set of related rows while retaining the current row.

For example:

```sql
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_revenue;
```

Unlike:

```sql
GROUP BY
```

the window operation does not collapse multiple customers into one row.

This distinction is fundamental:

| Operation | Preserves individual rows? | Typical purpose |
|---|---:|---|
| `GROUP BY` | No | Aggregate rows into groups |
| Window function | Yes | Calculate across related rows |
| CTE | Depends on its query | Organize intermediate query stages |

## A Practical Multi-Stage Pattern

Consider a reporting requirement:

> Find the top three products by revenue in each category, considering only completed orders.

A clean implementation is:

```sql
WITH product_revenue AS (
    SELECT
        oi.category_id,
        oi.product_id,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items AS oi
    JOIN orders AS o
        ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY
        oi.category_id,
        oi.product_id
),
ranked_products AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS category_rank
    FROM product_revenue
)
SELECT
    category_id,
    product_id,
    revenue,
    category_rank
FROM ranked_products
WHERE category_rank <= 3
ORDER BY category_id, category_rank;
```

The query has two clear responsibilities:

```text
Completed order items
        ↓
Aggregate revenue per product
        ↓
Rank products within category
        ↓
Keep top 3
```

This is easier to validate than mixing every operation into one query block.

## CTEs as Query Boundaries

A CTE is particularly useful when one operation logically depends on another.

For example:

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE_TRUNC('month', created_at)
),
revenue_with_growth AS (
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
FROM revenue_with_growth
ORDER BY month;
```

The first CTE establishes the monthly grain.

The second CTE applies a window calculation at that grain.

This separation prevents accidental mixing of row-level and aggregate-level logic.

## The Grain of Each CTE

One of the most important senior-level concepts is **data grain**.

Every CTE should have an intentional row meaning.

For example:

```text
orders
  → one row per order

customer_revenue
  → one row per customer

monthly_customer_revenue
  → one row per customer per month

ranked_customers
  → one row per customer per month + ranking metadata
```

Documenting the grain mentally makes window queries much easier to reason about.

For example:

```sql
WITH monthly_customer_revenue AS (
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
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank
FROM monthly_customer_revenue;
```

The window function operates on:

> One row per customer per month.

It does not operate on individual orders.

## Top-N Per Group

One of the most common CTE + window patterns is top-N per group.

```sql
WITH ranked_products AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS row_num
    FROM product_revenue
)
SELECT
    category_id,
    product_id,
    revenue
FROM ranked_products
WHERE row_num <= 5;
```

Use:

- `ROW_NUMBER()` when exactly N rows per partition are required.
- `RANK()` when ties should share a rank and tied rows should be retained.
- `DENSE_RANK()` when tied ranks should not create gaps.

For example, if revenues are:

| Product | Revenue | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---|---:|---:|---:|---:|
| A | 1000 | 1 | 1 | 1 |
| B | 900 | 2 | 2 | 2 |
| C | 900 | 3 | 2 | 2 |
| D | 700 | 4 | 4 | 3 |

The choice depends on the business requirement.

## Latest Row Per Entity

CTEs and `ROW_NUMBER()` are also useful for selecting the latest record for each entity.

Suppose an `account_status_history` table contains multiple status records:

```sql
WITH ranked_statuses AS (
    SELECT
        account_id,
        status,
        changed_at,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY changed_at DESC, id DESC
        ) AS row_num
    FROM account_status_history
)
SELECT
    account_id,
    status,
    changed_at
FROM ranked_statuses
WHERE row_num = 1;
```

The deterministic `id DESC` tie-breaker matters.

If two status records have the same timestamp, ordering only by `changed_at` does not guarantee which record receives row number `1`.

## Running Totals

A CTE can prepare a dataset before a running total is calculated.

```sql
WITH daily_revenue AS (
    SELECT
        DATE(created_at) AS day,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE(created_at)
)
SELECT
    day,
    revenue,
    SUM(revenue) OVER (
        ORDER BY day
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM daily_revenue
ORDER BY day;
```

The CTE changes the grain from:

```text
one row per order
```

to:

```text
one row per day
```

The window then calculates the cumulative value across those daily rows.

## Comparing Current and Previous Rows

`LAG()` and `LEAD()` become especially useful after a CTE establishes the correct analytical grain.

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (
        ORDER BY month
    ) AS previous_month_revenue
FROM monthly_revenue
ORDER BY month;
```

The CTE makes it clear that `LAG()` compares months rather than individual orders.

## Percentage of Total

CTEs are useful when a metric must first be aggregated and then compared with the aggregate total.

```sql
WITH category_revenue AS (
    SELECT
        category_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY category_id
)
SELECT
    category_id,
    revenue,
    ROUND(
        100.0 * revenue
        / NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS percentage_of_total
FROM category_revenue
ORDER BY revenue DESC;
```

The CTE establishes one row per category.

The window:

```sql
SUM(revenue) OVER ()
```

calculates the total across those category rows without collapsing them.

## Partitioned Percentages

The same pattern works within a partition.

```sql
WITH product_revenue AS (
    SELECT
        category_id,
        product_id,
        SUM(amount) AS revenue
    FROM order_items
    GROUP BY
        category_id,
        product_id
)
SELECT
    category_id,
    product_id,
    revenue,
    ROUND(
        100.0 * revenue
        / NULLIF(
            SUM(revenue) OVER (
                PARTITION BY category_id
            ),
            0
        ),
        2
    ) AS category_share
FROM product_revenue;
```

The calculation answers:

> What percentage of its category's revenue does this product represent?

## Multiple Window Calculations

A CTE can also make several analytical calculations easier to manage.

```sql
WITH customer_metrics AS (
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
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank,
    LAG(revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
    ) AS previous_month_revenue,
    SUM(revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_customer_revenue
FROM customer_metrics;
```

Each window answers a different question:

| Window | Question |
|---|---|
| `RANK()` by month | How does this customer compare with others this month? |
| `LAG()` by customer | How did this customer's revenue compare with last month? |
| Running `SUM()` by customer | What is this customer's cumulative revenue? |

## CTEs and Window Frames

CTEs can make window-frame semantics much clearer.

For example:

```sql
WITH daily_sales AS (
    SELECT
        DATE(created_at) AS day,
        SUM(amount) AS sales
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE(created_at)
)
SELECT
    day,
    sales,
    AVG(sales) OVER (
        ORDER BY day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_day_average
FROM daily_sales
ORDER BY day;
```

The frame is defined over the rows produced by `daily_sales`.

Therefore, the meaning of:

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

depends on the CTE's grain.

If `daily_sales` has exactly one row per day, it represents a seven-row window and normally a seven-day period.

If the CTE instead contained multiple rows per day, the same frame would mean seven rows, not seven days.

## CTEs and Filtering Window Results

A common pattern is:

```sql
WITH ranked AS (
    SELECT
        ...,
        ROW_NUMBER() OVER (...) AS row_num
    FROM ...
)
SELECT ...
FROM ranked
WHERE row_num <= 10;
```

This works because the outer query sees the window function's result as a normal column.

The same structure is useful for:

- Top-N results.
- Deduplication.
- Latest-row selection.
- Threshold filtering.
- Pagination over analytical results.

## CTE vs Subquery

A CTE is not automatically faster than an equivalent derived table or subquery.

These can express essentially the same logical operation:

```sql
WITH ranked AS (
    SELECT
        product_id,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS row_num
    FROM products
)
SELECT *
FROM ranked
WHERE row_num <= 10;
```

and:

```sql
SELECT *
FROM (
    SELECT
        product_id,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS row_num
    FROM products
) AS ranked
WHERE row_num <= 10;
```

Choose based on:

- Readability.
- Reuse.
- Number of stages.
- Debuggability.
- Database optimizer behavior.
- Team conventions.

## PostgreSQL CTE Materialization

In PostgreSQL, CTE behavior depends on the query and PostgreSQL version.

A CTE may be folded into the surrounding query when appropriate, while `MATERIALIZED` can explicitly request materialization and `NOT MATERIALIZED` can explicitly request inlining where permitted.

For example:

```sql
WITH customer_metrics AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_metrics;
```

Materialization can be useful when an expensive intermediate result is reused and computing it once is beneficial.

However, materialization can also prevent the optimizer from pushing filters into the CTE and may increase memory or temporary I/O.

Do not use `MATERIALIZED` as a generic performance optimization. Validate the effect with `EXPLAIN (ANALYZE, BUFFERS)`.

## Performance Considerations

CTEs and window functions introduce query stages, but they do not automatically imply poor performance.

The expensive parts are usually:

- Large scans.
- Large joins.
- Aggregation.
- Sorting for window functions.
- Large intermediate result sets.
- Multiple window specifications requiring different orderings.
- Materialization when it prevents useful optimization.

For example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS row_num
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue
FROM ranked
WHERE row_num <= 10;
```

Inspect:

- Actual row counts.
- Sort operations.
- Sort memory usage.
- Temporary disk usage.
- Sequential scans.
- Index scans.
- Aggregation cost.
- Join cardinality.
- Whether filters are pushed down effectively.

The goal is not to eliminate CTEs. The goal is to produce the correct query plan at an acceptable cost.

## Indexing Considerations

Indexes can reduce the cost of filtering and joining before the window stage.

For example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_status_customer
ON orders (status, customer_id);
```

Whether this index is useful depends on:

- Data distribution.
- Query predicates.
- Table size.
- Existing indexes.
- PostgreSQL statistics.
- Query plan.

An index does not necessarily eliminate the sort required by a window function, particularly when the window operates on an aggregated result.

Always verify with the execution plan rather than assuming an index will help.

## Production API Pattern

A backend service may expose an endpoint such as:

```text
GET /reports/customers/top
```

The application should generally separate:

1. Request validation.
2. Authorization and tenant filtering.
3. SQL execution.
4. Serialization.

For example, the SQL might be:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = :tenant_id
      AND status = 'completed'
    GROUP BY customer_id
    HAVING COUNT(*) >= :minimum_orders
),
ranked_customers AS (
    SELECT
        customer_id,
        order_count,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS position
    FROM customer_metrics
)
SELECT
    customer_id,
    order_count,
    revenue,
    position
FROM ranked_customers
WHERE position <= :limit
ORDER BY position;
```

The query stages correspond directly to the business rules:

```text
Tenant boundary
      ↓
Completed orders
      ↓
Customer metrics
      ↓
Minimum eligibility
      ↓
Ranking
      ↓
Top N
```

This makes the query easier to test against product requirements.

## Security Considerations

CTEs and window functions do not provide authorization boundaries.

For multi-tenant systems, tenant restrictions should be applied before tenant data participates in aggregation or analytical calculations:

```sql
WHERE tenant_id = :tenant_id
```

Otherwise, a calculation such as:

```sql
SUM(revenue) OVER ()
```

could include data belonging to other tenants even if the final output later filters rows.

Use parameterized queries:

```python
cursor.execute(
    """
    WITH customer_metrics AS (
        SELECT
            customer_id,
            SUM(amount) AS revenue
        FROM orders
        WHERE tenant_id = %s
        GROUP BY customer_id
    )
    SELECT
        customer_id,
        revenue,
        RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM customer_metrics
    """,
    [tenant_id],
)
```

Do not construct SQL by interpolating request parameters into SQL strings.

## Common Mistakes

### Using a Window Function Directly in `WHERE`

Incorrect:

```sql
SELECT
    customer_id,
    ROW_NUMBER() OVER (
        ORDER BY revenue DESC
    ) AS row_num
FROM customer_revenue
WHERE row_num <= 10;
```

Use a CTE or derived table:

```sql
WITH ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS row_num
    FROM customer_revenue
)
SELECT *
FROM ranked
WHERE row_num <= 10;
```

### Losing Track of Data Grain

If a CTE produces:

```text
one row per customer per month
```

then every later window calculation operates on that grain.

Joining another one-to-many table afterward can multiply rows and invalidate the analytical result.

Establish the grain of every intermediate result before adding more joins.

### Assuming CTEs Always Materialize

A CTE is a logical query construct, not a universal temporary table.

Do not assume:

```sql
WITH x AS (...)
SELECT ...
```

means:

```text
execute x completely
store x
then execute outer query
```

The optimizer may inline or otherwise transform the query.

### Using `RANK()` When Exactly N Rows Are Required

If the requirement is:

> Exactly five products per category.

prefer:

```sql
ROW_NUMBER()
```

with a deterministic tie-breaker.

`RANK()` can return more than five rows when multiple products share the same ranking value.

### Omitting Deterministic Tie-Breakers

Avoid:

```sql
ROW_NUMBER() OVER (
    PARTITION BY category_id
    ORDER BY revenue DESC
)
```

when deterministic results matter.

Prefer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY category_id
    ORDER BY revenue DESC, product_id
)
```

### Filtering Too Late

If a filter can safely reduce the base dataset before aggregation, applying it later may increase work.

Prefer:

```sql
WHERE status = 'completed'
```

before:

```sql
GROUP BY
```

when the business semantics require only completed rows.

### Assuming More CTEs Are Always Better

CTEs improve structure, but excessive staging can make a query harder to follow.

Use a CTE when it provides a meaningful semantic boundary:

- Changes the grain.
- Encapsulates a reusable intermediate result.
- Makes window filtering possible.
- Separates independent analytical stages.
- Improves reviewability.

Do not split every expression into a separate CTE.

## Interview Traps

| Question | Correct reasoning |
|---|---|
| Why use a CTE with a window function? | To create a query boundary so the window result can be filtered or reused by an outer query. |
| Can a window function normally be used directly in `WHERE` in the same query block? | No; window functions are logically evaluated after `WHERE`. |
| Does a CTE automatically materialize? | No. Database-specific optimizer behavior determines whether it is materialized or inlined unless explicitly controlled where supported. |
| Does a CTE automatically improve performance? | No. It primarily improves query organization; performance depends on the execution plan. |
| Why is data grain important? | Window calculations operate on the rows produced by their input relation, so changing the grain changes the meaning of the calculation. |
| When should `ROW_NUMBER()` be preferred over `RANK()`? | When exactly N rows per partition are required and ties need deterministic selection. |
| Can a window function operate on an aggregate produced by a CTE? | Yes. A CTE can establish the aggregate grain and the outer query can apply window calculations to those rows. |
| Why might materializing a CTE hurt performance? | It can prevent predicate pushdown or other optimizer transformations and may require additional memory or temporary I/O. |

## Key Takeaways

- **CTEs provide explicit query stages, while window functions calculate across related rows without collapsing the input grain.**
- **Use a CTE or derived table when a window result must be filtered, reused, or consumed by another query stage.**
- **Always know the grain of each CTE; changing the grain changes what `PARTITION BY`, ordering, frames, and aggregates mean.**
- **CTEs are primarily a query-organization tool, not an automatic performance optimization; validate materialization, sorting, joins, and scans with execution plans.**
- **For production analytical queries, make filtering, ranking semantics, tie-breaking, tenant boundaries, and intermediate data grain explicit.**
```
```

```
Markdown



```
# 15- Window Functions and CTEs

## Overview

Common Table Expressions (CTEs) and window functions solve different problems but complement each other extremely well.

A **CTE** creates a named intermediate query result that can be consumed by subsequent query logic. A **window function** calculates values across related rows while preserving the rows in the result.

Together, they allow complex analytical queries to be expressed as explicit stages:

```text
Base data
    ↓
Filter / Join
    ↓
CTE: establish dataset
    ↓
CTE: aggregate to required grain
    ↓
Window function: rank / compare / accumulate
    ↓
Outer query: filter or format result
```

This pattern is common in backend systems for:

- Top-N queries.
- Per-group ranking.
- Latest-record selection.
- Running totals.
- Customer analytics.
- Time-series reporting.
- Deduplication.
- Percent-of-total calculations.
- Multi-stage reporting queries.

The key engineering principle is:

> Use CTEs to make query stages explicit; use window functions when a calculation needs access to related rows without collapsing them.

## CTE Mental Model

A CTE is a named query expression defined with `WITH`:

```sql
WITH stage_name AS (
    SELECT ...
)
SELECT ...
FROM stage_name;
```

For example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT *
FROM customer_revenue;
```

The CTE establishes an intermediate relational result named `customer_revenue`.

Multiple CTEs can form a pipeline:

```sql
WITH customer_revenue AS (
    SELECT ...
),
ranked_customers AS (
    SELECT ...
    FROM customer_revenue
)
SELECT ...
FROM ranked_customers;
```

Each stage can establish a clearer semantic boundary.

### Why CTEs Exist

CTEs are useful when query logic has meaningful stages such as:

- Filtering a base dataset.
- Joining related data.
- Changing the data grain with aggregation.
- Applying window functions.
- Filtering window-function results.
- Reusing an intermediate relation.
- Making a complex query easier to review and maintain.

A CTE is primarily a **query-organization mechanism**, not an automatic performance optimization.

## Window Function Mental Model

A window function calculates a value across a set of related rows while retaining the current row.

For example:

```sql
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_revenue;
```

If there are 1,000 customers, the result still contains 1,000 customer rows.

This differs from `GROUP BY`:

```sql
SELECT
    customer_id,
    SUM(amount) AS revenue
FROM orders
GROUP BY customer_id;
```

`GROUP BY` changes the number of rows by collapsing records into groups.

| Operation | Preserves input rows? | Typical purpose |
|---|---:|---|
| `GROUP BY` | No | Aggregate rows into groups |
| Window function | Yes | Calculate across related rows |
| CTE | Depends on its query | Organize query stages |

## Why CTEs and Window Functions Work Well Together

A common requirement is:

> Rank rows and then keep only the top N.

A window function produces the rank:

```sql
ROW_NUMBER() OVER (
    PARTITION BY department_id
    ORDER BY salary DESC
)
```

But the resulting window value cannot normally be filtered in the same query block's `WHERE` clause.

This is invalid:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    ROW_NUMBER() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees
WHERE salary_rank <= 3;
```

A CTE creates the required query boundary:

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC, employee_id
        ) AS salary_rank
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary,
    salary_rank
FROM ranked_employees
WHERE salary_rank <= 3;
```

The outer query can treat `salary_rank` as a normal column.

## Query Processing Mental Model

For reasoning about window functions, a useful simplified logical sequence is:

```text
FROM / JOIN
    ↓
WHERE
    ↓
GROUP BY
    ↓
HAVING
    ↓
SELECT expressions
    ↓
Window functions
    ↓
ORDER BY
    ↓
LIMIT / OFFSET
```

The exact implementation and optimizer plan can differ, but this model explains several important rules.

For example:

- `WHERE` cannot normally reference a window-function result from the same query block.
- `HAVING` cannot normally reference a window-function result from the same query block.
- A CTE or derived table creates another query block.
- The outer query can then filter the computed window value.

## Data Grain Is the Most Important Concept

Every CTE should have an intentional **grain**: what one row represents.

For example:

```text
orders
    → one row per order

customer_revenue
    → one row per customer

monthly_customer_revenue
    → one row per customer per month

ranked_customers
    → one row per customer per month + ranking metadata
```

This matters because window functions operate over the rows produced by their input relation.

Consider:

```sql
WITH monthly_customer_revenue AS (
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
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank
FROM monthly_customer_revenue;
```

The window function ranks **customers within each month** because the CTE established one row per customer per month.

Without understanding the CTE's grain, the same window expression can easily be misunderstood.

## Top-N Per Group

One of the most common CTE + window patterns is top-N per group.

Suppose a reporting service needs the top three products by revenue in each category.

First aggregate:

```sql
WITH product_revenue AS (
    SELECT
        category_id,
        product_id,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items AS oi
    JOIN orders AS o
        ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY
        category_id,
        product_id
)
SELECT *
FROM product_revenue;
```

Then rank:

```sql
WITH product_revenue AS (
    SELECT
        category_id,
        product_id,
        SUM(oi.quantity * oi.unit_price) AS revenue
    FROM order_items AS oi
    JOIN orders AS o
        ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY
        category_id,
        product_id
),
ranked_products AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS category_rank
    FROM product_revenue
)
SELECT
    category_id,
    product_id,
    revenue,
    category_rank
FROM ranked_products
WHERE category_rank <= 3
ORDER BY category_id, category_rank;
```

The stages are explicit:

```text
Completed order items
        ↓
Revenue per product
        ↓
Rank within category
        ↓
Keep top 3
```

## Choosing the Ranking Function

The choice of window function determines how ties behave.

| Function | Ties share rank? | Rank gaps after ties? | Exactly N rows possible? |
|---|---:|---:|---:|
| `ROW_NUMBER()` | No | No | Yes |
| `RANK()` | Yes | Yes | No |
| `DENSE_RANK()` | Yes | No | No |

Example:

| Product | Revenue | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---|---:|---:|---:|---:|
| A | 1000 | 1 | 1 | 1 |
| B | 900 | 2 | 2 | 2 |
| C | 900 | 3 | 2 | 2 |
| D | 700 | 4 | 4 | 3 |

Use:

- `ROW_NUMBER()` when the requirement is exactly N rows.
- `RANK()` when equal values should share the same rank and rank gaps are meaningful.
- `DENSE_RANK()` when equal values should share the same rank without gaps.

## Latest Row Per Entity

A CTE combined with `ROW_NUMBER()` is a standard pattern for selecting the latest state for each entity.

Suppose an account has a status-history table:

```sql
WITH ranked_statuses AS (
    SELECT
        id,
        account_id,
        status,
        changed_at,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY changed_at DESC, id DESC
        ) AS row_num
    FROM account_status_history
)
SELECT
    account_id,
    status,
    changed_at
FROM ranked_statuses
WHERE row_num = 1;
```

The secondary ordering by `id DESC` is intentional.

If two records have the same timestamp, ordering only by `changed_at` does not provide a deterministic tie-breaker.

For production queries, deterministic ordering matters when the result is consumed by APIs, caches, background jobs, or downstream services.

## Running Totals

A CTE can first establish the correct aggregation grain and then a window function can calculate a cumulative value.

```sql
WITH daily_revenue AS (
    SELECT
        DATE(created_at) AS day,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE(created_at)
)
SELECT
    day,
    revenue,
    SUM(revenue) OVER (
        ORDER BY day
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM daily_revenue
ORDER BY day;
```

The CTE produces:

```text
one row per day
```

The window function therefore calculates the cumulative revenue over daily rows.

## Comparing Current and Previous Rows

`LAG()` and `LEAD()` are particularly useful after a CTE establishes the correct analytical grain.

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (
        ORDER BY month
    ) AS previous_month_revenue,
    revenue - LAG(revenue) OVER (
        ORDER BY month
    ) AS revenue_change
FROM monthly_revenue
ORDER BY month;
```

The CTE ensures `LAG()` compares months rather than individual orders.

## Percentage of Total

A CTE can aggregate first and then a window function can calculate the overall total.

```sql
WITH category_revenue AS (
    SELECT
        category_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY category_id
)
SELECT
    category_id,
    revenue,
    ROUND(
        100.0 * revenue
        / NULLIF(SUM(revenue) OVER (), 0),
        2
    ) AS percentage_of_total
FROM category_revenue
ORDER BY revenue DESC;
```

The expression:

```sql
SUM(revenue) OVER ()
```

calculates the total across all category rows while preserving each category row.

`NULLIF(..., 0)` prevents division-by-zero errors.

## Partitioned Percentage

The same technique can calculate each product's share within its category.

```sql
WITH product_revenue AS (
    SELECT
        category_id,
        product_id,
        SUM(amount) AS revenue
    FROM order_items
    GROUP BY
        category_id,
        product_id
)
SELECT
    category_id,
    product_id,
    revenue,
    ROUND(
        100.0 * revenue
        / NULLIF(
            SUM(revenue) OVER (
                PARTITION BY category_id
            ),
            0
        ),
        2
    ) AS category_share
FROM product_revenue;
```

Here the calculation answers:

> What percentage of the category's revenue does this product represent?

The CTE establishes the product-level revenue, and the window function calculates the category-level denominator.

## Multiple Analytical Stages

Complex reports often require several different window calculations.

```sql
WITH customer_metrics AS (
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
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank,
    LAG(revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
    ) AS previous_month_revenue,
    SUM(revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_customer_revenue
FROM customer_metrics;
```

Each window answers a different question:

| Window calculation | Question |
|---|---|
| `RANK()` by month | How does this customer compare with other customers this month? |
| `LAG()` by customer | What was this customer's previous month's revenue? |
| Running `SUM()` by customer | What is this customer's cumulative revenue? |

## CTEs and Window Frames

Window frames are evaluated against the rows available to the window operation.

For example:

```sql
WITH daily_sales AS (
    SELECT
        DATE(created_at) AS day,
        SUM(amount) AS sales
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE(created_at)
)
SELECT
    day,
    sales,
    AVG(sales) OVER (
        ORDER BY day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_day_average
FROM daily_sales
ORDER BY day;
```

The CTE produces one row per day.

Therefore:

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

represents seven rows and, assuming there is exactly one row for every calendar day, a seven-day period.

This distinction is important:

> `ROWS` counts rows, not time.

If dates are missing, seven rows may span more than seven calendar days.

## Filtering After a Window Function

A CTE provides a clean boundary for filtering analytical results.

```sql
WITH ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS row_num
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue,
    row_num
FROM ranked
WHERE row_num <= 10;
```

The same concept applies to:

- Top-N queries.
- Deduplication.
- Latest-record selection.
- Threshold filtering.
- Ranking-based pagination.
- Analytical eligibility rules.

## CTE vs Derived Table

A CTE is not inherently faster than an equivalent derived table.

CTE:

```sql
WITH ranked AS (
    SELECT
        product_id,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, product_id
        ) AS row_num
    FROM products
)
SELECT *
FROM ranked
WHERE row_num <= 10;
```

Derived table:

```sql
SELECT *
FROM (
    SELECT
        product_id,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, product_id
        ) AS row_num
    FROM products
) AS ranked
WHERE row_num <= 10;
```

Both create a query boundary.

Prefer a CTE when:

- The query has several logical stages.
- An intermediate result has a meaningful name.
- Multiple downstream expressions use the same stage.
- The query is easier to review when written as a pipeline.

A derived table can be preferable when the intermediate relation is small and local to a single expression.

## PostgreSQL CTE Materialization

In PostgreSQL, CTEs may be folded into the surrounding query when the optimizer determines that doing so is appropriate.

PostgreSQL also supports explicit materialization control:

```sql
WITH customer_metrics AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_metrics;
```

Conversely:

```sql
WITH customer_metrics AS NOT MATERIALIZED (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_metrics;
```

Materialization can be useful when an expensive intermediate result is reused and computing it once is beneficial.

However, materialization can also prevent useful optimizer transformations such as predicate pushdown and may introduce additional memory or temporary I/O.

Do not use `MATERIALIZED` as a generic performance optimization.

Validate the effect with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

## Performance Considerations

The presence of CTEs does not automatically make a query slow.

For window-heavy queries, common expensive operations include:

- Large table scans.
- Large joins.
- Aggregation.
- Sorting for window functions.
- Large intermediate relations.
- Multiple window specifications with incompatible ordering.
- Unnecessary materialization.
- Row multiplication caused by incorrect joins.

For example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS row_num
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue
FROM ranked
WHERE row_num <= 10;
```

Inspect:

- Actual row counts.
- Sort operations.
- Sort memory usage.
- Temporary disk usage.
- Sequential scans.
- Index scans.
- Aggregation cost.
- Join cardinality.
- Whether filters are pushed down effectively.

The objective is not to eliminate CTEs. It is to produce a correct execution plan at an acceptable cost.

## Indexing Considerations

Indexes can reduce the cost of filtering and joining before the window stage.

For example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_status_customer
ON orders (status, customer_id);
```

Whether this index helps depends on:

- Query predicates.
- Data distribution.
- Table size.
- Existing indexes.
- PostgreSQL statistics.
- The actual execution plan.

An index does not necessarily eliminate the sorting required by a window function, particularly when the window operates on an aggregated CTE result.

Always verify with `EXPLAIN (ANALYZE, BUFFERS)`.

## Production Backend Pattern

Consider an API endpoint:

```text
GET /reports/customers/top
```

The application might execute:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = :tenant_id
      AND status = 'completed'
    GROUP BY customer_id
    HAVING COUNT(*) >= :minimum_orders
),
ranked_customers AS (
    SELECT
        customer_id,
        order_count,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC, customer_id
        ) AS position
    FROM customer_metrics
)
SELECT
    customer_id,
    order_count,
    revenue,
    position
FROM ranked_customers
WHERE position <= :limit
ORDER BY position;
```

The query stages map directly to business rules:

```text
Tenant boundary
      ↓
Completed orders
      ↓
Customer aggregation
      ↓
Eligibility filter
      ↓
Ranking
      ↓
Top N
```

This structure is easier to test because each stage has a clear responsibility.

## Security Considerations

CTEs and window functions do not provide authorization boundaries.

In a multi-tenant system, tenant filtering should be applied before tenant data participates in aggregation or window calculations:

```sql
WHERE tenant_id = :tenant_id
```

This matters for calculations such as:

```sql
SUM(revenue) OVER ()
```

If other tenants are included before the window calculation, the denominator can contain data that the current tenant should never have access to.

Use parameterized queries:

```python
cursor.execute(
    """
    WITH customer_metrics AS (
        SELECT
            customer_id,
            SUM(amount) AS revenue
        FROM orders
        WHERE tenant_id = %s
        GROUP BY customer_id
    )
    SELECT
        customer_id,
        revenue,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM customer_metrics
    """,
    [tenant_id],
)
```

Do not interpolate request parameters directly into SQL.

For Django, FastAPI, or other Python services, the same principle applies whether SQL is executed through an ORM, query builder, or database driver.

## Common Mistakes

### Filtering a Window Result in the Same Query Block

Incorrect:

```sql
SELECT
    customer_id,
    ROW_NUMBER() OVER (
        ORDER BY revenue DESC
    ) AS row_num
FROM customer_revenue
WHERE row_num <= 10;
```

Correct:

```sql
WITH ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS row_num
    FROM customer_revenue
)
SELECT *
FROM ranked
WHERE row_num <= 10;
```

### Losing Track of Data Grain

Suppose a CTE produces:

```text
one row per customer per month
```

Joining another one-to-many relation afterward can multiply those rows.

The subsequent window calculation may then operate on duplicated business facts.

Before adding a join, explicitly ask:

> What does one row represent at this stage?

### Assuming Every CTE Materializes

Do not automatically think:

```text
CTE
 ↓
execute completely
 ↓
store temporary result
 ↓
outer query
```

The optimizer may inline or otherwise transform the query.

Use `EXPLAIN` to understand the actual plan.

### Assuming CTEs Always Improve Performance

CTEs improve structure and readability, but they do not inherently improve execution time.

A badly structured CTE can produce a huge intermediate relation or prevent useful optimization.

### Using the Wrong Ranking Function

If the requirement is:

> Return exactly five products per category.

`RANK()` may return more than five rows because ties share the same rank.

Use `ROW_NUMBER()` when exactly N rows are required.

### Omitting Tie-Breakers

Avoid:

```sql
ROW_NUMBER() OVER (
    PARTITION BY category_id
    ORDER BY revenue DESC
)
```

when deterministic output matters.

Prefer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY category_id
    ORDER BY revenue DESC, product_id
)
```

### Filtering Too Late

If a filter can safely reduce the dataset before aggregation, applying it afterward can cause unnecessary work.

Prefer:

```sql
WHERE status = 'completed'
```

before:

```sql
GROUP BY
```

when the business requirement is specifically based on completed orders.

### Overusing CTEs

CTEs should represent meaningful semantic boundaries.

Useful boundaries include:

- Changing data grain.
- Encapsulating expensive or reusable logic.
- Preparing data for a window calculation.
- Filtering a window result.
- Separating business stages.

Creating a CTE for every expression usually increases cognitive overhead without improving the query.

## Interview Traps

| Question | Correct reasoning |
|---|---|
| Why combine a CTE with a window function? | The CTE creates a query boundary that allows the window result to be filtered or consumed by another stage. |
| Can a window function normally be referenced in `WHERE` in the same query block? | No. The window result is not available at the `WHERE` stage. |
| Does a CTE automatically materialize? | No. Behavior depends on the database and optimizer; PostgreSQL can inline eligible CTEs. |
| Does a CTE automatically improve performance? | No. It primarily improves query organization; execution performance depends on the query plan. |
| Why is data grain important? | Window functions operate on the rows produced by their input relation, so changing the grain changes the meaning of the calculation. |
| When should `ROW_NUMBER()` be preferred over `RANK()`? | When exactly N rows per partition are required and deterministic tie-breaking is acceptable. |
| Can a window function operate on an aggregate produced by a CTE? | Yes. The CTE can establish the aggregate grain, after which the window operates over those aggregate rows. |
| Why can forced CTE materialization hurt performance? | It can prevent predicate pushdown and other optimizer transformations and may require additional memory or temporary I/O. |

## Key Takeaways

- **CTEs create explicit query stages, while window functions calculate across related rows without collapsing the input grain.**
- **Use a CTE or derived table when a window result must be filtered, reused, or consumed by another query stage.**
- **Always know the grain of each CTE because `PARTITION BY`, ordering, frames, and aggregates operate on that intermediate relation.**
- **CTEs are not automatic performance optimizations; validate sorting, joins, scans, materialization, and intermediate row counts with execution plans.**
- **Production analytical queries should make filtering, ranking semantics, tie-breaking, tenant boundaries, and data grain explicit.**