# 14- One-to-Many JOINs

## Overview

A one-to-many relationship exists when one row in a parent table can be associated with multiple rows in a child table.

This is one of the most common relationship patterns in backend systems:

- Customer → Orders
- User → API requests
- Account → Transactions
- Blog post → Comments
- Organization → Members
- Order → Line items
- Product → Inventory records

The database representation is normally a foreign key on the many-side:

```text
customers
    │
    ├── orders
    ├── orders
    └── orders
```

A `JOIN` retrieves the related rows. The foreign key establishes the relationship, while the absence of a uniqueness constraint allows multiple child rows to reference the same parent.

## Basic One-to-Many Relationship

Consider:

```text
customers
+----+---------------------+
| id | name                |
+----+---------------------+
| 1  | Alice               |
| 2  | Bob                 |
+----+---------------------+

orders
+----+-------------+--------+
| id | customer_id | amount |
+----+-------------+--------+
| 101| 1           | 500.00 |
| 102| 1           | 250.00 |
| 103| 2           | 800.00 |
+----+-------------+--------+
```

The relationship is:

```text
customers.id 1 ───┬── orders.customer_id 101
                  └── orders.customer_id 102

customers.id 2 ────── orders.customer_id 103
```

The SQL representation is:

```sql
SELECT
    c.id AS customer_id,
    c.name,
    o.id AS order_id,
    o.amount
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id;
```

The result contains one row for every matching child row:

```text
customer_id | name  | order_id | amount
------------+-------+----------+--------
1           | Alice | 101      | 500.00
1           | Alice | 102      | 250.00
2           | Bob   | 103      | 800.00
```

The repeated customer columns are expected. They represent the one-to-many cardinality.

## Schema Design

A typical PostgreSQL schema is:

```sql
CREATE TABLE customers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(id)
);
```

Notice that `customer_id` is not unique.

That is what permits:

```text
customer_id
-----------
1
1
1
2
2
3
```

Multiple orders can reference the same customer.

Adding:

```sql
UNIQUE (customer_id)
```

would change the relationship into one-to-one and would prevent a customer from having multiple orders.

## Why the Foreign Key Belongs on the Many Side

The child table stores the identifier of its parent:

```text
customers
    id
     ↑
     │
orders
    customer_id
```

Each order needs to know which customer owns it.

This makes the foreign key naturally belong on `orders`.

The design also supports efficient operations such as:

```sql
SELECT *
FROM orders
WHERE customer_id = 42;
```

For production workloads, `orders.customer_id` should normally be indexed.

```sql
CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);
```

A foreign key does not universally guarantee that an index exists on the referencing column, so indexing requirements should be evaluated explicitly for the target database and workload.

## INNER JOIN

Use `INNER JOIN` when only parents with matching children should appear.

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id;
```

If:

```text
customers
1 Alice
2 Bob
3 Carol

orders
101 → Alice
102 → Alice
103 → Bob
```

the result contains:

```text
Alice → 101
Alice → 102
Bob   → 103
```

Carol is excluded because she has no matching order.

This is appropriate for queries such as:

> "Show all customers who have placed at least one order."

## LEFT JOIN

Use `LEFT JOIN` when the parent must remain in the result even if it has no children.

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

The result becomes:

```text
customer_id | name  | order_id
------------+-------+---------
1           | Alice | 101
1           | Alice | 102
2           | Bob   | 103
3           | Carol | NULL
```

Carol appears once with `NULL` child columns.

This is useful for:

- Customer dashboards.
- Administrative reports.
- "Customers with or without orders" queries.
- Finding inactive customers.
- Optional child relationships.

## One-to-Many JOIN Cardinality

The most important mental model is:

> A parent row can expand into multiple result rows.

If a customer has:

```text
N matching orders
```

then joining that customer to orders can produce:

```text
N result rows
```

This has important consequences for aggregation, pagination, API serialization, and further joins.

For example:

```sql
SELECT
    c.id,
    c.name,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

does not return one row per customer.

It returns one row per matching customer-order pair.

## JOIN Multiplication

One-to-many relationships become particularly important when multiple one-to-many relationships are joined.

Suppose a customer has:

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

The database is not duplicating data incorrectly. The result represents every matching combination:

```text
Order 1 × Ticket 1
Order 1 × Ticket 2
Order 1 × Ticket 3
Order 1 × Ticket 4
Order 2 × Ticket 1
...
Order 3 × Ticket 4
```

This is a major production and interview concept.

## Avoiding Accidental Row Multiplication

If the goal is to count customers with orders and tickets, directly joining both child tables can produce inflated counts.

Instead of:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count,
    COUNT(t.id) AS ticket_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id
GROUP BY c.id;
```

use independent aggregation:

```sql
SELECT
    c.id,
    COALESCE(o.order_count, 0) AS order_count,
    COALESCE(t.ticket_count, 0) AS ticket_count
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
        COUNT(*) AS ticket_count
    FROM support_tickets
    GROUP BY customer_id
) AS t
    ON t.customer_id = c.id;
```

Another option is `COUNT(DISTINCT ...)` when the required semantics support it:

```sql
SELECT
    c.id,
    COUNT(DISTINCT o.id) AS order_count,
    COUNT(DISTINCT t.id) AS ticket_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN support_tickets AS t
    ON t.customer_id = c.id
GROUP BY c.id;
```

Pre-aggregation is often clearer and can be more efficient for complex reporting workloads.

## Aggregating One-to-Many Data

A common use case is summarizing child records by parent.

For example:

```sql
SELECT
    c.id,
    c.name,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.amount), 0) AS total_spent
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.name;
```

This produces one result row per customer:

```text
customer_id | name  | order_count | total_spent
------------+-------+-------------+------------
1           | Alice | 2           | 750.00
2           | Bob   | 1           | 800.00
3           | Carol | 0           | 0
```

`LEFT JOIN` is important if customers with zero orders must remain in the report.

## COUNT(*) vs COUNT(column)

This distinction is especially important with `LEFT JOIN`.

Consider:

```sql
SELECT
    c.id,
    COUNT(*) AS row_count,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

For a customer with no orders:

```text
COUNT(*)   → 1
COUNT(o.id) → 0
```

The `LEFT JOIN` still produces a parent row, but the child columns are `NULL`.

Therefore:

> Use `COUNT(child.id)` when counting matching child records in an outer join.

## Filtering Child Rows

Suppose the requirement is:

> Show every customer and their completed orders.

A subtle distinction exists between putting the filter in `ON` and putting it in `WHERE`.

### Filter in ON

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

Customers without completed orders remain:

```text
Alice → completed order
Bob   → NULL
Carol → NULL
```

### Filter in WHERE

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

The `WHERE` predicate removes rows where `o.status` is `NULL`.

The query therefore behaves like an inner join for this condition.

This distinction is critical when working with optional child records.

## Finding Parents Without Children

A common anti-join pattern is:

```sql
SELECT
    c.id,
    c.name
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.id IS NULL;
```

This returns customers with no matching orders.

For example:

```text
customers
1 Alice
2 Bob
3 Carol

orders
101 → Alice
102 → Bob
```

Result:

```text
Carol
```

For existence checks, `NOT EXISTS` is often a clearer alternative:

```sql
SELECT
    c.id,
    c.name
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

Both patterns can be valid. Always inspect the execution plan for performance-sensitive queries.

## EXISTS vs JOIN

If the requirement is:

> "Return customers who have at least one order."

You do not necessarily need the order rows.

A join can work:

```sql
SELECT DISTINCT
    c.id,
    c.name
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

But `EXISTS` expresses the intent more directly:

```sql
SELECT
    c.id,
    c.name
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

Advantages of `EXISTS` include:

- No duplicate parent rows.
- No need for `DISTINCT`.
- Clear existence semantics.
- The optimizer can often stop looking after finding a qualifying child.

Use a `JOIN` when child columns are needed. Use `EXISTS` when you primarily need to test whether related rows exist.

## One-to-Many JOINs and Pagination

One-to-many joins can break naive offset pagination.

Consider:

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
ORDER BY c.id
LIMIT 20 OFFSET 20;
```

The result is paginating **joined rows**, not customers.

A customer with many orders can consume many result rows and cause:

- Fewer unique customers per page.
- Customers appearing on different pages.
- Unstable pagination as child records change.
- Difficult API response construction.

For APIs that paginate parents, paginate the parent entity first.

For example:

```sql
SELECT
    c.id,
    c.name
FROM customers AS c
ORDER BY c.id
LIMIT 20 OFFSET 20;
```

Then retrieve children separately or use a carefully designed query.

For large datasets, keyset pagination is generally preferable to deep offset pagination:

```sql
SELECT
    c.id,
    c.name
FROM customers AS c
WHERE c.id > 10000
ORDER BY c.id
LIMIT 20;
```

## One-to-Many JOINs and API Responses

Relational results are flat while API responses are often hierarchical.

SQL may return:

```text
customer | order
---------+------
Alice    | 101
Alice    | 102
Alice    | 103
```

while an API might need:

```json
{
  "id": 1,
  "name": "Alice",
  "orders": [
    {"id": 101},
    {"id": 102},
    {"id": 103}
  ]
}
```

There are several strategies:

- Fetch parent and children separately.
- Use ORM eager loading.
- Aggregate child rows in SQL.
- Use database JSON aggregation when appropriate.
- Use a dedicated read model for complex API projections.

The correct approach depends on result size, latency requirements, consistency requirements, and application architecture.

## PostgreSQL JSON Aggregation

PostgreSQL can construct hierarchical data directly.

```sql
SELECT
    c.id,
    c.name,
    COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'id', o.id,
                'amount', o.amount
            )
            ORDER BY o.created_at DESC
        ) FILTER (WHERE o.id IS NOT NULL),
        '[]'::jsonb
    ) AS orders
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.name;
```

This can be useful for read-heavy APIs where the database is already responsible for producing the required projection.

However, large child collections can create large database result values and increase memory, serialization, and network costs. Do not aggregate unbounded collections into a single API row.

## Django and One-to-Many Relationships

Django models a one-to-many relationship with `ForeignKey`.

```python
from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=200)


class Order(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
```

The database contains:

```text
customer.id
     ↑
     │
order.customer_id
```

Django provides the reverse relation:

```python
customer.orders.all()
```

For retrieving customers and their orders, use `prefetch_related()`:

```python
customers = Customer.objects.prefetch_related("orders")
```

Unlike `select_related()`, which is appropriate for single-valued relationships, `prefetch_related()` is designed for multi-valued relationships.

Conceptually:

```text
Query 1 → customers
Query 2 → orders for those customers
```

Django combines the results in application memory.

This is generally preferable to issuing one query per customer.

## N+1 Query Problem

This pattern can cause N+1 queries:

```python
customers = Customer.objects.all()

for customer in customers:
    for order in customer.orders.all():
        print(order.id)
```

Potentially:

```text
1 query → customers
N queries → orders for each customer
```

Use:

```python
customers = Customer.objects.prefetch_related("orders")
```

The application can then access:

```python
for customer in customers:
    for order in customer.orders.all():
        print(order.id)
```

without issuing a separate query for every customer.

For large collections, consider filtering the prefetched queryset:

```python
from django.db.models import Prefetch

customers = Customer.objects.prefetch_related(
    Prefetch(
        "orders",
        queryset=Order.objects.filter(status="completed").order_by("-created_at"),
    )
)
```

This avoids loading unrelated child records.

## Performance and Indexing

The most important index for a typical one-to-many relationship is the foreign key on the child table:

```sql
CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);
```

This supports queries such as:

```sql
SELECT *
FROM orders
WHERE customer_id = 42;
```

and joins such as:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = 42;
```

For common production queries, a composite index may be more appropriate:

```sql
CREATE INDEX idx_orders_customer_status_created
    ON orders(customer_id, status, created_at DESC);
```

Whether this is beneficial depends on the query workload.

Do not add indexes simply because a column participates in a join. Consider:

- Filter predicates.
- Sort requirements.
- Cardinality.
- Query frequency.
- Write overhead.
- Index storage.
- Execution plans.

## EXPLAIN and Query Plans

For performance-sensitive queries, inspect the database execution plan.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    c.name,
    o.id,
    o.amount
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = 42;
```

Look for:

- Unexpected sequential scans.
- Large row estimates vs actual row counts.
- Excessive nested-loop iterations.
- Large sorts.
- Hash-table memory pressure.
- Poor join selectivity.
- Significant buffer reads.
- Unexpected intermediate result sizes.

A join that is fast for 10,000 rows can become expensive at hundreds of millions of rows.

## Join Algorithms

The database optimizer chooses a physical join strategy based on statistics, indexes, cardinality estimates, available memory, and query structure.

Common algorithms include:

| Join algorithm | Typical characteristic |
|---|---|
| Nested Loop | Efficient when one side is small and the other side can be efficiently probed |
| Hash Join | Effective for equality joins over larger inputs |
| Merge Join | Useful when both inputs are appropriately ordered |
| Index-assisted lookup | Can efficiently probe indexed child rows |

The SQL query describes **what** result is required. The optimizer decides **how** to produce it.

Do not force a specific join algorithm unless there is a strong database-specific reason and the behavior has been validated.

## Large One-to-Many Tables

Production systems often have relationships such as:

```text
account
   │
   └── millions of transactions
```

Joining an account to millions of transactions can produce a very large intermediate result.

For high-volume systems:

- Filter early when semantically valid.
- Select only required columns.
- Index foreign keys and common predicates.
- Aggregate before joining when possible.
- Avoid loading unbounded child collections.
- Use partitioning when the workload justifies it.
- Consider read replicas for read-heavy workloads.
- Use precomputed summaries for expensive recurring reports.

For example, if the API only needs total transaction volume:

```sql
SELECT
    a.id,
    COALESCE(SUM(t.amount), 0) AS total_amount
FROM accounts AS a
LEFT JOIN transactions AS t
    ON t.account_id = a.id
GROUP BY a.id;
```

There is no reason to transfer every transaction row to the application.

## Transaction and Consistency Considerations

One-to-many data often changes independently of its parent.

For example:

```text
Customer
   │
   ├── Order
   ├── Order
   └── Order
```

A request reading customer and order data must account for the database's transaction isolation semantics.

If a report performs multiple independent queries:

```text
Query 1 → customers
Query 2 → orders
```

the two queries may observe different database states depending on the transaction boundary and isolation level.

A single SQL statement generally provides a consistent statement-level snapshot under PostgreSQL's normal `READ COMMITTED` behavior.

For workflows requiring stronger consistency, explicitly choose an appropriate transaction strategy rather than assuming multiple queries are equivalent to one atomic read.

## Deletion Semantics

One-to-many relationships require deliberate deletion behavior.

Example:

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL
        REFERENCES customers(id)
        ON DELETE RESTRICT
);
```

Possible policies include:

| Action | Meaning | Example |
|---|---|---|
| `CASCADE` | Delete children with parent | Temporary dependent records |
| `RESTRICT` | Prevent parent deletion | Financial records |
| `NO ACTION` | Enforce FK according to constraint timing | General referential integrity |
| `SET NULL` | Preserve child but remove association | Optional ownership |

For orders, transactions, invoices, or audit records, cascading deletion is often inappropriate because those records may have legal, financial, or operational retention requirements.

## Security Considerations

A join can accidentally broaden the data returned by an API.

For multi-tenant applications:

```sql
SELECT
    o.id,
    o.amount
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.id = :order_id;
```

may be insufficient if the application must also ensure that the order belongs to the authenticated tenant.

Prefer explicit authorization constraints:

```sql
SELECT
    o.id,
    o.amount
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.id = :order_id
  AND c.organization_id = :organization_id;
```

Authorization should not depend on the fact that tables are related.

Also:

- Parameterize user-controlled values.
- Select only required columns.
- Avoid exposing internal identifiers unnecessarily.
- Restrict sensitive child tables through database permissions where appropriate.
- Never assume a foreign key provides authorization.

## Common Mistakes

### Assuming a One-to-Many JOIN Returns One Row Per Parent

It does not.

A parent with 100 children can produce 100 joined rows.

Use aggregation, `EXISTS`, or a separate query when the desired result is one row per parent.

### Using DISTINCT to Hide Join Multiplication

This:

```sql
SELECT DISTINCT c.id, c.name
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

can be valid when only unique customers are needed, but `DISTINCT` should not be used automatically to hide an incorrect query.

If child columns are selected, `DISTINCT` may not eliminate the duplicates you expect.

Use `EXISTS` when the actual requirement is existence.

### Incorrect COUNT with Multiple Child Tables

Joining two one-to-many relationships can multiply rows.

Use:

```sql
COUNT(DISTINCT ...)
```

or, preferably for complex reporting, aggregate each child relationship independently before joining.

### Forgetting the Difference Between COUNT(*) and COUNT(child.id)

With `LEFT JOIN`:

```sql
COUNT(*)
```

counts the preserved parent row.

Use:

```sql
COUNT(child.id)
```

to count matching children.

### Turning LEFT JOIN into INNER JOIN Accidentally

This:

```sql
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed'
```

removes customers with no matching order.

If those customers must remain, move the child predicate into `ON`:

```sql
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed'
```

### Paginating Joined Rows

Pagination over a one-to-many join paginates result rows, not necessarily parent entities.

For parent-based APIs, paginate the parent dataset first or use a carefully designed projection.

### Loading Entire Child Collections

Fetching millions of child records into an application process can exhaust memory and increase latency.

Prefer:

- Filtering.
- Pagination.
- Aggregation.
- Streaming where appropriate.
- Targeted queries.

### Creating N+1 Queries in an ORM

Django's:

```python
customer.orders.all()
```

inside a loop can issue one query per customer.

Use:

```python
prefetch_related("orders")
```

when the child collection is required.

### Missing Foreign-Key Indexes

A frequently queried foreign key without an appropriate index can cause expensive scans.

Inspect actual query plans and workload characteristics.

### Using CASCADE Without Considering Data Retention

Cascading from a parent can delete large numbers of child rows.

For financial, compliance, audit, or historical data, deletion should be explicitly designed.

## Production Checklist

Before deploying a one-to-many query or schema:

- [ ] Is the relationship correctly modeled with a foreign key?
- [ ] Is the foreign key indexed for the actual workload?
- [ ] Is the relationship intentionally one-to-many rather than one-to-one?
- [ ] Is `INNER JOIN` or `LEFT JOIN` appropriate?
- [ ] Could the join multiply rows unexpectedly?
- [ ] Are multiple one-to-many relationships being joined?
- [ ] Are aggregates protected against row multiplication?
- [ ] Is `COUNT(child.id)` required instead of `COUNT(*)`?
- [ ] Are optional-child filters placed correctly?
- [ ] Could `EXISTS` express the requirement more directly?
- [ ] Is pagination operating on the intended entity?
- [ ] Is the child collection bounded?
- [ ] Has the query been tested with production-scale data?
- [ ] Has `EXPLAIN (ANALYZE, BUFFERS)` been reviewed for critical queries?
- [ ] Is ORM eager loading configured to avoid N+1 queries?
- [ ] Are authorization and tenant constraints explicit?
- [ ] Are deletion and retention policies intentional?
- [ ] Are transaction boundaries appropriate for the consistency requirements?

## Interview Traps

| Question | Correct reasoning |
|---|---|
| Where is the foreign key normally stored? | On the many-side/child table. |
| Does a foreign key make the relationship one-to-one? | No. Multiple child rows can reference the same parent unless uniqueness is enforced. |
| What does a one-to-many join return? | Potentially multiple result rows for each parent row. |
| Why can two one-to-many joins multiply rows? | Each child row on one side can combine with every matching child row on the other side. |
| Why use `COUNT(child.id)` with a `LEFT JOIN`? | The child identifier is `NULL` when no child exists, so it counts only matching children. |
| How do you find parents with no children? | Use `LEFT JOIN ... WHERE child.id IS NULL` or `NOT EXISTS`. |
| When is `EXISTS` preferable to `JOIN`? | When you only need to determine whether a related row exists. |
| Why can `DISTINCT` be dangerous as a fix? | It can hide incorrect cardinality or add expensive deduplication without addressing the underlying query logic. |
| Why can a one-to-many join break pagination? | The database paginates joined rows rather than logical parent entities. |
| What causes N+1 queries in Django? | Lazy loading a multi-valued relationship inside a loop. |
| Which Django optimization is typically used for one-to-many relationships? | `prefetch_related()`. |
| What is the key indexing consideration? | Index the child foreign key when the workload frequently joins or filters through it. |

## Key Takeaways

- **A one-to-many relationship stores the foreign key on the many-side, allowing multiple child rows to reference the same parent.**
- **A one-to-many `JOIN` expands parent rows into one result row per matching child, which directly affects aggregation, pagination, and API design.**
- **Joining multiple one-to-many relationships can multiply rows; use independent aggregation, `EXISTS`, or carefully designed projections when appropriate.**
- **For production systems, index foreign keys, inspect execution plans, bound child collections, avoid ORM N+1 queries, and define deletion semantics deliberately.**
- **Treat cardinality as a correctness concern: never use `DISTINCT`, application logic, or ORM behavior to hide an incorrectly modeled relationship.**