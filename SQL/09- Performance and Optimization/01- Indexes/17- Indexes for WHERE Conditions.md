# 17- Indexes for WHERE Conditions

## Overview

`WHERE` conditions are one of the most common reasons to create database indexes. A well-designed index can allow the database to locate qualifying rows without scanning an entire table.

For example:

```sql
SELECT
    id,
    email,
    created_at
FROM users
WHERE email = $1;
```

With an appropriate index:

```sql
CREATE UNIQUE INDEX idx_users_email
ON users (email);
```

the database can locate the matching row through the index rather than scanning every row in `users`.

However, an index is not automatically useful just because a column appears in `WHERE`. The optimizer considers selectivity, table size, statistics, estimated cost, available indexes, query predicates, ordering, and the number of rows expected to be returned.

The practical rule is:

> **Design indexes around important query patterns, then verify their value with execution plans and production workload data.**

## How WHERE Indexing Works

Without an index, a typical table scan looks conceptually like:

```text
Table
 │
 ├── Row 1 → evaluate WHERE
 ├── Row 2 → evaluate WHERE
 ├── Row 3 → evaluate WHERE
 ├── ...
 └── Row N → evaluate WHERE
```

For a large table, this can require reading a substantial portion of the table.

With an index:

```text
WHERE condition
      │
      ▼
    Index
      │
      ▼
Matching row locations
      │
      ▼
     Table
      │
      ▼
Required rows
```

The index stores searchable values and references to table rows. The exact implementation varies by database and index type, but the goal is the same: reduce the amount of data that must be examined.

## Equality Conditions

Equality predicates are among the simplest and most common index candidates.

```sql
SELECT *
FROM users
WHERE account_id = $1;
```

An index can be created with:

```sql
CREATE INDEX idx_users_account_id
ON users (account_id);
```

This is particularly useful when:

- The table is large.
- The predicate is selective.
- The query executes frequently.
- Only a small fraction of rows match.
- The index can avoid substantial table I/O.

### High-Selectivity Example

Suppose a table contains:

```text
10,000,000 users
1 matching account_id
```

An index on `account_id` can dramatically reduce the search space.

### Low-Selectivity Example

Suppose:

```text
10,000,000 rows
9,500,000 rows have status = 'active'
```

Then:

```sql
WHERE status = 'active'
```

may not benefit much from a normal index because the query needs most of the table anyway.

The optimizer may reasonably choose a sequential scan.

## Range Conditions

Indexes can also support range predicates:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

An index such as:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

can efficiently locate rows within the requested range.

Common range predicates include:

```sql
>
>=
<
<=
BETWEEN
```

For time-series and event data, indexes on timestamp columns are common, but their usefulness depends on how narrow the requested time range is.

## `IN` Conditions

Indexes can generally support equality-style membership conditions:

```sql
SELECT *
FROM orders
WHERE customer_id IN ($1, $2, $3);
```

with:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

The optimizer may perform multiple index lookups or use another access strategy depending on the number of values and estimated result size.

As the number of values grows, an index may become less attractive than a sequential or bitmap-oriented strategy.

## `IS NULL` and `IS NOT NULL`

NULL predicates require careful reasoning.

Example:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL;
```

An index may be useful, but usefulness depends on the distribution of NULL and non-NULL values.

If almost every row has:

```text
deleted_at IS NULL
```

then a normal index may not be attractive.

A partial index can be much more effective:

```sql
CREATE INDEX idx_users_active
ON users (id)
WHERE deleted_at IS NULL;
```

This is especially useful when the application predominantly works with active records.

## Boolean Columns

Boolean columns are common candidates for over-indexing.

Consider:

```sql
SELECT *
FROM users
WHERE is_active = true;
```

If 98% of users are active, an index on:

```sql
is_active
```

may provide little benefit for this query.

If only 1% are active, the index may be significantly more useful.

A better production design might also use a partial index when the workload consistently targets a subset:

```sql
CREATE INDEX idx_users_active_id
ON users (id)
WHERE is_active = true;
```

The important factor is **data distribution**, not the fact that the column is boolean.

## `LIKE` and Pattern Matching

String predicates require special attention.

A query such as:

```sql
SELECT *
FROM users
WHERE email LIKE 'admin%';
```

can potentially use a B-tree index because the pattern has a fixed prefix.

But:

```sql
WHERE email LIKE '%admin%'
```

generally cannot use a normal B-tree index effectively for arbitrary substring matching.

The difference is:

```text
'admin%'
 │
 └── known prefix → potentially indexable

'%admin%'
 │
 └── unknown starting position → normal B-tree unsuitable
```

For substring or full-text workloads, consider database-specific alternatives such as trigram or full-text indexes.

## Functions in WHERE Conditions

A common performance problem occurs when a query applies a function to an indexed column:

```sql
SELECT *
FROM users
WHERE LOWER(email) = LOWER($1);
```

A normal index on:

```sql
email
```

may not be usable for the expression:

```text
LOWER(email)
```

because the indexed value is `email`, while the predicate operates on a transformed value.

A functional index can solve this:

```sql
CREATE INDEX idx_users_lower_email
ON users (LOWER(email));
```

Now the indexed expression matches the query expression.

The same principle applies to:

```sql
DATE(created_at)
COALESCE(...)
UPPER(...)
TRIM(...)
```

when the database supports appropriate expression indexes.

## Implicit Type Conversion

Type mismatches can interfere with index usage or produce inefficient plans.

For example, suppose:

```sql
user_id bigint
```

but application code sends an incompatible type that causes conversion.

Prefer parameter types that match the database schema.

In backend applications, ensure:

- ORM field types match database types.
- API input is validated and converted appropriately.
- SQL parameters are bound rather than interpolated.
- Comparisons do not unnecessarily cast indexed columns.

The goal is to keep the predicate aligned with the indexed representation.

## Multiple WHERE Conditions

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
  AND status = 'pending';
```

Possible indexes include:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);

CREATE INDEX idx_orders_status
ON orders (status);
```

or a composite index:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

The composite index can be preferable when the combined predicate is a frequent access pattern.

It is generally more useful to ask:

> "What are the application's high-frequency query shapes?"

rather than:

> "Which individual columns appear in WHERE?"

## Composite Indexes for WHERE Conditions

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
  AND status = $2
  AND created_at >= $3;
```

A possible index is:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at);
```

The index is ordered lexicographically:

```text
customer_id
    ↓
status
    ↓
created_at
```

This can efficiently support equality predicates on the leading columns followed by a range condition.

A common pattern is:

```text
equality columns
      ↓
range column
      ↓
ordering requirements
```

This is a useful starting heuristic, but actual index design must consider the complete workload.

## Column Order Matters

These indexes are different:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

and:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

For:

```sql
WHERE customer_id = $1
  AND status = 'pending'
```

both may be useful.

But for:

```sql
WHERE customer_id = $1;
```

the first index is naturally aligned with the leading column, while the second begins with `status`.

This is the **leftmost-prefix principle** commonly associated with B-tree composite indexes.

Do not assume that:

```text
(A, B)
```

and:

```text
(B, A)
```

are interchangeable.

## Selectivity

Selectivity describes how effectively a predicate narrows the result set.

Conceptually:

```text
High selectivity
10,000,000 rows
       ↓
10 matching rows

Low selectivity
10,000,000 rows
       ↓
8,000,000 matching rows
```

Indexes are generally more attractive when a predicate identifies a relatively small portion of the table.

Typical high-selectivity columns might include:

- UUIDs.
- Account identifiers.
- Order IDs.
- Unique email addresses.
- Timestamps for narrow time ranges.

Typical low-selectivity columns might include:

- Boolean flags.
- Status values with only a few categories.
- Gender or other low-cardinality attributes.

Low-cardinality columns are not automatically bad indexes. A partial or composite index can still make them useful.

## Cardinality vs Selectivity

These terms are related but not identical.

**Cardinality** describes the number of distinct values.

For:

```text
status = pending | completed | failed
```

cardinality is low.

For:

```text
user_id
```

with millions of users, cardinality is high.

**Selectivity** describes how much a particular predicate narrows the rows.

A high-cardinality column often provides strong selectivity, but actual data distribution matters.

## Query Shape Matters More Than Individual Columns

Suppose an API frequently executes:

```sql
SELECT
    id,
    total,
    created_at
FROM orders
WHERE customer_id = $1
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 20;
```

The query's access pattern is:

```text
customer_id
    +
status
    +
created_at ordering
    +
LIMIT 20
```

A production-oriented index might be:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC)
INCLUDE (id, total);
```

This is much more deliberate than creating independent indexes on every column.

## WHERE + ORDER BY

An index can sometimes optimize both filtering and ordering.

Query:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

Potential index:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

Conceptually:

```text
customer_id = 42
       ↓
matching index range
       ↓
already ordered by created_at DESC
       ↓
first 50 rows
```

This can avoid:

- Scanning unrelated rows.
- Sorting a large intermediate result.
- Processing rows that cannot contribute to the first page.

## WHERE + JOIN + ORDER BY

Production queries often combine all three:

```sql
SELECT
    o.id,
    o.created_at,
    c.name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.status = 'pending'
  AND o.created_at >= $1
ORDER BY o.created_at DESC
LIMIT 50;
```

Possible indexes include:

```sql
CREATE INDEX idx_orders_status_created
ON orders (status, created_at DESC);
```

and an existing:

```text
customers.id
```

primary-key index.

The correct design depends on:

- Number of pending orders.
- Time-range selectivity.
- Join cardinality.
- Sort requirements.
- Result size.
- Query frequency.

Always validate the final design using the actual execution plan.

## Partial Indexes for WHERE Conditions

Partial indexes are valuable when queries repeatedly target a stable subset of rows.

Example:

```sql
CREATE INDEX idx_orders_pending_customer
ON orders (customer_id, created_at DESC)
WHERE status = 'pending';
```

This index contains only pending orders.

Query:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE status = 'pending'
  AND customer_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

Advantages:

- Smaller index.
- Lower storage consumption.
- Potentially better cache efficiency.
- Less index maintenance for rows outside the predicate.

Limitations:

- Only useful for predicates compatible with the partial-index condition.
- Not a general replacement for a full index.
- More difficult to reason about if query predicates vary significantly.

## Covering Indexes for WHERE Conditions

If a query frequently filters using one set of columns and returns another small set, an index can sometimes include the returned columns.

PostgreSQL example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC)
INCLUDE (id, total);
```

Query:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

The key columns drive lookup and ordering:

```text
customer_id
created_at
```

while:

```text
id
total
```

are stored as included payload.

This can enable an index-only scan when PostgreSQL can satisfy visibility requirements from its visibility map.

Covering indexes should be used selectively because larger indexes increase:

- Storage.
- Cache pressure.
- Write amplification.
- Index build time.
- Maintenance cost.

## Sargable Predicates

A predicate is commonly described as **sargable** when the database can use an index efficiently to search for qualifying values.

Prefer:

```sql
WHERE created_at >= $1
```

over transformations such as:

```sql
WHERE DATE(created_at) = $1
```

The second form applies a function to the indexed column.

A better equivalent range is often:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

For a day-based query, the application can calculate the appropriate time boundaries and pass them as parameters.

The principle is:

> **Keep indexed columns in forms that allow the optimizer to use the index's search ordering.**

## OR Conditions

Queries containing `OR` can be more difficult to optimize:

```sql
SELECT *
FROM users
WHERE email = $1
   OR phone = $2;
```

Separate indexes may be useful:

```sql
CREATE UNIQUE INDEX idx_users_email
ON users (email);

CREATE UNIQUE INDEX idx_users_phone
ON users (phone);
```

The optimizer may combine multiple indexes or choose another strategy.

In some cases, query rewriting can produce a better plan, but rewriting solely to force index usage should be done only after measuring.

## `NOT`, `<>`, and Negative Predicates

Predicates such as:

```sql
WHERE status <> 'deleted'
```

can be difficult to optimize with a simple index when most rows satisfy the condition.

Likewise:

```sql
WHERE NOT is_deleted
```

may return a large percentage of the table.

The optimizer may prefer a sequential scan.

If the application consistently targets the small active subset, a partial index can be more appropriate:

```sql
CREATE INDEX idx_users_active
ON users (id)
WHERE is_deleted = false;
```

## `IN` vs Large Lists

A small:

```sql
WHERE id IN (...)
```

can be efficiently handled using an index.

But very large `IN` lists can change the cost calculation.

For example, instead of sending thousands of identifiers as a huge SQL expression, consider a staging or temporary relation and join against it:

```text
Application
    ↓
Batch identifiers
    ↓
Temporary/staging relation
    ↓
JOIN
    ↓
Target table
```

The appropriate strategy depends on workload, database, and transaction requirements.

## Pagination and WHERE Conditions

Offset pagination can become increasingly expensive:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50 OFFSET 100000;
```

The database may still need to locate and discard many rows.

For high-volume APIs, keyset pagination can be more efficient:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

An index aligned with the predicate and ordering can support this pattern:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at DESC, id DESC);
```

This is particularly valuable for large feeds, event streams, and customer order histories.

## Query Planner Decisions

An index does not force index usage.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = $1;
```

the planner estimates the cost of available plans.

Possible outcomes include:

```text
Index Scan
Bitmap Index Scan
Bitmap Heap Scan
Index Only Scan
Sequential Scan
```

A sequential scan can be the correct choice.

For example:

```text
Table = 100,000 rows
Predicate matches = 80,000 rows
```

Using an index could require many heap accesses, while a sequential scan can read the table efficiently.

## Bitmap Scans

PostgreSQL can use bitmap access when a predicate matches many rows.

Conceptually:

```text
Index
  ↓
Collect matching row locations
  ↓
Build bitmap
  ↓
Read heap pages efficiently
  ↓
Return rows
```

This can be particularly useful for moderately selective predicates.

It is another reason not to interpret:

```text
"Index exists"
```

as:

```text
"Index Scan must be used"
```

## Statistics and WHERE Indexes

The optimizer relies on statistics to estimate how many rows a predicate will match.

If statistics are inaccurate:

```text
Estimated rows = 10
Actual rows    = 500,000
```

the optimizer may choose an inappropriate plan.

PostgreSQL collects statistics through `ANALYZE` and autovacuum-related maintenance.

For a manually investigated query:

```sql
ANALYZE orders;
```

can refresh planner statistics.

For production systems, investigate why statistics are stale rather than treating manual `ANALYZE` as a permanent substitute for healthy database maintenance.

## Inspecting Existing Indexes

Before adding an index, inspect the schema.

In PostgreSQL:

```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'orders';
```

This helps prevent duplicate or overlapping indexes.

For example, before creating:

```sql
(customer_id, status)
```

check whether existing indexes already provide sufficient coverage.

## Measuring Index Usage

PostgreSQL exposes index usage statistics through system views such as:

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY idx_scan DESC;
```

A rarely used index may still be required for an important but infrequent query, so low usage alone is not proof that an index should be removed.

Use statistics as evidence, not as an automatic deletion mechanism.

## Production Example

Consider an order API:

```text
GET /customers/{customer_id}/orders?status=pending
```

The backend generates:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 50;
```

A possible index is:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC)
INCLUDE (id, total);
```

The access pattern is:

```text
customer_id
    ↓
status
    ↓
created_at DESC
    ↓
LIMIT 50
    ↓
id + total
```

The index is designed for the query's complete access pattern rather than simply indexing:

```text
customer_id
status
created_at
```

independently.

Whether this index is appropriate should be validated using:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 50;
```

## ORM Considerations

ORM abstractions do not remove the need for database index design.

Django model:

```python
class Order(models.Model):
    customer_id = models.BigIntegerField()
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(
                fields=["customer_id", "status", "-created_at"],
                name="idx_order_customer_status_created",
            ),
        ]
```

The important consideration is the generated SQL:

```sql
WHERE customer_id = ...
  AND status = ...
ORDER BY created_at DESC
```

not merely the ORM declaration.

For production systems:

- Inspect generated SQL.
- Identify high-frequency query patterns.
- Measure query latency.
- Review execution plans.
- Avoid creating indexes for hypothetical queries.
- Revisit indexes as access patterns change.

## Security Considerations

Indexes do not provide authorization.

This query:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;
```

may be efficiently indexed, but the application must still verify that the authenticated caller is authorized to access that customer's data.

Also use parameterized queries:

```python
cursor.execute(
    """
    SELECT id, total
    FROM orders
    WHERE customer_id = %s
    """,
    [customer_id],
)
```

Do not construct SQL by concatenating untrusted values.

Indexes improve data access performance; they do not replace application-level authorization or SQL injection defenses.

## Scalability and Cost

As tables grow, index design becomes increasingly important.

However, every index has a cost:

| Cost | Production impact |
|---|---|
| Disk space | Larger storage requirements |
| Write amplification | More work on INSERT/UPDATE/DELETE |
| Cache pressure | More pages competing for memory |
| Build time | Longer index creation on large tables |
| Replication | Additional WAL and replica work |
| Maintenance | More objects to monitor and maintain |

For high-write workloads, an index that saves 5 ms on a low-value query may not justify significant write overhead.

Prioritize indexes using:

```text
Query frequency
×
Query latency
×
Business importance
×
Resource consumption
```

rather than adding indexes indiscriminately.

## High Availability and Index Deployment

Adding an index to a large production table requires operational planning.

PostgreSQL supports:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_status
ON orders (customer_id, status);
```

This can reduce blocking of concurrent writes compared with a conventional index build, but it has additional operational considerations and can take longer.

For production deployments:

- Estimate index size.
- Estimate build duration.
- Check available storage.
- Consider replica impact.
- Monitor database load.
- Use appropriate migration tooling.
- Avoid deploying several large index builds simultaneously without capacity planning.

Test index migrations against production-scale data whenever possible.

## Common Mistakes and Pitfalls

### Indexing Every WHERE Column Independently

A schema with:

```text
index(status)
index(customer_id)
index(created_at)
```

is not automatically better than one workload-specific composite index.

**Why it happens:** developers optimize columns instead of query patterns.

**Avoid it:** start with actual high-value queries and their execution plans.

### Indexing Low-Selectivity Columns Blindly

An index on:

```sql
is_active
```

may be ineffective when almost every row has the same value.

**Avoid it:** inspect data distribution and planner decisions.

### Applying Functions to Indexed Columns

Example:

```sql
WHERE DATE(created_at) = $1
```

can prevent efficient use of a normal `created_at` index.

**Avoid it:** use a range predicate or an appropriate expression index.

### Ignoring Column Order

These are not equivalent:

```text
(customer_id, status)
(status, customer_id)
```

**Avoid it:** design composite indexes according to actual predicates and ordering requirements.

### Creating Duplicate Indexes

For example:

```text
(customer_id)
(customer_id, status)
```

may both be justified, but not always.

**Avoid it:** inspect existing indexes before adding new ones.

### Assuming an Index Must Be Used

A sequential scan can be faster when a query returns a large percentage of the table.

**Avoid it:** trust measured execution plans rather than forcing index usage.

### Ignoring `ORDER BY`

An index can sometimes satisfy both:

```text
WHERE
```

and:

```text
ORDER BY
```

A design that ignores ordering may require an expensive sort.

**Avoid it:** consider the full query shape.

### Ignoring Pagination

Large offsets can remain expensive even with indexes.

**Avoid it:** use keyset pagination for high-volume ordered datasets when the API semantics permit it.

### Treating ORM Indexes as a Guarantee

Defining an index in Django does not guarantee that every ORM query will use it.

**Avoid it:** inspect generated SQL and database execution plans.

## Interview Traps

### "Does every WHERE condition need an index?"

No. Indexes are useful when they reduce the estimated cost of accessing qualifying rows. A sequential scan may be faster for large result sets.

### "Which WHERE columns should I index?"

Start with frequently executed, performance-critical predicates and consider:

- Selectivity.
- Table size.
- Query frequency.
- Predicate combinations.
- Ordering.
- Result cardinality.
- Write overhead.

### "Is a composite index always better than separate indexes?"

No.

A composite index is optimized for particular column combinations and ordering. Separate indexes may be more flexible for independent query patterns, while composite indexes can be substantially better for specific multi-column queries.

### "Why does my database ignore an index?"

Possible reasons include:

- Low selectivity.
- Small table.
- Query returns many rows.
- Stale statistics.
- Poor cardinality estimates.
- Cost of random heap access.
- Another available plan is cheaper.
- Predicate does not align with the index.
- Type conversion or expression prevents efficient matching.

### "Does adding an index always make queries faster?"

No.

Indexes can make reads faster while making writes slower and increasing storage and maintenance costs.

### "Is indexing a boolean column useless?"

No. It depends on data distribution and query patterns. A partial or composite index can make a low-cardinality predicate highly useful.

## Key Takeaways

- **Index `WHERE` conditions based on real query patterns, selectivity, frequency, and execution plans—not simply because a column appears in a predicate.**
- **Composite indexes should align with the complete access pattern, including equality predicates, range predicates, `ORDER BY`, and pagination requirements.**
- **Keep predicates index-friendly: avoid unnecessary functions, casts, and transformations on indexed columns; use expression indexes when transformation is intentional.**
- **An existing index does not guarantee an index scan; the optimizer may correctly choose sequential, bitmap, hash, or other access strategies when they are cheaper.**
- **Every index has operational cost through storage, write amplification, cache pressure, maintenance, and replication overhead, so production indexes should be justified by measured workload value.**