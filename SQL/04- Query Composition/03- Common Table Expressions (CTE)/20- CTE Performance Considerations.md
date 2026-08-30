# 20- CTE Performance Considerations

## Overview

A Common Table Expression (CTE) is primarily a **query-composition mechanism**, not a performance feature by itself. It allows a complex SQL statement to be divided into named intermediate relations, but whether those relations are inlined, materialized, rescanned, or otherwise optimized depends on the database engine, version, query shape, and execution plan.

For production systems, the correct question is not:

> "Are CTEs fast or slow?"

The useful question is:

> "What execution strategy does this CTE produce for this workload, and is that strategy appropriate?"

A CTE can improve performance by reducing repeated work, improving query structure, or enabling efficient staged processing. It can also hurt performance when materialization prevents useful predicate pushdown, when an intermediate result becomes very large, or when the query creates unnecessary sorts, joins, scans, or memory pressure.

The optimization workflow should therefore be:

```text
SQL intent
   │
   ▼
CTE structure
   │
   ▼
Optimizer transformations
   │
   ▼
Execution plan
   │
   ▼
CPU / Memory / I/O
   │
   ▼
Application latency
```

## Why CTE Performance Requires Care

A CTE exists at the SQL level, while performance is determined by the physical execution plan.

Consider:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue >= 10000;
```

The database does not necessarily execute this as:

1. Run the CTE.
2. Store all CTE rows.
3. Scan the stored result.
4. Apply the outer filter.

The optimizer may transform the query substantially.

Depending on the database and query, the intermediate relation might be:

- Inlined into the surrounding query.
- Materialized into an intermediate structure.
- Computed once and reused.
- Recomputed for separate references.
- Optimized together with surrounding joins and predicates.

Therefore, SQL structure and physical execution should be treated as related but distinct concerns.

## CTE Materialization

**Materialization** means the database evaluates a CTE and stores its intermediate result for later consumption rather than fully integrating the CTE into the surrounding query plan.

The benefits and costs are workload-dependent.

### Potential Advantages

Materialization can be useful when:

- The CTE is expensive to compute.
- Multiple consumers need the same result.
- Recomputing the intermediate result would be more expensive.
- You intentionally want to isolate an expensive computation from repeated evaluation.

Example:

```sql
WITH expensive_customer_metrics AS MATERIALIZED (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    high_value.customer_id,
    high_value.revenue,
    high_value.order_count
FROM expensive_customer_metrics AS high_value
JOIN expensive_customer_metrics AS active_metrics
    ON active_metrics.customer_id = high_value.customer_id
WHERE high_value.revenue >= 50000;
```

Whether materialization is actually beneficial must be verified with the execution plan.

### Potential Costs

Materialization can introduce:

- Additional memory usage.
- Temporary disk I/O.
- Additional copying of intermediate rows.
- Loss of predicate pushdown opportunities.
- Larger intermediate datasets than necessary.
- Additional latency before downstream operations can proceed.

Materializing a huge intermediate result merely because a query is complex is usually a poor optimization strategy.

## PostgreSQL CTE Optimization

PostgreSQL provides explicit `MATERIALIZED` and `NOT MATERIALIZED` options for CTEs.

### `MATERIALIZED`

```sql
WITH customer_metrics AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_metrics
WHERE revenue >= 10000;
```

This explicitly requests materialization.

It can be useful when the intermediate result is expensive and reused, or when isolating the CTE from surrounding optimization is intentional.

### `NOT MATERIALIZED`

```sql
WITH customer_metrics AS NOT MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_metrics
WHERE revenue >= 10000;
```

This requests that the CTE be treated as an inlineable query expression where possible.

The potential advantage is preserving optimizer opportunities such as:

- Predicate pushdown.
- Join reordering.
- More efficient index usage.
- Elimination of unnecessary intermediate work.

Do not use either option mechanically. Use execution-plan evidence.

## Predicate Pushdown

One important performance consideration is whether filtering can happen close to the base table.

Consider:

```sql
WITH customer_orders AS (
    SELECT
        customer_id,
        order_id,
        total_amount
    FROM orders
)
SELECT
    customer_id,
    SUM(total_amount)
FROM customer_orders
WHERE customer_id = 42
GROUP BY customer_id;
```

An optimizer may be able to recognize that only rows for `customer_id = 42` are needed.

A forced materialization changes the optimization problem:

```sql
WITH customer_orders AS MATERIALIZED (
    SELECT
        customer_id,
        order_id,
        total_amount
    FROM orders
)
SELECT
    customer_id,
    SUM(total_amount)
FROM customer_orders
WHERE customer_id = 42
GROUP BY customer_id;
```

Now the database may need to construct the complete intermediate result before applying the outer filter.

For a large `orders` table, that can be substantially more expensive.

### Practical Rule

Prefer query structures that allow the optimizer to eliminate unnecessary rows early.

```text
Base table
    │
    ▼
Selective predicate
    │
    ▼
Smaller intermediate relation
    │
    ▼
Join / aggregation / sorting
```

Reducing rows early generally reduces downstream CPU, memory, and I/O.

## Intermediate Result Size

CTE performance is often dominated by the size of intermediate relations rather than the number of CTEs.

Consider:

```sql
WITH customer_orders AS (
    SELECT
        customer_id,
        order_id,
        total_amount
    FROM orders
)
SELECT
    c.id,
    COUNT(co.order_id)
FROM customers AS c
LEFT JOIN customer_orders AS co
    ON co.customer_id = c.id
GROUP BY c.id;
```

If `customer_orders` contains hundreds of millions of rows, downstream joins and aggregation can become expensive.

If the application only needs completed orders from the last 30 days, push those restrictions into the CTE:

```sql
WITH recent_completed_orders AS (
    SELECT
        customer_id,
        order_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT
    c.id,
    COUNT(rco.order_id)
FROM customers AS c
LEFT JOIN recent_completed_orders AS rco
    ON rco.customer_id = c.id
GROUP BY c.id;
```

The exact plan still needs verification, but reducing the logical working set is usually preferable.

## CTEs and Aggregation Cost

Aggregation can produce large intermediate results if the grouping cardinality is high.

```sql
WITH customer_daily_sales AS (
    SELECT
        customer_id,
        DATE_TRUNC('day', created_at) AS day,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY
        customer_id,
        DATE_TRUNC('day', created_at)
)
SELECT
    day,
    SUM(revenue) AS revenue
FROM customer_daily_sales
GROUP BY day;
```

The first aggregation may produce millions of customer-day rows.

The second aggregation then processes that intermediate relation.

This can still be the right architecture, but production review should consider:

- Number of input rows.
- Number of groups.
- Memory available for aggregation.
- Whether hashing or sorting is used.
- Temporary disk usage.
- Whether filtering can reduce input cardinality.
- Whether a pre-aggregated table or materialized view is more appropriate.

## CTEs and Window Functions

Window functions often require sorting or partitioning.

```sql
WITH ranked_orders AS (
    SELECT
        id,
        customer_id,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC
        ) AS row_number
    FROM orders
)
SELECT
    id,
    customer_id,
    total_amount
FROM ranked_orders
WHERE row_number <= 3;
```

The CTE makes it possible to filter on the computed window value in the outer query.

Performance depends heavily on:

- Input row count.
- Partition cardinality.
- Ordering requirements.
- Available indexes.
- Memory available for sorting.
- Whether the database can avoid or reduce sorting work.

For a high-volume table, inspect the plan rather than assuming the CTE itself is the problem.

## CTEs and JOIN Performance

CTEs frequently serve as pre-filtered or pre-aggregated inputs to joins.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    cr.revenue
FROM customers AS c
JOIN customer_revenue AS cr
    ON cr.customer_id = c.id
WHERE cr.revenue >= 10000;
```

Performance depends on the resulting relation and join strategy.

The database may choose:

- Nested loop joins.
- Hash joins.
- Merge joins.

The appropriate strategy depends on cardinality, indexes, statistics, and available resources.

A CTE does not force a particular join algorithm merely because it appears before the main query.

## Indexing and CTEs

Indexes are defined on base tables, not on ordinary query-local CTEs.

Suppose:

```sql
WITH recent_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
)
SELECT *
FROM recent_orders
WHERE customer_id = 42;
```

Potentially useful base-table indexes might involve:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

or, depending on workload and selectivity:

```sql
CREATE INDEX idx_orders_completed_customer_created
ON orders (customer_id, created_at)
WHERE status = 'completed';
```

The correct index depends on actual query patterns and data distribution.

Do not create indexes simply because a column appears inside a CTE.

## CTEs and Execution Plans

Use `EXPLAIN` and `EXPLAIN ANALYZE` to understand actual behavior.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue >= 10000;
```

Important information includes:

| Plan Signal | What It Helps Diagnose |
|---|---|
| Actual rows | Cardinality assumptions |
| Estimated rows | Statistics/estimation quality |
| Execution time | Runtime cost |
| Buffers | Memory/cache and I/O behavior |
| Sequential scan | Large or unselective scans |
| Index scan | Index-driven access |
| Hash aggregate | Hash-based aggregation |
| Sort | Ordering/window/merge requirements |
| Temporary I/O | Intermediate data exceeding memory |
| Nested loop | Potential repeated inner work |
| Hash join | Large relation joins |
| Materialize | Reuse/caching of intermediate results |

A production optimization should be based on measurable evidence.

## Estimated Rows vs Actual Rows

One of the most important senior-level performance signals is cardinality estimation.

Suppose the plan expects:

```text
rows=1000
```

but actually processes:

```text
actual rows=10000000
```

That mismatch can cause the optimizer to choose a poor strategy.

The root cause may be:

- Stale statistics.
- Data skew.
- Correlated columns.
- Complex predicates.
- Expressions that are difficult to estimate.
- Rapidly changing data.

Do not automatically blame the CTE.

A CTE may simply make an existing cardinality problem visible in a more complex query.

## Avoiding Unnecessary CTE Layers

A query can become slower to reason about without becoming slower to execute.

Avoid:

```sql
WITH a AS (
    SELECT *
    FROM orders
),
b AS (
    SELECT *
    FROM a
),
c AS (
    SELECT *
    FROM b
)
SELECT *
FROM c;
```

This adds no meaningful relational transformation.

Prefer:

```sql
SELECT *
FROM orders;
```

CTEs should communicate meaningful transformations such as:

```sql
WITH recent_completed_orders AS (...),
customer_revenue AS (...),
top_customers AS (...)
SELECT ...
FROM top_customers;
```

The goal is not to minimize the number of CTEs. The goal is to minimize unnecessary work while preserving understandable query structure.

## CTE Reuse and Repeated Computation

Consider:

```sql
WITH customer_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT ...
FROM customer_metrics AS a
JOIN customer_metrics AS b
    ON a.customer_id = b.customer_id;
```

A common assumption is:

> "The CTE runs once because it is written once."

That is not a reliable general rule.

The optimizer decides how the query is executed. Depending on the database, version, and query, the CTE may be materialized, inlined, or otherwise transformed.

When repeated expensive computation matters, inspect the plan.

## When Materialization Can Help

Materialization can be beneficial when an intermediate result is:

- Expensive to calculate.
- Relatively small after filtering/aggregation.
- Referenced multiple times.
- Stable during the statement.
- Cheaper to store temporarily than recompute.

Example:

```sql
WITH customer_metrics AS MATERIALIZED (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    ...
FROM customer_metrics AS cm1
JOIN customer_metrics AS cm2
    ON cm1.customer_id = cm2.customer_id;
```

This is a candidate for testing because the expensive aggregation may otherwise be repeated.

The important question is not whether materialization sounds efficient, but whether it reduces total work for the actual query.

## When Materialization Can Hurt

Avoid forcing materialization when:

- The CTE produces a very large result.
- Only a small subset is needed later.
- Outer predicates could otherwise be pushed down.
- The CTE is referenced only once.
- The surrounding query has opportunities for join or predicate optimization.

Example:

```sql
WITH orders_snapshot AS MATERIALIZED (
    SELECT *
    FROM orders
)
SELECT *
FROM orders_snapshot
WHERE customer_id = 42;
```

This is generally suspicious for a large table because it may force a large intermediate result before applying the selective filter.

A better query is usually:

```sql
SELECT *
FROM orders
WHERE customer_id = 42;
```

or, when an intermediate stage genuinely provides value:

```sql
WITH customer_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE customer_id = 42
)
SELECT *
FROM customer_orders;
```

## Memory and Temporary Disk Usage

Large intermediate results can consume substantial memory.

Operations commonly associated with memory pressure include:

- Hash aggregation.
- Hash joins.
- Sorts.
- Window functions.
- Materialized intermediate results.

When memory is insufficient, databases may spill work to temporary storage.

This can cause:

- Increased latency.
- Higher disk I/O.
- Increased database load.
- Query concurrency degradation.

A query that runs acceptably in development with thousands of rows may behave very differently with production-scale data.

## Query Concurrency

Performance should be evaluated at the workload level, not only by single-query latency.

A query that takes 200 ms in isolation may become problematic if:

- Hundreds of requests execute it concurrently.
- It consumes significant memory per connection.
- It performs large scans.
- It spills to disk.
- It holds database connections for long periods.

For backend services:

```text
API Requests
     │
     ▼
Connection Pool
     │
     ▼
Database
 ┌───┴───────────┐
 │ Query A       │
 │ Query B       │
 │ Query C       │
 │ ...           │
 └───────────────┘
```

A query optimization should therefore consider:

- p50 latency.
- p95/p99 latency.
- Queries per second.
- Connection utilization.
- CPU utilization.
- Memory utilization.
- Disk I/O.
- Lock contention.

## CTEs in API Workloads

Suppose a FastAPI endpoint retrieves a customer's dashboard:

```text
GET /customers/{id}/dashboard
            │
            ▼
        FastAPI
            │
            ▼
      Service Layer
            │
            ▼
        Repository
            │
            ▼
       PostgreSQL
            │
            ▼
   CTE-based SQL query
            │
            ▼
     Dashboard rows
```

A CTE can make the query easier to maintain:

```sql
WITH customer_orders AS (
    SELECT
        id,
        total_amount,
        created_at
    FROM orders
    WHERE customer_id = $1
      AND status = 'completed'
),
order_metrics AS (
    SELECT
        COUNT(*) AS order_count,
        COALESCE(SUM(total_amount), 0) AS revenue
    FROM customer_orders
)
SELECT
    order_count,
    revenue
FROM order_metrics;
```

For a request-specific query, the most important optimization is often filtering by the request's selective key as early as possible.

Do not fetch an entire customer population and filter it in application code.

## CTEs in Django

Django applications may use the ORM for ordinary query composition and raw SQL or third-party query tooling when advanced CTE functionality is required.

The performance principles remain the same:

- Inspect generated SQL.
- Measure database execution time.
- Avoid N+1 queries.
- Filter at the database.
- Use appropriate indexes.
- Inspect execution plans for expensive queries.

For example, even if a query originates from ORM code:

```python
customers = (
    Customer.objects
    .filter(status="active")
    .select_related("account")
)
```

the database remains responsible for executing the resulting SQL.

A CTE is not automatically preferable merely because the query is complex.

## CTEs in Background Jobs

Long-running Celery jobs can make large CTE queries especially important.

For example:

```text
Celery Worker
     │
     ▼
Large reporting query
     │
     ▼
PostgreSQL
     │
     ├── CPU
     ├── Memory
     ├── I/O
     └── Temporary storage
```

A poorly optimized analytical CTE can consume database resources and affect interactive API traffic.

For expensive reporting workloads:

- Schedule them during appropriate periods.
- Limit batch sizes where possible.
- Consider replicas for read-heavy workloads.
- Consider materialized views or precomputed tables.
- Avoid running unbounded analytical queries from request paths.
- Monitor query duration and database resource consumption.

## CTEs and Read Replicas

Read-only CTE queries can potentially run against a read replica when the application's consistency requirements allow it.

However, moving a query to a replica does not make the query intrinsically efficient.

Consider:

```text
Application
    │
    ├── OLTP API queries ───────► Primary
    │
    └── Reporting queries ──────► Read Replica
                                      │
                                      ▼
                                  CTE query
```

A complex CTE can still overload the replica.

Also account for:

- Replication lag.
- Read-after-write requirements.
- Replica capacity.
- Failover behavior.
- Query routing.

## When a CTE Is Not the Right Optimization

Sometimes the correct solution is to change the data architecture rather than optimize the CTE.

Consider alternatives when the query repeatedly performs expensive transformations:

| Requirement | Potential Alternative |
|---|---|
| Reusable logical abstraction | View |
| Persisted precomputed result | Materialized view |
| Large intermediate state across statements | Temporary table |
| Frequently queried aggregate | Summary table |
| Search-oriented workload | Specialized search/indexing system |
| Analytics at large scale | Analytical warehouse |
| Repeated application-level caching | Redis |
| Event-driven derived state | Kafka + consumer-maintained projection |

A CTE is query-local. If the same expensive transformation is required across many independent requests, repeatedly computing it may be the wrong architecture.

## Production Performance Checklist

Before deploying a complex CTE query, verify:

### Query Shape

- Is each CTE necessary?
- Does each CTE represent a meaningful transformation?
- Are filters applied as early as practical?
- Are joins occurring at appropriate stages?
- Are large intermediate relations unavoidable?

### Execution Plan

- Have you inspected `EXPLAIN`?
- Have you tested with production-like data volume?
- Are estimated and actual row counts reasonable?
- Are there unexpected sequential scans?
- Are there expensive sorts or hash operations?
- Is temporary disk I/O occurring?

### Indexes

- Are selective predicates supported by appropriate indexes?
- Are join keys indexed where beneficial?
- Are composite indexes aligned with actual access patterns?
- Would a partial index help?

### Resource Usage

- CPU usage acceptable?
- Memory usage acceptable?
- Temporary storage acceptable?
- Database connection time acceptable?
- Query concurrency acceptable?

### Application Impact

- Does the query fit the API latency budget?
- Does it increase p95/p99 latency?
- Could it block or starve interactive workloads?
- Should it run asynchronously?
- Should it execute against a read replica?

## Common Performance Mistakes

| Mistake | Why It Happens | Better Approach |
|---|---|---|
| Assuming CTEs are inherently slow | Confusing syntax with execution strategy | Inspect the actual plan |
| Assuming CTEs are inherently fast | Treating abstraction as optimization | Measure workload behavior |
| Forcing `MATERIALIZED` everywhere | Assuming one evaluation is always better | Use only when measured behavior supports it |
| Materializing huge relations | Ignoring intermediate result size | Filter and aggregate early |
| Ignoring predicate pushdown | Thinking in terms of query text only | Check optimizer behavior |
| Creating many unnecessary CTEs | Overusing query abstraction | Keep only meaningful stages |
| Assuming repeated CTE references run once | Confusing logical reuse with physical execution | Inspect the execution plan |
| Optimizing without production-scale data | Development data is too small | Benchmark realistic cardinalities |
| Adding indexes blindly | Treating indexes as universal fixes | Analyze predicates, joins, and plans |
| Ignoring concurrency | Testing only one query at a time | Measure under realistic load |
| Running heavy CTEs in request paths | Treating analytical SQL as OLTP | Use async jobs or precomputed data where appropriate |
| Moving expensive queries to replicas without limits | Assuming replicas solve query cost | Capacity-plan replicas and optimize SQL |

## Security Considerations

CTEs do not provide security isolation.

User-controlled values must still be parameterized:

```sql
WITH customer_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE customer_id = $1
)
SELECT *
FROM customer_orders;
```

Do not interpolate request values into SQL:

```python
# Avoid
query = f"""
WITH customer_orders AS (
    SELECT *
    FROM orders
    WHERE customer_id = {customer_id}
)
SELECT *
FROM customer_orders
"""
```

Use parameterized database APIs or ORM mechanisms.

Performance optimization must also respect authorization boundaries. Do not remove security predicates merely because doing so produces a faster execution plan.

## Monitoring and Observability

Complex database queries should be observable as part of the backend service.

Track:

- Query latency.
- Query frequency.
- p95/p99 latency.
- Rows returned.
- Database CPU.
- Database memory.
- Disk I/O.
- Connection-pool utilization.
- Slow-query counts.
- Temporary file usage where available.
- Lock and wait behavior.

For an API endpoint, correlate:

```text
API latency
    │
    ├── Application processing
    ├── Database connection acquisition
    ├── SQL execution
    ├── Network transfer
    └── Response serialization
```

This prevents blaming the CTE when the actual bottleneck is elsewhere.

## Benchmarking Strategy

A useful production-oriented workflow is:

1. Establish a baseline.
2. Capture the current execution plan.
3. Identify the dominant cost.
4. Change one query characteristic.
5. Re-run the plan.
6. Compare actual runtime and resource usage.
7. Test with representative data volume.
8. Test under realistic concurrency.
9. Validate correctness.
10. Deploy and monitor.

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue
FROM customer_revenue
WHERE revenue >= 10000;
```

Do not optimize based only on estimated cost numbers. Actual execution behavior is more useful when validating a concrete production problem.

## Senior-Level Performance Model

Think about CTE performance across four layers:

| Layer | Key Question |
|---|---|
| Logical SQL | Is the query expressing the required transformation efficiently? |
| Optimizer | Can the database transform the query effectively? |
| Physical execution | What scans, joins, sorts, aggregations, and materialization occur? |
| Workload | How does the query behave under real data volume and concurrency? |

This prevents a common optimization mistake: changing SQL syntax without understanding the workload.

A senior engineer should be able to move between all four layers.

## Key Takeaways

- **CTEs are primarily a query-composition feature; their performance depends on the optimizer, execution plan, database version, and workload.**
- **Large intermediate relations, unnecessary materialization, blocked predicate pushdown, and expensive joins or sorts are more important performance concerns than the mere presence of a CTE.**
- **Use `EXPLAIN`/`EXPLAIN ANALYZE` with production-like data to validate CTE performance instead of relying on rules such as "CTEs are slow."**
- **Materialization can reduce repeated expensive computation but can also increase memory, temporary I/O, and downstream work; use it deliberately and measure the result.**
- **For recurring expensive transformations, consider architectural alternatives such as materialized views, summary tables, temporary tables, replicas, or asynchronous processing rather than endlessly optimizing a request-time CTE.**