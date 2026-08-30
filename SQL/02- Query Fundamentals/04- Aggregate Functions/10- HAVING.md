# 10- HAVING

## Overview

`HAVING` filters groups **after aggregation**. It is primarily used with `GROUP BY` when the condition depends on an aggregate result such as `COUNT()`, `SUM()`, `AVG()`, `MIN()`, or `MAX()`.

For example, to find customers with at least 10 orders:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The key distinction is:

- `WHERE` filters individual source rows.
- `GROUP BY` forms groups.
- Aggregate functions calculate values for each group.
- `HAVING` filters those groups.

This makes `HAVING` particularly important for reporting, analytics, dashboards, fraud detection, operational metrics, and backend APIs that return aggregated data.

## WHERE vs HAVING

The most important rule is to understand what each clause operates on.

| Clause | Filters | Happens conceptually | Typical condition |
|---|---|---|---|
| `WHERE` | Individual rows | Before grouping | `status = 'paid'` |
| `GROUP BY` | Creates groups | After row filtering | `GROUP BY customer_id` |
| `HAVING` | Groups | After aggregation | `COUNT(*) >= 10` |
| `ORDER BY` | Final result | After grouping/filtering | `ORDER BY order_count DESC` |

Consider:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

The logical processing is approximately:

```text
orders
  │
  ▼
WHERE status = 'paid'
  │
  ▼
filtered rows
  │
  ▼
GROUP BY customer_id
  │
  ▼
COUNT(*) for each customer
  │
  ▼
HAVING COUNT(*) >= 10
  │
  ▼
final result
```

`WHERE` determines which rows are available to the aggregation. `HAVING` determines which resulting groups survive.

## Basic Syntax

```sql
SELECT
    grouping_column,
    aggregate_function(column)
FROM table_name
WHERE row_condition
GROUP BY grouping_column
HAVING aggregate_condition;
```

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

This returns only customers whose group contains at least 10 rows.

`HAVING` does not require `GROUP BY` in every SQL dialect. When used without grouping, the entire filtered result can be treated as one aggregate group.

For example:

```sql
SELECT
    COUNT(*) AS order_count
FROM orders
HAVING COUNT(*) > 100000;
```

This either returns one row or no rows depending on the aggregate result.

## Why HAVING Exists

Aggregate functions produce values that do not exist until rows have been grouped and aggregated.

For example:

```sql
COUNT(*)
SUM(total_amount)
AVG(total_amount)
```

cannot generally be evaluated as ordinary row-level predicates.

This query is conceptually incorrect:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE COUNT(*) >= 10
GROUP BY customer_id;
```

The problem is that `WHERE` operates before the grouping and aggregation stage.

The correct query is:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

`HAVING` exists to express predicates over grouped results.

## HAVING with COUNT

`COUNT()` is one of the most common uses of `HAVING`.

Find customers with more than five orders:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 5;
```

Find products appearing in at least 100 order lines:

```sql
SELECT
    product_id,
    COUNT(*) AS line_count
FROM order_items
GROUP BY product_id
HAVING COUNT(*) >= 100;
```

Find API endpoints receiving at least 10,000 requests:

```sql
SELECT
    service_name,
    endpoint,
    COUNT(*) AS request_count
FROM api_requests
GROUP BY
    service_name,
    endpoint
HAVING COUNT(*) >= 10000;
```

The predicate is evaluated once per group.

## HAVING with SUM

`HAVING` can filter based on accumulated values.

Find customers whose total purchase value exceeds `₹100,000`:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_spend
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total_amount) > 100000;
```

This is different from:

```sql
WHERE total_amount > 100000
```

The latter filters individual orders. The `HAVING` condition filters based on the customer's total across all qualifying orders.

## HAVING with AVG

Find products whose average selling price exceeds `₹5,000`:

```sql
SELECT
    product_id,
    AVG(unit_price) AS average_price
FROM order_items
GROUP BY product_id
HAVING AVG(unit_price) > 5000;
```

The database first calculates the average for each product and then applies the condition.

Be careful when NULL values are involved because `AVG()` ignores NULL input values.

## HAVING with MIN and MAX

Find customers whose maximum order exceeds `₹50,000`:

```sql
SELECT
    customer_id,
    MAX(total_amount) AS maximum_order
FROM orders
GROUP BY customer_id
HAVING MAX(total_amount) > 50000;
```

Find customers whose smallest order is at least `₹1,000`:

```sql
SELECT
    customer_id,
    MIN(total_amount) AS minimum_order
FROM orders
GROUP BY customer_id
HAVING MIN(total_amount) >= 1000;
```

These conditions operate on the aggregate value for each group rather than individual rows.

## HAVING with Multiple Conditions

Multiple aggregate conditions can be combined using logical operators:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS total_spend
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 5
   AND SUM(total_amount) >= 50000;
```

A customer must satisfy both conditions.

`OR` can also be used:

```sql
HAVING COUNT(*) >= 20
    OR SUM(total_amount) >= 100000;
```

Use parentheses when combining complex conditions:

```sql
HAVING
    (COUNT(*) >= 20 AND SUM(total_amount) >= 50000)
    OR MAX(total_amount) >= 25000;
```

Complex `HAVING` expressions should remain readable because they often encode business rules.

## HAVING with Multiple Grouping Columns

`HAVING` evaluates conditions at the same group grain established by `GROUP BY`.

For:

```sql
SELECT
    country,
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    country,
    status
HAVING COUNT(*) >= 100;
```

the condition is evaluated for each:

```text
(country, status)
```

combination.

For example:

| country | status | order_count |
|---|---|---:|
| IN | paid | 500 |
| IN | pending | 40 |
| US | paid | 250 |
| US | cancelled | 20 |

Only groups with at least 100 orders remain.

## WHERE and HAVING Together

Using both clauses is often the most efficient and expressive approach.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE
    status = 'paid'
    AND created_at >= DATE '2026-01-01'
GROUP BY customer_id
HAVING
    COUNT(*) >= 10
    AND SUM(total_amount) >= 100000;
```

The intended semantics are:

1. Ignore orders that are not paid.
2. Ignore orders before the reporting period.
3. Group remaining orders by customer.
4. Calculate order count and revenue.
5. Keep only customers satisfying the aggregate thresholds.

This is usually better than pushing row-level conditions into `HAVING`.

## Predicate Pushdown

A common production optimization is to move predicates that operate on individual rows from `HAVING` into `WHERE`.

Suppose:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 10;
```

The `HAVING` condition cannot simply be moved to `WHERE` because `COUNT(*)` does not exist until after grouping.

But a row-level condition such as:

```sql
HAVING status = 'paid'
```

should normally be expressed as:

```sql
WHERE status = 'paid'
```

when the query semantics allow it.

The difference matters because:

```text
WHERE
  ↓
reduces rows
  ↓
GROUP BY
  ↓
reduces into groups
  ↓
HAVING
```

Filtering earlier can reduce the amount of data that must be grouped.

## HAVING on Grouping Columns

A condition on a grouping column can often be expressed in either `WHERE` or `HAVING`, but `WHERE` is generally preferable because it filters before aggregation.

For example:

```sql
SELECT
    country,
    COUNT(*) AS user_count
FROM users
WHERE country = 'IN'
GROUP BY country;
```

is generally preferable to:

```sql
SELECT
    country,
    COUNT(*) AS user_count
FROM users
GROUP BY country
HAVING country = 'IN';
```

The second form can be valid, but it waits until after grouping to eliminate groups.

Prefer:

```sql
WHERE country = 'IN'
```

when the predicate is row-level.

## HAVING on Aggregate Aliases

Whether an aggregate alias can be referenced directly in `HAVING` depends on the SQL dialect.

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING order_count >= 10;
```

Some database systems support this syntax; others do not.

For portable SQL, use the aggregate expression:

```sql
HAVING COUNT(*) >= 10;
```

PostgreSQL, for example, does not generally allow a `SELECT`-list alias to be referenced in `HAVING`.

When writing production SQL intended for a specific database, follow that engine's documented behavior rather than relying on syntax accepted by another database.

## HAVING with NULL

Aggregate functions and NULL handling can affect `HAVING` results.

Consider:

```sql
SELECT
    customer_id,
    AVG(total_amount) AS average_order
FROM orders
GROUP BY customer_id
HAVING AVG(total_amount) > 1000;
```

`AVG()` ignores NULL `total_amount` values.

If a group contains only NULL values, the average is NULL. The expression:

```sql
NULL > 1000
```

does not evaluate to `TRUE`; it evaluates to `UNKNOWN`.

Therefore, the group does not pass the `HAVING` filter.

If the business rule requires explicit handling:

```sql
HAVING COALESCE(AVG(total_amount), 0) > 1000;
```

Use `COALESCE()` only when replacing NULL with zero accurately represents the business meaning.

## HAVING and COUNT Variants

The difference between `COUNT(*)`, `COUNT(column)`, and `COUNT(DISTINCT column)` matters when used in `HAVING`.

```sql
SELECT
    customer_id
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

Counts all rows.

```sql
SELECT
    customer_id
FROM orders
GROUP BY customer_id
HAVING COUNT(coupon_code) >= 10;
```

Counts only rows where `coupon_code` is not NULL.

```sql
SELECT
    customer_id
FROM orders
GROUP BY customer_id
HAVING COUNT(DISTINCT product_id) >= 10;
```

Counts distinct non-NULL products.

The correct expression depends on the business definition of the metric.

## HAVING with DISTINCT

`HAVING` can operate on distinct aggregates:

```sql
SELECT
    customer_id,
    COUNT(DISTINCT product_id) AS unique_products
FROM order_items
GROUP BY customer_id
HAVING COUNT(DISTINCT product_id) >= 20;
```

This finds customers who have purchased at least 20 distinct products.

`COUNT(DISTINCT ...)` can be substantially more expensive than `COUNT(*)` on large datasets because the database must identify unique values within each group.

## HAVING with Joins

`HAVING` is frequently used after joining related tables.

For example, find customers with at least five paid orders:

```sql
SELECT
    c.id AS customer_id,
    c.email,
    COUNT(o.id) AS paid_order_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid'
GROUP BY
    c.id,
    c.email
HAVING COUNT(o.id) >= 5;
```

The important sequence is:

```text
customers
    │
    ▼
JOIN orders
    │
    ▼
WHERE paid orders
    │
    ▼
GROUP BY customer
    │
    ▼
COUNT orders
    │
    ▼
HAVING count >= 5
```

Be careful with joins because aggregation happens over the joined rowset, not over the original tables independently.

## Join Multiplication and HAVING

A particularly dangerous production issue occurs when multiple one-to-many relationships are joined before aggregation.

Suppose a customer has:

```text
3 orders
4 support tickets
```

A direct join can create up to:

```text
3 × 4 = 12
```

intermediate rows.

Then:

```sql
COUNT(o.id)
```

may report `12` instead of `3`.

Using `HAVING` afterward does not fix the incorrect aggregation:

```sql
HAVING COUNT(o.id) >= 5
```

The group may incorrectly qualify.

A safer pattern is to aggregate each relationship separately before joining the results:

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

The general principle is:

> Aggregation must happen at the correct grain before unrelated one-to-many relationships are combined.

## HAVING with Date Ranges

Date filtering usually belongs in `WHERE`, while aggregate thresholds belong in `HAVING`.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE
    created_at >= TIMESTAMP '2026-01-01 00:00:00'
    AND created_at < TIMESTAMP '2026-02-01 00:00:00'
GROUP BY customer_id
HAVING
    COUNT(*) >= 10;
```

Using a half-open interval:

```text
[start, end)
```

avoids ambiguity around timestamps at the end of a period.

For timezone-sensitive business reporting, convert timestamps according to an explicitly defined reporting timezone rather than assuming the database session timezone matches the business requirement.

## HAVING and Query Performance

`HAVING` itself is not inherently slow. The cost depends on:

- Number of input rows
- Number of groups
- Aggregate complexity
- Join complexity
- `COUNT(DISTINCT ...)`
- Sorting or hashing requirements
- Available indexes
- Data distribution
- Database engine
- Memory available to the execution plan

A query such as:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

may require processing a large portion of the `orders` table.

If the query also has selective predicates:

```sql
WHERE created_at >= :start_time
  AND created_at < :end_time
```

the database may be able to reduce the input substantially before aggregation.

For PostgreSQL, inspect important queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE created_at >= DATE '2026-01-01'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

Pay attention to:

- Estimated vs actual row counts
- Sequential vs index scans
- Hash aggregate or sort aggregate
- Memory usage
- Temporary disk usage
- Execution time
- Rows removed by filters

## Indexing Considerations

Indexes cannot directly make every `HAVING COUNT(*)` condition cheap.

For:

```sql
GROUP BY customer_id
HAVING COUNT(*) >= 10
```

the database may still need to inspect many rows to determine each customer's count.

Indexes are more obviously useful for predicates such as:

```sql
WHERE tenant_id = :tenant_id
  AND created_at >= :start_time
  AND created_at < :end_time
```

An appropriate index might reduce the input to the aggregation.

For example, depending on workload:

```sql
CREATE INDEX idx_orders_tenant_created
ON orders (tenant_id, created_at);
```

Index design should be based on actual query patterns and execution plans, not merely on the presence of `GROUP BY` or `HAVING`.

## HAVING in Backend APIs

Aggregated SQL frequently powers reporting endpoints.

For example:

```text
GET /api/v1/customers/top-buyers
```

could execute:

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
HAVING
    COUNT(*) >= :minimum_orders
ORDER BY revenue DESC
LIMIT :limit;
```

The application should pass values through parameterized queries rather than constructing SQL through string concatenation.

For example, with Python database code:

```python
query = """
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE tenant_id = %s
      AND status = %s
      AND created_at >= %s
      AND created_at < %s
    GROUP BY customer_id
    HAVING COUNT(*) >= %s
    ORDER BY revenue DESC
    LIMIT %s
"""

cursor.execute(
    query,
    (
        tenant_id,
        "paid",
        start_time,
        end_time,
        minimum_orders,
        limit,
    ),
)
```

Parameterization protects value inputs from SQL injection and keeps query construction separate from user-provided data.

## Django ORM

Django expresses grouped aggregation through `values()` and `annotate()`.

For example:

```python
from django.db.models import Count, Sum

customers = (
    Order.objects
    .filter(status="paid")
    .values("customer_id")
    .annotate(
        order_count=Count("id"),
        revenue=Sum("total_amount"),
    )
    .filter(order_count__gte=10)
    .order_by("-revenue")
)
```

The ORM conceptually produces:

```sql
SELECT
    customer_id,
    COUNT(id) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(id) >= 10
ORDER BY revenue DESC;
```

When using ORM aggregation, inspect the generated SQL for complex queries. An ORM chain can hide expensive joins, grouping, or duplicate rows.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Using aggregate functions in `WHERE` | `WHERE` executes before aggregation | Use `HAVING` |
| Using `HAVING` for every filter | Confuses row-level and group-level filtering | Use `WHERE` for row predicates |
| Filtering grouping columns in `HAVING` unnecessarily | Filtering happens later than required | Prefer `WHERE` when semantics allow |
| Assuming aliases work everywhere in `HAVING` | SQL dialect differences | Use the aggregate expression for portability |
| Ignoring NULL behavior | Aggregates handle NULL differently | Understand each aggregate's NULL semantics |
| Using `COUNT(column)` when NULL rows should count | `COUNT(column)` ignores NULL | Use `COUNT(*)` when counting rows |
| Ignoring join multiplication | Aggregation operates on the joined rowset | Pre-aggregate independent one-to-many relationships |
| Assuming `HAVING` automatically improves performance | It filters after grouping | Reduce input with selective `WHERE` predicates |
| Using complex business logic directly in `HAVING` | Query becomes difficult to maintain | Keep expressions readable and document domain rules |
| Paginating grouped results without deterministic ordering | Ties can produce unstable pages | Add explicit tie-breakers |
| Trusting ORM output without inspecting SQL | ORM abstraction hides query shape | Review generated SQL and execution plans |

## Interview Traps

### Can HAVING Be Used Without GROUP BY?

Yes, depending on the SQL dialect and query form.

For example:

```sql
SELECT COUNT(*) AS order_count
FROM orders
HAVING COUNT(*) > 1000;
```

The aggregate result can be treated as a single group.

### Can WHERE and HAVING Be Used Together?

Yes, and this is common.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

`WHERE` filters rows; `HAVING` filters groups.

### Why Can't COUNT(*) Usually Be Used in WHERE?

Because `WHERE` is logically evaluated before grouping and aggregation.

Use:

```sql
HAVING COUNT(*) >= 10
```

instead.

### Which Is Usually Better: WHERE or HAVING?

Neither is universally "better." They solve different problems.

Use:

```sql
WHERE
```

for row-level predicates and:

```sql
HAVING
```

for group-level predicates.

If a condition can safely be evaluated before aggregation, filtering earlier can also reduce query work.

### Does HAVING Filter Rows or Groups?

It filters **groups**.

Given:

```sql
GROUP BY customer_id
HAVING COUNT(*) >= 10
```

the condition is evaluated once per customer group.

### Why Can HAVING Produce Incorrect Results in a Complex Query?

Usually because the input rowset is already incorrect.

Common causes include:

- Join multiplication
- Incorrect grouping grain
- Incorrect NULL assumptions
- Counting the wrong column
- Duplicate source rows

`HAVING` cannot correct an incorrectly constructed aggregation.

## Production Checklist

Before shipping a query containing `HAVING`:

- [ ] Define the result grain.
- [ ] Identify whether each predicate is row-level or group-level.
- [ ] Put row-level predicates in `WHERE` when appropriate.
- [ ] Use `HAVING` for aggregate/group-level conditions.
- [ ] Verify `COUNT(*)` vs `COUNT(column)` semantics.
- [ ] Check NULL behavior for all aggregates.
- [ ] Validate the grouping key.
- [ ] Check joins for row multiplication.
- [ ] Test aggregate results against known data.
- [ ] Inspect the execution plan for expensive reports.
- [ ] Verify indexes support selective `WHERE` and join predicates.
- [ ] Use parameterized SQL for application-supplied values.
- [ ] Define timezone semantics for date-based reporting.
- [ ] Use deterministic `ORDER BY` when paginating grouped results.
- [ ] Consider pre-aggregation, caching, or an analytical store for high-volume recurring reports.

## Key Takeaways

- `HAVING` filters **groups after aggregation**, while `WHERE` filters individual rows before aggregation.
- Use `WHERE` for selective row-level predicates and `HAVING` for conditions involving aggregate results such as `COUNT()`, `SUM()`, or `AVG()`.
- `HAVING` evaluates at the `GROUP BY` grain, so defining the correct result grain is essential.
- Join multiplication, NULL handling, and incorrect `COUNT` variants can produce wrong results even when the `HAVING` clause itself is valid.
- For production workloads, reduce input rows early, inspect execution plans, parameterize application values, and pre-aggregate or cache expensive recurring reports when appropriate.