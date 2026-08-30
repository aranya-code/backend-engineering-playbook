# 21- Subquery vs Window Function

## Overview

Subqueries and window functions can both solve problems involving comparisons, rankings, aggregates, and row-level calculations, but they operate at fundamentally different levels.

A **subquery** produces a result that another query consumes:

```sql
SELECT
    p.id,
    p.name,
    p.price
FROM products AS p
WHERE p.price > (
    SELECT AVG(price)
    FROM products
);
```

A **window function** calculates a value across a related set of rows while preserving the individual rows:

```sql
SELECT
    p.id,
    p.name,
    p.price,
    AVG(p.price) OVER () AS average_price
FROM products AS p;
```

The key distinction is:

> Use a subquery when you need another query's result to participate in filtering, joining, or further query composition. Use a window function when you need an aggregate, ranking, or analytic calculation alongside each row.

Choosing between them affects readability, execution plans, scalability, and the amount of data returned to a backend application.

## The Core Difference

Consider a requirement:

> Return each employee and the average salary of their department.

A subquery can express this with a correlated lookup:

```sql
SELECT
    e.id,
    e.name,
    e.department_id,
    e.salary,
    (
        SELECT AVG(e2.salary)
        FROM employees AS e2
        WHERE e2.department_id = e.department_id
    ) AS department_average
FROM employees AS e;
```

A window function expresses the same calculation directly:

```sql
SELECT
    e.id,
    e.name,
    e.department_id,
    e.salary,
    AVG(e.salary) OVER (
        PARTITION BY e.department_id
    ) AS department_average
FROM employees AS e;
```

The window-function version directly communicates the analytical requirement:

```text
Employees
   │
   ├── Partition by department
   │
   ├── Calculate AVG(salary)
   │
   └── Preserve every employee row
```

The subquery version asks the database to derive the department-level value and associate it with each employee.

## What a Window Function Does

A window function performs a calculation across a set of rows related to the current row without collapsing those rows into a single result.

Common window functions include:

- `ROW_NUMBER()`
- `RANK()`
- `DENSE_RANK()`
- `LAG()`
- `LEAD()`
- `SUM() OVER (...)`
- `AVG() OVER (...)`
- `MIN() OVER (...)`
- `MAX() OVER (...)`
- `COUNT() OVER (...)`

Example:

```sql
SELECT
    e.id,
    e.name,
    e.department_id,
    e.salary,
    RANK() OVER (
        PARTITION BY e.department_id
        ORDER BY e.salary DESC
    ) AS salary_rank
FROM employees AS e;
```

Unlike `GROUP BY`, the window function does not reduce one department to one row.

## Window Function vs GROUP BY

This distinction is critical.

`GROUP BY` collapses rows:

```sql
SELECT
    department_id,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department_id;
```

Result:

| department_id | average_salary |
|---:|---:|
| 10 | 85000 |
| 20 | 92000 |
| 30 | 78000 |

A window function preserves employee rows:

```sql
SELECT
    id,
    name,
    department_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS average_salary
FROM employees;
```

Result conceptually:

| id | name | department_id | salary | average_salary |
|---:|---|---:|---:|---:|
| 1 | Alice | 10 | 90000 | 85000 |
| 2 | Bob | 10 | 80000 | 85000 |
| 3 | Carol | 20 | 95000 | 92000 |

This makes window functions particularly useful for analytics where both the individual row and its group-level context are required.

## Subquery for Filtering Against an Aggregate

A common subquery pattern is filtering rows based on an aggregate:

```sql
SELECT
    e.id,
    e.name,
    e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT AVG(salary)
    FROM employees
);
```

The subquery calculates one scalar value, and the outer query uses it as a predicate.

A window-function equivalent can be written using a derived table or CTE:

```sql
WITH employee_metrics AS (
    SELECT
        e.id,
        e.name,
        e.salary,
        AVG(e.salary) OVER () AS average_salary
    FROM employees AS e
)
SELECT
    id,
    name,
    salary
FROM employee_metrics
WHERE salary > average_salary;
```

The reason for the additional query layer is important:

> Window functions are evaluated after `WHERE`, so a window-function result generally cannot be referenced directly in the same query block's `WHERE` clause.

## Logical Query Processing

Understanding SQL's logical processing order helps explain this difference.

A simplified model is:

```text
FROM / JOIN
    ↓
WHERE
    ↓
GROUP BY
    ↓
HAVING
    ↓
Window Functions
    ↓
SELECT / ORDER BY
```

The exact physical execution plan can differ because the optimizer is free to transform the query, but SQL semantics impose restrictions on where window-function results can be referenced.

For example, this is invalid:

```sql
SELECT
    e.id,
    e.salary,
    AVG(e.salary) OVER () AS average_salary
FROM employees AS e
WHERE e.salary > AVG(e.salary) OVER ();
```

Instead, use a CTE:

```sql
WITH metrics AS (
    SELECT
        e.id,
        e.salary,
        AVG(e.salary) OVER () AS average_salary
    FROM employees AS e
)
SELECT
    id,
    salary
FROM metrics
WHERE salary > average_salary;
```

Or use a scalar subquery:

```sql
SELECT
    e.id,
    e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT AVG(salary)
    FROM employees
);
```

## Correlated Subquery vs Window Function

Correlated subqueries reference columns from the outer query.

```sql
SELECT
    e.id,
    e.name,
    e.salary,
    (
        SELECT AVG(e2.salary)
        FROM employees AS e2
        WHERE e2.department_id = e.department_id
    ) AS department_average
FROM employees AS e;
```

The inner query depends on the current outer employee's department.

A window function expresses the same relationship more directly:

```sql
SELECT
    e.id,
    e.name,
    e.salary,
    AVG(e.salary) OVER (
        PARTITION BY e.department_id
    ) AS department_average
FROM employees AS e;
```

For this class of analytical calculation, the window function is often the clearer formulation.

However, do not assume that correlated subqueries are always inefficient. Modern optimizers can transform correlated subqueries into joins, semi-joins, aggregates, or other efficient plans.

Always inspect the execution plan for performance-sensitive workloads.

## Ranking: Subquery vs Window Function

Ranking is one of the strongest use cases for window functions.

Suppose the requirement is:

> Return the highest-paid employee in each department.

A window function:

```sql
WITH ranked_employees AS (
    SELECT
        e.id,
        e.name,
        e.department_id,
        e.salary,
        ROW_NUMBER() OVER (
            PARTITION BY e.department_id
            ORDER BY e.salary DESC, e.id
        ) AS row_num
    FROM employees AS e
)
SELECT
    id,
    name,
    department_id,
    salary
FROM ranked_employees
WHERE row_num = 1;
```

This is considerably more expressive than trying to construct the same result through nested subqueries.

### Why `ROW_NUMBER()` Instead of `MAX()`?

This query:

```sql
SELECT
    department_id,
    MAX(salary) AS maximum_salary
FROM employees
GROUP BY department_id;
```

only returns the salary.

If the application also needs the employee's ID and name, additional logic is required.

A window function keeps the complete row:

```sql
SELECT
    id,
    name,
    department_id,
    salary
FROM (
    SELECT
        e.*,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC, id
        ) AS row_num
    FROM employees AS e
) AS ranked
WHERE row_num = 1;
```

## Top N Per Group

Window functions are particularly effective for top-N-per-group queries.

Example:

> Return the three highest-revenue orders for every customer.

```sql
WITH ranked_orders AS (
    SELECT
        o.id,
        o.customer_id,
        o.amount,
        o.created_at,
        ROW_NUMBER() OVER (
            PARTITION BY o.customer_id
            ORDER BY o.amount DESC, o.id
        ) AS row_num
    FROM orders AS o
)
SELECT
    id,
    customer_id,
    amount,
    created_at
FROM ranked_orders
WHERE row_num <= 3;
```

The equivalent problem is awkward with ordinary scalar subqueries because the requirement is not simply to calculate one value; it requires ranking a set while retaining row identity.

## `RANK()` vs `DENSE_RANK()` vs `ROW_NUMBER()`

These functions are frequently confused.

| Function | Ties | Gaps after ties | Typical use |
|---|---|---|---|
| `ROW_NUMBER()` | Assigns unique numbers | No | Exactly N rows |
| `RANK()` | Same rank for ties | Yes | Competition ranking |
| `DENSE_RANK()` | Same rank for ties | No | Dense ranking |

Example salaries:

| Employee | Salary |
|---|---:|
| A | 100000 |
| B | 100000 |
| C | 90000 |
| D | 80000 |

```sql
SELECT
    name,
    salary,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_number,
    RANK() OVER (ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank
FROM employees;
```

Conceptually:

| Employee | Salary | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---|---:|---:|---:|---:|
| A | 100000 | 1 | 1 | 1 |
| B | 100000 | 2 | 1 | 1 |
| C | 90000 | 3 | 3 | 2 |
| D | 80000 | 4 | 4 | 3 |

The choice depends on the business definition of ranking.

## Running Totals

A correlated subquery can calculate a cumulative value:

```sql
SELECT
    o.id,
    o.customer_id,
    o.created_at,
    o.amount,
    (
        SELECT SUM(o2.amount)
        FROM orders AS o2
        WHERE o2.customer_id = o.customer_id
          AND o2.created_at <= o.created_at
    ) AS running_total
FROM orders AS o;
```

A window function expresses this naturally:

```sql
SELECT
    o.id,
    o.customer_id,
    o.created_at,
    o.amount,
    SUM(o.amount) OVER (
        PARTITION BY o.customer_id
        ORDER BY o.created_at, o.id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders AS o;
```

The explicit frame and deterministic ordering are important.

If multiple orders have the same timestamp, `o.id` provides a stable tie-breaker.

## Previous and Next Rows

Subqueries can sometimes find previous or next records, but window functions provide purpose-built operators.

```sql
SELECT
    o.id,
    o.customer_id,
    o.created_at,
    o.amount,
    LAG(o.amount) OVER (
        PARTITION BY o.customer_id
        ORDER BY o.created_at, o.id
    ) AS previous_amount
FROM orders AS o;
```

Similarly:

```sql
SELECT
    o.id,
    o.customer_id,
    o.created_at,
    o.amount,
    LEAD(o.amount) OVER (
        PARTITION BY o.customer_id
        ORDER BY o.created_at, o.id
    ) AS next_amount
FROM orders AS o;
```

These are useful for:

- Time-series analysis.
- Change detection.
- Customer behavior analysis.
- Event streams.
- Financial reporting.
- Audit history analysis.

## Comparing Each Row With a Group

A frequent backend analytics requirement is:

> Find products whose price is above the average price in their category.

Window-function approach:

```sql
WITH product_metrics AS (
    SELECT
        p.id,
        p.name,
        p.category_id,
        p.price,
        AVG(p.price) OVER (
            PARTITION BY p.category_id
        ) AS category_average
    FROM products AS p
)
SELECT
    id,
    name,
    category_id,
    price,
    category_average
FROM product_metrics
WHERE price > category_average;
```

Subquery approach:

```sql
SELECT
    p.id,
    p.name,
    p.category_id,
    p.price
FROM products AS p
WHERE p.price > (
    SELECT AVG(p2.price)
    FROM products AS p2
    WHERE p2.category_id = p.category_id
);
```

The window version is particularly useful if the response needs both the product and the category statistic.

The subquery can be more concise when the aggregate is only needed as a filter.

## When a Subquery Is Better

Subqueries remain preferable when the intermediate result is naturally independent of individual rows.

### Scalar Lookup

```sql
SELECT
    p.id,
    p.name,
    p.price
FROM products AS p
WHERE p.price > (
    SELECT AVG(price)
    FROM products
);
```

The average is a single scalar value. A window function would calculate the same average for every product even if the application only needs the threshold for filtering.

### Existence Checks

For existence semantics, use `EXISTS`:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'completed'
);
```

A window function is not the natural abstraction for this requirement.

### Membership Tests

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE status = 'completed'
);
```

This is a set-membership problem, not an analytical windowing problem.

## When a Window Function Is Better

Window functions are usually the better abstraction when the requirement involves:

- Ranking.
- Top N per group.
- Running totals.
- Previous/next row comparisons.
- Percentiles.
- Group-level metrics alongside individual rows.
- Sequential comparisons.
- Cumulative calculations.

Example:

```sql
SELECT
    o.id,
    o.customer_id,
    o.amount,
    SUM(o.amount) OVER (
        PARTITION BY o.customer_id
        ORDER BY o.created_at, o.id
    ) AS cumulative_spend
FROM orders AS o;
```

The query describes the analytical relationship directly.

## Performance Considerations

Neither construct has a universal performance advantage.

Performance depends on:

- Database engine.
- Database version.
- Table size.
- Indexes.
- Data distribution.
- Cardinality.
- Sort requirements.
- Join strategy.
- Correlation.
- Window partitions.
- Memory available to the database.
- Whether intermediate results spill to disk.

A window function often requires sorting or otherwise organizing rows according to the window's `PARTITION BY` and `ORDER BY`.

For example:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at
)
```

may require substantial work when `orders` is large.

A correlated subquery may also become expensive if the optimizer cannot decorrelate it efficiently.

Therefore:

> Query shape should guide the initial design, but execution plans should determine the production decision.

## Indexing Considerations

Indexes can help the underlying access pattern, although they do not guarantee that a window operation will avoid sorting.

For:

```sql
SELECT
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS running_total
FROM orders;
```

an index aligned with the partitioning and ordering columns may be useful:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at, id);
```

Whether this index actually improves the query depends on the optimizer and the rest of the execution plan.

Do not create indexes solely because a column appears in `PARTITION BY`.

Indexes also have costs:

- Additional storage.
- Additional write IO.
- Higher insert/update overhead.
- More maintenance work.
- Potentially longer vacuum or statistics maintenance in PostgreSQL.

## Window Frames Matter

Window functions with an `ORDER BY` can operate over a defined frame.

For running totals, explicitly specifying `ROWS` is often safer:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

Do not casually assume that the default frame has exactly the semantics you want.

This becomes especially important when ordering values can tie.

For example, using:

```sql
ORDER BY created_at
```

when multiple rows share the same timestamp can produce behavior that differs from an explicitly defined row-based frame.

Use deterministic ordering where business correctness depends on row sequence.

## Filtering Window Results

Window functions cannot normally be used directly in `WHERE` in the same query block.

Use a CTE:

```sql
WITH ranked AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY amount DESC, id
        ) AS row_num
    FROM orders AS o
)
SELECT
    id,
    customer_id,
    amount
FROM ranked
WHERE row_num <= 3;
```

A derived table works as well:

```sql
SELECT
    id,
    customer_id,
    amount
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY amount DESC, id
        ) AS row_num
    FROM orders AS o
) AS ranked
WHERE row_num <= 3;
```

Some database systems also provide features such as `QUALIFY` for filtering window-function results. Support is database-specific, so portable SQL should use a CTE or derived table unless the target database explicitly supports `QUALIFY`.

## `DISTINCT ON` and Window Functions in PostgreSQL

PostgreSQL provides another useful alternative for certain top-one-per-group queries:

```sql
SELECT DISTINCT ON (customer_id)
    id,
    customer_id,
    amount,
    created_at
FROM orders
ORDER BY customer_id, amount DESC, id;
```

This can be concise and performant for PostgreSQL-specific workloads.

The portable window-function approach is:

```sql
WITH ranked AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY amount DESC, id
        ) AS row_num
    FROM orders AS o
)
SELECT
    id,
    customer_id,
    amount,
    created_at
FROM ranked
WHERE row_num = 1;
```

The choice depends on portability requirements, query complexity, and measured execution performance.

## Backend API Considerations

Suppose a REST endpoint returns the top three orders per customer.

An inefficient application-level approach might:

1. Fetch customers.
2. Fetch all orders for each customer.
3. Sort orders in Python.
4. Keep the top three.
5. Serialize the result.

This can create excessive network transfer, application memory usage, and database round trips.

A database-side window function can perform the ranking:

```sql
WITH ranked_orders AS (
    SELECT
        o.id,
        o.customer_id,
        o.amount,
        o.created_at,
        ROW_NUMBER() OVER (
            PARTITION BY o.customer_id
            ORDER BY o.amount DESC, o.id
        ) AS row_num
    FROM orders AS o
)
SELECT
    id,
    customer_id,
    amount,
    created_at
FROM ranked_orders
WHERE row_num <= 3;
```

The backend receives only the required rows.

This principle applies equally to:

- Django.
- FastAPI.
- gRPC services.
- Background workers.
- Reporting services.

Use the database for set-based relational and analytical operations instead of unnecessarily transferring large datasets into Python.

## Django ORM Example

Django supports window expressions through `Window`.

For example:

```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber

ranked_orders = Order.objects.annotate(
    row_number=Window(
        expression=RowNumber(),
        partition_by=[F("customer_id")],
        order_by=[F("amount").desc(), F("id").asc()],
    )
)
```

Filtering on window expressions has database- and Django-version-specific considerations. For complex queries, inspect the generated SQL and execution plan rather than assuming ORM syntax maps to an optimal database operation.

The generated SQL should be treated as part of the production behavior.

## Security Considerations

Subqueries and window functions do not inherently introduce SQL injection vulnerabilities.

The security risk comes from constructing SQL with untrusted input.

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT
        id,
        email
    FROM customers
    WHERE id IN (
        SELECT customer_id
        FROM orders
        WHERE status = %s
    )
    """,
    [status],
)
```

Do not construct predicates or values through string interpolation:

```python
# Avoid
query = f"""
SELECT id
FROM customers
WHERE status = '{status}'
"""
```

ORMs such as Django's ORM and parameterized database drivers should be preferred for dynamic values.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Using a correlated subquery for ranking | Ranking is awkward and may require repeated work | Use `ROW_NUMBER()`, `RANK()`, or `DENSE_RANK()` |
| Using a window function for simple existence checks | Adds unnecessary complexity | Use `EXISTS` |
| Assuming window functions are always faster | Syntax does not determine execution cost | Inspect execution plans |
| Forgetting deterministic ordering | Ties can produce unstable row selection | Add a unique tie-breaker |
| Filtering directly on a window expression | Window results are not available to same-level `WHERE` | Use a CTE or derived table |
| Confusing `RANK()` and `ROW_NUMBER()` | Ties have different semantics | Choose based on business requirements |
| Ignoring window frames | Default frame may not match intended semantics | Specify the frame when correctness requires it |
| Fetching all rows into Python | Causes unnecessary network and memory usage | Push set-based processing into SQL |
| Adding indexes blindly | Indexes increase write and storage costs | Validate with execution plans and workload data |
| Assuming a correlated subquery always runs once per row | Optimizers may decorrelate it | Reason from the actual plan |

## Interview Traps

### Are window functions always better than subqueries?

No.

Window functions are excellent for analytical calculations over related rows, but subqueries are often clearer for scalar lookups, membership tests, and existence checks.

### Does a window function reduce the number of rows?

No.

Window functions preserve the input rows. `GROUP BY` generally reduces rows by forming groups.

### Why can't a window function normally be used in `WHERE`?

Because window functions are logically evaluated after the filtering phase of the same query block.

Use a CTE or derived table to introduce another query level.

### Are correlated subqueries always slow?

No.

A database optimizer can transform correlated subqueries into efficient joins or other execution strategies. Performance should be determined from the actual execution plan.

### When should `ROW_NUMBER()` be used instead of `RANK()`?

Use `ROW_NUMBER()` when each row must receive a unique position. Use `RANK()` when tied values should receive the same rank and gaps after ties are meaningful.

### Can a window function replace every subquery?

No.

Subqueries provide capabilities such as `EXISTS`, `IN`, scalar expressions, and independent query composition that window functions do not replace directly.

## Practical Decision Framework

| Requirement | Preferred approach |
|---|---|
| Check whether related rows exist | `EXISTS` |
| Check membership in another result set | `IN` / `EXISTS` |
| Compare against one global aggregate | Scalar subquery |
| Compare against a group aggregate while retaining rows | Window function |
| Rank rows | Window function |
| Top N per group | Window function |
| Running total | Window function |
| Previous/next row | `LAG()` / `LEAD()` |
| Calculate a value independently of each outer row | Non-correlated subquery |
| Complex multi-stage query | CTE, possibly with window functions |
| Recursive hierarchy | Recursive CTE |
| Need only grouped results | `GROUP BY` |
| Need row-level data plus grouped context | Window function |

## Production Workflow

When choosing between a subquery and a window function:

1. **Define the required result shape.**  
   Determine whether the result should preserve individual rows or collapse them into groups.

2. **Identify the relational operation.**  
   Existence and membership usually suggest subqueries; ranking and row-to-group analytics usually suggest window functions.

3. **Write the clearest set-based query.**  
   Prefer SQL that directly expresses the business requirement.

4. **Inspect the generated SQL.**  
   This is particularly important when using Django or another ORM.

5. **Inspect the execution plan.**

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ...
```

6. **Test with production-like data volumes.**  
   Small development datasets can hide sorting, memory, cardinality, and IO problems.

7. **Add or adjust indexes based on evidence.**  
   Validate that the resulting plan and workload actually improve.

8. **Measure application-level impact.**  
   Consider database latency, network transfer, serialization cost, and API response size—not only SQL execution time.

## Key Takeaways

- **Subqueries are best suited to scalar lookups, existence tests, membership checks, and independent query composition; window functions excel at row-level analytics.**
- **Window functions preserve individual rows while calculating aggregates, rankings, or sequential relationships across related rows.**
- **For ranking, top-N-per-group, running totals, and previous/next-row analysis, window functions are usually the most direct SQL abstraction.**
- **Window functions cannot normally be filtered in the same query block's `WHERE`; use a CTE or derived table to create another query level.**
- **Choose based on semantics first and execution plans second—neither subqueries nor window functions are universally faster.**