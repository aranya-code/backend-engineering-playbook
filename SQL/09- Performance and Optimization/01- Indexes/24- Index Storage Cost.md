# 24- Index Storage Cost

## Overview

An index is a persistent data structure that consumes storage in addition to the table it indexes. Index storage is easy to overlook because the performance benefit is visible in query latency, while the cost appears across disk capacity, memory pressure, backups, replication, maintenance, and write amplification.

For production systems, index design is therefore a resource-allocation problem:

```text
                    Index
                      │
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
     Storage        Memory       Write Cost
        │             │             │
        ↓             ↓             ↓
   Disk capacity   Cache usage   INSERT/UPDATE/DELETE
        │             │             │
        └─────────────┼─────────────┘
                      ↓
               Operational Cost
```

A table with several large indexes can consume substantially more storage than the table itself. This affects database sizing, cloud costs, backups, restores, replication, index creation, and overall system performance.

The goal is not to minimize index storage at all costs. The goal is to maintain **the smallest set of indexes that efficiently supports the production workload**.

## What Determines Index Size

Index size depends on several factors:

- Number of indexed rows.
- Number of indexed columns.
- Data types and their physical representation.
- Index implementation.
- Index tuple overhead.
- Page structure.
- Fill factor.
- Included columns.
- Duplicate or low-cardinality values.
- Table growth.
- Bloat and maintenance behavior.

Conceptually:

```text
Index Size
≈
Number of index entries
×
Average entry size
+
Page / tree overhead
+
Free space / fragmentation
```

This is an approximation rather than an exact storage formula.

For a B-tree index, the database stores keys and references needed to locate table rows, along with internal tree pages and page-level metadata.

## Why Index Storage Matters

Index storage affects more than disk capacity.

| Area | Impact of large index footprint |
|---|---|
| Disk | More database storage required |
| Memory | More pages competing for cache |
| Reads | Large indexes may require more I/O |
| Writes | More index structures require maintenance |
| Backups | Larger backup footprint |
| Restore | More data to restore and potentially rebuild |
| Replication | More write-related work can increase pressure |
| Index builds | More disk and I/O required |
| Cloud cost | Larger volumes and snapshots cost more |
| Operations | More structures to monitor and maintain |

A senior engineer considers all of these effects before adding a large index.

## Measuring Index Storage in PostgreSQL

PostgreSQL exposes relation sizes through functions such as `pg_relation_size()`.

To inspect index sizes for a table:

```sql
SELECT
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY pg_relation_size(indexrelid) DESC;
```

To inspect all indexes for a table:

```sql
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE tablename = 'orders'
ORDER BY pg_relation_size(indexname::regclass) DESC;
```

For a complete table-level picture, compare the heap and indexes:

```sql
SELECT
    pg_size_pretty(pg_table_size('orders')) AS table_size,
    pg_size_pretty(pg_indexes_size('orders')) AS indexes_size,
    pg_size_pretty(pg_total_relation_size('orders')) AS total_size;
```

This distinction is useful:

```text
pg_table_size
    ↓
Table data + associated storage

pg_indexes_size
    ↓
All indexes on the table

pg_total_relation_size
    ↓
Table + indexes + associated auxiliary storage
```

## Index Size vs Table Size

Consider:

```text
orders table       80 GB
indexes            55 GB
total              135 GB
```

The indexes represent a substantial portion of the database footprint.

That may be completely justified if the application has many critical read paths.

But if:

```text
orders table       80 GB
indexes            55 GB
only 8 GB of index data is actively useful
```

then the database may be carrying significant unnecessary storage and write overhead.

Storage percentage is therefore a useful signal:

```text
Index Ratio = Index Storage / Table Storage
```

A high ratio is not automatically bad. It should trigger investigation rather than an automatic cleanup.

## Why Wider Indexes Cost More

Consider:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);
```

versus:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (
    customer_id,
    status,
    created_at
);
```

The composite index generally requires more storage per index entry because it contains more key data.

A wider index can improve a family of queries, but it also increases:

- Storage.
- Memory pressure.
- Index build time.
- Write maintenance.
- Backup size.

This is why index design should balance query coverage against physical footprint.

## Included Columns Increase Storage

Covering indexes can add non-key columns to an index.

For PostgreSQL:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC)
INCLUDE (total, currency);
```

The key columns determine the index ordering and search structure. Included columns provide additional payload that can allow suitable queries to avoid heap access.

This can be an excellent optimization for a hot read path:

```sql
SELECT customer_id, created_at, total, currency
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

However, every included column increases the physical size of the index.

Use covering indexes when the reduction in table access is worth the additional storage and write cost.

## Composite Index Storage

Suppose a table contains:

```text
100 million rows
```

and has:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);

CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at);
```

The second index may be significantly larger because each index entry carries more key information.

However, it may replace several narrower indexes if it efficiently supports the actual query workload.

The right question is therefore not:

> "Which index is smallest?"

It is:

> "Which index set provides the required access paths with the lowest total cost?"

## Redundant Indexes and Storage Waste

Consider:

```text
(customer_id)
(customer_id, created_at)
(customer_id, status, created_at)
```

These indexes overlap.

The exact usefulness depends on the database engine and workload, but maintaining all three may be unnecessary.

Redundant indexes consume:

- Disk space.
- Cache capacity.
- Write bandwidth.
- Maintenance resources.

They also increase schema complexity.

Before adding a new index, inspect the existing index set.

```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'orders'
ORDER BY indexname;
```

Do not assume two indexes are redundant solely because one has a prefix of another. Query patterns, ordering, partial predicates, uniqueness, included columns, and optimizer behavior all matter.

## Storage Cost of Partial Indexes

Partial indexes can significantly reduce storage when only a subset of rows is operationally relevant.

Suppose:

```text
jobs
100 million rows

pending:
2 million

completed:
98 million
```

A general index:

```sql
CREATE INDEX idx_jobs_status_created
ON jobs (status, created_at);
```

indexes all rows.

A partial index:

```sql
CREATE INDEX idx_jobs_pending_created
ON jobs (created_at)
WHERE status = 'pending';
```

contains only rows satisfying the predicate.

Conceptually:

```text
Full index
100 million entries
████████████████████████████

Partial index
2 million entries
██
```

This can reduce both storage and write-maintenance cost for workloads focused on a small active subset.

## Storage Cost of Low-Cardinality Indexes

A common misconception is:

> "Low cardinality means the index is always small."

That is not necessarily true.

An index on:

```sql
status
```

still needs an index entry for each indexed row in a standard full-table index.

If the table contains 500 million rows, an index on a boolean or status column can still be large.

The issue with low cardinality is primarily **whether the index provides enough filtering benefit**, not simply how much disk space it consumes.

Partial indexes can sometimes make such workloads more attractive by indexing only the subset that matters.

## Indexes and Memory Pressure

Database memory is finite.

Suppose:

```text
Database cache:
32 GB

Table:
100 GB

Indexes:
150 GB
```

The entire working set cannot remain in memory.

Large indexes compete for cache space with:

- Table pages.
- Other indexes.
- Frequently accessed data.
- Internal database structures.

A smaller, frequently used index may have a much better cache profile than a very large index.

This creates an important production consideration:

> Index size matters even when disk capacity is not a problem.

An index can be affordable on disk but expensive in terms of cache efficiency.

## Indexes and Write Amplification

Every applicable write can require index maintenance.

Consider:

```text
1 table
+
6 indexes
```

An insert may conceptually require:

```text
Table write
+ Index A
+ Index B
+ Index C
+ Index D
+ Index E
+ Index F
```

The larger the index structures, the more pages may need to be accessed and modified.

This matters particularly for:

- High-throughput APIs.
- Kafka consumers.
- Celery workers.
- Event ingestion.
- Telemetry systems.
- Append-heavy workloads.

Storage cost and write cost are therefore related.

## Indexes and Table Updates

The cost of an index is especially relevant when indexed columns change frequently.

For example:

```sql
CREATE INDEX idx_users_status
ON users (status);
```

If an application constantly changes:

```sql
UPDATE users
SET status = $2
WHERE id = $1;
```

the index must track those changes.

By contrast:

```sql
UPDATE users
SET last_login_at = NOW()
WHERE id = $1;
```

does not directly require maintenance of the `status` index because the indexed value did not change.

This distinction is important when designing indexes on high-write tables.

## PostgreSQL HOT Updates

PostgreSQL can sometimes use **HOT (Heap-Only Tuple) updates** when an update does not modify indexed columns and the new tuple can remain on the same heap page.

This can avoid creating new index entries for that update.

Therefore:

```text
Frequently updated column
        │
        └── indexed by many indexes
                    ↓
             More index maintenance
                    ↓
       Fewer opportunities for HOT updates
```

This is one reason to avoid indexing frequently updated columns without a demonstrated read-performance benefit.

## Index Bloat

Index storage can also grow because of dead tuples, page utilization, and workload-specific fragmentation.

PostgreSQL's MVCC model means updates and deletes can leave obsolete row versions that require vacuuming and subsequent cleanup.

An index can therefore have a physical footprint that is larger than the amount of currently useful logical data suggests.

Bloat can result in:

- Increased disk consumption.
- More pages to scan.
- Reduced cache efficiency.
- Longer maintenance operations.

Index bloat should be measured rather than assumed.

When investigating suspected bloat, use PostgreSQL-specific monitoring and established operational tooling rather than manually rebuilding indexes without understanding the workload.

## Fill Factor and Storage

PostgreSQL indexes can use a fill factor that controls how full index pages are initially packed.

For example:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id)
WITH (fillfactor = 90);
```

Leaving free space can sometimes reduce page splits for workloads with significant index-page modification.

However, lower fill factors can increase initial storage requirements because more space is intentionally left available.

The trade-off is:

```text
Lower fillfactor
    ↓
More free space
    ↓
Potentially fewer page splits
    ↓
Potentially more initial storage
```

Use non-default fill factors only when workload characteristics justify them.

## Index Size and Page Splits

B-tree indexes grow through page allocation and page splitting as new entries are inserted into appropriate locations.

Randomly distributed keys can produce different page-access behavior from monotonically increasing keys.

For example:

```text
UUID/random key
    ↓
Inserts distributed throughout index
    ↓
Potential page splits across the tree
```

versus:

```text
Increasing key
    ↓
Inserts concentrated near the right side
    ↓
Different page-growth pattern
```

The exact behavior depends on the database and index implementation, but key distribution is an important factor in index maintenance and storage behavior.

## Measuring Storage Growth Over Time

A one-time size measurement is not enough for production systems.

Track index size periodically:

```sql
SELECT
    now() AS measured_at,
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    pg_relation_size(indexrelid) AS bytes,
    pg_size_pretty(pg_relation_size(indexrelid)) AS human_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

Store the results in your monitoring system or database inventory if long-term capacity analysis is required.

This allows teams to detect:

```text
Index size
   │
   ├── Stable
   ├── Growing with table
   ├── Growing faster than table
   └── Unexpected growth
```

Unexpected growth should trigger investigation.

## Production Capacity Planning

Database capacity planning should account for indexes explicitly.

A simplified model is:

```text
Required database storage
=
Table data
+
Indexes
+
WAL / transaction-log requirements
+
Temporary working space
+
Maintenance overhead
+
Growth headroom
```

For production systems, also consider:

- Backups.
- Snapshots.
- Replication.
- Read replicas.
- Index rebuild space.
- Major migrations.
- Data retention changes.
- Traffic growth.

A database volume that is sized only for current table data can become operationally constrained as indexes grow.

## Cloud Cost Implications

On AWS and similar cloud platforms, additional database storage has a direct infrastructure cost.

But storage capacity is not the only cost.

Larger indexes can indirectly increase:

- I/O requirements.
- Provisioned IOPS requirements.
- Backup storage.
- Snapshot size.
- Replica resources.
- Database instance memory requirements.

For managed PostgreSQL deployments, an apparently small schema change can therefore have a broader infrastructure impact.

A useful review question is:

```text
"If this table grows 10×, what happens to its indexes?"
```

## Index Storage and Backups

Indexes are part of the physical database footprint and influence backup and restore characteristics.

Larger databases generally mean:

- More storage to back up.
- More data to transfer.
- More capacity required for snapshots.
- Potentially longer restore operations.

Logical backups may behave differently depending on what is being backed up and restored, but index recreation can still become a significant part of recovery workflows.

For disaster recovery planning, measure actual backup and restore times rather than estimating only from table size.

## Index Creation and Temporary Storage

Creating a large index can require significant temporary resources.

For a production PostgreSQL deployment:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

`CONCURRENTLY` can reduce blocking of normal table operations compared with a standard index build, but it does not make the operation free.

Plan for:

- Additional disk consumption.
- CPU.
- I/O.
- Longer migration duration.
- Replica impact.
- Failed or invalid index cleanup.
- Monitoring during the operation.

Never assume that because an index is eventually only 20 GB, creating it requires only 20 GB of available operational headroom.

## Storage-Aware Index Design

A production index should satisfy three requirements:

```text
Useful access path
        +
Acceptable maintenance cost
        +
Acceptable physical footprint
```

A practical decision matrix:

| Candidate index | Read benefit | Storage cost | Write cost | Typical decision |
|---|---:|---:|---:|---|
| Narrow selective index | High | Low | Low | Strong candidate |
| Wide composite index | High | Medium/high | Medium/high | Validate workload |
| Covering index | Very high for target query | High | Higher | Use for hot queries |
| Low-selectivity full index | Low/variable | Medium | Medium | Usually investigate |
| Partial index | High for matching subset | Low/medium | Low/medium | Strong candidate when applicable |
| Redundant index | Low | High | High | Remove/reconsider |
| Rarely used large index | Low | High | High | Investigate before retaining |

## Example: Orders Table

Consider:

```text
orders
├── 500 million rows
├── 180 GB table
├── 40 GB primary key index
├── 55 GB customer index
├── 65 GB customer/status/created index
├── 45 GB covering index
└── 30 GB reporting index
```

The index footprint is:

```text
40 + 55 + 65 + 45 + 30 = 235 GB
```

The database now has:

```text
Table:    180 GB
Indexes:  235 GB
Total:    ~415 GB
```

This does not automatically indicate a problem.

The engineering investigation should ask:

- Which indexes support critical API queries?
- Which indexes are redundant?
- Which indexes are rarely scanned?
- Can a partial index replace a full index?
- Can overlapping indexes be consolidated?
- Is the covering index materially improving latency?
- Are indexes consuming too much cache?
- Is write throughput affected?
- Is storage growth sustainable?

## Index Inventory

A useful production inventory includes:

| Attribute | Why it matters |
|---|---|
| Index name | Identification |
| Table | Ownership/context |
| Definition | Understanding access path |
| Size | Capacity planning |
| Scan count | Usage signal |
| Indexed columns | Write impact |
| Included columns | Width |
| Predicate | Partial-index scope |
| Unique constraint | Integrity requirement |
| Creation date | Historical context |
| Query dependency | Business importance |

For large databases, maintain this inventory as part of regular database operations.

## When to Remove an Index

Dropping an index can reduce:

- Storage.
- Write overhead.
- Cache pressure.
- Maintenance complexity.

But removal should be evidence-driven.

Before dropping:

1. Identify all queries that might depend on it.
2. Check index usage over a representative observation period.
3. Check whether it enforces uniqueness or another constraint.
4. Check whether usage is seasonal or operationally rare.
5. Compare it with other indexes.
6. Validate query plans after removal in a staging or representative environment.
7. Deploy the change safely.
8. Monitor production after removal.

For critical systems, avoid making decisions from a very short usage window.

## Common Mistakes and Pitfalls

### Assuming Indexes Are "Free"

They are not.

Every index consumes storage and may increase write and maintenance costs.

### Looking Only at Table Size

A table might be:

```text
100 GB
```

while its indexes total:

```text
250 GB
```

Always inspect the complete physical footprint.

### Adding Columns to an Index Without Considering Width

A wide composite or covering index can become dramatically larger than the original narrow index.

Add columns based on query requirements, not convenience.

### Creating Multiple Overlapping Indexes

This can create large amounts of duplicated storage.

Review existing indexes before adding new ones.

### Assuming Low Cardinality Means Low Storage

An index on a boolean or status column can still contain an entry for every row.

Low cardinality primarily affects filtering effectiveness, not necessarily physical index size.

### Ignoring Growth

An index that is acceptable at:

```text
10 million rows
```

may become operationally significant at:

```text
1 billion rows
```

Always consider expected data growth.

### Ignoring Cache Pressure

An index can fit comfortably on disk but still consume valuable database cache capacity.

### Dropping Indexes Based Only on `idx_scan`

A low scan count does not prove that an index is useless.

It may support:

- Constraints.
- Rare but critical queries.
- Operational workflows.
- Compliance requirements.

### Rebuilding Indexes Without Capacity Planning

Large index operations can require substantial temporary disk and I/O resources.

Treat them as production operations.

## Monitoring Checklist

For large production databases, monitor:

- Total database size.
- Table size.
- Total index size.
- Individual index size.
- Index growth rate.
- Index scan frequency.
- Database cache behavior.
- CPU utilization.
- Storage I/O.
- WAL generation.
- Replication lag.
- Autovacuum activity.
- Backup size.
- Backup duration.
- Restore duration.
- Free disk capacity.

Useful PostgreSQL queries include:

```sql
-- Largest indexes
SELECT
    schemaname,
    relname AS table_name,
    indexrelname AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC
LIMIT 20;
```

```sql
-- Total index footprint by table
SELECT
    schemaname,
    relname AS table_name,
    pg_size_pretty(pg_indexes_size(relid)) AS indexes_size
FROM pg_stat_user_tables
ORDER BY pg_indexes_size(relid) DESC;
```

## Operational Best Practices

- Measure index size before and after major schema changes.
- Review existing indexes before creating new ones.
- Prefer narrow indexes unless additional columns provide measurable value.
- Use partial indexes when only a small subset of rows is queried.
- Use covering indexes selectively for proven hot paths.
- Monitor index growth alongside table growth.
- Include index storage in capacity planning.
- Account for backup, snapshot, and restore implications.
- Consider memory/cache pressure, not only disk usage.
- Evaluate write amplification for high-throughput tables.
- Use production query plans and workload metrics to justify index changes.
- Remove redundant indexes carefully and only after validating dependencies.
- Leave sufficient storage headroom for index creation and maintenance.
- Treat index changes as database migrations with operational risk.

## Interview Traps

### "Does an Index Store a Copy of the Entire Table?"

Usually no.

A typical B-tree index stores indexed key values and references needed to locate the corresponding table rows, plus structural metadata.

Covering indexes can store additional payload columns, but that still does not necessarily mean the entire row is duplicated.

### "Does an Index on a Boolean Column Take Almost No Space?"

No.

A standard index still generally contains an entry for each indexed row.

The low number of distinct values affects selectivity, not necessarily index entry count.

### "Can an Index Be Larger Than the Table?"

Yes.

Multiple indexes can collectively be larger than the table, and wide indexes or indexes with included columns can individually become substantial.

### "Why Does a Covering Index Increase Storage?"

Because included columns add payload to index entries.

The trade-off is potentially fewer table accesses for suitable queries.

### "Why Does Index Storage Matter if Disk Is Cheap?"

Because the cost is not limited to disk:

```text
Storage
+
Memory/cache
+
Write I/O
+
Maintenance
+
Backup
+
Replication
+
Index build resources
```

### "Should Large Indexes Always Be Removed?"

No.

A large index can be completely justified if it supports high-value production workloads.

The correct question is whether its **performance benefit justifies its total operational cost**.

## Key Takeaways

- **Indexes are a significant part of database storage and must be included in capacity, backup, restore, and cloud-cost planning.**
- **Index width, row count, included columns, overlap, and partial predicates directly influence physical index size.**
- **Large indexes also consume cache and increase maintenance work, so storage cost is closely connected to read and write performance.**
- **Measure index size and usage together; a large index is not necessarily wasteful, while a small unused index may still be unnecessary.**
- **Production index design should favor the smallest set of workload-driven indexes that provides the required query performance at an acceptable operational cost.**