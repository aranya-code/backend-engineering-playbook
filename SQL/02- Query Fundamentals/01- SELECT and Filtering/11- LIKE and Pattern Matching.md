# 11- LIKE and Pattern Matching

## Overview

`LIKE` is a SQL predicate used to match text values against a pattern. It is commonly used for search filters, prefix matching, partial identifiers, usernames, email addresses, and administrative queries.

The basic form is:

```sql
SELECT columns
FROM table_name
WHERE column_name LIKE pattern;
```

The two primary wildcard characters are:

| Wildcard | Meaning | Example |
|---|---|---|
| `%` | Zero or more characters | `'app%'` |
| `_` | Exactly one character | `'app_'` |

For example:

```sql
SELECT
    id,
    email
FROM users
WHERE email LIKE '%@example.com';
```

Pattern matching is easy to use but can become a significant performance concern at scale. The key production question is not only **whether the pattern is correct**, but also **whether the database can use an appropriate index**.

## Why LIKE Exists

Normal equality compares complete values:

```sql
WHERE username = 'aranya'
```

`LIKE` allows controlled pattern matching:

```sql
WHERE username LIKE 'ara%';
```

This is useful when the application does not know the complete value but does know some structure of it.

Typical backend use cases include:

- Prefix search
- Username lookup
- Email-domain filtering
- File-name filtering
- Product-name search
- Administrative search
- Partial identifiers
- Simple autocomplete queries

`LIKE` is not a general-purpose full-text search engine. Once search requirements become complex, dedicated database or search-engine capabilities are usually more appropriate.

## Basic Pattern Matching

### Exact Text with LIKE

```sql
SELECT
    id,
    username
FROM users
WHERE username LIKE 'aranya';
```

With no wildcard, this behaves similarly to equality for ordinary text comparisons, although collation and type semantics can matter.

For straightforward equality, prefer:

```sql
WHERE username = 'aranya';
```

Use `LIKE` when pattern matching is actually required.

### Prefix Matching

```sql
SELECT
    id,
    username
FROM users
WHERE username LIKE 'ara%';
```

Matches values such as:

```text
ara
aranya
arav
arash123
```

but not:

```text
baranya
xara
```

The `%` means that any sequence of characters may follow `ara`.

Prefix matching is one of the most important `LIKE` patterns from a performance perspective because some database engines can optimize it using an appropriate index.

### Suffix Matching

```sql
SELECT
    id,
    email
FROM users
WHERE email LIKE '%@example.com';
```

This matches:

```text
alice@example.com
bob@example.com
service@example.com
```

The leading `%` means the database cannot generally use an ordinary B-tree index as efficiently as it can for a prefix search.

### Substring Matching

```sql
SELECT
    id,
    product_name
FROM products
WHERE product_name LIKE '%keyboard%';
```

This finds `keyboard` anywhere in the value.

For example:

```text
Mechanical Keyboard
Wireless keyboard
Keyboard Stand
```

Substring searches are convenient but potentially expensive on large tables.

### Single-Character Matching

The `_` wildcard represents exactly one character:

```sql
SELECT
    id,
    code
FROM products
WHERE code LIKE 'AB_123';
```

Possible matches include:

```text
ABC123
ABD123
AB9123
```

but not:

```text
AB123
ABCD123
```

## LIKE Pattern Reference

| Pattern | Meaning | Example match |
|---|---|---|
| `'abc'` | Exact pattern | `abc` |
| `'abc%'` | Starts with `abc` | `abcdef` |
| `'%abc'` | Ends with `abc` | `xyzabc` |
| `'%abc%'` | Contains `abc` | `xyzabcdef` |
| `'a_c'` | `a`, any one character, `c` | `abc` |
| `'a__c'` | `a`, two characters, `c` | `abbc` |
| `'abc_%'` | Starts with `abc` and has at least one additional character | `abcd` |

The wildcard characters are interpreted by SQL, not by the application language.

## Combining LIKE with Other Predicates

`LIKE` is frequently combined with other filters:

```sql
SELECT
    id,
    product_name,
    price
FROM products
WHERE tenant_id = $1
  AND product_name LIKE $2
  AND price BETWEEN $3 AND $4;
```

This is a common backend API pattern:

```text
GET /products?search=keyboard&min_price=50&max_price=500
```

The database can apply the tenant restriction, text filter, and price range according to its optimizer and available indexes.

## LIKE and NULL

`LIKE` does not match `NULL`.

For example:

```sql
WHERE username LIKE 'ara%'
```

does not return rows where:

```text
username IS NULL
```

The expression evaluates to `UNKNOWN` for `NULL`.

If `NULL` has special business meaning, handle it explicitly:

```sql
WHERE username LIKE 'ara%'
   OR username IS NULL;
```

Only add this condition when `NULL` should actually be included.

## Case Sensitivity

Case sensitivity is database- and collation-dependent.

For example, PostgreSQL's `LIKE` is case-sensitive:

```sql
WHERE username LIKE 'ara%';
```

PostgreSQL provides `ILIKE` for case-insensitive pattern matching:

```sql
SELECT
    id,
    username
FROM users
WHERE username ILIKE 'ara%';
```

This can match values such as:

```text
aranya
Aranya
ARANYA
```

Other databases may use different collation or operator behavior.

Do not assume that `LIKE` behaves identically across PostgreSQL, MySQL, SQL Server, and other database systems.

## LIKE vs ILIKE

In PostgreSQL:

| Predicate | Typical behavior |
|---|---|
| `LIKE` | Case-sensitive pattern matching |
| `ILIKE` | Case-insensitive pattern matching |
| `=` | Equality |
| `~` | POSIX regular expression matching |
| `~*` | Case-insensitive POSIX regular expression matching |

Example:

```sql
SELECT
    id,
    name
FROM products
WHERE name ILIKE '%keyboard%';
```

`ILIKE` is useful for user-facing search where case should normally not matter.

However, case-insensitive matching can have different indexing requirements from ordinary `LIKE`, so performance should be evaluated with the actual database and workload.

## Escaping Wildcards

Sometimes `%` or `_` should be treated as literal characters rather than wildcards.

For example, suppose a product name contains:

```text
100% Cotton Shirt
```

A pattern containing `%` directly may interpret it as a wildcard.

SQL allows an escape character to indicate that a wildcard should be treated literally:

```sql
SELECT
    id,
    product_name
FROM products
WHERE product_name LIKE '%100\%%' ESCAPE '\';
```

Here:

```text
\%
```

means a literal `%`.

Similarly:

```sql
WHERE product_name LIKE '%size\_large%' ESCAPE '\';
```

matches a literal underscore.

The exact escaping behavior should be verified for the target database and driver.

## User-Supplied Search Terms

This is especially important in backend applications.

Suppose a client submits:

```text
search=100%
```

The application may intend to search for the literal text `100%`, but directly placing that value into a `LIKE` pattern makes `%` a wildcard.

There are therefore two separate concerns:

1. **SQL parameterization** protects the SQL statement structure.
2. **LIKE escaping** controls how user input behaves inside the pattern.

Parameterized SQL:

```sql
WHERE product_name LIKE $1
```

does not automatically mean that wildcard characters inside `$1` are literal.

If the application wants literal substring search, it must escape `%`, `_`, and the chosen escape character before constructing the pattern.

Conceptually:

```text
User input
    ↓
Escape LIKE metacharacters
    ↓
Add intended wildcard characters
    ↓
Bind as SQL parameter
    ↓
Execute query
```

This distinction is a common production and interview issue.

## SQL Injection vs LIKE Wildcards

These are different problems.

Unsafe SQL construction:

```python
query = f"""
    SELECT id, product_name
    FROM products
    WHERE product_name LIKE '%{search}%'
"""
```

This can create SQL injection risk.

Parameterized SQL:

```python
query = """
    SELECT id, product_name
    FROM products
    WHERE product_name LIKE %s
"""

params = [f"%{search}%"]
```

protects the SQL structure.

However, `%` and `_` inside `search` still have wildcard meaning.

Therefore:

```text
Parameterization → SQL injection protection
LIKE escaping    → Pattern semantics
```

Both may be required.

## Indexing and Performance

Pattern matching can have very different performance characteristics depending on the pattern.

Consider an indexed column:

```sql
CREATE INDEX idx_users_username
ON users (username);
```

A prefix query:

```sql
WHERE username LIKE 'ara%';
```

can often be optimized using the index, depending on the database, collation, operator class, and query plan.

A leading-wildcard query:

```sql
WHERE username LIKE '%ara%';
```

generally cannot use a normal B-tree index to efficiently locate arbitrary substrings.

This distinction is critical at scale.

| Pattern | Typical B-tree friendliness |
|---|---|
| `'abc%'` | Good potential |
| `'abc'` | Excellent; equality is usually preferable |
| `'%abc'` | Poor |
| `'%abc%'` | Poor |
| `'a_c%'` | Depends on optimizer and pattern structure |

Always verify with an execution plan rather than relying solely on rules of thumb.

## EXPLAIN for LIKE Queries

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    username
FROM users
WHERE username LIKE 'ara%';
```

Look for whether the database uses:

- Index Scan
- Index Only Scan
- Bitmap Index Scan
- Sequential Scan

A sequential scan is not automatically a problem. If the query returns a large percentage of the table, scanning the table may genuinely be cheaper than using an index.

The senior-level question is:

> Is the chosen execution plan appropriate for the data distribution and workload?

## Leading Wildcards

This query:

```sql
WHERE product_name LIKE '%keyboard%'
```

is a common source of scalability problems.

On a small table, a sequential scan may be completely acceptable.

On a table containing hundreds of millions of products, repeatedly scanning the table for every API request can become expensive.

Possible alternatives include:

- PostgreSQL trigram indexes
- PostgreSQL full-text search
- Dedicated search engines
- Search-specific data models
- Application-side search services

The appropriate choice depends on search requirements rather than simply replacing every `LIKE` query with an index.

## PostgreSQL Trigram Search

For substring and fuzzy text search in PostgreSQL, the `pg_trgm` extension can provide substantially better indexing options.

Enable the extension:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Create a GIN trigram index:

```sql
CREATE INDEX idx_products_name_trgm
ON products
USING GIN (product_name gin_trgm_ops);
```

Then:

```sql
SELECT
    id,
    product_name
FROM products
WHERE product_name ILIKE '%keyboard%';
```

can potentially use the trigram index.

This is particularly useful for:

- Substring search
- Similarity search
- User-facing search boxes
- Fuzzy matching

It is PostgreSQL-specific and should be evaluated against the actual workload.

## LIKE vs Full-Text Search

`LIKE` and full-text search solve different problems.

| Requirement | Better fit |
|---|---|
| Exact equality | `=` |
| Prefix matching | `LIKE 'term%'` |
| Simple substring matching | `LIKE '%term%'` |
| Case-insensitive simple matching | `ILIKE` where supported |
| Linguistic search | Full-text search |
| Relevance ranking | Full-text/search engine |
| Typo tolerance | Trigram or search engine |
| Complex search across many fields | Search engine or dedicated search architecture |

Do not use `%term%` as a substitute for a search system when requirements include:

- Relevance ranking
- Stemming
- Tokenization
- Typo tolerance
- Synonyms
- Faceting
- Complex ranking
- Large-scale search traffic

## LIKE in Django

Django exposes pattern matching through field lookups.

Case-sensitive:

```python
products = Product.objects.filter(
    name__contains="keyboard"
)
```

Case-insensitive:

```python
products = Product.objects.filter(
    name__icontains="keyboard"
)
```

Prefix matching:

```python
products = Product.objects.filter(
    name__startswith="Key"
)
```

Case-insensitive prefix matching:

```python
products = Product.objects.filter(
    name__istartswith="key"
)
```

These ORM operations should still be evaluated as SQL queries. An ORM abstraction does not remove database performance characteristics.

For example:

```python
Product.objects.filter(name__icontains="keyboard")
```

may translate into a substring-style SQL predicate that cannot efficiently use a conventional B-tree index.

## LIKE in API Design

A search endpoint should define its semantics explicitly.

For example:

```text
GET /users?username_prefix=ara
```

has clearer performance expectations than:

```text
GET /users?search=ara
```

when the application only supports prefix matching.

A production API should consider:

- Maximum search-term length
- Minimum search-term length
- Wildcard handling
- Case sensitivity
- Pagination
- Result limits
- Authorization
- Tenant isolation
- Rate limiting
- Query latency
- Index availability

For example, rejecting extremely short or broad searches can prevent accidental expensive queries:

```text
GET /products?search=a
```

may match a substantial portion of a large dataset.

## Pagination with Pattern Matching

Search queries should generally be paginated.

Avoid returning unbounded results:

```sql
SELECT
    id,
    product_name
FROM products
WHERE product_name LIKE 'key%';
```

Prefer a bounded query:

```sql
SELECT
    id,
    product_name
FROM products
WHERE product_name LIKE $1
ORDER BY id
LIMIT $2;
```

For high-throughput APIs, keyset pagination can be preferable to large `OFFSET` values:

```sql
SELECT
    id,
    product_name
FROM products
WHERE product_name LIKE $1
  AND id > $2
ORDER BY id
LIMIT $3;
```

The exact pagination strategy should account for the search ordering and index design.

## Multi-Tenant Systems

Pattern matching must remain within the tenant boundary.

Correct:

```sql
SELECT
    id,
    product_name
FROM products
WHERE tenant_id = $1
  AND product_name LIKE $2
ORDER BY id
LIMIT $3;
```

Do not rely on the search predicate itself to provide isolation.

For applications using PostgreSQL Row-Level Security, the database can provide an additional enforcement layer, but application and database authorization should still be designed deliberately.

## Security Considerations

`LIKE` introduces several security and operational concerns.

### SQL Injection

Never concatenate untrusted input into SQL:

```python
# Unsafe
query = f"SELECT * FROM users WHERE username LIKE '%{search}%'"
```

Use parameterized queries.

### Wildcard Abuse

Even when SQL injection is prevented, a user may submit:

```text
%
```

or:

```text
_
```

which can match a huge portion of the dataset.

For public APIs, consider:

- Input length limits
- Rate limiting
- Search-specific quotas
- Rejecting excessively broad patterns
- Escaping wildcards when literal search is intended
- Query timeouts

### Tenant Isolation

Always retain authorization predicates:

```sql
WHERE tenant_id = $1
  AND name LIKE $2;
```

Do not allow a flexible search feature to bypass access-control conditions.

## Common Mistakes

### Using `%term%` for Every Search

```sql
WHERE name LIKE '%keyboard%';
```

This is easy to write but may become expensive at scale.

Use prefix search, trigram indexing, full-text search, or a dedicated search system when requirements justify them.

### Assuming Parameterization Escapes Wildcards

This:

```sql
WHERE name LIKE $1
```

protects SQL structure, but `%` and `_` inside `$1` can still act as pattern operators.

Escape them separately when literal matching is required.

### Confusing LIKE with Full-Text Search

`LIKE` does not provide:

- Relevance ranking
- Stemming
- Linguistic analysis
- Typo tolerance
- Search scoring

Do not build a complex search engine out of increasingly complicated `LIKE` predicates.

### Ignoring Case Semantics

A query that works as expected in one database configuration may behave differently under another collation or database engine.

Define whether search is case-sensitive and implement that requirement deliberately.

### Returning Unbounded Results

A broad pattern can produce millions of rows.

Always consider:

```sql
ORDER BY ...
LIMIT ...
```

and an appropriate pagination strategy for API-facing queries.

### Forgetting NULL Semantics

`LIKE` does not match `NULL`.

Use `IS NULL` explicitly when required.

### Assuming an Index Will Always Be Used

Even an indexed column may result in a sequential scan if the optimizer determines that it is cheaper.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

to validate important production queries.

## Production Recommendations

### Prefer Equality When Equality Is Required

Instead of:

```sql
WHERE email LIKE 'alice@example.com';
```

prefer:

```sql
WHERE email = 'alice@example.com';
```

when the requirement is exact equality.

### Prefer Prefix Search When Possible

If the business requirement is:

> Find usernames beginning with `ara`.

use:

```sql
WHERE username LIKE 'ara%';
```

rather than:

```sql
WHERE username LIKE '%ara%';
```

This can have significantly better index characteristics.

### Make Search Semantics Explicit

Define whether the endpoint supports:

- Exact matching
- Prefix matching
- Substring matching
- Case-insensitive matching
- Wildcards
- Fuzzy matching

Do not leave these semantics implicit.

### Bound Expensive Queries

For public APIs:

```sql
SELECT
    id,
    name
FROM products
WHERE name ILIKE $1
ORDER BY id
LIMIT $2;
```

Combine this with application-level validation and sensible maximum page sizes.

### Monitor Search Queries

Monitor:

- Query latency
- Rows examined
- Rows returned
- Sequential scans
- Database CPU
- Buffer/cache behavior
- Query frequency
- Slow-query rate

A search query that takes `20 ms` during development may behave very differently after the table grows by two orders of magnitude.

## Production Decision Guide

| Requirement | Recommended approach |
|---|---|
| Exact lookup | `=` |
| Prefix autocomplete | `LIKE 'term%'` + appropriate index |
| Small-table substring search | `LIKE '%term%'` |
| PostgreSQL substring search at scale | `pg_trgm` |
| Linguistic search | Full-text search |
| Fuzzy/typo-tolerant search | Trigram or search engine |
| Large multi-field search | Dedicated search architecture |
| User-provided literal text | Escape LIKE metacharacters + parameterize |
| Public search API | Validate, authorize, paginate, rate-limit, monitor |

## Interview Traps

| Question | Strong answer |
|---|---|
| What does `%` mean in `LIKE`? | Zero or more characters. |
| What does `_` mean? | Exactly one character. |
| Does `LIKE` match `NULL`? | No. The result is `UNKNOWN` for `NULL`. |
| Is `LIKE` case-sensitive? | It depends on the database and collation; PostgreSQL's `LIKE` is case-sensitive while `ILIKE` provides case-insensitive matching. |
| Can `LIKE` use an index? | Yes, depending on the pattern, database, collation, operator class, and execution plan. Prefix patterns are generally more index-friendly than leading-wildcard patterns. |
| Why is `%term%` expensive? | A conventional B-tree index generally cannot efficiently locate arbitrary substrings, so a large scan may be required. |
| Does parameterization make `%` literal? | No. Parameterization prevents SQL injection, but `%` and `_` retain `LIKE` wildcard semantics. |
| How do you search for a literal `%`? | Escape it using the database's supported `LIKE` escape mechanism. |
| Should `LIKE` replace full-text search? | No. Full-text search and search engines provide capabilities such as tokenization, ranking, stemming, and fuzzy matching that `LIKE` does not. |
| How would you optimize PostgreSQL substring search? | Consider `pg_trgm` with an appropriate GIN/GiST index and validate with execution plans. |
| Is a sequential scan always bad? | No. For broad or small-table queries, a sequential scan may be the optimal plan. |

## Key Takeaways

- `LIKE` provides SQL pattern matching through `%` for zero-or-more characters and `_` for exactly one character.
- Prefix patterns such as `LIKE 'term%'` are generally more index-friendly than leading-wildcard patterns such as `LIKE '%term%'`.
- SQL parameterization prevents injection but does not make `%` and `_` literal; escape LIKE metacharacters separately when required.
- For large-scale substring, linguistic, fuzzy, or relevance-ranked search, use capabilities such as PostgreSQL `pg_trgm`, full-text search, or a dedicated search system instead of relying on `LIKE`.
- Production search requires more than correct SQL: enforce authorization, bound result sizes, paginate, validate input, monitor query performance, and verify execution plans.