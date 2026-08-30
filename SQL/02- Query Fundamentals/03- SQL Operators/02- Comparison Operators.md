# 02- Comparison Operators

## Overview

Comparison operators evaluate a relationship between two expressions and produce a boolean result used primarily for filtering rows. They are fundamental to `WHERE`, `HAVING`, `JOIN`, and conditional expressions.

The core comparison operators are:

| Operator | Meaning | Example |
|---|---|---|
| `=` | Equal to | `status = 'active'` |
| `<>` | Not equal to | `status <> 'deleted'` |
| `!=` | Not equal to | `status != 'deleted'` |
| `>` | Greater than | `price > 100` |
| `<` | Less than | `price < 100` |
| `>=` | Greater than or equal | `age >= 18` |
| `<=` | Less than or equal | `age <= 18` |

They look simple, but production correctness depends on understanding `NULL`, data types, three-valued logic, implicit conversions, collations, and index usage.

## Basic Comparison Operators

### Equality

`=` checks whether two expressions are equal.

```sql
SELECT
    id,
    email,
    status
FROM users
WHERE status = 'active';
```

This is one of the most common filtering operations in backend applications.

Equality is useful for:

- Status filtering.
- Foreign-key matching.
- Exact identifiers.
- Boolean flags.
- Tenant isolation.
- Business-state filtering.

For example:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = :customer_id
  AND status = 'paid';
```

Use parameterized values for application-supplied input.

### Not Equal

SQL commonly supports both `<>` and `!=`.

```sql
SELECT *
FROM users
WHERE status <> 'deleted';
```

Many systems also accept:

```sql
SELECT *
FROM users
WHERE status != 'deleted';
```

`<>` is the SQL-standard spelling. `!=` is widely supported but can be less portable across SQL implementations.

The important production issue is that neither expression matches `NULL` values.

```sql
WHERE status <> 'deleted'
```

does not mean:

```text
status is anything except 'deleted', including NULL
```

Rows where `status` is `NULL` evaluate to `UNKNOWN` and are normally excluded by `WHERE`.

## Greater Than and Less Than

Range comparisons use:

```text
>   greater than
<   less than
>=  greater than or equal
<=  less than or equal
```

Example:

```sql
SELECT
    id,
    price
FROM products
WHERE price > 100;
```

Inclusive boundary:

```sql
SELECT
    id,
    price
FROM products
WHERE price >= 100;
```

These operators are heavily used for:

- Numeric ranges.
- Timestamps.
- Pagination boundaries.
- Age or quantity constraints.
- Threshold-based business rules.

For timestamps:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

Half-open intervals are often preferable for time windows because adjacent ranges can be composed without overlapping at the boundary.

## Comparison Results and Three-Valued Logic

SQL does not have only `TRUE` and `FALSE`. Comparisons involving `NULL` can produce `UNKNOWN`.

Conceptually:

```text
TRUE
FALSE
UNKNOWN
```

For example:

```sql
SELECT *
FROM users
WHERE deleted_at = NULL;
```

This is incorrect because `NULL` represents the absence or unknown value rather than an ordinary value that can be compared with `=`.

Use:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

And:

```sql
SELECT *
FROM users
WHERE deleted_at IS NOT NULL;
```

### Why This Matters

Consider:

```text
id    status
----  --------
1     active
2     deleted
3     NULL
```

The predicate:

```sql
status <> 'deleted'
```

returns `TRUE` for row `1`, `FALSE` for row `2`, and `UNKNOWN` for row `3`.

Because `WHERE` retains rows whose predicate evaluates to `TRUE`, row `3` is excluded.

This is one of the most important SQL comparison rules to understand.

## Comparison Operator Reference

| Expression | Typical result |
|---|---|
| `5 = 5` | `TRUE` |
| `5 = 10` | `FALSE` |
| `5 <> 10` | `TRUE` |
| `5 > 3` | `TRUE` |
| `5 < 3` | `FALSE` |
| `NULL = NULL` | `UNKNOWN` |
| `NULL <> 5` | `UNKNOWN` |
| `NULL > 5` | `UNKNOWN` |
| `NULL IS NULL` | `TRUE` |
| `NULL IS NOT NULL` | `FALSE` |

The exact representation of boolean results varies by database, but the logical behavior is fundamental to SQL.

## Comparisons with Dates and Timestamps

Date and timestamp comparisons are common in backend systems.

```sql
SELECT
    id,
    created_at
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

For example, an API requesting orders created during a particular day can translate its application-level time window into a precise SQL range.

Prefer passing properly typed timestamp parameters rather than constructing date strings inside SQL.

### Avoiding Boundary Bugs

This pattern:

```sql
WHERE created_at BETWEEN :start_time AND :end_time
```

can be problematic when `:end_time` represents the beginning of the next period or when timestamp precision is misunderstood.

For time windows, this is often clearer:

```sql
WHERE created_at >= :start_time
  AND created_at < :end_time
```

The interval is:

```text
[start_time, end_time)
```

which includes the start and excludes the end.

## Comparisons with Strings

String equality depends on database behavior, collation, and data type.

```sql
SELECT
    id,
    email
FROM users
WHERE email = :email;
```

Do not assume every database performs case-sensitive or case-insensitive comparison identically.

For production systems, explicitly define requirements for:

- Case sensitivity.
- Unicode behavior.
- Collation.
- Normalization.
- Locale-specific sorting and comparison.

If email addresses are normalized at application boundaries, the query can often use direct equality without applying functions to the indexed column.

## Comparisons with Numeric Values

Numeric comparisons should use compatible numeric types.

```sql
SELECT
    id,
    price
FROM products
WHERE price >= :minimum_price;
```

Schema types should represent the domain accurately.

For monetary values, use exact numeric types such as `NUMERIC` or `DECIMAL` rather than relying on floating-point representation.

```sql
CREATE TABLE products (
    id BIGINT PRIMARY KEY,
    price NUMERIC(12, 2) NOT NULL
);
```

This avoids many precision problems when filtering and calculating financial values.

## Comparison Operators in JOIN Conditions

Comparison operators are not limited to `WHERE`.

The most common join uses equality:

```sql
SELECT
    o.id,
    u.email
FROM orders AS o
JOIN users AS u
    ON u.id = o.user_id;
```

Range comparisons can also be used when the relationship is based on an interval.

```sql
SELECT
    o.id,
    r.name
FROM orders AS o
JOIN shipping_rates AS r
    ON o.total_amount >= r.minimum_amount
   AND o.total_amount < r.maximum_amount;
```

Range joins can be significantly more expensive than simple equality joins, so they deserve execution-plan analysis for large datasets.

## Comparison Operators in HAVING

`HAVING` filters groups after aggregation.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The distinction is:

```text
WHERE
  filters rows before grouping

GROUP BY
  creates groups

HAVING
  filters groups after aggregation
```

Do not use `HAVING` when a row-level `WHERE` predicate can perform the filtering earlier.

Prefer:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

This can reduce the number of rows that reach the aggregation stage.

## Comparison Operators and Boolean Logic

Comparison operators are commonly combined with `AND`, `OR`, and `NOT`.

```sql
SELECT
    id,
    status,
    total_amount
FROM orders
WHERE status = 'paid'
  AND total_amount >= 100;
```

Use parentheses when mixing `AND` and `OR`.

```sql
SELECT
    id,
    status
FROM orders
WHERE status = 'paid'
  AND (
      total_amount >= 100
      OR priority = 'high'
  );
```

Without explicit grouping, operator precedence can produce a different predicate from the one intended by the business requirement.

## Comparison Operators and Indexes

Simple comparisons are often highly index-friendly.

Given:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

a query such as:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

can potentially use the index efficiently.

For equality:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

supports access patterns such as:

```sql
WHERE customer_id = :customer_id
```

The optimizer ultimately decides whether an index is beneficial.

### Avoid Transforming Indexed Columns Unnecessarily

Suppose an index exists on:

```sql
created_at
```

A predicate such as:

```sql
WHERE DATE(created_at) = :date
```

may prevent the database from using the plain index as efficiently as a direct range predicate.

Prefer a range where appropriate:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

If an expression is required frequently, a database-specific functional/expression index may be appropriate.

Always validate with `EXPLAIN`.

## Implicit Type Conversion

Comparing incompatible types can trigger implicit conversion.

For example:

```sql
WHERE user_id = '123'
```

when `user_id` is numeric may be accepted by some databases.

Do not rely on this behavior in production code.

Prefer correctly typed parameters:

```sql
WHERE user_id = :user_id
```

where the driver binds the parameter using the appropriate type.

Implicit conversions can cause:

- Unexpected comparison semantics.
- Runtime errors.
- Poor index usage.
- Database-specific behavior.
- Hidden performance regressions.

## Safe Application Filtering

A REST API might expose:

```text
GET /orders?min_total=100
```

The application should validate the input and pass it as a parameter.

```sql
SELECT
    id,
    customer_id,
    total_amount
FROM orders
WHERE total_amount >= :min_total
ORDER BY created_at DESC;
```

Do not construct SQL by interpolating request values:

```python
# Unsafe pattern
query = f"SELECT * FROM orders WHERE total_amount >= {request.query_params['min_total']}"
```

Use parameterized queries through the database driver or ORM instead.

For dynamic operators such as `>`, `<`, or `>=`, parameter binding generally applies to values, not arbitrary SQL syntax. If an API supports a dynamic operator, map an allowlisted API value to a known SQL fragment.

Conceptually:

```text
API operator
    ↓
allowlist validation
    ↓
known SQL operator
    ↓
parameterized value
    ↓
database
```

## Comparison Operators in Keyset Pagination

Comparison operators are central to keyset pagination.

For a descending timestamp-based feed:

```sql
SELECT
    id,
    created_at,
    title
FROM posts
WHERE created_at < :cursor_created_at
ORDER BY created_at DESC
LIMIT 50;
```

If multiple rows can have the same timestamp, use a deterministic tie-breaker:

```sql
SELECT
    id,
    created_at,
    title
FROM posts
WHERE (created_at, id) < (:cursor_created_at, :cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

The comparison boundary allows the database to seek directly into the ordered dataset rather than discarding a large number of preceding rows.

This is one reason comparison operators become increasingly important as backend systems move from basic SQL toward high-scale pagination.

## Performance Considerations

Comparison predicates are usually inexpensive individually, but query performance depends on:

- Selectivity.
- Index availability.
- Data distribution.
- Data types.
- Cardinality.
- Predicate expressions.
- Join strategy.
- Statistics.
- Result size.

For example:

```sql
WHERE status = 'active'
```

may not benefit much from an index if nearly every row is active.

Conversely:

```sql
WHERE customer_id = :customer_id
```

may be highly selective and suitable for indexed lookup.

Do not equate "has an index" with "will be faster."

Use:

```sql
EXPLAIN
SELECT ...
```

and, where appropriate in PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

to verify actual execution behavior.

## Common Mistakes

### Using `= NULL`

Incorrect:

```sql
WHERE deleted_at = NULL
```

Correct:

```sql
WHERE deleted_at IS NULL
```

`NULL` requires `IS NULL` or `IS NOT NULL`.

### Assuming `<>` Includes NULL

This:

```sql
WHERE status <> 'deleted'
```

does not include rows where `status IS NULL`.

If the business rule requires both conditions:

```sql
WHERE status <> 'deleted'
   OR status IS NULL
```

### Comparing the Wrong Data Types

Avoid unnecessary comparisons between strings and numeric columns.

Correct application-level typing reduces ambiguity and can preserve efficient index usage.

### Applying Functions to Indexed Columns

This:

```sql
WHERE DATE(created_at) = :date
```

can be less index-friendly than:

```sql
WHERE created_at >= :start
  AND created_at < :end
```

### Mixing AND and OR Without Parentheses

Potentially ambiguous:

```sql
WHERE status = 'paid'
  AND priority = 'high'
  OR total_amount > 1000
```

Make intent explicit:

```sql
WHERE status = 'paid'
  AND (
      priority = 'high'
      OR total_amount > 1000
  )
```

### Assuming String Comparison Is Universal

Case sensitivity and collation differ across database systems and configurations.

Do not build authentication, uniqueness, or search semantics around undocumented comparison assumptions.

### Dynamically Concatenating Operators

Avoid allowing raw request parameters to become SQL syntax.

Validate the operator against an explicit allowlist.

### Using Floating-Point Values for Financial Comparisons

Floating-point representation can produce surprising boundary behavior.

Use appropriate exact numeric types for monetary data.

## Production Considerations

### Correctness

Define comparison semantics explicitly for:

- `NULL`.
- Dates and time zones.
- Numeric precision.
- Case sensitivity.
- Collation.
- Inclusive versus exclusive boundaries.

### Scalability

For frequently executed filters:

- Index selective columns.
- Keep predicates sargable where possible.
- Avoid unnecessary functions on indexed columns.
- Inspect execution plans.
- Consider composite indexes for multi-column access patterns.

For example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

can support an access pattern that filters by customer and orders by creation time, subject to the database optimizer and exact query shape.

### Reliability

Time-based filtering should use explicit boundaries and consistent time zones.

A common production convention is to store timestamps consistently, typically in UTC, and convert to presentation time zones at the application boundary.

### Security

Use parameterized queries for values.

For dynamic comparison operators or columns, use allowlists rather than concatenating arbitrary request input into SQL.

### Observability

Monitor queries where comparison predicates are part of high-traffic endpoints.

Useful signals include:

- Query latency.
- Rows examined.
- Rows returned.
- Index usage.
- Sequential scans.
- Sort and aggregation cost.
- Query-plan changes after deployments.

## Interview Traps

| Question | Key Point |
|---|---|
| Why doesn't `column = NULL` work? | `NULL` represents an unknown/missing value and requires `IS NULL` |
| What does `column <> value` do with NULL? | The result is `UNKNOWN`, so the row is normally filtered out |
| What is SQL's three-valued logic? | Predicates can evaluate to `TRUE`, `FALSE`, or `UNKNOWN` |
| When should `WHERE` be preferred over `HAVING`? | For row-level filtering that can occur before aggregation |
| Why use `>= start AND < end` for timestamps? | It creates precise half-open intervals and avoids many boundary bugs |
| Can comparison predicates use indexes? | Often, provided the predicate and index are compatible with the access pattern |
| Why avoid functions on indexed columns? | They can prevent efficient use of a normal index |
| Why use parameterized comparisons? | They provide correct value binding and protect against SQL injection |
| Why are comparisons important for keyset pagination? | They define the cursor boundary used to seek to the next result set |

## Comparison Operator Decision Guide

| Requirement | Preferred approach |
|---|---|
| Exact value | `=` |
| Exclude a value | `<>` or `!=` |
| Minimum threshold | `>=` |
| Maximum threshold | `<=` |
| Strict lower boundary | `>` |
| Strict upper boundary | `<` |
| Missing value | `IS NULL` |
| Present value | `IS NOT NULL` |
| Time window | `>= start AND < end` |
| Keyset cursor | Comparison against ordered cursor columns |
| Dynamic API operator | Allowlist operator + parameterized value |

## Production Checklist

Before shipping comparison-heavy queries, verify:

- `NULL` semantics are intentional.
- Date and timestamp boundaries are explicit.
- Time zones are handled consistently.
- Numeric types match the domain.
- Monetary comparisons use exact numeric types.
- Application values are parameterized.
- Dynamic operators and identifiers use allowlists.
- `AND` and `OR` expressions use explicit parentheses where needed.
- Functions are not unnecessarily applied to indexed columns.
- Indexes match actual filtering and ordering patterns.
- Execution plans are checked for high-volume queries.
- Query latency and plan changes are observable in production.

## Key Takeaways

- Comparison operators power SQL filtering, joins, aggregation filters, and pagination boundaries.
- `NULL` follows three-valued logic; use `IS NULL` and `IS NOT NULL` rather than `=` or `<>` for null checks.
- Prefer explicit timestamp ranges such as `>= start AND < end` and correctly typed parameters for predictable production behavior.
- Keep comparison predicates index-friendly by avoiding unnecessary transformations of indexed columns and validating plans with `EXPLAIN`.
- Dynamic comparison behavior in APIs should use allowlists for SQL syntax and parameterized binding for values.