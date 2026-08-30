# 15- Common Aggregation Patterns

## Overview

Aggregation is one of the primary ways SQL converts detailed transactional data into business-level metrics. In backend systems, common aggregation patterns appear in dashboards, reporting APIs, billing, operational monitoring, analytics, and data-quality checks.

The core idea is to define:

- **Input population** — which rows participate.
- **Input grain** — what one row represents.
- **Grouping grain** — what one output row represents.
- **Metric** — what is being calculated.
- **NULL semantics** — whether missing values should be ignored, preserved, or converted.
- **Join cardinality** — whether joins can multiply rows before aggregation.

A reliable aggregation query can be viewed as:

```text
Raw rows
   ↓
Filter population
   ↓
Join required data
   ↓
Control row cardinality
   ↓
Group into required grain
   ↓
Calculate aggregates
   ↓
Filter groups with HAVING
   ↓
Return application/reporting result
```

## Core Aggregation Patterns

| Pattern | Typical SQL | Typical use |
|---|---|---|
| Total | `SUM(amount)` | Revenue, units, usage |
| Row count | `COUNT(*)` | Orders, events |
| Non-NULL count | `COUNT(column)` | Records with a value |
| Unique count | `COUNT(DISTINCT column)` | Customers, devices |
| Average | `AVG(value)` | Average order value |
| Minimum | `MIN(value)` | Earliest event, lowest price |
| Maximum | `MAX(value)` | Latest event, highest value |
| Grouped metrics | `GROUP BY ...` | Metrics per customer/region |
| Conditional metrics | `FILTER` / `CASE` | Paid vs failed operations |
| Group filtering | `HAVING` | Customers above a threshold |
| First/last row | `ORDER BY ... LIMIT 1` | Retrieve complete record |
| Top-N per group | Window functions | Best product per category |
| Running aggregate | Window functions | Cumulative revenue |

## Basic Metric Aggregation

Assume an `orders` table:

```text
orders
------
id
customer_id
status
total_amount
created_at
```

A basic reporting query might calculate several metrics together:

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order_value,
    MIN(total_amount) AS minimum_order_value,
    MAX(total_amount) AS maximum_order_value
FROM orders
WHERE status = 'paid';
```

The query returns one row because there is no `GROUP BY`.

The result represents the entire filtered population.

### Production Consideration

Do not calculate these metrics in application code by loading all matching rows:

```python
orders = load_all_paid_orders()

order_count = len(orders)
revenue = sum(order.total_amount for order in orders)
```

For large datasets this unnecessarily transfers rows from the database to the application and consumes application memory.

Prefer set-based aggregation in SQL:

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid';
```

## Aggregation by Entity

A common backend pattern is calculating metrics for every entity.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order_value
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;
```

The output grain is:

```text
one row per customer
```

This is useful for:

- Customer dashboards
- Account summaries
- Billing reports
- Customer segmentation
- Operational metrics

The database performs the aggregation before returning the result set.

## Multiple Grouping Dimensions

Aggregation can use more than one grouping column.

```sql
SELECT
    customer_id,
    status,
    COUNT(*) AS order_count,
    SUM(total_amount) AS amount
FROM orders
GROUP BY customer_id, status;
```

The output grain becomes:

```text
one row per (customer, status)
```

These are different metrics:

```sql
GROUP BY customer_id
```

versus:

```sql
GROUP BY customer_id, status
```

The second query produces a more detailed result.

### Grain Rule

Before writing `GROUP BY`, state the intended output in plain language:

> One row per customer.

or:

> One row per customer and order status.

If the output grain cannot be clearly stated, the query is not ready to be written.

## Time-Based Aggregation

Time-based aggregation is common in operational and product reporting.

For PostgreSQL:

```sql
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day;
```

This produces:

```text
day         order_count    revenue
----------  ------------   -------
2026-08-01       120       ...
2026-08-02       143       ...
2026-08-03       137       ...
```

### Why Half-Open Time Ranges Matter

Prefer:

```sql
created_at >= :start_time
AND created_at < :end_time
```

over:

```sql
created_at BETWEEN :start_time AND :end_time
```

for most time-window queries.

Half-open intervals compose cleanly:

```text
[2026-08-01 00:00, 2026-08-02 00:00)
[2026-08-02 00:00, 2026-08-03 00:00)
```

There is no ambiguity about whether the boundary timestamp belongs to both periods.

## Conditional Aggregation

Conditional aggregation calculates multiple subsets of metrics in one query.

In PostgreSQL:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'paid') AS paid_orders,
    COUNT(*) FILTER (WHERE status = 'pending') AS pending_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders,
    SUM(total_amount) FILTER (WHERE status = 'paid') AS paid_revenue
FROM orders;
```

This is useful for dashboards where several related metrics are derived from the same population.

A portable alternative uses `CASE`:

```sql
SELECT
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_orders,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_orders,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(
        CASE
            WHEN status = 'paid' THEN total_amount
            ELSE 0
        END
    ) AS paid_revenue
FROM orders;
```

### Advantages

- Multiple metrics can be computed together.
- Reduces application-side processing.
- Clearly expresses metric definitions.
- Often avoids separate queries for closely related metrics.

### Production Considerations

Make sure each conditional metric has explicitly defined semantics.

For example:

```sql
SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END)
```

means that non-paid rows contribute zero.

That is different from simply aggregating:

```sql
SUM(total_amount)
```

over all rows.

## Counting Boolean Conditions

Conditional counts are frequently used for operational metrics.

```sql
SELECT
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE status_code < 400) AS successful_requests,
    COUNT(*) FILTER (WHERE status_code >= 500) AS server_errors
FROM api_requests
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

From these values, an application can calculate:

```text
success rate
5xx rate
total request volume
```

For ratios, protect against division by zero:

```sql
SELECT
    COUNT(*) AS total_requests,
    COUNT(*) FILTER (WHERE status_code < 400) AS successful_requests,
    100.0
        * COUNT(*) FILTER (WHERE status_code < 400)
        / NULLIF(COUNT(*), 0) AS success_rate
FROM api_requests
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

`NULLIF` prevents a division-by-zero error.

## Aggregation With HAVING

`WHERE` filters rows before aggregation.

`HAVING` filters groups after aggregation.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total_amount) >= 10000;
```

The processing conceptually looks like:

```text
orders
  ↓
WHERE status = 'paid'
  ↓
GROUP BY customer_id
  ↓
SUM / COUNT
  ↓
HAVING revenue >= 10000
  ↓
result
```

Use `WHERE` whenever the condition applies to individual rows.

Use `HAVING` when the condition depends on an aggregate or group.

## Top-N Aggregation

A common requirement is:

> Which customers generated the most revenue?

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

The database:

1. Filters orders.
2. Groups by customer.
3. Calculates revenue.
4. Sorts groups by revenue.
5. Returns the top 10.

This is appropriate when the requirement is a global top-N list.

## Top-N Per Group

The requirement changes when the question becomes:

> What are the top 3 products in each category?

`LIMIT` alone cannot solve this because it limits the entire result.

A window function can rank rows within each category:

```sql
WITH product_sales AS (
    SELECT
        category_id,
        product_id,
        SUM(quantity) AS units_sold
    FROM order_items
    GROUP BY category_id, product_id
),
ranked AS (
    SELECT
        category_id,
        product_id,
        units_sold,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY units_sold DESC, product_id
        ) AS rank
    FROM product_sales
)
SELECT
    category_id,
    product_id,
    units_sold
FROM ranked
WHERE rank <= 3
ORDER BY category_id, rank;
```

This pattern separates:

```text
aggregate first
     ↓
rank within group
     ↓
filter ranked rows
```

Use `RANK()` or `DENSE_RANK()` instead of `ROW_NUMBER()` when ties should receive the same rank.

## Distinct Counts

Unique counts are common in product analytics.

```sql
SELECT
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

For grouped unique counts:

```sql
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(DISTINCT customer_id) AS daily_active_customers
FROM orders
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day;
```

### Production Considerations

`COUNT(DISTINCT ...)` can be substantially more expensive than `COUNT(*)`, especially with large datasets and high-cardinality values.

For very large analytics workloads, approximate distinct-count techniques or pre-aggregated structures may be appropriate, depending on the accuracy requirements.

Do not replace exact metrics with approximate metrics unless the business requirement permits it.

## Aggregating After a One-to-Many Join

Consider:

```text
customers
    │
    └── orders
```

A straightforward aggregate is:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS revenue
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

The `LEFT JOIN` preserves customers without orders.

`COUNT(o.id)` returns zero for those customers because `o.id` is NULL on the generated outer-join row.

This is preferable to:

```sql
COUNT(*)
```

when the requirement is specifically the number of matching orders.

With `COUNT(*)`, a customer with no matching orders still has one output row generated by the outer join, causing the count to be `1`.

## Avoiding Join Multiplication

Suppose a customer has:

```text
3 orders
4 support tickets
```

Joining both one-to-many relationships directly can produce:

```text
3 × 4 = 12 rows
```

before aggregation.

This can make:

```sql
SUM(order_amount)
```

incorrect.

A safer pattern is to aggregate each relationship independently:

```sql
WITH order_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
),
ticket_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
)
SELECT
    c.id,
    COALESCE(o.order_count, 0) AS order_count,
    COALESCE(o.revenue, 0) AS revenue,
    COALESCE(t.ticket_count, 0) AS ticket_count
FROM customers AS c
LEFT JOIN order_metrics AS o
    ON o.customer_id = c.id
LEFT JOIN ticket_metrics AS t
    ON t.customer_id = c.id;
```

This preserves the intended grain:

```text
one row per customer
```

for each intermediate aggregate.

## Aggregating Child Rows Into Parent Metrics

A common API requirement is:

> Return each customer with their order metrics.

The relational approach is:

```text
orders
  ↓
aggregate by customer_id
  ↓
customer metrics
  ↓
join to customers
```

For example:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS lifetime_value,
    MAX(o.created_at) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id, c.email;
```

This can provide a compact result to a REST or gRPC service without returning every underlying order.

## Aggregation With NULL

Aggregates have different NULL semantics.

| Expression | Typical behavior with NULL |
|---|---|
| `COUNT(*)` | Counts the row |
| `COUNT(column)` | Ignores NULL |
| `COUNT(DISTINCT column)` | Ignores NULL |
| `SUM(column)` | Ignores NULL |
| `AVG(column)` | Ignores NULL |
| `MIN(column)` | Ignores NULL |
| `MAX(column)` | Ignores NULL |

Example:

```sql
SELECT
    COUNT(*) AS rows,
    COUNT(discount) AS rows_with_discount,
    SUM(discount) AS total_discount,
    AVG(discount) AS average_discount
FROM orders;
```

Do not assume:

```text
NULL = 0
```

A NULL value often means:

```text
unknown
not recorded
not applicable
```

while zero means:

```text
known quantity of zero
```

Use `COALESCE` only when converting NULL to zero is semantically correct:

```sql
COALESCE(SUM(discount), 0)
```

## Conditional Aggregation by Group

Combining `GROUP BY` with conditional aggregation is one of the most useful reporting patterns.

```sql
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'paid') AS paid_orders,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_orders,
    COALESCE(
        SUM(total_amount) FILTER (WHERE status = 'paid'),
        0
    ) AS paid_revenue
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day;
```

This produces a compact time-series result suitable for dashboards.

## Percentage and Ratio Metrics

Ratios should be calculated carefully.

For example, calculate payment success rate:

```sql
SELECT
    COUNT(*) AS total_payments,
    COUNT(*) FILTER (WHERE status = 'succeeded') AS successful_payments,
    100.0
        * COUNT(*) FILTER (WHERE status = 'succeeded')
        / NULLIF(COUNT(*), 0) AS success_rate
FROM payments
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

Important considerations:

- Use a decimal-compatible expression when fractional results are required.
- Prevent division by zero with `NULLIF`.
- Define whether retries count as separate attempts.
- Define whether the denominator represents requests, attempts, or unique transactions.

A mathematically correct SQL expression can still represent the wrong business metric if the denominator is wrong.

## Weighted Average

When groups have different sizes, an average of averages can be incorrect.

Suppose daily metrics are stored as:

```text
day         order_count    revenue
----------  -----------    -------
day 1           10           1000
day 2          100           5000
```

The overall average order value is:

```sql
SELECT
    SUM(revenue) / NULLIF(SUM(order_count), 0) AS average_order_value
FROM daily_metrics;
```

Do not calculate:

```sql
AVG(revenue / order_count)
```

unless the business definition specifically calls for an unweighted average of daily averages.

The correct aggregation depends on the mathematical meaning of the metric.

## First and Last Activity Patterns

If only the timestamp is required:

```sql
SELECT
    customer_id,
    MIN(created_at) AS first_order_at,
    MAX(created_at) AS last_order_at
FROM orders
GROUP BY customer_id;
```

If the complete latest order is required, `MAX(created_at)` is insufficient because it does not identify the row.

A PostgreSQL-specific solution is:

```sql
SELECT DISTINCT ON (customer_id)
    customer_id,
    id,
    created_at,
    total_amount
FROM orders
ORDER BY customer_id, created_at DESC, id DESC;
```

Another portable approach uses `ROW_NUMBER()`:

```sql
WITH ranked_orders AS (
    SELECT
        customer_id,
        id,
        created_at,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS row_num
    FROM orders
)
SELECT
    customer_id,
    id,
    created_at,
    total_amount
FROM ranked_orders
WHERE row_num = 1;
```

The secondary `id` ordering makes tie handling deterministic.

## Aggregating Events

Event tables are common in backend systems:

```text
api_requests
payments
audit_events
user_events
kafka-consumed events
```

A typical operational query might calculate event volume:

```sql
SELECT
    service_name,
    event_type,
    COUNT(*) AS event_count,
    MIN(created_at) AS first_event_at,
    MAX(created_at) AS last_event_at
FROM events
WHERE created_at >= :start_time
  AND created_at < :end_time
GROUP BY service_name, event_type;
```

This can support operational dashboards and anomaly investigation.

For very high-volume event tables, repeatedly scanning raw events may become expensive. At that point, consider partitioning, pre-aggregation, materialized views, or moving analytical workloads to an appropriate analytics platform.

## Aggregation in Django

Django's ORM maps common SQL aggregation patterns to `Count`, `Sum`, `Avg`, `Min`, and `Max`.

For example:

```python
from django.db.models import Avg, Count, Max, Sum

metrics = (
    Order.objects
    .filter(status="paid")
    .values("customer_id")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("total_amount"),
        average_order_value=Avg("total_amount"),
        last_order_at=Max("created_at"),
    )
)
```

For production systems, understand the SQL generated by the ORM.

Be especially careful when aggregating across multiple relationships:

```python
Count("orders")
Count("support_tickets")
Sum("orders__total_amount")
```

A complex ORM expression can produce joins with the same cardinality problems as handwritten SQL.

When correctness or performance is uncertain, inspect the generated SQL and execution plan.

## Performance Considerations

Aggregation performance depends heavily on the amount and shape of data entering the aggregate.

Important factors include:

| Factor | Impact |
|---|---|
| Filter selectivity | Reduces rows entering aggregation |
| Number of groups | More groups require more state |
| Join cardinality | Can multiply input rows |
| `COUNT(DISTINCT ...)` | Can require substantial memory/work |
| Sort requirements | Can increase CPU and I/O |
| Hash aggregation | Can consume significant memory |
| Table size | Determines scan cost |
| Partition pruning | Can avoid irrelevant partitions |
| Data skew | Can affect parallel execution and memory use |

For PostgreSQL, inspect expensive production-like queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time
GROUP BY customer_id;
```

Do not assume that an index is always beneficial. For a large percentage of a table, a sequential scan followed by aggregation may be cheaper than many index lookups.

## Indexing for Aggregation Workloads

Indexes primarily help the database efficiently locate rows matching predicates and support certain ordering/grouping strategies.

For a query such as:

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

an index aligned with the selective filtering requirements may help:

```sql
CREATE INDEX CONCURRENTLY idx_orders_tenant_created
ON orders (tenant_id, created_at);
```

Whether this is actually beneficial depends on:

- Data distribution.
- Query frequency.
- Table size.
- Selectivity.
- Existing indexes.
- PostgreSQL's chosen execution plan.

Do not create indexes solely because a column appears in `GROUP BY`.

Index design should be driven by actual workload patterns and measured execution plans.

## Pre-Aggregation

When the same expensive aggregation is requested repeatedly, computing it from raw transactional data on every request may not scale.

A common architecture is:

```mermaid
flowchart LR
    A[Transactional Events] --> B[Aggregation Job]
    B --> C[Pre-Aggregated Metrics]
    C --> D[Reporting API]
    D --> E[Dashboard]
```

For example:

```text
orders
   ↓
Celery / scheduled SQL job
   ↓
daily_customer_metrics
   ↓
FastAPI / Django API
```

A pre-aggregated table might contain:

```text
customer_id
metric_date
order_count
revenue
```

The trade-off is:

```text
lower query cost
        vs
additional data freshness and consistency complexity
```

For real-time metrics, direct aggregation may be preferable. For historical dashboards over very large datasets, pre-aggregation can be significantly more scalable.

## Common Mistakes

### Using COUNT(*) After a LEFT JOIN

This:

```sql
COUNT(*)
```

counts the generated outer-join row even when no child record exists.

For child-record counts, prefer:

```sql
COUNT(child.id)
```

when the child identifier is non-NULL for real child rows.

### Aggregating Before Defining Grain

If you cannot state:

```text
one output row represents ______
```

the query is likely to be ambiguous or incorrect.

### Summing Values After Row Multiplication

Joining multiple one-to-many relationships can multiply values before aggregation.

Solve the cardinality problem rather than blindly adding `DISTINCT`.

### Using DISTINCT Everywhere

This:

```sql
COUNT(DISTINCT customer_id)
```

can be correct, but using `DISTINCT` to hide join problems can make queries slower while masking the underlying issue.

### Averaging Averages

```sql
AVG(daily_average)
```

is not necessarily the overall average.

Preserve the underlying numerator and denominator when a weighted average is required.

### Using MIN/MAX to Retrieve a Row

```sql
MAX(created_at)
```

returns a value, not the complete row associated with that value.

Use deterministic row-selection techniques when the full record is needed.

### Ignoring NULL Semantics

Do not treat:

```text
NULL
```

as automatically equivalent to:

```text
0
```

Decide what the metric means first.

### Returning Huge Aggregation Results to the Application

A query such as:

```sql
GROUP BY user_id
```

can still return millions of groups.

Aggregation reduces rows only when the grouping cardinality is significantly smaller than the input.

Apply appropriate filters, pagination, partitioning, or an analytics architecture when necessary.

## Interview Traps

| Question | Correct reasoning |
|---|---|
| `COUNT(*)` vs `COUNT(column)`? | `COUNT(*)` counts rows; `COUNT(column)` ignores NULL |
| Why does a LEFT JOIN sometimes produce a count of 1 for no children? | `COUNT(*)` counts the outer-join row |
| Why can SUM become too large after a JOIN? | One-to-many joins may multiply rows |
| Why isn't AVG of averages always correct? | Groups may have different weights |
| Can MAX(timestamp) return the latest row? | No, it only returns the maximum timestamp |
| When does HAVING run conceptually? | After grouping/aggregation |
| Is COUNT(DISTINCT ...) always better? | No; it changes semantics and may cost more |
| Does GROUP BY automatically make a query efficient? | No; aggregation can still require large scans and memory |

## Production Checklist

Before deploying an aggregation query, verify:

- **Metric definition:** Does the aggregate match the business question?
- **Input grain:** What does each source row represent?
- **Output grain:** What does each result row represent?
- **Population:** Are filters applied to the correct rows?
- **NULL behavior:** Is NULL distinct from zero or missing?
- **Join cardinality:** Can any join multiply rows?
- **Uniqueness:** Is `DISTINCT` actually required?
- **Time boundaries:** Are the interval and timezone correct?
- **Numerical precision:** Are monetary values represented with suitable exact types?
- **Division:** Can a denominator be zero?
- **Tie handling:** Are first/last/top-N results deterministic?
- **Performance:** Has the query been tested with production-like data?
- **Execution plan:** Has `EXPLAIN (ANALYZE, BUFFERS)` been evaluated where appropriate?
- **Scale:** Will repeated aggregation remain affordable as data grows?
- **Freshness:** If using pre-aggregation, is the metric's latency acceptable?

## Key Takeaways

- **Define input and output grain before writing an aggregate query**; aggregation correctness depends on the rows being measured.
- **Conditional aggregation, grouped aggregation, distinct counts, and time-based aggregation are core production patterns** for backend reporting and metrics.
- **Join cardinality is a major source of incorrect aggregates**; aggregate independent one-to-many relationships before combining them when necessary.
- **Treat NULLs, averages, ratios, ties, and monetary precision as explicit business semantics**, not implementation details.
- **Optimize large aggregation workloads with measured execution plans and, when appropriate, partitioning, pre-aggregation, or dedicated analytical infrastructure.**