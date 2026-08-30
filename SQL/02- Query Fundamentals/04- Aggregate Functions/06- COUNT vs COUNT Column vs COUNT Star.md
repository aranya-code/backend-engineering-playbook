# 06- COUNT vs COUNT Column vs COUNT Star

## Overview

SQL provides several forms of `COUNT` for measuring how many rows or non-NULL values exist in a result set. The most commonly encountered forms are:

```sql
COUNT(*)
COUNT(column_name)
COUNT(DISTINCT column_name)
```

The critical distinction is:

- `COUNT(*)` counts rows.
- `COUNT(column_name)` counts non-NULL values in that expression.
- `COUNT(DISTINCT column_name)` counts distinct non-NULL values.

These differences become important when columns contain `NULL`, when joins change row cardinality, when grouping is involved, and when the query is used for production metrics or API responses.

## COUNT(*) — Count Rows

### What It Is

`COUNT(*)` counts the number of rows produced by the query's `FROM`, `JOIN`, and `WHERE` operations.

```sql
SELECT COUNT(*)
FROM orders;
```

If the table contains 1,000 rows, the result is:

```text
1000
```

`COUNT(*)` counts rows regardless of whether individual columns contain `NULL`.

### Why It Exists

When the requirement is:

> How many rows satisfy this query?

`COUNT(*)` directly expresses that intent.

For example:

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'completed';
```

This means:

> How many completed order rows exist?

### NULL Does Not Matter

Given:

```text
id | email
---+-------------------
1  | a@example.com
2  | NULL
3  | c@example.com
```

then:

```sql
SELECT COUNT(*)
FROM users;
```

returns:

```text
3
```

The NULL email does not affect the row count.

## COUNT(column) — Count Non-NULL Values

### What It Is

`COUNT(column_name)` counts only rows where the specified expression is non-NULL.

```sql
SELECT COUNT(email)
FROM users;
```

For:

```text
id | email
---+-------------------
1  | a@example.com
2  | NULL
3  | c@example.com
```

the result is:

```text
2
```

The row containing `NULL` is not counted.

### Why It Exists

`COUNT(column)` is useful when the question is:

> How many rows contain a value for this field?

For example:

```sql
SELECT COUNT(phone_number)
FROM customers;
```

answers:

> How many customers have a non-NULL phone number?

It does **not** answer:

> How many customers exist?

For that, use:

```sql
SELECT COUNT(*)
FROM customers;
```

## COUNT(DISTINCT column)

`COUNT(DISTINCT column)` counts unique non-NULL values.

Given:

```text
customer_id
-----------
10
10
20
30
NULL
30
```

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

returns:

```text
3
```

The distinct values are:

```text
10
20
30
```

`NULL` is not counted.

This is useful for metrics such as:

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

which answers:

> How many unique customers placed orders during this period?

## Direct Comparison

| Expression | Counts | Includes NULL? | Removes duplicates? |
|---|---|---:|---:|
| `COUNT(*)` | Rows | Yes, because it counts rows | No |
| `COUNT(column)` | Non-NULL values | No | No |
| `COUNT(DISTINCT column)` | Unique non-NULL values | No | Yes |

The distinction can be summarized as:

```text
COUNT(*)                 → rows
COUNT(column)            → non-NULL values
COUNT(DISTINCT column)   → unique non-NULL values
```

## Example Dataset

Consider:

```text
users
+----+---------------------+------------+
| id | email               | country    |
+----+---------------------+------------+
| 1  | a@example.com       | IN         |
| 2  | NULL                | IN         |
| 3  | b@example.com       | US         |
| 4  | b@example.com       | US         |
| 5  | NULL                | NULL       |
+----+---------------------+------------+
```

Now compare:

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(email) AS email_count,
    COUNT(DISTINCT email) AS unique_email_count
FROM users;
```

Result:

```text
row_count          = 5
email_count        = 3
unique_email_count = 2
```

Why?

```text
COUNT(*)              → all 5 rows
COUNT(email)          → 3 non-NULL emails
COUNT(DISTINCT email) → 2 unique non-NULL emails
```

## COUNT and WHERE

`WHERE` determines which rows reach the aggregate.

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'completed';
```

Conceptually:

```text
All rows
   ↓
FROM / JOIN
   ↓
WHERE
   ↓
COUNT(*)
   ↓
Result
```

For example:

```sql
SELECT COUNT(email)
FROM users
WHERE country = 'IN';
```

This counts Indian users whose email is non-NULL.

It does **not** count all Indian users.

To count all Indian users:

```sql
SELECT COUNT(*)
FROM users
WHERE country = 'IN';
```

## COUNT with GROUP BY

`COUNT` is commonly used to calculate row counts per group.

```sql
SELECT
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY status;
```

Example result:

```text
status      order_count
----------  -----------
pending     120
completed   540
cancelled   30
```

For non-NULL values:

```sql
SELECT
    country,
    COUNT(phone_number) AS customers_with_phone
FROM customers
GROUP BY country;
```

Here the count represents customers with a non-NULL phone number in each country.

## COUNT(*) vs COUNT(column) with GROUP BY

Consider:

```text
country | phone
--------+------------
IN      | 9999999999
IN      | NULL
IN      | 8888888888
US      | NULL
US      | 7777777777
```

Query:

```sql
SELECT
    country,
    COUNT(*) AS customers,
    COUNT(phone) AS customers_with_phone
FROM customers
GROUP BY country;
```

Result:

```text
country | customers | customers_with_phone
--------+-----------+--------------------
IN      | 3         | 2
US      | 2         | 1
```

This pattern is useful for completeness metrics:

```sql
SELECT
    COUNT(*) AS total_customers,
    COUNT(phone) AS customers_with_phone,
    COUNT(email) AS customers_with_email
FROM customers;
```

## COUNT(DISTINCT) with GROUP BY

Distinct counts can also be calculated per group.

```sql
SELECT
    country,
    COUNT(DISTINCT email) AS unique_emails
FROM users
GROUP BY country;
```

This answers:

> How many unique non-NULL email addresses exist per country?

It does not count users. Multiple users can have the same email.

If email is supposed to be unique, a duplicate count can also expose data-quality problems:

```sql
SELECT
    email,
    COUNT(*) AS occurrences
FROM users
WHERE email IS NOT NULL
GROUP BY email
HAVING COUNT(*) > 1;
```

## COUNT and NULL Semantics

`NULL` is one of the most important concepts when using `COUNT`.

Consider:

```text
id | value
---+------
1  | 10
2  | 20
3  | NULL
4  | 30
```

Then:

```sql
SELECT
    COUNT(*) AS rows,
    COUNT(value) AS values
FROM metrics;
```

returns:

```text
rows   = 4
values = 3
```

A useful production pattern for completeness is:

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(value) AS populated_rows,
    COUNT(*) - COUNT(value) AS null_rows
FROM metrics;
```

This works because `COUNT(*)` counts all rows while `COUNT(value)` excludes NULL values.

## COUNT and COALESCE

`COALESCE` can change the behavior of `COUNT(column)`.

Without `COALESCE`:

```sql
SELECT COUNT(phone)
FROM customers;
```

only non-NULL phones are counted.

With:

```sql
SELECT COUNT(COALESCE(phone, ''))
FROM customers;
```

NULL phone values become an empty string, which is non-NULL, so they are counted.

Therefore, this query effectively counts rows rather than populated phone values.

The same principle applies to numeric expressions:

```sql
SELECT COUNT(COALESCE(discount, 0))
FROM orders;
```

This counts every row because `COALESCE` guarantees a non-NULL result.

Do not use `COALESCE` inside `COUNT` unless that semantic change is intentional.

## COUNT and JOINs

Joins are one of the most common sources of incorrect counts.

Consider:

```text
customers
+----+-------+
| id | name  |
+----+-------+
| 1  | Alice |
| 2  | Bob   |
+----+-------+

orders
+----+-------------+
| id | customer_id |
+----+-------------+
| 10 | 1           |
| 11 | 1           |
| 12 | 2           |
+----+-------------+
```

This query:

```sql
SELECT COUNT(*)
FROM customers
JOIN orders
    ON orders.customer_id = customers.id;
```

returns:

```text
3
```

It counts joined rows, not customers.

Alice appears twice because she has two orders.

To count customers who have at least one order:

```sql
SELECT COUNT(DISTINCT customers.id)
FROM customers
JOIN orders
    ON orders.customer_id = customers.id;
```

Result:

```text
2
```

Alternatively, `EXISTS` can express the requirement directly:

```sql
SELECT COUNT(*)
FROM customers
WHERE EXISTS (
    SELECT 1
    FROM orders
    WHERE orders.customer_id = customers.id
);
```

## LEFT JOIN and COUNT

`LEFT JOIN` introduces another important distinction.

Consider customers:

```text
Alice
Bob
Charlie
```

and orders:

```text
Alice → 2 orders
Bob   → 1 order
Charlie → 0 orders
```

This query:

```sql
SELECT
    c.id,
    COUNT(*)
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

can produce:

```text
Alice   2
Bob     1
Charlie 1
```

Why does Charlie get `1`?

Because the `LEFT JOIN` preserves Charlie as a result row with NULL values from `orders`. `COUNT(*)` counts that joined row.

To count actual orders:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Now:

```text
Alice   2
Bob     1
Charlie 0
```

This is a critical distinction:

```text
LEFT JOIN + COUNT(*)       → counts the preserved result row
LEFT JOIN + COUNT(child.id) → counts matching child rows
```

## COUNT(*) vs COUNT(id) in Joins

When the requirement is to count child records after a `LEFT JOIN`, prefer:

```sql
COUNT(child.id)
```

rather than:

```sql
COUNT(*)
```

provided `child.id` is guaranteed non-NULL for real child rows.

For example:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This correctly reports zero for customers without orders.

## COUNT and INNER JOIN

With an `INNER JOIN`, unmatched rows disappear.

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

Customers with no orders are absent entirely.

If the API requires every customer, including those with zero orders, use `LEFT JOIN`.

## COUNT(DISTINCT) and Join Explosion

Suppose:

```text
customers
    ↓
orders
    ↓
order_items
```

A customer may have many orders and each order may have many items.

A multi-table join can produce many rows for the same customer.

For example:

```sql
SELECT COUNT(*)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

This counts joined combinations, not customers.

If the requirement is unique customers represented in the result:

```sql
SELECT COUNT(DISTINCT c.id)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

At senior level, the key question is not:

> Which COUNT syntax should I use?

It is:

> What is the grain of the rows entering the aggregate?

Always identify the row grain before counting.

## COUNT and HAVING

`HAVING` filters groups based on aggregate values.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

This finds customers with at least 10 orders.

The distinction is:

```text
WHERE  → filters rows
GROUP BY → creates groups
COUNT   → calculates aggregate
HAVING → filters groups
```

## COUNT Multiple Metrics in One Query

A single aggregation query can calculate several related metrics.

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(completed_at) AS completed_orders,
    COUNT(cancelled_at) AS cancelled_orders,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders;
```

This can be more efficient and easier to maintain than issuing several separate queries.

However, the metrics must have clearly defined semantics.

For example, `COUNT(completed_at)` means:

> Orders where `completed_at` is non-NULL.

It does not necessarily mean:

> Orders whose current status is completed.

If both concepts exist, prefer the predicate that represents the actual business definition.

## Conditional Counting

Conditional counts are useful for dashboards and reporting.

Using PostgreSQL's `FILTER`:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders
FROM orders;
```

A portable alternative uses `CASE`:

```sql
SELECT
    COUNT(*) AS total_orders,
    COUNT(CASE
        WHEN status = 'completed' THEN 1
    END) AS completed_orders,
    COUNT(CASE
        WHEN status = 'cancelled' THEN 1
    END) AS cancelled_orders
FROM orders;
```

The `CASE` expression returns NULL when its condition is false, so `COUNT` ignores those rows.

## COUNT and DISTINCT Performance

`COUNT(DISTINCT column)` can be substantially more expensive than `COUNT(*)` because the database must determine uniqueness.

Depending on the database and execution plan, this may involve:

- Hash aggregation
- Sorting
- Memory allocation
- Temporary structures
- Parallel execution

For example:

```sql
SELECT COUNT(DISTINCT user_id)
FROM events
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

On a large event table, this can become a significant workload.

Inspect the actual execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(DISTINCT user_id)
FROM events
WHERE created_at >= :start_time
  AND created_at < :end_time;
```

Do not assume an index automatically makes `COUNT(DISTINCT)` cheap.

## COUNT and Indexes

For large tables, `COUNT(*)` is not necessarily an O(1) metadata lookup.

For example:

```sql
SELECT COUNT(*)
FROM events;
```

may require substantial work depending on the database engine and consistency requirements.

An index can sometimes improve count queries, especially when predicates allow an efficient index path:

```sql
SELECT COUNT(*)
FROM events
WHERE tenant_id = :tenant_id;
```

A candidate index could be:

```sql
CREATE INDEX idx_events_tenant_id
ON events (tenant_id);
```

But index usage depends on:

- Table size
- Selectivity
- Statistics
- Database engine
- Visibility rules
- Query predicates
- Cost estimates

Use the execution plan to validate the actual behavior.

## COUNT(*) and Performance Myths

A common misconception is:

> `COUNT(id)` is faster than `COUNT(*)`.

This is not a reliable rule.

In many relational databases, `COUNT(*)` is specifically optimized for counting rows and is the clearest expression when all rows should be counted.

Use:

```sql
COUNT(*)
```

when you mean:

> Count rows.

Use:

```sql
COUNT(column)
```

when you mean:

> Count non-NULL values in this column.

Do not choose between them based on an assumed micro-optimization.

## COUNT and Pagination

A common REST API pattern is:

```text
GET /orders?page=3&page_size=50
```

where the API returns:

```json
{
  "items": [],
  "total": 12480
}
```

The `total` often comes from:

```sql
SELECT COUNT(*)
FROM orders
WHERE tenant_id = :tenant_id
  AND status = :status;
```

This can become expensive for large datasets, particularly when every request performs both:

1. A page query.
2. An exact count query.

For high-scale APIs, consider whether clients actually need an exact total.

Alternatives include:

- Omit total counts.
- Return `has_next`.
- Use cursor pagination.
- Cache counts when appropriate.
- Maintain precomputed counters.
- Use approximate counts where business requirements allow.

Pagination strategy and counting strategy should be designed together.

## COUNT in Django

Django provides `.count()` for counting a QuerySet:

```python
total = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        status="completed",
    )
    .count()
)
```

For field-specific aggregation:

```python
from django.db.models import Count

result = User.objects.aggregate(
    total_users=Count("id"),
)
```

For distinct values:

```python
result = Order.objects.aggregate(
    unique_customers=Count("customer_id", distinct=True),
)
```

For grouped counts:

```python
from django.db.models import Count

orders_by_status = (
    Order.objects
    .values("status")
    .annotate(order_count=Count("id"))
)
```

Be aware that ORM abstractions can hide joins. Inspect the generated SQL for complex aggregation queries and validate the execution plan.

## COUNT in API and Service Design

Suppose an endpoint returns customer order counts:

```json
{
  "customer_id": 42,
  "order_count": 17
}
```

The service should define what `17` means.

Possible definitions include:

- All orders ever created
- Completed orders only
- Non-cancelled orders
- Orders in a specified date range
- Distinct orders after joins
- Orders visible to the requesting tenant

A technically correct `COUNT` can still produce an incorrect business metric if the population is wrong.

Document important metric definitions at the service or reporting layer.

## Production Considerations

### Define the Counting Grain

Before writing the query, identify what one input row represents.

Examples:

```text
users table              → one user
orders table             → one order
orders JOIN items        → one order-item combination
customers LEFT JOIN orders → one customer-order combination
```

Then decide whether the required result is:

- Rows
- Non-NULL values
- Distinct entities

### Protect Multi-Tenant Boundaries

Always apply tenant isolation before aggregation:

```sql
SELECT COUNT(*)
FROM orders
WHERE tenant_id = :tenant_id;
```

A missing tenant predicate can turn a valid count query into a data-isolation vulnerability.

### Validate Business Semantics

Do not infer business states from nullable columns without verifying their meaning.

For example:

```sql
COUNT(completed_at)
```

means "rows with a non-NULL completed timestamp."

It does not automatically mean "currently completed rows."

### Monitor Expensive Counts

Track:

- Query latency
- Database CPU
- Buffer reads
- Temporary disk usage
- Memory consumption
- Rows scanned
- Execution-plan changes

Large `COUNT(DISTINCT ...)` queries and exact counts for huge filtered datasets deserve particular attention.

## Common Mistakes

| Mistake | Why it is wrong | Better approach |
|---|---|---|
| Using `COUNT(column)` to count rows | NULL values are excluded | Use `COUNT(*)` |
| Assuming `COUNT(*)` ignores NULL rows | It counts rows, regardless of column values | Use `COUNT(column)` for non-NULL values |
| Using `COUNT(*)` after `LEFT JOIN` for child counts | Preserved parent rows are counted | Use `COUNT(child.id)` |
| Counting joined rows as entities | One entity can appear many times | Use `COUNT(DISTINCT entity_id)` when appropriate |
| Using `COUNT(DISTINCT ...)` automatically | Distinct counting can be expensive and may not match the metric | Define the required grain first |
| Assuming `COUNT(id)` is always faster | Performance depends on the database and plan | Use the expression matching the semantics |
| Counting a nullable state column | NULL may represent an unrelated state | Use an explicit predicate when required |
| Running exact counts on every API page | Can create unnecessary database load | Reconsider whether exact totals are required |
| Forgetting tenant filters | Can expose aggregate information across tenants | Enforce tenant isolation |
| Ignoring join cardinality | Aggregation may operate on multiplied rows | Inspect the joined row grain |

## Interview Traps

### `COUNT(*)` vs `COUNT(column)`

Given:

```text
id | email
---+------
1  | a
2  | NULL
3  | b
```

```sql
COUNT(*)       = 3
COUNT(email)   = 2
```

### `COUNT(DISTINCT)` Ignores NULL

Given:

```text
A
A
B
NULL
```

```sql
COUNT(DISTINCT value) = 2
```

The unique non-NULL values are `A` and `B`.

### LEFT JOIN Can Make COUNT(*) Misleading

This:

```sql
SELECT
    c.id,
    COUNT(*)
FROM customers c
LEFT JOIN orders o
    ON o.customer_id = c.id
GROUP BY c.id;
```

can return `1` for a customer with zero orders.

Use:

```sql
COUNT(o.id)
```

to count actual matching orders.

### COUNT(DISTINCT) Does Not Mean COUNT(*)

This:

```sql
COUNT(DISTINCT customer_id)
```

counts unique customers.

This:

```sql
COUNT(*)
```

counts result rows.

They answer fundamentally different questions.

### COUNTing an Expression

`COUNT` operates on the result of an expression.

For example:

```sql
COUNT(CASE WHEN status = 'completed' THEN 1 END)
```

counts only rows where the expression returns a non-NULL value.

Understanding expression NULLability is therefore essential.

## Practical Decision Table

| Business question | SQL expression |
|---|---|
| How many rows are there? | `COUNT(*)` |
| How many rows have a value in `email`? | `COUNT(email)` |
| How many unique customers exist? | `COUNT(DISTINCT customer_id)` |
| How many child rows exist after a `LEFT JOIN`? | `COUNT(child.id)` |
| How many groups satisfy a minimum count? | `HAVING COUNT(*) >= ...` |
| How many rows satisfy a condition? | `COUNT(*) FILTER (WHERE ...)` or `COUNT(CASE WHEN ... END)` |
| How many rows have a non-NULL expression? | `COUNT(expression)` |

## Production Checklist

Before shipping a `COUNT` query, verify:

- [ ] Am I counting rows, populated values, or distinct entities?
- [ ] Can the counted column contain NULL?
- [ ] Does a JOIN multiply the rows?
- [ ] Is `LEFT JOIN` involved?
- [ ] Should zero-count parent entities still appear?
- [ ] Does `COUNT(DISTINCT ...)` actually match the business requirement?
- [ ] Are tenant and authorization predicates applied?
- [ ] Is an exact count really required?
- [ ] Could the count become expensive at production scale?
- [ ] Has the execution plan been checked for important queries?
- [ ] Does the API contract define exactly what the count represents?

## Key Takeaways

- `COUNT(*)` counts result rows, while `COUNT(column)` counts only non-NULL values and `COUNT(DISTINCT column)` counts unique non-NULL values.
- After joins, always reason about row cardinality; use `COUNT(DISTINCT entity_id)` when the requirement is to count entities rather than joined rows.
- With a `LEFT JOIN`, `COUNT(*)` can report `1` for a parent with no children; `COUNT(child.id)` correctly reports zero when the child key is non-NULL for real rows.
- Exact counts and `COUNT(DISTINCT ...)` can become expensive at scale, so validate execution plans and reconsider whether every API request needs an exact total.
- The correct `COUNT` expression follows the business definition of the metric; SQL syntax alone cannot compensate for an incorrectly defined population.