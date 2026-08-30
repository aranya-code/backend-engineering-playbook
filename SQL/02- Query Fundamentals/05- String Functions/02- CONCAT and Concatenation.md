# 02- CONCAT and Concatenation

## Overview

String concatenation combines two or more values into a single string. It is commonly used to construct display values, identifiers, labels, export fields, log-oriented projections, and other derived text directly in SQL.

The two common approaches are:

- `CONCAT()` — explicit function-based concatenation.
- `||` — the SQL concatenation operator, supported by PostgreSQL and several other databases.

The important production concern is not simply how to join strings, but how **NULL values, data types, whitespace, indexing, portability, and data modeling** affect the resulting query.

## Basic Concatenation

Using PostgreSQL syntax:

```sql
SELECT
    first_name || ' ' || last_name AS full_name
FROM users;
```

For:

| `first_name` | `last_name` |
|---|---|
| `Alice` | `Johnson` |

the result is:

| `full_name` |
|---|
| `Alice Johnson` |

The expression:

```sql
first_name || ' ' || last_name
```

is evaluated from its component expressions and produces one text value.

### Using CONCAT

The equivalent function-based expression is:

```sql
SELECT
    CONCAT(first_name, ' ', last_name) AS full_name
FROM users;
```

`CONCAT()` is often easier to read when several values are being combined.

## CONCAT vs `||`

The exact semantics depend on the database engine, especially around `NULL`.

| Approach | PostgreSQL | Typical Use | NULL Behavior |
|---|---|---|---|
| `CONCAT(a, b)` | Supported | Explicit function-based concatenation | Treats NULL arguments as empty strings |
| `a \|\| b` | Supported | Native SQL operator | NULL generally propagates |
| `CONCAT_WS(sep, ...)` | Supported | Concatenate with separator | Skips NULL arguments |
| `CONCAT()` portability | Varies | Cross-database SQL | Verify target database semantics |

For PostgreSQL:

```sql
SELECT CONCAT('Alice', ' ', NULL);
```

produces:

```text
Alice
```

whereas:

```sql
SELECT 'Alice' || ' ' || NULL;
```

produces:

```text
NULL
```

This distinction is one of the most important interview and production considerations for concatenation.

## Why NULL Behavior Matters

Consider a user table:

```text
first_name = Alice
middle_name = NULL
last_name = Johnson
```

This expression:

```sql
SELECT first_name || ' ' || middle_name || ' ' || last_name
FROM users;
```

can produce:

```text
NULL
```

because NULL propagates through the concatenation expression.

Using `CONCAT()`:

```sql
SELECT CONCAT(first_name, ' ', middle_name, ' ', last_name)
FROM users;
```

produces a value without treating the NULL argument as fatal.

However, this does **not** necessarily produce the desired formatting:

```text
Alice  Johnson
```

There are two spaces where the optional middle name was absent.

For optional fields, `CONCAT_WS()` is often a better PostgreSQL approach.

## CONCAT_WS

`CONCAT_WS()` means concatenate with separator.

```sql
SELECT
    CONCAT_WS(' ', first_name, middle_name, last_name) AS full_name
FROM users;
```

For:

```text
first_name  = Alice
middle_name = NULL
last_name   = Johnson
```

the result is:

```text
Alice Johnson
```

The separator is inserted between non-NULL arguments rather than producing an unnecessary separator for the missing value.

### Practical Example

For an address:

```sql
SELECT
    CONCAT_WS(', ', city, state, country) AS location
FROM customers;
```

This is preferable to manually inserting separators when some components are optional.

## CONCAT with Different Data Types

Concatenation frequently combines strings with numbers, dates, or identifiers.

For example:

```sql
SELECT
    CONCAT('Order-', order_id) AS order_reference
FROM orders;
```

A numeric `order_id` can be converted as required by the database's function/operator rules.

With `||`, explicit casting may sometimes be necessary:

```sql
SELECT
    'Order-' || order_id::text AS order_reference
FROM orders;
```

Database-specific casting syntax varies.

Do not assume that concatenation automatically provides the exact formatting required for dates, decimals, timestamps, or monetary values.

## Formatting Numeric and Temporal Values

Concatenation and formatting are different concerns.

This:

```sql
SELECT CONCAT('Total: ', total_amount)
FROM invoices;
```

may not produce the exact representation required by an external API or financial report.

For production financial or API output, explicitly control formatting when required rather than relying on implicit database casts.

For example, PostgreSQL provides formatting functions such as:

```sql
SELECT
    TO_CHAR(total_amount, 'FM999999990.00') AS formatted_total
FROM invoices;
```

The appropriate approach depends on whether the output is:

- A database value.
- An internal report.
- An API response.
- A CSV export.
- A human-readable display string.

Do not store presentation-formatted values as canonical numeric data.

## Concatenating Columns

A common reporting query combines columns:

```sql
SELECT
    id,
    CONCAT(first_name, ' ', last_name) AS display_name,
    CONCAT(city, ', ', country) AS location
FROM customers;
```

This is useful when the derived value is needed only for the result set.

The database remains responsible for the source fields:

```text
first_name
last_name
city
country
```

rather than storing redundant copies such as:

```text
display_name
location
```

unless there is a specific modeling or performance reason to do so.

## Concatenating Constants

Concatenation can add fixed prefixes or suffixes.

```sql
SELECT
    CONCAT('USR-', id) AS external_reference
FROM users;
```

For example:

```text
id = 10452
```

produces:

```text
USR-10452
```

This can be useful for generating representations, but it does not automatically make the generated value a safe or globally unique identifier.

If an external identifier has uniqueness, lifecycle, or security requirements, model those requirements explicitly.

## Concatenation and NULL Handling with COALESCE

`COALESCE()` can explicitly define fallback behavior.

```sql
SELECT
    COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') AS full_name
FROM users;
```

However, this can produce undesirable whitespace when values are missing.

A cleaner approach is often:

```sql
SELECT
    CONCAT_WS(' ', first_name, last_name) AS full_name
FROM users;
```

Use `COALESCE()` when the fallback value itself has business meaning.

For example:

```sql
SELECT
    CONCAT('Account: ', COALESCE(account_name, 'Unknown'))
FROM accounts;
```

Here, `"Unknown"` is an explicit representation of missing data.

## Whitespace and Formatting

Concatenation does not automatically normalize whitespace.

This:

```sql
SELECT CONCAT(first_name, ' ', last_name)
FROM users;
```

can produce unexpected output if source data contains:

```text
first_name = " Alice "
last_name  = "Johnson "
```

The result may contain extra whitespace.

For controlled normalization:

```sql
SELECT
    CONCAT_WS(
        ' ',
        NULLIF(TRIM(first_name), ''),
        NULLIF(TRIM(last_name), '')
    ) AS full_name
FROM users;
```

This handles both:

- `NULL`
- Empty or whitespace-only values

The expression is more complex, so it should be used when the input data actually requires that level of normalization.

## Concatenation in WHERE Clauses

Concatenation can be used in predicates:

```sql
SELECT
    id,
    first_name,
    last_name
FROM users
WHERE CONCAT(first_name, ' ', last_name) = :full_name;
```

This is convenient but potentially problematic at scale.

The database may need to construct the concatenated expression for many rows before comparing it with the parameter. A normal index on:

```text
first_name
last_name
```

does not automatically mean the database can efficiently use those indexes for the concatenated expression.

For high-volume lookups, prefer predicates aligned with the data model:

```sql
SELECT
    id,
    first_name,
    last_name
FROM users
WHERE first_name = :first_name
  AND last_name = :last_name;
```

Or introduce an intentionally indexed derived value when the search requirement genuinely calls for it.

## Concatenation and Indexes

Consider:

```sql
SELECT *
FROM customers
WHERE CONCAT(first_name, ' ', last_name) = :name;
```

If this query becomes a hot path, inspect the execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM customers
WHERE CONCAT(first_name, ' ', last_name) = 'Alice Johnson';
```

Depending on the database, options may include:

- Expression/function-based indexes.
- Generated/computed columns.
- Canonical search columns.
- Separate predicates against normalized fields.

Do not create an expression index merely because a function appears in a query. Confirm that the query is frequent and expensive enough to justify the additional index storage and write overhead.

## Concatenation in Aggregations

String concatenation can also be combined with aggregation.

PostgreSQL provides `STRING_AGG()`:

```sql
SELECT
    customer_id,
    STRING_AGG(product_name, ', ' ORDER BY product_name) AS products
FROM order_items
GROUP BY customer_id;
```

This is different from `CONCAT()`.

| Function | Purpose |
|---|---|
| `CONCAT()` | Combines expressions within one row |
| `CONCAT_WS()` | Combines expressions using a separator |
| `STRING_AGG()` | Combines values across multiple rows |

This distinction is important:

```text
CONCAT()
row 1 → value

STRING_AGG()
row 1 ┐
row 2 ├→ one aggregated value
row 3 ┘
```

## Backend API Example

Suppose a REST API returns customer information:

```json
{
  "first_name": "Alice",
  "last_name": "Johnson",
  "display_name": "Alice Johnson"
}
```

If `display_name` is only a presentation field, it can be derived by SQL:

```sql
SELECT
    id,
    first_name,
    last_name,
    CONCAT_WS(' ', first_name, last_name) AS display_name
FROM customers
WHERE id = :customer_id;
```

The data flow is:

```mermaid
flowchart LR
    A[HTTP Request] --> B[FastAPI / Django]
    B --> C[Parameterized SQL]
    C --> D[(PostgreSQL)]
    D --> E[CONCAT_WS Derived Value]
    E --> F[Application Response]
    F --> G[HTTP Response]
```

The important architectural decision is whether `display_name` is:

- A transient presentation value.
- A canonical business attribute.
- A searchable identifier.
- A value required by downstream systems.

Only the first case generally calls for simple query-time concatenation.

## Django ORM

Django supports database functions through expressions.

For example:

```python
from django.db.models.functions import Concat
from django.db.models import F, Value

queryset = Customer.objects.annotate(
    display_name=Concat(
        F("first_name"),
        Value(" "),
        F("last_name"),
    )
)
```

For nullable or optional components, database-specific functions or expressions may be more appropriate.

When performance matters, inspect the SQL generated by the ORM and evaluate the actual database execution plan.

## Security Considerations

Concatenating strings in SQL is not the same as safely constructing SQL statements.

Never build SQL by interpolating user-controlled values:

```python
query = f"""
SELECT *
FROM users
WHERE CONCAT(first_name, ' ', last_name) = '{name}'
"""
```

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT id, first_name, last_name
    FROM users
    WHERE CONCAT(first_name, ' ', last_name) = %s
    """,
    (name,),
)
```

The concatenation happens **inside the SQL expression**, while the user-controlled value remains a bound parameter.

This distinction is critical:

```text
Unsafe:
user input → SQL source code

Safe:
user input → bound parameter → SQL expression
```

## Performance Considerations

Concatenation itself is usually inexpensive for small result sets. Problems arise when expressions are applied across large datasets or inside high-frequency predicates.

Potential costs include:

- CPU spent constructing strings.
- Large intermediate values.
- Reduced index effectiveness.
- Increased query latency.
- Additional memory consumption.
- Higher database CPU utilization.

Be especially careful with queries such as:

```sql
SELECT *
FROM customers
WHERE CONCAT(first_name, ' ', last_name) ILIKE '%alice%';
```

This combines:

- Per-row concatenation.
- Case-insensitive matching.
- A leading wildcard.

For large datasets, specialized search strategies may be significantly more appropriate.

## Production Considerations

### Prefer Canonical Data Over Derived Text

If a value can be represented structurally, keep the structured representation.

Prefer:

```text
first_name
last_name
country_code
customer_id
```

over repeatedly parsing:

```text
"Alice Johnson +91 9876543210"
```

### Avoid Redundant Storage

Do not automatically add:

```text
full_name
```

to the database merely because the API needs it.

Redundant data introduces synchronization concerns:

```text
first_name changes
    ↓
full_name must also change
```

A derived query value avoids this consistency problem when query-time computation is inexpensive.

### Consider Generated Columns for Hot Derived Values

If a deterministic derived string is queried frequently and query-time computation becomes expensive, a generated/computed column can be considered where supported.

The decision should account for:

- Read frequency.
- Write frequency.
- Index requirements.
- Storage overhead.
- Database capabilities.
- Consistency requirements.

### Keep Presentation Logic in the Appropriate Layer

Simple values such as:

```text
first_name + last_name
```

are reasonable SQL projections.

Complex presentation rules involving localization, pluralization, formatting, or user-specific presentation are usually better handled by the application layer.

## Common Mistakes

### Assuming `||` and `CONCAT()` Handle NULL the Same Way

They do not necessarily have the same semantics.

```sql
SELECT 'A' || NULL;
```

and:

```sql
SELECT CONCAT('A', NULL);
```

can produce different results.

Always verify the behavior of the target database.

### Creating Extra Separators

This:

```sql
CONCAT(first_name, ' ', middle_name, ' ', last_name)
```

can create malformed output when `middle_name` is NULL.

For optional fields, consider:

```sql
CONCAT_WS(' ', first_name, middle_name, last_name)
```

### Searching on Concatenated Columns Without Considering Indexes

This:

```sql
WHERE CONCAT(first_name, ' ', last_name) = :name
```

may not use ordinary indexes efficiently.

Validate with `EXPLAIN` before using such a pattern on a high-volume endpoint.

### Storing Every Derived String

Persisting:

```text
full_name
display_name
formatted_address
customer_label
```

can create unnecessary synchronization problems.

Store derived values only when there is a concrete modeling or performance reason.

### Using Concatenation for Security

Concatenation does not protect against SQL injection.

The correct protection is parameterized SQL, not string manipulation.

### Relying on Implicit Type Conversion

Combining numeric, date, timestamp, and textual values can produce database-specific results.

When exact output matters, use explicit casts or formatting functions.

## Interview Traps

| Question | Correct Reasoning |
|---|---|
| `CONCAT()` vs `\|\|`? | They are different mechanisms and can differ in NULL behavior. |
| What happens when `||` receives NULL? | In PostgreSQL, NULL generally propagates through concatenation. |
| Why use `CONCAT_WS()`? | It concatenates values using a separator while skipping NULL arguments. |
| Does concatenation preserve indexes? | Not automatically; expressions in predicates may require expression indexes or another strategy. |
| Should `full_name` always be stored? | No; derive it when appropriate unless storage/indexing requirements justify persistence. |
| Is `CONCAT()` SQL injection protection? | No. User input must still be parameterized. |
| `CONCAT()` vs `STRING_AGG()`? | `CONCAT()` combines expressions within a row; `STRING_AGG()` combines values across rows. |

## Decision Guide

| Requirement | Recommended Approach |
|---|---|
| Combine two required fields for display | `CONCAT()` or `\|\|` |
| Combine optional fields with separators | `CONCAT_WS()` |
| Generate a simple query-time label | SQL concatenation |
| Search frequently by a derived concatenated value | Evaluate expression/generated column + index |
| Combine values across rows | `STRING_AGG()` or database equivalent |
| Complex localized presentation | Application layer |
| User-controlled SQL values | Parameterized queries |
| Canonical business identifier | Explicitly modeled column |
| Large-scale text search | Appropriate text/search indexing rather than naive concatenation |

## Recommended Practices

- Choose `CONCAT()`, `CONCAT_WS()`, or `||` based on explicit NULL and formatting requirements.
- Use `CONCAT_WS()` when optional components need clean separator handling.
- Treat concatenated values as derived data unless the domain requires them to be canonical.
- Avoid filtering on concatenated expressions in hot paths without checking the execution plan.
- Use expression indexes or generated columns when measured workload characteristics justify them.
- Use parameterized SQL for every user-controlled value.
- Use explicit casting or formatting when exact numeric/date/time output matters.
- Keep complex presentation and localization logic outside SQL.
- Distinguish row-level concatenation from cross-row aggregation such as `STRING_AGG()`.

## Key Takeaways

- **`CONCAT()`, `CONCAT_WS()`, and `||` solve related problems but have different semantics, especially around NULL values.**
- **`CONCAT_WS()` is particularly useful for combining optional fields without generating unnecessary separators.**
- **Concatenated expressions in predicates can affect index usage, so production queries should be validated with execution plans and appropriate indexing strategies.**
- **Derived display strings should not automatically become persisted columns; model and persist them only when consistency, search, or performance requirements justify it.**
- **String concatenation is unrelated to SQL injection protection—user-controlled values must always be passed through parameterized queries.**