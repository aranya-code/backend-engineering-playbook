# 06- SUBSTRING

## Overview

`SUBSTRING` extracts a portion of a string based on a starting position and, optionally, a length. It is useful when a backend query needs to derive a value from structured text, such as extracting a country prefix, identifier segment, filename extension, or fixed-width component.

The exact syntax and edge-case behavior vary across database engines. The examples below use PostgreSQL-compatible syntax and focus on behavior that is broadly useful when working with relational databases.

`SUBSTRING` is primarily a **data transformation function**. It should not automatically be used as a substitute for proper schema design. If an application frequently queries a component of a value, storing that component separately or using an appropriate generated/expression column may be a better production design.

## Basic Syntax

The common PostgreSQL form is:

```sql
SUBSTRING(string FROM start [FOR length])
```

Example:

```sql
SELECT SUBSTRING('ORD-2026-001234' FROM 5 FOR 4);
```

Result:

```text
2026
```

The components are:

| Component | Meaning |
|---|---|
| `string` | Input text |
| `start` | Starting character position |
| `length` | Number of characters to extract |

Positions are **1-based**, meaning the first character is position `1`.

```text
O R D - 2 0 2 6 - 0 0 1 2 3 4
1 2 3 4 5 6 7 8 9 ...
```

Therefore:

```sql
SELECT SUBSTRING('ORD-2026-001234' FROM 5 FOR 4);
```

returns:

```text
2026
```

## Why SUBSTRING Exists

Many production systems receive strings containing multiple logical components.

Examples include:

```text
ORD-2026-001234
IN-560001
invoice-2026-08.pdf
user:12345
2026-08-30
```

A query may need to extract part of these values for:

- Reporting.
- Data migration.
- Legacy integration.
- ETL processing.
- Data-quality analysis.
- Temporary compatibility logic.
- Derived API responses.

For example, extracting the year from an order reference:

```sql
SELECT
    order_number,
    SUBSTRING(order_number FROM 5 FOR 4) AS order_year
FROM orders;
```

However, if `order_year` is a core business attribute that is frequently filtered or joined, deriving it from a string on every query is usually inferior to modeling it explicitly.

## Character Positions

`SUBSTRING` uses character positions rather than zero-based programming indexes.

```sql
SELECT SUBSTRING('backend' FROM 1 FOR 3);
```

Result:

```text
bac
```

```sql
SELECT SUBSTRING('backend' FROM 4 FOR 4);
```

Result:

```text
kend
```

A useful mental model is:

```text
SUBSTRING(value FROM start FOR length)
                     │      │
                     │      └── number of characters
                     └───────── 1-based starting position
```

This differs from Python slicing.

Python:

```python
value[0:3]
```

SQL:

```sql
SUBSTRING(value FROM 1 FOR 3)
```

When moving between application code and SQL, be careful not to transfer zero-based indexing assumptions.

## Omitting the Length

In PostgreSQL, the length can be omitted:

```sql
SELECT SUBSTRING('backend' FROM 4);
```

Result:

```text
kend
```

This means extraction continues from the specified starting position to the end of the string.

This is useful when the desired value is a suffix:

```sql
SELECT SUBSTRING(filename FROM 10)
FROM documents;
```

However, if the format is not guaranteed, relying on fixed positions can produce incorrect results.

## SUBSTRING and NULL

`SUBSTRING(NULL FROM 1 FOR 3)` produces `NULL`.

```sql
SELECT SUBSTRING(NULL FROM 1 FOR 3);
```

This follows SQL's general null-propagation behavior for string expressions.

Compare:

```text
NULL → NULL
'abc' → extracted substring
```

Do not automatically replace `NULL` with an empty string unless the application's data model treats those states as equivalent.

You can explicitly handle missing values with `COALESCE`:

```sql
SELECT COALESCE(
    SUBSTRING(reference_code FROM 1 FOR 3),
    ''
)
FROM orders;
```

Use this only when an empty string is actually the desired semantic result.

## SUBSTRING with Short Strings

If the requested length extends beyond the end of the string, PostgreSQL returns the available characters rather than failing.

```sql
SELECT SUBSTRING('abc' FROM 2 FOR 10);
```

Result:

```text
bc
```

This makes `SUBSTRING` convenient for extraction, but it can hide malformed input.

Suppose the application expects:

```text
ORD-2026-001234
```

and blindly executes:

```sql
SUBSTRING(order_number FROM 5 FOR 4)
```

against:

```text
ORD-X
```

The query may still return a value rather than raising an error.

For critical data formats, validate the input separately instead of assuming the substring proves that the source value is valid.

## SUBSTRING in SELECT

The simplest use is transforming data for output.

```sql
SELECT
    id,
    order_number,
    SUBSTRING(order_number FROM 5 FOR 4) AS order_year
FROM orders;
```

This is useful for reporting and read-only transformations.

A REST API might expose:

```json
{
  "order_number": "ORD-2026-001234",
  "order_year": "2026"
}
```

without requiring the database to persist a redundant `order_year` column.

Whether this belongs in SQL or application code depends on where the transformation is most naturally owned.

## SUBSTRING in WHERE

`SUBSTRING` can be used to filter based on part of a value.

```sql
SELECT id, order_number
FROM orders
WHERE SUBSTRING(order_number FROM 5 FOR 4) = '2026';
```

This is logically straightforward, but it can become a performance problem on large tables.

A normal index on:

```sql
order_number
```

does not automatically mean the database can efficiently use that index for:

```sql
SUBSTRING(order_number FROM 5 FOR 4)
```

The database may need to evaluate the expression for many rows.

For a large production table, inspect the query plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM orders
WHERE SUBSTRING(order_number FROM 5 FOR 4) = '2026';
```

## Expression Indexes

PostgreSQL supports indexes on expressions.

If a query pattern is stable and genuinely performance-critical:

```sql
CREATE INDEX orders_order_year_idx
ON orders (SUBSTRING(order_number FROM 5 FOR 4));
```

Then:

```sql
SELECT id
FROM orders
WHERE SUBSTRING(order_number FROM 5 FOR 4) = '2026';
```

can potentially use the expression index.

Before creating one, verify:

- Query frequency.
- Table size.
- Selectivity.
- Execution plans.
- Write overhead.
- Storage cost.

An expression index is often useful for compatibility with an existing schema, but it does not eliminate the architectural question of whether the derived attribute should be modeled separately.

## SUBSTRING in GROUP BY

A substring can be used to group records by a derived component.

```sql
SELECT
    SUBSTRING(order_number FROM 5 FOR 4) AS order_year,
    COUNT(*) AS order_count
FROM orders
GROUP BY SUBSTRING(order_number FROM 5 FOR 4)
ORDER BY order_year;
```

This can be useful for reporting legacy identifiers.

However, if the database is processing millions of rows, repeatedly calculating the same expression can add CPU cost. If the derived value is operationally important, consider storing or indexing it appropriately.

## SUBSTRING in ORDER BY

You can sort based on an extracted component:

```sql
SELECT
    order_number,
    SUBSTRING(order_number FROM 5 FOR 4) AS order_year
FROM orders
ORDER BY SUBSTRING(order_number FROM 5 FOR 4);
```

For frequently executed queries, avoid assuming the database can use the base-column index efficiently. Examine the execution plan.

## Extracting Prefixes

For fixed-width prefixes:

```sql
SELECT SUBSTRING(customer_code FROM 1 FOR 2) AS region_code
FROM customers;
```

For:

```text
IN123456
US123456
DE123456
```

the result is:

```text
IN
US
DE
```

This is useful when analyzing legacy identifiers.

For new schema design, however, storing:

```text
region_code
customer_number
```

as separate attributes is generally more maintainable when both values have independent business meaning.

## Extracting Suffixes

Omitting the length allows extraction through the end:

```sql
SELECT SUBSTRING(reference_code FROM 6)
FROM orders;
```

For:

```text
ORD-12345
```

this returns:

```text
2345
```

The exact starting position must reflect the actual format.

For variable-length structures, `SPLIT_PART()` or regular-expression functions may be more appropriate.

## SUBSTRING vs LEFT and RIGHT

When only a prefix or suffix is required, `LEFT()` and `RIGHT()` can communicate intent more clearly.

```sql
SELECT LEFT(order_number, 3)
FROM orders;
```

versus:

```sql
SELECT SUBSTRING(order_number FROM 1 FOR 3)
FROM orders;
```

For a suffix:

```sql
SELECT RIGHT(order_number, 6)
FROM orders;
```

versus a position-dependent `SUBSTRING`.

| Requirement | Prefer |
|---|---|
| First N characters | `LEFT()` |
| Last N characters | `RIGHT()` |
| Arbitrary position | `SUBSTRING()` |
| Delimited component | `SPLIT_PART()` |
| Pattern-based extraction | Regular expressions |

Use the function that communicates the actual intent rather than forcing every string operation through `SUBSTRING`.

## SUBSTRING vs SPLIT_PART

Consider:

```text
ORD-2026-001234
```

If the requirement is "extract the second hyphen-delimited component," `SPLIT_PART()` expresses that intent directly:

```sql
SELECT SPLIT_PART('ORD-2026-001234', '-', 2);
```

Result:

```text
2026
```

Using:

```sql
SUBSTRING('ORD-2026-001234' FROM 5 FOR 4)
```

depends on fixed character positions.

The distinction becomes important when formats evolve.

If:

```text
ORD-2026-001234
```

becomes:

```text
ORDER-2026-001234
```

the `SUBSTRING` positions are now wrong, while delimiter-based extraction can remain correct.

## SUBSTRING vs Regular Expressions

Regular expressions are appropriate when the extraction rule depends on a pattern rather than fixed positions.

For example, extracting digits from a value may require a regular expression.

Conceptually:

```sql
-- PostgreSQL
SELECT SUBSTRING('customer-12345' FROM '[0-9]+');
```

Result:

```text
12345
```

This is more flexible than fixed-position extraction, but regular expressions are generally more expensive and harder to reason about.

Use:

- `SUBSTRING` for fixed positions.
- `SPLIT_PART` for delimiters.
- Regex for pattern-based extraction.

Choosing the simplest correct operation improves maintainability and often performance.

## Negative Positions and Database Differences

String-function behavior is not completely uniform across SQL engines.

PostgreSQL, MySQL, SQL Server, Oracle, and other databases differ in:

- Function syntax.
- Position handling.
- Negative indexing support.
- Regex behavior.
- Implicit type conversion.
- NULL handling details.
- Character semantics.

For example, code written for one database may not be portable without modification.

For a production application, treat the database engine as part of the SQL contract and test the actual target engine rather than relying on generic SQL assumptions.

## Unicode and Character Semantics

Character positions can become more subtle with Unicode data.

A string may contain:

- ASCII characters.
- Accented characters.
- Emoji.
- Combining characters.
- Multi-code-point grapheme clusters.

The database's string functions operate according to its character and encoding semantics. A visually perceived "character" is not always equivalent to one Unicode code point.

For example, an emoji sequence may visually appear as one symbol while internally containing multiple code points.

Do not use `SUBSTRING` as a generic mechanism for safely truncating arbitrary user-visible Unicode text without testing the application's actual requirements.

For UI text truncation, application-layer or specialized Unicode-aware handling may be more appropriate.

## SUBSTRING and Data Validation

Extraction and validation are separate concerns.

This query:

```sql
SELECT SUBSTRING(order_number FROM 5 FOR 4)
FROM orders;
```

does not establish that `order_number` actually conforms to the expected format.

If the format is strict, enforce it explicitly.

For PostgreSQL, a check constraint may be appropriate:

```sql
ALTER TABLE orders
ADD CONSTRAINT orders_number_format_chk
CHECK (order_number ~ '^ORD-[0-9]{4}-[0-9]{6}$');
```

Now the database protects the format instead of requiring every query to assume it.

This becomes especially valuable when multiple services, scripts, migrations, or administrative tools can write to the same table.

## Data Modeling: Don't Encode Structure Unnecessarily

Consider an identifier:

```text
IN-2026-000123
```

Suppose the application frequently queries:

```text
country = IN
year = 2026
sequence = 000123
```

Repeatedly extracting these values with `SUBSTRING` is usually a sign that the string contains multiple independently meaningful attributes.

A more maintainable schema could be:

```text
country_code
order_year
sequence_number
```

The display identifier can then be generated when needed.

This provides:

- Better constraints.
- Better indexing.
- Easier querying.
- Easier validation.
- Less string parsing.
- More explicit domain modeling.

`SUBSTRING` is valuable for existing or externally defined formats, but it should not be used to compensate for poor schema design indefinitely.

## Production Performance

The computational cost of `SUBSTRING` is normally small for individual values, but the cost can become significant when applied to millions of rows.

For example:

```sql
SELECT
    SUBSTRING(reference_code FROM 1 FOR 4),
    COUNT(*)
FROM transactions
GROUP BY SUBSTRING(reference_code FROM 1 FOR 4);
```

The database may need to:

1. Read qualifying rows.
2. Extract the substring for each row.
3. Hash or sort the derived values.
4. Perform aggregation.
5. Return the grouped result.

On large datasets, performance depends on:

- Number of rows processed.
- String length.
- Selectivity.
- Query plan.
- Available indexes.
- Memory available for sorting/hash aggregation.
- Concurrent workload.

Do not optimize based solely on the presence of `SUBSTRING`. Measure the complete query.

## Generated and Derived Columns

If a derived substring is frequently queried, some databases support generated/computed columns.

Conceptually:

```sql
derived_year = SUBSTRING(order_number FROM 5 FOR 4)
```

The derived value can then be indexed depending on the database and column definition.

This can be a useful middle ground between:

```text
Parse on every query
```

and:

```text
Duplicate business data manually
```

The exact syntax and capabilities are database-specific.

For PostgreSQL, an expression index is often sufficient when the derived value does not need to be exposed as a separate stored column.

## Backend Application Integration

In Django or FastAPI applications, prefer using SQL expressions when the transformation belongs naturally to the database query.

For example, a reporting endpoint may need:

```text
order_number → order_year
```

The database can return the derived field directly rather than transferring the entire dataset to Python and processing every row.

Conceptually:

```text
Client
  ↓
REST API
  ↓
Backend service
  ↓
PostgreSQL
  ↓
SUBSTRING(...)
  ↓
Derived result
  ↓
JSON response
```

This is especially useful for aggregation and filtering that can be performed efficiently inside the database.

However, if the transformation is purely presentation logic and the dataset is already small, application-level processing may be simpler.

## Security Considerations

`SUBSTRING` itself is not an SQL injection vulnerability.

The security problem arises when application code constructs SQL unsafely.

Do not do:

```python
query = f"""
SELECT SUBSTRING(reference_code FROM {start_position} FOR {length})
FROM orders
"""
```

when values originate from untrusted input.

Prefer parameterized queries or ORM expression APIs.

For Django:

```python
from django.db.models.functions import Substr

queryset = Order.objects.annotate(
    order_year=Substr("order_number", 5, 4)
)
```

The ORM handles SQL generation and parameterization.

Still validate business constraints separately. SQL parameterization protects query construction; it does not validate that a reference code has the expected structure.

## Common Mistakes

### Confusing SQL and Programming Indexes

Python uses zero-based indexes:

```python
value[0:4]
```

SQL commonly uses one-based positions:

```sql
SUBSTRING(value FROM 1 FOR 4)
```

**Avoid it:** explicitly map the indexes when translating logic between Python and SQL.

### Using Fixed Positions for Variable-Length Data

This is fragile:

```sql
SUBSTRING(reference_code FROM 5 FOR 4)
```

if the prefix can change length.

**Avoid it:** use delimiter-based parsing such as `SPLIT_PART()` when the format is delimiter-driven.

### Using SUBSTRING Instead of Proper Schema Design

Repeatedly parsing:

```text
country-year-sequence
```

may indicate multiple business attributes have been packed into one column.

**Avoid it:** model independently queried attributes as separate columns when practical.

### Assuming a Base Index Solves an Expression Predicate

This:

```sql
WHERE SUBSTRING(reference_code FROM 1 FOR 3) = 'ORD'
```

does not automatically behave like:

```sql
WHERE reference_code = 'ORD...'
```

for index usage.

**Avoid it:** inspect the execution plan and consider an expression index or a schema-level redesign.

### Using SUBSTRING as Validation

Extraction does not prove that input is valid.

**Avoid it:** use constraints, validation rules, or regular expressions where the format must be enforced.

### Ignoring Database-Specific Syntax

SQL string functions differ across engines.

**Avoid it:** write against the actual database engine used in production and test migration compatibility explicitly.

### Assuming Visual Characters Equal Character Positions

Unicode grapheme clusters can contain multiple code points.

**Avoid it:** use Unicode-aware handling when truncating user-visible text.

### Performing Large-Scale Parsing on Every Request

Repeated substring processing over large datasets can become expensive.

**Avoid it:** move stable transformations toward ingestion, generated/derived values, or indexed expressions when justified.

## Interview Traps

| Question | Correct Reasoning |
|---|---|
| Is SQL substring indexing generally zero-based? | No. PostgreSQL's `SUBSTRING` positions are 1-based. |
| What does `SUBSTRING(value FROM 4 FOR 3)` mean? | Start at character 4 and return up to 3 characters. |
| What happens if the requested length exceeds the remaining string? | The available characters are returned rather than requiring the full length. |
| Does `SUBSTRING` validate the source format? | No. It only extracts data. |
| Is `SUBSTRING` interchangeable with `LEFT()`? | Not always. `LEFT()` clearly expresses prefix extraction, while `SUBSTRING` supports arbitrary positions. |
| When is `SPLIT_PART()` preferable? | When extracting a delimiter-separated component. |
| Can a normal index on a column always optimize `SUBSTRING(column ...)`? | No. The expression may require an expression index or another design. |
| Should frequently queried derived attributes always be extracted at query time? | No. Consider canonical columns, generated values, or expression indexes. |
| Does `SUBSTRING` behave identically across all SQL databases? | No. Syntax and edge cases are database-specific. |
| Does extracting a substring guarantee valid input? | No. Validation must be handled separately. |

## Practical Patterns

### Extract a Fixed-Length Prefix

```sql
SELECT
    customer_code,
    SUBSTRING(customer_code FROM 1 FOR 2) AS region_code
FROM customers;
```

### Extract a Fixed-Length Segment

```sql
SELECT
    order_number,
    SUBSTRING(order_number FROM 5 FOR 4) AS order_year
FROM orders;
```

### Extract Everything After a Known Position

```sql
SELECT
    SUBSTRING(reference_code FROM 6) AS sequence_value
FROM orders;
```

### Group by an Extracted Component

```sql
SELECT
    SUBSTRING(order_number FROM 5 FOR 4) AS order_year,
    COUNT(*) AS order_count
FROM orders
GROUP BY SUBSTRING(order_number FROM 5 FOR 4)
ORDER BY order_year;
```

### Filter by an Extracted Component

```sql
SELECT id, order_number
FROM orders
WHERE SUBSTRING(order_number FROM 5 FOR 4) = '2026';
```

For a large table, validate the execution plan before using this pattern on a high-throughput endpoint.

### Prefer Delimiter-Aware Extraction When Appropriate

```sql
SELECT SPLIT_PART(order_number, '-', 2) AS order_year
FROM orders;
```

This communicates that the value is structurally delimited rather than positionally fixed.

## Choosing the Right String Operation

| Requirement | Recommended Approach | Reason |
|---|---|---|
| Extract first N characters | `LEFT()` | Clear intent |
| Extract last N characters | `RIGHT()` | Clear intent |
| Extract characters at arbitrary positions | `SUBSTRING()` | Position-based extraction |
| Extract delimited field | `SPLIT_PART()` | Independent of field width |
| Extract pattern-based content | Regex functions | Flexible matching |
| Normalize surrounding whitespace | `TRIM()` | Boundary cleanup |
| Replace occurrences | `REPLACE()` | Substring replacement |
| Frequently query derived attribute | Column / expression index | Avoid repeated expensive computation |
| Validate structured identifier | Constraint / validation | Extraction is not validation |

## Production Checklist

Before using `SUBSTRING` in production, consider:

- **Indexing:** Is the expression used in a frequent filter or join?
- **Data format:** Is the source string fixed-width or delimiter-based?
- **Validation:** Is the format actually guaranteed?
- **Schema:** Are you repeatedly extracting values that should be separate columns?
- **Database:** Does the target SQL engine support the syntax and behavior being used?
- **Unicode:** Can the data contain complex Unicode characters?
- **Volume:** Will the expression run over thousands, millions, or billions of rows?
- **Migration:** Will changing the source format break fixed-position extraction?
- **Observability:** Has the query plan been inspected for high-volume workloads?
- **Application boundary:** Should the transformation happen during ingestion, in SQL, or in application code?

## Key Takeaways

- **`SUBSTRING` extracts characters using a starting position and optional length; PostgreSQL uses 1-based positions.**
- **Use `SUBSTRING` for position-based extraction, but prefer `LEFT`, `RIGHT`, or `SPLIT_PART` when they express the requirement more directly.**
- **Applying `SUBSTRING` to a column in filters or grouping can have performance implications; use execution plans and expression indexes where justified.**
- **Repeatedly parsing business attributes from a string can indicate a schema-design problem; independently queried attributes are often better modeled as columns.**
- **Extraction is not validation: enforce structured data formats separately with application validation and database constraints where appropriate.**