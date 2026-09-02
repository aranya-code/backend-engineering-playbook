# 07- Clustered Indexes

## Overview

A **clustered index** determines the physical or storage order of table rows according to an index key, or closely couples the table's storage structure to that key.

The important detail is that **"clustered index" does not mean exactly the same thing across database engines**. In some systems, the clustered index is the table's primary storage structure. In others, a table can be physically organized according to an index but the relationship is maintained differently. PostgreSQL does not have a permanently maintained clustered-index structure in the SQL Server sense.

A clustered organization can make range-oriented access efficient because rows with nearby index keys are physically close:

```text
Cluster key: order_id

Index / storage order
      ↓
1001 → row
1002 → row
1003 → row
1004 → row
1005 → row
      ↓
Nearby keys → nearby storage
```

This contrasts with a conventional secondary index where the index points to rows that may be distributed throughout the table.

For backend engineers, clustered indexing matters because it affects:

- Range-query performance
- Sequential access
- I/O locality
- Primary-key design
- Insert behavior
- Page splits
- Storage amplification
- Hotspots
- Pagination performance
- Table maintenance

## Clustered vs Non-Clustered Indexes

The core distinction is how the index relates to the table's row storage.

### Clustered Index

Conceptually:

```text
Clustered index
      ↓
Table data organized by index key
```

The leaf level of the clustered structure effectively contains the table's rows.

### Non-Clustered Index

Conceptually:

```text
Secondary index
      ↓
Key + row locator
      ↓
Table row
```

The table has an independent physical/storage structure, and the secondary index points to it.

| Property | Clustered Index | Non-Clustered / Secondary Index |
|---|---|---|
| Determines table storage organization | Yes, in systems with true clustered indexes | No |
| Typical number per table | Usually one | Multiple |
| Excellent for range access | Yes | Depends on locality |
| Leaf level contains table data | Commonly yes | Usually row references / indexed data |
| Multiple indexes possible | Usually only one clustered organization | Yes |
| Insert-order implications | Significant | Usually lower |
| Physical locality | Strong | Not guaranteed |
| Storage implications | Fundamental table organization | Additional structure |
| PostgreSQL equivalent | `CLUSTER` provides one-time physical reordering | Regular indexes |

## Why Clustered Indexes Exist

A database often needs to answer queries that access many nearby rows.

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = 42
ORDER BY created_at;
```

If matching rows are physically scattered:

```text
Page 1  → customer 42
Page 8  → customer 42
Page 19 → customer 42
Page 44 → customer 42
Page 72 → customer 42
```

the database may need many random page accesses.

With suitable physical locality:

```text
Page 20 → customer 42
Page 21 → customer 42
Page 22 → customer 42
Page 23 → customer 42
```

the same workload can require fewer I/O operations.

The fundamental goal is therefore **data locality**.

## Physical Locality

A clustered organization is valuable because databases operate on pages rather than individual application-level objects.

Conceptually:

```text
Application query
       ↓
Index lookup
       ↓
Relevant page range
       ↓
Rows located close together
       ↓
Fewer page accesses
```

This is especially useful for:

- Range queries
- Time-series access
- Sequential scans over related rows
- Queries returning many adjacent records

The performance benefit comes primarily from reducing expensive page access and improving cache behavior, not because a clustered index magically makes B-tree traversal faster.

## How a Clustered B-Tree Works

In systems where the clustered index is the table's storage structure, a B-tree can conceptually look like:

```text
                    Root
                  /      \
             Branch       Branch
             /   \         /   \
          Leaf   Leaf    Leaf   Leaf
            ↓      ↓       ↓      ↓
          Rows   Rows    Rows   Rows
```

The leaf pages contain the table rows.

For a range:

```sql
WHERE id BETWEEN 1000 AND 2000
```

the database can:

1. Navigate the B-tree to the first matching key.
2. Walk through adjacent leaf pages.
3. Read rows in key order.
4. Stop after the upper boundary.

This is particularly efficient because the index and row storage are integrated.

## Clustered Index and Range Queries

Consider:

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01';
```

If the table is organized by `created_at`, the relevant rows may be physically close.

Conceptually:

```text
January ── February ── March ── ... ── July ── August ── September
                                           ↑
                                      target range
```

The database can traverse directly to the August portion and process a relatively contiguous region.

This is one reason clustered storage can be highly effective for workloads dominated by range queries.

## Clustered Index and Sequential Access

A clustered organization can also help when an application reads many rows in index order:

```sql
SELECT *
FROM events
ORDER BY created_at
LIMIT 10000;
```

If storage follows `created_at`, the database can read rows in an order that closely matches the requested access pattern.

This can reduce random I/O and improve cache locality.

However, a query still needs to be evaluated against the database's actual execution plan. Clustering does not guarantee that an index will always be selected.

## Clustered Index and Primary Keys

Many database systems commonly use the primary key as the clustered index.

For example:

```sql
CREATE TABLE users (
    id bigint PRIMARY KEY,
    email text NOT NULL,
    created_at timestamptz NOT NULL
);
```

In a database where the primary key is clustered by default, rows may be stored according to:

```text
id
↓
1001
1002
1003
1004
1005
```

This can make:

```sql
SELECT *
FROM users
WHERE id BETWEEN 1000 AND 2000;
```

very efficient.

But **primary key does not universally mean clustered index**.

This is an important database-engine interview distinction.

## SQL Server Perspective

In SQL Server, a clustered index determines the logical order of the table's data pages.

For example:

```sql
CREATE CLUSTERED INDEX ix_orders_id
ON orders (id);
```

The clustered index contains the table's data at its leaf level.

Because there can only be one clustered organization per table, choosing its key is an important schema-design decision.

A table can also have a nonclustered primary key:

```sql
CREATE TABLE orders (
    id bigint NOT NULL,
    customer_id bigint NOT NULL,
    created_at datetime2 NOT NULL,
    CONSTRAINT pk_orders PRIMARY KEY NONCLUSTERED (id)
);
```

The database can therefore have:

```text
Primary key
   ↓
Nonclustered index

Clustered index
   ↓
Table storage
```

The primary key and clustered index are related concepts but are not synonymous.

## PostgreSQL Perspective

PostgreSQL does **not** implement a continuously maintained clustered index in the SQL Server sense.

A PostgreSQL table is a heap, and ordinary B-tree indexes are separate structures:

```text
Table heap
   ↑
   │
Index ────────────────→ tuple locations
```

PostgreSQL provides the `CLUSTER` command, which physically rewrites a table according to an existing index:

```sql
CLUSTER orders USING idx_orders_created_at;
```

This changes the physical row ordering based on the index at that point in time.

The critical limitation is that PostgreSQL does not continuously preserve that ordering as rows are inserted and updated.

## PostgreSQL `CLUSTER`

Suppose:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

Then:

```sql
CLUSTER orders USING idx_orders_created_at;
```

conceptually performs:

```text
Existing heap
    ↓
Read rows using index order
    ↓
Rewrite table
    ↓
Rows become physically ordered
```

After clustering:

```text
Heap pages
┌───────────────┐
│ older orders  │
├───────────────┤
│ older orders  │
├───────────────┤
│ recent orders │
├───────────────┤
│ recent orders │
└───────────────┘
```

Over time, normal writes can reduce this correlation.

## PostgreSQL `CLUSTER` Is Not Permanent

This is one of the most important PostgreSQL details.

After:

```sql
CLUSTER orders USING idx_orders_created_at;
```

future inserts do not guarantee that rows remain physically ordered by `created_at`.

For example:

```text
Initial state:

Page 1 → January
Page 2 → February
Page 3 → March


After months of writes:

Page 1 → January + random updates
Page 2 → February
Page 3 → March
Page 4 → new rows
Page 5 → updated rows
```

Physical correlation can deteriorate.

If physical ordering is important, the table may need to be reclustered periodically, or a different storage strategy may be more appropriate.

## PostgreSQL Correlation

PostgreSQL statistics include information about how strongly the physical row order correlates with an index order.

A high correlation means:

```text
Index order ≈ physical heap order
```

A low correlation means:

```text
Index order ≠ physical heap order
```

This influences planner cost estimates for index scans.

You can inspect statistics through PostgreSQL system views such as:

```sql
SELECT
    schemaname,
    tablename,
    attname,
    correlation
FROM pg_stats
WHERE tablename = 'orders';
```

High correlation can make index-based range access more attractive because fetching adjacent index entries is more likely to touch nearby heap pages.

## Clustered Index vs Heap + Secondary Index

Consider two simplified designs.

### Clustered Storage

```text
B-tree
  ↓
Rows
┌─────────┬─────────┬─────────┐
│ Page 1  │ Page 2  │ Page 3  │
│ rows    │ rows    │ rows    │
└─────────┴─────────┴─────────┘
```

### Heap + Secondary Index

```text
Index
  ↓
Row locations
  ↓
Heap
┌─────────┬─────────┬─────────┐
│ Page 1  │ Page 2  │ Page 3  │
│ mixed   │ mixed   │ mixed   │
└─────────┴─────────┴─────────┘
```

For a range returning many rows, clustered storage can provide stronger locality.

For highly selective point lookups, the difference may be much smaller.

## Choosing a Clustered Key

Choosing the clustered key is a workload-design decision.

A good candidate often has:

- Frequent range filtering
- Frequent ordering requirements
- Strong locality requirements
- Stable values
- Appropriate cardinality
- Predictable insertion behavior

Common candidates include:

```text
created_at
tenant_id + created_at
order_id
event_time
```

depending on the database and workload.

## Sequential Keys

A monotonically increasing key such as:

```text
1001
1002
1003
1004
...
```

has a useful insertion property.

New rows generally arrive near the end of the clustered structure:

```text
Existing pages
[1001 ... 5000]

New row
5001
  ↓
append near end
```

This can reduce page splitting compared with random insertion.

## Random UUIDs and Clustered Storage

Random UUIDs can be problematic as clustered keys in systems where the clustered index is the table's physical organization.

Suppose keys arrive randomly:

```text
7f...
12...
a3...
4b...
d1...
```

New records may need to be inserted throughout the B-tree.

Conceptually:

```text
Existing:

[1000–1999]
[2000–2999]
[3000–3999]


Random insert
2500
  ↓
middle page
  ↓
possible page split
```

Repeated random inserts can increase:

- Page splits
- Fragmentation
- Write amplification
- Storage overhead
- Cache churn

This does **not** mean UUIDs are inherently bad. The impact depends on the database engine, UUID generation strategy, workload, and index implementation.

## Time-Ordered Identifiers

For distributed systems, time-ordered identifiers can offer better locality than completely random identifiers.

Examples include:

- UUIDv7
- ULID
- Other application-generated sortable identifiers

For a clustered key, the important property is that new values have a useful ordering relationship.

Conceptually:

```text
Old event
2026-08-31T10:00 → ID A

New event
2026-08-31T10:01 → ID B

Later event
2026-08-31T10:02 → ID C
```

This can reduce the random insertion behavior associated with fully random identifiers.

The exact suitability depends on database support and application requirements.

## Hotspots

Sequential clustered keys have a trade-off.

If all writes target the rightmost portion of a B-tree:

```text
                 New writes
                     ↓
[old] [old] [old] [HOT]
                       ↑
                  write hotspot
```

high write concurrency can concentrate activity around the same pages or index region.

Database engines use techniques such as page latching, buffering, and internal concurrency control to manage this, but extremely high write rates can still make the insertion area a bottleneck.

A good senior-level design considers both:

```text
Sequential key
    ↓
Good locality
    +
Predictable inserts
    ↓
Potential write concentration
```

## Composite Clustered Keys

For multitenant systems, a clustered key such as:

```text
(tenant_id, created_at)
```

can provide useful locality:

```text
Tenant A
  ├── 10:00
  ├── 10:05
  └── 10:10

Tenant B
  ├── 10:01
  ├── 10:06
  └── 10:11
```

Queries such as:

```sql
WHERE tenant_id = $1
  AND created_at >= $2
  AND created_at < $3
```

can align naturally with this access pattern.

The exact column order matters.

A key:

```text
(tenant_id, created_at)
```

has different behavior from:

```text
(created_at, tenant_id)
```

because the leading key determines how the structure is ordered and navigated.

## Clustered Index and Pagination

Clustered ordering can be especially useful for **keyset pagination**.

Instead of:

```sql
SELECT *
FROM orders
ORDER BY id
LIMIT 50 OFFSET 100000;
```

use:

```sql
SELECT *
FROM orders
WHERE id > $1
ORDER BY id
LIMIT 50;
```

where `$1` is the last ID from the previous page.

If the clustered key matches `id`, the database can efficiently continue from the previous location.

Conceptually:

```text
Page 1
1001 ... 1050
           ↓
       last_id=1050

Page 2
1051 ... 1100
```

This avoids scanning and discarding a large number of earlier rows.

Keyset pagination is valuable regardless of clustering, but physical locality can make large sequential ranges particularly efficient.

## Clustered Index and Covering Indexes

A nonclustered index may need to perform an additional lookup to retrieve columns not contained in the index.

Conceptually:

```text
Secondary index
      ↓
Row locator
      ↓
Clustered table
      ↓
Full row
```

This additional lookup is sometimes called a **key lookup** or **bookmark lookup**, depending on the database engine.

If the query returns many rows, repeated lookups can become expensive.

A covering index can reduce this:

```text
Index
 ├── filter columns
 ├── ordering columns
 └── required output columns
```

The precise implementation differs between databases.

The important principle is that clustered storage affects the cost of secondary-index lookups because secondary indexes may ultimately need to locate rows through the clustered structure.

## Read Performance Trade-Offs

Clustered indexes can provide:

- Better range locality
- Efficient ordered access
- Reduced random I/O for suitable queries
- Efficient retrieval of many neighboring rows
- Good performance for keyset-style access patterns

But they can also introduce:

- More expensive random inserts
- Page splits
- Fragmentation
- Write hotspots
- A single physical ordering choice
- Reorganization or maintenance costs

The key is to optimize the **dominant access pattern**, not simply to maximize index count.

## Production Example

Consider an order-processing system:

```sql
CREATE TABLE orders (
    id bigint NOT NULL,
    tenant_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    status varchar(32) NOT NULL,
    created_at timestamp NOT NULL,
    total_amount numeric(12, 2) NOT NULL
);
```

Suppose the dominant query is:

```sql
SELECT id, status, total_amount, created_at
FROM orders
WHERE tenant_id = $1
  AND created_at >= $2
  AND created_at < $3
ORDER BY created_at, id
LIMIT 100;
```

The important access pattern is:

```text
tenant
  +
time range
  +
ordered retrieval
```

A suitable clustered organization in a database that supports it might use:

```text
(tenant_id, created_at, id)
```

This can provide strong locality for a tenant's time-based order history.

But the choice should be validated against:

- Tenant size distribution
- Write volume
- Query concurrency
- Retention policy
- Pagination strategy
- Secondary query patterns

## Clustered Indexes in Distributed Systems

Clustering should not be confused with **database clustering**.

These are different concepts:

| Term | Meaning |
|---|---|
| Clustered index | Organizes table data around an index key |
| Database cluster | A group or installation of database resources |
| Clustered database | Often refers to multiple database nodes working together |
| Partitioning | Splits logical data into separate partitions |
| Replication | Maintains copies of data |
| Sharding | Distributes data across independent database nodes |

For example:

```text
Database cluster
├── Node A
├── Node B
└── Node C
```

is unrelated to:

```text
Clustered index
└── Rows organized by key
```

This distinction is a common interview topic.

## Clustered Indexes vs Partitioning

Partitioning divides data into separate physical partitions.

Clustering organizes rows within a table according to a key.

They can complement each other:

```text
Orders
├── 2026-07 partition
│    └── clustered organization
├── 2026-08 partition
│    └── clustered organization
└── 2026-09 partition
     └── clustered organization
```

Partitioning primarily helps with:

- Data lifecycle
- Partition pruning
- Operational maintenance
- Large-table management

Clustering primarily helps with:

- Physical locality
- Access patterns
- Range performance

They solve different problems.

## PostgreSQL Alternatives

For PostgreSQL workloads requiring physical locality, consider several mechanisms rather than assuming `CLUSTER` is the universal answer.

### `CLUSTER`

Useful when:

- A table has a stable read-heavy access pattern.
- Physical ordering provides measurable benefits.
- Periodic maintenance is acceptable.

Example:

```sql
CREATE INDEX idx_events_created_at
ON events (created_at);

CLUSTER events USING idx_events_created_at;
```

### BRIN Indexes

For naturally ordered large tables, a BRIN index can be highly effective.

For example:

```sql
CREATE INDEX idx_events_created_at_brin
ON events USING brin (created_at);
```

BRIN stores summaries of value ranges for blocks rather than individual row locations.

This is particularly attractive for append-heavy time-series data where physical row order naturally correlates with time.

### Partitioning

For very large time-based tables:

```text
events
├── events_2026_07
├── events_2026_08
└── events_2026_09
```

partition pruning can reduce the amount of data considered by a query.

A production PostgreSQL design may therefore prefer:

```text
Partitioning
    +
BRIN / B-tree
    +
natural insertion order
```

rather than repeatedly reclustering a huge table.

## Maintenance Considerations

Physical clustering can deteriorate due to:

- Inserts
- Updates
- Deletes
- Page splits
- Table growth
- Randomly distributed new keys

Monitor actual workload behavior instead of assuming that an old clustering operation remains effective indefinitely.

For PostgreSQL, inspect:

```sql
SELECT
    schemaname,
    tablename,
    attname,
    correlation,
    n_distinct
FROM pg_stats
WHERE tablename = 'orders';
```

For production troubleshooting, combine statistics with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

Look for:

- Actual vs estimated rows
- Heap block reads
- Cache hits
- Scan type
- Execution time
- Rows removed by filtering

## High Availability and Disaster Recovery

A clustered index is part of the database's storage design; it does not replace:

- Replication
- Backups
- Point-in-time recovery
- Failover
- Disaster recovery procedures

For production systems:

```text
Application
    ↓
Primary database
    ├── Replication → Standby
    └── Backups → Object storage
```

Physical reorganization operations can also have operational implications. Large table rewrites or index rebuilds may require substantial I/O, storage, locks, or maintenance windows depending on the database engine.

Treat clustering and rebuilding as database operations that belong in controlled deployment and maintenance procedures.

## Performance Considerations

A clustered index is most valuable when the workload benefits from physical locality.

Evaluate:

| Question | Why It Matters |
|---|---|
| Are queries mostly point lookups? | Clustering may provide limited additional benefit |
| Are queries mostly ranges? | Clustering can be highly beneficial |
| Are rows returned in key order? | Physical locality can help |
| Are inserts random? | Page splits may increase |
| Are writes extremely high? | Write hotspots may matter |
| Is the table huge? | Maintenance cost becomes important |
| Are rows frequently updated? | Physical organization can deteriorate |
| Are there many secondary indexes? | Secondary lookup behavior matters |

Benchmark with representative production-like data.

## Common Mistakes

### Assuming the Primary Key Is Always Clustered

A primary key guarantees uniqueness and non-nullability according to the database's rules, but it does not universally define physical storage.

Always check the specific database engine.

### Assuming There Can Be Multiple Clustered Indexes

A table can generally have only one clustered physical ordering.

You cannot simultaneously physically order one table by:

```text
customer_id
```

and:

```text
created_at
```

as two independent clustered organizations.

Secondary indexes are used for additional access paths.

### Using a Random Key as the Clustered Key Without Evaluation

Random identifiers can create scattered inserts and page splits.

Evaluate:

- Insert distribution
- Key ordering
- Page utilization
- Write concurrency
- Fragmentation

### Treating Clustering as a Substitute for Index Design

Clustering does not eliminate the need for appropriate secondary indexes.

A query such as:

```sql
WHERE status = 'failed'
```

may still require an index on `status` even if the table is clustered by `id`.

### Assuming `CLUSTER` in PostgreSQL Is Permanent

PostgreSQL's `CLUSTER` physically reorders the table at the time it runs.

Normal writes can progressively destroy that ordering.

### Confusing Clustering With Partitioning

Partitioning determines which physical partition contains data.

Clustering determines physical ordering within a storage structure.

They address different optimization problems.

### Ignoring Write Performance

A clustered key that is excellent for reads can be problematic for writes.

Always evaluate:

```text
Read locality
     vs
Insert cost
     vs
Update cost
     vs
Maintenance cost
```

## Interview Traps

**"What is a clustered index?"**

A clustered index organizes the table's data around an index key. In systems such as SQL Server, the clustered index's leaf level contains the table rows.

**"How many clustered indexes can a table have?"**

Typically one, because a table can have only one clustered physical ordering. It can have many secondary/nonclustered indexes.

**"Is a primary key always a clustered index?"**

No. The relationship is database-engine specific. Some systems commonly cluster the primary key by default, while others do not.

**"Does PostgreSQL support clustered indexes?"**

PostgreSQL supports `CLUSTER`, which physically rewrites a table according to an index, but it does not continuously maintain clustered ordering in the same way as SQL Server's clustered index.

**"Why are random UUIDs potentially problematic as clustered keys?"**

Random keys can cause inserts throughout the clustered structure, increasing page splits, fragmentation, and write amplification.

**"Why are sequential keys useful?"**

They provide good locality and generally direct new inserts toward the end of the clustered structure, though this can create a write hotspot at very high concurrency.

**"What is the difference between clustering and partitioning?"**

Clustering concerns physical row organization within a table/storage structure. Partitioning divides a logical table into separate physical partitions.

**"What is the difference between a clustered index and a database cluster?"**

A clustered index is an index/storage organization concept. A database cluster refers to a collection or installation of database resources and is a completely different concept.

## Key Takeaways

- **A clustered index organizes table storage around an index key, making physical locality a major source of range-query performance.**
- **A table generally has only one clustered physical ordering, so the clustered key must be chosen around the dominant workload.**
- **Sequential keys usually provide strong locality, while random keys can increase page splits, fragmentation, and write amplification.**
- **PostgreSQL does not have a permanently maintained clustered index like SQL Server; `CLUSTER` performs a physical reorder that can degrade as the table changes.**
- **Clustering, partitioning, replication, and database clustering solve different problems and should not be treated as interchangeable concepts.**