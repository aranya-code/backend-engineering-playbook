# 02- CAST

## Overview

`CAST` explicitly converts an expression from one SQL data type to another. It is one of the primary tools for controlling type compatibility in SQL and is especially important when working with heterogeneous data, API parameters, joins, reporting queries, timestamps, numeric calculations, and legacy schemas.

The standard SQL syntax is:

```sql
CAST(expression AS target_type)
```

For example:

```sql
SELECT CAST('42' AS INTEGER);
```

Explicit casting is preferable to relying on implicit conversion when the conversion is intentional and its semantics matter.

In production systems, `CAST` should generally clarify a type boundary rather than compensate for poor schema design.

## Why CAST Exists

SQL operations often involve values whose types do not initially match.

Common examples include:

- A numeric identifier stored as text in a legacy table.
- An API parameter represented as a string.
- A timestamp that must be converted to a date.
- An integer calculation that needs decimal precision.
- A UUID stored in textual form.
- A numeric value that must be rendered as text.
- A column from one system being compared with a column from another system.

Without explicit conversion, the database must either find an implicit conversion path or reject the expression.

```text
Expression
    │
    ▼
Current data type
    │
    ▼
CAST(... AS target_type)
    │
    ▼
Target data type
    │
    ▼
SQL operation
```

`CAST` makes this conversion part of the SQL expression instead of leaving the behavior to implicit type-resolution rules.

## Basic Syntax

The general form is:

```sql
CAST(expression AS target_type)
```

Examples:

```sql
SELECT CAST('123' AS INTEGER);

SELECT CAST(123 AS TEXT);

SELECT CAST('2026-08-30' AS DATE);

SELECT CAST(10 AS NUMERIC(10, 2));
```

`CAST` can be applied to:

- Columns
- Literals
- Parameters
- Function results
- Arithmetic expressions
- `CASE` expressions
- Aggregation results
- JSON-extracted values

For example:

```sql
SELECT CAST(order_id AS TEXT)
FROM orders;
```

## Common CAST Conversions

The exact supported conversions depend on the database engine.

| Source | Target | Typical use |
| --- | --- | --- |
| `TEXT` | `INTEGER` | Parse numeric input |
| `INTEGER` | `TEXT` | Formatting or textual comparison |
| `TEXT` | `DATE` | Parse standard date strings |
| `TIMESTAMP` | `DATE` | Remove time component |
| `INTEGER` | `NUMERIC` | Preserve decimal arithmetic |
| `NUMERIC` | `INTEGER` | Convert to whole-number representation |
| `TEXT` | `UUID` | Convert textual UUID input |
| `JSON` value | SQL type | Extract typed data |
| Boolean | `TEXT` | Serialization or presentation |

Not every conversion is safe or lossless.

## String to Numeric

A common use case is converting textual data into a numeric value.

```sql
SELECT CAST('1000' AS INTEGER);
```

This is useful when processing legacy data:

```sql
SELECT
    CAST(external_customer_id AS BIGINT) AS customer_id
FROM legacy_orders;
```

However, the source must contain values that the target type can parse.

For example:

```sql
SELECT CAST('abc' AS INTEGER);
```

will fail in databases such as PostgreSQL because the value cannot be interpreted as an integer.

### Production Consideration

Do not use `CAST` as a substitute for input validation.

If an API accepts:

```json
{
  "quantity": "100"
}
```

prefer validating and typing the value in the application layer before executing the query.

The database should still validate its own persisted data, but external input should not be allowed to reach a critical query with an unknown format.

## Numeric to String

Casting numeric values to text is useful when a numeric value must participate in a textual representation.

```sql
SELECT CAST(order_id AS TEXT)
FROM orders;
```

For example:

```sql
SELECT
    'ORDER-' || CAST(order_id AS TEXT) AS order_reference
FROM orders;
```

This is generally appropriate for presentation or serialization.

It should not be used to compensate for inconsistent identifier types in relational joins.

## String to DATE

A standard date string can be explicitly converted:

```sql
SELECT CAST('2026-08-30' AS DATE);
```

This is useful when the input format follows the database's accepted date representation.

For application queries, prefer typed parameters rather than manually constructing date literals.

```sql
SELECT *
FROM orders
WHERE order_date >= $1;
```

The application or database driver should supply `$1` as an appropriate date value.

## Timestamp to DATE

Casting a timestamp to a date removes the time component.

```sql
SELECT CAST(created_at AS DATE)
FROM orders;
```

For example:

```text
2026-08-30 14:37:12
        ↓
2026-08-30
```

This is useful for reporting and grouping by calendar date.

However, filtering through a cast can have performance implications.

Prefer:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

over:

```sql
WHERE CAST(created_at AS DATE) = $1
```

when the column is indexed and the query is intended to be highly selective.

The range predicate preserves a direct range condition on the timestamp column.

## Numeric Precision

`CAST` is frequently used to control arithmetic types.

Consider:

```sql
SELECT 10 / 3;
```

When integer operands are used, the result may follow integer-division semantics depending on the database.

If decimal arithmetic is required:

```sql
SELECT CAST(10 AS NUMERIC) / 3;
```

For production financial calculations, explicitly use exact numeric types:

```sql
SELECT
    quantity * CAST(unit_price AS NUMERIC(12, 2)) AS total
FROM order_items;
```

Do not assume that numeric-looking values automatically provide the precision required by the business domain.

## Numeric to Integer

Casting a decimal value to an integer can change its meaning.

For example:

```sql
SELECT CAST(19.95 AS INTEGER);
```

The exact behavior of decimal-to-integer conversion can be database-specific, particularly around rounding and truncation.

For business-critical calculations, do not rely on assumed behavior.

If the requirement is explicitly to truncate:

```sql
SELECT TRUNC(19.95);
```

If the requirement is to round:

```sql
SELECT ROUND(19.95);
```

Then cast the result if necessary.

The important distinction is:

```text
Conversion
    ≠
Business rounding policy
```

A cast should not silently encode a financial or business rule.

## CAST with CASE

`CASE` expressions often require explicit casts when branches have different types.

For example:

```sql
SELECT
    CASE
        WHEN status = 'active' THEN CAST(1 AS INTEGER)
        ELSE CAST(0 AS INTEGER)
    END AS active_flag
FROM users;
```

A more concise version is:

```sql
SELECT
    CASE
        WHEN status = 'active' THEN 1
        ELSE 0
    END AS active_flag
FROM users;
```

Explicit casts become more useful when the branches originate from different expressions or when the desired output type needs to be unambiguous.

For example:

```sql
SELECT
    CASE
        WHEN status = 'active' THEN CAST(priority AS TEXT)
        ELSE 'unknown'
    END AS priority_label
FROM tickets;
```

The cast establishes a textual result.

## CAST with COALESCE

`COALESCE` also needs compatible result types.

Suppose:

```sql
user_id BIGINT
username TEXT
```

This expression may require explicit conversion:

```sql
SELECT COALESCE(CAST(user_id AS TEXT), username)
FROM users;
```

Both possible outputs are now textual.

This is preferable to depending on an implicit conversion that may not exist or may behave differently across database engines.

## CAST in JOINs

A cast can bridge incompatible schemas:

```sql
SELECT
    o.order_id,
    c.customer_name
FROM orders AS o
JOIN customers AS c
    ON CAST(o.customer_id AS TEXT) = c.customer_id;
```

This can be useful during migrations or when integrating legacy systems.

However, if both columns represent the same domain, the long-term solution is usually to make their types compatible.

Prefer:

```text
orders.customer_id    → BIGINT
customers.customer_id → BIGINT
```

over permanently maintaining:

```text
orders.customer_id    → BIGINT
customers.customer_id → TEXT
```

and casting on every join.

### Why This Matters for Performance

Casting a join key changes the expression being compared.

Depending on the database and indexes, this can make index usage less effective and increase CPU work.

For large tables, type consistency should be treated as an architectural concern rather than merely a query-writing concern.

## CAST and Indexes

Consider:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

This predicate is generally preferable:

```sql
WHERE customer_id = $1;
```

over:

```sql
WHERE CAST(customer_id AS TEXT) = $1;
```

The second form transforms the column before comparison.

When the conversion is unavoidable and the access pattern is stable, an expression index may be appropriate in databases that support it.

PostgreSQL example:

```sql
CREATE INDEX idx_orders_customer_id_text
ON orders ((customer_id::TEXT));
```

However, this should be driven by an actual query workload and execution-plan evidence.

Do not create expression indexes simply because a cast appears in one query.

## CAST and Query Performance

A cast has a computational cost, although the cost is often negligible for small result sets.

The larger concern is **where** the cast is applied.

### Usually Low Risk

```sql
SELECT CAST(order_id AS TEXT)
FROM orders
WHERE order_id = $1;
```

The filtering operation can still use the native type of `order_id`, while the conversion is applied to returned rows.

### Potentially Expensive

```sql
SELECT *
FROM orders
WHERE CAST(order_id AS TEXT) = $1;
```

Here the conversion is part of the filtering expression.

For high-volume tables, inspect the execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE CAST(order_id AS TEXT) = $1;
```

Look for:

- Sequential scans.
- Increased CPU usage.
- Unexpected row counts.
- Ineffective index usage.
- Expensive expression evaluation.

## CAST and NULL

Casting `NULL` generally produces `NULL`:

```sql
SELECT CAST(NULL AS INTEGER);
```

The result remains `NULL`.

This is different from converting `NULL` into a default value.

If a default is required, use `COALESCE`:

```sql
SELECT COALESCE(CAST(value AS INTEGER), 0)
FROM metrics;
```

The operations have different responsibilities:

```text
CAST
→ changes the type

COALESCE
→ chooses a fallback value
```

Do not confuse the two.

## CAST with Boolean Values

Boolean conversion behavior differs significantly between database engines.

In PostgreSQL:

```sql
SELECT CAST('true' AS BOOLEAN);
```

can produce a boolean value.

However, applications should not depend on loosely formatted textual booleans.

Prefer typed application parameters and native boolean columns:

```sql
is_active BOOLEAN NOT NULL
```

Then query directly:

```sql
SELECT *
FROM users
WHERE is_active = TRUE;
```

Avoid storing arbitrary strings such as:

```text
"yes"
"Y"
"true"
"1"
"enabled"
```

when the domain is actually boolean.

## CAST and UUID

PostgreSQL supports native UUID values.

A textual UUID can be explicitly converted:

```sql
SELECT CAST(
    '550e8400-e29b-41d4-a716-446655440000'
    AS UUID
);
```

For application queries, prefer typed parameters:

```sql
SELECT *
FROM users
WHERE user_id = $1;
```

rather than repeatedly casting the database column:

```sql
WHERE CAST(user_id AS TEXT) = $1;
```

If `user_id` is a UUID column, the parameter should ideally be supplied as a UUID-compatible value.

## CAST and JSON

Semi-structured data frequently requires extracting a value and converting it to a relational type.

PostgreSQL example:

```sql
SELECT
    CAST(payload ->> 'quantity' AS INTEGER) AS quantity
FROM events;
```

The JSON extraction operator returns text in this case, so the value is explicitly converted to an integer.

For example:

```json
{
  "quantity": "25"
}
```

becomes:

```text
JSONB
  ↓
payload ->> 'quantity'
  ↓
TEXT
  ↓
CAST(... AS INTEGER)
  ↓
INTEGER
```

This pattern is useful for event-processing and migration workflows, but malformed JSON values can cause query failures.

If the field is critical and frequently queried, consider extracting it into a properly typed relational column.

## CAST in Aggregation

Casting can control the type of an aggregate calculation.

For example:

```sql
SELECT
    AVG(CAST(quantity AS NUMERIC))
FROM order_items;
```

This can be useful when the source column is integer-based but the result requires decimal semantics.

Another common pattern is calculating a percentage:

```sql
SELECT
    100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
    / NULLIF(COUNT(*), 0) AS completion_rate
FROM orders;
```

Using a decimal literal such as `100.0` establishes decimal arithmetic without requiring an explicit cast in this particular expression.

An explicit form is also valid:

```sql
SELECT
    CAST(
        100 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
        AS NUMERIC
    ) / NULLIF(COUNT(*), 0) AS completion_rate
FROM orders;
```

The important production concern is to make the intended numeric semantics obvious.

## CAST in ORDER BY

Casting can change the sort semantics.

Suppose numeric values are stored as text:

```text
1
2
10
20
```

Text sorting produces:

```text
1
10
2
20
```

Numeric sorting produces:

```text
1
2
10
20
```

A temporary compatibility solution is:

```sql
SELECT *
FROM products
ORDER BY CAST(sort_position AS INTEGER);
```

However, if `sort_position` is fundamentally numeric, storing it as a numeric type is the better design.

## CAST in GROUP BY

Casting can also normalize values into a grouping type.

For example:

```sql
SELECT
    CAST(created_at AS DATE) AS order_date,
    COUNT(*) AS order_count
FROM orders
GROUP BY CAST(created_at AS DATE);
```

This groups timestamps by calendar date.

For large tables, consider the workload carefully. Repeatedly computing expressions over millions of rows may require:

- Appropriate indexes.
- Generated/computed columns.
- Expression indexes.
- Pre-aggregated reporting tables.
- Materialized views.

The correct solution depends on query frequency and data volume.

## Explicit CAST vs Implicit Conversion

| Aspect | Explicit `CAST` | Implicit conversion |
| --- | --- | --- |
| Intent | Clear | Hidden |
| Portability | Generally better | Database-specific |
| Debugging | Easier | Harder |
| Schema mismatch | Visible | Easy to overlook |
| Query readability | Usually better | Potentially ambiguous |
| Performance analysis | Easier to reason about | Conversion may be less obvious |
| Production safety | More predictable | Depends heavily on database rules |

Explicit conversion should be preferred when the type boundary is meaningful.

## CAST vs PostgreSQL `::`

PostgreSQL provides shorthand cast syntax:

```sql
SELECT '42'::INTEGER;
```

The equivalent standard syntax is:

```sql
SELECT CAST('42' AS INTEGER);
```

Comparison:

| Syntax | Standard SQL | PostgreSQL |
| --- | --- | --- |
| `CAST(value AS TYPE)` | Yes | Yes |
| `value::TYPE` | No | Yes |

Use `CAST()` when portability and explicitness are priorities.

Use `::` when writing PostgreSQL-specific SQL and concise syntax improves readability.

For a PostgreSQL-only engineering playbook, both are important to recognize.

## Safe Type Boundaries in Backend Systems

A robust backend system should establish types as early as practical.

```mermaid
flowchart LR
    A[HTTP / gRPC Request] --> B[Application Validation]
    B --> C[Typed Application Value]
    C --> D[Parameterized SQL]
    D --> E[Database Type System]
    E --> F[Typed Result]
    F --> G[API Serialization]
```

For example:

```text
HTTP JSON
"123"
   ↓
Request validation
   ↓
Python int
   ↓
Database driver parameter
   ↓
PostgreSQL BIGINT
```

This is generally preferable to passing unvalidated text into SQL and repeatedly casting it inside queries.

Frameworks such as Django and FastAPI can perform application-level validation and type conversion before database access.

The database should remain responsible for enforcing persistent data integrity.

## Production Migration Pattern

`CAST` is particularly useful during schema migrations.

Suppose a legacy table contains:

```sql
customer_id TEXT
```

but the target schema requires:

```sql
customer_id BIGINT
```

A migration may need to convert existing data:

```sql
SELECT CAST(customer_id AS BIGINT)
FROM legacy_orders;
```

Before executing a destructive schema change, validate the data.

For example:

```sql
SELECT customer_id
FROM legacy_orders
WHERE customer_id !~ '^[0-9]+$';
```

PostgreSQL-specific validation can identify values that cannot safely become integers.

A production migration should generally follow:

```text
Inspect existing data
        ↓
Identify invalid values
        ↓
Clean or quarantine invalid records
        ↓
Validate conversion
        ↓
Backfill / migrate
        ↓
Add constraints
        ↓
Remove legacy representation
```

Do not discover invalid conversion data halfway through a large production migration.

## Common Mistakes

### Casting Every Query Instead of Fixing the Schema

This is a common symptom of schema inconsistency:

```sql
ON orders.customer_id::TEXT = customers.customer_id
```

If the fields represent the same domain, align their database types.

### Casting the Indexed Column

Avoid unnecessary expressions such as:

```sql
WHERE CAST(user_id AS TEXT) = $1
```

when a correctly typed parameter can be used:

```sql
WHERE user_id = $1
```

### Assuming CAST Is Lossless

Conversions can:

- Truncate.
- Round.
- Reject values.
- Reduce precision.
- Remove time information.
- Change representation.

Always verify the semantics of the target type.

### Using CAST as Input Validation

This:

```sql
CAST(request_value AS INTEGER)
```

does not replace proper request validation.

Invalid input can still produce a database error and potentially turn a normal request into a `500` response if not handled correctly.

### Ignoring Database-Specific Behavior

The same conversion may behave differently across:

- PostgreSQL
- MySQL
- SQL Server
- Oracle

Production SQL should follow the target database's documented type-conversion rules.

### Casting for Presentation Inside Core Data Logic

If a value is only being formatted for an API response, consider whether the application or serialization layer should handle that formatting.

SQL should perform presentation transformations when they reduce data transfer or are genuinely part of the query's purpose, not merely because it is possible.

### Converting Monetary Values Without Defining Precision

Do not use:

```sql
CAST(amount AS INTEGER)
```

for a monetary business rule without explicitly deciding how fractional amounts should be handled.

## Performance Considerations

A cast is not automatically a performance problem.

The key questions are:

- How many rows are processed?
- Is the cast applied to a column or a parameter?
- Is the expression part of a join or filter?
- Can an index still be used efficiently?
- Is the conversion performed repeatedly?
- Is the result reused?
- Can the schema eliminate the conversion?

A practical optimization hierarchy is:

1. Use compatible schema types.
2. Bind correctly typed parameters.
3. Avoid casting indexed columns in predicates.
4. Use range predicates for temporal filtering where appropriate.
5. Inspect execution plans.
6. Consider expression indexes only when justified by workload.
7. Consider schema changes when repeated casts become a permanent performance concern.

## Security Considerations

`CAST` itself is not a SQL injection defense.

This is still unsafe:

```python
query = f"""
    SELECT *
    FROM users
    WHERE user_id = CAST('{user_input}' AS INTEGER)
"""
```

The input is still being interpolated into SQL.

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT *
    FROM users
    WHERE user_id = %s
    """,
    [user_id],
)
```

Application validation and parameter binding should handle untrusted input.

Type conversion should not be used as a security boundary.

## Operational Considerations

When introducing casts into production queries:

- Monitor query latency.
- Check execution plans for high-volume queries.
- Watch CPU utilization on database instances.
- Check index usage.
- Test malformed data paths.
- Validate migration scripts against production-like data.
- Measure before and after schema changes.
- Verify behavior under realistic row counts.

For PostgreSQL workloads, tools such as:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and database query statistics are useful for identifying conversion-heavy queries.

## When to Use CAST

Use explicit `CAST` when:

- A conversion is intentional.
- SQL expression types need to be made compatible.
- Numeric precision must be controlled.
- A legacy schema requires temporary conversion.
- JSON values need to become typed SQL values.
- A timestamp must become a date for reporting.
- A query needs an explicit type boundary.
- A migration requires validated data conversion.

Avoid it when:

- It compensates for a schema mismatch that should be fixed.
- It is repeatedly applied to indexed columns.
- The application could supply a correctly typed parameter.
- It hides a business rule such as rounding.
- It is used instead of input validation.
- It is added without checking query-plan impact.

## Interview Traps

| Interview question | Strong answer |
| --- | --- |
| Why use `CAST`? | To explicitly convert an expression to a target SQL type |
| Is `CAST` the same as implicit conversion? | No; `CAST` makes the conversion explicit |
| Can `CAST` affect indexes? | Yes, especially when applied to indexed columns in predicates or joins |
| Is every cast lossless? | No; conversions can truncate, round, reject, or discard information |
| Should application input always be cast in SQL? | No; validate and type input in the application and use parameters |
| `CAST()` vs `::` in PostgreSQL? | `CAST()` is standard SQL; `::` is PostgreSQL-specific shorthand |
| Why avoid casts in join conditions? | They can hide schema inconsistencies and may reduce efficient index usage |
| Does `CAST(NULL AS INTEGER)` return `0`? | No; it returns `NULL` |
| Does `CAST` perform validation? | It validates whether the value can be converted, but it is not a substitute for application validation |
| How do you investigate a slow cast-heavy query? | Inspect the execution plan, indexes, row counts, and where the cast is applied |

## Key Takeaways

- `CAST(expression AS type)` makes SQL type conversion explicit and predictable.
- Prefer correctly typed parameters and compatible schemas over repeatedly casting columns in joins and filters.
- Casting can lose precision, truncate information, reject invalid values, or alter temporal semantics; never assume conversion is lossless.
- `CAST` is useful for controlled transformations, reporting, JSON extraction, legacy migrations, and expression type resolution, but it is not input validation or a security mechanism.
- For production workloads, evaluate where casts execute, inspect query plans, and fix recurring type mismatches at the schema boundary when possible.