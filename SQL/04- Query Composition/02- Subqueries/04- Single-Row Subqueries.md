# 04- Single-Row Subqueries

## Overview

A **single-row subquery** is a subquery designed to return at most one row. It is commonly used when the outer query needs to compare a value against one related row or against a single derived result.

Single-row subqueries are especially useful when the business rule is naturally expressed as:

> "Find the row whose value is related to one specific row returned by another query."

For example, finding employees who earn more than a particular employee:

```sql
SELECT
    e.id,
    e.name,
    e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT salary
    FROM employees
    WHERE id = 42
);
```

The inner query must identify a single employee. If employee `42` is uniquely identified by a primary key, the database can safely use its salary as the comparison value.

Single-row subqueries are closely related to scalar subqueries, but the terminology emphasizes a different concern:

- **Scalar subquery**: one row and one column, used as a single value.
- **Single-row subquery**: at most one row, potentially involving multiple columns and therefore usable with row-value comparisons.

## Single-Row vs Scalar Subqueries

These concepts overlap but are not identical.

A scalar subquery:

```sql
(
    SELECT salary
    FROM employees
    WHERE id = 42
)
```

returns:

```text
1 row × 1 column
```

A single-row subquery can return multiple columns:

```sql
(
    SELECT department_id, salary
    FROM employees
    WHERE id = 42
)
```

The outer query can compare the resulting row:

```sql
SELECT
    e.id,
    e.name
FROM employees AS e
WHERE (e.department_id, e.salary) = (
    SELECT department_id, salary
    FROM employees
    WHERE id = 42
);
```

The subquery still needs to return at most one row.

| Type | Rows | Columns | Typical usage |
|---|---:|---:|---|
| Scalar subquery | 1 | 1 | Value comparison |
| Single-row subquery | ≤1 | 1+ | Row/value comparison |
| Multi-row subquery | 0+ | 1+ | `IN`, `ANY`, `ALL`, etc. |

## Why Single-Row Subqueries Exist

Single-row subqueries allow one query to derive a reference row and then use that row in an outer operation.

Typical use cases include:

- Comparing against a specific entity.
- Comparing multiple columns simultaneously.
- Finding records relative to a reference record.
- Selecting a single configuration row.
- Comparing an entity with its parent or peer.
- Expressing business rules involving one uniquely identified record.

They are useful when the relationship is conceptually **one outer result to one reference result**.

## Basic Syntax

A common form is:

```sql
SELECT ...
FROM table_a
WHERE column = (
    SELECT column
    FROM table_b
    WHERE condition
);
```

For multiple columns:

```sql
SELECT ...
FROM table_a
WHERE (column_a, column_b) = (
    SELECT column_a, column_b
    FROM table_b
    WHERE condition
);
```

The inner query must satisfy the cardinality expected by the outer expression.

## Example: Compare Against One Employee

Suppose an employee table contains:

```text
employees
---------
id
name
department_id
salary
```

To find employees earning more than employee `42`:

```sql
SELECT
    e.id,
    e.name,
    e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT salary
    FROM employees
    WHERE id = 42
);
```

The inner query returns one salary because `id` is a primary key.

Conceptually:

```text
employee 42
    │
    ▼
salary = 120000
    │
    ▼
compare every employee
    │
    ▼
salary > 120000
```

## Cardinality Is the Critical Property

A single-row subquery is only valid when its predicates guarantee the required cardinality.

This is safe when querying by a primary key:

```sql
SELECT (
    SELECT salary
    FROM employees
    WHERE id = 42
);
```

because:

```text
employees.id → PRIMARY KEY → at most one row
```

This may be unsafe:

```sql
SELECT (
    SELECT salary
    FROM employees
    WHERE department_id = 10
);
```

because department `10` may contain many employees.

The database may reject the query with an error such as:

```text
more than one row returned by a subquery used as an expression
```

Do not treat `LIMIT 1` as a generic solution to this problem. If the business rule requires one row, the schema or predicate should establish why exactly one row exists.

## Enforcing Single-Row Semantics with Constraints

Suppose an application expects one active configuration per environment.

Instead of relying on:

```sql
SELECT *
FROM configuration
WHERE environment = 'production'
  AND active = true
LIMIT 1;
```

enforce the invariant in the database.

In PostgreSQL:

```sql
CREATE UNIQUE INDEX uq_active_configuration_environment
    ON configuration (environment)
    WHERE active = true;
```

Now a query such as:

```sql
SELECT setting_value
FROM configuration
WHERE environment = 'production'
  AND active = true;
```

has a database-backed uniqueness guarantee.

This is significantly safer than relying on application code to maintain uniqueness.

## Row-Value Comparisons

Single-row subqueries become particularly useful with row-value expressions.

Consider:

```sql
employees (
    id,
    department_id,
    salary
)
```

To find employees with the same department and salary as employee `42`:

```sql
SELECT
    e.id,
    e.name
FROM employees AS e
WHERE (e.department_id, e.salary) = (
    SELECT department_id, salary
    FROM employees
    WHERE id = 42
);
```

The comparison is performed as a tuple:

```text
(outer department_id, outer salary)
              =
(reference department_id, reference salary)
```

This is often clearer than writing separate predicates:

```sql
WHERE e.department_id = (
    SELECT department_id
    FROM employees
    WHERE id = 42
)
AND e.salary = (
    SELECT salary
    FROM employees
    WHERE id = 42
);
```

The row-value form avoids repeating the same subquery.

## Row Comparisons and `NULL`

SQL's three-valued logic applies to row comparisons as well.

Suppose the reference employee has:

```text
department_id = 10
salary = NULL
```

Then:

```sql
WHERE (e.department_id, e.salary) = (
    SELECT department_id, salary
    FROM employees
    WHERE id = 42
);
```

may not behave like ordinary application-language equality because `NULL` represents an unknown value.

If the business rule requires null-safe comparison, PostgreSQL provides:

```sql
WHERE (e.department_id, e.salary) IS NOT DISTINCT FROM (
    SELECT department_id, salary
    FROM employees
    WHERE id = 42
);
```

Use null-safe semantics intentionally; do not assume SQL equality behaves like Python or Java equality.

## Single-Row Subqueries in `WHERE`

A common pattern is comparing against a reference row.

```sql
SELECT
    p.id,
    p.name,
    p.price
FROM products AS p
WHERE p.price > (
    SELECT price
    FROM products
    WHERE id = 100
);
```

This can express rules such as:

- Products more expensive than a reference product.
- Employees earning more than a reference employee.
- Orders larger than a particular order.
- Accounts created after a reference account.

The reference row should normally be identified through a unique key.

## Single-Row Subqueries in `HAVING`

The same idea can be applied to aggregated values.

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_spend
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT SUM(total_amount)
    FROM orders
    WHERE customer_id = 42
);
```

The inner query produces one aggregate result.

This expresses:

> Find customers whose total spending exceeds customer `42`'s spending.

Aggregates naturally collapse the inner result to one row.

## Single-Row Subqueries in `UPDATE`

A single-row subquery can provide a value for an update.

For example, copy the tax rate from a configuration table:

```sql
UPDATE products
SET tax_rate = (
    SELECT tax_rate
    FROM tax_configuration
    WHERE country_code = 'IN'
      AND product_category = products.category
)
WHERE country_code = 'IN';
```

This is a correlated subquery because the inner query references the outer row:

```text
products.category
        │
        ▼
tax_configuration
        │
        ▼
tax_rate
        │
        ▼
products.tax_rate
```

The inner query must still return at most one row for each product.

If multiple configuration rows can match, the schema should generally prevent that ambiguity.

## Single-Row Subqueries in `DELETE`

The same pattern can be used to identify records relative to a reference entity.

```sql
DELETE FROM audit_events
WHERE created_at < (
    SELECT created_at
    FROM audit_events
    WHERE id = :reference_event_id
);
```

This deletes events older than the reference event.

In production, destructive queries should be validated carefully before execution:

```sql
SELECT COUNT(*)
FROM audit_events
WHERE created_at < (
    SELECT created_at
    FROM audit_events
    WHERE id = :reference_event_id
);
```

Then execute the `DELETE` inside an appropriate transaction.

## Single-Row Subqueries vs JOINs

Many single-row subqueries can be rewritten using JOINs.

Subquery:

```sql
SELECT
    e.id,
    e.name
FROM employees AS e
WHERE e.salary > (
    SELECT salary
    FROM employees
    WHERE id = 42
);
```

A JOIN-based version can use a second reference to the table:

```sql
SELECT
    e.id,
    e.name
FROM employees AS e
CROSS JOIN employees AS reference_employee
WHERE reference_employee.id = 42
  AND e.salary > reference_employee.salary;
```

Neither form is universally faster.

The subquery often communicates the intent more directly:

```text
compare employee against reference employee
```

The JOIN form can become more useful when several attributes from the reference row are required.

## Single-Row Subqueries vs `IN`

Do not confuse:

```sql
WHERE department_id = (
    SELECT department_id
    FROM employees
    WHERE id = 42
)
```

with:

```sql
WHERE department_id IN (
    SELECT department_id
    FROM employees
    WHERE id = 42
)
```

The first expresses a **single value**.

The second expresses **membership in a set**.

For a genuinely single-row relationship, `=` communicates the stronger cardinality expectation.

For multiple possible rows, use `IN`, `EXISTS`, `ANY`, or another set-oriented construct according to the required semantics.

## Single-Row Subqueries vs `EXISTS`

`EXISTS` answers:

> Does at least one matching row exist?

A single-row subquery answers:

> What value does this one reference row contain?

For example:

```sql
WHERE department_id = (
    SELECT department_id
    FROM employees
    WHERE id = 42
)
```

is fundamentally different from:

```sql
WHERE EXISTS (
    SELECT 1
    FROM employees
    WHERE employees.id = 42
      AND employees.department_id = e.department_id
)
```

Use `EXISTS` when the value itself is irrelevant and only existence matters.

## Selecting the "Latest" Single Row

A frequent production pattern is selecting one related row using ordering:

```sql
SELECT
    u.id,
    u.email,
    (
        SELECT o.id
        FROM orders AS o
        WHERE o.user_id = u.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS latest_order_id
FROM users AS u;
```

This deliberately converts a potentially multi-row relationship into one deterministic row.

The ordering is important.

Avoid:

```sql
ORDER BY created_at DESC
```

when timestamps can tie and the selected row must be deterministic.

Prefer:

```sql
ORDER BY created_at DESC, id DESC
```

with a suitable index when justified:

```sql
CREATE INDEX idx_orders_user_created_id
    ON orders (user_id, created_at DESC, id DESC);
```

## `LIMIT 1` and Business Semantics

`LIMIT 1` is appropriate when the requirement genuinely means:

> Select the best matching row according to this ordering.

For example:

```sql
ORDER BY created_at DESC, id DESC
LIMIT 1
```

means:

> Select the most recently created order, breaking ties by the highest ID.

It is not appropriate when the requirement means:

> There must be exactly one matching row.

For the latter, enforce uniqueness.

| Requirement | Appropriate approach |
|---|---|
| Exactly one entity must exist | Primary/unique constraint |
| Any matching row is acceptable | `LIMIT 1` may be sufficient |
| Latest row | `ORDER BY ... DESC LIMIT 1` |
| Highest-priority row | Explicit priority ordering + `LIMIT 1` |
| Detect whether duplicates exist | Do not hide them with `LIMIT 1` |

## Production Performance

A single-row subquery is not automatically expensive.

Consider:

```sql
SELECT
    u.id,
    (
        SELECT o.created_at
        FROM orders AS o
        WHERE o.user_id = u.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS last_order_at
FROM users AS u;
```

With an appropriate index, the database may efficiently locate the first matching order for each user.

Without an appropriate access path, the database may need substantially more work.

The relevant questions are:

- How many outer rows are processed?
- How selective is the inner predicate?
- Is the correlation column indexed?
- Does the ordering match an index?
- How many loops occur?
- How much data is read?
- Is the query executed frequently?

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    u.id,
    (
        SELECT o.created_at
        FROM orders AS o
        WHERE o.user_id = u.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS last_order_at
FROM users AS u;
```

Do not optimize based solely on the appearance of a subquery.

## Query Planner Considerations

The SQL describes logical semantics. The database optimizer chooses the physical execution strategy.

Depending on the database and query, an optimizer may:

- Transform a subquery.
- Decorrelate a correlated subquery.
- Use an index lookup.
- Use a join internally.
- Materialize an intermediate result.
- Execute a nested-loop strategy.
- Reuse or cache intermediate results where possible.

Therefore:

> "Subquery means nested loop" is an incorrect performance assumption.

Likewise:

> "JOIN is always faster than a subquery" is not a valid engineering rule.

The execution plan and production workload determine the actual cost.

## Indexing Strategy

Indexes should support the predicates and access patterns used by the query.

For:

```sql
SELECT
    u.id,
    (
        SELECT o.created_at
        FROM orders AS o
        WHERE o.user_id = u.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS last_order_at
FROM users AS u;
```

an index such as:

```sql
CREATE INDEX idx_orders_user_created_id
    ON orders (user_id, created_at DESC, id DESC);
```

can support:

```text
user_id filtering
        +
created_at ordering
        +
id tie-breaking
```

Index design should consider:

- Write overhead.
- Storage consumption.
- Existing indexes.
- Query selectivity.
- Table size.
- Query frequency.
- Actual execution plans.

Avoid adding indexes solely because a query contains a subquery.

## ORM Example with Django

Django's `Subquery` and `OuterRef` can represent single-row subqueries.

```python
from django.db.models import OuterRef, Subquery

latest_order = (
    Order.objects
    .filter(user_id=OuterRef("pk"))
    .order_by("-created_at", "-id")
    .values("id")[:1]
)

users = User.objects.annotate(
    latest_order_id=Subquery(latest_order)
)
```

The slice:

```python
[:1]
```

limits the subquery to one row.

This is appropriate because the business requirement is explicitly:

> Return the latest order.

It would be inappropriate to use `[:1]` merely to hide duplicate rows when the underlying data should be unique.

## Practical Backend Example

Suppose a FastAPI endpoint needs to return accounts with their most recent login:

```text
GET /accounts
```

A PostgreSQL query might be:

```sql
SELECT
    a.id,
    a.email,
    (
        SELECT l.logged_in_at
        FROM login_events AS l
        WHERE l.account_id = a.id
        ORDER BY l.logged_in_at DESC, l.id DESC
        LIMIT 1
    ) AS last_login_at
FROM accounts AS a
ORDER BY a.id
LIMIT :limit
OFFSET :offset;
```

A supporting index:

```sql
CREATE INDEX idx_login_events_account_logged_in
    ON login_events (account_id, logged_in_at DESC, id DESC);
```

The API layer should use parameterized SQL rather than interpolating values into the query.

For example, with a database library that supports named parameters:

```python
query = """
SELECT
    a.id,
    a.email,
    (
        SELECT l.logged_in_at
        FROM login_events AS l
        WHERE l.account_id = a.id
        ORDER BY l.logged_in_at DESC, l.id DESC
        LIMIT 1
    ) AS last_login_at
FROM accounts AS a
ORDER BY a.id
LIMIT :limit
OFFSET :offset
"""
```

The important production concern is not merely the subquery syntax. It is the complete path:

```text
HTTP request
    │
    ▼
FastAPI handler
    │
    ▼
Parameterized SQL
    │
    ▼
PostgreSQL planner
    │
    ▼
Indexed lookup
    │
    ▼
Result set
    │
    ▼
API response
```

## Security Considerations

Single-row subqueries do not introduce a special SQL-injection vulnerability, but dynamically constructed SQL still does.

Bad:

```python
query = f"""
SELECT *
FROM users
WHERE id = {user_id}
"""
```

Prefer parameterized queries through the database driver or ORM.

```python
query = """
SELECT *
FROM users
WHERE id = %s
"""
cursor.execute(query, [user_id])
```

Also consider authorization boundaries. A query that correctly retrieves one row can still expose data the requesting user should not access.

For multi-tenant systems, tenant isolation must be part of the query or enforced through appropriate database mechanisms.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Assuming a predicate guarantees one row without a constraint | Application logic is mistaken for database integrity | Use PK/unique constraints |
| Using `LIMIT 1` to hide duplicates | Prevents an error but hides corrupted state | Enforce the business invariant |
| Omitting `ORDER BY` with `LIMIT 1` | Assumes natural row order | Define deterministic selection |
| Treating `=` like `IN` | Confuses scalar and set semantics | Use the operator matching cardinality |
| Ignoring `NULL` | Assumes application-style equality | Account for SQL three-valued logic |
| Repeating the same subquery | Makes queries unnecessarily complex | Use row-value comparison, JOIN, CTE, or aggregation |
| Assuming subqueries are always slower | Relies on syntax rather than execution plans | Inspect `EXPLAIN` |
| Forgetting indexes on correlated predicates | Works on small datasets | Validate query plans at realistic scale |
| Performing the lookup in application code | Can introduce N+1 queries | Keep set-oriented work in SQL where appropriate |

## Interview Traps

### What happens if a single-row subquery returns multiple rows?

If it is being used in a scalar or row comparison context that expects one row, the database raises a cardinality error.

### Is `LIMIT 1` the same as guaranteeing one row?

No. `LIMIT 1` limits the result returned by the query; it does not prove that the underlying data contains only one matching row.

### When should `LIMIT 1` be used?

When the business rule intentionally selects one row from potentially many, such as the latest or highest-priority record, and the ordering is explicit.

### Are single-row subqueries always slower than JOINs?

No. Query performance depends on the optimizer, indexes, cardinality, data distribution, and workload.

### Why are primary keys important for single-row subqueries?

They provide a database-enforced guarantee that a lookup by that key returns at most one row.

### What is the difference between a scalar and single-row subquery?

A scalar subquery produces one column from one row and behaves as a value. A single-row subquery can return multiple columns and can participate in row-value comparisons.

## Operational Best Practices

For production systems:

- Prefer database constraints for cardinality guarantees.
- Use explicit `ORDER BY` whenever selecting one row from many.
- Index correlation predicates when query plans justify it.
- Use parameterized SQL.
- Test with realistic data volumes.
- Inspect `EXPLAIN (ANALYZE, BUFFERS)` for important PostgreSQL queries.
- Monitor query latency, execution frequency, database CPU, I/O, and connection utilization.
- Avoid application-level N+1 query patterns.
- Re-evaluate correlated queries as table sizes and traffic increase.
- Keep destructive operations inside appropriate transactions and validate affected-row counts.

## Key Takeaways

- **Single-row subqueries are designed to return at most one row and are useful for comparing outer rows against a specific reference row.**
- **Database constraints such as primary keys and unique indexes should establish cardinality guarantees; `LIMIT 1` should not hide unexpected duplicates.**
- **When selecting one row from many, use deterministic `ORDER BY` semantics, especially for patterns such as "latest record."**
- **Single-row subqueries can return multiple columns through row-value comparisons, while scalar subqueries represent a single value.**
- **Performance depends on the execution plan, indexes, cardinality, and workload—not simply on whether the query uses a subquery or JOIN.**