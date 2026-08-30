# 01- CTE Introduction

## Overview

A Common Table Expression (CTE) is a named query expression defined with `WITH` and referenced by the main SQL statement. CTEs provide a structured way to decompose complex queries into logical stages without requiring temporary tables or moving intermediate data into application code.

A CTE is primarily a **query-composition tool**. It can improve readability, isolate transformations, support recursive queries, and make multi-stage relational logic easier to reason about.

```sql
WITH completed_orders AS (
    SELECT
        customer_id,
        order_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spend
FROM completed_orders
GROUP BY customer_id;
```

The important production distinction is that a CTE is not automatically a temporary table, cache, or performance optimization. The database optimizer determines how the CTE participates in the physical execution plan.

## CTE Anatomy

The basic structure is:

```sql
WITH cte_name AS (
    SELECT ...
)
SELECT ...
FROM cte_name;
```

Multiple CTEs can be declared in the same `WITH` clause:

```sql
WITH filtered_orders AS (
    SELECT *
    FROM orders
    WHERE status = 'completed'
),
customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_spend
    FROM filtered_orders
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    ct.total_spend
FROM customers AS c
JOIN customer_totals AS ct
    ON ct.customer_id = c.id;
```

Later CTEs can reference earlier CTEs in the same `WITH` clause.

## Why CTEs Exist

Complex SQL often becomes difficult to maintain when every transformation is nested inside another subquery:

```sql
SELECT ...
FROM (
    SELECT ...
    FROM (
        SELECT ...
        FROM orders
        WHERE ...
    ) AS filtered
    GROUP BY ...
) AS aggregated;
```

A CTE gives each logical stage a name:

```sql
WITH filtered_orders AS (
    SELECT ...
    FROM orders
    WHERE ...
),
aggregated_orders AS (
    SELECT ...
    FROM filtered_orders
    GROUP BY ...
)
SELECT ...
FROM aggregated_orders;
```

The resulting query is easier to inspect, modify, test, and review.

CTEs are particularly useful when a query contains multiple logical transformations such as:

- Filtering.
- Joining.
- Aggregation.
- Ranking.
- Deduplication.
- Enrichment.
- Recursive traversal.
- Final projection.

## Logical Data Flow

A multi-stage CTE query can be understood as a relational pipeline:

```mermaid
flowchart LR
    A[Base Tables] --> B[CTE: Filter]
    B --> C[CTE: Join / Transform]
    C --> D[CTE: Aggregate]
    D --> E[Final SELECT]
    E --> F[Application]
```

The stages improve the **logical organization** of the SQL. They do not necessarily imply that each stage creates a physical intermediate table.

## CTE vs Subquery

A CTE and a derived-table subquery can often express the same relational operation.

### Subquery

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_spend
FROM (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
) AS completed_orders
GROUP BY customer_id;
```

### CTE

```sql
WITH completed_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    SUM(total_amount) AS total_spend
FROM completed_orders
GROUP BY customer_id;
```

The CTE version gives the intermediate relation a name and separates the stages more clearly.

| Concern | CTE | Derived-table subquery |
|---|---|---|
| Readability | Usually better for multi-stage queries | Good for small transformations |
| Naming intermediate logic | Explicit | Alias only |
| Multiple references | Can be useful depending on database behavior | Requires repeating the expression |
| Recursive queries | Supported | Not the normal mechanism |
| Optimization behavior | Database-dependent | Database-dependent |
| Physical materialization | Not inherently guaranteed | Not inherently guaranteed |
| Best use | Complex query composition | Local, one-off transformation |

Do not choose a CTE solely because it looks cleaner. For performance-sensitive queries, inspect the execution plan.

## Multiple CTEs

Multiple CTEs are useful when each stage represents a meaningful relational operation.

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
),
customer_totals AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS total_spend
    FROM recent_orders
    GROUP BY customer_id
),
qualified_customers AS (
    SELECT
        customer_id,
        order_count,
        total_spend
    FROM customer_totals
    WHERE total_spend >= 1000
)
SELECT
    c.id,
    c.email,
    qc.order_count,
    qc.total_spend
FROM customers AS c
JOIN qualified_customers AS qc
    ON qc.customer_id = c.id;
```

Each CTE represents a clear business transformation:

1. Restrict the source dataset.
2. Aggregate by customer.
3. Apply the qualification rule.
4. Join the result to customer metadata.

This structure is often easier to maintain than a deeply nested query.

## CTE Scope

A CTE exists only for the statement in which it is defined.

```sql
WITH active_users AS (
    SELECT id
    FROM users
    WHERE is_active = TRUE
)
SELECT *
FROM active_users;
```

The CTE does not remain available after the statement completes:

```sql
SELECT *
FROM active_users;
```

This fails because `active_users` is not a persistent database object.

Use a:

- **CTE** for statement-local query composition.
- **Temporary table** for a session-scoped physical relation that may be indexed or reused across statements.
- **Permanent table** for durable application data.
- **View** for reusable logical query definitions.

## CTE and Materialization

One of the most important production concepts is that a CTE's logical definition does not necessarily describe its physical execution.

Depending on the database engine and query, the optimizer may:

- Inline the CTE into the surrounding query.
- Materialize the CTE.
- Apply filters through the CTE.
- Reorder operations.
- Transform the query into joins or other execution strategies.

PostgreSQL supports explicit control over CTE materialization:

```sql
WITH filtered_orders AS MATERIALIZED (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM filtered_orders
GROUP BY customer_id;
```

It also supports explicitly requesting inlining:

```sql
WITH filtered_orders AS NOT MATERIALIZED (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM filtered_orders
GROUP BY customer_id;
```

These options should be used only when there is a demonstrated reason. The optimizer's default behavior is generally preferable unless execution-plan analysis shows otherwise.

## CTE vs Temporary Table

CTEs and temporary tables solve different problems.

| Characteristic | CTE | Temporary Table |
|---|---|---|
| Lifetime | Single SQL statement | Session/transaction depending on database |
| Persistent object | No | Temporary database object |
| Can add indexes | No | Yes |
| Can be reused across statements | No | Yes |
| Transaction semantics | Part of statement | Database-dependent |
| Query composition | Excellent | More operational overhead |
| Large reusable intermediate dataset | Usually not the first choice | Often appropriate |
| Debugging intermediate data | Less convenient | Easier |
| Schema persistence | No | Temporary |

For example, if a backend job performs several independent queries against the same expensive intermediate dataset, a temporary table may be more appropriate than repeatedly embedding a CTE.

## Recursive CTEs

A recursive CTE allows a query to repeatedly traverse a relationship until a termination condition is reached.

A common use case is hierarchical data such as organizational structures or category trees.

```sql
WITH RECURSIVE category_tree AS (
    SELECT
        id,
        parent_id,
        name,
        0 AS depth
    FROM categories
    WHERE id = 100

    UNION ALL

    SELECT
        c.id,
        c.parent_id,
        c.name,
        ct.depth + 1
    FROM categories AS c
    JOIN category_tree AS ct
        ON c.parent_id = ct.id
)
SELECT
    id,
    parent_id,
    name,
    depth
FROM category_tree
ORDER BY depth, id;
```

Recursive CTEs generally consist of:

- **Anchor member** — establishes the initial rows.
- **Recursive member** — finds the next level.
- **Termination condition** — eventually prevents additional rows from being produced.

Recursive queries require careful handling of cycles, maximum depth, and potentially explosive result sets.

## CTEs in Backend Systems

CTEs are useful in backend applications when business logic naturally consists of several database-side transformations.

For example, a reporting endpoint might need:

1. Recent completed orders.
2. Customer-level aggregation.
3. Revenue threshold filtering.
4. Ranking.
5. Final API projection.

Keeping these operations in SQL can avoid transferring large intermediate datasets into Python.

```python
from django.db import connection

query = """
WITH recent_orders AS (
    SELECT customer_id, total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_DATE - INTERVAL '30 days'
),
customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_spend
    FROM recent_orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_spend
FROM customer_totals
WHERE total_spend >= %s
ORDER BY total_spend DESC
"""

with connection.cursor() as cursor:
    cursor.execute(query, [1000])
    rows = cursor.fetchall()
```

The important application-level rule is to keep values parameterized. CTEs do not change SQL injection requirements.

## CTEs and Django ORM

Django's ORM can express many CTE-like transformations through annotations, subqueries, aggregations, and window functions. For cases where the ORM cannot express the required SQL cleanly, carefully reviewed raw SQL can be appropriate.

For example, a simple aggregation may not need a CTE at all:

```python
from django.db.models import Sum

customer_totals = (
    Order.objects
    .filter(status="completed")
    .values("customer_id")
    .annotate(total_spend=Sum("total_amount"))
)
```

Do not introduce raw SQL or a CTE merely because the query is conceptually complex. First determine whether the existing ORM constructs provide an understandable and efficient representation.

## Performance Considerations

A CTE does not automatically make a query faster.

Performance depends on:

- Input cardinality.
- Predicate selectivity.
- Join strategy.
- Indexes.
- Statistics.
- Aggregation strategy.
- Sort and hash operations.
- CTE materialization or inlining.
- Number of references.
- Concurrent database workload.

For PostgreSQL, inspect the actual plan:

```sql
EXPLAIN (
    ANALYZE,
    BUFFERS
)
WITH completed_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    SUM(total_amount)
FROM completed_orders
GROUP BY customer_id;
```

Do not optimize based on the presence of `WITH` alone.

## When to Use a CTE

A CTE is a strong choice when:

- A query has multiple logical transformation stages.
- Naming an intermediate relation materially improves readability.
- The same intermediate expression needs to be referenced multiple times.
- Recursive traversal is required.
- A complex query needs a clear boundary between transformations.
- The query is easier to test and review when decomposed into named stages.

A good CTE name should describe the resulting relation:

```sql
WITH completed_orders AS (...)
```

is preferable to:

```sql
WITH temp1 AS (...)
```

The name should communicate the business or relational meaning of the dataset.

## When Not to Use a CTE

Avoid introducing a CTE when it only adds ceremony to a simple query.

Instead of:

```sql
WITH active_users AS (
    SELECT id
    FROM users
    WHERE is_active = TRUE
)
SELECT id
FROM active_users;
```

a direct query is clearer:

```sql
SELECT id
FROM users
WHERE is_active = TRUE;
```

Also reconsider CTEs when:

- The query becomes a long chain of trivial stages.
- A simple join expresses the relationship more naturally.
- A window function is the appropriate analytical operation.
- A temporary table is needed across multiple statements.
- Execution-plan analysis shows an undesirable materialization or repeated expensive work.
- The CTE hides rather than clarifies the query's intent.

## CTE Naming and Design Guidelines

Prefer names that describe the relation:

| Weak | Better |
|---|---|
| `tmp` | `recent_orders` |
| `data` | `customer_totals` |
| `x` | `eligible_customers` |
| `step1` | `completed_orders` |
| `result` | `ranked_products` |

Good CTEs usually have one clear responsibility.

```sql
WITH recent_orders AS (...),
customer_totals AS (...),
ranked_customers AS (...)
SELECT ...
```

This is easier to reason about than a single CTE containing unrelated transformations.

## Common Mistakes

### Treating a CTE as a Temporary Table

A CTE is not automatically a persisted intermediate table.

If you need to:

- Create indexes.
- Reuse the dataset across statements.
- Inspect intermediate results independently.
- Control its physical storage.

consider a temporary table instead.

### Assuming CTEs Improve Performance

A CTE can improve readability without changing the fundamental execution cost.

Always validate performance with representative data and execution plans.

### Creating Excessively Long CTE Chains

A query with many CTEs can become difficult to understand if every minor expression gets its own stage.

Use a new CTE when it creates a meaningful conceptual boundary.

### Ignoring Cardinality

A CTE can produce far more rows than expected.

For example:

```sql
WITH expanded_orders AS (
    SELECT
        o.id,
        oi.product_id,
        oi.quantity
    FROM orders AS o
    JOIN order_items AS oi
        ON oi.order_id = o.id
)
SELECT ...
FROM expanded_orders;
```

The result cardinality is now at the order-item level, not the order level.

Understand the grain of every CTE.

### Using CTEs to Hide Poor Joins

A CTE does not compensate for an inefficient join, missing index, accidental Cartesian product, or incorrect predicate.

The query still needs correct relational design.

## Production Checklist

Before deploying a complex CTE query:

- Confirm the expected row grain of every CTE.
- Validate join predicates and cardinality.
- Check `NULL` behavior.
- Check whether duplicate rows are intentional.
- Run `EXPLAIN ANALYZE` against representative data.
- Inspect actual versus estimated row counts.
- Review indexes supporting filters and joins.
- Check memory-intensive sorts and hash operations.
- Verify behavior under realistic concurrency.
- Parameterize application-supplied values.
- Avoid unnecessary CTE layers.
- Monitor query latency after deployment.

For high-throughput APIs, query performance should be evaluated against the complete workload rather than an isolated development database.

## Interview Perspective

Common interview questions include:

| Question | Key point |
|---|---|
| What is a CTE? | A named query expression defined with `WITH` for statement-level composition |
| Is a CTE a temporary table? | No; its lifetime and physical behavior are different |
| Does a CTE always materialize? | No; behavior is database- and optimizer-dependent |
| Why use a CTE? | Readability, decomposition, reuse, and recursive queries |
| Can CTEs reference other CTEs? | Yes, later CTEs can reference earlier ones |
| Can CTEs be recursive? | Yes, using recursive CTE syntax |
| Are CTEs always faster than subqueries? | No |
| Can a CTE have indexes? | No; use a temporary table when indexed intermediate storage is required |
| What should you check for performance? | Execution plan, cardinality, indexes, I/O, CPU, memory, and workload |

A strong senior-level answer distinguishes **logical SQL structure** from **physical query execution**. The presence of a CTE does not by itself determine whether data is materialized, scanned repeatedly, or optimized into another relational operation.

## Key Takeaways

- **A CTE is a statement-scoped named query expression used to structure complex SQL into meaningful relational stages.**
- **CTEs improve query composition and readability, but they are not automatically temporary tables or performance optimizations.**
- **Always reason about the row grain, cardinality, joins, and predicates of each CTE before composing later stages.**
- **Use execution plans to understand materialization, inlining, indexing, I/O, and actual performance behavior.**
- **Use temporary tables, views, joins, subqueries, or window functions when those constructs better match the required lifecycle or relational operation.**