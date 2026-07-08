# Database Indexing

Indexes are the single most impactful performance lever you have in a relational database. A missing index turns a 5ms query into a 30-second table scan. A poorly designed index wastes disk, bloats WAL traffic, and slows every INSERT. This guide covers the internals, the trade-offs, and the production patterns you need to get indexing right.

---

## What Is an Index?

An index is a separate data structure that maintains a sorted (or hashed) mapping from column values to row locations. Instead of scanning every row in a table, the database walks the index structure to locate matching rows directly.

Think of it as the index at the back of a textbook — you look up "B-Tree" in the index, get page 47, and flip there directly instead of reading every page.

---

## Index Types

### B-Tree (Default)

The workhorse of relational databases. Supports equality (`=`), range (`<`, `>`, `BETWEEN`), sorting (`ORDER BY`), and prefix matching (`LIKE 'foo%'`). This is the default index type in PostgreSQL, MySQL, and Oracle.

### Hash

Supports **only** equality checks (`=`). Faster than B-Tree for exact lookups but useless for range queries. PostgreSQL hash indexes were not WAL-logged before v10 — avoid them on older versions.

### GIN (Generalized Inverted Index)

Designed for composite values: arrays, JSONB, full-text search vectors. Maps each element inside a value to the rows containing it. Ideal for `@>`, `?`, `@@` operators.

### GiST (Generalized Search Tree)

Supports geometric data, range types, and full-text search. Used for PostGIS spatial queries (`ST_Contains`, `ST_DWithin`) and exclusion constraints.

| Index Type | Best For                    | Supports Range | Supports Equality | Write Overhead |
|------------|-----------------------------|:--------------:|:-----------------:|:--------------:|
| B-Tree     | General purpose             | ✅              | ✅                 | Medium         |
| Hash       | Exact lookups only          | ❌              | ✅                 | Low            |
| GIN        | JSONB, arrays, full-text    | ❌              | ✅                 | High           |
| GiST       | Spatial, ranges, full-text  | ✅              | ✅                 | Medium-High    |

---

## How B-Tree Indexes Work Internally

A B-Tree is a self-balancing tree where every leaf node is at the same depth. Internal nodes hold keys and pointers that guide traversal. Leaf nodes hold the indexed values and pointers (ctid/rowid) to the actual heap tuples.

```
                    ┌─────────────────┐
                    │   Root Node     │
                    │  [30]  [70]     │
                    └──┬─────┬─────┬──┘
                       │     │     │
            ┌──────────┘     │     └──────────┐
            ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │ Internal  │    │ Internal  │    │ Internal  │
    │ [10] [20] │    │ [45] [60] │    │ [80] [95] │
    └──┬──┬──┬──┘    └──┬──┬──┬──┘    └──┬──┬──┬──┘
       │  │  │          │  │  │          │  │  │
       ▼  ▼  ▼          ▼  ▼  ▼          ▼  ▼  ▼
    ┌─────┐┌─────┐  ┌─────┐┌─────┐  ┌─────┐┌─────┐
    │Leaf ││Leaf ││Leaf │  │Leaf │  │Leaf ││Leaf │
    │1-10 ││11-20││31-45│  │46-60│  │71-80││81-95│
    └──┬──┘└──┬──┘└──┬──┘  └──┬──┘  └──┬──┘└──┬──┘
       │      │      │        │        │      │
       ▼      ▼      ▼        ▼        ▼      ▼
    [Heap Tuples — Actual Table Rows on Disk]
```

**Key properties:**

- **Balanced**: All leaf nodes are equidistant from root. Lookup is always O(log n).
- **Sorted**: Leaf nodes are linked in order, enabling efficient range scans.
- **Fan-out**: Internal nodes hold many keys (typically hundreds), so even billion-row tables need only 3-4 levels.

A table with 100 million rows and a B-Tree index typically requires **3 page reads** to locate any single row. A sequential scan on the same table reads **millions** of pages.

---

## Clustered vs Non-Clustered Indexes

| Property              | Clustered Index                           | Non-Clustered Index                       |
|-----------------------|-------------------------------------------|-------------------------------------------|
| Table row order       | Physically reorders table rows            | Separate structure, table order unchanged |
| Count per table       | Only **one** per table                    | Multiple allowed                          |
| Leaf nodes contain    | Actual row data                           | Pointers to row locations                 |
| Range scan speed      | Extremely fast (sequential I/O)           | Slower (random I/O for each pointer)      |
| Example (SQL Server)  | Primary key by default                    | Any secondary index                       |
| PostgreSQL equivalent | `CLUSTER` command (one-time reorder)      | All indexes are non-clustered             |

```
  Clustered Index                    Non-Clustered Index

  B-Tree leaves = actual rows       B-Tree leaves = pointers
  ┌──────────────────────┐          ┌──────────────────────┐
  │ Key │ Row Data       │          │ Key │ Ptr → Heap Row │
  │  1  │ {Alice, 25}    │          │  1  │ → Page 5, Slot 3│
  │  2  │ {Bob, 30}      │          │  2  │ → Page 2, Slot 7│
  │  3  │ {Carol, 28}    │          │  3  │ → Page 9, Slot 1│
  └──────────────────────┘          └──────────────────────┘
```

**Production note:** PostgreSQL does not maintain clustered order after the initial `CLUSTER` command. New inserts go wherever there is free space. You must periodically re-cluster, which takes an `ACCESS EXCLUSIVE` lock. For most PostgreSQL workloads, rely on non-clustered indexes and let `shared_buffers` handle caching.

---

## Covering Indexes

A covering index includes all columns needed by a query, so the database never touches the heap table at all. This is called an **index-only scan**.

```sql
-- Query
SELECT email, created_at FROM users WHERE status = 'active';

-- Covering index (PostgreSQL INCLUDE syntax)
CREATE INDEX idx_users_status_covering
  ON users (status) INCLUDE (email, created_at);
```

The `INCLUDE` columns are stored in the leaf nodes but not in the internal nodes, so they do not affect sort order or tree depth. This is cheaper than making them part of the index key.

**When to use:** High-frequency queries where you know the exact column set. Do not create covering indexes for every query — each one adds write overhead and storage.

---

## Composite Indexes — Column Order Matters

A composite index on `(a, b, c)` is sorted first by `a`, then by `b` within each `a` group, then by `c` within each `(a, b)` group. This means:

- `WHERE a = 1` → **uses index** (leftmost prefix)
- `WHERE a = 1 AND b = 2` → **uses index**
- `WHERE a = 1 AND b = 2 AND c = 3` → **uses index** (full match)
- `WHERE b = 2` → **does NOT use index** (missing leftmost column)
- `WHERE a = 1 AND c = 3` → **partially uses index** (scans all `a=1` entries, filters `c` manually)

**Rule of thumb for column ordering:**

1. **Equality columns first** — columns compared with `=`
2. **Range columns last** — columns compared with `>`, `<`, `BETWEEN`
3. **High cardinality before low cardinality** within equality columns

```sql
-- Bad: range column first breaks subsequent index usage
CREATE INDEX idx_bad ON orders (created_at, customer_id, status);

-- Good: equality columns first, range column last
CREATE INDEX idx_good ON orders (customer_id, status, created_at);
```

---

## Index Scan vs Sequential Scan

The query planner chooses between an index scan and a sequential scan based on estimated row selectivity and I/O cost.

| Scan Type       | When Used                                | I/O Pattern    |
|-----------------|------------------------------------------|----------------|
| Sequential Scan | >5-15% of table rows match               | Sequential     |
| Index Scan      | Small percentage of rows match           | Random         |
| Index Only Scan | All needed columns are in the index      | Random (index) |
| Bitmap Scan     | Moderate selectivity, combines indexes   | Mixed          |

**Critical insight:** Random I/O is 50-100x slower than sequential I/O on spinning disks (less of a gap on SSDs). If your query returns 20% of the table, a sequential scan reading every page in order is faster than an index scan doing random seeks for each row.

---

## When Indexes Hurt

Indexes are not free. Every index adds cost to writes and consumes storage.

- **Write overhead:** Every `INSERT`, `UPDATE`, or `DELETE` must update every index on the table. A table with 10 indexes means 10 additional B-Tree modifications per write.
- **Index bloat:** Dead tuples from updates/deletes leave empty space in index pages. PostgreSQL's `REINDEX` or `pg_repack` fixes this, but it requires maintenance windows.
- **Planner confusion:** Too many indexes can cause the planner to choose suboptimal plans. Unused indexes waste resources.
- **HOT updates disabled:** In PostgreSQL, Heap-Only Tuple updates avoid index changes if no indexed column is modified. Adding unnecessary indexes on frequently-updated columns disables HOT.

```sql
-- Find unused indexes in PostgreSQL
SELECT schemaname, relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexrelname NOT LIKE '%pkey%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Production rule:** Drop indexes with zero scans over a 30-day observation period. Always check before dropping — some indexes exist solely for unique constraints.

---

## EXPLAIN ANALYZE — Reading Execution Plans

`EXPLAIN ANALYZE` actually executes the query and shows real timing and row counts.

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE customer_id = 42 AND status = 'shipped';
```

```
Index Scan using idx_orders_customer_status on orders
    (cost=0.43..8.45 rows=1 width=120) (actual time=0.023..0.025 rows=1 loops=1)
  Index Cond: ((customer_id = 42) AND (status = 'shipped'))
  Buffers: shared hit=4
Planning Time: 0.082 ms
Execution Time: 0.041 ms
```

**What to look for:**

| Signal                          | Problem                                        |
|---------------------------------|------------------------------------------------|
| `Seq Scan` on large table       | Missing index                                  |
| `actual rows` >> `rows`         | Stale statistics, run `ANALYZE`                |
| `Buffers: shared read` high     | Data not cached, consider `shared_buffers`     |
| `Sort Method: external merge`   | `work_mem` too low for in-memory sort          |
| Nested Loop with large inner    | Missing index on join column                   |

---

## AWS RDS Performance Insights

Performance Insights surfaces the exact SQL statements consuming the most database time, broken down by waits.

**Identifying missing indexes with Performance Insights:**

1. Open RDS Console → select your instance → Performance Insights
2. Look at **Top SQL** tab — queries with high `db.sql.total_wait` are candidates
3. Filter by `IO:DataFileRead` wait events — these indicate sequential scans hitting disk
4. Copy the SQL statement and run `EXPLAIN ANALYZE` in a read replica
5. Create the appropriate index based on the WHERE/JOIN predicates

**Automated detection:** Enable `pg_stat_statements` extension on RDS PostgreSQL. Query it periodically to find slow statements:

```sql
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

---

## Common Mistakes

1. **Indexing every column** — creates massive write overhead and confuses the planner. Index only columns that appear in WHERE, JOIN, and ORDER BY clauses of frequent queries.
2. **Wrong composite index order** — putting a range column before equality columns renders the index partially useless for the remaining columns.
3. **Ignoring index bloat** — an index that has grown to 10x its expected size due to dead tuples will perform poorly. Monitor `pg_stat_user_indexes` and schedule periodic `REINDEX CONCURRENTLY`.
4. **Not using INCLUDE columns** — creating a full composite index `(a, b, c, d)` when you only filter on `a` and just need `b, c, d` in the output. Use `(a) INCLUDE (b, c, d)` instead.
5. **Creating indexes in production without CONCURRENTLY** — `CREATE INDEX` takes a full table lock. Always use `CREATE INDEX CONCURRENTLY` on production tables.

---

## Interview Questions

**Q1: You have a composite index on (A, B, C). A query filters on B and C only. Will the index be used?**

No. B-Tree composite indexes require the leftmost prefix. Without column A in the filter, the database cannot efficiently navigate the tree. It may do a full index scan (worse than a table scan in many cases). You need a separate index on (B, C) or restructure the composite index.

**Q2: When would a sequential scan outperform an index scan?**

When the query returns a large fraction of the table (typically >10-15%). Sequential I/O reads contiguous disk pages, while an index scan issues random reads for each row pointer. On HDDs the crossover point is around 5-10%; on SSDs it is higher but still exists. The planner accounts for this via `random_page_cost` and `seq_page_cost` settings.

**Q3: What is the difference between a covering index and a composite index?**

A composite index includes multiple columns as part of the index key (affecting sort order and tree structure). A covering index uses `INCLUDE` to attach non-key columns to the leaf nodes purely so the query can be answered from the index alone (index-only scan), without affecting sort order. A composite index can also be covering if it contains all required columns, but `INCLUDE` is more storage-efficient for output-only columns.

**Q4: How do you safely add an index to a table with 500 million rows in production?**

Use `CREATE INDEX CONCURRENTLY`. This builds the index without holding an exclusive lock on the table, allowing reads and writes to continue. It takes longer and requires extra disk space during the build. Monitor replication lag if running on a primary with replicas. Set a generous `maintenance_work_mem` (1-2GB) to speed up the build. Always run on a read replica first to estimate build time.

---

## Key Takeaways

- **B-Tree indexes are O(log n)** — a 100M-row table needs ~3 page reads for a point lookup. Always start with B-Tree unless you have a specific reason for another type.
- **Composite index column order is critical** — equality columns first, range columns last. Getting this wrong makes the index partially or completely useless.
- **Every index has a write cost** — budget your indexes. Aim for the minimum set that covers your critical query paths. Drop unused indexes.
- **Use EXPLAIN ANALYZE religiously** — never guess whether an index is being used. Look at actual row counts, buffer hits, and scan types.
- **Covering indexes eliminate heap lookups** — use `INCLUDE` for columns that appear in SELECT but not in WHERE or ORDER BY.
- **Monitor with pg_stat_statements and RDS Performance Insights** — proactive index management prevents incidents. The top 20 slowest queries by mean execution time will tell you exactly where to focus.
