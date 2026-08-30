# 12- Aggregation Execution Logic

## Overview

SQL aggregation transforms multiple input rows into summarized results. Functions such as `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX` operate over a set of rows, while `GROUP BY` determines whether those rows are summarized into one result or multiple groups.

Understanding aggregation execution is important because the SQL query you write is a **logical description**, not necessarily the physical sequence the database executes. A senior backend engineer should be able to reason about both:

- **Logical query processing** — what the SQL means.
- **Physical execution** — how the database actually produces the result.

This distinction becomes important when debugging incorrect counts, understanding `NULL`, diagnosing slow reporting queries, choosing indexes, and interpreting `EXPLAIN` plans.

## Logical Aggregation Model

Consider:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

A useful logical model is:

```text
FROM orders
      │
      ▼
WHERE status = 'paid'
      │
      ▼
Filtered rows
      │
      ▼
GROUP BY customer_id
      │
      ▼
One logical group per customer
      │
      ├── COUNT(*)
      └── SUM(total_amount)
      │
      ▼
HAVING COUNT(*) >= 10
      │
      ▼
Final grouped result
```

The logical stages are approximately:

```text
FROM / JOIN
    ↓
WHERE
    ↓
GROUP BY
    ↓
Aggregate computation
    ↓
HAVING
    ↓
SELECT
    ↓
ORDER BY
    ↓
LIMIT
```

This is a semantic model. PostgreSQL, MySQL, SQL Server, and other database engines may use very different physical execution strategies while producing the same logical result.

## Aggregation Without GROUP BY

An aggregate query without `GROUP BY` produces one aggregate result over the qualifying input rows.

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order
FROM orders
WHERE status = 'paid';
```

Conceptually:

```text
All qualifying rows
        │
        ▼
   One group
        │
        ├── COUNT(*)
        ├── SUM(...)
        └── AVG(...)
        │
        ▼
    One result row
```

For example:

| order_count | revenue | average_order |
|---:|---:|---:|
| 50000 | 12500000 | 250 |

The result is one row even though the source table may contain millions of rows.

This pattern is common for:

- Dashboard totals
- Health metrics
- Billing calculations
- Reporting APIs
- Batch processing
- Monitoring queries

## Aggregation With GROUP BY

`GROUP BY` changes the aggregation grain.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id;
```

Instead of one global group, the database creates a logical group for every distinct `customer_id`.

```text
orders
  │
  ├── customer_id = 101 ──► group 101 ──► COUNT
  ├── customer_id = 102 ──► group 102 ──► COUNT
  ├── customer_id = 101 ──► group 101
  └── customer_id = 103 ──► group 103 ──► COUNT
```

The conceptual input:

| customer_id | order_id |
|---:|---:|
| 101 | 1 |
| 102 | 2 |
| 101 | 3 |
| 103 | 4 |
| 101 | 5 |

becomes:

| customer_id | rows in group | `COUNT(*)` |
|---:|---:|---:|
| 101 | 3 | 3 |
| 102 | 1 | 1 |
| 103 | 1 | 1 |

The most important design question is therefore:

> **What is the grain of the result?**

If the desired result is one row per customer, `GROUP BY customer_id` must produce exactly that grain.

## How Aggregate Functions Process Groups

Each aggregate maintains or derives a value from the rows belonging to a group.

| Function | Conceptual operation |
|---|---|
| `COUNT(*)` | Count every input row |
| `COUNT(column)` | Count non-NULL values |
| `SUM(column)` | Add non-NULL values |
| `AVG(column)` | Sum non-NULL values / count of non-NULL values |
| `MIN(column)` | Find the minimum non-NULL value |
| `MAX(column)` | Find the maximum non-NULL value |

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS orders,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order
FROM orders
GROUP BY customer_id;
```

Conceptually, each customer group maintains aggregation state:

```text
Customer 101
├── row 1 → count=1, sum=100
├── row 2 → count=2, sum=250
└── row 3 → count=3, sum=450

Final state:
count = 3
sum   = 450
avg   = 150
```

Actual database implementations can use optimized internal representations and specialized aggregate algorithms.

## Aggregation and NULL

`NULL` is not treated as an ordinary value by most standard aggregate functions.

Consider:

| customer_id | total_amount |
|---:|---:|
| 101 | 100 |
| 101 | NULL |
| 101 | 200 |

Then:

```sql
SELECT
    COUNT(*) AS rows,
    COUNT(total_amount) AS non_null_amounts,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_amount
FROM orders
WHERE customer_id = 101;
```

Conceptually:

| Expression | Result |
|---|---:|
| `COUNT(*)` | 3 |
| `COUNT(total_amount)` | 2 |
| `SUM(total_amount)` | 300 |
| `AVG(total_amount)` | 150 |

`AVG()` does not divide by all rows. It averages the non-NULL input values.

This distinction is critical in financial and analytics systems because:

```text
NULL
```

can mean "unknown/not recorded", whereas:

```text
0
```

means an explicitly recorded zero.

Replacing one with the other changes business semantics.

## Empty Input and NULL

Aggregate functions behave differently when there are no input rows.

For example:

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order,
    MIN(total_amount) AS minimum_order,
    MAX(total_amount) AS maximum_order
FROM orders
WHERE customer_id = -1;
```

A typical result is:

| order_count | revenue | average_order | minimum_order | maximum_order |
|---:|---:|---:|---:|---:|
| 0 | NULL | NULL | NULL | NULL |

This is an important API consideration.

If an API contract requires:

```json
{
  "order_count": 0,
  "revenue": 0
}
```

you may explicitly normalize values:

```sql
SELECT
    COUNT(*) AS order_count,
    COALESCE(SUM(total_amount), 0) AS revenue
FROM orders
WHERE customer_id = :customer_id;
```

Do this intentionally rather than mechanically.

## Physical Aggregation Strategies

Database engines can physically implement aggregation in different ways.

Two common strategies are:

- **Hash aggregation**
- **Sort-based aggregation**

A database optimizer chooses a strategy based on factors such as:

- Estimated row count
- Number of groups
- Available memory
- Existing ordering
- Cost estimates
- Parallel execution opportunities
- Query predicates

The SQL statement does not force one particular physical implementation.

## Hash Aggregation

Hash aggregation uses a hash structure keyed by the grouping columns.

For:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id;
```

the conceptual algorithm is:

```text
Read row
   │
   ▼
Hash customer_id
   │
   ▼
Find/create group state
   │
   ▼
Update COUNT
   │
   ▼
Read next row
```

Conceptually:

```text
Hash table

customer_id 101 → count = 37
customer_id 102 → count = 12
customer_id 103 → count = 91
...
```

### Advantages

- Does not require sorting all input rows by the grouping key.
- Can be efficient when the number of groups is manageable.
- Often effective for unordered input.

### Limitations

- Requires memory for group state.
- Large numbers of distinct groups can increase memory pressure.
- If memory is insufficient, the engine may need additional work such as spilling intermediate state to disk.

For high-cardinality grouping:

```sql
GROUP BY request_id
```

may produce almost as many groups as input rows, making aggregation substantially more expensive than:

```sql
GROUP BY service_name
```

with a small number of services.

## Sort-Based Aggregation

A sort-based strategy first orders rows by the grouping key and then processes consecutive rows belonging to the same group.

```text
Input rows
    │
    ▼
Sort by customer_id
    │
    ▼
101 101 101 102 102 103 103
    │
    ▼
Aggregate consecutive values
    │
    ▼
101 → count 3
102 → count 2
103 → count 2
```

### Advantages

- Naturally identifies group boundaries.
- Can exploit existing ordering.
- Can integrate efficiently with operations that also require sorted data.

### Limitations

- Sorting can be expensive.
- Large sorts may consume significant memory.
- External sorting may require temporary disk I/O.

The optimizer decides whether the expected cost justifies sorting.

## Hash vs Sort Aggregation

| Property | Hash aggregation | Sort-based aggregation |
|---|---|---|
| Main structure | Hash table | Sorted input |
| Requires ordering | No | Yes |
| Memory usage | Group-state dependent | Sort-state dependent |
| Strong with | Unordered input | Already ordered input |
| Risk | Many groups | Large sort |
| Disk spill possible | Yes | Yes |
| Choice | Optimizer-driven | Optimizer-driven |

Do not assume one is universally faster.

## Aggregation Memory

Aggregation can become expensive when the number of groups is large.

For example:

```sql
SELECT
    user_id,
    COUNT(*)
FROM events
GROUP BY user_id;
```

If the table contains 500 million events and 200 million distinct users, the aggregation state can become substantial.

A production engineer should distinguish:

```text
Number of input rows
```

from:

```text
Number of distinct groups
```

Both influence aggregation cost, but in different ways.

A query with:

```text
1 billion rows
100 groups
```

has a very different aggregation profile from:

```text
1 billion rows
500 million groups
```

## Partial and Parallel Aggregation

Modern databases can sometimes parallelize aggregation.

Conceptually:

```text
                 Orders
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
     Worker 1   Worker 2   Worker 3
        │          │          │
   partial agg partial agg partial agg
        │          │          │
        └──────────┼──────────┘
                   ▼
             Final aggregate
                   │
                   ▼
                Result
```

For example:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

workers may independently calculate partial aggregation states, after which those states are combined.

Parallel execution is workload- and database-dependent. It can improve throughput for sufficiently large queries but also introduces coordination and resource costs.

Do not assume that adding parallel workers always makes a query faster.

## Aggregation Execution With WHERE

Consider:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE
    status = 'paid'
GROUP BY customer_id;
```

The logical flow is:

```text
All orders
    │
    ▼
Filter paid orders
    │
    ▼
Group by customer
    │
    ▼
Count rows per customer
```

Filtering before aggregation is important because irrelevant rows do not need to contribute to aggregation state.

For a large table:

```text
1,000,000,000 total rows
        │
        ▼
100,000,000 paid rows
        │
        ▼
Aggregate only relevant rows
```

This can dramatically reduce work.

The optimizer may physically push predicates closer to the scan even when the SQL contains joins or other operations.

## Aggregation Execution With HAVING

Consider:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 100;
```

The logical flow is:

```text
orders
  │
  ▼
WHERE status = 'paid'
  │
  ▼
groups by customer_id
  │
  ▼
COUNT(*) for each group
  │
  ▼
HAVING COUNT(*) >= 100
  │
  ▼
final groups
```

`HAVING` generally cannot eliminate individual rows before the aggregate is known.

For example, the database cannot know that:

```text
customer 101 → COUNT(*) = 103
```

until enough input has been processed to establish that aggregate result.

Some optimizers can apply sophisticated transformations in particular cases, but application developers should reason from the logical semantics rather than assuming early elimination of aggregate-dependent predicates.

## Aggregation and Joins

Aggregation after joins is a major source of production bugs.

Consider:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

The join produces the rows that aggregation consumes.

Therefore:

```text
Customers
     │
     ▼
   JOIN
     │
     ▼
Joined row set
     │
     ▼
 GROUP BY
     │
     ▼
 COUNT
```

If the join multiplies rows unexpectedly, the aggregate operates on those multiplied rows.

## One-to-Many Join Multiplication

Suppose a customer has:

```text
3 orders
4 support tickets
```

A direct join can produce:

```text
3 × 4 = 12 joined rows
```

An aggregate over those rows may therefore report:

```text
COUNT(orders) = 12
```

instead of:

```text
COUNT(orders) = 3
```

This is not an aggregation bug. The aggregation is correctly counting the rows produced by the join.

The real problem is the join grain.

A safer pattern is to aggregate each relationship first:

```sql
WITH order_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
),
ticket_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
)
SELECT
    c.id,
    COALESCE(o.order_count, 0) AS order_count,
    COALESCE(t.ticket_count, 0) AS ticket_count
FROM customers AS c
LEFT JOIN order_counts AS o
    ON o.customer_id = c.id
LEFT JOIN ticket_counts AS t
    ON t.customer_id = c.id;
```

The key principle is:

> **Aggregate at the required grain before joining independent one-to-many relationships.**

## Aggregation and DISTINCT

`DISTINCT` changes the input set to an aggregate.

Compare:

```sql
SELECT COUNT(*)
FROM orders;
```

with:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

The first counts rows.

The second counts unique non-NULL customer IDs.

For:

| order_id | customer_id |
|---:|---:|
| 1 | 101 |
| 2 | 101 |
| 3 | 102 |
| 4 | 103 |

the results are:

```text
COUNT(*)              = 4
COUNT(DISTINCT ...)   = 3
```

Distinct aggregation can be more computationally expensive because the database must track which values have already been encountered.

For large datasets, inspect the execution plan instead of assuming the cost is negligible.

## Nested Aggregation

Sometimes the required result needs multiple aggregation stages.

For example:

> Find the average number of orders per customer.

This is not necessarily:

```sql
AVG(order_count)
```

over the raw orders table because `order_count` does not exist at the row level.

One approach is:

```sql
SELECT
    AVG(order_count)
FROM (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) AS customer_orders;
```

The logical flow is:

```text
orders
   │
   ▼
GROUP BY customer_id
   │
   ▼
one row per customer
   │
   ▼
COUNT(*) per customer
   │
   ▼
AVG(order_count)
   │
   ▼
one final result
```

This is an important distinction:

> **Aggregation changes the grain of the data. A later aggregate can operate on that new grain.**

## Aggregation Grain

Always identify the grain at each stage.

Consider:

```sql
SELECT
    customer_id,
    DATE(created_at) AS order_date,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    customer_id,
    DATE(created_at);
```

The final result grain is:

```text
one row per customer per day
```

It is not:

```text
one row per customer
```

If you later aggregate this result:

```sql
SELECT
    customer_id,
    SUM(order_count) AS total_orders
FROM (
    SELECT
        customer_id,
        DATE(created_at) AS order_date,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY
        customer_id,
        DATE(created_at)
) AS daily_orders
GROUP BY customer_id;
```

the intermediate grain is:

```text
customer + day
```

and the final grain is:

```text
customer
```

Thinking explicitly in terms of grain prevents many analytics and reporting errors.

## Aggregation Execution and Indexes

Indexes can help reduce the input to an aggregation, support joins, or provide useful ordering.

Consider:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time
GROUP BY customer_id;
```

An index such as:

```sql
CREATE INDEX idx_orders_tenant_created
ON orders (tenant_id, created_at);
```

may allow the database to locate the relevant time range for a tenant without scanning the entire table.

Whether this is beneficial depends on:

- Selectivity
- Table size
- Data distribution
- Query frequency
- Index size
- Write workload
- Database optimizer estimates

An index on every `GROUP BY` column is not automatically required.

## Ordered Aggregation and Indexes

An index may also provide rows in an order useful for aggregation.

For example:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

can potentially provide input ordered by `customer_id`.

That may be useful to an execution strategy that benefits from ordered input.

However, the optimizer may still choose another strategy if it estimates that a hash aggregate or different scan is cheaper.

The important principle is:

> **Indexes are access paths, not commands to the optimizer.**

## Aggregation and Materialized Data

Repeatedly aggregating a very large transactional table can become expensive.

For example:

```text
orders
events
transactions
api_requests
```

may contain billions of historical rows.

If a dashboard repeatedly asks:

```sql
SELECT
    service_name,
    DATE(created_at),
    COUNT(*),
    AVG(duration_ms)
FROM api_requests
GROUP BY
    service_name,
    DATE(created_at);
```

running this aggregation against raw data for every request may be inefficient.

A production architecture may instead maintain pre-aggregated data:

```text
Transactional events
        │
        ▼
Kafka / batch pipeline
        │
        ▼
Daily/hourly aggregate table
        │
        ▼
Reporting API
```

For example:

```sql
CREATE TABLE api_request_daily_metrics (
    metric_date date NOT NULL,
    service_name text NOT NULL,
    request_count bigint NOT NULL,
    average_duration_ms numeric,
    PRIMARY KEY (metric_date, service_name)
);
```

The reporting query then operates on much smaller data.

This introduces additional concerns:

- Freshness
- Backfills
- Late-arriving events
- Idempotency
- Reprocessing
- Data correction
- Retention

Pre-aggregation is an architectural trade-off, not merely a SQL optimization.

## Production Example

Consider a multi-tenant SaaS application that exposes a customer analytics endpoint.

The request might be:

```text
GET /api/v1/analytics/orders
```

The backend needs:

- Tenant isolation
- A reporting time window
- Paid orders only
- Per-customer grouping
- Minimum order threshold

The query could be:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE
    tenant_id = :tenant_id
    AND status = 'paid'
    AND created_at >= :start_time
    AND created_at < :end_time
GROUP BY customer_id
HAVING COUNT(*) >= :minimum_orders
ORDER BY revenue DESC, customer_id
LIMIT :limit;
```

The execution reasoning is:

```text
Tenant + time + status filters
              │
              ▼
       Reduced input set
              │
              ▼
      Group by customer
              │
              ▼
   Aggregate order metrics
              │
              ▼
    Apply HAVING threshold
              │
              ▼
      Sort / limit results
```

For a production implementation:

- Parameterize all values.
- Enforce tenant scoping server-side.
- Use half-open time intervals.
- Validate pagination limits.
- Inspect the execution plan.
- Monitor query latency.
- Consider pre-aggregated data for high-volume reporting.

## Reading EXPLAIN for Aggregation

For PostgreSQL, start with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE
    status = 'paid'
GROUP BY customer_id;
```

Important operators to recognize include:

| Plan node | Meaning |
|---|---|
| `Seq Scan` | Sequential table scan |
| `Index Scan` | Index-driven row access |
| `Bitmap Heap Scan` | Bitmap-assisted table access |
| `Sort` | Sorts rows |
| `HashAggregate` | Hash-based aggregation |
| `GroupAggregate` | Grouping over appropriately ordered input |
| `Gather` | Collects results from parallel workers |
| `Gather Merge` | Merges ordered parallel results |

Do not treat `Seq Scan` as automatically bad. For a query reading a large percentage of a table, a sequential scan can be cheaper than repeated random index access.

The goal is an efficient plan for the workload, not the presence of a particular operator.

## Memory and Disk Spills

Large aggregation or sorting operations may exceed the memory available to an execution node.

The engine can then spill intermediate data to temporary storage.

This can cause:

- Increased latency
- Higher I/O
- Increased disk utilization
- Resource contention
- Less predictable query performance

For production workloads, monitor:

- Query execution time
- Temporary file usage
- Memory pressure
- CPU utilization
- I/O latency
- Concurrent analytical queries

A query that performs well on a development dataset can behave very differently when the number of rows or groups increases by several orders of magnitude.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Assuming SQL execution follows textual order | SQL syntax differs from logical processing | Learn logical query processing |
| Ignoring result grain | Grouping is treated as just syntax | Define the intended grain explicitly |
| Counting after a multiplying join | Joined rows are mistaken for source entities | Validate join cardinality |
| Assuming `COUNT(*)` and `COUNT(column)` are equivalent | NULL behavior is overlooked | Choose based on required semantics |
| Treating `NULL` as zero | Missing and zero values are conflated | Normalize only when business semantics require it |
| Assuming aggregation is always cheap | Large input or high cardinality is ignored | Measure input rows and distinct groups |
| Assuming indexes automatically accelerate `GROUP BY` | Indexes are treated as universal optimizers | Validate with `EXPLAIN` |
| Assuming hash aggregation is always faster | Physical strategy is oversimplified | Let the optimizer choose and inspect plans |
| Aggregating raw events for every dashboard request | Transactional data is reused as an analytics store | Consider pre-aggregation |
| Ignoring intermediate grain | Nested aggregation produces unexpected results | Track grain at every query stage |
| Using `DISTINCT` to hide join duplication | Incorrect joins are masked rather than fixed | Correct the join model first |

## Production Considerations

### Performance

For large aggregation queries:

- Filter early with selective predicates.
- Avoid unnecessary columns in joins and intermediate results.
- Verify join cardinality.
- Reduce the number of rows entering aggregation where possible.
- Monitor the number of distinct groups.
- Use `EXPLAIN (ANALYZE, BUFFERS)` for PostgreSQL.
- Test with production-like data volumes.
- Consider pre-aggregation for repeated analytical workloads.

### Scalability

Aggregation scalability depends heavily on:

```text
Input rows
×
Number of groups
×
Aggregation complexity
```

A query can remain efficient with enormous input if the database can process it efficiently, but high cardinality, expensive expressions, distinct aggregates, joins, and sorting can substantially increase resource consumption.

For very large analytical workloads, consider:

- Partitioning
- Incremental aggregation
- Materialized views
- Summary tables
- Dedicated analytical systems

### Reliability

Aggregation results are only as correct as the input relation.

Validate:

- Join multiplicity
- NULL semantics
- Time boundaries
- Duplicate events
- Late-arriving data
- Data corrections
- Transaction consistency

For financial or billing systems, aggregate queries should be backed by well-defined data invariants and reconciliation processes.

### Security

Aggregation queries in multi-tenant systems must enforce tenant isolation before aggregation.

Prefer:

```sql
WHERE tenant_id = :tenant_id
```

rather than retrieving broad data and filtering it in application code.

Application-supplied values should always be parameterized.

Avoid dynamically concatenating:

```python
f"WHERE tenant_id = {tenant_id}"
```

Use your database driver's parameter binding or ORM query parameters instead.

### Operational Monitoring

For high-value aggregation queries, monitor:

- p50/p95/p99 latency
- Execution count
- Rows processed
- Temporary disk usage
- CPU consumption
- Database memory pressure
- Lock/wait behavior
- Query plan regressions

A query can be logically correct and still become an operational incident when data volume grows.

## Backend Integration

Django and FastAPI applications should treat database aggregation as database work rather than pulling raw rows into Python unnecessarily.

Prefer:

```python
from django.db.models import Count, Sum

customer_metrics = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="paid",
        created_at__gte=start_time,
        created_at__lt=end_time,
    )
    .values("customer_id")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("total_amount"),
    )
    .filter(order_count__gte=minimum_orders)
)
```

over:

```python
orders = list(
    Order.objects.filter(
        tenant_id=tenant_id,
        status="paid",
    )
)

# Aggregate millions of rows in Python.
```

Database engines are designed to perform relational operations and aggregation close to the data. Pulling large datasets across the application/database boundary increases:

- Network traffic
- Application memory
- CPU usage
- Serialization cost
- Request latency

Application-side aggregation is appropriate only when the data genuinely needs to be processed outside the database.

## Interview Traps

### Does GROUP BY Execute Before WHERE?

No.

The logical model is:

```text
FROM
↓
WHERE
↓
GROUP BY
↓
Aggregate
↓
HAVING
```

The optimizer can physically rearrange operations while preserving semantics.

### Is HAVING Always Slow?

No.

`HAVING` itself is not inherently slow. The cost depends on how much data must be processed to form the groups and calculate the aggregates.

### Does GROUP BY Always Require Sorting?

No.

A database can use hash aggregation or other strategies. Sorting is only one possible implementation.

### Is a Sequential Scan Bad for Aggregation?

Not necessarily.

If a query needs a large percentage of a table, a sequential scan can be the optimal strategy.

### Why Can COUNT Become Incorrect After a JOIN?

Because aggregation counts the rows produced by the join. If the join multiplies rows, the aggregate sees the multiplied relation.

### Why Is AVG Different From SUM / COUNT(*)?

`AVG(column)` generally ignores NULL values and therefore behaves conceptually like:

```text
SUM(non_NULL_values) / COUNT(non_NULL_values)
```

It is not necessarily:

```text
SUM(column) / COUNT(*)
```

### Can Aggregation Be Parallelized?

Yes, when the database engine and query plan support it. Partial aggregation can be performed by workers and combined into a final result.

## Key Takeaways

- Aggregation changes the **grain of the data**; always identify the input and output grain before reasoning about correctness.
- Physical aggregation commonly uses hash- or sort-based strategies, with memory, cardinality, ordering, and optimizer estimates influencing the choice.
- `WHERE` can reduce the rows entering aggregation, while `HAVING` filters groups after aggregate state has been produced.
- Joins can multiply rows before aggregation, so incorrect join cardinality is a common cause of inflated counts and sums.
- Production aggregation requires execution-plan analysis, NULL-aware semantics, appropriate indexing, resource monitoring, and pre-aggregation when raw-data scans no longer scale.