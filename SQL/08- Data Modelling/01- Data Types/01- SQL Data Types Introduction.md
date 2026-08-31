# 01- SQL Data Types Introduction

## Overview

SQL data types define the kind of values a column can store and determine how the database validates, stores, compares, indexes, and processes those values.

Choosing a data type is a schema-design decision, not merely a syntax decision. The wrong type can introduce precision loss, inefficient indexes, unexpected comparisons, timezone bugs, oversized storage, or application/database incompatibilities.

A production schema should choose the **narrowest type that accurately represents the domain** while considering:

- Value range and precision.
- Storage requirements.
- Index size and performance.
- Comparison and sorting semantics.
- `NULL` behavior.
- Constraints.
- Application serialization.
- Query patterns.
- Database portability.
- Future growth.
- Migration complexity.

Although SQL defines broad type categories, exact types and behavior vary between database engines. PostgreSQL is used for examples in this document where database-specific behavior is useful.

## Why Data Types Matter

A database does more than store bytes. A type communicates domain semantics to the database engine.

For example:

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL,
    total_amount numeric(12, 2) NOT NULL,
    status varchar(32) NOT NULL,
    created_at timestamptz NOT NULL
);
```

The type of each column affects:

| Concern | Example |
|---|---|
| Validation | `integer` rejects non-integer values |
| Precision | `numeric(12,2)` preserves decimal amounts |
| Storage | Smaller integer types can reduce storage |
| Indexes | Smaller indexed values generally reduce index size |
| Sorting | Numeric and textual ordering have different semantics |
| Arithmetic | Numeric arithmetic differs from string operations |
| Serialization | Application frameworks map SQL types to language types |
| Constraints | Types can prevent invalid representations |
| Query planning | Data types influence operators, casts, and indexes |

Using a string for every value moves validation into application code and weakens the database's ability to enforce domain invariants.

## SQL Type Categories

SQL data types can be grouped conceptually into several categories.

| Category | Common examples | Typical use |
|---|---|---|
| Numeric | `smallint`, `integer`, `bigint`, `numeric`, `real`, `double precision` | Counts, identifiers, measurements, money |
| Character | `char`, `varchar`, `text` | Names, labels, descriptions |
| Boolean | `boolean` | Binary state |
| Date/time | `date`, `time`, `timestamp`, `timestamptz` | Business dates and event times |
| Binary | `bytea` and engine-specific binary types | Raw bytes |
| JSON/document | `json`, `jsonb` | Semi-structured attributes |
| UUID | `uuid` | Globally unique identifiers |
| Arrays | `integer[]`, `text[]` | PostgreSQL collections |
| Enumerated | `enum` or constrained text | Finite state sets |
| Network | `inet`, `cidr` | IP addresses and networks |
| Spatial | Engine-specific | Geographic and geometric data |

Not every database supports all of these types, and equivalent types can have different semantics between engines.

## Type Selection Principles

### Model the Domain

Start with the business meaning rather than the application representation.

For example, an account balance is not simply a Python `float`. It represents a monetary value with exact decimal semantics.

Prefer:

```sql
balance numeric(19, 4) NOT NULL
```

over:

```sql
balance double precision NOT NULL
```

when exact decimal arithmetic is required.

Likewise, an IP address should not normally be stored as an arbitrary string when the database provides a native network type.

### Prefer Native Types

Native types allow the database to perform validation and operations efficiently.

For example:

```sql
CREATE TABLE api_clients (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    ip_address inet NOT NULL,
    active boolean NOT NULL DEFAULT true
);
```

This is preferable to storing `ip_address` as `text` when the application needs IP-aware operations.

### Avoid Overly Generic Types

A common anti-pattern is:

```sql
CREATE TABLE users (
    id text,
    age text,
    active text,
    created_at text
);
```

The database now cannot reliably enforce:

- Numeric semantics for `age`.
- Boolean semantics for `active`.
- Temporal semantics for `created_at`.
- Appropriate comparison and indexing behavior.

Generic types shift schema correctness into every application that accesses the database.

## Numeric Types

Numeric types fall broadly into **exact** and **approximate** representations.

| Type family | Precision model | Typical use |
|---|---|---|
| `smallint` | Exact integer | Small counters |
| `integer` | Exact integer | General integer values |
| `bigint` | Exact integer | Large identifiers/counters |
| `numeric` / `decimal` | Exact decimal | Money and precise quantities |
| `real` | Approximate | Scientific/measurement data |
| `double precision` | Approximate | Scientific/engineering calculations |

### Integer Types

PostgreSQL provides:

```sql
smallint
integer
bigint
```

They differ primarily in range and storage size.

| Type | Storage | Approximate signed range |
|---|---:|---:|
| `smallint` | 2 bytes | −32K to 32K |
| `integer` | 4 bytes | −2.1B to 2.1B |
| `bigint` | 8 bytes | −9.2E18 to 9.2E18 |

Use `integer` when the domain comfortably fits its range. Use `bigint` for identifiers or counters where long-term growth makes a 32-bit range unsuitable.

Example:

```sql
CREATE TABLE events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    retry_count integer NOT NULL DEFAULT 0
);
```

The `bigint` choice for a primary key is common in systems expected to accumulate large numbers of rows.

### Exact Decimal Types

`numeric` and `decimal` represent exact decimal values.

```sql
price numeric(12, 2) NOT NULL
```

Here:

- `12` is the maximum precision.
- `2` is the scale.
- Up to 10 digits can exist before the decimal point.
- 2 digits can exist after it.

For example:

```text
1234567890.12
```

is within `numeric(12,2)`.

Use exact decimal types for:

- Monetary values.
- Financial calculations.
- Rates requiring exact decimal representation.
- Quantities where rounding errors are unacceptable.

### Floating-Point Types

Floating-point values are approximate.

For example, repeatedly performing arithmetic with binary floating-point values can produce results that are mathematically surprising because many decimal fractions cannot be represented exactly in binary.

This makes floating-point types appropriate for many scientific and engineering workloads but risky for financial values.

### Integer Overflow

Choosing a type based only on today's values can create migration problems later.

For example:

```sql
id integer
```

may work for years and eventually approach its maximum range.

Changing a heavily indexed primary key from `integer` to `bigint` can be operationally expensive depending on the database and schema.

For high-growth tables, choose the identifier type with the expected lifetime of the system in mind.

## Character Types

Common character types include:

```sql
char(n)
varchar(n)
text
```

In PostgreSQL, `text` and unconstrained `varchar` generally have similar storage characteristics.

### `varchar(n)`

Use `varchar(n)` when the maximum length itself is a meaningful business rule.

```sql
country_code varchar(2) NOT NULL
```

The length constraint expresses a domain invariant.

### `text`

Use `text` for values where an arbitrary practical length is acceptable.

```sql
description text
```

Do not assume `varchar` is automatically faster than `text` in PostgreSQL. Type choice should represent domain semantics rather than rely on outdated performance assumptions.

### `char(n)`

Fixed-width character types can introduce padding semantics and are rarely necessary for ordinary application strings.

For most backend systems, `text` or appropriately constrained `varchar` is preferable.

## Boolean

A Boolean represents a logical state:

```sql
active boolean NOT NULL DEFAULT true
```

Boolean columns are useful for true/false attributes.

Avoid storing Boolean values as strings:

```sql
active varchar(5)
```

because values such as:

```text
true
TRUE
yes
1
active
```

can otherwise become inconsistent.

### Boolean Is Not Always the Right State Model

A Boolean becomes problematic when the domain has more than two states.

For example, an order might have:

```text
pending
paid
shipped
cancelled
```

Representing this as multiple Boolean columns:

```sql
is_paid boolean
is_shipped boolean
is_cancelled boolean
```

can permit invalid combinations.

A state column is often clearer:

```sql
status text NOT NULL
```

combined with an appropriate constraint or enum strategy.

## Date and Time Types

Temporal types require careful domain modeling.

Common concepts include:

- `date`
- `time`
- `timestamp`
- `timestamp with time zone` / `timestamptz`

### `date`

Use `date` for calendar dates without a time-of-day.

Examples:

```sql
date_of_birth date
billing_date date
contract_start_date date
```

Do not store these as timestamps if the business meaning is strictly a calendar date.

### Timestamp

A timestamp represents a date and time.

For event records, PostgreSQL commonly uses:

```sql
created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
```

`timestamp with time zone` in PostgreSQL represents an absolute instant and displays it according to the session timezone.

It does **not** store an arbitrary timezone label alongside the timestamp.

### Timezone-Aware Application Design

For distributed backend systems, a robust pattern is:

```text
Database
    ↓
Store absolute event instant
    ↓
Application
    ↓
Convert to user's/business timezone
    ↓
API/UI
```

For example, an order event should normally represent a precise instant:

```sql
created_at timestamptz NOT NULL
```

rather than storing a formatted local-time string.

### Business Dates vs Instants

Distinguish:

```text
2026-08-31
```

from:

```text
2026-08-31 14:30:00+05:30
```

The first is a calendar date. The second identifies an instant.

This distinction matters for:

- Birth dates.
- Billing periods.
- Expiration times.
- Scheduled jobs.
- Audit events.
- Distributed services.

## UUID

UUIDs provide 128-bit identifiers commonly represented as hexadecimal strings.

PostgreSQL supports a native:

```sql
uuid
```

type.

Example:

```sql
CREATE TABLE users (
    id uuid PRIMARY KEY,
    email text NOT NULL UNIQUE
);
```

UUIDs are useful when identifiers need to be generated independently across services or exposed externally without relying on sequential database IDs.

### UUID Trade-Offs

Advantages:

- Large identifier space.
- Easy distributed generation.
- No centralized ID allocator required.
- Useful for externally visible identifiers.

Limitations:

- Larger than a 32-bit or 64-bit integer.
- Random UUID layouts can produce less locality for B-tree indexes.
- Poorly designed identifier strategies can increase index and storage overhead.

For high-write systems, identifier choice should consider index locality and insertion patterns rather than only uniqueness.

## JSON and JSONB

PostgreSQL supports:

```sql
json
jsonb
```

`json` preserves the input representation, while `jsonb` stores a decomposed binary representation optimized for querying and indexing.

For application-side querying, `jsonb` is often the practical choice.

```sql
CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
```

JSON is useful for:

- Flexible metadata.
- External provider payload fragments.
- Attributes that genuinely vary by entity.
- Transitional schemas.

It should not automatically replace relational modeling.

If a field is frequently:

- Filtered.
- Joined.
- Aggregated.
- Constrained.
- Indexed.
- Used in business logic.

it is often a candidate for a normal relational column.

## Arrays

PostgreSQL supports array types:

```sql
tags text[]
```

Arrays can be appropriate for bounded collections that naturally belong to one entity.

```sql
CREATE TABLE articles (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title text NOT NULL,
    tags text[] NOT NULL DEFAULT '{}'
);
```

However, arrays should not replace a normalized child table when the collection needs independent identity, relationships, frequent joins, or complex querying.

## Enumerated Values

A domain with a finite set of values can be represented using:

- Database enums.
- Constrained text.
- Lookup/reference tables.

For example:

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status text NOT NULL CHECK (
        status IN ('pending', 'paid', 'shipped', 'cancelled')
    )
);
```

This approach is simple and keeps the allowed values close to the schema.

A reference table may be more appropriate when values are:

- Dynamic.
- Configurable.
- Associated with metadata.
- Managed by administrators.
- Referenced by other entities.

## Binary Data

PostgreSQL provides `bytea` for binary data.

```sql
payload bytea NOT NULL
```

Binary columns can store:

- Cryptographic material where appropriate.
- Small binary payloads.
- Application-specific encoded data.

Large files are often better stored in object storage such as Amazon S3, with the database storing metadata and the object key.

```text
API
 ↓
Application
 ├── PostgreSQL → metadata
 └── S3         → large object
```

This avoids turning the relational database into a general-purpose file store.

## NULL and Data Types

`NULL` does not mean zero, empty string, or false.

It represents the absence of a value or an unknown value depending on the domain semantics.

For example:

```sql
phone_number text NULL
```

means the phone number may be absent.

These values are distinct:

| Value | Meaning |
|---|---|
| `NULL` | No value / unknown |
| `''` | Empty string |
| `0` | Numeric zero |
| `false` | Boolean false |

SQL's three-valued logic means comparisons involving `NULL` require special handling.

Use:

```sql
WHERE deleted_at IS NULL
```

not:

```sql
WHERE deleted_at = NULL
```

The implications of `NULL` should be considered when designing constraints, indexes, queries, and application serialization.

## Type Conversion and Casting

Databases sometimes need to convert one type to another.

Explicit PostgreSQL casting:

```sql
SELECT '42'::integer;
```

or:

```sql
SELECT CAST('42' AS integer);
```

Implicit conversions may occur depending on the database and expression.

Avoid relying heavily on implicit casting in performance-sensitive queries because it can:

- Produce unexpected semantics.
- Cause runtime errors.
- Prevent effective index usage in some situations.
- Hide schema/application mismatches.

A particularly important production concern is ensuring that query parameters use compatible types.

## Data Types and Indexes

Data type choice affects index storage and performance.

For example:

```sql
CREATE INDEX idx_orders_customer_id
ON orders(customer_id);
```

A `bigint` key generally consumes more index space than a smaller integer key.

This matters when a table has:

- Millions of rows.
- Multiple indexes.
- Composite indexes.
- High write rates.
- Memory-constrained database instances.

The correct goal is not always "use the smallest possible type." The goal is to use a type that is **sufficiently sized for the domain without unnecessary overhead**.

## Data Types and Application Languages

Backend applications map database types into programming-language types.

A typical mapping might look like:

| SQL | Python | Typical API representation |
|---|---|---|
| `integer` | `int` | JSON number |
| `bigint` | `int` | JSON number/string depending on API constraints |
| `numeric` | `Decimal` | Usually string or carefully serialized number |
| `boolean` | `bool` | JSON boolean |
| `text` | `str` | JSON string |
| `date` | `date` | ISO date string |
| `timestamptz` | `datetime` | ISO 8601 timestamp |
| `uuid` | `UUID` | Usually string |
| `jsonb` | `dict` / `list` / scalar | JSON object/array/value |

With Python, monetary database values should normally map to `Decimal`, not `float`.

```python
from decimal import Decimal

amount = Decimal("19.99")
```

Frameworks such as Django and FastAPI provide additional schema and serialization layers, but the database remains the authoritative storage system.

## Type Design in Django

Django models expose database-oriented field types through Python classes.

Example:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.BigIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)
```

The Django field definition should match the domain and expected database behavior.

Avoid choosing a Django field only because it makes Python code convenient. Consider the resulting SQL type, constraints, indexes, and long-term data lifecycle.

## Type Design in API Services

FastAPI applications commonly use Pydantic models at the API boundary:

```python
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class OrderResponse(BaseModel):
    id: UUID
    total_amount: Decimal
    status: str
```

This creates multiple validation boundaries:

```text
Client
  ↓
API schema validation
  ↓
Application logic
  ↓
Database type + constraints
```

These layers complement each other. Application validation should provide clear client-facing errors, while database constraints protect persistent state.

## Portability Considerations

SQL is standardized, but data type implementations vary.

For example:

| Concept | PostgreSQL | MySQL | SQL Server |
|---|---|---|---|
| Large integer | `bigint` | `BIGINT` | `BIGINT` |
| Exact decimal | `numeric` / `decimal` | `DECIMAL` | `DECIMAL` |
| Boolean | `boolean` | Commonly `BOOLEAN` alias behavior varies | `BIT` |
| JSON | `json` / `jsonb` | `JSON` | `JSON` support differs |
| UUID | `uuid` | Commonly `CHAR`/`BINARY` patterns | `uniqueidentifier` |
| Binary | `bytea` | `BLOB` | `varbinary` |

If database portability is a requirement, avoid unnecessarily relying on vendor-specific types.

If PostgreSQL is a deliberate platform choice, however, native PostgreSQL types can often provide better correctness and functionality.

## Production Type-Selection Checklist

Before selecting a column type, ask:

1. What business value does the column represent?
2. What is its valid range?
3. Does precision matter?
4. Can the value be absent?
5. Does the database provide a native type?
6. Will the column be indexed?
7. Will it participate in joins?
8. How frequently will it be updated?
9. Could its range grow substantially?
10. Does the application map the type correctly?
11. Does the API serialize it safely?
12. Is database portability required?
13. Will the type make future migrations difficult?

## Common Mistakes and Pitfalls

| Mistake | Why it happens | Better approach |
|---|---|---|
| Using `text` for everything | Simplicity | Model domain semantics |
| Using floating point for money | Application language uses `float` | Use exact decimal types |
| Storing timestamps as strings | Easy serialization | Use temporal types |
| Storing IP addresses as strings | Familiar representation | Use native network types where useful |
| Choosing `integer` for every ID | Works initially | Evaluate long-term cardinality |
| Using JSON for relational data | Flexible schema | Normalize frequently queried business fields |
| Ignoring `NULL` semantics | Treating it like empty/zero | Model absence explicitly |
| Relying on implicit casts | Convenient queries | Use compatible parameter and column types |
| Overusing database-specific types | Native features are attractive | Balance capability against portability |
| Storing large files directly in DB | Centralized persistence | Consider object storage for large objects |

## Production Considerations

### Schema Evolution

Data type changes can be expensive on large tables.

Examples include:

- Increasing or changing numeric precision.
- Converting text to a constrained type.
- Changing identifier width.
- Migrating timestamp semantics.
- Converting JSON fields into relational columns.

For large production tables, evaluate whether the change requires a table rewrite, index rebuild, long-running locks, or significant replication traffic.

### Observability

Monitor type-related production failures such as:

- Numeric overflow.
- Invalid casts.
- Constraint violations.
- Serialization failures.
- Timezone inconsistencies.
- Unexpected `NULL` values.

Application logs should expose enough context to diagnose these errors without leaking sensitive data.

### High Availability and Replication

Schema changes involving data types can generate substantial write-ahead log or replication traffic.

Before a large type migration:

- Test on production-scale data.
- Estimate execution time.
- Check replication capacity.
- Monitor replica lag.
- Plan rollback or recovery.
- Consider phased migrations.

### Disaster Recovery

A type migration is a data transformation and should be treated accordingly.

For high-risk changes:

- Verify backups.
- Verify point-in-time recovery capability.
- Test restoration procedures.
- Keep migration scripts version-controlled.
- Record the exact schema version deployed.

Backups are only useful if restoration has been tested.

## Interview Traps

### `VARCHAR` vs `TEXT`

In PostgreSQL, choosing `varchar` does not automatically provide a performance advantage over `text`.

The important distinction is usually whether a maximum length is a meaningful domain constraint.

### `TIMESTAMP WITH TIME ZONE`

A timezone-aware PostgreSQL timestamp represents an instant. It does not preserve an arbitrary original timezone name such as `Asia/Kolkata` as part of the stored value.

If the original timezone itself is business data, store it separately.

### `NUMERIC` vs Floating Point

`numeric` provides exact decimal semantics. Floating-point types provide approximate binary representations and are therefore not interchangeable for financial calculations.

### `NULL` vs Empty Value

`NULL` is not equivalent to:

```text
0
''
false
```

SQL's three-valued logic makes this distinction fundamental.

### Database Type vs Application Type

A Python type annotation does not replace a database type.

```python
amount: float
```

does not mean the database should necessarily use a floating-point column.

The domain model, persistence model, and API model must each be considered.

## Key Takeaways

- **SQL data types encode domain semantics and directly affect validation, storage, indexing, querying, and long-term schema evolution.**
- **Choose types based on the business domain and expected growth; use exact numeric types for precise values such as money and appropriate temporal types for time semantics.**
- **Prefer native database types and constraints over generic strings, while recognizing when database-specific types create portability trade-offs.**
- **Treat `NULL`, casting, timezone behavior, application mappings, and serialization as first-class data-modeling concerns.**
- **For production schemas, evaluate data type choices against indexing, concurrency, migration cost, replication impact, and future scale rather than only today's requirements.**