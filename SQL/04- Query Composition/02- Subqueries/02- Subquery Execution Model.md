# 02- Subquery Execution Model

## Overview

A subquery is a query nested inside another SQL statement, but its **execution model is determined by the database optimizer**, not simply by the textual nesting of the SQL.

A common beginner mental model is:

```text
Run outer query
    ↓
For every outer row:
    ↓
Run inner query
```

That model is sometimes useful for understanding **correlated subquery semantics**, but it is not a reliable description of physical execution. Modern relational databases can transform subqueries into joins, semi-joins, anti-joins, aggregates, index lookups, or other execution strategies.

For backend engineers, the important distinction is:

> **SQL describes relational intent; the optimizer chooses the physical execution strategy.**

Understanding this distinction is essential when diagnosing slow queries, choosing between `JOIN`, `EXISTS`, `IN`, and subqueries, and reading execution plans.

## Logical Query Processing vs Physical Execution

There are two different concepts to keep separate.

### Logical Query Processing

Logical processing describes what the query means.

For example:

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

Logically:

1. Consider rows from `users`.
2. For each user, determine whether a matching order exists.
3. Keep users for which the condition is true.
4. Return the selected columns.

### Physical Execution

The database can implement the same logic using a different plan.

Possible strategies include:

- Nested-loop execution.
- Hash-based execution.
- Index scans.
- Bitmap scans.
- Semi-joins.
- Anti-joins.
- Materialization.
- Aggregation.
- Parallel execution.

The optimizer considers factors such as:

- Table cardinality.
- Predicate selectivity.
- Available indexes.
- Column statistics.
- Join selectivity.
- Estimated cost.
- Memory availability.
- Database configuration.

Therefore, never infer performance solely from the SQL's visual nesting.

## Uncorrelated Subquery Execution

An **uncorrelated subquery** does not reference the outer query.

Example:

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

The inner query is independent of the current product.

Conceptually:

```text
products
   │
   ├───────────────┐
   │               │
   ▼               ▼
outer rows      AVG(price)
   │               │
   └───────┬───────┘
           ▼
      comparison
           │
           ▼
   qualifying products
```

A useful logical model is:

```text
1. Calculate AVG(price)
2. Compare each product against that value
```

But the physical plan may calculate the aggregate once, scan the table in another way, or optimize the expression into an equivalent plan.

### Why This Matters

An uncorrelated scalar subquery often does **not** imply repeated execution for every outer row.

This query:

```sql
WHERE price > (SELECT AVG(price) FROM products)
```

should not automatically be rewritten just because someone assumes `AVG()` executes once per product.

Inspect the execution plan first.

## Correlated Subquery Execution

A **correlated subquery** references a value from the outer query.

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.status = 'completed'
);
```

The reference:

```sql
o.user_id = u.id
```

connects the inner query to the current outer row.

The logical model is:

```text
User
  │
  ▼
Find matching completed order
  │
  ├── exists → keep user
  └── absent → discard user
```

A naive physical model would be:

```text
users
  │
  ├── user A → execute subquery
  ├── user B → execute subquery
  ├── user C → execute subquery
  └── ...
```

However, the optimizer may transform the query into a semi-join or another strategy.

## Semi-Join Execution

`EXISTS` is naturally associated with **semi-join semantics**.

A semi-join returns rows from the left relation when at least one matching row exists on the right.

For example:

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

The result contains users, not orders.

If a user has 100 matching orders, the user still appears once.

```text
users                  orders
─────                  ──────
user 1 ──────────────> order 1
                     > order 2
                     > order 3
                     > ...
                     > order 100

Result:
user 1
```

This differs from a regular JOIN:

```sql
SELECT
    u.id,
    u.email
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

The JOIN can produce 100 rows for that user.

This is one reason `EXISTS` is often the better expression when the requirement is purely existence.

## Anti-Join Execution

`NOT EXISTS` expresses anti-join semantics.

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

The requirement is:

> Return users for whom no matching order exists.

Conceptually:

```text
users
  │
  ├── matching order → reject
  └── no matching order → keep
```

Database engines can implement this using an anti-join or another equivalent strategy.

## `IN` Subquery Execution

Consider:

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE u.id IN (
    SELECT o.user_id
    FROM orders AS o
    WHERE o.status = 'completed'
);
```

Logically, the inner query produces a set:

```text
completed order user IDs
        │
        ▼
       IN
        │
        ▼
matching users
```

The optimizer may transform this into a semi-join-like plan.

Therefore, the assumption:

> "`IN` always creates a temporary list in memory."

is incorrect.

The actual execution strategy depends on the optimizer and database engine.

## Scalar Subquery Execution

A scalar subquery returns one value.

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

The subquery has a cardinality requirement:

```text
0 or 1 value
```

An aggregate such as `AVG()` naturally produces one row, although its value can be `NULL` if there are no applicable rows.

A scalar subquery returning multiple rows is an error in PostgreSQL:

```sql
SELECT (
    SELECT id
    FROM users
);
```

The problem is not merely performance; it is invalid scalar cardinality.

## Derived Table Execution

A subquery in `FROM` creates a derived relation.

```sql
SELECT
    customer_id,
    order_count
FROM (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) AS customer_orders;
```

The logical processing is:

```text
orders
  │
  ▼
GROUP BY customer_id
  │
  ▼
derived relation
  │
  ▼
outer query
```

The database does not necessarily materialize the entire derived table as a physical temporary table.

The optimizer can often integrate the derived relation into the broader execution plan.

## Materialization

**Materialization** means producing and storing an intermediate result so that it can be consumed by another part of the execution plan.

Conceptually:

```text
Subquery
   │
   ▼
Intermediate result
   │
   ▼
Materialize
   │
   ▼
Outer operation
```

Materialization can be useful when:

- An intermediate result is reused.
- Recomputing it would be expensive.
- The optimizer determines that storing it is cheaper.
- The query structure requires a materialized boundary.

But materialization can also introduce:

- Memory usage.
- Temporary disk I/O.
- Additional processing.
- Larger execution latency.

Do not assume every subquery is materialized.

## Optimizer Transformations

A cost-based optimizer can transform logically equivalent SQL into different physical plans.

For example:

```sql
SELECT
    u.id
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

may conceptually become:

```text
Users
  │
  ▼
Semi Join
  ▲
  │
Orders
```

Similarly:

```sql
WHERE NOT EXISTS (...)
```

may become an anti-join.

This is why experienced SQL engineers reason in terms of **query semantics and execution plans**, rather than SQL syntax alone.

## Nested Loop Execution

A nested-loop strategy processes one relation and looks for matching rows in another relation.

Conceptually:

```text
Outer relation
     │
     ▼
for each outer row
     │
     ▼
find matching inner rows
```

For a correlated predicate such as:

```sql
o.user_id = u.id
```

an index on the inner relation can make this strategy efficient.

For example:

```sql
CREATE INDEX idx_orders_user_id
    ON orders (user_id);
```

The conceptual cost can then resemble:

```text
Scan users
   │
   ├── index lookup orders for user 1
   ├── index lookup orders for user 2
   ├── index lookup orders for user 3
   └── ...
```

This can work well when:

- The outer relation is relatively small.
- The inner lookup is highly selective.
- An appropriate index exists.

It can perform poorly when:

- The outer relation is huge.
- Inner lookups are expensive.
- The predicate has poor selectivity.
- Required indexes are missing.

## Hash-Based Execution

For larger datasets, a database may prefer a hash-based strategy.

Conceptually:

```text
Build hash structure
        │
        ▼
     orders
        │
        ▼
   hash on user_id
        │
        ▼
Probe with users
```

Hash-based execution can be efficient for large equality-based operations, but it requires memory for the hash structure.

If memory is insufficient, the database may spill intermediate data to temporary storage, increasing latency.

## Index-Driven Subquery Execution

Consider:

```sql
SELECT
    u.id
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.status = 'completed'
);
```

A useful index candidate may be:

```sql
CREATE INDEX idx_orders_user_status
    ON orders (user_id, status);
```

The database can potentially locate matching rows efficiently for each user.

For PostgreSQL workloads where completed orders are a small and stable subset, a partial index may be appropriate:

```sql
CREATE INDEX idx_orders_completed_user
    ON orders (user_id)
    WHERE status = 'completed';
```

The correct choice depends on:

- Data distribution.
- Query frequency.
- Write volume.
- Status distribution.
- Existing indexes.
- Actual execution plans.

## `EXPLAIN` Is the Source of Truth

When query performance matters, inspect the execution plan.

For PostgreSQL:

```sql
EXPLAIN
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.status = 'completed'
);
```

For production performance analysis, use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
      AND o.status = 'completed'
);
```

`EXPLAIN` shows the optimizer's intended plan.

`EXPLAIN ANALYZE` actually executes the query and reports runtime information.

Use caution with `EXPLAIN ANALYZE` on expensive production queries because it executes the statement.

## Reading a Subquery Execution Plan

Pay attention to:

| Plan characteristic | What it tells you |
|---|---|
| Estimated rows | Optimizer's expected cardinality |
| Actual rows | Rows actually processed |
| Loops | Number of executions of a plan node |
| Index Scan | Index-based access was selected |
| Sequential Scan | Table scan was selected |
| Nested Loop | Repeated lookup strategy |
| Hash Join | Hash-based join strategy |
| Buffers | Memory/cache and I/O behavior |
| Sort | Sorting work |
| Temporary I/O | Possible spill or intermediate storage pressure |

A particularly important signal is the difference between:

```text
estimated rows
```

and:

```text
actual rows
```

Large estimation errors can lead the optimizer to choose a poor plan.

## Correlation and Loop Counts

Consider:

```sql
SELECT
    u.id
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

If an execution plan contains a node with a large:

```text
loops
```

value, investigate whether a correlated operation is being repeatedly executed.

However, do not conclude:

> "High loops means the query is bad."

A highly efficient index lookup executed many times can still be faster than a large scan.

The important question is:

> **How expensive is each loop, and how much total work does the plan perform?**

## Cardinality Estimation

Cardinality is the number of rows produced by a relation or operation.

For subqueries, cardinality strongly affects optimizer decisions.

Suppose:

```text
users = 10 million rows
orders = 500 million rows
```

If only 100 users have completed orders, an execution strategy optimized for high selectivity may be ideal.

If 9.9 million users have completed orders, a different strategy may be cheaper.

This is why the same SQL query can perform differently as data distributions change.

Production performance is therefore a function of both:

```text
Query shape
+
Data distribution
+
Indexes
+
Statistics
+
Database configuration
```

## Statistics and Plan Quality

Cost-based optimizers depend on statistics to estimate cardinality.

When statistics are stale or insufficiently representative, the optimizer can make poor decisions.

Typical symptoms include:

- Unexpected sequential scans.
- Poor join ordering.
- Excessive nested-loop execution.
- Incorrect row estimates.
- Unexpected temporary I/O.

For PostgreSQL, routine maintenance such as `ANALYZE` helps keep statistics current.

Autovacuum normally handles much of this automatically, but high-volume or unusual workloads may require monitoring and tuning.

## Subquery Caching and Reuse

Do not assume that a database caches every subquery result.

Whether an expression is:

- evaluated once,
- evaluated repeatedly,
- materialized,
- transformed,
- or integrated into another operation

depends on the optimizer and execution plan.

For example, this uncorrelated expression:

```sql
SELECT
    p.id,
    p.price
FROM products AS p
WHERE p.price > (
    SELECT AVG(price)
    FROM products
);
```

has no dependency on the current `p` row, so the optimizer has opportunities to avoid redundant work.

By contrast, a correlated expression has dependencies that may require more complex execution.

The plan—not the source-code appearance—is what matters.

## `EXISTS` and Early Termination

One useful property of existence predicates is that the database only needs to establish whether a match exists.

For:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

once a qualifying order has been found, there is no semantic need to count all matching orders.

An appropriate plan can therefore avoid unnecessary work.

This is one reason `EXISTS` is preferable when the application needs a boolean existence test rather than related row data.

## Subqueries and `NULL`

Subquery semantics interact with SQL's three-valued logic.

Consider:

```sql
WHERE id NOT IN (
    SELECT user_id
    FROM orders
);
```

If the subquery returns `NULL`, the behavior of `NOT IN` can be surprising.

For example:

```text
id NOT IN (10, 20, NULL)
```

cannot establish that an arbitrary non-matching ID is definitely different from `NULL`.

For absence checks, prefer:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

This expresses the intended relational condition directly.

## Subquery Execution and JOIN Equivalence

Many subqueries have equivalent JOIN formulations.

For example:

```sql
SELECT
    u.id
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

could be represented using:

```sql
SELECT DISTINCT
    u.id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

The optimizer may produce similar execution strategies, but the semantics are expressed differently.

`EXISTS` communicates:

```text
I only care whether a matching row exists.
```

JOIN communicates:

```text
I am combining rows from two relations.
```

Use the construct that represents the business requirement most directly.

## Subqueries and CTEs

A CTE can make multi-stage query logic easier to understand:

```sql
WITH completed_orders AS (
    SELECT
        user_id
    FROM orders
    WHERE status = 'completed'
)
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM completed_orders AS co
    WHERE co.user_id = u.id
);
```

However, CTEs should not automatically be considered optimization boundaries.

Modern database engines can inline or otherwise optimize CTEs depending on their semantics and version.

If a CTE is explicitly materialized where the database supports that behavior:

```sql
WITH completed_orders AS MATERIALIZED (
    SELECT
        user_id
    FROM orders
    WHERE status = 'completed'
)
SELECT ...
```

the execution characteristics can change significantly.

Use materialization intentionally, not as a generic performance optimization.

## ORM Execution Model

ORMs can generate subqueries without making the SQL obvious in application code.

Django provides explicit support for `Exists`:

```python
from django.db.models import Exists, OuterRef

completed_orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
    status="completed",
)

customers = (
    Customer.objects
    .annotate(
        has_completed_order=Exists(completed_orders),
    )
    .filter(has_completed_order=True)
)
```

The ORM expresses the relationship at the application layer, while the database optimizer determines the physical execution.

For performance-sensitive endpoints, inspect the generated SQL and database plan.

A useful debugging workflow is:

```text
ORM expression
      │
      ▼
Generated SQL
      │
      ▼
EXPLAIN
      │
      ▼
Actual execution behavior
```

Do not optimize ORM syntax without understanding the SQL it generates.

## Production Performance Considerations

Subquery performance should be evaluated under realistic conditions.

Consider:

- Production-like row counts.
- Realistic data skew.
- Current indexes.
- Concurrent workload.
- Database memory.
- Connection pool size.
- Cache state.
- Query frequency.
- Read/write ratio.

A query that runs in 10 ms on a development database with 10,000 rows may behave very differently against hundreds of millions of production rows.

### Indexes

Index correlated predicates and frequently filtered columns when justified by workload.

### Selectivity

Highly selective predicates can make index-driven execution effective.

### Result Grain

Use `EXISTS` when you need one parent row regardless of child-row count.

### Query Plans

Measure before rewriting.

### Statistics

Monitor whether row estimates remain representative as data changes.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Assuming a subquery always runs once per outer row | Confusing logical semantics with physical execution | Inspect the execution plan |
| Assuming `IN` always materializes a list | Treating SQL syntax as implementation | Check the optimizer's chosen plan |
| Assuming every subquery is materialized | Confusing derived relations with temporary tables | Verify the plan |
| Rewriting every subquery as a JOIN | Following simplistic optimization advice | Preserve intended result semantics |
| Assuming `EXISTS` is always faster | Treating query patterns as universal rules | Benchmark and inspect plans |
| Ignoring correlated predicates | Missing the relationship between outer and inner queries | Check correlation and indexes |
| Ignoring cardinality | Optimizing without understanding data volume | Inspect estimated and actual rows |
| Trusting development performance | Testing against unrealistic datasets | Benchmark production-like data |
| Using `NOT IN` without considering NULL | Missing three-valued logic | Prefer `NOT EXISTS` for absence checks |
| Adding indexes without measuring | Assuming every index improves performance | Validate with workload and execution plans |

## Interview Traps

### "Does a correlated subquery always execute once per outer row?"

No.

That is a useful **logical mental model**, but the optimizer can transform correlated subqueries into joins or other strategies.

### "Are JOINs always faster than subqueries?"

No.

The database optimizer can transform equivalent query forms into similar physical plans. Performance depends on the specific query, data distribution, indexes, statistics, and database engine.

### "Does `EXISTS` scan every matching row?"

Not necessarily.

The logical requirement is only to establish whether at least one matching row exists. The optimizer can use an execution strategy that avoids unnecessary work.

### "Does a subquery always create a temporary table?"

No.

A subquery is a logical query expression. Materialization is a possible physical strategy, not an inherent property of subqueries.

### "Should I optimize based on SQL text?"

Not for serious performance work.

Use SQL text to understand intent, then use `EXPLAIN` and runtime metrics to understand physical behavior.

## Production Troubleshooting Workflow

When a subquery becomes slow:

1. Capture the exact SQL generated by the application.
2. Run `EXPLAIN` to inspect the chosen plan.
3. Run `EXPLAIN ANALYZE` in a safe environment when runtime measurements are required.
4. Compare estimated and actual row counts.
5. Inspect loops and expensive plan nodes.
6. Check whether correlated predicates have useful indexes.
7. Check for sequential scans over unexpectedly large relations.
8. Review sort, hash, and temporary I/O operations.
9. Validate database statistics.
10. Compare equivalent `EXISTS`, `JOIN`, CTE, or window-function formulations.
11. Benchmark against production-like data and concurrency.
12. Only then change the query or indexing strategy.

## Operational Monitoring

For production systems, query optimization should be observable rather than reactive.

Useful metrics include:

- Query latency percentiles.
- Query execution frequency.
- Rows returned.
- Rows examined.
- Buffer/cache activity.
- Temporary disk usage.
- Database CPU.
- Database memory pressure.
- Lock wait time.
- Connection pool saturation.

PostgreSQL environments can use facilities such as `pg_stat_statements` to identify expensive or frequently executed queries.

A query consuming only a small amount of time individually can still become a major production problem if it executes tens of thousands of times per minute.

## Reliability and Scalability

Subquery performance becomes a reliability concern when query cost grows with application traffic.

A backend endpoint might execute:

```text
10 requests/second
    ×
20 database queries/request
    =
200 queries/second
```

If one query contains an expensive correlated operation, database CPU and I/O can become the bottleneck before the application servers are saturated.

Production design should therefore consider:

- Query frequency.
- Dataset growth.
- Index maintenance.
- Connection pool pressure.
- Read replicas where appropriate.
- Caching for stable derived data.
- Precomputed aggregates for reporting workloads.
- Pagination and bounded result sets.

Read replicas can reduce primary database read load, but they do not make an inefficient query inherently efficient. Query shape and indexing still matter.

## Security Considerations

Subquery execution does not change the need for secure query construction.

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT id
    FROM users
    WHERE id IN (
        SELECT user_id
        FROM orders
        WHERE status = %s
    )
    """,
    ["completed"],
)
```

Avoid constructing SQL dynamically from untrusted input.

For multi-tenant systems, ensure authorization predicates apply consistently to both outer and inner relations where required.

For example:

```sql
SELECT
    u.id
FROM users AS u
WHERE u.tenant_id = :tenant_id
  AND EXISTS (
      SELECT 1
      FROM orders AS o
      WHERE o.user_id = u.id
        AND o.tenant_id = :tenant_id
  );
```

The database should enforce tenant isolation with constraints and, where appropriate, database-level security mechanisms rather than relying solely on application conventions.

## Senior-Level Mental Model

A robust mental model for subquery execution has four layers:

```text
SQL text
   │
   ▼
Logical semantics
   │
   ▼
Optimizer transformations
   │
   ▼
Physical execution plan
   │
   ▼
Runtime behavior
```

Each layer answers a different question:

| Layer | Question |
|---|---|
| SQL text | What did the application request? |
| Logical semantics | What result does the query mean? |
| Optimizer | Which equivalent strategy appears cheapest? |
| Execution plan | How will the database physically execute it? |
| Runtime | What actually happened under real data and load? |

Senior-level SQL optimization happens primarily by connecting these layers rather than reasoning from syntax alone.

## Key Takeaways

- **A subquery's textual nesting describes logical semantics, not necessarily physical execution; the optimizer can transform it into joins, semi-joins, anti-joins, aggregates, or other strategies.**
- **Correlated subqueries reference outer-row values, but they do not automatically imply one expensive inner query execution per outer row.**
- **Cardinality, indexes, statistics, selectivity, memory, and data distribution strongly influence the physical execution strategy.**
- **Use `EXPLAIN` and runtime measurements to evaluate subquery performance instead of relying on rules such as "JOINs are always faster" or "subqueries are always slow."**
- **For production systems, optimize query semantics, execution plans, indexing, and workload characteristics together rather than optimizing SQL syntax in isolation.**