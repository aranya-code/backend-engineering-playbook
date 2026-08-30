# 16- CTE vs Subquery

## Overview

Common Table Expressions (CTEs) and subqueries both allow a SQL statement to build intermediate query results. In many cases they can express the same logic, but they differ significantly in **readability, reuse within a statement, recursive capabilities, data-modifying support, and optimizer behavior**.

The important production-level distinction is that a CTE is primarily a **named query-composition mechanism**, while a subquery is an **embedded query expression**. Neither should be assumed to be faster merely because of its syntax.

For example, these queries can express the same logical operation:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.status = 'completed'
);
```

Using a CTE:

```sql
WITH completed_customers AS (
    SELECT DISTINCT
        customer_id
    FROM orders
    WHERE status = 'completed'
)
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN completed_customers AS cc
    ON cc.customer_id = c.id;
```

The right choice depends on the query's structure and the database optimizer, not simply on the number of lines of SQL.

## CTE and Subquery at a Glance

| Concern | CTE | Subquery |
|---|---|---|
| Syntax | `WITH name AS (...)` | Nested `SELECT` |
| Naming | Explicit relation name | Usually anonymous |
| Readability | Strong for multi-stage queries | Strong for localized logic |
| Reuse within statement | Easy | Usually requires duplication or restructuring |
| Recursive queries | Yes, with recursive CTE support | No |
| Multiple stages | Excellent | Can become deeply nested |
| Correlation | Possible through query references | Natural for correlated subqueries |
| Data-modifying workflows | Supported by some databases | More restricted |
| Statement scope | Statement | Enclosing query expression |
| Performance | Database/optimizer dependent | Database/optimizer dependent |

## Basic Equivalence

Consider finding customers who have placed at least one completed order.

### Using a subquery

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

The subquery is tightly coupled to the `customers` row being evaluated.

### Using a CTE

```sql
WITH completed_customers AS (
    SELECT DISTINCT
        customer_id
    FROM orders
    WHERE status = 'completed'
)
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN completed_customers AS cc
    ON cc.customer_id = c.id;
```

The CTE separates the derivation of completed customers from the final customer query.

Both can be valid production queries.

## When a Subquery Is the Better Choice

A subquery is usually preferable when the intermediate logic is:

- Used only once.
- Small and local to one predicate.
- Naturally expressed as `EXISTS`, `IN`, or a scalar expression.
- Closely coupled to the outer row.
- Easier to understand inline than as a separate query stage.

For example:

```sql
SELECT
    p.id,
    p.name
FROM products AS p
WHERE p.price > (
    SELECT AVG(price)
    FROM products
);
```

Creating a CTE here may add structure without providing much benefit:

```sql
WITH average_price AS (
    SELECT AVG(price) AS value
    FROM products
)
SELECT
    p.id,
    p.name
FROM products AS p
CROSS JOIN average_price AS ap
WHERE p.price > ap.value;
```

The CTE version is valid, but the subquery is more direct.

## When a CTE Is the Better Choice

A CTE becomes more useful when the query is naturally a sequence of transformations.

For example:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
),
customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM recent_orders
    GROUP BY customer_id
),
high_value_customers AS (
    SELECT
        customer_id,
        revenue
    FROM customer_revenue
    WHERE revenue >= 10000
)
SELECT
    c.id,
    c.email,
    hvc.revenue
FROM customers AS c
JOIN high_value_customers AS hvc
    ON hvc.customer_id = c.id;
```

The stages are explicit:

```text
orders
  │
  ▼
recent_orders
  │
  ▼
customer_revenue
  │
  ▼
high_value_customers
  │
  ▼
final SELECT
```

Writing this entirely as nested subqueries would make the dependency structure harder to read.

## Readability and Query Composition

The biggest practical advantage of a CTE is often **query organization**, not performance.

Compare deeply nested subqueries:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN (
    SELECT
        customer_id
    FROM (
        SELECT
            customer_id,
            SUM(total_amount) AS revenue
        FROM orders
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
        GROUP BY customer_id
    ) AS revenue_by_customer
    WHERE revenue >= 10000
) AS high_value_customers
    ON high_value_customers.customer_id = c.id;
```

With CTEs:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
),
revenue_by_customer AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM recent_orders
    GROUP BY customer_id
),
high_value_customers AS (
    SELECT
        customer_id
    FROM revenue_by_customer
    WHERE revenue >= 10000
)
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN high_value_customers AS hvc
    ON hvc.customer_id = c.id;
```

The second version makes the data flow easier to inspect and modify.

## Reusing an Intermediate Result

A CTE can be referenced multiple times within the same statement.

```sql
WITH customer_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM customer_orders
GROUP BY customer_id

UNION ALL

SELECT
    customer_id,
    COUNT(*)::numeric AS order_count
FROM customer_orders
GROUP BY customer_id;
```

A simple subquery generally does not provide the same named, reusable structure.

You could repeat the subquery:

```sql
SELECT ...
FROM (
    SELECT ...
) AS customer_orders
...
```

but once the same intermediate relation is needed by multiple branches, the CTE often communicates intent more clearly.

## Correlated Subqueries

Subqueries are particularly natural when the inner query depends on the current row of the outer query.

For example:

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

The inner query references:

```sql
c.id
```

from the outer query.

This is a correlated subquery.

A CTE can precompute the relevant customer IDs:

```sql
WITH completed_customers AS (
    SELECT DISTINCT
        customer_id
    FROM orders
    WHERE status = 'completed'
)
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN completed_customers AS cc
    ON cc.customer_id = c.id;
```

Whether this is better depends on the query's intent and execution plan.

For simple existence checks, `EXISTS` is often the clearest expression of the requirement.

## Scalar Subqueries

Scalar subqueries are useful when a query needs one value.

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

A scalar subquery is often preferable when the intermediate result is:

- Used once.
- Conceptually one value.
- Closely related to the predicate or expression.

A CTE is more appropriate when the derived result represents a meaningful relation used as a distinct query stage.

## Derived Tables vs CTEs

A subquery in the `FROM` clause is commonly called a **derived table**.

```sql
SELECT
    customer_id,
    revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
) AS revenue_by_customer
WHERE revenue >= 10000;
```

The equivalent CTE is:

```sql
WITH revenue_by_customer AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM revenue_by_customer
WHERE revenue >= 10000;
```

These often have equivalent logical intent.

The CTE version gives the intermediate relation a name before the final query begins, which is especially useful when several transformations follow.

## CTEs and Window Functions

CTEs are particularly useful when a window function produces a result that must then be filtered.

For example:

```sql
WITH ranked_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC
        ) AS order_rank
    FROM orders
)
SELECT
    id,
    customer_id,
    total_amount
FROM ranked_orders
WHERE order_rank = 1;
```

The CTE creates a clean boundary between:

1. Calculating the window function.
2. Filtering on its result.

Without a CTE, the query often requires another derived table:

```sql
SELECT
    id,
    customer_id,
    total_amount
FROM (
    SELECT
        id,
        customer_id,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC
        ) AS order_rank
    FROM orders
) AS ranked_orders
WHERE order_rank = 1;
```

Both are valid. The CTE is often easier to extend if additional stages are required.

## CTEs and Aggregations

CTEs work well when aggregation produces a reusable intermediate relation.

```sql
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
    month,
    revenue,
    revenue - LAG(revenue) OVER (
        ORDER BY month
    ) AS revenue_change
FROM monthly_revenue
ORDER BY month;
```

The first stage calculates monthly revenue. The outer query performs a window calculation over that aggregated result.

This separation makes the logical data flow explicit.

## Performance: CTE vs Subquery

There is no universal rule that:

> CTEs are faster than subqueries.

There is also no universal rule that:

> Subqueries are faster than CTEs.

The optimizer may transform logically equivalent queries into similar execution plans.

For PostgreSQL, inspect the actual plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM recent_orders
GROUP BY customer_id;
```

Compare it with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    SUM(total_amount)
FROM (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
) AS recent_orders
GROUP BY customer_id;
```

Compare:

- Actual execution time.
- Rows processed.
- Join strategy.
- Scan strategy.
- Sort operations.
- Memory usage.
- Buffer reads.
- Temporary file usage.
- Parallel execution.

Do not optimize based solely on SQL syntax.

## CTE Materialization and Subquery Optimization

One important reason performance discussions become confusing is that **logical query structure and physical execution are different things**.

Depending on the database and query, an optimizer may:

- Inline a CTE.
- Push predicates into an intermediate relation.
- Reorder joins.
- Eliminate unnecessary intermediate work.
- Materialize an intermediate result.
- Transform a subquery into a semi-join or anti-join.

PostgreSQL, for example, supports explicit CTE materialization controls:

```sql
WITH recent_orders AS MATERIALIZED (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT *
FROM recent_orders;
```

Or:

```sql
WITH recent_orders AS NOT MATERIALIZED (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT *
FROM recent_orders;
```

These are advanced optimization controls and should be used only when execution-plan evidence supports them.

## Recursive Queries

Recursive traversal is a major capability where CTEs are clearly more appropriate.

For an employee hierarchy:

```sql
WITH RECURSIVE employee_tree AS (
    SELECT
        id,
        manager_id,
        name,
        0 AS depth
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    SELECT
        e.id,
        e.manager_id,
        e.name,
        et.depth + 1
    FROM employees AS e
    JOIN employee_tree AS et
        ON e.manager_id = et.id
)
SELECT
    id,
    manager_id,
    name,
    depth
FROM employee_tree
ORDER BY depth, id;
```

A normal subquery cannot recursively reference itself in this manner.

Use recursive CTEs for structures such as:

- Organizational hierarchies.
- Category trees.
- Folder structures.
- Dependency graphs.
- Graph traversal.
- Parent-child relationships.

## Data-Modifying Statements

Some databases, notably PostgreSQL, allow data-modifying statements inside CTEs.

```sql
WITH expired_sessions AS (
    DELETE FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP
    RETURNING id
)
SELECT COUNT(*) AS deleted_count
FROM expired_sessions;
```

This can compose a mutation and a subsequent query in one statement.

Subqueries are not a general replacement for this capability.

This feature is particularly useful for tightly coupled database workflows where the operation should remain within one SQL statement.

## Scope and Lifetime

Both constructs are statement-scoped, but their syntactic scope differs.

A CTE is defined at the beginning of the statement:

```sql
WITH active_users AS (
    SELECT id
    FROM users
    WHERE status = 'active'
)
SELECT *
FROM active_users;
```

A subquery is nested directly where it is needed:

```sql
SELECT *
FROM users
WHERE id IN (
    SELECT id
    FROM active_users_source
);
```

Neither construct persists after the statement.

Neither should be treated as:

- A temporary table.
- A persistent database object.
- A cross-request cache.
- A session-level application variable.

## Production Decision Framework

Use this decision process when choosing between the two.

```text
Is the query logic naturally local to one expression?
                 │
             ┌───┴───┐
            Yes      No
             │        │
             ▼        ▼
         Subquery   Does the query have
                    multiple logical stages?
                         │
                     ┌───┴───┐
                    Yes      No
                     │        │
                     ▼        ▼
                    CTE    Prefer the simpler
                           representation
```

Then ask:

```text
Does the query require recursion?
        │
        ├── Yes → Recursive CTE
        │
        └── No

Does the intermediate result need
multiple references within the statement?
        │
        ├── Yes → CTE is often clearer
        │
        └── No

Is the logic naturally correlated with
the current outer row?
        │
        ├── Yes → Consider EXISTS/scalar subquery
        │
        └── No

Is performance uncertain?
        │
        └── Compare EXPLAIN ANALYZE plans
```

## Backend Application Example

Suppose a Django API exposes:

```text
GET /customers/high-value
```

The endpoint needs customers whose completed orders in the last 90 days exceed a revenue threshold.

A CTE can model the database-side transformation:

```sql
WITH recent_completed_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
),
customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM recent_completed_orders
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    cr.revenue
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id
WHERE cr.revenue >= $1
ORDER BY cr.revenue DESC
LIMIT $2;
```

The application should pass the threshold and limit as parameters rather than interpolating them into SQL.

The query remains a single database operation:

```text
HTTP request
     │
     ▼
Django / FastAPI
     │
     ▼
Parameterized SQL
     │
     ▼
Database optimizer
     │
     ├── recent_completed_orders
     ├── customer_revenue
     └── final result
     │
     ▼
API response
```

The same business logic could be expressed using nested derived tables, but the CTE version becomes easier to maintain as additional stages are introduced.

## ORM Considerations

High-level ORMs such as Django's ORM do not always expose every SQL composition feature directly.

For example, simple subqueries can be represented using Django expressions such as `Subquery` and `Exists`.

```python
from django.db.models import Exists, OuterRef

completed_orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
    status="completed",
)

customers = Customer.objects.filter(
    Exists(completed_orders),
)
```

For complex CTE-heavy workloads, teams may use:

- Database views.
- Carefully reviewed raw SQL.
- ORM extensions.
- Query-building libraries.
- Stored database abstractions where appropriate.

The important engineering rule is to preserve parameterization, observability, testability, and clear ownership of complex SQL.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Assuming CTEs are always faster | Confusing structure with execution | Compare execution plans |
| Replacing every subquery with a CTE | Treating CTEs as universally superior | Use the clearest representation |
| Using deeply nested subqueries everywhere | Avoiding named query stages | Introduce CTEs when composition becomes complex |
| Using a CTE for a single scalar value | Over-structuring simple logic | Prefer a scalar subquery when clearer |
| Ignoring correlated `EXISTS` | Treating all existence checks as joins | Consider `EXISTS` for existence semantics |
| Assuming CTEs always materialize | Confusing logical and physical behavior | Check database-specific optimizer behavior |
| Duplicating an expensive subquery | Avoiding CTE reuse | Consider a CTE when multiple references improve clarity |
| Using CTEs without checking indexes | Focusing only on SQL structure | Index join/filter columns and inspect plans |
| Assuming syntax is portable | CTE features vary by database | Verify target DBMS support |
| Building unsafe dynamic SQL | Concatenating application input | Use parameterized queries |

## Performance Pitfalls

### Filtering Too Late

A query can become unnecessarily expensive if an intermediate relation processes far more rows than required.

Prefer pushing selective predicates as close to the source data as correctness allows:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM recent_orders
GROUP BY customer_id;
```

However, do not manually rewrite queries solely based on assumptions about optimizer behavior. Verify the plan.

### Reusing a Large Intermediate Result

A CTE referenced multiple times can be useful, but if its intermediate result is large, the resulting execution strategy may consume significant:

- CPU.
- Memory.
- Temporary storage.
- I/O.

Use `EXPLAIN (ANALYZE, BUFFERS)` and database-specific guidance before forcing materialization.

### Missing Indexes

CTEs do not replace indexes.

For common access patterns, indexes may be needed on columns such as:

```sql
CREATE INDEX CONCURRENTLY idx_orders_status_created_customer
ON orders (status, created_at, customer_id);
```

The correct index depends on actual predicates, cardinality, ordering requirements, and workload. Avoid creating indexes merely because a column appears in a CTE.

## Security Considerations

CTEs and subqueries do not provide authorization by themselves.

For multi-tenant systems, tenant filtering must be enforced correctly:

```sql
WITH tenant_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE tenant_id = $1
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM tenant_orders
GROUP BY customer_id;
```

The application must ensure `$1` corresponds to the authenticated tenant.

Always parameterize external values:

```python
cursor.execute(
    """
    WITH tenant_orders AS (
        SELECT customer_id, total_amount
        FROM orders
        WHERE tenant_id = %s
    )
    SELECT customer_id, SUM(total_amount)
    FROM tenant_orders
    GROUP BY customer_id
    """,
    [tenant_id],
)
```

Neither CTEs nor subqueries should be treated as security boundaries unless the surrounding database security model explicitly enforces the required restrictions.

## Monitoring and Operations

Complex SQL should be observable in production.

Monitor:

- Query latency.
- Rows returned.
- Rows scanned.
- Buffer reads.
- Temporary file usage.
- Lock waits.
- CPU consumption.
- Connection utilization.
- Query frequency.
- Execution-plan changes after schema/data growth.

For PostgreSQL, useful investigation tools include:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

and, where enabled and appropriate, query statistics such as `pg_stat_statements`.

A query that performs well against one million rows can behave very differently after growing to one hundred million rows. CTE versus subquery should therefore be evaluated against realistic production-scale data.

## Interview Traps

### "Are CTEs faster than subqueries?"

**Not inherently.** They are query-composition mechanisms. The optimizer determines the physical execution strategy.

### "Can every subquery be replaced with a CTE?"

Many logical transformations can be expressed either way, but not every form has identical semantics, optimizer behavior, or readability. Correlated subqueries, scalar expressions, recursive traversal, and data-modifying CTEs are important distinctions.

### "Are CTEs always materialized?"

**No.** Materialization behavior is database- and query-dependent. PostgreSQL can inline eligible CTEs and also supports explicit materialization controls.

### "Why use a CTE if a subquery can do the same thing?"

Primarily for **composition, naming, readability, dependency management, and reuse within the statement**. Recursive queries are another major reason.

### "Should I always convert nested subqueries into CTEs?"

**No.** A simple `EXISTS` or scalar subquery can be clearer than introducing a named CTE.

## Practical Comparison

| Situation | Preferred starting point |
|---|---|
| Simple scalar calculation | Scalar subquery |
| Existence check | `EXISTS` subquery |
| Correlated lookup | Correlated subquery |
| One simple derived table | Either |
| Several transformation stages | CTE |
| Reusing an intermediate relation | CTE |
| Window function followed by filtering | CTE or derived table |
| Recursive hierarchy | Recursive CTE |
| Complex data-modifying workflow | CTE where supported |
| Performance-sensitive query | Either; verify with execution plan |

The goal is not to choose the "more advanced" feature. The goal is to choose the representation that makes the query **correct, understandable, maintainable, and performant under the target workload**.

## Key Takeaways

- **CTEs and subqueries can express overlapping logic, but CTEs are usually stronger for named, multi-stage query composition and recursive workloads.**
- **Use subqueries for localized logic such as scalar calculations, `EXISTS`, `IN`, and correlated predicates when they make the intent clearer.**
- **Do not assume either construct is faster; optimizer behavior, indexes, cardinality, and execution plans determine real performance.**
- **CTEs improve structure and reuse within a statement but are not caches or persistent database objects.**
- **For production SQL, choose based on semantics and maintainability first, then validate performance with realistic data and execution plans.**