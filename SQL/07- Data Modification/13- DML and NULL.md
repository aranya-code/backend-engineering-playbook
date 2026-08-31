# 13- DML and NULL

## Overview

`NULL` represents the absence of a value in SQL. It is not equivalent to `0`, an empty string, `FALSE`, or any other ordinary value.

`NULL` becomes particularly important during DML operations because `INSERT`, `UPDATE`, and `DELETE` interact with SQL's three-valued logic and with column constraints such as `NOT NULL`, defaults, and foreign keys.

For backend systems, incorrect handling of `NULL` can cause:

- Rows not being updated or deleted when expected.
- Unexpected query results.
- Constraint violations.
- Incorrect API behavior.
- Data-quality inconsistencies.
- Bugs that are difficult to reproduce because `NULL` changes predicate semantics.

A senior engineer should distinguish three separate concepts:

```text
NULL
  |
  +-- Storage state: value is absent
  |
  +-- Predicate result: TRUE / FALSE / UNKNOWN
  |
  +-- DML behavior: INSERT / UPDATE / DELETE semantics
```

The most important rule is:

> `NULL` is not compared using `=` or `<>`; use `IS NULL` and `IS NOT NULL`.

## What NULL Means

A column containing `NULL` does not contain a known value.

For example:

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    email text,
    phone_number text
);
```

The following row contains an absent phone number:

```sql
INSERT INTO users (id, email, phone_number)
VALUES (1, 'alice@example.com', NULL);
```

The following values are different from `NULL`:

| Value | Meaning |
|---|---|
| `NULL` | No value / unknown / not applicable depending on domain semantics |
| `''` | Empty string |
| `0` | Numeric zero |
| `FALSE` | Boolean false |
| `'NULL'` | Literal text containing four characters |

Do not use a sentinel such as `0` or `'N/A'` simply to avoid `NULL` unless that sentinel has explicit domain semantics.

## NULL and Three-Valued Logic

SQL predicates can evaluate to:

- `TRUE`
- `FALSE`
- `UNKNOWN`

For example:

```sql
NULL = NULL
```

does not evaluate to `TRUE`.

It evaluates to `UNKNOWN`.

Likewise:

```sql
NULL = 10
```

is `UNKNOWN`.

This is why:

```sql
WHERE phone_number = NULL
```

does not find rows where `phone_number` is null.

Use:

```sql
WHERE phone_number IS NULL
```

### Predicate Behavior

| Expression | Result |
|---|---|
| `NULL = NULL` | `UNKNOWN` |
| `NULL <> NULL` | `UNKNOWN` |
| `NULL = 10` | `UNKNOWN` |
| `NULL <> 10` | `UNKNOWN` |
| `NULL IS NULL` | `TRUE` |
| `NULL IS NOT NULL` | `FALSE` |

A `WHERE` clause retains rows only when its condition evaluates to `TRUE`.

Therefore, rows producing `UNKNOWN` are filtered out.

## NULL During INSERT

`INSERT` can explicitly store `NULL` when the target column permits it.

```sql
INSERT INTO users (
    id,
    email,
    phone_number
)
VALUES (
    1001,
    'user@example.com',
    NULL
);
```

You can also omit a nullable column:

```sql
INSERT INTO users (
    id,
    email
)
VALUES (
    1002,
    'user2@example.com'
);
```

These two statements can result in the same stored value for `phone_number`, but omission and explicit `NULL` have important differences when defaults exist.

## NULL vs DEFAULT During INSERT

Consider:

```sql
CREATE TABLE jobs (
    id bigint PRIMARY KEY,
    status text DEFAULT 'pending',
    started_at timestamptz
);
```

Omitting `status` allows the default to apply:

```sql
INSERT INTO jobs (id)
VALUES (1);
```

The result is:

```text
status = 'pending'
```

Explicitly inserting `NULL` does not mean "use the default":

```sql
INSERT INTO jobs (id, status)
VALUES (2, NULL);
```

The result is:

```text
status = NULL
```

This distinction is critical:

| INSERT behavior | Result |
|---|---|
| Column omitted | Default may apply |
| `DEFAULT` specified | Default expression is used |
| Explicit `NULL` | `NULL` is stored if permitted |

For example:

```sql
INSERT INTO jobs (id, status)
VALUES (3, DEFAULT);
```

uses the column default.

## NULL and NOT NULL

A `NOT NULL` constraint prevents a column from containing `NULL`.

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    email text NOT NULL
);
```

This fails:

```sql
INSERT INTO users (id, email)
VALUES (1, NULL);
```

It also fails if `email` is omitted and no applicable default provides a non-null value.

`NOT NULL` is therefore a database-level data-integrity guarantee, not merely an application validation rule.

For fields that are mandatory by domain semantics, enforce that invariant in the database.

## NULL During UPDATE

`UPDATE` can explicitly assign `NULL`:

```sql
UPDATE users
SET phone_number = NULL
WHERE id = $1;
```

This is useful when an optional attribute is intentionally cleared.

It is different from leaving the column unchanged.

For example:

```sql
UPDATE users
SET phone_number = $1
WHERE id = $2;
```

If `$1` is `NULL`, the column is cleared.

But if the application does not include `phone_number` in an update at all, the existing value remains unchanged.

This distinction is important for REST APIs:

```text
Field omitted
    -> preserve existing value

Field supplied as null
    -> clear existing value
```

Whether an API should expose that distinction depends on its contract.

## NULL During DELETE

`DELETE` predicates are affected by three-valued logic.

This does **not** delete users whose phone number is null:

```sql
DELETE FROM users
WHERE phone_number = NULL;
```

Use:

```sql
DELETE FROM users
WHERE phone_number IS NULL;
```

Similarly:

```sql
DELETE FROM users
WHERE phone_number IS NOT NULL;
```

deletes only rows where the value is known to be non-null.

## DML Predicate Safety

A common production failure is assuming that `NULL` behaves like an ordinary value.

Consider:

```sql
UPDATE orders
SET status = 'expired'
WHERE expires_at < CURRENT_TIMESTAMP
   OR expires_at >= CURRENT_TIMESTAMP;
```

This does **not** necessarily match every row.

For `expires_at = NULL`, both comparisons produce `UNKNOWN`.

The overall expression therefore does not become `TRUE`.

If null values have a defined business meaning, handle them explicitly:

```sql
UPDATE orders
SET status = 'expired'
WHERE expires_at < CURRENT_TIMESTAMP
   OR expires_at IS NULL;
```

Only do this when `NULL` actually means an order should be considered expired or otherwise belongs in the target set.

## NULL in SET Expressions

`NULL` propagates through many SQL expressions.

For example:

```sql
UPDATE products
SET discounted_price = price - discount
WHERE id = $1;
```

If `discount` is `NULL`, the result may also be `NULL`.

Conceptually:

```text
price - NULL
    |
    v
NULL
```

This can produce unexpected data if the application assumes missing discount means zero.

If the domain explicitly defines missing discount as zero, use:

```sql
UPDATE products
SET discounted_price = price - COALESCE(discount, 0)
WHERE id = $1;
```

Do not use `COALESCE` automatically. A missing value and zero can represent different business states.

## COALESCE in DML

`COALESCE` returns the first non-null expression.

```sql
COALESCE(value, fallback)
```

Example:

```sql
UPDATE users
SET display_name = COALESCE($1, display_name)
WHERE id = $2;
```

If `$1` is `NULL`, the existing value is retained.

This pattern is sometimes useful, but it has an important limitation: it prevents the caller from explicitly clearing the column.

If the API needs all three states:

```text
field omitted -> preserve
field null    -> clear
field value   -> replace
```

then `COALESCE` alone is insufficient.

## NULL and INSERT ... SELECT

`NULL` can propagate from a source query during an `INSERT ... SELECT`.

```sql
INSERT INTO customer_contacts (
    customer_id,
    phone_number
)
SELECT
    id,
    phone_number
FROM users;
```

If `users.phone_number` is null and `customer_contacts.phone_number` is nullable, null is inserted.

If the target column is `NOT NULL`, the operation can fail.

If the business rule requires a fallback:

```sql
INSERT INTO customer_contacts (
    customer_id,
    phone_number
)
SELECT
    id,
    COALESCE(phone_number, 'unknown')
FROM users;
```

The fallback should reflect an explicit domain decision rather than merely satisfy a constraint.

## NULL in UPDATE with JOIN

When updating from another table, nullable source columns require particular care.

For example:

```sql
UPDATE customer_profiles AS p
SET phone_number = c.phone_number
FROM customers AS c
WHERE p.customer_id = c.id;
```

If `c.phone_number` is null, the target value becomes null.

If that is not intended, explicitly define the desired behavior:

```sql
UPDATE customer_profiles AS p
SET phone_number = COALESCE(c.phone_number, p.phone_number)
FROM customers AS c
WHERE p.customer_id = c.id;
```

Again, this means "null from the source means preserve the target." That should be a deliberate business rule.

## NULL and Upserts

Upserts become subtle when nullable values are involved.

PostgreSQL example:

```sql
INSERT INTO users (id, email, phone_number)
VALUES ($1, $2, $3)
ON CONFLICT (id)
DO UPDATE
SET
    email = EXCLUDED.email,
    phone_number = EXCLUDED.phone_number;
```

If `$3` is `NULL`, the existing `phone_number` becomes `NULL`.

If the desired behavior is to preserve the existing value when the incoming value is null:

```sql
INSERT INTO users (id, email, phone_number)
VALUES ($1, $2, $3)
ON CONFLICT (id)
DO UPDATE
SET
    email = EXCLUDED.email,
    phone_number = COALESCE(EXCLUDED.phone_number, users.phone_number);
```

This changes the semantics from:

```text
incoming NULL -> clear
```

to:

```text
incoming NULL -> preserve
```

That distinction should be documented as part of the API and persistence contract.

## NULL and RETURNING

`RETURNING` can expose the final value after a DML operation.

For example:

```sql
UPDATE users
SET phone_number = NULL
WHERE id = $1
RETURNING id, phone_number;
```

The returned `phone_number` is `NULL`.

This is useful when the application needs confirmation of the resulting database state rather than assuming that the requested input exactly represents the persisted state.

## NULL and Foreign Keys

A nullable foreign key has different semantics from an invalid foreign key.

For example:

```sql
CREATE TABLE orders (
    id bigint PRIMARY KEY,
    assigned_employee_id bigint
        REFERENCES employees(id)
);
```

`assigned_employee_id = NULL` can be valid.

It means the order has no assigned employee.

But:

```sql
assigned_employee_id = 999999
```

must reference a valid employee if the foreign-key constraint is enforced.

This makes `NULL` useful for optional relationships:

```text
NULL
 |
 +-- no relationship currently exists
```

Do not use fake foreign-key values such as `0` or `-1` to represent "unassigned."

## NULL and UNIQUE Constraints

`NULL` and uniqueness require careful attention.

In PostgreSQL, a standard unique constraint generally allows multiple null values because nulls are not treated as equal for ordinary uniqueness enforcement.

For example:

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    phone_number text UNIQUE
);
```

Multiple users may have:

```text
phone_number = NULL
```

while non-null phone numbers must satisfy the uniqueness rule.

If the requirement is "at most one null," or some other special null semantics, use an explicit database design such as an appropriate partial or `NULLS NOT DISTINCT` constraint where supported by the target database/version.

## NULL and Aggregates

DML often depends on aggregates in maintenance or synchronization workflows.

Most aggregate functions ignore null inputs.

For example:

```sql
SELECT COUNT(phone_number)
FROM users;
```

counts only rows where `phone_number` is non-null.

Whereas:

```sql
SELECT COUNT(*)
FROM users;
```

counts rows regardless of whether `phone_number` is null.

This distinction becomes important when validating the effect of data modifications.

| Expression | Behavior |
|---|---|
| `COUNT(*)` | Counts rows |
| `COUNT(column)` | Counts non-null values |
| `SUM(column)` | Ignores null inputs |
| `AVG(column)` | Ignores null inputs |
| `MIN(column)` | Ignores null inputs |
| `MAX(column)` | Ignores null inputs |

## NULL and WHERE Conditions

Consider:

```sql
UPDATE users
SET status = 'inactive'
WHERE last_login_at < $1;
```

Users with `last_login_at = NULL` are not updated.

If the domain says "never logged in" should also be treated as inactive, make that rule explicit:

```sql
UPDATE users
SET status = 'inactive'
WHERE last_login_at < $1
   OR last_login_at IS NULL;
```

This is a common production distinction:

```text
NULL
 |
 +-- unknown
 +-- not applicable
 +-- never occurred
 +-- intentionally absent
```

SQL cannot determine which semantic interpretation you intended. The schema and application domain must define it.

## NULL and Boolean Columns

Boolean columns can technically have three states when nullable:

```text
TRUE
FALSE
NULL
```

This is sometimes appropriate, but often creates unnecessary complexity.

For example:

```sql
is_verified boolean
```

could mean:

```text
TRUE  -> verified
FALSE -> not verified
NULL  -> verification status unknown
```

If the domain only needs:

```text
verified / not verified
```

prefer:

```sql
is_verified boolean NOT NULL DEFAULT FALSE
```

Three-state booleans should be intentional, not accidental.

## NULL and API Design

Backend APIs need a clear contract for nullable fields.

Consider a PATCH-style endpoint:

```json
{
  "phone_number": null
}
```

This can mean:

```text
Clear phone number
```

while:

```json
{}
```

can mean:

```text
Leave phone number unchanged
```

The persistence layer must preserve this distinction.

A Python application can model this using an explicit "field provided" distinction rather than blindly converting missing fields to `None`.

The important principle is:

> Database `NULL` semantics should not be accidentally determined by framework defaults.

## NULL and Parameterized Queries

Application code should pass `NULL` through parameters rather than constructing SQL dynamically.

Preferred:

```python
cursor.execute(
    """
    UPDATE users
    SET phone_number = %s
    WHERE id = %s
    """,
    [phone_number, user_id],
)
```

If `phone_number` is `None`, the driver sends the appropriate database null value.

Avoid:

```python
query = f"""
UPDATE users
SET phone_number = {'NULL' if phone_number is None else repr(phone_number)}
WHERE id = {user_id}
"""
```

Parameterized queries provide safer SQL construction and cleaner type handling.

## NULL in Batch Processing

Batch jobs frequently encounter nullable columns.

For example:

```sql
UPDATE events
SET processed_at = CURRENT_TIMESTAMP
WHERE processed_at IS NULL
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '1 day';
```

This is safer than attempting:

```sql
WHERE processed_at = NULL
```

For large tables, combine correct null predicates with appropriate indexes and bounded processing strategies.

For PostgreSQL, a partial index may be appropriate for a frequently queried null state:

```sql
CREATE INDEX CONCURRENTLY idx_events_unprocessed
ON events (created_at)
WHERE processed_at IS NULL;
```

Whether this improves performance depends on data distribution and workload; verify with `EXPLAIN`.

## Performance Considerations

`IS NULL` itself is not inherently slow.

Performance depends on:

- Table size.
- Data distribution.
- Index design.
- Query selectivity.
- Database engine.
- Query plan.
- Concurrent workload.

For example:

```sql
UPDATE events
SET processed_at = CURRENT_TIMESTAMP
WHERE processed_at IS NULL;
```

can become expensive when a large percentage of the table matches.

For production workloads, inspect the execution plan and consider:

- Partial indexes.
- Batch processing.
- Short transactions.
- Appropriate locking strategy.
- Autovacuum behavior in PostgreSQL.
- Replication impact.

Large updates can generate substantial WAL, locks, vacuum work, and replica lag.

## Transaction and Reliability Considerations

DML involving nullable state should remain transactional when multiple related changes must be atomic.

For example:

```sql
BEGIN;

UPDATE orders
SET assigned_employee_id = NULL
WHERE id = $1;

INSERT INTO order_events (
    order_id,
    event_type
)
VALUES (
    $1,
    'unassigned'
);

COMMIT;
```

If both operations represent one business transition, they should normally succeed or fail together.

For workflows that publish external messages, database state and message delivery require a stronger design such as a transactional outbox.

## Common Mistakes

| Mistake | Why it fails | Correct approach |
|---|---|---|
| `WHERE column = NULL` | Comparison evaluates to `UNKNOWN` | `WHERE column IS NULL` |
| `WHERE column <> value` expecting nulls | Null rows produce `UNKNOWN` | Add explicit `IS NULL` logic |
| Treating null as empty string | Loses semantic distinction | Model absence explicitly |
| Using `NULL` to trigger a default | Explicit null does not mean default | Omit column or use `DEFAULT` |
| Using `COALESCE` everywhere | Can hide meaningful null semantics | Define domain behavior first |
| Nullable boolean without a reason | Creates unnecessary third state | Use `NOT NULL DEFAULT` when binary |
| Using sentinel foreign keys | Breaks referential semantics | Use nullable FK when relationship is optional |
| Assuming omitted API fields equal null | PATCH/update semantics become ambiguous | Distinguish omitted from explicit null |
| Returning nullable fields without documenting them | Clients may mishandle missing values | Define API schema clearly |
| Ignoring nulls in bulk DML | Rows may silently remain untouched | Test predicates against null cases |

## Production Checklist

Before deploying DML involving nullable fields, verify:

- Is `NULL` semantically different from an empty or zero value?
- Is the target column nullable?
- Should omission and explicit `NULL` behave differently?
- Should a default apply?
- Are `IS NULL` and `IS NOT NULL` used where required?
- Does a `<>` predicate unintentionally exclude null rows?
- Does `COALESCE` preserve the intended business semantics?
- Does an upsert treat incoming `NULL` as clear or preserve?
- Does the API distinguish omitted fields from explicit nulls?
- Could the operation affect a large percentage of the table?
- Does the relevant index support the predicate?
- Are transaction boundaries correct?
- Are audit, event, cache, and replication implications understood?
- Have both null and non-null test cases been exercised?

## Interview Traps

### Why does `column = NULL` not work?

Because comparisons involving `NULL` normally evaluate to `UNKNOWN`, not `TRUE`. `WHERE` retains only rows for which the predicate is `TRUE`.

### What is the difference between NULL and an empty string?

`NULL` represents absence of a value, while an empty string is an actual string value of length zero.

### Does explicit NULL use a column default?

No. Defaults generally apply when the column is omitted or when `DEFAULT` is explicitly specified. Explicit `NULL` stores `NULL` if allowed.

### Why can `WHERE column <> 'active'` miss rows?

Rows where `column` is `NULL` produce `UNKNOWN`, so they are not selected.

### Why can a nullable boolean be problematic?

It introduces three states:

```text
TRUE
FALSE
NULL
```

If the domain only requires two states, this adds unnecessary query and application complexity.

### Does `COUNT(column)` count NULL values?

No. `COUNT(column)` counts non-null values. `COUNT(*)` counts rows.

## Key Takeaways

- **`NULL` represents an absent value and participates in SQL's three-valued logic; comparisons such as `= NULL` and `<> NULL` do not produce `TRUE`.**
- **Use `IS NULL` and `IS NOT NULL` for null checks, and explicitly account for nulls when writing DML predicates.**
- **During `INSERT` and `UPDATE`, explicit `NULL`, omitted columns, and `DEFAULT` have different semantics and must not be conflated.**
- **`COALESCE`, nullable booleans, nullable foreign keys, and upserts should reflect deliberate domain semantics rather than being used merely to suppress null-related errors.**
- **Production DML involving `NULL` requires careful API semantics, indexing, transaction design, bulk-operation planning, and testing of both null and non-null cases.**