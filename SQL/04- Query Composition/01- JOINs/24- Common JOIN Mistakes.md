# 24- Common JOIN Mistakes

## Overview

JOINs are a frequent source of subtle SQL bugs because a query can be syntactically valid, execute successfully, and still return the wrong data.

Most JOIN failures are not caused by misunderstanding JOIN syntax. They come from incorrect assumptions about:

- Which rows must be preserved.
- What one result row represents.
- Relationship cardinality.
- NULL behavior.
- Predicate placement.
- Duplicate relationships.
- Many-to-many expansion.
- Query performance at production scale.

A useful production rule is:

> **Define the expected result grain and row-preservation semantics before writing the JOIN.**

For example, if an API requires **one row per customer**, joining directly to a one-to-many `orders` table can violate that requirement unless the order side is aggregated or existence is expressed with `EXISTS`.

## Mistake: Using the Wrong JOIN Type

The most basic mistake is choosing a JOIN based on habit rather than required semantics.

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

This `INNER JOIN` removes customers who have no orders.

If the requirement is:

> Return every customer, including customers with no orders.

use:

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

The choice should be based on which rows must survive.

| Requirement | Appropriate operation |
|---|---|
| Only matching rows | `INNER JOIN` |
| Preserve all left rows | `LEFT JOIN` |
| Preserve all right rows | `RIGHT JOIN` |
| Preserve both sides | `FULL OUTER JOIN` |
| Every combination | `CROSS JOIN` |
| Relationship existence only | `EXISTS` |
| Relationship absence | `NOT EXISTS` |

## Mistake: Turning a LEFT JOIN Into an INNER JOIN

This is one of the most common outer JOIN bugs.

Suppose customers without completed orders must still appear.

Incorrect:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

For a customer without an order, `o.status` is `NULL`, so the `WHERE` predicate fails.

The query therefore behaves like an inner join for this condition.

Prefer:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

Now:

- All customers remain.
- Only completed orders participate in the JOIN.
- Customers without completed orders receive NULLs for order columns.

The distinction is:

```text
ON    → controls which related rows participate
WHERE → filters the final result
```

This distinction becomes especially important with outer JOINs.

## Mistake: Filtering the Wrong Table in WHERE

Consider an API that needs:

> All active customers and their completed orders.

A clear query is:

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed'
WHERE c.status = 'active';
```

The predicates have different responsibilities:

```text
customers.status → primary population
orders.status    → relationship condition
```

A useful mental model is:

> Put predicates in `ON` when they define which related rows should be attached to an outer-joined entity. Put predicates in `WHERE` when they should remove rows from the final result.

## Mistake: Forgetting the JOIN Predicate

A JOIN without an appropriate relationship condition can produce a Cartesian product.

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
CROSS JOIN orders AS o;
```

If there are:

```text
10,000 customers
×
1,000,000 orders
```

the theoretical result contains:

```text
10,000,000,000 rows
```

An accidental Cartesian product can consume significant CPU, memory, temporary storage, and network bandwidth.

For an ordinary relationship query, explicitly specify the relationship:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

A `CROSS JOIN` is legitimate when every combination is intentionally required, but it should never be an accidental side effect.

## Mistake: Joining on the Wrong Column

A syntactically valid JOIN can still be logically wrong.

Incorrect:

```sql
SELECT
    o.id,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.id;
```

The query may execute successfully but relate orders to customers using unrelated identifiers.

The intended relationship is:

```sql
SELECT
    o.id,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id;
```

When reviewing a JOIN, verify:

- Which columns define the relationship?
- Are they primary key/foreign key pairs?
- Is the relationship composite?
- Can either side contain duplicates?
- Are data types compatible?
- Does the business relationship match the database relationship?

Do not assume that similarly named columns represent the same relationship.

## Mistake: Joining on an Incomplete Composite Key

Some relationships require multiple columns.

Suppose:

```text
warehouse_inventory
-------------------
warehouse_id
product_id
quantity
```

and another table contains warehouse-specific product records.

If the relationship is defined by both:

```text
warehouse_id + product_id
```

joining only on `product_id` is incorrect:

```sql
JOIN warehouse_products AS wp
    ON wp.product_id = wi.product_id
```

It can match the same product across multiple warehouses.

The correct relationship is:

```sql
JOIN warehouse_products AS wp
    ON wp.warehouse_id = wi.warehouse_id
   AND wp.product_id = wi.product_id
```

A missing component of a composite relationship can create both incorrect matches and unexpected row multiplication.

## Mistake: Ignoring One-to-Many Cardinality

Consider:

```text
customers
---------
id

orders
------
id
customer_id
```

A customer can have multiple orders.

This query:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

does not necessarily produce one row per customer.

If a customer has five orders, that customer can appear five times.

The JOIN is behaving correctly. The query's assumption about result grain is wrong.

If the requirement is one row per customer with an order count:

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

If only existence matters:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

## Mistake: Using DISTINCT to Hide JOIN Problems

A common repair is:

```sql
SELECT DISTINCT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

`DISTINCT` may produce the desired output, but it can hide an incorrect understanding of the relationship.

If the requirement is:

> Customers that have at least one order

then this communicates the requirement more directly:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

`DISTINCT` is appropriate when duplicate elimination is genuinely part of the required result.

It should not be the default response to unexpected row multiplication.

## Mistake: Joining Multiple One-to-Many Relationships Independently

This is a more advanced and expensive form of row multiplication.

Suppose:

```text
customers
    ├── orders
    └── support_tickets
```

A customer has:

```text
3 orders
4 support tickets
```

This query:

```sql
SELECT
    c.id,
    o.id AS order_id,
    t.id AS ticket_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id;
```

can produce:

```text
3 × 4 = 12 rows
```

for that customer.

The query has created combinations between two independent child collections.

This becomes especially dangerous when aggregating:

```sql
COUNT(o.id)
SUM(o.amount)
COUNT(t.id)
```

The aggregates may be inflated because each order is repeated for each ticket.

### Safer Pattern: Pre-Aggregate

Aggregate each one-to-many relationship independently:

```sql
WITH order_stats AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        COALESCE(SUM(amount), 0) AS order_total
    FROM orders
    GROUP BY customer_id
),
ticket_stats AS (
    SELECT
        customer_id,
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
)
SELECT
    c.id,
    c.email,
    COALESCE(os.order_count, 0) AS order_count,
    COALESCE(os.order_total, 0) AS order_total,
    COALESCE(ts.ticket_count, 0) AS ticket_count
FROM customers AS c
LEFT JOIN order_stats AS os
    ON os.customer_id = c.id
LEFT JOIN ticket_stats AS ts
    ON ts.customer_id = c.id;
```

Each derived relation has:

```text
one row per customer
```

before it is joined to `customers`.

This makes the intended cardinality explicit and avoids multiplying independent child collections.

## Mistake: Incorrect Many-to-Many JOINs

Many-to-many relationships normally use a junction table.

For example:

```text
users
roles
user_roles
```

The relationship is:

```sql
SELECT
    u.id,
    r.name
FROM users AS u
JOIN user_roles AS ur
    ON ur.user_id = u.id
JOIN roles AS r
    ON r.id = ur.role_id;
```

A common mistake is joining users directly to roles without using the relationship table.

Another mistake is allowing duplicate rows in the junction table:

```text
user_id | role_id
--------+--------
1       | 10
1       | 10
```

This causes duplicate results.

If the relationship should be unique, enforce it:

```sql
CREATE UNIQUE INDEX ux_user_roles_user_role
    ON user_roles(user_id, role_id);
```

Database constraints are preferable to relying exclusively on application-level validation.

## Mistake: Ignoring NULL Semantics

SQL uses three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

`NULL` comparisons produce `UNKNOWN`.

For example:

```sql
WHERE o.status = 'completed'
```

does not match rows where `o.status` is `NULL`.

This becomes important with outer JOINs because unmatched rows are represented using NULLs for columns from the missing side.

For example:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

For customers without orders:

```text
c.id | o.id
-----+-----
101  | NULL
```

Do not interpret this as an actual order whose `id` is NULL. It represents the absence of a matching right-side row.

## Mistake: Using `NOT IN` for Anti-JOIN Logic

This can be problematic when NULLs exist:

```sql
SELECT
    c.id
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

If the subquery contains `NULL`, SQL's three-valued logic can produce unexpected results.

Prefer:

```sql
SELECT
    c.id
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

A `LEFT JOIN ... IS NULL` anti-join is another valid pattern:

```sql
SELECT
    c.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.id IS NULL;
```

`NOT EXISTS` is often the clearest expression when the business requirement is absence of a related row.

## Mistake: Testing NULL With `= NULL`

Incorrect:

```sql
WHERE customer_id = NULL;
```

Correct:

```sql
WHERE customer_id IS NULL;
```

Likewise:

```sql
WHERE customer_id IS NOT NULL;
```

`NULL` represents an unknown or absent value, so ordinary equality operators do not behave like comparisons against ordinary values.

## Mistake: Selecting `*` From Multiple Joined Tables

This is convenient during exploration:

```sql
SELECT *
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

But it is usually poor production practice.

Problems include:

- Ambiguous duplicate column names.
- Large network payloads.
- Unnecessary database-to-application transfer.
- Fragile API mappings.
- Unexpected behavior when schemas change.
- Difficulty understanding the result grain.

Prefer explicit columns:

```sql
SELECT
    c.id AS customer_id,
    c.email,
    o.id AS order_id,
    o.amount,
    o.status
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Explicit projection is especially important for REST and gRPC backend responses.

## Mistake: Forgetting Column Qualification

Ambiguous queries become dangerous as JOIN count increases.

Avoid:

```sql
SELECT
    id,
    status
FROM orders AS o
JOIN payments AS p
    ON p.order_id = o.id;
```

If both tables contain `id` or `status`, the query can become ambiguous or difficult to maintain.

Prefer:

```sql
SELECT
    o.id AS order_id,
    o.status AS order_status,
    p.id AS payment_id,
    p.status AS payment_status
FROM orders AS o
JOIN payments AS p
    ON p.order_id = o.id;
```

Use short, meaningful aliases consistently.

## Mistake: Joining on Expressions Without Considering Indexes

This pattern can prevent efficient use of a normal index:

```sql
JOIN customers AS c
    ON LOWER(c.email) = LOWER(o.customer_email)
```

The exact impact depends on the database and available indexes.

In PostgreSQL, if this relationship is legitimate, an expression index may be appropriate:

```sql
CREATE INDEX idx_customers_lower_email
    ON customers (LOWER(email));
```

But a better data model may be to store a normalized representation and enforce uniqueness there.

For high-volume production systems, avoid repeatedly performing expensive transformations on large JOIN inputs when the relationship can be represented cleanly in the schema.

## Mistake: Joining Different Data Types

JOIN keys should have compatible semantics and preferably compatible data types.

For example:

```text
orders.customer_id → BIGINT
customers.id       → UUID
```

is a schema-design problem, not merely a query problem.

Implicit casts can:

- Increase CPU cost.
- Prevent efficient index usage.
- Produce surprising results.
- Hide schema inconsistencies.

Prefer consistent key types across related tables.

## Mistake: Assuming Foreign Keys Prevent Duplicates

A foreign key:

```sql
FOREIGN KEY (customer_id)
REFERENCES customers(id)
```

does not mean that `customer_id` is unique.

This is valid:

```text
order_id | customer_id
---------+------------
1        | 10
2        | 10
3        | 10
```

That is normal for a one-to-many relationship.

If one-to-one semantics are required, enforce uniqueness:

```sql
CREATE UNIQUE INDEX ux_customer_profile_customer_id
    ON customer_profiles(customer_id);
```

Always distinguish:

```text
referential integrity
```

from:

```text
uniqueness
```

## Mistake: Assuming JOIN Order Determines Execution Order

This query:

```sql
SELECT
    o.id,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id;
```

does not necessarily mean the database physically scans `orders` first and then `customers`.

For inner joins, the optimizer may reorder relations and choose a physical strategy such as:

- Nested loop join.
- Hash join.
- Merge join.
- Index scan.
- Sequential scan.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    o.id,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id;
```

to inspect what the database actually did.

Outer JOINs have additional semantic constraints because row preservation limits which transformations are valid.

## Mistake: Optimizing Without Looking at Cardinality

A JOIN's cost is heavily influenced by the number of rows entering and leaving each operation.

Suppose:

```text
customers        1,000,000
orders          50,000,000
```

A query joining both tables without selective filtering can require substantial work even when both tables are properly indexed.

Before optimizing, estimate:

```text
input rows
→ filtered rows
→ joined rows
→ grouped rows
→ final rows
```

Large intermediate relations often matter more than the final result size.

## Mistake: Missing Indexes on High-Value JOIN Paths

A common relationship is:

```sql
orders.customer_id → customers.id
```

The referenced primary key is normally indexed, but the foreign-key side is not automatically indexed in every database.

For PostgreSQL, explicitly consider:

```sql
CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);
```

This can help queries such as:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = 12345;
```

Index design must account for the actual workload rather than indexing every JOIN column indiscriminately.

Indexes also increase:

- Storage usage.
- Write cost.
- Vacuum/maintenance work.
- Insert/update overhead.

## Mistake: Adding Too Many Indexes

The opposite mistake is indexing everything.

For example, adding separate indexes for every column involved in every query can increase write amplification without solving the actual bottleneck.

Evaluate:

- Query frequency.
- Selectivity.
- Join patterns.
- Filter patterns.
- Sort requirements.
- Table size.
- Write volume.
- Execution plans.

Use production-like data and actual workload characteristics before adding indexes.

## Mistake: Applying Pagination After Row Multiplication

Suppose an API wants:

```text
20 customers per page
```

but directly joins customers to orders:

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
ORDER BY c.id
LIMIT 20;
```

The 20 rows represent joined rows, not necessarily 20 distinct customers.

One customer with many orders can consume multiple rows from the page.

If the API's resource is one row per customer, paginate the customer grain rather than an expanded child-row grain.

For large datasets, keyset pagination is often preferable to large offsets:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id > :last_customer_id
ORDER BY c.id
LIMIT 20;
```

Then retrieve related data according to the required result shape.

## Mistake: Joining Before Applying Selective Filters Without Understanding the Plan

Consider:

```sql
SELECT
    o.id,
    c.email
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.status = 'completed'
  AND o.created_at >= CURRENT_DATE - INTERVAL '30 days';
```

The optimizer may push filters down and avoid unnecessary work.

Do not manually rewrite queries solely because you assume SQL executes strictly top-to-bottom.

Instead, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

If filtering is highly selective, an appropriate composite index can be more valuable than rearranging the textual query.

For example, depending on workload:

```sql
CREATE INDEX idx_orders_status_created_customer
    ON orders(status, created_at, customer_id);
```

The ideal index depends on data distribution and the complete query workload.

## Mistake: Returning More Related Rows Than the API Needs

Suppose an endpoint needs only:

```text
customers who have at least one failed payment
```

A JOIN may produce every failed payment:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN payments AS p
    ON p.customer_id = c.id
WHERE p.status = 'failed';
```

If customers can have many failed payments, the query can multiply rows.

If payment details are not needed:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM payments AS p
    WHERE p.customer_id = c.id
      AND p.status = 'failed'
);
```

This expresses the business requirement directly.

## Mistake: Using Application Code to Repair a Bad JOIN

A backend developer may execute:

```sql
SELECT ...
```

and then deduplicate results in Python:

```python
unique_customers = {
    row["customer_id"]: row
    for row in rows
}
```

This is usually the wrong layer to solve a relational query problem.

It can cause:

- Excessive database output.
- Increased network traffic.
- Higher application memory usage.
- More CPU work.
- Incorrect aggregation.
- Pagination inconsistencies.

If the database can express the desired result correctly, perform the relational operation in SQL.

Application-level processing is appropriate when the transformation genuinely belongs in the application layer, not as a workaround for incorrect SQL cardinality.

## Mistake: Building N+1 Queries Instead of Joining Appropriately

A backend API may load customers first:

```python
customers = get_customers()

for customer in customers:
    orders = get_orders(customer["id"])
```

This can produce:

```text
1 query for customers
+
N queries for orders
```

For Django, this often appears as inefficient relationship access without appropriate `select_related()` or `prefetch_related()`.

For example:

```python
orders = (
    Order.objects
    .select_related("customer")
    .filter(status="completed")
)
```

For one-to-many relationships, `prefetch_related()` is commonly more appropriate:

```python
customers = (
    Customer.objects
    .prefetch_related("orders")
    .filter(status="active")
)
```

The correct ORM strategy depends on the result shape and relationship cardinality.

The underlying SQL principles remain the same:

> Understand the relationship, result grain, and number of database round trips.

## Mistake: Ignoring Soft-Delete or Tenant Filters

Production tables often contain columns such as:

```text
deleted_at
tenant_id
status
```

A JOIN that ignores these constraints can expose logically deleted or cross-tenant data.

For example:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

In a multi-tenant system, the relationship may also require tenant isolation:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
   AND o.tenant_id = c.tenant_id
WHERE c.tenant_id = :tenant_id
  AND c.deleted_at IS NULL
  AND o.deleted_at IS NULL;
```

The exact schema should ideally enforce tenant consistency through appropriate constraints and data-access boundaries, but query-level filtering remains important where applicable.

Treat authorization and tenant boundaries as correctness requirements, not merely performance filters.

## Mistake: Trusting ORM JOINs Without Inspecting Generated SQL

Django, SQLAlchemy, and other ORMs generate SQL on your behalf.

For a complex query, understand what SQL is actually executed.

In Django:

```python
queryset = (
    Order.objects
    .select_related("customer")
    .filter(customer__status="active")
)

print(queryset.query)
```

For production troubleshooting, database-side observability is more reliable than reasoning from ORM method names alone.

Inspect:

- Generated SQL.
- Bound parameters.
- Query duration.
- Execution plan.
- Number of returned rows.
- Database wait time.

An ORM abstraction does not remove the need to understand relational semantics.

## Mistake: Ignoring Transaction and Consistency Requirements

JOINs execute against a transactionally consistent database snapshot according to the database's isolation semantics.

In concurrent systems, related tables may change while application operations are running.

For workflows that require a consistent decision across multiple statements, use an appropriate transaction boundary.

For example, an order-processing workflow may require:

```text
read order
→ validate payment
→ update order
```

A JOIN in the initial read does not automatically make the entire multi-statement workflow atomic.

In PostgreSQL-backed Django applications, use the appropriate transaction management:

```python
from django.db import transaction

with transaction.atomic():
    # Read and write operations that must commit atomically.
    ...
```

JOIN correctness and transaction correctness are related but separate concerns.

## Production JOIN Review Checklist

Before shipping a complex JOIN query, verify:

| Check | Question |
|---|---|
| Result grain | What does one output row represent? |
| JOIN type | Which rows must survive? |
| Relationship | Are the JOIN columns actually related? |
| Cardinality | Can either side contain multiple matches? |
| Composite keys | Are all relationship columns included? |
| NULL behavior | What happens when no match exists? |
| Predicate placement | Should each condition be in `ON` or `WHERE`? |
| Duplication | Can independent one-to-many relationships multiply each other? |
| Existence | Should this be `EXISTS` instead of a JOIN? |
| Anti-join | Should this be `NOT EXISTS` instead of `NOT IN`? |
| Projection | Are only required columns selected? |
| Indexes | Are important access paths indexed? |
| Data types | Are JOIN keys compatible? |
| Pagination | Is pagination applied at the intended grain? |
| Tenant/security filters | Can unrelated or unauthorized rows be exposed? |
| ORM SQL | Does generated SQL match the intended query? |
| Execution plan | Does the database use a reasonable physical plan? |
| Production scale | Has the query been tested against realistic cardinality? |

## A Practical Debugging Method

When a JOIN returns unexpected results, do not immediately modify the query randomly.

Use a controlled process.

### Start With the Base Relation

```sql
SELECT COUNT(*)
FROM customers;
```

Confirm the expected population.

### Add the JOIN

```sql
SELECT COUNT(*)
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Compare the cardinality.

### Check Multiplication

```sql
SELECT
    c.id,
    COUNT(*) AS joined_rows
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id
HAVING COUNT(*) > 1;
```

This identifies customers producing multiple rows.

### Add Predicates Incrementally

Apply filters one at a time and verify how each predicate changes the result.

For outer JOINs, specifically test predicates in both:

```text
ON
```

and:

```text
WHERE
```

when semantics are in question.

### Inspect the Execution Plan

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ...
```

Separate:

```text
logical correctness
```

from:

```text
physical performance
```

A query can be logically correct but slow, or fast but logically incorrect.

## JOIN Mistakes by Severity

| Mistake | Typical impact | Priority |
|---|---|---|
| Wrong tenant/security JOIN | Data exposure | Critical |
| Wrong relationship key | Incorrect business data | Critical |
| Missing JOIN predicate | Massive result explosion | Critical |
| Incorrect `ON`/`WHERE` placement | Missing records | High |
| Uncontrolled many-to-many JOIN | Incorrect results/performance | High |
| Independent one-to-many JOINs | Inflated aggregates | High |
| Incorrect NULL handling | Missing/incorrect records | High |
| N+1 ORM access | Latency/database load | High |
| Missing high-value index | Query latency | Medium/High |
| `DISTINCT` hiding duplicates | Query design debt | Medium |
| `SELECT *` | Payload/maintenance issues | Medium |
| Excessive indexes | Write/storage overhead | Medium |

## Key Takeaways

- **Define result grain and row-preservation requirements before writing a JOIN; most serious JOIN bugs are semantic rather than syntactic.**
- **Be especially careful with `LEFT JOIN` predicates, NULL behavior, composite keys, and one-to-many or many-to-many relationships.**
- **Do not use `DISTINCT`, application-side deduplication, or ORM workarounds to hide unexpected row multiplication; fix the relational design.**
- **Use `EXISTS`/`NOT EXISTS` for existence semantics, pre-aggregate independent one-to-many relationships, and enforce uniqueness with database constraints where required.**
- **For production queries, validate generated SQL, indexes, security/tenant boundaries, cardinality, and `EXPLAIN (ANALYZE, BUFFERS)` results against realistic data volumes.**