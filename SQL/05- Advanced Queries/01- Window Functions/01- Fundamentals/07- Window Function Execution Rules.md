# 07- Window Function Execution Rules

## Overview

Window functions extend a query with calculations over a set of related rows while preserving the individual rows in the result.

The important distinction is that a window function does **not** collapse rows like `GROUP BY`. Instead, the database computes a value for each row based on a defined window.

```sql
function_name(...) OVER (
    PARTITION BY ...
    ORDER BY ...
    frame
)
```

Understanding execution rules is essential because window functions interact with:

- `WHERE`
- `GROUP BY`
- `HAVING`
- `SELECT`
- `ORDER BY`
- Window partitions
- Window ordering
- Window frames
- Joins and row cardinality

A useful logical model is:

```mermaid
flowchart LR
    A["FROM / JOIN"] --> B["WHERE"]
    B --> C["GROUP BY"]
    C --> D["HAVING"]
    D --> E["Window Functions"]
    E --> F["SELECT"]
    F --> G["Final ORDER BY"]
    G --> H["LIMIT / OFFSET"]
```

This is a **logical processing model**, not a promise about the physical execution plan. A database optimizer may reorder or combine physical operations when the resulting query semantics remain correct.

## Window Functions Preserve Rows

Consider:

```sql
SELECT
    department_id,
    employee_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS department_avg
FROM employees;
```

If there are 1,000 employees, the query still returns up to 1,000 employee rows.

Each row receives the aggregate value for its department:

```text
employee_id | department_id | salary | department_avg
------------+---------------+--------+---------------
101         | 10            | 80000  | 95000
102         | 10            | 110000 | 95000
103         | 10            | 95000  | 95000
```

Compare this with:

```sql
SELECT
    department_id,
    AVG(salary) AS department_avg
FROM employees
GROUP BY department_id;
```

This produces one row per department.

| Operation | Rows preserved? | Typical purpose |
|---|---:|---|
| `GROUP BY` | No | Collapse rows into groups |
| Window function | Yes | Calculate across related rows while retaining detail |

This distinction drives most window-function use cases.

## The Logical Window Execution Model

For a query such as:

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
WHERE active = true;
```

a useful conceptual sequence is:

1. Read rows from `employees`.
2. Apply `WHERE active = true`.
3. Divide the remaining rows into `department_id` partitions.
4. Order each partition by `salary DESC`.
5. Calculate `RANK()`.
6. Produce the selected columns.
7. Apply any final query-level `ORDER BY`.

The critical implication is:

> **A window function operates on the row set available at its query level.**

Therefore, filtering before the window function changes the population over which the window is calculated.

## `WHERE` and Window Functions

A common mistake is attempting to use a window function directly in `WHERE`:

```sql
SELECT
    employee_id,
    salary,
    ROW_NUMBER() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS row_number
FROM employees
WHERE row_number <= 3;
```

This does not work because the `WHERE` clause cannot directly reference a window-function result calculated at the same query level.

Use a subquery or CTE:

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC, employee_id
        ) AS row_number
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary
FROM ranked_employees
WHERE row_number <= 3;
```

The inner query first produces the window value. The outer query can then filter it.

This pattern is fundamental for:

- Top-N per group.
- Latest row per entity.
- Deduplication.
- Ranking-based filtering.

## `WHERE` Changes the Window Population

Consider:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS department_avg
FROM employees
WHERE active = true;
```

The average is calculated only across active employees.

If the business requirement is:

> Compare each active employee against the average salary of **all employees**

then this query is incorrect.

The filtering must happen after the window calculation:

```sql
WITH employee_metrics AS (
    SELECT
        employee_id,
        department_id,
        salary,
        active,
        AVG(salary) OVER (
            PARTITION BY department_id
        ) AS department_avg
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary,
    department_avg
FROM employee_metrics
WHERE active = true;
```

This is one of the most important execution-rule concepts:

> **Moving a filter across a window-function boundary can change the result.**

## `GROUP BY` and Window Functions

Window functions can operate on the result of grouping.

For example:

```sql
SELECT
    department_id,
    COUNT(*) AS employee_count,
    SUM(COUNT(*)) OVER () AS total_employee_count
FROM employees
GROUP BY department_id;
```

Conceptually:

```text
employees
    ↓
GROUP BY department_id
    ↓
one row per department
    ↓
COUNT(*)
    ↓
window function over grouped rows
```

If there are five departments, the window function sees approximately five grouped rows, not every employee row.

This makes window functions useful for comparing grouped metrics:

```sql
SELECT
    department_id,
    SUM(revenue) AS department_revenue,
    SUM(SUM(revenue)) OVER () AS total_revenue
FROM orders
GROUP BY department_id;
```

Each department row can therefore contain both its own revenue and the overall total.

## `HAVING` and Window Functions

`HAVING` filters grouped results before the window calculation.

```sql
SELECT
    department_id,
    SUM(revenue) AS department_revenue,
    RANK() OVER (
        ORDER BY SUM(revenue) DESC
    ) AS revenue_rank
FROM orders
GROUP BY department_id
HAVING SUM(revenue) > 100000;
```

The conceptual sequence is:

```text
orders
  ↓
GROUP BY department_id
  ↓
SUM(revenue)
  ↓
HAVING SUM(revenue) > 100000
  ↓
RANK() over remaining departments
```

Therefore, departments excluded by `HAVING` do not participate in the ranking.

If the requirement is to rank **all** departments and only display departments above a threshold, use another query level:

```sql
WITH department_metrics AS (
    SELECT
        department_id,
        SUM(revenue) AS department_revenue
    FROM orders
    GROUP BY department_id
),
ranked_departments AS (
    SELECT
        department_id,
        department_revenue,
        RANK() OVER (
            ORDER BY department_revenue DESC
        ) AS revenue_rank
    FROM department_metrics
)
SELECT
    department_id,
    department_revenue,
    revenue_rank
FROM ranked_departments
WHERE department_revenue > 100000;
```

The placement of the filter determines the ranking population.

## `ORDER BY` Inside `OVER`

The `ORDER BY` inside a window definition controls the sequence used by the window function.

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
)
```

It does **not** guarantee the final result order.

The final output requires a separate query-level clause:

```sql
SELECT
    ...
FROM ...
ORDER BY created_at, order_id;
```

The two clauses have different responsibilities.

| Clause | Responsibility |
|---|---|
| `OVER (... ORDER BY ...)` | Defines the sequence used by the window calculation |
| Query-level `ORDER BY` | Defines final result presentation |

For deterministic results, use stable tie-breakers when row position matters:

```sql
ORDER BY created_at DESC, order_id DESC
```

## Window Frames

For frame-sensitive functions, there is another execution layer to understand.

Consider:

```sql
SELECT
    account_id,
    transaction_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY account_id
        ORDER BY created_at, transaction_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_balance
FROM transactions;
```

Conceptually:

```text
1. Determine account partition
2. Order transactions
3. Identify current row
4. Determine its frame
5. Apply SUM() to that frame
6. Return the result
```

For a running total, the frame expands from the first row to the current row.

```text
Row 1 → [1]
Row 2 → [1, 2]
Row 3 → [1, 2, 3]
Row 4 → [1, 2, 3, 4]
```

`ORDER BY` therefore affects not only ranking and navigation functions but also the meaning of `PRECEDING`, `FOLLOWING`, and related frame boundaries.

## `ROW_NUMBER()` Execution

Consider:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, order_id DESC
    ) AS row_number
FROM orders;
```

For each customer:

```text
Partition
   ↓
Sort by created_at DESC, order_id DESC
   ↓
Assign sequential numbers
   ↓
Return original order rows + row_number
```

The number is assigned according to the window's logical ordering, not according to how rows happen to be stored.

## `RANK()` and Peer Rows

`RANK()` treats rows with equal ordering values as peers.

```sql
SELECT
    employee_id,
    salary,
    RANK() OVER (
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees;
```

If salaries are:

```text
200000
150000
150000
100000
```

the ranks are:

```text
1
2
2
4
```

If exact row ordering is required, use a unique tie-breaker with `ROW_NUMBER()`:

```sql
ROW_NUMBER() OVER (
    ORDER BY salary DESC, employee_id
)
```

Do not add a tie-breaker simply because it is available. For `RANK()` and `DENSE_RANK()`, peer semantics are often intentional.

## Window Functions Over Aggregated Results

Window functions become especially powerful when combined with grouped aggregates.

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_revenue,
    SUM(SUM(amount)) OVER () AS total_revenue,
    SUM(amount) / SUM(SUM(amount)) OVER () AS revenue_share
FROM orders
GROUP BY customer_id;
```

Conceptually:

```text
orders
   ↓
GROUP BY customer_id
   ↓
customer-level revenue
   ↓
window calculations over customer-level rows
   ↓
customer revenue share
```

This avoids joining an aggregate result back to itself in many cases.

For monetary calculations, ensure the data type and rounding behavior are appropriate for the database and business requirements.

## Multiple Window Functions

A single query can contain several windows:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,

    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
    ) AS sequence_number,

    LAG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
    ) AS previous_amount,

    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total

FROM orders;
```

All three functions use the same logical partition and ordering but perform different calculations.

A named window can make repeated definitions easier to maintain:

```sql
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    ROW_NUMBER() OVER w AS sequence_number,
    LAG(amount) OVER w AS previous_amount
FROM orders
WINDOW w AS (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
);
```

Named windows improve readability when the semantics genuinely match.

## Window Functions and Query Nesting

A query boundary is often used to control which rows a later window function sees.

For example:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(amount) AS total_spend
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_spend,
    RANK() OVER (
        ORDER BY total_spend DESC
    ) AS customer_rank
FROM customer_totals;
```

The window function operates over customer-level rows.

You can introduce another boundary to change the population again:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(amount) AS total_spend
    FROM orders
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        total_spend,
        RANK() OVER (
            ORDER BY total_spend DESC
        ) AS customer_rank
    FROM customer_totals
)
SELECT
    customer_id,
    total_spend,
    customer_rank
FROM ranked_customers
WHERE total_spend >= 1000;
```

The ranking is calculated across all customers before the final filter.

This is why CTEs and derived tables are frequently paired with window functions: they create explicit query-level boundaries.

## Window Functions and Joins

Joins affect the row set before the window function operates.

Suppose:

```sql
SELECT
    c.customer_id,
    o.order_id,
    o.amount,
    ROW_NUMBER() OVER (
        PARTITION BY c.customer_id
        ORDER BY o.created_at, o.order_id
    ) AS order_number
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.customer_id;
```

The window sees the rows produced by the join.

If another join accidentally creates multiple rows per order:

```text
customer
   ↓
orders
   ↓
order_items
   ↓
multiple rows per order
   ↓
window function
```

then `ROW_NUMBER()` ranks those duplicated join rows, not the logical orders.

This is a major production pitfall.

Before adding a window function, verify the **row grain** of the input relation.

## Query Grain Is More Important Than Syntax

A senior-level approach is to ask:

> "What does one row represent at the point where the window function runs?"

Examples:

| Query stage | One row represents |
|---|---|
| Raw `orders` | One order |
| Joined `orders + order_items` | Potentially one order-item |
| `GROUP BY customer_id` | One customer |
| Window over customer totals | One customer |
| Outer query after filtering | Selected customer rows |

Window functions operate according to the actual relation at their query level, not according to what the developer intended the rows to represent.

## Physical Execution and Performance

The logical processing order should not be confused with the physical execution plan.

A database optimizer may:

- Push predicates downward.
- Eliminate unnecessary operations.
- Reuse sorting work.
- Choose an index.
- Use incremental or partial strategies where supported.
- Materialize or inline intermediate results depending on the database and query.

For PostgreSQL, inspect actual plans for performance-sensitive queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    order_id,
    created_at,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, order_id DESC
    ) AS row_number
FROM orders;
```

Look for:

- Large sorts.
- Temporary disk usage.
- High row counts.
- Expensive joins before the window.
- Cardinality misestimates.
- Memory pressure.
- Repeated sorting for multiple incompatible windows.

Do not optimize based solely on the logical execution model.

## Filtering Before vs After a Window

The following two queries are semantically different.

### Filter Before Window

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
WHERE active = true;
```

The ranking considers active employees only.

### Filter After Window

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        active,
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
WHERE active = true;
```

The ranking considers all employees, but only active employees are returned.

This distinction is frequently tested in interviews and can cause subtle production bugs in reporting systems.

## Final `ORDER BY` Does Not Affect Window Results

Consider:

```sql
SELECT
    employee_id,
    salary,
    ROW_NUMBER() OVER (
        ORDER BY salary DESC
    ) AS salary_position
FROM employees
ORDER BY salary ASC;
```

The window assigns position `1` to the highest salary.

The final query then displays the lowest salary first.

Example:

```text
employee_id | salary | salary_position
------------+--------+----------------
104         | 50000  | 4
103         | 70000  | 3
102         | 90000  | 2
101         | 120000 | 1
```

The result looks reversed, but it is correct.

## `LIMIT` and Window Functions

`LIMIT` is applied after the window calculation at the same query level.

```sql
SELECT
    employee_id,
    salary,
    ROW_NUMBER() OVER (
        ORDER BY salary DESC
    ) AS row_number
FROM employees
LIMIT 10;
```

Conceptually, the window numbering is established before the final result is limited.

For top-N-per-group queries, `LIMIT` cannot replace the window filtering requirement:

```sql
ROW_NUMBER() OVER (
    PARTITION BY department_id
    ORDER BY salary DESC
)
```

because `LIMIT 3` means three rows globally, not three rows per department.

## Common Execution Mistakes

### Filtering a Window Result in `WHERE`

Incorrect:

```sql
WHERE row_number <= 3
```

at the same query level.

Use a CTE or derived table.

### Filtering Too Early

If the window should consider all rows, do not put the filter before the window calculation.

Move the filter to an outer query level.

### Ignoring Join Multiplication

A window function cannot know that duplicated rows are accidental.

Validate row cardinality before ranking or aggregating.

### Assuming Physical Row Order

This is unsafe:

```sql
LAG(status) OVER (PARTITION BY user_id)
```

when "previous" has business meaning.

Use:

```sql
LAG(status) OVER (
    PARTITION BY user_id
    ORDER BY occurred_at, event_id
)
```

### Confusing Logical Order With Physical Execution

The logical model explains semantics. It does not dictate the exact PostgreSQL execution plan.

Use `EXPLAIN (ANALYZE, BUFFERS)` when performance matters.

### Assuming CTEs Always Materialize

A CTE is a query-expression boundary, but its physical treatment depends on the database and query.

In PostgreSQL, modern versions can inline eligible CTEs rather than always materializing them. Use `MATERIALIZED` or `NOT MATERIALIZED` deliberately when the behavior matters.

## Production Design Checklist

Before shipping a window-function query:

- [ ] What does one input row represent?
- [ ] Is the window population correct?
- [ ] Does filtering happen before or after the window intentionally?
- [ ] Is `PARTITION BY` required?
- [ ] Is the window `ORDER BY` deterministic?
- [ ] Are ties intentional?
- [ ] Is the window frame correct for the calculation?
- [ ] Could a join multiply rows?
- [ ] Is a query boundary required to filter or reuse the window result?
- [ ] Is final result ordering separately defined?
- [ ] Has the query been tested with realistic data volume?
- [ ] Has the physical execution plan been inspected for expensive sorts and joins?

## Interview Traps

| Trap | Correct answer |
|---|---|
| Can a window-function alias normally be used in `WHERE` at the same query level? | No. Use another query level such as a CTE or derived table. |
| Does a window function reduce the number of rows? | No. It normally preserves the rows of its input relation. |
| Does `GROUP BY` happen before a window function logically? | Yes. Window functions can operate over grouped results. |
| Does `WHERE` affect the rows available to the window? | Yes. A pre-window filter changes the window population. |
| Does final `ORDER BY` determine `ROW_NUMBER()`? | No. The window's own `ORDER BY` does. |
| Does `LIMIT 3` produce three rows per partition? | No. It limits the query result globally. |
| Does the logical execution model describe the physical PostgreSQL plan exactly? | No. The optimizer can transform the physical execution. |
| Can a join change a window result? | Yes. Window functions operate over the rows produced by the preceding query stages. |

## Key Takeaways

- **Window functions preserve the rows of their input relation; they calculate values across related rows rather than collapsing them like `GROUP BY`.**
- **`WHERE`, `GROUP BY`, and `HAVING` determine the row population available to the window, so filter placement can change the result.**
- **Use a CTE or derived table when a window result must be filtered or consumed by another query stage.**
- **`PARTITION BY`, window `ORDER BY`, and the window frame define the calculation's semantics; query-level `ORDER BY` only controls final presentation.**
- **Logical execution rules explain query semantics, while `EXPLAIN (ANALYZE, BUFFERS)` is required to understand the actual physical performance.**