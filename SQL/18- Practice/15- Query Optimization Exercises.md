# 15- Query Optimization Exercises

## Overview

Query optimization is the process of improving SQL workload performance by changing the query, indexes, data access pattern, schema, execution environment, or architecture.

For senior backend engineers, optimization should not mean:

> "Add an index until the query becomes fast."

The correct approach is evidence-driven:

```text
Slow endpoint / workload
        ↓
Measure end-to-end latency
        ↓
Identify SQL + frequency + parameters
        ↓
Inspect execution plan
        ↓
Separate CPU / I/O / locking / network / pooling
        ↓
Identify root cause
        ↓
Rewrite query / improve index / change workload
        ↓
Benchmark
        ↓
Deploy safely
        ↓
Monitor for regression
```

These exercises use PostgreSQL and focus on the reasoning required to optimize real backend workloads.

---

## Practice Schema

Use the following schema for the exercises:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint NOT NULL,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint NOT NULL,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status text NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    total_amount numeric(12, 2) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE order_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    product_id bigint NOT NULL,
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL
);

CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    status text NOT NULL
        CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    amount numeric(12, 2) NOT NULL,
    paid_at timestamptz
);
```

For meaningful performance exercises, use production-like cardinality and distribution.

Example:

```sql
INSERT INTO customers (
    tenant_id,
    email,
    name,
    status
)
SELECT
    ((g - 1) % 1000) + 1,
    'customer-' || g || '@example.com',
    'Customer ' || g,
    CASE
        WHEN g % 20 = 0 THEN 'inactive'
        ELSE 'active'
    END
FROM generate_series(1, 500000) AS g;
```

---

## Optimization Principles

Before solving any exercise, distinguish these problems:

| Problem | Typical symptom | Potential solution |
|---|---|---|
| Poor access path | Large scans | Index/query rewrite |
| Bad cardinality estimate | Wrong join/scan strategy | Statistics/data-model investigation |
| N+1 | Huge query count | ORM/query-shape redesign |
| Lock contention | High wait time | Shorter transactions/concurrency redesign |
| Connection exhaustion | Pool wait | Pool/concurrency redesign |
| Large result transfer | Network/app latency | Projection/pagination |
| CPU-heavy query | High DB CPU | Query/index/aggregation optimization |
| I/O-heavy query | High reads | Access path/cache/storage |
| Sort/hash spill | Temporary I/O | Query/index/memory strategy |
| Replica lag | Stale/slow reads | Workload routing/replica capacity |
| Repeated expensive reads | High frequency | Caching/materialization |
| Analytical workload | OLTP degradation | Workload isolation/OLAP |

Do not optimize based solely on elapsed query time.

---

## Establish a Baseline

Before modifying a query, capture:

- SQL text.
- Parameters or representative parameter distributions.
- Execution frequency.
- Mean latency.
- p95/p99 latency.
- Rows returned.
- Rows scanned.
- CPU.
- Buffer hits.
- Buffer reads.
- Temporary I/O.
- Lock waits.
- Connection-pool wait.
- Replica lag if applicable.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 12345;
```

For workload-level analysis:

```sql
SELECT
    calls,
    total_exec_time,
    mean_exec_time,
    rows,
    shared_blks_hit,
    shared_blks_read,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

A query with 5 ms latency executed 100,000 times may matter more than a 2-second query executed once per day.

---

## Exercise: Find the Slow Query

Suppose an API endpoint is slow:

```text
GET /customers/12345/orders
```

The application executes:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC;
```

### Tasks

1. Measure the baseline.
2. Run `EXPLAIN (ANALYZE, BUFFERS)`.
3. Determine whether PostgreSQL performs a sequential scan.
4. Determine how many rows are examined.
5. Check existing indexes.
6. Determine whether a composite index would improve both filtering and ordering.
7. Re-run the plan.
8. Compare execution time and buffer usage.

Candidate index:

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC);
```

Do not stop after observing that execution time decreased. Determine why the plan changed.

---

## Exercise: Sequential Scan or Correct Plan?

Consider:

```sql
SELECT *
FROM orders
WHERE status = 'completed';
```

Suppose 95% of orders are completed.

### Tasks

1. Create an index on `status`.
2. Run `EXPLAIN (ANALYZE, BUFFERS)`.
3. Determine whether PostgreSQL uses the index.
4. Explain why a sequential scan may still be optimal.
5. Change the data distribution so that only 1% of rows are completed.
6. Compare the plans.

The goal is to understand:

```text
Index existence
        ≠
Index usefulness
        ≠
Index usage
```

---

## Exercise: `SELECT *` Optimization

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC
LIMIT 50;
```

Rewrite the query to return only the fields required by an API:

```sql
SELECT
    id,
    status,
    total_amount,
    created_at
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC
LIMIT 50;
```

### Tasks

Compare:

- Network transfer.
- Row width.
- Buffer behavior.
- Application deserialization.
- Serialization cost.
- Potential covering-index design.

Explain why reducing selected columns can improve performance even when the same index is used.

---

## Exercise: Optimize `ORDER BY ... LIMIT`

Given:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

Compare:

```sql
CREATE INDEX orders_customer_idx
    ON orders (customer_id);
```

with:

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC);
```

### Tasks

Inspect:

```text
Sort
Index Scan
Bitmap Heap Scan
Rows Removed by Filter
```

Determine whether the composite index allows PostgreSQL to retrieve the required rows in order without an explicit sort.

---

## Exercise: Optimize Keyset Pagination

Consider:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Create:

```sql
CREATE INDEX orders_customer_created_id_idx
    ON orders (customer_id, created_at DESC, id DESC);
```

### Tasks

Compare keyset pagination with:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
OFFSET 100000
LIMIT 50;
```

Increase the offset:

```text
1,000
10,000
100,000
1,000,000
```

Measure how work changes.

Explain why keyset pagination is generally more scalable for deep pagination.

---

## Exercise: N+1 Query Optimization

Suppose a Django endpoint loads:

```python
orders = Order.objects.filter(customer_id=customer_id)

for order in orders:
    print(order.customer.name)
```

Assume this generates:

```text
1 query for orders
+
N queries for customers
```

### Tasks

1. Capture the SQL query count.
2. Identify the N+1 pattern.
3. Determine whether an index solves the architectural problem.
4. Rewrite using:

```python
orders = (
    Order.objects
    .filter(customer_id=customer_id)
    .select_related("customer")
)
```

5. Compare query count.
6. Compare total latency.
7. Compare result size and join cost.

The senior-level optimization is often to reduce the number of round trips, not merely make each round trip faster.

---

## Exercise: Join Optimization

Consider:

```sql
SELECT
    o.id,
    o.total_amount,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.tenant_id = $1
  AND o.status = 'completed';
```

### Tasks

Inspect the execution plan.

Determine:

1. Which table is filtered first.
2. Which join algorithm is chosen.
3. Whether indexes exist for the access pattern.
4. Whether the query returns too many rows.
5. Whether a composite index could improve the order-side access.

Potential candidate:

```sql
CREATE INDEX orders_tenant_status_customer_idx
    ON orders (tenant_id, status, customer_id);
```

Do not assume this is automatically optimal. Validate it against actual cardinality and workload.

---

## Exercise: Nested Loop Investigation

Construct a query where PostgreSQL chooses:

```text
Nested Loop
```

### Tasks

Determine:

- Outer relation.
- Inner relation.
- Number of loops.
- Rows produced per loop.
- Index access on the inner side.
- Total rows examined.

Inspect:

```text
actual time
loops
rows
rows removed by filter
```

Explain why a nested loop can be excellent when the outer relation is small and the inner lookup is indexed, but disastrous when cardinality estimates are wrong.

---

## Exercise: Hash Join Investigation

Construct a join between two sufficiently large relations.

Inspect:

```text
Hash Join
Hash
Seq Scan
```

### Tasks

Determine:

1. Why PostgreSQL selected a hash join.
2. Estimated versus actual rows.
3. Hash table size.
4. Whether memory was sufficient.
5. Whether the query spilled to disk.

Explain when hash joins are useful and why they may become expensive for large inputs.

---

## Exercise: Merge Join Investigation

Create suitable indexes and ordering conditions for a query joining large relations.

### Tasks

Investigate when PostgreSQL chooses:

```text
Merge Join
```

Inspect:

- Sort operations.
- Existing index ordering.
- Join key ordering.
- Estimated cardinality.
- Input sizes.

Explain the trade-off between sorting and leveraging already ordered inputs.

---

## Exercise: Incorrect Cardinality Estimate

Find or construct a query where:

```text
Estimated Rows ≠ Actual Rows
```

For example:

```sql
SELECT *
FROM orders
WHERE tenant_id = 10
  AND status = 'completed';
```

Suppose certain tenants have dramatically different status distributions.

### Tasks

1. Compare estimated and actual rows.
2. Run `ANALYZE`.
3. Determine whether statistics improve the estimate.
4. Investigate extended statistics.
5. Determine whether the poor estimate changes the join or scan strategy.

Explore:

```sql
CREATE STATISTICS orders_tenant_status_stats
    (dependencies, mcv)
    ON tenant_id, status
FROM orders;

ANALYZE orders;
```

The goal is to understand that an index cannot compensate for fundamentally incorrect cardinality assumptions in every workload.

---

## Exercise: Statistics Troubleshooting

Inspect:

```sql
SELECT
    tablename,
    attname,
    n_distinct,
    most_common_vals,
    most_common_freqs,
    histogram_bounds
FROM pg_stats
WHERE tablename = 'orders';
```

### Tasks

Determine:

- Which columns have high cardinality.
- Which have low cardinality.
- Whether skew exists.
- Whether statistics are likely sufficient.
- Whether frequently changing columns require investigation.

Explain how statistics influence optimizer decisions.

---

## Exercise: Function on Indexed Column

Consider:

```sql
SELECT *
FROM orders
WHERE date(created_at) = current_date;
```

### Tasks

Compare with:

```sql
SELECT *
FROM orders
WHERE created_at >= current_date
  AND created_at < current_date + interval '1 day';
```

Determine:

- Which form is more naturally indexable.
- Whether an expression index is necessary.
- How time zones affect correctness.
- How many rows each form scans.

Do not optimize away correctness in timestamp handling.

---

## Exercise: `LIKE` Optimization

Compare:

```sql
SELECT *
FROM customers
WHERE email LIKE 'customer-123%';
```

with:

```sql
SELECT *
FROM customers
WHERE email LIKE '%123%';
```

### Tasks

Determine:

1. Whether the B-tree index can support each query.
2. Why leading wildcards change the access pattern.
3. Whether trigram indexing is appropriate.
4. Whether application-level search normalization would help.

If appropriate:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX customers_email_trgm_idx
    ON customers USING gin (email gin_trgm_ops);
```

Validate rather than assuming GIN is always faster.

---

## Exercise: `OR` and Bitmap Scans

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
   OR status = 'pending';
```

Create:

```sql
CREATE INDEX orders_customer_idx
    ON orders (customer_id);

CREATE INDEX orders_status_idx
    ON orders (status);
```

### Tasks

Inspect whether PostgreSQL uses:

```text
Bitmap Index Scan
Bitmap Heap Scan
```

Determine:

- How the bitmap combines index results.
- Why heap access remains necessary.
- Why a sequential scan may still win when the result set is large.

---

## Exercise: Aggregation Optimization

Consider:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

### Tasks

Investigate:

- Sequential scan.
- Index scan.
- Bitmap scan.
- Hash aggregate.
- Group aggregate.
- Sort.
- Memory usage.

Test:

```sql
CREATE INDEX orders_status_customer_idx
    ON orders (status, customer_id);
```

Determine whether it actually improves the workload.

Explain why:

```text
Filtering
+
Grouping
```

does not automatically mean an index will make the aggregation cheap.

---

## Exercise: Double-Counting Join

Consider:

```sql
SELECT
    o.customer_id,
    SUM(o.total_amount)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
GROUP BY o.customer_id;
```

### Tasks

Determine whether the aggregation is correct.

Explain how multiple `order_items` rows can multiply each order and inflate `SUM(o.total_amount)`.

Rewrite the query so that order totals are aggregated at the correct grain before being joined to item-level data.

The optimization lesson is:

> A fast incorrect query is still a production failure.

---

## Exercise: `EXISTS` Optimization

Consider:

```sql
SELECT
    o.id,
    o.total_amount
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM payments AS p
    WHERE p.order_id = o.id
      AND p.status = 'paid'
);
```

### Tasks

Compare:

```sql
CREATE INDEX payments_order_idx
    ON payments (order_id);
```

with:

```sql
CREATE INDEX payments_paid_order_idx
    ON payments (order_id)
    WHERE status = 'paid';
```

Determine whether the partial index improves the existence check.

Explain why `EXISTS` can stop once a qualifying row is found.

---

## Exercise: `IN` and Large Lists

Compare:

```sql
SELECT *
FROM customers
WHERE id IN (1, 2, 3, 4, 5);
```

with a very large list.

### Tasks

Increase the list size substantially.

Investigate:

- Planning overhead.
- Execution behavior.
- Query text size.
- Network transfer.
- Parameter handling.
- Alternative temporary/staging-table approaches.

For large sets, investigate:

```sql
SELECT c.*
FROM customers AS c
JOIN requested_customers AS r
    ON r.customer_id = c.id;
```

Explain why passing thousands of identifiers through a single SQL statement can become an application and planning concern.

---

## Exercise: Subquery vs Join

Compare:

```sql
SELECT *
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'completed'
);
```

with:

```sql
SELECT DISTINCT c.*
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

Then compare both with:

```sql
SELECT *
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'completed'
);
```

### Tasks

Compare:

- Execution plans.
- Join strategies.
- Cardinality.
- Duplicate elimination.
- Index usage.
- Readability.

The goal is not to memorize that one form is always faster. Let semantics and the planner determine the best approach.

---

## Exercise: CTE Optimization

Consider:

```sql
WITH completed_orders AS (
    SELECT *
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    COUNT(*)
FROM completed_orders
GROUP BY customer_id;
```

### Tasks

Investigate PostgreSQL's treatment of CTEs in the version you are using.

Compare:

```sql
WITH completed_orders AS MATERIALIZED (
    SELECT *
    FROM orders
    WHERE status = 'completed'
)
...
```

with:

```sql
WITH completed_orders AS NOT MATERIALIZED (
    SELECT *
    FROM orders
    WHERE status = 'completed'
)
...
```

Determine when materialization can help and when it can prevent useful predicate pushdown or other planner optimizations.

---

## Exercise: Predicate Pushdown

Consider:

```sql
SELECT *
FROM (
    SELECT
        id,
        customer_id,
        status,
        total_amount
    FROM orders
) AS o
WHERE customer_id = 12345;
```

### Tasks

Inspect the execution plan.

Determine whether PostgreSQL can push the predicate into the underlying scan.

Then construct a more complex query where pushdown becomes less straightforward.

Explain why optimizer transformations should be evaluated from actual plans rather than assumptions about SQL syntax.

---

## Exercise: `DISTINCT` Cost

Consider:

```sql
SELECT DISTINCT customer_id
FROM orders
WHERE status = 'completed';
```

### Tasks

Inspect:

```text
HashAggregate
Sort
Unique
```

depending on the chosen plan.

Determine:

- Input cardinality.
- Number of distinct values.
- Memory requirements.
- Sort/hash behavior.
- Whether an index changes the plan.

Explain why `DISTINCT` can be expensive when the input relation is large.

---

## Exercise: Window Function Optimization

Consider:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC
    ) AS row_number
FROM orders;
```

### Tasks

Inspect:

- Sort operations.
- Partitioning behavior.
- Memory use.
- Number of rows processed.

Then restrict the query to a tenant or customer subset.

Determine whether an index on:

```text
(tenant_id, customer_id, created_at DESC)
```

can reduce work.

Do not assume an index automatically eliminates every sort required by a window function.

---

## Exercise: Latest Row Per Group

Find the latest order for every customer.

Compare:

```sql
SELECT DISTINCT ON (customer_id)
    customer_id,
    id,
    created_at,
    total_amount
FROM orders
ORDER BY customer_id, created_at DESC, id DESC;
```

with a window-function approach:

```sql
SELECT
    customer_id,
    id,
    created_at,
    total_amount
FROM (
    SELECT
        customer_id,
        id,
        created_at,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
) AS ranked
WHERE rn = 1;
```

### Tasks

Compare execution plans.

Investigate:

```sql
CREATE INDEX orders_customer_created_id_idx
    ON orders (customer_id, created_at DESC, id DESC);
```

Explain how index ordering can make `DISTINCT ON` particularly effective for this access pattern.

---

## Exercise: Correlated Subquery

Consider:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count
FROM customers AS c;
```

### Tasks

Determine:

1. Whether the subquery is correlated.
2. How many times it may execute.
3. Whether an index on `orders.customer_id` helps.
4. Whether a grouped join may be more efficient.
5. How the optimizer transforms the query, if at all.

Compare with:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id, c.email;
```

Do not assume correlated subqueries are inherently bad; inspect the actual plan.

---

## Exercise: Sort Spill

Construct a query that requires sorting a large dataset:

```sql
SELECT *
FROM orders
ORDER BY total_amount DESC;
```

### Tasks

Inspect the plan and determine whether the sort fits in memory.

Investigate:

```text
Sort Method
Memory
Disk
```

Then compare:

```sql
ORDER BY total_amount DESC
LIMIT 100;
```

with the full sort.

Explain the difference between sorting a complete dataset and using a top-N strategy.

Do not globally increase `work_mem` merely to hide one expensive query.

---

## Exercise: Hash Aggregate Memory

Consider:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

### Tasks

Determine:

- Number of groups.
- Hash table requirements.
- Whether aggregation spills.
- Whether the query is CPU-bound or I/O-bound.
- Whether partitioning or workload isolation would help.

Investigate the relationship between:

```text
work_mem
×
concurrent operations
×
active queries
```

Explain why increasing `work_mem` globally can create memory pressure under concurrency.

---

## Exercise: Query Frequency Optimization

Suppose these queries have the following characteristics:

| Query | Mean latency | Calls/day |
|---|---:|---:|
| A | 20 ms | 10,000,000 |
| B | 5 seconds | 100 |
| C | 500 ms | 20,000 |
| D | 100 ms | 500,000 |

### Tasks

Rank the queries by optimization priority.

Calculate approximate daily database execution time.

Explain why:

```text
slowest query
```

is not necessarily:

```text
highest-impact query
```

Use total workload cost as part of optimization prioritization.

---

## Exercise: `pg_stat_statements` Investigation

Use:

```sql
SELECT
    queryid,
    calls,
    total_exec_time,
    mean_exec_time,
    rows,
    shared_blks_hit,
    shared_blks_read,
    temp_blks_read,
    temp_blks_written,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

### Tasks

Identify:

1. Highest total execution time.
2. Highest mean execution time.
3. Highest execution count.
4. Highest shared-block reads.
5. Highest temporary I/O.
6. Queries with unusually high rows returned.

Create a prioritization matrix:

| Query | Frequency | Latency | Total Cost | I/O | CPU | Priority |
|---|---:|---:|---:|---:|---:|---|

---

## Exercise: Lock Wait vs Slow Query

Consider a query that appears to take 10 seconds.

### Tasks

Determine whether the query is:

```text
Actually executing for 10 seconds
```

or:

```text
Executing for 100 ms
+
Waiting for a lock for 9.9 seconds
```

Inspect:

```sql
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    query,
    query_start
FROM pg_stat_activity
WHERE state <> 'idle';
```

Investigate blockers using:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    query
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

The optimization is different depending on whether the bottleneck is execution or waiting.

---

## Exercise: Long Transaction

Identify a transaction that keeps a database connection open for an extended period.

### Tasks

Investigate:

```sql
SELECT
    pid,
    state,
    xact_start,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

Determine:

- Transaction duration.
- Whether it is idle in transaction.
- Whether it contributes to lock contention.
- Whether it can delay cleanup.
- Whether application code performs external calls inside the transaction.

Explain why query optimization alone cannot solve problems caused by transaction scope.

---

## Exercise: Connection Pool Amplification

Suppose:

```text
10 Kubernetes pods
20 database connections per pod
5 Celery workers
10 connections per worker
```

### Tasks

Calculate the theoretical connection demand.

Then consider:

```text
Slow query
    ↓
Connections remain busy longer
    ↓
Pool exhaustion
    ↓
Requests wait
    ↓
Retries
    ↓
More concurrent work
    ↓
Database pressure increases
```

Explain why increasing pool size may make the incident worse.

---

## Exercise: Retry Storm

A service retries database operations three times after timeout.

### Tasks

Model:

```text
1 request
→ 1 DB attempt

after timeout:
→ retry 1
→ retry 2
→ retry 3
```

Determine how a database slowdown changes effective query volume.

Design a safer strategy involving:

- Bounded retries.
- Exponential backoff.
- Jitter.
- Idempotency.
- Timeout budgets.
- Circuit breaking where appropriate.

Explain why retry behavior is part of query performance engineering.

---

## Exercise: Replica Performance

A read-heavy API uses a PostgreSQL read replica.

The query is:

```sql
SELECT
    id,
    total_amount,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

### Tasks

Determine:

1. Whether the query is actually faster on the replica.
2. Whether the replica has the same index.
3. Whether replica lag affects freshness.
4. Whether replay conflicts exist.
5. Whether long-running reporting queries are affecting replay.

Compare:

```text
Primary
Replica
Redis
```

as solutions to read scaling.

---

## Exercise: Read-After-Write

A user creates an order:

```text
POST /orders
```

The API immediately requests:

```text
GET /orders/{id}
```

The GET is routed to a replica and does not find the order.

### Tasks

Explain why this can happen.

Design alternatives:

- Route immediately after write to primary.
- Use a consistency token/LSN-aware strategy where appropriate.
- Delay replica routing.
- Use a read-your-writes mechanism at the application layer.

Explain why query optimization cannot fix a consistency-routing problem.

---

## Exercise: Cache vs Query Optimization

Consider:

```sql
SELECT
    COUNT(*),
    SUM(total_amount)
FROM orders
WHERE customer_id = $1
  AND status = 'completed';
```

The query executes 50,000 times per second.

### Tasks

Evaluate:

1. Composite index.
2. Redis cache.
3. Precomputed summary.
4. Materialized view.
5. Event-driven aggregation.

For each, evaluate:

- Freshness.
- Read latency.
- Write complexity.
- Failure behavior.
- Operational cost.

Determine whether the correct optimization is at the query, database, cache, or architecture layer.

---

## Exercise: Large Result Set

Consider:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1;
```

The query returns millions of rows.

### Tasks

Determine whether the problem is:

```text
Query execution
```

or:

```text
Result generation
+
Network transfer
+
Application memory
+
Serialization
+
Client consumption
```

Redesign the API using:

- Projection.
- Pagination.
- Streaming where appropriate.
- Asynchronous export for very large datasets.

Consider:

```text
FastAPI
Celery
Object storage
```

for large exports.

---

## Exercise: API Pagination Strategy

Compare:

```sql
OFFSET 500000 LIMIT 100
```

with keyset pagination.

### Tasks

Measure:

- Rows examined.
- Execution time.
- Buffer usage.
- Performance as page depth increases.

Design an API cursor containing:

```text
created_at
id
```

Explain why the cursor must provide a stable ordering.

---

## Exercise: Large Delete

Consider:

```sql
DELETE FROM orders
WHERE created_at < now() - interval '5 years';
```

### Tasks

Explain why this may cause:

- Large transaction size.
- WAL generation.
- Dead tuples.
- Lock pressure.
- Autovacuum work.
- Replica lag.
- Long recovery time.

Design a safer approach using batching or partition lifecycle operations.

Do not assume query speed alone makes a large delete safe.

---

## Exercise: Large Update

Consider:

```sql
UPDATE orders
SET status = 'completed'
WHERE status = 'processing'
  AND completed_at IS NULL;
```

### Tasks

Determine:

- Number of rows affected.
- Lock duration.
- WAL volume.
- Dead tuple generation.
- Index maintenance.
- Replica impact.

Design an incremental update strategy.

Consider keyset/bounded batches and operational throttling.

---

## Exercise: Partition Pruning

Assume orders are partitioned by:

```text
created_at
```

Compare:

```sql
SELECT *
FROM orders
WHERE created_at >= '2026-01-01'
  AND created_at < '2026-02-01';
```

with:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345;
```

### Tasks

Determine:

1. Which query benefits from partition pruning.
2. Which may need indexes inside partitions.
3. How partition size affects planning/execution.
4. Whether partitioning alone solves customer lookup.

Explain:

```text
Partition pruning
```

and:

```text
Index access
```

as separate optimization mechanisms.

---

## Exercise: Query Plan Regression

A deployment changes:

```text
Plan A → Plan B
```

and p95 latency increases.

### Tasks

Compare:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

before and after.

Investigate:

- Statistics.
- Data distribution.
- Index changes.
- PostgreSQL version.
- Query parameter distribution.
- Generic/custom plans.
- Configuration changes.
- Table growth.

Design a regression detection strategy based on query fingerprints and workload statistics.

---

## Exercise: Generic vs Custom Plans

Prepare a parameterized query whose optimal plan depends heavily on the parameter value.

Example:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND status = 'completed';
```

Suppose one tenant owns 50% of the table while another owns 0.01%.

### Tasks

Investigate PostgreSQL's custom and generic prepared plans.

Determine:

- Why parameter sensitivity matters.
- How a generic plan can be suboptimal.
- How plan selection changes over repeated executions.
- Whether rewriting the query or improving statistics helps.

Do not assume prepared statements always improve performance.

---

## Exercise: Partitioning vs Indexing

A table contains:

```text
5 billion rows
```

and queries primarily access the last seven days.

### Tasks

Compare:

```text
B-tree index
Partial index
Partitioning
Partitioning + indexes
Archival
```

Evaluate:

- Query latency.
- Write performance.
- Retention operations.
- Storage.
- Maintenance.
- Planning complexity.
- Operational risk.

Design the solution you would recommend and justify it.

---

## Exercise: Materialized View

A reporting query takes:

```text
30 seconds
```

and executes every minute.

### Tasks

Determine whether a materialized view is appropriate.

Evaluate:

- Refresh cost.
- Data freshness.
- Concurrent reads.
- Refresh locking behavior.
- Incremental versus full refresh strategies.
- Failure handling.
- Storage.

Explain why moving an analytical workload away from the OLTP query path may be a better optimization than making the original query increasingly complex.

---

## Exercise: OLTP vs OLAP Workload

An API database handles:

```text
20,000 writes/sec
```

A new analytics dashboard runs:

```text
SELECT
    customer_id,
    date_trunc('day', created_at),
    SUM(total_amount)
FROM orders
GROUP BY customer_id, date_trunc('day', created_at);
```

### Tasks

Determine whether the query should run on the OLTP primary.

Evaluate:

- Read replica.
- Dedicated reporting database.
- CDC/Kafka pipeline.
- Data warehouse.
- Materialized views.
- Precomputed aggregates.

Explain why query optimization sometimes means moving the workload rather than tuning the SQL.

---

## Exercise: Query Optimization with Django

Given:

```python
orders = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="completed",
    )
    .select_related("customer")
    .order_by("-created_at")[:50]
)
```

### Tasks

1. Capture the generated SQL.
2. Run `EXPLAIN`.
3. Inspect the query plan.
4. Determine the required index.
5. Check for N+1 behavior.
6. Measure query count.
7. Measure endpoint latency.
8. Confirm tenant authorization independently.

Potential index candidate:

```python
class Meta:
    indexes = [
        models.Index(
            fields=["tenant_id", "status", "-created_at"],
            name="orders_tenant_status_created_idx",
        ),
    ]
```

Do not assume the ORM's generated SQL is optimal merely because it is concise.

---

## Exercise: Query Optimization with SQLAlchemy

Implement:

```python
stmt = (
    select(Order)
    .where(
        Order.tenant_id == tenant_id,
        Order.status == "completed",
    )
    .order_by(Order.created_at.desc())
    .limit(50)
)
```

### Tasks

1. Capture generated SQL.
2. Inspect bound parameters.
3. Run `EXPLAIN`.
4. Determine whether the composite index is useful.
5. Check query frequency.
6. Validate connection-pool behavior.
7. Compare application latency with database execution time.

---

## Exercise: Parameterized Query Performance

Compare a safe parameterized query with dynamically generated SQL.

Use:

```python
cursor.execute(
    """
    SELECT id, total_amount
    FROM orders
    WHERE customer_id = %s
    """,
    (customer_id,),
)
```

### Tasks

Determine:

- Security benefits.
- Type handling.
- Planning behavior.
- Logging behavior.
- Prepared-statement implications.

Do not confuse parameterization with prepared statements. They solve related but distinct problems.

---

## Exercise: Projection Optimization

Compare:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;
```

with:

```sql
SELECT
    id,
    status,
    total_amount,
    created_at
FROM orders
WHERE customer_id = $1;
```

### Tasks

Measure:

- Row width.
- Network transfer.
- Python object creation.
- JSON serialization.
- API response size.
- Database execution time.

Determine which layer actually benefits from the reduced projection.

---

## Exercise: Query Cancellation

A production query consumes excessive CPU.

### Tasks

Design an operational response.

Consider:

```sql
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    query,
    query_start
FROM pg_stat_activity
WHERE state <> 'idle';
```

Investigate:

```sql
SELECT pg_cancel_backend(<pid>);
```

and distinguish it from:

```sql
SELECT pg_terminate_backend(<pid>);
```

Explain why cancellation is preferable to termination when the backend session itself does not need to be forcibly disconnected.

---

## Exercise: Timeout Design

Design timeout layers for:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
FastAPI / Django
  ↓
Connection Pool
  ↓
PostgreSQL
```

Distinguish:

- Request timeout.
- Pool acquisition timeout.
- Query timeout.
- Lock timeout.
- Transaction timeout.

Explain why timeouts should form a coherent budget rather than independent arbitrary values.

---

## Exercise: Query Plan Comparison

For a slow query, capture:

```sql
EXPLAIN (ANALYZE, BUFFERS, SETTINGS)
SELECT
    id,
    total_amount,
    created_at
FROM orders
WHERE tenant_id = 10
  AND status = 'completed'
ORDER BY created_at DESC
LIMIT 100;
```

Create a comparison table:

| Metric | Before | After |
|---|---:|---:|
| Planning time | | |
| Execution time | | |
| Rows returned | | |
| Rows examined | | |
| Shared hits | | |
| Shared reads | | |
| Temp reads | | |
| Temp writes | | |
| Plan shape | | |

Do not declare success based solely on execution time.

---

## Exercise: Cold Cache vs Warm Cache

Run the same query multiple times.

### Tasks

Compare:

```text
First execution
Second execution
Repeated execution
```

Observe:

```text
shared_blks_hit
shared_blks_read
```

Explain why a query can appear fast during local testing because required pages are already cached.

For production benchmarking, distinguish:

- Warm-cache behavior.
- Cold-cache behavior.
- Mixed workload behavior.

Avoid using destructive operating-system cache commands in production simply to create a benchmark condition.

---

## Exercise: Index vs Query Rewrite

Consider:

```sql
SELECT *
FROM orders
WHERE date(created_at) = current_date;
```

### Tasks

Compare:

1. Adding an expression index.
2. Rewriting as a timestamp range.
3. Partitioning by date.
4. Caching today's data.

Determine which solution is most appropriate for different workload characteristics.

---

## Exercise: Redis Cache Stampede

Suppose:

```text
GET /customers/{id}/summary
```

is backed by a database query.

The Redis entry expires.

10,000 requests arrive simultaneously.

### Tasks

Model:

```text
Cache miss
   ↓
10,000 DB queries
   ↓
Database saturation
```

Design a cache-aside strategy with protection against stampede.

Consider:

- TTL jitter.
- Request coalescing.
- Short distributed coordination.
- Background refresh.
- Fallback behavior.

Explain why a fast query can still become dangerous when concurrency multiplies it.

---

## Exercise: Background Work

A report query takes:

```text
45 seconds
```

The API currently waits synchronously.

### Tasks

Redesign the request path using:

```text
API
 ↓
Celery
 ↓
PostgreSQL / OLAP store
 ↓
Object storage
 ↓
Download URL
```

Determine:

- When asynchronous processing is preferable.
- How job status is represented.
- How retries remain idempotent.
- How large result sets are stored.
- How database workload is isolated.

---

## Exercise: Kafka-Based Aggregation

Orders are emitted to Kafka.

### Tasks

Design a streaming aggregation pipeline:

```text
Order Service
     ↓
Kafka
     ↓
Consumer
     ↓
Aggregate Store
     ↓
API
```

Determine whether the API should continue executing:

```sql
SUM(total_amount)
GROUP BY customer_id
```

for every request.

Evaluate:

- Event ordering.
- Duplicate events.
- Idempotency.
- Consumer lag.
- Reprocessing.
- Eventual consistency.

Explain when precomputed aggregates are preferable to repeatedly scanning OLTP tables.

---

## Exercise: Security-Aware Optimization

Consider:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND customer_id = $2;
```

### Tasks

Optimize the query without weakening tenant isolation.

Evaluate:

- Composite indexes.
- RLS.
- Application authorization.
- Parameterized queries.
- Redis cache keys.
- Read replicas.

Verify that:

```text
Performance optimization
```

does not accidentally remove:

```text
Authorization enforcement
```

---

## Exercise: Production Incident

A production API experiences:

```text
p99 latency ↑
Database CPU ↑
Connection pool utilization ↑
Replica lag ↑
```

No schema deployment occurred.

### Tasks

Investigate in this order:

1. Query volume.
2. Query latency.
3. Retry volume.
4. Active connections.
5. Lock waits.
6. Execution plans.
7. Data distribution.
8. Cache behavior.
9. Background workers.
10. Recent application deployment.
11. Replica health.
12. Infrastructure metrics.

Build a hypothesis tree rather than immediately adding CPU or connections.

---

## Exercise: Production Optimization Decision Tree

For a slow SQL workload, classify the root cause:

```text
Slow request
   |
   +-- Waiting?
   |     |
   |     +-- Lock → concurrency/transaction issue
   |     +-- Pool → connection issue
   |     +-- Network → infrastructure/result-size issue
   |
   +-- Executing?
         |
         +-- CPU → query/aggregation/join issue
         +-- I/O → access path/storage issue
         +-- Sort spill → memory/query/index issue
         +-- Wrong plan → statistics/cardinality issue
         +-- Too many calls → application/N+1 issue
         +-- Too much data → projection/pagination issue
```

### Exercise

For each branch, provide:

- Evidence.
- Diagnostic SQL.
- Likely root cause.
- Candidate fix.
- Validation method.
- Production risk.

---

## Exercise: Optimization Without an Index

Optimize a query without adding any index.

Choose at least three techniques:

- Reduce projection.
- Rewrite predicates.
- Eliminate unnecessary joins.
- Replace repeated subqueries.
- Fix cardinality.
- Reduce result size.
- Use keyset pagination.
- Batch operations.
- Move aggregation to a read model.
- Cache stable results.
- Move analytics to an OLAP system.

Explain why indexing should be one tool in the optimization toolbox, not the default answer.

---

## Exercise: Production Optimization Review

Review this hypothetical change:

```text
Query latency: 800 ms → 40 ms
```

but:

```text
Index size: +80 GB
WAL: +35%
Write throughput: -15%
Replica lag: +20 seconds
```

### Tasks

Determine whether the optimization should ship.

Evaluate:

- Query frequency.
- SLO improvement.
- Read/write ratio.
- Replica requirements.
- Storage cost.
- Operational risk.
- Alternative query rewrites.
- Partial/covering indexes.
- Caching.
- Workload isolation.

Produce a decision:

```text
Ship
Ship with changes
Reject
```

and justify it using measurable trade-offs.

---

## Exercise: Benchmark Design

Build a benchmark comparing:

```text
Baseline query
      ↓
Query rewrite
      ↓
Index addition
      ↓
Composite index
      ↓
Partial index
      ↓
Covering index
      ↓
Cache
```

Measure:

| Metric | Baseline | Rewrite | Index | Cache |
|---|---:|---:|---:|---:|
| p50 | | | | |
| p95 | | | | |
| p99 | | | | |
| DB CPU | | | | |
| DB reads | | | | |
| Cache hit rate | | | | |
| Write throughput | | | | |
| Storage | | | | |

Test under realistic concurrency.

Do not benchmark only a single isolated query execution.

---

## Exercise: Load Testing

Design a load test for:

```text
10,000 requests/sec
```

with:

```text
70% reads
20% writes
10% analytical/background queries
```

### Tasks

Determine:

- Database connection requirements.
- Pool sizing.
- Read replica requirements.
- Query frequency.
- CPU/I/O saturation.
- Lock contention.
- Cache behavior.
- Replica lag.
- Background workload isolation.

Measure:

```text
Application p95/p99
Database p95/p99
Connection wait
Lock wait
CPU
I/O
WAL
Replica lag
```

Explain why database optimization must be validated under concurrency.

---

## Exercise: Query Optimization Runbook

Create a production runbook containing:

### Detection

- Application SLO breach.
- Database latency.
- CPU/I/O.
- Query statistics.
- Connection pool utilization.

### Diagnosis

- Identify query fingerprint.
- Inspect parameters.
- Run execution plan.
- Check locks.
- Check connection waits.
- Check replicas.
- Check recent deployments.

### Mitigation

- Reduce traffic.
- Disable expensive feature.
- Route reads appropriately.
- Cancel runaway queries.
- Temporarily disable background workloads.
- Adjust application concurrency.

### Permanent Fix

- Query rewrite.
- Index change.
- Statistics correction.
- Transaction redesign.
- Cache/read model.
- Workload isolation.
- Schema/partitioning change.

### Validation

- Benchmark.
- Load test.
- Compare query plans.
- Monitor p95/p99.
- Verify correctness.
- Verify security.

---

## Common Optimization Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Adding an index immediately | Indexes are easy to understand | Identify the actual bottleneck |
| Optimizing the slowest query only | Ignoring query frequency | Use total workload cost |
| Looking only at execution time | Ignoring waits | Separate CPU, I/O, locks, and network |
| Using `SELECT *` everywhere | Convenience | Return required columns |
| Ignoring N+1 | Focusing on individual SQL efficiency | Optimize query count |
| Increasing connection pools | Treating waiting as capacity | Fix query/transaction pressure |
| Increasing `work_mem` globally | Hiding sort/hash problems | Understand per-operation concurrency |
| Trusting local benchmarks | Small/cached datasets | Use production-like data |
| Ignoring parameter distribution | Assuming all values behave similarly | Investigate cardinality and plan sensitivity |
| Using `DISTINCT` to hide joins | Treating duplicates as performance issues | Fix result grain |
| Using cache first | Avoiding SQL investigation | Fix query and workload design |
| Ignoring replica lag | Treating replicas as free capacity | Monitor replay and freshness |
| Retrying aggressively | Trying to recover requests | Bound retries and add backoff |
| Optimizing without correctness tests | Focusing on speed | Verify result semantics |
| Ignoring security | Performance-first thinking | Preserve authorization and tenant isolation |
| Tuning production blindly | Fear of measuring | Use evidence and controlled changes |
| Treating plans as permanent | Data changes over time | Monitor for regressions |
| Optimizing one query in isolation | Ignoring system workload | Evaluate aggregate resource impact |

---

## Production Optimization Checklist

### Diagnose

- [ ] Exact SQL is known.
- [ ] Query parameters are understood.
- [ ] Query frequency is known.
- [ ] p50/p95/p99 latency is measured.
- [ ] `pg_stat_statements` has been inspected.
- [ ] Lock waits have been ruled out.
- [ ] Connection-pool waits have been ruled out.
- [ ] Network/result-transfer cost has been considered.

### Plan Analysis

- [ ] `EXPLAIN` has been inspected.
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` has been tested safely.
- [ ] Estimated versus actual rows are compared.
- [ ] Join algorithms are understood.
- [ ] Sort/hash behavior is understood.
- [ ] Temporary I/O is checked.
- [ ] Partition pruning is checked where applicable.
- [ ] Generic/custom plan behavior is considered where applicable.

### Query Design

- [ ] Result grain is correct.
- [ ] Projection is minimal.
- [ ] N+1 behavior is ruled out.
- [ ] Pagination strategy is appropriate.
- [ ] Predicates are index-compatible where useful.
- [ ] Unnecessary joins are removed.
- [ ] Duplicate-producing joins are understood.
- [ ] Aggregation occurs at the correct grain.

### Indexing

- [ ] Existing indexes were reviewed.
- [ ] Composite column order is intentional.
- [ ] Partial indexes were considered.
- [ ] Covering indexes were considered.
- [ ] Index size is understood.
- [ ] Write amplification is understood.
- [ ] Redundant indexes were considered.
- [ ] Deployment impact is understood.

### Production

- [ ] Query correctness is verified.
- [ ] Security and tenant isolation are preserved.
- [ ] Database CPU/I/O are monitored.
- [ ] Connection utilization is monitored.
- [ ] Replica lag is monitored.
- [ ] WAL impact is understood.
- [ ] Retry behavior is understood.
- [ ] Rollback/mitigation strategy exists.
- [ ] Regression monitoring exists.

---

## Interview Traps

### Is an index always the answer to a slow query?

No. The bottleneck may be locking, N+1 queries, connection pooling, poor cardinality estimates, excessive result transfer, CPU-heavy computation, or workload architecture.

### Why can a sequential scan be faster than an index scan?

When a query needs a large fraction of the table, sequential access can be cheaper than many index lookups and heap fetches.

### Is the slowest query always the highest-priority query?

No. Query frequency matters. A moderately slow query executed millions of times can dominate database resource consumption.

### Does `EXPLAIN` show actual execution time?

Plain `EXPLAIN` shows estimates. `EXPLAIN ANALYZE` executes the statement and reports actual execution information.

### Why should `EXPLAIN ANALYZE` be used carefully?

It executes the query. For `UPDATE`, `DELETE`, or other mutating statements, use an appropriate transaction/rollback strategy in a safe environment.

### Does `EXPLAIN ANALYZE` measure application latency?

No. It measures database planning/execution behavior. Application latency also includes connection acquisition, network transfer, serialization, application processing, and other layers.

### Does a faster query always mean a better optimization?

No. The optimization may increase write cost, storage, WAL, replica lag, memory pressure, or operational complexity.

### Should connection pools be increased when requests are waiting?

Not automatically. Increasing concurrency can amplify database CPU, locks, memory consumption, and queueing.

### Does caching replace query optimization?

No. Caching can reduce query frequency, but the underlying query still needs to be correct and reasonably efficient for cache misses and invalidation/rebuild workloads.

### Is a correlated subquery always slow?

No. PostgreSQL may transform or efficiently execute it, and indexed correlated lookups can be effective. Inspect the actual plan.

### Does a CTE always materialize?

No. Modern PostgreSQL can inline eligible CTEs. Explicit `MATERIALIZED` and `NOT MATERIALIZED` can influence behavior.

### Does partitioning make every query faster?

No. Partitioning is most useful when queries can benefit from pruning or when lifecycle/maintenance requirements justify it.

### Why can a query be fast in development but slow in production?

Differences in data volume, distribution, statistics, cache state, concurrency, indexes, configuration, hardware, replicas, and parameter values can change the execution plan and workload behavior.

---

## Senior-Level Optimization Questions

For every optimization proposal, ask:

1. What exactly is slow?
2. Is the query executing or waiting?
3. How often does it execute?
4. What is its total resource consumption?
5. What parameters produce different behavior?
6. What does the execution plan show?
7. Are estimates close to actual cardinality?
8. Which join algorithm is being used?
9. Is the workload CPU-bound or I/O-bound?
10. Is sorting or hashing expensive?
11. Is the result set unnecessarily large?
12. Is there an N+1 pattern?
13. Is transaction scope contributing to the problem?
14. Is connection pooling amplifying the problem?
15. Would a query rewrite solve it?
16. Would an index solve it?
17. What is the index write cost?
18. Would caching reduce workload more effectively?
19. Should the workload move to a read model or OLAP system?
20. How does the optimization affect replicas?
21. How does it affect WAL?
22. Does it preserve tenant isolation and authorization?
23. How will it behave at 10x data volume?
24. How will it behave under concurrency?
25. How will regression be detected?

---

## Final Practice Set

Complete these exercises without consulting reference material:

1. Diagnose a sequential scan.
2. Optimize an equality lookup.
3. Optimize range filtering.
4. Optimize `ORDER BY ... LIMIT`.
5. Design keyset pagination.
6. Diagnose N+1 queries.
7. Optimize a join.
8. Compare nested loop, hash join, and merge join.
9. Diagnose cardinality-estimation errors.
10. Investigate PostgreSQL statistics.
11. Optimize function-based predicates.
12. Optimize `LIKE` searches.
13. Analyze bitmap scans.
14. Optimize aggregation.
15. Detect aggregation double-counting.
16. Optimize `EXISTS`.
17. Analyze large `IN` lists.
18. Compare joins and subqueries.
19. Investigate CTE materialization.
20. Investigate predicate pushdown.
21. Optimize `DISTINCT`.
22. Optimize window-function workloads.
23. Optimize latest-row-per-group queries.
24. Diagnose correlated subqueries.
25. Investigate sort spills.
26. Investigate hash-aggregate memory.
27. Prioritize queries by workload impact.
28. Analyze `pg_stat_statements`.
29. Distinguish lock waits from execution time.
30. Diagnose long transactions.
31. Analyze connection-pool amplification.
32. Analyze retry storms.
33. Optimize replica-backed reads.
34. Design read-after-write behavior.
35. Compare indexes with Redis caching.
36. Optimize large result sets.
37. Compare offset and keyset pagination.
38. Design safe large deletes.
39. Design safe large updates.
40. Analyze partition pruning.
41. Diagnose query-plan regression.
42. Investigate generic versus custom plans.
43. Compare indexing and partitioning.
44. Evaluate materialized views.
45. Separate OLTP and OLAP workloads.
46. Optimize Django-generated SQL.
47. Optimize SQLAlchemy-generated SQL.
48. Analyze parameterized query behavior.
49. Optimize API projections.
50. Design query cancellation procedures.
51. Design timeout budgets.
52. Compare execution plans before and after optimization.
53. Benchmark cold and warm cache behavior.
54. Optimize using query rewrites without adding indexes.
55. Protect Redis-backed workloads from cache stampedes.
56. Move long-running work to asynchronous processing.
57. Design Kafka-based precomputed aggregates.
58. Optimize without weakening authorization.
59. Diagnose a multi-symptom production database incident.
60. Build a production query optimization runbook.
61. Perform a complete senior-level query optimization review.

## Key Takeaways

- **Optimize from evidence:** measure workload frequency, latency, waits, execution plans, cardinality, I/O, and concurrency before changing SQL or indexes.
- **Optimize the whole request path:** query shape, N+1 behavior, transactions, connection pools, result size, caching, replicas, and application retries can matter as much as SQL execution.
- **Validate correctness and trade-offs:** a faster query is not an improvement if it produces incorrect results or causes unacceptable write amplification, WAL, memory, replica lag, or operational cost.
- **Treat plans as workload-dependent:** statistics, data distribution, parameters, concurrency, cache state, and database growth can change the optimal execution strategy.
- **Senior optimization is architectural:** when SQL tuning reaches its limits, use caching, read models, asynchronous processing, partitioning, replicas, or OLAP workload isolation instead of endlessly tuning the same query.