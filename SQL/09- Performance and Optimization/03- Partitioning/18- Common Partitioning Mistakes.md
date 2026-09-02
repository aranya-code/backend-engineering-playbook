# 18- Common Partitioning Mistakes

## Overview

Partitioning can improve query performance and simplify the lifecycle of very large tables, but an incorrect design can make a database harder to operate without delivering measurable benefits.

Most partitioning failures are not caused by misunderstanding the syntax. They result from architectural mistakes such as choosing a partition key that does not match the workload, creating too many partitions, assuming pruning will always occur, or failing to automate partition lifecycle management.

A production partitioning review should therefore evaluate the complete lifecycle:

```text
                    Partitioning Design
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Queries          Writes          Lifecycle
          │                │                │
     Pruning          Hot spots       Retention
     Indexes          Routing         Creation
     Plans            Distribution    Removal
          │                │                │
          └────────────────┼────────────────┘
                           │
                    Operational Cost
```

The goal is not to maximize the number of partitions or achieve the most sophisticated schema. The goal is to create a physical layout that improves the application's real workload while remaining reliable and operationally manageable.

## Choosing the Wrong Partition Key

The partition key determines how rows are distributed and whether queries can benefit from partition pruning.

A common mistake is choosing a column because it appears important in the schema rather than because it matches actual access patterns.

For example:

```sql
CREATE TABLE events (
    id          BIGINT NOT NULL,
    tenant_id   BIGINT NOT NULL,
    event_type  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL,
    payload     JSONB NOT NULL
) PARTITION BY RANGE (created_at);
```

This can be appropriate when most queries look like:

```sql
SELECT *
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

But if most production queries are:

```sql
SELECT *
FROM events
WHERE tenant_id = 42
ORDER BY created_at DESC
LIMIT 100;
```

and almost never constrain `created_at`, time-based partitioning may provide limited pruning benefit.

### Better approach

Analyze:

- Query predicates.
- Data retention requirements.
- Data distribution.
- Write distribution.
- Partition growth.
- Operational boundaries.

The partition key should be justified by workload evidence.

## Partitioning by a High-Cardinality Column Without a Plan

Tenant IDs, user IDs, device IDs, and similar identifiers often have high cardinality.

Creating one partition per value can produce an operationally expensive schema:

```text
tenant_1
tenant_2
tenant_3
...
tenant_100000
```

This can result in:

- Excessive partition count.
- Large amounts of metadata.
- Complex migrations.
- Difficult monitoring.
- More expensive planning.
- Complicated partition lifecycle management.

High cardinality does not automatically make a column a good partition key.

If tenant isolation is the primary requirement, hash partitioning or a higher-level partitioning strategy may be more appropriate.

## Creating Too Many Partitions

Fine-grained partitioning can appear attractive because it provides precise pruning.

For example:

```text
One partition per day
```

may initially seem reasonable.

But:

```text
10 years × 365 days ≈ 3,650 partitions
```

The same strategy may become significantly more complex than necessary.

Partition count affects:

- Query planning.
- Schema metadata.
- Index management.
- Statistics management.
- Backup and restore operations.
- Monitoring.
- DDL operations.
- Automation.

The correct granularity depends on the database engine and workload.

Do not choose daily, hourly, or per-tenant partitions without projecting the resulting partition count over the expected lifetime of the system.

## Creating Partitions That Are Too Large

The opposite mistake is making partitions so large that partitioning provides little practical benefit.

For example:

```text
10 TB logical table

Partition A → 5 TB
Partition B → 5 TB
```

If typical queries touch both partitions, pruning does not significantly reduce the search space.

Large partitions can also reduce the benefits of:

- Retention operations.
- Maintenance isolation.
- Index management.
- Parallel operational workflows.

Partition sizing should balance:

- Query pruning.
- Maintenance duration.
- Partition count.
- Data growth.
- Retention boundaries.

## Assuming Partitioning Automatically Improves Performance

Partitioning is not inherently a performance optimization.

Consider:

```sql
SELECT *
FROM orders
WHERE customer_email = 'customer@example.com';
```

If the table is partitioned by:

```text
created_at
```

and the query does not constrain `created_at`, the database may need to inspect many partitions.

Partitioning cannot compensate for a missing index or poorly designed query.

A better optimization sequence is often:

```text
Slow query
   │
   ▼
Measure
   │
   ▼
EXPLAIN / EXPLAIN ANALYZE
   │
   ▼
Check query + indexes
   │
   ├── Fix query
   ├── Add/change index
   └── Consider partitioning
```

Partitioning should be introduced when it solves a demonstrated access or lifecycle problem.

## Assuming Partition Pruning Always Occurs

A partitioned table does not guarantee that every query will prune partitions.

Pruning depends on whether the optimizer can determine which partitions can contain matching rows.

For example:

```sql
SELECT *
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

is much more pruning-friendly than a query that obscures the partition key through an expression or otherwise prevents the optimizer from narrowing the partition set.

Always inspect representative plans:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, event_type
FROM events
WHERE created_at >= TIMESTAMPTZ '2026-08-01'
  AND created_at < TIMESTAMPTZ '2026-09-01';
```

Do not infer pruning from the table definition alone.

## Ignoring Query Patterns

A partition strategy should be designed around the workload, not around the table definition.

Consider a table with:

```text
tenant_id
created_at
region
status
```

Possible partition strategies include:

| Strategy | Strong Fit |
|---|---|
| Range by `created_at` | Time-range queries and retention |
| List by `region` | Small, stable regional categories |
| Hash by `tenant_id` | Even tenant distribution |
| Composite time + hash | High-volume multi-tenant time-series workloads |

The right strategy depends on how the application actually accesses and manages the data.

## Ignoring Data Lifecycle

One of the strongest reasons to partition is lifecycle management.

Suppose the application retains audit events for 180 days.

Without partitioning:

```sql
DELETE FROM audit_events
WHERE created_at < NOW() - INTERVAL '180 days';
```

A very large delete can generate substantial work involving:

- Row deletion.
- Index maintenance.
- WAL.
- Vacuum.
- Locking considerations.
- Replication traffic.
- Table and index bloat.

With time-based partitions, expired data can often be removed at partition granularity.

The mistake is not partitioning when retention is one of the dominant operational requirements.

## Failing to Automate Future Partitions

A time-partitioned table needs future partitions.

Consider:

```text
Current date: August 31

Existing:
orders_2026_08

Next:
orders_2026_09  ← missing
```

A new insert may fail because no partition accepts the row.

Production systems should create partitions ahead of time.

A typical lifecycle is:

```text
Scheduled automation
        │
        ▼
Check future horizon
        │
        ▼
Create missing partitions
        │
        ▼
Create required indexes
        │
        ▼
Validate
        │
        ▼
Emit monitoring signal
```

The automation should be idempotent so that retries are safe.

## Treating Partition Creation as a Manual Task

Manual partition creation is fragile.

It creates a dependency on an engineer remembering to execute DDL before a boundary is reached.

This is especially dangerous for:

- Continuous ingestion.
- Kafka consumers.
- Celery workers.
- High-volume APIs.
- Scheduled batch workloads.

Partition lifecycle should be part of infrastructure and operational automation rather than an undocumented runbook step.

## Forgetting Indexes on New Partitions

Partitioned tables frequently require indexes on individual partitions.

A common failure mode is:

```text
Existing partitions
├── index
├── index
└── index

New partition
└── no expected index
```

Queries may therefore perform differently as data moves into newer partitions.

Automate index creation and validate new partitions after creation.

## Assuming Parent Indexes Solve Every Operational Problem

Database-specific partitioned-index behavior matters.

A senior engineer should understand whether an index defined on the partitioned parent:

- Automatically propagates to partitions.
- Creates corresponding partition-local indexes.
- Supports the required constraint semantics.
- Can be created without unacceptable locking.
- Is automatically inherited by future partitions.

These details differ between database engines and versions.

Always verify behavior against the actual database version used in production.

## Ignoring Index Storage Multiplication

Suppose a partitioned table has:

```text
100 partitions
```

and each partition has:

```text
5 indexes
```

That is approximately:

```text
500 physical indexes
```

The logical schema may appear simple while the physical object count is large.

Every index consumes:

- Storage.
- Build time.
- Write maintenance.
- Monitoring overhead.
- Backup resources.

Index design must therefore be evaluated at the partitioned-table level.

## Ignoring Hot Partitions

Range partitioning can concentrate writes into the newest partition.

For example:

```text
orders_2026_06 → 1%
orders_2026_07 → 2%
orders_2026_08 → 97%
```

This is expected for time-based workloads but can become a bottleneck if the workload is extremely write-heavy.

Partitioning does not automatically distribute concurrent writes evenly.

When write distribution is the primary problem, evaluate:

- Hash partitioning.
- Composite partitioning.
- Sharding.
- Application-level workload distribution.

Do not assume range partitioning solves write scaling.

## Using Too Many Composite Partitioning Levels

Composite partitioning can be powerful:

```text
RANGE(created_at)
    │
    ├── HASH(tenant_id)
    ├── HASH(tenant_id)
    └── ...
```

But every additional partitioning dimension increases operational complexity.

Potential consequences include:

- Large partition counts.
- More complex DDL.
- More complicated query plans.
- More complicated retention automation.
- More difficult troubleshooting.

Use composite partitioning only when the workload requires the additional dimension.

## Partitioning by Unstable Business Values

List partitioning can be useful for a small, stable set of categories.

For example:

```text
region = us
region = eu
region = apac
```

It becomes problematic when the values change frequently:

```text
customer_tier
campaign_id
temporary_status
dynamic_category
```

Every new category may require a new partition or changes to partition definitions.

A partition key should generally represent a stable physical organization boundary rather than a rapidly changing business attribute.

## Using List Partitioning for High-Cardinality Data

List partitioning is not a replacement for arbitrary filtering.

This is risky:

```text
PARTITION BY LIST (customer_id)
```

when the system has thousands or millions of customers.

List partitioning is generally more appropriate when the partition values are:

- Relatively few.
- Stable.
- Operationally meaningful.
- Useful for routing or lifecycle management.

For large cardinalities, hash partitioning or another strategy may be more appropriate.

## Ignoring NULL Values and Default Partitions

Partitioning designs must account for values that do not match expected boundaries.

For example:

```sql
created_at IS NULL
```

may not fit normal time-range partitions.

A default partition can provide a safety mechanism in some designs:

```sql
CREATE TABLE events_default
PARTITION OF events DEFAULT;
```

However, a default partition can also hide application or partition-management errors.

A senior design should explicitly decide:

- Whether NULL is valid.
- Whether a default partition is needed.
- How unmatched rows are detected.
- How data is moved into the correct partition.

A default partition should not become a permanent dumping ground.

## Ignoring Partition Boundary Errors

Time boundaries are easy to get wrong.

For example:

```text
Partition A:
[2026-08-01, 2026-09-01)

Partition B:
[2026-09-01, 2026-10-01)
```

Using half-open ranges makes boundaries explicit.

Production systems should define and test:

- Time zone behavior.
- Inclusive/exclusive boundaries.
- Daylight-saving transitions where relevant.
- Timestamp precision.
- Application serialization formats.

For distributed systems, standardizing on UTC is generally the safest operational approach.

## Partitioning on the Wrong Time Column

A table may contain several timestamps:

```text
created_at
updated_at
processed_at
occurred_at
```

Choosing the wrong one can undermine both pruning and retention.

For example, if retention is based on event occurrence but the table is partitioned by processing time, late-arriving events may land in unexpected partitions.

Choose the timestamp based on the actual lifecycle and query semantics.

## Ignoring Late-Arriving Data

Time-based systems often receive delayed events.

For example:

```text
Event occurred:
2026-08-10

Event received:
2026-08-15
```

If partitioning is based on `occurred_at`, the application must correctly route the event to the August 10 partition.

If old partitions have already been archived or dropped, late events require an explicit policy.

Possible strategies include:

- Accepting a defined lateness window.
- Keeping historical partitions available longer.
- Rejecting events outside the supported window.
- Routing exceptional events to a controlled staging path.

Do not let late-arriving data become an undocumented failure mode.

## Ignoring Cross-Partition Queries

Partitioning may optimize:

```sql
WHERE created_at >= ...
  AND created_at < ...
```

but not:

```sql
SELECT COUNT(*)
FROM events
WHERE event_type = 'payment';
```

The second query may require work across many partitions.

Production workloads should be classified into:

- Single-partition queries.
- Few-partition queries.
- Many-partition queries.
- Full-table queries.

Benchmark all important categories.

## Ignoring Aggregation Costs

Aggregations across partitions can still require substantial work.

For example:

```sql
SELECT tenant_id, COUNT(*)
FROM events
GROUP BY tenant_id;
```

Partitioning may not significantly reduce the amount of data that must be examined.

If the workload is primarily analytical, consider whether the correct solution is:

- Pre-aggregation.
- Materialized views.
- Read replicas.
- Analytical databases.
- Data warehouses.

Partitioning is not a substitute for workload separation.

## Assuming Partitioning Replaces Caching

If an API repeatedly requests the same expensive result, partitioning may reduce database work but may not be the best optimization.

For example:

```text
Client
  │
  ▼
FastAPI
  │
  ├── Redis cache hit → response
  │
  └── cache miss
          │
          ▼
      PostgreSQL
```

Partitioning and caching address different bottlenecks.

Use partitioning for physical data organization and pruning; use caching when repeated reads are the dominant problem.

## Ignoring ORM Behavior

Django and other ORMs can hide the generated SQL.

A developer may believe a query includes the partition key when the actual SQL does not.

For example:

```python
orders = (
    Order.objects
    .filter(status="paid")
    .order_by("-created_at")[:100]
)
```

If the table is partitioned by `created_at` but the query has no time predicate, pruning may be limited.

Always inspect generated SQL and database execution plans for performance-critical ORM queries.

## Hiding Partitioning Behind the ORM

Partitioning is a physical database design concern, but application engineers still need to understand its operational implications.

The application may not directly reference:

```text
orders_2026_08
```

but engineers still need to know:

- Which column controls routing.
- Which queries enable pruning.
- What happens when a partition is missing.
- How retention works.
- How migrations affect partitions.

Treat partitioning as part of the application's operational architecture.

## Running Large DDL Operations Without a Migration Plan

Partitioning changes can be expensive on large tables.

Potentially risky operations include:

- Creating indexes.
- Attaching existing tables.
- Detaching partitions.
- Changing constraints.
- Migrating data.
- Repartitioning an existing table.

Do not introduce partitioning directly into a production-sized database without testing:

```text
Development
   │
   ▼
Production-sized staging
   │
   ▼
Migration benchmark
   │
   ▼
Lock / WAL / replication analysis
   │
   ▼
Production rollout
```

The migration strategy should include rollback and recovery procedures.

## Repartitioning a Large Existing Table Without a Plan

Adding partitioning to a table that already contains billions of rows is substantially more complex than creating a partitioned table from the beginning.

A migration may involve:

```text
Existing table
      │
      ▼
New partitioned structure
      │
      ▼
Data migration
      │
      ▼
Index creation
      │
      ▼
Constraint validation
      │
      ▼
Application cutover
```

Depending on the database engine and required availability, this may require:

- Dual writes.
- Backfill jobs.
- Controlled cutover.
- Replication validation.
- Temporary storage capacity.
- Extended migration windows.

Never treat large-table repartitioning as a simple schema migration.

## Ignoring Locking and Availability

Some partition-management operations can acquire locks that affect concurrent workloads.

The exact locking behavior depends on the database engine, version, command, and execution context.

Production DDL should therefore be tested for:

- Lock duration.
- Blocking behavior.
- Query impact.
- Replication behavior.
- Failure and retry semantics.

For high-availability services, database DDL is production traffic.

## Ignoring Replication

Partition operations can affect replication because DDL and data movement can generate replicated work.

Monitor:

```text
Primary
  │
  ├── WAL / replication stream
  │
  ▼
Replica
```

Important signals include:

- Replication lag.
- WAL generation.
- Replica replay time.
- Replica storage.
- Failover readiness.

A partitioning operation that is fast on the primary can still create downstream replication pressure.

## Ignoring Backup and Restore Complexity

Partitioning does not remove the need for backups.

It can increase operational object complexity:

```text
Parent
├── Partition A
├── Partition B
├── Partition C
└── Partition D
```

Validate that:

- Backups include partitioned data.
- Schema definitions are recoverable.
- Partition metadata is preserved.
- Restore procedures recreate the expected structure.
- Retention policies do not accidentally remove required recovery data.

The backup strategy must match the physical data lifecycle.

## Using Partitioning as a Substitute for Sharding

Partitioning and sharding solve different problems.

If one database instance has reached its CPU, memory, storage, or I/O limits, creating more partitions inside that same instance does not necessarily solve the fundamental capacity problem.

```text
Partitioning

Database
├── P1
├── P2
├── P3
└── P4


Sharding

Database 1
├── P1
└── P2

Database 2
├── P3
└── P4
```

Use partitioning for physical organization within a database system and consider sharding when the database instance itself is the scaling boundary.

## Ignoring Cost

Partitioning introduces costs beyond storage.

Consider:

| Cost | Typical Impact |
|---|---|
| Metadata | More database objects |
| Indexes | More physical indexes |
| Planning | More partitions to consider |
| DDL | More objects to manage |
| Monitoring | More granular metrics |
| Backups | More physical structures |
| Engineering | More automation and operational knowledge |

The expected benefit should be measurable.

For example:

```text
Before:
p99 query latency = 900 ms
retention cleanup = 45 minutes

Target:
p99 query latency < 200 ms
retention cleanup < 1 minute
```

If partitioning cannot plausibly achieve a meaningful improvement, simpler indexing or query optimization may be preferable.

## Failing to Monitor Partition Growth

Partitioning can hide data growth by distributing it across physical objects.

Monitor:

- Partition size.
- Row count.
- Index size.
- Growth rate.
- Oldest partition.
- Newest partition.
- Number of partitions.
- Unexpectedly large partitions.

A useful operational view is:

```text
Partition Health
├── Size
├── Rows
├── Indexes
├── Growth
├── Age
├── Query activity
└── Maintenance status
```

Monitoring should detect abnormal growth before capacity becomes an incident.

## Failing to Monitor Missing Partitions

A production system should alert before a future partition becomes necessary.

For example:

```text
Current:
2026-08-31

Required:
2026-09 partition

Status:
MISSING
```

This should be detected before ingestion reaches the boundary.

A useful alert should identify:

- Table.
- Missing partition.
- Expected boundary.
- Time until boundary.
- Remediation status.

## Ignoring Operational Ownership

Partitioning introduces ongoing operational responsibilities.

Someone must own:

- Partition creation.
- Index creation.
- Retention.
- Monitoring.
- Capacity planning.
- Migration procedures.
- Incident response.

If nobody owns these processes, the partitioning design is incomplete.

## Mixing Partitioning With Security Boundaries

Partitioning can sometimes align with tenant or region boundaries, but partitioning should not be treated as an authorization mechanism.

For example:

```text
tenant_id = 42
```

being stored in a specific partition does not replace:

- Application authorization.
- Row-level security.
- Database permissions.
- Input validation.

Partitioning is a physical storage strategy, not a security boundary by default.

## Ignoring Tenant Isolation Requirements

For multi-tenant systems, engineers sometimes assume:

```text
Partition by tenant
```

automatically provides isolation.

It does not.

A production multi-tenant design must separately address:

- Authorization.
- Row-level security where appropriate.
- Noisy-neighbor behavior.
- Backup isolation requirements.
- Data deletion requirements.
- Compliance boundaries.

Partitioning may support these requirements but does not satisfy them alone.

## Assuming Partitioning Guarantees Even Distribution

Range partitioning can produce highly uneven partitions:

```text
2026-01 → 20 GB
2026-02 → 22 GB
2026-03 → 25 GB
2026-04 → 400 GB
```

Hash partitioning generally provides more even distribution, but even hash partitioning does not guarantee equal workload.

Distribution should be measured using real data.

## Ignoring Skew

Data skew occurs when some partition keys are much more common than others.

For example:

```text
tenant_1 → 80% of traffic
tenant_2 → 5%
tenant_3 → 1%
...
```

A theoretically balanced strategy can still create hot workloads.

Measure:

- Rows per partition.
- Writes per partition.
- Reads per partition.
- CPU.
- I/O.
- Lock contention.

The physical distribution of rows and the distribution of workload are related but not identical.

## Partitioning Before Measuring

One of the most expensive mistakes is implementing partitioning because a table is "large."

Start with evidence:

```text
Table growth
      │
      ▼
Query latency
      │
      ▼
EXPLAIN ANALYZE
      │
      ▼
I/O + CPU + locks
      │
      ▼
Identify bottleneck
      │
      ├── Query
      ├── Index
      ├── Cache
      ├── Storage
      ├── Lifecycle
      └── Partitioning
```

Partitioning should be the result of capacity and workload analysis, not a default response to row count.

## Common Production Pitfalls

| Mistake | Why It Happens | Better Practice |
|---|---|---|
| Wrong partition key | Designing from schema instead of workload | Analyze real queries |
| Too many partitions | Over-optimizing pruning | Project partition count |
| Too few partitions | Ignoring data volume | Model partition size |
| No future partitions | Manual lifecycle | Automate creation |
| Missing indexes | New partitions treated as automatic | Automate index provisioning |
| Hot partition | Range writes concentrate | Evaluate hash/composite designs |
| No pruning verification | Assuming partitioning works | Inspect execution plans |
| Large delete retention | Not aligning lifecycle with partitions | Drop/detach old partitions |
| Unplanned repartitioning | Underestimating migration complexity | Design migration and cutover |
| Ignoring replicas | Testing only primary performance | Monitor replication |
| Ignoring backups | Treating partitions as temporary | Test restore procedures |
| ORM blind spot | SQL hidden behind application code | Inspect generated SQL |
| Security assumption | Confusing storage with authorization | Keep security controls independent |

## A Senior-Level Review Process

A production partitioning review should answer the following questions.

### Workload

- Which queries dominate database load?
- Which queries contain the proposed partition key?
- How often do queries span many partitions?
- What are the p95 and p99 latencies?
- What does `EXPLAIN (ANALYZE, BUFFERS)` show?

### Data

- How large is the table today?
- How quickly is it growing?
- How uneven is the distribution?
- What is the expected size in one, three, and five years?

### Lifecycle

- How long is data retained?
- Can expired data be removed at partition granularity?
- How is archival handled?
- How is late-arriving data handled?

### Operations

- Who creates partitions?
- Who creates indexes?
- How are failures detected?
- How is partition health monitored?
- How are schema migrations performed?

### Reliability

- How does partitioning affect replication?
- How does it affect backups?
- How does it affect recovery?
- What happens if partition automation fails?

### Cost

- How much additional storage is required?
- How many physical indexes will exist?
- What is the operational engineering cost?
- Does the measured benefit justify the complexity?

## Production Checklist

Before deploying a partitioned table:

- [ ] The workload has been measured.
- [ ] The partition key is justified by query and lifecycle requirements.
- [ ] Partition count has been projected.
- [ ] Partition size has been estimated.
- [ ] Data skew has been analyzed.
- [ ] Write hot spots have been evaluated.
- [ ] Partition pruning has been verified with execution plans.
- [ ] Index strategy has been designed.
- [ ] Index storage has been estimated.
- [ ] Future partitions are created automatically.
- [ ] New partition indexes are created automatically.
- [ ] Partition creation failures generate alerts.
- [ ] Retention automation is idempotent.
- [ ] Late-arriving data has an explicit policy.
- [ ] NULL and unmatched partition-key values have an explicit policy.
- [ ] Cross-partition queries have been benchmarked.
- [ ] ORM-generated SQL has been reviewed where applicable.
- [ ] DDL locking behavior has been tested.
- [ ] Replication impact has been tested.
- [ ] Backup and restore procedures have been validated.
- [ ] High-availability behavior has been tested.
- [ ] Disaster recovery procedures account for partition lifecycle.
- [ ] Security controls are independent of partition placement.
- [ ] Repartitioning and migration procedures are documented.
- [ ] Partition ownership is clearly assigned.
- [ ] Capacity monitoring is implemented.
- [ ] Success criteria are measurable.

## Key Takeaways

- **Choose partition keys from real query, data-distribution, and lifecycle requirements—not simply from table size or schema structure.**
- **Avoid excessive partitions, unmanaged lifecycle operations, missing indexes, and hot partitions; these are common sources of production complexity.**
- **Verify partition pruning, query plans, write distribution, replication impact, and cross-partition behavior with realistic workloads.**
- **Automate partition creation, indexing, retention, monitoring, and failure detection; manual partition operations are operational debt.**
- **Treat partitioning as a physical database optimization and lifecycle strategy, not as a replacement for indexing, caching, authorization, high availability, or sharding.**