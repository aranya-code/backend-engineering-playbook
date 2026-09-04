# 07- Aggregation Exercises

## Overview

Aggregation exercises test whether you can reason about **result grain, grouping, NULL semantics, joins, conditional logic, and cardinality** rather than simply remember `GROUP BY` syntax.

Aggregation is fundamental to backend systems because APIs, dashboards, billing systems, reporting pipelines, operational metrics, and analytics frequently require statements such as:

- How many orders did each customer place?
- What is the total revenue per day?
- Which products sold the most?
- Which customers exceeded a spending threshold?
- What percentage of orders were cancelled?
- What is the average order value by region?
- Which tenants exceeded their quota?
- How many active users performed an operation during a time window?

The most important question is:

> **What should one output row represent?**

If the answer is "one row per customer," every aggregation, join, and filter should preserve that intended grain.

---

## Practice Schema

Use the following PostgreSQL schema throughout the exercises:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    status text NOT NULL
        CHECK (status IN ('active', 'inactive', 'suspended')),
    organization_id bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku text NOT NULL UNIQUE,
    name text NOT NULL,
    price numeric(12, 2) NOT NULL
        CHECK (price >= 0),
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL
        REFERENCES customers(id),
    status text NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    total_amount numeric(12, 2) NOT NULL
        CHECK (total_amount >= 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    order_id bigint NOT NULL
        REFERENCES orders(id),
    product_id bigint NOT NULL
        REFERENCES products(id),
    quantity integer NOT NULL
        CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL
        CHECK (unit_price >= 0),
    PRIMARY KEY (order_id, product_id)
);
```

The important relationships are:

```text
customers
    │
    └──< orders
            │
            └──< order_items >── products
```

---

## Aggregation Mental Model

SQL aggregation transforms multiple input rows into fewer output rows.

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id;
```

The output grain is:

```text
one row per customer_id
```

The database conceptually performs:

```text
orders
   ↓
group rows by customer_id
   ↓
calculate COUNT(*)
   ↓
one output row per group
```

The grouping columns define the result grain.

---

## Basic COUNT Exercises

Count all orders:

```sql
SELECT COUNT(*) AS order_count
FROM orders;
```

Count completed orders:

```sql
SELECT COUNT(*) AS completed_order_count
FROM orders
WHERE status = 'completed';
```

Count orders by status:

```sql
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY status
ORDER BY status;
```

### Exercises

Write queries to:

1. Count all customers.
2. Count active customers.
3. Count inactive customers.
4. Count suspended customers.
5. Count products.
6. Count active products.
7. Count orders by customer.
8. Count orders by month.
9. Count orders by status.
10. Count order items by product.

---

## COUNT and NULL

These two expressions have different semantics:

```sql
COUNT(*)
```

and:

```sql
COUNT(column_name)
```

`COUNT(*)` counts rows.

`COUNT(column_name)` counts non-NULL values.

For a left join:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

a customer with no orders receives:

```text
order_count = 0
```

Using:

```sql
COUNT(*)
```

would count the preserved customer row and produce `1`.

---

## SUM Exercises

Calculate total order value:

```sql
SELECT
    SUM(total_amount) AS total_revenue
FROM orders
WHERE status = 'completed';
```

Calculate revenue by status:

```sql
SELECT
    status,
    SUM(total_amount) AS total_amount
FROM orders
GROUP BY status
ORDER BY status;
```

### Exercises

Write queries to:

1. Calculate completed revenue.
2. Calculate cancelled order value.
3. Calculate revenue per customer.
4. Calculate revenue per day.
5. Calculate revenue per month.
6. Calculate revenue per product using order items.
7. Calculate total quantity sold per product.
8. Calculate total quantity sold per customer.
9. Calculate revenue by order status.
10. Calculate revenue by tenant.

---

## AVG Exercises

Average completed order value:

```sql
SELECT
    AVG(total_amount) AS average_order_value
FROM orders
WHERE status = 'completed';
```

Average order value by customer:

```sql
SELECT
    customer_id,
    AVG(total_amount) AS average_order_value
FROM orders
GROUP BY customer_id;
```

### Important NULL Behavior

Aggregates such as:

```sql
AVG()
SUM()
MIN()
MAX()
```

ignore NULL input values.

However, `SUM()` over zero input rows returns `NULL`, not zero.

Therefore:

```sql
COALESCE(SUM(total_amount), 0)
```

is often appropriate when the API contract requires numeric zero.

---

## MIN and MAX

Find the largest completed order:

```sql
SELECT
    MAX(total_amount) AS largest_order
FROM orders
WHERE status = 'completed';
```

Find each customer's first and last order timestamps:

```sql
SELECT
    customer_id,
    MIN(created_at) AS first_order_at,
    MAX(created_at) AS last_order_at
FROM orders
GROUP BY customer_id;
```

### Exercises

Find:

1. Minimum order value per customer.
2. Maximum order value per customer.
3. First order timestamp per customer.
4. Latest order timestamp per customer.
5. Earliest completed order per month.
6. Largest completed order per month.
7. Price range across active products.

---

## GROUP BY Multiple Columns

You can group by more than one dimension:

```sql
SELECT
    status,
    date_trunc('month', created_at) AS month,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    status,
    date_trunc('month', created_at)
ORDER BY
    month,
    status;
```

The result grain is:

```text
one row per status + month
```

Not:

```text
one row per month
```

and not:

```text
one row per status
```

Always state the combined grouping key explicitly when reviewing an aggregation query.

---

## WHERE Versus HAVING

`WHERE` filters input rows before grouping.

`HAVING` filters groups after aggregation.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 5;
```

The processing intent is:

```text
orders
  ↓
WHERE status = completed
  ↓
GROUP BY customer
  ↓
COUNT
  ↓
HAVING count >= 5
```

### Exercises

Write queries to:

1. Find customers with at least five completed orders.
2. Find customers whose total completed revenue exceeds `10000`.
3. Find products with total quantity sold greater than `100`.
4. Find statuses with more than `1000` orders.
5. Find months with revenue above a threshold.

---

## Conditional Aggregation

Conditional aggregation is one of the most useful production SQL techniques.

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders
FROM orders
GROUP BY customer_id;
```

This produces one row per customer while calculating multiple metrics.

An alternative is:

```sql
SELECT
    customer_id,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled_orders
FROM orders
GROUP BY customer_id;
```

For PostgreSQL, `FILTER` is often clearer when calculating multiple conditional aggregates.

---

## Conditional Revenue

```sql
SELECT
    customer_id,
    SUM(total_amount) FILTER (
        WHERE status = 'completed'
    ) AS completed_revenue,
    SUM(total_amount) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_value
FROM orders
GROUP BY customer_id;
```

If customers without matching rows must receive zero rather than NULL:

```sql
COALESCE(
    SUM(total_amount) FILTER (
        WHERE status = 'completed'
    ),
    0
)
```

---

## Boolean Aggregation

PostgreSQL supports useful boolean aggregates.

For example:

```sql
SELECT
    customer_id,
    BOOL_OR(status = 'completed') AS has_completed_order,
    BOOL_AND(status <> 'cancelled') AS no_cancelled_orders
FROM orders
GROUP BY customer_id;
```

These can sometimes express business rules more directly than `COUNT` comparisons.

---

## Aggregation With LEFT JOIN

Return every customer and their order count:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email;
```

This is a critical pattern for dashboards and APIs because customers with zero orders remain visible.

---

## LEFT JOIN and Conditional Aggregation

Calculate completed orders while preserving customers with none:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) FILTER (
        WHERE o.status = 'completed'
    ) AS completed_orders
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email;
```

This is often preferable to placing:

```sql
WHERE o.status = 'completed'
```

because the latter removes customers with no matching completed order.

---

## JOIN Aggregation Pitfall

Consider:

```sql
SELECT
    c.id,
    SUM(o.total_amount) AS revenue
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id
GROUP BY c.id;
```

If an order has five items, the order row can participate five times.

If `o.total_amount` already represents the complete order value, revenue can be overstated.

This is one of the most common aggregation bugs in production systems.

---

## Avoiding Double Counting

If the order total is authoritative, do not join order items unnecessarily:

```sql
SELECT
    c.id,
    SUM(o.total_amount) AS revenue
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed'
GROUP BY c.id;
```

If item-level information is required, pre-aggregate it first.

```sql
WITH item_summary AS (
    SELECT
        order_id,
        SUM(quantity) AS total_quantity
    FROM order_items
    GROUP BY order_id
)
SELECT
    o.id,
    o.total_amount,
    item_summary.total_quantity
FROM orders AS o
JOIN item_summary
    ON item_summary.order_id = o.id;
```

The important principle is:

> **Aggregate at the correct grain before joining to another relation that can multiply rows.**

---

## Aggregation at Multiple Grains

A complex reporting query may involve:

```text
item
 ↓
order
 ↓
customer
 ↓
organization
```

Each layer has a different grain.

For example:

```text
order_items → one row per item
orders      → one row per order
customers   → one row per customer
organization→ one row per tenant
```

Do not aggregate an order-level metric after joining it to item-level data unless that multiplication is intentional.

---

## COUNT DISTINCT

Count unique customers who completed orders:

```sql
SELECT
    COUNT(DISTINCT customer_id) AS customers_with_completed_orders
FROM orders
WHERE status = 'completed';
```

Count distinct products purchased:

```sql
SELECT
    COUNT(DISTINCT oi.product_id) AS products_purchased
FROM order_items AS oi
JOIN orders AS o
    ON o.id = oi.order_id
WHERE o.status = 'completed';
```

`COUNT(DISTINCT ...)` is useful but can require more memory and computation than a simple count.

Do not use it automatically to hide join duplication.

---

## DISTINCT Versus GROUP BY

These can sometimes produce similar results:

```sql
SELECT DISTINCT customer_id
FROM orders;
```

and:

```sql
SELECT customer_id
FROM orders
GROUP BY customer_id;
```

But their intent differs.

Use `DISTINCT` when you need duplicate elimination.

Use `GROUP BY` when you are calculating aggregates or intentionally defining groups.

---

## Weighted Average

A common production reporting mistake is calculating an average of averages.

Suppose products have different quantities sold.

This:

```sql
AVG(unit_price)
```

may not represent the actual average selling price per unit if each row represents a different quantity.

A weighted average is:

```sql
SELECT
    SUM(unit_price * quantity)
    / NULLIF(SUM(quantity), 0) AS weighted_average_price
FROM order_items;
```

`NULLIF` prevents division by zero.

---

## Revenue From Order Items

If order totals should be derived from line items:

```sql
SELECT
    oi.order_id,
    SUM(oi.quantity * oi.unit_price) AS calculated_total
FROM order_items AS oi
GROUP BY oi.order_id;
```

Compare this against the stored order total:

```sql
SELECT
    o.id,
    o.total_amount AS stored_total,
    SUM(oi.quantity * oi.unit_price) AS calculated_total
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
GROUP BY
    o.id,
    o.total_amount;
```

This can be useful for reconciliation and integrity checks.

---

## Aggregation With CASE

Calculate revenue by status:

```sql
SELECT
    customer_id,
    SUM(
        CASE
            WHEN status = 'completed'
            THEN total_amount
            ELSE 0
        END
    ) AS completed_revenue
FROM orders
GROUP BY customer_id;
```

Be careful with NULL amounts if the schema permits them.

In the provided schema, `total_amount` is `NOT NULL`, so the expression is straightforward.

---

## Date-Based Aggregation

Daily order counts:

```sql
SELECT
    date_trunc('day', created_at) AS day,
    COUNT(*) AS order_count
FROM orders
GROUP BY date_trunc('day', created_at)
ORDER BY day;
```

Monthly revenue:

```sql
SELECT
    date_trunc('month', created_at) AS month,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY date_trunc('month', created_at)
ORDER BY month;
```

Always define the intended timezone when business reporting depends on local calendar boundaries.

`timestamptz` values are stored as instants; reporting by local day can require an explicit timezone conversion.

---

## Timezone-Aware Aggregation

For a business operating in a specific timezone:

```sql
SELECT
    date_trunc(
        'day',
        created_at AT TIME ZONE 'Asia/Kolkata'
    ) AS local_day,
    COUNT(*) AS order_count
FROM orders
GROUP BY 1
ORDER BY 1;
```

The correct timezone is a business requirement, not a database implementation detail.

---

## ROLLUP

PostgreSQL supports hierarchical grouping with `ROLLUP`.

```sql
SELECT
    status,
    date_trunc('month', created_at) AS month,
    COUNT(*) AS order_count
FROM orders
GROUP BY ROLLUP (
    status,
    date_trunc('month', created_at)
);
```

This can produce:

```text
status + month
status subtotal
grand total
```

Use `GROUPING()` when the output needs to distinguish subtotal rows from actual NULL values.

---

## GROUPING SETS

Multiple grouping levels can be calculated in one query:

```sql
SELECT
    status,
    date_trunc('month', created_at) AS month,
    COUNT(*) AS order_count
FROM orders
GROUP BY GROUPING SETS (
    (status, date_trunc('month', created_at)),
    (status),
    ()
);
```

This is useful for analytical reports that need several aggregation grains.

It is more common in reporting/OLAP workloads than latency-sensitive transactional API paths.

---

## Aggregation Exercises

Solve these without looking at the solutions:

1. Count all orders.
2. Count orders by status.
3. Count orders per customer.
4. Count completed orders per customer.
5. Count cancelled orders per customer.
6. Count orders per month.
7. Count active customers.
8. Count customers with at least one order.
9. Count customers with no orders.
10. Calculate total completed revenue.
11. Calculate revenue per customer.
12. Calculate average completed order value.
13. Find the largest order.
14. Find the smallest completed order.
15. Find each customer's first order date.
16. Find each customer's latest order date.
17. Find customers with more than five orders.
18. Find customers with more than five completed orders.
19. Find customers with completed revenue above `10000`.
20. Find products with more than `100` units sold.
21. Find products with more than `20` distinct orders.
22. Calculate total quantity sold per product.
23. Calculate completed revenue per month.
24. Calculate completed revenue per customer per month.
25. Calculate completed and cancelled order counts in one query.
26. Calculate completed and cancelled revenue in one query.
27. Calculate the percentage of orders that were completed.
28. Calculate the percentage of orders that were cancelled.
29. Calculate average order value per customer.
30. Find customers whose average completed order value exceeds `1000`.
31. Find the top five customers by completed revenue.
32. Find the top five products by quantity sold.
33. Find the top three customers by order count.
34. Find customers with both completed and cancelled orders.
35. Find customers with completed orders but no cancelled orders.
36. Find products never included in a completed order.
37. Calculate weighted average selling price per product.
38. Compare stored order totals with item-derived totals.
39. Calculate daily order counts in a specific timezone.
40. Produce monthly totals and grand totals using `ROLLUP`.

---

## Advanced Aggregation Exercises

### Customer Order Summary

Produce one row per customer containing:

- Total orders.
- Completed orders.
- Cancelled orders.
- Completed revenue.
- Average completed order value.
- First order timestamp.
- Latest order timestamp.

A PostgreSQL solution:

```sql
SELECT
    c.id,
    c.email,
    COUNT(o.id) AS total_orders,
    COUNT(o.id) FILTER (
        WHERE o.status = 'completed'
    ) AS completed_orders,
    COUNT(o.id) FILTER (
        WHERE o.status = 'cancelled'
    ) AS cancelled_orders,
    COALESCE(
        SUM(o.total_amount) FILTER (
            WHERE o.status = 'completed'
        ),
        0
    ) AS completed_revenue,
    AVG(o.total_amount) FILTER (
        WHERE o.status = 'completed'
    ) AS average_completed_order_value,
    MIN(o.created_at) AS first_order_at,
    MAX(o.created_at) AS latest_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email;
```

This is a useful production pattern for customer dashboards.

---

## Percentage Calculations

Calculate the percentage of completed orders:

```sql
SELECT
    100.0 * COUNT(*) FILTER (
        WHERE status = 'completed'
    ) / NULLIF(COUNT(*), 0) AS completed_percentage
FROM orders;
```

`100.0` ensures numeric division rather than integer truncation.

`NULLIF` protects against division by zero.

---

## Conditional Aggregation by Month

```sql
SELECT
    date_trunc('month', created_at) AS month,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders,
    COALESCE(
        SUM(total_amount) FILTER (
            WHERE status = 'completed'
        ),
        0
    ) AS completed_revenue
FROM orders
GROUP BY 1
ORDER BY 1;
```

This single query produces multiple operational metrics at the same grain.

---

## Aggregation and Window Functions

Aggregation and window functions solve different problems.

Aggregation reduces rows:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;
```

A window function preserves rows:

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

Use aggregation when you want one row per group.

Use window functions when you need group-level information while retaining individual rows.

---

## Top Customers

Top five customers by completed revenue:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
ORDER BY revenue DESC, customer_id
LIMIT 5;
```

The secondary ordering:

```sql
customer_id
```

makes the result deterministic when revenue values tie.

---

## Top Products

```sql
SELECT
    p.id,
    p.sku,
    p.name,
    SUM(oi.quantity) AS units_sold
FROM products AS p
JOIN order_items AS oi
    ON oi.product_id = p.id
JOIN orders AS o
    ON o.id = oi.order_id
WHERE o.status = 'completed'
GROUP BY
    p.id,
    p.sku,
    p.name
ORDER BY
    units_sold DESC,
    p.id
LIMIT 5;
```

The query aggregates at product grain after restricting orders to completed ones.

---

## Distinct Orders Per Product

```sql
SELECT
    oi.product_id,
    COUNT(DISTINCT oi.order_id) AS order_count
FROM order_items AS oi
JOIN orders AS o
    ON o.id = oi.order_id
WHERE o.status = 'completed'
GROUP BY oi.product_id;
```

This counts orders rather than individual line items.

---

## Products Ordered More Than Once

```sql
SELECT
    product_id,
    COUNT(DISTINCT order_id) AS order_count
FROM order_items
GROUP BY product_id
HAVING COUNT(DISTINCT order_id) > 1;
```

Be precise about what "ordered more than once" means.

It could mean:

- More than one order.
- More than one unit.
- More than one customer.
- More than one purchase event.

SQL cannot resolve ambiguous business semantics for you.

---

## Customers With Multiple Products

Find customers who purchased at least two distinct products:

```sql
SELECT
    o.customer_id,
    COUNT(DISTINCT oi.product_id) AS distinct_products
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
WHERE o.status = 'completed'
GROUP BY o.customer_id
HAVING COUNT(DISTINCT oi.product_id) >= 2;
```

The result grain is one row per customer.

---

## Aggregation and Pre-Aggregation

For large datasets, pre-aggregate before joining where doing so reduces cardinality.

Example:

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
    COALESCE(cr.revenue, 0) AS revenue
FROM customers AS c
LEFT JOIN customer_revenue AS cr
    ON cr.customer_id = c.id;
```

This creates a compact customer-level relation before the final join.

The optimizer may transform parts of the query, so always validate with `EXPLAIN`.

---

## Aggregation and Indexes

Indexes can help aggregation indirectly by reducing rows that must be scanned.

For example, if completed orders are frequently queried:

```sql
CREATE INDEX orders_completed_customer_idx
ON orders (customer_id)
WHERE status = 'completed';
```

This partial index can be valuable when:

- Completed orders are a subset of all orders.
- Queries frequently filter by `status = 'completed'`.
- The indexed columns support the access pattern.

Index design must be validated against actual workload and query plans.

---

## Aggregation and Partitioning

Large time-series tables often benefit from partitioning by time.

For example:

```text
orders
 ├── orders_2026_01
 ├── orders_2026_02
 ├── orders_2026_03
 └── ...
```

A query such as:

```sql
SELECT
    SUM(total_amount)
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

may benefit from partition pruning when the partitioning strategy matches the predicate.

Partitioning does not automatically make every aggregation faster.

It is primarily a data-management and workload-isolation technique that can also improve some query patterns.

---

## Aggregation and Materialized Views

Repeated expensive aggregations may justify a materialized view.

For example:

```sql
CREATE MATERIALIZED VIEW monthly_order_metrics AS
SELECT
    date_trunc('month', created_at) AS month,
    COUNT(*) AS order_count,
    SUM(total_amount) FILTER (
        WHERE status = 'completed'
    ) AS completed_revenue
FROM orders
GROUP BY 1;
```

Materialized views trade freshness for cheaper repeated reads.

Consider:

- Refresh frequency.
- Refresh duration.
- Locking behavior.
- Storage.
- Failure handling.
- Consumer expectations.

They are often better suited to reporting than transactional APIs requiring real-time data.

---

## Aggregation Performance

When an aggregation is slow, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

Look for:

- Sequential scans.
- Index or bitmap scans.
- Estimated versus actual rows.
- Hash aggregate memory.
- Sort operations.
- Temporary file usage.
- Partition pruning.
- Rows filtered before aggregation.
- Overall execution time.

A slow aggregation may be caused by:

- Too many input rows.
- Poor filtering.
- Missing indexes.
- Incorrect statistics.
- Expensive joins.
- Memory pressure.
- Data growth.
- Excessive query frequency.

---

## Hash Aggregate Versus Group Aggregate

PostgreSQL may use different aggregation strategies.

### Hash Aggregate

Conceptually:

```text
read rows
   ↓
hash by grouping key
   ↓
accumulate aggregate values
```

This can be efficient when the grouping state fits in memory.

### Group Aggregate

Conceptually:

```text
sorted input
   ↓
process each group
   ↓
emit aggregate
```

Sorting can be expensive, but an appropriate ordering path can sometimes make this efficient.

Do not optimize based on the operator name alone. Compare actual execution behavior.

---

## Aggregation Memory

Aggregation can consume significant memory when there are many distinct groups.

For example:

```text
GROUP BY customer_id
```

on hundreds of millions of distinct customer IDs can require substantial working memory.

At scale, consider:

- Filtering earlier.
- Pre-aggregation.
- Partitioning.
- Materialized summaries.
- Workload isolation.
- OLAP systems.
- Batch processing.

Increasing `work_mem` globally is rarely the first solution because memory is allocated per operation and can multiply across concurrent queries.

---

## Aggregation in OLTP APIs

A query such as:

```sql
SELECT
    COUNT(*)
FROM orders
WHERE customer_id = $1
  AND status = 'completed';
```

may be perfectly appropriate for an API.

A query scanning billions of rows to calculate historical global metrics probably belongs in a reporting or analytical workload.

A senior engineer distinguishes:

```text
transactional aggregation
```

from:

```text
analytical aggregation
```

and chooses the architecture accordingly.

---

## Aggregation in Django

Django exposes aggregation through ORM expressions:

```python
from django.db.models import Count, Sum

customer_metrics = (
    Customer.objects
    .annotate(
        order_count=Count("orders", distinct=True),
        completed_revenue=Sum(
            "orders__total_amount",
            filter=Q(orders__status="completed"),
        ),
    )
)
```

For complex aggregation:

- Inspect generated SQL.
- Check join cardinality.
- Verify `distinct=True` semantics.
- Avoid accidental relationship multiplication.
- Measure query latency.

ORM aggregation does not eliminate SQL-level correctness concerns.

---

## Aggregation in SQLAlchemy

SQLAlchemy can express grouped queries directly:

```python
from sqlalchemy import func, select

statement = (
    select(
        Order.customer_id,
        func.count(Order.id).label("order_count"),
        func.sum(Order.total_amount).label("revenue"),
    )
    .where(Order.status == "completed")
    .group_by(Order.customer_id)
)
```

For production systems, make the grouping semantics explicit in repository or service-layer code rather than returning arbitrary database rows to API callers.

---

## Aggregation Security

Aggregation can leak information even when individual records are not returned.

For example:

```text
COUNT(*) = 1
```

may reveal the existence of a sensitive record.

Tenant-scoped reporting should therefore enforce authorization before aggregation.

Example:

```sql
SELECT
    organization_id,
    COUNT(*) AS order_count
FROM orders
WHERE organization_id = $1
GROUP BY organization_id;
```

Do not rely solely on the fact that the query returns aggregate values.

The underlying rows still require authorization boundaries.

---

## Multi-Tenant Aggregation

For tenant-scoped systems:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE organization_id = $1
GROUP BY customer_id;
```

If tenant identity is represented in multiple related tables, validate that the relationship cannot cross tenant boundaries.

For systems using PostgreSQL RLS, ensure the aggregation executes under the expected role and tenant context.

---

## Aggregation and Read Replicas

Reporting aggregations may be routed to read replicas to reduce primary workload.

However:

```text
primary
   ↓ WAL
replica
   ↓
aggregation
```

means the report may be stale.

This is acceptable for:

- Dashboards with eventual consistency.
- Historical reports.
- Operational summaries with known freshness windows.

It may not be acceptable for:

- Immediately after a payment.
- Financial confirmation.
- Inventory decisions requiring current state.

---

## Aggregation and Caching

Frequently requested summaries can be cached:

```text
API
 ↓
Redis
 ↓ cache miss
PostgreSQL
 ↓
Redis
```

For example:

```text
customer:123:order-summary
```

The cache must have an explicit freshness and invalidation strategy.

Do not cache a highly dynamic aggregate indefinitely merely because it is expensive to compute.

---

## Aggregation and Background Jobs

Large reports should often be asynchronous:

```text
API
 ↓
create report job
 ↓
Celery
 ↓
PostgreSQL / replica / warehouse
 ↓
object storage
 ↓
client downloads report
```

This prevents long-running aggregations from consuming API workers and database connections.

Kafka can also support event-driven aggregation pipelines when near-real-time derived metrics are required.

---

## Aggregation Reliability

For asynchronous or incremental aggregation:

- Make processing idempotent.
- Track processing offsets/checkpoints.
- Handle duplicate events.
- Support replay.
- Reconcile derived totals against source data.
- Define freshness expectations.
- Make backfills safe.

A cached or materialized metric is a derived representation, not necessarily the authoritative source of truth.

---

## Aggregation and Concurrency

An aggregate query can observe data while concurrent transactions are modifying the underlying rows.

For example:

```sql
SELECT
    SUM(total_amount)
FROM orders
WHERE customer_id = $1;
```

does not automatically lock every order row.

The appropriate behavior depends on the transaction isolation level and business requirement.

If an aggregate is used to make a critical write decision, consider whether:

- A constraint can enforce the invariant.
- An atomic update is better.
- A lock is required.
- Serializable isolation is justified.
- The aggregate is informational only.

Do not assume aggregation itself provides synchronization.

---

## Aggregation Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Wrong `GROUP BY` grain | Incorrect result semantics | Define output grain first |
| `COUNT(*)` after `LEFT JOIN` | Zero-child parent becomes count 1 | Count nullable child key |
| Missing `COALESCE` | API receives NULL instead of zero | Normalize expected empty aggregates |
| `DISTINCT` hides join bugs | Incorrect cardinality remains | Fix relationship logic |
| Double-counted `SUM()` | Parent values multiply through child joins | Pre-aggregate or remove join |
| Average of averages | Statistically incorrect metric | Use weighted calculation |
| Integer division | Percentages truncated | Use numeric division |
| Ignoring timezone | Incorrect daily/monthly metrics | Define reporting timezone |
| Huge aggregation in API request | Worker/database pressure | Async reporting or OLAP |
| Global `work_mem` increase | Concurrent memory explosion | Optimize query and size carefully |
| Aggregating replica data as current | Stale results | Define consistency requirement |
| Aggregating unauthorized rows | Data leakage | Enforce tenant/resource authorization |
| Replacing durable data with cache | Derived state becomes source of truth | Keep authoritative source |

---

## Production Aggregation Review

Before shipping an important aggregate query, verify:

### Correctness

- What does one row represent?
- What rows are included?
- What statuses count?
- How are NULLs handled?
- What timezone defines date boundaries?
- Are duplicates possible?
- Are multiple one-to-many relationships involved?
- Can a join multiply an aggregate?

### Performance

- How many source rows are scanned?
- Is filtering selective?
- Are relevant indexes available?
- Is partition pruning effective?
- Is aggregation memory bounded?
- Are temporary files generated?
- Is the query executed frequently?
- Will concurrency multiply resource usage?

### Security

- Is tenant scope enforced?
- Is the aggregate itself sensitive?
- Can a small count reveal protected information?
- Does RLS apply correctly?
- Are query parameters bound safely?

### Reliability

- Is stale data acceptable?
- Can a replica be used?
- Should the result be cached?
- Should the query be asynchronous?
- Can derived metrics be rebuilt?
- Is there a reconciliation process?

---

## Senior Aggregation Decision Framework

When given an aggregation problem:

```text
Define output grain
        ↓
Define source population
        ↓
Define business filters
        ↓
Identify relationship cardinality
        ↓
Check for row multiplication
        ↓
Choose COUNT / SUM / AVG / MIN / MAX
        ↓
Choose conditional aggregation if needed
        ↓
Handle NULL and zero-result semantics
        ↓
Define timezone for temporal metrics
        ↓
Validate authorization / tenant scope
        ↓
Check indexes and partition pruning
        ↓
Inspect EXPLAIN
        ↓
Estimate workload and concurrency
        ↓
Choose API / cache / replica / async / OLAP architecture
```

The SQL expression is only one part of the solution.

The stronger interview answer explains:

> **What is being measured, at what grain, from which source rows, under which consistency and authorization requirements, and how the query behaves at production scale.**

---

## Final Aggregation Challenge

Design a query for:

> For one tenant, return the top 10 customers by completed revenue during the current calendar month. Include total completed orders, completed revenue, average completed order value, and the customer's most recent completed order timestamp. Customers with no completed orders must not appear. The result must be deterministic when revenue ties.

Before writing SQL, identify:

1. Result grain.
2. Tenant boundary.
3. Timezone.
4. Calendar-month boundaries.
5. Status filter.
6. Required aggregates.
7. Whether order items are needed.
8. Sorting and tie-breaking.
9. Index requirements.
10. Whether primary or replica consistency is required.

A possible implementation is:

```sql
SELECT
    c.id AS customer_id,
    c.email,
    COUNT(o.id) AS completed_orders,
    SUM(o.total_amount) AS completed_revenue,
    AVG(o.total_amount) AS average_completed_order_value,
    MAX(o.created_at) AS latest_completed_order_at
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.organization_id = $1
  AND o.status = 'completed'
  AND o.created_at >= $2
  AND o.created_at < $3
GROUP BY
    c.id,
    c.email
ORDER BY
    completed_revenue DESC,
    c.id ASC
LIMIT 10;
```

The application should calculate `$2` and `$3` using the tenant's intended reporting timezone.

For a high-volume production system, validate the query with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and evaluate whether the workload justifies a dedicated index, materialized summary, cache, read replica, or analytical pipeline.

---

## Practice Method

For every exercise:

1. State the expected result grain.
2. Identify the source tables.
3. Identify relationship cardinality.
4. Write the simplest correct query.
5. Test NULL and zero-row behavior.
6. Check for duplicate multiplication.
7. Validate aggregate semantics.
8. Test boundary conditions.
9. Inspect the execution plan for important queries.
10. Consider production workload and concurrency.

Do not move forward merely because you can reproduce an answer. For each exercise, be able to explain **why the query is correct, what assumptions it makes, and how it behaves when the dataset becomes large or concurrent**.

---

## Key Takeaways

- **Aggregation starts with result grain:** define whether each row represents a customer, order, product, day, month, or another business dimension before choosing grouping and joins.
- **Join cardinality determines aggregate correctness:** one-to-many joins can silently multiply rows and double-count `SUM`, `AVG`, and other metrics.
- **NULL, zero, and time semantics matter:** use `COUNT` variants, `COALESCE`, `NULLIF`, deterministic boundaries, and explicit timezones according to the business contract.
- **Production aggregation requires workload design:** indexes, memory, partitioning, replicas, caching, asynchronous jobs, and OLAP systems become important as data volume and query frequency grow.
- **Senior SQL reasoning connects metrics to architecture:** authorization, tenant isolation, consistency, concurrency, observability, and rebuildability are part of a correct aggregation design.