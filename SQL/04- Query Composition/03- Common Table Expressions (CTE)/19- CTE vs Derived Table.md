# 19- CTE vs Derived Table

## Overview

A **derived table** is a subquery placed in the `FROM` clause and treated as a temporary relation by the surrounding SQL statement. A **CTE (Common Table Expression)** provides a named query expression through a `WITH` clause.

Both are useful for decomposing complex SQL without creating persistent database objects.

The primary difference is **how the intermediate relation is expressed and referenced**:

```text
Derived Table
FROM (
    SELECT ...
) AS alias

CTE
WITH alias AS (
    SELECT ...
)
SELECT ...
FROM alias
```

For a single intermediate result used once, they can often express equivalent relational logic. The choice is primarily about **readability, composition, reuse within the statement, recursive capability, and optimizer behavior**, rather than an assumption that one construct is inherently faster.

## Derived Tables

### What a Derived Table Is

A derived table is a subquery in the `FROM` clause:

```sql
SELECT
    customer_id,
    revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
) AS customer_revenue
WHERE revenue >= 10000;
```

The inner query produces a relation that the outer query can treat like a table.

The alias is required by many SQL dialects and should always be provided for readability and portability.

### Why Derived Tables Exist

Derived tables allow an engineer to:

- Isolate an intermediate relational operation.
- Aggregate before joining.
- Filter or transform data before the outer query processes it.
- Avoid creating temporary or persistent database objects.
- Keep a transformation local to its consumer.

They are particularly useful when the intermediate result has a narrow scope and is consumed exactly once.

## CTEs

A CTE moves the intermediate query into a named `WITH` clause:

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
    revenue
FROM customer_revenue
WHERE revenue >= 10000;
```

The CTE name communicates the role of the intermediate relation before the final query begins.

This becomes increasingly valuable as a query contains multiple transformation stages.

## Equivalent Query Forms

Many derived-table queries can be rewritten as CTEs.

### Derived Table

```sql
SELECT
    c.id,
    c.email,
    x.revenue
FROM customers AS c
JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
) AS x
    ON x.customer_id = c.id
WHERE x.revenue >= 10000;
```

### CTE

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
    c.id,
    c.email,
    cr.revenue
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id
WHERE cr.revenue >= 10000;
```

The logical operation is essentially the same. The CTE form usually makes the intermediate relation easier to identify and reference.

## Readability and Query Composition

Derived tables tend to become harder to read as nesting increases:

```sql
SELECT ...
FROM (
    SELECT ...
    FROM (
        SELECT ...
        FROM (
            SELECT ...
        ) AS a
    ) AS b
) AS c;
```

CTEs can express the same pipeline sequentially:

```sql
WITH filtered_orders AS (
    SELECT ...
    FROM orders
),
customer_totals AS (
    SELECT ...
    FROM filtered_orders
),
ranked_customers AS (
    SELECT ...
    FROM customer_totals
)
SELECT ...
FROM ranked_customers;
```

The CTE version gives each transformation an explicit name and makes the data flow easier to inspect.

This is particularly useful for production queries containing:

- Multiple aggregations.
- Window functions.
- Complex joins.
- Data-quality filters.
- Multi-stage transformations.
- Recursive traversal.

## Multiple Intermediate Relations

A major advantage of CTEs is that multiple named query stages can coexist cleanly.

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
),
customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM recent_orders
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        revenue,
        DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue,
    revenue_rank
FROM ranked_customers
WHERE revenue_rank <= 100;
```

The dependency chain is explicit:

```mermaid
flowchart LR
    A[orders] --> B[recent_orders]
    B --> C[customer_revenue]
    C --> D[ranked_customers]
    D --> E[Final Result]
```

Trying to represent the same pipeline entirely with nested derived tables is possible, but the structure is generally harder to maintain.

## Referencing the Same Intermediate Relation

A CTE can be referenced multiple times within the same statement, subject to the database's SQL semantics.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    high.customer_id,
    high.revenue,
    low.revenue
FROM customer_revenue AS high
JOIN customer_revenue AS low
    ON low.customer_id = high.customer_id
WHERE high.revenue >= 10000
  AND low.revenue < 50000;
```

A derived table normally has to be repeated if its result is needed independently in multiple places:

```sql
SELECT ...
FROM (
    SELECT ...
) AS a
JOIN (
    SELECT ...
) AS b
    ON ...;
```

That duplication can make the query more verbose and can complicate maintenance.

However, **multiple references to a CTE do not automatically mean the database computes it only once**. Physical execution depends on the optimizer and DBMS.

## Recursive Queries

Recursive CTEs are a major capability that derived tables do not provide in the same form.

For hierarchical data:

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

Typical use cases include:

- Organization hierarchies.
- Category trees.
- Folder structures.
- Dependency graphs.
- Bill-of-materials structures.
- Parent-child relationships.

A conventional derived table is not a replacement for recursive CTE semantics.

## Scope and Lifetime

Both constructs are temporary from the perspective of database schema state.

| Property | CTE | Derived Table |
|---|---|---|
| Scope | One SQL statement | One SQL statement |
| Persistent database object | No | No |
| Visible outside statement | No | No |
| Can be named | Yes | Yes, through alias |
| Multiple references | Yes, within statement | Usually requires repetition |
| Recursive query support | Yes | No equivalent recursive mechanism |
| Query composition | Excellent | Good |
| Best fit | Multi-stage or reusable query-local logic | Small local intermediate relation |

Neither creates a persistent table.

For example:

```sql
WITH active_users AS (
    SELECT id
    FROM users
    WHERE status = 'active'
)
SELECT *
FROM active_users;
```

After the statement completes, `active_users` is no longer available.

## Performance Considerations

Do not use a blanket rule such as:

> "CTEs are slower than derived tables."

or:

> "CTEs are faster because the database can reuse them."

Neither statement is generally correct.

Modern optimizers may transform equivalent CTEs and derived tables into similar execution plans.

For example, inspect PostgreSQL with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue >= 10000;
```

Compare it with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
) AS customer_revenue
WHERE revenue >= 10000;
```

Evaluate:

- Execution time.
- Actual row counts.
- Join strategies.
- Scan types.
- Buffer reads/hits.
- Sort operations.
- Hash operations.
- Temporary I/O.
- Memory consumption.

The database engine and version matter.

## PostgreSQL CTE Materialization

PostgreSQL provides explicit control over CTE materialization:

```sql
WITH customer_totals AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals
WHERE revenue >= 10000;
```

Or:

```sql
WITH customer_totals AS NOT MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals
WHERE revenue >= 10000;
```

Materialization can sometimes be useful when a costly intermediate result is intentionally evaluated once and reused. Conversely, preventing inlining can inhibit optimizations such as predicate pushdown.

Use these options based on measured behavior, not as stylistic defaults.

## Predicate Pushdown and Optimization

Consider:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals
WHERE customer_id = 42;
```

An optimizer may be able to push the filter into the underlying operation or otherwise transform the query.

A derived-table equivalent:

```sql
SELECT *
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
) AS customer_totals
WHERE customer_id = 42;
```

may produce the same or a very similar plan.

The senior-level takeaway is that **SQL syntax describes relational intent; the execution plan determines physical behavior**.

## When a Derived Table Is Preferable

Use a derived table when:

- The intermediate query is used only once.
- The transformation is small.
- The relation is tightly coupled to one outer query operation.
- Naming it in the `WITH` section would add more structure than value.
- The query remains readable without additional CTE stages.

Example:

```sql
SELECT
    p.id,
    p.name,
    x.average_price
FROM products AS p
JOIN (
    SELECT
        category_id,
        AVG(price) AS average_price
    FROM products
    GROUP BY category_id
) AS x
    ON x.category_id = p.category_id;
```

The intermediate relation is simple and consumed directly by one join.

## When a CTE Is Preferable

Use a CTE when:

- The query has multiple logical stages.
- The intermediate relation needs a meaningful name.
- The same intermediate relation is referenced multiple times.
- Recursive traversal is required.
- Window functions and aggregations create a complex pipeline.
- You need a clearer separation between filtering, aggregation, ranking, and final selection.

Example:

```sql
WITH customer_orders AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
ranked_customers AS (
    SELECT
        customer_id,
        order_count,
        revenue,
        RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM customer_orders
)
SELECT
    customer_id,
    order_count,
    revenue
FROM ranked_customers
WHERE revenue_rank <= 50;
```

The names describe the transformations rather than forcing the reader to decode nested subqueries.

## CTEs and Derived Tables with JOINs

Both constructs work naturally with joins.

### Derived Table

```sql
SELECT
    c.id,
    c.email,
    x.order_count
FROM customers AS c
JOIN (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
) AS x
    ON x.customer_id = c.id;
```

### CTE

```sql
WITH completed_order_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    coc.order_count
FROM customers AS c
JOIN completed_order_counts AS coc
    ON coc.customer_id = c.id;
```

The CTE form becomes more maintainable if the intermediate relation grows more complex.

## CTEs and Aggregations

Aggregations often benefit from CTE composition.

```sql
WITH monthly_customer_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
)
SELECT
    month,
    SUM(revenue) AS monthly_revenue
FROM monthly_customer_revenue
GROUP BY month
ORDER BY month;
```

A derived table can express the same operation:

```sql
SELECT
    month,
    SUM(revenue) AS monthly_revenue
FROM (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
) AS monthly_customer_revenue
GROUP BY month
ORDER BY month;
```

For one simple stage, either is reasonable. As the transformation pipeline grows, CTEs usually provide better structural clarity.

## CTEs and Window Functions

CTEs are particularly useful when a window function result needs to be filtered.

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
        ) AS row_num
    FROM orders
)
SELECT
    id,
    customer_id,
    total_amount
FROM ranked_orders
WHERE row_num <= 3;
```

A derived table can perform the same operation:

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
        ) AS row_num
    FROM orders
) AS ranked_orders
WHERE row_num <= 3;
```

The CTE version is often easier to extend if additional ranking logic follows.

## Readability Rules

Prefer names that describe the **result's role**, not its implementation.

Good:

```sql
WITH completed_orders AS (...),
customer_revenue AS (...),
ranked_customers AS (...)
```

Less useful:

```sql
WITH query1 AS (...),
tmp AS (...),
data AS (...)
```

For derived tables, use descriptive aliases:

```sql
FROM (
    ...
) AS customer_revenue
```

Avoid meaningless aliases such as:

```sql
FROM (...) AS x
```

unless the query is extremely small and the alias is immediately obvious.

### Keep Each Transformation Focused

A CTE should generally represent one logical transformation:

```sql
WITH filtered_orders AS (...),
customer_totals AS (...),
ranked_customers AS (...)
```

Avoid creating a CTE merely to rename a few columns if it adds no meaningful structure.

## Production Considerations

### Query Review

For production queries, review both:

- Logical readability.
- Physical execution.

A beautifully structured CTE query can still produce a poor execution plan.

Conversely, a compact derived-table query can perform extremely well.

### Application Query Builders and ORMs

Django ORM and many query builders do not expose every CTE capability uniformly.

When using raw SQL:

- Keep queries version controlled.
- Use parameterized values.
- Test generated SQL.
- Add integration tests for important relational behavior.
- Inspect execution plans for expensive endpoints.

Do not introduce raw SQL solely to make a simple query look more sophisticated.

### API Latency

For a REST or gRPC endpoint backed by a complex query:

```text
HTTP/gRPC Request
       │
       ▼
Application Service
       │
       ▼
Repository
       │
       ▼
SQL with CTE / Derived Table
       │
       ▼
Database Optimizer
       │
       ▼
Execution Plan
       │
       ▼
Rows
       │
       ▼
API Response
```

The CTE versus derived-table syntax is only one part of the latency profile.

Also investigate:

- Indexes.
- Cardinality.
- Join order.
- Data volume.
- Lock contention.
- Connection-pool saturation.
- Network transfer.
- Serialization overhead.

## Security Considerations

Neither a CTE nor a derived table is a security mechanism.

Always parameterize external values:

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE customer_id = $1
)
SELECT *
FROM recent_orders;
```

Do not construct SQL by interpolating user input:

```python
# Avoid
query = f"""
SELECT *
FROM (
    SELECT *
    FROM orders
    WHERE customer_id = {customer_id}
) AS recent_orders
"""
```

Instead, use parameterized queries through the database driver or framework.

CTEs and derived tables organize relational computation; authentication and authorization remain application/database security concerns.

## Common Mistakes

| Mistake | Why It Happens | Better Approach |
|---|---|---|
| Assuming CTEs are always slower | Outdated optimizer assumptions | Compare execution plans |
| Assuming CTEs are always faster | Confusing readability with execution optimization | Measure actual workload |
| Using deeply nested derived tables | Query evolved incrementally | Refactor into named CTE stages |
| Creating a CTE for every expression | Overengineering | Use CTEs when they improve structure |
| Using meaningless aliases | Focus on syntax instead of maintainability | Name relations by business/query role |
| Repeating complex derived tables | No query-level reuse mechanism | Consider a CTE |
| Assuming repeated CTE references execute once | Confusing logical reuse with physical execution | Inspect the plan |
| Treating CTEs as temporary tables | Confusing query scope with stored state | Use temporary tables when cross-statement state is required |
| Using either construct as a security boundary | Confusing query structure with authorization | Enforce proper database/application permissions |
| Optimizing syntax before indexes | Premature micro-optimization | Fix cardinality, indexing, and plan problems first |

## CTE vs Derived Table Decision Guide

| Requirement | CTE | Derived Table |
|---|---:|---:|
| One simple intermediate query | Good | **Excellent** |
| Multiple transformation stages | **Excellent** | Possible but less readable |
| Same intermediate relation referenced multiple times | **Excellent** | Awkward |
| Recursive traversal | **Required** | Not suitable |
| Query-local abstraction | **Excellent** | Good |
| Minimal SQL structure | Good | **Excellent** |
| Complex analytical query | **Excellent** | Possible |
| Single-use aggregation before a join | Good | **Excellent** |
| Long-term readability | **Excellent** | Good for simple cases |
| Persistent reuse across statements | Neither | Neither |
| Persisted intermediate data | Neither | Neither |

## Practical Rule of Thumb

A useful engineering rule is:

```text
Simple + used once
        │
        ▼
Derived table

Complex + multiple stages
        │
        ▼
CTE

Recursive
        │
        ▼
Recursive CTE

Used across independent statements
        │
        ▼
Consider a View

Needs persisted/indexed intermediate data
        │
        ▼
Consider a Temporary Table,
Materialized View, or Persistent Table
```

This is a readability and lifecycle heuristic, not a performance law.

When performance matters, validate the chosen representation against the target database and production-like data volume.

## Interview Traps

### "Is a CTE just a derived table?"

They are conceptually similar because both can represent query-local intermediate relations, but they are not identical SQL constructs.

A CTE has explicit naming in the `WITH` clause, can be referenced multiple times within the statement, and supports recursive query semantics.

### "Which is faster?"

There is no universal answer.

Equivalent CTE and derived-table queries may produce the same execution plan. Database engine, version, query shape, indexes, statistics, and data distribution all matter.

### "Does a CTE always materialize?"

No.

Materialization behavior is database-specific and may depend on optimizer decisions or explicit options.

### "Why use a CTE if a derived table can do the same thing?"

Primarily for **query structure, naming, composition, reuse within the statement, and recursive queries**.

The purpose is not automatically performance optimization.

### "Can a derived table be reused?"

Its alias can be referenced by the query scope where it appears, but it does not provide the same convenient statement-level named relation semantics as a CTE. If the same complex relation needs multiple independent references, a CTE is usually clearer.

## Key Takeaways

- **A derived table is a `FROM`-clause subquery; a CTE is a named query expression introduced with `WITH`.**
- **Use derived tables for small, single-use intermediate relations and CTEs for complex, multi-stage, reusable, or recursive query composition.**
- **CTEs and derived tables can produce equivalent execution plans; never make performance decisions from syntax alone.**
- **CTEs improve structure and can be referenced multiple times within a statement, but logical reuse does not guarantee physical materialization or single execution.**
- **For production SQL, prioritize clear query structure, parameterization, appropriate indexes, and execution-plan evidence over premature CTE-versus-derived-table optimization.**