# 03- LENGTH and Character Functions

## Overview

Character functions operate on text values to measure, inspect, transform, or normalize strings. `LENGTH()` is one of the most commonly used functions because string length affects validation, storage, indexing, API contracts, search behavior, and data quality.

For backend systems, the important distinction is between **characters**, **bytes**, and sometimes **display width**. These are not interchangeable, particularly with Unicode data.

This document focuses on `LENGTH()` and closely related character-oriented functions, using PostgreSQL syntax where database behavior is implementation-specific.

## LENGTH

`LENGTH()` returns the length of a string.

```sql
SELECT LENGTH('backend');
```

Result:

```text
7
```

For a table:

```sql
SELECT
    id,
    username,
    LENGTH(username) AS username_length
FROM users;
```

This is useful for:

- Validation.
- Data-quality checks.
- Reporting.
- Detecting unexpectedly large values.
- Building derived query values.
- Diagnosing malformed input.

### Why It Exists

String length is frequently a business or technical constraint.

Examples include:

- Username must contain at least 3 characters.
- Country code must contain exactly 2 characters.
- External reference must not exceed 64 characters.
- Free-form text should remain below an operational limit.

SQL can evaluate these constraints close to the data rather than transferring every row to application code.

## Character Length vs Byte Length

One of the most important distinctions is:

> Character count is not necessarily byte count.

Consider Unicode:

```sql
SELECT
    LENGTH('café') AS character_length,
    OCTET_LENGTH('café') AS byte_length;
```

In PostgreSQL with UTF-8 encoding, the character count and byte count can differ because characters such as `é` may require multiple bytes.

A more explicit example:

```sql
SELECT
    LENGTH('你好') AS character_length,
    OCTET_LENGTH('你好') AS byte_length;
```

`LENGTH()` measures characters, while `OCTET_LENGTH()` measures bytes.

| Function | Measures | Typical Use |
|---|---|---|
| `LENGTH()` | Characters | Text validation and display-oriented limits |
| `CHAR_LENGTH()` | Characters | SQL-standard spelling |
| `CHARACTER_LENGTH()` | Characters | SQL-standard spelling |
| `OCTET_LENGTH()` | Bytes | Storage/protocol-oriented checks |
| `BIT_LENGTH()` | Bits | Low-level binary/text representation analysis |

For PostgreSQL, `LENGTH(text)` returns the number of characters, while `OCTET_LENGTH(text)` returns the number of bytes.

## LENGTH and Unicode

Unicode makes naive length assumptions dangerous.

For example:

```sql
SELECT LENGTH('é');
```

returns one character.

But the UTF-8 representation can occupy more than one byte.

Likewise, some visually perceived characters are composed of multiple Unicode code points.

For example, an accented character may be represented either as:

```text
é
```

or as:

```text
e + combining acute accent
```

A database character-count function may therefore count the underlying character/code-point representation rather than what a user visually perceives as one grapheme.

This matters when implementing:

- User-facing character limits.
- SMS/message limits.
- Search normalization.
- Internationalized applications.
- Storage/protocol limits.

For strict UI-visible limits, application-layer Unicode/grapheme-aware processing may be more appropriate.

## CHAR_LENGTH and CHARACTER_LENGTH

SQL provides standard spellings:

```sql
SELECT CHAR_LENGTH(username)
FROM users;
```

and:

```sql
SELECT CHARACTER_LENGTH(username)
FROM users;
```

In PostgreSQL, these are equivalent to character-oriented `LENGTH()` for text.

Using the standard forms can make intent explicit and improve portability across SQL implementations.

```sql
SELECT
    username,
    CHAR_LENGTH(username) AS username_length
FROM users;
```

## LENGTH with NULL

`NULL` represents an unknown or absent value.

Therefore:

```sql
SELECT LENGTH(NULL);
```

returns:

```text
NULL
```

It does not return `0`.

This distinction matters when writing validation logic.

Consider:

```sql
SELECT *
FROM users
WHERE LENGTH(username) < 3;
```

Rows where `username IS NULL` do not satisfy this predicate because:

```text
LENGTH(NULL) → NULL
NULL < 3     → UNKNOWN
```

SQL's three-valued logic means only `TRUE` rows pass the `WHERE` clause.

If NULL should be treated as an empty string for a particular business rule:

```sql
SELECT *
FROM users
WHERE LENGTH(COALESCE(username, '')) < 3;
```

However, do not use `COALESCE()` automatically. `NULL` and an empty string can represent different business states.

## Empty String vs NULL

These are distinct concepts:

```sql
SELECT
    LENGTH('') AS empty_length,
    LENGTH(NULL) AS null_length;
```

Conceptually:

| Input | Meaning | `LENGTH()` |
|---|---|---:|
| `''` | Empty string | `0` |
| `NULL` | Missing/unknown value | `NULL` |
| `'abc'` | Three-character string | `3` |

This distinction is important in backend APIs.

For example:

```text
username = null
```

could mean the field was not provided, while:

```text
username = ""
```

could mean the client explicitly supplied an empty value.

Do not collapse these states unless the application contract requires it.

## LENGTH in WHERE

Length-based filtering is straightforward:

```sql
SELECT
    id,
    username
FROM users
WHERE LENGTH(username) > 20;
```

This can be useful for data-quality analysis.

For validation:

```sql
SELECT
    id,
    username
FROM users
WHERE LENGTH(username) BETWEEN 3 AND 30;
```

The expression operates on each candidate row.

### Important Performance Consideration

A predicate such as:

```sql
WHERE LENGTH(username) > 20
```

applies a function to the column.

A normal index on:

```sql
CREATE INDEX idx_users_username ON users (username);
```

does not automatically provide an efficient index strategy for every `LENGTH(username)` predicate.

If this becomes a high-frequency query, inspect the execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE LENGTH(username) > 20;
```

Possible approaches include:

- Expression indexes.
- Generated columns.
- Explicit constraints.
- Data-model changes.
- Precomputed metadata where justified.

Do not add an index without validating the workload and execution plan.

## LENGTH in ORDER BY

Length can be used to sort results:

```sql
SELECT
    id,
    username,
    LENGTH(username) AS username_length
FROM users
ORDER BY LENGTH(username) DESC;
```

This can be useful for:

- Finding unusually long values.
- Data-quality reports.
- Operational investigations.
- Profiling imported data.

If the length is also selected, the expression can sometimes be reused depending on the database optimizer:

```sql
SELECT
    id,
    username,
    LENGTH(username) AS username_length
FROM users
ORDER BY username_length DESC;
```

For portability and maintainability, verify alias behavior against the target SQL dialect.

## LENGTH with GROUP BY

Length functions can be combined with aggregation:

```sql
SELECT
    LENGTH(username) AS username_length,
    COUNT(*) AS user_count
FROM users
GROUP BY LENGTH(username)
ORDER BY username_length;
```

This produces a distribution of username lengths.

A more operationally useful report might bucket values:

```sql
SELECT
    CASE
        WHEN LENGTH(username) < 5 THEN 'short'
        WHEN LENGTH(username) <= 10 THEN 'normal'
        ELSE 'long'
    END AS length_category,
    COUNT(*) AS user_count
FROM users
GROUP BY
    CASE
        WHEN LENGTH(username) < 5 THEN 'short'
        WHEN LENGTH(username) <= 10 THEN 'normal'
        ELSE 'long'
    END;
```

This pattern is useful when profiling production data without exporting all records to application code.

## LENGTH and TRIM

Whitespace can affect string length.

```sql
SELECT
    LENGTH('  Alice  ') AS raw_length,
    LENGTH(TRIM('  Alice  ')) AS trimmed_length;
```

`TRIM()` removes leading and trailing whitespace according to the database's semantics.

For validation:

```sql
SELECT *
FROM users
WHERE LENGTH(TRIM(username)) < 3;
```

This can detect values such as:

```text
"  "
```

that technically contain characters but are not meaningful input.

A stronger check can explicitly reject whitespace-only values:

```sql
SELECT *
FROM users
WHERE NULLIF(TRIM(username), '') IS NULL;
```

This converts an empty result after trimming into `NULL`, making the business condition explicit.

## Common Character Functions

`LENGTH()` is normally used alongside other string functions.

| Function | Purpose | Example |
|---|---|---|
| `LENGTH()` | Character length | `LENGTH(name)` |
| `CHAR_LENGTH()` | Character length | `CHAR_LENGTH(name)` |
| `OCTET_LENGTH()` | Byte length | `OCTET_LENGTH(name)` |
| `LOWER()` | Convert to lowercase | `LOWER(email)` |
| `UPPER()` | Convert to uppercase | `UPPER(country_code)` |
| `TRIM()` | Remove surrounding whitespace | `TRIM(name)` |
| `LEFT()` | Extract characters from left | `LEFT(code, 3)` |
| `RIGHT()` | Extract characters from right | `RIGHT(code, 4)` |
| `SUBSTRING()` | Extract part of a string | `SUBSTRING(code FROM 1 FOR 4)` |
| `POSITION()` | Find substring position | `POSITION('@' IN email)` |
| `REPLACE()` | Replace substring | `REPLACE(phone, '-', '')` |
| `REVERSE()` | Reverse a string | `REVERSE(value)` |

Function names and exact syntax vary across database engines.

## LEFT and RIGHT

`LEFT()` and `RIGHT()` extract a fixed number of characters.

```sql
SELECT
    LEFT(order_reference, 4) AS prefix,
    RIGHT(order_reference, 6) AS suffix
FROM orders;
```

For:

```text
ORDR-104582
```

the expressions can extract portions of the reference.

These functions are useful for structured identifiers, but avoid treating arbitrary strings as structured data when the domain can be modeled relationally.

## SUBSTRING

`SUBSTRING()` extracts a portion of a string.

PostgreSQL syntax:

```sql
SELECT SUBSTRING(order_reference FROM 1 FOR 4)
FROM orders;
```

This is useful when a value follows a stable, explicitly defined format.

For more complex parsing requirements, application code or specialized database functions may be more maintainable.

## POSITION

`POSITION()` locates a substring.

```sql
SELECT
    POSITION('@' IN email) AS at_position
FROM users;
```

A validation-oriented query could identify values that do not contain an `@`:

```sql
SELECT id, email
FROM users
WHERE POSITION('@' IN email) = 0;
```

This is not a complete email validation strategy. Production email validation should respect the actual application and domain requirements rather than attempting to encode the entire email grammar in a simple SQL predicate.

## REPLACE

`REPLACE()` substitutes occurrences of one string with another.

```sql
SELECT
    REPLACE(phone_number, '-', '') AS normalized_phone
FROM customers;
```

For example:

```text
+91-9876-543210
```

may become:

```text
+919876543210
```

This can be useful during data migration or normalization, but canonical normalization rules should ideally be defined at the application/data-model boundary rather than repeatedly performed by every query.

## LOWER and UPPER

Case transformation is commonly used for normalization:

```sql
SELECT
    LOWER(email) AS normalized_email
FROM users;
```

For case-insensitive identifiers, consider the database's collation and comparison semantics rather than assuming `LOWER()` is always the correct indexing strategy.

If a normalized form is a business invariant, enforcing it at write time can be more predictable than normalizing only during reads.

## Practical Data-Quality Audit

A production database can contain legacy or imported data that violates current expectations.

A targeted audit might be:

```sql
SELECT
    COUNT(*) AS invalid_username_count
FROM users
WHERE username IS NULL
   OR NULLIF(TRIM(username), '') IS NULL
   OR LENGTH(TRIM(username)) < 3
   OR LENGTH(TRIM(username)) > 30;
```

This query combines:

- NULL detection.
- Whitespace normalization.
- Empty-value detection.
- Character-length validation.

It is useful for migration planning and operational data-quality checks.

## Constraints vs Query-Time Validation

If a length requirement is a permanent database invariant, enforce it at the schema level when practical.

For example:

```sql
ALTER TABLE users
ADD CONSTRAINT users_username_length_chk
CHECK (
    username IS NULL
    OR CHAR_LENGTH(username) BETWEEN 3 AND 30
);
```

This protects data regardless of which application or service writes to the database.

However, schema constraints should encode **business invariants**, not every presentation concern.

For example:

```text
username: 3–30 characters
```

may be a legitimate database invariant.

But:

```text
button label: maximum 18 visible characters
```

is usually a UI concern.

## Application vs Database Responsibilities

A robust backend usually divides responsibilities deliberately.

| Requirement | Better Location |
|---|---|
| Database invariant | Database constraint |
| API input validation | Application/API layer |
| User-facing error message | Application layer |
| Data-quality audit | SQL |
| Large-scale migration | SQL |
| Complex Unicode/grapheme handling | Application layer or specialized tooling |
| Query-time reporting | SQL |
| Canonical normalization invariant | Database + application, depending on ownership |

For example, FastAPI can reject invalid request input before executing SQL, while PostgreSQL can enforce the invariant again:

```text
Client
  ↓
FastAPI validation
  ↓
Parameterized SQL
  ↓
PostgreSQL constraint
  ↓
Persistent data
```

Application validation improves user experience; database constraints protect integrity.

## Production Considerations

### Indexing

Avoid assuming that:

```sql
WHERE LENGTH(column) > ...
```

will use an ordinary index efficiently.

For performance-sensitive workloads:

1. Run `EXPLAIN (ANALYZE, BUFFERS)`.
2. Inspect actual row counts.
3. Measure execution time.
4. Determine whether the query is genuinely hot.
5. Consider an expression index or alternative schema design if justified.

### Large Text Columns

Running length operations across very large text columns can consume CPU and memory.

Be cautious with:

```sql
SELECT LENGTH(large_text_column)
FROM audit_events;
```

over millions of rows.

For operational reporting, consider:

- Restricting the time range.
- Sampling.
- Aggregating.
- Maintaining appropriate metadata.
- Running heavy analysis asynchronously.

### API Limits Are Not Always Database Limits

A database may allow a large text value while the API contract imposes a smaller limit.

For example:

```text
Database: TEXT
API request: maximum 5,000 characters
```

Using an unrestricted `TEXT` column does not mean clients should be allowed to submit unlimited data.

Apply limits at the correct layer.

### Storage Limits vs Character Limits

A byte-oriented infrastructure limit should not be implemented blindly with `LENGTH()`.

If the requirement is:

```text
maximum 4,096 bytes
```

use a byte-oriented measurement such as:

```sql
OCTET_LENGTH(payload) <= 4096
```

If the requirement is:

```text
maximum 4,096 characters
```

use:

```sql
CHAR_LENGTH(payload) <= 4096
```

These are different requirements.

## Security Considerations

Length checks can reduce some classes of abusive input, but they are not a complete security boundary.

For externally supplied text:

- Validate size at the API boundary.
- Reject unexpectedly large payloads early.
- Use parameterized SQL.
- Apply request/body limits at the HTTP layer.
- Consider reverse-proxy limits in Nginx or an AWS load-balancing/API layer.
- Avoid expensive repeated string processing on attacker-controlled input.

For example, a backend should not rely on a PostgreSQL `CHECK` constraint alone to protect the application from oversized HTTP requests. Rejecting excessive payloads earlier prevents unnecessary network, application, and database work.

## Common Mistakes

### Confusing Characters with Bytes

Incorrect assumption:

```text
1 character = 1 byte
```

This is not generally true with UTF-8.

Use:

```sql
LENGTH(value)
```

for character-oriented measurement and:

```sql
OCTET_LENGTH(value)
```

for byte-oriented measurement.

### Treating NULL as Zero Length

This:

```sql
LENGTH(NULL)
```

returns `NULL`, not `0`.

If the business rule explicitly treats missing values as empty:

```sql
LENGTH(COALESCE(value, ''))
```

Otherwise, preserve the distinction between missing and empty.

### Ignoring Whitespace

This:

```sql
LENGTH('   ')
```

is not zero.

If whitespace-only input is invalid:

```sql
NULLIF(TRIM(value), '') IS NULL
```

is a more meaningful validation condition.

### Applying Functions to Columns in Hot Predicates

Queries such as:

```sql
WHERE LENGTH(username) > 30
```

can prevent the optimizer from using a normal index as effectively as a predicate aligned with indexed data.

Measure before optimizing, and use an expression index only when justified.

### Assuming LENGTH Measures Visible Characters

Unicode code points, combining marks, and grapheme clusters can differ from what users perceive as one character.

For strict user-visible limits, use appropriate Unicode-aware application tooling.

### Validating Only in Application Code

Application validation can be bypassed by:

- Another microservice.
- An administrative script.
- A migration.
- A direct database client.
- A background worker.

Permanent data invariants should generally be enforced at the database boundary as well.

## Interview Traps

| Question | Correct Reasoning |
|---|---|
| What does `LENGTH()` return for `NULL`? | `NULL`, not zero. |
| Is character length the same as byte length? | No. Unicode encodings can use multiple bytes per character. |
| What measures bytes in PostgreSQL? | `OCTET_LENGTH()`. |
| What is `CHAR_LENGTH()`? | A character-count function; in PostgreSQL it is equivalent to character-oriented `LENGTH()` for text. |
| Why can `WHERE LENGTH(column) > 10` be expensive? | The database may need to evaluate the expression for many rows and cannot necessarily use a normal index efficiently. |
| How do you detect whitespace-only values? | Normalize with `TRIM()` and test the result, for example `NULLIF(TRIM(value), '') IS NULL`. |
| Should every length rule be a database constraint? | No. Encode persistent data invariants in the database; presentation and API-specific rules may belong elsewhere. |
| Does `LENGTH()` count what users visually perceive as characters? | Not necessarily; Unicode code points and grapheme clusters can differ from visible characters. |

## Recommended Practices

- Use `LENGTH()` or `CHAR_LENGTH()` for character-oriented requirements.
- Use `OCTET_LENGTH()` when the requirement is explicitly byte-oriented.
- Treat `NULL` and empty strings as different states unless the domain says otherwise.
- Normalize whitespace before validating text when whitespace is not meaningful.
- Enforce durable data invariants with database constraints where appropriate.
- Validate external input at the API boundary to reject oversized or invalid requests early.
- Inspect execution plans before adding indexes for length-based predicates.
- Be careful with Unicode when implementing user-facing character limits.
- Avoid repeatedly transforming large text columns in high-volume queries.
- Keep presentation-specific formatting out of database constraints.

## Key Takeaways

- **`LENGTH()` measures characters, while `OCTET_LENGTH()` measures bytes; Unicode makes this distinction operationally important.**
- **`NULL`, an empty string, and whitespace-only text are different states and should be handled deliberately.**
- **Length-based expressions in predicates can have indexing and performance implications, so production queries should be validated with execution plans.**
- **Permanent data-length invariants belong in database constraints when appropriate, while API and presentation limits should remain in their respective layers.**
- **Unicode-aware validation may require more than SQL character counting when the requirement is based on what users visually perceive as a character.**