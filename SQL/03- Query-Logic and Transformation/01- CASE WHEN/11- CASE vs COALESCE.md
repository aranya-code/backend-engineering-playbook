# 11- CASE vs COALESCE

## Overview

`CASE` and `COALESCE` can both participate in conditional value selection, but they solve different problems.

`CASE` expresses explicit conditional logic:

```sql
CASE
    WHEN condition THEN value
    ELSE fallback
END
```

`COALESCE` selects the first non-`NULL` expression:

```sql
COALESCE(value_1, value_2, value_3)
```

The practical distinction is:

| Requirement | Prefer |
| --- | --- |
| Choose a value based on a condition | `CASE` |
| Replace `NULL` with a fallback | `COALESCE` |
| Select the first available non-`NULL` value | `COALESCE` |
| Evaluate ranges or complex predicates | `CASE` |
| Map specific states to values | `CASE` |
| Normalize optional database fields | `COALESCE` |
| Express complex conditional business logic | `CASE` |

Using the simpler construct makes SQL easier to review, maintain, and optimize.

## What COALESCE Does

`COALESCE` returns the first expression that is not `NULL`.

```sql
SELECT COALESCE(display_name, username, 'Anonymous') AS name
FROM users;
```

Evaluation conceptually proceeds as:

```text
display_name
    ↓
non-NULL? ── yes → return display_name
    │
    no
    ↓
username
    ↓
non-NULL? ── yes → return username
    │
    no
    ↓
'Anonymous'
```

For example:

| display_name | username | Result |
| --- | --- | --- |
| `Alice` | `alice01` | `Alice` |
| `NULL` | `alice01` | `alice01` |
| `NULL` | `NULL` | `Anonymous` |

This makes `COALESCE` particularly useful for nullable columns and fallback values.

## CASE for the Same Problem

The equivalent logic can be written with `CASE`:

```sql
SELECT
    CASE
        WHEN display_name IS NOT NULL THEN display_name
        WHEN username IS NOT NULL THEN username
        ELSE 'Anonymous'
    END AS name
FROM users;
```

This is valid but unnecessarily verbose when the only requirement is selecting the first non-`NULL` value.

Prefer:

```sql
COALESCE(display_name, username, 'Anonymous')
```

The intent is immediately visible.

## COALESCE as a Specialized Conditional Tool

A useful mental model is:

```text
COALESCE
    ↓
"Give me the first usable non-NULL value."

CASE
    ↓
"Give me a value according to these conditions."
```

`COALESCE` is therefore not a general replacement for `CASE`.

For example, this requirement cannot be represented by simple `COALESCE`:

```sql
CASE
    WHEN account_status = 'suspended' THEN 'blocked'
    WHEN failed_attempts >= 5 THEN 'locked'
    WHEN is_active = TRUE THEN 'active'
    ELSE 'inactive'
END
```

The conditions are not merely checking whether values are `NULL`.

## CASE Versus COALESCE for Defaults

Suppose an API should expose zero when an optional balance is `NULL`.

Use:

```sql
SELECT COALESCE(balance, 0) AS balance
FROM accounts;
```

Instead of:

```sql
SELECT
    CASE
        WHEN balance IS NULL THEN 0
        ELSE balance
    END AS balance
FROM accounts;
```

`COALESCE` communicates the intent more directly.

This pattern is common when preparing database results for REST or gRPC responses where the application expects a concrete value.

## Multiple Fallbacks

`COALESCE` is especially useful when there are several possible sources:

```sql
SELECT
    COALESCE(
        shipping_address,
        billing_address,
        default_address
    ) AS effective_address
FROM customers;
```

The database selects the first non-`NULL` address.

A `CASE` implementation would require explicit checks:

```sql
SELECT
    CASE
        WHEN shipping_address IS NOT NULL THEN shipping_address
        WHEN billing_address IS NOT NULL THEN billing_address
        ELSE default_address
    END AS effective_address
FROM customers;
```

Again, `COALESCE` better communicates the underlying rule.

## CASE and COALESCE Together

The constructs are often complementary rather than competing.

For example:

```sql
SELECT
    CASE
        WHEN status = 'cancelled'
            THEN 'inactive'
        ELSE COALESCE(display_status, 'unknown')
    END AS effective_status
FROM orders;
```

Here:

- `CASE` handles the business condition.
- `COALESCE` handles nullable data.

This separation keeps each construct focused on the problem it solves.

## Conditional Transformation with a NULL Fallback

Consider an API that should display a payment method label.

```sql
SELECT
    CASE
        WHEN payment_method = 'card'
            THEN COALESCE(card_brand, 'Card')
        WHEN payment_method = 'bank_transfer'
            THEN 'Bank Transfer'
        ELSE 'Other'
    END AS payment_method_label
FROM payments;
```

The outer `CASE` performs classification while `COALESCE` handles missing card-brand information.

This is a common production pattern when database state and presentation fallback logic must be combined.

## NULL Semantics

`CASE` and `COALESCE` both require careful reasoning about `NULL`.

Consider:

```sql
SELECT
    CASE
        WHEN discount > 0 THEN 'discounted'
        ELSE 'full_price'
    END
FROM orders;
```

If `discount` is `NULL`, the comparison:

```sql
discount > 0
```

evaluates to `UNKNOWN`, so the `ELSE` branch is selected.

By contrast:

```sql
SELECT COALESCE(discount, 0)
FROM orders;
```

explicitly converts `NULL` into `0`.

These are not necessarily equivalent domain decisions.

If `NULL` means "discount was not calculated", converting it to zero may hide an important state.

## COALESCE Does Not Mean Zero

A common mistake is treating `COALESCE` as a numeric defaulting function.

For example:

```sql
COALESCE(discount, 0)
```

means:

> If `discount` is `NULL`, use `0`.

It does **not** mean:

> If `discount` is invalid, negative, or otherwise undesirable, use `0`.

If the business requirement is conditional:

```sql
CASE
    WHEN discount IS NULL OR discount < 0 THEN 0
    ELSE discount
END
```

is more appropriate.

## COALESCE and Empty Strings

`COALESCE` only handles `NULL`.

It does not treat an empty string as `NULL` in databases where these are distinct values.

For example:

```sql
COALESCE(display_name, 'Anonymous')
```

does not replace:

```text
''
```

with:

```text
Anonymous
```

If both `NULL` and empty strings should be treated as missing, the logic must express that explicitly.

For PostgreSQL:

```sql
CASE
    WHEN NULLIF(TRIM(display_name), '') IS NULL
        THEN 'Anonymous'
    ELSE display_name
END
```

or:

```sql
COALESCE(NULLIF(TRIM(display_name), ''), 'Anonymous')
```

The second form is concise when the requirement is specifically:

```text
trimmed value → use it if non-empty
otherwise → fallback
```

## Data Type Considerations

`CASE` and `COALESCE` must resolve their possible results to compatible types according to the SQL dialect's type-resolution rules.

For example:

```sql
COALESCE(quantity, 0)
```

is straightforward when `quantity` is numeric.

Be cautious when mixing types:

```sql
COALESCE(quantity, '0')
```

The exact behavior depends on the database's type coercion rules.

Prefer explicit, type-compatible values:

```sql
COALESCE(quantity, 0)
```

Similarly:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    ELSE 'disabled'
END
```

has consistent textual result types.

When a query becomes complicated, explicit casts can make intent unambiguous:

```sql
COALESCE(amount, 0::numeric)
```

PostgreSQL-specific casts should only be used when PostgreSQL is the intended database target.

## Evaluation and Side Effects

`COALESCE` is conceptually similar to a conditional expression because later arguments are only needed when earlier arguments are `NULL`.

However, do not build application logic around assumptions about evaluation behavior for arbitrary expressions across database engines.

Avoid unnecessary expensive expressions:

```sql
COALESCE(
    cached_value,
    expensive_function(...)
)
```

when the expensive computation can be avoided through a better query design.

For ordinary column fallbacks, `COALESCE` is generally straightforward and efficient.

## CASE Versus COALESCE in Aggregation

Both can be useful around aggregates.

For example, an aggregate over no matching rows may produce `NULL`:

```sql
SELECT SUM(amount) AS total_amount
FROM orders
WHERE status = 'completed';
```

If the API contract requires zero instead:

```sql
SELECT COALESCE(
    SUM(amount),
    0
) AS total_amount
FROM orders
WHERE status = 'completed';
```

This is usually preferable to:

```sql
SELECT
    CASE
        WHEN SUM(amount) IS NULL THEN 0
        ELSE SUM(amount)
    END AS total_amount
FROM orders
WHERE status = 'completed';
```

`COALESCE` directly expresses the fallback requirement.

For conditional aggregation itself, however, `CASE` remains useful:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders;
```

The two constructs solve different layers of the problem:

```text
CASE
    ↓
decide which rows/values contribute

COALESCE
    ↓
provide a value when the final result is NULL
```

## Backend API Example

Suppose an endpoint returns customer billing information.

The database contains:

- `credit_limit`
- `current_balance`
- nullable `last_payment_amount`

A query can normalize the nullable payment amount:

```sql
SELECT
    customer_id,
    credit_limit,
    current_balance,
    COALESCE(last_payment_amount, 0) AS last_payment_amount,
    CASE
        WHEN current_balance > credit_limit THEN 'over_limit'
        WHEN current_balance > 0 THEN 'balance_due'
        ELSE 'clear'
    END AS billing_status
FROM customers;
```

This cleanly separates:

```text
COALESCE → missing value normalization
CASE     → business classification
```

The FastAPI or Django layer can then serialize the already-derived representation without duplicating the SQL logic.

## Django ORM

Django supports both concepts.

`Case` and `When` express conditional logic:

```python
from django.db.models import Case, CharField, Value, When

customers = Customer.objects.annotate(
    billing_status=Case(
        When(current_balance__gt=F("credit_limit"), then=Value("over_limit")),
        When(current_balance__gt=0, then=Value("balance_due")),
        default=Value("clear"),
        output_field=CharField(),
    )
)
```

`Coalesce` expresses nullable fallback logic:

```python
from django.db.models.functions import Coalesce

customers = Customer.objects.annotate(
    effective_balance=Coalesce("current_balance", Value(0))
)
```

Use the ORM construct that matches the semantics instead of forcing everything through conditional branches.

## Performance Considerations

For simple column fallback:

```sql
COALESCE(nullable_column, default_value)
```

is generally not a performance concern.

Performance becomes more important when `CASE` or `COALESCE` appears in:

- Large scans.
- Join predicates.
- Filtering expressions.
- Sort keys.
- Grouping expressions.
- Complex nested expressions.

For example:

```sql
WHERE COALESCE(status, 'unknown') = 'active'
```

may be less index-friendly than:

```sql
WHERE status = 'active'
```

because the column is wrapped in an expression.

If the intended semantics are:

```text
only rows whose status is exactly active
```

use the direct predicate.

If the expression is required by the domain, measure the actual query plan.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE COALESCE(status, 'unknown') = 'active';
```

Do not assume that replacing `CASE` with `COALESCE`, or vice versa, automatically improves performance.

## Production Design Guidance

### Prefer COALESCE for NULL Fallbacks

Use:

```sql
COALESCE(phone_number, email)
```

when the requirement is simply:

> Use the phone number if present; otherwise use the email.

Avoid a verbose `CASE` for the same rule.

### Prefer CASE for Business Conditions

Use:

```sql
CASE
    WHEN balance > credit_limit THEN 'over_limit'
    WHEN balance > 0 THEN 'due'
    ELSE 'clear'
END
```

when the decision depends on business predicates.

### Preserve Meaningful NULLs

Do not normalize every `NULL` to an arbitrary default.

These values can have different meanings:

```text
NULL → unknown / not supplied
0    → known numeric zero
''   → known empty text
```

Changing `NULL` to a concrete value can alter downstream business behavior.

### Avoid Deep Nesting

This is difficult to maintain:

```sql
CASE
    WHEN ...
        THEN COALESCE(
            CASE
                WHEN ...
                    THEN ...
                ELSE ...
            END,
            CASE
                WHEN ...
                    THEN ...
                ELSE ...
            END
        )
    ELSE ...
END
```

If the expression becomes difficult to review, reconsider whether the logic belongs in one query, should be split into CTEs, or should be represented as relational data.

## Common Mistakes

### Using CASE for Simple NULL Fallbacks

Avoid:

```sql
CASE
    WHEN name IS NULL THEN 'Anonymous'
    ELSE name
END
```

Prefer:

```sql
COALESCE(name, 'Anonymous')
```

### Using COALESCE for Conditional Rules

Avoid trying to represent business conditions with:

```sql
COALESCE(...)
```

when the requirement depends on comparisons:

```sql
amount >= 1000
status = 'failed'
created_at < cutoff
```

Use `CASE`.

### Confusing NULL with False or Zero

This:

```sql
COALESCE(is_active, FALSE)
```

makes `NULL` behave as `FALSE`.

That may be appropriate for an API representation, but it is not necessarily correct for the underlying business meaning.

### Assuming Empty Strings Are NULL

`COALESCE` does not generally replace empty strings.

Handle empty values explicitly when the domain treats them as missing.

### Hiding Data Quality Problems

This:

```sql
COALESCE(status, 'active')
```

can make missing status values look valid.

A safer fallback may be:

```sql
COALESCE(status, 'unknown')
```

or explicit handling:

```sql
CASE
    WHEN status IS NULL THEN 'invalid'
    ...
END
```

The correct choice depends on whether missing data is expected or indicates a data-quality problem.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| What does `COALESCE` return? | The first non-`NULL` expression |
| Is `COALESCE` a replacement for `CASE`? | No; it is specialized for `NULL` fallback selection |
| When should `CASE` be preferred? | When selection depends on Boolean conditions, ranges, or business rules |
| When should `COALESCE` be preferred? | When selecting the first available non-`NULL` value |
| Does `COALESCE` convert empty strings to `NULL`? | No; empty strings and `NULL` are distinct in databases such as PostgreSQL |
| Can `CASE` and `COALESCE` be combined? | Yes; `CASE` can handle business conditions while `COALESCE` handles nullable values |
| Does `COALESCE(column, 0)` mean the column is zero? | No; it means `0` is returned when the column is `NULL` |
| Can wrapping a column in `COALESCE` affect index usage? | Yes; expression-based predicates can affect how an optimizer uses indexes |
| Can `COALESCE` replace conditional aggregation? | Not generally; `CASE` is used to conditionally determine which values contribute |
| Why is `COALESCE(SUM(...), 0)` common? | Aggregates such as `SUM` can return `NULL` when there are no input values, and the API may require an explicit zero |
| What is the key conceptual difference? | `CASE` asks which condition is true; `COALESCE` asks which expression is non-`NULL` first |

## Key Takeaways

- Use `COALESCE` for first-non-`NULL` fallback logic and `CASE` for explicit conditional business rules.
- `NULL`, zero, `FALSE`, and empty strings can represent different domain states; normalize them only when the API or business contract requires it.
- `CASE` and `COALESCE` are complementary and can be safely combined when each handles a distinct part of the transformation.
- Wrapping columns in conditional expressions can affect query plans and index usage, so optimize based on measured execution plans rather than syntax preferences.
- Prefer the simplest expression that accurately communicates the business rule: `COALESCE` for nullable fallbacks, `CASE` for conditional decisions.