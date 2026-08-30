# 03- CONVERT

## Overview

`CONVERT` is a database-specific function used to convert an expression from one SQL data type to another. It is most strongly associated with **Microsoft SQL Server**, where it is commonly used for data-type conversion and, particularly, for controlling date/time and string formatting through the optional `style` argument.

The basic SQL Server syntax is:

```sql
CONVERT(data_type [ ( length ) ], expression [ , style ])
```

For example:

```sql
SELECT CONVERT(INT, '42');
```

Unlike `CAST`, which is part of the SQL standard, `CONVERT` is a SQL Server-specific feature. The distinction matters when writing portable SQL or designing an application that may move between database engines.

`CONVERT` is most useful when working explicitly with SQL Server-specific functionality, especially date/time formatting and legacy SQL Server codebases.

## CAST vs CONVERT

Both functions perform type conversion:

```sql
SELECT CAST('42' AS INT);

SELECT CONVERT(INT, '42');
```

For straightforward conversions, they are often equivalent.

The major difference is that `CONVERT` supports a third `style` argument:

```sql
SELECT CONVERT(VARCHAR(10), GETDATE(), 23);
```

The style controls how certain values, especially dates and times, are converted to character representations.

| Feature | `CAST` | `CONVERT` |
| --- | --- | --- |
| SQL standard | Yes | No |
| SQL Server | Yes | Yes |
| Basic type conversion | Yes | Yes |
| Date/time style codes | No | Yes |
| Portability | Higher | SQL Server-specific |
| Typical use | General conversion | SQL Server-specific conversion and formatting |

For SQL Server-only applications, both are valid. For portable SQL, prefer `CAST` where it provides the required behavior.

## Basic Syntax

The general form is:

```sql
CONVERT(target_data_type, expression)
```

Examples:

```sql
SELECT CONVERT(INT, '100');

SELECT CONVERT(VARCHAR(50), 100);

SELECT CONVERT(DATE, '2026-08-30');

SELECT CONVERT(DECIMAL(12, 2), 19.95);
```

A style can optionally be supplied:

```sql
CONVERT(target_data_type, expression, style)
```

For example:

```sql
SELECT CONVERT(VARCHAR(10), GETDATE(), 23);
```

The target type is specified first, followed by the expression being converted.

## Converting Strings to Numbers

A common SQL Server use case is converting text into numeric values:

```sql
SELECT CONVERT(INT, '123');
```

This is useful when integrating with legacy schemas:

```sql
SELECT
    CONVERT(BIGINT, external_customer_id) AS customer_id
FROM legacy_orders;
```

If the source contains an invalid value:

```sql
SELECT CONVERT(INT, 'abc');
```

SQL Server raises a conversion error.

For data-cleaning workflows, SQL Server also provides `TRY_CONVERT`:

```sql
SELECT TRY_CONVERT(INT, 'abc');
```

Instead of failing the query, `TRY_CONVERT` returns `NULL` when the conversion cannot be performed.

This distinction is important for production data-quality pipelines.

## CONVERT vs TRY_CONVERT

| Function | Invalid conversion | Typical use |
| --- | --- | --- |
| `CONVERT` | Raises an error | Data known to be valid |
| `TRY_CONVERT` | Returns `NULL` | Untrusted or potentially malformed data |

Example:

```sql
SELECT
    external_id,
    TRY_CONVERT(BIGINT, external_id) AS customer_id
FROM imported_customers;
```

You can then identify invalid records:

```sql
SELECT external_id
FROM imported_customers
WHERE external_id IS NOT NULL
  AND TRY_CONVERT(BIGINT, external_id) IS NULL;
```

This is useful during migrations and ingestion validation.

However, `TRY_CONVERT` should not be used to silently hide bad data. A production pipeline should still measure, quarantine, or reject invalid records according to the domain's requirements.

## Converting Numbers to Strings

`CONVERT` can convert numeric values into character types:

```sql
SELECT CONVERT(VARCHAR(20), order_id)
FROM orders;
```

It can also be used to construct textual identifiers:

```sql
SELECT
    'ORDER-' + CONVERT(VARCHAR(20), order_id) AS order_reference
FROM orders;
```

Specify a sufficient target length.

For example:

```sql
CONVERT(VARCHAR(10), order_id)
```

may be insufficient if identifiers eventually exceed ten characters.

For stable production schemas, avoid using arbitrary string conversions to compensate for incompatible column types.

## VARCHAR vs CHAR During Conversion

SQL Server distinguishes between fixed-length and variable-length character types.

```sql
CONVERT(CHAR(10), value)
```

and:

```sql
CONVERT(VARCHAR(10), value)
```

do not have identical storage and padding semantics.

For most dynamic textual representations, `VARCHAR` is usually more appropriate.

When Unicode data is involved, use `NVARCHAR`:

```sql
SELECT CONVERT(NVARCHAR(100), customer_name);
```

The conversion target should match the application's character requirements.

## Date and Time Conversion

Date/time conversion is one of the most important SQL Server-specific uses of `CONVERT`.

For example:

```sql
SELECT CONVERT(DATE, GETDATE());
```

This removes the time component and returns a `date`.

Another example:

```sql
SELECT CONVERT(DATETIME2, '2026-08-30 14:30:00');
```

The target data type determines the resulting representation.

Common SQL Server temporal types include:

- `DATE`
- `TIME`
- `DATETIME`
- `DATETIME2`
- `DATETIMEOFFSET`
- `SMALLDATETIME`

Prefer modern temporal types such as `DATETIME2` for new SQL Server designs unless a specific compatibility requirement dictates otherwise.

## CONVERT Style Codes

SQL Server's `style` parameter controls formatting for supported conversions, especially date/time values.

For example:

```sql
SELECT CONVERT(VARCHAR(10), GETDATE(), 23);
```

Style `23` produces an ISO-like date representation:

```text
2026-08-30
```

Another common style is:

```sql
SELECT CONVERT(VARCHAR(19), GETDATE(), 120);
```

which produces a representation similar to:

```text
2026-08-30 14:30:00
```

Common styles include:

| Style | Typical representation | Common use |
| ---: | --- | --- |
| `23` | `yyyy-mm-dd` | Date-only output |
| `112` | `yyyymmdd` | Compact date representation |
| `120` | `yyyy-mm-dd hh:mi:ss` | ODBC-style timestamp |
| `121` | `yyyy-mm-dd hh:mi:ss.mmm` | Millisecond precision |
| `126` | ISO-style `yyyy-mm-ddThh:mi:ss.mmm` | Machine-readable representation |
| `127` | ISO-style with time-zone semantics | ISO-oriented output |

Exact formatting behavior depends on the source and target types.

For machine-to-machine interfaces, prefer unambiguous formats rather than locale-dependent representations.

## Why Style Codes Matter

Consider:

```sql
SELECT CONVERT(VARCHAR(10), GETDATE(), 101);
```

versus:

```sql
SELECT CONVERT(VARCHAR(10), GETDATE(), 103);
```

These represent different date conventions.

A format such as:

```text
08/30/2026
```

can be interpreted differently across systems.

An unambiguous representation such as:

```text
2026-08-30
```

is generally preferable for APIs, logs, exports, and data interchange.

Do not rely on server or session locale settings when the output is consumed by another system.

## Converting DATE to VARCHAR

For API or reporting output:

```sql
SELECT
    CONVERT(VARCHAR(10), order_date, 23) AS order_date
FROM orders;
```

The result is a string such as:

```text
2026-08-30
```

However, if the result is eventually serialized by a backend application, it is often better to return the native date/time value and let the application serialization layer format it.

For example, Django or FastAPI can serialize typed date/time values according to the API contract.

SQL formatting is most useful when:

- The database directly produces a report.
- A legacy export requires a specific format.
- Formatting reduces downstream transformation work.
- SQL Server-specific reporting logic is intentional.

## Converting VARCHAR to DATE

You can explicitly convert a string to a date:

```sql
SELECT CONVERT(DATE, '2026-08-30');
```

For predictable machine-generated input, use unambiguous formats.

Avoid depending on ambiguous strings such as:

```text
08/30/2026
```

because interpretation can depend on language, date format, and SQL Server session settings.

For application code, parameterized queries with typed values are preferable to constructing date strings manually.

## CONVERT with DATETIME2

For new SQL Server applications:

```sql
SELECT CONVERT(DATETIME2, '2026-08-30T14:30:00');
```

`DATETIME2` provides greater precision and a wider valid range than the older `DATETIME` type.

When the system needs timezone or offset information, use:

```sql
DATETIMEOFFSET
```

For example:

```sql
SELECT CONVERT(
    DATETIMEOFFSET,
    '2026-08-30T14:30:00+05:30'
);
```

This preserves the offset as part of the value.

The choice of temporal type should be based on the domain rather than the formatting requirements.

## CONVERT and Time Zones

`CONVERT` changes data types and formatting; it is not a general-purpose timezone conversion mechanism.

For timezone-aware SQL Server workloads, distinguish between:

```text
Type conversion
    ↓
CONVERT

Timezone transformation
    ↓
AT TIME ZONE
```

For example:

```sql
SELECT
    created_at AT TIME ZONE 'India Standard Time'
FROM orders;
```

Use the appropriate SQL Server timezone functionality instead of assuming that a `CONVERT` style code performs timezone conversion.

This distinction is important in distributed systems where services may run in different regions.

## CONVERT with NULL

Converting `NULL` produces `NULL`:

```sql
SELECT CONVERT(INT, NULL);
```

The result is not a default numeric value.

If a fallback is required:

```sql
SELECT COALESCE(
    CONVERT(INT, quantity),
    0
);
```

The responsibilities are different:

```text
CONVERT
→ Changes the type

COALESCE
→ Provides a fallback value
```

Do not use `CONVERT` when the actual requirement is null handling.

## CONVERT with CASE

`CONVERT` can be used to make `CASE` branches type-compatible.

```sql
SELECT
    CASE
        WHEN status = 'active'
            THEN CONVERT(VARCHAR(20), user_id)
        ELSE 'unknown'
    END AS user_reference
FROM users;
```

The conversion makes the intended textual result explicit.

It can also be used for numeric calculations:

```sql
SELECT
    CONVERT(DECIMAL(12, 2), quantity * unit_price) AS total_amount
FROM order_items;
```

Use explicit conversion when it clarifies the desired result type rather than adding casts mechanically.

## CONVERT with Aggregation

`CONVERT` can control the type of aggregation expressions.

For example:

```sql
SELECT
    CONVERT(DECIMAL(10, 2), AVG(CONVERT(DECIMAL(10, 2), amount)))
FROM payments;
```

However, excessive nested conversions often indicate that the underlying column type or query design should be reconsidered.

For financial values, store the data using an appropriate exact numeric type:

```sql
amount DECIMAL(19, 4)
```

Then aggregate directly whenever possible.

```sql
SELECT SUM(amount)
FROM payments;
```

The database schema should carry the domain's numeric semantics instead of forcing every query to reconstruct them.

## CONVERT in WHERE Clauses

A conversion in a predicate can affect performance.

Prefer:

```sql
SELECT *
FROM orders
WHERE created_at >= @start_date
  AND created_at < @end_date;
```

over:

```sql
SELECT *
FROM orders
WHERE CONVERT(DATE, created_at) = @target_date;
```

The first query expresses a range over the native column and is generally more compatible with an index on `created_at`.

The second transforms every candidate `created_at` value before comparison.

For large tables, this difference can be significant.

## SARGability

A predicate is generally considered **SARGable** when the database can efficiently use an index to satisfy the search condition.

Compare:

```sql
WHERE created_at >= @start
  AND created_at < @end
```

with:

```sql
WHERE CONVERT(DATE, created_at) = @date
```

The range predicate keeps the indexed column directly comparable.

This principle applies beyond `CONVERT`:

```sql
WHERE LOWER(email) = @email
```

or:

```sql
WHERE YEAR(created_at) = @year
```

can similarly transform the indexed column.

For production workloads, avoid wrapping indexed columns in functions unless an appropriate indexed expression/computed-column strategy has been deliberately designed.

## CONVERT in JOIN Conditions

A conversion may be required when joining legacy systems:

```sql
SELECT
    o.order_id,
    c.customer_name
FROM orders AS o
JOIN customers AS c
    ON CONVERT(VARCHAR(50), o.customer_id) = c.customer_id;
```

This can be useful temporarily during a migration.

It should not become the permanent design when both fields represent the same domain.

Prefer:

```text
orders.customer_id    → BIGINT
customers.customer_id → BIGINT
```

rather than maintaining:

```text
orders.customer_id    → BIGINT
customers.customer_id → VARCHAR
```

and converting during every join.

Repeated conversions can increase CPU usage and make indexing harder to exploit.

## CONVERT and Implicit Conversion

SQL Server can perform implicit conversions when expression types differ.

For example, comparing a numeric column with a string parameter may cause SQL Server to perform a conversion according to its type-precedence rules.

This can produce unexpected performance behavior.

Explicit conversion makes the intended boundary visible:

```sql
WHERE customer_id = CONVERT(BIGINT, @customer_id)
```

However, the better solution is usually to bind `@customer_id` using the correct type.

Prefer:

```text
Application
    ↓
Correctly typed parameter
    ↓
SQL Server
    ↓
Indexed native column
```

over:

```text
Application
    ↓
String parameter
    ↓
CONVERT(...)
    ↓
Database comparison
```

Explicit conversion is useful, but correctly typed parameters are better.

## CONVERT and Index Usage

Consider:

```sql
CREATE INDEX IX_orders_customer_id
ON orders(customer_id);
```

Prefer:

```sql
WHERE customer_id = @customer_id
```

with `@customer_id` supplied as the appropriate numeric type.

Avoid unnecessary expressions such as:

```sql
WHERE CONVERT(VARCHAR(50), customer_id) = @customer_id;
```

The latter changes the expression being evaluated against the indexed column.

If a converted representation is a legitimate business access path, SQL Server-specific options such as persisted computed columns and indexes may be appropriate.

For example:

```sql
ALTER TABLE orders
ADD customer_id_text AS CONVERT(VARCHAR(50), customer_id) PERSISTED;

CREATE INDEX IX_orders_customer_id_text
ON orders(customer_id_text);
```

This should be introduced only when there is a measured workload requirement.

## Data Migration with CONVERT

`CONVERT` is particularly useful during SQL Server schema migrations.

Suppose a legacy table contains:

```sql
customer_id VARCHAR(50)
```

but the target design requires:

```sql
customer_id BIGINT
```

First identify invalid values:

```sql
SELECT customer_id
FROM legacy_orders
WHERE customer_id IS NOT NULL
  AND TRY_CONVERT(BIGINT, customer_id) IS NULL;
```

Then inspect valid conversions:

```sql
SELECT
    customer_id,
    TRY_CONVERT(BIGINT, customer_id) AS converted_customer_id
FROM legacy_orders;
```

A safe migration sequence is:

```text
Inventory data
      ↓
Identify invalid values
      ↓
Define remediation
      ↓
Validate conversion
      ↓
Backfill
      ↓
Add constraints
      ↓
Switch application reads/writes
      ↓
Remove legacy representation
```

Do not run a large production migration using `CONVERT` without first measuring the data quality and rollback strategy.

## CONVERT and Unicode

SQL Server distinguishes between:

```sql
VARCHAR
```

and:

```sql
NVARCHAR
```

`NVARCHAR` is designed for Unicode data.

When converting application-facing text, be deliberate about the target type:

```sql
SELECT CONVERT(NVARCHAR(200), customer_name);
```

If multilingual customer or product data is possible, avoid accidentally converting Unicode text into a non-Unicode representation.

The conversion target should follow the application's actual character-set requirements.

## Formatting vs Type Conversion

One of the most important distinctions is:

```text
Type conversion
    ≠
Presentation formatting
```

For example:

```sql
CONVERT(DATE, created_at)
```

changes the data type.

Whereas:

```sql
CONVERT(VARCHAR(10), created_at, 23)
```

produces a textual representation.

Once a date has been converted to `VARCHAR`, the database no longer treats the result as a date.

That matters for:

- Sorting.
- Comparisons.
- Date arithmetic.
- Indexing.
- API serialization.

Keep values typed for as long as practical.

## Application Integration

In a Python backend using SQL Server, the preferred boundary is usually:

```text
HTTP request
    ↓
FastAPI / Django validation
    ↓
Python typed value
    ↓
Parameterized SQL
    ↓
SQL Server typed column
```

For example, an API should validate an identifier as an integer before executing:

```sql
SELECT *
FROM orders
WHERE customer_id = @customer_id;
```

rather than constructing:

```sql
WHERE customer_id = CONVERT(BIGINT, '...')
```

for every request.

`CONVERT` remains useful when the database itself must transform stored data or produce a SQL Server-specific representation.

## Security Considerations

`CONVERT` is not a SQL injection defense.

This is unsafe:

```python
query = f"""
    SELECT *
    FROM users
    WHERE user_id = CONVERT(INT, '{user_input}')
"""
```

Even though the value is passed to `CONVERT`, the input is still interpolated into SQL.

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT *
    FROM users
    WHERE user_id = ?
    """,
    [user_id],
)
```

The exact parameter placeholder depends on the Python SQL Server driver.

The security boundary should be:

```text
Untrusted input
    ↓
Validation
    ↓
Parameterized query
    ↓
Database
```

not:

```text
Untrusted input
    ↓
String concatenation
    ↓
CONVERT
```

## Performance Considerations

`CONVERT` itself is not inherently expensive.

The important factor is where and how often the conversion occurs.

| Pattern | Typical concern |
| --- | --- |
| `SELECT CONVERT(...)` on a few rows | Usually negligible |
| Conversion in a large projection | CPU overhead |
| Conversion on indexed column in `WHERE` | Potential index inefficiency |
| Conversion in large joins | CPU and join-performance impact |
| Repeated conversion of millions of rows | Potentially significant |
| Conversion during migration | CPU, locking, transaction duration |

Use execution plans to verify the actual impact.

For SQL Server:

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT *
FROM orders
WHERE CONVERT(DATE, created_at) = @target_date;
```

Also inspect the execution plan for:

- Index scans.
- Index seeks.
- Implicit conversion warnings.
- Excessive CPU.
- Large row estimates versus actual rows.
- Expensive compute scalars.

## Common Mistakes

### Treating CONVERT as Portable SQL

This:

```sql
CONVERT(VARCHAR(10), created_at, 23)
```

is SQL Server-specific.

For portable SQL, prefer standard `CAST` where formatting requirements do not require vendor-specific functionality.

### Formatting Dates Too Early

Avoid:

```sql
CONVERT(VARCHAR(10), created_at, 23)
```

when the application still needs a date.

Keep:

```sql
created_at
```

as a temporal value until the presentation boundary.

### Converting Indexed Columns

Avoid:

```sql
WHERE CONVERT(DATE, created_at) = @date
```

when a range predicate can express the same requirement:

```sql
WHERE created_at >= @start
  AND created_at < @end
```

### Using CONVERT Instead of Correct Parameter Types

Do not repeatedly convert application parameters when the database driver can send the correct type.

Correct parameter typing is usually simpler and more efficient.

### Ignoring Implicit Conversions

A query may contain no explicit `CONVERT` but still perform conversions internally.

SQL Server execution plans can expose implicit conversion warnings.

When investigating unexplained query slowness, inspect the data types of both sides of comparisons and joins.

### Using `TRY_CONVERT` to Hide Data Problems

This:

```sql
TRY_CONVERT(INT, external_id)
```

is excellent for identifying malformed data without aborting a scan.

It is not a replacement for fixing the malformed data.

Track and remediate invalid values instead of silently turning them into `NULL`.

### Choosing the Wrong Character Type

Converting Unicode data to `VARCHAR` can cause data loss when the target encoding cannot represent the source characters.

Use `NVARCHAR` when Unicode preservation is required.

## Production Best Practices

Prefer these principles when using `CONVERT`:

- Use `CONVERT` deliberately for SQL Server-specific behavior.
- Prefer `CAST` when portability is important.
- Use typed parameters rather than converting user input inside SQL.
- Keep database values in their native semantic types.
- Use date style codes only when textual formatting is genuinely required.
- Prefer ISO/unambiguous representations for machine-readable output.
- Avoid converting indexed columns in predicates.
- Investigate implicit conversion warnings in execution plans.
- Use `TRY_CONVERT` for controlled data-quality inspection and migration workflows.
- Fix permanent schema type mismatches instead of converting them on every query.
- Use `DATETIME2` or `DATETIMEOFFSET` where their semantics fit the domain.
- Keep formatting responsibilities at the appropriate application or presentation boundary.

## Interview Traps

| Interview question | Strong answer |
| --- | --- |
| What is `CONVERT`? | A SQL Server function for explicit data-type conversion |
| How is it different from `CAST`? | `CAST` is standard SQL; `CONVERT` is SQL Server-specific and supports style codes |
| What does the third `CONVERT` argument do? | It specifies a style for supported conversions, especially date/time formatting |
| What happens when `CONVERT` receives an invalid value? | It normally raises a conversion error |
| What does `TRY_CONVERT` do? | It returns `NULL` instead of raising an error for conversions it cannot perform |
| Does `CONVERT` perform timezone conversion? | No; use SQL Server timezone functionality such as `AT TIME ZONE` when appropriate |
| Why can `CONVERT` hurt index usage? | Applying it to an indexed column can make the predicate less directly searchable |
| Should application parameters be converted inside SQL? | Prefer supplying correctly typed parameters from the application |
| Is `CONVERT` portable SQL? | No; it is primarily a SQL Server-specific function |
| Why avoid converting dates to strings too early? | String values lose native temporal semantics and can complicate filtering, sorting, and arithmetic |
| When is `TRY_CONVERT` especially useful? | Data ingestion, validation, migration, and analysis of potentially malformed legacy data |
| How do you investigate conversion-related query performance issues? | Inspect execution plans, implicit conversion warnings, indexes, row counts, CPU, and logical reads |

## Key Takeaways

- `CONVERT` is a SQL Server-specific type-conversion function and is especially useful when date/time style codes are required.
- `CAST` is generally preferable for portable SQL, while `CONVERT` is appropriate when SQL Server-specific conversion behavior is valuable.
- Avoid converting indexed columns in filters and joins when a correctly typed parameter or range predicate can preserve efficient index access.
- Use `TRY_CONVERT` for controlled handling of potentially invalid data, especially during ingestion and schema migrations.
- Keep database values strongly typed and defer string formatting to the presentation boundary whenever possible.