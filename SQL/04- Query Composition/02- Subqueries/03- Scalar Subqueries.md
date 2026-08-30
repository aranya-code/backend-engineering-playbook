# 03- Scalar Subqueries

## Overview

A **scalar subquery** is a subquery that is expected to produce a single value: one row containing one column. It can be used anywhere a scalar expression is valid, such as in `SELECT`, `WHERE`, `HAVING`, `ORDER BY`, or an expression.

A common production use case is deriving a value from related data and using that value in an outer query:

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

The inner query produces one value:

```text
AVG(price)
    │
    ▼
scalar value
    │
    ▼
compare with each product
```

Scalar subqueries are useful because they allow a query to express dependent calculations without always introducing another join or separate application-side query. However, their correctness depends on **cardinality**: a scalar subquery must produce at most one row when the database requires a scalar result.

## What Is a Scalar Subquery?

A scalar subquery is a subquery used where SQL expects a single value.

For example:

```sql
SELECT (
    SELECT COUNT(*)
    FROM orders
) AS total_orders;
```

The inner query returns:

```text
1 row × 1 column
```

so its result can be treated as a scalar value.

Typical forms include:

```sql
SELECT (
    SELECT ...
);
```

```sql
WHERE column = (
    SELECT ...
);
```

```sql
SELECT
    column,
    (
        SELECT ...
    ) AS derived_value
FROM table;
```

The important constraint is:

> A scalar subquery cannot produce multiple rows where a single value is required.

## Scalar Subquery Cardinality

Consider:

```sql
SELECT (
    SELECT id
    FROM users
);
```

If `users` contains multiple rows, PostgreSQL raises an error similar to:

```text
ERROR: more than one row returned by a subquery used as an expression
```

The problem is not merely performance. The query has ambiguous scalar semantics.

A scalar subquery can therefore be classified by its result:

| Inner result | Scalar context |
|---|---|
| One row, one column | Valid |
| Zero rows | Usually produces `NULL` |
| Multiple rows | Error |
| Multiple columns | Error |

The exact behavior of a zero-row scalar subquery is particularly important: it generally evaluates to `NULL`.

For example:

```sql
SELECT (
    SELECT email
    FROM users
    WHERE id = 999999
) AS email;
```

If no matching user exists, the scalar result is:

```text
NULL
```

## Why Scalar Subqueries Exist

Scalar subqueries are useful when the outer query needs a value derived from another relation.

Common use cases include:

- Comparing against an aggregate.
- Retrieving a single related attribute.
- Calculating a per-row derived value.
- Checking a threshold derived from another query.
- Embedding configuration or reference data.
- Comparing a row against a group-level statistic.

They can keep related logic in a single SQL statement and avoid application-level query orchestration.

## Scalar Subquery in `WHERE`

One of the most common patterns is comparing a column against an aggregate.

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

The logical relationship is:

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
      result rows
```

The subquery returns one aggregate value, making it naturally suitable for scalar usage.

## Scalar Subquery in `SELECT`

A scalar subquery can produce a derived column.

```sql
SELECT
    p.id,
    p.name,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.product_id = p.id
    ) AS last_ordered_at
FROM products AS p;
```

This is a **correlated scalar subquery** because the inner query references:

```sql
p.id
```

from the outer query.

For each product, the inner query logically determines one value:

```text
Product
   │
   ▼
matching orders
   │
   ▼
MAX(created_at)
   │
   ▼
last_ordered_at
```

The aggregate guarantees at most one result row.

## Correlated Scalar Subqueries

A correlated scalar subquery depends on the current outer row.

```sql
SELECT
    u.id,
    u.email,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS last_order_at
FROM users AS u;
```

Logically:

```text
user 1 → MAX(orders for user 1)
user 2 → MAX(orders for user 2)
user 3 → MAX(orders for user 3)
...
```

This is different from an uncorrelated scalar subquery:

```sql
SELECT
    u.id,
    (
        SELECT MAX(created_at)
        FROM orders
    ) AS global_last_order_at
FROM users AS u;
```

The second query produces the same scalar value for every outer row.

## Uncorrelated vs Correlated Scalar Subqueries

| Property | Uncorrelated | Correlated |
|---|---|---|
| References outer query | No | Yes |
| Result dependency | Independent | Depends on current outer row |
| Common use | Global aggregate | Per-row aggregate |
| Potential repeated work | Usually avoidable | Depends on execution plan |
| Index importance | Depends on inner query | Often critical |
| Optimization | Often straightforward | Can require more complex transformations |

The key distinction is **dependency**, not whether the database literally executes the query once or repeatedly.

## Aggregate Scalar Subqueries

Aggregates are especially useful because they naturally collapse multiple rows into one result row.

Common examples:

```sql
SELECT AVG(price)
FROM products;
```

```sql
SELECT MAX(created_at)
FROM orders
WHERE user_id = 42;
```

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = 42;
```

This makes expressions such as the following safe from multi-row scalar errors:

```sql
SELECT
    u.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS order_count
FROM users AS u;
```

Even if a user has millions of orders, `COUNT(*)` returns one row.

## Scalar Subqueries and `NULL`

Zero-row scalar subqueries evaluate to `NULL`.

Consider:

```sql
SELECT
    p.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.product_id = p.id
    ) AS last_order_at
FROM products AS p;
```

For a product with no orders:

```text
MAX(...) = NULL
```

This matters when using the result in comparisons.

For example:

```sql
WHERE (
    SELECT MAX(o.created_at)
    FROM orders AS o
    WHERE o.product_id = p.id
) < CURRENT_TIMESTAMP - INTERVAL '30 days'
```

A product with no orders does **not** satisfy this predicate because:

```text
NULL < timestamp
```

evaluates to `UNKNOWN`, not `TRUE`.

If the business rule is "never ordered or not ordered in the last 30 days", express that explicitly:

```sql
WHERE (
    SELECT MAX(o.created_at)
    FROM orders AS o
    WHERE o.product_id = p.id
) IS NULL
OR (
    SELECT MAX(o.created_at)
    FROM orders AS o
    WHERE o.product_id = p.id
) < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

For more complex logic, a JOIN or CTE may make the expression easier to maintain.

## Using `COALESCE`

When a missing scalar result should have a default value, use `COALESCE`.

```sql
SELECT
    p.id,
    p.name,
    COALESCE(
        (
            SELECT SUM(oi.quantity)
            FROM order_items AS oi
            WHERE oi.product_id = p.id
        ),
        0
    ) AS units_sold
FROM products AS p;
```

This converts:

```text
NULL → 0
```

when no matching rows contribute to the aggregate.

Be careful to distinguish:

```text
no data
```

from:

```text
actual value is zero
```

The correct default depends on the domain.

## Scalar Subqueries vs JOINs

Consider retrieving the latest order timestamp.

A scalar subquery:

```sql
SELECT
    u.id,
    u.email,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS last_order_at
FROM users AS u;
```

A JOIN-based formulation:

```sql
SELECT
    u.id,
    u.email,
    MAX(o.created_at) AS last_order_at
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
GROUP BY
    u.id,
    u.email;
```

Both can express the same result.

The difference is primarily in **query structure and semantics**, not an inherent performance guarantee.

A scalar subquery can be clearer when the derived value is conceptually an attribute of each outer row.

A JOIN with aggregation may be preferable when multiple related metrics are needed from the same relation:

```sql
SELECT
    u.id,
    COUNT(o.id) AS order_count,
    MAX(o.created_at) AS last_order_at,
    SUM(o.total_amount) AS lifetime_value
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
GROUP BY
    u.id;
```

This can avoid expressing several independent correlated subqueries against the same table.

## Scalar Subqueries vs Window Functions

Some scalar subquery calculations are better expressed using window functions.

For example, calculating each product's difference from the global average:

```sql
SELECT
    p.id,
    p.name,
    p.price,
    p.price - AVG(p.price) OVER () AS difference_from_average
FROM products AS p;
```

This can be preferable to:

```sql
SELECT
    p.id,
    p.name,
    p.price,
    p.price - (
        SELECT AVG(price)
        FROM products
    ) AS difference_from_average
FROM products AS p;
```

Both express similar logic, but the window-function version communicates that the aggregate is a value associated with the result set.

Use the construct that best matches the relational operation.

## Scalar Subqueries and Cardinality Guarantees

A senior engineer should ask:

> **What guarantees that this subquery returns one row?**

Compare:

```sql
SELECT (
    SELECT email
    FROM users
    WHERE id = 42
);
```

with:

```sql
SELECT (
    SELECT email
    FROM users
    WHERE id = 42
    LIMIT 1
);
```

`LIMIT 1` forces a maximum of one returned row, but it can hide a data-integrity problem if `id` is supposed to be unique.

If `users.id` is a primary key, the first query already has a cardinality guarantee.

If the business rule says an email must be unique, enforce that with a database constraint rather than relying on `LIMIT 1`.

For example:

```sql
CREATE UNIQUE INDEX uq_users_email
    ON users (email);
```

Database constraints are stronger than application assumptions.

## Why `LIMIT 1` Can Be Dangerous

This query:

```sql
SELECT (
    SELECT id
    FROM users
    WHERE email = :email
    LIMIT 1
);
```

may appear safe, but it can silently select an arbitrary matching row if duplicate emails exist.

That is often worse than failing loudly.

Prefer:

```sql
SELECT (
    SELECT id
    FROM users
    WHERE email = :email
);
```

when the domain requires exactly one user and enforce:

```sql
UNIQUE (email)
```

at the database level.

Use `LIMIT 1` when multiple rows are legitimately possible and any qualifying row is acceptable, ideally with deterministic ordering when the selected row matters:

```sql
SELECT (
    SELECT id
    FROM orders
    WHERE user_id = :user_id
    ORDER BY created_at DESC, id DESC
    LIMIT 1
);
```

## Deterministic Scalar Selection

If the requirement is "latest order", do not rely on physical row order.

Bad:

```sql
SELECT (
    SELECT id
    FROM orders
    WHERE user_id = :user_id
    LIMIT 1
);
```

Better:

```sql
SELECT (
    SELECT id
    FROM orders
    WHERE user_id = :user_id
    ORDER BY created_at DESC, id DESC
    LIMIT 1
);
```

The secondary `id` ordering provides deterministic tie-breaking when timestamps are equal.

For PostgreSQL, an appropriate index can support this access pattern:

```sql
CREATE INDEX idx_orders_user_created
    ON orders (user_id, created_at DESC, id DESC);
```

The actual usefulness of the index should be validated against the workload and execution plan.

## Scalar Subquery Execution and Performance

A correlated scalar subquery can be expensive when the outer relation is large.

Example:

```sql
SELECT
    u.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS order_count
FROM users AS u;
```

The logical operation is:

```text
users
  │
  ├── user 1 → count orders
  ├── user 2 → count orders
  ├── user 3 → count orders
  └── ...
```

The optimizer may transform or optimize this, but the query still represents a potentially expensive per-user computation.

An index on:

```sql
orders(user_id)
```

may be important.

For PostgreSQL:

```sql
CREATE INDEX idx_orders_user_id
    ON orders (user_id);
```

But indexes are not a substitute for measurement. For high-volume reporting, a single grouped aggregation may be more appropriate:

```sql
SELECT
    u.id,
    COUNT(o.id) AS order_count
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
GROUP BY u.id;
```

## Avoiding Repeated Scalar Subqueries

This pattern can perform unnecessary repeated work:

```sql
SELECT
    u.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS last_order_at,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS order_count,
    (
        SELECT SUM(o.total_amount)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS lifetime_value
FROM users AS u;
```

A grouped JOIN can calculate all three metrics together:

```sql
SELECT
    u.id,
    MAX(o.created_at) AS last_order_at,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS lifetime_value
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
GROUP BY u.id;
```

The grouped form can be easier for the optimizer and avoids separately expressing the same relationship multiple times.

The correct choice should still be verified with `EXPLAIN`.

## Scalar Subqueries in `ORDER BY`

A scalar subquery can also participate in sorting.

```sql
SELECT
    u.id,
    u.email
FROM users AS u
ORDER BY (
    SELECT MAX(o.created_at)
    FROM orders AS o
    WHERE o.user_id = u.id
) DESC NULLS LAST;
```

This can be useful for ranking parent records by a derived related value.

For frequently executed endpoints, however, consider whether the sort can be expressed more efficiently through:

- A JOIN and aggregation.
- A maintained summary column.
- A materialized view.
- A dedicated reporting structure.

Sorting a large result set by a computed correlated value can become expensive.

## Scalar Subqueries in `HAVING`

Scalar subqueries can provide thresholds for grouped results.

```sql
SELECT
    customer_id,
    SUM(total_amount) AS customer_spend
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(customer_total)
    FROM (
        SELECT
            customer_id,
            SUM(total_amount) AS customer_total
        FROM orders
        GROUP BY customer_id
    ) AS totals
);
```

This expresses:

> Return customers whose spending exceeds the average customer spending.

The nested structure is logically useful, but the query may be expensive over a large orders table. For analytical workloads, inspect the execution plan and consider whether pre-aggregation is appropriate.

## Scalar Subqueries and Constraints

Cardinality should preferably be guaranteed by schema design.

Examples:

| Business invariant | Database mechanism |
|---|---|
| User ID identifies one user | Primary key |
| Email identifies one account | Unique constraint |
| Order belongs to one user | Foreign key |
| One active profile per user | Unique/partial constraint where supported |
| One configuration row per environment | Unique composite constraint |

Do not use scalar-subquery tricks to compensate for weak data integrity.

For example, this:

```sql
SELECT (
    SELECT id
    FROM users
    WHERE email = :email
    LIMIT 1
);
```

should not be the application's way of handling duplicate emails if the domain requires uniqueness.

## PostgreSQL Execution Plans

Use `EXPLAIN` to understand how PostgreSQL executes scalar subqueries.

```sql
EXPLAIN
SELECT
    u.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS last_order_at
FROM users AS u;
```

For runtime analysis:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    u.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.user_id = u.id
    ) AS last_order_at
FROM users AS u;
```

Look for:

- Actual vs estimated rows.
- Number of loops.
- Index scans vs sequential scans.
- Buffer reads and hits.
- Sort operations.
- Temporary I/O.
- Total execution time.

A high loop count is not automatically bad. An indexed lookup that executes many times can still be efficient.

The important measurement is total work.

## ORM Usage

Django can represent scalar subqueries explicitly.

For example:

```python
from django.db.models import OuterRef, Subquery

latest_order = (
    Order.objects
    .filter(user_id=OuterRef("pk"))
    .order_by("-created_at", "-id")
    .values("created_at")[:1]
)

users = User.objects.annotate(
    last_order_at=Subquery(latest_order)
)
```

This produces a scalar value for each user.

The application code should still be evaluated at the SQL level:

```text
Django QuerySet
      │
      ▼
Generated SQL
      │
      ▼
Database optimizer
      │
      ▼
Execution plan
```

Do not assume that ORM abstractions eliminate SQL performance concerns.

## Practical Backend Example

Suppose a REST API returns customers with their latest order timestamp:

```text
GET /api/customers
```

The response requires:

```json
{
  "id": 42,
  "email": "customer@example.com",
  "last_order_at": "2026-08-30T10:30:00Z"
}
```

A scalar subquery can express this directly:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT o.created_at
        FROM orders AS o
        WHERE o.customer_id = c.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS last_order_at
FROM customers AS c;
```

A supporting index can make the lookup efficient:

```sql
CREATE INDEX idx_orders_customer_created
    ON orders (customer_id, created_at DESC, id DESC);
```

For a high-traffic endpoint, verify:

- Pagination is applied.
- The customer query is bounded.
- The index is used.
- Query latency remains acceptable at production scale.
- The endpoint does not repeatedly execute this query unnecessarily.
- Connection pool capacity is sufficient.

## Production Considerations

### Query Frequency

A moderately expensive scalar subquery becomes significant when executed thousands of times per second.

### Dataset Growth

A correlated scalar subquery that works well with 100,000 rows may require redesign at hundreds of millions of rows.

### Index Design

Index the correlated predicate and ordering requirements when justified.

### Cardinality

Use database constraints to guarantee assumptions such as uniqueness.

### Null Semantics

Explicitly handle `NULL` when zero matching rows are possible.

### Observability

Monitor query latency and database resource consumption rather than relying solely on application response times.

### Read Replicas

Read-heavy scalar-subquery workloads can sometimes be routed to replicas, but replication lag must be acceptable for the endpoint's consistency requirements.

### Caching

If a scalar-derived value changes rarely and is requested frequently, application caching or precomputed data may be appropriate. Do not introduce Redis merely to avoid fixing an inefficient database query.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Assuming a scalar subquery always executes once per outer row | Confuses logical correlation with physical execution | Inspect the execution plan |
| Ignoring multi-row results | Causes runtime errors | Guarantee scalar cardinality |
| Adding `LIMIT 1` to hide duplicates | Masks data-integrity problems | Enforce uniqueness with constraints |
| Ignoring `NULL` | Produces incorrect comparisons | Handle `NULL` explicitly |
| Repeating the same correlated subquery several times | Can increase query complexity and work | Consider grouped aggregation |
| Assuming `EXISTS` and scalar subqueries are interchangeable | They have different result semantics | Use the construct matching the requirement |
| Missing an index on a correlation predicate | Can make repeated lookups expensive | Evaluate an appropriate index |
| Optimizing from SQL text alone | Physical execution may differ | Use `EXPLAIN` |
| Returning a scalar value without deterministic ordering | `LIMIT 1` can select an arbitrary row | Add meaningful `ORDER BY` |
| Moving scalar calculations into Python | Can create N+1 database queries | Prefer set-based SQL when appropriate |

## Interview Traps

### "What happens if a scalar subquery returns multiple rows?"

The database raises an error because a scalar expression requires a single value.

### "What happens if it returns zero rows?"

In a scalar expression context, the result is generally `NULL`.

### "Does a correlated scalar subquery always execute once for every outer row?"

No. That is a logical model, not a guarantee of physical execution. The optimizer can transform the query.

### "Is a scalar subquery always slower than a JOIN?"

No. Equivalent queries can produce similar execution plans. Performance depends on the optimizer, data distribution, indexes, cardinality, and workload.

### "Why not always use `LIMIT 1`?"

Because it can hide violations of expected uniqueness and produce nondeterministic results unless ordering is defined.

### "When is a scalar subquery a good choice?"

When the outer query needs one derived value and the scalar cardinality is clear and efficiently supported.

## When to Prefer Another SQL Construct

| Requirement | Often appropriate |
|---|---|
| Need one derived value | Scalar subquery |
| Need to know whether a related row exists | `EXISTS` |
| Need to combine columns from related rows | `JOIN` |
| Need multiple aggregates from the same relation | JOIN + `GROUP BY` |
| Need calculations across result rows | Window function |
| Need reusable multi-stage query logic | CTE |
| Need a frequently reused expensive aggregate | Materialized/precomputed data |
| Need arbitrary matching related row | Scalar subquery with deterministic ordering |
| Need exactly one related entity | Scalar subquery backed by a uniqueness constraint |

These are engineering defaults, not universal performance rules. Always validate important queries with the target database and realistic data.

## Key Takeaways

- **A scalar subquery produces a single value and therefore requires scalar cardinality: multiple rows in a scalar context cause an error.**
- **Correlated scalar subqueries can express per-row derived values cleanly, but their physical execution must be evaluated with `EXPLAIN` rather than assumed from SQL syntax.**
- **Use database constraints to guarantee uniqueness instead of using `LIMIT 1` to hide unexpected duplicate data.**
- **Handle `NULL` explicitly because zero-row scalar subqueries generally evaluate to `NULL`, which participates in SQL's three-valued logic.**
- **For production workloads, compare scalar subqueries with JOINs, aggregates, window functions, or precomputed data based on semantics, execution plans, data volume, and workload characteristics.**