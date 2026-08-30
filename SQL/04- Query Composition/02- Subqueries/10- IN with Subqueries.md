# 10- IN with Subqueries

## Overview

`IN` with a subquery is used when a query needs to test whether a value belongs to a set of values produced by another query.

The general pattern is:

```sql
SELECT ...
FROM ...
WHERE column IN (
    SELECT column
    FROM ...
);
```

This is particularly useful when the application needs to filter rows based on a related dataset without explicitly returning that dataset to the application.

Typical backend use cases include:

- Find orders belonging to enterprise customers.
- Find users who belong to selected organizations.
- Find products that have appeared in qualifying orders.
- Find accounts associated with active subscriptions.
- Restrict records to a dynamically calculated set of IDs.

For production systems, `IN` is less about memorizing syntax and more about understanding **set semantics, NULL behavior, query optimization, cardinality, and when `EXISTS` or a `JOIN` expresses the requirement better**.

## Basic Syntax

```sql
SELECT
    customer_id,
    email
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'paid'
);
```

The inner query produces a set:

```text
orders
   │
   │ status = 'paid'
   ▼
customer_id values
   │
   ▼
IN (...)
   │
   ▼
customers
```

The outer query returns customers whose `customer_id` occurs in the subquery result.

The subquery can return multiple rows. That is the key distinction from a scalar subquery.

## Why `IN` with a Subquery Exists

Without a subquery, applications often retrieve IDs first and then issue another query:

```python
customer_ids = get_paid_customer_ids()
customers = get_customers(customer_ids)
```

This can create:

- Additional network round trips.
- Large intermediate ID lists.
- Application memory usage.
- Race conditions between separate queries.
- More complicated application code.

A single SQL statement keeps the filtering operation inside the database:

```sql
SELECT *
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'paid'
);
```

The database optimizer can then choose an execution strategy appropriate for the data.

## `IN` with a Multi-Row Subquery

The subquery used with `IN` normally returns one column and zero or more rows.

For example:

```sql
SELECT
    id,
    name
FROM products
WHERE id IN (
    SELECT product_id
    FROM order_items
    WHERE quantity >= 10
);
```

Conceptually:

```text
Subquery:
product_id
----------
101
205
310

Outer query:
product.id IN (101, 205, 310)
```

The subquery does not need to return unique values for `IN` to work correctly.

For example:

```text
101
101
205
310
```

has the same membership meaning as:

```text
101
205
310
```

However, unnecessary duplicates can affect intermediate work depending on the optimizer and execution strategy.

## `IN` Is a Membership Predicate

The important semantic question is:

> Does this value belong to the set returned by the subquery?

Example:

```sql
SELECT
    id,
    email
FROM users
WHERE id IN (
    SELECT user_id
    FROM user_roles
    WHERE role = 'admin'
);
```

This means:

```text
Return users
WHERE user.id
belongs to
the set of user_roles.user_id
for admin roles.
```

It does not mean that the outer row must be joined to every matching subquery row.

That distinction becomes important when the relationship is one-to-many.

## `IN` vs `JOIN`

The following queries can express similar membership requirements:

```sql
SELECT c.*
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.status = 'paid'
);
```

and:

```sql
SELECT DISTINCT c.*
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

But they do not have identical semantics.

The `JOIN` produces a row for each matching order before `DISTINCT` removes duplicates.

`IN` directly expresses membership.

### Practical Comparison

| Requirement | Typical choice |
|---|---|
| Test membership in another result set | `IN` |
| Need columns from both tables | `JOIN` |
| Need to avoid one-to-many duplication | `IN` or `EXISTS` |
| Need only existence of a related row | `EXISTS` |
| Need aggregation across related rows | `JOIN` or grouped query |
| Need complex relationship traversal | `JOIN` |
| Need a simple semi-join condition | `IN` / `EXISTS` |

Do not choose `JOIN` merely because the tables are related. Choose the construct that best represents the required result semantics.

## `IN` vs `EXISTS`

A common equivalent formulation is:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.status = 'paid'
);
```

Using `EXISTS`:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
);
```

Both express:

> Return customers with at least one paid order.

### Semantic Difference

`IN` asks:

```text
Is c.id a member of this set?
```

`EXISTS` asks:

```text
Does at least one matching row exist?
```

For a simple non-NULL membership condition, the database may optimize both into similar physical strategies.

Do not assume one is universally faster.

Use:

- `IN` when set membership is the clearest expression.
- `EXISTS` when existence of a correlated related row is the actual business condition.

## The `NOT IN` Trap

`NOT IN` has particularly important `NULL` semantics.

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

If the subquery returns:

```text
101
205
NULL
```

then comparisons can become `UNKNOWN` because SQL uses three-valued logic.

As a result, rows you expect to be returned may disappear.

This is one of the most important interview and production traps involving `IN`.

### Prefer `NOT EXISTS` for Anti-Membership

Instead of:

```sql
SELECT c.*
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

prefer:

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

`NOT EXISTS` directly expresses:

> There is no matching order for this customer.

This avoids the problematic `NULL` behavior of `NOT IN`.

## `NULL` Semantics with `IN`

`IN` also interacts with `NULL`.

Consider:

```sql
SELECT *
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM orders
);
```

If the subquery contains `NULL`, that does not make every comparison true.

For a particular outer value:

```text
id = 101
subquery = {101, 205, NULL}
```

the result is `TRUE`.

For:

```text
id = 999
subquery = {101, 205, NULL}
```

the membership test can evaluate to `UNKNOWN`, not `FALSE`.

`WHERE` retains only rows for which the predicate evaluates to `TRUE`.

This distinction matters especially when switching between `IN` and `NOT IN`.

## Filtering by Related Business State

A common production use case is filtering entities based on a related business state.

For example:

> Return accounts that have at least one currently active subscription.

```sql
SELECT
    id,
    account_name
FROM accounts
WHERE id IN (
    SELECT account_id
    FROM subscriptions
    WHERE status = 'active'
);
```

This keeps the business condition in the database.

If the API is:

```text
GET /accounts?subscription_status=active
```

the application can translate the request into a parameterized query rather than retrieving subscription IDs into application memory.

## Multiple Conditions in the Subquery

The subquery can contain its own filtering logic.

```sql
SELECT
    id,
    email
FROM users
WHERE id IN (
    SELECT user_id
    FROM login_events
    WHERE event_type = 'successful_login'
      AND occurred_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
);
```

The outer query asks:

> Which users belong to the set of users with a successful login during the last 30 days?

This pattern is useful for:

- Feature eligibility.
- Customer segmentation.
- Security reporting.
- Activity-based filtering.
- Data migration selection.
- Batch processing.

## Combining Multiple `IN` Conditions

Multiple membership predicates can be combined:

```sql
SELECT
    id,
    email
FROM users
WHERE id IN (
    SELECT user_id
    FROM user_roles
    WHERE role = 'admin'
)
AND organization_id IN (
    SELECT id
    FROM organizations
    WHERE status = 'active'
);
```

This is valid, but complex queries with several independent subqueries should be reviewed for:

- Readability.
- Execution plan complexity.
- Repeated scans.
- Index requirements.
- Whether joins or CTEs provide a clearer structure.

Do not decompose a relationship into many independent `IN` predicates if the business relationship is better represented by a single relational expression.

## Correlated `IN` Subqueries

An `IN` subquery can be correlated with the outer query, although this is less common than correlated `EXISTS`.

For example:

```sql
SELECT
    p.id,
    p.name
FROM products AS p
WHERE p.id IN (
    SELECT oi.product_id
    FROM order_items AS oi
    JOIN orders AS o
        ON o.id = oi.order_id
    WHERE o.customer_id = p.preferred_customer_id
);
```

The subquery references:

```sql
p.preferred_customer_id
```

from the outer query.

Correlated subqueries can be more difficult to reason about and may produce more complex execution plans.

If the relationship can be expressed more directly with joins or `EXISTS`, prefer the clearer form.

## Subqueries Returning the Wrong Number of Columns

`IN` normally compares one expression against one-column subquery results:

```sql
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
);
```

This is invalid:

```sql
WHERE customer_id IN (
    SELECT customer_id, order_date
    FROM orders
);
```

The left-hand expression has one value, while the subquery produces two columns.

Some SQL dialects support row-value comparisons:

```sql
WHERE (customer_id, order_date) IN (
    SELECT customer_id, order_date
    FROM orders
);
```

This is a different construct and should be used only when the database and schema semantics support it.

## Empty Subquery Results

An empty subquery result is valid.

For:

```sql
SELECT *
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'cancelled'
);
```

if the subquery returns zero rows, no customer satisfies the membership predicate.

Conceptually:

```text
IN (empty set)
      ↓
FALSE for every non-NULL outer value
```

This is often useful for dynamic filters because no special application-side handling is required.

## Performance Considerations

`IN` does not inherently mean that the database constructs a massive in-memory list.

The optimizer can transform the query into different physical strategies depending on the database.

Possible strategies include:

- Hash-based membership testing.
- Nested-loop execution.
- Index lookups.
- Semi-join transformations.
- Materialization.
- Join-based execution.
- Other optimizer-specific strategies.

Therefore:

> SQL syntax describes the requested semantics; the execution plan determines how the database actually performs the work.

### Index the Relevant Columns

For:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.status = 'paid'
);
```

useful indexes may include:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

If the workload frequently filters by status first:

```sql
CREATE INDEX idx_orders_status_customer_id
ON orders (status, customer_id);
```

The best index depends on workload and data distribution.

For PostgreSQL, inspect the plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.status = 'paid'
);
```

Look for:

- Sequential scans over unexpectedly large tables.
- Poor row-count estimates.
- Expensive hash operations.
- Excessive buffer reads.
- Disk-based operations.
- Unexpected nested loops.
- Large execution-time regressions.

## `IN` with Large Result Sets

A common misconception is:

> "If the subquery returns many rows, `IN` must be slow."

Not necessarily.

For example:

```sql
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
)
```

can be optimized efficiently, especially when the database can use indexes or a semi-join strategy.

The real questions are:

- How large are the underlying tables?
- How selective is the subquery?
- Are appropriate indexes available?
- What does the optimizer estimate?
- How much data is actually processed?
- Does the query fit the workload's latency requirements?

Measure instead of assuming.

## When `JOIN` Is Better

Use a `JOIN` when the query needs attributes from the related table.

For example:

```sql
SELECT
    c.id,
    c.email,
    o.created_at,
    o.total_amount
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

The query needs order information, so a join naturally expresses the requirement.

Using `IN` would unnecessarily hide the related data:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
    WHERE o.status = 'paid'
);
```

The second form is appropriate only if membership is all that is needed.

## When `EXISTS` Is Better

Use `EXISTS` when the business requirement is explicitly:

> Return the outer row if at least one matching related row exists.

For example:

```sql
SELECT
    p.id,
    p.name
FROM products AS p
WHERE EXISTS (
    SELECT 1
    FROM order_items AS oi
    WHERE oi.product_id = p.id
);
```

This avoids producing duplicate product rows when a product appears in many order items.

It also communicates the intent directly.

## When a CTE Is Better

If the subquery contains significant business logic or is reused, a CTE can improve readability:

```sql
WITH eligible_customers AS (
    SELECT DISTINCT customer_id
    FROM orders
    WHERE status = 'paid'
      AND total_amount >= 1000
)
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT customer_id
    FROM eligible_customers
);
```

This can make complex reporting or eligibility logic easier to maintain.

However, do not assume that introducing a CTE automatically improves performance. Check the target database's optimizer behavior and execution plan.

## Security and Multi-Tenancy

Subqueries must respect the same authorization boundaries as the outer query.

For a multi-tenant system:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.tenant_id = :tenant_id
  AND c.id IN (
      SELECT o.customer_id
      FROM orders AS o
      WHERE o.tenant_id = :tenant_id
        AND o.status = :status
  );
```

The tenant restriction must not be omitted from the subquery merely because the outer query is scoped.

Otherwise, the subquery can derive IDs from another tenant and create incorrect cross-tenant behavior.

Use parameterized queries:

```sql
WHERE tenant_id = :tenant_id
```

rather than string interpolation.

## Django ORM

Django provides `Subquery` and `OuterRef` for cases where a subquery is required.

For simple membership filtering, a queryset can often express the same operation directly:

```python
customers = Customer.objects.filter(
    id__in=Order.objects.filter(
        status="paid",
    ).values("customer_id"),
)
```

Conceptually, this corresponds to:

```sql
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'paid'
)
```

For pure existence checks, Django's `Exists` can be a better expression:

```python
from django.db.models import Exists, OuterRef

paid_orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
    status="paid",
)

customers = Customer.objects.filter(
    Exists(paid_orders),
)
```

For production ORM queries:

- Inspect generated SQL for complex expressions.
- Use database indexes appropriate to the actual query.
- Avoid converting large querysets to Python lists merely to feed another query.
- Use `EXPLAIN` when performance matters.
- Test with production-like cardinalities.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Using `NOT IN` with nullable subquery values | `NULL` changes three-valued logic | Prefer `NOT EXISTS` for anti-membership |
| Using `JOIN` when only membership is needed | Tables are related, so join feels natural | Consider `IN` or `EXISTS` |
| Assuming `IN` always materializes a huge list | Confusing SQL semantics with execution strategy | Inspect the execution plan |
| Returning multiple columns from an ordinary `IN` subquery | Misunderstanding subquery shape | Return one column or use a row-value comparison |
| Pulling IDs into Python first | Application-oriented thinking | Let the database perform set membership |
| Ignoring duplicate rows in a join replacement | One-to-many relationships multiply rows | Use `IN`/`EXISTS` when only membership matters |
| Missing tenant filters inside subqueries | Assuming outer authorization automatically propagates | Scope every relevant relation |
| Optimizing based on syntax alone | Assuming one construct is universally faster | Benchmark and inspect `EXPLAIN` |
| Adding `DISTINCT` blindly | Trying to hide join duplication | Fix the relational semantics first |

## Interview Traps

### Is `IN` the same as `EXISTS`?

They can express equivalent logic in many cases, particularly for non-NULL membership tests, but they have different semantics and can produce different execution plans.

`IN` expresses set membership.

`EXISTS` expresses existence of a matching row.

### Which is faster: `IN` or `EXISTS`?

There is no universal answer.

Modern optimizers can transform both into efficient semi-join strategies. Performance depends on:

- Database engine.
- Statistics.
- Indexes.
- Cardinality.
- Selectivity.
- Correlation.
- Data distribution.
- Query shape.

Use the clearer expression first, then verify performance with an execution plan.

### Why is `NOT IN` dangerous with `NULL`?

Because SQL uses three-valued logic.

If the subquery contains `NULL`, comparisons that are neither definitely true nor definitely false can evaluate to `UNKNOWN`. `WHERE` only retains rows where the predicate is `TRUE`.

### Does `IN` require the subquery to return unique values?

No.

Duplicates do not change membership semantics.

However, eliminating unnecessary duplicates can sometimes reduce intermediate work, depending on the execution plan.

### Does `IN` always mean the database builds an in-memory list?

No.

The optimizer may transform the operation into a semi-join, hash operation, index lookup, or another physical strategy.

### When should `EXISTS` be preferred?

When the actual requirement is:

> Does at least one related row satisfy this condition?

`EXISTS` communicates that intent directly and avoids duplicate-row concerns associated with one-to-many joins.

## Key Takeaways

- **`IN` with a subquery expresses set membership and is useful for filtering rows against a dynamically derived set of values.**
- **`IN` and `EXISTS` can have similar performance, but choose based on semantics: membership for `IN`, existence for `EXISTS`.**
- **Treat `NOT IN` with nullable subquery columns as a production hazard; `NOT EXISTS` is usually safer for anti-membership logic.**
- **Do not assume `IN` materializes a large list or is inherently slow; inspect the execution plan, indexes, cardinality, and optimizer behavior.**
- **Keep authorization and tenant-scoping predicates inside subqueries as well as the outer query, and use parameterized SQL throughout.**