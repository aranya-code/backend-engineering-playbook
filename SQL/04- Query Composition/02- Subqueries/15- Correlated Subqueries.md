# 15- Correlated Subqueries

## Overview

A correlated subquery is a subquery that references a column from the outer query. Unlike an uncorrelated subquery, which can be evaluated independently, a correlated subquery depends on the current row being processed by the outer query.

The canonical form is:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The reference:

```sql
o.customer_id = c.id
```

connects the inner query to the current outer-row value.

Correlated subqueries are especially useful for:

- `EXISTS` and `NOT EXISTS` relationship checks.
- Per-row comparisons against related data.
- Finding the latest or highest-priority related record.
- Computing derived values for each outer row.
- Expressing conditions that naturally depend on the current outer row.

They are powerful, but they can become expensive when used carelessly. A senior-level understanding requires distinguishing **logical correlation** from the **physical execution strategy chosen by the optimizer**.

## Correlated vs Uncorrelated Subqueries

### Uncorrelated Subquery

An uncorrelated subquery does not reference the outer query:

```sql
SELECT
    p.id,
    p.sku
FROM products AS p
WHERE p.category_id IN (
    SELECT c.id
    FROM categories AS c
    WHERE c.department = 'electronics'
);
```

The inner query can logically be evaluated without knowing anything about the current product.

### Correlated Subquery

A correlated subquery references the outer query:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The subquery's predicate depends on `c.id`.

| Property | Uncorrelated | Correlated |
|---|---|---|
| References outer query | No | Yes |
| Independent evaluation | Possible | Not logically independent |
| Typical use | Derived sets | Per-row relationship logic |
| Common predicate | `IN` | `EXISTS` |
| Optimization complexity | Usually simpler | Potentially more complex |
| Main risk | Large intermediate result | Expensive repeated-looking work |

## Why Correlated Subqueries Exist

A correlated subquery lets the database express:

> For each outer row, evaluate a condition against data related to that row.

This is useful when the relationship itself is part of the condition.

For example:

> Return customers who have at least one completed order.

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

The outer row supplies the customer ID, and the subquery determines whether the required related row exists.

This keeps the operation set-oriented inside the database instead of requiring the application to fetch customers and issue one query per customer.

## Logical Execution Model

A useful conceptual model is:

```text
Outer query produces candidate row
              │
              ▼
       Current outer values
              │
              ▼
   Correlated subquery evaluates
              │
              ▼
      Predicate produces result
              │
              ▼
    Outer row is kept/rejected
```

For example:

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

Conceptually:

```text
Customer 101 → Does order.customer_id = 101 exist?
Customer 102 → Does order.customer_id = 102 exist?
Customer 103 → Does order.customer_id = 103 exist?
```

This is a **logical model**, not a promise about the physical execution plan.

A modern optimizer may transform the query into a semi-join or another efficient plan rather than literally executing the subquery independently for every outer row.

## `EXISTS` With Correlation

`EXISTS` is one of the most natural uses of correlated subqueries.

```sql
SELECT
    p.id,
    p.sku
FROM products AS p
WHERE EXISTS (
    SELECT 1
    FROM product_reviews AS r
    WHERE r.product_id = p.id
      AND r.rating <= 2
);
```

The requirement is:

> Return products that have at least one low-rated review.

The inner query does not need to return the review. It only needs to establish existence.

### Why This Is Useful

A join could also express the relationship:

```sql
SELECT DISTINCT
    p.id,
    p.sku
FROM products AS p
JOIN product_reviews AS r
    ON r.product_id = p.id
WHERE r.rating <= 2;
```

But the join naturally produces one row per matching review. If only product existence matters, `EXISTS` communicates the intent directly and avoids requiring `DISTINCT` merely to remove multiplicity.

## `NOT EXISTS` With Correlation

`NOT EXISTS` is the natural inverse:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This means:

> Return customers for whom no matching order exists.

It is particularly useful for anti-join logic.

Another production example:

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM user_permissions AS p
    WHERE p.user_id = u.id
      AND p.permission = 'admin.access'
);
```

This finds users without a particular permission.

Compared with `NOT IN`, `NOT EXISTS` generally avoids the problematic `NULL` semantics associated with nullable subquery values.

## Correlated Scalar Subqueries

Correlation is not limited to `EXISTS`.

A scalar subquery can reference the current outer row:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

The inner query computes a value specifically for the current customer.

Conceptually:

```text
Customer
   │
   ├── customer_id = 101 → MAX(order.created_at)
   ├── customer_id = 102 → MAX(order.created_at)
   └── customer_id = 103 → MAX(order.created_at)
```

This can be useful when the derived value is genuinely part of the outer result.

## Correlated Subquery for Latest Related Record

A common backend requirement is:

> Return each customer's most recent order.

One approach uses a correlated subquery:

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

The secondary ordering by `o.id` provides deterministic behavior when two orders have the same timestamp.

For a large production dataset, an appropriate index can make this access pattern efficient:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at DESC, id DESC);
```

Whether this is preferable to a window function, `DISTINCT ON` in PostgreSQL, or another formulation should be determined by the workload and execution plan.

## Correlated Aggregate Conditions

Correlated subqueries can compare each row against an aggregate calculated for its related records.

For example:

> Find products whose price is greater than the average price of products in the same category.

```sql
SELECT
    p.id,
    p.name,
    p.price
FROM products AS p
WHERE p.price > (
    SELECT AVG(p2.price)
    FROM products AS p2
    WHERE p2.category_id = p.category_id
);
```

The correlation is:

```sql
p2.category_id = p.category_id
```

The inner query calculates the category-specific average for the current product's category.

This pattern is powerful, but it can often be rewritten using window functions:

```sql
SELECT
    id,
    name,
    price
FROM (
    SELECT
        p.*,
        AVG(price) OVER (
            PARTITION BY category_id
        ) AS category_avg_price
    FROM products AS p
) AS ranked
WHERE price > category_avg_price;
```

For analytical workloads, the window-function formulation may be clearer and more efficient.

## Correlated Subqueries vs Joins

Many correlated subqueries have an equivalent join formulation.

Consider:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

A join-based alternative is:

```sql
SELECT DISTINCT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

The two queries are not conceptually identical:

- `EXISTS` asks whether a related row exists.
- `JOIN` combines rows and therefore introduces multiplicity.

If the relationship is one-to-many, the join can produce multiple rows for one customer.

### Choosing Between Them

| Requirement | Good starting point |
|---|---|
| Need columns from both tables | `JOIN` |
| Need only existence | `EXISTS` |
| Need absence | `NOT EXISTS` |
| Need one aggregate per group | `GROUP BY` or window function |
| Need per-row derived value | Correlated scalar subquery or window function |
| Need membership in a set | `IN` |
| Need complex relationship predicate | `EXISTS` |

Do not rewrite a correlated subquery into a join merely because joins are generally familiar. Preserve the intended cardinality.

## Correlated Subqueries and Query Cardinality

Consider:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

If a customer has 20 orders, the customer can appear 20 times.

With:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

the customer appears once.

This distinction matters in APIs.

If a REST endpoint returns customers, accidental join multiplication can:

- Duplicate response objects.
- Increase network payloads.
- Increase serialization work.
- Produce incorrect pagination.
- Require `DISTINCT`.
- Increase database work.

Use `EXISTS` when the API only needs a Boolean relationship condition.

## Physical Execution: The Important Senior-Level Distinction

It is tempting to describe a correlated subquery as:

> Run the inner query once for every outer row.

That is a useful conceptual model but not necessarily the physical execution.

Database optimizers may transform correlated expressions into:

- Nested-loop plans.
- Semi-joins.
- Anti-joins.
- Hash-based strategies.
- Index-driven lookups.
- Other decorrelated execution strategies.

For example:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

may be optimized into a semi-join.

Therefore, the source SQL does not tell you exactly how many times the database accesses the inner table.

Always inspect the execution plan for performance-sensitive queries.

## PostgreSQL Execution Plan

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

Pay attention to:

- Actual row counts.
- Estimated row counts.
- Join strategy.
- Index scans vs sequential scans.
- Rows removed by filters.
- Buffer hits.
- Buffer reads.
- Execution time.
- Whether the planner transformed the correlated predicate.

A major estimation mismatch can indicate stale statistics, data skew, or an unsuitable query shape.

## Indexing Correlated Predicates

Consider:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'completed'
)
```

The correlated lookup depends on:

```sql
o.customer_id
```

and also filters on:

```sql
o.status
```

An index such as:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

may support this access pattern.

For PostgreSQL, if only completed orders matter for a heavily used query:

```sql
CREATE INDEX idx_completed_orders_customer
ON orders (customer_id)
WHERE status = 'completed';
```

can be more targeted.

Index selection should consider the complete workload, including writes, storage overhead, and other query patterns.

## Correlated Subqueries and `NULL`

Correlation uses ordinary SQL comparison semantics.

For example:

```sql
WHERE o.customer_id = c.id
```

does not match when either side is `NULL`.

If both values can be nullable and the business rule considers `NULL` equal to `NULL`, ordinary `=` is not sufficient. PostgreSQL provides:

```sql
WHERE o.customer_id IS NOT DISTINCT FROM c.id
```

Whether this is appropriate depends on the data model.

For most foreign-key relationships, `NULL` has a different meaning and should not be treated as an identifier value.

## Correlated Subqueries in `UPDATE`

Correlated subqueries can also be used in data modification statements.

For example:

```sql
UPDATE customers AS c
SET last_order_at = (
    SELECT MAX(o.created_at)
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This can be useful for controlled backfills or denormalized fields.

However, production systems should consider:

- Number of rows affected.
- Lock duration.
- Transaction size.
- Write amplification.
- Replication lag.
- Concurrent writes.
- Rollback cost.

For large backfills, batch processing may be safer than updating an entire table in one transaction.

## Correlated Subqueries in `DELETE`

The same relationship logic can be used for deletes.

For example:

```sql
DELETE FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This requires extreme care in production.

Before executing a destructive correlated query:

```sql
SELECT
    c.id
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

first verify the exact candidate set.

For destructive operations, also consider:

- Foreign-key constraints.
- Cascading deletes.
- Transaction boundaries.
- Backup/recovery requirements.
- Audit requirements.
- Concurrent inserts.
- Business-level deletion policies.

## Correlated Subqueries in Application Backends

A common mistake is to reproduce correlated logic in application code.

Avoid patterns like:

```python
customers = Customer.objects.all()

for customer in customers:
    customer.has_orders = Order.objects.filter(
        customer_id=customer.id
    ).exists()
```

This can generate an N+1 query pattern.

Instead, express the relationship in SQL.

Django supports correlated existence queries:

```python
from django.db.models import Exists, OuterRef

orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
)

customers = Customer.objects.annotate(
    has_orders=Exists(orders),
)
```

The database can evaluate the relationship as part of the query rather than requiring a separate round trip per customer.

This principle applies equally to SQL generated by other ORMs and query builders.

## Correlation and N+1 Queries Are Different

A correlated subquery inside one SQL statement is **not automatically an N+1 database request pattern**.

For example:

```sql
SELECT
    c.id,
    EXISTS (
        SELECT 1
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS has_orders
FROM customers AS c;
```

is one SQL statement and one database round trip from the application.

The database may perform many internal operations, but the application is not issuing one SQL request per customer.

The problematic pattern is:

```text
Application
   │
   ├── Query customers
   │
   ├── Query orders for customer 1
   ├── Query orders for customer 2
   ├── Query orders for customer 3
   └── ...
```

A correlated subquery can keep the entire operation inside the database:

```text
Application
   │
   └── One SQL statement
          │
          ├── Customers
          └── Correlated order checks
```

## When Correlated Subqueries Are a Good Choice

Use them when:

- The condition naturally depends on the current outer row.
- `EXISTS` or `NOT EXISTS` expresses a relationship clearly.
- A per-row scalar value is required.
- The correlated predicate has good supporting indexes.
- The query remains understandable and maintainable.
- The optimizer produces an acceptable execution plan.

Typical examples include:

```sql
-- Has at least one matching row
EXISTS (...)

-- Has no matching row
NOT EXISTS (...)

-- Latest related value
(
    SELECT ...
    ORDER BY ...
    LIMIT 1
)

-- Per-group comparison
(
    SELECT AVG(...)
    WHERE related_key = outer_key
)
```

## When to Prefer a Different Form

A correlated subquery may not be the best representation when:

- A straightforward join is clearer.
- A window function expresses the calculation naturally.
- A grouped aggregate is required.
- The query repeatedly scans a large relation.
- The correlated expression is difficult to reason about.
- The optimizer produces an inefficient plan.
- The same derived data is needed across many outer rows.

For example, this correlated calculation:

```sql
SELECT
    p.id,
    p.price,
    (
        SELECT AVG(p2.price)
        FROM products AS p2
        WHERE p2.category_id = p.category_id
    ) AS category_avg
FROM products AS p;
```

may be more naturally represented using a window function:

```sql
SELECT
    p.id,
    p.price,
    AVG(p.price) OVER (
        PARTITION BY p.category_id
    ) AS category_avg
FROM products AS p;
```

The correct choice depends on semantics and execution characteristics.

## Performance Pitfalls

### Missing Index on the Correlated Column

This pattern:

```sql
WHERE o.customer_id = c.id
```

can become expensive if the related table is large and the database has no useful access path.

Check indexes before assuming the query is inherently slow.

### High Outer Cardinality

A query against millions of outer rows creates substantial work even if each individual correlated lookup is cheap.

Consider whether the outer query can be filtered earlier.

### Low Selectivity

If almost every outer row has matching related rows, the existence predicate may provide little filtering value.

The database still has to establish existence for many rows.

### Expensive Scalar Subqueries

A scalar correlated subquery that performs sorting or aggregation for every outer row can become expensive:

```sql
SELECT
    c.id,
    (
        SELECT SUM(o.total_amount)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS lifetime_value
FROM customers AS c;
```

This may be appropriate, but for large datasets a pre-aggregated relation, grouped query, materialized view, or other formulation may be more suitable.

### Assuming `LIMIT 1` Guarantees Fast Execution

This:

```sql
ORDER BY o.created_at DESC
LIMIT 1
```

can be efficient with a suitable index.

Without an appropriate access path, the database may still need significant work to identify the latest row.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Assuming correlation means one physical execution per outer row | Confusing logical and physical execution | Inspect the execution plan |
| Assuming correlated subqueries are always slow | Applying a blanket rule | Measure the actual query |
| Using a join for existence and forgetting multiplicity | Treating joins as Boolean checks | Prefer `EXISTS` when only existence matters |
| Creating N+1 queries in application code | Checking relationships in a loop | Express the relationship in one SQL statement |
| Missing an index on the correlated predicate | Testing against small datasets | Index based on actual access patterns |
| Using scalar correlated aggregation at huge scale | Convenience | Consider grouped aggregates or window functions |
| Ignoring `NULL` semantics | Treating SQL comparisons like application equality | Model and test nullable relationships explicitly |
| Using `DISTINCT` to hide join multiplication | Fixing symptoms rather than cardinality | Use `EXISTS` when appropriate |
| Executing correlated `UPDATE`/`DELETE` without validation | Underestimating affected rows | Preview with `SELECT` and use controlled transactions |
| Assuming ORM abstraction eliminates SQL costs | Focusing only on application code | Inspect generated SQL and execution plans |

## Production Review Checklist

Before shipping a correlated subquery on a production query path:

- Confirm that correlation expresses the actual business relationship.
- Determine whether `EXISTS`, `JOIN`, aggregation, or a window function is the clearest formulation.
- Check indexes on correlated predicates.
- Test using realistic table cardinalities.
- Run `EXPLAIN` or `EXPLAIN ANALYZE` where appropriate.
- Compare estimated and actual row counts.
- Check buffer and IO behavior for expensive queries.
- Verify `NULL` semantics.
- Confirm that joins are not introducing unintended row multiplication.
- Avoid application-side N+1 queries.
- Inspect ORM-generated SQL when using Django or another ORM.
- Consider transaction and locking implications for `UPDATE` and `DELETE`.
- Monitor latency and database resource consumption after deployment.

## Interview Traps

### Does a correlated subquery always execute once per outer row?

No.

That is the logical dependency model. The optimizer may decorrelate the query or transform it into a semi-join, anti-join, nested loop, or another physical strategy.

### Are correlated subqueries always slower than joins?

No.

An indexed `EXISTS` query can be highly efficient, and the optimizer may produce an execution strategy comparable to a join.

The query shape should be selected based on semantics and measured performance.

### Why is `EXISTS` often a good fit for correlated subqueries?

Because the requirement often naturally means:

> For this outer row, does at least one related row satisfy these conditions?

The correlation supplies the outer key, while `EXISTS` reduces the result to a Boolean existence test.

### Is one correlated SQL query equivalent to N+1 application queries?

No.

A correlated subquery is part of a single SQL statement. N+1 occurs when the application sends separate database queries repeatedly, usually once for each outer object.

### When should a correlated scalar subquery be replaced?

Consider a join, grouped aggregate, window function, materialized view, or precomputed value when:

- The computation is repeated over a large outer dataset.
- The same related data is needed across many rows.
- The execution plan shows excessive work.
- Another formulation is clearer and measurably more efficient.

### Can correlated subqueries be used in `UPDATE` and `DELETE`?

Yes.

They can be powerful for data maintenance and denormalization, but write operations require additional attention to transaction size, locking, concurrency, replication, rollback, and recovery.

## Key Takeaways

- **A correlated subquery references values from the current outer query row, making it ideal for per-row relationship and derived-value logic.**
- **Correlation describes logical dependency, not necessarily repeated physical execution; optimizers can decorrelate or transform the query into efficient join strategies.**
- **`EXISTS` and `NOT EXISTS` are particularly strong patterns for correlated existence and anti-existence checks without introducing join multiplicity.**
- **Performance depends on indexes, cardinality, selectivity, statistics, and the execution plan; never judge correlated queries from syntax alone.**
- **In backend applications, keep correlated relationship logic inside one SQL statement rather than reproducing it with application-side loops that create N+1 queries.**