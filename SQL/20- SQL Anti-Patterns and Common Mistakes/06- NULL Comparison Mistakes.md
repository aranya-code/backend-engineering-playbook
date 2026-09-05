# 06- NULL Comparison Mistakes

## Overview

`NULL` is one of the most common sources of subtle SQL bugs because it does not behave like an ordinary value.

`NULL` represents the absence of a known value. Comparisons involving `NULL` therefore follow SQL's three-valued logic rather than normal two-valued Boolean logic.

The most common mistake is:

```sql
WHERE email = NULL
```

This does **not** find rows where `email` is NULL.

The correct expression is:

```sql
WHERE email IS NULL
```

Likewise:

```sql
WHERE email <> NULL
```

does not find non-NULL emails. Use:

```sql
WHERE email IS NOT NULL
```

NULL-related mistakes can cause:

- Missing API results.
- Incorrect reports.
- Incorrect joins.
- Broken filters.
- Wrong aggregates.
- Failed authorization conditions.
- Incorrect `NOT IN` queries.
- Unexpected sorting behavior.
- Data-quality bugs that are difficult to reproduce.

The core principle is:

> **`NULL` means unknown or missing, not equal to a particular value. Use `IS NULL` / `IS NOT NULL` for null checks and reason explicitly about three-valued logic.**

---

## What NULL Means

In SQL, `NULL` represents an absent or unknown value.

It is not:

- `0`
- `false`
- `''`
- `'NULL'`
- `None` as a SQL literal
- A default value

For example:

```text
id | email
---+--------------------
1  | alice@example.com
2  | NULL
3  | bob@example.com
```

The second row does not contain the string `"NULL"`.

It contains SQL `NULL`.

---

## NULL Is Not an Ordinary Value

This is incorrect:

```sql
SELECT *
FROM customers
WHERE email = NULL;
```

The comparison does not evaluate to `TRUE`.

Likewise:

```sql
SELECT *
FROM customers
WHERE email <> NULL;
```

does not evaluate to `TRUE` for non-NULL values.

Use:

```sql
SELECT *
FROM customers
WHERE email IS NULL;
```

and:

```sql
SELECT *
FROM customers
WHERE email IS NOT NULL;
```

---

## Three-Valued Logic

Normal Boolean logic has:

```text
TRUE
FALSE
```

SQL introduces:

```text
UNKNOWN
```

A comparison involving NULL commonly evaluates to `UNKNOWN`.

For example:

```sql
NULL = NULL
```

produces `UNKNOWN`, not `TRUE`.

Similarly:

```sql
NULL <> 'alice@example.com'
```

produces `UNKNOWN`.

A `WHERE` clause returns rows only when its predicate evaluates to `TRUE`.

Therefore:

```sql
WHERE email = NULL
```

returns no rows because the predicate is not `TRUE`.

---

## Comparison Behavior

A useful mental model:

| Expression | Result |
|---|---|
| `5 = 5` | `TRUE` |
| `5 = 10` | `FALSE` |
| `NULL = 5` | `UNKNOWN` |
| `NULL = NULL` | `UNKNOWN` |
| `NULL <> 5` | `UNKNOWN` |
| `NULL <> NULL` | `UNKNOWN` |
| `NULL IS NULL` | `TRUE` |
| `NULL IS NOT NULL` | `FALSE` |

This behavior is fundamental to understanding SQL filtering.

---

## IS NULL and IS NOT NULL

Use:

```sql
WHERE deleted_at IS NULL
```

to find active rows when `deleted_at` represents a soft-delete timestamp.

Use:

```sql
WHERE deleted_at IS NOT NULL
```

to find deleted rows.

These predicates explicitly test NULL state rather than comparing NULL as a value.

---

## Why `= NULL` Fails

Consider:

```sql
SELECT
    id,
    email
FROM customers
WHERE email = NULL;
```

The database conceptually evaluates:

```text
email = NULL
```

as:

```text
UNKNOWN
```

for every row.

The `WHERE` clause therefore filters them out.

The correct form:

```sql
WHERE email IS NULL
```

explicitly asks:

```text
Is the value NULL?
```

---

## NULL in AND Conditions

Three-valued logic becomes more important with compound predicates.

For example:

```sql
WHERE email = 'alice@example.com'
  AND phone = NULL;
```

The second predicate is `UNKNOWN`.

Therefore:

```text
TRUE AND UNKNOWN
```

produces:

```text
UNKNOWN
```

and the row is not returned.

Correct:

```sql
WHERE email = 'alice@example.com'
  AND phone IS NULL;
```

---

## NULL in OR Conditions

Consider:

```sql
WHERE email = 'alice@example.com'
   OR phone = NULL;
```

The second predicate is `UNKNOWN`.

For a row where email matches:

```text
TRUE OR UNKNOWN
= TRUE
```

For a row where email does not match:

```text
FALSE OR UNKNOWN
= UNKNOWN
```

Only the first case is returned.

The correct NULL test is:

```sql
WHERE email = 'alice@example.com'
   OR phone IS NULL;
```

---

## NOT and NULL

A common misconception is:

```sql
NOT (email = NULL)
```

will find non-NULL emails.

It does not.

Since:

```text
email = NULL
```

is `UNKNOWN`,

```text
NOT UNKNOWN
```

is still:

```text
UNKNOWN
```

Therefore the row is not selected.

Use:

```sql
WHERE email IS NOT NULL;
```

---

## The NOT IN NULL Trap

One of the most important NULL-related SQL bugs involves `NOT IN`.

Suppose:

```sql
SELECT *
FROM customers
WHERE id NOT IN (
    SELECT customer_id
    FROM orders
);
```

If the subquery contains a NULL:

```text
customer_id
-----------
1
2
NULL
```

the semantics of `NOT IN` can produce `UNKNOWN` for values that otherwise appear to be absent.

This can cause unexpectedly few or zero rows.

For relational exclusion, prefer:

```sql
SELECT *
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

`NOT EXISTS` avoids the NULL poisoning behavior of `NOT IN`.

---

## NOT IN vs NOT EXISTS

Consider:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
)
```

versus:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = customers.id
)
```

The second expresses the business requirement more directly:

```text
There does not exist a matching order.
```

Use `NOT EXISTS` when NULLs are possible and the requirement is relational exclusion.

If `NOT IN` is used deliberately, ensure the subquery cannot contain NULL:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM orders
    WHERE customer_id IS NOT NULL
)
```

Even then, `NOT EXISTS` is often easier to reason about.

---

## NULL and JOIN Conditions

NULL also affects joins.

Consider:

```sql
SELECT
    o.id,
    c.id AS customer_id
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id;
```

If:

```text
o.customer_id IS NULL
```

the equality condition does not match a customer.

With an `INNER JOIN`, the order disappears from the result.

With a `LEFT JOIN`:

```sql
SELECT
    o.id,
    c.id AS customer_id
FROM orders AS o
LEFT JOIN customers AS c
    ON c.id = o.customer_id;
```

the order remains and:

```text
customer_id = NULL
```

appears in the result.

---

## Joining NULL to NULL

A common misconception is that:

```sql
ON a.code = b.code
```

matches two NULL values.

It does not.

Because:

```text
NULL = NULL
```

is `UNKNOWN`.

Therefore two rows with NULL join keys do not match under normal equality joins.

---

## NULL-Safe Equality in PostgreSQL

PostgreSQL provides:

```sql
IS NOT DISTINCT FROM
```

which treats two NULL values as equal.

For example:

```sql
SELECT *
FROM a
JOIN b
    ON a.code IS NOT DISTINCT FROM b.code;
```

The semantics are approximately:

```text
a.code = b.code
```

including:

```text
NULL ↔ NULL
```

as a match.

The inverse is:

```sql
IS DISTINCT FROM
```

which treats NULL as a comparable state.

These operators are useful when NULL-safe equality is explicitly part of the business requirement.

---

## IS DISTINCT FROM

Consider:

```sql
WHERE old_value IS DISTINCT FROM new_value;
```

This detects a change while handling NULL correctly.

Examples:

| old_value | new_value | `IS DISTINCT FROM` |
|---|---|---|
| `A` | `A` | `FALSE` |
| `A` | `B` | `TRUE` |
| `A` | `NULL` | `TRUE` |
| `NULL` | `A` | `TRUE` |
| `NULL` | `NULL` | `FALSE` |

This is often useful for synchronization and change-detection logic.

---

## NULL and COALESCE

`COALESCE` returns the first non-NULL expression:

```sql
SELECT
    COALESCE(phone, 'not provided') AS phone
FROM customers;
```

For:

```text
phone = NULL
```

the result is:

```text
not provided
```

This is useful for presentation and fallback logic.

However, do not confuse:

```sql
COALESCE(phone, 'not provided')
```

with:

```sql
phone IS NULL
```

The first transforms the result.

The second tests the database value.

---

## COALESCE in WHERE Clauses

This pattern is sometimes used:

```sql
WHERE COALESCE(status, 'unknown') = 'active'
```

It can be logically valid, but wrapping columns in expressions can affect index usage depending on the query and database.

Prefer direct predicates when possible:

```sql
WHERE status = 'active';
```

If NULL and a particular value should intentionally be treated as equivalent, express that business rule explicitly and validate the execution plan.

---

## NULL vs Empty String

These are different:

```text
NULL
''
```

For example:

```sql
SELECT
    COALESCE('', 'fallback');
```

returns:

```text
''
```

not:

```text
fallback
```

If empty strings should be treated as missing:

```sql
SELECT
    COALESCE(NULLIF(email, ''), 'unknown')
FROM customers;
```

Here:

```sql
NULLIF(email, '')
```

converts an empty string to NULL.

This distinction is important when integrating APIs, CSV files, legacy databases, and user input.

---

## NULL and Aggregates

Aggregate functions have specific NULL behavior.

For example:

```sql
SELECT
    COUNT(*),
    COUNT(phone),
    SUM(total_amount),
    AVG(total_amount)
FROM customers;
```

Generally:

- `COUNT(*)` counts rows.
- `COUNT(column)` counts non-NULL values.
- `SUM(column)` ignores NULL inputs.
- `AVG(column)` ignores NULL inputs.
- `MIN(column)` and `MAX(column)` ignore NULL inputs.

For example, if:

```text
total_amount
------------
100
200
NULL
```

then:

```sql
SUM(total_amount)
```

is:

```text
300
```

not `NULL`.

---

## SUM With No Input Rows

A subtle case occurs when an aggregate receives no input rows.

For PostgreSQL:

```sql
SELECT SUM(total_amount)
FROM orders
WHERE customer_id = 999999;
```

can return:

```text
NULL
```

while:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = 999999;
```

returns:

```text
0
```

If the API requires numeric zero:

```sql
SELECT
    COALESCE(SUM(total_amount), 0) AS total_amount
FROM orders
WHERE customer_id = $1;
```

---

## COUNT(*) vs COUNT(column)

These are not equivalent:

```sql
COUNT(*)
```

and:

```sql
COUNT(phone)
```

If there are:

```text
5 rows
2 non-NULL phone numbers
```

then:

```text
COUNT(*)       = 5
COUNT(phone)   = 2
```

This distinction becomes especially important after `LEFT JOIN`.

---

## LEFT JOIN and COUNT

Consider:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

For a customer with no orders:

```text
COUNT(o.id) = 0
```

because `o.id` is NULL in the outer-join row.

Compare:

```sql
COUNT(*)
```

which counts the preserved customer row and would return:

```text
1
```

for a customer without orders.

Therefore, for counting matched child entities after a `LEFT JOIN`, use the nullable child key:

```sql
COUNT(o.id)
```

rather than blindly using:

```sql
COUNT(*)
```

---

## NULL and CASE

Consider:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    WHEN status = 'inactive' THEN 'disabled'
    ELSE 'unknown'
END
```

If:

```text
status IS NULL
```

neither equality condition is TRUE.

The `ELSE` branch is therefore used.

This is often preferable to trying to compare directly against NULL:

```sql
WHEN status = NULL THEN ...
```

Use:

```sql
WHEN status IS NULL THEN ...
```

when NULL needs a specific branch.

---

## Correct CASE With NULL

```sql
SELECT
    CASE
        WHEN status IS NULL THEN 'unknown'
        WHEN status = 'active' THEN 'enabled'
        ELSE 'disabled'
    END AS status_label
FROM customers;
```

The condition explicitly distinguishes NULL from known values.

---

## NULL in ORDER BY

NULL ordering can affect API pagination and reporting.

PostgreSQL supports:

```sql
ORDER BY last_login DESC NULLS LAST;
```

or:

```sql
ORDER BY last_login ASC NULLS FIRST;
```

Do not assume NULL will appear where the business requirement expects it.

For deterministic APIs, explicitly define NULL ordering when nullable sort columns are involved.

---

## NULL and Pagination

Suppose an API sorts by:

```sql
ORDER BY last_login DESC
```

where `last_login` can be NULL.

If keyset pagination is used, NULL handling must be part of the cursor semantics.

A safer deterministic ordering might include a non-NULL unique tie-breaker:

```sql
ORDER BY
    last_login DESC NULLS LAST,
    id DESC;
```

The cursor logic must use predicates consistent with this ordering.

Pagination correctness depends on deterministic ordering and explicit NULL semantics.

---

## NULL and Unique Constraints

NULL interacts with uniqueness differently from ordinary values.

In PostgreSQL, a standard unique constraint generally permits multiple NULL values because NULLs are not considered equal for ordinary uniqueness enforcement.

For example:

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    external_id text UNIQUE
);
```

Multiple rows may have:

```text
external_id = NULL
```

If the requirement is:

```text
NULL allowed
but non-NULL values must be unique
```

a normal unique constraint may already express the desired rule.

If the requirement differs, use an appropriate constraint or index strategy.

---

## Partial Unique Index

A common PostgreSQL pattern is:

```sql
CREATE UNIQUE INDEX users_active_email_unique
ON users (email)
WHERE deleted_at IS NULL;
```

This can enforce uniqueness only for active rows.

It is useful for soft-delete models where historical deleted records may retain the same email.

The important distinction is that NULL semantics and uniqueness rules are schema design concerns, not merely query concerns.

---

## NULL and Soft Deletes

A common soft-delete model uses:

```text
deleted_at = NULL
```

for active rows and:

```text
deleted_at = timestamp
```

for deleted rows.

Correct:

```sql
SELECT *
FROM customers
WHERE deleted_at IS NULL;
```

Incorrect:

```sql
WHERE deleted_at = NULL;
```

For high-traffic applications, a partial index can support the active-row workload:

```sql
CREATE INDEX customers_active_idx
ON customers (id)
WHERE deleted_at IS NULL;
```

The exact index should be based on actual query patterns and execution plans.

---

## NULL and Multi-Tenancy

Nullable tenant or ownership fields require explicit semantics.

For example:

```sql
WHERE tenant_id = $1
```

does not match rows where:

```text
tenant_id IS NULL
```

This can be correct if NULL means:

```text
not assigned
```

but dangerous if NULL is being interpreted as:

```text
global
```

Do not rely on implicit NULL behavior for authorization.

Define explicitly whether NULL means:

- No tenant.
- Global resource.
- Unknown tenant.
- Invalid state.

Then enforce the rule through schema constraints and authorization logic.

---

## NULL and Authorization

Consider:

```sql
SELECT *
FROM documents
WHERE owner_id = $1
   OR visibility = 'public';
```

A NULL `owner_id` simply fails:

```sql
owner_id = $1
```

and the `visibility` predicate determines the result.

For complex authorization rules, avoid assuming that UNKNOWN behaves like FALSE in every expression without checking the full Boolean expression.

Authorization predicates should be explicit and tested with:

- NULL ownership.
- Missing relationships.
- Cross-tenant IDs.
- Public/private states.
- Deleted resources.

---

## NULL in Python and Django

Python uses:

```python
None
```

to represent the absence of a value.

Django translates:

```python
Customer.objects.filter(phone__isnull=True)
```

to a SQL NULL check.

For non-NULL:

```python
Customer.objects.filter(phone__isnull=False)
```

Do not write application code that assumes:

```python
phone == ""
```

is equivalent to:

```text
SQL NULL
```

They are separate states.

---

## Django Nullable Fields

For example:

```python
class Customer(models.Model):
    phone = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )
```

`null=True` controls database NULL semantics.

`blank=True` primarily controls validation/form behavior.

They are not interchangeable.

For string fields, teams should establish a consistent convention for whether missing data is represented by:

```text
NULL
```

or:

```text
''
```

Mixing both states unnecessarily increases query complexity.

---

## FastAPI and JSON NULL

A REST API may receive:

```json
{
  "phone": null
}
```

or:

```json
{}
```

These can have different application semantics:

```text
null
→ explicitly set to no value

missing
→ field was not provided
```

The application layer must distinguish these cases when PATCH semantics matter.

The SQL layer then needs corresponding behavior:

```sql
SET phone = NULL
```

versus:

```text
leave phone unchanged
```

NULL handling is therefore part of end-to-end API design.

---

## Database NULL vs Redis

Redis does not have SQL NULL semantics.

If an application serializes:

```text
database NULL
```

into:

```text
JSON null
```

that is an application representation.

Do not assume Redis queries will behave like SQL predicates.

The boundary should explicitly define:

```text
database NULL
    ↓
application representation
    ↓
cache representation
```

---

## NULL and Kafka Events

Event schemas should explicitly define whether a field can be:

```text
null
```

or omitted.

For example:

```json
{
  "customer_id": 42,
  "phone": null
}
```

can mean:

```text
phone was explicitly cleared
```

while:

```json
{
  "customer_id": 42
}
```

may mean:

```text
phone was not part of the event
```

Consumers must not blindly map both states to the same database operation.

---

## Performance Considerations

NULL predicates can use indexes depending on the database, index structure, predicate selectivity, and query plan.

For example:

```sql
SELECT id
FROM customers
WHERE deleted_at IS NULL;
```

may use an appropriate index.

For a heavily accessed active-row workload, a partial index can be useful:

```sql
CREATE INDEX customers_active_id_idx
ON customers (id)
WHERE deleted_at IS NULL;
```

Always validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM customers
WHERE deleted_at IS NULL;
```

Do not assume every NULL predicate requires a special index.

---

## Common NULL Anti-Patterns

| Anti-pattern | Problem | Better approach |
|---|---|---|
| `column = NULL` | Produces UNKNOWN | `column IS NULL` |
| `column <> NULL` | Produces UNKNOWN | `column IS NOT NULL` |
| `NOT (column = NULL)` | Still UNKNOWN | `column IS NOT NULL` |
| `NOT IN` with nullable subquery | NULL can poison predicate | `NOT EXISTS` |
| `COUNT(*)` after `LEFT JOIN` | Counts preserved parent row | `COUNT(child.id)` |
| `SUM()` without fallback | Can return NULL with no input | `COALESCE(SUM(...), 0)` |
| `column = ''` for NULL data | Empty string differs from NULL | Define missing-value convention |
| Assuming `NULL = NULL` | Equality is UNKNOWN | `IS NOT DISTINCT FROM` when required |
| Implicit NULL ordering | Pagination/reporting ambiguity | Explicit `NULLS FIRST/LAST` |
| Treating NULL as authorization FALSE | Complex predicates can be subtle | Explicit authorization conditions |

---

## Production Debugging Workflow

When a query unexpectedly returns zero or too few rows:

1. Identify nullable columns in the predicates.
2. Replace `= NULL` and `<> NULL` with explicit NULL checks.
3. Inspect `AND`, `OR`, and `NOT` expressions.
4. Check for nullable values inside `IN` / `NOT IN`.
5. Inspect outer joins.
6. Check `COUNT(*)` versus `COUNT(column)`.
7. Check aggregate behavior for empty input.
8. Inspect API-to-database NULL conversions.
9. Check ORM-generated SQL.
10. Validate the execution plan for performance-sensitive queries.
11. Add tests for NULL and non-NULL cases.

A useful diagnostic query is:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(phone) AS non_null_phone_rows,
    COUNT(*) - COUNT(phone) AS null_phone_rows
FROM customers;
```

This quickly shows whether NULL data is present.

---

## Testing NULL Behavior

For every nullable field involved in business logic, test at least:

| Input | Expected behavior |
|---|---|
| Known value | Normal path |
| NULL | Missing/unknown path |
| Empty string | Separate if allowed |
| Zero | Separate from NULL |
| False | Separate from NULL |
| No matching joined row | Outer-join behavior |

For example:

```sql
SELECT
    id,
    email
FROM customers
WHERE email IS NULL;
```

should have a dedicated test if NULL email is a meaningful business state.

For critical reporting or authorization queries, test combinations rather than only individual NULL values.

---

## Production Checklist

### Predicates

- [ ] Are NULL checks using `IS NULL` / `IS NOT NULL`?
- [ ] Are compound predicates understood under three-valued logic?
- [ ] Are `NOT` expressions safe?
- [ ] Are nullable values present in `IN` / `NOT IN`?

### JOINs

- [ ] Can join keys be NULL?
- [ ] Should NULL keys match?
- [ ] Is `IS NOT DISTINCT FROM` required?
- [ ] Does an outer join preserve the intended rows?

### Aggregation

- [ ] Is `COUNT(*)` intentional?
- [ ] Should `COUNT(column)` be used?
- [ ] Can `SUM()` return NULL when there are no input rows?
- [ ] Is `COALESCE()` required for API output?

### API and Application

- [ ] Is `None` mapped correctly to SQL NULL?
- [ ] Is missing JSON different from explicit `null`?
- [ ] Does the ORM generate the intended predicate?
- [ ] Are NULL and empty string intentionally distinguished?

### Security

- [ ] Can NULL affect tenant filtering?
- [ ] Can NULL affect ownership checks?
- [ ] Are authorization predicates explicitly tested?
- [ ] Are NULL states constrained where they should be impossible?

---

## Interview Traps

### "Why doesn't `WHERE column = NULL` work?"

Because equality involving NULL produces `UNKNOWN`, not `TRUE`.

Use:

```sql
WHERE column IS NULL
```

### "Does `NULL = NULL` return TRUE?"

No.

It evaluates to `UNKNOWN`.

Use:

```sql
NULL IS NULL
```

which returns `TRUE`.

### "Why can NOT IN return no rows unexpectedly?"

Because a NULL in the compared set can cause the `NOT IN` predicate to evaluate to `UNKNOWN`.

Use `NOT EXISTS` for relational exclusion when appropriate.

### "What is the difference between COUNT(*) and COUNT(column)?"

`COUNT(*)` counts rows. `COUNT(column)` counts only non-NULL values.

### "Does LEFT JOIN match NULL to NULL?"

Not with normal equality:

```sql
a.key = b.key
```

does not match two NULLs.

Use:

```sql
a.key IS NOT DISTINCT FROM b.key
```

when NULL-to-NULL matching is required in PostgreSQL.

### "Is NULL the same as an empty string?"

No.

They represent different states.

### "Can NULL be used in a UNIQUE column?"

Yes. PostgreSQL's standard unique semantics generally allow multiple NULLs because NULLs are not equal for ordinary uniqueness enforcement.

---

## Senior Mental Model

Treat NULL as a separate state in the data model:

```text
Known value
    │
    ├── comparisons can be TRUE/FALSE
    │
NULL
    │
    └── ordinary comparisons produce UNKNOWN
```

Then reason about the full query:

```text
NULL state
    ↓
predicate
    ↓
TRUE / FALSE / UNKNOWN
    ↓
WHERE / JOIN / HAVING
    ↓
result set
```

For production systems, also reason across boundaries:

```text
API JSON
   ↓
Python None
   ↓
ORM parameter
   ↓
PostgreSQL NULL
   ↓
SQL predicate
   ↓
query result
   ↓
JSON response / Kafka / Redis
```

A NULL bug can originate at any layer.

---

## Practical Decision Guide

| Requirement | SQL pattern |
|---|---|
| Find NULL values | `column IS NULL` |
| Find non-NULL values | `column IS NOT NULL` |
| Compare values including NULL as equal | `IS NOT DISTINCT FROM` |
| Compare values treating NULL as different | `IS DISTINCT FROM` |
| Provide a fallback value | `COALESCE()` |
| Convert a specific value to NULL | `NULLIF()` |
| Exclude matching rows safely | `NOT EXISTS` |
| Count all rows | `COUNT(*)` |
| Count non-NULL values | `COUNT(column)` |
| Explicitly control NULL sorting | `NULLS FIRST/LAST` |

---

## Practical Rule

When reviewing SQL containing nullable columns, never reason about NULL as if it were an ordinary value.

Instead of:

```sql
WHERE column = NULL
```

use:

```sql
WHERE column IS NULL
```

Instead of:

```sql
WHERE column <> NULL
```

use:

```sql
WHERE column IS NOT NULL
```

For exclusion:

```sql
WHERE NOT EXISTS (...)
```

is often safer than:

```sql
WHERE value NOT IN (...)
```

For NULL-safe comparison in PostgreSQL:

```sql
a IS NOT DISTINCT FROM b
```

For presentation or aggregate defaults:

```sql
COALESCE(value, fallback)
```

The senior-level skill is not memorizing `IS NULL`.

It is understanding how **NULL propagates through predicates, joins, aggregation, ordering, constraints, ORMs, APIs, and authorization logic**.

## Key Takeaways

- **NULL is not an ordinary value; normal comparisons such as `= NULL`, `<> NULL`, and `NULL = NULL` produce `UNKNOWN`, so use `IS NULL` and `IS NOT NULL` for null checks.**
- **Three-valued logic affects compound predicates, joins, filtering, and authorization; reason explicitly about `TRUE`, `FALSE`, and `UNKNOWN`.**
- **Be especially careful with `NOT IN` because a NULL in the compared set can produce unexpected results; `NOT EXISTS` is often the safer relational exclusion pattern.**
- **NULL affects aggregates, outer joins, ordering, uniqueness, pagination, and API serialization; `COUNT(*)`, `COUNT(column)`, `COALESCE`, and explicit NULL ordering have different semantics.**
- **Production-grade NULL handling requires consistent semantics across PostgreSQL, Django/Python, REST or gRPC APIs, Redis, Kafka, and database constraints rather than treating NULL as equivalent to empty strings or missing application fields.**