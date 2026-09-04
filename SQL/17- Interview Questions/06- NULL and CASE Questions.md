# 06- NULL and CASE Questions

## Overview

`NULL` and `CASE` are frequent SQL interview topics because they expose whether you understand SQL's three-valued logic, conditional expressions, aggregation semantics, and data modeling.

They are especially important in backend systems because nullable database fields commonly appear in:

- Optional attributes
- Soft deletes
- Partial state
- Missing timestamps
- Optional relationships
- Legacy data
- Migration transitions
- Multi-stage workflows

`CASE` is equally important for:

- Conditional projections
- Business classification
- Conditional aggregation
- Data transformation
- Ordering
- Reporting
- State mapping

The key senior-level principle is:

> **`NULL` does not mean zero, false, empty string, or an unknown business state unless the schema explicitly defines it that way.**

---

## What Is NULL?

`NULL` represents the absence of a value or an unknown/non-applicable value.

It is not:

```text
0
''
FALSE
```

For example:

```text
customer_id | deleted_at
------------+---------------------
101         | NULL
102         | 2026-08-20 10:00:00
```

`NULL` in `deleted_at` might mean:

> This record has not been deleted.

But the exact business meaning comes from the schema and application contract.

---

## Why NULL Exists

Relational systems need to represent situations where a value is not available or does not apply.

Examples:

```text
middle_name = NULL
```

The customer may not have provided a middle name.

```text
deleted_at = NULL
```

The record may still be active.

```text
shipped_at = NULL
```

The order may not have shipped yet.

The important distinction is:

> `NULL` represents missing/unknown/non-applicable information; it is not a normal value.

---

## NULL Is Not Equal to NULL

A classic interview question:

```sql
SELECT *
FROM users
WHERE middle_name = NULL;
```

This does not correctly find null values.

Use:

```sql
SELECT *
FROM users
WHERE middle_name IS NULL;
```

And:

```sql
WHERE middle_name IS NOT NULL
```

for non-null values.

---

## Why `= NULL` Does Not Work

SQL uses three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

An ordinary comparison involving `NULL` usually produces `UNKNOWN`.

For example:

```sql
NULL = NULL
```

does not evaluate to `TRUE`.

Conceptually:

```text
NULL = NULL
     ↓
UNKNOWN
```

A `WHERE` clause retains rows only when its condition evaluates to `TRUE`.

Therefore:

```sql
WHERE column = NULL
```

does not match null rows.

---

## Three-Valued Logic

SQL predicates can evaluate to:

| Result | Meaning |
|---|---|
| `TRUE` | Condition is satisfied |
| `FALSE` | Condition is not satisfied |
| `UNKNOWN` | Result cannot be determined because of `NULL` |

Example:

```sql
SELECT
    CASE
        WHEN NULL = 10 THEN 'true'
        WHEN NULL <> 10 THEN 'false'
        ELSE 'unknown'
    END;
```

The result is:

```text
unknown
```

This is one reason SQL does not behave exactly like ordinary two-valued Boolean logic in programming languages.

---

## NULL and Comparison Operators

For a nullable column:

```sql
column = 10
column <> 10
column > 10
column < 10
```

do not match rows where `column` is `NULL`.

To explicitly handle nullability:

```sql
column IS NULL
```

or:

```sql
column IS NOT NULL
```

---

## NULL and WHERE

Consider:

```text
status
------
paid
pending
NULL
```

Query:

```sql
SELECT *
FROM orders
WHERE status <> 'paid';
```

This returns:

```text
pending
```

The `NULL` row is not returned because:

```text
NULL <> 'paid'
```

evaluates to `UNKNOWN`.

If the requirement is:

> Everything except paid, including missing status

write the logic explicitly:

```sql
SELECT *
FROM orders
WHERE status <> 'paid'
   OR status IS NULL;
```

---

## NULL and AND

SQL's three-valued logic affects compound predicates.

Important cases:

| A | B | A AND B |
|---|---|---|
| TRUE | TRUE | TRUE |
| TRUE | FALSE | FALSE |
| TRUE | UNKNOWN | UNKNOWN |
| FALSE | UNKNOWN | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

Example:

```sql
WHERE status = 'paid'
  AND cancelled_at IS NULL
```

The condition is true only when both requirements are satisfied.

---

## NULL and OR

Important cases:

| A | B | A OR B |
|---|---|---|
| TRUE | UNKNOWN | TRUE |
| FALSE | UNKNOWN | UNKNOWN |
| FALSE | FALSE | FALSE |
| UNKNOWN | UNKNOWN | UNKNOWN |

Example:

```sql
WHERE status = 'paid'
   OR status IS NULL
```

The explicit `IS NULL` predicate is `TRUE` for null rows.

---

## NULL and NOT

`NOT` also interacts with three-valued logic.

For example:

```text
NOT TRUE    → FALSE
NOT FALSE   → TRUE
NOT UNKNOWN → UNKNOWN
```

Therefore:

```sql
WHERE NOT (status = 'paid')
```

does not include rows where `status` is `NULL`.

If nulls should be included, write that requirement explicitly.

---

## NULL and ORDER BY

PostgreSQL supports explicit null ordering:

```sql
ORDER BY created_at DESC NULLS LAST;
```

or:

```sql
ORDER BY created_at ASC NULLS FIRST;
```

This is preferable when the placement of missing values is part of the business or API requirement.

Do not rely on implicit null ordering when deterministic behavior matters.

---

## NULL and DISTINCT

`DISTINCT` treats null values as belonging to the same distinct result category.

For example:

```sql
SELECT DISTINCT middle_name
FROM users;
```

can return one `NULL` result even if many rows have a null middle name.

This is different from ordinary equality semantics.

---

## NULL and GROUP BY

Null values form a grouping category.

For example:

```sql
SELECT
    status,
    COUNT(*)
FROM orders
GROUP BY status;
```

Rows where:

```text
status IS NULL
```

are grouped together.

Conceptually:

```text
paid       → group
pending    → group
NULL       → group
```

This is another important interview distinction:

> `NULL` does not compare equal to `NULL`, but null values can form one group under `GROUP BY`.

---

## NULL and COUNT

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
COUNT(*)          → 3
COUNT(amount)     → 2
COUNT(DISTINCT amount) → 2
```

`COUNT(*)` counts rows.

`COUNT(column)` ignores null values.

---

## NULL and SUM

```sql
SELECT SUM(amount)
FROM payments;
```

`SUM` ignores null inputs.

For:

```text
100
200
NULL
```

the result is:

```text
300
```

If all input values are null, the result can be `NULL`.

Use:

```sql
COALESCE(SUM(amount), 0)
```

when zero is the intended business result.

---

## NULL and AVG

For:

```text
100
200
NULL
```

```sql
SELECT AVG(amount)
FROM payments;
```

returns:

```text
150
```

The null value is not treated as zero.

This distinction matters for metrics.

---

## NULL and MIN/MAX

`MIN` and `MAX` ignore null inputs.

Example:

```sql
SELECT
    MIN(amount),
    MAX(amount)
FROM payments;
```

Null values do not become the minimum or maximum.

If every input is null, the result is `NULL`.

---

## COALESCE

`COALESCE` returns the first non-null expression.

```sql
SELECT
    COALESCE(display_name, email, 'Unknown') AS name
FROM users;
```

Evaluation:

```text
display_name
    ↓
NULL?
    ↓ yes
email
    ↓
NULL?
    ↓ yes
'Unknown'
```

---

## When to Use COALESCE

Use `COALESCE` when the application needs a defined fallback.

Examples:

```sql
COALESCE(order_count, 0)
COALESCE(display_name, email)
COALESCE(discount, 0)
```

It is especially useful for API-facing aggregate values.

---

## COALESCE and Business Semantics

Do not automatically replace every `NULL` with zero.

These can mean different things:

```text
NULL → value is unknown
0    → value is known to be zero
```

For example:

```sql
COALESCE(balance, 0)
```

may be dangerous if `NULL` means:

> Balance has not been calculated yet.

The conversion should reflect business semantics.

---

## NULLIF

`NULLIF(a, b)` returns:

```text
NULL if a = b
a    otherwise
```

Example:

```sql
SELECT NULLIF(quantity, 0)
FROM inventory;
```

This can prevent division by zero:

```sql
SELECT
    total_amount / NULLIF(quantity, 0)
FROM order_items;
```

If `quantity = 0`, the denominator becomes `NULL` instead of causing a division-by-zero error.

---

## COALESCE + NULLIF

A common production pattern:

```sql
SELECT
    COALESCE(
        total_amount / NULLIF(quantity, 0),
        0
    ) AS unit_price
FROM order_items;
```

The semantics are:

```text
quantity = 0
    ↓
NULLIF → NULL
    ↓
division → NULL
    ↓
COALESCE → 0
```

Use this only when zero is genuinely the desired fallback.

---

## CASE Expression

`CASE` provides conditional logic inside SQL.

Basic form:

```sql
SELECT
    CASE
        WHEN status = 'paid' THEN 'completed'
        WHEN status = 'pending' THEN 'open'
        ELSE 'other'
    END AS status_group
FROM orders;
```

It is similar conceptually to conditional branching in application code.

---

## Why CASE Exists

`CASE` allows the database to derive values based on row contents.

Typical uses:

- Classification
- Business rules
- Conditional aggregation
- Data transformation
- Bucketing
- Sorting
- API projections

It can reduce unnecessary application-side transformation.

---

## Searched CASE

The most flexible form is:

```sql
CASE
    WHEN condition THEN result
    WHEN condition THEN result
    ELSE result
END
```

Example:

```sql
SELECT
    CASE
        WHEN total_amount >= 1000 THEN 'high'
        WHEN total_amount >= 500 THEN 'medium'
        ELSE 'low'
    END AS order_value_band
FROM orders;
```

Conditions are evaluated in order.

---

## CASE Evaluation Order

Consider:

```sql
CASE
    WHEN total_amount >= 500 THEN 'medium'
    WHEN total_amount >= 1000 THEN 'high'
    ELSE 'low'
END
```

An amount of `1500` matches:

```text
>= 500
```

first.

Therefore the result is:

```text
medium
```

Order conditions from most specific to least specific when ranges overlap.

---

## Simple CASE

A simple `CASE` compares one expression against multiple values:

```sql
CASE status
    WHEN 'paid' THEN 'completed'
    WHEN 'pending' THEN 'open'
    WHEN 'cancelled' THEN 'closed'
    ELSE 'unknown'
END
```

This is useful when the logic is equality-based.

---

## Searched CASE vs Simple CASE

| Form | Best suited for |
|---|---|
| Simple `CASE expression` | Equality against known values |
| Searched `CASE WHEN condition` | Ranges and complex predicates |

Example simple form:

```sql
CASE status
    WHEN 'paid' THEN 1
    WHEN 'pending' THEN 2
END
```

Example searched form:

```sql
CASE
    WHEN total_amount > 1000 THEN 'large'
    WHEN total_amount > 100 THEN 'medium'
    ELSE 'small'
END
```

---

## CASE and NULL

A `CASE` expression can explicitly handle nulls:

```sql
CASE
    WHEN shipped_at IS NULL THEN 'not shipped'
    ELSE 'shipped'
END
```

Avoid:

```sql
CASE
    WHEN shipped_at = NULL THEN 'not shipped'
    ELSE 'shipped'
END
```

because `shipped_at = NULL` is not a valid null test.

---

## CASE With ELSE

Always consider whether an explicit `ELSE` is appropriate.

Without `ELSE`:

```sql
CASE
    WHEN status = 'paid' THEN 'completed'
END
```

rows that do not match produce:

```text
NULL
```

An explicit fallback can make the result contract clearer:

```sql
CASE
    WHEN status = 'paid' THEN 'completed'
    ELSE 'other'
END
```

---

## CASE and Data Types

All branches of a `CASE` must resolve to a compatible result type.

Good:

```sql
CASE
    WHEN status = 'paid' THEN 'completed'
    ELSE 'pending'
END
```

Problematic logic can occur when branches mix incompatible types.

Prefer explicit casts when necessary rather than relying on complicated implicit conversion.

---

## CASE in SELECT

A common transformation:

```sql
SELECT
    id,
    status,
    CASE
        WHEN status = 'paid' THEN TRUE
        ELSE FALSE
    END AS is_completed
FROM orders;
```

In PostgreSQL, this could often be simplified to:

```sql
SELECT
    id,
    status,
    status = 'paid' AS is_completed
FROM orders;
```

Use `CASE` when conditional logic genuinely requires it.

---

## CASE in WHERE

`CASE` can be used in predicates:

```sql
SELECT *
FROM orders
WHERE
    CASE
        WHEN status = 'paid' THEN total_amount > 100
        ELSE TRUE
    END;
```

This is valid but can make predicates harder to optimize and reason about.

Often a Boolean expression is clearer:

```sql
WHERE status <> 'paid'
   OR total_amount > 100;
```

Prefer direct predicates when they express the requirement naturally.

---

## CASE in ORDER BY

You can implement custom ordering:

```sql
SELECT *
FROM orders
ORDER BY
    CASE status
        WHEN 'pending' THEN 1
        WHEN 'paid' THEN 2
        WHEN 'cancelled' THEN 3
        ELSE 4
    END,
    created_at DESC;
```

This is useful when business priority does not match lexical or chronological ordering.

---

## CASE in GROUP BY

You can group by a classification:

```sql
SELECT
    CASE
        WHEN total_amount >= 1000 THEN 'high'
        WHEN total_amount >= 500 THEN 'medium'
        ELSE 'low'
    END AS value_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN total_amount >= 1000 THEN 'high'
        WHEN total_amount >= 500 THEN 'medium'
        ELSE 'low'
    END;
```

For complex expressions, a CTE can improve readability.

---

## CASE in Aggregation

Conditional aggregation is one of the most common interview patterns.

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'paid' THEN total_amount
            ELSE 0
        END
    ) AS paid_revenue
FROM orders;
```

PostgreSQL also supports:

```sql
SELECT
    SUM(total_amount) FILTER (
        WHERE status = 'paid'
    ) AS paid_revenue
FROM orders;
```

The latter can be clearer when PostgreSQL-specific SQL is acceptable.

---

## COUNT With CASE

Count paid orders:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'paid' THEN 1
            ELSE 0
        END
    ) AS paid_orders
FROM orders;
```

Another approach is:

```sql
SELECT
    COUNT(*) FILTER (
        WHERE status = 'paid'
    ) AS paid_orders
FROM orders;
```

---

## CASE and NULL in Aggregation

Consider:

```sql
SUM(
    CASE
        WHEN status = 'paid' THEN total_amount
    END
)
```

There is no `ELSE`, so non-paid rows produce `NULL`.

`SUM` ignores those values.

This can be useful and is semantically different from:

```sql
SUM(
    CASE
        WHEN status = 'paid' THEN total_amount
        ELSE 0
    END
)
```

Both can produce the same result for many datasets, but understanding the null behavior is important.

---

## CASE vs COALESCE

These solve different problems.

`COALESCE`:

```sql
COALESCE(value, fallback)
```

means:

> Use a fallback when the value is `NULL`.

`CASE`:

```sql
CASE
    WHEN condition THEN value
    ELSE fallback
END
```

means:

> Choose a result based on a condition.

Example:

```sql
COALESCE(discount, 0)
```

is simpler than:

```sql
CASE
    WHEN discount IS NULL THEN 0
    ELSE discount
END
```

---

## NULL-Safe Equality in PostgreSQL

PostgreSQL provides:

```sql
IS DISTINCT FROM
IS NOT DISTINCT FROM
```

These operators provide deterministic comparison semantics even when `NULL` is involved.

Example:

```sql
SELECT *
FROM users
WHERE email IS NOT DISTINCT FROM $1;
```

If `$1` is `NULL`, this can match rows where `email` is also `NULL`.

This is different from:

```sql
email = $1
```

when `$1` is `NULL`.

---

## `IS DISTINCT FROM`

Example:

```sql
SELECT
    old_value IS DISTINCT FROM new_value AS changed
FROM ...
```

This is useful for change detection because it treats:

```text
NULL vs NULL → not changed
NULL vs value → changed
value vs NULL → changed
value vs same value → not changed
value vs different value → changed
```

This can be extremely useful in migration and synchronization logic.

---

## NULL and `NOT IN`

A major interview trap:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM blocked_customers
);
```

If the subquery contains `NULL`, the result can become unintuitive because `NOT IN` uses three-valued logic.

Prefer:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_customers AS b
    WHERE b.customer_id = customers.id
);
```

when expressing non-existence.

---

## NULL and `IN`

For:

```sql
WHERE status IN ('paid', 'pending')
```

a null status does not match.

This is expected because:

```text
NULL = 'paid'    → UNKNOWN
NULL = 'pending' → UNKNOWN
```

If null should be included, add it explicitly:

```sql
WHERE status IN ('paid', 'pending')
   OR status IS NULL;
```

---

## NULL and JOINs

Consider:

```sql
SELECT *
FROM orders AS o
JOIN customers AS c
    ON o.customer_id = c.id;
```

If:

```text
o.customer_id = NULL
```

the equality condition does not match.

Therefore that order is excluded from the inner join.

With:

```sql
LEFT JOIN
```

the order can remain, but customer columns become `NULL`.

---

## NULL and LEFT JOIN Filtering

This is a classic interview question.

Query:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

Customers without orders are removed.

Why?

For an unmatched customer:

```text
o.status = NULL
```

and:

```text
NULL = 'paid'
→ UNKNOWN
```

The `WHERE` clause removes the row.

---

## Correct LEFT JOIN Predicate

If all customers must remain:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'paid';
```

Now the status condition determines which orders match while preserving customers with no paid orders.

---

## NULL and Foreign Keys

A nullable foreign key:

```sql
customer_id bigint REFERENCES customers(id)
```

can contain `NULL`.

This commonly means:

> No related customer is assigned.

It does not violate the foreign key because `NULL` is not an invalid customer ID.

Whether the column should be nullable depends on the domain.

---

## NULL vs NOT NULL

Use `NOT NULL` when the application invariant requires a value.

Example:

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status text NOT NULL
);
```

This moves an important correctness guarantee into the database.

Do not make every field nullable simply because the application can handle missing values.

---

## NULL and Default Values

A default does not mean the column can never be null.

For example:

```sql
CREATE TABLE users (
    is_active boolean DEFAULT TRUE
);
```

An insert that omits `is_active` receives:

```text
TRUE
```

But an explicit:

```sql
INSERT INTO users (is_active)
VALUES (NULL);
```

can still produce `NULL` unless the column is also `NOT NULL`.

If the invariant is:

> `is_active` must always have a Boolean value

use:

```sql
is_active boolean NOT NULL DEFAULT TRUE
```

---

## NULL in API Design

Database nullability should map intentionally to API semantics.

For example:

```json
{
  "middle_name": null,
  "deleted_at": null
}
```

can be different from omitting the field entirely.

Backend APIs should define whether:

```text
missing
null
empty string
zero
false
```

have distinct meanings.

This is especially important for PATCH semantics.

---

## NULL in Django

Django's:

```python
null=True
```

controls database nullability.

For string fields, Django commonly distinguishes:

```text
NULL
''
```

depending on field configuration and application conventions.

Avoid introducing multiple representations for the same business state without a strong reason.

For example:

```text
NULL
''
'unknown'
```

can make filtering and uniqueness semantics unnecessarily complex.

---

## NULL in Pydantic / FastAPI

An API model can explicitly represent optional values.

Conceptually:

```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    middle_name: str | None
```

This should correspond to a deliberate API contract.

Do not assume database `NULL` automatically means the API field should be optional in every endpoint.

---

## NULL and PATCH Semantics

PATCH APIs often need to distinguish:

```text
field omitted
field explicitly set to null
field set to a value
```

For example:

```json
{}
```

can mean:

> Leave the current value unchanged.

While:

```json
{
  "middle_name": null
}
```

can mean:

> Clear the value.

This distinction belongs to API semantics as well as SQL semantics.

---

## CASE and State Machines

SQL `CASE` is useful for derived state.

Example:

```sql
SELECT
    id,
    CASE
        WHEN cancelled_at IS NOT NULL THEN 'cancelled'
        WHEN shipped_at IS NOT NULL THEN 'shipped'
        WHEN paid_at IS NOT NULL THEN 'paid'
        ELSE 'pending'
    END AS derived_status
FROM orders;
```

The ordering of conditions matters.

For production systems, prefer a canonical persisted status when the state itself is authoritative and complex rather than deriving it inconsistently across queries.

---

## CASE and Business Rules

Avoid putting large amounts of business logic into SQL `CASE` expressions when the same rules must be maintained across many services.

Good use:

```text
simple classification
reporting
database-side projection
conditional aggregation
```

Potentially problematic:

```text
hundreds of lines of evolving business rules
```

Such logic may be better represented in application code, a dedicated rules layer, or a normalized state model.

---

## CASE and Performance

A `CASE` expression itself is usually not a problem.

The issue is often using expressions around indexed columns in filtering predicates.

For example:

```sql
WHERE
    CASE
        WHEN status = 'paid' THEN customer_id
        ELSE NULL
    END = $1
```

can be harder to optimize than a direct predicate.

Prefer predicates that preserve straightforward access paths where possible.

---

## CASE and Indexes

If the same derived expression is queried frequently, PostgreSQL can support expression indexes.

For example:

```sql
CREATE INDEX idx_orders_active_customer
ON orders (customer_id)
WHERE deleted_at IS NULL;
```

A partial index may be preferable to embedding equivalent conditional logic inside every query.

The index should match the actual workload.

---

## CASE and Generated Columns

For stable derived values, a generated column can sometimes be more appropriate than repeating a complex expression.

The choice depends on:

- Expression stability
- Query frequency
- Storage requirements
- Update cost
- Indexing needs
- Database capabilities

Do not materialize every `CASE` expression automatically.

---

## NULL and Conditional Aggregation

A useful pattern for counting records with a condition:

```sql
SELECT
    COUNT(*) FILTER (
        WHERE shipped_at IS NOT NULL
    ) AS shipped_count,
    COUNT(*) FILTER (
        WHERE shipped_at IS NULL
    ) AS pending_shipment_count
FROM orders;
```

Equivalent `CASE` form:

```sql
SELECT
    SUM(
        CASE
            WHEN shipped_at IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS shipped_count,
    SUM(
        CASE
            WHEN shipped_at IS NULL THEN 1
            ELSE 0
        END
    ) AS pending_shipment_count
FROM orders;
```

---

## NULL and Boolean Columns

A nullable Boolean has three possible states:

```text
TRUE
FALSE
NULL
```

This may be intentional, but it creates more complexity than:

```text
TRUE
FALSE
```

For example:

```sql
WHERE is_active = FALSE
```

does not match:

```text
NULL
```

If the application requires a binary state, prefer:

```sql
is_active boolean NOT NULL DEFAULT TRUE
```

---

## Three-State Business Logic

Nullable booleans can be appropriate when:

```text
TRUE  → explicitly approved
FALSE → explicitly rejected
NULL  → not reviewed
```

In this case, collapsing `NULL` to `FALSE` would destroy information.

This is a good example of why nullability should reflect domain semantics rather than convenience.

---

## NULL and Dates

Nullable timestamps are common:

```text
created_at
paid_at
shipped_at
cancelled_at
```

A null timestamp can represent an event that has not occurred.

For example:

```sql
WHERE shipped_at IS NULL
```

means:

> The shipment timestamp has not been recorded.

This is often clearer than storing a sentinel date such as:

```text
1970-01-01
```

---

## Avoid Sentinel Values

Bad modeling can use:

```text
-1
0
''
1970-01-01
9999-12-31
```

to represent missing values.

This creates ambiguity because the sentinel becomes part of application logic.

Prefer `NULL` when the domain genuinely needs absence.

---

## NULL and Uniqueness

PostgreSQL allows multiple `NULL` values in a normal unique constraint because null values are not treated as equal for ordinary uniqueness semantics.

For example:

```sql
CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    external_id text UNIQUE
);
```

multiple rows can have:

```text
external_id = NULL
```

If the requirement is:

> Only non-null values must be unique

this behavior is often exactly what is wanted.

---

## Partial Unique Index and NULL

A partial unique index can encode a more specific invariant.

Example:

```sql
CREATE UNIQUE INDEX idx_active_user_email
ON users (email)
WHERE deleted_at IS NULL;
```

This can enforce uniqueness among active users while allowing historical soft-deleted rows to retain the same email.

This is a strong example of combining `NULL` semantics with database-enforced business rules.

---

## NULL and Soft Deletes

A common pattern:

```sql
deleted_at timestamptz NULL
```

Active rows:

```text
deleted_at IS NULL
```

Deleted rows:

```text
deleted_at IS NOT NULL
```

A partial index can optimize active records:

```sql
CREATE INDEX idx_active_orders_customer
ON orders (customer_id)
WHERE deleted_at IS NULL;
```

This is often preferable to indexing every historical row when active records dominate application traffic.

---

## NULL and Query Correctness

When a query returns unexpected results, explicitly inspect:

```sql
SELECT
    COUNT(*) AS total,
    COUNT(column_name) AS non_null,
    COUNT(*) - COUNT(column_name) AS null_count
FROM table_name;
```

This quickly reveals whether nullability is influencing the result.

---

## Practical Interview Questions

### How Do You Find NULL Values?

```sql
SELECT *
FROM users
WHERE middle_name IS NULL;
```

Not:

```sql
WHERE middle_name = NULL;
```

---

### How Do You Find Non-NULL Values?

```sql
SELECT *
FROM users
WHERE middle_name IS NOT NULL;
```

---

### Why Does `NULL = NULL` Not Return TRUE?

Because SQL uses three-valued logic and ordinary comparisons involving `NULL` produce `UNKNOWN`.

Use:

```sql
IS NULL
```

or PostgreSQL's:

```sql
IS NOT DISTINCT FROM
```

when null-safe equality is required.

---

### What Does `COUNT(column)` Do With NULL?

It ignores null values.

---

### What Does `COUNT(*)` Do With NULL?

It counts the row regardless of null values.

---

### What Does `SUM()` Do With NULL?

It ignores null inputs. If there are no non-null values, the aggregate can return `NULL`.

---

### What Is the Difference Between NULL and Zero?

`NULL` represents missing/unknown/non-applicable information.

`0` is a known numeric value.

They should not be treated as interchangeable without explicit business semantics.

---

### What Is the Difference Between NULL and Empty String?

`NULL` represents absence/unknown information.

`''` is a string value containing zero characters.

They are different database values.

---

### What Is Three-Valued Logic?

SQL predicates can evaluate to:

```text
TRUE
FALSE
UNKNOWN
```

`NULL` commonly causes `UNKNOWN`.

---

### Why Does `NOT IN` Behave Unexpectedly With NULL?

Because if the compared set contains `NULL`, the predicate can evaluate to `UNKNOWN`.

Use `NOT EXISTS` when expressing non-existence.

---

### What Is COALESCE?

`COALESCE` returns the first non-null expression.

```sql
COALESCE(value, fallback)
```

---

### What Is NULLIF?

`NULLIF(a, b)` returns `NULL` when `a = b`; otherwise it returns `a`.

It is commonly used to prevent division by zero:

```sql
value / NULLIF(denominator, 0)
```

---

### What Is CASE?

`CASE` is a conditional SQL expression that returns a value based on one or more conditions.

---

### What Is the Difference Between CASE and COALESCE?

`CASE` evaluates arbitrary conditions.

`COALESCE` specifically chooses the first non-null expression.

---

### Does CASE Return NULL?

Yes.

If no `WHEN` matches and there is no `ELSE`, the result is `NULL`.

---

### Does CASE Evaluate Conditions in Order?

Yes, conditions are evaluated in order and the first matching branch determines the result.

Do not write overlapping conditions without understanding their ordering.

---

## Practical SQL Problems

### Replace NULL With a Default Display Name

```sql
SELECT
    COALESCE(display_name, email) AS display_name
FROM users;
```

---

### Find Orders That Have Not Shipped

```sql
SELECT *
FROM orders
WHERE shipped_at IS NULL;
```

---

### Classify Orders by Value

```sql
SELECT
    id,
    CASE
        WHEN total_amount >= 1000 THEN 'high'
        WHEN total_amount >= 500 THEN 'medium'
        ELSE 'low'
    END AS value_band
FROM orders;
```

---

### Count Orders by Shipment State

```sql
SELECT
    COUNT(*) FILTER (
        WHERE shipped_at IS NOT NULL
    ) AS shipped_orders,
    COUNT(*) FILTER (
        WHERE shipped_at IS NULL
    ) AS unshipped_orders
FROM orders;
```

---

### Calculate Paid Revenue Safely

```sql
SELECT
    COALESCE(
        SUM(total_amount) FILTER (
            WHERE status = 'paid'
        ),
        0
    ) AS paid_revenue
FROM orders;
```

---

### Prevent Division by Zero

```sql
SELECT
    total_amount / NULLIF(quantity, 0) AS unit_price
FROM order_items;
```

---

### Find Records Whose Value Changed

PostgreSQL:

```sql
SELECT *
FROM records
WHERE old_value IS DISTINCT FROM new_value;
```

---

### Find Customers With No Orders

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This avoids the common `NOT IN` + `NULL` trap.

---

## Debugging NULL-Related Bugs

When a query behaves unexpectedly:

```text
Unexpected result
      ↓
Check nullable columns
      ↓
Check = / <> predicates
      ↓
Check IS NULL / IS NOT NULL
      ↓
Check AND / OR / NOT
      ↓
Check NOT IN
      ↓
Check JOIN predicates
      ↓
Check aggregation
      ↓
Check COALESCE / CASE
```

A useful diagnostic query:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(target_column) AS non_null_rows,
    COUNT(*) - COUNT(target_column) AS null_rows
FROM target_table;
```

---

## Debugging CASE Logic

When a `CASE` result is wrong, test the conditions independently.

For example:

```sql
SELECT
    id,
    total_amount,
    total_amount >= 1000 AS high_condition,
    total_amount >= 500 AS medium_condition
FROM orders;
```

Then compare with:

```sql
SELECT
    id,
    CASE
        WHEN total_amount >= 1000 THEN 'high'
        WHEN total_amount >= 500 THEN 'medium'
        ELSE 'low'
    END AS value_band
FROM orders;
```

This makes overlapping conditions easier to detect.

---

## NULL and Query Performance

Null handling itself is usually not the performance problem.

The important considerations are:

- Predicate shape
- Index availability
- Selectivity
- Expression usage
- Statistics
- Data distribution

For example:

```sql
WHERE deleted_at IS NULL
```

can work efficiently with an appropriate partial index:

```sql
CREATE INDEX idx_orders_active
ON orders (customer_id)
WHERE deleted_at IS NULL;
```

Always validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

---

## NULL and Partial Indexes

Partial indexes are especially useful when a nullable column separates hot and cold records.

Example:

```text
deleted_at IS NULL
```

identifies active records.

Index:

```sql
CREATE INDEX idx_active_customer_orders
ON orders (customer_id)
WHERE deleted_at IS NULL;
```

Benefits can include:

- Smaller index
- Lower write-maintenance cost
- Better cache utilization
- Faster active-record queries

The workload must actually match the predicate for the index to be useful.

---

## NULL and Constraints

Use constraints to encode intended nullability:

```sql
CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    paid_at timestamptz,
    amount numeric(12, 2) NOT NULL CHECK (amount >= 0)
);
```

Here:

```text
order_id → required
amount   → required
paid_at  → optional
```

This communicates domain semantics directly through the schema.

---

## NULL and Transactions

Within a transaction, `NULL` can represent an intermediate state.

For example:

```text
order created
paid_at = NULL
```

Later:

```text
payment completed
paid_at = timestamp
```

If multiple services update related state, define transaction boundaries and state transitions carefully.

Do not use nullability as an uncontrolled substitute for explicit state management.

---

## NULL in Migrations

During an expand-and-contract migration, a new column is often introduced as nullable:

```sql
ALTER TABLE orders
ADD COLUMN processed_at timestamptz;
```

The application can begin populating it before the column becomes mandatory.

Later:

```text
add nullable column
        ↓
deploy compatible application
        ↓
backfill
        ↓
validate
        ↓
enforce NOT NULL if required
```

This is a common production use of intentional nullability.

---

## NULL and Backfills

A backfill often uses:

```sql
UPDATE orders
SET processed_at = created_at
WHERE processed_at IS NULL
  AND id > $1
  AND id <= $2;
```

The `IS NULL` predicate makes the operation idempotent for already-processed rows.

For large tables, execute the backfill in bounded batches rather than one enormous transaction.

---

## NULL and Idempotency

A nullable field can sometimes represent whether a processing step has occurred:

```text
processed_at IS NULL
    → not processed
processed_at IS NOT NULL
    → processed
```

This can be useful, but concurrency still needs to be considered.

For reliable workers, combine state checks with appropriate locking or atomic updates when multiple workers can process the same row.

---

## NULL and Authorization

A nullable relationship should not automatically imply authorization.

For example:

```sql
WHERE organization_id IS NULL
```

does not mean:

> The user is allowed to access this resource.

Authorization should be explicitly enforced through:

- Tenant predicates
- Membership checks
- RLS
- Database roles
- Application authorization

Nullability is a data property, not an authorization mechanism.

---

## Common Mistakes

### Using `= NULL`

Wrong:

```sql
WHERE deleted_at = NULL
```

Correct:

```sql
WHERE deleted_at IS NULL
```

### Treating NULL as Zero

Wrong:

```text
NULL revenue = 0 revenue
```

unless the business contract explicitly defines it that way.

### Using `NOT IN` With Nullable Data

Prefer:

```sql
NOT EXISTS
```

for non-existence logic.

### Forgetting NULL in `<>` Conditions

```sql
status <> 'paid'
```

does not include null statuses.

### Using CASE Conditions in the Wrong Order

Overlapping conditions can cause the first matching branch to win.

### Omitting ELSE Without Intention

No matching `CASE` branch produces `NULL`.

### Using CASE to Hide Poor Query Design

Complex conditional logic inside predicates can make queries harder to optimize and maintain.

### Creating Nullable Booleans Without a Reason

A nullable Boolean creates three states.

Use `NOT NULL` when only two states are valid.

### Replacing NULL With Sentinel Values

Values such as `-1`, `0`, or fake dates can make domain semantics ambiguous.

### Using COALESCE Blindly

Converting unknown into zero or another fallback can hide data-quality problems.

---

## Interview Traps

### Is NULL Equal to NULL?

No.

```sql
NULL = NULL
```

produces `UNKNOWN`.

---

### Can NULL Be Compared With `=`?

Not for null testing.

Use:

```sql
IS NULL
```

or:

```sql
IS NOT NULL
```

---

### Does `WHERE column <> 'x'` Include NULL?

No.

The comparison evaluates to `UNKNOWN`.

---

### Does GROUP BY Treat NULL Values as One Group?

Yes.

Rows with null grouping values are grouped together.

---

### Does COUNT(column) Count NULL?

No.

---

### Does COUNT(*) Count NULL?

Yes, because it counts rows.

---

### Does SUM(NULL) Return Zero?

Not necessarily.

`SUM` ignores null inputs, but if there are no non-null values, the aggregate can be `NULL`.

Use `COALESCE` when zero is required.

---

### What Happens if CASE Has No ELSE?

Unmatched rows return `NULL`.

---

### What Happens if Multiple CASE Conditions Match?

The first matching `WHEN` branch is selected.

---

### Why Is `NOT IN` Dangerous With NULL?

A `NULL` in the compared set can cause the predicate to become `UNKNOWN`.

Use `NOT EXISTS` for robust non-existence semantics.

---

### What Is the Difference Between `NULLIF` and `COALESCE`?

```sql
NULLIF(a, b)
```

turns a matching value into `NULL`.

```sql
COALESCE(a, b)
```

replaces `NULL` with the first available non-null value.

---

### When Should You Use `IS DISTINCT FROM`?

When PostgreSQL null-safe comparison semantics are required, especially for change detection or synchronization.

---

## Senior-Level Reasoning

At senior level, NULL questions are rarely just syntax questions.

Interviewers may expect you to reason about:

```text
NULL semantics
    ↓
query correctness
    ↓
aggregation
    ↓
JOIN behavior
    ↓
constraints
    ↓
API contracts
    ↓
migrations
    ↓
data quality
```

For example:

> "We need to find all users who did not complete onboarding."

You should first determine whether:

```text
completed_at IS NULL
```

actually means:

> onboarding not completed

or whether `NULL` could also mean:

> legacy record
> unknown status
> migration incomplete
> processing failed

The correct SQL depends on the domain semantics.

---

## Production Design Heuristic

When designing nullable fields, ask:

1. What does `NULL` mean?
2. Is `NULL` different from zero, empty, false, or unknown?
3. Can the field safely be `NOT NULL`?
4. Will queries frequently filter by `IS NULL` or `IS NOT NULL`?
5. Does the field require an index or partial index?
6. How will the value map to API semantics?
7. How will migrations and backfills handle it?
8. Does nullability affect authorization or tenant isolation?
9. Does a nullable Boolean create an unnecessary third state?
10. Can the database enforce the intended invariant?

---

## Production Checklist

Before shipping SQL involving `NULL` or `CASE`:

- [ ] `NULL` semantics are explicitly understood.
- [ ] Null comparisons use `IS NULL` / `IS NOT NULL`.
- [ ] Three-valued logic is considered.
- [ ] `NOT IN` is avoided when nullable values can cause ambiguity.
- [ ] `EXISTS` / `NOT EXISTS` is considered for existence logic.
- [ ] `COUNT(*)` vs `COUNT(column)` is intentional.
- [ ] Aggregate `NULL` behavior is understood.
- [ ] `COALESCE` is used only when the fallback is semantically correct.
- [ ] `CASE` conditions are ordered correctly.
- [ ] `CASE` has an intentional `ELSE` behavior.
- [ ] Boolean columns are nullable only when a third state is meaningful.
- [ ] Tenant and authorization predicates are independent of nullability.
- [ ] API semantics distinguish null, missing, empty, and zero where required.
- [ ] Large backfills are batched.
- [ ] Relevant partial/expression indexes are evaluated.
- [ ] Query plans are validated for important workloads.

---

## Key Takeaways

- **`NULL` is not a normal value:** SQL uses three-valued logic, so `NULL` requires `IS NULL`, `IS NOT NULL`, and deliberate handling in comparisons, joins, filters, and aggregates.
- **`NULL` semantics determine correctness:** distinguish missing, unknown, zero, false, and empty values instead of collapsing them through `COALESCE` or sentinel values without a business reason.
- **`CASE` is conditional data transformation:** use it for classification, projections, ordering, and conditional aggregation, while keeping overlapping conditions and `ELSE` behavior explicit.
- **`NOT EXISTS` and PostgreSQL null-safe operators solve important edge cases:** prefer `NOT EXISTS` over nullable `NOT IN` patterns and use `IS DISTINCT FROM` when null-safe comparison is required.
- **Senior SQL design connects nullability to the whole system:** constraints, partial indexes, APIs, migrations, backfills, authorization, and data quality should all reflect the intended meaning of `NULL`.