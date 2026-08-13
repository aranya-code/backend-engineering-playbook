# SQL Performance Optimization

Slow queries are the single most common cause of production database incidents. A poorly optimized query at scale does not degrade gracefully — it cascades into connection pool exhaustion, lock contention, and application-wide outages. This guide covers the tools and techniques to identify, diagnose, and fix SQL performance problems in PostgreSQL on AWS (RDS and Aurora).

---

## Query Execution Plan Analysis

The query planner is your most important debugging tool. Before optimizing anything, read the plan.

### EXPLAIN vs EXPLAIN ANALYZE

```sql
-- Shows the planner's estimated plan (does NOT execute the query)
EXPLAIN SELECT * FROM orders WHERE user_id = 12345;

-- Executes the query and shows actual timing and row counts
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = 12345;
```

**Always use `EXPLAIN ANALYZE` in non-production or with read-only queries.** It shows the difference between what the planner estimated and what actually happened. Large discrepancies between estimated and actual rows indicate stale statistics.

### Scan Types

```
  Scan Type Hierarchy (best to worst for point lookups)

  ┌──────────────────────────────────────────────────┐
  │  Index Only Scan                                 │  Best: reads from index only,
  │  (covers all needed columns)                     │  never touches the table heap
  ├──────────────────────────────────────────────────┤
  │  Index Scan                                      │  Good: uses index to find rows,
  │  (index lookup + heap fetch)                     │  then fetches full row from heap
  ├──────────────────────────────────────────────────┤
  │  Bitmap Index Scan → Bitmap Heap Scan            │  OK: builds bitmap of matching
  │  (batch index lookup + batch heap fetch)         │  pages, then fetches in bulk
  ├──────────────────────────────────────────────────┤
  │  Sequential Scan                                 │  Worst for point lookups:
  │  (full table scan, row by row)                   │  reads every row in the table
  └──────────────────────────────────────────────────┘
```

**Sequential scans are not always bad.** For queries returning more than ~5-10% of a table, a sequential scan is often faster than an index scan because it reads pages sequentially rather than randomly. The planner knows this — trust it unless statistics are stale.

---

## Identifying Slow Queries

### pg_stat_statements

The most important extension for production PostgreSQL. It tracks execution statistics for every query.

```sql
-- Top 10 queries by total execution time
SELECT
    query,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    round(mean_exec_time::numeric, 2) AS avg_ms,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

**Install it on every production database.** On RDS/Aurora, add `pg_stat_statements` to `shared_preload_libraries` in your parameter group and run `CREATE EXTENSION pg_stat_statements;`.

Focus on **total time** first, not average time. A query that runs 1ms but executes 10 million times per day consumes more resources than a query that runs 5 seconds once.

### Slow Query Log

Enable in your RDS parameter group:

```
log_min_duration_statement = 1000    -- Log queries taking > 1 second
log_statement = 'none'               -- Don't log all queries (too noisy)
```

For Aurora, use Performance Insights — it provides visual query analysis without manual log parsing.

---

## Index Optimization

### Covering Indexes

A covering index includes all columns needed by a query, enabling an Index Only Scan that never touches the table heap.

```sql
-- Query: frequently called by the API
SELECT order_id, status, total_amount
FROM orders
WHERE user_id = $1 AND created_at > $2;

-- Covering index: includes all selected columns
CREATE INDEX idx_orders_user_created_covering
ON orders (user_id, created_at)
INCLUDE (order_id, status, total_amount);
```

### Partial Indexes

Index only the rows that matter. Dramatically reduces index size and maintenance cost.

```sql
-- Only 2% of orders are in 'pending' status, but 90% of queries filter for them
CREATE INDEX idx_orders_pending
ON orders (user_id, created_at)
WHERE status = 'pending';
```

### Expression Indexes

Index the result of a function applied to a column.

```sql
-- Queries filter by lowercase email
CREATE INDEX idx_users_email_lower
ON users (LOWER(email));

-- Now this uses the index:
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';
```

**Index maintenance cost:** Every index slows down writes. A table with 10 indexes processes INSERT operations 5-10x slower than a table with 1 index. Audit unused indexes with `pg_stat_user_indexes` and drop those with `idx_scan = 0`.

---

## Query Rewriting

### Avoid SELECT *

```sql
-- Bad: fetches all columns, cannot use covering indexes
SELECT * FROM orders WHERE user_id = 12345;

-- Good: fetch only what you need
SELECT order_id, status, total_amount FROM orders WHERE user_id = 12345;
```

### Use EXISTS Instead of IN for Subqueries

```sql
-- Bad: IN materializes the entire subquery result
SELECT * FROM users
WHERE user_id IN (SELECT user_id FROM orders WHERE total > 1000);

-- Good: EXISTS short-circuits on first match
SELECT * FROM users u
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.user_id AND o.total > 1000);
```

### Avoid Functions in WHERE Clauses

```sql
-- Bad: function prevents index usage on created_at
SELECT * FROM orders WHERE DATE(created_at) = '2025-01-15';

-- Good: use range scan against the indexed column directly
SELECT * FROM orders
WHERE created_at >= '2025-01-15 00:00:00'
  AND created_at <  '2025-01-16 00:00:00';
```

---

## Connection Pooling

PostgreSQL forks a new process for each connection. At 500+ connections, the OS scheduler and shared memory management become bottlenecks.

```
  Without Pooling                    With Pooling (PgBouncer/RDS Proxy)

  App (500 threads)                  App (500 threads)
       │ │ │ │ │                          │ │ │ │ │
       ▼ ▼ ▼ ▼ ▼                          ▼ ▼ ▼ ▼ ▼
  ┌────────────────┐                 ┌────────────────┐
  │  PostgreSQL    │                 │   Connection   │
  │  500 processes │                 │     Pooler     │
  │  (500 x 10MB  │                 │  500 app conns │
  │   = 5GB RAM)  │                 │   → 50 DB conns│
  └────────────────┘                 └───────┬────────┘
                                             │
                                     ┌───────▼────────┐
                                     │  PostgreSQL    │
                                     │  50 processes  │
                                     │  (50 x 10MB   │
                                     │   = 500MB RAM) │
                                     └────────────────┘
```

### PgBouncer vs RDS Proxy

| Feature | PgBouncer | RDS Proxy |
|---------|-----------|-----------|
| Deployment | Self-managed (EC2/container) | Fully managed |
| Pool modes | Session, Transaction, Statement | Transaction (primary mode) |
| Latency overhead | ~100μs | ~1-2ms |
| IAM auth | No (needs plugin) | Yes (native) |
| Multi-AZ failover | Manual | Automatic |
| Cost | EC2 instance cost | Per-vCPU pricing |

**Use RDS Proxy** when you want managed connection pooling with automatic failover, especially for Lambda-to-RDS workloads. **Use PgBouncer** when you need lower latency overhead and want transaction or statement-level pooling with fine-grained control.

---

## Vacuum and Autovacuum

PostgreSQL uses MVCC (Multi-Version Concurrency Control). UPDATE and DELETE operations do not remove old rows — they create new versions and mark old ones as dead tuples. VACUUM reclaims this space.

```
  Table State Over Time (without adequate vacuuming)

  Day 1:     [live][live][live][live][live]         100% efficient
  Day 30:    [live][dead][live][dead][live][dead]    50% bloated
  Day 90:    [dead][dead][live][dead][dead][live]    70% bloated → slow scans
  Day 180:   Table is 5x larger than actual data    Critical bloat
```

### Autovacuum Configuration

Default autovacuum settings are conservative. For high-write tables, tune these parameters:

```sql
-- Per-table autovacuum tuning for a high-write table
ALTER TABLE orders SET (
    autovacuum_vacuum_threshold = 1000,         -- default: 50
    autovacuum_vacuum_scale_factor = 0.05,      -- default: 0.2
    autovacuum_analyze_threshold = 500,          -- default: 50
    autovacuum_analyze_scale_factor = 0.025      -- default: 0.1
);
```

**Monitor dead tuple count:**

```sql
SELECT relname, n_dead_tup, n_live_tup,
       round(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct,
       last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

If `dead_pct` exceeds 20%, autovacuum is not keeping up. Increase `autovacuum_max_workers` or reduce per-table thresholds.

---

## Real-World Optimization: 5 Seconds → 50ms

**Scenario:** An API endpoint listing recent orders for a user takes 5 seconds under load.

**Original query:**

```sql
SELECT * FROM orders
WHERE DATE(created_at) = CURRENT_DATE
  AND user_id IN (SELECT user_id FROM premium_users)
ORDER BY created_at DESC;
```

**Step 1: Read the execution plan**

```
Seq Scan on orders  (cost=0.00..185432.00 rows=50000 width=320)
  Filter: (date(created_at) = CURRENT_DATE AND
           (hashed SubPlan: SELECT user_id FROM premium_users))
  Rows Removed by Filter: 4950000
  Actual Time: 4823ms
```

Full sequential scan on 5M rows. Three problems: `DATE()` function blocks index usage, `IN` subquery materializes all premium users, `SELECT *` returns unused columns.

**Step 2: Rewrite the query**

```sql
SELECT order_id, status, total_amount, created_at
FROM orders o
WHERE o.created_at >= CURRENT_DATE
  AND o.created_at < CURRENT_DATE + INTERVAL '1 day'
  AND EXISTS (SELECT 1 FROM premium_users p WHERE p.user_id = o.user_id)
ORDER BY o.created_at DESC
LIMIT 50;
```

**Step 3: Add a covering index**

```sql
CREATE INDEX idx_orders_created_user
ON orders (created_at, user_id)
INCLUDE (order_id, status, total_amount);
```

**Result:**

```
Index Only Scan using idx_orders_created_user on orders
  Index Cond: (created_at >= ... AND created_at < ...)
  Actual Time: 0.045..0.052
  Rows: 50
  Buffers: shared hit=8
```

**5 seconds → 48ms.** The fix was mechanical: remove the function from WHERE, replace IN with EXISTS, select only needed columns, add a covering index.

---

## Common Mistakes

1. **Adding indexes without checking if they are used.** Every unused index wastes disk, slows writes, and consumes vacuum resources. Audit `pg_stat_user_indexes` monthly.
2. **Ignoring autovacuum.** Table bloat is a silent killer. Monitor dead tuples and `last_autovacuum` as production metrics.
3. **Using ORM-generated queries without review.** ORMs generate correct SQL, not optimal SQL. Review the actual queries hitting your database with `pg_stat_statements`.
4. **Opening too many direct connections.** Lambda functions and microservices create connection storms. Use RDS Proxy or PgBouncer — always.
5. **Optimizing queries in development with small datasets.** A query that runs in 10ms against 1,000 rows may take 10 seconds against 10 million rows. Test with production-scale data.

---

## Interview Questions

**Q1: A production query uses an index in development but switches to a sequential scan in production. Same query, same indexes. What happened?**

The planner uses table statistics to choose the optimal plan. If the production table has different data distribution (e.g., low cardinality column, skewed values), the planner may calculate that a sequential scan is cheaper. Run `ANALYZE` to update statistics. Also check if the `random_page_cost` setting is too high for SSD-backed storage — the default of 4.0 assumes spinning disks. Set it to 1.1 for SSD.

**Q2: Your application uses connection pooling with PgBouncer in transaction mode. Developers report that prepared statements and SET commands are not working. Why?**

In transaction mode, PgBouncer reassigns connections between transactions. Prepared statements and session-level SET commands are bound to the server connection, not the client connection. After reassignment, the prepared statement does not exist on the new server connection. Use `DEALLOCATE ALL` at transaction end, or switch to session mode for workloads that require prepared statements.

**Q3: A table with 50 million rows has 40% dead tuples despite autovacuum being enabled. What is your investigation and fix?**

Check `pg_stat_user_tables` for `last_autovacuum` — it may never have completed. Common causes: long-running transactions holding back the `xmin` horizon (preventing dead tuple cleanup), autovacuum being interrupted by lock conflicts, or autovacuum cost limits being too aggressive (`autovacuum_vacuum_cost_delay`). Fix: kill long-running idle transactions, lower per-table vacuum thresholds, increase `autovacuum_max_workers`, and run a manual `VACUUM VERBOSE` to diagnose.

---

## Key Takeaways

- **Always start with `EXPLAIN ANALYZE`.** Never guess why a query is slow — read the plan. The answer is in the estimated vs actual rows and the scan type.
- **`pg_stat_statements` is non-negotiable in production.** Enable it on every PostgreSQL instance. Sort by total execution time to find the queries that matter most.
- **Covering indexes eliminate heap fetches.** An Index Only Scan is the fastest possible read path. Use `INCLUDE` to add non-key columns to indexes.
- **Connection pooling is mandatory at scale.** PostgreSQL's process-per-connection model breaks down beyond a few hundred connections. Use RDS Proxy for managed pooling.
- **Autovacuum needs tuning for high-write tables.** Default settings assume low write volume. Monitor dead tuple ratios and adjust per-table thresholds.
- **Fix the query before adding hardware.** Scaling up the instance masks the real problem. A rewritten query with proper indexes often delivers 100x improvement.
