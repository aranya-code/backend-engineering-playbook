# 01- Understanding NULL

## Overview

`NULL` represents the absence of a known value in SQL. It is not the same as `0`, an empty string, `FALSE`, or a missing row.

Understanding `NULL` is essential because SQL uses **three-valued logic** rather than ordinary two-valued Boolean logic. Comparisons involving `NULL` can therefore produce `UNKNOWN` instead of `TRUE` or `FALSE`.

This affects:

- `WHERE` filtering.
- `JOIN` conditions.
- Aggregations.
- Sorting.
- Constraints.
- Unique indexes.
- Conditional expressions.
- Application/database boundaries.

A query can be syntactically correct and still produce incorrect results because `NULL` semantics were misunderstood.

## What `NULL` Means

`NULL` indicates that a value is absent, unknown, or not applicable according to the data model.

Consider:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    middle_name TEXT,
    deleted_at TIMESTAMPTZ
);
```

For a user without a middle name:

```text
middle_name = NULL
```

For an active user:

```text
deleted_at = NULL
```

The database is not saying that `deleted_at` is an empty timestamp. It is saying there is no value stored for that attribute.

### `NULL` Is Not Zero

```text
NULL ≠ 0
```

### `NULL` Is Not an Empty String

```text
NULL ≠ ''
```

### `NULL` Is Not `FALSE`

```text
NULL ≠ FALSE
```

These values can have completely different business meanings.

| Value | Typical meaning |
|---|---|
| `NULL` | Unknown, absent, or not applicable |
| `0` | Known numeric value |
| `''` | Known empty string |
| `FALSE` | Known negative Boolean value |
| `'N/A'` | Application-defined textual value |

Do not use sentinel values such as `-1`, `'UNKNOWN'`, or `'1970-01-01'` merely to avoid nullable columns unless the domain explicitly requires that representation.

## Why `NULL` Exists

Real systems frequently have attributes that are not known or do not apply.

Examples:

```text
user.middle_name
user.deleted_at
payment.refunded_at
order.shipped_at
employee.termination_date
```

An order that has not shipped does not necessarily have a shipping timestamp of:

```text
1970-01-01
```

It has no shipping timestamp yet:

```text
shipped_at = NULL
```

This allows the database schema to represent domain state directly instead of encoding state through arbitrary sentinel values.

## Three-Valued Logic

SQL uses three logical outcomes:

| Result | Meaning |
|---|---|
| `TRUE` | Predicate is satisfied |
| `FALSE` | Predicate is not satisfied |
| `UNKNOWN` | Predicate cannot be determined because of `NULL` |

This is the source of many `NULL`-related bugs.

For example:

```sql
SELECT NULL = 10;
```

does not return `FALSE`. The result is `UNKNOWN`.

Likewise:

```sql
SELECT NULL = NULL;
```

also produces `UNKNOWN`.

The key principle is:

> `NULL` does not compare equal to anything using ordinary comparison operators.

## Comparing Values with `NULL`

These expressions are incorrect when checking for `NULL`:

```sql
WHERE deleted_at = NULL
```

```sql
WHERE deleted_at != NULL
```

Use:

```sql
WHERE deleted_at IS NULL
```

and:

```sql
WHERE deleted_at IS NOT NULL
```

Example:

```sql
SELECT id
FROM users
WHERE deleted_at IS NULL;
```

This is the standard way to find active users in a soft-delete model.

## Why `= NULL` Does Not Work

Consider:

```sql
WHERE deleted_at = NULL
```

For a row where:

```text
deleted_at = NULL
```

the comparison becomes conceptually:

```text
NULL = NULL
```

which evaluates to:

```text
UNKNOWN
```

A `WHERE` clause retains rows only when its predicate evaluates to `TRUE`.

Therefore the row is not returned.

The same problem exists with:

```sql
WHERE deleted_at != NULL
```

Use `IS NULL` and `IS NOT NULL` instead.

## `NULL` in `WHERE`

A `WHERE` clause keeps only rows for which the predicate is `TRUE`.

Suppose:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    total_amount NUMERIC(12, 2),
    discount NUMERIC(12, 2)
);
```

If:

```text
discount = NULL
```

then:

```sql
SELECT *
FROM orders
WHERE discount > 0;
```

does not return that row.

The predicate:

```text
NULL > 0
```

is `UNKNOWN`, not `FALSE`.

This distinction matters when combining conditions.

## `NULL` and `AND`

With three-valued logic:

| A | B | `A AND B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE |
| TRUE | UNKNOWN | UNKNOWN |
| FALSE | TRUE | FALSE |
| FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | FALSE |
| UNKNOWN | TRUE | UNKNOWN |
| UNKNOWN | FALSE | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

Example:

```sql
WHERE is_active = TRUE
  AND deleted_at IS NULL
```

The explicit `IS NULL` predicate produces a known Boolean result, which makes the overall condition predictable.

## `NULL` and `OR`

| A | B | `A OR B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | TRUE |
| TRUE | UNKNOWN | TRUE |
| FALSE | TRUE | TRUE |
| FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | UNKNOWN |
| UNKNOWN | TRUE | TRUE |
| UNKNOWN | FALSE | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN |

This becomes important when implementing optional filters.

For example:

```sql
WHERE status = :status
   OR status IS NULL
```

has a very different meaning from:

```sql
WHERE status = :status
```

## `NULL` and `NOT`

`NOT UNKNOWN` remains `UNKNOWN`.

Therefore:

```sql
WHERE NOT (deleted_at = NULL)
```

does not find non-null values.

Use:

```sql
WHERE deleted_at IS NOT NULL
```

Do not attempt to convert ordinary comparison logic into `NULL` checks through `NOT`.

## `NULL` and Arithmetic

Arithmetic involving `NULL` normally produces `NULL`.

```sql
SELECT 100 + NULL;
```

produces:

```text
NULL
```

Similarly:

```sql
SELECT price * quantity
FROM order_items;
```

can produce `NULL` if either operand is `NULL`.

If the domain defines a missing discount as zero, explicitly encode that rule:

```sql
SELECT price - COALESCE(discount, 0)
FROM order_items;
```

Do not assume that SQL will automatically interpret missing numeric values as zero.

## `COALESCE`

`COALESCE()` returns the first non-`NULL` expression.

```sql
SELECT COALESCE(discount, 0)
FROM orders;
```

If:

```text
discount = NULL
```

the result is:

```text
0
```

Multiple fallbacks are possible:

```sql
SELECT COALESCE(
    preferred_name,
    legal_name,
    'Unknown'
)
FROM users;
```

### When to Use `COALESCE`

Use it when a fallback value is part of the intended business or presentation logic.

Examples:

```sql
COALESCE(quantity, 0)
```

```sql
COALESCE(display_name, username)
```

```sql
COALESCE(refund_amount, 0)
```

### When Not to Use It

Do not blindly replace `NULL` everywhere.

For example:

```sql
COALESCE(shipped_at, created_at)
```

changes the meaning of the data. It makes an unshipped order appear as though it shipped at creation time.

A fallback should represent a deliberate domain rule, not merely make the query return a non-null value.

## `NULLIF`

`NULLIF(a, b)` returns `NULL` when `a = b`; otherwise it returns `a`.

Example:

```sql
SELECT NULLIF(discount, 0)
FROM orders;
```

This can be useful when a sentinel value should be interpreted as missing.

A common mathematical use is preventing division by zero:

```sql
SELECT revenue / NULLIF(order_count, 0)
FROM daily_metrics;
```

If `order_count` is zero, the denominator becomes `NULL` rather than causing a division-by-zero error.

## `NULL` and Aggregate Functions

Aggregate functions have important `NULL` semantics.

For most aggregates, `NULL` values are ignored.

```sql
SELECT AVG(score)
FROM reviews;
```

If the scores are:

```text
5
4
NULL
```

the average is calculated from:

```text
5, 4
```

not:

```text
5, 4, 0
```

This distinction is critical for metrics.

| Aggregate | Typical `NULL` behavior |
|---|---|
| `COUNT(*)` | Counts rows, including rows containing `NULL` |
| `COUNT(column)` | Counts non-`NULL` values |
| `SUM(column)` | Ignores `NULL` values |
| `AVG(column)` | Ignores `NULL` values |
| `MIN(column)` | Ignores `NULL` values |
| `MAX(column)` | Ignores `NULL` values |

Example:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(discount) AS orders_with_discount,
    AVG(discount) AS average_discount
FROM orders;
```

These metrics answer different questions.

## `COUNT(*)` vs `COUNT(column)`

This is a common interview and production trap.

Suppose:

```text
id | discount
---+---------
1  | 10
2  | NULL
3  | 20
```

Then:

```sql
COUNT(*)
```

returns:

```text
3
```

while:

```sql
COUNT(discount)
```

returns:

```text
2
```

Use:

```sql
COUNT(*)
```

when counting rows.

Use:

```sql
COUNT(column)
```

when counting rows where that column contains a non-`NULL` value.

## All-`NULL` Aggregations

Consider:

```sql
SELECT SUM(discount)
FROM orders;
```

If every `discount` value is `NULL`, the aggregate may return `NULL`, not zero.

If the business metric requires zero:

```sql
SELECT COALESCE(SUM(discount), 0)
FROM orders;
```

Again, the `COALESCE()` expresses a business interpretation:

```text
no known values → report zero
```

rather than changing the underlying data.

## `NULL` and `GROUP BY`

`GROUP BY` treats `NULL` values as belonging to the same grouping key.

Example:

```sql
SELECT
    status,
    COUNT(*)
FROM orders
GROUP BY status;
```

If multiple orders have:

```text
status = NULL
```

they appear in the same `NULL` group.

This is different from ordinary equality:

```sql
NULL = NULL
```

which evaluates to `UNKNOWN`.

The database's grouping semantics are specifically designed to form groups from equivalent grouping keys.

## `NULL` and `DISTINCT`

`DISTINCT` collapses multiple `NULL` values into one distinct result.

```sql
SELECT DISTINCT status
FROM orders;
```

If the data contains:

```text
pending
completed
NULL
NULL
```

the result contains one `NULL` entry.

Do not interpret this as ordinary `NULL = NULL` comparison. `DISTINCT` has its own duplicate-elimination semantics.

## `NULL` and Sorting

Ordering behavior for `NULL` is database-specific.

PostgreSQL supports explicit control:

```sql
ORDER BY created_at NULLS LAST;
```

or:

```sql
ORDER BY created_at NULLS FIRST;
```

For example:

```sql
SELECT id, shipped_at
FROM orders
ORDER BY shipped_at ASC NULLS LAST;
```

This makes the intended ordering explicit.

Do not rely on implicit `NULL` ordering when query behavior is important to the application.

## `NULL` and Joins

`NULL` can significantly affect joins.

Consider:

```sql
SELECT *
FROM orders o
JOIN customers c
    ON o.customer_id = c.id;
```

If:

```text
o.customer_id = NULL
```

the row does not match a normal equality join.

This is usually desirable because a missing foreign key does not identify a customer.

### `LEFT JOIN`

A `LEFT JOIN` can introduce `NULL` values into columns from the right-side table.

```sql
SELECT
    o.id,
    c.name
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.id;
```

For an order with no matching customer:

```text
c.name = NULL
```

These `NULL`s mean:

> No matching row was found in the joined table.

They do not necessarily mean that the actual customer record contains a `NULL` name.

## `NULL` and `LEFT JOIN` Filters

A common production bug is accidentally converting a `LEFT JOIN` into an effective inner join.

Consider:

```sql
SELECT o.id, c.name
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.id
WHERE c.status = 'active';
```

The `WHERE` condition eliminates rows where `c.status` is `NULL`, including orders without a matching customer.

If the requirement is:

> Return all orders, but only populate the joined customer when that customer is active

the condition may belong in the join:

```sql
SELECT o.id, c.name
FROM orders o
LEFT JOIN customers c
    ON o.customer_id = c.id
   AND c.status = 'active';
```

The placement of a predicate can therefore change query semantics.

## `NULL` and `NOT IN`

`NOT IN` can produce surprising results when the subquery contains `NULL`.

Consider:

```sql
SELECT id
FROM users
WHERE id NOT IN (
    SELECT user_id
    FROM blocked_users
);
```

If `blocked_users.user_id` contains a `NULL`, SQL's three-valued logic can cause rows to evaluate to `UNKNOWN`.

For anti-join semantics, `NOT EXISTS` is often safer:

```sql
SELECT u.id
FROM users u
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_users b
    WHERE b.user_id = u.id
);
```

This explicitly asks whether a matching row exists.

When designing `NOT IN`, verify whether the compared set can contain `NULL`.

## `NULL` and `IN`

`IN` also inherits SQL's three-valued logic.

For example:

```sql
WHERE status IN ('active', NULL)
```

does **not** mean:

```text
status = 'active' OR status IS NULL
```

Use:

```sql
WHERE status = 'active'
   OR status IS NULL
```

or:

```sql
WHERE status IN ('active')
   OR status IS NULL
```

if `NULL` should be included explicitly.

## `NULL` and `BETWEEN`

A comparison involving `NULL` produces `UNKNOWN`.

Therefore:

```sql
WHERE created_at BETWEEN :start AND :end
```

does not match rows where `created_at` is `NULL`.

This is normally correct because an unknown creation timestamp cannot satisfy a temporal boundary.

For timestamp filtering, prefer explicit half-open ranges:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

The same `NULL` behavior applies to the individual comparisons.

## `NULL` and Constraints

`NULL` interacts directly with constraints.

### `NOT NULL`

Use `NOT NULL` when the application requires a value to exist.

```sql
CREATE TABLE payments (
    id BIGINT PRIMARY KEY,
    amount NUMERIC(12, 2) NOT NULL
);
```

This moves an important invariant into the database.

### `CHECK`

`CHECK` constraints have subtle `NULL` behavior.

Consider:

```sql
CHECK (amount > 0)
```

If `amount` is `NULL`, the expression evaluates to `UNKNOWN`, and PostgreSQL permits the row because a `CHECK` constraint is violated only when its expression evaluates to `FALSE`.

If the column must be both present and positive:

```sql
amount NUMERIC(12, 2) NOT NULL
CHECK (amount > 0)
```

This is an important distinction.

## `NULL` and Unique Constraints

`NULL` handling for uniqueness is database-specific and can have significant design implications.

In PostgreSQL, ordinary unique constraints allow multiple `NULL` values because `NULL` values are not treated as equal for ordinary uniqueness enforcement.

For example:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    external_id TEXT UNIQUE
);
```

Multiple users can have:

```text
external_id = NULL
```

while non-null values must remain unique.

This is often exactly what is needed for optional external identifiers.

If the requirement is more specific, such as enforcing uniqueness under a particular `NULL` policy, design the constraint or index explicitly rather than assuming all databases behave identically.

## Partial Indexes and `NULL`

Partial indexes are useful when only a subset of rows is relevant.

For a soft-delete model:

```sql
CREATE INDEX idx_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

This can be useful when most application queries operate only on active users.

The query should use a predicate compatible with the partial-index condition:

```sql
SELECT id, email
FROM users
WHERE deleted_at IS NULL
  AND email = :email;
```

Partial indexes can reduce index size and improve relevant query performance, but they must match actual workload patterns.

## `NULL` in Application Code

Application languages typically have their own null-like value:

| SQL | Python |
|---|---|
| `NULL` | `None` |

A database driver maps SQL `NULL` to the application's null representation.

For example:

```python
if user.deleted_at is None:
    ...
```

Do not use:

```python
if user.deleted_at == 0:
    ...
```

or:

```python
if user.deleted_at == "":
    ...
```

unless those values have explicitly defined domain meanings.

### Django

Django queries translate null checks into SQL:

```python
User.objects.filter(deleted_at__isnull=True)
```

and:

```python
User.objects.filter(deleted_at__isnull=False)
```

For nullable fields, prefer Django's explicit null lookup rather than relying on Python-side filtering.

### FastAPI

When receiving JSON:

```json
{
  "middle_name": null
}
```

the API contract should distinguish between:

```text
field omitted
```

and:

```text
field explicitly set to null
```

These can have different PATCH semantics.

For example:

```text
PATCH {"middle_name": null}
```

may mean:

> Clear the middle name.

while:

```text
PATCH {}
```

may mean:

> Leave the existing middle name unchanged.

This distinction becomes important in production APIs.

## `NULL` in Soft Deletes

Soft deletion is a common backend pattern:

```sql
deleted_at TIMESTAMPTZ NULL
```

Active rows:

```text
deleted_at IS NULL
```

Deleted rows:

```text
deleted_at IS NOT NULL
```

Typical query:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

For systems using soft deletes extensively, consider encapsulating the invariant in repository/query-layer code rather than relying on every engineer to remember the predicate.

Also consider whether unique constraints should apply to deleted records. PostgreSQL partial indexes can help:

```sql
CREATE UNIQUE INDEX users_active_email_unique
ON users (email)
WHERE deleted_at IS NULL;
```

This permits an email to be reused after the previous account is soft-deleted.

## `NULL` in Data Modeling

Nullable columns should represent meaningful domain states.

A useful design question is:

> What does `NULL` mean for this specific attribute?

For example:

```text
shipped_at = NULL
```

could mean:

- Not shipped yet.
- Shipping information unavailable.
- Shipping does not apply.
- Data was not migrated.

Those are not necessarily the same state.

If multiple business states are being encoded through one `NULL`, the schema may be under-modeled.

Sometimes an explicit status is better:

```sql
status TEXT NOT NULL
```

combined with:

```sql
shipped_at TIMESTAMPTZ
```

where:

```text
status = 'pending'
shipped_at = NULL
```

has a clearly defined relationship.

## When Nullable Columns Are Appropriate

Use nullable columns when absence itself is meaningful.

Good examples:

```text
deleted_at
refunded_at
shipped_at
middle_name
secondary_phone
external_reference
```

Be cautious when a nullable column causes every query to repeatedly interpret ambiguous states.

For example, if an account can be:

```text
active
suspended
pending
deleted
```

encoding everything through several nullable timestamps can become difficult to reason about.

Prefer explicit state modeling where the domain requires it.

## Production Considerations

### Database Invariants

Enforce important invariants in the database:

```sql
amount NUMERIC(12, 2) NOT NULL
```

rather than relying exclusively on application validation.

Application validation improves user experience; database constraints provide the final integrity boundary.

### Query Correctness

Review queries involving:

- `NULL`.
- `NOT IN`.
- `LEFT JOIN`.
- Aggregates.
- `CHECK`.
- `UNIQUE`.
- Optional filters.
- Nullable foreign keys.

These are common sources of subtle production defects.

### Indexing

Do not assume nullable columns cannot be indexed.

Indexes can efficiently support null-aware predicates depending on database and query structure.

For PostgreSQL:

```sql
CREATE INDEX idx_orders_unshipped
ON orders (created_at)
WHERE shipped_at IS NULL;
```

This is useful when the workload frequently processes unshipped orders.

### Performance

Avoid loading rows into Python merely to interpret `NULL`:

```python
orders = list(Order.objects.all())

active = [
    order for order in orders
    if order.deleted_at is None
]
```

Prefer:

```python
orders = Order.objects.filter(deleted_at__isnull=True)
```

This allows PostgreSQL to perform filtering and potentially use indexes.

## Common Mistakes

| Mistake | Why It Fails | Better Approach |
|---|---|---|
| `column = NULL` | Produces `UNKNOWN` | `column IS NULL` |
| `column != NULL` | Also produces `UNKNOWN` | `column IS NOT NULL` |
| Treating `NULL` as `0` | Changes business meaning | Use `COALESCE()` only when intended |
| Treating `NULL` as `''` | Confuses absent and empty | Model the distinction explicitly |
| Assuming `COUNT(column)` counts rows | It ignores `NULL` | Use `COUNT(*)` for rows |
| Using `NOT IN` with nullable subqueries | `NULL` can produce `UNKNOWN` | Prefer `NOT EXISTS` when appropriate |
| Putting a right-table filter in `WHERE` after `LEFT JOIN` | Can eliminate unmatched rows | Put the condition in `ON` when appropriate |
| Using `NULL` as every domain state | Creates ambiguous models | Introduce explicit status/state |
| Assuming all DBs treat `NULL` identically | SQL dialects differ | Verify database-specific behavior |
| Ignoring `NULL` in API contracts | PATCH/update semantics become ambiguous | Define omitted vs explicit-null behavior |
| Handling nullability only in application code | Concurrent writers can violate assumptions | Enforce critical invariants in SQL |
| Filtering nullable columns in Python | Increases memory and latency | Push filtering into SQL |

## Interview Traps

### Is `NULL = NULL` true?

No.

```sql
NULL = NULL
```

evaluates to `UNKNOWN`.

Use:

```sql
IS NULL
```

for null checks.

### What is the difference between `COUNT(*)` and `COUNT(column)`?

`COUNT(*)` counts rows.

`COUNT(column)` counts only rows where the column is non-`NULL`.

### Why can `NOT IN` return unexpected results?

Because a `NULL` in the compared set can cause the predicate to evaluate to `UNKNOWN`.

For anti-join logic, `NOT EXISTS` is often a safer formulation.

### Does `WHERE` keep `UNKNOWN` rows?

No.

A `WHERE` clause keeps rows only when its predicate evaluates to `TRUE`.

### Does `CHECK (x > 0)` reject `x = NULL`?

Not by itself in PostgreSQL. The expression evaluates to `UNKNOWN`, and `CHECK` rejects only `FALSE`.

If `NULL` is invalid:

```sql
x INTEGER NOT NULL
CHECK (x > 0)
```

## Practical Review Checklist

When reviewing SQL involving nullable values, ask:

- What exactly does `NULL` mean in this column?
- Should the column actually be nullable?
- Is `IS NULL` or `IS NOT NULL` being used for null checks?
- Could three-valued logic change the result?
- Could a `NOT IN` subquery contain `NULL`?
- Could a `LEFT JOIN` predicate accidentally become an inner join?
- Does the aggregate intentionally ignore `NULL`?
- Should `COALESCE()` be used, and does its fallback represent the business rule?
- Does a `CHECK` constraint require an accompanying `NOT NULL`?
- Does uniqueness have the intended `NULL` behavior?
- Can an index or partial index improve the workload?
- Does the API distinguish omitted fields from explicit `null`?
- Are critical invariants enforced by the database?

## Key Takeaways

- **`NULL` represents an absent or unknown value and is neither `0`, an empty string, nor `FALSE`; model its meaning explicitly.**
- **SQL uses three-valued logic, so ordinary comparisons with `NULL` produce `UNKNOWN`; use `IS NULL` and `IS NOT NULL` for null checks.**
- **`NULL` affects aggregates, joins, `NOT IN`, constraints, sorting, grouping, and uniqueness, making it a frequent source of production bugs.**
- **Use `COALESCE()` and `NULLIF()` deliberately to express business rules rather than merely hiding missing data.**
- **Enforce important nullability and integrity rules at the database layer and make nullable-state semantics explicit in application and API contracts.**