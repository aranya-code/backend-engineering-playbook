# README

## Overview

Partitioning divides a large logical SQL table into smaller physical partitions while preserving a single logical table interface for application queries.

The primary goals are to reduce the amount of data scanned for selective queries, isolate maintenance operations, improve data lifecycle management, and make very large tables easier to operate.

Partitioning is most effective when the partition strategy matches the workload. It is not a universal replacement for indexing, query optimization, caching, read replicas, or sharding.

This section builds partitioning knowledge from fundamentals through production design, with PostgreSQL as the primary reference implementation.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Partitioning Introduction](./01-%20Partitioning%20Introduction.md) | Partitioning fundamentals, architecture, and core terminology |
| 02 | [02- Why Partition Tables](./02-%20Why%20Partition%20Tables.md) | Reasons to partition and the problems it can solve |
| 03 | [03- Partitioning vs Sharding](./03-%20Partitioning%20vs%20Sharding.md) | Differences between database partitioning and sharding |
| 04 | [04- Range Partitioning](./04-%20Range%20Partitioning.md) | Range-based partition design and implementation |
| 05 | [05- List Partitioning](./05-%20List%20Partitioning.md) | List-based partition design and suitable workloads |
| 06 | [06- Hash Partitioning](./06-%20Hash%20Partitioning.md) | Hash-based distribution and workload considerations |
| 07 | [07- Composite Partitioning](./07-%20Composite%20Partitioning.md) | Multi-level partitioning strategies |
| 08 | [08- Partition Keys](./08-%20Partition%20Keys.md) | Selecting effective partition keys |
| 09 | [09- Partition Pruning](./09-%20Partition%20Pruning.md) | How pruning reduces unnecessary partition scans |
| 10 | [10- Partition Maintenance](./10-%20Partition%20Maintenance.md) | Creation, indexing, retention, and lifecycle automation |
| 11 | [11- Partitioning Large Tables](./11-%20Partitioning%20Large%20Tables.md) | Designing and migrating very large tables |
| 12 | [12- Partitioning by Date](./12-%20Partitioning%20by%20Date.md) | Time-based partitioning patterns |
| 13 | [13- Partitioning by Tenant](./13-%20Partitioning%20by%20Tenant.md) | Multi-tenant partitioning strategies |
| 14 | [14- Choosing a Partition Strategy](./14-%20Choosing%20a%20Partition%20Strategy.md) | Framework for selecting a partitioning approach |
| 15 | [15- When to Partition](./15-%20When%20to%20Partition.md) | Conditions that justify partitioning |
| 16 | [16- When Not to Partition](./16-%20When%20Not%20to%20Partition.md) | Cases where partitioning adds unnecessary complexity |
| 17 | [17- Partitioning Tradeoffs](./17-%20Partitioning%20Tradeoffs.md) | Performance, scalability, and operational tradeoffs |
| 18 | [18- Common Partitioning Mistakes](./18-%20Common%20Partitioning%20Mistakes.md) | Common design and production failures |

## Partitioning at a Glance

A partitioned table consists of:

```text
Logical Table
     │
     ▼
Partitioned Parent
     │
     ├── Partition A
     ├── Partition B
     ├── Partition C
     └── Partition D
```

Applications normally query the logical parent:

```sql
SELECT *
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

The database optimizer can use the partition bounds to determine which physical partitions may contain matching rows.

The key optimization is **partition pruning**:

```text
Query
  │
  ▼
Partitioned Table
  │
  ▼
Analyze partition predicate
  │
  ├── Partition A → skip
  ├── Partition B → scan
  ├── Partition C → skip
  └── Partition D → skip
```

## Partitioning vs Sharding

Partitioning and sharding are related but solve different scaling problems.

| Aspect | Partitioning | Sharding |
|---|---|---|
| Physical scope | Usually within one database system | Across multiple database instances |
| Application complexity | Usually lower | Higher |
| Cross-partition queries | Database-managed | Often application/database-router managed |
| Scaling database compute | Limited by database instance | Can scale across instances |
| Operational complexity | Moderate | High |
| Typical use | Large tables, pruning, lifecycle management | Database capacity limits |
| Example | Monthly event partitions | Tenant groups distributed across databases |

Partitioning should generally be considered before sharding when a single database can still provide sufficient compute, storage, and I/O capacity.

## Partitioning Strategies

The main partitioning strategies covered in this section are:

| Strategy | Partition Key | Strong Use Case |
|---|---|---|
| Range | Ordered value or interval | Time-series data and retention |
| List | Discrete values | Small stable categories |
| Hash | Hash of a key | Even distribution |
| Composite | Multiple strategies | High-volume workloads requiring multiple dimensions |

### Range Partitioning

Rows are assigned according to value ranges.

```text
events
├── events_2026_07
├── events_2026_08
└── events_2026_09
```

A common PostgreSQL design is:

```sql
CREATE TABLE events (
    id          BIGINT NOT NULL,
    tenant_id   BIGINT NOT NULL,
    event_type  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL,
    payload     JSONB NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2026_08
PARTITION OF events
FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
```

Range partitioning is particularly effective when queries frequently constrain the partition key and when data has a natural lifecycle.

### List Partitioning

Rows are assigned to explicitly defined values.

```sql
CREATE TABLE orders (
    id          BIGINT NOT NULL,
    region      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL
) PARTITION BY LIST (region);

CREATE TABLE orders_us
PARTITION OF orders
FOR VALUES IN ('us');

CREATE TABLE orders_eu
PARTITION OF orders
FOR VALUES IN ('eu');

CREATE TABLE orders_apac
PARTITION OF orders
FOR VALUES IN ('apac');
```

List partitioning works best for a relatively small and stable set of categories.

### Hash Partitioning

Rows are distributed according to a hash of the partition key.

```sql
CREATE TABLE events (
    id          BIGINT NOT NULL,
    tenant_id   BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL
) PARTITION BY HASH (tenant_id);

CREATE TABLE events_p0
PARTITION OF events
FOR VALUES WITH (MODULUS 8, REMAINDER 0);

CREATE TABLE events_p1
PARTITION OF events
FOR VALUES WITH (MODULUS 8, REMAINDER 1);
```

Hash partitioning is useful when the primary requirement is relatively even distribution rather than range-based pruning or lifecycle management.

### Composite Partitioning

Composite partitioning combines multiple partitioning levels.

A common architecture is:

```text
RANGE(created_at)
       │
       ├── August
       │      ├── HASH(tenant_id) → P0
       │      ├── HASH(tenant_id) → P1
       │      └── HASH(tenant_id) → P2
       │
       └── September
              ├── HASH(tenant_id) → P0
              ├── HASH(tenant_id) → P1
              └── HASH(tenant_id) → P2
```

This can be useful for high-volume multi-tenant event systems, but it increases partition count and operational complexity.

## Why Partition Tables

Partitioning should be driven by a measurable engineering requirement.

Typical reasons include:

- Large-table query performance.
- Partition pruning.
- Time-based retention.
- Fast removal of historical data.
- Maintenance isolation.
- Managing very large indexes.
- Controlling data growth.
- Reducing the working set for common queries.

Partitioning is particularly valuable when the same column naturally represents both:

1. A common query predicate.
2. A lifecycle boundary.

Time is a strong example:

```text
created_at
    │
    ├── Query filtering
    └── Retention boundary
```

## Choosing a Partition Key

A partition key should be selected from workload characteristics rather than simply from schema semantics.

Evaluate:

- Query predicates.
- Query selectivity.
- Data distribution.
- Write distribution.
- Retention requirements.
- Archival requirements.
- Expected growth.
- Late-arriving data.
- Partition count.
- Operational complexity.

A useful decision process is:

```text
Workload
   │
   ├── Time-range queries?
   │        │
   │        └── Consider RANGE(time)
   │
   ├── Stable small categories?
   │        │
   │        └── Consider LIST(category)
   │
   ├── Need even distribution?
   │        │
   │        └── Consider HASH(key)
   │
   └── Multiple independent requirements?
            │
            └── Consider COMPOSITE
```

## Partition Pruning

Partition pruning is one of the primary performance benefits of partitioning.

For example:

```sql
SELECT id, event_type
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

If the table is partitioned by `created_at`, the optimizer can eliminate partitions whose ranges cannot contain matching rows.

Always verify pruning with execution plans:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, event_type
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

Partitioning does not guarantee pruning. Query shape, partition bounds, parameterization, database version, and optimizer behavior all matter.

## Partitioning Large Tables

Partitioning becomes more valuable as tables become operationally difficult to manage.

A large table should be evaluated using more than row count:

| Metric | Why It Matters |
|---|---|
| Total size | Storage and I/O pressure |
| Index size | Maintenance and cache pressure |
| Growth rate | Capacity planning |
| Query latency | User-facing performance |
| Rows scanned | Query efficiency |
| Retention volume | Lifecycle operations |
| Write rate | Hot partition risk |
| Partition count | Operational complexity |

A table containing billions of rows is not automatically a partitioning candidate. A smaller table with extreme retention or maintenance requirements may benefit more.

## Partitioning by Date

Date-based partitioning is one of the most common production strategies.

Typical granularity:

| Granularity | Typical Use |
|---|---|
| Year | Low-volume historical data |
| Month | Common default for large application tables |
| Week | High-volume workloads |
| Day | Very high-volume time-series workloads |
| Hour | Specialized ingestion systems |

Avoid choosing a granularity based only on intuition.

For example, daily partitions over ten years produce approximately:

```text
10 × 365 = 3,650 partitions
```

That may be unnecessarily complex.

Partition sizing should be based on:

- Data volume.
- Query patterns.
- Retention operations.
- Maintenance duration.
- Database capabilities.
- Expected growth.

## Partitioning by Tenant

Tenant-based partitioning can be useful when tenant identity strongly determines access patterns.

For example:

```sql
SELECT *
FROM events
WHERE tenant_id = 42
ORDER BY created_at DESC
LIMIT 100;
```

However, one partition per tenant can become problematic at high tenant counts.

For multi-tenant systems, evaluate:

- Tenant cardinality.
- Tenant size distribution.
- Noisy-neighbor behavior.
- Tenant-specific retention.
- Data isolation requirements.
- Backup requirements.
- Hash partitioning.
- Composite partitioning.
- Sharding.

Partition placement is not an authorization boundary.

## Partition Maintenance

Partitioning introduces an ongoing lifecycle.

For time-based partitioning:

```text
Before boundary
      │
      ▼
Create future partition
      │
      ▼
Create/validate indexes
      │
      ▼
Ingest data
      │
      ▼
Monitor partition
      │
      ▼
Retention threshold reached
      │
      ▼
Archive / detach / remove
```

Partition maintenance should be automated and idempotent.

Automation should handle:

- Future partition creation.
- Index provisioning.
- Retention.
- Monitoring.
- Missing partition detection.
- Failed DDL.
- Capacity thresholds.

A production system should not depend on an engineer manually creating next month's partition.

## Partition Lifecycle

A robust lifecycle may look like:

```text
                    Partition Lifecycle

        ┌──────────────┐
        │   Planned    │
        └──────┬───────┘
               │ Create
               ▼
        ┌──────────────┐
        │    Active    │
        └──────┬───────┘
               │ Retention threshold
               ▼
        ┌──────────────┐
        │   Archived   │
        └──────┬───────┘
               │ Recovery window ends
               ▼
        ┌──────────────┐
        │    Removed   │
        └──────────────┘
```

The exact lifecycle depends on the application's retention, compliance, and recovery requirements.

## Partitioning Tradeoffs

Partitioning provides benefits but introduces complexity.

| Benefit | Tradeoff |
|---|---|
| Partition pruning | Requires appropriate query predicates |
| Easier retention | Requires lifecycle automation |
| Smaller physical objects | More objects to manage |
| Maintenance isolation | More operational procedures |
| Large-table organization | More complex schema management |
| Potential performance improvements | Not guaranteed for every query |
| Better lifecycle boundaries | Cross-partition operations may remain expensive |

The correct question is not:

> "Can this table be partitioned?"

It is:

> "Does partitioning solve a measured problem better than simpler alternatives?"

## When to Partition

Partitioning is a strong candidate when several of the following are true:

- The table is large or growing rapidly.
- Queries frequently filter on a suitable partition key.
- Data has a natural lifecycle.
- Historical data is routinely removed or archived.
- Maintenance on the full table is becoming expensive.
- Index size is becoming operationally significant.
- Query performance benefits from reducing the scanned data set.
- The partition count can remain operationally manageable.

Before implementation, establish measurable targets such as:

```text
Current:
p99 query latency      = 900 ms
retention cleanup      = 45 min
table size             = 4 TB

Target:
p99 query latency      < 250 ms
retention cleanup      < 5 min
maintenance impact     = acceptable
```

## When Not to Partition

Avoid partitioning when:

- The table is small and stable.
- Queries rarely constrain the proposed partition key.
- The table does not have meaningful lifecycle boundaries.
- Partition count would become excessive.
- Indexing already solves the workload.
- The primary bottleneck is elsewhere.
- The operational complexity exceeds the expected benefit.

For many workloads, a well-designed index is simpler and more effective.

## Partitioning vs Indexing

Partitioning and indexes are complementary rather than interchangeable.

| Concern | Index | Partitioning |
|---|---|---|
| Locate rows efficiently | Excellent | Sometimes |
| Reduce partitions scanned | No | Yes |
| Lifecycle management | Limited | Strong |
| Remove historical data | Expensive row operations | Partition-level operations |
| Reduce index working set | Limited | Can help |
| Query performance | Often primary optimization | Workload-dependent |
| Operational complexity | Lower | Higher |

A common production design is:

```text
Partition by created_at
+
Index on tenant_id, created_at
```

This allows partition pruning to reduce the physical search space while indexes efficiently locate rows within relevant partitions.

## Partitioning vs Caching

Caching addresses repeated computation or data retrieval.

Partitioning changes physical database organization.

```text
API Request
    │
    ▼
Redis
    │
    ├── Cache hit ───────► Response
    │
    └── Cache miss
             │
             ▼
         PostgreSQL
             │
             ▼
       Partition pruning
             │
             ▼
           Index
```

A system can use both.

Do not introduce partitioning merely because an endpoint is slow if the actual bottleneck is repeated identical reads that would be better served by caching.

## Partitioning vs Read Replicas

Read replicas address read capacity and workload isolation.

Partitioning addresses data organization and potentially query and lifecycle efficiency.

They can be combined:

```text
Application
    │
    ├── Writes ──────► Primary
    │
    └── Reads ───────► Replica
                          │
                          ▼
                    Partitioned Table
```

Neither mechanism automatically solves all database scaling problems.

## Partitioning vs Sharding

Partitioning usually keeps data within one database system.

Sharding distributes data across separate database instances.

```text
Partitioning

             Database
          ┌────┬────┬────┐
          │ P1 │ P2 │ P3 │
          └────┴────┴────┘


Sharding

       ┌─────────────┐
       │ Router/App  │
       └──────┬──────┘
              │
       ┌──────┴──────┐
       ▼             ▼
   Database A    Database B
    P1 / P2       P3 / P4
```

Consider sharding when a single database instance becomes the fundamental capacity boundary.

## Common Partitioning Mistakes

Common failures include:

- Choosing a partition key without analyzing queries.
- Creating one partition per high-cardinality tenant.
- Creating thousands of unnecessarily small partitions.
- Creating partitions that are too large to provide useful isolation.
- Assuming partitioning automatically improves performance.
- Failing to verify partition pruning.
- Forgetting indexes on new partitions.
- Failing to automate future partition creation.
- Ignoring hot partitions.
- Ignoring data skew.
- Ignoring late-arriving events.
- Using unstable business attributes for list partitioning.
- Treating partition placement as a security mechanism.
- Performing large repartitioning migrations without a cutover plan.
- Ignoring replication and backup impact.
- Assuming partitioning replaces sharding.
- Partitioning before measuring the actual bottleneck.

## Production Considerations

### Performance

Measure partitioning using realistic production-like workloads.

Monitor:

- Query latency.
- Rows scanned.
- Buffer hits and reads.
- CPU.
- I/O.
- Query planning time.
- Partition count.
- Partition sizes.

Use execution plans rather than assumptions:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id
FROM events
WHERE tenant_id = 42
  AND created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

### Scalability

Project partition growth before deployment.

For example:

```text
Monthly partitions
×
Expected retention horizon
×
Future growth
```

Also estimate:

- Number of indexes.
- Total index storage.
- DDL frequency.
- Maintenance workload.
- Monitoring object count.

### High Availability

Test partition operations under production concurrency.

Evaluate:

- Lock acquisition.
- Blocking queries.
- Replication lag.
- WAL generation.
- Failover behavior.
- Partition automation failure.

Partition DDL is part of the production availability model.

### Reliability

Partition automation should be:

- Idempotent.
- Retryable.
- Observable.
- Tested.
- Alerted.

A missing partition should be detected before application writes reach the boundary.

### Disaster Recovery

Validate that:

- Backups contain partitioned data.
- Partition definitions are recoverable.
- Restore procedures recreate the expected structure.
- Retention jobs do not conflict with recovery requirements.
- Archived partitions remain recoverable for their required lifetime.

### Security

Partitioning should not be considered an access-control mechanism.

Continue to enforce:

- Authentication.
- Authorization.
- Tenant checks.
- Database permissions.
- Row-level security where appropriate.
- Input validation.

Physical row placement should never determine whether an API request is authorized.

### Cost

Evaluate both infrastructure and engineering cost.

Partitioning can increase:

- Physical object count.
- Index storage.
- DDL operations.
- Monitoring complexity.
- Backup complexity.
- Migration complexity.

The benefit should be measurable enough to justify that additional complexity.

## Django and Backend Application Considerations

Django and similar ORMs can hide the SQL generated by application code.

For performance-critical queries, inspect:

```python
queryset = (
    Event.objects
    .filter(
        tenant_id=42,
        created_at__gte=start,
        created_at__lt=end,
    )
    .order_by("-created_at")[:100]
)

print(queryset.query)
```

The important question is whether the generated SQL includes predicates that allow the database to prune partitions.

The application should generally query the logical parent table rather than hard-coding physical partition names.

Partition management should remain a database/infrastructure responsibility unless the application's architecture explicitly requires otherwise.

## Operational Workflow

A production rollout should typically follow this sequence:

```text
Measure workload
      │
      ▼
Identify bottleneck
      │
      ▼
Design partition key
      │
      ▼
Estimate partition count
      │
      ▼
Benchmark realistic workload
      │
      ▼
Design indexes
      │
      ▼
Design lifecycle automation
      │
      ▼
Test migration and DDL locking
      │
      ▼
Validate replication and backups
      │
      ▼
Deploy incrementally
      │
      ▼
Monitor production behavior
```

For an existing very large table, migration complexity can be substantial. Depending on availability requirements, a migration may require backfill jobs, dual writes, validation, controlled cutover, and rollback procedures.

## Decision Matrix

| Requirement | Recommended Direction |
|---|---|
| Time-based queries and retention | Range partitioning |
| Small stable categories | List partitioning |
| Even distribution by identifier | Hash partitioning |
| Time + tenant workload | Consider composite partitioning |
| Repeated identical reads | Consider caching |
| Query lookup efficiency | Start with indexing |
| Read capacity limitation | Consider replicas |
| Single database capacity exhausted | Consider sharding |
| Small stable table | Usually avoid partitioning |
| Very high partition count | Reconsider partition granularity |

## Interview Traps

### "Partitioning makes queries faster."

Not necessarily.

Partitioning can improve performance when it enables pruning or reduces the amount of data that must be processed. Queries that do not constrain the partition key may still touch many or all partitions.

### "Partitioning removes the need for indexes."

False.

Indexes are still frequently required inside partitions.

A common design is:

```text
Partition pruning
      +
Partition-local indexes
      =
Efficient query execution
```

### "More partitions are always better."

False.

Too many partitions increase metadata, planning, DDL, monitoring, and maintenance overhead.

### "Hash partitioning solves every distribution problem."

False.

Hashing can distribute rows more evenly, but it does not automatically solve query locality, lifecycle management, hot tenants, or application-level scaling.

### "Partitioning is the same as sharding."

False.

Partitioning generally organizes data within a database system. Sharding distributes data across separate database instances or nodes.

### "A partition is a security boundary."

False.

Partition placement does not replace authorization or tenant isolation controls.

## Practical Design Example

Consider a multi-tenant event ingestion service:

```text
FastAPI
   │
   ▼
Kafka
   │
   ▼
Consumer Workers
   │
   ▼
PostgreSQL
   │
   ▼
events
   │
   ├── 2026-08
   │     ├── tenant hash 0
   │     ├── tenant hash 1
   │     └── ...
   │
   └── 2026-09
         ├── tenant hash 0
         ├── tenant hash 1
         └── ...
```

Potential requirements:

- Very high event volume.
- Queries primarily filter by tenant and time.
- Data retained for a fixed period.
- Continuous ingestion.
- Large historical data volume.

A composite strategy may therefore be justified:

```text
RANGE(created_at)
        │
        ▼
HASH(tenant_id)
```

But it should only be adopted after verifying that the additional partitioning level produces measurable benefits over simpler alternatives.

## Partitioning Review Checklist

Before approving a partitioned production table:

- [ ] Workload has been measured.
- [ ] Primary bottleneck has been identified.
- [ ] Partition key matches important query predicates.
- [ ] Partition key supports required lifecycle operations.
- [ ] Data distribution has been analyzed.
- [ ] Write hot spots have been evaluated.
- [ ] Partition count has been projected.
- [ ] Partition size has been estimated.
- [ ] Index strategy has been designed.
- [ ] Partition pruning has been verified.
- [ ] Cross-partition queries have been benchmarked.
- [ ] Future partition creation is automated.
- [ ] New partition indexes are handled automatically.
- [ ] Retention automation is idempotent.
- [ ] Late-arriving data has an explicit policy.
- [ ] NULL and unmatched partition-key values have an explicit policy.
- [ ] Locking behavior has been tested.
- [ ] Replication impact has been measured.
- [ ] Backup and restore procedures have been tested.
- [ ] Disaster recovery procedures include partition lifecycle.
- [ ] Security does not depend on partition placement.
- [ ] Migration and rollback procedures are documented.
- [ ] Partition ownership is defined.
- [ ] Monitoring and alerting are implemented.
- [ ] Success criteria are measurable.

## Key Takeaways

- **Partitioning organizes a large logical table into smaller physical units and is most valuable when it improves pruning, lifecycle management, or maintenance.**
- **Range, list, hash, and composite partitioning solve different workload problems; the partition key should be selected from real query and data characteristics.**
- **Partitioning complements indexes, caching, replicas, and sharding rather than replacing them.**
- **Production partitioning requires automated creation, indexing, retention, monitoring, backup, replication, and failure handling.**
- **Measure the workload and validate execution plans before introducing partitioning; additional database complexity must have a measurable engineering benefit.**