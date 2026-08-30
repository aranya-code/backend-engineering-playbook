# 05- MIN and MAX

## Overview

`MIN` and `MAX` are SQL aggregate functions used to identify the smallest and largest value in a set of rows.

```sql
SELECT
    MIN(amount) AS minimum_amount,
    MAX(amount) AS maximum_amount
FROM payments;
```

They are commonly used for:

- Minimum and maximum prices
- Earliest and latest timestamps
- Lowest and highest scores
- Minimum and maximum processing times
- Operational thresholds
- Data-quality checks
- Reporting and dashboards
- Detecting unusual values

Although the syntax is simple, production usage requires understanding `NULL` behavior, data types, grouping, joins, ordering, indexes, timestamps, and the distinction between finding an extreme **value** and retrieving the **row associated with that value**.

## Basic Syntax

```sql
MIN(expression)
MAX(expression)
```

Example:

```sql
SELECT
    MIN(amount) AS minimum_payment,
    MAX(amount) AS maximum_payment
FROM payments;
```

`MIN` returns the lowest non-NULL value and `MAX` returns the highest non-NULL value.

They can operate on expressions:

```sql
SELECT
    MIN(quantity * unit_price) AS minimum_line_value,
    MAX(quantity * unit_price) AS maximum_line_value
FROM order_items;
```

## How MIN and MAX Work

Conceptually, the database scans the qualifying input values and maintains an aggregate state.

For:

```text
amount
------
100
250
75
500
```

the result is:

```text
MIN(amount) = 75
MAX(amount) = 500
```

The database optimizer may execute these operations using different strategies depending on the database, indexes, predicates, statistics, and query shape.

For example, a database may be able to exploit an appropriate index to locate an extreme value without scanning every table row.

This means query performance depends not only on the aggregate itself but also on:

- Filtering predicates
- Available indexes
- Data distribution
- Table size
- Query planner decisions
- Database engine
- Physical storage
- Concurrent workload

## NULL Behavior

`MIN` and `MAX` ignore `NULL` values.

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
SELECT
    MIN(score) AS minimum_score,
    MAX(score) AS maximum_score
FROM reviews;
```

returns:

```text
minimum_score = 10
maximum_score = 30
```

`NULL` is not treated as zero.

This distinction matters when `NULL` represents "unknown", "not measured", or "not applicable".

If the business meaning explicitly requires NULL to behave as zero:

```sql
SELECT
    MIN(COALESCE(score, 0)) AS minimum_score,
    MAX(COALESCE(score, 0)) AS maximum_score
FROM reviews;
```

Use `COALESCE` deliberately. Replacing unknown values with zero can change the meaning of the metric.

## No Rows and All-NULL Values

When no values participate in the aggregate, both `MIN` and `MAX` return `NULL`.

```sql
SELECT
    MIN(amount) AS minimum_amount,
    MAX(amount) AS maximum_amount
FROM payments
WHERE status = 'does_not_exist';
```

Result:

```text
minimum_amount = NULL
maximum_amount = NULL
```

The same applies when matching rows exist but the aggregated expression is NULL for all of them.

If an API contract requires a default:

```sql
SELECT
    COALESCE(MIN(amount), 0) AS minimum_amount,
    COALESCE(MAX(amount), 0) AS maximum_amount
FROM payments;
```

However, zero means something different from "no observations".

Prefer preserving `NULL` unless the application explicitly defines a fallback value.

## MIN and MAX with WHERE

Filtering controls the population from which the extreme value is calculated.

```sql
SELECT
    MIN(amount) AS minimum_payment,
    MAX(amount) AS maximum_payment
FROM payments
WHERE tenant_id = :tenant_id
  AND status = 'completed';
```

For time-based reporting:

```sql
SELECT
    MIN(amount) AS minimum_payment,
    MAX(amount) AS maximum_payment
FROM payments
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time;
```

The aggregate is calculated only after the filtering predicates determine the input rows.

## MIN and MAX with GROUP BY

`MIN` and `MAX` are frequently used to calculate boundaries per group.

```sql
SELECT
    customer_id,
    MIN(amount) AS smallest_payment,
    MAX(amount) AS largest_payment
FROM payments
WHERE status = 'completed'
GROUP BY customer_id;
```

For operational metrics:

```sql
SELECT
    service_name,
    MIN(response_time_ms) AS fastest_response_ms,
    MAX(response_time_ms) AS slowest_response_ms
FROM request_metrics
WHERE recorded_at >= :start_time
  AND recorded_at < :end_time
GROUP BY service_name;
```

The result contains one aggregate row per group.

## MIN and MAX with HAVING

`HAVING` can filter groups based on aggregate values.

```sql
SELECT
    customer_id,
    MIN(amount) AS minimum_payment,
    MAX(amount) AS maximum_payment
FROM payments
GROUP BY customer_id
HAVING MAX(amount) > 10000;
```

The important distinction is:

- `WHERE` filters rows before aggregation.
- `HAVING` filters groups after aggregation.

Conceptually:

```text
FROM
  ↓
WHERE
  ↓
GROUP BY
  ↓
MIN / MAX
  ↓
HAVING
  ↓
Result
```

## MIN and MAX with Different Data Types

`MIN` and `MAX` are not limited to numeric values.

They can operate on values with an ordering defined by the database.

| Data type | Example | Typical use |
|---|---|---|
| Integer | `100`, `500` | Numeric boundaries |
| Decimal | `19.99`, `99.99` | Monetary values |
| Date | `2026-08-01` | Earliest/latest date |
| Timestamp | `2026-08-30 12:00:00` | Event boundaries |
| String | `"alpha"`, `"zulu"` | Lexicographic boundaries |
| Boolean | Database-dependent ordering semantics | Specialized cases |

For timestamps:

```sql
SELECT
    MIN(created_at) AS first_created_at,
    MAX(created_at) AS last_created_at
FROM orders;
```

For dates:

```sql
SELECT
    MIN(due_date) AS earliest_due_date,
    MAX(due_date) AS latest_due_date
FROM invoices;
```

The result is based on the database's ordering rules for that data type.

## String MIN and MAX

`MIN` and `MAX` can be applied to strings where the database defines an ordering.

```sql
SELECT
    MIN(username) AS first_username,
    MAX(username) AS last_username
FROM users;
```

This does **not** mean the shortest and longest username.

It means the values at the lower and upper ends of the database's string ordering.

String ordering can depend on:

- Collation
- Database configuration
- Locale
- Case sensitivity
- Character encoding
- Database engine

Therefore, do not use string `MIN` or `MAX` when the requirement is actually based on string length.

Use:

```sql
SELECT
    MIN(LENGTH(username)) AS shortest_username,
    MAX(LENGTH(username)) AS longest_username
FROM users;
```

If you need the actual username, additional query logic is required.

## MIN/MAX Value vs Associated Row

A critical distinction is:

```sql
SELECT MAX(amount)
FROM payments;
```

This returns the maximum amount.

It does **not** return the payment row that contains that amount.

For example:

```text
id | amount
---+-------
1  | 100
2  | 500
3  | 250
```

The query:

```sql
SELECT MAX(amount)
FROM payments;
```

returns:

```text
500
```

If you need the corresponding payment:

```sql
SELECT id, amount, created_at
FROM payments
WHERE amount = (
    SELECT MAX(amount)
    FROM payments
);
```

This can return multiple rows if multiple payments share the maximum amount.

That may be correct or incorrect depending on the requirement.

## Retrieving the Top Row

If the requirement is "return the single highest-value payment", ordering is often clearer:

```sql
SELECT id, amount, created_at
FROM payments
ORDER BY amount DESC, id DESC
LIMIT 1;
```

The secondary `id` ordering makes the result deterministic when multiple rows have the same amount.

For the minimum:

```sql
SELECT id, amount, created_at
FROM payments
ORDER BY amount ASC, id ASC
LIMIT 1;
```

The choice between aggregation and ordering depends on the actual requirement:

| Requirement | Preferred approach |
|---|---|
| Find only the maximum value | `MAX()` |
| Find only the minimum value | `MIN()` |
| Return the row with the maximum value | `ORDER BY ... DESC LIMIT 1` or equivalent |
| Return all rows tied for maximum | `WHERE value = (SELECT MAX(...))` |
| Find maximum per group and associated row | Window functions or database-specific techniques |

## MAX Per Group with Associated Rows

A common production requirement is:

> Find the highest-value order for every customer.

A simple aggregate:

```sql
SELECT
    customer_id,
    MAX(total_amount) AS maximum_order_amount
FROM orders
GROUP BY customer_id;
```

returns the maximum value but not the order ID.

A window function can identify the actual row:

```sql
SELECT
    customer_id,
    id,
    total_amount,
    created_at
FROM (
    SELECT
        customer_id,
        id,
        total_amount,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS row_number
    FROM orders
) ranked
WHERE row_number = 1;
```

This produces one deterministic top order per customer.

If all tied maximum rows are required instead, `RANK()` can be appropriate:

```sql
SELECT
    customer_id,
    id,
    total_amount
FROM (
    SELECT
        customer_id,
        id,
        total_amount,
        RANK() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC
        ) AS rank
    FROM orders
) ranked
WHERE rank = 1;
```

The distinction between `ROW_NUMBER()` and `RANK()` is important:

- `ROW_NUMBER()` selects exactly one row per group.
- `RANK()` preserves ties.

## MIN/MAX and JOIN Cardinality

As with other aggregates, joins can change the input population.

Suppose:

```text
orders
  │
  └── order_items
```

and one order has several items.

A query such as:

```sql
SELECT
    MIN(o.total_amount),
    MAX(o.total_amount)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

may process the same order multiple times.

For `MIN` and `MAX`, duplicated values usually do not change the extreme itself:

```text
100
100
100
500
```

still has:

```text
MIN = 100
MAX = 500
```

This makes join duplication less visibly dangerous than with `AVG` or `SUM`.

However, the query may still be semantically incorrect if the join is intended to restrict the population or if additional aggregates are introduced.

For example:

```sql
SELECT
    MIN(o.total_amount),
    MAX(o.total_amount)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
WHERE oi.product_id = :product_id;
```

This means:

> Minimum and maximum order total among orders having at least one matching item.

That may be correct, but it is different from:

> Minimum and maximum value of the matching order items.

Define the metric's grain before constructing the query.

## MIN/MAX and DISTINCT

`MIN(DISTINCT expression)` and `MAX(DISTINCT expression)` generally produce the same extreme value as `MIN(expression)` and `MAX(expression)`.

For example:

```text
100
100
500
```

Both:

```sql
MIN(amount)
```

and:

```sql
MIN(DISTINCT amount)
```

return:

```text
100
```

Duplicates do not affect the minimum or maximum value.

Therefore, `DISTINCT` is generally unnecessary for these aggregates and can add unnecessary work or obscure the intent.

## MIN/MAX and Indexes

`MIN` and `MAX` can sometimes benefit significantly from suitable indexes.

Consider:

```sql
SELECT MAX(created_at)
FROM orders
WHERE tenant_id = :tenant_id;
```

An index such as:

```sql
CREATE INDEX idx_orders_tenant_created_at
ON orders (tenant_id, created_at);
```

may allow the database to locate the relevant boundary efficiently.

For:

```sql
SELECT MIN(created_at)
FROM orders
WHERE tenant_id = :tenant_id;
```

the same index may also be useful.

The actual execution plan determines whether the index is chosen.

Inspect it in PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT MAX(created_at)
FROM orders
WHERE tenant_id = 42;
```

Do not assume that an index is always beneficial. Consider:

- Predicate selectivity
- Index column order
- Table size
- Statistics
- Data distribution
- Visibility and heap access
- Write overhead
- Existing indexes

## Composite Index Design

Index column order matters.

For:

```sql
SELECT MAX(created_at)
FROM orders
WHERE tenant_id = :tenant_id
  AND status = 'completed';
```

an index such as:

```sql
CREATE INDEX idx_orders_tenant_status_created_at
ON orders (tenant_id, status, created_at);
```

can be a strong candidate because the equality predicates precede the timestamp being optimized.

Whether the optimizer uses it efficiently depends on the database and workload.

For high-volume systems, use `EXPLAIN (ANALYZE, BUFFERS)` rather than relying on theoretical index behavior.

## Latest and Earliest Records

`MIN` and `MAX` are often used to find temporal boundaries.

For example:

```sql
SELECT
    MIN(created_at) AS first_order_at,
    MAX(created_at) AS latest_order_at
FROM orders
WHERE customer_id = :customer_id;
```

This answers:

> What are the earliest and latest order timestamps?

It does not necessarily answer:

> What were the first and latest orders?

If the order row is required, use ordering or a window function.

```sql
SELECT id, created_at, total_amount
FROM orders
WHERE customer_id = :customer_id
ORDER BY created_at ASC, id ASC
LIMIT 1;
```

The secondary key is important because timestamps may not be unique.

## Timestamp Precision and Determinism

Suppose two events have:

```text
created_at = 2026-08-30 12:00:00
```

Then:

```sql
SELECT MAX(created_at)
FROM events;
```

cannot identify which event was latest.

If the application needs a deterministic latest event, define a tie-breaker:

```sql
SELECT id, created_at, event_type
FROM events
WHERE aggregate_id = :aggregate_id
ORDER BY created_at DESC, id DESC
LIMIT 1;
```

For distributed systems, timestamp ordering can be especially subtle because:

- Application clocks may differ.
- Multiple events can share timestamps.
- Clock precision varies.
- Events can arrive out of order.
- Database insertion order is not equivalent to business event order.

Choose the ordering field according to the business semantics rather than assuming `created_at` always represents causality.

## MIN/MAX and Conditional Aggregation

Multiple boundaries can be calculated from the same dataset.

PostgreSQL's `FILTER` syntax is concise:

```sql
SELECT
    MIN(amount) AS minimum_amount,
    MAX(amount) AS maximum_amount,
    MIN(amount) FILTER (
        WHERE status = 'completed'
    ) AS minimum_completed_amount,
    MAX(amount) FILTER (
        WHERE status = 'completed'
    ) AS maximum_completed_amount
FROM payments;
```

A portable alternative uses `CASE`:

```sql
SELECT
    MIN(CASE
        WHEN status = 'completed' THEN amount
    END) AS minimum_completed_amount,
    MAX(CASE
        WHEN status = 'completed' THEN amount
    END) AS maximum_completed_amount
FROM payments;
```

Rows that do not satisfy the condition produce NULL and are ignored by the aggregate.

## MIN/MAX for Data Quality

Extreme-value queries are useful for detecting bad data.

For example:

```sql
SELECT
    MIN(amount) AS minimum_amount,
    MAX(amount) AS maximum_amount
FROM payments;
```

If the domain requires:

```text
0 <= amount <= 1,000,000
```

an unexpected maximum can reveal:

- Unit conversion errors
- Currency mistakes
- Integer overflow
- Corrupt imports
- Duplicate transformations
- Incorrect API payloads
- Data migration bugs

For continuous validation, combine aggregates with explicit checks:

```sql
SELECT COUNT(*) AS invalid_payment_count
FROM payments
WHERE amount < 0
   OR amount > 1000000;
```

Aggregates are useful diagnostics, but domain constraints should ideally also be enforced at the database boundary where possible.

## MIN/MAX in Backend Applications

Django exposes these functions through `Min` and `Max`:

```python
from django.db.models import Max, Min

bounds = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="completed",
    )
    .aggregate(
        minimum_amount=Min("total_amount"),
        maximum_amount=Max("total_amount"),
    )
)
```

The resulting dictionary may contain:

```python
{
    "minimum_amount": Decimal("100.00"),
    "maximum_amount": Decimal("9500.00"),
}
```

If there are no qualifying values, the values can be `None`.

For grouped results:

```python
from django.db.models import Max, Min

customer_bounds = (
    Order.objects
    .filter(tenant_id=tenant_id, status="completed")
    .values("customer_id")
    .annotate(
        minimum_amount=Min("total_amount"),
        maximum_amount=Max("total_amount"),
    )
)
```

If the API needs the actual row corresponding to the maximum value, use appropriate ordering or window-function support rather than assuming `Max()` returns the object.

## MIN/MAX in API Design

An API reporting order boundaries might return:

```json
{
  "minimum_order_value": "100.00",
  "maximum_order_value": "9500.00",
  "currency": "INR",
  "sample_size": 842
}
```

Including `sample_size` helps consumers interpret the result.

For example:

```text
maximum = 100000
sample_size = 1
```

has a different operational meaning from:

```text
maximum = 100000
sample_size = 2,000,000
```

API contracts should explicitly define:

- Population
- Time window
- Filters
- NULL behavior
- Units
- Currency
- Precision
- Whether ties are possible
- Whether the metric is exact or eventually consistent

## Performance and Large Tables

For a large transactional table:

```sql
SELECT
    MIN(created_at),
    MAX(created_at)
FROM events
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time;
```

performance depends heavily on the filtering strategy and indexes.

For frequently requested historical boundaries, consider:

- Appropriate composite indexes
- Partitioning by time for very large datasets
- Summary tables
- Materialized views
- Precomputed reporting data
- Read replicas for read-heavy workloads
- Dedicated analytical systems for large-scale analytics

Do not prematurely denormalize every minimum or maximum value.

First establish:

1. Query frequency
2. Data volume
3. Latency requirement
4. Freshness requirement
5. Execution plan
6. Write/update cost

## Security and Multi-Tenant Systems

Aggregates must respect authorization boundaries.

For a multi-tenant system:

```sql
SELECT
    MIN(amount),
    MAX(amount)
FROM payments
WHERE tenant_id = :tenant_id;
```

The tenant boundary must come from trusted application context.

Do not allow clients to arbitrarily select another tenant's identifier and rely solely on application conventions.

For PostgreSQL deployments using Row-Level Security, database-enforced policies can provide an additional isolation boundary.

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT MIN(amount), MAX(amount)
    FROM payments
    WHERE tenant_id = %s
      AND status = %s
    """,
    [tenant_id, "completed"],
)
```

Never construct SQL by concatenating request parameters.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Assuming NULL means zero | Changes the metric's semantics | Preserve NULL unless zero is explicitly required |
| Assuming `MAX()` returns a row | It returns only the extreme value | Use ordering or a window function when the row is needed |
| Using `MAX()` to identify the latest entity | Multiple rows can share the same timestamp | Define deterministic ordering |
| Using string `MIN()` for shortest text | String ordering is not length | Use `MIN(LENGTH(...))` |
| Adding `DISTINCT` unnecessarily | Obscures intent and may add work | Use plain `MIN()`/`MAX()` |
| Ignoring JOIN semantics | The population may be different from the intended metric | Define row grain and join purpose |
| Assuming indexes guarantee performance | The optimizer may choose another plan | Inspect execution plans |
| Mixing currencies | Numeric extremes become meaningless across currencies | Group or normalize by currency |
| Replacing NULL with zero automatically | No observations become false observations | Define the API/business contract explicitly |
| Assuming latest timestamp identifies one row | Timestamps may tie | Add a deterministic tie-breaker |

## Interview Traps

### `MAX()` Does Not Return the Row

This:

```sql
SELECT MAX(amount)
FROM payments;
```

returns the value, not the payment record.

To return a row:

```sql
SELECT id, amount
FROM payments
ORDER BY amount DESC, id DESC
LIMIT 1;
```

### NULL Is Ignored

Given:

```text
10
20
NULL
30
```

both:

```sql
MIN(value)
```

and:

```sql
MAX(value)
```

ignore the NULL.

### No Matching Values Return NULL

```sql
SELECT MAX(amount)
FROM payments
WHERE false;
```

returns:

```text
NULL
```

not zero.

### Duplicate Rows Usually Do Not Change MIN/MAX

Unlike `SUM` and `AVG`, duplicate values do not change the minimum or maximum.

```text
100
100
500
```

and:

```text
100
500
```

both produce:

```text
MIN = 100
MAX = 500
```

This does not mean the join is necessarily semantically correct.

### MAX Timestamp Is Not the Same as Latest Row

```sql
SELECT MAX(created_at)
FROM events;
```

finds the greatest timestamp.

It does not identify which event owns that timestamp.

### Ties Must Be Handled Explicitly

If multiple rows share the maximum value, this:

```sql
SELECT id, amount
FROM payments
WHERE amount = (
    SELECT MAX(amount)
    FROM payments
);
```

can return multiple rows.

If exactly one row is required, define a deterministic tie-breaker:

```sql
SELECT id, amount
FROM payments
ORDER BY amount DESC, id DESC
LIMIT 1;
```

## Production Checklist

Before shipping a `MIN` or `MAX` query, verify:

- [ ] What population does the metric represent?
- [ ] Is the requirement for an extreme value or the associated row?
- [ ] What should happen when there are no observations?
- [ ] Are NULL values semantically correct?
- [ ] Can joins alter the intended population?
- [ ] Are timestamps sufficiently precise for the business requirement?
- [ ] Are ties handled deterministically?
- [ ] Are monetary values expressed in the same currency?
- [ ] Is the data type appropriate?
- [ ] Is the filtering path indexed appropriately?
- [ ] Has the execution plan been inspected at realistic scale?
- [ ] Does the query respect tenant and authorization boundaries?
- [ ] Is returning sample size useful for the API consumer?
- [ ] Is the metric fresh enough for the application's consistency requirements?

## Key Takeaways

- `MIN` and `MAX` return the smallest and largest non-NULL values; they return `NULL` when no value contributes to the aggregate.
- `MIN()` and `MAX()` return values, not the rows that contain those values; use ordering or window functions when associated row data is required.
- Temporal queries require explicit tie-breaking because the maximum timestamp does not necessarily identify a unique latest record.
- Correct aggregation still depends on defining the intended population and understanding JOIN behavior, even though duplicate values do not normally change `MIN` or `MAX`.
- Production performance depends on predicates, indexes, data volume, and the optimizer; validate important boundary queries with real execution plans.