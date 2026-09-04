# 05- Aggregation Questions

## Overview

SQL aggregation is one of the most common interview areas because it tests whether you can transform row-level data into meaningful business-level results.

Aggregation questions typically involve:

- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`
- `GROUP BY`
- `HAVING`
- `DISTINCT`
- Conditional aggregation
- `NULL` behavior
- Aggregation with joins
- Aggregation with window functions
- Aggregation at different grains
- Date/time aggregation
- PostgreSQL-specific aggregation
- Performance and execution plans

At senior backend level, the important question is not simply:

> "How does `GROUP BY` work?"

It is:

> "What does one output row represent, which rows contribute to it, and can joins or filters change the measure being calculated?"

---

## What Is Aggregation?

Aggregation reduces multiple input rows into a smaller result set by calculating values such as:

```text
COUNT
SUM
AVG
MIN
MAX
```

For example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_revenue
FROM orders
GROUP BY customer_id;
```

Input:

```text
customer_id | total_amount
------------+-------------
1           | 100
1           | 200
2           | 150
```

Output:

```text
customer_id | total_revenue
------------+--------------
1           | 300
2           | 150
```

The query changes the result grain from:

> one row per order

to:

> one row per customer.

---

## The Most Important Aggregation Concept: Grain

Before writing an aggregate query, define the grain.

Suppose:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

The grain is:

> one row per customer.

If you instead write:

```sql
SELECT
    customer_id,
    order_date,
    SUM(total_amount)
FROM orders
GROUP BY customer_id, order_date;
```

the grain becomes:

> one row per customer per order date.

Adding a grouping column changes the number and meaning of result rows.

---

## `GROUP BY`

`GROUP BY` divides rows into groups.

```sql
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY status;
```

Conceptually:

```text
orders
   ↓
group by status
   ↓
one group per status
   ↓
COUNT each group
```

Example result:

```text
status     | order_count
-----------+------------
pending    | 120
paid       | 850
shipped    | 430
cancelled  | 90
```

---

## Why `GROUP BY` Exists

Aggregation is useful when the application needs business-level metrics rather than individual rows.

Examples:

- Revenue per customer
- Orders per day
- Users per organization
- Average transaction value
- Products sold per category
- Failed requests per service
- Events per hour

Instead of transferring millions of rows to Python and aggregating them there, the database can perform the aggregation close to the data.

---

## Basic Aggregate Functions

| Function | Purpose |
|---|---|
| `COUNT` | Count rows or non-null values |
| `SUM` | Add numeric values |
| `AVG` | Calculate average |
| `MIN` | Minimum value |
| `MAX` | Maximum value |

Example:

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order_value,
    MIN(total_amount) AS smallest_order,
    MAX(total_amount) AS largest_order
FROM orders;
```

Without `GROUP BY`, the entire filtered input is treated as one aggregation group.

---

## `COUNT(*)`

`COUNT(*)` counts rows.

```sql
SELECT COUNT(*)
FROM orders;
```

If 10,000 rows qualify, the result is:

```text
10000
```

It does not depend on whether individual columns contain `NULL`.

---

## `COUNT(column)`

`COUNT(column)` counts non-null values.

```sql
SELECT COUNT(customer_id)
FROM orders;
```

If 1,000 rows exist but 50 have `customer_id = NULL`, the result is:

```text
950
```

This distinction is extremely important in interviews.

---

## `COUNT(*)` vs `COUNT(column)`

| Expression | Counts |
|---|---|
| `COUNT(*)` | Every qualifying row |
| `COUNT(column)` | Rows where `column IS NOT NULL` |
| `COUNT(DISTINCT column)` | Distinct non-null values |

Example:

```sql
SELECT
    COUNT(*) AS rows,
    COUNT(customer_id) AS non_null_customers,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders;
```

---

## `COUNT(DISTINCT ...)`

To count unique customers:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

This answers:

> How many distinct customers placed orders?

It does not answer:

> How many orders were placed?

Those are different metrics.

---

## `SUM`

`SUM` adds non-null numeric values.

```sql
SELECT
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid';
```

If no qualifying rows exist, `SUM` can return `NULL`.

If the application requires zero:

```sql
SELECT
    COALESCE(SUM(total_amount), 0) AS revenue
FROM orders
WHERE status = 'paid';
```

---

## `AVG`

`AVG` calculates the average of non-null values.

```sql
SELECT
    AVG(total_amount) AS average_order_value
FROM orders;
```

Important:

> `AVG` does not treat `NULL` as zero.

If rows are:

```text
100
200
NULL
```

the average is:

```text
150
```

not:

```text
100
```

---

## `MIN` and `MAX`

```sql
SELECT
    MIN(total_amount) AS minimum_order,
    MAX(total_amount) AS maximum_order
FROM orders;
```

These functions ignore `NULL` values.

If all values are `NULL`, the result is `NULL`.

---

## `NULL` and Aggregation

Consider:

```text
amount
------
100
200
NULL
```

Then:

```sql
COUNT(*)             → 3
COUNT(amount)        → 2
SUM(amount)          → 300
AVG(amount)          → 150
```

This is a frequent interview question.

The key distinction is:

> `COUNT(*)` counts rows; most ordinary aggregate functions operate on non-null input values.

---

## `GROUP BY` Multiple Columns

```sql
SELECT
    customer_id,
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    customer_id,
    status;
```

The grain becomes:

> one row per customer per status.

Example:

```text
customer_id | status    | order_count
------------+-----------+------------
1           | paid      | 10
1           | cancelled | 2
2           | paid      | 4
```

---

## Grouping Changes Result Cardinality

Suppose there are:

```text
1,000,000 orders
100,000 customers
```

Grouping by:

```sql
customer_id
```

can produce at most approximately:

```text
100,000 groups
```

Grouping by:

```sql
customer_id, status
```

can produce more groups.

The number of groups affects:

- Memory
- Sorting
- Hash aggregation
- Network transfer
- Query latency

---

## `WHERE` vs `HAVING`

`WHERE` filters input rows before aggregation.

`HAVING` filters groups after aggregation.

Example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total_amount) > 1000;
```

Conceptually:

```text
orders
  ↓
WHERE status = 'paid'
  ↓
GROUP BY customer_id
  ↓
SUM
  ↓
HAVING revenue > 1000
```

---

## Why `WHERE` Cannot Usually Use Aggregate Results

This is invalid:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
WHERE SUM(total_amount) > 1000
GROUP BY customer_id;
```

The aggregate has not been computed at the point where `WHERE` logically filters rows.

Use:

```sql
HAVING SUM(total_amount) > 1000
```

instead.

---

## `WHERE` and `HAVING` Together

Use `WHERE` to reduce the input set as early as the semantics allow.

Use `HAVING` to filter aggregate groups.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS paid_orders
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 5;
```

This is preferable to grouping all statuses and then trying to filter them using `HAVING`.

---

## Can `HAVING` Be Used Without `GROUP BY`?

Yes.

For example:

```sql
SELECT
    COUNT(*) AS order_count
FROM orders
HAVING COUNT(*) > 1000;
```

The query treats the entire input as one aggregation group.

If the condition is false, the query returns no row.

---

## Grouping by Expressions

You can group by expressions:

```sql
SELECT
    DATE(created_at) AS order_date,
    COUNT(*) AS order_count
FROM orders
GROUP BY DATE(created_at);
```

This is useful for reporting but can have performance implications if the expression prevents efficient use of an index.

For large time-series workloads, range filtering, generated columns, expression indexes, or pre-aggregated structures may be more appropriate depending on the requirement.

---

## Date Aggregation

A common reporting query:

```sql
SELECT
    DATE(created_at) AS order_date,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE created_at >= $1
  AND created_at < $2
GROUP BY DATE(created_at)
ORDER BY order_date;
```

The filtering range should generally remain sargable:

```sql
created_at >= $1
AND created_at < $2
```

rather than filtering the timestamp through a function in the `WHERE` clause.

---

## Timezone-Aware Aggregation

"Orders per day" is ambiguous in a global application.

A day could mean:

- UTC day
- Tenant-local day
- Customer-local day
- Business timezone

For production reporting, define the timezone explicitly.

Otherwise a transaction near midnight can be assigned to different business dates depending on the execution environment.

---

## Conditional Aggregation

Conditional aggregation calculates multiple metrics in one query.

PostgreSQL supports:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'paid'
    ) AS paid_orders,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders
FROM orders;
```

This is often cleaner than running separate queries.

---

## `FILTER` in PostgreSQL

PostgreSQL's `FILTER` clause applies a condition to an aggregate.

```sql
SELECT
    SUM(total_amount) FILTER (
        WHERE status = 'paid'
    ) AS paid_revenue,
    SUM(total_amount) FILTER (
        WHERE status = 'refunded'
    ) AS refunded_amount
FROM orders;
```

This can be particularly useful for dashboards and operational metrics.

---

## Conditional Aggregation With `CASE`

Portable SQL often uses:

```sql
SELECT
    SUM(
        CASE
            WHEN status = 'paid' THEN total_amount
            ELSE 0
        END
    ) AS paid_revenue
FROM orders;
```

PostgreSQL's `FILTER` syntax can be more expressive when supported by the target database.

---

## `SUM(CASE ...)`

A common interview pattern:

```sql
SELECT
    customer_id,
    SUM(
        CASE
            WHEN status = 'paid' THEN 1
            ELSE 0
        END
    ) AS paid_orders
FROM orders
GROUP BY customer_id;
```

This counts paid orders per customer.

---

## Boolean Aggregation

PostgreSQL provides boolean aggregates:

```sql
BOOL_AND(condition)
BOOL_OR(condition)
```

Example:

```sql
SELECT
    customer_id,
    BOOL_AND(status = 'paid') AS all_orders_paid,
    BOOL_OR(status = 'cancelled') AS has_cancelled_order
FROM orders
GROUP BY customer_id;
```

These can express business conditions more directly than complicated `CASE` expressions.

---

## `ARRAY_AGG`

PostgreSQL can aggregate values into arrays:

```sql
SELECT
    customer_id,
    ARRAY_AGG(id ORDER BY created_at DESC) AS order_ids
FROM orders
GROUP BY customer_id;
```

This can be useful for controlled result construction.

However, very large arrays can create substantial memory and response-size costs.

Do not use aggregation to construct enormous application payloads indiscriminately.

---

## `STRING_AGG`

PostgreSQL provides string aggregation:

```sql
SELECT
    customer_id,
    STRING_AGG(status, ', ' ORDER BY created_at) AS statuses
FROM orders
GROUP BY customer_id;
```

This is useful for reporting but should be used carefully when the resulting strings can become very large.

---

## `JSON_AGG` and JSON Construction

PostgreSQL can aggregate structured data:

```sql
SELECT
    customer_id,
    JSON_AGG(
        JSON_BUILD_OBJECT(
            'id', id,
            'status', status,
            'amount', total_amount
        )
        ORDER BY created_at DESC
    ) AS orders
FROM orders
GROUP BY customer_id;
```

This can be useful for specialized API/read-model queries.

For large collections, however, application pagination is usually preferable to creating unbounded JSON aggregates inside one database response.

---

## Aggregation With JOINs

Consider:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This produces one row per customer, including customers with zero orders.

The `LEFT JOIN` is essential because an inner join would remove customers without orders.

---

## `COUNT(*)` With LEFT JOIN

Consider:

```sql
SELECT
    c.id,
    COUNT(*) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

A customer with no orders can still produce one joined row:

```text
customer + NULL order
```

Therefore `COUNT(*)` can return:

```text
1
```

instead of zero.

Use:

```sql
COUNT(o.id)
```

when the requirement is to count actual orders.

---

## Aggregation After One-to-Many JOINs

This is a common source of incorrect metrics.

Suppose:

```text
orders
1 → $100
2 → $200

order_items
order 1 → 3 items
order 2 → 2 items
```

Joining orders to items creates:

```text
100
100
100
200
200
```

If you calculate:

```sql
SUM(o.total_amount)
```

after that join, you can get:

```text
700
```

instead of:

```text
300
```

The join changed the grain before aggregation.

---

## Preventing Join-Induced Double Counting

Possible approaches include:

- Aggregate before joining
- Aggregate the more granular relation separately
- Use `EXISTS` when only existence is required
- Use `DISTINCT` only when semantically appropriate
- Define the measure's grain explicitly

Example:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    c.id,
    cr.revenue
FROM customers AS c
LEFT JOIN customer_revenue AS cr
    ON cr.customer_id = c.id;
```

The revenue is calculated at customer grain before the later join.

---

## `SUM(DISTINCT ...)` Is Not a General Fix

A common attempted fix is:

```sql
SUM(DISTINCT o.total_amount)
```

This can be incorrect.

Suppose two legitimate orders both have:

```text
total_amount = 100
```

`SUM(DISTINCT total_amount)` counts only one of them.

Therefore `DISTINCT` must be applied to the correct entity identity, not blindly to a measure.

---

## Aggregating at Different Grains

Consider:

```text
order
  ↓
order item
  ↓
product
```

Possible grains include:

```text
one row per order
one row per order item
one row per product
one row per customer
one row per customer per month
```

A senior SQL engineer explicitly tracks grain through every query stage.

This prevents:

- Double counting
- Missing rows
- Incorrect averages
- Incorrect pagination
- Incorrect dashboards

---

## Weighted vs Unweighted Average

Suppose two stores have:

```text
Store A: 100 orders, average $100
Store B: 10 orders, average $200
```

The average of store averages is:

```text
($100 + $200) / 2 = $150
```

But the actual order-level average is:

```text
(100 × 100 + 10 × 200) / 110
= $109.09
```

Therefore:

> Never average averages unless the weighting semantics are correct.

---

## Average From SUM and COUNT

Sometimes it is useful to reason about averages as:

```text
SUM(value) / COUNT(value)
```

For example:

```sql
SELECT
    SUM(total_amount) / NULLIF(COUNT(total_amount), 0)
FROM orders;
```

This makes the denominator explicit.

`AVG` is usually clearer, but understanding the underlying arithmetic helps when combining aggregates from different groups.

---

## `NULLIF` in Aggregation

To avoid division by zero:

```sql
SELECT
    SUM(total_amount)
    / NULLIF(COUNT(*), 0) AS average_amount
FROM orders;
```

`NULLIF(x, 0)` returns `NULL` when `x` is zero.

This is useful in calculated metrics.

---

## `COALESCE` in Aggregation

For application-facing metrics:

```sql
SELECT
    COALESCE(SUM(total_amount), 0) AS revenue
FROM orders
WHERE status = 'paid';
```

This converts a `NULL` aggregate result into zero.

Whether zero or `NULL` is the correct business meaning should be decided explicitly.

---

## `GROUP BY` and Functional Dependency

PostgreSQL can sometimes allow selecting columns that are functionally dependent on grouped columns.

For example, if a grouped column is a primary key, related non-grouped columns may sometimes be accepted because the database knows the dependency.

However, writing explicit grouping is often clearer for portable SQL and future schema changes.

Do not rely on obscure functional-dependency behavior in interview answers unless the question specifically tests it.

---

## `GROUP BY` and `SELECT`

In standard SQL, selected non-aggregate expressions generally need to be represented in the grouping criteria.

For example:

```sql
SELECT
    customer_id,
    status,
    COUNT(*)
FROM orders
GROUP BY customer_id, status;
```

This is valid.

But:

```sql
SELECT
    customer_id,
    status,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

is generally invalid because multiple statuses could exist for one customer.

The database cannot know which status should be returned.

---

## `GROUP BY` and Expressions

If selecting:

```sql
DATE(created_at)
```

the query can group by the same expression:

```sql
SELECT
    DATE(created_at) AS order_date,
    COUNT(*) AS order_count
FROM orders
GROUP BY DATE(created_at);
```

Some SQL dialects provide alias-based grouping behavior, but explicit expressions are more portable and clear.

---

## Aggregation With `DISTINCT`

Example:

```sql
SELECT
    COUNT(DISTINCT customer_id)
FROM orders
WHERE status = 'paid';
```

This is useful for:

> Number of unique customers with paid orders.

Be careful with:

```sql
COUNT(DISTINCT ...)
```

on very large datasets because deduplication can require significant memory or sorting/hashing work.

---

## Multiple `COUNT(DISTINCT ...)`

A query such as:

```sql
SELECT
    COUNT(DISTINCT customer_id),
    COUNT(DISTINCT product_id)
FROM order_items;
```

may require separate distinct-processing work for each aggregate.

At high scale, approximate or pre-aggregated analytics techniques may be more appropriate depending on accuracy requirements.

---

## `HAVING` With Multiple Conditions

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10
   AND SUM(total_amount) >= 5000;
```

This returns customers satisfying both aggregate conditions.

---

## `HAVING` vs `WHERE` Interview Question

Question:

> Find customers with at least five paid orders.

Correct:

```sql
SELECT
    customer_id,
    COUNT(*) AS paid_orders
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 5;
```

Why?

```text
WHERE → selects paid order rows
GROUP BY → forms customer groups
COUNT → calculates group metric
HAVING → filters groups
```

---

## Aggregation With `ORDER BY`

You can order aggregate results:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
ORDER BY revenue DESC;
```

Ordering by the aggregate alias is supported in PostgreSQL.

For deterministic ordering when ties matter:

```sql
ORDER BY revenue DESC, customer_id;
```

---

## Top Customers

A typical business query:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
ORDER BY revenue DESC
LIMIT 10;
```

This finds the ten highest-revenue customers among paid orders.

The database still has to compute the relevant groups before determining the top results unless the planner can exploit a different structure.

---

## Top-N Per Group

Suppose you need:

> Top three orders for each customer.

A regular `GROUP BY` is not sufficient because you need individual rows ranked within each group.

Use a window function:

```sql
SELECT *
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS rn
    FROM orders AS o
) AS ranked
WHERE rn <= 3;
```

This is a common interview distinction:

- `GROUP BY` reduces rows into groups.
- Window functions calculate across groups while retaining row-level results.

---

## Aggregation vs Window Functions

Compare:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

with:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM orders;
```

The first returns:

```text
one row per customer
```

The second returns:

```text
one row per order
```

with the customer-level aggregate attached to each row.

---

## Running Totals

Window functions can calculate cumulative aggregates:

```sql
SELECT
    id,
    created_at,
    total_amount,
    SUM(total_amount) OVER (
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_revenue
FROM orders
ORDER BY created_at, id;
```

This is different from `GROUP BY` because rows are retained.

---

## Aggregation With Window Functions After GROUP BY

You can aggregate first and then apply a window function.

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue,
    SUM(SUM(total_amount)) OVER () AS total_revenue
FROM orders
GROUP BY customer_id;
```

The inner `SUM` creates customer-level revenue.

The windowed `SUM` then calculates the total across those grouped results.

---

## `ROLLUP`

PostgreSQL supports grouping extensions such as `ROLLUP`.

Example:

```sql
SELECT
    customer_id,
    status,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY ROLLUP (customer_id, status);
```

This can produce:

```text
customer + status
customer subtotal
grand total
```

It is useful for reporting queries that require hierarchical subtotals.

---

## `CUBE`

PostgreSQL also supports `CUBE`:

```sql
SELECT
    customer_id,
    status,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY CUBE (customer_id, status);
```

This produces aggregates across combinations of the grouping dimensions.

The number of generated grouping combinations can grow quickly, so use it carefully on large datasets.

---

## `GROUPING SETS`

`GROUPING SETS` provides explicit grouping combinations.

```sql
SELECT
    customer_id,
    status,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY GROUPING SETS (
    (customer_id),
    (status),
    ()
);
```

This can calculate:

- Revenue per customer
- Revenue per status
- Grand total

in one query.

---

## Identifying Rollup Rows

When using grouping extensions, PostgreSQL provides:

```sql
GROUPING(column)
```

to identify whether a column represents a subtotal/grand-total row rather than an ordinary grouped value.

This is useful when building reporting APIs or exporting analytical results.

---

## Aggregation Performance

Aggregation can use different physical strategies.

PostgreSQL commonly uses:

```text
HashAggregate
GroupAggregate
```

depending on the query and planner estimates.

### Hash Aggregate

Conceptually:

```text
input rows
   ↓
hash group key
   ↓
aggregate state per group
```

### Group Aggregate

Conceptually:

```text
sorted/grouped input
        ↓
aggregate each group
```

The planner chooses based on estimated costs and available resources.

---

## Hash Aggregation and Memory

A query with millions of groups can require significant memory.

Example:

```sql
SELECT
    unique_key,
    COUNT(*)
FROM very_large_table
GROUP BY unique_key;
```

If the aggregation cannot remain within available memory, PostgreSQL may use disk-based batching or spilling behavior.

Large aggregation workloads should therefore be evaluated using:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and production resource metrics.

---

## Aggregation and Sorting

Some aggregation strategies require sorted input.

Sorting large datasets can consume:

- CPU
- Memory
- Temporary disk
- I/O

A query that appears simple:

```sql
GROUP BY customer_id
ORDER BY SUM(total_amount) DESC;
```

may require substantial work when there are millions of customers.

---

## Aggregation and Indexes

An index does not automatically make aggregation fast.

For:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

PostgreSQL may still prefer a sequential scan because a large portion of the table must be read.

Indexes become more useful when combined with selective filtering or when they support a useful access pattern.

---

## Aggregation With Selective Filtering

Consider:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
WHERE tenant_id = $1
  AND status = 'paid'
GROUP BY customer_id;
```

An index such as:

```sql
CREATE INDEX idx_orders_tenant_status_customer
ON orders (
    tenant_id,
    status,
    customer_id
);
```

may help reduce the input set.

The exact index should be validated against the workload and execution plan.

---

## Aggregation and Partial Indexes

If the workload frequently aggregates only active records:

```sql
SELECT
    customer_id,
    COUNT(*)
FROM orders
WHERE deleted_at IS NULL
GROUP BY customer_id;
```

a partial index can sometimes reduce the indexed data:

```sql
CREATE INDEX idx_orders_active_customer
ON orders (customer_id)
WHERE deleted_at IS NULL;
```

Whether this improves the query depends on selectivity, table size, and the chosen plan.

---

## Aggregation and Partitioning

Large time-series tables may be partitioned by date:

```text
orders
├── 2026-01
├── 2026-02
├── 2026-03
└── ...
```

A bounded query:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

can allow partition pruning.

This reduces the amount of data participating in the aggregation.

Partitioning is not automatically an aggregation optimization; it is most useful when the partition key aligns with common filtering patterns and lifecycle requirements.

---

## Aggregation on OLTP Databases

Simple aggregates are normal OLTP operations:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = $1;
```

But large analytical aggregation can interfere with transactional workloads.

For example:

```text
OLTP PostgreSQL
    ├── API transactions
    ├── background jobs
    └── billion-row analytics query
```

The analytical workload can consume:

- CPU
- Memory
- I/O
- Connections

At scale, isolate analytical workloads using:

- Read replicas
- Materialized views
- Warehouses
- OLAP systems
- CDC pipelines

---

## Materialized Views for Repeated Aggregation

If a dashboard repeatedly calculates:

```sql
SELECT
    date,
    SUM(revenue)
FROM events
GROUP BY date;
```

a materialized view can precompute the result.

Conceptually:

```text
Raw events
    ↓
Aggregation
    ↓
Materialized view
    ↓
Dashboard
```

The trade-off is freshness and refresh cost.

---

## Aggregation and Caching

Redis can cache expensive aggregate results:

```text
PostgreSQL
    ↓
aggregate
    ↓
Redis
    ↓
API
```

But cached metrics introduce invalidation and freshness concerns.

For rapidly changing financial or transactional values, do not blindly cache without defining acceptable staleness.

---

## Aggregation in Django

Django provides aggregation APIs:

```python
from django.db.models import Count, Sum

result = (
    Order.objects
    .filter(status="paid")
    .values("customer_id")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("total_amount"),
    )
)
```

Conceptually:

```sql
SELECT
    customer_id,
    COUNT(id),
    SUM(total_amount)
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;
```

The generated SQL should still be understood and reviewed for important workloads.

---

## Django `annotate()` vs `aggregate()`

`aggregate()` produces a summary over the entire queryset:

```python
Order.objects.filter(status="paid").aggregate(
    revenue=Sum("total_amount")
)
```

`annotate()` attaches aggregate values to grouped/queryset results:

```python
Order.objects.values("customer_id").annotate(
    revenue=Sum("total_amount")
)
```

Understanding the resulting SQL is more important than memorizing the ORM method names.

---

## Django Aggregation and JOIN Multiplication

ORM relationship traversal can introduce joins.

For example:

```python
Customer.objects.annotate(
    order_count=Count("orders")
)
```

is generally straightforward.

But when combining multiple one-to-many relationships in one query, aggregates can multiply each other.

For complex annotations, inspect the generated SQL and validate counts against known data.

---

## Django `Count(..., distinct=True)`

Django supports:

```python
Count("orders", distinct=True)
```

when distinct counting is actually required.

However, `distinct=True` should not automatically be used to hide incorrect join cardinality.

First determine why the join multiplies rows.

---

## FastAPI and SQLAlchemy Aggregation

SQLAlchemy:

```python
stmt = (
    select(
        Order.customer_id,
        func.count(Order.id).label("order_count"),
        func.sum(Order.total_amount).label("revenue"),
    )
    .where(Order.status == "paid")
    .group_by(Order.customer_id)
)
```

The generated SQL is still executed by PostgreSQL.

For high-volume endpoints, inspect:

- Query plan
- Number of groups
- Response size
- Execution time
- Connection duration

---

## Aggregation in API Design

A REST endpoint such as:

```text
GET /customers/{id}/metrics
```

might return:

```json
{
  "order_count": 125,
  "paid_revenue": 18250.50,
  "average_order_value": 146.00
}
```

The backend can calculate these metrics with one carefully designed aggregate query rather than fetching all orders into Python.

This reduces:

- Network transfer
- Application memory
- Python CPU
- Serialization work

---

## Aggregation and Pagination

Aggregation results can themselves be paginated.

Example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
ORDER BY revenue DESC, customer_id
LIMIT 50;
```

For deep pagination of aggregated results, standard offset pagination can still become expensive because the database must identify and order grouped results.

At large scale, precomputed ranking/read models may be more appropriate.

---

## Aggregation and Background Jobs

Large reports should often be asynchronous.

Architecture:

```text
API
 ↓
create report job
 ↓
Celery
 ↓
PostgreSQL / OLAP
 ↓
generate report
 ↓
S3 / object storage
 ↓
client notification
```

This prevents a long-running aggregation from consuming an API request connection indefinitely.

---

## Aggregation and Kafka

Kafka can provide an event stream for incremental aggregation:

```text
Application
    ↓
Kafka
    ↓
Consumer
    ↓
Aggregate state
    ↓
Read model
```

For high-volume metrics, this can avoid repeatedly scanning the entire transactional table.

The trade-offs include:

- Eventual consistency
- Ordering requirements
- Duplicate events
- Reprocessing
- State recovery

---

## Incremental Aggregation

Instead of:

```text
scan 1 billion rows
→ calculate total
```

a system can maintain:

```text
current aggregate
+
new events
→
updated aggregate
```

This is useful for high-volume dashboards and counters.

However, the system must define how to handle:

- Corrections
- Duplicate events
- Late events
- Backfills
- Replays
- Failed consumers

---

## Aggregation Correctness With Eventual Consistency

A Kafka-backed aggregate may temporarily differ from the transactional database.

Therefore API contracts should define whether a metric is:

```text
strongly consistent
eventually consistent
approximately consistent
```

Do not present eventually consistent metrics as authoritative transactional values without qualification.

---

## Security and Aggregation

Aggregation can leak information even when individual records are not exposed.

For example:

```sql
SELECT
    COUNT(*)
FROM confidential_records
WHERE department = $1;
```

A user might infer sensitive information from the count.

Security controls should apply to aggregate queries as well:

- Authorization
- Tenant isolation
- RLS
- Role permissions
- Data classification
- Query scope

---

## Multi-Tenant Aggregation

A tenant-scoped metric should include the tenant boundary:

```sql
SELECT
    COUNT(*),
    SUM(total_amount)
FROM orders
WHERE tenant_id = $1
  AND status = 'paid';
```

If RLS is used, the database can provide an additional enforcement layer.

Never assume that an aggregate is safe merely because it does not return individual records.

---

## Aggregation and High Availability

For aggregate queries routed to replicas:

```text
Primary
   ↓
WAL
   ↓
Read Replica
   ↓
Reporting query
```

the result can lag behind the primary.

For dashboards, this may be acceptable.

For transactional decisions such as:

> "Does this account have enough balance?"

a stale replica aggregate may be unsafe.

---

## Aggregation and Disaster Recovery

If important reports are generated from transactional data:

- Ensure source data is backed up
- Test recovery
- Understand replica lag
- Preserve event streams where needed
- Define whether aggregate tables can be rebuilt
- Document recomputation procedures

Derived aggregates should generally be treated as rebuildable when the source of truth is preserved.

---

## Common Aggregation Mistakes

### Using `COUNT(column)` When You Need Row Count

Wrong:

```sql
COUNT(customer_id)
```

when `customer_id` can be `NULL`.

Use:

```sql
COUNT(*)
```

for row count.

### Using `COUNT(*)` With LEFT JOIN

This can count the preserved parent row rather than matching children.

Use:

```sql
COUNT(child.id)
```

when counting children.

### Using `DISTINCT` to Hide Join Problems

Fix the relationship or aggregation grain instead.

### Summing After a Multiplying JOIN

Aggregate at the measure's natural grain first.

### Averaging Averages

Use correct weighting.

### Using `WHERE` for Aggregate Conditions

Use `HAVING`.

### Ignoring NULL

`NULL` affects counts, sums, averages, and comparisons.

### Aggregating Entire OLTP Tables for Every Dashboard Request

Precompute or isolate analytical workloads when necessary.

---

## Interview Traps

### What Is the Difference Between `WHERE` and `HAVING`?

`WHERE` filters rows before grouping.

`HAVING` filters groups after aggregation.

---

### What Is the Difference Between `COUNT(*)` and `COUNT(column)`?

`COUNT(*)` counts qualifying rows.

`COUNT(column)` counts only non-null values.

---

### Does `COUNT(*)` Count NULL Rows?

Yes.

A row is counted regardless of whether its columns contain `NULL`.

---

### Does `SUM()` Treat NULL as Zero?

`SUM()` ignores null inputs, but if no non-null input values exist, the aggregate result can be `NULL`.

Use `COALESCE` when zero is the intended result.

---

### Does `AVG()` Treat NULL as Zero?

No.

`AVG()` ignores `NULL` values.

---

### Why Can a JOIN Make `SUM()` Incorrect?

A one-to-many join can repeat an order-level measure once for every child row.

The aggregate then sums the repeated values.

---

### Why Not Use `SUM(DISTINCT amount)`?

Because two legitimate entities can have the same amount.

Distinctness must be applied to the correct entity or aggregation grain.

---

### Can You Use Aggregate Functions in `WHERE`?

Not directly in the same query level.

Use `HAVING`, a subquery, or a CTE depending on the requirement.

---

### Can You Use Aggregate Results in `ORDER BY`?

Yes.

Example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
ORDER BY revenue DESC;
```

---

### Does `GROUP BY` Always Sort Results?

No.

Grouping and ordering are separate concerns.

If output order matters, use:

```sql
ORDER BY
```

explicitly.

---

### Is `GROUP BY` Always Faster Than Application-Side Aggregation?

Usually database-side aggregation avoids transferring and processing large raw datasets in the application, but actual performance depends on workload and architecture.

For very large analytical workloads, a dedicated OLAP system may be more appropriate than either approach.

---

### Is an Index Always Used for `GROUP BY`?

No.

If most rows must be scanned, a sequential scan followed by hash or sort-based aggregation may be cheaper.

---

## Practical Interview Problems

### Find Total Revenue Per Customer

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;
```

---

### Find Customers With Revenue Above 10,000

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total_amount) > 10000;
```

---

### Count Orders Per Status

```sql
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY status;
```

---

### Count Unique Customers With Paid Orders

```sql
SELECT
    COUNT(DISTINCT customer_id) AS customer_count
FROM orders
WHERE status = 'paid';
```

---

### Find Average Order Value Per Customer

```sql
SELECT
    customer_id,
    AVG(total_amount) AS average_order_value
FROM orders
GROUP BY customer_id;
```

---

### Find Customers With At Least Five Orders

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 5;
```

---

### Count Orders Including Customers With Zero Orders

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

---

### Calculate Paid and Cancelled Orders in One Query

PostgreSQL:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'paid'
    ) AS paid_orders,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders
FROM orders;
```

---

### Calculate Revenue Per Day

```sql
SELECT
    DATE(created_at) AS order_date,
    SUM(total_amount) AS revenue
FROM orders
WHERE created_at >= $1
  AND created_at < $2
GROUP BY DATE(created_at)
ORDER BY order_date;
```

---

### Find the Highest-Spending Customer

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
ORDER BY revenue DESC, customer_id
LIMIT 1;
```

---

### Find Customers With Both Paid and Cancelled Orders

```sql
SELECT
    customer_id
FROM orders
GROUP BY customer_id
HAVING COUNT(*) FILTER (
           WHERE status = 'paid'
       ) > 0
   AND COUNT(*) FILTER (
           WHERE status = 'cancelled'
       ) > 0;
```

---

## Aggregation Debugging Workflow

When an aggregate result looks wrong:

### Define the Expected Grain

Ask:

```text
One row per what?
```

### Validate the Base Row Count

```sql
SELECT COUNT(*)
FROM orders;
```

### Inspect the JOIN

```sql
SELECT COUNT(*)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

### Compare Before and After Aggregation

```sql
SELECT
    customer_id,
    COUNT(*) AS rows
FROM orders
GROUP BY customer_id;
```

Then repeat after every additional join.

### Validate Against Known Data

Take a small set of entities and manually verify the metric.

### Inspect the Execution Plan

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
GROUP BY customer_id;
```

---

## Senior Aggregation Reasoning Framework

When solving an aggregation interview problem:

```text
Define business metric
        ↓
Define result grain
        ↓
Define input rows
        ↓
Apply row-level filters
        ↓
Check NULL semantics
        ↓
Identify joins
        ↓
Check cardinality multiplication
        ↓
Choose aggregate
        ↓
GROUP BY required dimensions
        ↓
Apply HAVING
        ↓
Order / limit if required
        ↓
Validate correctness
        ↓
Inspect performance
```

This framework prevents most aggregation mistakes.

---

## Production Aggregation Checklist

Before shipping an aggregate query:

- [ ] Result grain is explicitly defined.
- [ ] `NULL` semantics are intentional.
- [ ] `COUNT(*)` vs `COUNT(column)` is correct.
- [ ] Joins do not multiply measures unexpectedly.
- [ ] `SUM(DISTINCT ...)` is not being used as a generic duplicate fix.
- [ ] `WHERE` and `HAVING` are used for the correct stages.
- [ ] Timezone semantics are explicit.
- [ ] Tenant boundaries are enforced.
- [ ] Authorization applies to aggregate results.
- [ ] Result size is bounded where appropriate.
- [ ] Query frequency is known.
- [ ] Execution plan has been reviewed for expensive workloads.
- [ ] Memory and temporary I/O are understood.
- [ ] OLTP and OLAP workloads are separated when necessary.
- [ ] Derived aggregates have a defined freshness model.
- [ ] Recovery/recomputation strategy exists for important derived data.

---

## Key Takeaways

- **Aggregation is fundamentally about grain:** define what one output row represents before choosing `GROUP BY`, joins, or aggregate functions.
- **`NULL` and join cardinality are the major correctness traps:** understand `COUNT(*)`, `COUNT(column)`, aggregate `NULL` behavior, and how one-to-many joins can multiply measures.
- **Use `WHERE` before grouping and `HAVING` after grouping:** row-level predicates and group-level predicates solve different problems and should be placed accordingly.
- **Aggregation performance depends on workload:** indexes, filtering, group cardinality, memory, sorting, partitioning, query frequency, and OLTP/OLAP separation all matter.
- **Senior aggregation design includes architecture:** consider tenant isolation, authorization, replicas, caching, materialized views, asynchronous reporting, Kafka-based projections, freshness, and recovery of derived metrics.