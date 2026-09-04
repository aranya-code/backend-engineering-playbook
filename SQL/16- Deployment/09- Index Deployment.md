# 09- Index Deployment

## Overview

Indexes are one of the most important tools for improving database query performance, but creating, changing, or removing an index in production is itself a database workload.

A production index deployment must consider:

- Table size
- Query workload
- Locking
- CPU and I/O
- Disk capacity
- WAL generation
- Replication lag
- Connection pressure
- Application rollout order
- Query plan changes
- Rollback strategy

For small development tables, this may be as simple as:

```sql
CREATE INDEX customers_email_idx
ON customers (email);
```

For a large production table, the same operation requires architectural planning.

The core production principle is:

> **An index should be deployed as a controlled production change, not treated as a harmless metadata operation.**

A typical lifecycle is:

```text
Identify slow query
       ↓
Validate query pattern
       ↓
Design index
       ↓
Estimate cost
       ↓
Create safely
       ↓
Verify index
       ↓
Deploy / enable query
       ↓
Observe execution plans
       ↓
Measure benefit
       ↓
Retain or remove
```

---

## Why Index Deployment Matters

An index can reduce the amount of data PostgreSQL must inspect.

Without a useful index:

```text
Query
  ↓
Sequential Scan
  ↓
Large portion of table
  ↓
CPU + I/O
  ↓
Higher latency
```

With a suitable index:

```text
Query
  ↓
Index Scan
  ↓
Relevant rows
  ↓
Lower work
  ↓
Lower latency
```

However, an index also has a cost:

```text
INSERT
UPDATE
DELETE
   ↓
Maintain table
   +
Maintain indexes
   ↓
CPU + WAL + I/O
   ↓
Storage + replication cost
```

Therefore:

> **Index optimization is a workload trade-off, not a rule that more indexes are always better.**

---

## Index Deployment Lifecycle

A mature index deployment follows an evidence-driven workflow.

```mermaid
flowchart LR
    A[Identify Query Problem] --> B[Inspect Workload]
    B --> C[Design Candidate Index]
    C --> D[Validate With EXPLAIN]
    D --> E[Estimate Operational Cost]
    E --> F[Create Index Safely]
    F --> G[Verify Index]
    G --> H[Observe Production Plans]
    H --> I[Measure Benefit]
    I --> J[Keep or Remove]
```

Each stage answers a different question.

| Stage | Main question |
|---|---|
| Identify | Which query needs improvement? |
| Design | What access pattern should the index support? |
| Validate | Would the planner actually use it? |
| Cost | Can production absorb the build and ongoing maintenance? |
| Create | How can it be built with acceptable disruption? |
| Observe | Did the production plan and latency improve? |
| Review | Is the index worth its ongoing cost? |

---

## Start With the Query

Do not start with:

```text
"We need an index on this column."
```

Start with:

```text
"This production query is expensive."
```

Example:

```sql
SELECT id, created_at, total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

A candidate index might be:

```sql
CREATE INDEX orders_customer_created_idx
ON orders (customer_id, created_at DESC);
```

The index is derived from the access pattern:

```text
Equality filter
      ↓
customer_id

Ordering
      ↓
created_at DESC

Small result
      ↓
LIMIT 50
```

---

## Inspect the Existing Indexes

Before creating a new index, inspect what already exists.

```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'orders';
```

Also inspect usage where appropriate.

PostgreSQL statistics can provide evidence about index activity:

```sql
SELECT
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY idx_scan DESC;
```

Low usage does not automatically mean an index should be removed.

Consider:

- Observation period
- Traffic patterns
- Seasonal workloads
- Recent deployments
- Statistics resets
- Constraint usage
- Rare but critical queries

---

## Design Around Access Patterns

Index design should reflect complete query patterns.

For:

```sql
SELECT id
FROM orders
WHERE customer_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 100;
```

a candidate might be:

```sql
CREATE INDEX orders_customer_status_created_idx
ON orders (customer_id, status, created_at DESC);
```

The exact index depends on:

- Selectivity
- Data distribution
- Query frequency
- Ordering
- Range conditions
- Projection
- Write workload

Do not mechanically create an index for every `WHERE` column.

---

## Composite Index Column Order

For a B-tree index:

```sql
CREATE INDEX orders_customer_status_created_idx
ON orders (customer_id, status, created_at DESC);
```

the ordering of indexed columns matters.

A simplified interpretation is:

```text
customer_id
    ↓
status
    ↓
created_at
```

Queries that constrain the leading columns can often use the index efficiently.

Consider:

```sql
WHERE customer_id = $1
  AND status = $2
```

versus:

```sql
WHERE status = $1
```

The second query may not benefit from the composite index as effectively because `status` is not the leading key.

Index ordering must be derived from actual workload rather than memorized rules.

---

## Equality, Range, and Ordering

Suppose:

```sql
SELECT *
FROM events
WHERE tenant_id = $1
  AND created_at >= $2
ORDER BY created_at DESC
LIMIT 100;
```

A candidate is:

```sql
CREATE INDEX events_tenant_created_idx
ON events (tenant_id, created_at DESC);
```

The pattern is:

```text
tenant_id
   ↓
Equality

created_at
   ↓
Range + ordering
```

This can be much more useful than separate indexes such as:

```text
tenant_id
created_at
```

because the composite index directly represents the query's access path.

---

## Validate With EXPLAIN

Before deployment, inspect the query plan.

```sql
EXPLAIN
SELECT id, created_at, total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

After creating the candidate index, compare the plan.

For production-like testing:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, created_at, total
FROM orders
WHERE customer_id = 123
ORDER BY created_at DESC
LIMIT 50;
```

Remember:

> **`EXPLAIN ANALYZE` executes the query.**

Do not run it casually against production DML such as:

```sql
EXPLAIN ANALYZE DELETE ...
```

because the statement will actually execute.

---

## What to Look For in a Plan

Important signals include:

- Sequential scan vs index scan
- Bitmap heap/index scans
- Index-only scans
- Estimated rows
- Actual rows
- `Rows Removed by Filter`
- Sort operations
- Join strategy
- Buffer reads
- Buffer hits
- Execution time
- Loops

For example:

```text
Seq Scan
  Rows Removed by Filter: 4,900,000
  actual rows: 50
```

may indicate that the query is doing far more work than necessary.

But a sequential scan is not automatically a problem. For a small table or query returning most rows, it can be the correct plan.

---

## Creating an Index in PostgreSQL

For a small or low-risk table:

```sql
CREATE INDEX customers_email_idx
ON customers (email);
```

For a busy large production table, consider:

```sql
CREATE INDEX CONCURRENTLY customers_email_idx
ON customers (email);
```

`CREATE INDEX CONCURRENTLY` is specifically designed to reduce blocking of normal table writes while the index is built.

It is often the preferred approach for large, actively used production tables.

---

## CREATE INDEX vs CREATE INDEX CONCURRENTLY

| Characteristic | `CREATE INDEX` | `CREATE INDEX CONCURRENTLY` |
|---|---|---|
| Simpler | Yes | No |
| Faster build | Usually | Usually slower |
| Blocks normal writes | More restrictive | Designed to allow normal writes |
| Resource usage | High | High |
| Transaction block | Yes | No |
| Failure handling | Simpler | More complex |
| Large busy table | Requires careful scheduling | Often preferable |

`CONCURRENTLY` does not mean "free."

It still consumes:

- CPU
- I/O
- Memory
- Disk
- WAL
- Replication bandwidth

---

## CREATE INDEX CONCURRENTLY

Example:

```sql
CREATE INDEX CONCURRENTLY orders_customer_created_idx
ON orders (customer_id, created_at DESC);
```

Important operational properties:

- It cannot run inside a transaction block.
- It takes longer than a regular index build in many cases.
- It still places resource pressure on the database.
- It can leave an invalid index if the operation fails.
- It requires careful migration tooling.

For PostgreSQL, inspect invalid indexes after failed concurrent builds.

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisvalid,
    indisready
FROM pg_index
WHERE NOT indisvalid
   OR NOT indisready;
```

An invalid index should be explicitly investigated and cleaned up according to the failure state.

---

## Migration Tooling

Index creation has implications for migration frameworks.

### Django

A migration such as:

```python
migrations.AddIndex(
    model_name="order",
    index=models.Index(
        fields=["customer_id", "-created_at"],
        name="orders_customer_created_idx",
    ),
)
```

may need special handling for large production tables.

For concurrent PostgreSQL index creation, Django supports non-atomic migrations:

```python
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY orders_customer_created_idx
                ON orders (customer_id, created_at DESC)
            """,
            reverse_sql="""
                DROP INDEX CONCURRENTLY IF EXISTS orders_customer_created_idx
            """,
        ),
    ]
```

The exact migration strategy should match the project's Django and PostgreSQL versions.

### Alembic

With Alembic, index creation can be expressed directly:

```python
op.create_index(
    "orders_customer_created_idx",
    "orders",
    ["customer_id", "created_at"],
)
```

For PostgreSQL-specific concurrent behavior, use the appropriate migration options or explicit SQL and ensure the migration is not executed inside an incompatible transaction.

Always inspect generated migration SQL rather than relying on ORM metadata alone.

---

## Deployment Ordering

An index is often deployed before the application query that needs it.

```text
Create index
      ↓
Verify index
      ↓
Deploy application
      ↓
New query becomes active
      ↓
Observe plan
```

This avoids introducing a high-volume query before its intended access path exists.

However, the planner may begin using the index immediately after creation, even before application deployment, if existing queries can benefit from it.

Therefore, index creation itself should be treated as a production change.

---

## Query Plan Changes

Creating an index can change plans for existing queries.

This is generally desirable, but not always.

For example:

```text
Before
Query → Seq Scan

After index
Query → Index Scan
```

An index scan can be worse when:

- A large fraction of the table is returned
- Random heap access is expensive
- Statistics are stale
- The index is poorly selective

After deployment, observe actual production behavior rather than assuming the new plan is always better.

---

## Statistics

The planner depends on statistics.

After significant data changes, PostgreSQL may need updated statistics to make good decisions.

Inspect:

```sql
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    most_common_vals,
    histogram_bounds
FROM pg_stats
WHERE tablename = 'orders'
  AND attname IN ('customer_id', 'status');
```

For important changes, ensure `ANALYZE` and autovacuum are functioning properly.

Do not blame an index when the real problem is inaccurate cardinality estimation.

---

## Index Build on a Large Table

For a very large table:

```text
CREATE INDEX
      ↓
Large table scan
      ↓
CPU + I/O
      ↓
Index construction
      ↓
WAL / storage impact
      ↓
Replica pressure
```

Before starting, estimate:

- Table size
- Current disk usage
- Available disk
- Write rate
- CPU utilization
- I/O utilization
- Replica capacity
- Expected build duration

A failed index build because the database runs out of disk can become a major incident.

---

## Disk Capacity

An index requires additional storage.

Before deployment, check available capacity and existing database usage.

At the database level:

```sql
SELECT
    pg_size_pretty(pg_database_size(current_database()));
```

For a table:

```sql
SELECT
    pg_size_pretty(pg_total_relation_size('orders'));
```

For an index:

```sql
SELECT
    pg_size_pretty(pg_relation_size('orders_customer_created_idx'));
```

The actual index size depends on:

- Number of rows
- Key width
- Included columns
- Data distribution
- Index type
- PostgreSQL version
- Table contents

Do not assume an index is small because the indexed column is logically small.

---

## WAL and Replication

Index creation can generate substantial WAL and resource consumption.

```text
Index build
    ↓
Database work
    ↓
WAL
    ↓
Replica transport
    ↓
Replica replay
```

Potential consequences:

- Replica lag
- Increased replication bandwidth
- Larger WAL retention
- Delayed failover readiness
- Increased storage usage

Monitor replicas while building large indexes.

---

## Lock Contention

Even a concurrent index build can interact with transactions and locks.

Long-running transactions can delay phases of the operation.

Inspect active transactions:

```sql
SELECT
    pid,
    usename,
    state,
    xact_start,
    query_start,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

If a migration is waiting:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

The correct operational response is to identify the blocker and understand why it exists.

---

## lock_timeout

Migration execution can be protected from indefinite lock waits.

For example:

```sql
SET lock_timeout = '3s';
```

This is different from:

```sql
SET statement_timeout = '30min';
```

The distinction is:

| Setting | Meaning |
|---|---|
| `lock_timeout` | Maximum time waiting to acquire a lock |
| `statement_timeout` | Maximum total execution time |

A migration should fail quickly when it cannot acquire a required lock rather than silently consuming resources while waiting.

---

## Unique Indexes

Unique indexes can enforce application invariants.

For example:

```sql
CREATE UNIQUE INDEX CONCURRENTLY users_email_unique_idx
ON users (email);
```

However, before deploying a unique index:

```text
Check existing duplicates
       ↓
Repair duplicates
       ↓
Create unique index
```

Find duplicates:

```sql
SELECT
    email,
    count(*)
FROM users
GROUP BY email
HAVING count(*) > 1;
```

Do not discover duplicate data during a production uniqueness migration.

---

## Partial Indexes

If only a subset of rows matters, a partial index can reduce index size and maintenance cost.

Example:

```sql
CREATE INDEX CONCURRENTLY orders_pending_created_idx
ON orders (created_at DESC)
WHERE status = 'pending';
```

This can be effective when:

```text
Most rows → completed
Small active subset → pending
```

The query must have predicates that allow PostgreSQL to infer that the partial index applies.

For example:

```sql
SELECT id
FROM orders
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 100;
```

Do not assume a partial index will be used merely because the logical condition appears related.

---

## Expression Indexes

If the query transforms a column:

```sql
SELECT *
FROM customers
WHERE lower(email) = lower($1);
```

a normal index on:

```sql
(email)
```

may not provide the desired access path.

A suitable expression index can be:

```sql
CREATE INDEX CONCURRENTLY customers_lower_email_idx
ON customers (lower(email));
```

Deploy the index based on the actual expression used by the query.

---

## Covering Indexes

PostgreSQL supports included columns:

```sql
CREATE INDEX CONCURRENTLY orders_customer_created_idx
ON orders (customer_id, created_at DESC)
INCLUDE (total, status);
```

Included columns can help enable index-only scans without making those columns part of the index's search ordering.

Important distinction:

```text
Key columns
    ↓
Search / ordering structure

INCLUDE columns
    ↓
Payload for covering queries
```

Do not add large payload columns indiscriminately. They increase index size and maintenance cost.

---

## Index-Only Scans

A covering index may allow PostgreSQL to satisfy a query primarily from the index.

For example:

```sql
SELECT customer_id, created_at, total
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 100;
```

A suitable covering index can reduce heap access.

However, index-only scans still depend on PostgreSQL visibility information and table maintenance.

Do not assume:

```text
Index contains all columns
=
Always index-only
```

The execution plan is the authority.

---

## Removing an Index

Index deployment also includes knowing when not to keep an index.

Before removal, evaluate:

- `idx_scan`
- Query frequency
- Query latency
- Constraints
- Uniqueness enforcement
- Production workload
- Historical usage
- Recent application changes

Dropping an index can improve:

- Write performance
- Storage usage
- Cache efficiency
- Maintenance overhead

But it can also cause unexpected query regressions.

---

## DROP INDEX CONCURRENTLY

For an index that is safe to remove, PostgreSQL supports:

```sql
DROP INDEX CONCURRENTLY orders_customer_created_idx;
```

This is useful for production systems where normal workload must continue.

Like concurrent index creation, it has restrictions and should be treated as an operational migration rather than a trivial cleanup statement.

Verify that the index is not required for:

- Primary/unique enforcement
- Foreign-key-related requirements
- Critical query paths
- Application behavior

Do not delete an index simply because `idx_scan` is currently zero.

---

## Redundant Indexes

Consider:

```text
(customer_id)
(customer_id, created_at)
```

The first index may be redundant depending on the workload because the composite index can often support queries constrained by its leading column.

But redundancy must be evaluated carefully.

Potential reasons to retain both include:

- Different ordering requirements
- Different covering requirements
- Different partial predicates
- Significant size differences
- Different query patterns

Use workload evidence rather than purely structural comparison.

---

## Wide Indexes

Avoid creating:

```sql
CREATE INDEX ...
ON orders (customer_id, status, created_at, total, currency, ...)
```

just because it seems convenient.

Wide indexes increase:

- Storage
- Write amplification
- WAL
- Cache pressure
- Backup size
- Replication traffic
- Build time
- Maintenance cost

Use `INCLUDE` selectively when a covering index provides measurable value.

---

## Write Workload Impact

Every additional index can increase write cost.

For:

```text
INSERT
```

PostgreSQL must maintain:

```text
Heap
+
Index 1
+
Index 2
+
Index 3
...
```

This matters especially for:

- High-ingestion APIs
- Kafka consumers
- Celery workers
- Event stores
- Audit tables
- Time-series workloads

An index that saves 5 ms on a rare read may not justify a significant cost on millions of writes.

---

## Index Deployment in Read-Heavy Systems

Read-heavy systems generally tolerate more indexes than write-heavy systems.

Example:

```text
API
 ↓
PostgreSQL
 ├── Primary
 └── Read Replicas
```

Indexes may be deployed to support:

- Search
- Filtering
- Sorting
- Pagination
- Reporting

However, replicas also need the relevant index if queries are routed there.

Do not assume an index on the primary automatically means every independently managed read store has the same optimization.

---

## Index Deployment in Write-Heavy Systems

For high-write workloads, be conservative.

Example:

```text
Kafka
  ↓
Consumer
  ↓
PostgreSQL
  ↓
Millions of writes
```

Every additional index can increase ingestion cost.

Prioritize indexes that support:

- Critical reads
- Referential integrity
- Operational queries
- High-value access paths

Avoid speculative indexing.

---

## Multi-Tenant Applications

Suppose:

```sql
SELECT *
FROM invoices
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 100;
```

A common candidate is:

```sql
CREATE INDEX CONCURRENTLY invoices_tenant_status_created_idx
ON invoices (tenant_id, status, created_at DESC);
```

Tenant-aware indexes can be particularly important when:

- Most queries include tenant filtering.
- Tenants share tables.
- Row-level security is used.
- Large tenants create uneven workloads.

But index design should still consider:

- Tenant size distribution
- Selectivity
- Large-tenant behavior
- Partitioning
- Query frequency

---

## RLS and Indexes

Row-level security adds predicates to the effective query security model.

For example:

```text
Application query
      +
RLS policy
      ↓
Effective row filtering
```

Indexes should support the actual workload after considering tenant and authorization predicates.

However:

> **Indexes do not replace authorization.**

Do not remove tenant filtering or RLS because an index makes a query fast.

Security correctness remains separate from query optimization.

---

## Partitioned Tables

For partitioned tables, index deployment must account for partitions.

```text
orders
 ├── orders_2026_01
 ├── orders_2026_02
 ├── orders_2026_03
 └── orders_2026_04
```

Indexes may exist on individual partitions or be defined through the partitioned table depending on the PostgreSQL design.

Consider:

- Number of partitions
- Build concurrency
- Historical vs hot partitions
- Partition pruning
- Disk usage
- Deployment duration

Do not blindly create indexes independently on thousands of partitions without evaluating the operational impact.

---

## Keyset Pagination

Index deployment often supports scalable pagination.

Instead of:

```sql
SELECT id, created_at
FROM orders
ORDER BY created_at DESC
OFFSET 100000
LIMIT 100;
```

a keyset approach can use:

```sql
SELECT id, created_at
FROM orders
WHERE created_at < $1
ORDER BY created_at DESC
LIMIT 100;
```

A suitable index:

```sql
CREATE INDEX CONCURRENTLY orders_created_id_idx
ON orders (created_at DESC, id DESC);
```

The exact predicate should account for ties.

For example:

```sql
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 100;
```

This can provide a much more scalable access pattern for large datasets.

---

## ORM Considerations

Django and SQLAlchemy can hide the SQL that drives index requirements.

For Django:

```python
Order.objects.filter(
    customer_id=customer_id,
    status="pending",
).order_by("-created_at")[:100]
```

Inspect the generated SQL and execution plan.

For SQLAlchemy:

```python
stmt = (
    select(Order)
    .where(
        Order.customer_id == customer_id,
        Order.status == "pending",
    )
    .order_by(Order.created_at.desc())
    .limit(100)
)
```

The index should be based on the actual SQL semantics rather than ORM model fields alone.

---

## CI/CD Integration

Index deployment should be treated as a controlled deployment artifact.

A mature pipeline might be:

```text
Pull Request
    ↓
Migration Review
    ↓
SQL / Plan Validation
    ↓
Staging Test
    ↓
Production Migration
    ↓
Verification
    ↓
Application Deployment
```

Reviewers should ask:

- Why is the index needed?
- What query does it support?
- What is the expected size?
- Is concurrent creation required?
- Can it run during peak traffic?
- What is the rollback plan?
- What happens to replicas?

---

## Canary Deployment

For high-risk query changes:

```text
Create index
     ↓
Deploy to small percentage of traffic
     ↓
Observe query plan and latency
     ↓
Increase traffic
     ↓
Full rollout
```

This is especially useful when the new index changes a critical query plan.

Monitor:

- p50 latency
- p95 latency
- p99 latency
- CPU
- I/O
- database load
- error rates
- query execution statistics

---

## Query Plan Regression

An index can improve one query and degrade another.

For example:

```text
Query A
Before: 500 ms
After:   20 ms

Query B
Before: 30 ms
After:  200 ms
```

Possible reasons include:

- Planner choice
- Statistics
- Different data distributions
- Generic/custom plan behavior
- Cache effects
- Index competition

Use production telemetry to evaluate the overall workload.

---

## Monitoring Index Builds

During large index creation, monitor:

- Database CPU
- Disk I/O
- Disk capacity
- WAL generation
- Replication lag
- Active sessions
- Lock waits
- Query latency

Do not monitor only:

```text
Migration process: running
```

The database and application must remain healthy while the migration runs.

---

## PostgreSQL Index Monitoring

Useful catalog views include:

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

Index size:

```sql
SELECT
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

For deeper analysis, combine index statistics with:

- `pg_stat_statements`
- `EXPLAIN`
- `EXPLAIN ANALYZE`
- Database CPU/I/O metrics
- Application latency

No single statistic is sufficient for index lifecycle decisions.

---

## Security Considerations

Index definitions can expose information about data structures.

Restrict migration privileges appropriately.

Also consider:

- Migration credentials
- Audit logging
- Production SQL review
- Sensitive table names
- Access to query statistics
- Backup and replication exposure

Indexes can contain copies of indexed data, so sensitive values may exist in more than one physical structure.

Do not assume:

```text
Column encrypted
=
Every derived database structure has identical security properties
```

Evaluate the database's encryption, access controls, and data-handling requirements as a whole.

---

## High Availability

For HA PostgreSQL systems:

```text
Primary
   │
   ├── Replica A
   └── Replica B
```

A large index build can affect:

- Primary load
- WAL generation
- Replica lag
- Failover readiness
- Disk usage

Before a major index deployment:

- Verify replica health.
- Check replication capacity.
- Monitor lag continuously.
- Confirm enough disk headroom.
- Understand failover behavior.

A performance optimization should not reduce availability.

---

## Disaster Recovery

Index creation is generally reproducible from schema definitions, but the operational impact can still matter for recovery.

Large indexes affect:

- Backup size
- Restore time
- Storage
- WAL volume

For disaster recovery planning, consider:

```text
Schema migration
      ↓
Backup / PITR
      ↓
Recovery
      ↓
Index state
```

A migration should be represented in version-controlled schema definitions so a recovered environment can reproduce the intended database structure.

---

## Cost Considerations

An index has both build cost and ongoing cost.

### Build Cost

- CPU
- I/O
- Temporary storage
- WAL
- Replication
- Migration runtime

### Ongoing Cost

- Disk
- Cache memory
- INSERT/UPDATE/DELETE overhead
- Vacuum/maintenance
- Backup storage
- Replication traffic

A useful engineering question is:

> **What production workload justifies this index's lifetime cost?**

---

## Common Mistakes

### Creating an Index Without a Query

**Problem:** Adds storage and write overhead without measurable benefit.

**Better:** Start with an actual workload problem.

### Assuming Every Sequential Scan Is Bad

**Problem:** PostgreSQL may correctly choose a sequential scan for small or low-selectivity workloads.

**Better:** Evaluate the complete execution plan and workload.

### Creating Separate Indexes for Every Filter Column

**Problem:** Multiple indexes may cost more than a carefully designed composite index.

**Better:** Design around complete access patterns.

### Using `CREATE INDEX CONCURRENTLY` Without Understanding Its Restrictions

**Problem:** It cannot run inside a transaction block and has different operational behavior.

**Better:** Make migration tooling explicitly compatible with concurrent index creation.

### Running `EXPLAIN ANALYZE` on Production DML

**Problem:** `EXPLAIN ANALYZE` executes the statement.

**Better:** Use plain `EXPLAIN` when execution would be unsafe.

### Ignoring Disk Headroom

**Problem:** A large index build can consume substantial storage.

**Better:** Estimate and monitor storage before deployment.

### Ignoring Replication

**Problem:** Large index builds can increase WAL and replica lag.

**Better:** Monitor replication throughout the operation.

### Keeping Redundant Indexes Forever

**Problem:** Unnecessary indexes increase write cost and storage.

**Better:** Review index usage periodically using workload evidence.

### Removing an Index Based Only on `idx_scan`

**Problem:** Low usage may reflect a short observation period or infrequent but important workloads.

**Better:** Consider business-critical queries, seasonality, constraints, and historical behavior.

### Making Every Index Cover Everything

**Problem:** Wide indexes increase storage and write amplification.

**Better:** Use narrow keys and `INCLUDE` selectively.

---

## Production Index Deployment Checklist

### Before Deployment

- [ ] Identify the slow or high-value query
- [ ] Capture representative SQL
- [ ] Inspect existing indexes
- [ ] Inspect current execution plan
- [ ] Confirm query frequency
- [ ] Analyze selectivity
- [ ] Design candidate index
- [ ] Estimate index size
- [ ] Verify disk headroom
- [ ] Review write workload
- [ ] Review replication capacity
- [ ] Decide whether concurrent creation is required
- [ ] Define rollback/cleanup procedure

### During Deployment

- [ ] Set appropriate migration timeouts
- [ ] Create index using the appropriate method
- [ ] Monitor CPU
- [ ] Monitor I/O
- [ ] Monitor disk usage
- [ ] Monitor WAL
- [ ] Monitor replication lag
- [ ] Monitor lock waits
- [ ] Monitor application latency
- [ ] Monitor connection pressure

### After Deployment

- [ ] Verify index validity
- [ ] Verify execution plan
- [ ] Measure query latency
- [ ] Compare database resource usage
- [ ] Check replica health
- [ ] Check application error rates
- [ ] Confirm expected index usage
- [ ] Document the reason for the index
- [ ] Review long-term index cost

---

## Production Example

Suppose an orders API frequently executes:

```sql
SELECT id, created_at, total
FROM orders
WHERE customer_id = $1
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 50;
```

Initial investigation:

```text
5 million orders
High request frequency
Sequential scan
High database CPU
```

Candidate index:

```sql
CREATE INDEX CONCURRENTLY orders_customer_status_created_idx
ON orders (customer_id, status, created_at DESC);
```

Deployment:

```text
Analyze query
    ↓
Inspect existing indexes
    ↓
Estimate index size
    ↓
Check disk headroom
    ↓
Create concurrently
    ↓
Monitor database + replicas
    ↓
Verify plan
    ↓
Measure API latency
```

Expected outcome:

```text
Before
API → Seq Scan → many rows examined → high latency

After
API → B-tree index → small candidate set → lower latency
```

But the final decision should be based on production measurements, not the expectation alone.

---

## Senior-Level Index Review

A senior engineer should evaluate an index across four dimensions.

### Query Value

- Which query does it optimize?
- How frequently does that query execute?
- What is its latency?
- What is its business importance?

### Index Quality

- Is the column order correct?
- Is selectivity sufficient?
- Could a partial index be better?
- Could `INCLUDE` help?
- Is the index redundant?

### Operational Cost

- How large is it?
- How much write amplification does it introduce?
- How expensive is creation?
- What is the replication impact?
- What is the backup cost?

### Lifecycle

- How will usage be monitored?
- When should it be reconsidered?
- What evidence would justify removal?

A strong index design therefore looks like:

```text
Query evidence
     +
Access-pattern analysis
     +
Execution-plan validation
     +
Operational cost analysis
     +
Production measurement
     ↓
Index decision
```

---

## Key Takeaways

- **Deploy indexes from workload evidence, not intuition:** start with real queries, execution plans, selectivity, and frequency.
- **Treat index creation as a production workload:** evaluate locks, CPU, I/O, disk capacity, WAL generation, replication lag, and migration tooling.
- **Use `CREATE INDEX CONCURRENTLY` deliberately for busy production tables:** it reduces write blocking but remains resource-intensive and has transaction and failure-handling constraints.
- **An index has lifetime cost:** storage, write amplification, cache pressure, backups, replication, and maintenance must be justified by measurable query value.
- **Validate after deployment:** compare execution plans, latency, resource consumption, and index usage rather than assuming a new index automatically improves the system.