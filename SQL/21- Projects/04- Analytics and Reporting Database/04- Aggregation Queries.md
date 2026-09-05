# 04- Aggregation Queries

## Overview

Aggregation is the core of analytical SQL. OLTP queries commonly retrieve or modify individual records, while analytics queries transform many rows into business-level measurements.

Typical analytical questions include:

```text
How much revenue was generated?
How many orders were completed?
What is the average order value?
Which products generated the most revenue?
How many active customers exist per month?
What percentage of usage belongs to each tenant?
How has revenue changed month over month?
```

The primary SQL tools for aggregation are:

- `COUNT`
- `SUM`
- `AVG`
- `MIN`
- `MAX`
- `GROUP BY`
- `HAVING`
- Conditional aggregation
- `FILTER`
- `DISTINCT`
- Window functions

The difficult part is rarely writing `SUM()` or `COUNT()`. Production analytics requires understanding:

```text
row grain
    ↓
join cardinality
    ↓
filter semantics
    ↓
NULL behavior
    ↓
aggregation level
    ↓
metric definition
    ↓
performance
```

A correct aggregation query must produce the correct result **at the intended grain**.

---

## Aggregation Mental Model

Consider:

```text
Raw rows
   ↓
Filter
   ↓
Join
   ↓
Group
   ↓
Aggregate
   ↓
Report
```

For example:

```sql
SELECT
    customer_id,
    SUM(net_amount) AS revenue
FROM fact_orders
WHERE order_status = 'COMPLETED'
GROUP BY customer_id;
```

The result changes the row grain from:

```text
one row per order
```

to:

```text
one row per customer
```

That grain change is fundamental.

---

## Aggregate Functions

PostgreSQL provides standard aggregate functions such as:

| Function | Purpose |
|---|---|
| `COUNT(*)` | Count input rows |
| `COUNT(column)` | Count non-NULL values |
| `COUNT(DISTINCT column)` | Count unique non-NULL values |
| `SUM(column)` | Sum values |
| `AVG(column)` | Average values |
| `MIN(column)` | Minimum |
| `MAX(column)` | Maximum |

Example:

```sql
SELECT
    COUNT(*) AS order_count,
    SUM(net_amount) AS revenue,
    AVG(net_amount) AS average_order_value,
    MIN(net_amount) AS smallest_order,
    MAX(net_amount) AS largest_order
FROM fact_orders
WHERE order_status = 'COMPLETED';
```

---

## `COUNT(*)` vs `COUNT(column)`

These are not equivalent.

```sql
COUNT(*)
```

counts rows.

```sql
COUNT(column)
```

counts rows where `column` is not `NULL`.

Example:

```text
id | customer_id
---|-----------
1  | C001
2  | C002
3  | NULL
```

Then:

```sql
COUNT(*)           -- 3
COUNT(customer_id) -- 2
```

For row counts, prefer `COUNT(*)`.

---

## `COUNT(DISTINCT ...)`

Use `COUNT(DISTINCT ...)` when the metric requires unique entities.

Example:

```sql
SELECT
    COUNT(DISTINCT customer_id) AS active_customers
FROM fact_orders
WHERE order_status = 'COMPLETED';
```

This answers:

```text
How many unique customers placed completed orders?
```

It does not answer:

```text
How many completed orders existed?
```

That would use:

```sql
COUNT(*)
```

---

## `SUM`

`SUM()` is appropriate for additive measures.

Example:

```sql
SELECT
    SUM(net_amount) AS net_revenue
FROM fact_orders
WHERE order_status = 'COMPLETED';
```

Good candidates include:

```text
revenue
quantity
usage units
transaction amount
discount amount
```

The measure must have well-defined semantics.

For financial amounts, use exact numeric types and preserve currency context.

---

## `AVG`

`AVG()` computes an arithmetic mean.

Example:

```sql
SELECT
    AVG(net_amount) AS average_order_value
FROM fact_orders
WHERE order_status = 'COMPLETED';
```

Be careful when averaging averages.

For example:

```text
Store A average = $10 over 100 orders
Store B average = $100 over 2 orders
```

The average of the two store averages is not the overall average order value.

The correct calculation uses the underlying totals and counts:

```text
total revenue / total orders
```

---

## `MIN` and `MAX`

These functions identify boundaries.

Example:

```sql
SELECT
    MIN(occurred_at) AS first_order,
    MAX(occurred_at) AS latest_order
FROM fact_orders;
```

They are useful for:

- First/last event detection.
- Date ranges.
- Price ranges.
- Transaction boundaries.
- Data-quality checks.

Do not confuse:

```sql
MAX(amount)
```

with:

```text
the entire row associated with the maximum amount
```

Finding the complete row requires techniques such as window functions, `DISTINCT ON`, or a suitable join/subquery.

---

## `GROUP BY`

`GROUP BY` changes the result grain.

Example:

```sql
SELECT
    tenant_key,
    COUNT(*) AS order_count,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY tenant_key;
```

Input:

```text
one row per order
```

Output:

```text
one row per tenant
```

Every selected non-aggregated expression must be compatible with the grouping semantics.

---

## Multiple Grouping Dimensions

Analytics frequently groups by multiple dimensions.

```sql
SELECT
    tenant_key,
    date_key,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY tenant_key, date_key
ORDER BY tenant_key, date_key;
```

The output grain becomes:

```text
one row per tenant per date
```

Adding dimensions increases the number of possible groups.

---

## Time-Based Aggregation

PostgreSQL's `date_trunc()` is useful for time-based reporting.

```sql
SELECT
    date_trunc('month', occurred_at) AS month,
    COUNT(*) AS orders,
    SUM(net_amount) AS revenue
FROM fact_orders
WHERE occurred_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
GROUP BY 1
ORDER BY 1;
```

Typical granularities include:

```text
hour
day
week
month
quarter
year
```

Time-zone semantics should be explicit.

---

## Time Zones in Aggregation

The reporting timezone can change which bucket an event belongs to.

For example:

```sql
SELECT
    date_trunc(
        'day',
        occurred_at AT TIME ZONE 'Asia/Kolkata'
    ) AS report_day,
    COUNT(*) AS orders
FROM fact_orders
GROUP BY 1
ORDER BY 1;
```

An event close to midnight UTC can belong to a different local reporting day.

Never assume UTC and business-local dates are interchangeable.

---

## `WHERE` Before Aggregation

`WHERE` filters rows before grouping.

```sql
SELECT
    tenant_key,
    SUM(net_amount) AS revenue
FROM fact_orders
WHERE order_status = 'COMPLETED'
GROUP BY tenant_key;
```

Conceptually:

```text
all orders
   ↓ WHERE
completed orders
   ↓ GROUP BY
tenant totals
```

This is often the correct place for:

- Date filters.
- Tenant filters.
- Status filters.
- Soft-delete filters.
- Source filters.

---

## `HAVING` After Aggregation

`HAVING` filters groups after aggregation.

Example:

```sql
SELECT
    tenant_key,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY tenant_key
HAVING SUM(net_amount) >= 100000;
```

This means:

```text
group all orders
    ↓
calculate revenue per tenant
    ↓
keep tenants with revenue >= 100000
```

Do not use `HAVING` for row predicates that can safely be applied with `WHERE`.

---

## `WHERE` vs `HAVING`

| Requirement | Preferred clause |
|---|---|
| Orders after a date | `WHERE` |
| Completed orders | `WHERE` |
| Tenant restriction | `WHERE` |
| Revenue per tenant > threshold | `HAVING` |
| Number of orders > threshold | `HAVING` |
| Average order value > threshold | `HAVING` |

Filtering earlier can substantially reduce the amount of data that must be grouped.

---

## Conditional Aggregation

Conditional aggregation is one of the most useful reporting patterns.

Example:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE order_status = 'COMPLETED'
    ) AS completed_orders,
    COUNT(*) FILTER (
        WHERE order_status = 'CANCELLED'
    ) AS cancelled_orders
FROM fact_orders;
```

This produces multiple metrics from one scan.

---

## `FILTER` vs `CASE`

PostgreSQL supports:

```sql
COUNT(*) FILTER (WHERE ...)
```

which is often clearer than:

```sql
SUM(
    CASE
        WHEN ...
        THEN 1
        ELSE 0
    END
)
```

Example:

```sql
SELECT
    COUNT(*) FILTER (WHERE order_status = 'COMPLETED') AS completed,
    COUNT(*) FILTER (WHERE order_status = 'CANCELLED') AS cancelled
FROM fact_orders;
```

`CASE` remains useful for more complex expressions.

---

## Conditional Revenue

Example:

```sql
SELECT
    SUM(net_amount) FILTER (
        WHERE order_status = 'COMPLETED'
    ) AS completed_revenue,
    SUM(net_amount) FILTER (
        WHERE order_status = 'REFUNDED'
    ) AS refunded_amount
FROM fact_orders;
```

This allows multiple business metrics to be calculated without separate queries.

---

## NULL Behavior

Aggregate functions have different NULL semantics.

For example:

```sql
SUM(amount)
```

ignores NULL values.

But if there are no input rows, `SUM()` returns `NULL`.

`COUNT(*)` returns:

```text
0
```

for no input rows.

This distinction matters for APIs and dashboards.

---

## `COALESCE` with Aggregates

If the API contract requires zero rather than `NULL`:

```sql
SELECT
    COALESCE(SUM(net_amount), 0) AS revenue
FROM fact_orders
WHERE tenant_key = $1;
```

This is useful when:

```text
no rows
```

should semantically mean:

```text
zero revenue
```

rather than:

```text
unknown revenue
```

Do not use `COALESCE` blindly. Missing and zero can have different business meanings.

---

## Aggregation After Joins

One of the most common analytical errors occurs when aggregation follows multiple joins.

Consider:

```text
customer
   |
   +-- orders
   |
   +-- payments
```

If both relationships are one-to-many:

```text
customer
    ↓
3 orders
    ↓
2 payments
```

a join can create:

```text
3 × 2 = 6 rows
```

instead of:

```text
3 orders
2 payments
```

Aggregating after the join can therefore double-count metrics.

---

## Correct Aggregate-Before-Join Pattern

Aggregate each fact independently.

```sql
WITH order_totals AS (
    SELECT
        customer_id,
        SUM(net_amount) AS order_revenue
    FROM fact_orders
    GROUP BY customer_id
),
payment_totals AS (
    SELECT
        customer_id,
        SUM(amount) AS payment_amount
    FROM fact_payments
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    COALESCE(o.order_revenue, 0) AS order_revenue,
    COALESCE(p.payment_amount, 0) AS payment_amount
FROM dim_customer AS c
LEFT JOIN order_totals AS o
    ON o.customer_id = c.customer_id
LEFT JOIN payment_totals AS p
    ON p.customer_id = c.customer_id;
```

Each source is first reduced to:

```text
one row per customer
```

The final join therefore preserves the intended grain.

---

## Aggregating Order Items

Suppose:

```text
fact_order_items
= one row per order item
```

To calculate order-level revenue:

```sql
SELECT
    order_id,
    SUM(line_amount) AS order_revenue
FROM fact_order_items
GROUP BY order_id;
```

The result becomes:

```text
one row per order
```

This can then safely be joined to order-level datasets.

---

## Multi-Level Aggregation

Analytics often requires multiple levels:

```text
order item
   ↓
order
   ↓
customer
   ↓
month
```

Each level should be explicit.

Example:

```sql
WITH customer_monthly AS (
    SELECT
        customer_id,
        date_trunc('month', occurred_at) AS month,
        SUM(net_amount) AS revenue
    FROM fact_orders
    GROUP BY
        customer_id,
        date_trunc('month', occurred_at)
)
SELECT
    month,
    SUM(revenue) AS monthly_revenue
FROM customer_monthly
GROUP BY month
ORDER BY month;
```

This can also make business logic easier to validate.

---

## Aggregation and Window Functions

`GROUP BY` collapses rows.

Window functions preserve rows.

Example:

```sql
SELECT
    customer_id,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY customer_id;
```

produces:

```text
one row per customer
```

A window expression can instead retain the original grain:

```sql
SELECT
    order_id,
    customer_id,
    net_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM fact_orders;
```

produces:

```text
one row per order
+
customer total on every row
```

This distinction is fundamental to analytical SQL.

---

## Percentage of Total

A common reporting pattern is:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(net_amount) AS revenue
    FROM fact_orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    revenue / SUM(revenue) OVER () AS revenue_share
FROM customer_revenue
ORDER BY revenue DESC;
```

The intermediate aggregation establishes:

```text
one row per customer
```

The window function then calculates the total across those customers.

---

## Ranking Aggregated Results

Aggregation can be combined with ranking.

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(net_amount) AS revenue
    FROM fact_orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_revenue
ORDER BY revenue_rank;
```

This is useful for:

- Top customers.
- Top products.
- Regional ranking.
- Tenant ranking.

---

## Top-N by Group

For example, top products per category:

```sql
WITH product_revenue AS (
    SELECT
        category_id,
        product_id,
        SUM(net_amount) AS revenue
    FROM fact_order_items
    GROUP BY category_id, product_id
),
ranked AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS position
    FROM product_revenue
)
SELECT
    category_id,
    product_id,
    revenue
FROM ranked
WHERE position <= 10
ORDER BY category_id, position;
```

The aggregation and ranking stages have different responsibilities.

---

## Distinct Aggregation

Example:

```sql
SELECT
    date_key,
    COUNT(DISTINCT customer_id) AS active_customers
FROM fact_orders
GROUP BY date_key;
```

`COUNT(DISTINCT ...)` can be expensive on large datasets because the database must identify unique values within each group.

For high-volume analytics, alternatives may include:

- Pre-aggregated tables.
- Incremental distinct-count structures.
- Approximate algorithms where supported.
- Warehouse-specific analytical functions.

Exactness requirements should drive the choice.

---

## Aggregation Across Dimensions

A common report is:

```text
month
tenant
product category
revenue
```

Example:

```sql
SELECT
    date_trunc('month', o.occurred_at) AS month,
    o.tenant_key,
    p.category,
    SUM(o.net_amount) AS revenue
FROM fact_orders AS o
JOIN dim_product AS p
    ON p.product_key = o.product_key
GROUP BY
    date_trunc('month', o.occurred_at),
    o.tenant_key,
    p.category
ORDER BY
    month,
    o.tenant_key,
    p.category;
```

The final grain is:

```text
one row per month + tenant + category
```

---

## Aggregation and Slowly Changing Dimensions

Historical dimensions require careful joins.

Suppose:

```text
customer_key = 101
customer_id = C123
segment = SMB
effective_from = Jan 1
effective_to = Mar 31
```

and:

```text
customer_key = 205
customer_id = C123
segment = Enterprise
effective_from = Apr 1
effective_to = NULL
```

Facts should reference the correct historical version when historical reporting depends on that attribute.

Otherwise, a historical revenue report can incorrectly classify past transactions using the customer's current segment.

---

## Additive Measures

An additive measure can be safely summed across the relevant dimensions.

Examples:

```text
order amount
quantity
usage units
transaction amount
```

Example:

```sql
SELECT
    SUM(quantity)
FROM fact_order_items;
```

---

## Semi-Additive Measures

Some measures can be aggregated across dimensions but not across time.

Account balance is a classic example.

```text
Monday balance = $100
Tuesday balance = $120
Wednesday balance = $110
```

Summing those balances does not produce a meaningful period balance.

Instead, the report may require:

```text
latest balance
average balance
end-of-period balance
```

The schema should document these semantics.

---

## Non-Additive Measures

Ratios and percentages are usually non-additive.

For example:

```text
conversion_rate
```

should generally be calculated from:

```text
conversions / eligible_population
```

rather than summed or blindly averaged across groups.

Example:

```sql
SELECT
    SUM(conversions)::numeric
    / NULLIF(SUM(eligible_users), 0) AS conversion_rate
FROM daily_metrics;
```

---

## Avoiding Average-of-Averages

This is incorrect for weighted metrics:

```sql
SELECT AVG(conversion_rate)
FROM daily_metrics;
```

when days have different numbers of eligible users.

Prefer:

```sql
SELECT
    SUM(conversions)::numeric
    / NULLIF(SUM(eligible_users), 0) AS conversion_rate
FROM daily_metrics;
```

The correct formula depends on the metric definition.

---

## `GROUP BY` and Functional Dependencies

SQL grouping rules matter when selecting non-aggregated columns.

A safe pattern is to group by the dimensions explicitly required by the report:

```sql
SELECT
    tenant_key,
    region,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY tenant_key, region;
```

Do not rely on assumptions about which columns are "obviously associated" with a grouped identifier.

---

## `GROUP BY` Ordinals

PostgreSQL supports:

```sql
GROUP BY 1, 2;
```

Example:

```sql
SELECT
    tenant_key,
    date_key,
    SUM(net_amount)
FROM fact_orders
GROUP BY 1, 2;
```

This is concise, but changing the select-list order can silently change the meaning.

For long-lived production SQL, explicit expressions can be easier to review:

```sql
GROUP BY tenant_key, date_key;
```

---

## `ROLLUP`

PostgreSQL supports grouping extensions such as `ROLLUP`.

Example:

```sql
SELECT
    tenant_key,
    date_key,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY ROLLUP (tenant_key, date_key);
```

This can produce:

```text
tenant + date
tenant subtotal
grand total
```

It is useful for hierarchical reports but requires careful interpretation of NULL values representing subtotal rows.

---

## `GROUPING`

Use `GROUPING()` to distinguish subtotal NULLs from actual NULL dimension values.

Example:

```sql
SELECT
    tenant_key,
    date_key,
    SUM(net_amount) AS revenue,
    GROUPING(tenant_key) AS tenant_total,
    GROUPING(date_key) AS date_total
FROM fact_orders
GROUP BY ROLLUP (tenant_key, date_key);
```

This is important for reliable report serialization.

---

## `CUBE`

`CUBE` can generate combinations of grouping dimensions.

Example:

```sql
SELECT
    tenant_key,
    region,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY CUBE (tenant_key, region);
```

This can generate:

```text
tenant + region
tenant total
region total
grand total
```

It can produce many groups and should be used deliberately.

---

## `GROUPING SETS`

`GROUPING SETS` allows explicitly defining required aggregation levels.

```sql
SELECT
    tenant_key,
    date_key,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY GROUPING SETS (
    (tenant_key, date_key),
    (tenant_key),
    ()
);
```

This can be more controlled than generating every possible combination with `CUBE`.

---

## Aggregation Execution

Conceptually, PostgreSQL may implement grouping through strategies such as:

```text
HashAggregate
GroupAggregate
```

A hash-based strategy groups rows using in-memory hash structures.

A sort-based strategy can process rows in grouping order.

The optimizer chooses a plan based on:

```text
estimated rows
group cardinality
available memory
sort cost
statistics
parallelism
```

Inspect the actual plan rather than assuming which strategy PostgreSQL will use.

---

## `EXPLAIN ANALYZE`

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    tenant_key,
    SUM(net_amount)
FROM fact_orders
WHERE occurred_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
GROUP BY tenant_key;
```

Inspect:

```text
estimated rows
actual rows
execution time
shared hits
shared reads
temporary reads/writes
sort methods
aggregate strategy
parallel workers
```

Aggregation performance depends heavily on input cardinality and group cardinality.

---

## Memory and Aggregation

Large aggregations may require significant memory.

Potential outcomes include:

```text
in-memory aggregation
        ↓
memory pressure
        ↓
temporary files / disk spill
```

For PostgreSQL, `work_mem` affects operations such as sorts and hash operations.

Increasing it globally without considering concurrency can be dangerous.

For example:

```text
100 concurrent queries
×
large per-operation memory
=
substantial memory consumption
```

Tune based on workload and measure actual behavior.

---

## Parallel Aggregation

PostgreSQL can use parallel query execution for suitable workloads.

Conceptually:

```text
Large fact table
      ↓
+-----+-----+-----+
|     |     |     |
Worker Worker Worker
|     |     |     |
+-----+-----+-----+
      ↓
Partial aggregates
      ↓
Final aggregate
```

Parallel execution is not guaranteed.

The planner considers:

- Query cost.
- Table size.
- Parallel safety.
- Configuration.
- Available workers.
- Data access strategy.

---

## Indexes and Aggregation

Indexes can help when aggregation includes selective predicates.

Example:

```sql
WHERE tenant_key = $1
  AND occurred_at >= $2
```

with a suitable index can reduce the input rows before aggregation.

However, an index does not automatically make:

```sql
GROUP BY tenant_key
```

fast on a huge table.

For large analytical workloads, other strategies may matter more:

- Partition pruning.
- Pre-aggregation.
- Materialized views.
- Columnar storage.
- Data clustering.
- Warehouse-native execution.

---

## Partition Pruning

Time-partitioned fact tables can reduce the amount of data scanned.

```text
fact_orders
├── 2026-01
├── 2026-02
├── 2026-03
├── ...
└── 2026-09
```

A query such as:

```sql
WHERE occurred_at >= DATE '2026-09-01'
  AND occurred_at < DATE '2026-10-01'
```

can allow PostgreSQL to exclude irrelevant partitions.

The partitioning strategy must align with common query predicates.

---

## Pre-Aggregation

If a report repeatedly scans billions of rows to calculate:

```text
daily tenant revenue
```

it may be better to maintain:

```text
fact_daily_revenue
```

Example:

```text
raw orders
    ↓
daily aggregation
    ↓
fact_daily_revenue
    ↓
dashboard
```

Benefits:

- Lower query latency.
- Lower compute cost.
- Predictable dashboard performance.

Costs:

- Additional storage.
- Refresh complexity.
- Backfill complexity.
- Freshness delay.
- Additional correctness checks.

---

## Materialized Views

Materialized views can cache the result of an analytical query.

```sql
CREATE MATERIALIZED VIEW report_daily_revenue AS
SELECT
    date_trunc('day', occurred_at) AS day,
    tenant_key,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY 1, 2;
```

The result can be refreshed:

```sql
REFRESH MATERIALIZED VIEW report_daily_revenue;
```

For very large systems, a full refresh may become too expensive. Explicit incremental aggregate tables can provide more control.

---

## Aggregation Through Django

Django ORM can express common aggregations.

```python
from django.db.models import Count, Sum

queryset = (
    Order.objects
    .filter(status="COMPLETED")
    .values("tenant_id")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("net_amount"),
    )
)
```

The generated SQL should still be understood and inspected.

ORM abstraction does not remove:

```text
grain
join cardinality
NULL semantics
indexing
execution-plan
```

concerns.

---

## Aggregation Through SQLAlchemy

SQLAlchemy can express analytical aggregation explicitly.

```python
from sqlalchemy import func, select

stmt = (
    select(
        FactOrder.tenant_key,
        func.count().label("order_count"),
        func.sum(FactOrder.net_amount).label("revenue"),
    )
    .where(FactOrder.order_status == "COMPLETED")
    .group_by(FactOrder.tenant_key)
)
```

For complex reporting queries, keeping the SQL shape explicit can improve maintainability.

---

## Reporting API Design

A reporting endpoint should define its aggregation semantics.

Example:

```http
GET /v1/reports/revenue?from=2026-01-01&to=2026-09-01&group_by=month
```

The backend should validate:

```text
allowed dimensions
allowed date range
tenant authorization
maximum result size
supported metrics
```

Do not accept arbitrary SQL expressions from clients.

---

## Dynamic Grouping

An API may support:

```text
group_by=day
group_by=month
group_by=tenant
group_by=product
```

Map client values to known SQL expressions.

Avoid directly interpolating user input:

```python
sql = f"GROUP BY {user_input}"
```

Instead use an allowlist:

```python
GROUP_BY_OPTIONS = {
    "day": "date_trunc('day', occurred_at)",
    "month": "date_trunc('month', occurred_at)",
}
```

Parameters protect values, but SQL identifiers and expressions require separate validation.

---

## Multi-Tenant Aggregation

Tenant filters should be applied consistently.

```sql
SELECT
    date_key,
    SUM(net_amount) AS revenue
FROM fact_orders
WHERE tenant_key = $1
GROUP BY date_key
ORDER BY date_key;
```

For platform-level reports:

```text
cross-tenant aggregation
```

requires explicit authorization.

Do not rely solely on frontend filters to prevent cross-tenant data exposure.

---

## Security and Aggregation

Aggregated data can itself be sensitive.

For example:

```text
revenue by tenant
employee count by department
usage by customer
```

may reveal commercially sensitive information.

Security controls should consider:

- Row-level access.
- Column-level access.
- Tenant boundaries.
- BI roles.
- Export permissions.
- Audit logging.

A user who cannot view raw transactions should not automatically receive unrestricted aggregates derived from them.

---

## Redis and Cached Aggregates

Frequently requested reports may be cached.

Example key:

```text
analytics:tenant:{tenant_id}:revenue:{from}:{to}:{group_by}
```

The cache key must include every parameter affecting the result.

Define:

```text
TTL
staleness tolerance
invalidation strategy
maximum result size
```

Do not use Redis as the source of truth for analytical correctness.

---

## Kafka and Streaming Aggregation

For near-real-time analytics:

```text
Application
    ↓
Kafka
    ↓
Stream processor
    ↓
Aggregated state
    ↓
Analytics database
```

Streaming aggregation introduces additional concerns:

- Event ordering.
- Duplicate events.
- Late events.
- State recovery.
- Watermarks.
- Replay.
- Exactly-once claims.

Do not assume streaming aggregation eliminates the need for batch reconciliation.

---

## Celery and Scheduled Aggregations

Celery can refresh derived datasets periodically.

Example:

```text
00:00
  ↓
daily aggregation job
  ↓
load fact_daily_revenue
  ↓
validate totals
  ↓
mark dataset successful
```

Jobs should be:

- Idempotent.
- Observable.
- Restartable.
- Bounded.

A failed refresh should not leave consumers believing that stale data is current.

---

## Data Quality Checks

Aggregation pipelines should validate important invariants.

Examples:

```sql
SELECT
    COUNT(*) AS invalid_rows
FROM fact_orders
WHERE net_amount < 0;
```

Reconciliation can compare:

```text
OLTP completed revenue
        vs
analytics completed revenue
```

Differences should have defined tolerances and investigation procedures.

---

## Large-Scale Aggregation Strategy

For very large datasets, prefer a layered strategy:

```text
Raw events
    ↓
Partitioned facts
    ↓
Curated facts
    ↓
Daily aggregates
    ↓
Monthly aggregates
    ↓
Reporting API / BI
```

Do not force every dashboard to scan raw event data.

The appropriate layer depends on:

```text
freshness
query complexity
data volume
cost
concurrency
```

---

## Common Aggregation Mistakes

### Double-Counting After Joins

**Problem:**

```text
one-to-many × one-to-many
```

creates multiplicative rows.

**Solution:** aggregate each fact independently before joining.

### Using `COUNT(column)` for Row Counts

**Problem:** NULL values are excluded.

**Solution:** use `COUNT(*)` when counting rows.

### Confusing Zero and NULL

**Problem:** missing data and zero are treated as identical.

**Solution:** define metric semantics explicitly and use `COALESCE` only when appropriate.

### Averaging Averages

**Problem:** groups with different population sizes receive equal weight.

**Solution:** calculate the ratio from underlying totals when the metric requires weighted aggregation.

### Using `HAVING` for Row Filtering

**Problem:** unnecessary rows may be processed before aggregation.

**Solution:** use `WHERE` for predicates that apply before grouping.

### Aggregating at the Wrong Grain

**Problem:** the query produces technically valid SQL but semantically incorrect metrics.

**Solution:** state the expected row grain before writing the query.

### Summing Semi-Additive Measures

**Problem:** balances or snapshots are incorrectly summed across time.

**Solution:** define the correct temporal aggregation such as ending balance or average balance.

### Blind `COUNT(DISTINCT ...)`

**Problem:** exact distinct aggregation can become expensive at scale.

**Solution:** evaluate pre-aggregation or approximate methods when business accuracy requirements permit.

### Using `SELECT *` in Reports

**Problem:** unnecessary columns increase I/O, network traffic, and application memory.

**Solution:** project only required dimensions and measures.

### Unbounded Reporting Queries

**Problem:** large date ranges can trigger massive scans.

**Solution:** enforce bounded ranges, asynchronous exports, and workload-specific limits.

---

## Production Optimization Workflow

When an aggregation query is slow:

1. Define the expected grain.
2. Verify the metric semantics.
3. Check for duplicate-producing joins.
4. Reduce the input rows with valid predicates.
5. Project only required columns.
6. Inspect `EXPLAIN (ANALYZE, BUFFERS)`.
7. Check estimated versus actual row counts.
8. Inspect aggregation and sort strategies.
9. Check memory usage and temporary spills.
10. Evaluate indexes and partition pruning.
11. Consider pre-aggregation.
12. Consider materialization or a dedicated analytical engine.

Do not start by adding an index without understanding the execution plan.

---

## Production Checklist

### Correctness

- [ ] Fact grain is documented.
- [ ] Metric definitions are explicit.
- [ ] Join cardinality is understood.
- [ ] Duplicate rows are handled.
- [ ] NULL semantics are intentional.
- [ ] Currency semantics are explicit.
- [ ] Time-zone semantics are documented.
- [ ] Additive behavior is understood.

### Query Design

- [ ] `WHERE` filters are applied before aggregation where valid.
- [ ] `HAVING` is used for group-level conditions.
- [ ] `COUNT(*)` is used appropriately.
- [ ] `COUNT(DISTINCT ...)` is used intentionally.
- [ ] Conditional aggregation is used where appropriate.
- [ ] Multiple fact tables are aggregated independently when required.
- [ ] Result grain is explicit.

### Performance

- [ ] Queries are bounded.
- [ ] Large scans are understood.
- [ ] Execution plans have been inspected.
- [ ] Statistics are current.
- [ ] Partition pruning is effective where applicable.
- [ ] Temporary spills are monitored.
- [ ] Pre-aggregation has been evaluated for repeated expensive reports.
- [ ] OLTP workloads are protected from heavy analytics.

### Backend

- [ ] Reporting APIs validate dimensions and filters.
- [ ] Dynamic SQL uses allowlists.
- [ ] Large exports are asynchronous.
- [ ] Redis caching has explicit freshness semantics.
- [ ] Celery jobs are idempotent.
- [ ] Tenant authorization is enforced.

### Operations

- [ ] Query latency is monitored.
- [ ] Data freshness is monitored.
- [ ] Pipeline failures are observable.
- [ ] Reconciliation checks exist.
- [ ] Storage growth is tracked.
- [ ] Backfill procedures are documented.

---

## Senior Decision Framework

When designing an aggregation query, reason in this order:

```text
What does one input row represent?
        ↓
What should one output row represent?
        ↓
Which rows qualify?
        ↓
Which joins are required?
        ↓
Can any join multiply rows?
        ↓
Which measures are additive?
        ↓
How should NULLs behave?
        ↓
What time semantics apply?
        ↓
Can the query execute at the required scale?
        ↓
Should the result be pre-aggregated?
```

This prevents a common failure mode in analytics engineering:

```text
SQL is syntactically correct
        ↓
query executes successfully
        ↓
numbers are wrong
```

Correct analytical SQL is about **semantic correctness first, physical performance second**.

## Key Takeaways

- **Aggregation changes data grain, so every analytical query should explicitly define the grain of its input and expected output.**
- **The most dangerous aggregation bugs usually come from join cardinality, incorrect NULL handling, averaging averages, or using the wrong additive semantics.**
- **`WHERE` reduces input rows before grouping, while `HAVING` filters groups after aggregation; use each according to its semantic role.**
- **Large analytical aggregations require execution-plan analysis, realistic statistics, memory awareness, partitioning, and sometimes pre-aggregation or materialized datasets.**
- **Production reporting should combine correct metric definitions, bounded queries, tenant-aware security, observable pipelines, and explicit freshness and reconciliation guarantees.**