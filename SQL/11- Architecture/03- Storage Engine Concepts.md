# 03- Storage Engine Concepts

## Overview

A storage engine is the part of a database system responsible for representing logical database objects as durable physical data and managing how that data is written, read, updated, recovered, and maintained.

For backend engineers, storage-engine knowledge explains why database operations behave differently from ordinary in-memory operations.

A SQL statement such as:

```sql
UPDATE orders
SET status = 'paid'
WHERE id = 1001;
```

does not simply overwrite a variable in memory. The database must coordinate:

- Table storage
- Indexes
- Memory buffers
- Transactions
- MVCC
- WAL
- Locks
- Durability
- Crash recovery
- Background maintenance

A useful mental model is:

```text
                SQL
                 │
                 ▼
        Query Execution Engine
                 │
                 ▼
        Storage Access Layer
          ┌──────┴──────┐
          │             │
          ▼             ▼
        Tables        Indexes
          │             │
          └──────┬──────┘
                 ▼
            Buffer Cache
                 │
                 ▼
          Durable Storage
                 ▲
                 │
                WAL
```

PostgreSQL is used throughout this document for concrete examples. PostgreSQL does not expose a pluggable storage-engine architecture in the same way as MySQL's InnoDB/MyISAM model; instead, PostgreSQL has a tightly integrated storage subsystem built around heap tables, indexes, MVCC, WAL, and related components.

---

## Logical Data vs Physical Storage

SQL exposes a logical model:

```text
Database
 ├── Schema
 │    ├── Table
 │    ├── Index
 │    └── Constraint
 └── View
```

The storage subsystem represents these logical objects using physical structures.

For example:

```text
Logical table: orders

Physical representation:
├── table relation
├── indexes
├── metadata
├── visibility information
└── associated storage structures
```

This abstraction is important because application developers should normally work with logical database objects rather than manipulating physical files directly.

The database is responsible for maintaining the mapping between:

```text
SQL object
   ↓
Database relation
   ↓
Pages / blocks
   ↓
Storage
```

---

## What the Storage Engine Does

A database storage subsystem is responsible for several fundamental operations.

| Responsibility | Purpose |
|---|---|
| Data layout | Store rows and pages efficiently |
| Reads | Retrieve table/index data |
| Writes | Persist inserts, updates, and deletes |
| Buffering | Cache frequently accessed pages |
| Transactions | Maintain atomicity and visibility |
| Concurrency | Coordinate simultaneous operations |
| WAL | Record changes for recovery |
| Recovery | Restore consistency after failure |
| Maintenance | Remove obsolete versions and maintain statistics |
| Index storage | Maintain structures for efficient lookup |

The exact implementation differs across database systems.

---

## PostgreSQL Storage Architecture

A simplified PostgreSQL architecture is:

```text
PostgreSQL
│
├── Query Executor
│
├── Buffer Manager
│
├── Heap Tables
│
├── Indexes
│
├── Transaction / MVCC
│
├── Lock Manager
│
├── WAL
│
├── Background Maintenance
│   └── VACUUM / ANALYZE
│
└── Persistent Storage
```

These components cooperate rather than operating independently.

For example, an update can involve:

```text
UPDATE
  │
  ▼
Executor
  │
  ├── Locate row through index/table scan
  │
  ├── Create new row version
  │
  ├── Update indexes where required
  │
  ├── Generate WAL
  │
  └── Make changes visible according to transaction rules
```

---

## Pages and Blocks

Database storage is generally organized into fixed-size pages or blocks.

PostgreSQL uses 8 KB pages by default.

Conceptually:

```text
Table
│
├── Page 0
│   ├── Row
│   ├── Row
│   └── Row
│
├── Page 1
│   ├── Row
│   ├── Row
│   └── Row
│
├── Page 2
│   ├── Row
│   └── Row
│
└── ...
```

The database reads and writes pages rather than treating every row as an independent disk operation.

This has important performance implications:

- Sequential page access can be efficient.
- Random access can be expensive.
- Large scans can generate substantial I/O.
- Row size affects how many rows fit into a page.
- Indexes help locate relevant pages without scanning the entire relation.

---

## Heap Tables

PostgreSQL's ordinary tables use a heap-storage model.

A heap table does not store rows in sorted order based on a primary key.

For example:

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
```

The physical row placement is separate from the logical ordering implied by:

```sql
ORDER BY id;
```

A primary key creates a unique index, but that does not mean the table itself is physically sorted by `id`.

This distinction is important when reasoning about:

- Sequential scans
- Index scans
- Physical locality
- Updates
- Table bloat

---

## Row Storage

A logical row is represented physically within a database page.

Conceptually:

```text
Page
┌──────────────────────────────┐
│ Page metadata                │
├──────────────────────────────┤
│ Row pointer / item metadata  │
├──────────────────────────────┤
│ Row data                     │
│ Row data                     │
│ Row data                     │
└──────────────────────────────┘
```

PostgreSQL rows also contain transaction-related metadata used by MVCC.

This means physical row representation contains more information than just application columns.

---

## TOAST

PostgreSQL uses TOAST (The Oversized-Attribute Storage Technique) for values that are too large to fit efficiently inside ordinary row storage.

This is particularly relevant for large:

- `TEXT`
- `BYTEA`
- `JSONB`
- Other variable-length values

Conceptually:

```text
Main table row
     │
     ├── small attributes
     │
     └── pointer to large value
                 │
                 ▼
             TOAST table
```

TOAST can keep large values out of the main row when appropriate.

### Production implications

Large columns can still affect:

- I/O
- Network transfer
- Cache efficiency
- WAL generation
- Update cost
- Storage consumption

Do not assume that using TOAST makes large values free.

---

## Index Storage

Indexes provide a separate physical structure used to locate table data efficiently.

For a B-tree index:

```text
             Root
            /    \
           /      \
       Internal  Internal
         /           \
       Leaf          Leaf
        │              │
        ▼              ▼
   Table locations
```

A common PostgreSQL index is:

```sql
CREATE INDEX idx_orders_customer_id
ON orders(customer_id);
```

A query can then potentially locate matching rows through the index rather than scanning every table page.

---

## B-Tree Indexes

PostgreSQL's default index type is B-tree.

B-tree indexes are suitable for many common predicates:

```sql
WHERE customer_id = 42
```

```sql
WHERE created_at >= '2026-01-01'
```

and ordering operations such as:

```sql
ORDER BY created_at DESC
```

when the index and query shape make that useful.

B-tree indexes provide logarithmic-style tree navigation rather than requiring a full scan of the index for every lookup.

---

## Index Scan vs Sequential Scan

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = 42;
```

The planner may choose:

```text
Sequential Scan
```

or:

```text
Index Scan
```

depending on estimated cost.

An index is not automatically faster.

For example:

```text
Rows in table       = 1,000
Rows matching       = 900
```

Reading most of the table may be cheaper than using an index and then performing many table lookups.

But:

```text
Rows in table       = 100,000,000
Rows matching       = 10
```

an index can dramatically reduce the amount of data examined.

---

## Heap Fetches and Index-Only Scans

A traditional index scan may require:

```text
Index
  │
  ▼
Table page
  │
  ▼
Row
```

An index-only scan can sometimes return the required data directly from the index without fetching the corresponding heap page.

For example:

```sql
CREATE INDEX idx_users_email_id
ON users(email, id);
```

A query that only needs indexed columns may be eligible for an index-only scan.

Visibility information also matters for PostgreSQL index-only scans because PostgreSQL must determine whether the relevant table entries are visible to the current transaction.

---

## Buffer Cache

The database uses memory to avoid repeatedly reading the same pages from storage.

Simplified:

```text
Query
  │
  ▼
Buffer Manager
  │
  ├── Cache hit
  │      │
  │      ▼
  │    Return page
  │
  └── Cache miss
         │
         ▼
       Storage
         │
         ▼
     Load page
         │
         ▼
      Cache
```

PostgreSQL's shared buffer pool is called `shared_buffers`.

The operating-system page cache also participates in the overall caching behavior.

Therefore:

> Database memory performance cannot be understood by looking at one cache layer in isolation.

---

## Cache Hit vs Disk Read

A cache hit avoids a physical storage read.

For example:

```text
Query
 │
 ▼
Buffer cache
 │
 ├── Hit → fast access
 │
 └── Miss → storage I/O
```

Repeated access to hot data can therefore be much faster than cold access.

However, cache behavior depends on:

- Working-set size
- Query patterns
- Memory configuration
- Concurrent workload
- OS caching
- Storage performance

Do not assume that one successful benchmark represents production behavior.

---

## WAL

PostgreSQL uses Write-Ahead Logging to provide durability and crash recovery.

The basic rule is:

> Required WAL records must reach durable storage before the corresponding transaction is considered durably committed.

Simplified write path:

```text
Application
    │
    ▼
UPDATE
    │
    ▼
Modify database state
    │
    ├──────────────► WAL record
    │                    │
    │                    ▼
    │               Durable WAL
    │
    ▼
COMMIT
```

Data pages may be written to their final storage locations later.

This separation allows PostgreSQL to use WAL for recovery and replication.

---

## WAL and Write Amplification

A single logical update can cause multiple physical changes.

For example:

```sql
UPDATE orders
SET status = 'paid'
WHERE id = 1001;
```

Potential physical effects include:

```text
Table modification
       │
       ├── WAL record
       │
       ├── Index changes, if required
       │
       └── New row version
```

Heavy write workloads can therefore generate substantial WAL.

High WAL generation can affect:

- Storage throughput
- Replication bandwidth
- Replica lag
- Backup volume
- Recovery time
- Cost

---

## MVCC

PostgreSQL uses Multi-Version Concurrency Control.

An update does not simply replace a row in place from the perspective of transaction visibility.

Conceptually:

```text
Before UPDATE

Row Version A
     │
     ▼
Visible to transaction T1


After UPDATE

Row Version A ──► old version
     │
     ▼
Row Version B ──► new version
```

Different transactions may see different row versions depending on transaction visibility rules.

MVCC enables readers and writers to operate concurrently without requiring every read to acquire traditional blocking locks.

---

## UPDATE Is Not Always an In-Place Overwrite

Consider:

```sql
UPDATE accounts
SET balance = balance - 100
WHERE id = 42;
```

From an application perspective, this is a simple modification.

Internally, PostgreSQL's MVCC model can create a new row version while the old version remains relevant to transactions that may still need to see it.

This is one reason PostgreSQL requires vacuuming.

---

## DELETE and MVCC

A delete also interacts with MVCC.

Conceptually:

```text
DELETE row
    │
    ▼
Row marked obsolete
    │
    ▼
Existing transactions may still need visibility
    │
    ▼
VACUUM later removes reclaimable versions
```

Therefore:

```sql
DELETE FROM events
WHERE created_at < now() - interval '1 year';
```

can have substantial storage and maintenance consequences when executed against a very large table.

---

## Table Bloat

Table bloat refers broadly to wasted or temporarily unusable space resulting from obsolete row versions, dead tuples, page layout, and other storage effects.

A simplified lifecycle is:

```text
INSERT
  │
  ▼
Row version
  │
  ▼
UPDATE / DELETE
  │
  ▼
Old version
  │
  ▼
VACUUM
  │
  ▼
Space becomes reusable
```

Bloat can increase:

- Table size
- Index size
- I/O
- Cache requirements
- Scan cost

The exact cleanup and reclamation behavior depends on PostgreSQL maintenance operations and workload.

---

## VACUUM

`VACUUM` performs important PostgreSQL maintenance.

It can:

- Remove obsolete row versions from active consideration
- Make space reusable
- Maintain visibility information
- Support healthy MVCC operation

Autovacuum normally performs this work automatically.

Inspecting tables can begin with:

```sql
SELECT
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

Do not disable autovacuum simply because it creates background activity.

---

## VACUUM vs VACUUM FULL

These operations have very different characteristics.

| Operation | Typical Purpose | Lock / Operational Impact |
|---|---|---|
| `VACUUM` | Routine MVCC cleanup | Designed for regular online maintenance |
| `VACUUM (ANALYZE)` | Cleanup + refresh statistics | Common maintenance operation |
| `VACUUM FULL` | Compact/rewrite table | Much more disruptive; requires stronger locking |

`VACUUM FULL` should not be treated as routine maintenance.

Large production tables require careful planning before using operations that rewrite the table.

---

## ANALYZE and Statistics

The query planner needs statistics to estimate query costs.

`ANALYZE` collects statistics about table data.

For example:

```sql
ANALYZE orders;
```

The planner can use statistics to estimate:

- Number of rows
- Value distribution
- Predicate selectivity
- Join cardinality

Bad statistics can lead to poor execution plans.

This is why autovacuum and auto-analyze are important parts of database performance.

---

## Checkpoints

A checkpoint establishes a point from which crash recovery can reason about durable database state.

Conceptually:

```text
WAL
─────────────────────────────────────────────►

      Checkpoint
          │
          ▼
   Recovery reference point
```

Checkpoints involve writing dirty data pages and other coordination.

Checkpoint behavior influences:

- I/O patterns
- WAL generation
- Recovery time
- Write latency

Database configuration should be tuned using production measurements rather than copied blindly from another environment.

---

## Crash Recovery

Suppose PostgreSQL modifies a page in memory and then the host crashes before the data page reaches durable storage.

If the corresponding WAL is durable, PostgreSQL can replay the WAL during recovery.

```text
Before crash

WAL ────────────────► Durable
Data page ──────────► Memory

              ↓

            Crash

              ↓

Recovery reads WAL
              │
              ▼
Reconstruct required state
```

This is a fundamental storage-engine reliability mechanism.

---

## Durability

Durability means that after a successful commit, the database can recover the committed transaction after a failure according to its configured durability guarantees.

Durability depends on:

- WAL
- Storage behavior
- PostgreSQL configuration
- Filesystem behavior
- Hardware
- Replication
- Backup architecture

A production engineer should distinguish:

```text
Transaction committed
```

from:

```text
Data replicated to another region
```

These are different guarantees.

---

## Replication and WAL

PostgreSQL streaming replication uses WAL as the change stream.

A simplified architecture is:

```text
Primary
  │
  ├── Generate WAL
  │
  ▼
WAL sender
  │
  │ streaming
  ▼
WAL receiver
  │
  ▼
Replica
  │
  ▼
Replay WAL
```

This architecture enables:

- Read replicas
- High availability
- Standby servers
- Disaster recovery architectures

Replication lag means a replica has not yet replayed all changes received/generated by the primary.

---

## Storage and Read Replicas

A replica's ability to serve reads depends on its ability to keep up with WAL replay.

```text
Primary write rate
        │
        ▼
WAL generation
        │
        ▼
Network transfer
        │
        ▼
Replica WAL receive
        │
        ▼
WAL replay
        │
        ▼
Readable state
```

If any stage becomes a bottleneck, replication lag can increase.

Potential causes include:

- High write volume
- Network constraints
- Replica CPU pressure
- Replica storage latency
- Long-running queries
- Recovery/replay contention

---

## Storage Performance

Database storage performance has several dimensions.

| Dimension | Meaning |
|---|---|
| Latency | Time for an individual I/O |
| IOPS | Number of I/O operations per second |
| Throughput | Amount of data transferred per second |
| Durability | Ability to preserve data across failures |
| Capacity | Available storage space |

A workload can be limited by one dimension without being limited by another.

For example:

```text
Small random reads
→ latency / IOPS sensitive
```

while:

```text
Large sequential scan
→ throughput sensitive
```

---

## SSD and Cloud Storage

Modern production PostgreSQL deployments commonly use SSD-backed storage.

On AWS, managed PostgreSQL deployments can use EBS-backed storage or Aurora's distributed storage architecture depending on the service.

Storage selection should consider:

- IOPS requirements
- Throughput
- Latency
- Capacity
- Growth rate
- Backup requirements
- Cost

Storage should be selected based on workload characteristics rather than simply choosing the largest available disk.

---

## Storage and Query Performance

A query can be CPU-bound or I/O-bound.

Example:

```sql
SELECT *
FROM events
WHERE payload @> '{"type": "payment"}';
```

Potential bottlenecks include:

```text
CPU
 │
 ├── JSON processing
 │
 └── query execution

I/O
 │
 ├── table reads
 │
 └── index reads
```

Use execution plans and system metrics to determine the actual bottleneck.

---

## Sequential I/O vs Random I/O

Sequential access:

```text
Page 1 → Page 2 → Page 3 → Page 4
```

is generally more storage-efficient than many unrelated random accesses:

```text
Page 103 → Page 9 → Page 700 → Page 42
```

Indexes can reduce the total amount of data read but may introduce random access patterns.

This is one reason an index is not automatically faster for every query.

---

## Write Amplification

Write amplification occurs when one logical application write causes multiple physical writes.

For example:

```text
Application UPDATE
       │
       ├── table changes
       ├── index changes
       ├── WAL
       └── associated metadata
```

Additional indexes can therefore increase write amplification.

For write-heavy systems, excessive indexing can become a major performance cost.

---

## Large Transactions and Storage

Large transactions can generate substantial:

- WAL
- Dirty pages
- Row versions
- Lock duration
- Replication work

For example:

```sql
DELETE FROM audit_events
WHERE created_at < '2024-01-01';
```

on a multi-billion-row table can create significant operational pressure.

A safer approach may be bounded batches:

```sql
DELETE FROM audit_events
WHERE id IN (
    SELECT id
    FROM audit_events
    WHERE created_at < '2024-01-01'
    ORDER BY id
    LIMIT 5000
);
```

The exact batching strategy should be designed around indexes, transaction semantics, lock behavior, and acceptable intermediate states.

---

## Storage and Transactions

Transaction design directly affects storage behavior.

Short transaction:

```text
BEGIN
  ↓
few writes
  ↓
COMMIT
  ↓
resources released
```

Long transaction:

```text
BEGIN
  ↓
many operations
  ↓
long wait
  ↓
more row versions retained
  ↓
locks/snapshots remain active
  ↓
COMMIT
```

Long-running transactions can interfere with MVCC cleanup and increase operational risk.

---

## Temporary Files

Some database operations require temporary disk space.

Examples include:

- Large sorts
- Hash operations
- Complex joins
- Aggregations

A query may therefore consume storage even when it does not explicitly modify a table.

Monitor temporary file generation when investigating queries that consume unexpectedly large amounts of I/O.

---

## Storage and Sorting

Consider:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC;
```

If the database cannot efficiently satisfy the ordering from an appropriate index or other strategy, it may need to perform a sort.

Large sorts can consume memory and potentially spill to temporary storage.

A suitable index may sometimes help:

```sql
CREATE INDEX idx_orders_created_at
ON orders(created_at DESC);
```

Whether this is beneficial depends on the complete query and planner cost model.

---

## Storage and Joins

Joins can also create significant memory and I/O activity.

For example:

```sql
SELECT o.id, c.email
FROM orders o
JOIN customers c
  ON c.id = o.customer_id;
```

The planner may choose among different join strategies depending on statistics and available indexes.

Possible strategies include:

- Nested loop
- Hash join
- Merge join

The storage subsystem determines how efficiently the chosen plan can access the required pages.

---

## Monitoring Storage Behavior

Useful PostgreSQL observability areas include:

### Table statistics

```sql
SELECT
    relname,
    n_live_tup,
    n_dead_tup,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

### Index usage

```sql
SELECT
    relname,
    indexrelname,
    idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

### Active queries

```sql
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE state <> 'idle';
```

### Query execution

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 42;
```

`BUFFERS` helps distinguish execution behavior involving shared/local/temp buffer activity.

---

## Storage Health Metrics

A production monitoring system should track:

- Database storage utilization
- Storage latency
- IOPS
- Throughput
- Cache hit behavior
- WAL generation
- WAL retention
- Replication lag
- Temporary file usage
- Table growth
- Index growth
- Dead tuples
- Autovacuum activity

A useful capacity model is:

```text
Storage Growth
     │
     ├── Table data
     ├── Indexes
     ├── WAL
     ├── Temporary files
     └── Maintenance overhead
```

Planning only for current table size is insufficient.

---

## Backup and Recovery Implications

Storage architecture directly affects recovery.

Backups may involve:

- Base backups
- WAL archiving
- Point-in-time recovery
- Snapshots
- Managed backup services

A recovery architecture should answer:

```text
How much data can we lose?
        │
        ▼
RPO

How quickly must service recover?
        │
        ▼
RTO
```

Replication can improve availability but should not be treated as a complete backup strategy.

---

## Security Considerations

Storage-engine security includes more than SQL permissions.

Consider:

- Encryption at rest
- Encryption in transit
- Disk access controls
- Database role privileges
- Backup encryption
- Backup access controls
- Secret management
- Audit logging
- Secure deletion requirements

On managed cloud platforms, storage encryption should be configured using the platform's supported encryption mechanisms.

Sensitive data should also be minimized and retained only as long as required.

---

## Cost Considerations

Storage costs come from more than table size.

Total database cost can include:

```text
Compute
+ Memory
+ Primary storage
+ IOPS
+ Backup storage
+ WAL/archive storage
+ Replica capacity
+ Network transfer
+ Operational tooling
```

Poor storage design can increase cost through:

- Excessive indexes
- Unbounded table growth
- Duplicate data
- Large temporary files
- Excessive replicas
- High WAL volume

Performance optimization should therefore consider cost as well as latency.

---

## Common Storage Engine Mistakes

### Assuming Rows Are Stored in Primary-Key Order

A primary key does not guarantee physical table ordering.

Use `ORDER BY` when ordering is required.

---

### Treating Indexes as Free

Indexes consume storage and increase write and maintenance costs.

Create indexes based on real access patterns.

---

### Disabling Autovacuum

Autovacuum is fundamental to healthy PostgreSQL MVCC operation.

If autovacuum appears problematic, investigate:

- Table workload
- Thresholds
- Scale factors
- Long-running transactions
- I/O pressure
- Table-specific configuration

Do not simply disable it.

---

### Using `VACUUM FULL` as Routine Maintenance

`VACUUM FULL` rewrites the table and requires stronger locking.

Use it only when its operational impact is understood and justified.

---

### Running Huge Deletes in One Transaction

A massive delete can generate substantial WAL, retain many resources, increase replication lag, and create long-running transactions.

Prefer appropriate batching or partition lifecycle management when the business semantics allow it.

---

### Ignoring Large Values

Large `TEXT`, `JSONB`, or binary payloads can affect storage, caching, WAL, and network performance even when TOAST is involved.

Store large objects deliberately.

---

### Assuming SSD Eliminates Database I/O Problems

Fast storage does not eliminate:

- Excessive scans
- Poor indexes
- Bad query plans
- Random I/O
- Excessive WAL
- Cache pressure

Database design still matters.

---

### Optimizing Storage Before Inspecting the Query

Changing storage capacity without understanding the query workload can waste money without fixing the bottleneck.

Start with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

and correlate the result with system metrics.

---

## Production Design Guidelines

### For Read-Heavy Systems

- Keep frequently accessed data cache-friendly.
- Use appropriate indexes.
- Avoid unnecessary columns in result sets.
- Use read replicas where consistency requirements permit.
- Monitor cache and storage behavior.

### For Write-Heavy Systems

- Minimize unnecessary indexes.
- Keep transactions appropriately sized.
- Monitor WAL generation.
- Monitor replica lag.
- Avoid unnecessary updates.
- Batch large maintenance operations when appropriate.

### For Very Large Tables

- Consider partitioning where access and lifecycle patterns justify it.
- Plan retention policies.
- Monitor table and index growth.
- Avoid unbounded transactions.
- Test maintenance operations against production-scale data.

### For High Availability

- Monitor replication.
- Test failover.
- Verify backups.
- Test point-in-time recovery where required.
- Ensure applications reconnect correctly after database failover.

---

## Storage Engine Decision Model

When investigating a storage-related database problem, use a layered approach:

```text
Slow database operation
        │
        ▼
Is the SQL efficient?
        │
        ▼
Check EXPLAIN / EXPLAIN ANALYZE
        │
        ▼
Is the plan appropriate?
        │
        ▼
Check indexes and statistics
        │
        ▼
Check buffer / I/O behavior
        │
        ▼
Check CPU and storage latency
        │
        ▼
Check concurrency and locks
        │
        ▼
Check WAL / replication pressure
        │
        ▼
Apply the smallest justified change
```

This prevents premature infrastructure scaling.

---

## Interview Traps

### "Does PostgreSQL overwrite a row in place for every UPDATE?"

Not conceptually from the perspective of MVCC. PostgreSQL creates row versions so concurrent transactions can maintain appropriate visibility.

### "Why does PostgreSQL need VACUUM?"

Because MVCC creates obsolete row versions that eventually need cleanup and space reclamation.

### "Does a primary key physically sort a PostgreSQL table?"

No. The primary key normally creates a unique index; the heap table itself is not automatically maintained in primary-key order.

### "Why can an index make writes slower?"

Every relevant write may require changes to one or more indexes in addition to the table itself, increasing write amplification and maintenance work.

### "Why can a read replica lag?"

The primary generates WAL that must be transferred, received, and replayed by the replica. Any bottleneck in that pipeline can increase lag.

### "Why is WAL important?"

WAL provides the foundation for crash recovery and durability and is also used for PostgreSQL replication.

### "Why can a large transaction affect unrelated queries?"

Large or long-running transactions can increase WAL, retain MVCC snapshots, hold locks, consume connections, and increase storage and replication pressure.

### "Is a sequential scan always bad?"

No. For small tables or queries returning a large percentage of rows, a sequential scan can be cheaper than an index-based strategy.

### "Does faster storage solve poor SQL?"

No. Poor query plans, missing or excessive indexes, inefficient access patterns, and unnecessary data transfer can remain the dominant bottlenecks.

## Key Takeaways

- PostgreSQL storage is page-oriented and built around heap tables, indexes, buffers, MVCC, WAL, and background maintenance rather than direct row-by-row disk operations.
- MVCC means updates and deletes create storage-maintenance consequences, making VACUUM, autovacuum, statistics, and transaction duration important production concerns.
- WAL provides the foundation for durability, crash recovery, and streaming replication, while write volume directly affects storage, replication, and recovery costs.
- Indexes and caching reduce read work but introduce storage and write-maintenance costs; their value must be evaluated against real query plans and workload characteristics.
- Senior database troubleshooting should correlate SQL execution plans with memory, I/O, WAL, replication, concurrency, and storage metrics before changing infrastructure.