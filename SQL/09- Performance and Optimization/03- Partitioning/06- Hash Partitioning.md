# 06- Hash Partitioning

## Overview

Hash partitioning distributes rows across a fixed number of partitions according to a hash function applied to the partition key.

Unlike list partitioning, which explicitly maps values to partitions, or range partitioning, which maps intervals to partitions, hash partitioning is designed primarily for **even distribution**.

A simplified model is:

```text
partition = hash(partition_key) % number_of_partitions
```

The actual hash algorithm and routing behavior are database-specific, but the architectural idea is the same: rows with different key values are distributed across a set of partitions.

Hash partitioning is particularly useful for large tables where:

- The partition key has high cardinality.
- Queries frequently filter by that key.
- Even distribution is more important than business-oriented partition boundaries.
- A predictable number of partitions can be maintained.
- The workload would otherwise create a hotspot in a single logical table.

PostgreSQL supports declarative hash partitioning and is a practical reference implementation for backend systems.

## What Hash Partitioning Is

Hash partitioning divides a table according to a hash of one or more partition-key columns.

For example:

```text
                    orders
                       │
                 hash(customer_id)
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Bucket 0     Bucket 1     Bucket 2
          │            │            │
          ▼            ▼            ▼
     orders_p0     orders_p1     orders_p2
```

A row such as:

```text
customer_id = 10042
```

is passed through the partitioning mechanism, which determines its target partition.

The application normally continues to query the logical parent table:

```sql
SELECT id, total_amount
FROM orders
WHERE customer_id = 10042;
```

The database determines which partition or partitions need to participate.

## Why Hash Partitioning Exists

Large tables can develop problems that are not solved well by range or list partitioning.

Consider:

```text
orders
├── 1 billion rows
├── customer_id has 50 million distinct values
└── queries frequently filter by customer_id
```

List partitioning by every customer would create an impractical number of partitions.

Range partitioning by customer ID may also create undesirable distribution because the ranges do not necessarily correspond to equal workloads.

Hash partitioning provides a mechanism to spread rows across a controlled number of partitions.

The primary objective is therefore:

> **Distribute data and workload predictably across partitions while avoiding excessive partition cardinality.**

## When to Use Hash Partitioning

Hash partitioning is a strong candidate when:

| Requirement | Hash Partitioning |
|---|---|
| High-cardinality partition key | Excellent |
| Even data distribution | Excellent |
| Queries filter by partition key | Good |
| Stable number of partitions | Good |
| Business-readable partitions | Poor |
| Time-based retention | Poor |
| Category-specific archival | Poor |
| Large tenant population | Often good |
| Sequential time-series data | Usually poor |
| Explicit regional isolation | Poor |

Typical candidates include:

- `customer_id`
- `tenant_id`
- `user_id`
- `account_id`
- `device_id`
- Other high-cardinality identifiers

Hash partitioning is generally less suitable when the primary requirement is data lifecycle management.

## PostgreSQL Hash Partitioning

PostgreSQL supports declarative hash partitioning.

Example:

```sql
CREATE TABLE orders (
    id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    status TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
) PARTITION BY HASH (customer_id);
```

Create four hash partitions:

```sql
CREATE TABLE orders_p0
PARTITION OF orders
FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE orders_p1
PARTITION OF orders
FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE orders_p2
PARTITION OF orders
FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE orders_p3
PARTITION OF orders
FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

The four partitions represent hash remainders:

```text
orders_p0 → remainder 0
orders_p1 → remainder 1
orders_p2 → remainder 2
orders_p3 → remainder 3
```

The application does not need to know which physical partition contains a particular customer.

## How Hash Routing Works

Conceptually:

```text
customer_id
     │
     ▼
Hash function
     │
     ▼
Hash value
     │
     ▼
Partition routing
     │
     ├── remainder 0 → orders_p0
     ├── remainder 1 → orders_p1
     ├── remainder 2 → orders_p2
     └── remainder 3 → orders_p3
```

The exact internal implementation is database-specific.

The important engineering property is that equivalent partition-key values consistently map to the same partition configuration.

## Partition Pruning

Hash partitioning can benefit queries that constrain the partition key.

For example:

```sql
SELECT id, total_amount
FROM orders
WHERE customer_id = 10042;
```

The optimizer can determine the relevant hash partition and avoid scanning unrelated partitions when the query provides sufficient information.

This is particularly valuable for high-cardinality lookup workloads.

A query without the partition key is different:

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'pending';
```

The database may need to examine every partition because `status` does not determine which hash partition contains the row.

Conceptually:

```text
WHERE customer_id = 10042
             │
             ▼
      Hash partition key
             │
             ▼
      Target partition
             │
             ▼
        Index / Scan
```

versus:

```text
WHERE status = 'pending'
             │
             ▼
       No partition key
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
      P0    P1    P2 ... Pn
       │     │     │
       └─────┴─────┘
             │
             ▼
       Combine results
```

Partitioning does not automatically accelerate predicates unrelated to the partition key.

## Hash Partitioning and Indexes

Hash partitioning and indexes solve different problems.

Partitioning determines:

> Which partition contains the row?

An index determines:

> How efficiently can the row be found inside that partition?

For example:

```sql
CREATE INDEX orders_p0_customer_status_idx
ON orders_p0 (customer_id, status);

CREATE INDEX orders_p1_customer_status_idx
ON orders_p1 (customer_id, status);

CREATE INDEX orders_p2_customer_status_idx
ON orders_p2 (customer_id, status);

CREATE INDEX orders_p3_customer_status_idx
ON orders_p3 (customer_id, status);
```

A query:

```sql
SELECT id, total_amount
FROM orders
WHERE customer_id = 10042
  AND status = 'pending';
```

can potentially benefit from:

```text
customer_id
     │
     ▼
Partition pruning
     │
     ▼
orders_pN
     │
     ▼
Index lookup
     │
     ▼
Matching rows
```

Do not introduce hash partitioning simply because an index is becoming large.

First determine whether the actual bottleneck is:

- Index size.
- Table size.
- I/O.
- Cache behavior.
- Write contention.
- Query planning.
- Maintenance.
- Storage growth.

## Choosing the Hash Partition Key

The partition key should normally have:

- High cardinality.
- Good distribution characteristics.
- Strong correlation with common query predicates.
- Stable semantics.
- A meaningful relationship to the workload.

For example:

```text
tenant_id
```

may be appropriate for a SaaS workload where queries frequently execute:

```sql
WHERE tenant_id = $1
```

Similarly:

```text
customer_id
```

may be appropriate for a customer-centric transactional workload.

A poor partition key might be:

```text
status
```

when values are only:

```text
pending
completed
failed
cancelled
```

This creates only a small number of logical groups and provides little reason to use hashing.

List partitioning would better represent such explicit categories.

## High Cardinality Does Not Automatically Mean Good Distribution

High cardinality is useful, but it is not sufficient.

Suppose the partition key is:

```text
tenant_id
```

and the workload contains:

```text
tenant A → 60% of all rows
tenant B → 20%
tenants C..Z → 20%
```

Hashing individual tenant IDs can distribute rows by key, but a single extremely large tenant can still become a hotspot because all of that tenant's rows map to the same hash partition.

Hash partitioning distributes **keys**, not individual rows independently.

This distinction is important for senior-level system design.

## Data Skew

Hash partitioning generally provides better distribution than list partitioning, but it does not guarantee perfectly equal data or workload distribution.

Potential causes of skew include:

- A few keys producing most of the traffic.
- Unequal row counts per key.
- Hot tenants.
- Non-uniform access patterns.
- Composite partition keys with skewed combinations.

Monitor:

```text
Rows per partition
Storage per partition
Writes per partition
Reads per partition
Index size per partition
Query latency
```

If one partition consistently receives disproportionate traffic, investigate whether the partition key reflects the actual workload.

## Hot Tenant Problem

Multi-tenant systems are a common use case for hash partitioning.

Consider:

```text
tenant_id
```

with:

```text
Tenant A → 500 million rows
Tenant B → 20 million rows
Tenant C → 10 million rows
```

Hash partitioning does not split Tenant A's rows across multiple partitions if `tenant_id` alone is the partition key.

The result may look like:

```text
Partition 0 → 20M rows
Partition 1 → 530M rows
Partition 2 → 15M rows
Partition 3 → 5M rows
```

Possible strategies include:

- Composite partition keys.
- Hashing a more granular key.
- Subpartitioning.
- Isolating very large tenants.
- Moving large tenants to dedicated databases.
- Sharding.

Do not assume that hash partitioning automatically eliminates hot spots.

## Hash Partitioning vs List Partitioning

| Characteristic | Hash | List |
|---|---|---|
| Distribution | Algorithmic | Explicit |
| Primary goal | Even distribution | Logical grouping |
| High-cardinality keys | Good | Poor |
| Business-readable partitions | Poor | Excellent |
| Region partitioning | Poor | Excellent |
| Tenant grouping | Good | Good for small groups |
| Predictable category membership | Poor | Excellent |
| Data balancing | Generally good | Manual |
| Lifecycle management | Limited | Strong for categories |

Use hash partitioning when distribution matters more than business semantics.

Use list partitioning when explicit categories have operational meaning.

## Hash Partitioning vs Range Partitioning

| Characteristic | Hash | Range |
|---|---|---|
| Distribution | Generally even | Depends on ranges |
| Ordered access | Poor | Excellent |
| Time-based data | Poor | Excellent |
| Retention management | Poor | Excellent |
| Equality lookups | Good | Good depending on key/range |
| High-cardinality identifiers | Good | Sometimes |
| Sequential inserts | Can distribute | Can hotspot newest range |
| Business lifecycle | Limited | Excellent for time ranges |

A timestamp-based event table usually benefits more from range partitioning:

```text
events_2026_01
events_2026_02
events_2026_03
```

A tenant-centric transactional table may benefit more from hash partitioning:

```text
tenant hash
├── partition 0
├── partition 1
├── partition 2
└── partition 3
```

## Hash Partitioning vs Sharding

Hash partitioning and sharding are related but operate at different architectural levels.

Hash partitioning:

```text
Application
     │
     ▼
One PostgreSQL database
     │
     ├── Hash partition 0
     ├── Hash partition 1
     ├── Hash partition 2
     └── Hash partition 3
```

Sharding:

```text
Application
     │
     ▼
Routing layer
     │
     ├── Database A
     │     └── shard data
     │
     ├── Database B
     │     └── shard data
     │
     └── Database C
           └── shard data
```

Partitioning generally remains within the database system.

Sharding distributes data across independent database instances or nodes.

Hash partitioning can therefore be considered a useful data-layout technique without requiring the operational complexity of distributed databases.

## Partition Count

Choosing the number of hash partitions is an architectural decision.

For example:

```text
4 partitions
8 partitions
16 partitions
32 partitions
```

More partitions can provide finer distribution, but also increase operational complexity.

Potential costs include:

- More indexes.
- More metadata.
- More maintenance operations.
- More complex migrations.
- More objects to monitor.
- More complex backup and restore procedures.
- Potential planning overhead.

Avoid choosing an arbitrary large number such as:

```text
1024 partitions
```

without measuring whether the workload benefits from it.

The correct number depends on:

- Table size.
- Expected growth.
- Hardware.
- Query workload.
- Index sizes.
- Maintenance requirements.
- Database engine behavior.

## Changing the Number of Hash Partitions

Hash partitioning has an important operational consideration: changing the partition count can require significant data movement.

Conceptually:

```text
4 partitions

P0  P1  P2  P3
 │   │   │   │
 └───┴───┴───┘
       │
       ▼
Repartition
       │
       ▼
8 partitions

P0 P1 P2 P3 P4 P5 P6 P7
```

Changing the number of partitions can change the mapping between keys and partitions.

This means partition-count changes should not be treated as a trivial configuration update.

Before resizing:

1. Estimate data movement.
2. Estimate WAL and replication impact.
3. Evaluate locking requirements.
4. Test the migration.
5. Confirm backup coverage.
6. Plan rollback and recovery.
7. Validate application performance afterward.

Design the initial partition count with expected growth in mind.

## Composite Hash Partition Keys

Some workloads require more than one column to distribute data effectively.

For example:

```sql
CREATE TABLE events (
    id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    device_id BIGINT NOT NULL,
    event_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
) PARTITION BY HASH (tenant_id, device_id);
```

A composite key can improve distribution when one column alone is insufficient.

However, it also changes the routing characteristics.

If most queries use only:

```sql
WHERE tenant_id = $1
```

the query-planning and pruning behavior should be verified rather than assumed.

The partition key should reflect actual access patterns.

## Multi-Level Partitioning

Hash partitioning can be combined with another partitioning strategy.

For example:

```text
events
│
├── January
│    ├── hash 0
│    ├── hash 1
│    ├── hash 2
│    └── hash 3
│
├── February
│    ├── hash 0
│    ├── hash 1
│    ├── hash 2
│    └── hash 3
│
└── March
     ├── hash 0
     ├── hash 1
     ├── hash 2
     └── hash 3
```

This can combine:

- Range partitioning for lifecycle management.
- Hash partitioning for distribution within each range.

For example, PostgreSQL can use:

```sql
CREATE TABLE events (
    id BIGINT NOT NULL,
    tenant_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
) PARTITION BY RANGE (created_at);
```

A monthly partition can then be further partitioned:

```sql
CREATE TABLE events_2026_01
PARTITION OF events
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
PARTITION BY HASH (tenant_id);
```

Subpartitions can then be created beneath it.

Multi-level partitioning is powerful but should be introduced only when the workload clearly requires both dimensions.

## Query Behavior

Hash partitioning works best when the partition key appears in selective queries.

Good candidate:

```sql
SELECT id, status, total_amount
FROM orders
WHERE customer_id = 10042;
```

Less useful:

```sql
SELECT id, customer_id
FROM orders
WHERE status = 'pending';
```

Potentially expensive:

```sql
SELECT COUNT(*)
FROM orders;
```

The latter may require processing all partitions because there is no partition predicate.

Partitioning does not reduce the logical amount of work required for every query.

## Aggregation Across Hash Partitions

Queries that need data from all partitions can require multiple scans and result aggregation.

For example:

```sql
SELECT status, COUNT(*)
FROM orders
GROUP BY status;
```

Conceptually:

```text
P0 ──┐
P1 ──┤
P2 ──┼──► Partial aggregation ──► Final aggregation
P3 ──┘
```

Parallel execution can help depending on the database engine, configuration, statistics, and query plan.

Do not assume that partitioning makes global aggregations faster.

The database may still need to process the complete dataset.

## Write Distribution

Hash partitioning can distribute inserts across partitions when the partition key has good cardinality and distribution.

This can reduce concentration of:

- Table-level storage activity.
- Index activity.
- Buffer pressure.
- Certain forms of contention.

For example:

```text
Incoming writes
      │
      ▼
Hash(tenant_id)
      │
 ┌────┼────┬────┐
 ▼    ▼    ▼    ▼
 P0   P1   P2   P3
```

However, partitioning does not automatically eliminate database-level contention.

Shared resources such as:

- CPU.
- Memory.
- WAL.
- Connections.
- Storage.
- Locks.
- Checkpoints.

can still become bottlenecks.

## Application Integration

Applications should generally interact with the logical parent table.

Django:

```python
orders = Order.objects.filter(
    customer_id=customer_id,
)
```

FastAPI with SQLAlchemy:

```python
query = """
    SELECT id, status, total_amount
    FROM orders
    WHERE customer_id = :customer_id
"""

result = connection.execute(
    text(query),
    {"customer_id": customer_id},
)
```

The application should not manually calculate the hash partition.

Avoid logic such as:

```python
partition = hash(customer_id) % 4
```

and then constructing SQL against:

```text
orders_p2
```

This couples application behavior to database internals and makes future partition changes significantly harder.

Let the database own partition routing unless the architecture explicitly requires application-level sharding.

## Transactions and Partitioning

Hash partitioning normally remains transparent to transactions.

A transaction can insert into the logical table:

```sql
BEGIN;

INSERT INTO orders (
    id,
    customer_id,
    status,
    total_amount,
    created_at
)
VALUES (
    900001,
    10042,
    'pending',
    149.99,
    CURRENT_TIMESTAMP
);

COMMIT;
```

PostgreSQL routes the row to the appropriate partition.

Transactions that touch multiple partitions still operate within the same database transaction.

Partitioning does not create independent transactional systems.

This is an important distinction from sharding, where cross-shard transactions can become significantly more complex.

## Constraints and Uniqueness

Partitioned-table constraints require careful schema design.

If a primary key or unique constraint is expected to be globally unique across all partitions, the database's partitioning restrictions must be considered.

For example:

```sql
id BIGINT PRIMARY KEY
```

should be designed according to the database engine's rules for partitioned tables.

A unique constraint on a single partition does not automatically mean that the value is unique across every partition.

For globally unique identifiers, UUIDs or properly coordinated ID-generation strategies can be useful, but they do not remove the need to understand the database's constraint rules.

## Operational Considerations

Hash partitioning reduces some data-management problems but introduces its own operational responsibilities.

Production teams should define:

- Partition naming conventions.
- Partition-count strategy.
- Index strategy.
- Migration procedures.
- Backup and restore procedures.
- Monitoring.
- Capacity planning.
- Repartitioning procedures.
- Disaster-recovery testing.

Partition definitions should be managed through:

```text
Migration
   │
   ▼
CI/CD
   │
   ▼
Database
```

rather than manual production changes.

## Monitoring

Monitor the actual distribution rather than assuming the hash function is sufficient.

Useful metrics include:

| Metric | Why It Matters |
|---|---|
| Rows per partition | Detect uneven distribution |
| Storage per partition | Detect physical skew |
| Writes per partition | Detect write hotspots |
| Reads per partition | Detect workload hotspots |
| Index size per partition | Detect maintenance growth |
| Query latency by key | Validate routing effectiveness |
| Partition count | Track operational complexity |
| WAL generation | Measure migration/write impact |
| Replication lag | Detect operational pressure |
| Buffer/cache behavior | Identify I/O pressure |

Use database execution plans to verify pruning.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, total_amount
FROM orders
WHERE customer_id = 10042;
```

Performance decisions should be based on measured execution behavior.

## Security Considerations

Hash partitioning is not a security mechanism.

For a tenant-aware API:

```sql
SELECT id, total_amount
FROM orders
WHERE tenant_id = $1
  AND customer_id = $2;
```

the application must still enforce authorization.

Use:

- Parameterized queries.
- Proper tenant authorization.
- Database roles where appropriate.
- Row-Level Security where appropriate.
- Least-privilege database credentials.

Do not expose physical partition names or use partition identifiers as authorization controls.

A malicious or buggy application must not be able to bypass tenant isolation simply by targeting a different partition.

## Scalability Considerations

Hash partitioning can improve scalability inside a single database by distributing table data and reducing the amount of data associated with individual physical partitions.

It does not automatically provide:

- Multiple database servers.
- Independent CPU per partition.
- Independent memory per partition.
- Cross-region scaling.
- Automatic horizontal database scaling.

When a single PostgreSQL instance becomes the bottleneck, possible next steps include:

```text
Optimization
     │
     ├── Better indexes
     ├── Query optimization
     ├── Connection pooling
     ├── Caching
     ├── Read replicas
     ├── Vertical scaling
     └── Sharding
```

Partitioning should be viewed as one layer in the database scaling strategy.

## High Availability

Hash partitions normally live within the same database availability boundary.

High availability therefore depends on the database architecture, not merely on partitioning.

For PostgreSQL deployments, evaluate:

- Streaming replication.
- Automated failover.
- Synchronous vs asynchronous replication requirements.
- Backup strategy.
- Point-in-time recovery.
- Replica monitoring.
- Recovery testing.

A partitioned table does not become highly available simply because it has multiple partitions.

## Backup and Disaster Recovery

Partitioning does not eliminate the need for database-level backup and recovery.

Validate that:

- All partitions are included in backups.
- Partition definitions are recoverable.
- Indexes can be rebuilt when appropriate.
- Schema migrations are version-controlled.
- Point-in-time recovery has been tested.
- Restore procedures work with the complete partition hierarchy.

For large systems, test restoration against realistic partition sizes.

A backup strategy that has never been restored is not a reliable disaster-recovery strategy.

## Cost Considerations

Hash partitioning can reduce operational cost when it improves:

- Query performance.
- Maintenance efficiency.
- Storage management.
- Workload distribution.

But it introduces additional complexity through:

- More indexes.
- More database objects.
- More migrations.
- More monitoring.
- More complex capacity planning.

Partitioning should not be introduced solely because a table is large.

The performance and operational benefits must justify the additional complexity.

## Common Mistakes and Pitfalls

### Assuming Hashing Guarantees Perfect Balance

Hashing generally improves distribution, but hot keys and uneven row counts can still create skew.

Monitor actual partition sizes and workloads.

### Choosing a Low-Cardinality Key

Hashing a column with only a few distinct values provides little benefit.

Use a partition key with enough distinct values to distribute workload effectively.

### Partitioning by `status`

A key such as:

```text
pending
completed
failed
```

usually belongs to list partitioning if partitioning by status is appropriate at all.

Hash partitioning provides little value for such a small domain.

### One Partition per Tenant

Hash partitioning does not mean one physical partition per tenant.

A fixed set of partitions can contain many tenants.

This is one of its major advantages over naïve list partitioning.

### Assuming Hash Partitioning Solves Hot Tenants

A very large tenant can still dominate one partition.

Consider composite strategies or tenant isolation when the workload requires it.

### Ignoring Queries Without the Partition Key

Queries that do not constrain the partition key may scan many or all partitions.

Review real query patterns before selecting the partition key.

### Creating Too Many Partitions

More partitions are not automatically better.

Excessive partition counts increase metadata, index, migration, and monitoring overhead.

### Hard-Coding Partition Names

Application code should normally query:

```sql
FROM orders
```

rather than:

```sql
FROM orders_p3
```

This keeps storage layout independent from business logic.

### Manually Calculating the Database Hash

Do not replicate the database's partition-routing algorithm in application code.

Database-specific hash behavior should remain a database concern.

### Ignoring Repartitioning Costs

Changing the number of hash partitions can require significant data movement.

Treat partition-count changes as potentially disruptive migrations.

### Assuming Partitioning Replaces Indexing

Partition pruning narrows the search space; indexes optimize access inside that search space.

Use both where justified by query patterns.

## Practical Design Example

Suppose a SaaS platform stores:

```text
500 million orders
20 million customers
50,000 tenants
```

Most API requests are:

```sql
WHERE tenant_id = $1
  AND customer_id = $2
```

A possible design is:

```text
orders
│
├── hash partition 0
├── hash partition 1
├── hash partition 2
├── ...
└── hash partition N
```

with:

```sql
PARTITION BY HASH (tenant_id)
```

Indexes inside each partition can then support common tenant/customer queries.

Before implementing the design, validate:

1. Tenant sizes are reasonably distributed.
2. Queries consistently constrain `tenant_id`.
3. The expected partition count is operationally manageable.
4. Hot tenants will not overwhelm individual partitions.
5. The resulting query plans actually prune partitions.
6. Migration and backup procedures support the partition hierarchy.

If these assumptions do not hold, another strategy may be better.

## Decision Guide

| Requirement | Recommended Strategy |
|---|---|
| Data naturally divided by time | Range |
| Stable categorical groups | List |
| High-cardinality identifiers and even distribution | Hash |
| Millions of tenants with tenant-filtered queries | Hash candidate |
| Regional data management | List |
| Time-based retention | Range |
| Large hot tenants | Hash plus additional strategy |
| Data must span multiple database servers | Sharding |
| Queries rarely use the proposed partition key | Avoid partitioning |

Partitioning should follow the workload rather than the other way around.

## Production Checklist

- [ ] Identify the dominant query patterns.
- [ ] Choose a high-cardinality partition key when using hash partitioning.
- [ ] Verify that common queries filter on the partition key.
- [ ] Estimate expected partition count and growth.
- [ ] Measure key and row distribution.
- [ ] Check for hot tenants or hot keys.
- [ ] Design indexes independently from the partitioning strategy.
- [ ] Verify partition pruning using `EXPLAIN`.
- [ ] Avoid hard-coding partition names in application code.
- [ ] Avoid calculating partition routing in application code.
- [ ] Test partition-count changes against production-scale data.
- [ ] Measure WAL, replication, and locking impact of migrations.
- [ ] Monitor rows, storage, reads, writes, and latency per partition.
- [ ] Automate partition schema changes through CI/CD.
- [ ] Include all partitions in backup and disaster-recovery testing.
- [ ] Reassess the design when workload distribution changes significantly.

## Interview Perspective

A strong senior-level answer should distinguish hash partitioning from list partitioning, range partitioning, and sharding.

A concise explanation is:

> **Hash partitioning distributes rows across a fixed set of partitions using a hash of the partition key. It is useful for high-cardinality keys such as tenant IDs or customer IDs when even distribution is more important than business-readable partition boundaries. Queries that constrain the partition key can benefit from partition pruning. The main concerns are partition count, data skew, hot keys, repartitioning cost, indexes, and operational complexity.**

Common follow-up questions include:

- Why use hash partitioning instead of list partitioning?
- Why is a high-cardinality key usually a better candidate?
- Does hash partitioning guarantee equal data distribution?
- What happens when one tenant is much larger than the others?
- What happens when the partition count changes?
- Does hash partitioning replace indexes?
- What happens to queries that do not use the partition key?
- How is hash partitioning different from sharding?
- Can hash partitioning improve write distribution?
- How would you monitor partition skew?
- When would you combine range and hash partitioning?

The strongest answer emphasizes that **hash partitioning is primarily a distribution strategy**. It can improve query and write behavior, but it does not automatically solve database scalability, hot-key problems, or distributed-system requirements.

## Key Takeaways

- **Hash partitioning distributes rows across a fixed set of partitions using a hash of the partition key and is well suited to high-cardinality identifiers.**
- **The partition key should match real query patterns; queries without that key may still need to process many or all partitions.**
- **Hash partitioning improves distribution but does not guarantee perfect balance or eliminate hot-key and hot-tenant problems.**
- **Partition count, repartitioning cost, index management, monitoring, and backup procedures are important production concerns.**
- **Hash partitioning operates within a database, while sharding distributes data across independent database nodes or instances.**