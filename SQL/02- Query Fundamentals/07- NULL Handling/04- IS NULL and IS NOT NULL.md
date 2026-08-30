# 04- IS NULL and IS NOT NULL

## Overview

`NULL` represents the absence of a known value in SQL. Because `NULL` is not an ordinary value, it cannot be tested reliably with standard comparison operators such as `=` or `<>`.

SQL provides two dedicated predicates:

```sql
IS NULL
IS NOT NULL
```

They are the correct way to test whether an expression evaluates to `NULL`.

This distinction is fundamental to SQL correctness because:

```sql
column = NULL
```

evaluates to `UNKNOWN`, while:

```sql
column IS NULL
```

evaluates deterministically to `TRUE` or `FALSE`.

In production systems, `IS NULL` and `IS NOT NULL` appear frequently in soft-delete queries, optional relationships, lifecycle timestamps, data-quality checks, partial indexes, reporting queries, and API filtering.

## Why `IS NULL` Exists

SQL uses three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

Suppose:

```sql
SELECT *
FROM users
WHERE email = NULL;
```

For every row, the comparison with `NULL` produces `UNKNOWN`:

```text
email = NULL → UNKNOWN
```

`WHERE` retains only rows whose predicate is `TRUE`, so no rows are returned.

The correct query is:

```sql
SELECT *
FROM users
WHERE email IS NULL;
```

Here the predicate directly tests whether `email` is null.

## Basic Syntax

### `IS NULL`

```sql
SELECT *
FROM users
WHERE phone_number IS NULL;
```

Returns rows where `phone_number` has no value.

### `IS NOT NULL`

```sql
SELECT *
FROM users
WHERE phone_number IS NOT NULL;
```

Returns rows where `phone_number` contains a non-`NULL` value.

The predicates are logically complementary:

```text
IS NULL
    ↓
value is NULL

IS NOT NULL
    ↓
value is not NULL
```

For a normal SQL value, exactly one of these predicates is `TRUE`.

## `=` vs `IS NULL`

This distinction is worth memorizing:

| Predicate | Purpose | Result for `NULL` |
|---|---|---|
| `column = value` | Compare values | `UNKNOWN` when column is `NULL` |
| `column <> value` | Compare inequality | `UNKNOWN` when column is `NULL` |
| `column = NULL` | Incorrect null test | `UNKNOWN` |
| `column <> NULL` | Incorrect null test | `UNKNOWN` |
| `column IS NULL` | Test for `NULL` | `TRUE` |
| `column IS NOT NULL` | Test for non-`NULL` | `FALSE` |

For example:

```sql
-- Incorrect
SELECT *
FROM users
WHERE deleted_at = NULL;

-- Correct
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

## How SQL Evaluates `IS NULL`

Consider:

```text
id | deleted_at
---+---------------------
1  | 2026-08-20 10:00:00
2  | NULL
3  | 2026-08-25 15:30:00
```

Query:

```sql
SELECT id
FROM users
WHERE deleted_at IS NULL;
```

Evaluation:

| `id` | `deleted_at` | `deleted_at IS NULL` |
|---:|---|---|
| 1 | timestamp | FALSE |
| 2 | `NULL` | TRUE |
| 3 | timestamp | FALSE |

Only row `2` is returned.

Unlike ordinary comparisons with `NULL`, `IS NULL` does not produce `UNKNOWN`.

## `IS NOT NULL`

The inverse test is:

```sql
SELECT id
FROM users
WHERE deleted_at IS NOT NULL;
```

Evaluation:

| `id` | `deleted_at` | `deleted_at IS NOT NULL` |
|---:|---|---|
| 1 | timestamp | TRUE |
| 2 | `NULL` | FALSE |
| 3 | timestamp | TRUE |

Rows with an actual timestamp are returned.

## Common Production Pattern: Soft Deletes

A common backend design uses a nullable timestamp:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL,
    deleted_at TIMESTAMPTZ
);
```

The semantics are:

```text
deleted_at IS NULL      → active
deleted_at IS NOT NULL  → soft-deleted
```

The application can query active users with:

```sql
SELECT id, email
FROM users
WHERE deleted_at IS NULL;
```

Soft deletion can then be implemented as:

```sql
UPDATE users
SET deleted_at = CURRENT_TIMESTAMP
WHERE id = :user_id;
```

The record remains available for auditing and recovery, while normal application queries exclude it.

## `IS NULL` With Multiple Conditions

`IS NULL` can be combined with other predicates:

```sql
SELECT *
FROM orders
WHERE cancelled_at IS NULL
  AND shipped_at IS NULL;
```

This could represent:

```text
not cancelled
AND
not shipped
```

provided the schema defines the timestamps with those semantics.

Another example:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL
  AND status = 'active';
```

This explicitly handles the nullable lifecycle field while applying a normal value comparison to `status`.

## `OR` and Nullable Columns

Sometimes the business rule requires treating `NULL` as a valid alternative.

For example:

> Find users whose status is not `suspended`, including users whose status is unknown.

Use:

```sql
SELECT *
FROM users
WHERE status <> 'suspended'
   OR status IS NULL;
```

Without the second predicate:

```sql
WHERE status <> 'suspended'
```

`NULL` rows are excluded because:

```text
NULL <> 'suspended' → UNKNOWN
```

and `WHERE` rejects `UNKNOWN`.

This is a business-rule decision. Do not automatically include `NULL` unless the domain requires it.

## `IS NULL` With `LEFT JOIN`

`IS NULL` is especially useful with outer joins.

Suppose:

```sql
users
-----
id

orders
------
id
user_id
```

To find users who have no orders:

```sql
SELECT u.id
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
WHERE o.id IS NULL;
```

The `LEFT JOIN` preserves users even when there is no matching order. For those users, the right-side columns are populated with `NULL`.

Therefore:

```text
o.id IS NULL
```

identifies unmatched users.

This is a common anti-join pattern.

## `NOT EXISTS` vs `LEFT JOIN ... IS NULL`

The same requirement can often be expressed with `NOT EXISTS`:

```sql
SELECT u.id
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.user_id = u.id
);
```

Both approaches can be valid.

| Pattern | Typical use |
|---|---|
| `LEFT JOIN ... WHERE right.id IS NULL` | Find unmatched rows |
| `NOT EXISTS` | Express anti-join semantics directly |
| `NOT IN` | Use cautiously when nullable values are possible |

`NOT EXISTS` often communicates intent more clearly and avoids the `NULL` hazards associated with `NOT IN`.

The optimizer may produce similar execution plans for equivalent queries, so correctness and plan inspection should drive the final choice.

## `IS NULL` and Indexes

`IS NULL` can use an index depending on the database engine, index definition, statistics, data distribution, and query plan.

For example:

```sql
CREATE INDEX idx_users_deleted_at
ON users (deleted_at);
```

may support:

```sql
SELECT id
FROM users
WHERE deleted_at IS NULL;
```

However, an index is not automatically beneficial.

If almost every row has:

```text
deleted_at IS NULL
```

the predicate may have low selectivity, and the optimizer may prefer a sequential scan.

Always verify important production queries with the database's execution-plan tools.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE deleted_at IS NULL;
```

## Partial Indexes for `IS NULL`

PostgreSQL supports partial indexes, which are particularly useful for soft-delete patterns.

For example:

```sql
CREATE INDEX idx_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

This index contains only active users.

A query such as:

```sql
SELECT id, email
FROM users
WHERE deleted_at IS NULL
  AND email = 'user@example.com';
```

can potentially benefit substantially from the smaller index.

Partial indexes are useful when:

- the predicate is stable and frequently queried;
- only a subset of rows is relevant;
- the full table index would be unnecessarily large;
- the query predicate matches the index predicate.

They are database-specific, so use them deliberately rather than assuming portability across SQL engines.

## `IS NOT NULL` and Index Selectivity

Consider:

```sql
SELECT *
FROM users
WHERE phone_number IS NOT NULL;
```

If almost every user has a phone number, the predicate may be poorly selective.

If only a small fraction of users have a phone number, the predicate may be much more useful for an index.

The important engineering principle is:

> Index usefulness depends on access patterns and selectivity, not merely on whether a predicate can technically use an index.

Do not create indexes solely because a column is nullable.

## `IS NULL` in `JOIN` Conditions

`IS NULL` can also be used directly in join logic.

For example:

```sql
SELECT *
FROM subscriptions AS s
JOIN users AS u
    ON s.user_id = u.id
   AND u.deleted_at IS NULL;
```

This ensures that only active users participate in the join.

For an outer join, placement matters.

Compare:

```sql
SELECT u.id, o.id
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
WHERE o.deleted_at IS NULL;
```

with:

```sql
SELECT u.id, o.id
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
   AND o.deleted_at IS NULL;
```

The second version explicitly says:

> Keep every user, but only match non-deleted orders.

This distinction becomes important when preserving unmatched rows is part of the requirement.

## `IS NULL` in `CASE`

`IS NULL` is useful when converting database state into application-facing labels:

```sql
SELECT
    id,
    CASE
        WHEN deleted_at IS NULL THEN 'active'
        ELSE 'deleted'
    END AS lifecycle_state
FROM users;
```

This is deterministic because `IS NULL` returns a normal Boolean result.

For reporting:

```sql
SELECT
    COUNT(*) FILTER (WHERE deleted_at IS NULL) AS active_users,
    COUNT(*) FILTER (WHERE deleted_at IS NOT NULL) AS deleted_users
FROM users;
```

The `FILTER` syntax shown above is PostgreSQL-specific. Equivalent conditional aggregation can be used in databases with different feature sets.

## `IS NULL` and Aggregates

`IS NULL` is useful for measuring data completeness.

For example:

```sql
SELECT
    COUNT(*) AS total_users,
    COUNT(*) FILTER (WHERE phone_number IS NULL) AS missing_phone_numbers
FROM users;
```

Or using portable-style conditional aggregation:

```sql
SELECT
    COUNT(*) AS total_users,
    SUM(
        CASE
            WHEN phone_number IS NULL THEN 1
            ELSE 0
        END
    ) AS missing_phone_numbers
FROM users;
```

This can support data-quality monitoring.

For example:

```text
total_users = 1,000,000
missing_phone_numbers = 125,000
```

A sudden increase in missing values could indicate an ingestion or API regression.

## `IS NULL` vs Empty Values

`NULL` is different from an empty string:

```text
NULL
''
```

For a text column:

```sql
WHERE name IS NULL
```

finds missing `NULL` values.

It does not find:

```text
''
```

Likewise:

```sql
WHERE name = ''
```

does not find `NULL`.

If the application intentionally allows both states, they must be handled separately:

```sql
WHERE name IS NULL
   OR name = '';
```

However, it is usually better to define clear application and database semantics rather than accumulating multiple representations of "missing."

## `IS NULL` vs Whitespace

An input such as:

```text
'   '
```

is neither `NULL` nor an empty string.

Therefore:

```sql
WHERE name IS NULL
```

does not match it.

If whitespace-only values are invalid according to the domain, normalize them at the application or database boundary rather than relying on every query to account for them.

For example, PostgreSQL can use:

```sql
WHERE NULLIF(BTRIM(name), '') IS NULL;
```

This treats both empty and whitespace-only strings as missing for the purpose of the expression.

Be aware that applying functions to columns can affect ordinary index usage.

## `IS NOT NULL` Does Not Mean "Valid"

Consider:

```sql
WHERE email IS NOT NULL;
```

This only establishes that the value exists.

It does not establish that the value is:

- syntactically valid;
- unique;
- verified;
- non-empty;
- normalized;
- semantically correct.

For example:

```text
email = 'not-an-email'
```

is still `NOT NULL`.

Validation and nullability are separate concerns.

## `IS NULL` and Constraints

A nullable column can be queried with:

```sql
WHERE column IS NULL;
```

If the business domain says the value must always exist, the better solution may be a schema constraint:

```sql
CREATE TABLE customers (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL
);
```

Then:

```sql
WHERE email IS NULL
```

should normally return zero rows because the database itself prevents the invalid state.

This is preferable to relying exclusively on application code.

## `IS NULL` and Foreign Keys

Foreign keys are frequently nullable.

For example:

```sql
CREATE TABLE tickets (
    id BIGINT PRIMARY KEY,
    assigned_agent_id BIGINT REFERENCES agents(id)
);
```

Here:

```text
assigned_agent_id IS NULL
```

can legitimately mean:

```text
ticket has not been assigned
```

A query for unassigned tickets is therefore:

```sql
SELECT *
FROM tickets
WHERE assigned_agent_id IS NULL;
```

A query for assigned tickets is:

```sql
SELECT *
FROM tickets
WHERE assigned_agent_id IS NOT NULL;
```

Whether `NULL` is allowed should be determined by the domain.

If every ticket must have an agent, make the relationship mandatory:

```sql
assigned_agent_id BIGINT NOT NULL
    REFERENCES agents(id)
```

## ORM Usage

Application frameworks generally map null checks to SQL `IS NULL`.

### Django

Django QuerySets use:

```python
User.objects.filter(deleted_at__isnull=True)
```

which corresponds conceptually to:

```sql
WHERE deleted_at IS NULL
```

For non-null values:

```python
User.objects.filter(deleted_at__isnull=False)
```

Avoid trying to express a null check as ordinary equality in application code:

```python
# Do not rely on ordinary equality for SQL NULL semantics.
```

Use the ORM's explicit null predicate.

### SQLAlchemy

With SQLAlchemy:

```python
from sqlalchemy import select

stmt = select(User).where(User.deleted_at.is_(None))
```

For non-null:

```python
stmt = select(User).where(User.deleted_at.is_not(None))
```

The ORM generates the appropriate SQL null predicate.

The important principle is the same across frameworks:

```text
ORM null predicate
        ↓
SQL IS NULL / IS NOT NULL
```

## API Filtering

Suppose a REST API exposes:

```text
GET /users?deleted=false
```

The service layer should translate the business concept into a precise database predicate.

For active users:

```sql
WHERE deleted_at IS NULL
```

For deleted users:

```sql
WHERE deleted_at IS NOT NULL
```

Avoid exposing raw SQL semantics directly through arbitrary query parameters. The API should define what the state means, while the repository layer translates that meaning into SQL.

This keeps API contracts stable even if the database representation changes.

## Common Mistakes

| Mistake | Why It Fails | Correct Approach |
|---|---|---|
| `column = NULL` | Equality with `NULL` produces `UNKNOWN` | Use `column IS NULL` |
| `column <> NULL` | Inequality with `NULL` produces `UNKNOWN` | Use `column IS NOT NULL` |
| Assuming `NULL = NULL` | Ordinary equality does not establish equality | Use `IS NULL` or null-safe equality |
| Assuming `IS NOT NULL` means valid | It only tests existence | Apply domain validation separately |
| Confusing `NULL` and `''` | They represent different states | Handle explicitly or normalize |
| Confusing `NULL` and whitespace | `'   '` is still a string | Normalize or explicitly test whitespace |
| Assuming `IS NULL` always uses an index | Query plans depend on selectivity and statistics | Inspect the execution plan |
| Filtering the right side of a `LEFT JOIN` in `WHERE` | Can eliminate unmatched rows | Put relationship filters in `ON` when required |
| Using `NOT IN` for nullable anti-joins | `NULL` can produce `UNKNOWN` | Prefer `NOT EXISTS` |
| Making every column nullable | Creates ambiguous domain states | Enforce `NOT NULL` where absence is invalid |

## Production Pitfalls

### Treating `NULL` as a Default Value

Do not automatically assume:

```text
NULL → 0
NULL → ''
NULL → FALSE
```

These transformations change semantics.

Use `COALESCE()` only when the business rule explicitly defines such a fallback:

```sql
SELECT COALESCE(display_name, 'Unknown')
FROM users;
```

### Hiding Data Quality Problems

A query such as:

```sql
SELECT COALESCE(phone_number, 'missing')
FROM users;
```

may be useful for presentation, but it can hide the underlying data-quality issue.

For operational systems, distinguish between:

```text
presentation fallback
```

and:

```text
stored data quality
```

### Overusing Nullable Fields

A schema such as:

```sql
status TEXT NULL
```

may create three states:

```text
active
inactive
NULL
```

If the business domain only supports two states, prefer:

```sql
status TEXT NOT NULL
```

with an appropriate constraint.

### Relying on Application-Level Checks

This pattern is unsafe:

```text
application checks value
        ↓
application assumes value is non-null
        ↓
database accepts NULL from another path
```

If nullability is a real invariant, enforce it in the database:

```sql
NOT NULL
```

The database may receive writes from multiple application versions, scripts, migrations, ETL jobs, or administrative tools.

## Performance Guidelines

For high-volume tables:

- Index columns that support important access patterns, not merely nullable columns.
- Consider partial indexes for frequently queried subsets such as active records.
- Check data distribution and selectivity.
- Inspect actual execution plans.
- Avoid unnecessary functions around indexed columns.
- Keep soft-delete predicates consistent across repositories.
- Measure query performance after significant data growth.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, email
FROM users
WHERE deleted_at IS NULL
  AND email = 'user@example.com';
```

The goal is not to force an index but to verify that the optimizer selects an efficient plan for the actual workload.

## Interview Traps

### Why does `column = NULL` return no rows?

Because:

```sql
column = NULL
```

evaluates to `UNKNOWN`, not `TRUE`.

`WHERE` keeps only `TRUE`.

### What is the correct way to find `NULL` values?

```sql
WHERE column IS NULL
```

### What is the correct way to exclude `NULL` values?

```sql
WHERE column IS NOT NULL
```

### Does `IS NOT NULL` guarantee a meaningful value?

No.

It only guarantees that the expression is not `NULL`.

For example:

```text
''
'   '
'unknown'
```

can all be non-`NULL`.

### How can `LEFT JOIN` find records without a relationship?

Use the nullable right-side column generated by the outer join:

```sql
SELECT u.*
FROM users AS u
LEFT JOIN orders AS o
    ON o.user_id = u.id
WHERE o.id IS NULL;
```

Alternatively, use:

```sql
WHERE NOT EXISTS (...)
```

### Can `IS NULL` use an index?

Yes, depending on the database, index, data distribution, and optimizer plan. Always validate important queries with `EXPLAIN`.

## Practical Checklist

Before shipping a query involving nullable columns, verify:

- [ ] `NULL` is tested with `IS NULL` or `IS NOT NULL`.
- [ ] The business meaning of `NULL` is documented.
- [ ] `NULL` is not accidentally treated as `FALSE`, `0`, or `''`.
- [ ] `<>` predicates have the intended behavior for `NULL`.
- [ ] `IN` and especially `NOT IN` have been reviewed for nullable values.
- [ ] `LEFT JOIN` predicates are placed correctly between `ON` and `WHERE`.
- [ ] Required non-null invariants are enforced with `NOT NULL`.
- [ ] Important nullable-column queries have appropriate indexes.
- [ ] Execution plans have been checked for high-volume workloads.
- [ ] Tests include both populated and `NULL` states.

## Key Takeaways

- **Use `IS NULL` and `IS NOT NULL` for null checks; ordinary equality and inequality do not work with `NULL`.**
- **`IS NOT NULL` means only that a value exists; it does not establish that the value is valid, meaningful, or correctly formatted.**
- **`LEFT JOIN ... IS NULL` and `NOT EXISTS` are important patterns for finding records without matching relationships.**
- **Nullable predicates affect query performance and index design, so validate important `IS NULL` queries with execution plans and real data distributions.**
- **Use database constraints such as `NOT NULL` when absence is invalid instead of relying solely on application-level validation.**