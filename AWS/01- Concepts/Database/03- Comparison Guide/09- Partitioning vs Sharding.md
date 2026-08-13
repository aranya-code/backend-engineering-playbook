# Partitioning vs Sharding

Both techniques split data into smaller pieces. The critical difference: partitioning happens inside a single database instance, sharding spreads data across multiple independent instances. One is a storage optimization. The other is an architectural decision you can't easily undo.

---

## Partitioning (Single Instance)

The database engine splits a logical table into physical segments stored on the same instance. The app sees one table. The engine manages the segments internally.

```
┌─────────────────────────────────────────────────┐
│              Single DB Instance                 │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │         Logical Table: orders             │   │
│  ├──────────────────────────────────────────┤   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ │   │
│  │  │Partition │ │Partition │ │Partition │ │   │
│  │  │ 2024-Q1  │ │ 2024-Q2  │ │ 2024-Q3  │ │   │
│  │  │ 2.1M rows│ │ 2.4M rows│ │ 2.8M rows│ │   │
│  │  └──────────┘ └──────────┘ └──────────┘ │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
│  Single query engine, single transaction scope  │
└─────────────────────────────────────────────────┘
```

### PostgreSQL Partitioning Types

**Range Partitioning** — Split by value ranges. Ideal for time-series data.

```sql
CREATE TABLE orders (
    id         BIGSERIAL,
    customer_id INT,
    created_at  TIMESTAMPTZ,
    total       DECIMAL(10,2)
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
```

**List Partitioning** — Split by discrete values. Ideal for categorical data.

```sql
CREATE TABLE orders (
    id     BIGSERIAL,
    region TEXT,
    total  DECIMAL(10,2)
) PARTITION BY LIST (region);

CREATE TABLE orders_us PARTITION OF orders FOR VALUES IN ('us-east', 'us-west');
CREATE TABLE orders_eu PARTITION OF orders FOR VALUES IN ('eu-west', 'eu-central');
```

**Hash Partitioning** — Split by hash of column value. Even distribution when no natural range or list exists.

```sql
CREATE TABLE orders (
    id          BIGSERIAL,
    customer_id INT,
    total       DECIMAL(10,2)
) PARTITION BY HASH (customer_id);

CREATE TABLE orders_p0 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE orders_p1 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE orders_p2 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE orders_p3 PARTITION OF orders FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### Partition Pruning

The real performance win. When your query includes the partition key in the WHERE clause, PostgreSQL skips irrelevant partitions entirely.

```sql
-- Scans ONLY orders_2024_q1, ignores Q2 and Q3
EXPLAIN SELECT * FROM orders WHERE created_at = '2024-02-15';
-- Output includes: "Partitions selected: orders_2024_q1"
```

Without the partition key in the predicate, the engine scans all partitions — you get zero benefit and pay overhead for partition management.

---

## Sharding (Multiple Instances)

Data is distributed across completely independent database instances. Each shard is a standalone database with its own compute, storage, and connection limits.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Shard 0    │     │  Shard 1    │     │  Shard 2    │
│  (RDS #1)   │     │  (RDS #2)   │     │  (RDS #3)   │
│             │     │             │     │             │
│ customer_id │     │ customer_id │     │ customer_id │
│  0 - 999    │     │ 1000 - 1999 │     │ 2000 - 2999 │
│             │     │             │     │             │
│ Independent │     │ Independent │     │ Independent │
│ storage,    │     │ storage,    │     │ storage,    │
│ compute,    │     │ compute,    │     │ compute,    │
│ backups     │     │ backups     │     │ backups     │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────┬───────┘───────────────────┘
                   ▼
          ┌────────────────┐
          │  Shard Router  │
          │  (App / Proxy) │
          │                │
          │ route(cust_id) │
          │ = cust_id % 3  │
          └────────────────┘
                   ▲
                   │
          ┌────────────────┐
          │  Application   │
          └────────────────┘
```

### Shard Routing Strategies

**Hash-based:** `shard_id = hash(shard_key) % num_shards`. Even distribution but resharding requires data migration. Consistent hashing minimizes migration when adding shards.

**Range-based:** `shard_id = lookup(range_table, shard_key)`. Natural for time-series or geographic splits. Risk of hot shards if ranges are uneven.

**Directory-based:** A lookup table maps each key to its shard. Maximum flexibility but the directory becomes a single point of failure and a bottleneck.

---

## DynamoDB: Automatic Partitioning

DynamoDB abstracts away both partitioning and sharding. You pick a partition key; the service handles the rest.

**How it works:** DynamoDB hashes the partition key to assign items to internal partitions. Each partition handles up to 3,000 RCU or 1,000 WCU and stores up to 10 GB. When limits are hit, the partition splits automatically.

**Hot partition problem:** If your partition key has low cardinality (e.g., `status = "active"` for 95% of items), most traffic hits a single partition. The fix: design high-cardinality partition keys. Use composite keys like `customer_id#order_date` or add synthetic suffixes for write-heavy keys.

**Adaptive capacity:** DynamoDB automatically redistributes throughput to hot partitions, but this only mitigates — it doesn't eliminate — poor key design. A single partition can still bottleneck if it receives sustained disproportionate traffic.

---

## Cross-Shard Queries

This is where sharding hurts the most.

**Scatter-Gather:** Query all shards in parallel, merge results in the application. Works for aggregations (COUNT, SUM) but adds latency proportional to the slowest shard.

```
App ──► Shard 0: SELECT COUNT(*) WHERE status='active' ──► 1,234
    ──► Shard 1: SELECT COUNT(*) WHERE status='active' ──► 2,456
    ──► Shard 2: SELECT COUNT(*) WHERE status='active' ──► 1,890
                                                    Total: 5,580
```

**Cross-shard JOINs:** Don't. Joining data across shards means pulling rows from multiple databases into the application and joining in memory. It's slow, resource-intensive, and defeats the purpose of sharding. Denormalize or maintain materialized views instead.

**Cross-shard transactions:** Two-phase commit across independent databases is fragile and slow. Use saga patterns with compensating transactions, or redesign so transactions stay within a single shard boundary.

---

## Comparison Table

| Dimension                  | Partitioning                     | Sharding                          |
|----------------------------|----------------------------------|-----------------------------------|
| **Scope**                  | Single DB instance               | Multiple independent instances    |
| **Transparency**           | Fully transparent to app         | App must know routing logic       |
| **Query across segments**  | Native SQL (cross-partition)     | Scatter-gather (app-level)        |
| **JOINs across segments**  | Native (same instance)           | Impractical — denormalize instead |
| **Transactions**           | Full ACID (single instance)      | Distributed — complex, fragile   |
| **Scaling limit**          | Single instance ceiling          | Practically unlimited             |
| **Write throughput**       | Single instance limit            | Scales with number of shards      |
| **Read throughput**        | Single instance limit            | Scales with number of shards      |
| **Partition pruning**      | Yes (query optimizer)            | Yes (shard router skips shards)   |
| **Rebalancing**            | Automatic (DB engine)            | Manual or semi-automated migration|
| **Operational complexity** | Low (single DB to manage)        | High (N databases to manage)      |
| **Backup/restore**         | Single snapshot                  | Per-shard snapshots, coordination |
| **Schema changes**         | Single DDL                       | Must apply to every shard         |
| **Connection pooling**     | Single pool                      | Pool per shard                    |
| **Failure blast radius**   | Entire table unavailable         | Only affected shard unavailable   |

---

## Decision Guidance

### When to Partition (Not Shard)

- Table is large but fits on a single instance (storage and compute)
- You need faster queries on time-range data (partition pruning eliminates 90%+ of scans)
- You want easier maintenance — `DROP` old partitions instead of `DELETE` millions of rows
- You need full ACID transactions across the entire dataset
- Team doesn't have the operational maturity for distributed databases

### When to Shard

- Single instance can't handle the write throughput (you've already maxed vertical scaling)
- Dataset exceeds single-instance storage limits
- You need fault isolation — one shard's failure shouldn't take down the entire system
- Geographic distribution requires data locality (users in EU query EU shard)
- You've already partitioned and still hit single-instance limits

### The Escalation Path

```
Single table (no partitioning)
        │
        ▼  Table > 100M rows or slow time-range queries
Partitioned table (same instance)
        │
        ▼  Instance CPU/storage maxed, write throughput bottleneck
Read replicas (horizontal read scaling)
        │
        ▼  Write throughput still bottlenecked on single primary
Sharded across multiple instances
```

---

## Interview-Ready Explanation

> "Partitioning splits a table into segments within a single database instance. PostgreSQL supports range, list, and hash partitioning. The key benefit is partition pruning — when the query includes the partition key, the optimizer skips irrelevant partitions entirely, dramatically reducing scan time. You keep full ACID transactions and can JOIN across partitions natively because everything is on the same instance.
>
> Sharding distributes data across multiple independent database instances. Each shard is a standalone database with its own compute and storage. The application or a proxy routes queries to the correct shard based on a shard key. You gain horizontal write scaling and fault isolation, but you lose cross-shard JOINs, distributed transactions become complex, and every operational task — schema changes, backups, monitoring — multiplies by the number of shards.
>
> The decision path is straightforward: partition first for query performance and maintenance wins. Move to sharding only when the single instance can't handle the write load or storage volume, and you've already exhausted vertical scaling and read replicas."

---

## Key Takeaways

1. **Partitioning is a query optimization.** It makes a big table perform like several small tables, without any application changes.
2. **Sharding is an architectural decision.** It scales writes beyond a single instance but fundamentally changes how your application interacts with the database.
3. **Partition pruning only works** when the partition key appears in the WHERE clause. Design partitions around your most common query patterns.
4. **Avoid cross-shard JOINs.** Denormalize aggressively or use materialized views. If you need frequent cross-shard queries, reconsider whether sharding is the right choice.
5. **DynamoDB handles partitioning for you** but punishes poor key design. High-cardinality partition keys are non-negotiable.
6. **The hot partition problem** applies to both partitioning and sharding. Uneven key distribution defeats the purpose of splitting data.
7. **Partition first, shard last.** Sharding is expensive in engineering time, operational complexity, and lost capabilities. Exhaust simpler options before committing to it.
