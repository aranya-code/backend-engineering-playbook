# 18- Indexes for ORDER BY

## Overview

`ORDER BY` determines the order in which a query returns rows. Without a suitable index, the database may need to retrieve a result set and explicitly sort it before returning the requested rows.

For example:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

A suitable index can potentially provide rows in the required order:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

This matters most for production queries that combine:

- `WHERE`
- `ORDER BY`
- `LIMIT`
- Pagination
- Large datasets
- High request volume

The important distinction is:

> **An index does not merely make filtering faster; an appropriately ordered index can also eliminate or reduce the cost of sorting.**

The optimizer is still free to choose another plan when sorting is cheaper.

## Why ORDER BY Can Be Expensive

Consider:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC;
```

Without an index that provides the requested ordering, the database may need to:

```text
Read rows
   ↓
Produce candidate result set
   ↓
Sort rows
   ↓
Return ordered result
```

For `N` rows, a general-purpose sort is typically on the order of:

```text
O(N log N)
```

The actual implementation and cost depend on the database engine, available memory, data types, parallelism, and query plan.

For a large result set, sorting can consume substantial:

- CPU
- Memory
- Temporary storage
- I/O

An index can instead provide an already ordered traversal:

```text
B-tree index
     ↓
ordered leaf entries
     ↓
first matching entry
     ↓
next entry
     ↓
next entry
     ↓
LIMIT reached
```

This is particularly valuable when only a small number of rows are required.

## How Indexes Provide Ordering

B-tree indexes maintain keys in sorted order.

For:

```sql
CREATE INDEX idx_orders_created
ON orders (created_at);
```

the index is conceptually ordered as:

```text
2026-01-01
2026-01-02
2026-01-03
...
2026-08-31
```

A forward traversal can provide ascending order:

```sql
ORDER BY created_at ASC
```

and a backward traversal can often provide descending order:

```sql
ORDER BY created_at DESC
```

Therefore, for a simple single-column B-tree index, explicitly declaring `DESC` is often not necessary merely to support the opposite direction.

However, direction becomes more important for **multi-column indexes**, especially when different columns need different sort directions.

## ORDER BY Without WHERE

For:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
ORDER BY created_at DESC
LIMIT 50;
```

an index such as:

```sql
CREATE INDEX idx_orders_created
ON orders (created_at);
```

can allow the database to traverse the index in descending order and stop after 50 rows.

Conceptually:

```text
Index
created_at
   ↓
latest row
   ↓
next latest row
   ↓
...
   ↓
50 rows
```

This can be substantially cheaper than:

```text
scan millions of rows
        ↓
sort millions of rows
        ↓
return 50 rows
```

The `LIMIT` makes this access pattern particularly valuable.

## ORDER BY With WHERE

The more common production pattern is:

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

A composite index can align both operations:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

The index structure is conceptually:

```text
customer_id = 100
    ├── latest order
    ├── next order
    ├── next order
    └── ...

customer_id = 101
    ├── latest order
    ├── next order
    └── ...
```

The database can locate the customer's section and traverse it in the required order.

This is one of the most valuable index patterns for backend APIs.

## Filtering Before Ordering

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

An index on only:

```sql
created_at
```

can provide ordering, but it may still require the database to inspect many unrelated customers.

An index on:

```text
(customer_id, created_at)
```

aligns the access pattern more closely:

```text
customer_id filter
        ↓
matching index range
        ↓
created_at ordering
        ↓
LIMIT 20
```

This can dramatically reduce the number of index entries and table rows that need to be processed.

## Composite Index Column Order

Column order is critical.

Compare:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

with:

```sql
CREATE INDEX idx_orders_created_customer
ON orders (created_at, customer_id);
```

For:

```sql
WHERE customer_id = $1
ORDER BY created_at DESC
```

the first index is generally much better aligned with the access pattern.

The first index organizes data as:

```text
customer_id
    ↓
created_at
```

The second organizes data as:

```text
created_at
    ↓
customer_id
```

The database cannot generally treat the two indexes as interchangeable.

A useful starting heuristic is:

```text
Equality filtering
      ↓
Range filtering
      ↓
Ordering
      ↓
Additional covering columns
```

This is a heuristic, not an absolute rule. Actual workload and optimizer behavior determine the final design.

## Mixed Sort Directions

Consider:

```sql
SELECT *
FROM events
ORDER BY tenant_id ASC, created_at DESC;
```

An index such as:

```sql
CREATE INDEX idx_events_tenant_created
ON events (tenant_id ASC, created_at DESC);
```

matches the requested ordering.

This becomes important because a multi-column index cannot always satisfy arbitrary combinations of sort directions using a simple forward or backward traversal.

For example:

```text
(tenant_id ASC, created_at DESC)
```

is different from:

```text
(tenant_id ASC, created_at ASC)
```

when the query requires mixed directions.

### Direction and PostgreSQL

PostgreSQL B-tree indexes support explicit per-column sort direction:

```sql
CREATE INDEX idx_events_tenant_created
ON events (tenant_id ASC, created_at DESC);
```

This is particularly useful for queries requiring mixed ordering.

For a single-column index:

```sql
(created_at ASC)
```

PostgreSQL can generally scan the B-tree backward to satisfy:

```sql
ORDER BY created_at DESC
```

But a mixed-direction multi-column requirement may need the index definition to encode the desired ordering.

## ORDER BY and LIMIT

`ORDER BY` becomes especially valuable with `LIMIT`.

Compare:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC;
```

with:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 20;
```

If an index provides the ordering, the second query can potentially stop after reading only the required rows.

Conceptually:

```text
Index traversal
      ↓
row 1
      ↓
row 2
      ↓
...
      ↓
row 20
      ↓
STOP
```

This is a major optimization for:

- Latest records.
- Dashboards.
- Feeds.
- Admin interfaces.
- Search results.
- API pagination.
- Event processing.

## Top-N Queries

A query such as:

```sql
SELECT
    id,
    total
FROM orders
ORDER BY total DESC
LIMIT 10;
```

is a classic **Top-N** query.

A suitable index can allow the database to find the highest values without sorting the entire table:

```sql
CREATE INDEX idx_orders_total
ON orders (total DESC);
```

The optimizer may still choose a sequential scan plus sort if it estimates that to be cheaper.

This is especially relevant when:

- The table is large.
- `LIMIT` is small.
- The requested ordering is stable.
- The index is selective or highly useful for the access pattern.

## WHERE + ORDER BY + LIMIT

This is one of the highest-value patterns to recognize:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 20;
```

A candidate index is:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

The intended access path is:

```text
customer_id
     ↓
status
     ↓
created_at DESC
     ↓
first 20 rows
```

The index is designed around the query, not around the individual columns in isolation.

## ORDER BY and Covering Indexes

Suppose:

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

A PostgreSQL index can include additional payload columns:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC)
INCLUDE (id, total);
```

The key columns provide:

```text
customer_id
created_at
```

while:

```text
id
total
```

are included as non-key payload.

This can enable an index-only scan when PostgreSQL's visibility requirements permit it.

Covering indexes can reduce heap access, but they also make indexes larger.

## ORDER BY and Keyset Pagination

Offset pagination becomes increasingly expensive at large offsets:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50 OFFSET 100000;
```

Even with an index, the database may need to walk past many rows before returning the requested page.

Keyset pagination instead uses the last row from the previous page as a cursor:

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

The corresponding index:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at DESC, id DESC);
```

allows the database to seek near the cursor and continue traversing the index.

This is generally a better scaling pattern for large ordered datasets.

## Deterministic Ordering

Never assume that:

```sql
ORDER BY created_at DESC
```

produces a deterministic order when multiple rows have the same timestamp.

For stable pagination, add a unique tie-breaker:

```sql
ORDER BY created_at DESC, id DESC;
```

Then create an aligned index:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at DESC, id DESC);
```

This is especially important for:

- REST APIs.
- Infinite scrolling.
- Keyset pagination.
- Event feeds.
- Distributed systems.

Without a deterministic tie-breaker, rows with equal sort keys may appear in different relative positions across executions.

## NULL Ordering

NULL values require attention.

For example:

```sql
ORDER BY created_at DESC NULLS LAST;
```

The requested NULL positioning may affect whether an existing index can directly satisfy the ordering.

In PostgreSQL, index definitions can explicitly specify NULL positioning:

```sql
CREATE INDEX idx_orders_created
ON orders (created_at DESC NULLS LAST);
```

The query and index ordering should be evaluated together.

Do not assume that:

```text
ASC/DESC
```

is the only ordering dimension. NULL placement can matter as well.

## ORDER BY Expressions

A normal index on:

```sql
created_at
```

does not automatically mean that this expression is efficiently ordered:

```sql
ORDER BY DATE(created_at);
```

The query orders by the transformed expression.

If the workload genuinely requires ordering by that expression, an expression index may be appropriate:

```sql
CREATE INDEX idx_orders_created_date
ON orders ((DATE(created_at)));
```

However, expression indexes should be introduced deliberately because they:

- Increase write overhead.
- Consume storage.
- Depend on expression semantics.
- Serve a narrower query pattern.

Often the better design is to order by the original timestamp when application semantics permit it.

## ORDER BY Functions and Computed Values

Consider:

```sql
ORDER BY LOWER(email);
```

A regular:

```sql
CREATE INDEX idx_users_email
ON users (email);
```

does not necessarily provide ordering by:

```sql
LOWER(email)
```

A PostgreSQL expression index can align the index with the query:

```sql
CREATE INDEX idx_users_lower_email
ON users (LOWER(email));
```

The expression in the query and index should match sufficiently for the optimizer to recognize the access path.

## Sorting After Filtering

Consider:

```sql
SELECT *
FROM orders
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 50;
```

An index on:

```sql
created_at
```

can provide global ordering, but the database may still need to examine many rows before finding enough `pending` rows.

An index on:

```sql
(status, created_at DESC)
```

can directly narrow to the desired status and preserve the requested order:

```sql
CREATE INDEX idx_orders_status_created
ON orders (status, created_at DESC);
```

Conceptually:

```text
status = pending
       ↓
ordered pending rows
       ↓
latest 50
```

This is often much more useful for a query with a selective leading predicate.

## When a Sort Is Still Better

An index is not automatically preferable.

Suppose:

```text
Table: 100,000 rows
Query returns: 90,000 rows
```

Using an index may require many random heap accesses.

A sequential scan followed by an in-memory or efficient external sort may be cheaper.

The optimizer evaluates alternatives such as:

```text
Sequential Scan
      +
Sort

versus

Index Scan
      +
already ordered output
```

The correct choice depends on estimated cost.

## Execution Plans

Use execution plans to verify whether an index is actually helping.

PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC
LIMIT 50;
```

Look for operations such as:

```text
Index Scan
Index Only Scan
Bitmap Heap Scan
Sort
Incremental Sort
Seq Scan
```

A plan containing:

```text
Sort
```

does not automatically indicate a problem. The database may correctly determine that sorting is cheaper than using an index.

The important question is whether the total execution cost and observed latency are acceptable for the production workload.

## Incremental Sort

Modern PostgreSQL versions can use **incremental sort** in suitable cases.

If input data is already partially ordered, the database may sort smaller groups instead of sorting the complete input as one large operation.

Conceptually:

```text
Partially ordered input
        ↓
group 1 → sort
group 2 → sort
group 3 → sort
        ↓
ordered output
```

This can be useful when an index provides a prefix of the requested ordering but not the complete ordering.

The optimizer decides whether incremental sorting is worthwhile.

## ORDER BY and JOINs

Consider:

```sql
SELECT
    o.id,
    o.created_at,
    c.name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.status = 'pending'
ORDER BY o.created_at DESC
LIMIT 50;
```

An index on:

```sql
orders(status, created_at DESC)
```

may help the database find pending orders in the desired order.

The join still requires an efficient lookup for:

```text
customers.id
```

which is normally provided by the primary-key index.

The final plan depends on:

- Join order.
- Cardinality estimates.
- Predicate selectivity.
- Number of rows.
- Ordering requirements.
- Available indexes.

Never design the `ORDER BY` index without considering the rest of the query.

## Indexes for Latest-Row Queries

A common backend requirement is:

> Get the latest record for each request.

For a single entity:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 1;
```

An index such as:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

is well aligned with this access pattern.

The combination:

```text
customer_id
+
created_at DESC
+
LIMIT 1
```

can allow the database to locate the newest matching row with very little work.

This pattern appears frequently in:

- Latest payment state.
- Latest customer activity.
- Latest job execution.
- Latest device event.
- Latest status transition.

## Indexes for Feeds

A typical feed query:

```sql
SELECT
    id,
    author_id,
    body,
    created_at
FROM posts
WHERE author_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

can use:

```sql
CREATE INDEX idx_posts_author_created_id
ON posts (author_id, created_at DESC, id DESC);
```

This gives the application:

```text
author filter
     ↓
newest-first ordering
     ↓
stable tie-breaker
     ↓
small page
```

This pattern scales significantly better than repeatedly querying large offsets.

## Indexes for Queue-Like Queries

Consider a worker retrieving pending jobs:

```sql
SELECT
    id,
    payload
FROM jobs
WHERE status = 'pending'
ORDER BY created_at
LIMIT 100;
```

A candidate index is:

```sql
CREATE INDEX idx_jobs_pending_created
ON jobs (created_at)
WHERE status = 'pending';
```

This partial index contains only pending jobs.

For PostgreSQL workloads where multiple workers claim jobs concurrently, indexing is only one part of the design. Row-locking behavior, transaction isolation, `FOR UPDATE SKIP LOCKED`, job visibility, retries, and worker concurrency must also be considered.

For example:

```sql
SELECT
    id,
    payload
FROM jobs
WHERE status = 'pending'
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

The index can reduce the search space, while `SKIP LOCKED` helps multiple workers avoid waiting on rows already claimed by another worker.

## Django Example

Django can define an index matching an ordering pattern:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.BigIntegerField()
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(
                fields=["customer_id", "-created_at"],
                name="idx_order_customer_created",
            ),
        ]
```

A query such as:

```python
orders = (
    Order.objects
    .filter(customer_id=customer_id)
    .order_by("-created_at")[:50]
)
```

can generate an access pattern aligned with the index.

Still verify the generated SQL and database execution plan. ORM configuration alone does not prove that the optimizer will use the index.

## FastAPI and REST API Example

A REST endpoint such as:

```text
GET /customers/42/orders?limit=50
```

often maps to:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
LIMIT $2;
```

A production design should consider:

- Maximum page size.
- Stable ordering.
- Keyset pagination.
- Appropriate composite indexes.
- Parameter validation.
- Query timeout.
- Observability.
- Database connection pooling.

The API should not allow an arbitrary client to request:

```text
LIMIT 1000000
```

and turn a well-indexed endpoint into an expensive database operation.

## Common Mistakes and Pitfalls

### Indexing Only the ORDER BY Column

Creating:

```sql
CREATE INDEX idx_orders_created
ON orders (created_at);
```

for:

```sql
WHERE customer_id = $1
ORDER BY created_at DESC
```

may leave the database with substantial filtering work.

**Avoid it:** consider the combined `WHERE` + `ORDER BY` access pattern.

### Ignoring LIMIT

A query with:

```sql
ORDER BY created_at DESC
LIMIT 20
```

has very different optimization opportunities from a query that returns the entire table.

**Avoid it:** design indexes around actual result size and pagination behavior.

### Ignoring Tie-Breakers

Using:

```sql
ORDER BY created_at DESC
```

for pagination can produce unstable ordering when timestamps collide.

**Avoid it:** use a unique secondary key:

```sql
ORDER BY created_at DESC, id DESC
```

### Assuming ASC and DESC Are Always Equivalent

For a single B-tree column, reverse traversal often handles the opposite direction.

For multi-column indexes with mixed directions, it may not.

**Avoid it:** explicitly reason about the complete ordering requirement.

### Sorting Expressions Without Matching Indexes

Example:

```sql
ORDER BY LOWER(email)
```

with only:

```sql
INDEX(email)
```

may not provide the desired ordered access path.

**Avoid it:** use an expression index when the expression is a stable, justified query requirement.

### Creating an Index for Every ORDER BY

An index for every possible sort order creates excessive write and storage overhead.

**Avoid it:** prioritize production query patterns.

### Assuming an Index Eliminates Every Sort

The optimizer may still need:

```text
Sort
```

because the index does not fully satisfy the ordering or because sorting is cheaper.

**Avoid it:** evaluate `EXPLAIN (ANALYZE, BUFFERS)` rather than expecting a particular node.

### Using Large OFFSET Values

Even with a good ordering index:

```sql
OFFSET 500000
```

can require walking through many rows.

**Avoid it:** use keyset pagination for large ordered datasets.

### Ignoring NULL Ordering

Different NULL placement requirements can prevent an index from directly matching the requested order.

**Avoid it:** explicitly define and align NULL semantics where necessary.

## Production Considerations

### Measure Before Adding the Index

Start with real queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC
LIMIT 50;
```

Record:

- Execution time.
- Rows examined.
- Rows returned.
- Buffer hits.
- Buffer reads.
- Sort operations.
- Temporary I/O.
- Index usage.

Then compare after the index is introduced.

### Monitor Index Size

PostgreSQL:

```sql
SELECT
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size,
    idx_scan
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY pg_relation_size(indexrelid) DESC;
```

A large index can affect:

- Storage cost.
- Buffer-cache efficiency.
- Backup size.
- Replication traffic.
- Index maintenance.

### Consider Write Amplification

Every insert may need to update relevant indexes.

Updates that modify indexed columns can also require additional index maintenance.

Therefore:

```text
More indexes
    ↓
More write work
    ↓
More WAL / replication work
    ↓
More storage and cache pressure
```

For high-write systems, indexes must justify their operational cost.

### Production Index Creation

On PostgreSQL, a large production index may be created concurrently:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

This can reduce blocking of concurrent writes compared with a regular index build, but it has its own operational requirements and can take longer.

Before creating a large index:

- Estimate index size.
- Check available disk capacity.
- Consider replica impact.
- Monitor database load.
- Test the migration.
- Have a rollback/remediation plan.

## Security Considerations

Indexes themselves are not an authorization mechanism.

For example:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

may be efficiently indexed, but the application must still verify that the authenticated caller is allowed to access that `customer_id`.

Also enforce reasonable API limits:

```text
maximum page size
maximum cursor size
query timeout
```

Use parameterized queries rather than constructing SQL from untrusted input.

Performance optimization must not weaken authorization or input validation.

## Interview Traps

### "Does ORDER BY always require a sort?"

No. A suitable index can provide rows in the required order, allowing the database to avoid an explicit sort.

### "Does an index on the ORDER BY column always make ORDER BY fast?"

No. If the query has a selective `WHERE` condition, an index aligned with the complete access pattern may be much better.

### "Can an index satisfy both WHERE and ORDER BY?"

Yes. Composite indexes are frequently designed specifically for this purpose.

For example:

```sql
(customer_id, created_at DESC)
```

can support:

```sql
WHERE customer_id = $1
ORDER BY created_at DESC
```

### "Why can the database still sort when an index exists?"

Possible reasons include:

- The index does not provide the required ordering.
- The query has additional ordering expressions.
- Mixed sort directions are incompatible with the index.
- NULL ordering differs.
- The optimizer estimates sorting to be cheaper.
- The result set is large enough that an index scan is expensive.

### "Why is ORDER BY + LIMIT such an important index pattern?"

Because an ordered index can allow the database to stop after finding the required number of rows.

```text
ordered index
     ↓
first row
     ↓
...
     ↓
Nth row
     ↓
STOP
```

This can avoid scanning and sorting a large dataset.

### "Is `(A, B)` equivalent to `(B, A)` for ORDER BY?"

No. Composite index order determines how entries are physically organized and which filtering and ordering patterns can be efficiently traversed.

### "Is keyset pagination just an indexing technique?"

No. It is a pagination strategy that uses an ordered, stable cursor. Indexes make the strategy efficient, but API semantics, cursor design, uniqueness, and consistency also matter.

## Key Takeaways

- **Design indexes around the complete query pattern: `WHERE` + `ORDER BY` + `LIMIT` + pagination, not `ORDER BY` in isolation.**
- **Composite index column order determines which filtering and ordering patterns can be efficiently traversed; `(A, B)` and `(B, A)` are not interchangeable.**
- **`ORDER BY` with a small `LIMIT` is a high-value indexing pattern because an ordered index can allow the database to stop after retrieving the required rows.**
- **Use deterministic ordering such as `created_at DESC, id DESC` for stable pagination, and prefer keyset pagination over large offsets for high-volume datasets.**
- **Always validate index effectiveness with execution plans and production measurements; an optimizer may correctly choose a sort or sequential scan even when an index exists.**