# 05- NULL with Comparison Operators

## Overview

`NULL` is not an ordinary SQL value. It represents the absence of a known value, and this changes how comparison operators behave.

The operators:

```sql
=
<>
!=
<
>
<=
>=
```

do not produce `TRUE` or `FALSE` when one of their operands is `NULL`. Instead, the comparison produces `UNKNOWN`.

This is a direct consequence of SQL's three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

Understanding this behavior is essential for writing correct `WHERE`, `JOIN`, `HAVING`, `CASE`, and filtering logic. It is particularly important in production systems where nullable columns represent optional relationships, lifecycle timestamps, missing data, or partially populated records.

The central rule is:

> Never use ordinary comparison operators to test whether a value is `NULL`. Use `IS NULL` or `IS NOT NULL`.

## Why Comparisons With NULL Produce UNKNOWN

Consider:

```sql
SELECT *
FROM users
WHERE email = NULL;
```

A common assumption is:

```text
email = NULL → TRUE when email is NULL
```

That is not how SQL works.

Conceptually, SQL evaluates:

```text
NULL = NULL → UNKNOWN
NULL = 'alice@example.com' → UNKNOWN
NULL <> 'alice@example.com' → UNKNOWN
```

`NULL` means that the value is unknown or absent, so SQL cannot establish an ordinary value comparison.

For example:

```text
5 = 5       → TRUE
5 = 10      → FALSE
5 = NULL    → UNKNOWN
NULL = NULL → UNKNOWN
```

`WHERE` returns only rows for which the condition evaluates to `TRUE`.

Therefore:

```sql
WHERE email = NULL
```

does not identify rows where `email` is `NULL`.

## Three-Valued Logic

SQL predicates can evaluate to three possible logical states:

| Result | Meaning | `WHERE` behavior |
|---|---|---|
| `TRUE` | Predicate is satisfied | Row is retained |
| `FALSE` | Predicate is not satisfied | Row is discarded |
| `UNKNOWN` | Predicate cannot be determined | Row is discarded |

For example:

```sql
SELECT *
FROM users
WHERE age > 18;
```

If:

```text
age = 25  → TRUE
age = 15  → FALSE
age = NULL → UNKNOWN
```

the user with `age = NULL` is excluded.

This is one of the most important consequences of nullable columns.

## Equality Operator

The equality operator is:

```sql
=
```

For ordinary values:

```sql
SELECT *
FROM users
WHERE status = 'active';
```

works as expected.

But:

```sql
SELECT *
FROM users
WHERE status = NULL;
```

does not test for nullability.

The correct expression is:

```sql
SELECT *
FROM users
WHERE status IS NULL;
```

### Equality Truth Table

| Left | Right | `Left = Right` |
|---|---|---|
| `10` | `10` | `TRUE` |
| `10` | `20` | `FALSE` |
| `10` | `NULL` | `UNKNOWN` |
| `NULL` | `10` | `UNKNOWN` |
| `NULL` | `NULL` | `UNKNOWN` |

The last row is a frequent interview trap.

`NULL = NULL` is not `TRUE`.

## Inequality Operators

The same rule applies to:

```sql
<>
```

and, in databases that support it:

```sql
!=
```

Consider:

```sql
SELECT *
FROM users
WHERE status <> 'deleted';
```

Rows with:

```text
status = 'active'   → TRUE
status = 'deleted'  → FALSE
status = NULL       → UNKNOWN
```

Therefore, nullable rows are excluded.

If the business rule is:

> Return users whose status is not deleted, including users whose status is NULL.

then the query must explicitly include the null case:

```sql
SELECT *
FROM users
WHERE status <> 'deleted'
   OR status IS NULL;
```

This is not a SQL workaround. It is an explicit statement of the business semantics.

## Comparison Operators

All ordinary comparison operators have the same `NULL` behavior.

| Expression | Result when one operand is `NULL` |
|---|---|
| `x = NULL` | `UNKNOWN` |
| `x <> NULL` | `UNKNOWN` |
| `x != NULL` | `UNKNOWN` |
| `x < NULL` | `UNKNOWN` |
| `x > NULL` | `UNKNOWN` |
| `x <= NULL` | `UNKNOWN` |
| `x >= NULL` | `UNKNOWN` |

For example:

```sql
SELECT *
FROM orders
WHERE shipped_at < CURRENT_TIMESTAMP;
```

If `shipped_at` is `NULL`, the predicate becomes:

```text
NULL < CURRENT_TIMESTAMP → UNKNOWN
```

Therefore the order is excluded.

This may be exactly what you want: an order with no shipment timestamp has not established a shipment time.

## Why `NOT` Does Not Fix NULL Comparisons

A common mistake is:

```sql
WHERE NOT (status = NULL)
```

The assumption is:

```text
status = NULL → FALSE
NOT FALSE     → TRUE
```

But the actual evaluation is:

```text
status = NULL → UNKNOWN
NOT UNKNOWN   → UNKNOWN
```

So the query still does not identify null values.

Use:

```sql
WHERE status IS NULL;
```

Similarly:

```sql
WHERE NOT (status <> 'active')
```

does not necessarily mean:

```text
status = 'active'
```

for nullable columns.

For nullable data, reason explicitly about the `UNKNOWN` state.

## `AND` With UNKNOWN

Three-valued logic becomes especially important when combining predicates.

Consider:

```sql
WHERE status = 'active'
  AND last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
```

If `last_login_at` is `NULL`:

```text
status = 'active'       → TRUE
last_login_at > ...     → UNKNOWN

TRUE AND UNKNOWN        → UNKNOWN
```

The row is excluded.

A simplified truth table for `AND`:

| A | B | `A AND B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE |
| TRUE | UNKNOWN | UNKNOWN |
| FALSE | UNKNOWN | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

The important production implication is that a nullable column can silently eliminate rows from an otherwise valid query.

## `OR` With UNKNOWN

Consider:

```sql
WHERE status = 'active'
   OR last_login_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
```

If:

```text
status = 'active' → FALSE
last_login_at > ... → UNKNOWN
```

then:

```text
FALSE OR UNKNOWN → UNKNOWN
```

and the row is excluded.

But:

```text
TRUE OR UNKNOWN → TRUE
```

because once one side of an `OR` is definitely true, the unknown side cannot change the result.

| A | B | `A OR B` |
|---|---|---|
| TRUE | UNKNOWN | TRUE |
| FALSE | UNKNOWN | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN |

This matters when building complex filtering conditions.

## `CASE` and UNKNOWN

`CASE` conditions also interact with three-valued logic.

For example:

```sql
SELECT
    CASE
        WHEN age >= 18 THEN 'adult'
        WHEN age < 18 THEN 'minor'
        ELSE 'unknown'
    END AS age_group
FROM users;
```

For:

```text
age = 25 → age >= 18 is TRUE
age = 15 → age >= 18 is FALSE, age < 18 is TRUE
age = NULL → both comparisons are UNKNOWN
```

Therefore the nullable value reaches:

```sql
ELSE 'unknown'
```

This is often preferable to pretending that `NULL` represents a numeric value.

## `WHERE` and UNKNOWN

The following query:

```sql
SELECT *
FROM users
WHERE age > 18;
```

can be viewed as:

```text
age = 25 → TRUE    → returned
age = 18 → FALSE   → excluded
age = NULL → UNKNOWN → excluded
```

This explains why nullable columns frequently cause "missing" rows in production reports.

When debugging an unexpected filtering result, inspect whether nullable columns participate in the predicate.

## Explicitly Handling NULL

If `NULL` should be included, express that requirement explicitly.

For example:

```sql
SELECT *
FROM accounts
WHERE balance > 0
   OR balance IS NULL;
```

This means:

```text
positive balance
OR
balance is unknown/absent
```

Do not write:

```sql
WHERE balance >= 0;
```

and assume it includes `NULL`.

It does not.

## `COALESCE` as an Alternative

Sometimes the business rule requires treating `NULL` as a defined fallback value.

For example:

```sql
SELECT *
FROM accounts
WHERE COALESCE(balance, 0) >= 0;
```

This treats:

```text
NULL → 0
```

for the purpose of the expression.

However, this is semantically different from:

```sql
WHERE balance >= 0
   OR balance IS NULL;
```

The first says:

> Treat missing balance as zero.

The second says:

> Accept either a non-negative balance or missing balance.

Those statements may produce the same result for a particular predicate but represent different domain semantics.

## `COALESCE` and Indexes

Applying a function to an indexed column can affect index usage.

For example:

```sql
WHERE COALESCE(balance, 0) >= 0
```

may be less straightforward for the optimizer than a predicate directly involving the column.

For performance-sensitive queries, prefer a predicate that preserves direct column comparisons when it expresses the business rule correctly:

```sql
WHERE balance >= 0
   OR balance IS NULL;
```

If functional indexing is appropriate, database-specific features can be considered after measuring the workload.

## NULL With Date and Time Comparisons

Nullable timestamps are common in backend systems:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    shipped_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);
```

A query such as:

```sql
SELECT *
FROM orders
WHERE shipped_at < CURRENT_TIMESTAMP;
```

automatically excludes rows where:

```text
shipped_at IS NULL
```

because:

```text
NULL < CURRENT_TIMESTAMP → UNKNOWN
```

If the requirement is:

> Find orders that have already shipped or have no shipment timestamp.

then the condition must be explicit:

```sql
SELECT *
FROM orders
WHERE shipped_at < CURRENT_TIMESTAMP
   OR shipped_at IS NULL;
```

Whether that is correct depends on the domain.

## NULL With Numeric Comparisons

Consider:

```sql
SELECT *
FROM products
WHERE price > 100;
```

A product with:

```text
price = NULL
```

does not satisfy the condition.

This is usually desirable because an unknown price should not be treated as:

```text
0
```

or:

```text
greater than 100
```

If the domain says missing price means free, that should be represented explicitly, preferably through a well-defined data model rather than accidental SQL behavior.

## NULL With String Comparisons

For text:

```sql
SELECT *
FROM customers
WHERE name = 'Alice';
```

a `NULL` name produces:

```text
NULL = 'Alice' → UNKNOWN
```

Similarly:

```sql
SELECT *
FROM customers
WHERE name <> 'Alice';
```

does not return rows with `name = NULL`.

If the requirement is "everyone except Alice, including customers without a name":

```sql
SELECT *
FROM customers
WHERE name <> 'Alice'
   OR name IS NULL;
```

## NULL With Foreign Keys

Nullable foreign keys are common:

```sql
CREATE TABLE tickets (
    id BIGINT PRIMARY KEY,
    assigned_agent_id BIGINT REFERENCES agents(id)
);
```

A ticket can have:

```text
assigned_agent_id = 42
```

or:

```text
assigned_agent_id = NULL
```

This query:

```sql
SELECT *
FROM tickets
WHERE assigned_agent_id <> 42;
```

does not return unassigned tickets.

To include them:

```sql
SELECT *
FROM tickets
WHERE assigned_agent_id <> 42
   OR assigned_agent_id IS NULL;
```

If unassigned tickets are not valid according to the domain, the stronger design may be:

```sql
assigned_agent_id BIGINT NOT NULL
```

The best solution is often a schema constraint rather than increasingly complicated query logic.

## `NULL` and `NOT IN`

`NOT IN` deserves special attention because nullable values can make it behave unexpectedly.

Suppose:

```sql
SELECT *
FROM users
WHERE id NOT IN (
    SELECT user_id
    FROM banned_users
);
```

If the subquery returns a `NULL`, the result can become `UNKNOWN` for values that are not otherwise found in the list.

Conceptually:

```text
5 NOT IN (1, 2, NULL)
```

behaves like:

```text
5 <> 1
AND
5 <> 2
AND
5 <> NULL
```

The final comparison is:

```text
5 <> NULL → UNKNOWN
```

Therefore the complete predicate becomes `UNKNOWN`.

For anti-join semantics, `NOT EXISTS` is usually safer:

```sql
SELECT u.*
FROM users AS u
WHERE NOT EXISTS (
    SELECT 1
    FROM banned_users AS b
    WHERE b.user_id = u.id
);
```

This avoids the `NULL` behavior of `NOT IN` and more directly expresses:

> No matching banned-user row exists.

## NULL-Safe Equality

Some database systems provide operators specifically for null-safe comparison.

PostgreSQL supports:

```sql
IS DISTINCT FROM
```

and:

```sql
IS NOT DISTINCT FROM
```

For example:

```sql
SELECT *
FROM users
WHERE preferred_language IS NOT DISTINCT FROM :language;
```

This treats two `NULL` values as equal for comparison purposes.

Conceptually:

| A | B | `A IS NOT DISTINCT FROM B` |
|---|---|---|
| `10` | `10` | TRUE |
| `10` | `20` | FALSE |
| `10` | `NULL` | FALSE |
| `NULL` | `10` | FALSE |
| `NULL` | `NULL` | TRUE |

This is different from:

```sql
A = B
```

where:

```text
NULL = NULL → UNKNOWN
```

Null-safe comparison is useful when `NULL` itself is a meaningful comparable state, but the syntax is database-specific.

## Comparison Semantics by Operator

| Operator | Example | With `NULL` |
|---|---|---|
| `=` | `a = b` | `UNKNOWN` if either side is `NULL` |
| `<>` | `a <> b` | `UNKNOWN` if either side is `NULL` |
| `!=` | `a != b` | `UNKNOWN` if either side is `NULL` |
| `<` | `a < b` | `UNKNOWN` if either side is `NULL` |
| `>` | `a > b` | `UNKNOWN` if either side is `NULL` |
| `<=` | `a <= b` | `UNKNOWN` if either side is `NULL` |
| `>=` | `a >= b` | `UNKNOWN` if either side is `NULL` |
| `IS NULL` | `a IS NULL` | `TRUE` when `a` is `NULL` |
| `IS NOT NULL` | `a IS NOT NULL` | `FALSE` when `a` is `NULL` |
| `IS DISTINCT FROM` | `a IS DISTINCT FROM b` | Null-safe comparison |
| `IS NOT DISTINCT FROM` | `a IS NOT DISTINCT FROM b` | Null-safe equality |

## Production Considerations

### Define the Meaning of NULL

Before writing a predicate, determine what `NULL` means for the domain.

For example:

```text
deleted_at = NULL
```

might mean:

```text
record is active
```

while:

```text
assigned_agent_id = NULL
```

might mean:

```text
not yet assigned
```

These are different business semantics even though both use `NULL`.

### Prefer Constraints Over Query Compensation

If a value should always exist:

```sql
email TEXT NOT NULL
```

is stronger than requiring every query to account for:

```sql
email IS NULL
```

Database constraints reduce the number of states the application must reason about.

### Test Nullable States

Integration tests should include:

```text
normal value
NULL
boundary value
```

For example, for:

```sql
WHERE age >= 18
```

test:

```text
age = 17
age = 18
age = 19
age = NULL
```

The `NULL` case is particularly important because it often exposes incorrect assumptions in repository and service-layer code.

### Review Query Changes Carefully

Adding a predicate such as:

```sql
AND verified_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
```

to an existing query can silently exclude all rows where:

```text
verified_at IS NULL
```

That may be correct or it may introduce a production bug.

Treat nullable-column predicates as semantic changes, not merely filtering changes.

## Performance Considerations

`NULL` semantics themselves do not make a query inherently slow.

Performance depends on:

- indexes;
- selectivity;
- statistics;
- data distribution;
- join strategy;
- predicate structure;
- database optimizer behavior.

For example:

```sql
SELECT id
FROM users
WHERE deleted_at IS NULL;
```

may benefit from an appropriate index or partial index, but the optimizer may choose a sequential scan if most rows satisfy the condition.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE deleted_at IS NULL;
```

Use actual execution plans rather than assuming a particular index strategy.

## Application and ORM Considerations

Application frameworks must preserve SQL's null semantics.

### Django

For nullable fields:

```python
User.objects.filter(deleted_at__isnull=True)
```

maps conceptually to:

```sql
WHERE deleted_at IS NULL
```

For non-null:

```python
User.objects.filter(deleted_at__isnull=False)
```

For ordinary comparisons:

```python
User.objects.filter(age__gte=18)
```

rows where `age` is `NULL` will not satisfy the SQL predicate.

This behavior should be reflected in repository tests.

### SQLAlchemy

Use explicit null predicates:

```python
from sqlalchemy import select

stmt = select(User).where(User.deleted_at.is_(None))
```

and:

```python
stmt = select(User).where(User.deleted_at.is_not(None))
```

For ordinary comparisons:

```python
stmt = select(User).where(User.age >= 18)
```

nullable `age` values naturally fail the predicate because the database comparison evaluates to `UNKNOWN`.

## Common Mistakes

| Mistake | Problem | Correct Approach |
|---|---|---|
| `column = NULL` | Produces `UNKNOWN` | `column IS NULL` |
| `column <> NULL` | Produces `UNKNOWN` | `column IS NOT NULL` |
| `NOT (column = NULL)` | `NOT UNKNOWN` remains `UNKNOWN` | Use `IS NULL` |
| Assuming `NULL = NULL` | Ordinary equality cannot establish equality | Use `IS NOT DISTINCT FROM` where supported |
| Assuming `column <> value` includes `NULL` | `NULL <> value` is `UNKNOWN` | Add `OR column IS NULL` when required |
| Treating `NULL` as `0` | Changes domain semantics | Use explicit `COALESCE` only when intended |
| Treating `NULL` as empty string | `NULL` and `''` are different | Handle or normalize explicitly |
| Using `NOT IN` with nullable subquery values | Can produce `UNKNOWN` | Prefer `NOT EXISTS` for anti-joins |
| Assuming `WHERE` keeps `UNKNOWN` | `WHERE` retains only `TRUE` | Account for three-valued logic |
| Ignoring nullable predicates in query changes | New filters can silently remove rows | Test `NULL` states explicitly |

## Practical Debugging Technique

When a query unexpectedly excludes rows, isolate each predicate.

Suppose:

```sql
SELECT *
FROM orders
WHERE status = 'pending'
  AND shipped_at > CURRENT_TIMESTAMP - INTERVAL '7 days';
```

Break it down:

```sql
SELECT
    id,
    status,
    shipped_at,
    status = 'pending' AS status_match,
    shipped_at > CURRENT_TIMESTAMP - INTERVAL '7 days' AS shipment_match
FROM orders;
```

This makes `UNKNOWN` visible.

For a row with:

```text
status = 'pending'
shipped_at = NULL
```

the results are conceptually:

```text
status_match   = TRUE
shipment_match = UNKNOWN
```

and therefore:

```text
TRUE AND UNKNOWN = UNKNOWN
```

The row is excluded.

This technique is useful when debugging complex reporting queries and production data issues.

## Interview Traps

### Why does `NULL = NULL` not return TRUE?

Because `NULL` is not treated as an ordinary value in SQL equality comparisons.

```text
NULL = NULL → UNKNOWN
```

### Why does `WHERE column <> 'x'` exclude NULL rows?

Because:

```text
NULL <> 'x' → UNKNOWN
```

and `WHERE` retains only `TRUE`.

### How do you include NULL values in an inequality?

Explicitly:

```sql
WHERE column <> 'x'
   OR column IS NULL;
```

### Does `NOT (column = NULL)` find NULL rows?

No.

```text
column = NULL → UNKNOWN
NOT UNKNOWN   → UNKNOWN
```

Use:

```sql
WHERE column IS NULL;
```

### Why can `NOT IN` fail with NULL?

Because SQL effectively evaluates the list as a series of comparisons combined with `AND`. A `NULL` comparison produces `UNKNOWN`, which can make the overall predicate `UNKNOWN`.

Prefer:

```sql
WHERE NOT EXISTS (...)
```

for anti-join semantics.

### When should you use null-safe equality?

Use a database-supported null-safe comparison when `NULL` itself should participate in equality semantics.

In PostgreSQL:

```sql
a IS NOT DISTINCT FROM b
```

treats:

```text
NULL and NULL
```

as equal.

## Key Takeaways

- **Ordinary comparison operators involving `NULL` produce `UNKNOWN`, not `TRUE` or `FALSE`.**
- **`WHERE` retains only `TRUE`, so nullable values can silently disappear from query results.**
- **Use `IS NULL` and `IS NOT NULL` for null tests; explicitly add null branches when business logic requires them.**
- **Be especially careful with `<>`, `NOT`, `NOT IN`, and compound `AND`/`OR` predicates because three-valued logic changes their behavior.**
- **Use null-safe comparison operators such as PostgreSQL's `IS DISTINCT FROM` when `NULL` must participate in equality semantics.**