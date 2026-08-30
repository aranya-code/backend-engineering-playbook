# 24- Common CTE Mistakes

## Overview

Common Table Expressions (CTEs) are primarily a query-composition tool. They make complex SQL easier to decompose into logical stages, but they do not automatically make a query faster, safer, or more correct.

Most CTE failures in production are not syntax errors. They are problems involving:

- Incorrect row cardinality.
- Accidental aggregation errors.
- Misunderstood optimizer behavior.
- Excessive intermediate data.
- Poor naming and unclear dependencies.
- Unbounded recursive traversal.
- Incorrect assumptions about ordering.
- Missing authorization predicates.
- Using a CTE where another database primitive is more appropriate.

The key engineering principle is:

> Use a CTE to make a relational transformation explicit, then validate that the resulting SQL has the correct semantics and execution plan.

## Incorrect Row Grain

One of the most dangerous CTE mistakes is failing to understand how many rows a CTE produces.

Consider:

```sql
WITH customer_orders AS (
    SELECT
        customer_id,
        id AS order_id,
        total_amount
    FROM orders
)
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM customer_orders
GROUP BY customer_id;
```

This produces one row per order inside the CTE and one row per customer in the final query.

If a later engineer assumes `customer_orders` contains one row per customer, subsequent joins can silently produce incorrect results.

Document the intended grain mentally and through naming:

```text
orders
└── one row per order

customer_order_totals
└── one row per customer
```

A useful rule is:

> Every non-trivial CTE should have an intentional row grain.

## Aggregating After a Multiplying Join

Joining multiple one-to-many relationships before aggregating can multiply rows.

Suppose a customer has:

- 5 orders.
- 3 support tickets.

A direct join can produce up to:

```text
5 × 3 = 15 rows
```

If those rows are aggregated afterward, order revenue and ticket counts can be overstated.

### Problematic Query

```sql
SELECT
    c.id,
    SUM(o.total_amount) AS revenue,
    COUNT(t.id) AS ticket_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id
GROUP BY c.id;
```

### Safer CTE Composition

```sql
WITH order_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
),
ticket_totals AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
)
SELECT
    c.id,
    COALESCE(ot.revenue, 0) AS revenue,
    COALESCE(tt.ticket_count, 0) AS ticket_count
FROM customers AS c
LEFT JOIN order_totals AS ot
    ON ot.customer_id = c.id
LEFT JOIN ticket_totals AS tt
    ON tt.customer_id = c.id;
```

Each aggregate establishes a one-row-per-customer relation before the final join.

## Assuming CTEs Are Always Materialized

A CTE is a logical query expression. Whether it becomes a physically materialized intermediate result depends on the database and optimizer behavior.

Therefore, this assumption is unsafe:

```text
CTE = temporary table
```

They are not equivalent.

For PostgreSQL, CTEs may be folded into the surrounding query when the optimizer determines that this is appropriate, while materialization can also be explicitly requested in supported versions.

```sql
WITH expensive_result AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT ...
FROM expensive_result;
```

Conversely:

```sql
WITH recent_orders AS NOT MATERIALIZED (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT ...
FROM recent_orders;
```

Do not choose either option based on intuition alone.

Validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH ...
SELECT ...;
```

## Assuming CTEs Are Always Faster

CTEs are not a performance feature by definition.

These two queries can produce equivalent execution plans:

```sql
WITH recent_orders AS (
    SELECT *
    FROM orders
    WHERE status = 'completed'
)
SELECT COUNT(*)
FROM recent_orders;
```

and:

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'completed';
```

The optimizer may transform them into similar physical operations.

Performance depends on:

- Database engine.
- Database version.
- Statistics.
- Indexes.
- Data distribution.
- Query structure.
- Join strategy.
- Materialization behavior.
- Workload concurrency.

The correct workflow is:

```text
Write clear SQL
      │
      ▼
Validate semantics
      │
      ▼
EXPLAIN / ANALYZE
      │
      ▼
Measure
      │
      ▼
Optimize if necessary
```

## Using Too Many CTEs

CTEs should represent meaningful logical boundaries.

This is often unnecessarily fragmented:

```sql
WITH
a AS (...),
b AS (...),
c AS (...),
d AS (...),
e AS (...),
f AS (...)
SELECT ...
FROM f;
```

If each CTE merely renames a simple expression, the query may become harder to understand rather than easier.

Prefer stages that communicate intent:

```sql
WITH eligible_orders AS (...),
customer_revenue AS (...),
ranked_customers AS (...)
SELECT ...;
```

A senior engineer should optimize for **logical clarity**, not the number of CTEs.

## Naming CTEs Poorly

Names such as:

```sql
WITH temp1 AS (...),
temp2 AS (...)
```

provide almost no information.

Prefer names that communicate the relation's meaning:

```sql
WITH eligible_orders AS (...),
customer_revenue AS (...),
latest_payment_attempt AS (...)
```

Good names help reviewers infer:

- What rows represent.
- What stage has already occurred.
- What the CTE is safe to join with.
- What the final query is trying to achieve.

Avoid names that encode implementation details instead of semantics.

## Hiding Row Multiplication Behind Generic Names

This is especially dangerous:

```sql
WITH data AS (
    SELECT ...
)
```

A generic name makes cardinality problems harder to identify.

Prefer:

```sql
WITH orders_per_customer AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
)
```

The name communicates both the subject and the aggregation level.

## Using `SELECT *`

This pattern is convenient:

```sql
WITH recent_orders AS (
    SELECT *
    FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT ...
FROM recent_orders;
```

But it can unnecessarily propagate columns through multiple query stages.

Prefer:

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at
    FROM orders
    WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT ...
FROM recent_orders;
```

Explicit projections improve:

- Readability.
- Query review.
- Schema-change resilience.
- Data transfer.
- Memory usage.
- Downstream planning.

## Filtering Too Late

If a query can safely eliminate irrelevant rows before an expensive join or aggregation, filtering earlier can reduce the working set.

Prefer:

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
    SUM(total_amount)
FROM completed_orders
GROUP BY customer_id;
```

instead of carrying all statuses into the aggregation when they are not needed.

However, do not blindly rewrite queries to push every predicate into every CTE. Optimizers can perform predicate pushdown themselves, and restructuring can sometimes change semantics.

Use execution plans to determine whether the filter placement matters physically.

## Relying on CTE Ordering

A CTE's internal ordering should not be treated as the ordering of the final result.

This is unsafe as a general assumption:

```sql
WITH ranked_orders AS (
    SELECT
        id,
        total_amount
    FROM orders
    ORDER BY total_amount DESC
)
SELECT *
FROM ranked_orders;
```

If the final result must be ordered, specify it in the final query:

```sql
SELECT *
FROM ranked_orders
ORDER BY total_amount DESC;
```

Ordering is part of the result contract only when the query producing the consumed result explicitly requires it.

## Incorrect "Latest Row" Logic

This pattern is common:

```sql
SELECT
    customer_id,
    MAX(created_at) AS latest_order
FROM orders
GROUP BY customer_id;
```

It gives the latest timestamp, but not necessarily the complete row associated with that timestamp.

If you need the actual order record, use a deterministic window function:

```sql
WITH ranked_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM orders
)
SELECT
    id,
    customer_id,
    total_amount,
    created_at
FROM ranked_orders
WHERE row_number = 1;
```

The secondary `id` ordering provides deterministic tie-breaking.

## Forgetting Null Semantics

Aggregations and outer joins frequently introduce `NULL`.

For example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    c.id,
    cr.revenue
FROM customers AS c
LEFT JOIN customer_revenue AS cr
    ON cr.customer_id = c.id;
```

Customers with no orders receive `NULL`, not `0`.

If the application expects zero:

```sql
COALESCE(cr.revenue, 0)
```

Use null handling deliberately rather than allowing SQL semantics to leak unexpectedly into API responses.

## Filtering a `LEFT JOIN` in the Wrong Place

A common mistake is accidentally turning an outer join into an inner join.

This:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

eliminates customers without matching orders because the `WHERE` predicate rejects the `NULL` side of the join.

If the intended semantics are "all customers, with completed orders when present," put the condition in the join:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

CTEs do not eliminate this relational behavior.

## Unbounded Recursive CTEs

Recursive CTEs require explicit termination.

A hierarchy traversal can unexpectedly become expensive because of:

- Cycles.
- Corrupt parent references.
- Extremely deep trees.
- Unexpected fan-out.

A basic recursive query:

```sql
WITH RECURSIVE hierarchy AS (
    SELECT
        id,
        manager_id,
        name,
        0 AS depth
    FROM employees
    WHERE id = $1

    UNION ALL

    SELECT
        e.id,
        e.manager_id,
        e.name,
        h.depth + 1
    FROM employees AS e
    JOIN hierarchy AS h
        ON e.manager_id = h.id
    WHERE h.depth < 50
)
SELECT
    id,
    manager_id,
    name,
    depth
FROM hierarchy;
```

A depth limit is not a universal cycle solution, but it provides an operational guardrail.

For graph-like data, also consider explicit cycle detection and the database's supported recursive-query features.

## Ignoring Recursive Query Fan-Out

Depth is not the only concern.

A hierarchy with branching factor `b` and depth `d` can generate a rapidly growing number of paths or rows.

For example:

```text
             root
           /  |  \
          A   B   C
        / |\
       ...
```

A recursive query that is reasonable for an organizational tree may be dangerous for a dependency graph.

Before using recursive CTEs in production, understand:

- Maximum expected depth.
- Maximum branching factor.
- Duplicate paths.
- Cycle behavior.
- Required indexes.
- Maximum acceptable result size.

## Forgetting Indexes on Recursive Traversal Columns

A recursive query commonly traverses a relationship such as:

```sql
JOIN employees AS e
    ON e.manager_id = hierarchy.id
```

An index on the traversal column can be critical:

```sql
CREATE INDEX idx_employees_manager_id
ON employees (manager_id);
```

The exact index strategy depends on the workload and schema, but recursive query performance should be evaluated with realistic hierarchy sizes.

## Using a CTE Where `EXISTS` Is Clearer

Sometimes a CTE introduces unnecessary intermediate structure.

For example:

```sql
WITH active_customers AS (
    SELECT id
    FROM customers
    WHERE status = 'active'
)
SELECT c.id
FROM customers AS c
JOIN active_customers AS ac
    ON ac.id = c.id;
```

If the intent is simply to filter customers, this is unnecessarily complicated.

Use:

```sql
SELECT id
FROM customers
WHERE status = 'active';
```

Likewise, existence checks are often clearer with `EXISTS`:

```sql
SELECT
    c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The best SQL abstraction is the one that expresses the relational intent most directly.

## Treating a CTE as Persistent State

A CTE exists only within its statement.

This will not work:

```sql
WITH customer_totals AS (...)
SELECT ...
FROM customer_totals;

SELECT ...
FROM customer_totals;
```

If the intermediate result must survive beyond one statement, consider:

- Temporary tables.
- Permanent tables.
- Staging tables.
- Views.
- Materialized views.
- Application-side storage.

Choose based on required lifetime, reuse, indexing, and refresh behavior.

## Using CTEs for Large Reusable Intermediate Data

A CTE is often a poor choice when an intermediate dataset is:

- Very large.
- Reused across many independent statements.
- Expensive to compute.
- Frequently queried.
- Beneficial to index.

A temporary table may be more appropriate:

```sql
CREATE TEMP TABLE customer_totals AS
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;

CREATE INDEX idx_customer_totals_customer_id
ON customer_totals (customer_id);
```

The choice should be based on workload requirements rather than a preference for one SQL construct.

## Ignoring Authorization Boundaries

A CTE does not provide authorization by itself.

In a multi-tenant backend application, this is dangerous:

```sql
WITH recent_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT ...
FROM recent_orders;
```

If the final query does not restrict the organization or tenant, it may expose data across tenants.

Prefer:

```sql
WITH accessible_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE organization_id = $1
      AND status = 'completed'
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM accessible_orders
GROUP BY customer_id;
```

Use bound parameters rather than string interpolation.

```python
cursor.execute(sql, [organization_id])
```

For sensitive systems, database-level controls such as PostgreSQL Row-Level Security can provide an additional defense layer.

## Building Dynamic SQL With CTEs

CTEs can make an already complex query significantly harder to safely construct dynamically.

Avoid:

```python
sql = f"""
WITH orders AS (
    SELECT *
    FROM orders
    WHERE organization_id = {organization_id}
)
SELECT ...
"""
```

Use parameter binding:

```python
sql = """
WITH accessible_orders AS (
    SELECT
        customer_id,
        total_amount
    FROM orders
    WHERE organization_id = %s
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM accessible_orders
GROUP BY customer_id
"""

cursor.execute(sql, [organization_id])
```

Parameters should represent values, not arbitrary SQL fragments. Dynamic identifiers require separate safe composition mechanisms provided by the database driver.

## Ignoring Transaction Size

CTEs used for large data modifications can create substantial transactional work.

For example:

```sql
WITH expired_sessions AS (
    SELECT id
    FROM sessions
    WHERE expires_at < CURRENT_TIMESTAMP
)
DELETE FROM sessions AS s
USING expired_sessions AS es
WHERE s.id = es.id;
```

On a very large table, this can produce:

- Large WAL volume.
- Long-running transactions.
- Lock contention.
- Replication lag.
- Large vacuum debt.
- Increased storage pressure.

For high-volume cleanup jobs, consider controlled batching, appropriate indexes, and operational limits.

The correct approach depends on the database and workload; the key mistake is treating a large mutation as equivalent to a small transactional query.

## Ignoring Execution Plans

Readable SQL is not necessarily efficient SQL.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
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
    cr.revenue
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id;
```

Look for:

| Signal | What to investigate |
|---|---|
| Large row estimate mismatch | Statistics or data-distribution assumptions |
| Sequential scan | Missing/ineffective index or intentional full scan |
| Large sort | Ordering, window functions, memory pressure |
| Hash spill | Insufficient memory or large intermediate relation |
| Temporary reads/writes | Intermediate result pressure |
| Nested-loop explosion | Join cardinality and indexes |
| High execution time | Overall query shape and workload |

Do not optimize the CTE syntax before understanding the physical plan.

## Overusing CTEs for ORM Escape Hatches

Frameworks such as Django can generate complex SQL through ORM expressions, but jumping directly to raw SQL with many CTEs can create a maintenance boundary.

Before introducing raw SQL, evaluate:

- Whether the ORM can express the query clearly.
- Whether the query is performance-critical.
- Whether the SQL needs database-specific functionality.
- How migrations will evolve the schema.
- How tests will validate the query.
- Whether developers can safely maintain the SQL.

For complex reporting or database-specific operations, raw SQL can be the right choice. It should still live in a deliberate data-access layer rather than being embedded throughout request handlers.

## Not Testing With Production-Scale Data

A CTE query that works well against:

```text
10,000 rows
```

may behave very differently against:

```text
500 million rows
```

Test important queries using realistic:

- Row counts.
- Data distributions.
- Cardinalities.
- Skew.
- Concurrent load.
- Index state.
- Statistics.

A query's performance characteristics often emerge only at realistic scale.

## Not Testing Edge Cases

CTEs are especially susceptible to semantic edge cases.

Test cases should include:

- No matching rows.
- Exactly one matching row.
- Multiple matches.
- Duplicate timestamps.
- `NULL` values.
- Empty groups.
- Multiple tenants.
- Large groups.
- Deep hierarchies.
- Cyclic relationships where applicable.
- Boundary timestamps.
- Concurrent modifications for write queries.

For "latest row" logic, explicitly test equal timestamps.

For aggregation, test customers with no orders.

For recursive queries, test maximum expected depth and malformed relationships.

## Common Mistakes by Category

| Mistake | Primary Risk | Prevention |
|---|---|---|
| Wrong row grain | Incorrect results | Define cardinality for every stage |
| Aggregating after multiplying joins | Inflated metrics | Aggregate one-to-many relations independently |
| Assuming materialization | Incorrect performance assumptions | Inspect execution plans |
| Assuming CTEs are faster | Misguided optimization | Benchmark actual workload |
| Too many CTEs | Reduced readability | Keep meaningful logical stages |
| `SELECT *` | Excess data and coupling | Project required columns |
| Missing deterministic ordering | Non-repeatable results | Add stable tie-breakers |
| Unbounded recursion | Resource exhaustion | Bound depth and handle cycles |
| Missing traversal indexes | Slow recursion | Index relationship columns |
| Late authorization filters | Data exposure | Enforce tenant predicates deliberately |
| Large write CTEs | Lock/WAL pressure | Batch and monitor mutations |
| Treating CTEs as persistent state | Incorrect design | Use temp tables or persistent structures |
| Ignoring execution plans | Production latency | Use `EXPLAIN ANALYZE` |
| Testing only small datasets | Scale surprises | Test production-like volumes |

## Production Review Checklist

Before merging a complex CTE query, review:

### Correctness

- [ ] Is the row grain of every CTE understood?
- [ ] Are joins producing the intended cardinality?
- [ ] Are aggregates protected from row multiplication?
- [ ] Are `NULL` results handled intentionally?
- [ ] Is ordering deterministic where required?
- [ ] Are recursive termination conditions correct?

### Performance

- [ ] Are unnecessary columns excluded?
- [ ] Are selective predicates applied appropriately?
- [ ] Are join and traversal columns indexed?
- [ ] Is the intermediate result reasonably sized?
- [ ] Has the query been inspected with `EXPLAIN`?
- [ ] Has it been tested with production-scale data?

### Security

- [ ] Are tenant boundaries enforced?
- [ ] Are authorization predicates applied consistently?
- [ ] Are query parameters bound safely?
- [ ] Could the query expose rows belonging to another tenant?

### Operations

- [ ] Is the query latency monitored?
- [ ] Is query frequency understood?
- [ ] Could a large mutation create lock or WAL pressure?
- [ ] Could recursion generate an unexpectedly large result?
- [ ] Is there a safe rollback or recovery strategy for write operations?

## Key Takeaways

- **The most dangerous CTE mistakes are semantic: incorrect row grain, join multiplication, aggregation errors, and unintended `NULL` behavior.**
- **Do not assume CTEs are faster, always materialized, or equivalent to temporary tables; validate behavior with the target database's execution plan.**
- **Keep CTEs focused on meaningful logical stages, use precise names and projections, and avoid unnecessary query fragmentation.**
- **Treat recursive CTEs and large data-modifying CTEs as operationally sensitive workloads requiring bounds, indexes, transaction discipline, and monitoring.**
- **In production, validate CTE queries for correctness, authorization, performance, concurrency, and realistic data volume—not merely whether the SQL executes successfully.**