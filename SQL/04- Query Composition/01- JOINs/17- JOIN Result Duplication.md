# 17- JOIN Result Duplication

## Overview

JOIN result duplication occurs when a query returns multiple rows representing the same logical entity because one or more JOINs match multiple rows.

The database is usually behaving correctly. The problem is that the query's **result grain** does not match the application's intended grain.

For example, suppose one customer has three orders:

```text
customers
+----+---------+
| id | name    |
+----+---------+
| 1  | Alice   |
+----+---------+

orders
+-----+-------------+--------+
| id  | customer_id | amount |
+-----+-------------+--------+
| 101 | 1           | 100    |
| 102 | 1           | 200    |
| 103 | 1           | 300    |
+-----+-------------+--------+
```

This query:

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

returns three rows for Alice:

```text
Alice → 101
Alice → 102
Alice → 103
```

If the application expects one row per customer, those rows may appear to be duplicates.

They are not duplicate database rows. They are different customer-order combinations.

The engineering problem is therefore not simply "remove duplicates." It is:

> **Determine why the result has multiple rows and make the query produce the intended grain.**

## Why JOINs Produce Duplicate-Looking Rows

A JOIN returns a row for each matching combination.

If one customer matches:

```text
3 orders
2 addresses
```

then joining both collections can produce:

```text
3 × 2 = 6 rows
```

For example:

```sql
SELECT
    c.id,
    o.id AS order_id,
    a.id AS address_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN addresses AS a
    ON a.customer_id = c.id;
```

The result represents combinations:

```text
customer 1
├── order 101 × address A
├── order 101 × address B
├── order 102 × address A
├── order 102 × address B
├── order 103 × address A
└── order 103 × address B
```

The database is correctly representing the Cartesian combinations implied by the relationships.

## The Most Important Question: What Is the Result Grain?

Before fixing duplication, define what one result row should represent.

Examples:

```text
One row per customer
One row per order
One row per order item
One row per customer-order relationship
One row per customer with aggregate order metrics
```

Consider:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

The result grain is:

```text
one row per order
```

because every order contributes a row.

If the intended grain is:

```text
one row per customer
```

then the query shape must change.

This distinction is more important than adding `DISTINCT`.

## A Typical Duplication Scenario

Consider an e-commerce system:

```text
customers
orders
order_items
```

The relationships are:

```text
customer 1 ───── N orders
order    1 ───── N order_items
```

A query such as:

```sql
SELECT
    c.id AS customer_id,
    o.id AS order_id,
    oi.id AS item_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

has the grain:

```text
one row per order item
```

If an order contains 10 items, the order appears 10 times.

If an API expects one row per order, this query cannot be directly serialized as one order object without additional processing.

## How to Diagnose JOIN Duplication

### Start With the Base Table

Check the expected number of entities:

```sql
SELECT COUNT(*)
FROM customers;
```

Then inspect the primary key:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT id) AS distinct_ids
FROM customers;
```

For a properly constrained primary key:

```text
total_rows = distinct_ids
```

### Add JOINs Incrementally

Start with:

```sql
SELECT COUNT(*)
FROM customers;
```

Then:

```sql
SELECT COUNT(*)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Then add the next relationship:

```sql
SELECT COUNT(*)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

The JOIN that causes the unexpected increase usually identifies the cardinality change.

### Compare Entity Counts

For a result expected to contain one row per customer:

```sql
SELECT
    COUNT(*) AS result_rows,
    COUNT(DISTINCT customer_id) AS customers
FROM (
    SELECT
        c.id AS customer_id,
        o.id AS order_id
    FROM customers AS c
    JOIN orders AS o
        ON o.customer_id = c.id
) AS result;
```

If:

```text
result_rows = 50,000
customers   = 10,000
```

the query returns an average of five rows per customer.

That may be correct if customers have multiple orders, but incorrect if the intended result is one row per customer.

## Find Which Entities Are Duplicated

Use `GROUP BY` to identify entities with multiple result rows:

```sql
SELECT
    c.id AS customer_id,
    COUNT(*) AS row_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id
HAVING COUNT(*) > 1
ORDER BY row_count DESC;
```

This helps identify high-cardinality entities.

For multiple relationships:

```sql
SELECT
    c.id AS customer_id,
    COUNT(*) AS row_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN addresses AS a
    ON a.customer_id = c.id
GROUP BY c.id
HAVING COUNT(*) > 1
ORDER BY row_count DESC;
```

Large counts can reveal multiplicative JOIN behavior.

## `DISTINCT` Is Not a General Fix

A common response to duplicated-looking rows is:

```sql
SELECT DISTINCT
    c.id,
    c.name
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

This can be correct when the requirement is:

> Return each customer once if they have at least one order.

But it can also hide a poorly designed query.

For example:

```sql
SELECT DISTINCT
    c.id,
    c.name,
    o.id,
    o.amount
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Every order can still be different, so `DISTINCT` does not collapse the rows.

The result is distinct based on the **entire selected row**, not just `customer_id`.

### When `DISTINCT` Is Appropriate

Use `DISTINCT` when:

- The query intentionally projects a smaller set of columns.
- Multiple JOIN paths can produce repeated projected values.
- The desired result is genuinely a set of unique projected rows.
- The performance cost is acceptable.

Do not use it merely because a JOIN produced more rows than expected.

## Prefer `EXISTS` for Existence Checks

If the requirement is:

> Return customers who have at least one completed order.

A JOIN produces order rows:

```sql
SELECT DISTINCT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

An existence predicate expresses the requirement directly:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'completed'
);
```

This avoids creating a result row for every matching order when the application only needs to know whether a match exists.

A suitable index can improve the lookup:

```sql
CREATE INDEX idx_orders_customer_status
    ON orders(customer_id, status);
```

The exact optimal index depends on the workload and existing indexes.

## Pre-Aggregate Before Joining

Suppose the API needs one row per customer with the total completed-order value.

Do not join every order and then attempt to collapse the result:

```sql
SELECT
    c.id,
    SUM(o.amount) AS total_amount
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed'
GROUP BY c.id;
```

Instead, establish one row per customer in the order aggregation:

```sql
SELECT
    c.id,
    c.email,
    COALESCE(o.total_amount, 0) AS total_amount
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        SUM(amount) AS total_amount
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
) AS o
    ON o.customer_id = c.id;
```

The subquery has a known grain:

```text
one row per customer
```

The outer JOIN therefore preserves the intended customer-level grain.

## Avoid Multiplying Independent One-to-Many Relationships

Consider:

```text
Customer
├── Orders
└── Addresses
```

Suppose:

```text
Customer 1
5 orders
4 addresses
```

This query:

```sql
SELECT
    c.id,
    o.id AS order_id,
    a.id AS address_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN addresses AS a
    ON a.customer_id = c.id;
```

can return:

```text
5 × 4 = 20 rows
```

This is often the most dangerous form of JOIN duplication because developers may expect:

```text
5 orders + 4 addresses
```

but SQL produces:

```text
20 combinations
```

### Better Query Shapes

Depending on the requirement, use:

- Separate queries.
- Pre-aggregation.
- `EXISTS`.
- LATERAL queries.
- JSON aggregation.
- Application-side assembly for bounded collections.

For example, if the API needs order and address counts:

```sql
SELECT
    c.id,
    COALESCE(o.order_count, 0) AS order_count,
    COALESCE(a.address_count, 0) AS address_count
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) AS o
    ON o.customer_id = c.id
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS address_count
    FROM addresses
    GROUP BY customer_id
) AS a
    ON a.customer_id = c.id;
```

Each derived relation has one row per customer, preventing cross-multiplication.

## Correcting Duplicate Aggregates

Suppose:

```text
Customer 1
3 orders
2 addresses
```

This query:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN addresses AS a
    ON a.customer_id = c.id
GROUP BY c.id;
```

can calculate:

```text
3 × 2 = 6
```

for `COUNT(o.id)`.

One possible correction is:

```sql
COUNT(DISTINCT o.id)
```

```sql
SELECT
    c.id,
    COUNT(DISTINCT o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN addresses AS a
    ON a.customer_id = c.id
GROUP BY c.id;
```

But if several aggregates are required, pre-aggregation is often more robust:

```sql
SELECT
    c.id,
    COALESCE(o.order_count, 0) AS order_count,
    COALESCE(a.address_count, 0) AS address_count
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) AS o
    ON o.customer_id = c.id
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS address_count
    FROM addresses
    GROUP BY customer_id
) AS a
    ON a.customer_id = c.id;
```

## `SUM()` Can Be Silently Wrong

Duplication is especially dangerous for monetary values.

Suppose:

```text
Orders:
$100
$200
$300

Addresses:
2
```

A direct JOIN can produce each order twice.

Then:

```sql
SUM(o.amount)
```

returns:

```text
$1,200
```

instead of:

```text
$600
```

This is more dangerous than visibly duplicated rows because the final result may look perfectly reasonable.

For financial reporting, always validate the query grain before trusting aggregates.

## `GROUP BY` Does Not Automatically Fix Duplication

Another common mistake is adding:

```sql
GROUP BY c.id;
```

without understanding which values are being aggregated.

For example:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id, o.id;
```

still has one row per customer-order pair.

Grouping does not magically make a result one row per customer.

To produce one row per customer, every non-grouped attribute must either:

- Be functionally determined by the grouped columns.
- Be aggregated.
- Be removed from the result.

For example:

```sql
SELECT
    c.id,
    MAX(o.created_at) AS latest_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

has one row per customer.

## PostgreSQL `DISTINCT ON`

PostgreSQL provides `DISTINCT ON` for selecting one row from each group.

For example, to retrieve the latest order per customer:

```sql
SELECT DISTINCT ON (o.customer_id)
    o.customer_id,
    o.id,
    o.created_at,
    o.amount
FROM orders AS o
ORDER BY
    o.customer_id,
    o.created_at DESC,
    o.id DESC;
```

The ordering determines which row survives for each customer.

This is useful for PostgreSQL-specific workloads, but it should be used deliberately because it is not portable SQL.

A suitable index can help:

```sql
CREATE INDEX idx_orders_customer_created
    ON orders(customer_id, created_at DESC, id DESC);
```

## Window Functions

Window functions provide another way to identify one row from each relationship.

For example:

```sql
SELECT
    customer_id,
    id,
    created_at,
    amount
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS row_number
    FROM orders AS o
) AS ranked
WHERE row_number = 1;
```

This produces one order per customer.

Window functions are particularly useful when the selection rule is more complex than a simple aggregate.

The important point is that the query establishes the desired grain before joining the result to other tables.

## `LEFT JOIN` and Apparent Duplicates

`LEFT JOIN` can preserve a parent even when there is no child:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

For a customer with no orders:

```text
customer_id | order_id
------------+---------
42          | NULL
```

For a customer with three orders:

```text
customer_id | order_id
------------+---------
42          | 101
42          | 102
42          | 103
```

The NULL row is not a duplicate. It represents the unmatched side of the outer JOIN.

## JOIN Conditions Can Create Accidental Duplication

Incorrect or incomplete JOIN conditions can create far more rows than expected.

Suppose the intended relationship is:

```text
tenant_id + customer_id
```

but the query joins only on:

```sql
ON o.customer_id = c.id
```

while the system is multi-tenant.

Rows from other tenants may match.

A safer condition may be:

```sql
ON o.customer_id = c.id
AND o.tenant_id = c.tenant_id
```

The exact schema and constraints determine the correct predicate.

This is both a correctness and security issue in multi-tenant systems.

## Joining on Non-Unique Columns

Joining on a non-unique business attribute can produce unexpected multiplicity.

For example:

```sql
SELECT
    u.id,
    d.id
FROM users AS u
JOIN departments AS d
    ON d.name = u.department_name;
```

If department names are not unique, one user can match multiple departments.

Prefer stable, constrained identifiers:

```sql
SELECT
    u.id,
    d.id
FROM users AS u
JOIN departments AS d
    ON d.id = u.department_id;
```

Foreign keys and unique constraints make cardinality assumptions explicit and enforceable.

## ORM-Level Duplication

ORMs can hide SQL JOIN behavior.

In Django:

```python
users = User.objects.filter(
    orders__status="completed"
)
```

may return the same user multiple times when multiple completed orders match.

If the requirement is one user per result:

```python
users = User.objects.filter(
    orders__status="completed"
).distinct()
```

may be appropriate.

For existence checks, prefer an `Exists` expression when it better matches the requirement:

```python
from django.db.models import Exists, OuterRef

completed_orders = Order.objects.filter(
    user_id=OuterRef("pk"),
    status="completed",
)

users = User.objects.annotate(
    has_completed_order=Exists(completed_orders)
).filter(
    has_completed_order=True,
)
```

For production debugging, inspect the SQL generated by the ORM rather than reasoning only from Python relationships.

## API Response Duplication

JOIN duplication frequently becomes an API-level problem.

Suppose an endpoint returns:

```text
GET /customers
```

and directly maps a JOIN result into JSON:

```json
[
  {
    "id": 1,
    "email": "alice@example.com",
    "order_id": 101
  },
  {
    "id": 1,
    "email": "alice@example.com",
    "order_id": 102
  }
]
```

The database result is valid, but the API contract may be wrong.

If the endpoint represents customers, a better response shape might be:

```json
[
  {
    "id": 1,
    "email": "alice@example.com"
  }
]
```

with orders exposed through a separate paginated resource.

Alternatively, if orders genuinely belong in the same response:

```json
[
  {
    "id": 1,
    "email": "alice@example.com",
    "orders": [
      {"id": 101},
      {"id": 102}
    ]
  }
]
```

The application must explicitly reconstruct the hierarchical shape rather than assuming flat JOIN rows are already an API representation.

## Pagination and JOIN Duplication

Pagination is particularly sensitive to row multiplication.

Suppose:

```text
Customer 1 → 100 orders
Customer 2 → 2 orders
Customer 3 → 1 order
```

This query:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
ORDER BY c.id, o.id
LIMIT 20;
```

returns 20 joined rows, not 20 customers.

Customer 1 can consume the entire page.

If the endpoint is supposed to paginate customers, paginate the customer relation first.

For example:

```sql
WITH paged_customers AS (
    SELECT
        id,
        email
    FROM customers
    WHERE id > :last_customer_id
    ORDER BY id
    LIMIT 20
)
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM paged_customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
ORDER BY c.id, o.id;
```

The exact application strategy depends on how the response is assembled, but the key is that pagination occurs at the intended entity grain.

## Query Planner and Performance

JOIN duplication is not only a correctness problem.

A query can generate a large intermediate result even if the final response contains only a few rows.

For example:

```text
10,000 customers
        ↓
500,000 orders
        ↓
2,000,000 order items
```

A multi-table JOIN can produce millions of intermediate rows.

That can increase:

- CPU usage.
- Memory consumption.
- Sort cost.
- Hash-table size.
- Temporary disk usage.
- Network transfer.
- Application memory.
- Serialization cost.

For critical queries, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ...
```

Pay particular attention to:

```text
estimated rows
actual rows
loops
buffer reads
temporary file usage
```

A large difference between estimated and actual rows can indicate poor cardinality estimates and lead to inefficient join strategies.

## Preventing Duplication With Database Constraints

If the application assumes a relationship is one-to-one, enforce that assumption.

For example:

```sql
CREATE TABLE user_profiles (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    timezone TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

Now:

```text
users 1 ───── 0..1 user_profiles
```

is enforced by the database.

Without `UNIQUE (user_id)`, the application might assume one profile exists while the database permits many.

This is a common source of unexpected JOIN multiplication.

## Production Considerations

### Correctness

Validate the result against the intended business grain.

For reporting queries, compare:

```text
database source totals
vs.
query totals
```

before deploying.

For financial or billing data, test edge cases involving:

- Multiple child records.
- Missing relationships.
- Duplicate business identifiers.
- NULL values.
- Historical records.
- Soft-deleted records.

### Performance

Avoid retrieving rows that the application does not need.

If the requirement is:

```text
Does a matching row exist?
```

use `EXISTS`.

If the requirement is:

```text
What is the total?
```

aggregate.

If the requirement is:

```text
Give me the latest record.
```

use a query shape that selects one record per parent.

### Scalability

Test cardinality with realistic high-volume entities.

A query that works for:

```text
10 orders/customer
```

may fail for:

```text
100,000 orders/customer
```

especially when combined with other one-to-many relationships.

### Monitoring

Monitor:

- Query latency.
- Rows processed.
- Rows returned.
- Buffer usage.
- Temporary disk activity.
- Database CPU.
- Connection utilization.

A sudden increase in query row counts can indicate a data or query regression even when application-level error rates remain normal.

### Security

Incorrect JOIN predicates can cause cross-tenant data exposure.

For tenant-aware schemas, ensure all required tenant boundaries participate in the JOIN and filtering logic.

Do not assume a foreign key alone enforces tenant isolation.

## Common Mistakes

| Mistake | Problem | Better approach |
|---|---|---|
| Adding `DISTINCT` immediately | Hides the underlying cardinality issue | Determine why rows multiply |
| Joining two one-to-many tables directly | Produces `N × M` combinations | Pre-aggregate or query independently |
| Counting after a multiplying JOIN | Inflated counts | Use `COUNT(DISTINCT ...)` or pre-aggregate |
| Summing after a multiplying JOIN | Inflated monetary metrics | Aggregate before joining |
| Joining on non-unique columns | One row can match many unexpected rows | Join on constrained identifiers |
| Assuming FK means one-to-one | Foreign keys do not imply uniqueness | Add a unique constraint when required |
| Paginating joined rows | Pages contain fewer parent entities than expected | Paginate at the intended grain |
| Using JOIN for existence | Produces unnecessary matching rows | Prefer `EXISTS` |
| Using `GROUP BY` blindly | Does not necessarily remove logical duplication | Define the target grain first |
| Ignoring ORM-generated SQL | JOIN expansion is hidden behind abstractions | Inspect generated SQL |
| Testing only small datasets | Cardinality explosions remain invisible | Test realistic production-scale data |
| Ignoring tenant predicates | Cross-tenant matches can occur | Include complete tenant-aware JOIN conditions |

## A Practical Debugging Workflow

When a production query unexpectedly returns duplicate entities:

1. **Define the expected grain.**  
   State exactly what one result row should represent.

2. **Check the base relation.**  
   Confirm that its primary key is unique and determine the expected row count.

3. **Add JOINs incrementally.**  
   Identify which JOIN changes the result cardinality.

4. **Inspect relationship uniqueness.**  
   Check primary keys, foreign keys, and unique constraints.

5. **Count matches per parent.**  
   Use `GROUP BY ... HAVING COUNT(*) > 1` to identify high-cardinality relationships.

6. **Check for independent one-to-many relationships.**  
   Look for `N × M` multiplication.

7. **Check JOIN predicates.**  
   Verify every column required to uniquely identify the relationship is included.

8. **Review aggregates.**  
   Verify `COUNT`, `SUM`, `AVG`, and window functions operate at the intended grain.

9. **Choose the correct query shape.**  
   Consider `EXISTS`, pre-aggregation, window functions, `DISTINCT ON`, or separate queries.

10. **Inspect the execution plan.**  
    Use `EXPLAIN (ANALYZE, BUFFERS)` with realistic data.

11. **Validate the API contract.**  
    Ensure the database result grain matches what the application and serializer expect.

## Interview Traps

| Question | Strong answer |
|---|---|
| Why does a JOIN produce duplicate rows? | A row is returned for every matching combination; multiple child rows therefore repeat the parent columns. |
| Are JOIN duplicates actually duplicate database records? | Usually no. They are often distinct result rows representing different relationships. |
| Why doesn't `DISTINCT` always fix JOIN duplication? | `DISTINCT` compares the complete projected row. Different child columns still make rows distinct. |
| What happens when two one-to-many tables are joined? | Their matching rows can multiply, producing `N × M` combinations per parent. |
| Why can `COUNT()` be wrong after a JOIN? | JOIN multiplication can cause the same logical entity to appear multiple times. |
| Why can `SUM()` be wrong after a JOIN? | A value can be repeated once for every matching row from another relationship. |
| When should `EXISTS` be preferred? | When the requirement is only whether at least one matching row exists. |
| How can you preserve one row per parent while calculating child metrics? | Pre-aggregate the child relation by parent before joining it. |
| How do you guarantee one-to-one JOIN behavior? | Use a foreign key plus a unique constraint on the referencing column. |
| Why can pagination break after a JOIN? | `LIMIT` applies to result rows, which may represent child relationships rather than parent entities. |
| How do you debug unexpected JOIN multiplication? | Define the grain, add JOINs incrementally, inspect match counts, verify constraints, and inspect the execution plan. |
| What is the danger of joining on a non-unique column? | A single row may match multiple rows, unexpectedly increasing result cardinality. |
| Can JOIN duplication become a security issue? | Yes. Incorrect multi-tenant JOIN predicates can expose records from another tenant. |

## Key Takeaways

- **JOIN result duplication usually reflects row multiplication, not duplicate database records; first determine the intended result grain.**
- **`DISTINCT` can remove repeated projected rows, but it should not be used to hide an unknown cardinality problem.**
- **Use `EXISTS` for existence checks and pre-aggregate one-to-many relationships when the required output is one row per parent.**
- **Joining multiple independent one-to-many relationships can create `N × M` explosions that corrupt aggregates, pagination, API responses, and performance.**
- **Diagnose production duplication systematically with relationship constraints, incremental JOIN testing, realistic data, and `EXPLAIN (ANALYZE, BUFFERS)`.**