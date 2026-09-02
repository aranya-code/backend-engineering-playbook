# 10- Index Scans

## Overview

An index scan is a query execution strategy where the database uses an index to locate qualifying rows instead of examining every table row.

For selective queries against large tables, an index scan can reduce the amount of data that PostgreSQL needs to inspect:

```text
SQL Query
   ↓
Query Optimizer
   ↓
Index Scan
   ↓
Locate matching index entries
   ↓
Fetch required table rows
   ↓
Return result
```

Index scans are fundamental to high-performance OLTP systems. They are especially valuable for point lookups, selective filters, range queries, and queries whose ordering can be satisfied by an index.

However, an index scan is not automatically faster than a sequential scan. PostgreSQL chooses an index-based plan only when its cost model estimates that doing so is beneficial.

## Why Index Scans Exist

A sequential scan examines table pages broadly:

```text
Table
├── Page 1 → inspect
├── Page 2 → inspect
├── Page 3 → inspect
├── ...
└── Page N → inspect
```

An index provides a separate structure that helps locate relevant rows:

```text
Index
   ↓
Matching index entries
   ↓
Heap/table locations
   ↓
Required rows
```

For a large table containing millions of rows where a query needs only a few rows, avoiding unnecessary table-page processing can dramatically reduce CPU and I/O.

For example:

```sql
SELECT
    id,
    email
FROM users
WHERE email = 'customer@example.com';
```

If `email` has a suitable index and is highly selective, PostgreSQL can navigate the index directly to the relevant entry rather than scanning the entire table.

## How an Index Scan Works

A simplified B-tree index lookup looks like:

```text
Root page
   ↓
Internal index page
   ↓
Leaf page
   ↓
Matching index entry
   ↓
Heap tuple location
   ↓
Table page
   ↓
Visible row
```

The index generally stores indexed values together with information that identifies the corresponding table tuple.

PostgreSQL then performs the necessary table access to retrieve columns that are not available directly from the index.

The exact behavior depends on the index type, query, visibility state, selected columns, and execution plan.

## Basic Example

Create an index:

```sql
CREATE INDEX CONCURRENTLY idx_users_email
ON users (email);
```

Query the indexed column:

```sql
SELECT
    id,
    email
FROM users
WHERE email = 'customer@example.com';
```

Inspect the plan:

```sql
EXPLAIN
SELECT
    id,
    email
FROM users
WHERE email = 'customer@example.com';
```

A possible plan is:

```text
Index Scan using idx_users_email on users
  Index Cond: (email = 'customer@example.com')
```

The important part is:

```text
Index Cond
```

This indicates that the index is being used to identify candidate rows.

## Index Scan vs Sequential Scan

| Characteristic | Index Scan | Sequential Scan |
|---|---|---|
| Main access structure | Index | Table |
| Best suited for | Selective queries | Large portions of table |
| Small result set | Usually efficient | Often wasteful |
| Large result set | Can become expensive | Often efficient |
| Random table access | Can be significant | Usually lower |
| Requires suitable index | Yes | No |
| Index maintenance | Required | None |
| Can support ordering | Often | Usually requires sorting |
| Can avoid heap access | With suitable covering/index-only strategy | No |

Neither strategy is universally better.

The optimizer chooses based on estimated total cost.

## Selectivity and Index Scans

Selectivity is one of the most important factors affecting index usefulness.

Suppose a table contains:

```text
10,000,000 rows
```

and:

```sql
WHERE id = 123
```

returns:

```text
1 row
```

An index scan is an obvious candidate.

Now consider:

```sql
WHERE status = 'active'
```

where:

```text
9,500,000 rows = active
500,000 rows = inactive
```

Using an index for the `active` query may require finding and fetching millions of rows.

A sequential scan may be cheaper.

```text
Highly selective
10,000,000 rows
       ↓
      1 row
       ↓
Index scan is attractive


Low selectivity
10,000,000 rows
       ↓
9,500,000 rows
       ↓
Sequential scan may be attractive
```

## Index Scan Is Not the Same as "Fast"

An index scan can still be expensive.

Consider:

```text
Index Scan
  ↓
1,000,000 index entries
  ↓
1,000,000 heap fetches
  ↓
Large I/O workload
```

The index reduced the initial search space, but the database still has to retrieve a large number of rows.

This is why senior-level query analysis focuses on **total work**, not simply whether an index appears in the plan.

## Heap Fetches and Random Access

In PostgreSQL, an ordinary index scan often needs to access the heap to retrieve the complete row.

For example:

```sql
SELECT
    id,
    email,
    first_name,
    last_name
FROM users
WHERE email = 'customer@example.com';
```

The index might contain:

```text
email → tuple location
```

The database then follows that location to the heap.

Conceptually:

```mermaid
flowchart LR
    A[Query] --> B[Index]
    B --> C[Matching Index Entry]
    C --> D[Heap Tuple Location]
    D --> E[Table Page]
    E --> F[Visible Row]
```

If matching rows are spread across many table pages, the resulting access pattern can become expensive.

## Correlation

Physical correlation between index order and table order can influence the cost of an index scan.

Consider a table where rows are physically organized approximately in the same order as an indexed column:

```text
Index order
1 → Page 1
2 → Page 1
3 → Page 2
4 → Page 2
5 → Page 3
```

Accesses are relatively localized.

With poor correlation:

```text
1 → Page 100
2 → Page 4
3 → Page 900
4 → Page 27
5 → Page 701
```

The index may lead to many scattered heap accesses.

This can make a sequential scan more attractive for larger result sets.

## Range Scans

Index scans are useful for range predicates.

Example:

```sql
SELECT
    id,
    customer_id,
    total
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day';
```

With an index:

```sql
CREATE INDEX CONCURRENTLY idx_orders_created_at
ON orders (created_at);
```

PostgreSQL can locate the beginning of the relevant range and traverse matching index entries.

Conceptually:

```text
B-tree
        ┌───────────────┐
        │  root         │
        └───────┬───────┘
                ↓
       ┌─────────────────┐
       │ internal pages  │
       └────────┬────────┘
                ↓
       ┌─────────────────┐
       │ leaf entries    │
       └────────┬────────┘
                ↓
       created_at >= X
                ↓
       matching entries
```

Range scans are particularly useful when the requested range represents a relatively small portion of the table.

## Equality Lookups

Point lookups are among the strongest use cases for indexes.

Example:

```sql
SELECT
    id,
    account_id,
    balance
FROM accounts
WHERE account_id = 987654;
```

A unique index:

```sql
CREATE UNIQUE INDEX CONCURRENTLY idx_accounts_account_id
ON accounts (account_id);
```

can allow PostgreSQL to locate the row efficiently.

Primary keys and unique constraints commonly provide indexes that support this pattern.

## Ordering With Indexes

Indexes can also help satisfy `ORDER BY`.

Example:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

An index such as:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

can potentially support both:

```text
customer_id = 123
        ↓
ordered created_at entries
        ↓
first 50 rows
```

This can be much more efficient than:

```text
Filter many rows
      ↓
Sort many rows
      ↓
Return 50
```

The exact plan still depends on statistics, data distribution, and cost estimates.

## Composite Indexes

Composite indexes contain multiple columns.

Example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_status
ON orders (customer_id, status);
```

This can support queries such as:

```sql
SELECT
    id,
    total
FROM orders
WHERE customer_id = 123
  AND status = 'completed';
```

Column order matters.

For a B-tree index:

```text
(customer_id, status)
```

is generally strongest when the query constrains the leading column:

```sql
WHERE customer_id = 123
```

or:

```sql
WHERE customer_id = 123
  AND status = 'completed'
```

It is not equivalent to having:

```text
(status, customer_id)
```

The correct order depends on actual query patterns, selectivity, ordering requirements, and workload.

## Covering Indexes and Index-Only Scans

An index can sometimes contain all columns required by a query.

For example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_created
ON orders (customer_id, created_at DESC)
INCLUDE (total);
```

A query:

```sql
SELECT
    created_at,
    total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

may be able to use an **Index Only Scan**.

Conceptually:

```text
Query
  ↓
Index
  ├── customer_id
  ├── created_at
  └── total
  ↓
Required data available
  ↓
Reduced heap access
```

However, an index-only scan is not guaranteed to avoid heap access completely. PostgreSQL's visibility map determines whether heap visits are necessary to confirm tuple visibility.

Therefore:

```text
Covering index
    ≠
Guaranteed zero heap access
```

## Index Scan vs Index-Only Scan

| Feature | Index Scan | Index-Only Scan |
|---|---|---|
| Uses index | Yes | Yes |
| May access heap | Yes | Sometimes |
| Required columns in index | Not necessarily | Must be available from index |
| Depends on visibility map | Less directly | Yes |
| Can reduce heap I/O | Sometimes | Often |
| Storage overhead | Lower | Potentially higher with included columns |

Index-only scans are especially valuable for frequently executed read-heavy queries where the required projection is small and the relevant pages have favorable visibility-map coverage.

## Index Scans and `LIMIT`

Indexes can be particularly effective when combined with `LIMIT`.

Example:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 20;
```

With a suitable index:

```text
Index
  ↓
customer_id = 123
  ↓
created_at DESC
  ↓
first 20 entries
  ↓
stop
```

Without a suitable access path, PostgreSQL may need to:

```text
Find qualifying rows
        ↓
Process many rows
        ↓
Sort
        ↓
Return 20
```

This pattern is common in production APIs implementing:

- Recent orders.
- Latest events.
- User activity.
- Notifications.
- Message history.
- Time-ordered feeds.

## Index Scans and Pagination

Offset pagination can become increasingly expensive:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50 OFFSET 500000;
```

The database may still need to walk through a large number of index entries before returning the requested page.

Keyset pagination can be more efficient:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 123
  AND created_at < TIMESTAMP '2026-08-31 12:00:00'
ORDER BY created_at DESC
LIMIT 50;
```

With a suitable composite index, PostgreSQL can seek directly into the relevant portion of the index.

For production APIs, keyset pagination is often preferable for large datasets when the product requirements allow it.

## Index Conditions vs Filter Conditions

Execution plans may distinguish between:

```text
Index Cond
```

and:

```text
Filter
```

For example:

```text
Index Scan using idx_orders_customer
  Index Cond: (customer_id = 123)
  Filter: (status = 'completed')
```

This means the index is being used to locate rows for:

```sql
customer_id = 123
```

but PostgreSQL still has to apply:

```sql
status = 'completed'
```

to the rows it retrieves.

This distinction is important.

A query can technically use an index while still performing substantial filtering work.

## Why an Index May Not Be Used

Even when an appropriate-looking index exists, PostgreSQL may choose a different plan.

Common reasons include:

- Low predicate selectivity.
- Small table size.
- Large expected result set.
- Poor index/table correlation.
- Stale statistics.
- Data distribution.
- Query expression not matching the index.
- Cost model estimates.
- Parallel sequential scan being cheaper.
- Most relevant pages already being cached.
- Query projection requiring extensive heap access.

Example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_status
ON orders (status);
```

does not guarantee that:

```sql
SELECT *
FROM orders
WHERE status = 'completed';
```

will use the index.

If most rows are completed, PostgreSQL may correctly prefer a sequential scan.

## Statistics and Index Scans

The optimizer needs accurate estimates to select appropriate plans.

Inspect statistics:

```sql
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    most_common_vals,
    most_common_freqs
FROM pg_stats
WHERE tablename = 'orders'
  AND attname = 'status';
```

Refresh statistics when appropriate:

```sql
ANALYZE orders;
```

Large discrepancies between:

```text
estimated rows
```

and:

```text
actual rows
```

can indicate estimation problems.

Example:

```text
Index Scan
  estimated rows=10
  actual rows=2,000,000
```

The optimizer expected a highly selective lookup but the actual predicate matched a huge portion of the table.

This can produce a poor index-based plan.

## Inspecting an Index Scan

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    customer_id,
    total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

Look at:

| Metric | What it tells you |
|---|---|
| `Index Scan` | Access path chosen |
| `Index Cond` | Predicate used by the index |
| `Filter` | Predicate evaluated after row lookup |
| `actual time` | Observed execution timing |
| `rows` | Actual rows produced |
| `loops` | Number of executions |
| `Buffers` | Memory/storage page activity |
| `Rows Removed by Filter` | Rows retrieved but rejected |
| Estimated rows | Optimizer's cardinality estimate |

The plan should be interpreted as a whole.

## Practical PostgreSQL Example

Assume:

```sql
CREATE TABLE orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    total NUMERIC(12, 2) NOT NULL
);
```

Create an index supporting a common API query:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

Query:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

A suitable plan can conceptually become:

```text
Limit
└── Index Scan using idx_orders_customer_created on orders
      Index Cond: (customer_id = 123)
```

The database can traverse the index for one customer in the requested order and stop after enough rows are found.

This is a common and effective pattern for backend APIs.

## Django Integration

Django indexes should be designed around query patterns.

For example:

```python
from django.db import models


class Order(models.Model):
    customer_id = models.BigIntegerField()
    created_at = models.DateTimeField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(
                fields=["customer_id", "-created_at"],
                name="idx_orders_customer_created",
            ),
        ]
```

The corresponding ORM query:

```python
orders = (
    Order.objects
    .filter(customer_id=123)
    .order_by("-created_at")
    .values("id", "created_at", "total")[:50]
)
```

The ORM expresses the access requirement, but PostgreSQL still decides whether the index scan is the best plan.

Inspect it:

```python
print(
    orders.explain(
        analyze=True,
        buffers=True,
    )
)
```

For production systems, verify plans against realistic data volumes rather than relying on development databases containing a few hundred rows.

## Production Index Creation

Creating an index on a large production table requires operational planning.

For PostgreSQL, `CREATE INDEX CONCURRENTLY` can reduce blocking of ordinary writes compared with a regular index build.

Example:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

Important operational considerations:

- Concurrent index creation takes longer.
- It performs more work.
- It cannot run inside a transaction block.
- Failed concurrent builds may leave an invalid index that requires cleanup.
- Monitor database CPU, I/O, replication lag, and build progress.

Check index status:

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisvalid,
    indisready
FROM pg_index
WHERE indexrelid::regclass::text = 'idx_orders_customer_created';
```

For large production databases, schedule and observe index creation rather than treating it as a trivial schema change.

## Index Maintenance Costs

Every additional index has a write cost.

For:

```sql
INSERT INTO orders (...)
```

PostgreSQL must update the relevant table structure and each applicable index.

For updates affecting indexed columns, index entries may also need modification.

Therefore:

```text
More indexes
    ↓
More write work
    ↓
More storage
    ↓
More vacuum / maintenance work
    ↓
Potentially larger backups and replication traffic
```

Index design is therefore a workload optimization problem, not simply a read optimization problem.

## Index Bloat and Maintenance

Indexes can accumulate unused space as rows are updated and deleted.

Monitor index size:

```sql
SELECT
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY pg_relation_size(indexrelid) DESC;
```

Index maintenance strategies depend on the database workload and PostgreSQL version/configuration.

Avoid rebuilding indexes routinely without evidence.

Investigate:

- Excessive bloat.
- Write-heavy workloads.
- Poor fill-factor choices.
- Duplicate indexes.
- Unused indexes.
- Long-running transactions preventing cleanup.

## Monitoring Index Usage

PostgreSQL exposes index statistics through `pg_stat_user_indexes`.

Example:

```sql
SELECT
    relname AS table_name,
    indexrelname AS index_name,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

These metrics can help identify indexes that are frequently used.

However, an index with low usage is not automatically safe to remove.

It may support:

- Rare but critical operations.
- Unique constraints.
- Operational jobs.
- Disaster recovery workflows.
- Queries not represented in the current observation period.

Index removal should be based on workload evidence and dependency analysis.

## Common Index Scan Anti-Patterns

### Indexing Every Column

Creating an index on every commonly queried column can produce excessive write and storage overhead.

Index according to workload.

### Assuming More Indexes Always Improve Performance

Additional indexes can improve some reads while degrading writes.

### Ignoring Composite Index Order

An index on:

```text
(customer_id, created_at)
```

is not interchangeable with:

```text
(created_at, customer_id)
```

### Selecting Too Many Columns

A query such as:

```sql
SELECT *
FROM orders
WHERE customer_id = 123;
```

may require extensive heap access even if the predicate is indexed.

Retrieve only the columns required by the application.

### Using Offset Pagination at Extreme Depths

Large offsets can force the database to walk through many index entries before returning the desired page.

Consider keyset pagination.

### Ignoring `Filter`

Seeing:

```text
Index Scan
```

does not mean the query is fully optimized.

A large:

```text
Rows Removed by Filter
```

can indicate significant remaining work.

### Ignoring Cardinality Estimates

An index scan based on incorrect row estimates can be substantially slower than expected.

### Forcing an Index

Forcing or manipulating planner behavior to make PostgreSQL use an index can hide the real problem and make the workload fragile as data changes.

## Performance Investigation Checklist

When evaluating an index scan, ask:

```text
Is the query actually slow?
        ↓
How many rows are estimated?
        ↓
How many rows are actually returned?
        ↓
How many rows are read?
        ↓
How many are filtered?
        ↓
How much heap access occurs?
        ↓
What do BUFFERS show?
        ↓
Is the index selective?
        ↓
Is the index order appropriate?
        ↓
Would an index-only strategy help?
        ↓
What is the write/maintenance cost?
```

A good optimization process compares:

```text
Before
  ↓
EXPLAIN (ANALYZE, BUFFERS)
  ↓
Change
  ↓
EXPLAIN (ANALYZE, BUFFERS)
  ↓
Production-like benchmark
  ↓
Monitor workload impact
```

## Scalability Considerations

Index scans are particularly important for high-QPS OLTP workloads.

Suppose:

```text
API requests = 500 requests/second
Database lookups = 2 per request
```

This can produce:

```text
~1,000 database lookups/second
```

A selective indexed lookup can keep each operation small.

Without suitable access paths, repeated scans can cause:

```text
High CPU
   +
High I/O
   +
Connection contention
   ↓
Database saturation
   ↓
API latency
```

As traffic grows, query frequency matters as much as individual query latency.

A 2 ms query executed 10,000 times per second can be more operationally significant than a 500 ms query executed once per hour.

## Reliability Considerations

Indexes should support predictable access patterns without creating excessive write pressure.

For production systems:

- Monitor slow queries continuously.
- Monitor index growth.
- Review duplicate and unused indexes.
- Test migrations against production-sized datasets.
- Monitor replication lag during large index builds.
- Avoid adding indexes without workload evidence.
- Validate query plans after significant data-growth events.

An index that was optimal at 1 million rows may not remain optimal at 500 million rows.

## Cost Considerations

Indexes consume resources beyond query execution.

| Resource | Index impact |
|---|---|
| Storage | Index occupies disk space |
| Memory | Frequently accessed index pages may occupy cache |
| CPU | Index traversal and maintenance consume CPU |
| Writes | Inserts/updates/deletes may update indexes |
| Replication | Index changes contribute to replicated work |
| Backups | Larger database footprint |
| Maintenance | Vacuum and index-management overhead |

For cloud databases, unnecessary indexes can indirectly increase infrastructure requirements.

## Security and Resource Protection

Indexes are not a substitute for API-level resource controls.

A user-controlled endpoint should still enforce:

- Authorization.
- Pagination.
- Maximum page size.
- Query limits where appropriate.
- Rate limiting.
- Validated filters.

For example:

```text
Authenticated API request
        ↓
Authorization
        ↓
Validated query parameters
        ↓
Bounded result size
        ↓
Indexed database query
        ↓
Response
```

This provides defense in depth against expensive database operations.

## Interview Traps

| Question | Strong answer |
|---|---|
| Is an index scan always faster than a sequential scan? | No. It is generally advantageous for selective access, but sequential scans can be cheaper for large result sets or small tables. |
| Why can an index scan still be expensive? | It may require many heap fetches, random page accesses, or filtering of many candidate rows. |
| What is `Index Cond`? | A predicate PostgreSQL can use to navigate the index and identify candidate tuples. |
| What is the difference between `Index Cond` and `Filter`? | `Index Cond` restricts the index scan itself; `Filter` is applied after candidate rows are obtained. |
| What is an index-only scan? | A scan where the required query data can be obtained from the index, with heap visibility checks potentially avoided when the visibility map permits it. |
| Does a covering index guarantee an index-only scan? | No. The optimizer still chooses the plan, and heap visibility can still require table access. |
| Why does composite index column order matter? | B-tree indexes are ordered lexicographically, so leading columns strongly influence which predicates and ordering operations can use the index efficiently. |
| Why might PostgreSQL ignore an index? | Low selectivity, large result sets, table size, cache state, cost estimates, statistics, correlation, or an unsuitable predicate/index relationship. |
| What is a good index candidate? | A frequently executed query with selective predicates, meaningful latency/resource cost, and a workload where reduced row/page access justifies index maintenance. |
| Why can too many indexes hurt performance? | Every relevant write must maintain those indexes, increasing CPU, storage, maintenance, and replication overhead. |
| How do you validate an index optimization? | Compare actual execution plans and buffers before and after the change, then validate under realistic data and concurrency. |

## Key Takeaways

- **Index scans efficiently locate selective rows, but they are not universally faster than sequential scans.**
- **Analyze `Index Cond`, `Filter`, actual rows, heap access, buffers, and cardinality estimates rather than judging an index scan by its presence alone.**
- **Composite index order, selectivity, ordering requirements, and pagination strategy determine whether an index can substantially reduce query work.**
- **Index-only scans can reduce heap access, but they depend on the available index data, visibility information, and optimizer decisions.**
- **Production index design must balance read performance against storage, write amplification, maintenance, replication, and operational cost.**