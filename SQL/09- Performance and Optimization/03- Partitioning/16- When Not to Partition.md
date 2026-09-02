# 16- When Not to Partition

## Overview

Partitioning is a powerful database design technique, but it is not a default optimization for large tables. It introduces additional physical structures, indexes, metadata, lifecycle automation, migration complexity, and operational responsibilities.

A table should **not** be partitioned merely because it is large, contains millions of rows, or is expected to grow. Partitioning is justified when it solves a specific workload or operational problem that cannot be addressed more simply.

The senior-level decision is therefore not:

> "Can this table be partitioned?"

It is:

> **"Does partitioning provide enough measurable value to justify its operational and performance costs?"**

In many systems, a well-designed index, query rewrite, caching strategy, read replica, archival policy, or hardware upgrade provides a better return with substantially less complexity.

## The Core Decision

A useful decision model is:

```text
                    Production problem
                           │
                           ▼
                    Measure workload
                           │
                           ▼
                  Inspect query plans
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       Index/query fix              Lifecycle problem?
             │                           │
             ▼                           ▼
       Can it solve it?              Yes ───────┐
             │                                  │
       ┌─────┴─────┐                            ▼
       │           │                     Evaluate partitioning
      Yes          No                           │
       │           │                            ▼
       ▼           ▼                     Benchmark benefits
     Stop      Evaluate other                   │
                strategies                      ▼
                                           Complexity justified?
                                                 │
                                          ┌──────┴──────┐
                                          │             │
                                         Yes            No
                                          │             │
                                          ▼             ▼
                                    Partition      Keep simpler design
```

Partitioning should be introduced only when the evidence supports it.

## Small and Moderate Tables

Small tables generally do not benefit enough from partitioning to justify the additional complexity.

For example:

```text
users
10 million rows
20 GB total
```

This may still be a perfectly reasonable unpartitioned table if:

- Queries use effective indexes.
- Maintenance is fast.
- Storage is available.
- Retention is not complicated.
- Query latency meets the service-level objective.

The fact that a table has millions of rows does not itself indicate that partitioning is required.

### Why Partitioning Can Be Worse

Partitioning can introduce:

- More indexes.
- More statistics.
- More metadata.
- More DDL operations.
- More migration complexity.
- More monitoring requirements.
- More complicated backup and recovery procedures.
- More opportunities for configuration mistakes.

For a table that already performs well, these costs provide little value.

## When an Index Is the Better Solution

A common reason not to partition is that a normal index solves the actual problem.

Consider:

```sql
SELECT id, status, created_at
FROM orders
WHERE tenant_id = 42
ORDER BY created_at DESC
LIMIT 100;
```

A suitable index may be enough:

```sql
CREATE INDEX orders_tenant_created_idx
ON orders (tenant_id, created_at DESC);
```

If `EXPLAIN (ANALYZE, BUFFERS)` shows an efficient index scan with acceptable latency, partitioning may add complexity without improving the workload.

The distinction is important:

| Technique | Primary Purpose |
|---|---|
| Index | Efficiently locate matching rows |
| Partitioning | Reduce the physical data scope |
| Caching | Avoid repeated database work |
| Read replica | Scale read workloads |
| Archiving | Move infrequently accessed data |
| Sharding | Scale across database instances |

Do not use partitioning to solve a problem that indexing already solves.

## When Query Optimization Is the Better Solution

Partitioning cannot compensate for poorly written SQL.

Consider:

```sql
SELECT *
FROM orders
WHERE DATE(created_at) = DATE '2026-08-01';
```

Depending on the database and indexing strategy, applying a function to the column can make efficient index usage harder.

A range predicate is generally preferable:

```sql
SELECT id, status, created_at
FROM orders
WHERE created_at >= TIMESTAMPTZ '2026-08-01 00:00:00+00'
  AND created_at < TIMESTAMPTZ '2026-09-01 00:00:00+00';
```

Before introducing partitions, investigate:

- Query predicates.
- Join conditions.
- Sorting.
- Aggregations.
- Functions applied to indexed columns.
- Implicit casts.
- Pagination strategy.
- Selected columns.
- N+1 queries at the application layer.

A query rewrite can sometimes produce a larger performance improvement than partitioning.

## When Queries Do Not Restrict the Partition Key

Partitioning works best when queries provide predicates that allow the database to eliminate irrelevant partitions.

Suppose a table is partitioned by:

```sql
created_at
```

This query is partition-friendly:

```sql
SELECT *
FROM events
WHERE created_at >= '2026-08-01'
  AND created_at < '2026-09-01';
```

But this query does not constrain the partition key:

```sql
SELECT *
FROM events
WHERE event_type = 'payment';
```

The database may need to inspect many or all partitions.

If the dominant workload looks like:

```text
Query
  │
  └── no partition-key predicate
           │
           ▼
      many partitions
           │
           ▼
      many scans
```

partitioning may provide little benefit.

### A Critical Rule

> **Do not choose a partition key simply because the column looks logical. Choose it because important production queries and lifecycle operations actually use it.**

## When Full-Table Queries Dominate

Partitioning can be a poor fit when the application frequently needs most or all rows.

Examples include:

- Full-table exports.
- Large analytical queries.
- Historical reports.
- Global aggregation.
- Data warehouse extraction.
- Batch processing across the entire dataset.

For example:

```sql
SELECT
    COUNT(*),
    SUM(amount)
FROM transactions;
```

If this query regularly needs the entire dataset, partition pruning provides little benefit.

Partitioning may still provide lifecycle or maintenance benefits, but it should not be justified solely on query performance.

## When Cross-Partition Queries Dominate

Partitioning introduces a physical boundary that queries may need to cross.

For example:

```text
Partition A ─┐
Partition B ─┤
Partition C ─┼── Query
Partition D ─┤
Partition E ─┘
```

A query spanning many partitions may require:

- Planning across multiple relations.
- Scans against multiple partitions.
- Multiple index operations.
- Result merging.
- Additional I/O.

This does not mean cross-partition queries are inherently bad. It means their cost must be included in the benchmark.

If most important queries span nearly every partition, partitioning may not provide meaningful query-performance benefits.

## When the Partition Count Would Become Excessive

Partitioning should be rejected when the required partition count becomes operationally unreasonable.

Consider a tenant-per-partition design:

```text
tenant_001
tenant_002
tenant_003
...
tenant_100000
```

This can create a significant management problem.

Each partition may introduce:

- Physical storage.
- Indexes.
- Statistics.
- Metadata.
- Maintenance work.
- Monitoring requirements.
- DDL complexity.

Composite partitioning can multiply the problem.

For example:

```text
10,000 tenants × 84 monthly partitions
= 840,000 potential partitions
```

Even if the database technically permits a large number of partitions, that does not mean the design is operationally sound.

## When Tenant-per-Partition Is the Wrong Design

Multi-tenant systems frequently tempt engineers into creating one partition per tenant.

That approach can work for a **small, controlled number of large tenants**, but it becomes problematic when tenant count is highly dynamic.

Prefer alternatives when there are thousands or millions of tenants:

- Composite indexes.
- Hash partitioning with a bounded partition count.
- Tenant grouping.
- Separate databases for very large tenants.
- Sharding for true horizontal scaling.

For example:

```text
Instead of:

tenant_1
tenant_2
...
tenant_100000

Consider:

partition_0
partition_1
...
partition_31

WHERE hash(tenant_id) determines the partition
```

The exact strategy depends on workload characteristics and database capabilities.

## When Data Growth Is Slow

Partitioning is less compelling when the table grows slowly.

For example:

```text
Current size: 8 GB
Growth: 100 MB/month
```

If the table has good indexes and predictable maintenance costs, introducing partitioning years before it is needed can create unnecessary complexity.

Premature partitioning creates a maintenance obligation before there is a corresponding benefit.

A better approach may be:

1. Monitor growth.
2. Establish thresholds.
3. Optimize indexes and queries.
4. Define a future partitioning strategy.
5. Partition when measurable requirements justify it.

## When Retention Does Not Require Partitioning

Time-based retention is one of the strongest arguments for range partitioning, but not every retention policy requires it.

For moderate deletion volumes, a controlled batch-delete process may be sufficient.

For example:

```sql
DELETE FROM audit_logs
WHERE id IN (
    SELECT id
    FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
    ORDER BY id
    LIMIT 5000
);
```

The exact implementation should be adapted to the database engine and workload.

If retention operations are already inexpensive and reliable, partitioning solely to simplify deletion may not justify the additional complexity.

However, continuously deleting very large volumes of old rows can create substantial write amplification, WAL, bloat, and vacuum pressure. That is a point where partitioning should be reconsidered.

## When Application Requirements Change Frequently

Partitioning creates a physical schema structure that must evolve with the application.

If the partition strategy depends on frequently changing business rules, it can become difficult to maintain.

For example, partitioning by:

```text
business_category
```

may become problematic if categories are frequently:

- Added.
- Removed.
- Renamed.
- Reorganized.
- Reassigned.

Partitioning is better suited to stable dimensions with predictable boundaries.

## When Partition Key Cardinality Is a Poor Fit

The partition key should have characteristics appropriate to the selected strategy.

A poor partition key can cause:

- Skewed partitions.
- Hot partitions.
- Poor pruning.
- Excessive partition count.
- Difficult lifecycle management.

For example:

```text
Partition by country
```

may produce:

```text
US       → 70%
IN       → 15%
DE       → 5%
others   → 10%
```

This is not necessarily wrong, but the uneven distribution must be considered.

Hash partitioning may be more appropriate when the goal is even distribution rather than semantic grouping.

## When a Single Partition Becomes a Hot Spot

Partitioning does not automatically distribute workload.

With range partitioning:

```text
events_2026_08
       │
       ├── 90% of writes
       ├── recent reads
       └── index updates
```

the current partition may still be the system's primary bottleneck.

This is especially relevant for:

- Event ingestion.
- Metrics.
- IoT workloads.
- Kafka consumers.
- High-volume API writes.
- Log ingestion.

If one partition receives almost all writes, adding more historical partitions does not solve the write bottleneck.

## When Sharding Is the Actual Requirement

Partitioning operates within a database-level architecture. It does not inherently distribute workload across multiple database instances.

If the primary problem is:

- Database CPU saturation.
- Maximum storage capacity.
- Write throughput limits.
- Memory constraints.
- Failure-domain requirements.

then partitioning may not be sufficient.

The architecture may instead require:

```text
Application
    │
    ▼
Shard Router
    │
    ├── Database Shard A
    ├── Database Shard B
    ├── Database Shard C
    └── Database Shard D
```

Sharding introduces significant complexity, so it should not be the first response to a large table. But if the bottleneck is the capacity of a single database instance, partitioning alone cannot solve that architectural constraint.

## When Caching Is the Better Solution

If the workload repeatedly reads the same data, caching may be more effective.

For example:

```text
FastAPI / Django
       │
       ▼
     Redis
       │
       ├── Cache hit → response
       │
       └── Cache miss
               │
               ▼
            PostgreSQL
```

If database load comes primarily from repeated reads of relatively stable data, partitioning may attack the wrong layer.

Use partitioning for physical data organization and lifecycle problems, not as a replacement for a properly designed caching strategy.

## When Read Replicas Are the Better Solution

Partitioning does not inherently distribute read traffic across database instances.

If the problem is:

```text
Primary database
    │
    ├── Application reads
    ├── Reporting reads
    ├── API reads
    └── Background-job reads
```

then read replicas or workload isolation may be more appropriate:

```text
                    ┌── Read Replica A
Application ────────┼── Read Replica B
                    └── Primary
                         │
                         └── Writes
```

Partitioning and replicas solve different problems and can also be combined when appropriate.

## When an Analytical Workload Should Move Elsewhere

A common mistake is using an OLTP database as an analytical platform.

If queries perform:

- Large aggregations.
- Historical scans.
- Complex reporting.
- Data science workloads.
- Long-running joins.

partitioning may reduce some physical scanning but does not change the fundamental workload characteristics.

Consider separating analytical workloads using:

- Data warehouses.
- Lakehouse architectures.
- ETL/ELT pipelines.
- CDC pipelines.
- Dedicated analytical databases.

For AWS-based systems, this might involve moving analytical workloads toward services such as S3-based data lakes and analytical query engines rather than continuously increasing complexity in the transactional database.

## When Partitioning Increases Migration Risk

Partitioning an existing production table can be significantly more complicated than creating a partitioned table from the beginning.

Potential migration work includes:

```text
Existing table
     │
     ▼
Create partitioned structure
     │
     ▼
Move / copy data
     │
     ▼
Rebuild indexes
     │
     ▼
Validate constraints
     │
     ▼
Synchronize writes
     │
     ▼
Cut over
```

Depending on the database engine and migration approach, this may involve:

- Long-running operations.
- Additional storage.
- Replication pressure.
- Locking.
- Increased WAL.
- Application coordination.
- Rollback complexity.

If the expected performance improvement is small, the migration risk may not be justified.

## When Operational Automation Is Not Ready

A partitioned system requires lifecycle management.

For time-based partitioning, automation typically needs to:

- Create future partitions.
- Verify boundaries.
- Monitor missing partitions.
- Archive expired data.
- Remove expired partitions.
- Validate storage.
- Handle failures.

If the team cannot reliably automate these tasks, partitioning introduces operational risk.

A database that depends on:

```text
"Someone needs to create next month's partition manually."
```

is not production-ready.

## When Backup and Recovery Become Too Complex

Partitioning changes the physical organization of data and therefore needs to be considered in:

- Backups.
- Point-in-time recovery.
- Replication.
- Restore testing.
- Archival.
- Disaster recovery.

If the partition strategy makes recovery procedures significantly harder without solving an important problem, the simpler design may be preferable.

A partitioned database is still one logical database system. Partitioning does not automatically provide:

- High availability.
- Disaster recovery.
- Fault isolation.
- Backup redundancy.

## When the Team Cannot Operate the Complexity

Database design is also an operational decision.

A technically elegant partition strategy can be a poor production design if the team cannot confidently:

- Diagnose partition-pruning failures.
- Manage partition lifecycle.
- Perform schema changes.
- Monitor partition health.
- Restore backups.
- Handle failed partition creation.
- Migrate partitions.
- Troubleshoot cross-partition queries.

Senior engineering decisions account for **organizational operational capacity**, not only theoretical database performance.

## Complexity Has a Real Cost

Partitioning adds a complexity budget.

| Area | Unpartitioned | Partitioned |
|---|---|---|
| Schema | Simpler | More complex |
| Index management | Simpler | More involved |
| Query planning | Simpler | Partition-aware |
| Retention | Row-level operations | Can be partition-level |
| Maintenance | Table-wide | Potentially scoped |
| Monitoring | Simpler | More granular |
| Migrations | Simpler | More complex |
| Automation | Lower | Higher |
| Debugging | Simpler | More complex |
| Operational risk | Lower | Higher |

The additional complexity is justified only when it produces corresponding value.

## A Better Alternative: Archive Old Data

If the main problem is historical data volume, archiving may be better than partitioning.

For example:

```text
Primary OLTP database
        │
        ├── Recent 90 days
        │
        ▼
Historical archive
        │
        ├── Object storage
        ├── Data warehouse
        └── Analytical store
```

This can keep the transactional system focused on operational data.

Archiving is especially attractive when:

- Historical data is rarely accessed.
- Retention is long.
- OLTP latency matters more than historical query latency.
- An analytical platform already exists.

## Decision Matrix

| Situation | Prefer Not to Partition | Consider Partitioning |
|---|---:|---:|
| Small table | Strongly | Rarely |
| Good indexes solve workload | Strongly | Rarely |
| Slow query caused by bad SQL | Strongly | Rarely |
| No partition-key predicates | Strongly | Rarely |
| Frequent full-table scans | Often | Only for lifecycle benefits |
| Very high growth | Not automatically | Yes, evaluate |
| Time-based retention | Sometimes | Strong candidate |
| Massive time-series data | Rarely | Strong candidate |
| Excessive partition count | Strongly | No |
| Tenant count is huge | Strongly | Only with bounded strategy |
| Single hot range | Often | Evaluate alternative strategy |
| Single DB capacity limit | Insufficient | May still be insufficient |
| Repeated cacheable reads | Often | Usually not primary solution |
| Read-heavy workload | Often | Depends |
| Analytical workload | Often | Usually separate workload |
| Operational team lacks automation | Strongly | No |
| Existing table migration is high-risk | Often | Only with strong justification |

## Production Evaluation Process

Before deciding not to partition, validate the decision with evidence.

### Measure the Current Workload

Capture:

- p50 latency.
- p95 latency.
- p99 latency.
- Query throughput.
- Rows scanned.
- Buffer reads.
- CPU.
- I/O.
- Storage growth.
- Index size.
- Maintenance duration.
- WAL generation.
- Replication lag.

### Inspect Query Plans

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, created_at
FROM orders
WHERE tenant_id = 42
ORDER BY created_at DESC
LIMIT 100;
```

Determine whether:

- Indexes are used.
- The planner estimates rows correctly.
- Too many rows are scanned.
- Sorting is expensive.
- I/O is the real bottleneck.

### Compare Alternatives

Evaluate at least:

```text
Query optimization
       │
       ├── Index changes
       ├── Query rewrites
       ├── Pagination improvements
       ├── Caching
       ├── Read replicas
       ├── Archival
       ├── Workload isolation
       └── Partitioning
```

Choose the smallest architectural change that solves the actual problem.

## Production Example

Suppose a PostgreSQL `orders` table has:

```text
Rows:           80 million
Storage:        120 GB
Growth:         1 million rows/month
Primary query:  tenant_id + status
Retention:      indefinite
```

The dominant query is:

```sql
SELECT id, status, created_at
FROM orders
WHERE tenant_id = 42
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 100;
```

The workload does not naturally require time-based lifecycle operations.

A composite index may be more appropriate:

```sql
CREATE INDEX orders_tenant_status_created_idx
ON orders (tenant_id, status, created_at DESC);
```

If benchmark results show acceptable latency and maintenance cost, partitioning by `created_at` would add complexity without solving the primary problem.

By contrast, consider:

```text
Rows:           10 billion
Growth:         500 million/month
Queries:        Primarily time ranges
Retention:      90 days
Deletes:        Extremely expensive
```

Time-based range partitioning becomes much more compelling because both query pruning and lifecycle management align with the same partition key.

## Beginner Mistakes

### "Millions of Rows Means Partitioning"

**Why it happens:** Engineers associate row count with performance.

**Why it is wrong:** Proper indexes and hardware can handle very large tables efficiently.

**Better approach:** Measure the workload and identify the bottleneck.

### "Partitioning Is Always Faster"

**Why it happens:** Partition pruning is associated with reduced scanning.

**Why it is wrong:** Queries that span many partitions may see little benefit.

**Better approach:** Benchmark representative queries.

### "Partitioning Replaces Indexes"

**Why it happens:** Both are perceived as performance features.

**Why it is wrong:** Partitioning reduces physical scope; indexes locate rows within that scope.

**Better approach:** Design both independently.

### "One Tenant Equals One Partition"

**Why it happens:** It appears to provide natural isolation.

**Why it is wrong:** High tenant counts can create excessive partition counts.

**Better approach:** Keep partition count bounded.

### "More Partitions Means Better Performance"

**Why it happens:** Smaller partitions appear easier to scan.

**Why it is wrong:** Excessive partitions create planning and operational overhead.

**Better approach:** Select a practical partition granularity.

### "Partition Now Because the Table Might Become Large"

**Why it happens:** Engineers optimize for hypothetical future problems.

**Why it is wrong:** It creates complexity before the benefit exists.

**Better approach:** Establish measurable thresholds and monitor growth.

## Production Pitfalls

| Pitfall | Result | Mitigation |
|---|---|---|
| Missing indexes | Slow queries inside partitions | Design partition-local indexes |
| No pruning | Many partitions scanned | Align queries with partition key |
| Too many partitions | Planning/management overhead | Bound partition count |
| Hot partition | Uneven write load | Evaluate key and workload distribution |
| Manual partition creation | Production failures | Automate lifecycle |
| Large migration | Locking / replication pressure | Use controlled migration strategy |
| Poor retention process | Data loss or storage growth | Automate and verify lifecycle |
| Ignored replicas | Replication problems | Test partition DDL and recovery |
| No restore testing | Recovery surprises | Perform regular DR tests |
| Cross-partition assumptions | Unexpected query cost | Benchmark broad queries |

## Interview Traps

### "Should every large table be partitioned?"

No.

Partitioning should be justified by workload, lifecycle, or maintenance requirements.

### "What is the biggest reason not to partition?"

There is no single universal reason. The strongest general argument is:

> **Partitioning adds complexity without sufficient measurable benefit.**

### "If a table has 1 billion rows, would you partition it?"

A strong answer should avoid giving an automatic yes.

Evaluate:

- Query patterns.
- Index effectiveness.
- Data distribution.
- Growth rate.
- Retention requirements.
- Partition-key suitability.
- Partition count.
- Maintenance costs.
- Database capacity.
- Operational complexity.

### "Can partitioning make performance worse?"

Yes.

Potential causes include:

- Planning overhead.
- Excessive partitions.
- Poor pruning.
- Cross-partition queries.
- Additional indexes.
- Poor partition-key distribution.
- Hot partitions.

### "What should you do before partitioning?"

A strong sequence is:

```text
Measure
  ↓
Inspect execution plans
  ↓
Optimize queries
  ↓
Optimize indexes
  ↓
Evaluate caching / replicas / archival
  ↓
Evaluate partitioning
  ↓
Benchmark
  ↓
Deploy only if justified
```

## Senior Engineering Heuristics

Use these heuristics when evaluating a partitioning proposal:

### Prefer Simplicity When Performance Is Already Acceptable

A simpler system is usually easier to:

- Operate.
- Debug.
- Migrate.
- Back up.
- Restore.
- Scale.

Do not exchange simplicity for theoretical performance.

### Partition for a Specific Reason

A good design should be able to answer:

> "We partition this table because..."

with a concrete statement such as:

- "Time-range queries need pruning."
- "Retention requires removing old data efficiently."
- "Maintenance on the full table has become operationally expensive."

Avoid:

> "The table is large."

### Make Complexity Measurable

Document:

- Expected latency improvement.
- Expected maintenance reduction.
- Partition count.
- Partition growth.
- Operational tasks.
- Failure scenarios.
- Rollback strategy.

### Revisit the Decision as Workloads Change

A table that should not be partitioned today may become a good candidate later.

Monitor:

```text
Table size
Growth rate
Query latency
Rows scanned
Index size
Maintenance time
Retention cost
Storage utilization
```

Partitioning should be treated as an architectural decision that can be revisited when evidence changes.

## Production Checklist

Before explicitly deciding **not** to partition:

- [ ] The current workload has been measured.
- [ ] Slow queries have been analyzed with execution plans.
- [ ] Existing indexes have been reviewed.
- [ ] Query rewrites have been considered.
- [ ] Table growth has been quantified.
- [ ] Retention requirements have been evaluated.
- [ ] Full-table and cross-partition workload characteristics have been considered.
- [ ] Partition-key candidates have been evaluated.
- [ ] Future partition count has been estimated.
- [ ] Hot-partition risks have been considered.
- [ ] Caching has been evaluated where appropriate.
- [ ] Read replicas have been evaluated where appropriate.
- [ ] Archival has been evaluated where appropriate.
- [ ] Analytical workloads have been separated where appropriate.
- [ ] Sharding has been considered only if single-database capacity is the actual constraint.
- [ ] Operational automation requirements have been evaluated.
- [ ] Backup and recovery implications have been considered.
- [ ] Migration complexity has been assessed.
- [ ] The simpler alternative meets the required performance and reliability targets.
- [ ] The decision and measurable thresholds for revisiting it are documented.

## Key Takeaways

- **Do not partition a table simply because it is large; partition only when measurable workload, lifecycle, or maintenance requirements justify the added complexity.**
- **If indexes, query optimization, caching, replicas, or archival solve the actual problem, prefer those simpler solutions.**
- **Partitioning is a poor fit when important queries do not constrain the partition key, routinely span most partitions, or would require an excessive partition count.**
- **Consider operational cost—including migrations, automation, monitoring, backups, recovery, and debugging—as part of the partitioning decision.**
- **Revisit the decision as table growth, query latency, retention cost, and maintenance requirements change rather than partitioning prematurely.**