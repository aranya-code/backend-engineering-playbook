# 07- Composite Partitioning

## Overview

Composite partitioning combines multiple partitioning dimensions to address workloads where a single partitioning strategy is insufficient.

A common pattern is **multi-level partitioning**, where a table is first partitioned using one strategy and each resulting partition is further partitioned using another strategy.

For example:

```text
events
│
├── 2026-01
│   ├── tenant hash 0
│   ├── tenant hash 1
│   ├── tenant hash 2
│   └── tenant hash 3
│
├── 2026-02
│   ├── tenant hash 0
│   ├── tenant hash 1
│   ├── tenant hash 2
│   └── tenant hash 3
│
└── 2026-03
    ├── tenant hash 0
    ├── tenant hash 1
    ├── tenant hash 2
    └── tenant hash 3
```

This allows different dimensions to solve different operational problems:

- **Range partitioning** can isolate time periods and simplify retention.
- **Hash partitioning** can distribute tenants or customers within each time period.
- **List partitioning** can separate explicit business categories.
- A combination can provide both lifecycle management and workload distribution.

Composite partitioning is powerful, but it increases schema and operational complexity. It should be introduced only when the workload demonstrates a need for multiple partitioning dimensions.

## What Composite Partitioning Is

Composite partitioning means applying partitioning at more than one level.

For example:

```text
events
  │
  ▼
RANGE(created_at)
  │
  ├── January
  ├── February
  └── March
       │
       ▼
HASH(tenant_id)
       │
       ├── P0
       ├── P1
       ├── P2
       └── P3
```

The first level determines a broad logical boundary.

The second level distributes data inside that boundary.

This differs from simply having a composite partition key:

```sql
PARTITION BY HASH (tenant_id, customer_id)
```

A composite partition key is one partitioning operation using multiple columns.

Composite or multi-level partitioning is a **hierarchy of partitioning operations**.

## Why Composite Partitioning Exists

Single-level partitioning often optimizes one dimension well but leaves another operational problem unresolved.

Consider a multi-tenant event platform:

```text
500 million events
50,000 tenants
Data retained for 12 months
Queries filter by tenant_id and created_at
```

Range partitioning by time provides:

```text
events_2026_01
events_2026_02
...
```

which is excellent for retention.

However, a single monthly partition may still be extremely large.

Hash partitioning by tenant provides:

```text
tenant hash 0
tenant hash 1
...
```

which can improve distribution.

But hash partitioning alone does not provide convenient time-based lifecycle management.

Composite partitioning combines both:

```text
Range(created_at)
        │
        ├── Month 1
        │     └── Hash(tenant_id)
        │
        ├── Month 2
        │     └── Hash(tenant_id)
        │
        └── Month 3
              └── Hash(tenant_id)
```

## When to Use Composite Partitioning

Composite partitioning is appropriate when multiple independent workload characteristics matter.

Typical examples include:

| Workload | First Level | Second Level |
|---|---|---|
| Multi-tenant event platform | Range by time | Hash by tenant |
| Regional analytics | List by region | Range by time |
| SaaS audit logs | Range by time | Hash by tenant |
| Large customer datasets | Hash by tenant | Range by time |
| IoT telemetry | Range by time | Hash by device |
| Business categories with retention | List by category | Range by time |

Use it when each partitioning dimension solves a distinct problem.

Avoid it when one well-designed partitioning strategy already meets the workload requirements.

## Composite Partitioning vs Composite Partition Key

These concepts are commonly confused.

### Composite Partition Key

A database partitions using multiple columns in one partitioning expression:

```sql
PARTITION BY HASH (tenant_id, device_id)
```

The database uses the combined key to determine the target partition.

### Multi-Level Partitioning

The table is partitioned first by one key:

```sql
PARTITION BY RANGE (created_at)
```

and individual partitions are themselves partitioned:

```sql
PARTITION BY HASH (tenant_id)
```

The hierarchy becomes:

```text
created_at
    │
    ▼
Month
    │
    ▼
tenant_id hash
    │
    ▼
Physical partition
```

The distinction matters because the query-pruning behavior and operational model are different.

## Why Range + Hash Is a Common Combination

Range + hash is particularly useful for large time-series or event datasets.

Range partitioning provides:

- Time-based pruning.
- Easy archival.
- Easy deletion of old data.
- Smaller indexes per time period.
- Operationally meaningful partitions.

Hash partitioning provides:

- Distribution within each time period.
- Reduced concentration of data.
- Better handling of high-cardinality tenant or customer keys.

Together:

```text
                  events
                    │
            RANGE(created_at)
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    January      February       March
       │            │            │
 HASH(tenant)  HASH(tenant)  HASH(tenant)
       │            │            │
    ┌──┼──┐      ┌──┼──┐      ┌──┼──┐
    P0 P1 P2      P0 P1 P2      P0 P1 P2
```

The first dimension manages **time**.

The second dimension manages **distribution**.

## PostgreSQL Example

Create a range-partitioned parent table:

```sql
CREATE TABLE events (
    id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (created_at);
```

Create a monthly partition that is itself hash-partitioned:

```sql
CREATE TABLE events_2026_01
PARTITION OF events
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
PARTITION BY HASH (tenant_id);
```

Create hash partitions underneath it:

```sql
CREATE TABLE events_2026_01_p0
PARTITION OF events_2026_01
FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE events_2026_01_p1
PARTITION OF events_2026_01
FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE events_2026_01_p2
PARTITION OF events_2026_01
FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE events_2026_01_p3
PARTITION OF events_2026_01
FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

The resulting hierarchy is:

```text
events
└── events_2026_01
    ├── events_2026_01_p0
    ├── events_2026_01_p1
    ├── events_2026_01_p2
    └── events_2026_01_p3
```

Additional monthly partitions can follow the same pattern.

## Insert Routing

The application inserts into the logical parent:

```sql
INSERT INTO events (
    id,
    tenant_id,
    event_type,
    payload,
    created_at
)
VALUES (
    100001,
    42,
    'order.created',
    '{"order_id": 9001}',
    '2026-01-15T10:30:00Z'
);
```

The database routes the row through both levels:

```text
INSERT
  │
  ▼
events
  │
  ▼
created_at = 2026-01-15
  │
  ▼
events_2026_01
  │
  ▼
hash(tenant_id = 42)
  │
  ▼
events_2026_01_pN
```

The application does not need to calculate or know the final physical partition.

## Query Pruning

Composite partitioning can provide pruning at multiple levels.

Consider:

```sql
SELECT id, event_type, payload
FROM events
WHERE tenant_id = 42
  AND created_at >= '2026-01-15'
  AND created_at < '2026-01-16';
```

The optimizer can potentially eliminate:

```text
Unrelated months
      │
      ▼
Relevant month
      │
      ▼
Relevant hash partition
```

Conceptually:

```text
Query
 │
 ├── created_at
 │      │
 │      ▼
 │   January only
 │
 └── tenant_id
        │
        ▼
     Hash partition P2
        │
        ▼
      Scan
```

This can significantly reduce the amount of data accessed when the query constrains both partitioning dimensions.

Always verify actual pruning with `EXPLAIN`.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, event_type
FROM events
WHERE tenant_id = 42
  AND created_at >= '2026-01-15'
  AND created_at < '2026-01-16';
```

## Queries Missing One Partition Key

Composite partitioning does not make every query efficient.

Consider:

```sql
SELECT COUNT(*)
FROM events
WHERE tenant_id = 42;
```

The query does not constrain `created_at`.

The database may need to examine the relevant hash partition in many or all time partitions:

```text
January  → P2
February → P2
March    → P2
April    → P2
...
```

Conversely:

```sql
SELECT COUNT(*)
FROM events
WHERE created_at >= '2026-01-01'
  AND created_at < '2026-02-01';
```

can prune the time dimension but may need to scan all hash subpartitions within January:

```text
January
├── P0 ──┐
├── P1 ──┤
├── P2 ──┼──► Aggregate
└── P3 ──┘
```

This is an important design trade-off.

The partition hierarchy should reflect the most important access patterns, not simply the columns with the largest cardinality.

## Partitioning Order Matters

These two designs are not equivalent operationally.

### Range → Hash

```text
events
└── month
    └── tenant hash
```

### Hash → Range

```text
events
└── tenant hash
    └── month
```

Choose the first level based on the dominant operational dimension.

For a time-series system with retention requirements, range-first is often preferable:

```text
Range(created_at)
        │
        ▼
Time partition
        │
        ▼
Hash(tenant_id)
```

This makes operations such as:

```text
Drop old month
Archive old month
Restore specific period
```

more straightforward.

## Hash → Range

Hash-first can be appropriate when tenant distribution is the primary concern and time-based organization is secondary.

Conceptually:

```text
events
│
├── tenant hash 0
│   ├── January
│   ├── February
│   └── March
│
├── tenant hash 1
│   ├── January
│   ├── February
│   └── March
│
└── tenant hash 2
    ├── January
    ├── February
    └── March
```

However, time-based lifecycle operations become more distributed.

Deleting one month's data means touching many top-level branches:

```text
P0 → January
P1 → January
P2 → January
P3 → January
...
```

Range-first is often easier for workloads where retention is a major operational requirement.

## Partitioning Strategy Selection

| Requirement | Better First-Level Strategy |
|---|---|
| Time-based retention | Range |
| Strong tenant distribution requirement | Hash |
| Explicit business categories | List |
| Region-specific lifecycle | List |
| Time-series workload | Range |
| Multi-tenant event stream | Often Range |
| Tenant isolation is dominant | Possibly Hash |
| Multiple independent dimensions | Composite |

The first level should usually represent the most important pruning or lifecycle dimension.

## Advantages

### Better Data Organization

Composite partitioning allows each level to solve a different physical data-management problem.

For example:

```text
Time → lifecycle
Tenant → distribution
```

### Improved Partition Pruning

Queries containing both partitioning predicates may eliminate large portions of the dataset.

### Smaller Physical Partitions

Instead of one massive monthly partition:

```text
January → 500 GB
```

you may have:

```text
January
├── P0 → 125 GB
├── P1 → 125 GB
├── P2 → 125 GB
└── P3 → 125 GB
```

assuming reasonably balanced distribution.

### Better Maintenance Boundaries

Maintenance operations can potentially work against smaller physical partitions.

This can improve:

- Index maintenance.
- Vacuum behavior.
- Statistics management.
- Data movement.
- Operational troubleshooting.

### Flexible Lifecycle Management

Range-first designs can make retention workflows straightforward:

```text
DROP / DETACH old time partition
```

instead of deleting billions of rows individually.

## Limitations

### Increased Complexity

A simple table:

```text
events
```

becomes:

```text
events
└── month
    └── hash partitions
```

The schema is more difficult to understand and operate.

### More Database Objects

If you have:

```text
12 months × 16 hash partitions
```

you already have:

```text
192 leaf partitions
```

before accounting for indexes and other database objects.

### More Complex Migrations

Creating, attaching, detaching, validating, and maintaining multiple levels requires disciplined migration procedures.

### Query Planning Complexity

More partitions can increase planning and execution overhead, especially for queries that cannot prune effectively.

### Harder Troubleshooting

Performance problems can occur at multiple levels:

```text
Parent
  ↓
First-level partition
  ↓
Second-level partition
  ↓
Index
  ↓
Storage
```

Operational tooling must understand the hierarchy.

## Choosing the Number of Subpartitions

Avoid multiplying partition counts without justification.

For example:

```text
24 monthly partitions
×
32 hash partitions
=
768 leaf partitions
```

This may be appropriate for a very large system, but it should not be the default.

Evaluate:

- Rows per leaf partition.
- Storage per leaf partition.
- Query frequency.
- Index size.
- Planning time.
- Vacuum behavior.
- Backup duration.
- Migration complexity.
- Monitoring overhead.

A smaller number of well-sized partitions is often preferable to a huge partition hierarchy.

## Index Strategy

Indexes are generally created with the query workload in mind.

For example:

```sql
CREATE INDEX events_tenant_created_at_idx
ON events (tenant_id, created_at);
```

For a partitioned table, PostgreSQL can maintain corresponding indexes across partitions through partitioned-index mechanisms.

The appropriate index design depends on:

- Query predicates.
- Sort requirements.
- Selectivity.
- Partition pruning.
- Index size.
- Write volume.

Do not automatically duplicate every possible index across every leaf partition.

Each additional index increases:

- Storage.
- Write amplification.
- Vacuum work.
- Maintenance time.

## Composite Partitioning and Unique Constraints

Unique constraints and primary keys require careful design with partitioned tables.

If a uniqueness requirement is intended to span the entire logical table, verify that the database can enforce it across the partition hierarchy.

For example:

```text
id
```

must not accidentally become unique only within one physical partition when global uniqueness is required.

Partitioning restrictions differ across database engines, so schema design must follow the selected database's actual constraint semantics.

## Multi-Tenant Architecture

Composite partitioning is particularly relevant to SaaS platforms.

Consider:

```text
API
 │
 ▼
Application
 │
 ▼
PostgreSQL
 │
 ▼
events
 │
 ├── 2026-01
 │   ├── tenant hash 0
 │   ├── tenant hash 1
 │   ├── tenant hash 2
 │   └── tenant hash 3
 │
 └── 2026-02
     ├── tenant hash 0
     ├── tenant hash 1
     ├── tenant hash 2
     └── tenant hash 3
```

An API request:

```http
GET /tenants/42/events?from=2026-01-15&to=2026-01-16
```

can map naturally to:

```sql
WHERE tenant_id = 42
  AND created_at >= $1
  AND created_at < $2
```

This gives the database the information needed to prune both dimensions.

## Django and FastAPI Integration

Application frameworks generally should interact with the logical parent table rather than physical partitions.

Django:

```python
events = Event.objects.filter(
    tenant_id=tenant_id,
    created_at__gte=start,
    created_at__lt=end,
)
```

FastAPI with SQLAlchemy:

```python
query = text("""
    SELECT id, event_type, payload
    FROM events
    WHERE tenant_id = :tenant_id
      AND created_at >= :start_time
      AND created_at < :end_time
""")

result = connection.execute(
    query,
    {
        "tenant_id": tenant_id,
        "start_time": start_time,
        "end_time": end_time,
    },
)
```

The application should not construct:

```text
events_2026_01_p2
```

itself.

That physical layout belongs to the database layer.

## Time-Based Retention

One of the strongest reasons to combine range and hash partitioning is retention.

Suppose events are retained for 12 months:

```text
events_2025_03
events_2025_04
...
events_2026_02
```

Once a month expires, the database can use partition-level lifecycle operations rather than issuing:

```sql
DELETE FROM events
WHERE created_at < ...;
```

against hundreds of millions of rows.

Conceptually:

```text
Old data
   │
   ▼
Detach/archive partition
   │
   ▼
Drop or archive storage
```

This can reduce transaction volume, WAL generation, locking duration, and table bloat compared with large row-by-row deletes.

The exact operational behavior depends on the database engine and the detach/drop procedure used.

## Production Partition Lifecycle

For range-first composite partitioning, production automation commonly needs to:

```text
Create future range partition
        │
        ▼
Create required subpartitions
        │
        ▼
Create/validate indexes
        │
        ▼
Monitor usage
        │
        ▼
Archive or detach expired partition
        │
        ▼
Drop after retention policy
```

This process should be automated rather than dependent on manual database administration.

A scheduler such as Celery can trigger application-level orchestration, but schema changes should still be carefully controlled and preferably executed through database-aware migration or operational tooling.

## Monitoring

Monitor both levels of the hierarchy.

### First-Level Metrics

Track:

- Rows per time partition.
- Storage per time partition.
- Query volume.
- Retention state.
- Partition age.
- Index size.

### Leaf-Level Metrics

Track:

- Rows per hash partition.
- Storage per hash partition.
- Read volume.
- Write volume.
- Query latency.
- Index growth.
- Vacuum activity.

A useful conceptual metric is:

```text
Partition skew =
largest leaf partition / average leaf partition
```

Large and persistent skew should trigger investigation.

## Performance Verification

Never assume composite partitioning improved performance.

Compare:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, event_type
FROM events
WHERE tenant_id = 42
  AND created_at >= '2026-01-01'
  AND created_at < '2026-02-01';
```

Check:

- Number of partitions scanned.
- Partition pruning.
- Actual rows.
- Estimated rows.
- Index usage.
- Buffer reads.
- Execution time.
- Planning time.

The goal is not:

> "We have many partitions."

The goal is:

> "The optimizer eliminates most irrelevant data and the remaining access path is efficient."

## Common Mistakes and Pitfalls

### Using Composite Partitioning Without Two Real Problems

Do not add a second partitioning layer simply because the database supports it.

Each level should solve a measurable problem.

### Multiplying Partitions Excessively

A hierarchy of:

```text
24 months × 32 hash partitions
```

creates 768 leaf partitions.

Add indexes and operational metadata, and complexity increases rapidly.

Start with the smallest partition hierarchy that satisfies the workload.

### Choosing the Wrong First-Level Dimension

If retention is the primary operational requirement, hash-first may make retention unnecessarily complicated.

If tenant distribution is the primary requirement, range-first may not address the actual bottleneck.

### Assuming Both Levels Always Prune

A query may constrain only one partitioning dimension.

For example:

```sql
WHERE tenant_id = 42
```

does not necessarily eliminate all time partitions.

Verify pruning with execution plans.

### Ignoring Hot Tenants

Hashing by `tenant_id` does not split one tenant across multiple hash partitions.

A very large tenant can still create a hot leaf partition.

### Hard-Coding Physical Partitions

Avoid application code such as:

```python
table_name = f"events_{month}_p{partition}"
```

This couples business logic to database topology.

### Treating Partitioning as Sharding

Composite partitioning does not automatically distribute data across database servers.

All partitions can still reside on one PostgreSQL instance.

### Over-Indexing

Creating the same large collection of indexes across hundreds of leaf partitions can create substantial storage and write overhead.

Design indexes from real query patterns.

### Ignoring Migration Cost

Creating future partitions may be inexpensive compared with moving or repartitioning existing production data.

Plan lifecycle changes ahead of time.

### Forgetting Future Partitions

Range partitioning requires coverage for future values.

If a new month's partition is not created in time, inserts can fail unless an appropriate default partition or other valid routing path exists.

Automate future partition creation.

## Security Considerations

Composite partitioning is not an authorization mechanism.

A tenant-scoped query should still enforce authorization:

```sql
SELECT id, event_type, payload
FROM events
WHERE tenant_id = $1
  AND created_at >= $2
  AND created_at < $3;
```

Use:

- Parameterized queries.
- Tenant-aware authorization.
- Least-privilege database roles.
- Row-Level Security where appropriate.

Do not treat:

```text
tenant hash partition
```

as a security boundary.

A database partition is a physical organization mechanism, not a replacement for access control.

## High Availability and Disaster Recovery

Composite partitioning does not inherently provide high availability.

All partitions may still depend on the same:

- Database instance.
- Storage subsystem.
- Network.
- Replication topology.

Production systems should independently address:

- Streaming replication.
- Automated failover.
- Backups.
- Point-in-time recovery.
- Replica monitoring.
- Restore testing.
- Migration recovery.

Partition-level lifecycle operations should also be included in operational runbooks.

## Cost Considerations

Composite partitioning can reduce costs by improving:

- Query efficiency.
- Retention operations.
- Maintenance boundaries.
- Storage management.
- Data archival.

But excessive partitioning can increase:

- Storage metadata.
- Index storage.
- CPU used for planning.
- Maintenance workload.
- Migration complexity.
- Monitoring overhead.

The objective is not to maximize the number of partitions.

The objective is to create useful physical boundaries that improve the overall system.

## Production Design Checklist

- [ ] Identify the primary workload dimension.
- [ ] Identify the secondary workload or lifecycle dimension.
- [ ] Confirm that each partitioning level solves a real problem.
- [ ] Select the appropriate first-level strategy.
- [ ] Select the appropriate second-level strategy.
- [ ] Estimate total leaf partition count.
- [ ] Measure expected rows and storage per leaf partition.
- [ ] Analyze tenant or key distribution.
- [ ] Identify potential hot keys or hot tenants.
- [ ] Verify partition pruning with `EXPLAIN`.
- [ ] Design indexes based on actual queries.
- [ ] Automate future partition creation.
- [ ] Automate retention and archival operations.
- [ ] Monitor partition and leaf-partition skew.
- [ ] Test migrations against production-scale data.
- [ ] Include partition lifecycle operations in backup and DR procedures.
- [ ] Keep application code independent of physical partition names.
- [ ] Reassess the hierarchy as workload characteristics change.

## Interview Perspective

A strong senior-level explanation should distinguish **multi-level partitioning** from a simple composite partition key.

A concise answer is:

> **Composite partitioning combines multiple partitioning dimensions, commonly by partitioning a table first by range and then subpartitioning each range by hash. It is useful when one dimension provides lifecycle or pruning benefits while another provides workload distribution. The main trade-offs are increased partition count, operational complexity, query-planning overhead, migration complexity, and the possibility of skew or hot keys.**

Common follow-up questions include:

- What is the difference between a composite partition key and multi-level partitioning?
- Why is range + hash a common combination?
- Why might range be preferable as the first level?
- What happens if a query filters only on the second-level key?
- How does partition pruning work across multiple levels?
- How do you choose the number of subpartitions?
- What happens when one tenant is much larger than the others?
- Does composite partitioning provide horizontal database scaling?
- How would you handle time-based retention?
- How would you monitor partition skew?
- When would you choose sharding instead?

The key engineering principle is:

> **Use each partitioning level for a distinct, measurable workload or lifecycle requirement.**

## Key Takeaways

- **Composite partitioning applies multiple partitioning dimensions, commonly using range for lifecycle management and hash for distribution.**
- **Multi-level partitioning is different from a composite partition key; it creates a hierarchy of partitioning operations.**
- **Query performance depends on effective pruning at each level, so real execution plans must be measured rather than assumed.**
- **Partition multiplication, hot tenants, index overhead, migrations, and lifecycle automation are the major production concerns.**
- **Composite partitioning remains database-level organization; it does not replace sharding, authorization, indexing, or high-availability architecture.**