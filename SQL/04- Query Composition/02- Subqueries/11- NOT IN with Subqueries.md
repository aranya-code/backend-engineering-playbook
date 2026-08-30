# 11- NOT IN with Subqueries

## Overview

`NOT IN` with a subquery is used to exclude rows whose values belong to a set produced by another query.

The basic pattern is:

```sql
SELECT ...
FROM ...
WHERE column NOT IN (
    SELECT column
    FROM ...
);
```

A common example is finding customers who have never placed an order:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

The syntax is straightforward, but `NOT IN` has one of the most important edge cases in SQL: **`NULL` values in the subquery can change the result of the entire predicate**.

For production systems, this makes `NOT EXISTS` the safer default for many anti-join requirements.

## What `NOT IN` Means

`NOT IN` is the inverse membership predicate of `IN`.

For example:

```sql
SELECT
    id,
    email
FROM customers
WHERE id NOT IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'cancelled'
);
```

The query means:

> Return customers whose ID does not belong to the set of customer IDs associated with cancelled orders.

Conceptually:

```text
customers
    │
    │ customer.id
    ▼
NOT IN
    ▲
    │
    │ customer_id
    │
orders
    │
    └── status = 'cancelled'
```

The database evaluates membership as part of the SQL expression. It does not require the application to retrieve the subquery results first.

## Why `NOT IN` Exists

Without a subquery, applications sometimes implement exclusion in multiple steps:

```python
blocked_ids = get_blocked_customer_ids()
customers = get_customers_excluding(blocked_ids)
```

This approach can introduce:

- Additional database round trips.
- Large ID lists transferred to the application.
- Increased application memory usage.
- More complex application code.
- Race conditions between queries.
- Large dynamically generated `IN` clauses.

A database-side query keeps the exclusion logic within the relational engine:

```sql
SELECT *
FROM customers
WHERE id NOT IN (
    SELECT customer_id
    FROM blocked_customers
);
```

The optimizer can then select an execution strategy based on table statistics, indexes, cardinality, and database-specific capabilities.

## The Critical `NULL` Problem

The most important rule is:

> **`NOT IN` is unsafe when the subquery can return `NULL`.**

Consider:

```sql
SELECT
    id,
    email
FROM customers
WHERE id NOT IN (
    SELECT customer_id
    FROM orders
);
```

Suppose the subquery produces:

```text
101
205
NULL
```

For:

```text
id = 101
```

the row is clearly excluded.

For:

```text
id = 999
```

SQL cannot establish that `999` is different from every value because one of the values is `NULL`, which represents an unknown value.

The comparison therefore becomes `UNKNOWN`.

Because a `WHERE` clause retains only rows for which the predicate evaluates to `TRUE`, the customer may not be returned.

This is why a nullable column in the subquery can make an apparently correct `NOT IN` query return **zero rows or fewer rows than expected**.

## SQL Three-Valued Logic

SQL predicates can evaluate to:

| Result | Meaning |
|---|---|
| `TRUE` | Predicate is definitely satisfied |
| `FALSE` | Predicate is definitely not satisfied |
| `UNKNOWN` | Result cannot be determined because of `NULL` |

Consider:

```sql
SELECT *
FROM customers
WHERE id NOT IN (101, 205, NULL);
```

For `id = 999`, SQL effectively needs to determine:

```text
999 <> 101
AND
999 <> 205
AND
999 <> NULL
```

The final comparison is:

```text
999 <> NULL
```

which evaluates to:

```text
UNKNOWN
```

Therefore:

```text
TRUE AND TRUE AND UNKNOWN
```

becomes:

```text
UNKNOWN
```

and the row is filtered out by `WHERE`.

This is the core reason `NOT IN` and `NULL` are a dangerous combination.

## Safe `NOT IN` When `NULL` Is Impossible

`NOT IN` can be perfectly valid when the subquery column is guaranteed to be non-null.

For example, if:

```sql
orders.customer_id
```

is declared:

```sql
customer_id BIGINT NOT NULL
```

then:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

does not have the same `NULL` hazard from the subquery.

However, the guarantee should come from the actual schema or a reliably enforced predicate, not from an assumption in application code.

## Filtering `NULL` Explicitly

You can make a `NOT IN` query safer by excluding `NULL` values:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.customer_id IS NOT NULL
);
```

This prevents `NULL` from entering the subquery result.

However, if the actual requirement is:

> Return customers for which no matching order exists

then `NOT EXISTS` is usually clearer:

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

The second query directly expresses the business condition.

## `NOT IN` vs `NOT EXISTS`

These are common alternatives:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

and:

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

They may produce the same result when the subquery column is guaranteed to be non-null.

But they differ significantly when `NULL` is possible.

### Semantic Comparison

| Aspect | `NOT IN` | `NOT EXISTS` |
|---|---|---|
| Expresses | Value not in a set | No matching row exists |
| `NULL` sensitivity | High | Much safer |
| Handles correlated relationship naturally | Less natural | Yes |
| Common anti-join pattern | Yes | Yes |
| Requires subquery value | Yes | No selected value required |
| Recommended for nullable related columns | Usually no | Usually yes |

For relational anti-join logic, `NOT EXISTS` is generally the safer and clearer choice.

## Anti-Join Semantics

A query such as:

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

is an **anti-join**.

It means:

> Return rows from the left side for which no matching row exists on the right side.

The equivalent conceptual flow is:

```text
Customers
    │
    ├── matching order exists ──► exclude
    │
    └── no matching order ──────► include
```

This pattern is common in production systems.

Examples include:

- Customers without orders.
- Users without required permissions.
- Accounts without active subscriptions.
- Products without inventory.
- Jobs without successful executions.
- Records not yet synchronized.
- Entities missing a corresponding downstream record.

## Practical Example: Customers Without Orders

Using `NOT IN`:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

Using `NOT EXISTS`:

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

For production code, prefer the second form when the business requirement is absence of a related row.

It remains correct even if `orders.customer_id` is nullable.

## Practical Example: Accounts Without Active Subscriptions

Suppose an account should be considered eligible for a new subscription only if it does not already have an active one.

```sql
SELECT
    a.id,
    a.account_name
FROM accounts AS a
WHERE NOT EXISTS (
    SELECT 1
    FROM subscriptions AS s
    WHERE s.account_id = a.id
      AND s.status = 'active'
);
```

The important detail is that the condition belongs inside the subquery:

```sql
WHERE s.account_id = a.id
  AND s.status = 'active'
```

This asks whether an active subscription exists.

It does **not** exclude an account merely because it has some historical subscription.

## Practical Example: Excluding Recently Processed Records

A batch worker may need to select records that have not yet been successfully processed:

```sql
SELECT
    e.id,
    e.payload
FROM events AS e
WHERE NOT EXISTS (
    SELECT 1
    FROM processed_events AS p
    WHERE p.event_id = e.id
      AND p.status = 'success'
)
ORDER BY e.id
LIMIT 100;
```

This pattern is useful in:

- Celery workers.
- Scheduled jobs.
- Data synchronization.
- ETL pipelines.
- Reconciliation processes.

For concurrent workers, the query may also need appropriate transaction isolation and row-locking strategies. `NOT EXISTS` alone does not prevent two workers from selecting the same record simultaneously.

## `NOT IN` with Additional Filtering

If `NOT IN` is appropriate and the subquery column can contain `NULL`, explicitly eliminate `NULL`:

```sql
SELECT
    p.id,
    p.name
FROM products AS p
WHERE p.id NOT IN (
    SELECT oi.product_id
    FROM order_items AS oi
    WHERE oi.product_id IS NOT NULL
      AND oi.quantity > 0
);
```

This means:

> Return products that do not belong to the set of products appearing in positive-quantity order items.

For complex relationship logic, however, `NOT EXISTS` may be easier to reason about:

```sql
SELECT
    p.id,
    p.name
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items AS oi
    WHERE oi.product_id = p.id
      AND oi.quantity > 0
);
```

## Performance Considerations

Do not assume that `NOT IN` is slower or faster than `NOT EXISTS`.

Modern query optimizers can transform both into anti-join-like execution strategies when the semantics permit it.

Actual performance depends on:

- Table cardinality.
- Selectivity.
- Indexes.
- Statistics.
- Nullability.
- Data distribution.
- Query correlation.
- Database engine.
- Execution-plan choices.

For PostgreSQL, inspect the actual execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
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

Look for:

- Unexpected sequential scans.
- Large row counts.
- Poor cardinality estimates.
- Excessive buffer reads.
- Expensive hash operations.
- Nested loops over unexpectedly large relations.
- Disk-based operations.
- Latency regressions under production-sized data.

## Indexing Anti-Joins

For:

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

an index on the related lookup column is usually important:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

If the query includes additional predicates:

```sql
WHERE o.customer_id = c.id
  AND o.status = 'active'
```

a composite index may be appropriate:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

Index design should follow actual workload and query plans rather than generic rules.

## `NOT IN` vs `LEFT JOIN ... IS NULL`

Another common anti-join formulation is:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.id IS NULL;
```

This asks for customers for whom no matching order row was found.

It can be equivalent to:

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

### Comparison

| Pattern | Strength | Main concern |
|---|---|---|
| `NOT IN` | Concise set exclusion | `NULL` semantics |
| `NOT EXISTS` | Direct existence semantics | Slightly more verbose |
| `LEFT JOIN ... IS NULL` | Natural when joins are already required | Can become confusing in complex joins |

Do not choose based solely on perceived performance. Compare execution plans on the target database.

## `NOT EXISTS` Is Usually the Production Default

For requirements such as:

> Find rows that have no matching related record.

a strong default is:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM related_table
    WHERE related_table.foreign_key = outer_table.id
)
```

Reasons include:

- It directly represents absence.
- It avoids the `NULL` trap associated with `NOT IN`.
- It works naturally with correlated conditions.
- It maps well to anti-join execution strategies.
- It remains readable when additional related-row predicates are added.

`NOT IN` is still useful when the requirement genuinely is:

> Exclude values contained in this known non-null set.

## Multi-Column Exclusion

Some databases support row-value comparisons:

```sql
WHERE (customer_id, region_id) NOT IN (
    SELECT customer_id, region_id
    FROM blocked_customers
);
```

This is more advanced and has additional `NULL` considerations.

If either component can be `NULL`, reasoning about the predicate becomes more difficult.

For relationship-based exclusion, an explicit `NOT EXISTS` is often clearer:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_customers AS b
    WHERE b.customer_id = c.customer_id
      AND b.region_id = c.region_id
);
```

Use row-value `NOT IN` only when its semantics are well understood and supported consistently by the target database.

## Application and ORM Considerations

### Django

Django can express a simple `NOT IN` using `exclude()`:

```python
blocked_customer_ids = BlockedCustomer.objects.values("customer_id")

customers = Customer.objects.exclude(
    id__in=blocked_customer_ids,
)
```

For relationship-based exclusion, `Exists` can make the intended semantics explicit:

```python
from django.db.models import Exists, OuterRef

orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
)

customers = Customer.objects.filter(
    ~Exists(orders),
)
```

For production ORM usage:

- Prefer database-side subqueries over loading IDs into Python.
- Inspect generated SQL for complex ORM expressions.
- Verify nullable-field behavior.
- Ensure foreign-key lookup columns are indexed.
- Use `EXPLAIN` for performance-sensitive queries.
- Test with production-like data volumes.

### FastAPI or Other API Services

An API endpoint should not normally implement database exclusion like this:

```python
blocked_ids = [row.id for row in db.query(...)]
```

followed by a large dynamically generated `NOT IN` list.

Prefer a database-side subquery or `NOT EXISTS`:

```sql
SELECT ...
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_customers AS b
    WHERE b.customer_id = c.id
);
```

This reduces application-level data movement and lets the database optimize the operation.

## Multi-Tenant Systems

Anti-joins must preserve tenant boundaries.

Consider:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.tenant_id = :tenant_id
  AND NOT EXISTS (
      SELECT 1
      FROM orders AS o
      WHERE o.customer_id = c.id
        AND o.tenant_id = :tenant_id
  );
```

The subquery is explicitly scoped to the same tenant.

This is important because authorization constraints should not depend on an assumption that the outer query's tenant predicate automatically limits every related relation.

For sensitive multi-tenant systems:

- Scope related tables explicitly.
- Use foreign keys and tenant-aware constraints where appropriate.
- Use parameterized SQL.
- Consider database-level row-level security where appropriate.
- Test cross-tenant isolation as part of integration testing.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Using `NOT IN` against a nullable column | `NULL` causes `UNKNOWN` results | Prefer `NOT EXISTS` |
| Assuming `NULL` behaves like an ordinary value | Treating SQL like two-valued Boolean logic | Understand three-valued logic |
| Fixing `NOT IN` with `DISTINCT` | Duplicates are not the problem | Remove `NULL` or use `NOT EXISTS` |
| Pulling IDs into Python | Application code feels easier | Keep set operations in SQL |
| Assuming `NOT EXISTS` is always faster | Treating syntax as an execution plan | Inspect `EXPLAIN` |
| Using `LEFT JOIN` and forgetting join predicates | Incorrect matches can change the result | Verify anti-join semantics carefully |
| Omitting tenant filters | Assuming outer predicates propagate | Scope every relevant relation |
| Ignoring concurrency in batch selection | Existence check is mistaken for locking | Use transactions and locking where required |
| Adding `DISTINCT` to hide duplicate joins | Treating symptoms rather than semantics | Use anti-join semantics directly |

## Production Considerations

### Reliability

For exclusion logic, correctness is more important than minor syntactic differences.

A `NOT IN` query that silently returns no rows because of a newly introduced nullable value can cause:

- Incorrect API responses.
- Missing background jobs.
- Failed reconciliation.
- Incorrect reports.
- Data synchronization gaps.
- Business workflows being skipped.

Schema changes should therefore be evaluated against dependent SQL predicates.

### Scalability

For large datasets:

- Index the columns used to correlate the subquery.
- Keep predicates selective where possible.
- Avoid application-side ID materialization.
- Inspect execution plans.
- Monitor query latency as cardinality grows.
- Test against production-like distributions rather than small development databases.

### Monitoring

Track production queries that use anti-join logic when they are on critical paths.

Useful metrics include:

- Query latency.
- Rows returned.
- Rows examined.
- Buffer/cache activity.
- Database CPU.
- Lock waits.
- Query frequency.
- Error rates.

A query that performs well at 100,000 rows may behave very differently at 100 million rows.

### Schema Design

If a relationship should never contain `NULL`, enforce it at the database level:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id)
);
```

A database constraint is stronger than relying on application validation.

This can make the semantics of `NOT IN` safer, but `NOT EXISTS` can still be preferable because it communicates the business requirement more directly.

## Interview Traps

### Why can `NOT IN` return no rows unexpectedly?

Because the subquery may return `NULL`.

For example:

```sql
WHERE id NOT IN (1, 2, NULL)
```

can evaluate to `UNKNOWN` for values other than `1` and `2`, causing them to be filtered out.

### Why is `NOT EXISTS` safer?

`NOT EXISTS` tests whether a matching row exists.

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

The selected value inside the subquery is irrelevant. A nullable unrelated column does not introduce the same `NOT IN` membership problem.

### Is `NOT IN` always wrong?

No.

If the subquery result is guaranteed to contain no `NULL` values, `NOT IN` can be correct and performant.

The important question is whether that non-null guarantee is real and enforced.

### Is `NOT EXISTS` always faster?

No.

The database optimizer may transform different formulations into similar anti-join strategies.

Performance should be established with execution plans and realistic workloads.

### Why doesn't `DISTINCT` fix the `NULL` problem?

Consider:

```sql
NOT IN (
    SELECT DISTINCT customer_id
    FROM orders
)
```

`DISTINCT` removes duplicate values, but it does not remove `NULL`.

The result can still contain:

```text
101
205
NULL
```

If `NULL` is the problem, use:

```sql
WHERE customer_id IS NOT NULL
```

or, preferably for absence checks, use `NOT EXISTS`.

### What is the difference between an anti-join and `NOT IN`?

An anti-join describes the relational operation:

> Return rows from one relation that have no matching row in another relation.

`NOT IN` is one SQL expression that can represent certain forms of this requirement.

`NOT EXISTS` and `LEFT JOIN ... IS NULL` can also express anti-join semantics.

## Key Takeaways

- **`NOT IN` performs set exclusion, but a single `NULL` in the subquery can turn expected `FALSE` comparisons into `UNKNOWN` and remove rows unexpectedly.**
- **For "no matching related row exists" requirements, prefer `NOT EXISTS` because it directly expresses anti-join semantics and avoids the `NOT IN` `NULL` trap.**
- **`NOT IN` is safe when the subquery result is guaranteed to be non-null; enforce that guarantee through schema constraints or explicit predicates when appropriate.**
- **Do not assume `NOT IN`, `NOT EXISTS`, or `LEFT JOIN ... IS NULL` has universally better performance; inspect execution plans and test with production-scale data.**
- **For production systems, preserve tenant boundaries, index correlated lookup columns, keep set operations in the database, and account for concurrency in batch-processing workflows.**