# 02- NULL vs Empty String vs Blank Space

## Overview

`NULL`, an empty string (`''`), and a string containing only whitespace are different database states. Treating them as interchangeable creates incorrect filters, inconsistent validation, broken uniqueness rules, and ambiguous API behavior.

For a text column:

| Representation | Example | Meaning |
|---|---|---|
| `NULL` | `NULL` | No value / unknown / not applicable |
| Empty string | `''` | A known string with zero characters |
| Blank space | `' '` | A known string containing one space |
| Multiple spaces | `'   '` | A known string containing only whitespace |
| Normal text | `'Aranya'` | A known non-empty value |

The distinction matters because SQL comparisons, indexes, constraints, aggregation, and application-level validation operate on these values differently.

## Core Distinction

Consider:

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    display_name TEXT
);
```

These rows are not equivalent:

```sql
INSERT INTO users (id, display_name)
VALUES
    (1, NULL),
    (2, ''),
    (3, ' '),
    (4, '   '),
    (5, 'Aranya');
```

Conceptually:

```text
id | display_name
---+-------------
1  | NULL
2  | ''
3  | ' '
4  | '   '
5  | 'Aranya'
```

The database stores different states:

```text
NULL       → no value
''         → value exists, length = 0
' '        → value exists, length = 1
'   '      → value exists, length = 3
'Aranya'   → value exists, length = 6
```

A database does not automatically interpret whitespace-only strings as missing data.

## Why the Distinction Matters

Suppose an API receives a user's optional nickname.

These inputs can have different semantics:

```json
{}
```

```json
{"nickname": null}
```

```json
{"nickname": ""}
```

```json
{"nickname": "   "}
```

For a PATCH endpoint, they could mean:

| Input | Possible meaning |
|---|---|
| Field omitted | Do not modify the current value |
| `null` | Clear the value |
| `""` | Set an explicitly empty value |
| `"   "` | Invalid or normalized to empty |
| `"Alice"` | Set the nickname |

The correct behavior depends on the API contract, but the distinction should be intentional.

## `NULL`

`NULL` represents the absence of a known value.

```sql
INSERT INTO users (id, display_name)
VALUES (1, NULL);
```

Check it with:

```sql
SELECT *
FROM users
WHERE display_name IS NULL;
```

Do not use:

```sql
WHERE display_name = NULL;
```

because comparisons involving `NULL` produce `UNKNOWN`.

`NULL` is especially useful when the domain needs to distinguish:

```text
value not supplied
value not known
value not applicable
value has not occurred yet
```

For example:

```sql
deleted_at TIMESTAMPTZ NULL
```

can represent:

```text
deleted_at IS NULL     → not deleted
deleted_at IS NOT NULL → deleted
```

## Empty String

An empty string is a real string value containing zero characters:

```sql
SELECT LENGTH('');
```

The result is:

```text
0
```

It can be compared normally:

```sql
SELECT *
FROM users
WHERE display_name = '';
```

Unlike `NULL`:

```sql
'' = ''
```

evaluates to `TRUE`.

This makes empty strings ordinary values from SQL's comparison perspective.

## Blank Space

A blank-space value contains whitespace characters.

For example:

```sql
SELECT LENGTH(' ');
```

returns:

```text
1
```

while:

```sql
SELECT LENGTH('   ');
```

returns:

```text
3
```

The value is not empty:

```text
' ' <> ''
```

Whitespace is data unless the database or application explicitly normalizes it.

This distinction becomes particularly important with:

- User-entered names.
- Search filters.
- Email addresses.
- Tags.
- API payloads.
- CSV imports.
- ETL pipelines.

## Comparing the Three States

A useful comparison:

| Expression | `NULL` | `''` | `' '` |
|---|---:|---:|---:|
| `column IS NULL` | `TRUE` | `FALSE` | `FALSE` |
| `column = ''` | `UNKNOWN` | `TRUE` | `FALSE` |
| `column = ' '` | `UNKNOWN` | `FALSE` | `TRUE` |
| `column IS NOT NULL` | `FALSE` | `TRUE` | `TRUE` |
| `LENGTH(column) = 0` | `NULL`/`UNKNOWN` in predicate | `TRUE` | `FALSE` |
| `TRIM(column) = ''` | `UNKNOWN` | `TRUE` | `TRUE` |

The final row is particularly useful for detecting both empty and whitespace-only strings, but applying a function to a column has indexing implications.

## Detecting Empty Strings

Use:

```sql
SELECT *
FROM users
WHERE display_name = '';
```

This finds only empty strings.

It does not find:

```text
NULL
' '
'   '
```

To find empty strings and `NULL`:

```sql
SELECT *
FROM users
WHERE display_name IS NULL
   OR display_name = '';
```

If the application considers whitespace-only values equivalent to empty:

```sql
SELECT *
FROM users
WHERE display_name IS NULL
   OR TRIM(display_name) = '';
```

The last query is semantically broader and should be used only when that normalization rule is intentional.

## Detecting Whitespace-Only Values

A common PostgreSQL approach is:

```sql
SELECT *
FROM users
WHERE display_name IS NOT NULL
  AND TRIM(display_name) = '';
```

This identifies values such as:

```text
''
' '
'   '
```

but excludes:

```text
NULL
'Alice'
```

For Unicode-heavy applications, be careful about assuming that `TRIM()` handles every Unicode whitespace character exactly as your application expects. If the application uses more sophisticated Unicode normalization rules, define those rules explicitly at the application/data-processing boundary.

## Treating All "Missing Text" as One State

If the business rule is:

> A display name is considered missing when it is `NULL`, empty, or whitespace-only.

then the predicate can be written as:

```sql
WHERE display_name IS NULL
   OR BTRIM(display_name) = '';
```

PostgreSQL's `BTRIM()` removes characters from both ends according to its trimming rules.

Another compact formulation is:

```sql
WHERE NULLIF(BTRIM(display_name), '') IS NULL;
```

This works because:

```text
NULL          → NULL
''            → NULL
' '           → NULL
'   '         → NULL
'Alice'       → 'Alice'
```

Therefore only the missing/blank cases produce `NULL`.

However, the compact expression can be less obvious to readers and may have indexing implications. Prefer the clearest form for important production queries.

## `TRIM()` and Data Normalization

`TRIM()` removes leading and trailing spaces.

```sql
SELECT TRIM('  Alice  ');
```

produces:

```text
Alice
```

It does not generally mean:

> Remove every whitespace character from the string.

For example, internal whitespace is preserved:

```text
'  Alice Smith  '
       ↓
'Alice Smith'
```

This is useful for normalization but should not be confused with general-purpose Unicode whitespace normalization.

## `NULLIF()`

`NULLIF()` can convert an empty value into `NULL`.

```sql
SELECT NULLIF(display_name, '')
FROM users;
```

For:

```text
NULL → NULL
''   → NULL
' '  → ' '
```

If whitespace-only strings should also become `NULL`:

```sql
SELECT NULLIF(BTRIM(display_name), '')
FROM users;
```

This is useful during migration or ingestion when existing data contains multiple representations of "missing."

## `COALESCE()`

`COALESCE()` converts `NULL` to another value:

```sql
SELECT COALESCE(display_name, 'Anonymous')
FROM users;
```

But it does not convert empty strings or spaces:

```text
NULL → 'Anonymous'
''   → ''
' '  → ' '
```

If all missing representations should display as a fallback:

```sql
SELECT COALESCE(NULLIF(BTRIM(display_name), ''), 'Anonymous')
FROM users;
```

The processing pipeline is:

```text
display_name
     │
     ▼
   BTRIM()
     │
     ▼
 NULLIF(..., '')
     │
     ▼
 COALESCE(..., 'Anonymous')
```

This is useful for presentation logic, but do not use it to hide data-quality problems in operational queries.

## Filtering Correctly

Suppose the application should return users whose display names contain meaningful text.

A naive query:

```sql
SELECT *
FROM users
WHERE display_name IS NOT NULL;
```

is insufficient because it includes:

```text
''
' '
'   '
```

A more precise PostgreSQL query is:

```sql
SELECT *
FROM users
WHERE display_name IS NOT NULL
  AND BTRIM(display_name) <> '';
```

This excludes:

```text
NULL
''
' '
'   '
```

and retains:

```text
Alice
Alice Smith
```

## Equality and Whitespace

These values should not be assumed equal:

```sql
'Alice' = ' Alice '
```

The expression is not generally `TRUE`.

If the application defines leading and trailing whitespace as insignificant:

```sql
BTRIM(display_name) = 'Alice'
```

However, applying `BTRIM()` to the database column can prevent a normal index on `display_name` from being used directly.

For frequent normalized lookups, consider storing a canonical value or using an appropriate expression index.

## Indexing Implications

Consider:

```sql
CREATE INDEX idx_users_display_name
ON users (display_name);
```

A query such as:

```sql
WHERE display_name = :name
```

can potentially use the index efficiently.

But:

```sql
WHERE BTRIM(display_name) = :name
```

applies a function to the indexed expression.

Depending on the database and available indexes, the ordinary index may not support this predicate efficiently.

In PostgreSQL, an expression index can support the normalized lookup:

```sql
CREATE INDEX idx_users_display_name_trimmed
ON users (BTRIM(display_name));
```

Then:

```sql
SELECT *
FROM users
WHERE BTRIM(display_name) = :name;
```

can use the corresponding expression index when the planner determines it is beneficial.

For high-volume systems, prefer designing normalization intentionally rather than repeatedly transforming millions of rows at query time.

## Normalize at Write Time

For data whose canonical representation is well-defined, normalization at ingestion is often preferable.

For example, instead of allowing:

```text
NULL
''
' '
'   '
```

to represent the same business state, establish one representation.

A possible rule:

```text
missing display name → NULL
non-empty display name → trimmed canonical text
```

Then:

```text
NULL     → NULL
''       → NULL
' '      → NULL
' Alice ' → 'Alice'
```

This dramatically simplifies downstream queries.

A PostgreSQL example using a generated value or application-controlled normalization depends on the exact schema and requirements. The important principle is:

> Normalize once when the business meaning is known instead of repeatedly normalizing during every read.

## Database Constraint Strategy

Suppose a field must contain meaningful text when supplied.

A simple:

```sql
display_name TEXT
```

allows:

```text
NULL
''
' '
'   '
```

If `NULL` is allowed but blank strings are not, a PostgreSQL check constraint can enforce:

```sql
ALTER TABLE users
ADD CONSTRAINT users_display_name_not_blank
CHECK (
    display_name IS NULL
    OR BTRIM(display_name) <> ''
);
```

Now:

```text
NULL       → allowed
'Alice'    → allowed
''         → rejected
' '        → rejected
'   '      → rejected
```

This is stronger than relying only on application validation.

## `NOT NULL` Does Not Mean "Non-Blank"

This is a common mistake.

Consider:

```sql
display_name TEXT NOT NULL
```

It prevents:

```text
NULL
```

but still allows:

```text
''
' '
'   '
```

If meaningful text is required, `NOT NULL` alone is insufficient.

Use an additional constraint:

```sql
display_name TEXT NOT NULL
CHECK (BTRIM(display_name) <> '')
```

This expresses two separate invariants:

```text
NOT NULL                 → a value must exist
BTRIM(display_name) <> '' → the value must contain meaningful text
```

## PostgreSQL Example

A production-oriented table might look like:

```sql
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL,
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT users_display_name_not_blank
        CHECK (
            display_name IS NULL
            OR BTRIM(display_name) <> ''
        )
);
```

This allows:

```text
display_name = NULL
display_name = 'Alice'
display_name = 'Alice Smith'
```

and rejects:

```text
display_name = ''
display_name = ' '
display_name = '   '
```

Whether `NULL` should be allowed remains a domain decision.

## Application-Level Validation

Database constraints protect integrity, but validation should normally happen before a write so the API can return a useful error.

### Python

A simple normalization rule:

```python
def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value or None
```

This converts:

```text
None       → None
""         → None
"   "      → None
" Alice "  → "Alice"
```

The important part is not the helper itself but having one explicit canonicalization rule shared across relevant write paths.

### Django

For model validation, a nullable optional text field can be represented using Django's model configuration, but database-level constraints should still protect critical invariants.

For example:

```python
from django.db import models
from django.db.models import Q

class User(models.Model):
    display_name = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(display_name__isnull=True) | ~Q(display_name=""),
                name="display_name_not_empty",
            ),
        ]
```

For a production system where whitespace-only strings must also be rejected, ensure the database constraint matches the actual database dialect and normalization requirement rather than assuming model-level `blank=True` performs database enforcement.

## API Design

A REST API should define whether `null`, empty strings, and whitespace are accepted.

For example:

```json
{
  "display_name": "Alice"
}
```

could be the only valid representation for a populated name.

A useful contract might define:

| Input | Behavior |
|---|---|
| Field omitted | Preserve existing value on PATCH |
| `null` | Clear optional value |
| `""` | Reject or normalize to `null` |
| `"   "` | Reject or normalize to `null` |
| `" Alice "` | Normalize to `"Alice"` |
| `"Alice"` | Store `"Alice"` |

The important requirement is consistency across:

```text
API → application → ORM → database
```

Without a defined contract, different services may interpret the same payload differently.

## Data Migration

Legacy databases often contain multiple representations of missing values.

Before normalizing, inspect the distribution:

```sql
SELECT
    CASE
        WHEN display_name IS NULL THEN 'NULL'
        WHEN BTRIM(display_name) = '' THEN 'BLANK'
        ELSE 'VALUE'
    END AS category,
    COUNT(*) AS row_count
FROM users
GROUP BY 1;
```

This helps determine the scale of the cleanup.

A migration might then normalize blank values:

```sql
UPDATE users
SET display_name = NULL
WHERE display_name IS NOT NULL
  AND BTRIM(display_name) = '';
```

For large production tables, do not treat this as a trivial update. Consider:

- Transaction duration.
- Row locks.
- WAL generation.
- Replication lag.
- Vacuum requirements.
- Batch size.
- Deployment sequencing.
- Constraint validation strategy.

Test the migration against production-scale data before execution.

## Search and User Input

Search systems frequently encounter whitespace problems.

A request such as:

```text
GET /users?name=   
```

should not necessarily become:

```sql
WHERE name = '   '
```

The API layer should define whether whitespace-only search parameters are:

- Invalid.
- Treated as omitted.
- Normalized to an empty search.
- Rejected with a validation error.

For example, after normalization:

```python
name = name.strip() if name is not None else None

if not name:
    name = None
```

The resulting SQL can avoid executing an unnecessary filter.

## `NULL` vs Empty String in Aggregations

These values behave differently with `COUNT(column)`.

Suppose:

```text
display_name
------------
NULL
''
' '
Alice
```

Then:

```sql
SELECT COUNT(display_name)
FROM users;
```

counts all non-`NULL` values:

```text
3
```

The empty string and whitespace string are values, so they are counted.

If the business definition is:

> Count users with meaningful display names

then:

```sql
SELECT COUNT(*)
FROM users
WHERE display_name IS NOT NULL
  AND BTRIM(display_name) <> '';
```

This is a different metric from `COUNT(display_name)`.

## `DISTINCT` and Data Quality

Consider:

```sql
SELECT DISTINCT display_name
FROM users;
```

The database can return distinct representations such as:

```text
NULL
''
' '
'Alice'
' Alice '
```

These are different values.

If the application considers them equivalent after normalization, normalize before applying uniqueness or grouping.

For example:

```sql
SELECT DISTINCT BTRIM(display_name)
FROM users;
```

can reveal equivalent values that differ only in leading/trailing spaces.

## Uniqueness Considerations

Suppose usernames must be unique.

These values are technically different:

```text
alice
Alice
 alice
alice 
```

Whether they should represent the same username is a domain decision.

A robust design usually defines a canonical form before enforcing uniqueness.

For example:

```text
Input       → Canonical
" Alice "   → "Alice"
"alice"     → "alice"
```

If uniqueness is case-insensitive as well, case normalization or a database-specific case-insensitive strategy may be required.

Do not assume trimming, case folding, Unicode normalization, and database collation are interchangeable concerns.

## Production Best Practices

### Define One Canonical Representation

For each optional text field, explicitly decide:

```text
Missing → NULL or ''
Blank   → valid or invalid
Spaces  → preserved or normalized
Case    → significant or insignificant
Unicode → normalization requirements
```

Avoid letting different services make independent decisions.

### Validate at the Boundary

Normalize user-controlled strings as close to the input boundary as practical:

```text
HTTP request
    ↓
validation
    ↓
normalization
    ↓
application logic
    ↓
database
```

This prevents multiple internal representations from spreading through the system.

### Enforce Critical Rules in SQL

Application validation can be bypassed by:

- Admin scripts.
- Data migrations.
- Background workers.
- Other microservices.
- Direct database clients.
- Older application versions.

Use database constraints for invariants that must always hold.

### Avoid Functions on Indexed Columns Without a Plan

This pattern:

```sql
WHERE BTRIM(display_name) = :name
```

may require an expression index for efficient execution at scale.

Always inspect the actual execution plan for important queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users
WHERE BTRIM(display_name) = 'Alice';
```

Do not add indexes blindly; validate them against real workload and cardinality.

## Common Mistakes

| Mistake | Problem | Better Approach |
|---|---|---|
| Treating `NULL` as `''` | They have different SQL semantics | Define explicit representation |
| Using `= NULL` | Produces `UNKNOWN` | Use `IS NULL` |
| Assuming `NOT NULL` rejects spaces | It only rejects `NULL` | Add a blank-value constraint |
| Treating `' '` as empty | Whitespace is still data | Normalize or validate explicitly |
| Using `COALESCE(column, '')` everywhere | Hides the distinction between missing and empty | Use only when presentation/business logic requires it |
| Filtering only `IS NOT NULL` | Includes empty and whitespace-only strings | Add explicit blank handling |
| Applying `TRIM()` to indexed columns | Can prevent normal index usage | Normalize on write or use an expression index |
| Cleaning data without measuring it | Can cause unexpected production changes | Profile data before migration |
| Assuming all whitespace is ASCII space | Unicode whitespace can differ | Define application-specific normalization |
| Relying only on ORM validation | Other writers can bypass it | Enforce database invariants |
| Using empty strings as universal "missing" values | Creates ambiguous semantics | Prefer a consistent canonical representation |

## Interview Traps

### Is `NULL` the same as an empty string?

No.

```text
NULL → absence of a value
''   → a known string containing zero characters
```

They behave differently in comparisons, aggregates, constraints, and indexes.

### Does `NOT NULL` prevent blank strings?

No.

This:

```sql
display_name TEXT NOT NULL
```

still permits:

```text
''
' '
'   '
```

if no additional constraint exists.

### How do you find both `NULL` and blank strings?

For empty strings:

```sql
WHERE display_name IS NULL
   OR display_name = ''
```

For whitespace-only strings as well:

```sql
WHERE display_name IS NULL
   OR BTRIM(display_name) = ''
```

### Does `COALESCE()` convert empty strings to a fallback?

No.

```sql
COALESCE(display_name, 'Anonymous')
```

only replaces `NULL`.

To treat empty/blank values as missing:

```sql
COALESCE(NULLIF(BTRIM(display_name), ''), 'Anonymous')
```

### Why is whitespace normalization an indexing concern?

A predicate such as:

```sql
WHERE BTRIM(display_name) = :name
```

operates on a transformed expression rather than directly on the stored column. A normal index on `display_name` may therefore not be sufficient.

For PostgreSQL, an expression index can support the normalized expression:

```sql
CREATE INDEX idx_users_display_name_trimmed
ON users (BTRIM(display_name));
```

## Data Modeling Decision

Before choosing how to store optional text, answer these questions:

| Question | Example decision |
|---|---|
| Does absence have meaning? | Use `NULL` |
| Is empty text a meaningful business value? | Allow `''` |
| Should whitespace-only text be valid? | Usually reject for human-entered fields |
| Should leading/trailing whitespace matter? | Usually normalize for identifiers |
| Should case matter? | Define explicitly |
| Must every writer obey the rule? | Add database constraints |
| Is normalized lookup frequent? | Consider canonical storage or expression indexes |
| Does API omission differ from clearing? | Define PATCH semantics explicitly |

For most human-entered optional text fields, a clean production model is often:

```text
missing / blank input
        ↓
normalize
        ↓
NULL
```

and:

```text
meaningful input
        ↓
trim / validate
        ↓
canonical text
```

The exact rule depends on the domain, but consistency is more important than choosing one universal representation.

## Key Takeaways

- **`NULL`, `''`, and whitespace-only strings are distinct values with different SQL semantics; never treat them as interchangeable by accident.**
- **`NOT NULL` prevents only `NULL`; use explicit validation or database `CHECK` constraints when empty or whitespace-only text is invalid.**
- **Normalize text deliberately at the application/database boundary, especially when multiple representations of "missing" would otherwise spread through the system.**
- **Functions such as `BTRIM()` are useful for detecting or normalizing blank values but can affect index usage; use canonical storage or expression indexes for high-volume normalized lookups.**
- **Define null, empty, whitespace, omission, and clearing semantics consistently across APIs, application code, ORM models, migrations, and database constraints.**