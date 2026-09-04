# 20- SQL Troubleshooting Questions

## Overview

SQL troubleshooting interviews test whether you can move from a symptom to a measurable root cause.

A strong backend engineer does not respond to:

> "The database is slow."

with:

> "Add an index."

Instead, reason through the complete execution path:

```text
Application
    ↓
Connection pool
    ↓
Transaction
    ↓
SQL + parameters
    ↓
Query planner
    ↓
Execution
    ↓
Locks / I/O / CPU / memory
    ↓
Result transfer
    ↓
Application processing
```

The objective is to determine whether the problem is caused by:

- Query design
- Missing or incorrect indexes
- Poor cardinality estimates
- Lock contention
- Long transactions
- Connection exhaustion
- CPU or memory pressure
- I/O saturation
- Replica lag
- ORM-generated SQL
- N+1 queries
- Excessive query volume
- Data growth
- Schema or migration changes
- Application behavior
- Infrastructure capacity

For senior-level interviews, explain both **how you would diagnose the issue** and **how you would prevent the same class of failure from recurring**.

---

## Troubleshooting Framework

A reliable troubleshooting process is:

```text
Observe
  ↓
Reproduce
  ↓
Measure
  ↓
Classify
  ↓
Inspect SQL
  ↓
Inspect execution plan
  ↓
Check database waits/resources
  ↓
Check application behavior
  ↓
Mitigate
  ↓
Fix root cause
  ↓
Validate
  ↓
Monitor for regression
```

### First Questions to Ask

Before changing anything, establish:

| Question | Why it matters |
|---|---|
| What is slow? | Query, endpoint, transaction, or entire database |
| When did it start? | Correlates with deployment, migration, or data growth |
| Is it always slow? | Distinguishes deterministic problems from contention/load |
| How much data exists? | Determines scalability characteristics |
| How frequently does it run? | Total workload may matter more than single-query latency |
| Is it read or write heavy? | Determines appropriate optimization strategies |
| Is it primary or replica? | Replica lag and replay behavior can change symptoms |
| What changed recently? | Often identifies the fastest path to root cause |
| What is the consistency requirement? | Determines whether replicas/cache are acceptable |
| What happens under concurrency? | Exposes locks, pool exhaustion, and race conditions |

---

## Scenario: A Query Is Suddenly Slow

### Question

A query that normally takes 50 ms now takes 5 seconds. How do you investigate?

### Strong Answer

First capture the exact SQL, parameters, execution frequency, and affected environment.

Then inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

Compare:

```text
estimated rows
vs
actual rows
```

and inspect:

- Scan type
- Join strategy
- Sorts
- Aggregations
- Buffer hits/reads
- Execution time
- Loops
- Temporary I/O

Then check whether the query is waiting rather than executing.

Possible causes include:

```text
bad execution plan
lock contention
CPU saturation
I/O pressure
connection pool wait
replica lag
stale statistics
data growth
recent index/migration changes
```

### Interview Trap

Do not immediately add an index.

A query can be slow even with the correct index if it is blocked on a lock or waiting for a connection.

---

## Scenario: Query Has a Sequential Scan

### Question

`EXPLAIN` shows a sequential scan. Is that automatically a problem?

### Answer

No.

PostgreSQL may correctly choose a sequential scan when:

- The table is small.
- The query returns a large fraction of the table.
- The predicate has low selectivity.
- An index would require excessive random access.
- Planner statistics indicate a sequential scan is cheaper.

The correct question is:

> Is the chosen access path appropriate for this workload?

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

to validate the decision.

---

## Scenario: Index Exists but PostgreSQL Does Not Use It

### Question

There is an index on `customer_id`, but PostgreSQL still uses a sequential scan. Why?

Possible causes:

| Cause | Explanation |
|---|---|
| Low selectivity | Most rows match |
| Small table | Sequential scan is cheaper |
| Wrong index | Query uses a different access pattern |
| Composite ordering | Indexed columns do not align with predicate |
| Stale statistics | Planner estimates are inaccurate |
| Expression mismatch | Query expression differs from indexed expression |
| Type mismatch | Implicit conversion can interfere with index usage |
| Query returns many rows | Sequential access may be cheaper |
| Cost configuration | Planner cost assumptions influence plan selection |

Never treat "index not used" as proof that the optimizer is wrong.

---

## Scenario: Query Returns Too Many Rows

### Question

An endpoint expects 100 records but receives 100,000. How do you troubleshoot it?

First define the intended result grain.

For example:

```text
Expected:
one row per order

Actual:
one row per order item
```

Then inspect joins.

A one-to-many join naturally multiplies rows.

Check:

```text
JOIN predicates
foreign-key relationships
many-to-many relationships
LEFT JOIN conditions
missing tenant filters
soft-delete filters
```

Do not blindly use:

```sql
DISTINCT
```

to hide the problem.

The underlying join cardinality should be corrected.

---

## Scenario: Query Returns No Rows

### Question

The data exists, but the query returns zero rows. What do you check?

Check systematically:

```text
database/environment
schema
parameters
NULL semantics
case/whitespace
timestamps/time zones
tenant filtering
soft deletion
RLS
transaction visibility
replica lag
join predicates
```

Simplify the query:

```sql
SELECT id
FROM customers
WHERE id = $1;
```

Then add predicates and joins incrementally.

### Senior Consideration

If the write went to the primary and the read went to an asynchronous replica, the data may not have replayed yet.

---

## Scenario: Query Has the Wrong Execution Plan

### Question

A query previously used an index but now uses a sequential scan. What could have changed?

Investigate:

```text
data volume
data distribution
statistics
index availability
query parameters
PostgreSQL version
planner configuration
query text
parameter-sensitive planning
```

Run:

```sql
ANALYZE orders;
```

if statistics are stale.

Then compare the old and current plans.

### Senior Principle

Execution plans are workload-dependent. A plan that was optimal yesterday may not be optimal after significant data distribution changes.

---

## Scenario: Estimated Rows Are Very Different from Actual Rows

### Example

```text
Estimated rows: 100
Actual rows:    5,000,000
```

### Why It Matters

The optimizer uses cardinality estimates to select join strategies, scan methods, sorting, aggregation, and parallelism.

A severe estimation error can therefore produce a poor plan.

Investigate:

- Statistics freshness
- Data skew
- Correlated columns
- Complex predicates
- Expression selectivity
- Parameter values

For correlated columns, PostgreSQL extended statistics may improve estimates.

### Interview Answer

> "I would compare estimated and actual cardinality before changing indexes because a planner decision can be wrong because of inaccurate statistics rather than missing indexes."

---

## Scenario: Query Is Slow Because of a JOIN

### Investigation

Inspect:

```text
join order
join cardinality
join predicates
indexes on join keys
estimated vs actual rows
join algorithm
```

PostgreSQL may use:

- Nested loop
- Hash join
- Merge join

A nested loop can be excellent when the outer relation is small and the inner side is efficiently indexed, but disastrous when cardinality is underestimated.

A hash join can be effective for larger equality joins but may require significant memory.

A merge join can be useful when both inputs are appropriately ordered.

---

## Scenario: Nested Loop Processes Millions of Rows

### Question

Why might a nested loop become unexpectedly expensive?

Example:

```text
outer rows = 1,000,000
inner lookup = 1
```

Even a cheap inner operation may be repeated a million times.

Inspect:

```text
loops
actual rows
index lookup cost
outer cardinality estimate
```

If the planner expected:

```text
outer rows = 10
```

but receives:

```text
outer rows = 1,000,000
```

the plan may be fundamentally inappropriate.

The root cause may be cardinality estimation rather than the join algorithm itself.

---

## Scenario: Query Has a Large Sort

### Question

How do you troubleshoot a slow `ORDER BY`?

Check:

- Number of rows entering the sort
- Whether filtering occurs early
- Whether ordering is actually required
- Whether an index can provide the desired order
- Whether `LIMIT` can reduce work
- Whether the sort spills to temporary storage

For:

```sql
SELECT id, created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

an index aligned with the access pattern may help:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

The index should be validated against the actual workload and write cost.

---

## Scenario: Query Uses Too Much Memory

### Possible Causes

- Large sort
- Hash join
- Hash aggregation
- Large result set
- Excessive concurrency
- Large `work_mem`
- Many concurrent operations

A critical PostgreSQL concept is that `work_mem` applies to individual operations, not as one global memory allocation per query.

One query can contain multiple memory-intensive operators, and many sessions can execute simultaneously.

Therefore:

```text
memory risk
≈
per-operation memory
×
operations
×
concurrent sessions
```

Do not blindly increase `work_mem` globally.

---

## Scenario: Database CPU Is 100%

### Question

What do you do?

First determine whether CPU is caused by:

```text
query cost
query frequency
concurrency
N+1 behavior
retry storms
background workers
autovacuum
DDL
```

Inspect query statistics:

```sql
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

Then correlate with:

```text
pg_stat_activity
execution plans
wait events
application deployments
worker activity
infrastructure metrics
```

### Important Distinction

These workloads are different:

```text
Query A:
5 seconds × 1 call

Query B:
5 ms × 1,000,000 calls
```

Query B can consume much more total CPU.

---

## Scenario: Database Memory Is High

### Question

PostgreSQL memory usage is high. Is that automatically an incident?

No.

Evaluate:

```text
MemAvailable
swap usage
OOM events
database latency
query memory
connection count
shared buffers
OS cache
container limits
```

A high cache utilization can be healthy.

The dangerous signals are things such as:

```text
memory pressure
swapping
OOM kills
latency increase
query failures
```

Investigate the full hierarchy:

```text
PostgreSQL
 ↓
OS page cache
 ↓
application
 ↓
Redis
 ↓
Kafka / workers
 ↓
container / VM limits
```

---

## Scenario: Connection Pool Is Exhausted

### Symptoms

```text
request timeout
connection acquisition timeout
low database CPU
```

### Possible Causes

- Slow queries
- Long transactions
- Lock waits
- Connection leaks
- External calls inside transactions
- Database failure
- Pool configured too small

Inspect:

```sql
SELECT
    state,
    wait_event_type,
    wait_event,
    count(*)
FROM pg_stat_activity
GROUP BY state, wait_event_type, wait_event;
```

Then compare:

```text
application pool usage
vs
database connection usage
```

### Senior Insight

Pool exhaustion is often a downstream symptom.

Increasing pool size without finding the cause can move the bottleneck into PostgreSQL.

---

## Scenario: Database Has Too Many Connections

### Question

The application has multiple Kubernetes replicas, each with a connection pool. How do you calculate capacity?

Suppose:

```text
30 pods
×
10 connections
=
300 connections
```

Then add:

```text
Celery workers
migration jobs
administrative connections
monitoring
other services
```

The database must be able to handle the aggregate.

Connection limits are not only a database setting; they are an application architecture concern.

---

## Scenario: Requests Are Waiting for Locks

### Investigation

Identify:

```text
waiting session
blocking session
locked relation
transaction age
query
application request
```

Useful PostgreSQL information includes:

```sql
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    query,
    xact_start
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

Use `pg_locks` and `pg_blocking_pids()` to reconstruct the blocking relationship.

### Senior Approach

Do not only investigate the waiting query.

Find the blocker.

Then determine why the blocker is holding the lock for so long.

---

## Scenario: Lock Contention Is High but There Are No Deadlocks

### Explanation

Lock contention means sessions are waiting for conflicting locks.

A deadlock is a specific cycle:

```text
A waits for B
B waits for A
```

Contention can occur without any cycle.

### Mitigation

- Shorten transactions.
- Reduce lock scope.
- Reduce hot-row contention.
- Avoid external calls inside transactions.
- Use atomic SQL.
- Use optimistic concurrency where appropriate.
- Use `NOWAIT` or `SKIP LOCKED` where semantics allow.

---

## Scenario: Deadlocks Occur in Production

### Question

How do you diagnose and prevent them?

PostgreSQL reports deadlocks using:

```text
SQLSTATE 40P01
```

Inspect:

```text
deadlock logs
pg_locks
pg_stat_activity
transaction order
application code
foreign-key behavior
triggers
advisory locks
```

Most common design solution:

```text
establish deterministic lock ordering
```

For example:

```text
Transaction A:
account 10 → account 20

Transaction B:
account 20 → account 10
```

should become:

```text
both:
account 10 → account 20
```

Retry the **entire transaction** with bounded exponential backoff and jitter.

---

## Scenario: `statement_timeout` vs `lock_timeout`

### Question

What is the difference?

| Setting | Purpose |
|---|---|
| `statement_timeout` | Limits total statement execution time |
| `lock_timeout` | Limits time waiting to acquire a lock |

A query can therefore spend time:

```text
waiting for lock
```

before it performs any meaningful execution.

Use the appropriate timeout for the failure mode.

Do not use timeouts as a substitute for fixing persistent contention.

---

## Scenario: Query Is Slow Only Under Load

### Possible Causes

A query that is fast in isolation can become slow because of:

```text
CPU contention
I/O contention
lock waits
connection pool queueing
memory pressure
cache behavior
concurrent updates
replica replay
```

Therefore benchmark both:

```text
single-query latency
```

and:

```text
realistic concurrent workload
```

### Interview Insight

Production performance is a property of the complete workload, not just one execution.

---

## Scenario: Query Is Fast but API Is Slow

### Example

```text
SQL execution: 20 ms
API latency:   2 seconds
```

Investigate:

```text
connection acquisition
multiple hidden queries
ORM processing
serialization
external services
network transfer
application CPU
```

Trace:

```text
request
 ↓
pool acquisition
 ↓
SQL
 ↓
result transfer
 ↓
ORM
 ↓
serialization
 ↓
response
```

Do not optimize a 20 ms query when the request spends most of its time elsewhere.

---

## Scenario: Django Endpoint Has N+1 Queries

### Symptoms

```text
100 orders
101 SQL queries
```

Inspect ORM access patterns.

Use:

```python
orders = (
    Order.objects
    .select_related("customer")
    .prefetch_related("items")
)
```

But validate the resulting SQL and response size.

Eager loading can itself become expensive when relationships are large.

### Interview Answer

> "I would first identify which relationship causes the N+1 pattern, then use `select_related` or `prefetch_related` based on relationship type, and validate query count, execution time, row multiplication, and memory usage."

---

## Scenario: Query Uses `SELECT *`

### Question

Why can `SELECT *` be problematic?

It can increase:

```text
database I/O
network transfer
driver decoding
ORM object creation
serialization
memory
```

Prefer the columns actually required by the operation.

This is especially important for:

- Wide tables
- APIs
- Large exports
- Frequently executed queries

---

## Scenario: Query Returns Millions of Rows

### Problem

A Python application loads the entire result set into memory.

### Better Design

Use:

```text
pagination
streaming where appropriate
batch processing
background jobs
bulk database operations
```

For large exports:

```text
API
 ↓
create job
 ↓
Celery
 ↓
database extraction
 ↓
object storage
 ↓
download
```

Do not hold an HTTP request and database transaction open while processing millions of records.

---

## Scenario: OFFSET Pagination Becomes Slow

### Query

```sql
SELECT id, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 50
OFFSET 1000000;
```

The database may need to process and discard many preceding rows.

Use keyset pagination where appropriate:

```sql
SELECT id, created_at
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

A supporting index should align with the ordering and filtering pattern.

---

## Scenario: Query Is Slow Because of an Incorrect Index

### Question

How do you determine whether an index is wrong rather than missing?

Inspect:

```text
query predicates
join keys
ordering
composite column order
partial predicate
expression
data distribution
selectivity
index size
index usage
write cost
```

An index can exist and still be ineffective because its column order does not match the access pattern.

For example:

```text
WHERE tenant_id = ?
  AND status = ?
ORDER BY created_at DESC
```

may need an index designed around that complete workload rather than separate indexes chosen independently.

---

## Scenario: Too Many Indexes Slow Writes

Every index can increase write cost.

An `INSERT`, `UPDATE`, or `DELETE` may need to maintain multiple indexes.

Excess indexes can increase:

```text
WAL
storage
write latency
vacuum work
replication traffic
maintenance cost
```

Therefore index design is a trade-off:

```text
read performance
vs
write cost
vs
storage
vs
maintenance
```

Do not keep indexes simply because they were once useful.

---

## Scenario: Missing Foreign-Key Index Causes Performance Problems

A foreign key does not automatically mean that the referencing column has an index in PostgreSQL.

For example:

```text
orders.customer_id
```

may benefit from an index if the application frequently:

```text
joins by customer_id
filters by customer_id
deletes/updates parent rows
```

The index should be justified by actual access patterns.

---

## Scenario: Statistics Are Stale

### Symptoms

```text
bad plan
incorrect row estimates
unexpected join strategy
```

Run targeted statistics maintenance where appropriate:

```sql
ANALYZE orders;
```

For persistent problems, investigate:

```text
autovacuum/analyze configuration
data churn
column statistics
extended statistics
```

Do not repeatedly run `ANALYZE` as a blind fix without understanding why estimates become inaccurate.

---

## Scenario: Autovacuum Is Behind

### Symptoms

Potential signals include:

```text
dead tuples increasing
table/index growth
bloat
slow queries
transaction ID pressure
```

Investigate:

```text
table churn
autovacuum activity
long-running transactions
autovacuum thresholds
table-specific settings
```

A common mistake is treating autovacuum as an optional maintenance process.

For PostgreSQL production systems, it is fundamental to healthy MVCC operation.

---

## Scenario: Long-Running Transaction Causes Problems

### Why It Matters

A long transaction can:

- Keep snapshots old
- Delay cleanup
- Increase bloat
- Hold locks
- Consume connections
- Interfere with replication/recovery behavior

Check:

```sql
SELECT
    pid,
    state,
    xact_start,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start;
```

Avoid:

```text
BEGIN
 ↓
database operation
 ↓
HTTP request
 ↓
external API
 ↓
more processing
 ↓
COMMIT
```

Keep database transactions focused.

---

## Scenario: Idle in Transaction Sessions Exist

### Problem

A connection has started a transaction but is not actively executing a query.

This can be harmful because the transaction may retain:

```text
snapshot
locks
connection
```

and interfere with cleanup.

Investigate:

```sql
SELECT
    pid,
    state,
    xact_start,
    state_change,
    query
FROM pg_stat_activity
WHERE state = 'idle in transaction';
```

Application transaction handling and pool behavior should be reviewed.

---

## Scenario: Replica Lag Is Increasing

### Investigation

Determine whether the bottleneck is:

```text
WAL generation
network transfer
replica I/O
replica CPU
replay rate
long-running replica queries
```

Bulk writes and migrations can dramatically increase WAL volume.

Monitor:

```text
write LSN
flush/replay LSN
replication lag
WAL retention
```

If consistency-sensitive reads depend on the replica, route them appropriately during lag.

---

## Scenario: Read Replica Returns Stale Data

### Example

```text
POST /orders
 → primary

GET /orders/123
 → replica

result:
not found
```

This can be normal under asynchronous replication.

Solutions include:

- Read from primary after writes.
- Use consistency-aware routing.
- Use LSN-aware routing.
- Accept eventual consistency when the product permits it.

The solution depends on business semantics.

---

## Scenario: Primary Is Overloaded Despite Read Replicas

### Investigation

Check:

```text
read traffic still hitting primary
write workload
WAL generation
index maintenance
autovacuum
background jobs
replication overhead
```

Replicas do not reduce the cost of writes on the primary.

---

## Scenario: Migration Makes Queries Slow

### Possible Causes

- DDL lock
- Table rewrite
- Index build
- Large backfill
- Increased WAL
- Replica lag
- Autovacuum pressure
- Storage I/O saturation

For large changes, separate:

```text
schema expansion
+
data migration
+
application cutover
+
schema contraction
```

Use online/concurrent techniques where supported and validate locking behavior before production execution.

---

## Scenario: Large UPDATE Causes Database Problems

### Bad Approach

```sql
UPDATE orders
SET status = 'archived'
WHERE created_at < $1;
```

on hundreds of millions of rows in one transaction.

Potential consequences:

```text
large WAL
dead tuples
long transaction
replica lag
vacuum pressure
lock impact
```

Prefer bounded batches with checkpoints and throttling.

For example:

```text
find next batch
 ↓
update batch
 ↓
commit
 ↓
record progress
 ↓
repeat
```

---

## Scenario: Large DELETE Causes Replica Lag

A large delete generates WAL and creates dead tuples.

Possible strategies:

```text
bounded deletes
+
throttling
+
monitoring
```

For time-based retention, partitioning can be much more operationally efficient than deleting individual rows.

---

## Scenario: Background Workers Cause Database Saturation

### Situation

Celery workers are increased from 20 to 200.

Database CPU and connections spike.

### Root Cause

Application concurrency exceeded useful database capacity.

Control:

```text
worker concurrency
connection pools
batch size
transaction duration
retry rate
queue depth
```

Background processing should have a separate resource budget from latency-sensitive API traffic.

---

## Scenario: Retry Storm Causes Database Failure

### Sequence

```text
Database slows
    ↓
requests timeout
    ↓
clients retry
    ↓
more queries
    ↓
database becomes slower
    ↓
more retries
```

This is positive feedback.

Use:

- Exponential backoff
- Jitter
- Maximum retry attempts
- Timeouts
- Circuit breakers where appropriate
- Idempotency
- Rate limiting
- Load shedding

Retries should reduce pressure, not amplify it.

---

## Scenario: Query Fails with a Constraint Error

### Question

Should the application retry?

Usually not.

Classify the error first.

Examples:

```text
unique violation
foreign-key violation
check violation
not-null violation
serialization failure
deadlock
connection failure
```

Some are permanent application/data errors.

Others are transient concurrency or infrastructure failures.

Only retry errors when the operation is actually retryable.

---

## Scenario: Serialization Failures Occur

PostgreSQL can raise:

```text
SQLSTATE 40001
```

for serialization failures.

A serialization failure is a signal that the transaction could not safely commit under the selected isolation semantics.

The correct pattern is:

```text
retry whole transaction
+
bounded backoff
+
jitter
+
idempotent operation
```

Do not retry only the failed SQL statement while keeping the invalid transaction state.

---

## Scenario: Application Reports "Current Transaction Is Aborted"

### Cause

A statement inside a PostgreSQL transaction failed.

Subsequent statements fail until the transaction is rolled back or a savepoint is used appropriately.

For Django:

```python
from django.db import transaction

with transaction.atomic():
    ...
```

Use nested `atomic()` blocks/savepoints when partial recovery is intentionally required.

### Interview Trap

Do not continue issuing SQL inside a transaction after an error as though nothing happened.

---

## Scenario: Query Is Slow Because of a Lock, Not Execution

### Question

`EXPLAIN ANALYZE` appears to show a query taking seconds. How do you distinguish execution from waiting?

Check:

```text
wait_event_type
wait_event
lock relationships
transaction duration
application timing
```

A query can spend most of its wall-clock time waiting for another transaction.

This distinction matters because adding an index will not fix a lock wait.

---

## Scenario: Query Is Slow Only for One Customer

### Possible Causes

- Tenant has unusually large data volume.
- Data distribution is highly skewed.
- Query plan is parameter-sensitive.
- Customer-specific hot rows exist.
- Missing tenant-aware index.
- Large tenant creates a noisy-neighbor effect.

This is common in multi-tenant systems.

Possible architectural responses include:

```text
tenant-aware indexes
partitioning
workload isolation
tenant sharding
dedicated resources for large tenants
```

---

## Scenario: Cache Misses Cause Database Overload

### Sequence

```text
Redis unavailable
    ↓
all requests hit PostgreSQL
    ↓
database load increases
    ↓
latency increases
```

This is a cache failure amplification problem.

A cache fallback should be capacity-aware.

Possible mitigations:

- Request coalescing
- TTL jitter
- Rate limiting
- Load shedding
- Stale cache serving where acceptable
- Controlled fallback

A cache should improve performance without becoming a hidden single point of failure.

---

## Scenario: Database Is Healthy but Endpoint Is Still Slow

Measure the complete latency budget:

```text
Nginx / ALB
 ↓
application
 ↓
connection pool
 ↓
database
 ↓
result transfer
 ↓
application processing
 ↓
Redis
 ↓
external services
```

Use distributed tracing where available.

A senior engineer should be able to explain:

> "The SQL query is healthy, but the endpoint is slow because the application waits 1.2 seconds for another dependency."

---

## Scenario: Query Works in Development but Not Production

Check differences in:

```text
data volume
data distribution
indexes
statistics
PostgreSQL version
configuration
collation
concurrency
query parameters
extensions
schema
```

Production-like data volume is especially important for query-plan testing.

---

## Scenario: Query Becomes Slow After Data Growth

A query may be acceptable at:

```text
100,000 rows
```

and unacceptable at:

```text
100,000,000 rows
```

Investigate:

```text
access path
selectivity
index design
pagination
partitioning
retention
query frequency
```

Ask:

> What happens at 10× the current data volume?

This is a senior-level scalability question.

---

## Scenario: Query Uses a Function on an Indexed Column

### Query

```sql
SELECT id
FROM users
WHERE LOWER(email) = LOWER($1);
```

An ordinary index on:

```text
email
```

does not necessarily match the expression.

An expression index may be appropriate:

```sql
CREATE INDEX users_lower_email_idx
ON users (LOWER(email));
```

The general principle is:

> The indexed expression must match the query's access pattern.

---

## Scenario: Type Conversion Prevents Efficient Access

Suppose a column is:

```text
BIGINT
```

but application code sends values using incompatible types or expressions.

Investigate:

```text
column type
parameter type
casts
operators
expression
index definition
```

Avoid unnecessary casts around indexed columns.

Correct data modeling and parameter binding reduce this class of problem.

---

## Scenario: `LIKE` Search Is Slow

Compare:

```sql
WHERE email LIKE 'admin%'
```

with:

```sql
WHERE email LIKE '%example.com'
```

A leading wildcard generally prevents ordinary B-tree indexing from being used in the same way as a left-anchored prefix search.

For advanced substring/fuzzy search, PostgreSQL extensions and specialized indexes such as trigram indexes may be appropriate.

Choose the index based on actual search semantics.

---

## Scenario: JSON Query Is Slow

If application data is stored in JSON/JSONB, inspect:

```text
operator
path
selectivity
index type
query frequency
document size
```

Possible solutions include:

- Appropriate GIN indexes
- Expression indexes
- Generated/derived columns
- Normalized relational columns for heavily queried attributes

Do not put frequently queried relational fields into JSON simply to avoid schema design.

---

## Scenario: Aggregation Is Slow

### Query

```sql
SELECT customer_id, SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

Investigate:

```text
number of rows scanned
filter selectivity
aggregation strategy
sort/hash memory
partition pruning
OLTP vs OLAP workload
```

If the query scans billions of transactional rows repeatedly, consider:

```text
materialized view
pre-aggregation
read model
OLAP warehouse
```

rather than endlessly tuning the same OLTP query.

---

## Scenario: Aggregation Returns Incorrect Results

Check:

```text
result grain
join multiplication
NULL behavior
GROUP BY columns
DISTINCT usage
filter placement
```

For example, joining:

```text
orders
+
order_items
+
payments
```

before aggregating order totals can multiply rows.

Aggregate each relationship at the appropriate grain before combining them.

---

## Scenario: `LEFT JOIN` Produces Unexpected Results

Consider:

```sql
SELECT c.id, o.id
FROM customers c
LEFT JOIN orders o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

The `WHERE` predicate removes rows where `o` is `NULL`, effectively behaving like an inner join for this condition.

If the requirement is to preserve customers without paid orders:

```sql
SELECT c.id, o.id
FROM customers c
LEFT JOIN orders o
    ON o.customer_id = c.id
   AND o.status = 'paid';
```

This is a frequent SQL troubleshooting and interview question.

---

## Scenario: `NOT IN` Returns Unexpected Results

Consider:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM blocked_customers
);
```

If the subquery can contain `NULL`, SQL's three-valued logic can produce surprising results.

When the requirement is existence-based, prefer a semantically explicit form:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_customers b
    WHERE b.customer_id = customers.id
);
```

Understand the semantics rather than applying a mechanical rewrite.

---

## Scenario: Production Database Storage Is Filling Up

Determine what is growing:

```text
table data
indexes
WAL
temporary files
dead tuples
logs
backups
```

Inspect large relations:

```sql
SELECT
    relname,
    pg_size_pretty(
        pg_total_relation_size(relid)
    ) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC
LIMIT 20;
```

Potential remedies include:

- Retention
- Partition lifecycle
- Archival
- Index cleanup
- Vacuum maintenance
- Storage expansion

Do not delete data simply to clear an alert without checking retention, compliance, and recovery requirements.

---

## Scenario: Database Storage Is Full During a Migration

A migration may temporarily require substantial additional space for:

```text
new indexes
table rewrites
WAL
temporary files
backups
shadow tables
```

Before execution, estimate:

```text
current data size
+
index size
+
expected WAL
+
temporary space
+
replication overhead
```

Storage capacity is part of migration planning.

---

## Scenario: A Query Causes Temporary File Growth

Possible causes:

- Large sorts
- Hash operations
- Aggregations
- Insufficient available memory
- Large analytical queries

Investigate the execution plan and temporary I/O.

Do not simply increase memory without considering concurrent workload.

---

## Scenario: Query Plan Changes After an Index Is Added

Adding an index can change unrelated query plans because the optimizer now has a new access path.

Possible consequences:

```text
improvement
regression
different join order
different scan
different memory behavior
```

Always validate representative queries after significant index changes.

Index deployment is therefore a workload change, not merely a schema change.

---

## Scenario: Query Performance Regresses After Deployment

Compare:

```text
before deployment
vs
after deployment
```

Check:

```text
SQL changes
query frequency
parameters
indexes
statistics
connection pools
transaction duration
worker concurrency
feature flags
```

Useful sources include:

```text
pg_stat_statements
application metrics
distributed traces
execution plans
database infrastructure metrics
```

Correlating application and database telemetry is often the fastest way to identify the change.

---

## Scenario: A Query Is Executed Thousands of Times Per Request

This usually indicates an N+1 or repeated lookup pattern.

Measure:

```text
queries/request
database time/request
rows/request
```

A query taking 2 ms is still a serious problem if it runs 1,000 times.

Optimize the request-level workload rather than focusing only on individual query latency.

---

## Scenario: Database Is Saturated by a Reporting Query

### Situation

An analyst runs a large aggregation on the transactional database.

### Better Architecture

```text
OLTP PostgreSQL
       ↓
CDC / ETL / events
       ↓
OLAP / warehouse
```

Intermediate solutions can include:

```text
read replica
materialized views
reporting database
```

But a reporting replica can still compete for resources and may suffer replication/replay interactions.

Separate analytical workloads when their scale justifies it.

---

## Scenario: Query Needs to Run Every Minute

### Question

Would you optimize the query or cache the result?

First determine:

```text
freshness requirement
query cost
query frequency
number of consumers
data change rate
```

Potential solutions:

```text
optimized query
+
appropriate index
+
materialized view
+
cache
+
precomputed read model
```

Caching is not automatically better than making the query efficient.

---

## Scenario: Database Failure Occurs During a Transaction

### Question

Should the application retry?

Determine whether the outcome is known.

If the connection fails before execution, retrying may be straightforward.

If the failure occurs around commit:

```text
database may have committed
but
client does not know
```

Use:

```text
idempotency
operation IDs
unique constraints
reconciliation
```

This is especially important for:

```text
payments
orders
inventory
external side effects
```

---

## Scenario: Deadlock or Serialization Failure Is Retried

A retry should normally encompass the entire transaction:

```text
BEGIN
 ↓
all reads/writes
 ↓
COMMIT
```

not:

```text
failed statement
 ↓
continue same transaction
```

Use:

```text
bounded retries
+
backoff
+
jitter
+
idempotency
```

Avoid infinite retry loops.

---

## Scenario: Query Troubleshooting in Django

A senior Django engineer should inspect generated SQL rather than assuming ORM behavior.

Useful techniques include:

```python
queryset = (
    Order.objects
    .filter(customer_id=customer_id)
    .select_related("customer")
)

print(queryset.query)
```

For production diagnosis, combine ORM-level metrics with PostgreSQL-level evidence.

Look for:

```text
N+1
unbounded querysets
unnecessary columns
missing indexes
implicit joins
long transactions
```

Django ORM abstraction does not remove the need to understand SQL.

---

## Scenario: Query Troubleshooting in SQLAlchemy

For SQLAlchemy applications, inspect:

```text
generated SQL
bound parameters
session lifecycle
transaction boundaries
connection pool metrics
```

Also verify that database sessions are returned to the pool promptly.

A slow endpoint can result from:

```text
pool acquisition
```

rather than SQL execution itself.

---

## Scenario: SQL Troubleshooting in Kubernetes

When the application runs across many pods, always reason about aggregate behavior.

For example:

```text
50 pods
×
10 DB connections
=
500 potential connections
```

Then add:

```text
Celery
migrations
cron jobs
admin tools
other services
```

Kubernetes scaling can therefore unintentionally scale database concurrency.

Horizontal application scaling is not equivalent to horizontal database scaling.

---

## Scenario: SQL Troubleshooting in AWS

For managed PostgreSQL such as Amazon RDS or Aurora, correlate database-level evidence with infrastructure metrics.

Investigate:

```text
CPU
memory pressure
storage latency
IOPS
throughput
connections
replica lag
storage growth
```

The database query plan and infrastructure metrics should tell the same story.

For example:

```text
high query latency
+
high storage latency
```

suggests a different problem from:

```text
high query latency
+
lock waits
+
low CPU
```

---

## Scenario: Production Query Needs Immediate Mitigation

During an incident, separate:

```text
mitigation
```

from:

```text
root-cause fix
```

Possible mitigations:

- Disable an expensive feature.
- Reduce background-worker concurrency.
- Stop a runaway batch.
- Route appropriate reads away from an overloaded primary.
- Cancel clearly runaway queries.
- Temporarily increase capacity where justified.
- Roll back a problematic deployment.

Do not make emergency changes that compromise:

```text
data integrity
security
recovery
```

---

## Scenario: How Do You Verify a SQL Optimization?

Never stop at:

> "The query looks better."

Measure before and after:

```text
execution time
planning time
buffer reads
buffer hits
rows processed
CPU
I/O
query frequency
p95/p99
database load
```

Use representative data and realistic concurrency.

A query that improves from:

```text
100 ms → 50 ms
```

may be less valuable than reducing:

```text
1,000,000 calls → 100,000 calls
```

Optimization should consider total workload impact.

---

## Scenario: How Do You Prevent SQL Performance Regressions?

Build feedback loops:

```text
application metrics
+
query statistics
+
execution-plan analysis
+
slow-query logging
+
index reviews
+
load testing
+
migration testing
```

Track important queries over time.

For high-value endpoints, performance should be treated as an operational contract rather than something investigated only after an incident.

---

## Troubleshooting Decision Matrix

| Symptom | First Investigation |
|---|---|
| High query latency | Execution plan + waits |
| Sequential scan | Selectivity + plan |
| Index ignored | Statistics + access pattern |
| Wrong row count | Join cardinality |
| Zero rows | Filters + visibility + replica |
| High CPU | Query workload + frequency |
| High memory | `work_mem` + concurrency |
| Pool exhausted | Pool wait + query/transaction duration |
| Lock wait | Blocker + transaction age |
| Deadlock | Lock ordering |
| Replica lag | WAL generation + replay |
| Storage growth | Tables/indexes/WAL/bloat |
| N+1 | Queries per request |
| Large export | Async/batch architecture |
| Slow pagination | OFFSET vs keyset |
| Migration slowdown | Locks/WAL/I/O |
| Retry storm | Backoff + idempotency |
| Aggregation slow | Cardinality + workload isolation |
| API slow but SQL fast | Application/request path |

---

## Common Troubleshooting Mistakes

### Adding an Index Without Measuring

Why it fails:

```text
index may not match query
```

or:

```text
problem may be a lock
```

### Looking Only at Average Latency

Averages can hide p95/p99 problems.

Production systems must consider tail latency.

### Ignoring Query Frequency

A cheap query executed millions of times can dominate database resources.

### Increasing `work_mem` Globally

Memory consumption multiplies with operations and concurrency.

### Increasing Connection Pool Size Automatically

More connections can increase contention and memory pressure.

### Blaming the Database for N+1

The database executes the workload it receives.

### Using `DISTINCT` to Hide Join Problems

This can mask incorrect cardinality.

### Treating Replicas as Strongly Consistent

Asynchronous replication can lag.

### Running Large Data Changes in One Transaction

This can create WAL, bloat, lock, and replication problems.

### Retrying Permanent Errors

Unique violations and validation errors usually need correction, not retries.

### Retrying Without Idempotency

A retry can duplicate a successful operation whose response was lost.

### Debugging Only the Query

The real bottleneck may be:

```text
pool
lock
application
network
serialization
external service
```

### Optimizing Without a Baseline

Without measurements, you cannot prove improvement or regression.

---

## Senior-Level Troubleshooting Checklist

When asked to troubleshoot a SQL problem, cover:

### Correctness

- [ ] Result grain is correct.
- [ ] Join cardinality is understood.
- [ ] `NULL` semantics are correct.
- [ ] Tenant isolation is enforced.
- [ ] Constraints protect important invariants.
- [ ] Transaction semantics are correct.

### Query Performance

- [ ] Exact SQL is known.
- [ ] Parameters are known.
- [ ] Query frequency is known.
- [ ] `EXPLAIN` has been inspected.
- [ ] Estimated vs actual rows are compared.
- [ ] Indexes match access patterns.
- [ ] Sort/hash/aggregate behavior is understood.

### Database Resources

- [ ] CPU is checked.
- [ ] Memory pressure is checked.
- [ ] I/O is checked.
- [ ] Connections are checked.
- [ ] Lock waits are checked.
- [ ] Long transactions are checked.
- [ ] Autovacuum is checked.

### Application

- [ ] N+1 is ruled out.
- [ ] Connection-pool wait is measured.
- [ ] Transaction boundaries are reviewed.
- [ ] Background-worker concurrency is checked.
- [ ] Retry behavior is checked.
- [ ] Result serialization is checked.

### Distributed Architecture

- [ ] Replica lag is checked.
- [ ] Read-after-write requirements are understood.
- [ ] Redis behavior is understood.
- [ ] Kafka/Celery workloads are considered.
- [ ] External calls inside transactions are ruled out.

### Operations

- [ ] Recent deployments are correlated.
- [ ] Recent migrations are correlated.
- [ ] Monitoring exists.
- [ ] Mitigation is defined.
- [ ] Root cause is validated.
- [ ] Regression monitoring is added.

---

## Key Takeaways

- **SQL troubleshooting starts with measurement, not assumptions:** identify the exact query, workload, execution plan, waits, resource usage, and application path before changing indexes or configuration.
- **Separate execution problems from waiting problems:** sequential scans, bad joins, and poor cardinality estimates require different fixes from lock contention, connection-pool exhaustion, and replica lag.
- **Optimize workload impact, not just individual query latency:** query frequency, N+1 behavior, concurrency, result size, and background workers can matter more than the latency of one execution.
- **Production troubleshooting includes the entire system:** PostgreSQL, Django/FastAPI, connection pools, Redis, Kafka, Celery, Kubernetes, replicas, migrations, and infrastructure capacity all influence SQL behavior.
- **Senior troubleshooting includes prevention:** after fixing the immediate issue, add appropriate constraints, indexes, observability, timeouts, retry controls, migration safeguards, capacity limits, and regression detection.