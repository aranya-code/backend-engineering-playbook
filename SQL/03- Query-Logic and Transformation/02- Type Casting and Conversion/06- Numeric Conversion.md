# 06- Numeric Conversion

## Overview

Numeric conversion in SQL is the explicit or implicit transformation of values between numeric data types such as `INT`, `BIGINT`, `DECIMAL`, `NUMERIC`, `FLOAT`, and numeric-compatible string types.

In production backend systems, numeric conversion matters because the chosen data type affects:

- Precision and rounding.
- Overflow behavior.
- Arithmetic results.
- Integer division.
- Index usage.
- Storage requirements.
- API serialization.
- Financial correctness.
- Query performance.

The most important rule is:

> **Choose the numeric type based on the business meaning of the value, then convert explicitly when crossing type boundaries.**

For SQL Server, the common numeric types can be broadly viewed as:

| Type | Typical use | Precision characteristics |
| --- | --- | --- |
| `TINYINT` | Small non-negative integers | Exact |
| `SMALLINT` | Small integer values | Exact |
| `INT` | General-purpose integers | Exact |
| `BIGINT` | Large identifiers/counters | Exact |
| `DECIMAL` / `NUMERIC` | Money, measurements requiring exact precision | Exact |
| `FLOAT` | Scientific/statistical calculations | Approximate |
| `REAL` | Lower-precision approximate calculations | Approximate |
| `MONEY` / `SMALLMONEY` | Currency values in legacy SQL Server systems | Fixed precision |

Conversion is not merely a syntax concern. A conversion can change the mathematical meaning of a value.

## Numeric Type Families

### Exact Integer Types

SQL Server provides:

```text
TINYINT
SMALLINT
INT
BIGINT
```

They represent whole numbers exactly.

For example:

```sql
DECLARE @order_count INT = 1250;
DECLARE @event_count BIGINT = 9000000000;
```

Use the smallest type that safely accommodates the domain, but avoid premature optimization. `INT` is usually the default integer type for ordinary application data, while `BIGINT` is common for high-volume identifiers, event counters, and monotonically increasing values that may exceed the `INT` range.

### Exact Decimal Types

`DECIMAL(p, s)` and `NUMERIC(p, s)` represent exact decimal numbers.

```text
p = total number of significant decimal digits
s = number of digits to the right of the decimal point
```

For example:

```sql
DECIMAL(12, 2)
```

can represent values with up to 12 total digits, including 2 fractional digits.

A value such as:

```text
1234567890.12
```

fits within `DECIMAL(12, 2)`.

For financial values, exact decimal types are generally preferable to floating-point types.

### Approximate Numeric Types

`FLOAT` and `REAL` store approximate numeric values.

They are useful for domains such as:

- Scientific calculations.
- Statistical models.
- Measurements where approximation is acceptable.
- Large ranges of values where exact decimal representation is unnecessary.

They should generally not be used for monetary amounts where exact decimal semantics are required.

## Explicit Numeric Conversion

Use `CAST` when you need standard SQL conversion syntax:

```sql
SELECT CAST(quantity AS BIGINT)
FROM order_items;
```

Use `CONVERT` when SQL Server-specific behavior is useful:

```sql
SELECT CONVERT(BIGINT, quantity)
FROM order_items;
```

For numeric conversion, these are often equivalent:

```sql
CAST(amount AS DECIMAL(12, 2))
```

and:

```sql
CONVERT(DECIMAL(12, 2), amount)
```

The important difference is not the function itself but the target type and its precision.

## Converting Integers

A common conversion is widening an integer:

```sql
SELECT CAST(order_id AS BIGINT)
FROM orders;
```

This is useful when an expression needs to operate in a larger integer range.

For example:

```sql
DECLARE @a INT = 2000000000;
DECLARE @b INT = 2000000000;

SELECT CAST(@a AS BIGINT) + @b;
```

Casting one operand to `BIGINT` causes the arithmetic expression to operate using a larger integer type.

This can prevent overflow.

## Integer Overflow

Integer arithmetic can overflow even when the final intended result would fit into a larger type.

Consider:

```sql
DECLARE @a INT = 2000000000;
DECLARE @b INT = 2000000000;

SELECT @a + @b;
```

The operands are `INT`, so the addition is evaluated using integer arithmetic and can exceed the `INT` range.

Prefer:

```sql
SELECT CAST(@a AS BIGINT) + @b;
```

The conversion must happen **before** the arithmetic operation.

This distinction is important:

```sql
CAST(@a + @b AS BIGINT)
```

may be too late because the addition can overflow before the result is cast.

Prefer:

```sql
CAST(@a AS BIGINT) + @b
```

when the calculation itself requires a wider type.

## Decimal Precision and Scale

Decimal conversion requires deliberate precision and scale selection.

```sql
SELECT CAST(123.4567 AS DECIMAL(10, 2));
```

The result is represented using two decimal places.

A production system should define the required precision based on domain constraints rather than simply using a convenient value such as `DECIMAL(10, 2)` everywhere.

Examples:

| Domain | Possible type |
| --- | --- |
| Product quantity | `DECIMAL(12, 3)` |
| Currency amount | `DECIMAL(19, 4)` |
| Percentage | `DECIMAL(7, 4)` |
| Large financial total | `DECIMAL(19, 4)` |
| Integer count | `INT` or `BIGINT` |

These are examples, not universal rules. The correct precision and scale depend on the application's maximum values and required accuracy.

## Scale Reduction

When converting to a decimal with fewer fractional digits, SQL Server must reconcile the difference.

For example:

```sql
SELECT CAST(123.456 AS DECIMAL(10, 2));
```

The resulting value has only two fractional digits.

Do not use type conversion as a substitute for an explicit business rounding policy.

If the requirement is:

> Round the price to two decimal places.

make the intent explicit:

```sql
SELECT CAST(ROUND(price, 2) AS DECIMAL(12, 2))
FROM products;
```

Conversion controls the target representation; `ROUND()` communicates a rounding operation.

## Decimal to Integer Conversion

Converting a decimal to an integer removes the fractional component.

```sql
SELECT CAST(123.99 AS INT);
```

This produces:

```text
123
```

It does not mean:

```text
124
```

If the business rule requires nearest-integer rounding, use:

```sql
SELECT ROUND(123.99, 0);
```

followed by conversion if an integer type is required.

```sql
SELECT CAST(ROUND(123.99, 0) AS INT);
```

The distinction is:

```text
CAST
  ↓
Change representation/type

ROUND
  ↓
Apply a rounding rule
```

## Numeric String Conversion

External systems frequently provide numeric values as strings.

For example:

```text
"1250"
"1999.95"
"0.8525"
```

A staging pipeline can convert them into typed values:

```sql
SELECT
    TRY_CAST(raw_amount AS DECIMAL(19, 4)) AS amount
FROM payment_import;
```

`TRY_CAST` is particularly useful when the input may contain invalid records.

Invalid input produces `NULL` instead of terminating the query with a conversion error.

For SQL Server-specific conversion:

```sql
SELECT
    TRY_CONVERT(DECIMAL(19, 4), raw_amount) AS amount
FROM payment_import;
```

## CAST vs TRY_CAST

| Function | Invalid conversion |
| --- | --- |
| `CAST` | Raises an error |
| `TRY_CAST` | Returns `NULL` |
| `CONVERT` | Raises an error |
| `TRY_CONVERT` | Returns `NULL` |

For trusted application data, `CAST` can be appropriate.

For external or dirty data, `TRY_CAST` or `TRY_CONVERT` is often safer.

However, silently turning invalid data into `NULL` can hide data-quality problems. Production ingestion pipelines should usually capture and monitor rejected values separately.

## Numeric Division

Numeric conversion is especially important for division.

Consider:

```sql
SELECT 5 / 2;
```

With integer operands, the result is integer division.

To obtain a decimal result:

```sql
SELECT CAST(5 AS DECIMAL(10, 2)) / 2;
```

or:

```sql
SELECT 5.0 / 2;
```

For production queries, explicit conversion communicates intent more clearly:

```sql
SELECT
    CAST(completed_orders AS DECIMAL(12, 4))
    / NULLIF(total_orders, 0) AS completion_rate
FROM order_metrics;
```

This also protects against division by zero.

## Percentage Calculations

A common backend reporting query calculates percentages.

Avoid:

```sql
SELECT
    completed_orders / total_orders * 100 AS completion_percentage
FROM order_metrics;
```

If both columns are integers, integer division can produce an incorrect result.

Prefer:

```sql
SELECT
    CAST(completed_orders AS DECIMAL(12, 4))
    / NULLIF(total_orders, 0) * 100 AS completion_percentage
FROM order_metrics;
```

The data flow is:

```text
Integer counts
     ↓
Explicit decimal conversion
     ↓
Decimal division
     ↓
Percentage calculation
     ↓
API / report
```

This pattern is common in:

- Analytics APIs.
- Dashboard queries.
- Monitoring metrics.
- Business reports.
- Service-level calculations.

## NULLIF for Safe Division

When the denominator can be zero:

```sql
SELECT
    CAST(success_count AS DECIMAL(12, 4))
    / NULLIF(total_count, 0) AS success_rate
FROM metrics;
```

`NULLIF(total_count, 0)` converts a zero denominator into `NULL`.

The result becomes `NULL` instead of raising a division-by-zero error.

If the API contract requires a fallback:

```sql
SELECT
    COALESCE(
        CAST(success_count AS DECIMAL(12, 4))
        / NULLIF(total_count, 0),
        0
    ) AS success_rate
FROM metrics;
```

The fallback should be chosen according to business semantics. A missing denominator is not always equivalent to a zero success rate.

## Implicit Numeric Conversion

SQL Server can implicitly convert compatible numeric values.

For example:

```sql
SELECT
    CAST(10 AS INT) + CAST(2.5 AS DECIMAL(10, 2));
```

SQL Server determines a result type based on its data type precedence and numeric precision/scale rules.

This can be convenient, but relying heavily on implicit conversion makes complex expressions harder to reason about.

Prefer explicit conversion when:

- Precision matters.
- Division is involved.
- Arithmetic crosses integer and decimal types.
- External input is involved.
- API output must have a defined type.
- Overflow is possible.

## Data Type Precedence

SQL Server assigns precedence to data types.

When expressions contain different types, SQL Server may implicitly convert the lower-precedence type to the higher-precedence type.

This matters because implicit conversions can:

- Change the result type.
- Affect precision.
- Cause conversion errors.
- Increase CPU work.
- Affect index access when conversions occur in predicates.

For example, do not assume that comparing a string column with an integer parameter is harmless:

```sql
WHERE external_id = @integer_parameter
```

If the types are mismatched, inspect the resulting execution plan and align the parameter type with the database column whenever possible.

## Conversion and Indexes

Suppose:

```sql
CREATE INDEX IX_orders_customer_id
ON orders(customer_id);
```

Avoid converting the indexed column unnecessarily:

```sql
SELECT *
FROM orders
WHERE CAST(customer_id AS VARCHAR(50)) = @customer_id;
```

Prefer:

```sql
SELECT *
FROM orders
WHERE customer_id = @customer_id;
```

with `@customer_id` declared using the same type as `customer_id`.

If the input arrives as text, convert the input before executing the query rather than forcing every indexed row through a conversion.

The preferred pattern is:

```text
HTTP request
    ↓
Application validation
    ↓
Typed parameter
    ↓
SQL predicate
    ↓
Index seek
```

rather than:

```text
HTTP request
    ↓
String parameter
    ↓
Convert database column
    ↓
Potentially inefficient access
```

## Numeric Conversion in Aggregations

Keep values numeric during aggregation.

Prefer:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_amount,
    AVG(amount) AS average_amount
FROM payments
GROUP BY customer_id;
```

If a particular numeric type is required:

```sql
SELECT
    customer_id,
    CAST(SUM(amount) AS DECIMAL(19, 4)) AS total_amount
FROM payments
GROUP BY customer_id;
```

Do not convert numeric values to strings before aggregation.

Bad:

```sql
SUM(CAST(amount AS VARCHAR(50)))
```

The aggregation should operate on numeric values.

## Aggregate Overflow

Aggregation can create a result larger than the source column's range.

For high-volume counters, consider widening the expression before aggregation.

For example:

```sql
SELECT
    SUM(CAST(event_count AS BIGINT)) AS total_events
FROM service_metrics;
```

This is especially relevant when:

- Aggregating large event counts.
- Summing historical records.
- Processing telemetry.
- Calculating financial totals.
- Running warehouse/reporting queries.

The principle is the same as arithmetic overflow:

> **Widen the type before the operation that may exceed the original type's range.**

## FLOAT vs DECIMAL Conversion

Converting between approximate and exact numeric types requires care.

For example:

```sql
SELECT CAST(float_value AS DECIMAL(19, 6))
FROM measurements;
```

The decimal value is exact relative to the converted representation, but the original `FLOAT` value was approximate.

Therefore:

```text
FLOAT → DECIMAL
```

does not recover precision that was never present in the original floating-point representation.

For financial systems, avoid using `FLOAT` as the primary storage type and converting it to `DECIMAL` later.

Prefer storing the value using an appropriate exact decimal type from the beginning.

## Money and Numeric Types

SQL Server supports `MONEY` and `SMALLMONEY`.

These types can be convenient in legacy systems, but many modern application schemas prefer `DECIMAL`/`NUMERIC` because precision and scale are explicit.

For example:

```sql
amount DECIMAL(19, 4)
```

makes the numeric contract visible in the schema.

For new financial schemas, choose the representation based on:

- Required precision.
- Maximum amount.
- Currency rules.
- Tax calculations.
- Exchange-rate calculations.
- External accounting requirements.

Do not select a type simply because its name contains `MONEY`.

## Conversion in CASE Expressions

`CASE` expressions containing different numeric types can cause SQL Server to determine a common result type.

For example:

```sql
SELECT
    CASE
        WHEN status = 'paid' THEN amount
        ELSE 0
    END AS normalized_amount
FROM payments;
```

A better pattern is to ensure the branches have compatible intended types:

```sql
SELECT
    CASE
        WHEN status = 'paid'
            THEN CAST(amount AS DECIMAL(19, 4))
        ELSE CAST(0 AS DECIMAL(19, 4))
    END AS normalized_amount
FROM payments;
```

This is useful when downstream consumers depend on a predictable numeric type.

Avoid returning strings from one branch and numbers from another unless the output is intentionally textual.

## Conversion with COALESCE

`COALESCE` can also influence the resulting data type.

Prefer:

```sql
SELECT
    COALESCE(
        amount,
        CAST(0 AS DECIMAL(19, 4))
    ) AS amount
FROM payments;
```

when `amount` has a known decimal contract.

This is clearer than relying on implicit conversion of a literal:

```sql
COALESCE(amount, 0)
```

For simple expressions the latter may work correctly, but explicit typing is useful when precision and scale matter.

## Conversion and Application Layers

A typical backend system has multiple numeric boundaries:

```mermaid
flowchart LR
    A[HTTP / JSON Input] --> B[Application Validation]
    B --> C[Typed SQL Parameter]
    C --> D[Database Numeric Type]
    D --> E[SQL Calculation]
    E --> F[Typed Query Result]
    F --> G[API Serialization]
```

For example, a FastAPI service may receive:

```json
{
  "quantity": 12,
  "unit_price": 19.95
}
```

The application should validate the values and pass parameters using appropriate database-compatible types.

The database should perform authoritative calculations using appropriate numeric types rather than relying on string manipulation.

For financial APIs, preserve semantic information:

```json
{
  "amount": 1999.95,
  "currency": "USD"
}
```

rather than:

```json
{
  "amount": "$1,999.95"
}
```

The second representation is presentation-oriented and should generally be produced at the UI/reporting boundary.

## Production Example: Order Totals

Suppose an order contains:

```text
quantity × unit_price
```

A robust query can make the numeric contract explicit:

```sql
SELECT
    order_id,
    SUM(
        CAST(quantity AS DECIMAL(19, 4))
        * unit_price
    ) AS subtotal
FROM order_items
GROUP BY order_id;
```

If discounts and tax are also involved:

```sql
SELECT
    order_id,
    CAST(
        SUM(
            CAST(quantity AS DECIMAL(19, 4))
            * unit_price
        )
        * (1 - discount_rate)
        AS DECIMAL(19, 4)
    ) AS discounted_subtotal
FROM order_items
GROUP BY order_id;
```

The exact precision and business rounding policy should be defined by the financial domain rather than copied blindly from this example.

## Production Example: Metrics

Suppose an observability system stores:

```sql
CREATE TABLE service_metrics (
    service_id BIGINT NOT NULL,
    total_requests BIGINT NOT NULL,
    failed_requests BIGINT NOT NULL
);
```

A failure rate can be calculated as:

```sql
SELECT
    service_id,
    CAST(failed_requests AS DECIMAL(12, 6))
    / NULLIF(total_requests, 0) AS failure_rate
FROM service_metrics;
```

This keeps the calculation numeric and avoids integer division.

The API can then serialize:

```json
{
  "service_id": 42,
  "failure_rate": 0.012500
}
```

A dashboard can decide whether to display that value as:

```text
1.25%
```

The database does not need to convert the metric into a presentation string.

## Performance Considerations

Numeric conversion itself is usually inexpensive, but conversion becomes operationally important when performed across millions of rows or inside hot predicates.

Watch for:

- Conversion on indexed columns.
- Repeated conversions in large scans.
- Implicit conversions.
- Large `DECIMAL` arithmetic.
- Unnecessary string conversion.
- Formatting during data retrieval.
- Conversion inside joins.
- Conversion inside aggregation pipelines.

For SQL Server, inspect actual execution plans and runtime metrics.

Useful diagnostics include:

```sql
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
```

Look for:

- High logical reads.
- Increased CPU time.
- Index scans where seeks were expected.
- Implicit conversion warnings.
- Unexpected cardinality estimates.

## Security Considerations

Numeric conversion is not a substitute for input validation or SQL parameterization.

Do not construct SQL dynamically from numeric input:

```python
query = f"""
    SELECT *
    FROM orders
    WHERE customer_id = {customer_id}
"""
```

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT order_id, total_amount
    FROM orders
    WHERE customer_id = ?
    """,
    [customer_id],
)
```

The application should also validate domain constraints before executing the query:

```text
Request
  ↓
Type validation
  ↓
Range validation
  ↓
Parameterized query
  ↓
Database constraints
```

Database constraints remain important because not every write necessarily passes through the same application path.

## Common Mistakes

### Performing Arithmetic Before Widening the Type

Bad:

```sql
CAST(a + b AS BIGINT)
```

if `a + b` can overflow as `INT`.

Prefer:

```sql
CAST(a AS BIGINT) + b
```

### Accidental Integer Division

Bad:

```sql
successful / total * 100
```

when both operands are integers.

Prefer:

```sql
CAST(successful AS DECIMAL(12, 4))
/ NULLIF(total, 0) * 100
```

### Treating CAST as Rounding

Bad assumption:

```sql
CAST(123.99 AS INT)
```

does not mean "round to the nearest integer."

Use an explicit rounding operation when rounding is required.

### Using FLOAT for Currency

Bad:

```sql
price FLOAT
```

for a monetary ledger.

Prefer an exact decimal type with a domain-appropriate precision and scale.

### Converting Indexed Columns

Bad:

```sql
WHERE CAST(customer_id AS VARCHAR(50)) = @customer_id
```

Prefer a correctly typed parameter.

### Converting Before Aggregation

Bad:

```sql
SUM(CAST(amount AS VARCHAR(50)))
```

Keep the value numeric throughout the aggregation.

### Ignoring Overflow During SUM

Bad:

```sql
SUM(request_count)
```

when the source type may not safely contain the aggregate result.

Consider widening the expression:

```sql
SUM(CAST(request_count AS BIGINT))
```

### Using TRY_CAST Without Monitoring Invalid Data

`TRY_CAST` prevents a query from failing, but turning bad input into `NULL` can hide upstream data-quality issues.

For ingestion pipelines, track rejected or invalid records separately.

### Mixing Numeric and Textual CASE Branches

Avoid:

```sql
CASE
    WHEN status = 'paid' THEN amount
    ELSE 'N/A'
END
```

unless a textual result is explicitly intended.

Prefer returning a numeric value and handling the display state separately.

## Production Checklist

Before deploying numeric conversion logic, verify:

- [ ] The target numeric type matches the business domain.
- [ ] `INT` vs `BIGINT` capacity has been considered.
- [ ] Decimal precision and scale are intentional.
- [ ] Rounding rules are explicit.
- [ ] Integer division is not occurring accidentally.
- [ ] Division-by-zero behavior is defined.
- [ ] Overflow is impossible or explicitly handled.
- [ ] `FLOAT` is not being used where exact decimal semantics are required.
- [ ] Indexed columns are not unnecessarily converted.
- [ ] Application parameters match database column types.
- [ ] External numeric input is validated.
- [ ] `TRY_CAST`/`TRY_CONVERT` failures are observable where appropriate.
- [ ] Execution plans have been checked for conversion-related performance issues.
- [ ] API responses preserve semantic numeric types where possible.

## Interview Traps

| Question | Strong answer |
| --- | --- |
| Why cast before addition instead of after? | The arithmetic can overflow before the result is converted |
| How do you avoid integer division? | Convert at least one operand to an appropriate decimal type before division |
| Does `CAST(123.99 AS INT)` round the value? | No; it removes the fractional portion |
| `DECIMAL` vs `FLOAT`? | `DECIMAL` is exact with defined precision/scale; `FLOAT` is approximate |
| Why can implicit conversion be dangerous? | It can change expression behavior, cause errors, increase CPU work, or interfere with index usage |
| How do you safely parse dirty numeric input? | Use `TRY_CAST` or `TRY_CONVERT`, while separately monitoring invalid records |
| Why widen a column before `SUM()`? | The aggregate result may exceed the range of the original integer type |
| Should currency normally use `FLOAT`? | No; exact decimal semantics are generally preferable |
| Why avoid converting indexed columns in predicates? | It can prevent efficient index access and reduce SARGability |
| Does `TRY_CAST` validate business rules? | No; it validates whether conversion is possible, not whether the value is semantically valid |
| Where should currency formatting usually occur? | At the presentation boundary rather than inside core database calculations |
| Why is explicit numeric typing useful in `CASE` or `COALESCE`? | It makes the result type and precision/scale predictable |

## Key Takeaways

- **Choose numeric types according to domain semantics**: use exact integers for counts and identifiers, and appropriate `DECIMAL`/`NUMERIC` types when exact decimal precision matters.
- **Convert before arithmetic when a wider type is required**; casting an already-overflowed expression is too late.
- **Make division explicitly decimal when fractional results are required**, and use `NULLIF` when a zero denominator is possible.
- **Keep numeric values numeric throughout filtering, aggregation, and calculations**; avoid unnecessary conversion to strings and avoid conversions on indexed columns.
- **Treat external numeric data as untrusted input**: validate ranges, use `TRY_CAST`/`TRY_CONVERT` where appropriate, and monitor invalid records instead of silently hiding data-quality problems.