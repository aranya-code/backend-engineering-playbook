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