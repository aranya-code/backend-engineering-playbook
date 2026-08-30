# 11- WHERE vs HAVING

## Overview

`WHERE` and `HAVING` both filter query results, but they operate at different stages of query processing.

- `WHERE` filters **rows before grouping and aggregation**.
- `HAVING` filters **groups after grouping and aggregation**.

This distinction is fundamental when writing analytical queries, reporting queries, dashboards, and backend APIs. Using the wrong clause can produce invalid SQL, incorrect results, or unnecessarily expensive execution plans.

A useful mental model is:

```text
Source rows
    │
    ▼
  WHERE          ← filter individual rows
    │
    ▼
Filtered rows
    │
    ▼
 GROUP BY        ← form groups
    │
    ▼
Aggregates       ← COUNT, SUM, AVG, MIN, MAX
    │
    ▼
 HAVING          ← filter groups
    │
    ▼
 ORDER BY
    │
    ▼
Final result
```

## Core Difference

| Aspect | `WHERE` | `HAVING` |
|---|---|---|
| Filters | Rows | Groups |
| Evaluation | Before aggregation | After aggregation |
| Common use | Row-level conditions | Aggregate conditions |
| Can use aggregate functions directly? | Generally no | Yes |
| Can reduce input before grouping? | Yes | No |
| Typical example | `status = 'paid'` | `COUNT(*) >= 10` |
| Performance role | Often highly significant | Applied after grouping |

The simplest rule is:

> **If the condition describes an individual row, use `WHERE`. If it describes an aggregated group, use `HAVING`.**

## WHERE

`WHERE` filters rows from the source relation before grouping or aggregation.

Example:

```sql
SELECT
    id,
    customer_id,
    total_amount
FROM orders
WHERE status = 'paid';
```

Only paid orders participate in subsequent query processing.

With aggregation:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;
```

The database conceptually performs:

```text
All orders
    │
    ▼
WHERE status = 'paid'
    │
    ▼
Paid orders
    │
    ▼
GROUP BY customer_id
    │
    ▼
SUM(total_amount)
```

This matters because filtering rows before aggregation can significantly reduce the amount of data that must be grouped.

## HAVING

`HAVING` filters groups produced by `GROUP BY`.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The database first forms a group for each customer, calculates the order count, and then removes customers whose count is below 10.

The predicate:

```sql
COUNT(*) >= 10
```

cannot normally be evaluated by `WHERE` because the count does not exist until aggregation occurs.

## The Canonical Pattern

Production queries frequently use both clauses:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE
    status = 'paid'
    AND created_at >= TIMESTAMP '2026-01-01 00:00:00'
    AND created_at < TIMESTAMP '2026-02-01 00:00:00'
GROUP BY customer_id
HAVING
    COUNT(*) >= 10
    AND SUM(total_amount) >= 100000;
```

The responsibilities are clearly separated:

| Stage | Responsibility |
|---|---|
| `WHERE` | Select qualifying orders |
| `GROUP BY` | Define the customer grain |
| `COUNT` / `SUM` | Calculate customer metrics |
| `HAVING` | Select qualifying customers |

This separation is usually the clearest way to express business reporting requirements.

## Why Aggregate Conditions Belong in HAVING

Consider a requirement:

> Find customers who placed at least 10 paid orders.

An incorrect approach is:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE COUNT(*) >= 10
  AND status = 'paid'
GROUP BY customer_id;
```

The problem is that `WHERE` operates before `COUNT(*)` has been calculated.

The correct query is:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The row-level condition belongs in `WHERE`; the group-level condition belongs in `HAVING`.

## Why WHERE Is Usually Preferable for Row-Level Filters

Suppose the requirement is:

> Calculate revenue for paid orders from India.

Use:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE
    status = 'paid'
    AND country = 'IN'
GROUP BY customer_id;
```

Do not unnecessarily write:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
HAVING status = 'paid'
   AND country = 'IN';
```

Apart from grouping semantics and validity issues, the first form expresses the intent correctly: remove irrelevant rows before aggregation.

For large tables, early filtering can also reduce:

- Rows read by later operators
- Hash aggregation memory
- Sort work
- Temporary storage
- CPU consumption
- Query latency

## Predicate Pushdown

A senior-level SQL optimization principle is **predicate pushdown**: apply filters as early as possible when they are semantically safe to do so.

Consider:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE created_at >= TIMESTAMP '2026-01-01 00:00:00'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The date condition reduces the rows entering the aggregation.

Conceptually:

```text
orders
  │
  ├── discard old rows
  │
  ▼
recent orders
  │
  ├── group by customer
  │
  ▼
customer groups
  │
  ├── discard groups with < 10 orders
  │
  ▼
result
```

The database optimizer may rewrite or reorder operations internally, but expressing predicates at the correct logical level gives the optimizer useful information and makes the query's intent explicit.

## Conditions That Can Move Between WHERE and HAVING

Some predicates reference grouping columns rather than aggregate values.

For example:

```sql
SELECT
    country,
    COUNT(*) AS user_count
FROM users
GROUP BY country
HAVING country = 'IN';
```

The condition can generally be expressed more naturally as:

```sql
SELECT
    country,
    COUNT(*) AS user_count
FROM users
WHERE country = 'IN'
GROUP BY country;
```

The second query filters source rows before grouping.

However, do not blindly move predicates between clauses. A rewrite is valid only when it preserves semantics, particularly around:

- Outer joins
- NULL values
- Grouping expressions
- Window functions
- Subqueries
- Duplicate-producing joins

The goal is not "always move `HAVING` into `WHERE`." The goal is to place each predicate at the earliest stage where its meaning is valid.

## WHERE with Aggregation

`WHERE` does not mean aggregation cannot be used in the same query.

It determines which rows participate in aggregation.

Example:

```sql
SELECT
    department_id,
    AVG(salary) AS average_salary
FROM employees
WHERE employment_status = 'active'
GROUP BY department_id;
```

The average is calculated only from active employees.

This is different from:

```sql
SELECT
    department_id,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department_id
HAVING AVG(salary) > 100000;
```

Here:

- `WHERE` chooses which employees participate.
- `HAVING` chooses which departments remain.

They answer different questions.

## HAVING with Multiple Aggregates

Multiple aggregate conditions can be combined:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING
    COUNT(*) >= 10
    AND SUM(total_amount) >= 100000
    AND AVG(total_amount) >= 5000;
```

Each condition operates at the customer-group level.

This pattern is common for:

- Customer segmentation
- Fraud detection
- Account qualification
- Sales reporting
- SLA reporting
- Operational dashboards

## WHERE vs HAVING with NULL

NULL handling can make seemingly equivalent rewrites produce different results.

Consider:

```sql
SELECT
    customer_id,
    AVG(total_amount) AS average_order
FROM orders
GROUP BY customer_id
HAVING AVG(total_amount) > 1000;
```

`AVG()` ignores NULL values. If every `total_amount` in a group is NULL, the result is NULL.

The predicate:

```sql
NULL > 1000
```

is `UNKNOWN`, not `TRUE`, so the group is removed.

Explicit handling may be appropriate:

```sql
HAVING COALESCE(AVG(total_amount), 0) > 1000;
```

But do not use `COALESCE(..., 0)` automatically. Zero and "no non-NULL observations" may represent different business states.

## WHERE vs HAVING with Joins

The distinction becomes especially important with joins.

Example:

```sql
SELECT
    c.id AS customer_id,
    COUNT(o.id) AS order_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid'
GROUP BY c.id
HAVING COUNT(o.id) >= 10;
```

Here:

```text
JOIN
  ↓
WHERE paid orders
  ↓
GROUP BY customer
  ↓
COUNT orders
  ↓
HAVING count >= 10
```

The `WHERE` condition removes unpaid orders before the count is calculated.

### Outer Join Warning

Moving a predicate from an outer join's `ON` clause to `WHERE` can change the query's semantics.

Compare:

```sql
SELECT
    c.id,
    COUNT(o.id) AS paid_orders
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'paid'
GROUP BY c.id;
```

with:

```sql
SELECT
    c.id,
    COUNT(o.id) AS paid_orders
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid'
GROUP BY c.id;
```

The second form removes rows where the joined order is NULL, effectively eliminating customers without matching paid orders from the result.

This is a common production bug.

## Join Multiplication

`WHERE` and `HAVING` cannot protect against an incorrectly shaped join.

Suppose:

```text
Customer A
├── 3 orders
└── 4 support tickets
```

Joining both one-to-many relationships directly can produce:

```text
3 × 4 = 12 rows
```

An aggregation over those rows can therefore overcount.

For example:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN support_tickets AS t
    ON t.customer_id = c.id
GROUP BY c.id;
```

`HAVING COUNT(o.id) >= 3` does not fix the underlying multiplication.

A safer design is to aggregate each relationship independently:

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
    o.customer_id,
    o.order_count,
    COALESCE(t.ticket_count, 0) AS ticket_count
FROM order_counts AS o
LEFT JOIN ticket_counts AS t
    ON t.customer_id = o.customer_id;
```

The important principle is:

> **Choose the aggregation grain before joining unrelated one-to-many datasets.**

## Logical Query Processing Order

SQL is written in one order but logically processed in another.

A useful simplified model is:

```text
FROM / JOIN
      ↓
WHERE
      ↓
GROUP BY
      ↓
Aggregate calculations
      ↓
HAVING
      ↓
SELECT
      ↓
ORDER BY
      ↓
LIMIT
```

This explains several common SQL rules.

For example:

```sql
WHERE COUNT(*) > 10
```

is invalid because `COUNT(*)` belongs to a later logical stage.

Whereas:

```sql
HAVING COUNT(*) > 10
```

is valid because `HAVING` operates after grouping and aggregation.

Actual database engines use sophisticated optimizers and do not necessarily execute operations in exactly this physical order. The logical order is a model for understanding SQL semantics, not a description of the physical execution plan.

## Execution and Performance

For large production datasets, the distinction affects query cost.

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

A database may use an execution strategy involving:

```text
Scan / Index Scan
      ↓
Filter status = 'paid'
      ↓
Hash Aggregate or Sort Aggregate
      ↓
Filter count >= 100
```

The exact physical plan depends on the database engine, statistics, indexes, data distribution, and configuration.

In PostgreSQL, inspect important queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 100;
```

Look for:

- Actual vs estimated row counts
- Scan type
- Rows removed by filters
- Hash aggregate vs sort aggregate
- Memory consumption
- Temporary disk usage
- Buffer reads
- Execution time

Do not optimize based only on SQL appearance. Validate the actual execution plan against production-like data.

## Indexing Considerations

An index does not automatically make `HAVING COUNT(*) >= 100` inexpensive.

For:

```sql
GROUP BY customer_id
HAVING COUNT(*) >= 100
```

the database generally needs enough information about the relevant rows to determine each customer's count.

Indexes are often more useful for selective `WHERE` predicates such as:

```sql
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time
```

For a multi-tenant application, an index such as:

```sql
CREATE INDEX idx_orders_tenant_created_at
ON orders (tenant_id, created_at);
```

may help reduce the rows entering aggregation, depending on the complete query and workload.

Index design should be driven by:

- Actual query patterns
- Execution plans
- Cardinality
- Selectivity
- Write overhead
- Storage cost

## Backend API Example

A reporting endpoint might expose:

```text
GET /api/v1/customers/qualified
```

with parameters such as:

```text
tenant_id
start_time
end_time
minimum_orders
```

A corresponding query could be:

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

This query demonstrates a clean division:

- Tenant and time boundaries → `WHERE`
- Business event eligibility → `WHERE`
- Customer grouping → `GROUP BY`
- Customer metrics → aggregates
- Minimum order threshold → `HAVING`
- Ranking → `ORDER BY`

Adding `customer_id` as a deterministic tie-breaker is useful when the result is paginated or consumed by downstream systems.

## Django ORM

Django's aggregation API maps naturally to this distinction.

```python
from django.db.models import Count, Sum

qualified_customers = (
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
    .order_by("-revenue", "customer_id")
)
```

Conceptually:

```text
filter(...)
    ↓
WHERE

values("customer_id")
    ↓
GROUP BY

annotate(...)
    ↓
COUNT / SUM

filter(order_count__gte=...)
    ↓
HAVING
```

The ORM abstraction is convenient, but complex relationship traversals can introduce unexpected joins and duplicate rows. Inspect generated SQL and use `EXPLAIN` for expensive queries.

## Common Mistakes

| Mistake | Problem | Correct approach |
|---|---|---|
| `WHERE COUNT(*) >= 10` | Aggregate is not available at row-filtering stage | Use `HAVING COUNT(*) >= 10` |
| Putting every filter in `HAVING` | Delays row filtering and obscures intent | Use `WHERE` for row predicates |
| Moving `HAVING` to `WHERE` blindly | Can change semantics | Verify the predicate is row-level and safely movable |
| Filtering an outer join in `WHERE` | Can turn a `LEFT JOIN` into inner-join behavior | Consider filtering in `ON` |
| Ignoring NULL behavior | Aggregate and predicate semantics can change | Test NULL cases explicitly |
| Counting after multiple one-to-many joins | Produces inflated aggregates | Pre-aggregate relationships |
| Assuming `HAVING` improves performance | It filters after grouping | Reduce input with selective predicates |
| Assuming indexes solve aggregation | Grouping may still require substantial data processing | Inspect the execution plan |
| Using `COALESCE(..., 0)` automatically | Can confuse "no value" with zero | Apply only when business semantics support it |
| Trusting ORM grouping without inspecting SQL | Hidden joins can alter aggregation grain | Review generated SQL for complex queries |

## Common Production Patterns

### Filter Rows, Then Filter Groups

This is the most common pattern:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE
    status = 'paid'
    AND created_at >= :start_time
    AND created_at < :end_time
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

### Find Groups Exceeding a Threshold

```sql
SELECT
    product_id,
    SUM(quantity) AS units_sold
FROM order_items
GROUP BY product_id
HAVING SUM(quantity) >= 10000;
```

### Filter Groups Using Multiple Metrics

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    AVG(total_amount) AS average_order
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 10
   AND AVG(total_amount) >= 5000;
```

### Use WHERE to Reduce a Reporting Window

```sql
SELECT
    service_name,
    endpoint,
    COUNT(*) AS request_count,
    AVG(duration_ms) AS average_duration
FROM api_requests
WHERE
    created_at >= :start_time
    AND created_at < :end_time
GROUP BY
    service_name,
    endpoint
HAVING COUNT(*) >= 1000;
```

This pattern is useful for operational metrics where the reporting window should be applied before aggregation.

## Interview Traps

### Is HAVING Just WHERE for Groups?

Conceptually, that is a useful mental model, but it is incomplete.

`WHERE` filters source rows. `HAVING` filters grouped results. Their position in the logical query-processing model gives them different semantics.

### Can HAVING Be Used Without GROUP BY?

Yes, depending on the SQL dialect and query form.

For example:

```sql
SELECT COUNT(*) AS order_count
FROM orders
HAVING COUNT(*) >= 100000;
```

The aggregate can represent a single group.

### Can WHERE and HAVING Appear in the Same Query?

Yes, and this is extremely common:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

### Which One Is Faster?

Neither is inherently faster.

The correct question is whether a predicate can be evaluated earlier. A selective row-level `WHERE` predicate can reduce the amount of data that aggregation must process, which can improve performance.

### Can Every HAVING Predicate Be Replaced by WHERE?

No.

This cannot be moved directly:

```sql
HAVING COUNT(*) >= 10
```

because `COUNT(*)` is a group-level value.

A grouping-column predicate may sometimes be moved, but semantic equivalence must be established first.

### Does SQL Physically Execute WHERE Before HAVING?

The logical processing model places `WHERE` before grouping and `HAVING` after aggregation. The optimizer may transform the physical execution plan while preserving the required SQL semantics.

## Production Checklist

Before shipping a query containing `WHERE` and/or `HAVING`:

- [ ] Identify the required result grain.
- [ ] Classify every predicate as row-level or group-level.
- [ ] Put row-level filters in `WHERE` when semantically valid.
- [ ] Put aggregate-dependent filters in `HAVING`.
- [ ] Verify NULL semantics.
- [ ] Check `COUNT(*)` vs `COUNT(column)` behavior.
- [ ] Validate joins for one-to-many multiplication.
- [ ] Be especially careful when filtering `LEFT JOIN` results.
- [ ] Inspect generated SQL when using an ORM.
- [ ] Run `EXPLAIN` on important production queries.
- [ ] Verify indexes support selective filters and joins.
- [ ] Parameterize application-provided values.
- [ ] Use explicit time boundaries for reporting queries.
- [ ] Add deterministic ordering when paginating grouped results.
- [ ] Consider pre-aggregation or materialized reporting data for expensive recurring analytics.

## Key Takeaways

- `WHERE` filters **rows before aggregation**, while `HAVING` filters **groups after aggregation**.
- Put row-level predicates such as status, tenant, and time filters in `WHERE`; use `HAVING` for conditions involving `COUNT()`, `SUM()`, `AVG()`, `MIN()`, or `MAX()`.
- Predicate placement affects both correctness and performance, but predicates should only be moved when their semantics remain equivalent.
- Joins, NULL handling, and aggregation grain can cause subtle correctness bugs that neither `WHERE` nor `HAVING` can independently fix.
- For production SQL, validate query semantics with representative data and validate performance with execution plans rather than relying on clause placement alone.