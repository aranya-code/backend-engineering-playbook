# Database Partitioning

When a table grows past 100 million rows, even well-indexed queries start to degrade. Vacuum takes hours. Index rebuilds lock production. Backup windows stretch. Partitioning solves this by splitting a single logical table into multiple physical segments, each independently manageable. This guide covers the partitioning strategies, the internals, and the production patterns that keep large-scale systems fast.

---

## What Is Partitioning?

Partitioning divides a table into smaller, physically separate pieces (partitions) based on a column value (partition key). The database treats partitions as a single logical table — your queries do not change. But under the hood, the planner can skip entire partitions that do not match the query predicate. This is called **partition pruning**.

```
  Without Partitioning                 With Partitioning (by year)
  ┌────────────────────────┐          ┌─────────────────┐
  │     orders             │          │ orders_2023     │  100M rows
  │     500M rows          │          ├─────────────────┤
  │     (full scan)        │          │ orders_2024     │  150M rows
  │                        │          ├─────────────────┤
  └────────────────────────┘          │ orders_2025     │  200M rows
                                      ├─────────────────┤
  Query scans 500M rows               │ orders_2026     │   50M rows
                                      └─────────────────┘

                                      Query for 2025 scans only 200M rows
                                      (60% reduction in I/O)
```

---

## Horizontal vs Vertical Partitioning

### Horizontal Partitioning

Splits rows across partitions. Every partition has the same columns but contains a subset of rows. This is what most people mean when they say "partitioning."

```
  Original Table: users (10M rows, 20 columns)
  ┌─────────────────────────────────────────────────┐
  │ id │ name   │ region │ email   │ ... 17 cols    │
  ├────┼────────┼────────┼─────────┼────────────────┤
  │ 1  │ Alice  │ US     │ a@x.com │ ...            │
  │ 2  │ Bob    │ EU     │ b@y.com │ ...            │
  │ 3  │ Carol  │ US     │ c@z.com │ ...            │
  │ ...│ ...    │ ...    │ ...     │ ...            │
  └────┴────────┴────────┴─────────┴────────────────┘
                       │
            Horizontal Partition by region
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────────┐
  │ users_us    │ │ users_eu │ │ users_apac   │
  │ 4M rows     │ │ 3M rows  │ │ 3M rows      │
  │ (all cols)  │ │(all cols)│ │ (all cols)    │
  └─────────────┘ └──────────┘ └──────────────┘
```

### Vertical Partitioning

Splits columns across tables. Each partition has the same rows but contains a subset of columns. Useful when some columns are accessed frequently and others (like BLOBs or text fields) are rarely read.

```
  Original Table: products (5M rows, 30 columns)
  ┌──────────────────────────────────────────────────┐
  │ id │ name │ price │ description │ image │ specs  │
  └──────────────────────────────────────────────────┘
                        │
             Vertical Partition by access pattern
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
  ┌────────────────────┐    ┌─────────────────────────┐
  │ products_core      │    │ products_detail         │
  │ (hot columns)      │    │ (cold columns)          │
  │ id, name, price    │    │ id, description, image, │
  │ 5M rows × 3 cols   │    │ specs                   │
  │ ~50 MB             │    │ 5M rows × 4 cols        │
  └────────────────────┘    │ ~2 GB                   │
                            └─────────────────────────┘

  Listing query reads 50 MB instead of 2 GB
```

**Vertical partitioning is usually done manually** by splitting into separate tables with a shared primary key. Horizontal partitioning is natively supported by most databases.

---

## Horizontal Partitioning Strategies

### Range Partitioning

Partition by value ranges. Most common for time-series data.

```sql
-- PostgreSQL native range partitioning
CREATE TABLE orders (
    order_id    BIGSERIAL,
    customer_id INT NOT NULL,
    order_date  DATE NOT NULL,
    total       DECIMAL(10,2),
    status      VARCHAR(20)
) PARTITION BY RANGE (order_date);

CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
CREATE TABLE orders_2024_q3 PARTITION OF orders
    FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');
CREATE TABLE orders_2024_q4 PARTITION OF orders
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
CREATE TABLE orders_2025_q1 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
```

**Use when:** Data has a natural ordering (dates, timestamps, monotonically increasing IDs) and queries almost always filter on the partition key.

### List Partitioning

Partition by discrete values. Ideal for geographical or categorical splits.

```sql
CREATE TABLE customers (
    customer_id BIGSERIAL,
    name        VARCHAR(100),
    region      VARCHAR(10) NOT NULL,
    email       VARCHAR(255)
) PARTITION BY LIST (region);

CREATE TABLE customers_us   PARTITION OF customers FOR VALUES IN ('US');
CREATE TABLE customers_eu   PARTITION OF customers FOR VALUES IN ('EU');
CREATE TABLE customers_apac PARTITION OF customers FOR VALUES IN ('APAC');
CREATE TABLE customers_other PARTITION OF customers DEFAULT;
```

**Use when:** You have a small, well-defined set of partition values and queries consistently filter on them.

### Hash Partitioning

Partition by a hash of the key value. Distributes rows evenly regardless of data distribution.

```sql
CREATE TABLE events (
    event_id    BIGSERIAL,
    user_id     INT NOT NULL,
    event_type  VARCHAR(50),
    payload     JSONB,
    created_at  TIMESTAMPTZ
) PARTITION BY HASH (user_id);

CREATE TABLE events_p0 PARTITION OF events FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE events_p1 PARTITION OF events FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE events_p2 PARTITION OF events FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE events_p3 PARTITION OF events FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

**Use when:** No natural range or list applies, and you want uniform data distribution. Hash partitioning does not support partition pruning on range queries — only equality.

| Strategy | Best For                   | Supports Range Pruning | Supports Equality Pruning | Data Distribution |
|----------|----------------------------|:----------------------:|:-------------------------:|-------------------|
| Range    | Time-series, ordered data  | ✅                      | ✅                         | Can be uneven     |
| List     | Categories, regions        | ❌                      | ✅                         | Depends on data   |
| Hash     | Uniform distribution       | ❌                      | ✅                         | Even by design    |

---

## Partition Pruning

Partition pruning is the query planner's ability to skip partitions that cannot contain matching rows. This is the primary performance benefit of partitioning.

```sql
-- This query only scans orders_2025_q1 partition
EXPLAIN SELECT * FROM orders WHERE order_date = '2025-02-15';
```

```
Append  (cost=0.00..18.50 rows=4 width=52)
  ->  Seq Scan on orders_2025_q1  (cost=0.00..18.50 rows=4 width=52)
        Filter: (order_date = '2025-02-15'::date)
```

**Pruning requirements:**

- The query must filter on the partition key
- The filter must use a constant or parameter (not a function result that hides the value)
- PostgreSQL must have `enable_partition_pruning = on` (default since v11)

**Common pitfall:** Wrapping the partition key in a function disables pruning.

```sql
-- BAD: No pruning (function hides the value)
SELECT * FROM orders WHERE EXTRACT(YEAR FROM order_date) = 2025;

-- GOOD: Pruning works (direct comparison on partition key)
SELECT * FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01';
```

---

## Partition Keys — Choosing the Right Column

The partition key determines which partition each row lands in. Choose poorly and you get hot partitions, no pruning, and worse performance than an unpartitioned table.

**Selection criteria:**

1. **Present in most queries** — if 90% of your queries filter on `order_date`, partition by `order_date`. If they filter on `customer_id`, partition by `customer_id`.
2. **Even distribution** — the key should distribute rows roughly evenly across partitions. A key with 99% of values in one bucket creates a hot partition.
3. **Low cardinality for list, high cardinality for range** — list partitioning needs a small set of discrete values. Range partitioning works with continuous values.
4. **Aligns with data lifecycle** — if you need to drop data older than 2 years, partitioning by date lets you `DROP TABLE orders_2023_q1` instead of `DELETE FROM orders WHERE order_date < '2023-04-01'` (which generates massive WAL and takes hours).

---

## The Hot Partition Problem

A hot partition occurs when one partition receives disproportionately more traffic than others.

```
  Hash partitioned by user_id, 4 partitions:

  Normal Distribution:          Hot Partition (power user):
  ┌──────┐ ┌──────┐            ┌──────┐ ┌──────┐
  │ P0   │ │ P1   │            │ P0   │ │ P1   │
  │ 25%  │ │ 25%  │            │ 5%   │ │ 5%   │
  │ ████ │ │ ████ │            │ █    │ │ █    │
  ├──────┤ ├──────┤            ├──────┤ ├──────┤
  │ P2   │ │ P3   │            │ P2   │ │ P3   │
  │ 25%  │ │ 25%  │            │ 5%   │ │ 85%  │ ← HOT
  │ ████ │ │ ████ │            │ █    │ │██████│
  └──────┘ └──────┘            └──────┘ │██████│
                                        └──────┘
```

**Causes:**

- Temporal skew (all today's writes go to the latest range partition)
- Key skew (a few customer_ids generate 80% of traffic)
- Hash collision (rare, but possible with low modulus)

**Mitigations:**

- **Composite partition key** — partition by `(region, order_date)` to spread writes
- **Sub-partitioning** — partition by date at the top level, then by hash within each date partition
- **Write sharding at application level** — distribute writes across partitions using a shard key
- **DynamoDB adaptive capacity** — DynamoDB automatically redistributes throughput to hot partitions, but extreme skew still causes throttling

---

## PostgreSQL Table Partitioning

PostgreSQL has supported **declarative partitioning** since v10 (range, list) and v11 (hash). Key operational details:

```sql
-- Create indexes on partitioned tables (automatically applied to all partitions)
CREATE INDEX idx_orders_customer ON orders (customer_id);

-- Each partition gets its own copy of the index:
-- idx_orders_customer_orders_2024_q1
-- idx_orders_customer_orders_2024_q2
-- ...
```

**Operational considerations:**

| Operation                | Unpartitioned       | Partitioned                               |
|--------------------------|---------------------|-------------------------------------------|
| Adding new partition     | N/A                 | `CREATE TABLE ... PARTITION OF` (instant)  |
| Dropping old data        | `DELETE` (slow, WAL)| `DROP TABLE partition` (instant, no WAL)   |
| VACUUM                   | Entire table        | Per-partition (parallel, smaller)          |
| Index rebuild            | Entire table        | Per-partition (less lock contention)       |
| Unique constraint        | Global              | Must include partition key                 |
| Foreign keys (referencing)| Supported          | Not supported until PG 12                 |

**Critical limitation:** Unique constraints and primary keys on partitioned tables **must include the partition key**. You cannot have a globally unique `order_id` across partitions unless `order_id` is part of the partition key or you use a sequence (which guarantees uniqueness across partitions at the generation level, not the constraint level).

```sql
-- This FAILS on a partitioned table:
-- PRIMARY KEY (order_id)

-- This WORKS:
PRIMARY KEY (order_id, order_date)  -- partition key included
```

---

## DynamoDB Partition Keys

DynamoDB partitions data automatically based on the partition key (hash key). You do not control the number of partitions — DynamoDB manages this internally.

```
  DynamoDB Table: Orders
  Partition Key: customer_id
  Sort Key: order_date

  ┌──────────────────────────────────────────┐
  │           DynamoDB Internal              │
  │                                          │
  │  Partition A          Partition B         │
  │  (hash range 0-33%)   (hash range 34-66%)│
  │  ┌────────────────┐  ┌────────────────┐  │
  │  │ customer_id=1  │  │ customer_id=42 │  │
  │  │  2025-01-01    │  │  2025-03-15    │  │
  │  │  2025-01-15    │  │  2025-04-01    │  │
  │  │ customer_id=7  │  │ customer_id=99 │  │
  │  │  2025-02-01    │  │  2025-05-20    │  │
  │  └────────────────┘  └────────────────┘  │
  │                                          │
  │  Partition C                             │
  │  (hash range 67-100%)                    │
  │  ┌────────────────┐                      │
  │  │ customer_id=55 │                      │
  │  │  2025-01-10    │                      │
  │  │  2025-06-30    │                      │
  │  └────────────────┘                      │
  └──────────────────────────────────────────┘
```

**Partition key design rules for DynamoDB:**

1. **High cardinality** — the partition key should have many distinct values (e.g., `user_id`, `device_id`). Using `status` (3 values) as a partition key creates 3 hot partitions.
2. **Uniform access** — avoid keys where a small number of values receive most of the traffic. A viral post with `post_id` as PK gets all reads on one partition.
3. **Composite keys for access patterns** — use `PK=CUSTOMER#42`, `SK=ORDER#2025-01-15` to enable both point lookups and range queries within a partition.

**Write sharding for hot keys:**

```
  Instead of:  PK = "trending_post_123"  (all writes hit one partition)

  Use:         PK = "trending_post_123#shard_0"  (random suffix 0-9)
               PK = "trending_post_123#shard_1"
               ...
               PK = "trending_post_123#shard_9"

  Scatter writes across 10 partitions, aggregate reads.
```

---

## Real-World Example: Partitioning Orders by Date Range

### Problem

An e-commerce platform has an `orders` table with 800 million rows spanning 5 years. Queries for recent orders (last 30 days) scan the full table despite indexes. Nightly `VACUUM` takes 4 hours. Archiving old data requires `DELETE` statements that generate massive WAL and cause replication lag.

### Solution: Quarterly Range Partitioning

```sql
-- Step 1: Create partitioned table
CREATE TABLE orders_partitioned (
    order_id    BIGSERIAL,
    customer_id INT NOT NULL,
    order_date  DATE NOT NULL,
    total       DECIMAL(10,2),
    status      VARCHAR(20),
    PRIMARY KEY (order_id, order_date)
) PARTITION BY RANGE (order_date);

-- Step 2: Create partitions for each quarter
-- (automated via pg_partman extension)
SELECT partman.create_parent(
    p_parent_table := 'public.orders_partitioned',
    p_control := 'order_date',
    p_type := 'range',
    p_interval := '3 months',
    p_premake := 4  -- create 4 future partitions
);

-- Step 3: Migrate data (done in batches during low traffic)
INSERT INTO orders_partitioned
SELECT * FROM orders_old
WHERE order_date >= '2024-01-01' AND order_date < '2024-04-01';
-- Repeat for each quarter...

-- Step 4: Drop old data (instant, no DELETE)
DROP TABLE orders_partitioned_2021_q1;
DROP TABLE orders_partitioned_2021_q2;
```

### Results

| Metric                  | Before Partitioning | After Partitioning     |
|-------------------------|---------------------|-----------------------|
| Recent orders query     | 450ms (full scan)   | 12ms (single partition)|
| VACUUM runtime          | 4 hours             | 15 min per partition   |
| Data archival           | 2 hours DELETE       | Instant DROP TABLE     |
| Replication lag (archive)| 30 minutes          | <1 second             |
| Storage reclaim         | Manual `VACUUM FULL` | Automatic with DROP   |

---

## When to Partition

Partitioning adds complexity. Do not partition a table unless you have a clear performance or operational reason.

```
  Decision Criteria:
  ┌────────────────────────────────────────────────┐
  │ Table size > 100M rows?                        │
  │   → YES: Consider partitioning                 │
  │   → NO:  Indexes are sufficient                │
  ├────────────────────────────────────────────────┤
  │ Need to archive/drop old data regularly?       │
  │   → YES: Range partition by date               │
  │   → NO:  May not need partitioning             │
  ├────────────────────────────────────────────────┤
  │ Queries consistently filter on one column?     │
  │   → YES: Good partition key candidate          │
  │   → NO:  Partitioning may not help             │
  ├────────────────────────────────────────────────┤
  │ VACUUM / maintenance takes too long?           │
  │   → YES: Partitioning reduces maintenance scope│
  │   → NO:  Indexes are sufficient                │
  └────────────────────────────────────────────────┘
```

---

## Partition Management Overhead

Partitioning is not free. It adds operational complexity that you must plan for.

- **Partition creation** — new partitions must be created before data arrives. Use `pg_partman` or cron jobs to pre-create future partitions. A missing partition causes INSERT failures.
- **Global unique constraints** — unique indexes must include the partition key. This limits some schema designs.
- **Cross-partition queries** — queries that do not filter on the partition key scan all partitions (partition-wise join helps, but is not always faster than a single large table).
- **Too many partitions** — hundreds of partitions slow down the planner. Keep partition count under 1000. Use quarterly instead of daily partitions for most workloads.
- **pg_dump complexity** — backing up and restoring partitioned tables requires careful handling of partition definitions.
- **ORM compatibility** — some ORMs do not handle partitioned tables well. Test your ORM's INSERT and SELECT behavior with partitioned tables before committing.

---

## Common Mistakes

1. **Partitioning small tables** — a table with 10M rows and proper indexes does not need partitioning. The overhead of managing partitions outweighs any benefit. Wait until you hit 100M+ rows or have a clear operational need (data lifecycle management).
2. **Choosing the wrong partition key** — partitioning by a column that is rarely used in WHERE clauses means the planner cannot prune partitions. Every query scans all partitions, making performance worse due to overhead.
3. **Creating too many partitions** — daily partitions on a 10-year dataset means 3,650 partitions. The planner evaluates every partition for each query. Use monthly or quarterly intervals.
4. **Forgetting to pre-create partitions** — with range partitioning, if no partition exists for an incoming value, the INSERT fails. Automate partition creation with `pg_partman` or scheduled scripts that create partitions months in advance.
5. **Wrapping partition key in functions** — `WHERE YEAR(order_date) = 2025` prevents partition pruning. Use `WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'` instead.

---

## Interview Questions

**Q1: What is the difference between partitioning and sharding?**

Partitioning splits a table within a single database instance. All partitions reside on the same server and are managed by the same database engine. Sharding distributes data across multiple independent database instances (different servers). Partitioning is transparent to the application — the database handles routing. Sharding typically requires application-level routing logic or a proxy layer. You can combine both: shard across servers, then partition within each shard.

**Q2: You have a table with 500M rows partitioned by month. Queries that filter by customer_id (not the partition key) are slow. What do you do?**

Three options: (1) Add an index on `customer_id` to each partition — this allows index scans within each partition but still requires scanning all partition indexes. (2) Consider sub-partitioning by hash on `customer_id` within each monthly partition — but this multiplies partition count and adds complexity. (3) Re-evaluate the partition key — if most queries filter on `customer_id`, partition by `customer_id` (hash) instead of by month. The best choice depends on the query distribution: if 80% of queries filter on date and 20% on customer_id, keep date partitioning and add the customer_id index.

**Q3: How does DynamoDB handle hot partitions differently from PostgreSQL?**

DynamoDB has adaptive capacity — it automatically redistributes provisioned throughput from underutilized partitions to hot partitions. It also supports burst capacity using accumulated unused credits. However, extreme hot-key scenarios (single item receiving thousands of writes/second) still cause throttling. PostgreSQL has no such mechanism — a hot partition simply gets all the I/O, and you must manually re-partition or add sub-partitions to redistribute load.

**Q4: When would you use hash partitioning over range partitioning?**

Hash partitioning when: (1) you need uniform data distribution and have no natural ordering, (2) queries primarily use equality filters on the partition key, (3) you want to avoid temporal hot spots (all today's writes hitting the latest partition). Range partitioning when: (1) data has a natural time ordering, (2) queries use range filters, (3) you need to drop old data efficiently. In practice, range partitioning is far more common because most large tables are time-series or event-driven.

---

## Key Takeaways

- **Partition when tables exceed 100M rows** or when you need efficient data lifecycle management (dropping old data). Below that threshold, indexes are sufficient.
- **Range partitioning by date is the most common strategy** — it aligns with time-series access patterns and enables instant data archival via `DROP TABLE`.
- **Partition pruning is the primary benefit** — if your queries do not filter on the partition key, partitioning provides no read performance improvement and may make things worse.
- **The hot partition problem is real** — monitor partition sizes and query distribution. Use composite keys or sub-partitioning to spread load.
- **Automate partition management** — use `pg_partman` in PostgreSQL or equivalent tools to pre-create future partitions and drop expired ones. Manual management does not scale.
- **Partitioning and sharding are different** — partitioning is within one database instance (transparent), sharding is across multiple instances (requires routing logic). Know when each applies.
