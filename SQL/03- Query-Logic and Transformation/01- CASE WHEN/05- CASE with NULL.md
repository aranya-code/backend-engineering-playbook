# 05- CASE with NULL

## Overview

`NULL` is not an ordinary value in SQL. It represents the absence of a known value, and comparisons involving `NULL` use SQL's three-valued logic: `TRUE`, `FALSE`, and `UNKNOWN`.

Because `CASE` selects a `WHEN` branch only when its condition evaluates to `TRUE`, `NULL` can change classification logic in ways that are easy to miss.

For example:

```sql
SELECT
    CASE
        WHEN shipped_at > CURRENT_TIMESTAMP THEN 'future'
        ELSE 'shipped'
    END AS shipment_state
FROM orders;
```

If `shipped_at` is `NULL`, the comparison:

```sql
shipped_at > CURRENT_TIMESTAMP
```

evaluates to `UNKNOWN`, not `FALSE`. The `WHEN` does not match, so the `ELSE` branch is selected.

For production SQL, treat `NULL` handling as part of the business rule rather than as an afterthought.

## Why NULL Requires Special Handling

Consider a table containing:

```text
order_id | shipped_at
---------+-------------------
1001     | 2026-08-30 10:00
1002     | NULL
```

A query such as:

```sql
SELECT
    order_id,
    CASE
        WHEN shipped_at > CURRENT_TIMESTAMP THEN 'future'
        ELSE 'shipped'
    END AS state
FROM orders;
```

does not mean:

```text
NULL -> FALSE -> shipped
```

The actual reasoning is:

```text
NULL > CURRENT_TIMESTAMP
        ↓
     UNKNOWN
        ↓
WHEN requires TRUE
        ↓
ELSE
```

This distinction becomes important when `NULL` represents a meaningful domain state such as:

- Not yet processed
- Not yet shipped
- Not assigned
- Unknown
- Not applicable
- Missing source data
- Pending external processing

## Three-Valued Logic

SQL predicates can produce three logical outcomes.

| Condition result | Meaning | Does `WHEN` match? |
| --- | --- | --- |
| `TRUE` | Condition satisfied | Yes |
| `FALSE` | Condition not satisfied | No |
| `UNKNOWN` | Result cannot be determined because of `NULL` or related semantics | No |

Example:

```sql
SELECT
    CASE
        WHEN amount > 1000 THEN 'large'
        WHEN amount <= 1000 THEN 'small'
        ELSE 'unknown'
    END AS category
FROM orders;
```

For:

```text
amount = NULL
```

both comparisons evaluate to `UNKNOWN`.

Therefore:

```text
ELSE -> unknown
```

is selected.

This is often the correct result if `NULL` means that the amount is unavailable.

## Explicit NULL Detection

Use `IS NULL` and `IS NOT NULL` to test for `NULL`.

Correct:

```sql
CASE
    WHEN amount IS NULL THEN 'missing'
    WHEN amount > 1000 THEN 'large'
    ELSE 'small'
END
```

Incorrect:

```sql
CASE
    WHEN amount = NULL THEN 'missing'
    ELSE 'known'
END
```

The expression:

```sql
amount = NULL
```

does not evaluate to `TRUE` for a `NULL` amount.

Use:

```sql
amount IS NULL
```

instead.

Similarly:

```sql
amount IS NOT NULL
```

is the correct test for presence.

## NULL and Equality

These expressions behave differently from ordinary equality:

```sql
NULL = NULL
```

and:

```sql
NULL <> NULL
```

Both produce `UNKNOWN`.

Therefore:

```sql
CASE
    WHEN status = NULL THEN 'missing'
    ELSE 'present'
END
```

does not correctly identify `NULL`.

Use:

```sql
CASE
    WHEN status IS NULL THEN 'missing'
    ELSE 'present'
END
```

## Handling NULL as a Distinct Business State

A common production pattern is to explicitly classify `NULL`.

```sql
SELECT
    customer_id,
    CASE
        WHEN phone_number IS NULL THEN 'missing'
        WHEN phone_verified_at IS NULL THEN 'unverified'
        ELSE 'verified'
    END AS phone_state
FROM customers;
```

This distinguishes:

```text
NULL phone_number       -> missing
known phone + NULL date -> unverified
known phone + date      -> verified
```

The ordering matters.

If the phone number is missing, the customer cannot meaningfully be classified as verified.

## NULL and CASE Branch Ordering

`NULL` conditions should usually appear before broader conditions when they represent a distinct state.

Prefer:

```sql
CASE
    WHEN shipped_at IS NULL THEN 'not_shipped'
    WHEN shipped_at > CURRENT_TIMESTAMP THEN 'scheduled'
    ELSE 'shipped'
END
```

over:

```sql
CASE
    WHEN shipped_at > CURRENT_TIMESTAMP THEN 'scheduled'
    ELSE 'shipped'
END
```

The second query collapses both:

```text
shipped_at < now
shipped_at IS NULL
```

into the same output.

That may be incorrect if the application needs to distinguish those states.

## NULL in Date and Time Logic

Date comparisons are especially susceptible to accidental `NULL` handling.

Consider:

```sql
CASE
    WHEN expires_at < CURRENT_TIMESTAMP THEN 'expired'
    ELSE 'active'
END
```

If:

```text
expires_at = NULL
```

the comparison is `UNKNOWN`, so the row becomes:

```text
active
```

This may incorrectly imply that the record is currently valid.

A safer domain-specific classification is:

```sql
CASE
    WHEN expires_at IS NULL THEN 'no_expiry'
    WHEN expires_at < CURRENT_TIMESTAMP THEN 'expired'
    ELSE 'active'
END
```

Now the result distinguishes:

```text
NULL       -> no_expiry
past date  -> expired
future date -> active
```

## NULL in Numeric Classification

Suppose a risk score is optional:

```sql
CASE
    WHEN risk_score >= 80 THEN 'high'
    WHEN risk_score >= 50 THEN 'medium'
    ELSE 'low'
END
```

A `NULL` score becomes `low`.

That is potentially dangerous because:

```text
NULL != low
```

If the score is unavailable, use:

```sql
CASE
    WHEN risk_score IS NULL THEN 'unrated'
    WHEN risk_score >= 80 THEN 'high'
    WHEN risk_score >= 50 THEN 'medium'
    ELSE 'low'
END
```

This prevents missing information from being interpreted as a favorable or unfavorable business value.

## NULL in Boolean Columns

Boolean columns can also contain `NULL` unless constrained otherwise.

For example:

```text
is_verified
-----------
TRUE
FALSE
NULL
```

These represent three potentially distinct states:

```text
TRUE  -> verified
FALSE -> explicitly not verified
NULL  -> unknown / not evaluated
```

A `CASE` can preserve that distinction:

```sql
CASE
    WHEN is_verified IS TRUE THEN 'verified'
    WHEN is_verified IS FALSE THEN 'not_verified'
    ELSE 'unknown'
END
```

This is often preferable to:

```sql
CASE
    WHEN is_verified = TRUE THEN 'verified'
    ELSE 'not_verified'
END
```

The latter maps `NULL` into `not_verified`.

Whether that is correct depends on the domain.

## IS TRUE and IS FALSE

Some SQL databases support predicates such as:

```sql
is_verified IS TRUE
```

and:

```sql
is_verified IS FALSE
```

These are useful when the distinction between:

```text
TRUE
FALSE
NULL
```

matters.

For PostgreSQL:

```sql
CASE
    WHEN is_verified IS TRUE THEN 'verified'
    WHEN is_verified IS FALSE THEN 'not_verified'
    ELSE 'unknown'
END
```

is explicit and avoids relying on implicit three-valued logic.

## NULL and String Values

Do not confuse:

```text
NULL
```

with:

```text
''
```

An empty string is a value; `NULL` represents absence of a known value.

For example:

```sql
CASE
    WHEN display_name IS NULL THEN 'missing'
    WHEN display_name = '' THEN 'empty'
    ELSE 'present'
END
```

This distinguishes:

| `display_name` | Result |
| --- | --- |
| `NULL` | `missing` |
| `''` | `empty` |
| `'Aranya'` | `present` |

Whether empty strings should be accepted should be defined by the application's data model and validation layer.

## CASE with COALESCE

`COALESCE` is often useful when the requirement is to replace `NULL` with a fallback value.

```sql
SELECT
    COALESCE(display_name, 'Unknown') AS display_name
FROM customers;
```

A `CASE` can express the same idea:

```sql
SELECT
    CASE
        WHEN display_name IS NULL THEN 'Unknown'
        ELSE display_name
    END AS display_name
FROM customers;
```

For simple fallback logic, `COALESCE` is usually clearer.

Use `CASE` when the transformation contains actual conditional business rules.

For example:

```sql
CASE
    WHEN deleted_at IS NOT NULL THEN 'deleted'
    WHEN status IS NULL THEN 'unknown'
    ELSE status
END
```

is more expressive than a simple `COALESCE`.

## CASE with NULLIF

`NULLIF` is useful when a specific value should be treated as `NULL`.

For example:

```sql
NULLIF(quantity, 0)
```

turns zero into `NULL`.

This can be combined with `CASE`:

```sql
CASE
    WHEN NULLIF(quantity, 0) IS NULL THEN 'invalid_quantity'
    ELSE 'valid_quantity'
END
```

For safe division:

```sql
SELECT
    revenue / NULLIF(quantity, 0) AS revenue_per_unit
FROM product_metrics;
```

This is preferable to relying on a `CASE` expression to protect an unsafe arithmetic operation.

## CASE and Aggregates with NULL

`NULL` interacts strongly with aggregate functions.

Consider:

```sql
SUM(
    CASE
        WHEN status = 'completed' THEN amount
    END
)
```

Rows that do not satisfy the condition produce `NULL`, and `SUM` generally ignores `NULL` values.

An explicit alternative is:

```sql
SUM(
    CASE
        WHEN status = 'completed' THEN amount
        ELSE 0
    END
)
```

The distinction becomes important when no rows satisfy the condition.

For example:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
        END
    ) AS completed_amount,
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_amount_zero
FROM orders;
```

Depending on the dataset, the first expression may return `NULL` while the second returns `0`.

Choose based on the meaning required by the API or report.

## NULL and COUNT

`COUNT` has different behavior depending on what is being counted.

```sql
COUNT(*)
```

counts rows, including rows containing `NULL`.

But:

```sql
COUNT(column_name)
```

counts only non-`NULL` values.

This matters when combined with `CASE`.

For example:

```sql
SELECT
    COUNT(
        CASE
            WHEN status = 'completed' THEN order_id
        END
    ) AS completed_orders
FROM orders;
```

Non-matching rows produce `NULL`, which `COUNT(expression)` ignores.

A common alternative is:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN 1
            ELSE 0
        END
    ) AS completed_orders
FROM orders;
```

Both patterns can be valid. Choose the one whose semantics are easiest to review and maintain.

## NULL and Conditional Joins

Avoid hiding join conditions inside unnecessary `CASE` expressions.

Instead of:

```sql
JOIN accounts a
    ON CASE
        WHEN u.account_id IS NULL THEN 0
        ELSE u.account_id
       END = a.id
```

prefer a domain-appropriate direct join.

If `NULL` has special join semantics, make that requirement explicit.

For example:

```sql
JOIN accounts a
    ON u.account_id = a.id
```

naturally does not match when `u.account_id` is `NULL`.

If unmatched rows must still be preserved, use an appropriate outer join:

```sql
FROM users u
LEFT JOIN accounts a
    ON u.account_id = a.id
```

The distinction between `NULL` handling in a `CASE` expression and `NULL` behavior in joins is important when designing production queries.

## NULL and ORDER BY

Sorting `NULL` values is database-specific.

For predictable behavior, use explicit ordering when supported.

PostgreSQL example:

```sql
SELECT
    customer_id,
    last_login_at
FROM customers
ORDER BY
    CASE
        WHEN last_login_at IS NULL THEN 1
        ELSE 0
    END,
    last_login_at DESC;
```

This puts known login timestamps first and missing timestamps afterward.

PostgreSQL also supports:

```sql
ORDER BY last_login_at DESC NULLS LAST;
```

Prefer native ordering syntax when it clearly expresses the requirement.

## NULL and GROUP BY

`NULL` values are grouped together by `GROUP BY`.

For example:

```sql
SELECT
    region,
    COUNT(*) AS customer_count
FROM customers
GROUP BY region;
```

Rows where:

```text
region = NULL
```

belong to the same `NULL` group.

A `CASE` can expose that group as an explicit label:

```sql
SELECT
    CASE
        WHEN region IS NULL THEN 'unknown'
        ELSE region
    END AS region,
    COUNT(*) AS customer_count
FROM customers
GROUP BY
    CASE
        WHEN region IS NULL THEN 'unknown'
        ELSE region
    END;
```

If supported by the database and appropriate for the query, aliases, derived tables, or other query structures can reduce duplication.

## Backend API Implications

The database representation of `NULL` often affects the API contract.

Suppose PostgreSQL contains:

```text
last_login_at = NULL
```

A REST API might serialize this as:

```json
{
  "last_login_at": null
}
```

or derive a state:

```json
{
  "last_login_at": null,
  "login_state": "never_logged_in"
}
```

Do not silently transform `NULL` into a string such as:

```json
{
  "last_login_at": "N/A"
}
```

unless that is explicitly part of the API contract.

For Python applications, preserve the distinction between:

```python
None
```

and meaningful values when mapping database results into application models.

The same principle applies to Django ORM and FastAPI response models.

## Production Design Rule

A useful boundary is:

```text
Database NULL
      ↓
Domain interpretation
      ↓
API representation
```

Do not assume that every `NULL` should be converted at the SQL layer.

For example:

```sql
SELECT
    CASE
        WHEN phone_number IS NULL THEN 'missing'
        ELSE 'available'
    END AS phone_state
FROM customers;
```

may be appropriate if `phone_state` is a reusable database-level classification.

But if the API needs to distinguish several states, converting `NULL` too early may discard information that the application needs.

Preserve information until the layer responsible for the business decision can safely interpret it.

## Performance Considerations

Basic `NULL` checks such as:

```sql
column IS NULL
```

are generally inexpensive, but performance depends on:

- Data distribution
- Index design
- Database engine
- Query structure
- Cardinality
- Whether the expression is used for filtering, joining, grouping, or sorting

For example:

```sql
WHERE deleted_at IS NULL
```

is a common pattern for soft deletes.

If this predicate is executed frequently on a large table, index strategy matters.

PostgreSQL can use a partial index:

```sql
CREATE INDEX idx_orders_active
ON orders (tenant_id, created_at)
WHERE deleted_at IS NULL;
```

This can be effective when most application queries target active rows and the predicate is stable.

Always validate with realistic data and:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

rather than assuming an index will improve every workload.

## Production Pitfalls

### Treating NULL as Zero

Avoid:

```sql
CASE
    WHEN amount IS NULL THEN 0
    ELSE amount
END
```

unless `NULL` genuinely means zero.

For financial or accounting data, this distinction can affect reporting and reconciliation.

### Treating NULL as FALSE

Avoid:

```sql
CASE
    WHEN is_active = TRUE THEN 'active'
    ELSE 'inactive'
END
```

if `NULL` means unknown.

Use explicit classification:

```sql
CASE
    WHEN is_active IS TRUE THEN 'active'
    WHEN is_active IS FALSE THEN 'inactive'
    ELSE 'unknown'
END
```

### Treating NULL as an Empty String

Avoid:

```sql
COALESCE(name, '')
```

when the distinction between missing and empty is meaningful.

### Using `= NULL`

Never use:

```sql
column = NULL
```

to test for `NULL`.

Use:

```sql
column IS NULL
```

### Accidentally Hiding Data Quality Problems

This:

```sql
COALESCE(status, 'active')
```

can make missing data appear valid.

If `NULL` indicates a data integrity problem, silently replacing it may hide an operational issue.

Consider exposing unexpected `NULL`s through validation, monitoring, or data-quality checks.

## Testing NULL-Heavy Logic

For any `CASE` involving nullable columns, test at least:

| Scenario | Example |
| --- | --- |
| Expected value | `amount = 500` |
| Boundary value | `amount = 1000` |
| Below boundary | `amount = 999` |
| `NULL` | `amount = NULL` |
| Unexpected value | Invalid or newly introduced status |
| Multiple matching conditions | Overlapping predicates |

A production test suite should verify not only the normal path but also the semantic distinction between:

```text
NULL
0
FALSE
''
```

when those states are possible.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| Does `column = NULL` detect NULL? | No; use `IS NULL` |
| What does `NULL > 10` return? | `UNKNOWN` |
| Does `WHEN UNKNOWN` match? | No; `WHEN` requires `TRUE` |
| What happens without `ELSE`? | An unmatched `CASE` returns `NULL` |
| Is `NULL` the same as zero? | No |
| Is `NULL` the same as an empty string? | No |
| Why explicitly test `NULL` before another condition? | To preserve a distinct business state instead of allowing it to fall into `ELSE` |
| What does `COUNT(column)` do with NULL? | It ignores `NULL` values |
| What does `COUNT(*)` do with NULL? | It counts rows regardless of column values |
| Should every NULL be converted with `COALESCE`? | No; only when the fallback value matches the domain semantics |
| Why can NULL handling affect APIs? | SQL `NULL` often maps to application-level `None`/`null`, and transforming it prematurely can change the API's meaning |

## Key Takeaways

- `NULL` is not an ordinary value; comparisons involving it can produce `UNKNOWN`, and `CASE` selects a branch only when its condition is `TRUE`.
- Use `IS NULL` and `IS NOT NULL` for explicit `NULL` detection; never use `= NULL` or `<> NULL`.
- Do not automatically interpret `NULL` as zero, false, empty, or a valid default; preserve domain meaning.
- Explicitly classify meaningful `NULL` states when required, especially in billing, authorization, lifecycle, reporting, and API data.
- Validate nullable `CASE` expressions with boundary, `NULL`, unexpected-state, aggregate, and production-scale performance tests.