# 09- Multiple JOINs

## Overview

A query often needs data from more than two tables. **Multiple JOINs** allow a single SQL statement to compose related data across several tables while preserving explicit relationship and row-preservation semantics at each join.

A typical backend query might need to combine:

```text
customers
   │
   ├── orders
   │     │
   │     └── order_items
   │             │
   │             └── products
   │
   └── addresses
```

For example, an API endpoint returning an order summary may need customer, order, product, and payment information.

```sql
SELECT
    o.id AS order_id,
    c.id AS customer_id,
    c.email,
    p.id AS product_id,
    p.name AS product_name,
    oi.quantity,
    oi.unit_price
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
WHERE o.id = $1;
```

The important engineering principle is:

> Each JOIN adds another relational operation. Its join condition and join type can change both the meaning and the cardinality of the result.

## Why Multiple JOINs Matter

Production applications rarely store all information in one table. Normalized schemas deliberately separate entities and relationships:

- `customers` stores customer identity.
- `orders` stores order-level state.
- `order_items` stores line items.
- `products` stores product metadata.
- `payments` stores payment transactions.

Multiple joins allow the database to reconstruct the required view without duplicating the same information across tables.

This is especially important for:

- REST API read models.
- Reporting queries.
- Administrative dashboards.
- Financial reconciliation.
- Search endpoints.
- Authorization checks.
- Operational tooling.
- Analytics and business intelligence.

## Basic Structure

Multiple joins are written by adding JOIN clauses to the same query:

```sql
SELECT
    ...
FROM table_a AS a
JOIN table_b AS b
    ON b.a_id = a.id
JOIN table_c AS c
    ON c.b_id = b.id
JOIN table_d AS d
    ON d.c_id = c.id;
```

Each table reference gets an alias when the query becomes non-trivial.

A useful mental model is:

```text
FROM
  A
   │
   JOIN B
   │
   JOIN C
   │
   JOIN D
```

The optimizer is free to choose an efficient physical execution strategy; the textual order should primarily communicate the intended relationships and semantics.

## Example Schema

Consider an e-commerce system:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    email text NOT NULL
);

CREATE TABLE orders (
    id bigint PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status text NOT NULL,
    created_at timestamptz NOT NULL
);

CREATE TABLE products (
    id bigint PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE order_items (
    order_id bigint NOT NULL REFERENCES orders(id),
    product_id bigint NOT NULL REFERENCES products(id),
    quantity integer NOT NULL,
    unit_price numeric(12, 2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

A query spanning the schema:

```sql
SELECT
    o.id AS order_id,
    c.email,
    p.name,
    oi.quantity,
    oi.unit_price
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
WHERE o.id = $1;
```

produces one result row per matching order item.

That last point is critical: joining a one-to-many relationship changes result cardinality.

## JOIN Types in a Multiple-JOIN Query

Different joins can coexist in the same query.

```sql
SELECT
    o.id,
    c.email,
    p.name,
    pay.status
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
LEFT JOIN payments AS pay
    ON pay.order_id = o.id
WHERE o.id = $1;
```

Here:

- `JOIN customers` requires a customer.
- `JOIN order_items` requires at least one item.
- `JOIN products` requires each item to resolve to a product.
- `LEFT JOIN payments` preserves the order even when no payment exists.

The join type is a semantic decision, not merely a syntax preference.

## INNER JOIN Chains

An `INNER JOIN` keeps only rows satisfying every required relationship.

```sql
SELECT
    o.id,
    c.email,
    p.name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id;
```

Conceptually:

```text
orders
  ↓
customers
  ↓
order_items
  ↓
products
```

An order with no order items disappears.

An order item referencing no product also disappears.

With enforced foreign keys, the latter should normally be impossible.

## Mixing INNER and LEFT JOINs

A common production pattern is:

```sql
SELECT
    o.id,
    c.email,
    s.tracking_number,
    p.name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
LEFT JOIN shipments AS s
    ON s.order_id = o.id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
WHERE o.status = 'confirmed';
```

This means:

```text
Order
 ├── Customer      required
 ├── Shipment      optional
 └── Items         required
      └── Product  required
```

A missing shipment does not eliminate the order.

This is often what an API needs when an order can exist before fulfillment creates a shipment.

## Multiple LEFT JOINs

Multiple optional relationships can be composed:

```sql
SELECT
    c.id,
    c.email,
    a.city,
    o.id AS order_id,
    pay.status AS payment_status
FROM customers AS c
LEFT JOIN addresses AS a
    ON a.id = c.default_address_id
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN payments AS pay
    ON pay.order_id = o.id;
```

Every customer remains in the result, including customers with:

- No address.
- No orders.
- Orders without payments.

However, the result may contain multiple rows per customer because one customer can have multiple orders.

## Join Cardinality

One of the most important concepts in multiple joins is **cardinality**.

Suppose:

```text
1 customer
   ↓
10 orders
   ↓
5 items per order
```

A query joining all three levels can produce approximately:

```text
1 × 10 × 5 = 50 rows
```

The database is not necessarily duplicating data incorrectly. Each result row represents a particular combination of related entities.

For example:

```text
customer | order | product
---------+-------+--------
Alice    | 101   | A
Alice    | 101   | B
Alice    | 102   | C
Alice    | 102   | D
...
```

The customer values repeat because the relational result is at the order-item grain.

## Row Grain

Before writing a multiple-join query, explicitly identify the intended **grain** of the result.

Examples:

| Desired grain | Typical result |
| --- | --- |
| One row per customer | Customer-level |
| One row per order | Order-level |
| One row per order item | Line-item-level |
| One row per product | Product-level |
| One row per customer/order combination | Relationship-level |

This prevents many aggregation and duplication bugs.

For example, if the API needs one row per order, directly joining `order_items` will normally produce multiple rows per order.

You may instead aggregate:

```sql
SELECT
    o.id AS order_id,
    c.email,
    COUNT(oi.product_id) AS item_count
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
LEFT JOIN order_items AS oi
    ON oi.order_id = o.id
GROUP BY
    o.id,
    c.email;
```

## The Row Multiplication Problem

Consider:

```text
customers
    │
    ├── orders
    │
    └── addresses
```

If a customer has:

```text
3 orders
2 addresses
```

and both are independently one-to-many relationships, joining both directly can create:

```text
3 × 2 = 6 rows
```

Example:

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

The query produces every matching order-address combination.

This is a common cause of inflated counts and incorrect aggregates.

## Avoiding Cross-Product Effects

If independent one-to-many relationships are being aggregated, aggregate each relationship separately before joining.

For example:

```sql
WITH order_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
),
address_counts AS (
    SELECT
        customer_id,
        COUNT(*) AS address_count
    FROM addresses
    GROUP BY customer_id
)
SELECT
    c.id,
    COALESCE(oc.order_count, 0) AS order_count,
    COALESCE(ac.address_count, 0) AS address_count
FROM customers AS c
LEFT JOIN order_counts AS oc
    ON oc.customer_id = c.id
LEFT JOIN address_counts AS ac
    ON ac.customer_id = c.id;
```

Now each aggregated relationship has one row per customer before the joins occur.

This preserves the intended customer-level grain.

## JOIN Conditions Matter

Each join should express the relationship between the two logical entities.

Good:

```sql
JOIN order_items AS oi
    ON oi.order_id = o.id
```

Potentially dangerous:

```sql
JOIN order_items AS oi
    ON oi.order_id = o.id
   OR oi.product_id = p.id
```

Broad conditions can dramatically increase cardinality.

A missing or incorrect join predicate can effectively create a Cartesian product.

Always validate:

- Which entities are being connected.
- Which key defines the relationship.
- Whether the relationship is one-to-one, one-to-many, or many-to-many.
- Whether additional predicates belong in the join condition.

## Filtering in ON vs WHERE

This distinction becomes especially important with `LEFT JOIN`.

Consider:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

The `WHERE` condition removes rows where `o.status` is `NULL`, effectively eliminating customers without paid orders.

The query behaves much more like an inner join for that condition.

If the requirement is:

> Return every customer and attach only paid orders.

Use:

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'paid';
```

Now customers without paid orders remain.

This is one of the most important practical `LEFT JOIN` rules.

## Join Order and Query Semantics

SQL's logical processing model should be understood separately from the optimizer's physical execution plan.

Conceptually:

```text
FROM
  ↓
JOIN / ON
  ↓
WHERE
  ↓
GROUP BY
  ↓
HAVING
  ↓
SELECT
  ↓
ORDER BY
  ↓
LIMIT
```

The database optimizer can reorder joins and choose different algorithms when doing so preserves query semantics.

Therefore:

> Do not assume the textual JOIN order is the physical execution order.

Use `EXPLAIN` to understand the actual plan.

## Join Algorithms

Database engines commonly implement joins using algorithms such as:

| Join algorithm | Typical use |
| --- | --- |
| Nested Loop | Small outer input or efficient indexed lookup |
| Hash Join | Large equality joins |
| Merge Join | Sorted inputs or useful ordering |
| Nested Loop with index scan | Highly selective lookup |

For example:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    o.id,
    c.email,
    p.name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days';
```

The exact plan depends on:

- Table sizes.
- Statistics.
- Indexes.
- Predicate selectivity.
- Available memory.
- Data distribution.
- Database configuration.

## Indexing Multiple JOINs

Each relationship should be evaluated independently.

Suppose:

```sql
orders.customer_id
order_items.order_id
order_items.product_id
```

are frequently used for joins.

Useful indexes may include:

```sql
CREATE INDEX ix_orders_customer_id
ON orders (customer_id);

CREATE INDEX ix_order_items_order_id
ON order_items (order_id);

CREATE INDEX ix_order_items_product_id
ON order_items (product_id);
```

Primary keys already provide indexes in typical relational databases, so an additional index on:

```sql
customers.id
products.id
```

is usually unnecessary.

Do not blindly add an index for every column appearing in a query. Indexes have:

- Storage cost.
- Write amplification.
- Maintenance overhead.
- Cache implications.

Use query plans and workload characteristics to validate indexing decisions.

## Filtering Early

Selective predicates can dramatically reduce the amount of data participating in subsequent operations.

For example:

```sql
SELECT
    o.id,
    c.email,
    p.name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
WHERE o.status = 'completed'
  AND o.created_at >= $1;
```

The optimizer may push predicates down automatically when safe.

Do not rely on manually rewriting queries solely to force execution order. Instead:

1. Write correct relational logic.
2. Provide appropriate predicates.
3. Maintain useful statistics.
4. Inspect the execution plan.
5. Optimize based on measured behavior.

## Many-to-Many Relationships

Multiple joins are commonly required to traverse many-to-many relationships.

Consider:

```text
users
  │
  ▼
user_roles
  │
  ▼
roles
```

Query:

```sql
SELECT
    u.id,
    u.email,
    r.name AS role
FROM users AS u
JOIN user_roles AS ur
    ON ur.user_id = u.id
JOIN roles AS r
    ON r.id = ur.role_id
WHERE u.id = $1;
```

The join table is not an implementation detail to ignore. It represents the relationship and determines result cardinality.

A user with five roles produces five rows.

## Multiple JOINs in Authorization

A production authorization query may traverse several relationships:

```sql
SELECT 1
FROM users AS u
JOIN organization_members AS om
    ON om.user_id = u.id
JOIN roles AS r
    ON r.id = om.role_id
JOIN role_permissions AS rp
    ON rp.role_id = r.id
JOIN permissions AS p
    ON p.id = rp.permission_id
WHERE u.id = $1
  AND om.organization_id = $2
  AND p.name = $3;
```

This can answer:

> Does this user have this permission in this organization?

The tenant boundary:

```sql
om.organization_id = $2
```

must be part of the authorization logic rather than inferred from unrelated application state.

For security-sensitive queries, review the entire join path for possible cross-tenant access.

## Multiple JOINs in Backend APIs

Suppose a FastAPI endpoint returns order details.

A single SQL query can retrieve a flat relational result:

```sql
SELECT
    o.id AS order_id,
    o.status,
    c.email,
    oi.quantity,
    oi.unit_price,
    p.id AS product_id,
    p.name AS product_name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
WHERE o.id = $1
ORDER BY p.id;
```

The application can then transform rows into the API representation:

```json
{
  "id": 1001,
  "status": "confirmed",
  "customer": {
    "email": "customer@example.com"
  },
  "items": [
    {
      "product_id": 10,
      "name": "Keyboard",
      "quantity": 1,
      "unit_price": "79.00"
    }
  ]
}
```

This is often preferable to executing one query for the order, one for the customer, one for every item, and one for every product.

The trade-off is that SQL result shaping and application-level transformation must be designed together.

## ORM Considerations

Django provides explicit tools for traversing relationships efficiently.

For single-valued relationships:

```python
orders = (
    Order.objects
    .filter(status="confirmed")
    .select_related("customer")
)
```

For collections:

```python
orders = (
    Order.objects
    .filter(status="confirmed")
    .select_related("customer")
    .prefetch_related("items__product")
)
```

The distinction matters:

| Relationship | Django strategy |
| --- | --- |
| `ForeignKey` / `OneToOneField` | `select_related()` |
| Reverse FK / many-to-many | `prefetch_related()` |

The objective is not to minimize the number of SQL statements at all costs. The objective is to avoid unnecessary round trips while keeping result size and memory usage reasonable.

## Debugging Multiple JOINs

When a query returns unexpected rows, debug it incrementally.

Start with the base relation:

```sql
SELECT COUNT(*)
FROM orders;
```

Add one relationship:

```sql
SELECT COUNT(*)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

Add the next:

```sql
SELECT COUNT(*)
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id;
```

Then inspect the grain:

```sql
SELECT
    o.id,
    COUNT(*) AS rows_per_order
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
JOIN products AS p
    ON p.id = oi.product_id
GROUP BY o.id
ORDER BY rows_per_order DESC;
```

This makes it easier to identify which relationship introduces unexpected multiplicity.

## Common Production Pitfalls

### Joining Without Understanding Cardinality

Assuming every join preserves one row per entity leads to incorrect results.

Before joining, determine whether the relationship is:

```text
1 → 1
1 → many
many → many
```

Then predict the resulting grain.

### Using DISTINCT to Hide Duplicates

A common reaction to duplicate rows is:

```sql
SELECT DISTINCT ...
```

This can hide the symptom without fixing the relational problem.

`DISTINCT` is appropriate when duplicate elimination is part of the actual requirement. It should not normally be used as a generic repair mechanism for an incorrect join.

### Incorrect LEFT JOIN Filtering

This:

```sql
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid'
```

can remove customers without paid orders.

If optional rows must remain, put the optional-row predicate in `ON`:

```sql
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'paid'
```

### Joining Independent One-to-Many Relationships

Joining two independent child collections can multiply rows:

```text
customer
 ├── orders
 └── addresses
```

Aggregate or pre-filter the relationships when the required result is at the parent grain.

### Selecting `*`

Avoid:

```sql
SELECT *
```

in production API queries.

Explicit projection:

```sql
SELECT
    o.id,
    o.status,
    c.email,
    p.name
```

provides:

- Stable API-facing data.
- Less network transfer.
- Lower memory usage.
- Better readability.
- Reduced accidental exposure of sensitive columns.

### Missing Tenant Predicates

In multi-tenant systems, joining by an ID without validating tenant ownership can expose data if the schema permits inconsistent references.

Prefer database-enforced tenant invariants where possible and include tenant predicates where required by the access model.

### Assuming More JOINs Always Mean Worse Performance

The number of joins alone does not determine query performance.

A query joining several small, well-indexed tables can be faster than multiple application round trips.

Measure:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and optimize the actual bottleneck.

## Performance and Scalability

For production workloads:

- Select only required columns.
- Filter by selective predicates.
- Index foreign-key columns used heavily for lookups.
- Keep statistics current.
- Avoid accidental many-to-many expansion.
- Paginate at the correct grain.
- Avoid loading huge relational graphs into memory.
- Inspect execution plans for slow queries.
- Consider pre-aggregation for expensive reporting workloads.
- Use read replicas carefully for read-heavy workloads where replica lag is acceptable.

For very large datasets, joining a broad unfiltered relationship and applying pagination afterward can be expensive.

For example, this:

```sql
SELECT
    c.id,
    o.id,
    oi.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id
ORDER BY c.id
LIMIT 50;
```

does not necessarily mean only 50 logical customers are being processed.

If the API requires **50 customers**, pagination should be designed around the customer grain rather than the multiplied join result.

## Observability

Slow multiple-join queries should be observable through:

- Query duration.
- Rows returned.
- Rows examined or processed.
- Database CPU.
- Buffer/cache behavior.
- Lock waits.
- Connection pool saturation.
- Query frequency.
- Error rate.

In PostgreSQL, tools such as:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and workload statistics can help identify expensive joins.

For backend services, correlate database query latency with:

```text
HTTP/gRPC request
        ↓
Application service
        ↓
SQL query
        ↓
Database execution
        ↓
Serialized response
```

A query that is fast in isolation can still cause production problems when executed thousands of times per minute.

## A Practical Query Review Process

When reviewing a multiple-join query:

1. Identify the required result grain.
2. List every table required to produce that grain.
3. Document the relationship between each table.
4. Choose `INNER` versus outer joins deliberately.
5. Check whether any one-to-many relationship multiplies rows.
6. Check predicates on optional relationships.
7. Verify tenant and authorization boundaries.
8. Select only required columns.
9. Check relevant indexes.
10. Run the query with realistic data volumes.
11. Inspect `EXPLAIN (ANALYZE, BUFFERS)` for performance-sensitive queries.
12. Test edge cases such as missing optional relationships and empty collections.

## Interview Traps

| Question | Correct reasoning |
| --- | --- |
| Does adding a JOIN always increase result rows? | No. An inner join can reduce rows; outer joins preserve rows from one side; one-to-many relationships can multiply rows. |
| Does textual JOIN order determine execution order? | No. The optimizer can reorder joins when semantics permit. |
| Why can two LEFT JOINs produce unexpected duplicates? | Independent one-to-many relationships can create combinations between child rows. |
| Why does `WHERE child.status = ...` change a LEFT JOIN? | It removes NULL-extended rows, often making the optional relationship behave like an inner join for that predicate. |
| Is `DISTINCT` the best fix for duplicate rows? | Usually not. First identify the incorrect cardinality or join condition. |
| What should be identified before writing a complex query? | The intended result grain and the cardinality of each relationship. |
| How do you optimize a multi-join query? | Measure with execution plans, validate indexes, reduce unnecessary rows/columns, and address the actual bottleneck. |
| Can several JOINs be faster than several application queries? | Yes. A well-planned query can avoid network round trips and application-side N+1 behavior. |
| What happens when a one-to-many table is joined? | A source row can appear once for each matching child row. |
| How should independent child collections be aggregated? | Often aggregate each collection before joining it back to the parent grain. |

## Production Checklist

- [ ] Define the intended result grain.
- [ ] Verify every JOIN condition against the actual data model.
- [ ] Understand the cardinality of every relationship.
- [ ] Deliberately choose `INNER`, `LEFT`, `RIGHT`, or `FULL` semantics.
- [ ] Check for accidental row multiplication.
- [ ] Review `ON` versus `WHERE` predicates for outer joins.
- [ ] Enforce tenant boundaries where applicable.
- [ ] Avoid `SELECT *` for production-facing queries.
- [ ] Verify indexes for high-frequency join paths.
- [ ] Test with realistic data volumes and distributions.
- [ ] Inspect `EXPLAIN (ANALYZE, BUFFERS)` for performance-sensitive queries.
- [ ] Check ORM-generated SQL for N+1 behavior.
- [ ] Validate pagination at the intended result grain.
- [ ] Monitor query latency and database resource usage.
- [ ] Test missing optional relationships and empty child collections.

## Key Takeaways

- **Multiple JOINs compose several relationships in one SQL statement, but every JOIN can change result cardinality and semantics.**
- **Always define the intended result grain and understand each relationship's cardinality before composing the query.**
- **Be especially careful when joining multiple independent one-to-many relationships because their rows can multiply each other.**
- **With outer joins, predicate placement in `ON` versus `WHERE` can determine whether unmatched rows survive.**
- **For production performance, measure the complete query with realistic data using execution plans rather than judging performance by JOIN count alone.**