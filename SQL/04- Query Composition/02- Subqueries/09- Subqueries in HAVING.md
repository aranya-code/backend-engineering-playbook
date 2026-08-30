# 09- Subqueries in HAVING

## Overview

The `HAVING` clause filters groups after `GROUP BY` and aggregation have been applied. A subquery inside `HAVING` allows the threshold or comparison used to decide whether a group qualifies to be derived dynamically from another query.

This is useful when grouped results must be compared against:

- A global aggregate.
- Another group's aggregate.
- A scalar threshold calculated from the database.
- A set of values from another relation.
- A related condition expressed through `EXISTS` or `NOT EXISTS`.

For backend systems, common examples include:

- Finding departments whose average salary exceeds the company-wide average.
- Returning customers whose spending exceeds the average customer spending.
- Finding product categories with more orders than a threshold derived from another dataset.
- Selecting tenants whose activity exceeds a system-wide baseline.
- Filtering grouped reports against dynamically calculated business metrics.

The important distinction is:

```text
WHERE  → filters rows before grouping
GROUP BY → creates groups
HAVING → filters groups after aggregation
```

A subquery inside `HAVING` is therefore particularly useful when the **group-level result must be compared against another derived value or set**.

## Query Processing Context

A simplified logical processing order is:

```mermaid
flowchart LR
    A[FROM / JOIN] --> B[WHERE]
    B --> C[GROUP BY]
    C --> D[Aggregate Functions]
    D --> E[HAVING]
    E --> F[SELECT]
    F --> G[ORDER BY]
    G --> H[LIMIT]
```

For example:

```sql
SELECT
    department_id,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department_id
HAVING AVG(salary) > (
    SELECT AVG(salary)
    FROM employees
);
```

The inner query calculates the company-wide average salary.

The outer query:

1. Reads employees.
2. Groups them by department.
3. Calculates each department's average salary.
4. Compares each department average with the scalar subquery result.
5. Keeps only qualifying departments.

The optimizer is free to execute this differently from the logical order shown above.

## Basic Syntax

The general pattern is:

```sql
SELECT
    grouping_column,
    aggregate_function(value) AS aggregate_value
FROM table_name
GROUP BY grouping_column
HAVING aggregate_function(value) operator (
    SELECT ...
);
```

A practical example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS customer_spend
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(total_amount)
    FROM orders
);
```

This compares each customer's total spending against the **average individual order amount**, not average customer spending.

That distinction matters.

If the business requirement is:

> Find customers whose total spending exceeds the average spending per customer.

then the subquery must also aggregate by customer:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS customer_spend
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(customer_spend)
    FROM (
        SELECT
            customer_id,
            SUM(total_amount) AS customer_spend
        FROM orders
        GROUP BY customer_id
    ) AS customer_totals
);
```

The second query demonstrates an important production principle:

> The subquery must calculate the metric at the same semantic level as the comparison requires.

## Scalar Subqueries in `HAVING`

The most common pattern is comparing a group aggregate with a scalar value.

Example:

```sql
SELECT
    department_id,
    AVG(salary) AS department_avg_salary
FROM employees
GROUP BY department_id
HAVING AVG(salary) > (
    SELECT AVG(salary)
    FROM employees
);
```

The subquery returns one value:

```text
company-wide average salary
```

Each department's aggregate is compared against that value.

### When to Use

Use this pattern when a group must be compared with a global baseline.

Typical examples:

```text
department average > company average
category revenue > global average
tenant activity > platform average
region sales > global sales threshold
```

### Cardinality Requirement

A scalar subquery must produce at most one row.

This is valid:

```sql
SELECT AVG(salary)
FROM employees;
```

This is not suitable as a scalar expression:

```sql
SELECT salary
FROM employees;
```

If multiple rows are returned, the database can raise a cardinality violation.

## Comparing Group Aggregates with Global Aggregates

A useful production pattern is comparing grouped metrics against a global aggregate.

For example:

```sql
SELECT
    category_id,
    SUM(amount) AS category_revenue
FROM orders
WHERE status = 'paid'
GROUP BY category_id
HAVING SUM(amount) > (
    SELECT AVG(category_revenue)
    FROM (
        SELECT
            category_id,
            SUM(amount) AS category_revenue
        FROM orders
        WHERE status = 'paid'
        GROUP BY category_id
    ) AS category_totals
);
```

The two aggregation levels are different:

```text
Individual orders
       │
       ▼
Revenue per category
       │
       ▼
Average revenue across categories
       │
       ▼
Compare each category against that average
```

This is different from:

```sql
HAVING SUM(amount) > (
    SELECT AVG(amount)
    FROM orders
);
```

because the latter compares category revenue against the average **order amount**.

Always identify the grain of each metric before writing the query.

## `HAVING` with `EXISTS`

`EXISTS` can also be used inside `HAVING` when group qualification depends on the existence of another relation.

For example, suppose a reporting query groups orders by customer and should only return customers that have an active subscription:

```sql
SELECT
    o.customer_id,
    COUNT(*) AS order_count
FROM orders AS o
GROUP BY o.customer_id
HAVING EXISTS (
    SELECT 1
    FROM subscriptions AS s
    WHERE s.customer_id = o.customer_id
      AND s.status = 'active'
);
```

The grouped result is retained only when a matching subscription exists.

However, if the subscription relationship is naturally part of the row-selection stage, filtering it in `WHERE` before grouping may be clearer and more efficient:

```sql
SELECT
    o.customer_id,
    COUNT(*) AS order_count
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM subscriptions AS s
    WHERE s.customer_id = o.customer_id
      AND s.status = 'active'
)
GROUP BY o.customer_id;
```

These forms can have different semantics if the existence condition is intended to apply before versus after aggregation.

## `HAVING` with `IN`

A multi-row subquery can be used with `IN` when the aggregate or grouping value must belong to a derived set.

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING customer_id IN (
    SELECT customer_id
    FROM customer_segments
    WHERE segment = 'enterprise'
);
```

This can work, but if the requirement is simply:

> Only aggregate orders belonging to enterprise customers.

then pushing the predicate into `WHERE` is often more natural:

```sql
SELECT
    o.customer_id,
    COUNT(*) AS order_count
FROM orders AS o
WHERE o.customer_id IN (
    SELECT customer_id
    FROM customer_segments
    WHERE segment = 'enterprise'
)
GROUP BY o.customer_id;
```

The distinction is important because filtering before aggregation can reduce the amount of data that must be grouped.

## `WHERE` vs `HAVING` with Subqueries

Consider:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE customer_id IN (
    SELECT customer_id
    FROM customers
    WHERE country = 'IN'
)
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

There are two independent requirements:

```text
WHERE:
Only Indian customers' orders participate in aggregation.

HAVING:
Only customers with at least 10 qualifying orders remain.
```

This separation is generally preferable to placing everything in `HAVING`.

| Requirement | Preferred location |
|---|---|
| Filter individual source rows | `WHERE` |
| Filter based on aggregate result | `HAVING` |
| Filter groups based on a derived aggregate | `HAVING` |
| Filter source rows using existence | `WHERE EXISTS` |
| Filter groups using an aggregate existence rule | `HAVING EXISTS` |
| Reduce rows before expensive grouping | `WHERE` when semantics allow |

A common performance optimization is to push predicates into `WHERE` whenever doing so preserves the intended semantics.

## Correlated Subqueries in `HAVING`

A correlated subquery can reference a grouping column from the outer query.

Example:

```sql
SELECT
    department_id,
    AVG(salary) AS department_avg_salary
FROM employees AS e
GROUP BY department_id
HAVING AVG(salary) > (
    SELECT AVG(e2.salary)
    FROM employees AS e2
    WHERE e2.location_id = e.location_id
);
```

This attempts to compare a department's average salary against the average salary for its location.

The correlation is:

```sql
e.location_id
```

The exact legality of references to non-grouped outer columns depends on the SQL dialect and query shape. When correlated expressions participate in grouped queries, make the grouping relationship explicit and validate the query against the target database.

A clearer formulation may first derive the required grouping grain:

```sql
SELECT
    department_id,
    location_id,
    AVG(salary) AS department_avg_salary
FROM employees
GROUP BY department_id, location_id;
```

Then compare that derived result against location-level aggregates.

## A More Maintainable Pattern: Derived Aggregates

Complex `HAVING` subqueries can become difficult to reason about.

Suppose the requirement is:

> Find categories whose revenue exceeds the average revenue of all categories.

A layered query makes the aggregation levels explicit:

```sql
SELECT
    category_id,
    category_revenue
FROM (
    SELECT
        category_id,
        SUM(amount) AS category_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY category_id
) AS category_totals
WHERE category_revenue > (
    SELECT AVG(category_revenue)
    FROM (
        SELECT
            category_id,
            SUM(amount) AS category_revenue
        FROM orders
        WHERE status = 'paid'
        GROUP BY category_id
    ) AS totals
);
```

This is verbose because the category-level result is calculated twice.

A Common Table Expression can improve maintainability:

```sql
WITH category_totals AS (
    SELECT
        category_id,
        SUM(amount) AS category_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY category_id
)
SELECT
    category_id,
    category_revenue
FROM category_totals
WHERE category_revenue > (
    SELECT AVG(category_revenue)
    FROM category_totals
);
```

CTE optimization behavior varies by database version and query. Do not assume a CTE is always materialized or always inlined; inspect the execution plan for the target database.

## Window Functions as an Alternative

Some `HAVING` subqueries are better represented using window functions.

For example, the goal:

> Return categories whose revenue exceeds the average category revenue.

can be expressed as:

```sql
WITH category_totals AS (
    SELECT
        category_id,
        SUM(amount) AS category_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY category_id
),
scored AS (
    SELECT
        category_id,
        category_revenue,
        AVG(category_revenue) OVER () AS average_category_revenue
    FROM category_totals
)
SELECT
    category_id,
    category_revenue
FROM scored
WHERE category_revenue > average_category_revenue;
```

This makes the data flow explicit:

```text
orders
  │
  ▼
category_totals
  │
  ├── category_revenue
  │
  └── average(category_revenue) OVER ()
          │
          ▼
       comparison
```

Window functions are particularly useful when the query needs to retain both:

- The group's aggregate.
- A broader aggregate used for comparison.

## Common Production Pattern: Minimum Group Size

Sometimes a group must satisfy multiple conditions.

For example:

> Return customers with at least five paid orders and spending above the average customer spend.

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS total_spend
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)
SELECT
    customer_id,
    order_count,
    total_spend
FROM customer_totals
WHERE order_count >= 5
  AND total_spend > (
      SELECT AVG(total_spend)
      FROM customer_totals
  );
```

This is usually easier to maintain than deeply nesting aggregation directly inside `HAVING`.

The business conditions are also visible:

```text
order_count >= 5
AND
total_spend > average customer spend
```

## Performance Considerations

A subquery inside `HAVING` can be inexpensive or expensive depending on the amount of data and whether the database can optimize the expression.

Important factors include:

### Reduce Rows Before Grouping

If a condition applies to source rows, prefer:

```sql
WHERE
```

over:

```sql
HAVING
```

when semantics permit.

For example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total_amount) > 10000;
```

is generally preferable to aggregating every order and then attempting to remove unpaid orders later.

### Indexes

Indexes can help the database efficiently locate source rows used by the query.

For example:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

may be useful for workloads frequently filtering by `status` and grouping or joining by `customer_id`.

However, index usefulness depends on:

- Predicate selectivity.
- Table size.
- Data distribution.
- Query frequency.
- Write volume.
- Existing indexes.
- Database optimizer behavior.

Do not blindly create composite indexes based only on column appearance.

### Execution Plans

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_totals AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS total_spend
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)
SELECT
    customer_id,
    order_count,
    total_spend
FROM customer_totals
WHERE order_count >= 5
  AND total_spend > (
      SELECT AVG(total_spend)
      FROM customer_totals
  );
```

Inspect:

- Actual versus estimated rows.
- Scan type.
- Sort operations.
- Hash aggregation.
- Temporary disk usage.
- Buffer reads.
- Execution time.
- Repeated expensive operations.

The SQL text alone cannot tell you the actual cost.

## NULL and Empty-Set Behavior

Aggregates and subqueries interact with SQL's `NULL` semantics.

For example:

```sql
SELECT AVG(total_amount)
FROM orders;
```

returns `NULL` when there are no non-NULL values.

Then:

```sql
HAVING SUM(total_amount) > (
    SELECT AVG(total_amount)
    FROM orders
);
```

may evaluate the comparison as `UNKNOWN` if the scalar subquery returns `NULL`.

If the business rule requires a defined fallback, handle it explicitly:

```sql
HAVING SUM(total_amount) > (
    SELECT COALESCE(AVG(total_amount), 0)
    FROM orders
);
```

Do not use `COALESCE` automatically. The fallback must represent a valid business rule.

## Security Considerations

Subqueries do not remove the need for parameterized queries.

Use parameters:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_spend
FROM orders
WHERE status = :status
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(total_amount)
    FROM orders
    WHERE status = :status
);
```

Do not interpolate user-controlled values into SQL strings.

In multi-tenant applications, apply tenant boundaries consistently:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_spend
FROM orders
WHERE tenant_id = :tenant_id
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(total_amount)
    FROM orders
    WHERE tenant_id = :tenant_id
);
```

Otherwise, the comparison baseline can accidentally include data from other tenants.

This is both a correctness and authorization concern.

## Production Pitfalls

| Pitfall | Problem | Better approach |
|---|---|---|
| Filtering ordinary rows in `HAVING` | More rows may be grouped unnecessarily | Push row-level predicates into `WHERE` |
| Comparing against the wrong aggregate grain | Produces logically incorrect metrics | Define the grain of both sides explicitly |
| Assuming a scalar subquery returns one row | Runtime cardinality errors | Enforce uniqueness or aggregate to one value |
| Ignoring `NULL` aggregate results | Comparisons become `UNKNOWN` | Define explicit `NULL` semantics |
| Assuming subqueries always execute independently | Misunderstands optimizer behavior | Inspect the actual execution plan |
| Repeating complex aggregation | Expensive and difficult to maintain | Consider CTEs or window functions |
| Using `DISTINCT` to repair incorrect grouping | Masks a modeling/query error | Fix the grouping or join semantics |
| Ignoring data growth | Query degrades as tables grow | Benchmark with representative production volumes |
| Missing tenant filters in subqueries | Cross-tenant metrics or data leakage | Apply authorization scope consistently |
| Optimizing without `EXPLAIN ANALYZE` | Tuning based on assumptions | Measure actual execution behavior |

## Django and Application-Level Considerations

ORMs such as Django can express many subquery patterns using `Subquery`, `OuterRef`, `Exists`, and aggregation APIs.

For example, conceptually:

```python
from django.db.models import Exists, OuterRef

paid_orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
    status="paid",
)

customers = Customer.objects.annotate(
    has_paid_order=Exists(paid_orders),
).filter(
    has_paid_order=True,
)
```

The ORM ultimately generates SQL. Production optimization therefore remains a database concern.

For complex analytical queries:

- Inspect the generated SQL.
- Use database execution plans.
- Avoid blindly assuming ORM expressions are optimal.
- Prefer database-side aggregation over loading large datasets into Python.
- Add indexes based on measured query patterns.
- Test queries against production-like data volumes.

## Interview Traps

### Why use `HAVING` instead of `WHERE`?

`WHERE` filters rows before grouping. `HAVING` filters groups after aggregation.

```sql
WHERE status = 'paid'
```

filters source rows.

```sql
HAVING COUNT(*) >= 10
```

filters grouped results.

### Can `HAVING` contain a subquery?

Yes. The subquery can provide a scalar threshold, set, or existence condition used to decide whether a group qualifies.

### Does the subquery execute after `GROUP BY`?

Not necessarily. That is the logical interpretation of the query, not a guarantee about the physical execution plan.

### Why might a `WHERE` predicate be better than the same predicate in `HAVING`?

A `WHERE` predicate can eliminate rows before grouping, reducing the amount of data that must be aggregated.

### What is a common logical error when comparing aggregates?

Comparing metrics with different grains.

For example:

```text
category revenue
```

must not accidentally be compared against:

```text
average individual order amount
```

when the requirement is actually:

```text
average revenue per category
```

### When should a window function be considered?

When the query needs to compare each grouped metric with a broader aggregate while retaining both values, such as comparing category revenue with average category revenue.

## Key Takeaways

- **`HAVING` filters groups after aggregation; subqueries inside it are useful for dynamic group-level comparisons and existence conditions.**
- **Always compare metrics at the correct aggregation grain; confusing order-level, customer-level, and category-level aggregates is a common source of silent business-logic errors.**
- **Push row-level predicates into `WHERE` when possible so unnecessary rows are eliminated before grouping.**
- **For complex aggregate comparisons, CTEs and window functions can improve clarity and sometimes performance; validate the choice with the actual execution plan.**
- **Production queries must account for cardinality, `NULL` behavior, tenant boundaries, indexes, data growth, and measured execution cost.**