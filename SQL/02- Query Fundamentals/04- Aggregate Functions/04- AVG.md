# 04- AVG

## Overview

`AVG` is a SQL aggregate function that calculates the arithmetic mean of numeric values:

```text
average = sum of values / number of non-NULL values
```

It is useful for metrics such as average order value, average response time, average transaction amount, average rating, and average processing duration.

The basic form is:

```sql
SELECT AVG(amount) AS average_amount
FROM payments;
```

`AVG` looks simple, but production usage requires careful attention to `NULL`, numeric precision, integer division, filtering, grouping, joins, outliers, and the semantic meaning of the metric.

## Basic Syntax

```sql
AVG(expression)
```

Examples:

```sql
SELECT AVG(amount) AS average_payment
FROM payments;
```

With filtering:

```sql
SELECT AVG(amount) AS average_completed_payment
FROM payments
WHERE status = 'completed';
```

With grouping:

```sql
SELECT
    customer_id,
    AVG(amount) AS average_payment
FROM payments
GROUP BY customer_id;
```

The expression can also be calculated:

```sql
SELECT
    AVG(quantity * unit_price) AS average_line_value
FROM order_items;
```

## How AVG Works

Conceptually, the database computes:

```text
AVG(value) = SUM(value) / COUNT(value)
```

where the count represents non-NULL input values.

For:

```text
amount
------
100
200
300
```

the result is:

```text
200
```

For:

```text
amount
------
100
200
NULL
300
```

the result is still:

```text
200
```

because the NULL value does not participate in the calculation.

The database optimizer does not necessarily execute `AVG` as two separate SQL queries. The engine can maintain aggregate state internally and may use partial aggregation, parallel workers, or other execution strategies.

## NULL Behavior

`AVG` ignores NULL values.

Given:

```text
score
-----
10
20
NULL
30
```

```sql
SELECT AVG(score)
FROM reviews;
```

returns:

```text
20
```

The NULL row is not interpreted as zero.

This distinction matters because these two datasets have different meanings:

```text
10
20
30
```

Average:

```text
20
```

versus:

```text
10
20
NULL
30
```

Average:

```text
20
```

versus treating NULL as zero:

```text
(10 + 20 + 0 + 30) / 4 = 15
```

If NULL semantically means zero in the business domain, explicitly encode that requirement:

```sql
SELECT AVG(COALESCE(score, 0))
FROM reviews;
```

Do not use this merely because `NULL` looks inconvenient. NULL may mean "not measured", "not applicable", or "unknown", which is different from zero.

## AVG with No Rows

When no input values contribute to the aggregate, `AVG` returns `NULL`.

```sql
SELECT AVG(amount) AS average_amount
FROM payments
WHERE status = 'does_not_exist';
```

Result:

```text
NULL
```

If the application contract requires a default value:

```sql
SELECT COALESCE(AVG(amount), 0) AS average_amount
FROM payments
WHERE status = 'does_not_exist';
```

Whether zero is an appropriate fallback is a business decision. An average of zero and an absence of observations are not mathematically equivalent.

For APIs, distinguish between:

```json
{
  "average_response_time_ms": null
}
```

and:

```json
{
  "average_response_time_ms": 0
}
```

The former can mean "no observations", while the latter means "observed average is zero".

## AVG with WHERE

Filtering determines which rows participate in the average.

```sql
SELECT AVG(amount) AS average_order_value
FROM orders
WHERE status = 'completed';
```

A common production pattern is filtering by tenant and time range:

```sql
SELECT AVG(amount) AS average_order_value
FROM orders
WHERE tenant_id = :tenant_id
  AND status = 'completed'
  AND created_at >= :start_time
  AND created_at < :end_time;
```

For time-based reporting, half-open intervals are generally easier to compose:

```text
[start_time, end_time)
```

For example:

```sql
WHERE created_at >= TIMESTAMP '2026-08-01 00:00:00'
  AND created_at <  TIMESTAMP '2026-09-01 00:00:00'
```

## AVG with GROUP BY

`AVG` is commonly used to calculate metrics per business dimension.

```sql
SELECT
    customer_id,
    AVG(amount) AS average_order_value
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

Multiple dimensions can be used:

```sql
SELECT
    tenant_id,
    currency,
    AVG(amount) AS average_payment
FROM payments
WHERE status = 'completed'
GROUP BY tenant_id, currency;
```

Grouping by currency is important because averaging monetary values from different currencies produces a meaningless result unless they have first been normalized to a common monetary basis.

## AVG with HAVING

`HAVING` filters groups after aggregation.

For example:

```sql
SELECT
    customer_id,
    AVG(amount) AS average_order_value
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING AVG(amount) > 1000;
```

The logical processing sequence is:

```text
FROM
  ↓
WHERE
  ↓
GROUP BY
  ↓
AVG
  ↓
HAVING
  ↓
Result
```

`WHERE` filters individual rows before aggregation.

`HAVING` filters the resulting groups.

## AVG and Join Cardinality

Join cardinality can silently produce incorrect averages.

Suppose an order has multiple related records:

```text
orders
  │
  └── order_items
```

Joining orders to items changes the number of rows representing each order.

For example:

```text
Order A → 3 items
Order B → 1 item
```

A naive query such as:

```sql
SELECT AVG(o.total_amount)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

does not calculate the average order value.

Conceptually, the joined rows are:

```text
Order A   100
Order A   100
Order A   100
Order B   200
```

The average becomes:

```text
(100 + 100 + 100 + 200) / 4 = 125
```

while the actual average across orders is:

```text
(100 + 200) / 2 = 150
```

The problem is not `AVG`; it is that the query changed the grain of the data.

### Aggregate at the Correct Grain

If the metric is "average per order", ensure the input contains one row per order:

```sql
SELECT AVG(o.total_amount) AS average_order_value
FROM orders AS o
WHERE o.status = 'completed';
```

If a join is required for filtering, use a structure that preserves order-level cardinality:

```sql
SELECT AVG(o.total_amount) AS average_order_value
FROM orders AS o
WHERE o.status = 'completed'
  AND EXISTS (
      SELECT 1
      FROM order_items AS oi
      WHERE oi.order_id = o.id
  );
```

The senior-level rule is:

> Define the grain of the metric before writing the aggregate query, and verify that joins preserve that grain.

## AVG and DISTINCT

`AVG(DISTINCT expression)` calculates the average of distinct values.

Given:

```text
100
100
200
```

```sql
SELECT AVG(amount)
FROM payments;
```

returns:

```text
133.333...
```

while:

```sql
SELECT AVG(DISTINCT amount)
FROM payments;
```

returns:

```text
150
```

`DISTINCT` applies to the values, not to the underlying entities.

Therefore, if two legitimate payments both have an amount of `100`, `AVG(DISTINCT amount)` treats those values as one value.

Do not use `AVG(DISTINCT amount)` as a generic solution for duplicate rows caused by an incorrect join. Fix the relational query instead.

## AVG and Numeric Precision

The data type used by the average matters.

For financial values, prefer exact numeric types such as PostgreSQL `NUMERIC` rather than floating-point storage when exact decimal semantics are required.

Example:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    total_amount NUMERIC(19, 4) NOT NULL
);
```

Then:

```sql
SELECT AVG(total_amount) AS average_order_value
FROM orders;
```

The appropriate precision and scale depend on the domain.

For integer minor units:

```text
amount_minor = 12550
```

can represent:

```text
125.50
```

for a currency whose minor unit is 1/100.

The application must preserve the currency and scale semantics.

## Integer Values and Division

A common misconception is that all databases behave identically when calculating averages from integers.

`AVG` is an aggregate with database-specific result-type rules, so its result should not be assumed to behave exactly like manually writing:

```sql
SUM(value) / COUNT(value)
```

in every database.

For example, manually performing integer division can lose the fractional component in systems or expressions where both operands are integer-valued.

Prefer:

```sql
SELECT AVG(score)
FROM reviews;
```

when the intended metric is an average.

If implementing the calculation manually, explicitly control the numeric type when necessary:

```sql
SELECT
    SUM(score)::numeric / NULLIF(COUNT(score), 0) AS average_score
FROM reviews;
```

The exact casting syntax is database-specific.

## AVG of Derived Expressions

`AVG` can operate on expressions rather than stored columns.

For example, average order line value:

```sql
SELECT AVG(quantity * unit_price) AS average_line_value
FROM order_items;
```

Average processing duration can also be calculated:

```sql
SELECT
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) AS average_duration_seconds
FROM jobs
WHERE completed_at IS NOT NULL;
```

The expression should reflect the business metric precisely.

For example, averaging raw processing times may not be equivalent to calculating a percentile such as p95 or p99.

## Average vs Percentiles

An average is not always an appropriate latency metric.

Suppose API response times are:

```text
50ms
52ms
55ms
60ms
3000ms
```

The average is heavily affected by the 3-second outlier.

For backend latency, production observability often needs:

- Average
- Median / p50
- p90
- p95
- p99
- Maximum

For example, "average latency is 100 ms" does not tell you whether 1% of requests take several seconds.

For user-facing performance and SLO analysis, percentiles are often more informative than `AVG`.

## Weighted vs Unweighted Average

`AVG` calculates an unweighted arithmetic mean.

Suppose:

```text
Service A:
100 requests
average latency = 100 ms

Service B:
10 requests
average latency = 1000 ms
```

The simple average of the two service averages is:

```text
(100 + 1000) / 2 = 550 ms
```

But the request-weighted average is:

```text
(100 × 100 + 1000 × 10) / 110
≈ 181.82 ms
```

Therefore, do not average averages unless the groups have equal weighting or the resulting metric is explicitly defined that way.

A weighted average can be expressed as:

```sql
SELECT
    SUM(score * weight) / NULLIF(SUM(weight), 0) AS weighted_average
FROM metrics;
```

This is useful for metrics such as:

- Weighted ratings
- Cost per unit
- Weighted conversion metrics
- Aggregated latency measurements
- Revenue-weighted measurements

## AVG with Conditional Aggregation

A report may require multiple averages from the same dataset.

PostgreSQL supports `FILTER`:

```sql
SELECT
    AVG(amount) AS average_payment,
    AVG(amount) FILTER (
        WHERE status = 'completed'
    ) AS average_completed_payment,
    AVG(amount) FILTER (
        WHERE status = 'refunded'
    ) AS average_refunded_payment
FROM payments;
```

A portable alternative is:

```sql
SELECT
    AVG(CASE
        WHEN status = 'completed' THEN amount
    END) AS average_completed_payment,
    AVG(CASE
        WHEN status = 'refunded' THEN amount
    END) AS average_refunded_payment
FROM payments;
```

The `CASE` expression returns NULL for rows that do not belong to the requested category, and `AVG` ignores those rows.

## AVG and LEFT JOIN

`LEFT JOIN` is useful when entities with no related records must remain visible.

For example:

```sql
SELECT
    c.id,
    AVG(p.amount) AS average_payment
FROM customers AS c
LEFT JOIN payments AS p
    ON p.customer_id = c.id
GROUP BY c.id;
```

A customer with no payments remains in the result, but their average may be NULL.

That is usually preferable to automatically returning zero because:

```text
No payments
```

does not mean:

```text
Average payment = 0
```

If the API explicitly defines no observations as zero:

```sql
SELECT
    c.id,
    COALESCE(AVG(p.amount), 0) AS average_payment
FROM customers AS c
LEFT JOIN payments AS p
    ON p.customer_id = c.id
GROUP BY c.id;
```

Make this semantic choice deliberately.

## AVG and Statistical Outliers

The arithmetic mean is sensitive to extreme values.

For example:

```text
10
10
10
10
1000
```

has an average of:

```text
208
```

even though four of five observations are `10`.

For production analytics, consider whether the metric should use:

- Mean
- Median
- Trimmed mean
- Percentiles
- Winsorized statistics
- Domain-specific filtering

Do not remove outliers simply to make an average look more representative. First determine whether the outlier is:

- A legitimate event
- A data-quality problem
- A fraud event
- A system anomaly
- A measurement error

## AVG and Performance

An unfiltered query such as:

```sql
SELECT AVG(amount)
FROM payments;
```

may require the database to process a large portion of the table.

An index does not automatically make every aggregate query fast.

Filtering can reduce the amount of data processed:

```sql
SELECT AVG(amount)
FROM payments
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time;
```

A supporting index may be useful:

```sql
CREATE INDEX idx_payments_tenant_created_at
ON payments (tenant_id, created_at);
```

Whether this improves the query depends on selectivity, table size, statistics, workload, and the optimizer.

Inspect the actual execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT AVG(amount)
FROM payments
WHERE tenant_id = 42
  AND created_at >= TIMESTAMP '2026-08-01 00:00:00'
  AND created_at < TIMESTAMP '2026-09-01 00:00:00';
```

Do not add indexes solely because an aggregate exists. Index the filtering and access patterns that matter.

## Large-Scale AVG Queries

Repeatedly calculating averages over very large transactional tables can become expensive.

A production system may use:

| Strategy | Suitable for | Tradeoff |
|---|---|---|
| Direct `AVG` | Moderate data volume | Simple but can require large scans |
| Index-supported filtering | Selective queries | Extra storage and write overhead |
| Summary tables | Frequent dashboards | Requires maintenance |
| Materialized views | Repeated analytical queries | Potentially stale results |
| Pre-aggregated statistics | High-volume time-series metrics | Reduced flexibility |
| Read replicas | Offloading read-heavy workloads | Replication lag |
| Analytical database | Large-scale analytics | Additional infrastructure |

A useful optimization is to store sufficient statistics rather than only an average.

For an ordinary arithmetic mean:

```text
average = sum / count
```

so storing:

```text
sum
count
```

can be enough to recompute the average.

For example:

```text
daily_metrics
-------------
date
tenant_id
value_sum
value_count
```

Then:

```sql
SELECT
    SUM(value_sum) / NULLIF(SUM(value_count), 0) AS average_value
FROM daily_metrics
WHERE tenant_id = :tenant_id
  AND date >= :start_date
  AND date < :end_date;
```

This is more correct than averaging daily averages:

```sql
AVG(daily_average)
```

because days may contain different numbers of observations.

## AVG in Django

Django exposes `AVG` through `Avg`:

```python
from django.db.models import Avg

average_order_value = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="completed",
    )
    .aggregate(avg=Avg("total_amount"))
)["avg"]
```

If there are no matching rows, the result can be `None`.

If the application explicitly defines no observations as zero:

```python
from decimal import Decimal
from django.db.models import Avg, Value
from django.db.models.functions import Coalesce

average_order_value = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="completed",
    )
    .aggregate(
        avg=Coalesce(
            Avg("total_amount"),
            Value(Decimal("0")),
        )
    )
)["avg"]
```

Grouped averages:

```python
from django.db.models import Avg

averages = (
    Order.objects
    .filter(tenant_id=tenant_id, status="completed")
    .values("customer_id")
    .annotate(average_order_value=Avg("total_amount"))
)
```

When joins are involved, inspect the generated SQL and verify the resulting row grain rather than assuming the ORM will prevent aggregation errors.

## AVG in Backend APIs

A REST endpoint might return:

```json
{
  "average_order_value": "1250.50",
  "currency": "INR",
  "sample_size": 842
}
```

Including `sample_size` is often useful because an average without its observation count can be misleading.

For example:

```text
Average rating = 5.0
Sample size = 2
```

is materially different from:

```text
Average rating = 5.0
Sample size = 200000
```

A production API should define:

- Metric definition
- Population included
- NULL treatment
- Time window
- Currency and units
- Precision
- Sample size
- Filtering rules
- Consistency guarantees
- Whether the result is exact or eventually consistent

## Security and Multi-Tenant Systems

Aggregate queries must enforce authorization at the data layer.

For a multi-tenant system:

```sql
SELECT AVG(amount)
FROM payments
WHERE tenant_id = :tenant_id;
```

The `tenant_id` predicate should be derived from trusted request context rather than blindly accepting an arbitrary tenant identifier from an untrusted client.

Application-level authorization should ensure users cannot request aggregate data belonging to another tenant.

For systems using PostgreSQL Row-Level Security, database-enforced policies can provide an additional isolation boundary.

Parameterized queries should be used for dynamic values:

```python
cursor.execute(
    """
    SELECT AVG(amount)
    FROM payments
    WHERE tenant_id = %s
      AND status = %s
    """,
    [tenant_id, "completed"],
)
```

Do not construct SQL by string concatenation.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Treating NULL as zero automatically | NULL may mean no observation | Decide NULL semantics explicitly |
| Returning zero when no rows exist | Hides the distinction between zero and no data | Use NULL unless the business contract says otherwise |
| Averaging after a one-to-many JOIN | Rows may be duplicated and bias the result | Preserve the intended grain |
| Using `AVG(DISTINCT value)` to fix duplicate joins | Legitimate equal values can be discarded | Fix join cardinality |
| Averaging averages | Groups with different sizes get equal weight | Use `SUM(total) / SUM(count)` when appropriate |
| Ignoring outliers | Mean can be heavily distorted | Consider median or percentiles |
| Mixing currencies | Produces meaningless monetary metrics | Group by currency or normalize first |
| Using floating point for exact financial metrics | Precision can be inappropriate | Use exact decimal or domain-appropriate representation |
| Assuming an index guarantees fast AVG | Large scans may still be required | Inspect execution plans |
| Omitting sample size | Average can hide very small populations | Return count alongside the metric |

## Interview Traps

### AVG Ignores NULL

Given:

```text
10
20
NULL
30
```

```sql
SELECT AVG(value)
FROM metrics;
```

returns:

```text
20
```

It does not divide by four.

### No Rows Produce NULL

```sql
SELECT AVG(value)
FROM metrics
WHERE false;
```

returns:

```text
NULL
```

not zero.

### AVG(DISTINCT) Is Value-Based

For:

```text
100
100
200
```

```sql
AVG(value)           → 133.333...
AVG(DISTINCT value)  → 150
```

`DISTINCT` removes duplicate values, not duplicate entities.

### Join Multiplication Changes the Population

If one order appears three times after a join, its value can influence the average three times.

Always identify the intended grain before aggregating.

### Average of Averages Can Be Wrong

Given:

```text
Group A: average = 10, count = 100
Group B: average = 100, count = 10
```

this:

```sql
AVG(group_average)
```

produces:

```text
55
```

while the correct combined average is:

```text
(10 × 100 + 100 × 10) / 110
= 18.18...
```

The correct calculation depends on the observation counts.

## Production Checklist

Before shipping an `AVG` query, verify:

- [ ] What population does the metric represent?
- [ ] What is the intended row grain?
- [ ] Can any JOIN multiply observations?
- [ ] Should NULL mean "not observed" or zero?
- [ ] What should happen when there are no observations?
- [ ] Are all monetary values expressed in the same currency?
- [ ] Is the numeric type appropriate for the domain?
- [ ] Are outliers legitimate and expected?
- [ ] Is a mean actually the right metric, or should percentiles/median be used?
- [ ] If aggregating precomputed groups, are groups weighted correctly?
- [ ] Is sample size exposed where useful?
- [ ] Has the query been tested against production-scale data?
- [ ] Has the execution plan been inspected?
- [ ] Are tenant and authorization boundaries enforced?
- [ ] Does the API contract define precision and NULL behavior?

## Key Takeaways

- `AVG` computes an arithmetic mean over non-NULL values; no contributing rows produce `NULL`, not zero.
- Aggregation correctness depends heavily on row grain: one-to-many joins can silently bias an average by duplicating observations.
- Never blindly average averages; when group sizes differ, combine their underlying sums and counts or use an explicitly weighted calculation.
- For latency and other skewed metrics, an average can hide severe tail behavior; use percentiles and sample counts when the domain requires them.
- Production `AVG` queries require explicit handling of numeric precision, currency, NULL semantics, authorization boundaries, query performance, and metric definition.