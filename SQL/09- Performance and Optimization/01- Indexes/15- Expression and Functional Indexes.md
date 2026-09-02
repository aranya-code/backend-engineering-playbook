# 15- Expression and Functional Indexes

## Overview

An **expression index**, also called a **functional index**, indexes the result of an expression rather than the raw value stored in a column.

A conventional index might store:

```sql
CREATE INDEX idx_users_email
ON users (email);
```

An expression index can instead index:

```sql
LOWER(email)
```

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

This is useful when application queries repeatedly transform a column before comparing, sorting, or searching it.

Typical examples include:

- Case-insensitive email or username lookups.
- Normalized text comparisons.
- Date/time extraction.
- JSON expressions.
- Arithmetic expressions.
- Computed values.
- Domain-specific normalization.
- Queries where the expression would otherwise prevent a normal index from being used.

The key principle is:

> **If a query consistently searches on a deterministic transformation of a column, index the transformation rather than forcing the database to compute it for every row.**

## Why Expression Indexes Exist

Consider:

```sql
SELECT id, email
FROM users
WHERE LOWER(email) = LOWER($1);
```

A normal index on:

```sql
CREATE INDEX idx_users_email
ON users (email);
```

does not directly provide an ordered structure for:

```sql
LOWER(email)
```

The database may need to evaluate `LOWER(email)` across many rows.

An expression index changes the access path:

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

Conceptually:

```text
Table
  │
  ├── email = "Alice@Example.com"
  │          ↓
  │      LOWER(email)
  │          ↓
  │      "alice@example.com"
  │
  └── Expression Index
             ↓
      "alice@example.com" → row location
```

The transformation is materialized as part of the index structure, allowing the database to search the computed value efficiently.

## How Expression Indexes Work

The database evaluates the expression when maintaining the index.

For:

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

an insert conceptually performs:

```text
INSERT row
    ↓
Evaluate LOWER(email)
    ↓
Generate index key
    ↓
Insert key into B-tree
```

An update follows the same principle:

```text
UPDATE email
    ↓
Recalculate LOWER(email)
    ↓
Remove/update old index entry
    ↓
Insert new index entry
```

A query using the same expression can then search the index:

```text
Query
  ↓
LOWER(email) = 'alice@example.com'
  ↓
Expression index
  ↓
B-tree lookup
  ↓
Matching row(s)
```

The index does not eliminate the need to execute the expression in every context. Rather, it provides a precomputed search structure for the expression's value.

## PostgreSQL Expression Indexes

PostgreSQL supports indexes directly on expressions:

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

Query:

```sql
SELECT id, email
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

The expression in the query should correspond to the indexed expression.

Inspect the index definition:

```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'users';
```

## Common Use Case: Case-Insensitive Lookup

Case-insensitive identifiers are one of the most common use cases.

Suppose the application treats email addresses case-insensitively:

```sql
SELECT id
FROM users
WHERE LOWER(email) = LOWER($1);
```

Create:

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

For uniqueness:

```sql
CREATE UNIQUE INDEX idx_users_email_lower_unique
ON users (LOWER(email));
```

This allows the database to enforce:

```text
Alice@example.com
alice@example.com
ALICE@example.com
```

as the same logical identifier.

This is much stronger than relying on application code to perform a pre-insert lookup.

## Django Example

Django applications frequently need case-insensitive lookups.

For example:

```python
User.objects.filter(email__iexact=email)
```

may generate a query involving a case-insensitive comparison depending on the database and configuration.

When using PostgreSQL, an explicit expression index can be created with Django:

```python
from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                Lower("email"),
                name="user_email_lower_idx",
            ),
        ),
    ]
```

For case-insensitive uniqueness, Django's model-level constraints can often express the requirement more clearly:

```python
from django.db import models
from django.db.models.functions import Lower


class User(models.Model):
    email = models.EmailField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="user_email_lower_unique",
            ),
        ]
```

The exact migration and generated SQL should still be reviewed for the target database.

## Expression Index vs Normal Index

| Query | Normal index | Expression index |
|---|---|---|
| `WHERE email = $1` | Excellent fit | Not required |
| `WHERE LOWER(email) = $1` | Usually not a direct match | Strong fit |
| `WHERE created_at >= $1` | Strong fit | Usually unnecessary |
| `WHERE DATE(created_at) = $1` | Often poor fit | Can be useful |
| `WHERE price * quantity > $1` | Cannot directly index raw columns for this expression | Expression index can help |
| `ORDER BY LOWER(name)` | Normal `name` index may not provide desired ordering | Expression index can |

The index should match the operation that the workload actually performs.

## Date and Time Expressions

Consider:

```sql
SELECT count(*)
FROM events
WHERE DATE(created_at) = DATE '2026-08-31';
```

A normal index:

```sql
CREATE INDEX idx_events_created_at
ON events (created_at);
```

may not be the ideal access path because the query applies `DATE()` to the indexed column.

An expression index can target:

```sql
CREATE INDEX idx_events_created_date
ON events ((created_at::date));
```

The query can then use the corresponding expression:

```sql
SELECT count(*)
FROM events
WHERE created_at::date = DATE '2026-08-31';
```

However, an expression index is not automatically the best solution.

For time-range queries, this is often preferable:

```sql
SELECT count(*)
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-31 00:00:00+00'
  AND created_at < TIMESTAMPTZ '2026-09-01 00:00:00+00';
```

with:

```sql
CREATE INDEX idx_events_created_at
ON events (created_at);
```

The range predicate preserves direct use of the timestamp index and avoids storing an additional expression index.

This illustrates an important senior-level principle:

> **Do not create an expression index merely because an expression appears in a query. First determine whether the query can be rewritten into a more index-friendly form.**

## Sargability

**Sargability** describes whether a predicate can use an index efficiently.

Compare:

```sql
WHERE created_at::date = DATE '2026-08-31'
```

with:

```sql
WHERE created_at >= TIMESTAMPTZ '2026-08-31 00:00:00+00'
  AND created_at < TIMESTAMPTZ '2026-09-01 00:00:00+00'
```

The second form directly constrains the indexed column.

A common pattern is:

```text
Function(column)
```

which can interfere with a normal index:

```sql
WHERE LOWER(email) = ...
WHERE DATE(created_at) = ...
WHERE CAST(account_id AS text) = ...
```

An expression index can restore an efficient access path when rewriting the query is undesirable or impossible.

## Deterministic Expressions

An expression index requires an expression whose result is suitable for persistent indexing.

The database must be able to maintain a stable index key.

Conceptually:

```text
same row value
    ↓
same expression
    ↓
same index key
```

Functions whose result can arbitrarily change independently of the row are unsuitable for ordinary index maintenance.

In PostgreSQL, function volatility matters:

- `IMMUTABLE` — result depends only on arguments; strongest fit.
- `STABLE` — consistent within a statement but can change between statements.
- `VOLATILE` — can change even within a statement.

PostgreSQL restricts expression-index definitions to expressions it considers safe for index storage, including restrictions related to function volatility.

When designing custom functions for indexed expressions, understand their volatility classification before using them in an index.

## Function Choice Matters

Consider:

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

This assumes the application and database agree on the semantics of `LOWER()`.

For internationalized applications, case conversion can involve collation and Unicode behavior.

Do not assume:

```text
ASCII lowercase
=
correct global case-insensitive identity
```

For user-facing identifiers, define normalization semantics explicitly and ensure application, database, and index behavior agree.

## JSON Expression Indexes

Expression indexes can target JSON-derived values.

For PostgreSQL:

```sql
CREATE TABLE accounts (
    id bigint PRIMARY KEY,
    metadata jsonb NOT NULL
);
```

Suppose queries repeatedly access:

```sql
metadata ->> 'external_id'
```

An expression index can be:

```sql
CREATE INDEX idx_accounts_external_id
ON accounts ((metadata ->> 'external_id'));
```

Query:

```sql
SELECT id
FROM accounts
WHERE metadata ->> 'external_id' = $1;
```

This can be preferable to repeatedly scanning the table when the workload consistently searches this specific JSON field.

However, if the application frequently queries many different keys or performs containment queries across the entire JSON document, a PostgreSQL `jsonb` GIN index may be more appropriate.

The index should reflect the query workload rather than the storage format alone.

## Expression Indexes vs Generated Columns

An alternative design is to expose the computed value as a generated column and index that column.

Conceptually:

```text
Raw column
    ↓
Generated column
    ↓
Normal index
```

instead of:

```text
Raw column
    ↓
Expression index
```

For example:

```sql
CREATE TABLE products (
    id bigint PRIMARY KEY,
    sku text NOT NULL,
    normalized_sku text
        GENERATED ALWAYS AS (lower(sku)) STORED
);

CREATE INDEX idx_products_normalized_sku
ON products (normalized_sku);
```

This can be useful when:

- The computed value is needed by multiple queries.
- The derived value is useful for application inspection.
- You want a named schema attribute.
- Multiple indexes or constraints need the same derived value.
- Operational visibility of the computed value matters.

An expression index is often simpler when the derived value exists purely for indexing.

| Approach | Best fit |
|---|---|
| Normal index | Raw column is queried directly |
| Expression index | Derived value exists primarily for access-path optimization |
| Generated column + index | Derived value is part of the data model |
| Query rewrite | Expression can be avoided with a more index-friendly predicate |

## Expression Indexes and Composite Indexes

Expressions can be combined with normal columns.

For example:

```sql
CREATE INDEX idx_users_tenant_email_lower
ON users (tenant_id, LOWER(email));
```

This supports:

```sql
SELECT id
FROM users
WHERE tenant_id = $1
  AND LOWER(email) = $2;
```

Conceptually:

```text
B-tree
│
├── tenant_id
│     │
│     └── LOWER(email)
│
└── row location
```

This is particularly useful in multi-tenant systems where identifiers are unique or frequently searched within a tenant.

A senior-level design still requires attention to column order:

```text
tenant_id
    ↓
LOWER(email)
```

is not equivalent to:

```text
LOWER(email)
    ↓
tenant_id
```

The correct order depends on the workload and query patterns.

## Expression Indexes and Ordering

Expression indexes can also optimize ordering:

```sql
CREATE INDEX idx_users_lower_name
ON users (LOWER(name));
```

Query:

```sql
SELECT id, name
FROM users
ORDER BY LOWER(name)
LIMIT 50;
```

The index can provide values in the required expression order, potentially avoiding an expensive sort.

This becomes especially valuable for:

- Large result sets.
- Small `LIMIT` queries.
- Frequently executed endpoints.
- Stable sorting requirements.

For example:

```text
API request
    ↓
ORDER BY LOWER(name)
    ↓
Expression index
    ↓
Already ordered keys
    ↓
LIMIT 50
```

## Expression Indexes and Covering Indexes

In PostgreSQL, an expression can be combined with included columns:

```sql
CREATE INDEX idx_users_lower_email
ON users (LOWER(email))
INCLUDE (id, email);
```

A query such as:

```sql
SELECT id, email
FROM users
WHERE LOWER(email) = $1;
```

may be able to use an index-only scan when visibility-map and other conditions allow it.

This combines:

```text
Expression index
→ search on LOWER(email)

INCLUDE columns
→ return id and email
```

Do not assume `INCLUDE` guarantees an index-only scan. PostgreSQL still has to determine whether an index-only plan is beneficial and whether heap visibility information permits avoiding heap accesses.

## Expression Indexes and Partial Indexes

The techniques can be combined:

```sql
CREATE INDEX idx_active_users_email_lower
ON users (LOWER(email))
WHERE deleted_at IS NULL;
```

This means:

```text
Expression
→ LOWER(email)

Predicate
→ deleted_at IS NULL
```

A query such as:

```sql
SELECT id
FROM users
WHERE deleted_at IS NULL
  AND LOWER(email) = $1;
```

can potentially use this highly targeted access path.

This is powerful, but the combined index should be justified by a high-value workload because it increases design complexity.

## Query Planner Validation

Never assume that an expression index is being used.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

Look for an appropriate index access path, such as:

```text
Index Scan
Index Only Scan
Bitmap Index Scan
```

The exact plan depends on:

- Table size.
- Selectivity.
- Statistics.
- Cache state.
- Cost parameters.
- Query shape.
- Data distribution.

A small table may still use a sequential scan because scanning the table is cheaper than traversing an index.

That is not necessarily a failure.

## Statistics and Expression Indexes

The optimizer needs accurate information to choose an effective plan.

After substantial data changes:

```sql
ANALYZE users;
```

PostgreSQL maintains statistics for indexed expressions in supported scenarios, allowing the planner to estimate selectivity for expression predicates.

For highly skewed data, inspect whether estimated and actual row counts differ significantly:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

A large difference between:

```text
estimated rows
actual rows
```

can indicate a statistics or data-distribution problem that deserves investigation.

## Production Performance Characteristics

Expression indexes trade computation at write time for faster reads.

### Reads

Potential benefits:

- Faster lookup.
- Efficient ordering.
- Lower CPU from repeated expression evaluation.
- Fewer rows examined.
- Better latency for high-frequency queries.

### Writes

Every insert or relevant update may need to:

1. Evaluate the expression.
2. Generate an index key.
3. Modify the index structure.
4. Generate additional WAL/replication work.

Therefore:

```text
More expression indexes
        ↓
More write amplification
        ↓
Potentially higher write latency
```

The performance trade-off should be evaluated against actual read/write workload.

## Operational Considerations

For a large production PostgreSQL table:

```sql
CREATE INDEX CONCURRENTLY idx_users_email_lower
ON users (LOWER(email));
```

`CONCURRENTLY` can reduce blocking of normal writes compared with a standard index build, at the cost of additional work and a longer build process.

Important operational considerations include:

- Index build duration.
- Disk consumption.
- WAL generation.
- Replica lag.
- I/O pressure.
- Deployment windows.
- Failure handling.
- Migration transaction behavior.

For Django migrations, production index creation should be planned explicitly rather than treating every index migration as a trivial schema change.

## Monitoring

PostgreSQL index usage can be inspected with:

```sql
SELECT
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname = 'users'
ORDER BY idx_scan DESC;
```

Inspect index size:

```sql
SELECT
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE relname = 'users';
```

Monitor:

- Index scan frequency.
- Query latency.
- p95/p99 endpoint latency.
- CPU utilization.
- Buffer reads.
- Disk usage.
- Write latency.
- Replica lag.
- Index growth.

An expression index with almost no usage is a candidate for review.

## Common Mistakes

### Indexing the Wrong Expression

Creating:

```sql
CREATE INDEX idx_email_lower
ON users (LOWER(email));
```

does not automatically optimize:

```sql
WHERE TRIM(LOWER(email)) = $1
```

The query expression and index definition must be compatible with the optimizer's rules.

Design from the actual production query.

### Wrapping a Column Without Considering Query Rewriting

Developers sometimes immediately create:

```sql
CREATE INDEX idx_created_date
ON events ((created_at::date));
```

when a range query would work with the existing timestamp index:

```sql
WHERE created_at >= $1
  AND created_at < $2;
```

Prefer a query rewrite when it provides the same semantics and a simpler access path.

### Ignoring Collation and Locale

Case conversion and sorting can depend on database and collation behavior.

Do not design a global case-insensitive identifier strategy without validating Unicode and collation semantics.

### Assuming Any Function Can Be Indexed

Database engines impose restrictions on indexed expressions and functions.

Custom functions should have appropriate volatility and deterministic behavior for the target database.

### Creating an Expression Index Without Measuring

An expression index adds:

- Storage.
- Write work.
- WAL.
- Backup overhead.
- Maintenance complexity.

Create it because a measurable workload benefits from it.

### Forgetting ORM Query Shape

Application code such as:

```python
User.objects.filter(email__iexact=email)
```

does not guarantee that the generated SQL exactly matches:

```sql
LOWER(email) = $1
```

Inspect the generated SQL and execution plan before deciding which expression to index.

### Assuming the Index Must Always Be Used

The optimizer may correctly choose a sequential scan when:

- The table is small.
- The predicate is not selective.
- The requested result contains a large percentage of the table.
- The index traversal cost exceeds sequential scanning.

Index presence does not imply index usage.

## Security Considerations

Expression indexes do not provide authorization or data isolation.

For example:

```sql
CREATE INDEX idx_users_tenant_email
ON users (tenant_id, LOWER(email));
```

does not enforce tenant authorization.

The application or database security model must still ensure:

```text
request
  ↓
authenticate
  ↓
authorize tenant
  ↓
execute query
```

Expression indexes can also contain derived values from sensitive columns. Treat indexes as database-resident copies of indexed information and include them in:

- Backup controls.
- Access controls.
- Data retention policies.
- Encryption-at-rest considerations.
- Database security reviews.

## Scalability Guidance

Expression indexes are particularly effective when:

- The query is frequent.
- The expression is deterministic.
- The result is selective.
- The table is large.
- The expression is expensive enough to matter.
- The access pattern is stable.

They are less attractive when:

- The table is small.
- The query is rare.
- The expression has poor selectivity.
- The query can be cheaply rewritten.
- The workload is heavily write-oriented.
- The expression changes frequently.

For high-scale systems, avoid accumulating specialized indexes without measuring their benefit.

A useful rule is:

```text
Index benefit
>
Read cost saved
+
Operational cost
+
Write maintenance cost
```

## Practical Design Workflow

Use this process when considering an expression index:

1. Capture the actual production query.
2. Identify the expression applied to the indexed column.
3. Determine whether the query can be rewritten to use the raw column.
4. Measure baseline latency and buffer usage.
5. Estimate expression selectivity.
6. Check existing indexes for overlap.
7. Create the smallest useful expression index.
8. Validate with `EXPLAIN (ANALYZE, BUFFERS)`.
9. Measure application-level p95/p99 latency.
10. Monitor index usage and write impact after deployment.

Example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, email
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

Then:

```sql
CREATE INDEX CONCURRENTLY idx_users_email_lower
ON users (LOWER(email));
```

Validate again:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, email
FROM users
WHERE LOWER(email) = 'alice@example.com';
```

Compare:

- Execution time.
- Rows examined.
- Shared buffer hits/reads.
- Index usage.
- CPU utilization.
- API p95/p99 latency.

## Interview Traps

### "What is an expression index?"

An index whose key is derived from an expression rather than directly from a stored column value.

### "Why would you use one?"

When production queries repeatedly search, sort, or filter using a deterministic expression and a normal index does not provide an efficient access path.

### "Give an example."

```sql
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));
```

for:

```sql
WHERE LOWER(email) = $1
```

### "Is `LOWER(email)` the same as an index on `email`?"

No.

An index on:

```sql
email
```

organizes raw email values.

An index on:

```sql
LOWER(email)
```

organizes the transformed values.

They serve different query expressions.

### "Can expression indexes be unique?"

Yes, where supported by the database.

For PostgreSQL:

```sql
CREATE UNIQUE INDEX idx_users_email_lower_unique
ON users (LOWER(email));
```

### "Can expression indexes be composite?"

Yes.

```sql
CREATE INDEX idx_users_tenant_email_lower
ON users (tenant_id, LOWER(email));
```

### "Can expression indexes be partial?"

Yes, in systems such as PostgreSQL that support both capabilities:

```sql
CREATE INDEX idx_active_users_email_lower
ON users (LOWER(email))
WHERE deleted_at IS NULL;
```

### "Are expression indexes always better than rewriting the query?"

No. If a range predicate or another query rewrite can use an existing normal index efficiently, that may be the simpler and more maintainable solution.

### "What is the primary trade-off?"

Read performance improves at the cost of additional storage and write-time expression/index maintenance.

## Key Takeaways

- **Expression indexes index the result of a deterministic expression, allowing queries such as `LOWER(email) = ...` to use an appropriate indexed access path.**
- **Always consider query rewriting first; a sargable predicate on the raw column can be simpler and cheaper than adding a specialized expression index.**
- **Expression indexes can be combined with composite, covering, unique, and partial-index techniques to create highly targeted production access paths.**
- **They increase write, storage, WAL, backup, and operational costs, so their value should be demonstrated through production query patterns and execution-plan measurements.**
- **Validate expression semantics, ORM-generated SQL, collation behavior, planner estimates, and actual index usage before deploying expression indexes at scale.**