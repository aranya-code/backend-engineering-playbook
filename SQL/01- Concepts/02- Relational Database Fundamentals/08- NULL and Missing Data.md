# 08- NULL and Missing Data

## Overview

`NULL` represents the absence of a known value in a relational database. It is not the same as `0`, an empty string, `FALSE`, or a sentinel value such as `-1`.

Handling `NULL` correctly matters because SQL uses **three-valued logic**:

```text
TRUE
FALSE
UNKNOWN
```

A comparison involving `NULL` generally produces `UNKNOWN`, not `TRUE` or `FALSE`.

This affects:

- Filtering
- Comparisons
- Joins
- Aggregations
- Constraints
- Indexes
- Unique values
- API serialization
- ORM behavior
- Data validation
- Reporting

For backend engineers, `NULL` is less about syntax and more about modeling what the system actually knows.

---

## What NULL Means

Consider:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    email TEXT NOT NULL,
    phone_number TEXT
);
```

A row may contain:

```text
id | email          | phone_number
---|----------------|-------------
1  | alice@example  | +911234567890
2  | bob@example    | NULL
```

For Bob, `phone_number = NULL` means:

```text
There is no known phone number value in this row.
```

It does **not necessarily mean**:

```text
Bob does not have a phone.
```

The application may need to distinguish:

```text
unknown
not provided
not applicable
intentionally removed
not yet collected
```

That distinction is a data-modeling decision.

---

## NULL Is Not a Normal Value

`NULL` is a special SQL marker.

These are different:

| Representation | Meaning |
|---|---|
| `NULL` | Value is absent/unknown |
| `''` | Empty string |
| `0` | Numeric zero |
| `FALSE` | Boolean false |
| `'UNKNOWN'` | Literal string |
| `-1` | Numeric sentinel |

Avoid using sentinel values merely to avoid nullable columns.

For example:

```sql
phone_number = 'N/A'
```

mixes actual data with metadata about the data.

Prefer:

```sql
phone_number IS NULL
```

when absence is a valid state.

---

## Why NULL Exists

Real systems contain incomplete information.

Examples:

```text
User has not supplied a phone number
Order has not been shipped
Employee has no termination date
Payment has not been completed
Profile has no middle name
Delivery address is not applicable
```

For example:

```sql
CREATE TABLE employees (
    id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    hired_at TIMESTAMPTZ NOT NULL,
    terminated_at TIMESTAMPTZ
);
```

An active employee may have:

```text
terminated_at = NULL
```

because termination has not occurred.

Here `NULL` represents an intentionally absent lifecycle value.

---

## NULL and Three-Valued Logic

SQL predicates can evaluate to:

```text
TRUE
FALSE
UNKNOWN
```

Consider:

```sql
SELECT *
FROM users
WHERE phone_number = NULL;
```

This does not correctly find rows where `phone_number` is `NULL`.

The comparison evaluates to:

```text
UNKNOWN
```

Use:

```sql
SELECT *
FROM users
WHERE phone_number IS NULL;
```

and:

```sql
SELECT *
FROM users
WHERE phone_number IS NOT NULL;
```

### Comparison Behavior

| Expression | Result when `x` is `NULL` |
|---|---|
| `x = 10` | `UNKNOWN` |
| `x <> 10` | `UNKNOWN` |
| `x > 10` | `UNKNOWN` |
| `x < 10` | `UNKNOWN` |
| `x = NULL` | `UNKNOWN` |
| `x IS NULL` | `TRUE` |
| `x IS NOT NULL` | `FALSE` |

The key rule is:

> Use `IS NULL` and `IS NOT NULL` for NULL checks.

---

## Why WHERE Filters NULL Rows

Consider:

```sql
SELECT *
FROM users
WHERE phone_number <> '123';
```

It may be tempting to think this means:

```text
phone_number is anything except '123'
```

But for a `NULL` phone number:

```text
NULL <> '123'
→ UNKNOWN
```

A `WHERE` clause retains only rows where the predicate is `TRUE`.

Therefore the `NULL` row is excluded.

If the business requirement is:

```text
phone_number is not 123 OR phone_number is unknown
```

write that explicitly:

```sql
SELECT *
FROM users
WHERE phone_number <> '123'
   OR phone_number IS NULL;
```

---

## NULL and AND

SQL's three-valued logic affects compound predicates.

| A | B | `A AND B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE |
| TRUE | UNKNOWN | UNKNOWN |
| FALSE | TRUE | FALSE |
| FALSE | UNKNOWN | FALSE |
| UNKNOWN | TRUE | UNKNOWN |
| UNKNOWN | FALSE | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

Example:

```sql
WHERE phone_number = '+911234567890'
  AND status = 'active'
```

If `phone_number` is `NULL`:

```text
UNKNOWN AND TRUE
→ UNKNOWN
```

The row is excluded.

---

## NULL and OR

For `OR`:

| A | B | `A OR B` |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | TRUE |
| TRUE | UNKNOWN | TRUE |
| FALSE | FALSE | FALSE |
| FALSE | UNKNOWN | UNKNOWN |
| UNKNOWN | UNKNOWN | UNKNOWN |

This is useful when explicitly including unknown values.

Example:

```sql
WHERE phone_number = '+911234567890'
   OR phone_number IS NULL;
```

The `IS NULL` condition evaluates to `TRUE` for missing phone numbers.

---

## NULL and NOT

`NOT` also follows three-valued logic:

```text
NOT TRUE
→ FALSE

NOT FALSE
→ TRUE

NOT UNKNOWN
→ UNKNOWN
```

Therefore:

```sql
WHERE NOT (phone_number = '123')
```

does not include `NULL` phone numbers.

This is a common SQL interview and production trap.

If `NULL` should be included, make the requirement explicit:

```sql
WHERE phone_number <> '123'
   OR phone_number IS NULL;
```

---

## NULL and DISTINCT

`NULL` has special behavior with `DISTINCT`.

Consider:

```text
NULL
NULL
NULL
'active'
'pending'
```

Then:

```sql
SELECT DISTINCT status
FROM orders;
```

returns one `NULL` representation rather than one result for every `NULL` row.

`DISTINCT` treats all `NULL` values as one indistinguishable result for duplicate elimination.

This should not be confused with equality:

```sql
NULL = NULL
```

is still `UNKNOWN`.

---

## NULL and ORDER BY

Ordering behavior for `NULL` is database-specific.

PostgreSQL supports explicit control:

```sql
SELECT *
FROM users
ORDER BY phone_number NULLS LAST;
```

or:

```sql
SELECT *
FROM users
ORDER BY phone_number NULLS FIRST;
```

This is preferable when ordering semantics are part of an API or business requirement.

Do not rely on implicit `NULL` ordering when deterministic behavior matters.

---

## NULL and Aggregations

Aggregate functions generally ignore `NULL` values.

Consider:

```text
amount
------
100
200
NULL
```

Then:

```sql
SELECT AVG(amount)
FROM payments;
```

calculates the average of:

```text
100
200
```

not:

```text
100
200
0
```

`NULL` does not automatically become zero.

This distinction is critical for financial and analytical queries.

---

## COUNT and NULL

These two queries have different semantics:

```sql
SELECT COUNT(*)
FROM users;
```

counts rows.

Whereas:

```sql
SELECT COUNT(phone_number)
FROM users;
```

counts non-`NULL` phone numbers.

Example:

```text
users = 1000
phone_number IS NOT NULL = 700
```

Then:

```text
COUNT(*)           = 1000
COUNT(phone_number) = 700
```

This is one of the most important `NULL` behaviors to remember.

---

## COUNT DISTINCT and NULL

Consider:

```sql
SELECT COUNT(DISTINCT phone_number)
FROM users;
```

`NULL` values are not counted as a distinct phone number.

Therefore:

```text
NULL
NULL
+911111111111
+922222222222
```

produces:

```text
2
```

not:

```text
3
```

If the business definition of "missing phone number" needs to be counted separately, calculate it explicitly:

```sql
SELECT
    COUNT(*) FILTER (WHERE phone_number IS NULL) AS missing_phone_numbers,
    COUNT(DISTINCT phone_number) AS distinct_phone_numbers
FROM users;
```

---

## COALESCE

`COALESCE` returns the first non-`NULL` expression.

```sql
SELECT
    COALESCE(display_name, email) AS name
FROM users;
```

If:

```text
display_name = NULL
email = alice@example.com
```

the result is:

```text
alice@example.com
```

It is useful for:

- Presentation defaults
- Reporting
- Calculated values
- Fallback logic

Example:

```sql
SELECT
    order_id,
    COALESCE(discount_amount, 0) AS discount_amount
FROM orders;
```

This is appropriate when the output semantics explicitly require:

```text
missing discount → display as zero
```

Do not use `COALESCE` blindly to hide data-quality problems.

---

## COALESCE and Data Semantics

These are not always equivalent:

```sql
COALESCE(amount, 0)
```

and:

```text
amount = 0
```

The first means:

```text
Treat missing amount as zero for this result.
```

The second means:

```text
The actual stored amount is zero.
```

If `NULL` has meaningful business semantics, converting it to zero can destroy information.

---

## NULLIF

`NULLIF` returns `NULL` when two expressions are equal.

Example:

```sql
SELECT NULLIF(discount_code, '')
FROM orders;
```

This converts an empty string to `NULL`.

It can also prevent division-by-zero:

```sql
SELECT
    revenue / NULLIF(order_count, 0) AS revenue_per_order
FROM metrics;
```

If:

```text
order_count = 0
```

then:

```text
NULLIF(0, 0)
→ NULL
```

and the division does not raise a zero-denominator error.

---

## CASE and NULL

`CASE` can explicitly handle missing values:

```sql
SELECT
    CASE
        WHEN phone_number IS NULL THEN 'missing'
        ELSE 'provided'
    END AS phone_status
FROM users;
```

For more complex business rules, explicit `CASE` expressions are often clearer than deeply nested `COALESCE` calls.

---

## NULL in Joins

`NULL` affects join predicates.

Consider:

```sql
SELECT *
FROM users AS u
JOIN profiles AS p
    ON p.user_id = u.id;
```

If:

```text
p.user_id = NULL
```

then:

```text
p.user_id = u.id
```

evaluates to `UNKNOWN`.

The row does not match an inner join.

This is expected because `NULL` does not equal another value.

---

## LEFT JOIN and NULL

A `LEFT JOIN` introduces `NULL` values for missing rows on the right side.

Example:

```sql
SELECT
    u.id,
    p.avatar_url
FROM users AS u
LEFT JOIN profiles AS p
    ON p.user_id = u.id;
```

If a user has no profile:

```text
u.id       = 42
p.avatar_url = NULL
```

That `NULL` can mean:

```text
No matching profile row exists.
```

This is different from:

```text
A profile exists but avatar_url itself is NULL.
```

Both situations can produce `NULL` in the result.

---

## Distinguishing Missing Rows From NULL Columns

Suppose:

```text
users
-----
id

profiles
--------
user_id
avatar_url
```

Query:

```sql
SELECT
    u.id,
    p.user_id,
    p.avatar_url
FROM users AS u
LEFT JOIN profiles AS p
    ON p.user_id = u.id;
```

If:

```text
p.user_id IS NULL
```

the profile row does not exist.

If:

```text
p.user_id IS NOT NULL
AND p.avatar_url IS NULL
```

the profile exists but has no avatar.

This distinction is important in reporting and application logic.

---

## NULL and Foreign Keys

A foreign key can be nullable.

Example:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    assigned_agent_id BIGINT
        REFERENCES agents(id)
);
```

Then:

```text
assigned_agent_id = NULL
```

can mean:

```text
Order has not yet been assigned.
```

This is different from:

```text
assigned_agent_id = 0
```

A nullable foreign key is appropriate when the relationship itself is optional.

If every order must have an agent, use:

```sql
assigned_agent_id BIGINT NOT NULL
    REFERENCES agents(id);
```

---

## NULL and UNIQUE Constraints

A common production detail is that `NULL` interacts differently with uniqueness than ordinary values.

In PostgreSQL, a normal unique constraint allows multiple `NULL` values:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    external_id TEXT UNIQUE
);
```

This can allow:

```text
external_id
-----------
abc
NULL
NULL
NULL
```

The reason is that `NULL` represents an unknown/non-value rather than equal values.

PostgreSQL also supports explicit `NULLS NOT DISTINCT` behavior:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    external_id TEXT UNIQUE NULLS NOT DISTINCT
);
```

This treats `NULL` values as not distinct for uniqueness purposes, allowing at most one `NULL`.

Database dialects differ in how they implement unique constraints involving `NULL`, so verify the target database behavior.

---

## NULL and CHECK Constraints

Consider:

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    price NUMERIC(12, 2),
    CHECK (price >= 0)
);
```

A nullable `price` can still contain:

```text
NULL
```

because:

```text
price >= 0
```

evaluates to `UNKNOWN`, and a PostgreSQL `CHECK` constraint passes when its condition is `TRUE` or `UNKNOWN`.

If `price` must always exist:

```sql
price NUMERIC(12, 2) NOT NULL
    CHECK (price >= 0)
```

This distinction is important:

```text
CHECK constraint
```

validates known values.

```text
NOT NULL
```

controls whether a value may be absent.

Use both when both properties are required.

---

## NULL and Default Values

A default does not make a column non-null.

Consider:

```sql
CREATE TABLE users (
    active BOOLEAN DEFAULT TRUE
);
```

An omitted value can result in:

```text
active = TRUE
```

but explicitly inserting:

```sql
INSERT INTO users (active)
VALUES (NULL);
```

can still produce:

```text
active = NULL
```

if the column is nullable.

If the application requires a value:

```sql
active BOOLEAN NOT NULL DEFAULT TRUE
```

The distinction is:

```text
DEFAULT
→ what to use when a value is omitted

NOT NULL
→ whether NULL is permitted
```

---

## NULL and Application APIs

Backend APIs commonly have at least three states:

```text
Field omitted
Field = null
Field = actual value
```

These states can have different meanings.

For example, a PATCH request:

```json
{}
```

may mean:

```text
Do not change phone_number.
```

Whereas:

```json
{
  "phone_number": null
}
```

may mean:

```text
Remove the phone number.
```

And:

```json
{
  "phone_number": "+911234567890"
}
```

means:

```text
Set the phone number.
```

This distinction should be deliberately modeled in Django, FastAPI, or other API frameworks.

---

## NULL in Python and ORMs

Python uses:

```python
None
```

to represent the absence of a value.

For example, Django commonly maps:

```text
SQL NULL ↔ Python None
```

A nullable field might be:

```python
class User(models.Model):
    phone_number = models.CharField(
        max_length=30,
        null=True,
        blank=True,
    )
```

However:

```text
null=True
```

and:

```text
blank=True
```

mean different things in Django.

- `null=True` affects database storage.
- `blank=True` affects validation.

For string fields, decide carefully whether database `NULL` is actually needed or whether an empty string should represent missing input according to the application's conventions.

---

## NULL in FastAPI and Pydantic

An optional API field can represent `null` explicitly.

For example:

```python
from pydantic import BaseModel


class UserUpdate(BaseModel):
    phone_number: str | None = None
```

This means the field can accept:

```json
{
  "phone_number": null
}
```

But API update semantics may require distinguishing:

```text
field absent
```

from:

```text
field explicitly set to null
```

A robust PATCH implementation should model that distinction rather than assuming:

```python
None
```

always means "not supplied."

---

## NULL and Serialization

Suppose the database contains:

```text
phone_number = NULL
```

An API might serialize this as:

```json
{
  "phone_number": null
}
```

or omit it:

```json
{}
```

These are not necessarily equivalent.

Clients may interpret:

```json
"phone_number": null
```

as:

```text
The field exists and has no value.
```

while omission may mean:

```text
The field is unavailable or intentionally excluded.
```

Define serialization semantics consistently across the API.

---

## Modeling Missing Data

Before making a column nullable, ask:

```text
What does NULL mean?
```

Good answers include:

```text
Not yet assigned
Not applicable
Not collected
Unknown
Not completed
```

Bad answer:

```text
We weren't sure what else to use.
```

A nullable column should have a clear semantic contract.

---

## NULL vs Multiple Business States

Sometimes `NULL` is insufficient.

Suppose an order's delivery date can be:

```text
Not scheduled
Scheduled
Delivered
Cancelled
```

Using only:

```text
delivery_date
```

with:

```text
NULL
```

may not distinguish:

```text
not scheduled
```

from:

```text
cancelled
```

A better model may be:

```sql
status TEXT NOT NULL,
delivery_date TIMESTAMPTZ
```

with explicit state rules.

For example:

```text
status = 'pending'   → delivery_date may be NULL
status = 'scheduled' → delivery_date should be populated
status = 'delivered' → delivery_date should be populated
status = 'cancelled' → delivery_date may be NULL
```

The database can enforce some of these invariants with constraints.

---

## NULL vs Sentinel Values

Avoid:

```text
terminated_at = '1970-01-01'
```

to represent:

```text
Not terminated
```

Prefer:

```text
terminated_at = NULL
```

Likewise avoid:

```text
customer_id = -1
```

to represent:

```text
No customer
```

A nullable foreign key communicates the optional relationship directly and preserves referential integrity.

---

## NULL and Data Quality

Nullable fields can hide incomplete data.

For example:

```sql
SELECT COUNT(*)
FROM users
WHERE phone_number IS NULL;
```

This can reveal how much data is missing.

Track meaningful data-quality metrics such as:

```text
percentage of records with missing email
percentage of orders without shipping address
percentage of users without verified phone numbers
```

For operational systems, these metrics can be more useful than simply knowing that the database permits `NULL`.

---

## Migration Considerations

Changing:

```sql
phone_number TEXT
```

to:

```sql
phone_number TEXT NOT NULL
```

requires existing rows to satisfy the new invariant.

A safer production migration often follows:

```text
1. Identify NULL rows
2. Decide how to remediate them
3. Backfill valid values where possible
4. Deploy application validation
5. Monitor for new NULL writes
6. Add NOT NULL constraint
```

Do not assume that adding `NOT NULL` is merely a schema change.

It is a change to the application's data contract.

---

## Production Query Patterns

### Correct NULL Check

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

This is a common soft-delete pattern.

### Include Missing Values

```sql
SELECT *
FROM users
WHERE country_code = 'IN'
   OR country_code IS NULL;
```

### Provide a Presentation Default

```sql
SELECT
    COALESCE(display_name, 'Unnamed user') AS display_name
FROM users;
```

### Count Missing Values

```sql
SELECT
    COUNT(*) FILTER (WHERE phone_number IS NULL) AS missing,
    COUNT(*) FILTER (WHERE phone_number IS NOT NULL) AS present
FROM users;
```

---

## Soft Deletes and NULL

Soft deletion commonly uses:

```sql
deleted_at TIMESTAMPTZ
```

where:

```text
NULL        → active
timestamp   → deleted
```

A standard query becomes:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

This is simple and effective, but every relevant query must consistently apply the active-row predicate.

In ORMs, centralizing this behavior can reduce accidental exposure of deleted records.

For authorization-sensitive systems, do not rely solely on ORM conventions; verify generated SQL and access-control behavior.

---

## NULL and Partial Indexes

PostgreSQL partial indexes can be useful when only non-deleted or active rows are queried.

For example:

```sql
CREATE INDEX idx_users_active_email
ON users(email)
WHERE deleted_at IS NULL;
```

This can reduce index size and improve queries targeting active records.

Partial indexes are particularly useful when:

```text
active rows are a subset of the table
```

and the application's query pattern consistently includes the predicate.

---

## NULL and Query Performance

`IS NULL` and `IS NOT NULL` are not inherently slow.

Performance depends on:

- Database engine
- Index structure
- Column distribution
- Query selectivity
- Statistics
- Table size
- Query shape

For example:

```sql
CREATE INDEX idx_users_deleted_at
ON users(deleted_at);
```

may help some queries, but whether it is useful depends on the distribution of:

```text
NULL
vs
non-NULL
```

and the query planner's cost model.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

to validate performance assumptions.

---

## Common Mistakes

### Using `= NULL`

Incorrect:

```sql
WHERE column = NULL
```

Correct:

```sql
WHERE column IS NULL
```

### Assuming `NULL = NULL`

It does not.

```sql
NULL = NULL
```

produces:

```text
UNKNOWN
```

### Treating NULL as Zero

This can corrupt financial or analytical semantics.

Use `COALESCE` only when the business meaning supports the conversion.

### Treating NULL as an Empty String

These represent different states.

Do not normalize them interchangeably without a deliberate data contract.

### Assuming `NOT NULL` Is a Validation Constraint

`NOT NULL` only says:

```text
a value must be present
```

It does not validate:

```text
format
range
business meaning
```

Use appropriate constraints and application validation.

### Forgetting NULL in Negative Filters

This:

```sql
WHERE status <> 'deleted'
```

does not include rows where:

```text
status IS NULL
```

if such rows exist.

### Using NULL to Represent Too Many States

If one `NULL` value is being overloaded to mean:

```text
unknown
not applicable
pending
cancelled
not collected
```

the model is likely underspecified.

### Converting NULL During Every Query

Repeatedly applying:

```sql
COALESCE(column, ...)
```

can hide data-quality issues and alter semantics.

Use it intentionally.

### Assuming ORM Semantics Match SQL Automatically

ORMs abstract SQL but do not eliminate SQL semantics.

Inspect generated SQL for important queries involving:

- `NULL`
- `LEFT JOIN`
- Aggregations
- Filters
- Partial indexes
- Soft deletes

---

## Interview Traps

| Trap | Correct interpretation |
|---|---|
| `NULL = NULL` is true | It evaluates to `UNKNOWN` |
| `column = NULL` finds missing values | Use `IS NULL` |
| `COUNT(column)` counts all rows | It ignores `NULL` |
| `COUNT(*)` ignores NULL rows | It counts rows |
| `column <> value` includes NULL | NULL rows evaluate to `UNKNOWN` |
| `NULL` means zero | NULL represents absence/unknown |
| `DEFAULT` prevents NULL | Only `NOT NULL` prevents NULL |
| `CHECK` always rejects NULL | A nullable CHECK can evaluate to `UNKNOWN` |
| LEFT JOIN NULL always means a NULL column | It can also indicate no matching right-side row |
| Multiple NULLs always violate UNIQUE | Behavior is database-specific; PostgreSQL normally allows them |
| `NOT NULL` solves data quality | It only enforces presence |
| `COALESCE` is always safe | It can change business semantics |

---

## Production Best Practices

### Define the Meaning of NULL

For every nullable column, document what `NULL` means.

Examples:

```text
terminated_at:
NULL = employee has not been terminated
```

```text
assigned_agent_id:
NULL = order has not been assigned
```

### Prefer NOT NULL When Absence Is Invalid

If every valid row requires the value:

```sql
email TEXT NOT NULL
```

is better than allowing:

```text
NULL
```

and relying on application validation.

### Use Database Constraints

Enforce invariants in the database:

```sql
NOT NULL
CHECK
UNIQUE
FOREIGN KEY
```

Application validation improves developer experience but should not be the only integrity boundary.

### Avoid Sentinel Values

Prefer semantic SQL `NULL` over arbitrary values such as:

```text
-1
0
1970-01-01
'UNKNOWN'
```

unless those values are legitimate domain values.

### Monitor Missing Data

If missing data matters operationally, measure it.

### Treat API Semantics Separately

Explicitly define:

```text
omitted
vs
null
vs
value
```

for create and update APIs.

### Verify Database-Specific Behavior

Do not assume every SQL database handles:

```text
NULL + UNIQUE
NULL + ORDER BY
NULL + indexes
```

identically.

---

## Key Takeaways

- **`NULL` represents missing or unknown data and participates in SQL's three-valued logic**, so comparisons such as `NULL = NULL` and `column = NULL` do not behave like ordinary value comparisons.
- **Use `IS NULL` and `IS NOT NULL` for NULL checks**, and remember that `WHERE` retains only predicates evaluating to `TRUE`.
- **Aggregations treat `NULL` specially**: `COUNT(*)` counts rows, while `COUNT(column)` ignores `NULL`; most aggregate functions similarly ignore missing values.
- **A nullable column should have an explicit business meaning**; do not use `NULL`, empty strings, zero, or sentinel values interchangeably.
- **Production-grade NULL handling spans schema constraints, query semantics, ORM behavior, API serialization, migrations, indexing, data quality, and database-specific behavior.**