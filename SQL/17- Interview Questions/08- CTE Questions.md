# 08- CTE Questions

## Overview

Common Table Expressions (CTEs) are one of the most useful SQL constructs for expressing complex queries as a sequence of named relational steps.

A CTE is introduced with:

```sql
WITH ...
```

Example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue > 10000;
```

CTEs are frequently tested in interviews because they combine:

- Query decomposition
- Aggregation
- Joins
- Subqueries
- Recursion
- Window functions
- Data modification
- Query planning
- Performance reasoning

The senior-level question is not simply whether you know the `WITH` syntax.

It is:

> **Can you use a CTE to make complex relational logic clearer without accidentally introducing unnecessary materialization, repeated work, poor cardinality, or production-scale performance problems?**

---

## What Is a CTE?

A Common Table Expression is a named query expression defined before the main SQL statement.

General form:

```sql
WITH cte_name AS (
    SELECT ...
)
SELECT ...
FROM cte_name;
```

The CTE can be referenced by the statement that follows it.

Conceptually:

```text
Base tables
    ↓
CTE
    ↓
named intermediate result
    ↓
outer query
    ↓
final result
```

A CTE is primarily a query-composition mechanism. It should not automatically be interpreted as a temporary table or permanent database object.

---

## Why CTEs Exist

Complex SQL can become difficult to reason about when everything is written as deeply nested subqueries.

Instead of:

```sql
SELECT ...
FROM (
    SELECT ...
    FROM (
        SELECT ...
    ) AS x
) AS y;
```

a CTE can make each logical stage explicit:

```sql
WITH first_step AS (
    SELECT ...
),
second_step AS (
    SELECT ...
    FROM first_step
)
SELECT ...
FROM second_step;
```

This improves:

- Readability
- Debuggability
- Logical decomposition
- Maintenance
- Complex reporting queries

---

## CTE Syntax

Basic syntax:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals;
```

Multiple CTEs:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
),
high_value_customers AS (
    SELECT
        customer_id,
        revenue
    FROM customer_totals
    WHERE revenue > 10000
)
SELECT *
FROM high_value_customers;
```

A later CTE can reference an earlier CTE in the same `WITH` clause.

---

## CTE Execution Model

A common misconception is:

> "A CTE always creates a temporary table."

That is not generally correct.

The SQL text describes a named relational expression. The optimizer can decide how it should be executed.

Depending on the query and PostgreSQL version, a CTE may be:

- Inlined into the surrounding query
- Materialized
- Explicitly forced to materialize
- Explicitly forced to inline

This distinction is important for performance.

---

## CTE vs Subquery

These can represent similar logical operations.

### Subquery

```sql
SELECT *
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
) AS customer_totals
WHERE revenue > 10000;
```

### CTE

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
WHERE revenue > 10000;
```

The CTE version often becomes easier to read as complexity increases.

---

## CTE vs Temporary Table

A CTE:

- Exists only within the statement
- Is not independently queryable after the statement
- Does not require explicit cleanup
- Is part of one SQL statement

A temporary table:

- Is a database object for the session/transaction
- Can be queried multiple times
- Can have indexes
- Can be populated and modified independently
- May be useful when intermediate results need to survive across multiple statements

| Feature | CTE | Temporary Table |
|---|---|---|
| Scope | One statement | Session/transaction |
| Explicit object | No | Yes |
| Can create indexes | No | Yes |
| Reusable across statements | No | Yes |
| Planner can inline | Yes, depending on query | No |
| Useful for procedural workflows | Limited | Stronger |

Do not use a temporary table merely because a query contains multiple logical stages.

---

## CTE vs View

A view is a persistent database object:

```sql
CREATE VIEW customer_totals AS
SELECT ...
```

A CTE is local to one statement:

```sql
WITH customer_totals AS (
    SELECT ...
)
SELECT ...
```

Use a view when the relational interface should be reused across many queries.

Use a CTE when the intermediate logic belongs to one specific statement.

---

## Non-Recursive CTE

Most CTEs are ordinary non-recursive CTEs.

Example:

```sql
WITH paid_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'paid'
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM paid_orders
GROUP BY customer_id;
```

The CTE creates a logical stage:

```text
orders
  ↓
paid_orders
  ↓
customer aggregation
```

---

## Multiple CTEs as a Query Pipeline

A complex report can be decomposed:

```sql
WITH paid_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'paid'
),
customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM paid_orders
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
    c.name,
    h.revenue
FROM high_value_customers AS h
JOIN customers AS c
    ON c.id = h.customer_id;
```

This makes the data flow explicit:

```text
orders
  ↓
paid_orders
  ↓
customer_revenue
  ↓
high_value_customers
  ↓
customers
  ↓
final result
```

---

## CTE Naming

Good names describe the logical result:

```text
paid_orders
customer_revenue
active_customers
latest_orders
eligible_accounts
```

Avoid:

```text
temp1
data
result
x
cte
```

Good names make complex SQL significantly easier to review.

---

## CTE Column Naming

You can explicitly define CTE column names:

```sql
WITH customer_totals (customer_id, revenue) AS (
    SELECT
        customer_id,
        SUM(total_amount)
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals;
```

Usually the names inside the CTE query are clearer, but explicit column lists can be useful for complex transformations.

---

## CTE and Aggregation

CTEs are particularly useful for multi-stage aggregation.

Example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    AVG(revenue) AS average_customer_revenue
FROM customer_revenue;
```

This calculates:

```text
orders
  ↓
revenue per customer
  ↓
average revenue per customer
```

The intermediate grain is:

> one row per customer.

---

## CTE and Grain

As with subqueries, always define the grain.

For:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
```

the CTE grain is:

```text
one row per customer
```

If you later join it to a one-to-many relationship, you must account for the resulting cardinality.

CTEs improve readability but do not automatically protect against incorrect joins.

---

## CTE and JOIN Multiplication

Suppose:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    cr.customer_id,
    cr.revenue,
    COUNT(oi.id) AS item_count
FROM customer_revenue AS cr
JOIN orders AS o
    ON o.customer_id = cr.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
GROUP BY
    cr.customer_id,
    cr.revenue;
```

The CTE's revenue is already correct at customer grain, but the outer query can still produce multiple rows before its final grouping.

The key is to preserve the intended grain at every stage.

---

## CTE for Pre-Aggregation

A strong production pattern is to aggregate a large child table before joining it to another relation.

```sql
WITH order_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)
SELECT
    c.id,
    c.name,
    COALESCE(ot.revenue, 0) AS revenue
FROM customers AS c
LEFT JOIN order_totals AS ot
    ON ot.customer_id = c.id;
```

This avoids repeatedly carrying raw order rows through later joins.

---

## CTE and Window Functions

CTEs are useful when a window function produces an intermediate result that must then be filtered.

For example:

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE row_number <= 3;
```

This returns the top three orders for each customer.

The CTE provides a clean boundary between:

```text
calculate ranking
        ↓
filter ranking
```

---

## CTE and Latest Record Per Group

A common interview problem:

> Return the latest order for every customer.

One solution:

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;
```

The `id` tie-breaker makes the ordering deterministic when timestamps are equal.

---

## PostgreSQL DISTINCT ON Alternative

PostgreSQL provides another solution:

```sql
SELECT DISTINCT ON (customer_id)
    *
FROM orders
ORDER BY
    customer_id,
    created_at DESC,
    id DESC;
```

This can be concise and efficient for PostgreSQL-specific workloads when the access pattern and index support it.

An index such as:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (
    customer_id,
    created_at DESC,
    id DESC
);
```

may support the access pattern.

Validate with an execution plan.

---

## CTE and Deduplication

CTEs can isolate a deduplication stage:

```sql
WITH unique_customers AS (
    SELECT DISTINCT customer_id
    FROM orders
)
SELECT c.*
FROM customers AS c
JOIN unique_customers AS u
    ON u.customer_id = c.id;
```

However, if the only requirement is existence, `EXISTS` may express the semantics more directly:

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

Do not introduce a CTE just to make SQL look more sophisticated.

---

## CTE and Filtering

A CTE can isolate filtering logic:

```sql
WITH active_orders AS (
    SELECT *
    FROM orders
    WHERE deleted_at IS NULL
      AND status = 'paid'
)
SELECT
    customer_id,
    COUNT(*)
FROM active_orders
GROUP BY customer_id;
```

The query is readable, but an important production question remains:

> Does the optimizer push the surrounding predicates into the CTE or is the CTE materialized?

The answer depends on the query and PostgreSQL's planning behavior.

---

## PostgreSQL CTE Inlining

In PostgreSQL, a non-recursive CTE can often be folded into the parent query when doing so is advantageous.

This means:

```sql
WITH active_orders AS (
    SELECT *
    FROM orders
)
SELECT *
FROM active_orders
WHERE customer_id = $1;
```

does not necessarily require PostgreSQL to first materialize every row from `orders`.

The optimizer can often treat it similarly to:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;
```

This is an important interview correction to the old statement:

> "CTEs are optimization fences."

That behavior applied to older PostgreSQL versions and certain materialization scenarios, but should not be treated as a universal modern rule.

---

## MATERIALIZED

PostgreSQL allows explicit materialization:

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
WHERE revenue > 10000;
```

This can be useful when you deliberately want the intermediate result computed and stored for reuse within the statement.

But materialization can also prevent optimizations such as predicate pushdown.

Use it intentionally.

---

## NOT MATERIALIZED

PostgreSQL also supports:

```sql
WITH customer_totals AS NOT MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals;
```

This requests that the CTE be treated like a normal subquery where possible.

It can allow the planner to optimize the surrounding query more aggressively.

However, `NOT MATERIALIZED` is not automatically faster.

---

## When MATERIALIZED Can Help

Materialization can be useful when:

- An expensive CTE is referenced multiple times
- Recomputing the CTE would be expensive
- You intentionally want a stable intermediate result
- You want to prevent repeated evaluation
- The intermediate result is substantially smaller than the source

Example:

```sql
WITH expensive_metrics AS MATERIALIZED (
    SELECT
        customer_id,
        expensive_expression(...) AS metric
    FROM large_table
)
SELECT ...
FROM expensive_metrics
JOIN ...
UNION ALL
SELECT ...
FROM expensive_metrics;
```

The actual benefit depends on the execution plan and workload.

---

## When MATERIALIZED Can Hurt

Materialization can hurt when:

- The CTE is huge
- Only a small subset is required by the outer query
- Predicate pushdown would have eliminated most rows
- Temporary storage becomes significant
- Memory or I/O pressure increases

For example:

```sql
WITH all_orders AS MATERIALIZED (
    SELECT *
    FROM orders
)
SELECT *
FROM all_orders
WHERE customer_id = $1;
```

If only one customer is required, materializing all orders may be wasteful.

---

## CTE Referenced Multiple Times

A CTE can be referenced multiple times:

```sql
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT ...
FROM customer_totals AS a
JOIN customer_totals AS b
    ON a.customer_id = b.customer_id;
```

Whether this should be materialized or inlined depends on planner behavior and query structure.

If repeated evaluation is expensive, materialization can sometimes be beneficial.

---

## CTE and EXPLAIN

For performance-sensitive CTEs, use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_totals AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals
WHERE revenue > 10000;
```

Look for:

- `CTE Scan`
- Aggregation nodes
- Sorts
- Hash operations
- Actual rows
- Loops
- Buffer usage
- Temporary I/O
- Execution time

Do not optimize CTEs based only on how the SQL looks.

---

## CTE Scan

When a CTE is materialized, PostgreSQL can expose a `CTE Scan` in the execution plan.

Conceptually:

```text
source tables
     ↓
CTE computation
     ↓
materialized result
     ↓
CTE Scan
     ↓
outer query
```

The presence of a CTE does not itself mean this plan will occur.

---

## CTE and Predicate Pushdown

Suppose:

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
WHERE customer_id = $1;
```

An optimizer may be able to push the customer predicate toward the underlying table when the CTE is inlined.

This can dramatically reduce work.

Forced materialization may prevent such optimization.

---

## CTE and ORDER BY

Avoid adding unnecessary ordering inside intermediate CTEs:

```sql
WITH orders_sorted AS (
    SELECT *
    FROM orders
    ORDER BY created_at DESC
)
SELECT *
FROM orders_sorted;
```

The outer query does not necessarily inherit a meaningful ordering guarantee.

If final output ordering matters:

```sql
ORDER BY
```

should be specified in the final query.

Intermediate ordering should have a semantic purpose.

---

## CTE and LIMIT

Similarly:

```sql
WITH recent_orders AS (
    SELECT *
    FROM orders
    ORDER BY created_at DESC
    LIMIT 100
)
SELECT *
FROM recent_orders;
```

has clear semantics because `LIMIT` affects which rows enter the outer query.

But be careful when adding `LIMIT` merely to "make a query faster."

A limit can change correctness.

---

## CTE and Pagination

CTEs can help construct paginated result sets.

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
    customer_id,
    revenue
FROM customer_revenue
WHERE
    (revenue, customer_id) < ($1, $2)
ORDER BY
    revenue DESC,
    customer_id DESC
LIMIT 50;
```

This illustrates keyset-style pagination over an aggregated result.

The ordering tuple must match the pagination semantics.

---

## Recursive CTE

A recursive CTE references itself.

General structure:

```sql
WITH RECURSIVE cte_name AS (
    -- Anchor query
    SELECT ...

    UNION ALL

    -- Recursive query
    SELECT ...
    FROM cte_name
    ...
)
SELECT *
FROM cte_name;
```

Recursive CTEs are useful for hierarchical data.

Examples:

- Organization trees
- Category hierarchies
- Folder structures
- Dependency graphs
- Parent-child relationships

---

## Recursive CTE Structure

A recursive CTE has two logical components:

```text
Anchor
  ↓
initial rows
  ↓
recursive step
  ↓
new rows
  ↓
recursive step
  ↓
...
```

The recursion stops when the recursive term produces no additional rows or another limiting condition is reached.

---

## Organization Hierarchy Example

Suppose:

```text
CEO
├── Engineering
│   ├── Backend
│   └── Frontend
└── Sales
```

A recursive CTE can traverse the hierarchy.

Example:

```sql
WITH RECURSIVE org_tree AS (
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
        ot.depth + 1
    FROM employees AS e
    JOIN org_tree AS ot
        ON e.manager_id = ot.id
)
SELECT
    id,
    manager_id,
    name,
    depth
FROM org_tree
ORDER BY depth, id;
```

The anchor finds root employees.

The recursive term finds their direct reports.

---

## Recursive CTE With Paths

You can maintain a traversal path:

```sql
WITH RECURSIVE category_tree AS (
    SELECT
        id,
        parent_id,
        name,
        ARRAY[id] AS path
    FROM categories
    WHERE parent_id IS NULL

    UNION ALL

    SELECT
        c.id,
        c.parent_id,
        c.name,
        ct.path || c.id
    FROM categories AS c
    JOIN category_tree AS ct
        ON c.parent_id = ct.id
)
SELECT *
FROM category_tree;
```

The path can be useful for:

- Ordering
- Debugging
- Hierarchy representation
- Cycle detection

---

## Recursive CTE Depth

A production recursive query should consider maximum depth.

Example:

```sql
WITH RECURSIVE org_tree AS (
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
        ot.depth + 1
    FROM employees AS e
    JOIN org_tree AS ot
        ON e.manager_id = ot.id
    WHERE ot.depth < 50
)
SELECT *
FROM org_tree;
```

The depth limit is a safety mechanism, but it should not replace proper data integrity.

---

## Recursive CTE and Cycles

Hierarchical data can contain accidental cycles:

```text
A → B → C → A
```

A recursive query without cycle protection can repeatedly traverse the same nodes.

Use:

- Database constraints where possible
- Path tracking
- Explicit cycle detection
- Depth limits
- PostgreSQL recursive query features when appropriate

Do not assume production hierarchy data is always a valid tree.

---

## Recursive CTE vs Application Recursion

Application recursion may require:

```text
query parent
→ query children
→ query grandchildren
→ ...
```

This can create many database round trips.

A recursive CTE can move traversal into one SQL statement.

However, application-side traversal can still be preferable when:

- The graph spans multiple services
- Complex business logic is required at each node
- The hierarchy is small
- The data is already loaded
- The traversal needs external service calls

Choose based on workload and architecture.

---

## Recursive CTE and Graphs

Recursive CTEs can traverse graph-like data, but relational recursive queries are not automatically equivalent to specialized graph databases.

For very complex graph workloads involving:

- Massive traversal
- Shortest-path algorithms
- Centrality analysis
- Highly connected graphs

a specialized analytical or graph-oriented architecture may be more appropriate.

---

## CTE With INSERT

PostgreSQL allows CTEs before data-modification statements.

Example:

```sql
WITH eligible_customers AS (
    SELECT id
    FROM customers
    WHERE status = 'active'
)
INSERT INTO customer_notifications (
    customer_id,
    notification_type
)
SELECT
    id,
    'monthly_summary'
FROM eligible_customers;
```

The CTE provides a clean selection stage.

---

## Data-Modifying CTE

PostgreSQL supports data-modifying statements inside CTEs.

Example:

```sql
WITH archived AS (
    DELETE FROM orders
    WHERE created_at < $1
    RETURNING id, customer_id
)
INSERT INTO archived_orders (
    order_id,
    customer_id
)
SELECT
    id,
    customer_id
FROM archived;
```

This can perform related operations as one statement.

The `RETURNING` clause exposes rows affected by the data-modifying CTE.

---

## Data-Modifying CTE and Transactions

A data-modifying CTE participates in the same statement and transaction context.

This can be powerful for atomic workflows.

However, it should not be confused with independent sequential execution where later statements necessarily observe intermediate effects in the same way procedural code would.

When correctness depends on interaction between multiple modifications, understand PostgreSQL's statement and snapshot semantics.

---

## CTE and RETURNING

PostgreSQL's `RETURNING` can be combined with CTEs:

```sql
WITH inserted_orders AS (
    INSERT INTO orders (
        customer_id,
        total_amount
    )
    VALUES ($1, $2)
    RETURNING id, customer_id
)
INSERT INTO order_events (
    order_id,
    event_type
)
SELECT
    id,
    'created'
FROM inserted_orders;
```

This is useful for database-side workflows where generated IDs must be passed to a subsequent operation.

---

## CTE and Transactional Outbox

A carefully designed SQL statement can sometimes combine data creation and event-row creation.

Conceptually:

```text
transaction
    ├── business row
    └── outbox row
```

The important architectural property is that both are committed atomically.

For complex workflows, however, keep transaction boundaries and failure semantics explicit rather than turning a CTE into an unreadable procedural program.

---

## CTE and Migrations

CTEs can be useful during controlled migrations:

```sql
WITH affected_rows AS (
    SELECT id
    FROM orders
    WHERE processed_at IS NULL
    ORDER BY id
    LIMIT 5000
)
UPDATE orders AS o
SET processed_at = created_at
FROM affected_rows AS a
WHERE o.id = a.id;
```

This can define a bounded batch.

For very large tables, still consider:

- Lock duration
- WAL generation
- Vacuum pressure
- Replica lag
- Batch size
- Retry behavior
- Transaction duration

A CTE does not automatically make a migration safe.

---

## CTE for Batch Processing

A PostgreSQL pattern using `FOR UPDATE SKIP LOCKED`:

```sql
WITH batch AS (
    SELECT id
    FROM jobs
    WHERE status = 'pending'
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 100
)
UPDATE jobs AS j
SET status = 'processing'
FROM batch
WHERE j.id = batch.id
RETURNING j.id;
```

This can support queue-like worker coordination.

Important production considerations include:

- Short transactions
- Worker limits
- Retry semantics
- Idempotency
- Fairness/starvation
- Lock contention
- Failure recovery

---

## CTE and DELETE Batching

For large deletes:

```sql
WITH batch AS (
    SELECT id
    FROM audit_logs
    WHERE created_at < $1
    ORDER BY id
    LIMIT 5000
)
DELETE FROM audit_logs AS a
USING batch
WHERE a.id = batch.id;
```

This is generally safer than one enormous delete.

Run batches in separate transactions when appropriate.

---

## CTE and OFFSET

Avoid using repeated large offsets for batch processing:

```sql
OFFSET 500000
LIMIT 5000
```

The database may need to walk through many preceding rows.

Prefer keyset progression:

```sql
WHERE id > $last_id
ORDER BY id
LIMIT 5000;
```

A CTE can then define the bounded batch.

---

## CTE and ORM

Django's core ORM historically has not provided a general-purpose CTE abstraction comparable to raw SQL, although ecosystem packages and newer ORM capabilities may vary by version.

When a query genuinely requires complex CTE behavior:

- Evaluate whether ORM composition is sufficient
- Consider a database view
- Use carefully parameterized raw SQL
- Isolate the SQL behind a repository/service boundary
- Add integration tests

Do not force an unreadable ORM query when SQL is the clearer abstraction.

---

## SQLAlchemy and CTEs

SQLAlchemy provides CTE support:

```python
from sqlalchemy import select

customer_totals = (
    select(
        Order.customer_id,
        func.sum(Order.total_amount).label("revenue"),
    )
    .group_by(Order.customer_id)
    .cte("customer_totals")
)

stmt = select(customer_totals).where(
    customer_totals.c.revenue > 10000
)
```

The generated SQL should still be evaluated as SQL, not just as ORM/API syntax.

---

## CTEs in Backend Services

A backend API might need:

```text
active customers
    ↓
customer revenue
    ↓
ranking
    ↓
top customers
    ↓
API response
```

A CTE can express these stages in one query.

Benefits include:

- One database round trip
- Database-side computation
- Clear query structure
- Reduced application-side processing

But large reports may still belong in asynchronous jobs or OLAP infrastructure.

---

## CTEs and N+1 Queries

A complex CTE can consolidate work that would otherwise require multiple application queries.

Bad:

```text
query customers
→ query orders
→ query metrics
→ query ranking
```

Potentially better:

```text
one SQL statement
→ CTE pipeline
→ final result
```

This does not mean every multi-query workflow should become one giant SQL statement.

If a query becomes too complex to maintain or causes excessive database resource usage, separate stages or precomputed read models may be better.

---

## CTEs and Microservices

CTEs cannot cross independent service database boundaries.

If:

```text
Service A → Database A
Service B → Database B
```

a CTE in Database A cannot simply query Database B.

Cross-service reporting should generally use:

- Events
- Kafka
- CDC
- Data warehouse
- Materialized read models
- Explicit service APIs

Database-level CTEs operate within the database environment available to the statement.

---

## CTEs and Redis

Redis can cache the final result of an expensive CTE-based query.

Example:

```text
API
 ↓
Redis
 ↓ miss
PostgreSQL CTE query
 ↓
Redis
 ↓
API
```

But caching does not solve an incorrect or inefficient SQL query.

First validate:

- Correctness
- Query plan
- Freshness requirements
- Cache invalidation
- Tenant isolation

---

## CTEs and Kafka

For high-volume aggregation, Kafka may move computation away from transactional SQL:

```text
transactional service
      ↓
Kafka
      ↓
consumer
      ↓
aggregate/read model
      ↓
API
```

A CTE is appropriate when the data can be efficiently queried from the relational database.

Kafka-based projections become more attractive when repeated large scans are the real bottleneck.

---

## CTEs and OLAP

CTEs are common in analytical SQL:

```text
raw data
  ↓
filter
  ↓
aggregate
  ↓
join dimensions
  ↓
calculate metrics
  ↓
final report
```

For very large analytical workloads, however, the database engine, storage format, partitioning, and execution model matter more than whether the SQL uses CTEs.

A CTE does not turn an OLTP database into an OLAP system.

---

## Security Considerations

CTEs do not change the basic SQL security rules.

Use parameterized values:

```sql
WITH eligible_orders AS (
    SELECT id
    FROM orders
    WHERE customer_id = $1
)
SELECT *
FROM eligible_orders;
```

Avoid constructing SQL by string interpolation.

Also enforce:

- Tenant isolation
- Authorization
- Least-privilege database roles
- RLS where appropriate
- Safe dynamic SQL rules

Nested query structure does not provide security by itself.

---

## Multi-Tenant CTEs

A tenant-scoped CTE should preserve the tenant boundary.

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

If PostgreSQL RLS is used, understand how the executing role and tenant context affect every referenced table.

Do not assume a CTE creates an authorization boundary.

---

## CTE and Connection Pooling

CTE execution occurs within the database connection executing the SQL statement.

Long-running CTE queries can therefore occupy pooled connections.

If:

```text
10 connections
+
10 expensive CTE reports
=
no capacity for API traffic
```

the problem is architectural, not just SQL syntax.

Separate reporting workloads when necessary.

---

## CTE and Timeouts

For expensive CTE queries, configure appropriate database and application timeouts.

Examples include:

```text
request timeout
query timeout
statement_timeout
connection acquisition timeout
```

A timeout should prevent runaway analytical queries from consuming database resources indefinitely.

Do not solve query overload by simply increasing timeouts.

---

## CTE and Locking

Data-modifying CTEs can acquire locks like other DML operations.

For example:

```sql
WITH batch AS (
    SELECT id
    FROM jobs
    WHERE status = 'pending'
    FOR UPDATE SKIP LOCKED
    LIMIT 100
)
UPDATE jobs AS j
SET status = 'processing'
FROM batch
WHERE j.id = batch.id;
```

Production concerns include:

- Lock duration
- Transaction boundaries
- Worker concurrency
- Deadlocks
- Lock waits
- Retry behavior

---

## CTE and Replicas

A read-only CTE query executed against a PostgreSQL read replica can be useful for reporting.

But remember:

```text
Primary
  ↓ WAL
Replica
  ↓
CTE query
```

The replica may lag.

Therefore aggregate results may be stale.

Do not route consistency-sensitive business decisions to a lagging replica merely because the query is read-only.

---

## CTE and Replication Load

A large CTE query on a primary can generate significant resource consumption and indirectly affect replication.

Heavy reporting can consume:

- CPU
- Memory
- I/O
- Connections

For production analytics, consider:

- Read replicas
- Materialized views
- OLAP systems
- Precomputed read models

---

## CTE Performance Checklist

For an expensive CTE query, inspect:

- CTE materialization behavior
- Predicate pushdown
- Cardinality
- Join strategy
- Aggregation strategy
- Sorts
- Hash memory
- Temporary I/O
- Index usage
- Partition pruning
- Query frequency
- Concurrent executions

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

rather than guessing.

---

## Common CTE Mistakes

### Assuming Every CTE Is Materialized

Modern PostgreSQL can inline eligible non-recursive CTEs.

### Assuming CTEs Are Always Faster

A CTE improves structure, not necessarily execution speed.

### Using CTEs Everywhere

Simple queries can become unnecessarily verbose.

### Materializing Huge Intermediate Results

Forced materialization can increase memory and I/O.

### Ignoring Predicate Pushdown

A poorly structured or forced-materialized CTE can process far more rows than required.

### Using CTEs to Hide Bad Joins

A CTE does not fix incorrect cardinality.

### Recursive CTE Without Cycle Protection

Hierarchy corruption can cause excessive recursion.

### Using One Giant CTE for Business Logic

Complex application rules can become difficult to test and maintain.

### Using CTEs for Cross-Service Queries

Independent service databases require an architectural integration mechanism.

### Assuming CTEs Are Temporary Tables

A CTE is statement-scoped and does not provide an independently indexed intermediate object.

---

## Interview Traps

### What Is a CTE?

A named query expression defined with `WITH` and used within a SQL statement.

---

### Why Use a CTE?

Primarily to structure complex SQL into readable logical stages.

It can also support:

- Recursive queries
- Multi-stage transformations
- Data-modifying workflows
- Reusable intermediate results within a statement

---

### Is a CTE the Same as a Temporary Table?

No.

A CTE is statement-scoped.

A temporary table is a database object with session/transaction scope and can have indexes.

---

### Is a CTE Always Materialized?

No.

In modern PostgreSQL, eligible non-recursive CTEs can often be inlined.

`MATERIALIZED` can explicitly request materialization.

---

### Are CTEs Faster Than Subqueries?

Not inherently.

They are primarily a readability and query-composition mechanism.

Execution depends on the optimizer and query structure.

---

### What Is a Recursive CTE?

A CTE that references itself to recursively traverse hierarchical or graph-like data.

---

### What Are the Two Parts of a Recursive CTE?

Typically:

```text
anchor query
+
recursive query
```

combined with:

```sql
UNION ALL
```

---

### What Happens if a Recursive CTE Has a Cycle?

It can repeatedly revisit nodes and potentially consume substantial resources.

Use data integrity, cycle detection, path tracking, or depth limits as appropriate.

---

### Can a CTE Perform INSERT, UPDATE, or DELETE?

PostgreSQL supports data-modifying statements inside CTEs.

---

### Can a CTE Return Rows From an UPDATE?

Yes, using `RETURNING`.

Example:

```sql
WITH updated AS (
    UPDATE orders
    SET status = 'processed'
    WHERE id = $1
    RETURNING id
)
SELECT *
FROM updated;
```

---

### What Is MATERIALIZED?

In PostgreSQL:

```sql
WITH x AS MATERIALIZED (...)
```

requests that the CTE result be materialized rather than freely inlined.

---

### What Is NOT MATERIALIZED?

It requests that PostgreSQL treat the CTE more like an inline subquery when possible.

---

### Can a CTE Be Referenced Multiple Times?

Yes.

Whether repeated use benefits from materialization depends on the query and execution plan.

---

### Does a CTE Guarantee Execution Order?

No.

SQL describes relational semantics, and the optimizer determines the physical execution strategy.

Do not treat CTE ordering as procedural execution ordering unless the SQL semantics explicitly require it.

---

## Practical Interview Problems

### Find Customers With Revenue Above the Average Customer Revenue

```sql
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
WHERE revenue > (
    SELECT AVG(revenue)
    FROM customer_revenue
);
```

This demonstrates:

- CTE
- Aggregation
- Scalar subquery
- Multi-level aggregation

---

### Find the Top Three Orders Per Customer

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE rn <= 3;
```

---

### Find Latest Order Per Customer

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;
```

---

### Aggregate Before Joining

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
)
SELECT
    c.id,
    c.name,
    COALESCE(cr.revenue, 0) AS revenue
FROM customers AS c
LEFT JOIN customer_revenue AS cr
    ON cr.customer_id = c.id;
```

---

### Batch Process Jobs

```sql
WITH batch AS (
    SELECT id
    FROM jobs
    WHERE status = 'pending'
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 100
)
UPDATE jobs AS j
SET status = 'processing'
FROM batch
WHERE j.id = batch.id
RETURNING j.id;
```

---

### Traverse an Employee Hierarchy

```sql
WITH RECURSIVE org_tree AS (
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
        ot.depth + 1
    FROM employees AS e
    JOIN org_tree AS ot
        ON e.manager_id = ot.id
)
SELECT *
FROM org_tree;
```

---

## CTE Debugging Workflow

When a complex CTE query returns incorrect results:

### Test Each CTE Independently

Run:

```sql
WITH customer_revenue AS (
    ...
)
SELECT *
FROM customer_revenue
LIMIT 100;
```

Validate:

- Row count
- Grain
- Null behavior
- Duplicate rows
- Expected values

### Validate Each Join

Check cardinality before and after joins.

### Validate Aggregates

Confirm that measures are calculated at the intended grain.

### Check Recursive Termination

For recursive CTEs, verify:

- Base case
- Recursive condition
- Depth
- Cycles

### Inspect the Final Execution Plan

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

---

## Senior-Level CTE Reasoning

A strong interview answer should distinguish three separate questions:

### Is the Query Correct?

Check:

```text
grain
joins
NULL
filters
recursion
authorization
```

### Is the Query Maintainable?

Check:

```text
CTE naming
logical stages
duplication
business-rule complexity
ORM integration
```

### Is the Query Efficient?

Check:

```text
cardinality
materialization
predicate pushdown
indexes
aggregation
sort/hash memory
temporary I/O
concurrency
```

A readable CTE can still be an expensive query.

A fast query can still be unreadable.

Senior engineering requires balancing both.

---

## Production Architecture Example

A reporting endpoint might use:

```text
REST API
    ↓
Django / FastAPI
    ↓
connection pool
    ↓
PostgreSQL
    ↓
CTE pipeline
    ├── filter transactions
    ├── aggregate customers
    ├── rank results
    └── construct response
    ↓
API response
```

For moderate workloads, this can be a clean architecture.

For high-volume analytics:

```text
Application
    ↓
Kafka / CDC
    ↓
Analytics pipeline
    ↓
OLAP / warehouse
    ↓
precomputed metrics
    ↓
API
```

The second architecture avoids repeatedly executing expensive analytical CTEs against the transactional database.

---

## Production Checklist

Before shipping a complex CTE:

- [ ] Each CTE has a clearly defined purpose.
- [ ] CTE names describe the intermediate result.
- [ ] Result grain is documented mentally or explicitly.
- [ ] Joins do not introduce unintended duplication.
- [ ] `NULL` behavior is intentional.
- [ ] Recursive CTEs have termination and cycle considerations.
- [ ] Materialization behavior is understood.
- [ ] `MATERIALIZED` is used only intentionally.
- [ ] `NOT MATERIALIZED` is used only when its optimization effect is understood.
- [ ] Predicate pushdown has been considered.
- [ ] Indexes support important filtering and join paths.
- [ ] Aggregation memory and temporary I/O are understood.
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` has been reviewed for expensive queries.
- [ ] Query frequency and concurrency are understood.
- [ ] Long-running CTEs do not monopolize API connection pools.
- [ ] Tenant isolation and authorization are preserved.
- [ ] Read-replica consistency is acceptable if replicas are used.
- [ ] Heavy analytics are isolated from OLTP when necessary.
- [ ] ORM-generated SQL is validated when CTE logic is hidden behind application abstractions.

---

## Key Takeaways

- **CTEs are primarily a query-composition tool:** use them to create clear logical stages, not because a `WITH` clause is inherently faster than a subquery.
- **Modern PostgreSQL can inline eligible CTEs:** understand `MATERIALIZED`, `NOT MATERIALIZED`, predicate pushdown, and actual execution plans instead of relying on outdated "CTEs are optimization fences" rules.
- **Recursive CTEs require correctness safeguards:** define a clear anchor, termination condition, depth strategy, and cycle handling for hierarchical or graph-like data.
- **CTEs do not eliminate relational problems:** grain, join cardinality, `NULL` semantics, indexing, memory, locking, and transaction behavior still determine correctness and performance.
- **Senior CTE design considers the whole backend system:** connection pools, replicas, Django/FastAPI integration, tenant isolation, asynchronous processing, OLAP separation, observability, and workload scale all influence whether a CTE is the right production solution.