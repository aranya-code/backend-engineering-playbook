# 09- COALESCE

## Overview

`COALESCE()` is a SQL expression used to return the first non-`NULL` value from a list of expressions.

It is primarily useful for handling optional data at query boundaries: presenting defaults, normalizing nullable values, building derived fields, and making aggregate results usable by application code.

The basic form is:

```sql
COALESCE(value1, value2, value3)
```

SQL evaluates the arguments from left to right and returns the first value that is not `NULL`.

```sql
SELECT COALESCE(NULL, NULL, 'fallback');
```

Result:

```text
fallback
```

`COALESCE()` is especially important when working with:

- Nullable columns.
- `LEFT JOIN` results.
- Aggregates such as `SUM()` and `AVG()`.
- API response projections.
- Reporting queries.
- Optional configuration values.
- Default display values.

A senior engineer should also understand when **not** to use it. `COALESCE()` can change business semantics, hide data-quality problems, affect query performance, and interact with indexes and data types.

## Basic Syntax

```sql
COALESCE(expression_1, expression_2, ..., expression_n)
```

The first non-`NULL` expression is returned.

```sql
SELECT
    COALESCE(NULL, 10, 20) AS result;
```

Result:

```text
10
```

If every expression is `NULL`, the result is `NULL`:

```sql
SELECT
    COALESCE(NULL, NULL) AS result;
```

Result:

```text
NULL
```

### Evaluation model

Conceptually:

```text
expression 1
     │
     ├── non-NULL ──> return it
     │
     └── NULL
          │
          ▼
expression 2
     │
     ├── non-NULL ──> return it
     │
     └── NULL
          │
          ▼
       continue
```

`COALESCE()` is therefore a convenient SQL representation of fallback logic.

## Why COALESCE Exists

SQL uses `NULL` to represent missing, unknown, or inapplicable values. Application code, however, often needs a concrete value for presentation or computation.

For example:

```text
discount = NULL
```

may need to appear in an API as:

```json
{
  "discount": 0
}
```

The database can perform that transformation:

```sql
SELECT
    COALESCE(discount, 0) AS discount
FROM orders;
```

This keeps the query result aligned with the contract expected by the application.

However, replacing `NULL` with a value should be a deliberate semantic decision.

`NULL` and `0` do not inherently mean the same thing:

```text
NULL → unknown / absent / not applicable
0    → known value of zero
```

Use `COALESCE()` only when the fallback accurately represents the business meaning.

## COALESCE With Columns

Suppose:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    display_name TEXT,
    nickname TEXT
);
```

A query can prefer `nickname`, then `display_name`, then a fallback:

```sql
SELECT
    id,
    COALESCE(nickname, display_name, 'Anonymous') AS name
FROM users;
```

The precedence is:

```text
nickname
   ↓ if NULL
display_name
   ↓ if NULL
'Anonymous'
```

This is useful for projection logic where several sources can provide the same logical value.

## COALESCE With LEFT JOIN

`COALESCE()` is particularly common after `LEFT JOIN`.

Consider:

```sql
SELECT
    c.id,
    c.email,
    o.amount
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

A customer without an order receives:

```text
o.amount = NULL
```

If the application wants an explicit zero:

```sql
SELECT
    c.id,
    c.email,
    COALESCE(o.amount, 0) AS order_amount
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

The important distinction is:

```text
No matching order
        ↓
LEFT JOIN produces NULL
        ↓
COALESCE(..., 0)
        ↓
Result contains 0
```

The original relationship remains absent. `COALESCE()` only changes the value exposed by the query.

## COALESCE With Aggregates

Aggregate functions have important `NULL` behavior.

For example:

```sql
SELECT SUM(amount)
FROM orders
WHERE customer_id = 999;
```

If no qualifying rows exist, `SUM()` returns `NULL`, not `0`.

When the application needs zero:

```sql
SELECT
    COALESCE(SUM(amount), 0) AS total_amount
FROM orders
WHERE customer_id = 999;
```

This pattern is common in financial and reporting queries.

### COUNT is different

`COUNT()` returns zero when no rows qualify:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = 999;
```

Therefore:

```sql
COUNT(*)        -- 0
SUM(amount)     -- NULL
AVG(amount)     -- NULL
MIN(amount)     -- NULL
MAX(amount)     -- NULL
```

The exact result also depends on whether qualifying rows exist and whether the aggregated values themselves are `NULL`.

## COALESCE With GROUP BY

Suppose customer totals are required:

```sql
SELECT
    c.id,
    COALESCE(SUM(o.amount), 0) AS total_spent
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Every customer remains in the result because of the `LEFT JOIN`.

Customers with qualifying order amounts receive their total. Customers without orders receive zero.

This is a common backend reporting pattern.

## COALESCE and NULL Values Inside Aggregates

Consider:

```text
amount
------
100
NULL
50
```

Then:

```sql
SELECT SUM(amount)
FROM payments;
```

returns:

```text
150
```

`SUM()` ignores `NULL` input values.

Compare that with a dataset containing no non-`NULL` values:

```text
amount
------
NULL
NULL
```

Then:

```sql
SUM(amount)
```

returns:

```text
NULL
```

Using:

```sql
COALESCE(SUM(amount), 0)
```

converts that final `NULL` to zero.

This is different from:

```sql
SUM(COALESCE(amount, 0))
```

Both can produce the same numeric result in many cases, but they express different semantics.

### Prefer the outer form when the intent is "default the aggregate"

```sql
COALESCE(SUM(amount), 0)
```

This means:

> Calculate the aggregate, then use zero if the aggregate has no value.

It is generally clearer than introducing a transformation into every input row.

## COALESCE Before vs After Aggregation

Compare:

```sql
SELECT COALESCE(SUM(amount), 0)
FROM payments;
```

with:

```sql
SELECT SUM(COALESCE(amount, 0))
FROM payments;
```

The first is usually the better expression when the requirement is to default a missing aggregate result.

The second explicitly defines each `NULL` amount as zero before aggregation.

That distinction matters when business semantics distinguish:

```text
missing amount
```

from:

```text
known amount of zero
```

The query should communicate that distinction.

## COALESCE With Arithmetic

Arithmetic involving `NULL` normally produces `NULL`.

```sql
SELECT
    price + discount
FROM products;
```

If:

```text
price = 100
discount = NULL
```

the result is:

```text
NULL
```

If the domain defines a missing discount as zero:

```sql
SELECT
    price - COALESCE(discount, 0) AS final_price
FROM products;
```

Now:

```text
100 - NULL → NULL
100 - 0    → 100
```

This is useful for optional numeric fields, but only when the default is semantically correct.

## COALESCE With String Concatenation

String concatenation can also be affected by `NULL`, depending on the database.

For portable intent, normalize optional components explicitly:

```sql
SELECT
    CONCAT(
        COALESCE(first_name, ''),
        ' ',
        COALESCE(last_name, '')
    ) AS full_name
FROM users;
```

Be careful with this approach because:

```text
NULL
```

may mean that a name is unknown, while:

```text
''
```

means an explicitly empty string.

If those states matter to the application, blindly converting `NULL` to an empty string loses information.

## COALESCE and Empty Strings

`COALESCE()` only checks for `NULL`.

It does **not** consider an empty string to be `NULL`.

For example:

```sql
SELECT COALESCE('', 'fallback');
```

returns:

```text
''
```

because the empty string is not `NULL`.

Likewise, whitespace is not `NULL`:

```sql
SELECT COALESCE('   ', 'fallback');
```

returns the whitespace value.

If the requirement is:

> Use a fallback when the value is NULL or an empty string

you need additional logic:

```sql
SELECT
    CASE
        WHEN value IS NULL OR value = '' THEN 'fallback'
        ELSE value
    END
FROM table_name;
```

In PostgreSQL, whitespace can be handled explicitly:

```sql
SELECT
    CASE
        WHEN value IS NULL OR BTRIM(value) = '' THEN 'fallback'
        ELSE value
    END
FROM table_name;
```

Do not use `COALESCE()` as a general-purpose "missing string" detector.

## COALESCE in JOIN Conditions

`COALESCE()` can technically be used in join predicates:

```sql
SELECT *
FROM users AS u
JOIN accounts AS a
    ON COALESCE(u.external_id, '') = COALESCE(a.external_id, '');
```

But this changes the semantics significantly.

Two `NULL` values become:

```text
NULL → ''
NULL → ''
```

and therefore match.

If `NULL` means "unknown external ID", this can incorrectly associate unrelated rows.

It can also make index-based access less straightforward because the database must evaluate an expression around the indexed column.

When null-to-null matching is intentionally required, PostgreSQL provides a more explicit expression:

```sql
ON u.external_id IS NOT DISTINCT FROM a.external_id
```

This communicates the intended NULL semantics more directly.

## COALESCE and Indexes

Using `COALESCE()` in a `WHERE` predicate can affect index usage.

For example:

```sql
SELECT *
FROM users
WHERE COALESCE(status, 'active') = 'active';
```

The database may need to evaluate the expression for many rows instead of using a straightforward index lookup on:

```sql
status
```

A semantically equivalent predicate may be easier for the optimizer:

```sql
SELECT *
FROM users
WHERE status = 'active'
   OR status IS NULL;
```

Whether this produces a better plan depends on the database, indexes, statistics, and data distribution.

For large production tables, verify rather than assume:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users
WHERE status = 'active'
   OR status IS NULL;
```

### Functional indexes

If an expression is genuinely part of a frequent query pattern, a functional or expression index can sometimes be appropriate.

For PostgreSQL:

```sql
CREATE INDEX idx_users_effective_status
    ON users (COALESCE(status, 'active'));
```

Then the corresponding expression can potentially use that index:

```sql
SELECT *
FROM users
WHERE COALESCE(status, 'active') = 'active';
```

Do not add expression indexes automatically. They increase storage and write overhead and should be justified by actual workload patterns.

## COALESCE and Data Types

The arguments to `COALESCE()` need compatible types.

For example:

```sql
SELECT COALESCE(NULL, 100);
```

works naturally as a numeric expression.

But mixing unrelated types can cause type-resolution problems or implicit conversions:

```sql
SELECT COALESCE(amount, 'unknown')
FROM payments;
```

If `amount` is numeric, the database may reject the expression because a numeric value and text literal cannot be reconciled as the required result type.

Prefer explicit, type-consistent fallbacks:

```sql
SELECT COALESCE(amount, 0::numeric)
FROM payments;
```

The exact casting syntax is database-specific.

## COALESCE Evaluation and Side Effects

`COALESCE()` is defined in terms of selecting the first non-`NULL` expression, and PostgreSQL generally avoids evaluating unnecessary later arguments.

For example:

```sql
SELECT COALESCE('value', expensive_expression);
```

does not need the second expression to determine the result.

However, do not use `COALESCE()` as a mechanism for controlling arbitrary side effects or relying on evaluation order of expressions with volatile behavior. SQL optimizers have significant freedom in expression evaluation.

For normal data expressions, the practical rule is simple:

> Put the preferred value first and fallbacks afterward.

## COALESCE in Backend APIs

A common architecture is:

```text
Database
   │
   │ SQL projection
   ▼
COALESCE(nullable_value, default)
   │
   ▼
Repository / ORM
   │
   ▼
Service layer
   │
   ▼
REST / gRPC response
```

For example:

```sql
SELECT
    id,
    COALESCE(display_name, 'Anonymous') AS display_name,
    COALESCE(login_count, 0) AS login_count
FROM users;
```

This can simplify application code because the repository returns values that already satisfy the projection's contract.

However, do not use SQL defaults to conceal important domain states.

For example, replacing:

```text
last_payment_at = NULL
```

with:

```text
last_payment_at = '1970-01-01'
```

would be a poor design because the fallback is not semantically equivalent to the missing state.

For API contracts, prefer explicit nullable fields when the distinction matters.

## COALESCE in Django

Django ORM exposes SQL `COALESCE()` through `Coalesce`.

```python
from django.db.models import Value
from django.db.models.functions import Coalesce

users = User.objects.annotate(
    effective_name=Coalesce(
        "nickname",
        "display_name",
        Value("Anonymous"),
    )
)
```

For numeric values:

```python
from django.db.models import DecimalField, Value
from django.db.models.functions import Coalesce

orders = Order.objects.annotate(
    effective_discount=Coalesce(
        "discount",
        Value(0),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )
)
```

Be explicit about types when ORM expressions involve literals and nullable fields.

The SQL generated by the ORM should still be inspected when the query is performance-sensitive.

## COALESCE in PostgreSQL

PostgreSQL supports `COALESCE()` directly:

```sql
SELECT
    COALESCE(phone_number, email, 'No contact information') AS contact
FROM users;
```

PostgreSQL also provides related conditional expressions such as:

- `NULLIF()`
- `CASE`
- `GREATEST()`
- `LEAST()`

These solve different problems and should not be treated as interchangeable.

## COALESCE vs CASE

These are often equivalent:

```sql
COALESCE(preferred_name, display_name, 'Anonymous')
```

and:

```sql
CASE
    WHEN preferred_name IS NOT NULL THEN preferred_name
    WHEN display_name IS NOT NULL THEN display_name
    ELSE 'Anonymous'
END
```

Use `COALESCE()` when the requirement is simply:

> Return the first non-NULL value.

Use `CASE` when the decision depends on more complex conditions.

For example:

```sql
CASE
    WHEN status = 'cancelled' THEN 'Cancelled'
    WHEN deleted_at IS NOT NULL THEN 'Deleted'
    ELSE COALESCE(display_name, 'Anonymous')
END
```

`CASE` is more appropriate because the logic is not merely a NULL fallback chain.

## COALESCE vs NULLIF

`NULLIF()` performs the opposite type of transformation:

```sql
NULLIF(value, '')
```

turns an empty string into `NULL`.

For example:

```sql
SELECT NULLIF('', '');
```

returns:

```text
NULL
```

Combining the two is useful when input data uses empty strings to represent missing values:

```sql
SELECT
    COALESCE(NULLIF(email, ''), 'unknown@example.com')
FROM users;
```

The flow is:

```text
empty string
     ↓
NULLIF()
     ↓
NULL
     ↓
COALESCE()
     ↓
fallback
```

This should be used deliberately because it normalizes two distinct representations into one.

## Practical Reporting Example

Suppose an order dashboard needs:

- every customer;
- total number of orders;
- total revenue;
- zero instead of missing totals.

A safe query is:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.amount), 0) AS total_revenue
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email;
```

The important details are:

```text
LEFT JOIN
    → keeps customers with no orders

COUNT(o.id)
    → returns 0 for customers without orders

COALESCE(SUM(o.amount), 0)
    → converts a missing aggregate result into 0
```

This is preferable to using `COUNT(*)`, which would count the preserved customer row.

## Common Production Patterns

| Requirement | Recommended expression |
|---|---|
| First available name | `COALESCE(nickname, display_name, 'Anonymous')` |
| Default missing numeric aggregate | `COALESCE(SUM(amount), 0)` |
| Optional numeric value defaults to zero | `COALESCE(discount, 0)` |
| Optional timestamp remains semantically nullable | Do not force a synthetic timestamp |
| Empty string should remain distinct | Use `COALESCE()` alone |
| Empty string should mean missing | `NULLIF(value, '')` then `COALESCE()` |
| Complex conditional fallback | `CASE` |
| Null-safe equality in PostgreSQL | `IS NOT DISTINCT FROM` |

## Common Mistakes and Pitfalls

| Mistake | Why it is a problem | Better approach |
|---|---|---|
| Assuming `COALESCE('', 'fallback')` returns the fallback | Empty string is not `NULL` | Handle empty strings explicitly |
| Replacing every `NULL` with `0` | Can destroy business semantics | Use zero only when it represents the missing state correctly |
| Using `COALESCE()` in every join | Can alter matching behavior | Define NULL semantics before modifying joins |
| Wrapping indexed columns in `COALESCE()` | May make index access less efficient | Compare alternative predicates and inspect the query plan |
| Using `COUNT(*)` after `LEFT JOIN` | Counts preserved parent rows | Use `COUNT(child.id)` when counting children |
| Assuming `SUM()` returns zero for no rows | Most SQL databases return `NULL` | Use `COALESCE(SUM(...), 0)` |
| Mixing incompatible data types | Can cause type errors or unwanted casts | Use compatible types and explicit casts where needed |
| Using synthetic dates as fallbacks | Can make "unknown" appear as real data | Keep timestamps nullable when absence matters |
| Using `COALESCE()` to hide bad data | Masks data-quality issues | Validate and monitor upstream data |
| Adding an expression index without evidence | Increases storage and write cost | Add indexes based on measured workload |

## Performance and Operational Considerations

`COALESCE()` itself is usually inexpensive. The production concern is where and how it is used.

### Prefer projection-time normalization

This is often straightforward:

```sql
SELECT
    COALESCE(SUM(amount), 0) AS total
FROM orders;
```

The database computes the aggregate and normalizes the final result.

### Be careful in predicates

This pattern:

```sql
WHERE COALESCE(status, 'active') = 'active'
```

may have different performance characteristics from:

```sql
WHERE status = 'active'
   OR status IS NULL
```

Test with realistic data:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE status = 'active'
   OR status IS NULL;
```

### Monitor query plans

For high-volume endpoints, watch:

- execution time;
- rows scanned;
- index usage;
- buffer reads;
- CPU;
- temporary memory;
- result cardinality.

`COALESCE()` should not be blamed automatically for a slow query. The surrounding predicate, join strategy, cardinality, and indexing strategy usually matter more.

## Security Considerations

`COALESCE()` does not provide SQL injection protection.

Values supplied by users should still be passed through parameterized queries:

```python
cursor.execute(
    """
    SELECT
        id,
        COALESCE(display_name, %s) AS display_name
    FROM users
    WHERE id = %s
    """,
    ["Anonymous", user_id],
)
```

Do not construct SQL using string interpolation:

```python
# Avoid
query = f"""
SELECT COALESCE(display_name, '{fallback}')
FROM users
WHERE id = {user_id}
"""
```

Use parameterized queries or the database abstraction provided by the framework.

## Senior-Level Design Guidance

The key question is not:

> "Can I use `COALESCE()` here?"

The better question is:

> "What does NULL mean in this domain, and is the fallback semantically equivalent?"

For example:

```text
discount = NULL
```

could mean:

1. no discount was applied;
2. discount has not been calculated;
3. discount is not applicable;
4. source data is missing.

Only the first interpretation may justify:

```sql
COALESCE(discount, 0)
```

If the distinction matters operationally, preserve `NULL` and expose that state explicitly.

Similarly:

```sql
COALESCE(last_login_at, created_at)
```

is not merely formatting. It asserts:

> If the user has never logged in, treat account creation time as their effective last-login time.

That may be useful for a particular report, but it should not silently become domain truth.

## Interview Traps

### What does `COALESCE()` return?

The first non-`NULL` expression.

```sql
COALESCE(NULL, NULL, 42, 100)
```

returns:

```text
42
```

### What happens if every argument is NULL?

The result is:

```text
NULL
```

### Does `COALESCE()` treat an empty string as NULL?

No.

```sql
COALESCE('', 'fallback')
```

returns the empty string.

### Why use `COALESCE(SUM(amount), 0)`?

Because `SUM()` can return `NULL` when there are no non-`NULL` values, while the application may require an explicit numeric zero.

### What is the difference between these?

```sql
COALESCE(SUM(amount), 0)
```

and:

```sql
SUM(COALESCE(amount, 0))
```

The first defaults the final aggregate result. The second converts each `NULL` input into zero before aggregation. They often produce the same numeric result, but they express different semantics.

### Can COALESCE affect indexes?

Yes. Expressions such as:

```sql
WHERE COALESCE(status, 'active') = 'active'
```

can make a normal index on `status` less directly usable. The actual query plan should be inspected.

### Is COALESCE the same as CASE?

Not exactly.

`COALESCE()` is specialized for first-non-`NULL` fallback logic. `CASE` supports arbitrary conditional logic.

### Should COALESCE be used to make NULL foreign keys match?

Usually no.

This:

```sql
COALESCE(a.customer_id, 0) = COALESCE(b.customer_id, 0)
```

can make unrelated missing relationships match. Null-safe matching should only be introduced when explicitly required by the data model.

## Key Takeaways

- **`COALESCE()` returns the first non-`NULL` expression and is primarily useful for explicit fallback and projection logic.**
- **`NULL` should not automatically be converted to `0`, `''`, or a synthetic value; the fallback must match the domain semantics.**
- **`COALESCE(SUM(...), 0)` is a common production pattern, while `COUNT(column)` is preferable to `COUNT(*)` for counting children after a `LEFT JOIN`.**
- **Using `COALESCE()` in predicates or joins can change semantics and affect index usage, so validate both correctness and execution plans.**
- **Treat `COALESCE()` as a semantic transformation, not merely a NULL-cleanup function.**