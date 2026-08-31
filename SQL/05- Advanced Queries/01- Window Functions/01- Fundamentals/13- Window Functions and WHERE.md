# 13- Window Functions and WHERE

## Overview

A window function calculates a value across a set of related rows while preserving the rows in the result. The `WHERE` clause, however, filters rows before the window calculation is logically evaluated.

This ordering creates one of the most important rules for writing correct analytical SQL:

> A window function cannot normally be used directly in the `WHERE` clause of the same query block.

The practical consequence is that filtering on a window result requires another relational layer, typically a:

- Common Table Expression (CTE)
- Derived table
- View
- Materialized view for repeatedly used analytical results

This distinction matters for queries such as:

- Top-N records per customer.
- Latest record per entity.
- Highest-paid employees per department.
- Ranking products within categories.
- Filtering rows based on running totals.
- Selecting rows based on `ROW_NUMBER()`, `RANK()`, or `DENSE_RANK()`.

## The Core Execution Model

A useful logical model for a query containing a window function is:

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

The database optimizer is free to implement the query differently, but this logical ordering explains the SQL language rules.

Consider:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    RANK() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees
WHERE salary_rank <= 3;
```

This is invalid because `salary_rank` is produced by the window-function stage, while `WHERE` must filter its input before that value exists.

The database cannot logically evaluate:

```text
WHERE salary_rank <= 3
```

before calculating:

```sql
RANK() OVER (...)
```

## Why the Extra Query Layer Is Required

The solution is to calculate the window value first and filter it in an outer query.

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        RANK() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
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

The logical flow becomes:

```text
employees
    │
    ▼
calculate salary_rank
    │
    ▼
ranked_employees
    │
    ▼
WHERE salary_rank <= 3
    │
    ▼
final result
```

The CTE creates a new query boundary where `salary_rank` is now an ordinary column that can be filtered.

## Same Query Block vs Outer Query

The important distinction is not:

> "SQL cannot filter window functions."

SQL absolutely can filter the results of window functions.

The actual rule is:

> A query block cannot normally reference a window-function result in its own `WHERE` clause.

This works:

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC, order_id DESC
        ) AS row_num
    FROM orders
)
SELECT *
FROM ranked_orders
WHERE row_num = 1;
```

The window function belongs to one query block, while the filter belongs to another.

## The Most Common Pattern: Top-N Per Group

A common backend requirement is:

> Return the three most recent orders for every customer.

A correlated query or application-side loop is unnecessary.

Use:

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        order_date,
        amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC, order_id DESC
        ) AS row_num
    FROM orders
)
SELECT
    order_id,
    customer_id,
    order_date,
    amount
FROM ranked_orders
WHERE row_num <= 3
ORDER BY
    customer_id,
    order_date DESC,
    order_id DESC;
```

The window function assigns a position within each customer.

The outer query filters those positions.

### Why `ROW_NUMBER()` Is Useful Here

`ROW_NUMBER()` assigns exactly one number to each row:

```text
customer_id   order_id   row_num
-----------   --------   -------
10            501        1
10            502        2
10            503        3
20            601        1
20            602        2
```

Filtering:

```sql
WHERE row_num <= 3
```

therefore returns exactly three rows per customer, assuming at least three rows exist.

## `RANK()` Changes the Semantics

Suppose two employees have the same salary.

```sql
RANK() OVER (
    PARTITION BY department_id
    ORDER BY salary DESC
)
```

can produce:

```text
employee   salary   rank
-------    ------   ----
A          200000   1
B          180000   2
C          180000   2
D          150000   4
```

Filtering:

```sql
WHERE rank <= 2
```

returns three employees, not two.

This is correct because `RANK()` preserves ties.

If the business requirement means:

> Exactly three rows per department

use `ROW_NUMBER()` with a deterministic tie-breaker.

If the requirement means:

> Everyone tied within the top three ranking positions

use `RANK()`.

## `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`

| Function | Ties share rank? | Gaps after ties? | Typical use |
|---|---:|---:|---|
| `ROW_NUMBER()` | No | N/A | Exactly N rows |
| `RANK()` | Yes | Yes | Competition-style ranking |
| `DENSE_RANK()` | Yes | No | Ranking distinct values |

Example:

```text
salary
------
200
180
180
150
```

produces:

| Salary | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---:|---:|---:|---:|
| 200 | 1 | 1 | 1 |
| 180 | 2 | 2 | 2 |
| 180 | 3 | 2 | 2 |
| 150 | 4 | 4 | 3 |

Choosing the function is a business-semantics decision, not merely a SQL syntax decision.

## `WHERE` Changes the Window Population

Another critical issue is that `WHERE` does not merely affect the final output. It changes the rows available to the window function.

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

The window function sees only orders from 2026 onward.

Therefore:

```sql
customer_total
```

means:

> Total amount for this customer among orders from 2026 onward.

It does **not** mean:

> Lifetime total for this customer.

This is a frequent production bug because the SQL looks reasonable while the metric's population is wrong.

## Filtering After the Window

If the requirement is:

> Show only 2026 orders, but calculate each customer's lifetime total.

The lifetime calculation must occur before the date filter.

One approach is aggregation plus a join:

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
    o.order_date,
    ct.lifetime_total
FROM orders AS o
JOIN customer_totals AS ct
    ON ct.customer_id = o.customer_id
WHERE o.order_date >= DATE '2026-01-01';
```

Another approach uses a window in an inner query:

```sql
WITH orders_with_totals AS (
    SELECT
        order_id,
        customer_id,
        amount,
        order_date,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS lifetime_total
    FROM orders
)
SELECT
    order_id,
    customer_id,
    amount,
    order_date,
    lifetime_total
FROM orders_with_totals
WHERE order_date >= DATE '2026-01-01';
```

Here the window calculation happens before the outer query applies the date filter.

## Filtering Before vs After the Window

These two queries have different meanings.

### Filter Before the Window

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

Conceptually:

```text
all orders
   ↓
filter 2026 orders
   ↓
calculate customer totals
```

### Filter After the Window

```sql
WITH orders_with_totals AS (
    SELECT
        order_id,
        customer_id,
        amount,
        order_date,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
)
SELECT *
FROM orders_with_totals
WHERE order_date >= DATE '2026-01-01';
```

Conceptually:

```text
all orders
   ↓
calculate lifetime customer totals
   ↓
filter displayed orders
```

The difference is entirely about the population over which the metric is calculated.

## `HAVING` Has a Similar Effect

`HAVING` filters grouped rows before the window function operates on the grouped result.

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

The ranking population contains only customers whose total is at least `1000`.

If the requirement is:

> Rank every customer, then return only customers ranked in the top 10.

use an outer query:

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

This preserves the full ranking population.

## CTE vs Derived Table

Both CTEs and derived tables can create the required query boundary.

### CTE

```sql
WITH ranked_products AS (
    SELECT
        product_id,
        revenue,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS product_rank
    FROM product_revenue
)
SELECT *
FROM ranked_products
WHERE product_rank <= 10;
```

### Derived Table

```sql
SELECT *
FROM (
    SELECT
        product_id,
        revenue,
        RANK() OVER (
            ORDER BY revenue DESC
        ) AS product_rank
    FROM product_revenue
) AS ranked_products
WHERE product_rank <= 10;
```

The choice is usually about readability, maintainability, and query structure rather than correctness.

| Approach | Strength |
|---|---|
| CTE | Clear multi-stage query structure |
| Derived table | Compact local transformation |
| View | Reusable logical interface |
| Materialized view | Useful for repeatedly queried expensive results |

A CTE should not automatically be interpreted as a physically materialized temporary table. Modern optimizers may inline or transform CTEs.

## `QUALIFY`

Some SQL systems support `QUALIFY`, which is specifically designed to filter rows after window-function evaluation.

Conceptually:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    ROW_NUMBER() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS row_num
FROM employees
QUALIFY row_num <= 3;
```

This expresses the intent directly:

```text
FROM
  ↓
WHERE
  ↓
GROUP BY / HAVING
  ↓
Window function
  ↓
QUALIFY
  ↓
SELECT
```

However, `QUALIFY` is not universally supported across SQL databases.

For portable SQL, a CTE or derived table remains the safer approach.

## PostgreSQL Consideration

PostgreSQL does not provide a general `QUALIFY` clause, so the standard pattern is:

```sql
WITH ranked_rows AS (
    SELECT
        ...,
        ROW_NUMBER() OVER (...) AS row_num
    FROM ...
)
SELECT ...
FROM ranked_rows
WHERE row_num <= 3;
```

This is particularly relevant for PostgreSQL-backed Django, FastAPI, and SQLAlchemy applications.

## Window Functions and Pagination

A common API requirement is:

> Return the top 10 products in each category.

A window function is appropriate:

```sql
WITH ranked_products AS (
    SELECT
        product_id,
        category_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS row_num
    FROM product_revenue
)
SELECT
    product_id,
    category_id,
    revenue
FROM ranked_products
WHERE row_num <= 10;
```

The `product_id` tie-breaker makes the ordering deterministic.

For general API pagination, however, do not assume window functions are always the best tool. For a globally ordered feed, keyset pagination can be significantly more efficient than repeatedly calculating row numbers across a large dataset.

## Deterministic Ordering

A window function with an incomplete ordering can produce unstable results.

Avoid:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY order_date DESC
)
```

if multiple orders can share the same `order_date` and the application requires deterministic selection.

Prefer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY order_date DESC, order_id DESC
)
```

The unique `order_id` provides a deterministic tie-breaker.

This matters for:

- APIs.
- Scheduled jobs.
- Reconciliation processes.
- Pagination.
- Tests.
- Repeated report generation.

## Performance Considerations

Filtering before a window can reduce the amount of data that the window must process.

For example:

```sql
SELECT
    ...,
    ROW_NUMBER() OVER (...) AS row_num
FROM orders
WHERE tenant_id = :tenant_id;
```

may be substantially cheaper than calculating a window across every tenant and filtering later.

But this is only correct if the window's intended population is the tenant's rows.

The optimization must never change the metric's semantics.

For PostgreSQL, inspect important queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
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
WHERE row_num <= 3;
```

Pay particular attention to:

- Sort operations.
- Large intermediate row sets.
- Memory usage.
- Temporary-file spills.
- Sequential scans.
- Join cardinality.
- Actual versus estimated row counts.

Indexes can improve filtering and joins and may help with ordering, but the optimizer determines whether an index is beneficial.

## Multi-Tenant Backend Systems

Tenant isolation should be applied carefully.

For example:

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        tenant_id,
        order_date,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY order_date DESC, order_id DESC
        ) AS row_num
    FROM orders
    WHERE tenant_id = :tenant_id
)
SELECT *
FROM ranked_orders
WHERE row_num <= 10;
```

Filtering by `tenant_id` inside the inner query is both:

- Semantically important when rankings should be tenant-local.
- Potentially more efficient because fewer rows reach the window operation.

In production systems, tenant filters should also be enforced through appropriate application authorization and, where applicable, PostgreSQL Row-Level Security rather than relying solely on developer discipline.

## Security Considerations

Window functions do not create a security boundary.

A query such as:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

does not prevent one tenant from seeing another tenant's rows.

Authorization and tenant filtering must happen in the relational input.

For example:

```sql
FROM orders
WHERE tenant_id = :tenant_id
```

must reflect the actual authorization context.

Prefer parameterized queries:

```python
cursor.execute(
    """
    SELECT
        order_id,
        customer_id,
        amount
    FROM orders
    WHERE tenant_id = %s
    """,
    [tenant_id],
)
```

Never construct SQL by interpolating untrusted request parameters.

## Common Mistakes

### Referencing a Window Alias in `WHERE`

Incorrect:

```sql
SELECT
    employee_id,
    ROW_NUMBER() OVER (
        ORDER BY salary DESC
    ) AS row_num
FROM employees
WHERE row_num <= 10;
```

Correct:

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        ROW_NUMBER() OVER (
            ORDER BY salary DESC
        ) AS row_num
    FROM employees
)
SELECT *
FROM ranked_employees
WHERE row_num <= 10;
```

### Filtering Before a Lifetime Calculation

Incorrect when lifetime totals are required:

```sql
SELECT
    order_id,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS lifetime_total
FROM orders
WHERE order_date >= :start_date;
```

The window only sees rows surviving `WHERE`.

Use a separate query layer when the calculation must include historical rows.

### Ranking After Filtering the Wrong Population

This:

```sql
WHERE region = 'APAC'
```

before:

```sql
RANK() OVER (ORDER BY revenue DESC)
```

creates an APAC-only ranking.

That is incorrect if the requirement is global ranking followed by an APAC filter.

### Using `RANK()` When Exactly N Rows Are Required

Because ties share ranks:

```sql
RANK() OVER (...)
```

can return more than N rows for:

```sql
WHERE rank <= N
```

Use `ROW_NUMBER()` if exactly N rows per partition are required.

### Missing a Tie-Breaker

This:

```sql
ORDER BY created_at DESC
```

may leave the relative order of equal timestamps unspecified.

Use a stable unique column when deterministic results matter:

```sql
ORDER BY created_at DESC, id DESC
```

### Performing Analytics in Application Code

Avoid patterns such as:

```python
orders = fetch_all_orders()
orders.sort(...)
```

followed by Python loops to calculate ranks or running totals.

For relational analytical operations, pushing the computation into PostgreSQL usually:

- Reduces network transfer.
- Reduces application memory usage.
- Uses database query optimization.
- Avoids duplicating SQL semantics in application code.

The exception is when the computation genuinely belongs to the application layer or requires non-relational business logic.

## Production Checklist

Before shipping a query that filters on a window-function result:

- [ ] Is the window calculation in an inner query layer?
- [ ] Is the filter on the window result in the outer query?
- [ ] Is the intended window population correct?
- [ ] Are `WHERE` and `HAVING` filtering too early?
- [ ] Does the query require `ROW_NUMBER()`, `RANK()`, or `DENSE_RANK()`?
- [ ] Are ties handled according to business requirements?
- [ ] Is the window `ORDER BY` deterministic?
- [ ] Are tenant and authorization filters applied to the correct input?
- [ ] Has the query been tested with realistic duplicate values and ties?
- [ ] Has `EXPLAIN (ANALYZE, BUFFERS)` been reviewed for expensive workloads?
- [ ] Is the query appropriate for the OLTP database, or should it run against a read replica or analytical system?

## Interview Traps

| Question | Correct reasoning |
|---|---|
| Can a window function be used directly in `WHERE`? | No, not in the same query block because `WHERE` logically precedes window evaluation. |
| How do you filter `ROW_NUMBER()` results? | Calculate it in a CTE or derived table and filter in the outer query. |
| Does `WHERE` affect a window function? | Yes. Rows removed by `WHERE` are not visible to the window in that query block. |
| How do you calculate a lifetime metric while returning only recent rows? | Calculate the metric in an inner query and apply the recent-row filter in an outer query. |
| Why might `RANK() <= 3` return more than three rows? | Ties share the same rank. |
| How do you guarantee exactly three rows per partition? | Use `ROW_NUMBER()` with deterministic ordering. |
| What does an outer query provide? | A new query boundary where the window result can be treated as a normal column. |
| Does a CTE necessarily materialize its result? | No. The optimizer may inline or transform it. |
| What is `QUALIFY`? | A clause supported by some SQL systems for filtering after window-function evaluation. |

## Key Takeaways

- **A window function cannot normally be referenced directly in the `WHERE` clause of the same query block because `WHERE` is logically evaluated before window functions.**
- **Use a CTE or derived table to calculate the window value first, then filter it in an outer query.**
- **`WHERE` changes the population visible to a window function, so filtering before versus after the window can completely change the meaning of a metric.**
- **Choose `ROW_NUMBER()`, `RANK()`, or `DENSE_RANK()` according to tie semantics and whether the requirement demands exactly N rows or N ranking positions.**
- **Make window ordering deterministic, apply authorization filters to the correct input population, and validate expensive analytical queries with realistic execution plans.**