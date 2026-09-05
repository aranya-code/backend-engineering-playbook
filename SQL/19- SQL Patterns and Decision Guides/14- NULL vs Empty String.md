# 14- NULL vs Empty String

## Overview

`NULL` and an empty string (`''`) both represent "missing-looking" values in application data, but they have fundamentally different SQL semantics.

- `NULL` means the value is unknown, missing, or not applicable.
- `''` is an actual string value containing zero characters.

They behave differently in:

- Comparisons.
- Filtering.
- `ORDER BY`.
- Aggregation.
- Constraints.
- Indexes.
- Unique constraints.
- API serialization.
- ORM behavior.
- Data validation.

For example:

```sql
SELECT *
FROM customers
WHERE email = '';
```

matches rows containing an actual empty string.

This does **not** match `NULL` values.

To find `NULL`:

```sql
SELECT *
FROM customers
WHERE email IS NULL;
```

A production database should have an intentional semantic distinction between "missing" and "present but empty" rather than allowing clients and services to use the two interchangeably.

---

## NULL vs Empty String

| Property | `NULL` | `''` |
|---|---|---|
| Represents | Missing/unknown/not applicable | Known string with zero characters |
| Data type | Special SQL null marker | `text`/`varchar` value |
| `= ''` | Does not match | Matches |
| `IS NULL` | Matches | Does not match |
| `IS NOT NULL` | Does not match | Matches |
| `LENGTH()` | Usually `NULL` | `0` |
| `COALESCE(value, 'x')` | Returns `'x'` | Returns `''` |
| Storage | Null representation | Actual string value |
| Counts with `COUNT(column)` | Excluded | Included |
| Meaning | Absence | Present value |

The distinction is especially important for backend APIs where:

```json
{
  "middle_name": null
}
```

and:

```json
{
  "middle_name": ""
}
```

may have different business meanings.

---

## What NULL Means

`NULL` is not:

- Zero.
- An empty string.
- `False`.
- The literal string `"NULL"`.

It represents the absence of a usable value according to SQL's null semantics.

For example:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    email text,
    phone text
);
```

A customer with no known phone number may have:

```text
phone = NULL
```

This means:

> There is no stored phone value.

It does not mean:

```text
phone = ''
```

---

## What an Empty String Means

An empty string is a valid string value:

```sql
''
```

Its length is zero:

```sql
SELECT LENGTH('');
```

Result:

```text
0
```

It can be compared normally:

```sql
SELECT '' = '';
```

Result:

```text
true
```

An empty string therefore means:

> The application explicitly stored a string containing zero characters.

Whether that is meaningful depends on the domain.

---

## NULL Uses Three-Valued Logic

SQL uses three-valued logic for expressions involving `NULL`:

```text
TRUE
FALSE
UNKNOWN
```

For example:

```sql
SELECT NULL = NULL;
```

The result is not `TRUE`.

It is:

```text
UNKNOWN
```

Similarly:

```sql
SELECT NULL = '';
```

returns `UNKNOWN`.

This is why this query is incorrect for finding missing values:

```sql
SELECT *
FROM customers
WHERE phone = NULL;
```

Use:

```sql
SELECT *
FROM customers
WHERE phone IS NULL;
```

---

## NULL Comparison Rules

Consider:

```sql
CREATE TABLE example (
    id integer,
    value text
);

INSERT INTO example (id, value)
VALUES
    (1, NULL),
    (2, ''),
    (3, 'hello');
```

Then:

```sql
SELECT id
FROM example
WHERE value = '';
```

returns:

```text
2
```

Whereas:

```sql
SELECT id
FROM example
WHERE value IS NULL;
```

returns:

```text
1
```

And:

```sql
SELECT id
FROM example
WHERE value IS NOT NULL;
```

returns:

```text
2
3
```

---

## `NULL` Is Not Equal to Anything

A common mistake is:

```sql
WHERE column <> 'active'
```

assuming this returns every row that is not `'active'`.

Rows where `column` is `NULL` do not satisfy the predicate because:

```text
NULL <> 'active'
```

evaluates to:

```text
UNKNOWN
```

If the intended meaning is:

> Return values other than `'active'`, including missing values.

then write the condition explicitly:

```sql
WHERE status <> 'active'
   OR status IS NULL;
```

---

## Empty String Filtering

To find empty strings:

```sql
SELECT *
FROM customers
WHERE phone = '';
```

To find either `NULL` or empty string:

```sql
SELECT *
FROM customers
WHERE phone IS NULL
   OR phone = '';
```

For text values where whitespace-only values should also be considered empty:

```sql
SELECT *
FROM customers
WHERE phone IS NULL
   OR BTRIM(phone) = '';
```

Be careful with this pattern because it changes the business definition of "empty."

For example:

```text
'   '
```

is not technically an empty string.

---

## `NULLIF`

`NULLIF` is useful when an empty string should be normalized to `NULL`:

```sql
SELECT NULLIF(phone, '')
FROM customers;
```

Examples:

```sql
SELECT
    NULLIF('', '') AS result_1,
    NULLIF('123456', '') AS result_2;
```

Conceptually:

```text
NULLIF(value, '')
    ↓
if value = ''
    return NULL
else
    return value
```

This is useful during migrations and data cleanup.

---

## Combining `NULLIF` and `COALESCE`

A common normalization pattern is:

```sql
COALESCE(NULLIF(BTRIM(phone), ''), 'Unknown')
```

The processing is:

```text
' 123456 '
    ↓
BTRIM
    ↓
'123456'
    ↓
NULLIF(..., '')
    ↓
'123456'
    ↓
COALESCE
    ↓
'123456'
```

For:

```text
'   '
```

the result becomes:

```text
'Unknown'
```

For:

```text
NULL
```

the result also becomes:

```text
'Unknown'
```

This is useful for presentation, but it does not replace proper schema design.

---

## `COALESCE` Behavior

`COALESCE` returns the first non-`NULL` expression:

```sql
SELECT COALESCE(phone, 'Unknown')
FROM customers;
```

Important:

```sql
SELECT COALESCE('', 'Unknown');
```

returns:

```text
''
```

It does **not** return:

```text
'Unknown'
```

because an empty string is not `NULL`.

If both should be considered missing:

```sql
SELECT COALESCE(NULLIF(phone, ''), 'Unknown')
FROM customers;
```

---

## Aggregation Differences

`NULL` and empty strings behave differently with aggregates.

Consider:

```text
value
-----
NULL
''
'abc'
```

Then:

```sql
SELECT COUNT(value)
FROM example;
```

counts non-`NULL` values:

```text
2
```

The empty string is counted.

But:

```sql
SELECT COUNT(*)
FROM example;
```

returns:

```text
3
```

`COUNT(*)` counts rows regardless of nullability.

---

## String Aggregation

`NULL` can also affect string aggregation.

For example:

```sql
SELECT string_agg(value, ',')
FROM example;
```

PostgreSQL's `string_agg` ignores `NULL` input values, while an empty string is still an actual value and contributes its separator position.

The distinction becomes important when generating:

- CSV output.
- Search indexes.
- Reports.
- Export files.
- API representations.

Always define whether missing values should be omitted or represented explicitly.

---

## `LENGTH` and String Functions

For an empty string:

```sql
SELECT LENGTH('');
```

returns:

```text
0
```

For `NULL`:

```sql
SELECT LENGTH(NULL::text);
```

returns:

```text
NULL
```

This pattern:

```sql
WHERE LENGTH(name) = 0
```

therefore does not match `NULL`.

If both states should be treated as missing:

```sql
WHERE name IS NULL
   OR LENGTH(name) = 0;
```

or:

```sql
WHERE NULLIF(BTRIM(name), '') IS NULL;
```

---

## CASE Expressions

`CASE` can distinguish the states explicitly:

```sql
SELECT
    CASE
        WHEN phone IS NULL THEN 'missing'
        WHEN phone = '' THEN 'empty'
        ELSE 'present'
    END AS phone_state
FROM customers;
```

This is useful when the distinction has business meaning.

Avoid hiding domain semantics behind generic fallback expressions when downstream logic needs to know whether the value was:

```text
missing
empty
present
```

---

## WHERE vs COALESCE

This query:

```sql
WHERE COALESCE(phone, '') = '';
```

finds both:

```text
NULL
''
```

but applying a function to a column in a predicate can affect index usage depending on the query and available indexes.

Prefer explicit predicates when possible:

```sql
WHERE phone IS NULL
   OR phone = '';
```

If normalization through an expression is central to the workload, consider whether an expression index is justified.

For example:

```sql
CREATE INDEX idx_customers_normalized_phone
ON customers (NULLIF(BTRIM(phone), ''));
```

Do not add expression indexes without workload evidence.

---

## Schema Design

The most important decision is usually not how to query `NULL` and `''`, but whether both states should exist at all.

Suppose:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    email text
);
```

Ask:

> Is an empty email meaningfully different from an unknown email?

If not, allowing both:

```text
NULL
''
```

creates unnecessary state combinations.

A cleaner model may be:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    email text
);
```

with application validation ensuring that missing email values are stored as `NULL`.

If email is mandatory:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    email text NOT NULL
);
```

The database constraint should reflect the actual business invariant.

---

## NULL vs NOT NULL

`NOT NULL` answers:

> Can this column have no value?

It does not mean:

> Can this column contain an empty string?

For example:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    display_name text NOT NULL
);
```

This is valid:

```sql
INSERT INTO customers (id, display_name)
VALUES (1, '');
```

`NOT NULL` rejects only:

```sql
NULL
```

If an empty string is also invalid, the schema needs an additional constraint.

---

## Preventing Empty Strings

For a required text value:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    display_name text NOT NULL,
    CONSTRAINT customers_display_name_not_blank
        CHECK (BTRIM(display_name) <> '')
);
```

This prevents:

```text
NULL
''
'   '
```

while allowing:

```text
'Alice'
```

The combination is important:

```text
NOT NULL
+
CHECK
```

because the `CHECK` expression alone does not necessarily enforce non-nullability.

---

## Normalizing on Write

A strong production approach is to normalize input before persistence.

For example:

```text
API request
    ↓
Validation
    ↓
Normalize whitespace
    ↓
Convert blank → NULL
    ↓
Database
```

If blank and missing have the same domain meaning:

```python
def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    return value or None
```

Then:

```python
phone = normalize_optional_text(payload.get("phone"))
```

This creates a consistent representation.

The exact policy should be domain-specific. Some fields legitimately distinguish empty from missing.

---

## Django Models

Django has an important distinction between `null` and `blank`.

For example:

```python
class Customer(models.Model):
    phone = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )
```

Conceptually:

- `null=True` controls database `NULL`.
- `blank=True` controls validation behavior.

They are not interchangeable.

For string fields, Django commonly recommends avoiding `null=True` and using an empty string to represent no data, but this is a convention rather than a universal rule. If the domain requires a distinct SQL `NULL` state, model the distinction intentionally.

For an engineering playbook, the important rule is:

> Decide whether missing, blank, and unknown are distinct domain states before choosing ORM options.

---

## FastAPI and Pydantic

An optional API field might be represented as:

```python
from pydantic import BaseModel


class CustomerUpdate(BaseModel):
    phone: str | None = None
```

But there can be multiple API semantics:

```json
{}
```

versus:

```json
{
  "phone": null
}
```

versus:

```json
{
  "phone": ""
}
```

These may mean:

```text
field omitted
    ↓
do not modify

field = null
    ↓
clear existing value

field = ""
    ↓
set empty string
```

For update APIs, distinguish these states deliberately.

Do not automatically collapse them if PATCH semantics depend on the difference.

---

## REST API Semantics

Consider:

```http
PATCH /customers/123
```

with:

```json
{
  "phone": null
}
```

This may mean:

> Remove the phone number.

Whereas:

```json
{
  "phone": ""
}
```

may mean:

> Set the phone field to an empty string.

If the database normalizes both to `NULL`, the API contract should explicitly document that behavior.

Consistency across:

```text
REST
Python
Django/FastAPI
PostgreSQL
events
caches
```

is more important than choosing one representation blindly.

---

## PostgreSQL Empty Strings

PostgreSQL treats:

```sql
''
```

as a normal zero-length string.

For example:

```sql
SELECT ''::text;
```

is valid.

This differs from Oracle, where empty character strings have historically been treated as `NULL` for character datatypes.

When designing portable SQL, do not assume that all databases have identical empty-string semantics.

For PostgreSQL-centric systems, treat:

```text
NULL
```

and:

```text
''
```

as distinct values.

---

## Unique Constraints

This distinction can affect uniqueness.

Consider:

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    external_id text UNIQUE
);
```

PostgreSQL permits multiple `NULL` values under a normal unique constraint because `NULL` values are not considered equal for ordinary uniqueness semantics.

For example:

```text
NULL
NULL
NULL
```

can coexist.

But multiple empty strings:

```text
''
''
```

conflict with a normal unique constraint.

This can create unexpected behavior if an application inconsistently uses `NULL` and `''` for "no external ID."

---

## Partial Unique Index

If the business rule is:

> External IDs must be unique when present.

a useful PostgreSQL design is:

```sql
CREATE UNIQUE INDEX users_external_id_unique
ON users (external_id)
WHERE external_id IS NOT NULL;
```

If empty strings are also considered absent, normalize them first or use an appropriate expression:

```sql
CREATE UNIQUE INDEX users_external_id_unique
ON users (NULLIF(BTRIM(external_id), ''))
WHERE NULLIF(BTRIM(external_id), '') IS NOT NULL;
```

This should be used only when the database-level semantics match the domain rule.

---

## Indexing and NULL

B-tree indexes in PostgreSQL can index `NULL` values.

Therefore, a query such as:

```sql
SELECT *
FROM customers
WHERE phone IS NULL;
```

can potentially use an appropriate index.

Whether it actually does depends on:

- Table size.
- Null fraction.
- Statistics.
- Query cost.
- Index structure.
- Visibility.
- Other predicates.

Do not assume:

```text
IS NULL → sequential scan
```

or:

```text
IS NULL → index scan
```

without checking the execution plan.

---

## Partial Index for Missing Values

If queries frequently target missing values:

```sql
SELECT id
FROM customers
WHERE phone IS NULL;
```

a partial index can sometimes be appropriate:

```sql
CREATE INDEX idx_customers_missing_phone
ON customers (id)
WHERE phone IS NULL;
```

This can be much smaller than a full-column index when only a subset of rows is relevant.

As always, validate with real workload measurements.

---

## Data Migration

Legacy systems often contain mixed representations:

```text
NULL
''
' '
'   '
'unknown'
'N/A'
```

A cleanup migration should not blindly convert everything.

First measure:

```sql
SELECT
    COUNT(*) FILTER (WHERE phone IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE phone = '') AS empty_count,
    COUNT(*) FILTER (WHERE BTRIM(phone) = '') AS blank_count,
    COUNT(*) FILTER (WHERE phone = 'unknown') AS unknown_count
FROM customers;
```

Then determine the domain mapping.

For example:

```text
NULL       → missing
''         → missing
'   '      → missing
'unknown'  → unknown
'N/A'      → not applicable
```

The mapping should be agreed upon before destructive normalization.

---

## Safe Normalization Migration

For a large table:

```sql
UPDATE customers
SET phone = NULL
WHERE phone IS NOT NULL
  AND BTRIM(phone) = '';
```

For millions of rows, avoid assuming a single massive transaction is harmless.

Consider:

- Batch updates.
- Lock duration.
- WAL generation.
- Replication lag.
- Dead tuples.
- Autovacuum behavior.
- Application traffic.

After large changes, inspect table health and query performance.

---

## NULL and Soft Deletes

Soft-delete columns often use:

```sql
deleted_at timestamptz NULL
```

where:

```text
NULL       → active
timestamp  → deleted
```

An empty string is inappropriate for a timestamp column.

For text-based status fields, however, the same principle applies:

```text
NULL
''
```

should not be used interchangeably without a defined semantic model.

Prefer typed columns and explicit state representation where possible.

---

## NULL in JOINs

`NULL` behavior becomes especially important with outer joins.

Example:

```sql
SELECT
    c.id,
    p.phone
FROM customers AS c
LEFT JOIN customer_phones AS p
    ON p.customer_id = c.id;
```

If no phone exists:

```text
p.phone = NULL
```

The query does not produce:

```text
p.phone = ''
```

unless the query explicitly converts it.

For presentation:

```sql
SELECT
    c.id,
    COALESCE(p.phone, '') AS phone
FROM customers AS c
LEFT JOIN customer_phones AS p
    ON p.customer_id = c.id;
```

But this conversion should generally happen at the presentation boundary rather than changing the stored relational meaning.

---

## Filtering a LEFT JOIN

This distinction matters when filters are applied.

Consider:

```sql
SELECT c.id
FROM customers AS c
LEFT JOIN customer_profiles AS p
    ON p.customer_id = c.id
WHERE p.nickname <> '';
```

Customers without a profile have:

```text
p.nickname = NULL
```

and therefore fail the predicate.

If the intended semantics are different, make them explicit.

For example:

```sql
WHERE p.nickname IS NULL
   OR p.nickname <> '';
```

Do not assume a `LEFT JOIN` automatically means rows with missing related data will survive every `WHERE` condition.

---

## Search Queries

Suppose a customer search should ignore missing names.

This is different from searching for an empty string:

```sql
WHERE name = '';
```

For optional text search:

```sql
WHERE name IS NOT NULL
  AND BTRIM(name) <> '';
```

For normalized search:

```sql
WHERE NULLIF(BTRIM(name), '') IS NOT NULL;
```

For user-provided search terms, parameterize the value and define how blank input should behave before constructing the query.

---

## Full-Text and Search Indexes

If text columns feed:

- PostgreSQL full-text search.
- Elasticsearch/OpenSearch.
- Redis search structures.
- External indexing pipelines.

inconsistent representations can create different indexing behavior.

For example:

```text
NULL
''
'   '
```

may produce different application-level decisions even when the user considers all three "no name."

Normalize the representation before publishing data to downstream systems.

---

## Redis Caches

If PostgreSQL stores:

```text
phone = NULL
```

but the API serializes it as:

```json
"phone": ""
```

a Redis cache may contain yet another representation.

This creates potential inconsistencies:

```text
PostgreSQL
    ↓
NULL

API response
    ↓
""

Redis
    ↓
missing key
```

Define a consistent contract for:

- Database representation.
- Cache representation.
- API representation.
- Event representation.

Do not let each layer independently decide what "missing" means.

---

## Kafka Events

Events should distinguish states when the distinction matters.

For example:

```json
{
  "customer_id": 123,
  "phone": null
}
```

may mean:

> Phone number was cleared.

But an omitted field may mean:

> Phone number was not part of this event.

These are different event semantics.

For event-driven systems, document whether:

```text
field omitted
field = null
field = ""
```

represent different operations.

This is particularly important for partial-update events and consumers maintaining their own read models.

---

## Security Considerations

`NULL` versus empty strings can affect authorization logic when a value is used as an access-control attribute.

For example:

```sql
WHERE organization_id = $1
```

must not be replaced with a generic fallback that accidentally changes authorization semantics.

Avoid patterns such as:

```sql
WHERE COALESCE(organization_id, '') = $1;
```

unless that behavior is explicitly required.

Authorization predicates should be:

- Explicit.
- Tenant-aware.
- Parameterized.
- Tested for `NULL` cases.

A missing security attribute should not accidentally become a valid default tenant, role, or permission value.

---

## Reliability Considerations

Inconsistent representations create hidden state combinations.

Suppose an application expects:

```text
phone IS NULL
```

to mean missing.

A legacy service writes:

```text
phone = ''
```

Now different services may disagree about whether the customer has a phone.

This can affect:

- Notification delivery.
- Search.
- Data exports.
- Analytics.
- Deduplication.
- Event processing.
- Cache invalidation.

Schema constraints and centralized normalization reduce this class of distributed inconsistency.

---

## Testing

Test all meaningful states explicitly.

For an optional string:

```text
NULL
''
'   '
valid value
```

For API updates:

```text
field omitted
field = null
field = ""
field = valid value
```

Test both database and application behavior.

Example SQL test cases:

```sql
SELECT
    value,
    value IS NULL AS is_null,
    value = '' AS is_empty
FROM example;
```

Integration tests should verify that:

```text
API → ORM → PostgreSQL → event → cache → API
```

preserves the intended semantics.

---

## Common Mistakes

### Using `= NULL`

Incorrect:

```sql
WHERE phone = NULL;
```

Correct:

```sql
WHERE phone IS NULL;
```

### Assuming `NULL` Equals Empty String

Incorrect:

```sql
COALESCE(phone, 'Unknown')
```

does not treat `''` as missing.

Use:

```sql
COALESCE(NULLIF(phone, ''), 'Unknown')
```

when that is actually the intended rule.

### Using `NOT NULL` to Reject Blank Strings

`NOT NULL` rejects only `NULL`.

Use a `CHECK` constraint if blank strings are invalid.

### Mixing Representations Across Services

One service writes:

```text
NULL
```

while another writes:

```text
''
```

for the same domain state.

Define and enforce a canonical representation.

### Using `DISTINCT` or Other Query Tricks to Hide Data Problems

If duplicate-looking records are caused by inconsistent data modeling, query-level workarounds can hide the underlying problem.

### Converting NULL to Empty String Too Early

A query such as:

```sql
COALESCE(phone, '')
```

may be appropriate for presentation but can destroy information needed by downstream logic.

### Forgetting `NULL` in Negative Predicates

This:

```sql
WHERE status <> 'active'
```

does not include `NULL`.

Handle the `NULL` state explicitly when required.

### Assuming `LEFT JOIN` Preserves NULL Rows Through Every Filter

A `WHERE` predicate on the nullable side can eliminate rows produced by the outer join.

### Treating Whitespace as Automatically Empty

`' '` is not the same value as `''`.

Use `BTRIM` only when whitespace normalization is part of the business rule.

### Using Empty Strings as Sentinel Values

Values such as:

```text
''
'unknown'
'N/A'
'-'
```

often indicate missing or special states that should be modeled explicitly.

---

## Production Decision Matrix

| Requirement | Recommended approach |
|---|---|
| Value genuinely unknown | `NULL` |
| Value explicitly absent | `NULL` when domain treats absence as no value |
| Valid zero-length string | `''` |
| Required non-blank text | `NOT NULL` + `CHECK` |
| Blank and missing have same meaning | Normalize to one representation |
| User-facing fallback | `COALESCE` at presentation/query boundary |
| Convert empty to missing | `NULLIF` |
| Ignore whitespace-only values | `NULLIF(BTRIM(value), '')` |
| Unique value only when present | Partial unique index where appropriate |
| API omitted vs clear | Preserve distinct PATCH semantics if required |
| Event field omitted vs null | Define event contract explicitly |

---

## Senior Engineering Guidance

The strongest production design is usually:

```text
Define domain semantics
        ↓
Choose canonical representation
        ↓
Enforce database invariants
        ↓
Normalize application input
        ↓
Preserve semantics in APIs/events
        ↓
Convert for presentation only when needed
```

Do not begin with:

> Should I use `NULL` or `''`?

Begin with:

> What states does this business attribute actually have?

For example, a phone number might have:

```text
unknown
not applicable
known
```

That may require more than a simple `NULL`/empty-string distinction.

Sometimes the correct model is:

```sql
phone text,
phone_status text NOT NULL
```

with a constraint controlling valid combinations.

The database should model business states rather than forcing domain semantics into string conventions.

---

## Key Takeaways

- **`NULL` represents missing/unknown data, while `''` is a real zero-length string; SQL treats them as fundamentally different values.**
- **Use `IS NULL`/`IS NOT NULL` for null checks, and remember that ordinary comparisons involving `NULL` produce `UNKNOWN`.**
- **`NOT NULL` does not reject empty or whitespace-only strings; use explicit validation or `CHECK` constraints when blank values are invalid.**
- **Normalize missing values consistently across PostgreSQL, Python/Django/FastAPI, APIs, caches, and Kafka events when the domain does not distinguish them.**
- **Model the actual business states first; use `NULL`, empty strings, status columns, or constraints according to domain semantics rather than convention.**