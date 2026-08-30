# 01- Data Types and Type Compatibility

## Overview

SQL is strongly typed: every expression has a data type, and operations are valid only when the participating values can be compared, combined, or converted according to the database engine's type rules.

Understanding data types and type compatibility is essential when writing joins, filters, `CASE` expressions, arithmetic, aggregations, inserts, and updates. Many SQL bugs that appear to be "logic errors" are actually type errors, implicit conversions, precision loss, or mismatched semantics.

For backend engineers, type compatibility matters at the boundary between:

- Application types and database types.
- API payloads and persisted values.
- Different database columns.
- SQL expressions and function arguments.
- Numeric calculations and financial values.
- Timestamps and time zones.
- JSON/document data and relational columns.

The exact type system differs between PostgreSQL, MySQL, SQL Server, Oracle, and other databases, so production SQL should be written with the target database's conversion and type-resolution rules in mind.

## Why Data Types Matter

A database type is not merely storage metadata. It determines what values are valid and how the database interprets operations on those values.

For example:

```sql
CREATE TABLE products (
    product_id BIGINT,
    price NUMERIC(12, 2),
    quantity INTEGER,
    is_active BOOLEAN,
    created_at TIMESTAMPTZ
);
```

Each column communicates a different semantic contract:

| Type | Meaning |
| --- | --- |
| `BIGINT` | Large integer identifier |
| `INTEGER` | Whole-number quantity |
| `NUMERIC(12, 2)` | Exact decimal value |
| `BOOLEAN` | True/false state |
| `TIMESTAMPTZ` | Timestamp representing an instant |

Choosing an inappropriate type can create correctness, performance, interoperability, and maintenance problems.

For example, storing monetary amounts as floating-point values can introduce representation errors that are unacceptable for financial calculations.

## Common SQL Data Type Categories

Although exact names vary by database, most relational systems provide comparable categories.

| Category | Examples | Typical use |
| --- | --- | --- |
| Integer | `SMALLINT`, `INTEGER`, `BIGINT` | Counts, IDs, quantities |
| Exact numeric | `NUMERIC`, `DECIMAL` | Money, precise measurements |
| Floating point | `REAL`, `DOUBLE PRECISION` | Approximate scientific calculations |
| Character | `CHAR`, `VARCHAR`, `TEXT` | Strings |
| Boolean | `BOOLEAN` | State flags |
| Date/time | `DATE`, `TIME`, `TIMESTAMP` | Temporal values |
| Binary | `BYTEA`, `BLOB` | Raw binary data |
| JSON | `JSON`, `JSONB` | Semi-structured data |
| UUID | `UUID` | Globally unique identifiers |
| Network | `INET`, `CIDR` | IP/network values |

PostgreSQL provides particularly rich native types, including arrays, ranges, JSON/JSONB, UUIDs, geometric types, and network types.

## Type Compatibility

Two expressions are type-compatible when the database can legally use them together for a particular operation.

For example:

```sql
SELECT 10 + 20;
```

works because both operands are numeric.

A comparison such as:

```sql
SELECT *
FROM users
WHERE age = 30;
```

also compares compatible numeric values.

The problem becomes more apparent when types differ:

```sql
SELECT *
FROM users
WHERE user_id = '100';
```

Whether this works, fails, or causes an implicit conversion depends on the database engine and the involved types.

The important production principle is:

> Do not rely on implicit conversion merely because a particular query happens to work.

Make type intent explicit when crossing type boundaries.

## Implicit Conversion

An implicit conversion occurs when the database automatically converts one value to another type.

For example, a database may convert a textual numeric value into a numeric value when evaluating a comparison.

Conceptually:

```text
integer = text
   │
   └── database determines whether conversion is possible
                │
                ├── convert text → integer
                └── reject expression
```

The exact behavior is database-specific.

Implicit conversion can be convenient, but it can also introduce:

- Unexpected query behavior.
- Runtime conversion failures.
- Precision loss.
- Poor index utilization.
- Ambiguous expression types.
- Portability problems between database engines.

For production code, prefer explicitly typed parameters and explicit casts when the conversion is intentional.

## Explicit Casting

Explicit casting tells the database exactly how a value should be converted.

PostgreSQL supports both `CAST` and the `::` operator:

```sql
SELECT CAST('42' AS INTEGER);
```

or:

```sql
SELECT '42'::INTEGER;
```

`CAST` is standard SQL and is generally more portable:

```sql
SELECT CAST(order_id AS TEXT)
FROM orders;
```

The PostgreSQL shorthand is concise:

```sql
SELECT order_id::TEXT
FROM orders;
```

Use explicit casts when they clarify a deliberate type boundary.

## CAST vs Conversion Functions

Database systems may also provide specialized conversion functions.

For example, PostgreSQL provides functions such as:

```sql
SELECT TO_DATE('2026-08-30', 'YYYY-MM-DD');
```

and:

```sql
SELECT TO_TIMESTAMP('2026-08-30 14:30:00', 'YYYY-MM-DD HH24:MI:SS');
```

These are different from a generic cast because they can interpret a value according to a specified format.

A useful distinction is:

| Technique | Purpose |
| --- | --- |
| `CAST()` | Convert between compatible SQL types |
| PostgreSQL `::` | PostgreSQL-specific cast syntax |
| `TO_DATE()` | Parse formatted text into a date |
| `TO_TIMESTAMP()` | Parse formatted text into a timestamp |
| Application validation | Validate external input before database operations |

## Numeric Compatibility

Numeric types deserve particular attention because arithmetic can involve type promotion and precision rules.

Consider:

```sql
SELECT 10 / 3;
```

The result depends on the operand types and database rules. Integer division can produce a different result from decimal division.

When fractional precision is required, make the intended type explicit:

```sql
SELECT 10::NUMERIC / 3;
```

For financial calculations:

```sql
SELECT
    quantity,
    unit_price,
    quantity * unit_price AS total
FROM order_items;
```

Use exact numeric types such as `NUMERIC` or `DECIMAL` when the domain requires exact decimal arithmetic.

### Floating Point vs Exact Numeric

| Type | Characteristics | Suitable for |
| --- | --- | --- |
| Integer | Exact whole numbers | Counts, quantities |
| `NUMERIC` / `DECIMAL` | Exact decimal arithmetic | Money, financial values |
| Floating point | Approximate representation | Scientific/engineering calculations |

Do not use floating-point types for monetary values merely because they are convenient.

## String and Numeric Comparisons

A common application mistake is mixing API strings with numeric database columns without considering conversion behavior.

Suppose an API receives:

```json
{
  "user_id": "123"
}
```

The application should validate the identifier according to the API contract before querying a numeric database column.

Prefer an application parameter with the correct database-compatible type:

```python
user_id = int(payload["user_id"])
```

Then:

```sql
SELECT *
FROM users
WHERE user_id = $1;
```

The database receives a typed parameter rather than an arbitrary SQL string.

This is preferable to constructing SQL such as:

```sql
WHERE user_id = '123'
```

and relying on implicit conversion.

Parameterized queries also protect against SQL injection.

## Type Compatibility in JOINs

Type mismatches frequently appear in joins.

Consider:

```sql
SELECT
    o.order_id,
    u.email
FROM orders AS o
JOIN users AS u
    ON o.user_id = u.user_id;
```

Ideally, both columns should represent the same domain and use compatible types.

A problematic schema might contain:

```text
orders.user_id → BIGINT
users.user_id  → TEXT
```

The query may require casting:

```sql
ON o.user_id::TEXT = u.user_id
```

but this is often a schema-design problem rather than a query problem.

### Why This Matters

Casting inside a join can make optimization harder and may prevent efficient use of indexes depending on the expression and available indexes.

Instead of repeatedly compensating for inconsistent schemas:

```sql
ON CAST(a.customer_id AS TEXT) = b.customer_id
```

prefer consistent column types:

```text
customers.customer_id → BIGINT
orders.customer_id    → BIGINT
```

The database schema should preserve domain compatibility at the storage layer.

## Type Compatibility in WHERE

Filtering is another common type boundary.

Prefer:

```sql
WHERE created_at >= $1
```

where `$1` is supplied as the appropriate timestamp parameter.

Avoid unnecessary casts around indexed columns:

```sql
WHERE created_at::DATE = $1
```

This changes the expression being evaluated against the column and can interfere with ordinary index usage.

For date-based filtering, a range is often better:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

For example, to retrieve one UTC day:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-30 00:00:00+00'
  AND created_at <  TIMESTAMPTZ '2026-08-31 00:00:00+00'
```

This preserves a range predicate on the timestamp column.

## Type Resolution in CASE

`CASE` expressions must produce compatible result types.

For example:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    ELSE 'disabled'
END
```

has a consistent textual result.

But mixing unrelated result types can fail:

```sql
CASE
    WHEN status = 'active' THEN 'enabled'
    ELSE 0
END
```

The database must determine a common result type. If no suitable common type exists, the query fails.

For numeric expressions, explicitly cast branches when necessary:

```sql
CASE
    WHEN status = 'active' THEN 1
    ELSE 0
END
```

If the result must be text:

```sql
CASE
    WHEN status = 'active' THEN '1'
    ELSE '0'
END
```

Do not rely on accidental type coercion to make mixed expressions work.

## NULL and Type Compatibility

`NULL` represents an unknown or absent value rather than a normal value of a specific domain.

This has important consequences for type resolution.

For example:

```sql
CASE
    WHEN is_active THEN 'active'
    ELSE NULL
END
```

can still resolve to a textual result because the non-`NULL` branch establishes the intended type.

`COALESCE` also requires compatible result types:

```sql
COALESCE(display_name, username)
```

works when both values are compatible textual types.

A problematic expression might mix unrelated domains:

```sql
COALESCE(user_id, username)
```

if one is numeric and the other textual.

If conversion is genuinely intended, make it explicit:

```sql
COALESCE(user_id::TEXT, username)
```

## Date and Time Compatibility

Date/time handling is one of the most important sources of production bugs.

Common temporal types include:

| Type | Meaning |
| --- | --- |
| `DATE` | Calendar date without time |
| `TIME` | Time of day |
| `TIMESTAMP` | Date and time without time-zone semantics |
| `TIMESTAMPTZ` | Timestamp representing an instant, with PostgreSQL session-time-zone display semantics |

Do not treat these as interchangeable.

For systems operating across regions, define a clear temporal convention. A common backend design is:

```text
API input
   ↓
Validate timezone-aware timestamp
   ↓
Application
   ↓
Database TIMESTAMPTZ
   ↓
Store instant consistently
   ↓
Convert for presentation
```

Be especially careful when comparing:

- UTC timestamps.
- Local timestamps.
- Date-only values.
- User-specific time zones.
- Business-calendar dates.

## Character Type Compatibility

String types can differ in length semantics, collation, encoding, and comparison behavior.

For example:

```sql
VARCHAR(255)
```

and:

```sql
TEXT
```

are both textual types in PostgreSQL, but they communicate different schema intent.

Do not add arbitrary length constraints merely because a framework convention uses them. Use constraints when the domain actually requires them.

More importantly, be consistent with:

- Character encoding.
- Collation.
- Case sensitivity.
- Normalization rules.
- Locale-specific comparison requirements.

## Boolean Compatibility

Boolean values should be modeled as booleans when the domain is genuinely binary.

Prefer:

```sql
is_active BOOLEAN NOT NULL DEFAULT TRUE
```

over:

```sql
is_active VARCHAR(10)
```

with values such as:

```text
"true"
"false"
"yes"
"no"
"1"
"0"
```

A real boolean type provides stronger data integrity and clearer query semantics:

```sql
WHERE is_active = TRUE
```

or, depending on the database and style:

```sql
WHERE is_active
```

Do not encode multiple meanings into a boolean if the domain actually has multiple states.

For example:

```text
pending
active
suspended
deleted
```

should generally be represented by a status domain rather than several loosely related boolean columns.

## UUID and Identifier Types

UUIDs should generally be stored using the database's native UUID type when supported.

PostgreSQL:

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY
);
```

This is preferable to treating UUIDs as arbitrary text when the identifier is semantically a UUID.

Native types can provide:

- Better schema semantics.
- Type validation.
- Cleaner application/database contracts.
- Appropriate operators and functions.
- Better interoperability with database tooling.

The same principle applies to native network, JSON, range, and other domain-specific types where appropriate.

## JSON and Relational Types

Modern backend systems frequently combine relational and JSON data.

For example:

```sql
CREATE TABLE events (
    event_id BIGINT PRIMARY KEY,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL
);
```

JSONB is useful when the structure is genuinely variable or event-specific.

However, frequently queried, constrained, or relationally significant fields often belong in normal columns.

A common mistake is to store an entire relational domain inside JSON simply because it is flexible.

A useful rule is:

> Use relational columns for stable, query-critical attributes and JSON for genuinely semi-structured data.

## Application-to-Database Type Mapping

Backend frameworks provide their own type systems that map to database types.

For example:

```text
Python
  ↓
Django / SQLAlchemy / driver
  ↓
PostgreSQL
```

A simplified mapping might look like:

| Python concept | PostgreSQL example |
| --- | --- |
| `int` | `INTEGER` / `BIGINT` |
| `Decimal` | `NUMERIC` |
| `str` | `TEXT` / `VARCHAR` |
| `bool` | `BOOLEAN` |
| `datetime` | `TIMESTAMP` / `TIMESTAMPTZ` |
| `UUID` | `UUID` |
| `dict` / JSON structure | `JSONB` |

The exact mapping depends on the framework, driver, model definition, and database configuration.

Senior backend engineers should verify the generated schema rather than assuming the ORM mapping.

## ORM Type Safety

An ORM does not eliminate database type concerns.

For example, a Django model:

```python
class Order(models.Model):
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
```

should map to an appropriate database numeric type.

The database remains the final persistence boundary and should enforce critical constraints.

For production systems:

- Use migrations as the schema source of truth.
- Inspect generated SQL for important changes.
- Validate database constraints.
- Avoid silently relying on Python coercion.
- Keep model and database types aligned.

## Parameter Types

Parameterized SQL is the preferred boundary between application code and database queries.

Conceptually:

```text
Python value
    ↓
Database driver
    ↓
Typed SQL parameter
    ↓
SQL expression
    ↓
Database type system
```

For example:

```python
cursor.execute(
    """
    SELECT order_id
    FROM orders
    WHERE customer_id = %s
    """,
    [customer_id],
)
```

The driver handles parameter binding instead of requiring the application to concatenate values into SQL.

Avoid:

```python
query = f"""
    SELECT order_id
    FROM orders
    WHERE customer_id = {customer_id}
"""
```

Even when the value appears numeric, dynamic SQL construction creates unnecessary security and correctness risks.

## Type Compatibility and Indexes

Type conversion can affect index usage.

Suppose:

```sql
CREATE INDEX idx_users_user_id
ON users (user_id);
```

A direct predicate is usually preferable:

```sql
WHERE user_id = $1
```

rather than transforming the indexed column:

```sql
WHERE user_id::TEXT = $1
```

The second query applies a function/cast to the indexed expression.

Depending on the database and available indexes, the optimizer may not be able to use the ordinary index as efficiently.

If a cast is unavoidable and is a stable access pattern, an expression index may sometimes be appropriate:

```sql
CREATE INDEX idx_users_user_id_text
ON users ((user_id::TEXT));
```

Do not create such an index automatically. First establish that the query pattern is required and performance-sensitive.

## Type Compatibility and Query Plans

When a query behaves unexpectedly, inspect the execution plan.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users
WHERE user_id = $1;
```

Look for:

- Sequential scans where an index scan was expected.
- Explicit conversion operations.
- Large row estimates versus actual rows.
- Expensive casts or functions.
- Type mismatches in joins.
- Unexpected filtering behavior.

The key point is that type correctness and performance are related but separate concerns. A query can be logically valid while still being inefficient.

## Schema Design Principles

Good type design starts with the domain.

Ask:

1. What values are valid?
2. What operations will be performed?
3. Does precision matter?
4. Can the value be absent?
5. Does the database have a native type for the domain?
6. Will this column participate in joins?
7. Will it be indexed?
8. Will it cross service or API boundaries?
9. Is the representation stable?
10. What constraints should the database enforce?

For example, an order quantity should normally be an integer:

```sql
quantity INTEGER NOT NULL CHECK (quantity > 0)
```

rather than a string such as:

```text
"five"
```

The stronger schema prevents invalid states from entering the system.

## Production Migration Considerations

Changing a column type in production can be more significant than changing application code.

For example:

```sql
ALTER TABLE orders
ALTER COLUMN customer_id TYPE BIGINT;
```

may require:

- Table rewriting.
- Locks.
- Index rebuilding.
- Constraint validation.
- Foreign-key coordination.
- Application compatibility during rollout.

For large production tables, investigate the database-specific behavior before deploying a type migration.

A safer rollout may involve:

```text
Old schema
   ↓
Introduce compatible new representation
   ↓
Deploy application supporting both
   ↓
Backfill data
   ↓
Validate
   ↓
Switch reads/writes
   ↓
Remove legacy representation
```

This expand-and-contract approach reduces deployment risk for high-volume systems.

## Common Type Compatibility Problems

| Problem | Risk | Better approach |
| --- | --- | --- |
| Numeric column compared to arbitrary text | Conversion errors or implicit casts | Bind typed parameters |
| Different types on join keys | Poor performance and complexity | Align schema types |
| Casting indexed columns | Possible index inefficiency | Cast the parameter or use suitable indexing |
| Floating point for money | Precision errors | `NUMERIC` / `DECIMAL` |
| Text-based booleans | Invalid states | Native `BOOLEAN` |
| String timestamps | Parsing and timezone bugs | Native date/time types |
| UUID stored as generic text | Weak semantic enforcement | Native `UUID` where supported |
| Large JSON object for relational fields | Difficult constraints and queries | Normalize stable fields |
| ORM-only validation | Invalid database states | Enforce critical constraints in DB |
| Implicit conversion everywhere | Hidden behavior | Explicit types and casts |

## Best Practices

### Prefer Native Database Types

Use a database type that represents the domain accurately.

```sql
price NUMERIC(12, 2)
```

is preferable to:

```sql
price TEXT
```

when the value represents an exact monetary amount.

### Keep Join Keys Type-Compatible

If two columns represent the same identifier domain, use compatible types.

```text
users.id       → BIGINT
orders.user_id → BIGINT
```

Avoid designing schemas that require permanent casting during joins.

### Bind Parameters Instead of Formatting SQL

Let the database driver handle values.

```python
cursor.execute(
    "SELECT * FROM users WHERE user_id = %s",
    [user_id],
)
```

This provides a safer and more predictable application/database boundary.

### Cast Intentionally

Use explicit casts when they clarify semantics:

```sql
CAST(order_id AS TEXT)
```

Do not scatter casts throughout queries to compensate for inconsistent schema design.

### Avoid Casting Indexed Columns Unnecessarily

Prefer:

```sql
WHERE created_at >= $1
```

over:

```sql
WHERE created_at::DATE >= $1
```

when the requirement can be expressed as a native range.

### Make Precision Explicit

For financial and other exact calculations, use exact numeric types and define precision deliberately.

### Let the Database Enforce Critical Invariants

Application validation improves user experience, but the database should enforce invariants that must never be violated.

For example:

```sql
quantity INTEGER NOT NULL CHECK (quantity > 0)
```

## Common Mistakes

### Treating All Numbers as Equivalent

`INTEGER`, `BIGINT`, `NUMERIC`, and floating-point types have different semantics.

Choose based on domain requirements rather than convenience.

### Storing Everything as TEXT

This weakens:

- Validation.
- Query semantics.
- Indexing.
- Constraint enforcement.
- Application contracts.

Use text only when the value is genuinely textual.

### Relying on Implicit Conversion

A query that works today may become problematic after:

- A schema change.
- A database migration.
- A query rewrite.
- A database-engine change.
- A change in parameter binding.

Make important conversions explicit.

### Casting Join Columns

This is often a symptom of schema inconsistency:

```sql
ON orders.user_id::TEXT = users.user_id
```

Fix the underlying type mismatch when possible.

### Casting Indexed Columns in Filters

This pattern:

```sql
WHERE order_id::TEXT = $1
```

may make an ordinary index less useful.

Prefer correctly typed parameters.

### Using Floating Point for Money

Floating-point arithmetic is approximate.

Use exact decimal types for monetary values.

### Ignoring Time Zones

Treating timestamps as arbitrary strings or mixing local and UTC semantics can produce subtle production bugs.

Define a system-wide temporal contract.

### Assuming ORM Types Are the Database Contract

The database schema is the actual persistence boundary.

Inspect migrations and database metadata when correctness matters.

## Interview Traps

| Question | Correct reasoning |
| --- | --- |
| Why avoid implicit casts? | They hide conversion behavior and can affect correctness and performance |
| Why align join-column types? | It avoids unnecessary conversion and preserves clean schema semantics |
| Why use `NUMERIC` for money? | It provides exact decimal arithmetic |
| Why can casting a column hurt performance? | It can prevent or complicate use of a normal index |
| Should application validation replace DB constraints? | No; critical invariants should also be enforced by the database |
| Why use native UUID types? | Stronger semantic typing and database-level validation |
| Is `TEXT` always worse than `VARCHAR`? | Not necessarily; the right choice depends on the database and domain |
| Why use parameterized queries? | Correct parameter binding, safer SQL construction, and protection against injection |
| Why is timestamp handling difficult? | Dates, instants, offsets, and time zones have different semantics |
| Should every conversion use `CAST()`? | No; use the simplest explicit conversion that correctly expresses the intent |

## Key Takeaways

- SQL types define data semantics, valid operations, conversion behavior, and part of the application's persistence contract.
- Prefer native, domain-appropriate types and keep related columns type-compatible, especially join keys and indexed fields.
- Use parameterized queries and explicit casts for intentional conversions instead of relying on implicit coercion.
- Treat numeric precision, timestamps, `NULL`, UUIDs, booleans, and JSON as distinct domains with different production requirements.
- When type changes or casts affect large tables and critical queries, validate execution plans, migration behavior, locking, and application compatibility before deployment.