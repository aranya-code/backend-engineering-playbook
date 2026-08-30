# 14- Choosing the Right Aggregate

## Overview

SQL aggregate functions reduce multiple input rows into a smaller result, but choosing the correct aggregate is a **data semantics decision**, not merely a syntax choice.

The common aggregates answer different questions:

- `COUNT` — How many rows or non-NULL values exist?
- `SUM` — What is the total numeric value?
- `AVG` — What is the arithmetic mean?
- `MIN` — What is the smallest value?
- `MAX` — What is the largest value?
- `COUNT(DISTINCT ...)` — How many unique non-NULL values exist?

The correct aggregate depends on the business question, the input relation's grain, NULL semantics, join cardinality, and required output grain.

A reliable approach is:

```text
Business question
      ↓
Define the population
      ↓
Define the row grain
      ↓
Choose the aggregate
      ↓
Handle NULL semantics
      ↓
Validate joins and filters
      ↓
Validate execution cost
```

## Aggregate Selection

| Requirement | Typical aggregate | Example |
|---|---|---|
| Count every input row | `COUNT(*)` | Number of orders |
| Count non-NULL values | `COUNT(column)` | Orders with a recorded coupon |
| Count unique values | `COUNT(DISTINCT column)` | Active customers |
| Calculate a total | `SUM(column)` | Total revenue |
| Calculate an arithmetic mean | `AVG(column)` | Average order value |
| Find the smallest value | `MIN(column)` | Earliest order timestamp |
| Find the largest value | `MAX(column)` | Latest order timestamp |

The important distinction is between **what is being measured** and **how the database computes it**.

For example, "number of customers" usually does not mean:

```sql
COUNT(*)
```

when the input contains multiple rows per customer.

It may mean:

```sql
COUNT(DISTINCT customer_id)
```

or, depending on the query structure, one row per customer followed by another aggregation.

## COUNT

### What It Measures

`COUNT` measures cardinality.

Use:

```sql
COUNT(*)
```

when the requirement is:

> How many rows are in the input relation?

Example:

```sql
SELECT COUNT(*) AS order_count
FROM orders
WHERE status = 'paid';
```

This counts paid order rows.

### COUNT(column)

Use:

```sql
COUNT(column)
```

when the requirement is:

> How many rows contain a non-NULL value for this expression?

```sql
SELECT COUNT(shipped_at) AS shipped_order_count
FROM orders;
```

This counts orders where `shipped_at` is non-NULL.

### COUNT(DISTINCT column)

Use:

```sql
SELECT COUNT(DISTINCT customer_id) AS customer_count
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

when the requirement is:

> How many unique non-NULL customers appear in the input?

This is common in analytics and product metrics.

### Advantages

- Directly expresses cardinality.
- `COUNT(*)` has clear row-count semantics.
- Can be combined with `GROUP BY`.
- Can count unique values with `DISTINCT`.

### Limitations

- `COUNT(*)` does not identify business entities unless the input has that grain.
- `COUNT(column)` excludes NULL.
- `COUNT(DISTINCT ...)` can be considerably more expensive than a simple count on large, high-cardinality datasets.

## SUM

### What It Measures

`SUM` calculates the total of numeric values.

```sql
SELECT
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid';
```

Use it for additive measures such as:

- Revenue
- Units sold
- Credits consumed
- Storage consumed
- Transaction amounts

### SUM and NULL

NULL values are generally ignored.

If the input is:

| amount |
|---:|
| 100 |
| 200 |
| NULL |

then:

```text
SUM(amount) = 300
```

If there are no non-NULL values, the result can be NULL rather than zero.

When the business meaning requires zero:

```sql
SELECT COALESCE(SUM(total_amount), 0) AS revenue
FROM orders
WHERE customer_id = :customer_id;
```

### The Critical Question: Is the Measure Additive?

Do not automatically sum every numeric column.

For example:

```text
account_balance
```

is generally a snapshot rather than an additive event measure.

Summing balances across multiple snapshots can produce meaningless results.

By contrast:

```text
transaction_amount
```

is normally additive across transactions.

This distinction becomes important in financial reporting and analytics systems.

## AVG

### What It Measures

`AVG` calculates an arithmetic mean.

```sql
SELECT AVG(total_amount) AS average_order_value
FROM orders
WHERE status = 'paid';
```

Use it when the business question genuinely asks for an average.

### AVG and NULL

`AVG(column)` generally ignores NULL values.

Conceptually:

```text
AVG(column) = SUM(column) / COUNT(column)
```

not:

```text
SUM(column) / COUNT(*)
```

For:

| amount |
|---:|
| 100 |
| 300 |
| NULL |

the result is:

```text
AVG = 200
```

not:

```text
133.33
```

### Average of Averages Is Usually Wrong

Suppose two regions have:

```text
Region A → 10 orders, average = $100
Region B → 1000 orders, average = $20
```

A simple average of regional averages:

```text
(100 + 20) / 2 = 60
```

does not represent the overall average order value.

The correct calculation uses the underlying totals and counts:

```text
(10 × 100 + 1000 × 20) / (10 + 1000)
≈ 20.79
```

This is a common analytics and interview trap.

If you have already aggregated data, preserve the required numerator and denominator when a later weighted average is needed.

## MIN

### What It Measures

`MIN` returns the smallest value according to the database's comparison rules.

For timestamps:

```sql
SELECT MIN(created_at) AS first_order_at
FROM orders;
```

For numeric values:

```sql
SELECT MIN(total_amount) AS smallest_order
FROM orders;
```

For grouped data:

```sql
SELECT
    customer_id,
    MIN(created_at) AS first_order_at
FROM orders
GROUP BY customer_id;
```

### Common Uses

- First event timestamp
- Earliest deployment
- Lowest price
- Minimum observed latency
- Earliest customer activity

### NULL Behavior

NULL values are generally ignored by `MIN`.

If every input value is NULL, the result is generally NULL.

This matters when distinguishing:

```text
no recorded value
```

from:

```text
minimum value is zero
```

## MAX

### What It Measures

`MAX` returns the largest value according to the database's comparison rules.

```sql
SELECT MAX(created_at) AS latest_order_at
FROM orders;
```

For grouped data:

```sql
SELECT
    customer_id,
    MAX(created_at) AS latest_order_at
FROM orders
GROUP BY customer_id;
```

Common uses include:

- Last activity timestamp
- Latest order
- Highest price
- Maximum latency
- Highest transaction amount

Like `MIN`, NULL inputs are generally ignored.

## Choosing by Business Question

A useful decision table is:

| Business question | Correct starting point |
|---|---|
| How many orders occurred? | `COUNT(*)` |
| How many orders have tracking information? | `COUNT(tracking_number)` |
| How many unique customers ordered? | `COUNT(DISTINCT customer_id)` |
| What is total revenue? | `SUM(total_amount)` |
| What is average order value? | `AVG(total_amount)` |
| What was the first order? | `MIN(created_at)` |
| What was the latest order? | `MAX(created_at)` |
| What is the highest order amount? | `MAX(total_amount)` |
| What is the lowest order amount? | `MIN(total_amount)` |

The key is to translate the business question into a mathematical operation before writing SQL.

## Aggregates With GROUP BY

Aggregates become more useful when combined with grouping.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order_value,
    MIN(created_at) AS first_order_at,
    MAX(created_at) AS last_order_at
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;
```

The output grain is:

```text
one row per customer
```

Each aggregate answers a different question about that customer.

| Expression | Meaning |
|---|---|
| `COUNT(*)` | Number of qualifying orders |
| `SUM(total_amount)` | Total qualifying order value |
| `AVG(total_amount)` | Average qualifying order value |
| `MIN(created_at)` | First qualifying order timestamp |
| `MAX(created_at)` | Last qualifying order timestamp |

## Aggregation and Data Grain

The same aggregate can produce different meanings depending on the input grain.

Suppose the source contains:

```text
one row per order
```

Then:

```sql
SUM(total_amount)
```

can represent total order value.

But if the source has already been joined or transformed into:

```text
one row per order item
```

then summing an order-level `total_amount` can multiply the order total.

For example:

```text
Order 101
├── Item A
├── Item B
└── Item C
```

If `orders.total_amount = 300` and the order is represented by three item rows, then:

```sql
SUM(order_total)
```

can produce:

```text
300 + 300 + 300 = 900
```

instead of:

```text
300
```

Always establish the row grain before choosing an aggregate.

## Aggregation After JOINs

Join cardinality is one of the most common causes of incorrect aggregate results.

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

The relationship is:

```text
customer → orders
```

so `COUNT(o.id)` is appropriate.

Now suppose another one-to-many relationship is added:

```sql
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id
```

The relation can become:

```text
customer × orders × tickets
```

A customer with 3 orders and 4 tickets can produce 12 joined rows.

This can corrupt:

```text
COUNT
SUM
AVG
```

even though the SQL is syntactically valid.

### Safer Pattern

Aggregate each independent relationship at the required grain:

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

Each aggregate is calculated before the independent one-to-many relationships are combined.

## DISTINCT and Aggregate Choice

`DISTINCT` should represent a real uniqueness requirement.

Correct:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

Business meaning:

> Count unique customers who placed orders.

Potentially suspicious:

```sql
SELECT COUNT(DISTINCT o.id)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN support_tickets AS t
    ON t.customer_id = c.id;
```

If `DISTINCT` is only being used because a previous join multiplied rows, the query may be hiding a flawed data model for the aggregation.

`COUNT(DISTINCT ...)` can be appropriate, but it should not become a default repair strategy.

## Conditional Aggregation

Conditional aggregation is useful when multiple metrics must be calculated from the same input relation.

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'paid') AS paid_orders,
    COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders,
    SUM(total_amount) FILTER (WHERE status = 'paid') AS paid_revenue
FROM orders
GROUP BY customer_id;
```

`FILTER` syntax is supported by PostgreSQL and some other SQL implementations.

A more portable pattern is:

```sql
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_orders,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders,
    SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) AS paid_revenue
FROM orders
GROUP BY customer_id;
```

This avoids issuing separate scans for every metric in application code.

## Choosing Between COUNT and SUM for Conditions

These can both represent counts:

```sql
COUNT(*) FILTER (WHERE status = 'paid')
```

and:

```sql
SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)
```

The first directly expresses:

> Count rows satisfying this condition.

The second expresses:

> Sum one for each matching row.

Prefer the form that most clearly communicates the business meaning and matches the SQL dialect and team conventions.

## Choosing MIN/MAX vs ORDER BY LIMIT

These queries can look related but have different semantics.

To find the earliest timestamp:

```sql
SELECT MIN(created_at)
FROM orders;
```

To retrieve the complete earliest order:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount
FROM orders
ORDER BY created_at ASC, id ASC
LIMIT 1;
```

`MIN` returns a scalar value.

`ORDER BY ... LIMIT 1` returns a row.

If the requirement is:

> What is the earliest timestamp?

use `MIN`.

If the requirement is:

> Which order was earliest, and what are its other attributes?

you generally need row selection such as `ORDER BY ... LIMIT 1`, a window function, or another relational technique.

## Tie Handling

`MIN` and `MAX` do not identify a unique row.

If two orders have the same earliest timestamp:

```text
Order 101 → 2026-08-01 10:00
Order 102 → 2026-08-01 10:00
```

then:

```sql
MIN(created_at)
```

returns the timestamp, not which order should be selected.

For deterministic row selection:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM orders
ORDER BY created_at ASC, id ASC
LIMIT 1;
```

The secondary ordering criterion makes tie behavior deterministic.

This matters in production APIs, tests, pagination, and reconciliation jobs.

## Numeric Precision and SUM/AVG

For monetary values, aggregate semantics are affected by the underlying numeric type.

Prefer exact numeric representations appropriate to the database and application rather than binary floating-point types for financial amounts.

For PostgreSQL, a common choice is:

```sql
NUMERIC(19, 4)
```

or another precision/scale chosen according to the domain.

For example:

```sql
SELECT
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order_value
FROM orders;
```

The precision of the result depends on the database's numeric type and aggregate implementation.

Do not assume that converting monetary values to floating-point values in application code improves accuracy.

## Time-Based Aggregates

Time-based analytics often combine filtering, grouping, and aggregation.

For example:

```sql
SELECT
    DATE_TRUNC('day', created_at) AS day,
    COUNT(*) AS orders,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS average_order_value
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY day;
```

Important production considerations include:

- Use a half-open interval: `>= start` and `< end`.
- Define the timezone expected by the reporting requirement.
- Ensure the grouping expression matches the desired reporting calendar.
- Avoid accidentally mixing UTC storage with local-time reporting semantics.
- Validate the query against daylight-saving transitions when local time matters.

## Aggregates in Backend APIs

Suppose a FastAPI endpoint exposes customer metrics:

```text
GET /customers/{customer_id}/metrics
```

The database should generally calculate the metrics rather than transferring every order to Python.

A query might be:

```sql
SELECT
    COUNT(*) AS order_count,
    COALESCE(SUM(total_amount), 0) AS revenue,
    AVG(total_amount) AS average_order_value,
    MIN(created_at) AS first_order_at,
    MAX(created_at) AS last_order_at
FROM orders
WHERE customer_id = :customer_id
  AND status = 'paid';
```

The API layer should consume the aggregate result rather than performing:

```python
orders = load_all_orders()
total = sum(order.total_amount for order in orders)
```

The database is optimized for set-based operations and can avoid transferring unnecessary rows across the database connection.

## ORM Considerations

Django exposes these operations through its aggregation API:

```python
from django.db.models import Avg, Count, Max, Min, Sum

metrics = Order.objects.filter(
    customer_id=customer_id,
    status="paid",
).aggregate(
    order_count=Count("id"),
    revenue=Sum("total_amount"),
    average_order_value=Avg("total_amount"),
    first_order_at=Min("created_at"),
    last_order_at=Max("created_at"),
)
```

For grouped metrics:

```python
from django.db.models import Count, Sum

metrics = (
    Order.objects
    .filter(status="paid")
    .values("customer_id")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("total_amount"),
    )
)
```

The ORM does not remove the need to understand SQL semantics. In particular, inspect generated SQL when:

- Multiple relationships are involved.
- Aggregates appear alongside joins.
- `distinct=True` is introduced.
- Query performance changes unexpectedly.
- The grouping grain is non-trivial.

## Performance Considerations

Aggregate performance depends on more than the aggregate function.

Important factors include:

| Factor | Why it matters |
|---|---|
| Input row count | More rows may require more scanning and processing |
| Group cardinality | More groups can require more memory |
| Join cardinality | Multiplication increases aggregation work |
| `DISTINCT` | May require additional sorting or hashing |
| Filter selectivity | Reduces the number of rows entering aggregation |
| Index design | Can improve access paths for selective predicates |
| Data distribution | Skew can affect execution strategy |
| Parallel execution | Can improve large aggregation workloads when supported |

Inspect production-like plans:

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

Do not optimize based solely on whether a query uses an index. A sequential scan followed by an efficient aggregation can be the correct plan for a large range query.

## Scaling Large Aggregations

For high-volume systems, repeatedly aggregating billions of raw events may become expensive even when the SQL is logically correct.

Possible strategies include:

- Pre-aggregated reporting tables.
- Materialized views.
- Incremental aggregation pipelines.
- Time-partitioned tables.
- Appropriate indexes.
- Read replicas for reporting workloads.
- Dedicated analytics systems where OLTP databases are no longer appropriate.

For example:

```text
Kafka events
     ↓
Aggregation consumer
     ↓
Daily customer metrics
     ↓
Reporting API
     ↓
Dashboard
```

This can move expensive repeated aggregation away from the transactional database.

However, pre-aggregation introduces consistency and freshness trade-offs. The system must define whether metrics are:

```text
real-time
near-real-time
eventually consistent
```

before choosing the architecture.

## Common Mistakes

### Using COUNT(*) to Count Business Entities

Incorrect when multiple rows represent one entity:

```sql
SELECT COUNT(*)
FROM orders;
```

If the requirement is unique customers:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

### Treating NULL as Zero

This:

```sql
SUM(amount)
```

does not automatically mean:

```text
zero when no values exist
```

Use:

```sql
COALESCE(SUM(amount), 0)
```

only when zero is the intended business meaning.

### Averaging Already-Aggregated Averages

Avoid:

```text
AVG(region_average)
```

unless every region has equal statistical weight.

Use weighted aggregation based on the underlying counts and totals when the business metric requires an overall average.

### Summing Snapshot Values

A snapshot such as:

```text
account_balance
```

usually should not be summed across time.

Use event-based or period-end logic appropriate to the metric.

### Ignoring Join Multiplication

An aggregate can be mathematically correct over an incorrect relation.

Always inspect the relation immediately before aggregation.

### Using DISTINCT as a Repair Mechanism

`DISTINCT` can hide an incorrect join rather than fixing it.

Determine why duplicate business entities appear before adding `DISTINCT`.

### Returning MIN/MAX When the Requirement Is a Full Row

This:

```sql
SELECT MIN(created_at)
FROM orders;
```

does not return the corresponding order ID.

Use deterministic row-selection techniques when the full record is required.

## Production Checklist

Before shipping an aggregate query, verify:

- **Business metric:** What exactly is being measured?
- **Population:** Which rows should participate?
- **Grain:** What does one input row represent?
- **Output grain:** What does one result row represent?
- **NULL semantics:** Should NULL be ignored, preserved, or converted to zero?
- **Uniqueness:** Does the metric require `DISTINCT`?
- **Join cardinality:** Can any join multiply rows?
- **Numerical semantics:** Is the underlying type appropriate for the metric?
- **Time semantics:** Are timezone and interval boundaries correct?
- **Performance:** Is the input relation appropriately filtered?
- **Execution plan:** Has the query been evaluated with realistic data?
- **API behavior:** Does the application expect `NULL` or zero?
- **Scale:** Will the query remain acceptable as data volume grows?

## Key Takeaways

- **Choose an aggregate from the business question and data grain**, not from the column's data type alone.
- **`COUNT`, `SUM`, `AVG`, `MIN`, and `MAX` have different NULL and cardinality semantics** that directly affect production correctness.
- **Join cardinality must be validated before aggregation** because multiplied rows can silently corrupt counts, sums, and averages.
- **`DISTINCT`, `COALESCE`, and weighted calculations are semantic decisions**, not generic fixes for incorrect aggregate queries.
- **For large-scale systems, correctness comes first, then execution-plan validation and architectural decisions such as pre-aggregation or dedicated analytics workloads.**