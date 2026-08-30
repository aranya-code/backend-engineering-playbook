# 13- Common String Function Mistakes

## Overview

SQL string functions are straightforward individually, but production bugs usually come from **incorrect assumptions about `NULL`, whitespace, case, indexing, character semantics, or the location of the transformation**.

Common mistakes include applying functions unnecessarily in predicates, confusing `NULL` with an empty string, using the wrong function for the required transformation, assuming string length means byte length, and normalizing values without considering domain semantics.

These mistakes matter because string expressions frequently appear in:

- API filtering and search.
- Data validation.
- ETL and migration jobs.
- User identity lookups.
- Reporting queries.
- Data cleanup.
- Uniqueness checks.
- Legacy-system integrations.

The examples use PostgreSQL syntax where behavior is database-specific.

## Mistaking NULL for an Empty String

`NULL` means an unknown or absent value. An empty string is a value containing zero characters.

They require different SQL predicates:

```sql
WHERE email IS NULL
```

versus:

```sql
WHERE email = ''
```

They are not interchangeable.

| Value | Meaning |
|---|---|
| `NULL` | Missing/unknown value |
| `''` | Empty string |
| `' '` | One whitespace character |
| `'   '` | Multiple whitespace characters |

If the business rule considers blank strings equivalent to missing data, normalize them deliberately:

```sql
NULLIF(TRIM(email), '')
```

This converts:

```text
NULL      → NULL
''        → NULL
'   '     → NULL
' alice ' → 'alice'
```

Do not assume every application should make this conversion. Some domains distinguish an intentionally empty value from an absent value.

## Using `=` to Compare NULL

A common mistake is:

```sql
WHERE email = NULL
```

This does not identify `NULL` values.

Use:

```sql
WHERE email IS NULL
```

For PostgreSQL, when comparing nullable values and treating two `NULL`s as equal, use:

```sql
WHERE email IS NOT DISTINCT FROM $1
```

This is particularly useful when implementing nullable equality semantics.

## Applying Functions to Indexed Columns

Consider:

```sql
SELECT id
FROM users
WHERE LOWER(email) = LOWER($1);
```

A normal index on `email` may not support the expression as efficiently as an index designed for the expression.

For PostgreSQL:

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

The important principle is:

> The database needs an access path that matches the expression used by the query.

Always inspect the real execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE LOWER(email) = LOWER('alice@example.com');
```

### Better Design for High-Volume Lookups

If normalized lookup is a core domain requirement, consider making the canonical representation explicit.

Possible approaches include:

- Expression indexes.
- Generated columns where supported and appropriate.
- Dedicated normalized columns.
- Database-specific case-insensitive types or collations.

Choose based on query volume, uniqueness requirements, and domain semantics rather than blindly adding indexes.

## Using Functions in Predicates Without Considering Scale

This query:

```sql
SELECT *
FROM customers
WHERE TRIM(email) = $1;
```

may be acceptable for a small dataset.

On a large table, applying `TRIM()` to many rows can become expensive if no suitable access path exists.

The cost becomes more significant when:

- The table contains millions of rows.
- The endpoint is called frequently.
- The query runs concurrently.
- The predicate is combined with other expensive expressions.
- The result is expected to have low latency.

Do not optimize every string expression prematurely. Measure first, then design the appropriate index or canonical representation.

## Using the Wrong Function for the Job

Several functions appear similar but solve different problems.

| Requirement | Appropriate operation |
|---|---|
| Remove surrounding whitespace | `TRIM()` |
| Convert to lowercase | `LOWER()` |
| Convert to uppercase | `UPPER()` |
| Replace a substring | `REPLACE()` |
| Extract part of a string | `SUBSTRING()` |
| Count characters | `LENGTH()` |
| Count encoded bytes | `OCTET_LENGTH()` |
| Join nullable strings | `CONCAT_WS()` |
| Convert empty value to `NULL` | `NULLIF()` |
| Provide fallback | `COALESCE()` |

For example, do not use `REPLACE()` to solve a boundary-whitespace problem:

```sql
REPLACE(name, ' ', '')
```

This removes **all spaces**, potentially changing:

```text
"Alice Johnson"
```

into:

```text
"AliceJohnson"
```

If the requirement is to remove surrounding whitespace:

```sql
TRIM(name)
```

is the correct operation.

## Removing Meaningful Whitespace

A dangerous cleanup query is:

```sql
UPDATE users
SET display_name = REPLACE(display_name, ' ', '');
```

This destroys meaningful internal spaces.

For example:

```text
"Mary Jane Watson"
```

becomes:

```text
"MaryJaneWatson"
```

Use `TRIM()` when only boundary whitespace is invalid:

```sql
UPDATE users
SET display_name = TRIM(display_name);
```

If internal whitespace must also be normalized, define the rule explicitly and test it against representative data.

## Incorrect Use of UPPER and LOWER

Case conversion is not automatically a safe normalization strategy.

This may be appropriate:

```sql
LOWER(email)
```

but should not be applied indiscriminately to:

- Passwords.
- API keys.
- Access tokens.
- Cryptographic material.
- Case-sensitive identifiers.
- Signed payloads.

Case semantics belong to the domain.

A username might be case-insensitive while a secret token is explicitly case-sensitive.

## Assuming LOWER and UPPER Are Simple ASCII Operations

International text introduces additional considerations:

- Unicode characters.
- Collation.
- Locale.
- Database encoding.
- Case conversion rules.

Do not assume that every character behaves like an English alphabetic character.

For globally distributed applications, define and test the expected behavior for the application's supported languages and database configuration.

## Confusing Character Length with Byte Length

`LENGTH()` and byte-oriented length functions are not necessarily measuring the same thing.

In PostgreSQL:

```sql
SELECT LENGTH('café');
```

measures characters, while:

```sql
SELECT OCTET_LENGTH('café');
```

measures bytes in the encoded representation.

For ASCII:

```text
characters = bytes
```

For many Unicode strings:

```text
characters ≠ bytes
```

This distinction matters when:

- Enforcing UI length requirements.
- Designing protocol limits.
- Estimating storage.
- Handling external APIs with byte limits.
- Working with encoded payloads.

Do not substitute one measurement for the other without checking the requirement.

## Using SUBSTRING for Schema Problems

Suppose an application stores:

```text
ORD-2026-000184
```

and repeatedly extracts the year:

```sql
SUBSTRING(order_reference FROM 5 FOR 4)
```

This can be useful for integration or legacy data.

However, if the application frequently queries the year independently, repeatedly parsing it may indicate that the data model should expose the year separately.

A relational model could instead contain:

```text
order_type
order_year
order_sequence
```

This enables:

- Explicit constraints.
- Independent indexes.
- Simpler queries.
- Better type semantics.
- Easier validation.

String parsing is not inherently bad; using it as a permanent replacement for appropriate schema design is the problem.

## Using CONCAT Without Understanding NULL Behavior

Different concatenation mechanisms can have different `NULL` semantics.

For PostgreSQL:

```sql
SELECT CONCAT('Alice', NULL, 'Johnson');
```

produces a concatenated value while treating the `NULL` argument specially.

For the SQL concatenation operator:

```sql
SELECT 'Alice' || NULL || 'Johnson';
```

the result is `NULL`.

When optional fields are involved, `CONCAT_WS()` is often clearer:

```sql
SELECT CONCAT_WS(' ', first_name, middle_name, last_name)
FROM users;
```

Do not assume all concatenation operators and functions behave identically across database engines.

## Building Strings with Manual Separators

This is fragile:

```sql
first_name || ' ' || last_name
```

when either component may be `NULL`.

It can produce unexpected results depending on the database's concatenation semantics.

For nullable components, prefer:

```sql
CONCAT_WS(' ', first_name, last_name)
```

This expresses the intent directly: join available values with a separator.

## Treating TRIM as a Universal Whitespace Normalizer

`TRIM()` is commonly used to remove leading and trailing whitespace, but it should not be interpreted as a complete whitespace-normalization pipeline.

A value can contain:

- Leading spaces.
- Trailing spaces.
- Repeated internal spaces.
- Tabs.
- Newlines.
- Unicode whitespace characters.

If the requirement is:

```text
"  Alice    Johnson  "
```

→

```text
"Alice Johnson"
```

then a simple `TRIM()` is insufficient because it does not collapse internal whitespace.

The normalization rule must be explicit.

## Using REPLACE When Pattern Matching Is Required

`REPLACE()` performs literal replacement.

For example:

```sql
REPLACE(phone_number, '-', '')
```

removes literal hyphens.

If the requirement is more complex, such as removing every character except digits, a regular expression may be appropriate in PostgreSQL:

```sql
REGEXP_REPLACE(phone_number, '[^0-9]', '', 'g')
```

However, regex should not be the default choice.

Prefer the simplest function that satisfies the requirement because complex expressions can be harder to understand and may have higher CPU cost.

## Using Regex for Simple String Operations

This is unnecessary:

```sql
REGEXP_REPLACE(name, '^-+|-+$', '', 'g')
```

if the requirement is simply to remove a known delimiter from the beginning or end and `TRIM()` with the appropriate character set can express the intended behavior.

Similarly, prefer:

```sql
REPLACE(value, '-', '')
```

over a regex when only literal replacement is required.

Use regex when the **pattern itself** is the requirement.

## Performing Expensive String Processing During Every Request

A REST endpoint might execute:

```sql
SELECT id, name
FROM users
WHERE LOWER(TRIM(name)) LIKE '%' || LOWER(TRIM($1)) || '%';
```

This is convenient but potentially expensive at scale.

If this endpoint receives substantial traffic, investigate:

- Query frequency.
- Table cardinality.
- Search selectivity.
- Index availability.
- PostgreSQL `pg_trgm`.
- Full-text search requirements.
- Dedicated search infrastructure.

For PostgreSQL substring searches, trigram indexing may be appropriate:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX idx_users_name_trgm
ON users USING gin (name gin_trgm_ops);
```

Validate the improvement with `EXPLAIN (ANALYZE, BUFFERS)` rather than assuming an index will solve every search workload.

## Ignoring Search Semantics

These queries have very different behavior:

```sql
WHERE email = $1
```

```sql
WHERE email LIKE $1 || '%'
```

```sql
WHERE email ILIKE '%' || $1 || '%'
```

They represent:

- Exact search.
- Prefix search.
- Case-insensitive substring search.

The broader the search pattern, the harder it may be to optimize with ordinary B-tree indexes.

Do not implement substring search when the product requirement only needs exact or prefix matching.

## Concatenating Nullable Data for Business Logic

A display string is usually presentation data:

```sql
CONCAT_WS(' ', first_name, last_name)
```

It should not automatically become a business identifier.

For example, constructing:

```text
customer_key = first_name + last_name
```

is unsafe because names are:

- Non-unique.
- Mutable.
- Subject to formatting differences.
- Potentially internationalized.

Use stable identifiers such as primary keys or explicitly defined business keys for identity.

## Normalizing Data Without Defining a Canonical Representation

A system can easily end up with:

```text
Alice@example.com
 alice@example.com
ALICE@EXAMPLE.COM
alice@example.com
```

If all of these are logically the same value, the application needs a clear canonicalization strategy.

A possible PostgreSQL query-time representation is:

```sql
LOWER(TRIM(email))
```

But if uniqueness depends on that representation, the uniqueness rule must use the same semantics.

Otherwise the application can believe two values are equivalent while the database allows both.

## Ignoring Uniqueness After Normalization

Suppose an application performs:

```sql
SELECT id
FROM users
WHERE LOWER(TRIM(email)) = LOWER(TRIM($1));
```

but the database has only:

```sql
UNIQUE (email)
```

The application and database may disagree about uniqueness.

If normalized email is the domain's uniqueness rule, enforce it at the database boundary.

For PostgreSQL, an expression-based unique index can be appropriate:

```sql
CREATE UNIQUE INDEX users_email_normalized_unique
ON users (LOWER(TRIM(email)));
```

Before deploying this, clean existing duplicates and verify that the chosen normalization rule is actually correct for the business domain.

## Updating Production Data Without Previewing the Transformation

Avoid immediately executing:

```sql
UPDATE users
SET email = LOWER(TRIM(email));
```

on a large production table.

First inspect the proposed result:

```sql
SELECT
    id,
    email AS current_email,
    LOWER(TRIM(email)) AS normalized_email
FROM users
WHERE email IS DISTINCT FROM LOWER(TRIM(email))
LIMIT 100;
```

Then determine:

- How many rows change.
- Whether normalization creates duplicates.
- Whether constraints are affected.
- How much WAL the update could generate.
- Whether replicas can keep up.
- Whether the operation should be batched.

## Ignoring Duplicate Creation During Normalization

Normalization can collapse previously distinct values.

For example:

```text
Alice@example.com
alice@example.com
```

may become identical after:

```sql
LOWER(email)
```

Before adding a normalized uniqueness constraint, detect collisions:

```sql
SELECT
    LOWER(TRIM(email)) AS normalized_email,
    COUNT(*) AS row_count
FROM users
WHERE email IS NOT NULL
GROUP BY LOWER(TRIM(email))
HAVING COUNT(*) > 1;
```

This is an important migration safety check.

## Performing Large String Updates in One Transaction

A large statement such as:

```sql
UPDATE users
SET normalized_email = LOWER(TRIM(email));
```

can affect millions of rows.

Potential consequences include:

- Long transaction duration.
- Increased WAL generation.
- Lock contention.
- Replica lag.
- Table and index bloat.
- Increased disk and I/O usage.
- Difficult rollback.

For large datasets, consider controlled batching or an online migration strategy.

Monitor:

- Database CPU.
- I/O.
- Transaction duration.
- Replication lag.
- Lock waits.
- WAL growth.
- Query latency.

## Mixing Application and Database Normalization Inconsistently

A microservice architecture can accidentally produce different canonicalization rules:

```text
Service A → LOWER(TRIM(email))
Service B → LOWER(email)
Service C → raw email
```

This leads to inconsistent behavior across APIs.

Define normalization rules explicitly and enforce important invariants at the database boundary.

Application-layer normalization can still improve user experience, but it should not be the only protection for cross-service data integrity.

## Using String Functions as SQL Injection Protection

This is incorrect:

```sql
WHERE LOWER(username) = LOWER('$user_input')
```

String functions do not make interpolated SQL safe.

Use parameterized queries:

```sql
SELECT id
FROM users
WHERE LOWER(username) = LOWER($1);
```

The same principle applies whether the value is passed to:

- `LOWER()`.
- `TRIM()`.
- `REPLACE()`.
- `SUBSTRING()`.
- `LIKE`.
- Regex functions.

Parameterization is a query-construction concern, not a string-function concern.

## Ignoring User-Controlled Search Cost

Search parameters can be attacker-controlled.

A query such as:

```sql
WHERE name ILIKE '%' || $1 || '%'
```

may be expensive for large datasets, especially when combined with broad result sets.

Production APIs should consider:

- Maximum search-term length.
- Pagination limits.
- Query timeouts.
- Appropriate indexes.
- Rate limiting.
- Search-specific infrastructure where required.

The application should also avoid returning unbounded result sets.

## Interview Traps

| Trap | Correct reasoning |
|---|---|
| `email = NULL` | Use `IS NULL` |
| `TRIM()` removes all whitespace | It primarily handles leading/trailing characters |
| `LOWER(column)` always uses the normal index | The expression may require a matching expression index |
| `NULL` equals `''` | They are distinct values |
| `LENGTH()` always means bytes | Character and byte length can differ |
| `REPLACE()` is equivalent to regex replacement | `REPLACE()` performs literal substitution |
| Normalizing at the API is sufficient | Important invariants should be protected at the database boundary |
| Substring search is just a normal indexed lookup | Search pattern and index strategy matter |
| String functions prevent SQL injection | Parameterization prevents SQL injection |

## Production Checklist

Before deploying string-heavy SQL, verify:

### Correctness

- Are `NULL` and empty strings handled intentionally?
- Is case sensitivity defined by the domain?
- Is whitespace normalization explicit?
- Are Unicode and collation requirements understood?
- Does the transformation preserve meaningful data?
- Can normalization create duplicates?

### Performance

- Does a function appear around an indexed predicate column?
- Is an expression index appropriate?
- Would a generated or normalized representation be better?
- Is substring search required?
- Would `pg_trgm` or another search strategy help?
- Has the query been tested with realistic data volume?

### Data Migration

- Have affected rows been counted?
- Has the transformation been previewed?
- Have duplicate collisions been checked?
- Has transaction and WAL impact been estimated?
- Is batching required?
- Is replication lag being monitored?

### Security

- Are all dynamic values parameterized?
- Can users trigger expensive search patterns?
- Are search endpoints rate-limited where appropriate?
- Are secrets and credentials excluded from generic normalization?

### Maintainability

- Is the transformation simple enough to understand?
- Is the canonical representation documented?
- Are normalization rules consistent across services?
- Is the transformation really a database concern, or should it happen elsewhere?

## Key Takeaways

- **Do not confuse `NULL`, empty strings, and whitespace-only strings; normalize them only when the domain explicitly defines them as equivalent.**
- **String functions inside predicates can affect index usage and query cost, so align normalization strategies with appropriate indexes or canonical representations.**
- **Do not use string functions as substitutes for schema design, security controls, or domain rules such as uniqueness and identity.**
- **Treat large string transformations as production database operations: preview changes, detect duplicate collisions, assess WAL and replication impact, and execute safely.**
- **Choose the simplest correct string operation, and explicitly account for case sensitivity, Unicode, search semantics, and character-versus-byte behavior.**