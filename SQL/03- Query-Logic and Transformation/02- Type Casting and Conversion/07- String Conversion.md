# 07- String Conversion

## Overview

String conversion is the process of converting values between textual and non-textual SQL data types. In backend systems, this commonly occurs when database values must be returned to APIs, imported from external systems, compared with legacy columns, or combined with textual data.

Typical conversions include:

- Numeric → string
- Date/time → string
- Boolean-like values → string
- `UNIQUEIDENTIFIER` → string
- Binary → hexadecimal/base64-oriented representations
- String → numeric
- String → date/time

The important production distinction is between **data conversion** and **presentation formatting**. Converting a value to a string is sometimes necessary, but formatting a value for human display usually belongs in the application or presentation layer.

## Why String Conversion Matters

SQL is strongly typed, while external systems frequently communicate using text-based representations.

A typical request path may look like:

```mermaid
flowchart LR
    A[HTTP / JSON] --> B[Application]
    B --> C[Parameterized SQL]
    C --> D[Typed Database Values]
    D --> E[SQL Conversion]
    E --> F[Query Result]
    F --> G[API Serialization]
```

String conversion becomes important when these boundaries do not share the same representation.

For example:

```text
Database:
DECIMAL(19,4)

        ↓ conversion

SQL result:
VARCHAR

        ↓ serialization

API:
"1999.9500"
```

Whether the final API value should actually be a JSON number or a string is an API contract decision. SQL conversion should not be used merely because the frontend expects a particular display format.

## CAST to String Types

The standard approach is `CAST`:

```sql
SELECT CAST(order_id AS VARCHAR(50))
FROM orders;
```

You can also specify a bounded character type:

```sql
SELECT CAST(customer_name AS VARCHAR(200))
FROM customers;
```

For Unicode text:

```sql
SELECT CAST(customer_name AS NVARCHAR(200))
FROM customers;
```

Use `NVARCHAR` when the data can contain Unicode characters that must be preserved.

## VARCHAR vs NVARCHAR

In SQL Server, the choice between `VARCHAR` and `NVARCHAR` matters.

| Type | Character representation | Typical use |
| --- | --- | --- |
| `VARCHAR` | Non-Unicode code page | Known non-Unicode data |
| `NVARCHAR` | Unicode | Multilingual/user-generated text |
| `CHAR` | Fixed-length non-Unicode | Fixed-width values |
| `NCHAR` | Fixed-length Unicode | Fixed-width Unicode values |

For general user-facing text, `NVARCHAR` is usually the safer choice when Unicode support is required.

For example:

```sql
SELECT CAST(customer_name AS NVARCHAR(200))
FROM customers;
```

Do not arbitrarily convert Unicode data to `VARCHAR`, because characters outside the target code page may be lost or replaced.

## Numeric to String Conversion

Numeric values can be converted to text using `CAST` or `CONVERT`:

```sql
SELECT CAST(total_amount AS VARCHAR(50))
FROM orders;
```

or:

```sql
SELECT CONVERT(VARCHAR(50), total_amount)
FROM orders;
```

This is useful when a numeric value needs to participate in a textual expression.

For example:

```sql
SELECT
    'Order #' + CAST(order_id AS VARCHAR(20)) AS order_reference
FROM orders;
```

The database value remains numeric in storage, while the derived expression is textual.

## Decimal Precision During String Conversion

Converting a decimal to a string preserves the decimal representation according to the source value and target conversion rules.

For example:

```sql
SELECT CAST(total_amount AS VARCHAR(50))
FROM orders;
```

If the application requires a specific number of decimal places, define that representation intentionally rather than assuming string conversion is formatting.

For example:

```sql
SELECT
    CAST(CAST(total_amount AS DECIMAL(19, 2)) AS VARCHAR(50))
FROM orders;
```

This first establishes the numeric scale and then converts the value to text.

However, for API responses, it is generally preferable to keep the value numeric and let the serialization layer determine the representation.

## Integer to String Conversion

Integer identifiers are frequently converted to strings when constructing references.

```sql
SELECT
    'ORD-' + CAST(order_id AS VARCHAR(20)) AS order_reference
FROM orders;
```

This is useful for derived labels:

```text
ORD-102481
ORD-102482
ORD-102483
```

Do not change the underlying `order_id` column to a string merely because a presentation-level identifier contains a prefix.

Keep:

```text
order_id → BIGINT
```

and derive:

```text
order_reference → VARCHAR
```

when appropriate.

## Date and Time to String Conversion

Date/time values often need conversion when integrating with systems that require textual representations.

Using `CONVERT`:

```sql
SELECT
    CONVERT(VARCHAR(19), created_at, 120) AS created_at_text
FROM orders;
```

Style `120` produces a representation similar to:

```text
2026-08-30 14:35:12
```

For machine-to-machine communication, prefer an unambiguous standard representation.

For example, ISO 8601-oriented output is generally preferable to locale-dependent formats.

Avoid formats such as:

```text
08/30/2026
30/08/2026
08-30-26
```

when the value crosses system boundaries without an explicit contract.

## CONVERT Styles

SQL Server's `CONVERT` supports style codes for certain conversions, particularly date/time and binary representations.

Example:

```sql
SELECT
    CONVERT(VARCHAR(10), created_at, 23) AS created_date
FROM orders;
```

This produces:

```text
2026-08-30
```

Common date-oriented styles include:

| Style | Typical representation |
| --- | --- |
| `23` | `yyyy-mm-dd` |
| `120` | `yyyy-mm-dd hh:mi:ss` |
| `121` | `yyyy-mm-dd hh:mi:ss.mmm` |

The exact supported output depends on the source and target types.

Style codes are SQL Server-specific, so do not treat them as portable SQL syntax.

## FORMAT for String Output

SQL Server's `FORMAT()` can create presentation-oriented strings.

For example:

```sql
SELECT
    FORMAT(total_amount, 'N2') AS formatted_amount
FROM orders;
```

This can be convenient when producing human-readable reports.

However, `FORMAT()` is generally more expensive than simple `CAST`/`CONVERT` operations and relies on .NET formatting behavior.

Use it selectively rather than as the default conversion mechanism for large production queries.

For large result sets:

```text
CAST / CONVERT
    ↓
Usually preferred for straightforward conversion

FORMAT
    ↓
Use when rich culture-aware presentation formatting is actually required
```

## String Concatenation

String conversion is often required when combining different data types.

For example:

```sql
SELECT
    'Customer ' +
    CAST(customer_id AS VARCHAR(20)) +
    ': ' +
    customer_name AS customer_label
FROM customers;
```

The integer `customer_id` must be converted before concatenation with character data.

For more complex expressions, explicit conversion keeps the result type predictable.

## CONCAT and Implicit Conversion

SQL Server provides `CONCAT()` for string construction:

```sql
SELECT
    CONCAT('Customer ', customer_id, ': ', customer_name)
FROM customers;
```

`CONCAT()` handles conversion of arguments to strings automatically.

This can be cleaner than manually using `CAST` and the `+` operator.

It also has important `NULL` behavior differences compared with ordinary string concatenation.

For example:

```sql
SELECT 'Customer ' + NULL;
```

can produce `NULL`, while:

```sql
SELECT CONCAT('Customer ', NULL);
```

treats the `NULL` argument as an empty string.

Choose the behavior intentionally.

## NULL and String Conversion

`CAST(NULL AS VARCHAR(50))` remains `NULL`:

```sql
SELECT CAST(NULL AS VARCHAR(50));
```

Conversion does not turn `NULL` into an empty string.

If the application requires a fallback:

```sql
SELECT COALESCE(
    CAST(reference_code AS VARCHAR(50)),
    ''
)
FROM orders;
```

But distinguish between:

```text
NULL
```

and:

```text
''
```

They represent different states.

A `NULL` may mean:

> Value is unknown or not provided.

An empty string may mean:

> Value is known to contain no characters.

Do not collapse these states without a business reason.

## Safe String-to-Numeric Conversion

The reverse direction is also common.

External systems may provide:

```text
"1250"
"1999.95"
"42.75"
```

Convert them explicitly:

```sql
SELECT CAST(raw_amount AS DECIMAL(19, 4))
FROM payment_import;
```

If malformed data is possible:

```sql
SELECT TRY_CAST(raw_amount AS DECIMAL(19, 4))
FROM payment_import;
```

For example:

```text
"1999.95" → 1999.9500
"invalid" → NULL
```

`TRY_CAST` prevents a single malformed value from causing the entire conversion expression to fail.

However, production ingestion systems should also monitor failed conversions rather than silently accepting `NULL`.

## String-to-Date Conversion

External systems often provide dates as strings.

Prefer an unambiguous input format:

```sql
SELECT TRY_CONVERT(
    DATE,
    raw_date,
    23
) AS parsed_date
FROM import_rows;
```

If `raw_date` contains:

```text
2026-08-30
```

the conversion is deterministic.

Avoid relying on ambiguous strings such as:

```text
08/30/2026
30/08/2026
```

unless the input format is explicitly defined and the conversion logic matches it.

## Avoid Locale-Dependent Parsing

Machine-generated data should use an explicit format.

Bad:

```sql
CAST('08/30/2026' AS DATE)
```

The interpretation can depend on context and conversion rules.

Prefer:

```sql
TRY_CONVERT(DATE, '2026-08-30', 23)
```

The explicit format communicates the intended representation.

This is especially important in distributed systems where services may run with different locale or language configurations.

## Conversion in WHERE Clauses

Avoid converting the database column when the parameter can instead be converted.

Suppose:

```sql
CREATE INDEX IX_orders_order_id
ON orders(order_id);
```

Avoid:

```sql
SELECT *
FROM orders
WHERE CAST(order_id AS VARCHAR(50)) = @order_id;
```

Prefer:

```sql
SELECT *
FROM orders
WHERE order_id = TRY_CAST(@order_id AS BIGINT);
```

The second form keeps the indexed column in its native type.

This generally gives the optimizer a better opportunity to use an index efficiently.

The preferred flow is:

```mermaid
flowchart LR
    A[String Request Parameter] --> B[Validate / Convert Parameter]
    B --> C[Typed BIGINT Parameter]
    C --> D[Indexed order_id]
    D --> E[Index Seek]
```

rather than:

```mermaid
flowchart LR
    A[String Parameter] --> B[Convert Every order_id]
    B --> C[Predicate Evaluation]
    C --> D[Potential Scan]
```

Actual access paths depend on the optimizer, statistics, schema, and query shape, but unnecessary conversions on indexed columns are a common performance smell.

## Conversion in JOIN Conditions

The same principle applies to joins.

Avoid:

```sql
SELECT ...
FROM orders o
JOIN legacy_orders l
    ON CAST(o.order_id AS VARCHAR(50)) = l.order_id;
```

If `legacy_orders.order_id` is textual because of a legacy design, consider converting the legacy value where safe:

```sql
SELECT ...
FROM orders o
JOIN legacy_orders l
    ON o.order_id = TRY_CAST(l.order_id AS BIGINT);
```

However, converting a large legacy table can still be expensive.

For frequently executed joins, a better long-term approach may be:

- Align the schema types.
- Introduce a persisted normalized column.
- Backfill clean data.
- Add an appropriate index.
- Migrate consumers away from the legacy representation.

Do not repeatedly pay conversion costs in every production request if the mismatch can be eliminated architecturally.

## Persisted Computed Columns

When a conversion is unavoidable but frequently queried, a computed column can sometimes provide a better design.

For example:

```sql
ALTER TABLE legacy_orders
ADD order_id_numeric AS TRY_CONVERT(BIGINT, order_id);
```

If the workload and SQL Server configuration support the intended indexing strategy, this can allow the normalized representation to be indexed.

The broader principle is:

> **Normalize expensive repeated transformations when they are part of a stable access pattern.**

Do not add computed columns solely to avoid a small conversion cost. Verify the workload and execution plan first.

## String Length and Truncation

Always choose an appropriate target length.

For example:

```sql
CAST(order_id AS VARCHAR(20))
```

is appropriate only if the converted representation fits within that limit.

Avoid arbitrary small sizes:

```sql
CAST(order_id AS VARCHAR(5))
```

A conversion that truncates meaningful information can corrupt identifiers.

For fixed-size output contracts, explicitly verify the maximum possible representation.

## CHAR vs VARCHAR During Conversion

`CHAR(n)` is fixed-length, while `VARCHAR(n)` is variable-length.

For derived strings, prefer `VARCHAR` unless fixed-width output is required.

For example:

```sql
SELECT CAST(order_id AS VARCHAR(20))
FROM orders;
```

is generally more appropriate than:

```sql
SELECT CAST(order_id AS CHAR(20))
FROM orders;
```

Fixed-width types can introduce padding behavior that becomes inconvenient when values are concatenated, compared, or serialized.

## GUID / UNIQUEIDENTIFIER Conversion

Identifiers stored as `UNIQUEIDENTIFIER` may need to be exposed as strings.

```sql
SELECT CAST(order_id AS VARCHAR(36))
FROM orders;
```

A standard GUID textual representation is typically 36 characters including hyphens.

For API responses, however, most application serializers can convert UUID/GUID values without requiring SQL to turn them into strings manually.

Prefer preserving the native type until the actual serialization boundary when possible.

## Binary to String Conversion

Binary values sometimes need textual representations for logs, integrations, or transport.

SQL Server `CONVERT` supports styles for binary-to-character conversions.

For example:

```sql
SELECT
    CONVERT(VARCHAR(100), binary_value, 2)
FROM encrypted_values;
```

The exact representation depends on the conversion style.

Be careful with sensitive binary data. Converting encrypted values, hashes, tokens, or credentials into logs can create a security incident even when the conversion itself is technically correct.

## Conversion and API Design

A database should generally return semantic values rather than presentation-specific strings.

Prefer:

```sql
SELECT
    order_id,
    total_amount,
    created_at
FROM orders;
```

over:

```sql
SELECT
    CAST(order_id AS VARCHAR(20)) AS order_id,
    FORMAT(total_amount, 'N2') AS total_amount,
    CONVERT(VARCHAR(19), created_at, 120) AS created_at
FROM orders;
```

The first query preserves type information.

The application layer can then serialize:

```json
{
  "order_id": 102481,
  "total_amount": 1999.95,
  "created_at": "2026-08-30T14:35:12Z"
}
```

This separation improves reuse because the same database query can support:

- REST APIs.
- gRPC services.
- Background jobs.
- Internal reports.
- Data exports.

## Production Example: Legacy Import

Suppose a legacy payment system stores amounts as strings:

```text
payment_id | amount_text
-----------+-----------
1001       | 1999.95
1002       | 875.50
1003       | INVALID
```

A safe staging query can identify valid and invalid records:

```sql
SELECT
    payment_id,
    amount_text,
    TRY_CAST(amount_text AS DECIMAL(19, 4)) AS amount
FROM legacy_payments;
```

Then invalid records can be isolated:

```sql
SELECT
    payment_id,
    amount_text
FROM legacy_payments
WHERE amount_text IS NOT NULL
  AND TRY_CAST(amount_text AS DECIMAL(19, 4)) IS NULL;
```

This separates:

```text
Parsing
    ↓
Validation
    ↓
Normalization
    ↓
Business processing
```

rather than allowing malformed input to reach the financial calculation layer.

## Production Example: API Reference

Suppose an order has:

```sql
order_id BIGINT
```

and the API requires a human-readable reference:

```text
ORD-102481
```

The database can derive it:

```sql
SELECT
    order_id,
    CONCAT('ORD-', order_id) AS order_reference
FROM orders;
```

This is reasonable when the reference is a simple deterministic projection.

If the reference is part of the domain identity, uniqueness, or security model, it should instead be modeled explicitly rather than treated as a display-only conversion.

## Performance Considerations

String conversion can become expensive when applied to large datasets.

Be cautious with:

```sql
SELECT
    FORMAT(amount, 'N2')
FROM large_table;
```

especially when millions of rows are returned.

Potential issues include:

- Increased CPU usage.
- Larger result payloads.
- Reduced index usability when conversion occurs in predicates.
- Expensive formatting operations.
- Increased memory pressure during large transformations.
- Unnecessary database work that could be performed by the application.

For high-volume queries:

```text
Native typed value
    ↓
Database
    ↓
Application serializer
```

is generally preferable to:

```text
Native typed value
    ↓
Database formatting
    ↓
Large textual result
    ↓
Application
```

Measure with the actual execution plan and runtime statistics rather than assuming every conversion is expensive.

## Security Considerations

String conversion can expose sensitive values.

Avoid logging or returning:

- Password hashes.
- Access tokens.
- Session identifiers.
- Encryption keys.
- Sensitive personal information.
- Raw binary credentials.
- Internal security metadata.

For example, this query may be technically valid but operationally dangerous:

```sql
SELECT CONVERT(VARCHAR(200), encrypted_secret, 2)
FROM credentials;
```

A conversion does not make sensitive data safe to expose.

Also avoid dynamic SQL based on converted user input. Parameterize values at the application/database driver boundary.

## Common Mistakes

### Formatting in SQL by Default

Bad:

```sql
SELECT FORMAT(total_amount, 'N2')
FROM orders;
```

for a high-volume API endpoint.

Prefer returning the numeric value and formatting it at the presentation boundary.

### Converting Indexed Columns

Bad:

```sql
WHERE CAST(order_id AS VARCHAR(50)) = @order_id
```

Prefer converting the input:

```sql
WHERE order_id = TRY_CAST(@order_id AS BIGINT)
```

### Using Ambiguous Date Strings

Bad:

```sql
CAST('08/30/2026' AS DATE)
```

Prefer an explicit machine-readable format:

```sql
TRY_CONVERT(DATE, '2026-08-30', 23)
```

### Using VARCHAR for Unicode Data

Bad:

```sql
CAST(customer_name AS VARCHAR(200))
```

when Unicode characters must be preserved.

Prefer:

```sql
CAST(customer_name AS NVARCHAR(200))
```

when the target system requires Unicode.

### Converting NULL to Empty String Unnecessarily

Bad:

```sql
COALESCE(CAST(reference_code AS VARCHAR(50)), '')
```

when `NULL` carries meaningful domain semantics.

Do this only when the consumer explicitly requires an empty string.

### Using FORMAT for Large Data Sets

`FORMAT()` is convenient but can be significantly more expensive than simpler conversion operations.

Use it for appropriate presentation-oriented workloads rather than large transactional queries.

### Arbitrary String Lengths

Bad:

```sql
CAST(order_id AS VARCHAR(5))
```

if the identifier can exceed five characters.

Choose the target length based on the domain's maximum representation.

### Converting Data Repeatedly Instead of Fixing the Schema

If every query contains:

```sql
TRY_CAST(legacy_id AS BIGINT)
```

the real problem may be schema inconsistency.

For high-frequency workloads, consider normalizing the stored representation.

## Production Guidelines

| Situation | Preferred approach |
| --- | --- |
| Numeric → simple string | `CAST` / `CONVERT` |
| Date → machine-readable string | `CONVERT` with explicit style where appropriate |
| Rich human formatting | Application layer or carefully scoped `FORMAT()` |
| Potentially invalid string → numeric | `TRY_CAST` / `TRY_CONVERT` |
| Predicate against indexed numeric column | Convert the parameter, not the column |
| Unicode text | `NVARCHAR` |
| API response | Preserve semantic types when possible |
| Large result sets | Avoid unnecessary formatting in SQL |
| Legacy string identifiers | Normalize types where practical |
| Sensitive binary values | Avoid unnecessary conversion/logging |

## Interview Traps

| Question | Strong answer |
| --- | --- |
| Why convert a parameter instead of an indexed column? | It preserves the column's native type and gives the optimizer a better chance of using the index efficiently |
| `CAST` vs `CONVERT` in SQL Server? | Both perform conversion; `CONVERT` adds SQL Server-specific features such as style codes |
| When should `FORMAT()` be avoided? | Especially in high-volume queries where simple conversion or application-level formatting is sufficient |
| What does `TRY_CAST()` do with invalid input? | Returns `NULL` instead of raising a conversion error |
| Does `CAST(NULL AS VARCHAR(20))` produce an empty string? | No; it remains `NULL` |
| Why can `VARCHAR` be unsafe for international text? | It may not preserve characters outside the applicable code page |
| Why avoid formatting dates with locale-dependent strings? | Different environments can interpret ambiguous representations differently |
| Should an API identifier always be converted to a string in SQL? | No; preserve the native type unless the API contract explicitly requires textual representation |
| Why can repeated conversion indicate a schema problem? | Frequent runtime normalization often means systems are storing equivalent data using incompatible types |
| Is string conversion itself a security control? | No; converting sensitive data to text does not make it safe to expose or log |

## Key Takeaways

- **Use `CAST` or `CONVERT` for straightforward type conversion, but separate conversion from presentation formatting.**
- **Preserve native database types through query execution whenever possible**, especially for API and service-to-service data flows.
- **Avoid conversions on indexed columns in predicates and joins**; convert parameters or normalize incompatible schemas instead.
- **Use explicit, unambiguous representations for machine-to-machine dates and numeric data**, and use `TRY_CAST`/`TRY_CONVERT` when malformed external input is possible.
- **Treat string conversion as a data-boundary concern, not a reason to weaken type safety, precision, Unicode handling, performance, or security.**