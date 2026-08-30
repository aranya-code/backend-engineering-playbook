# 06- Subqueries in SELECT

## Overview

A subquery in the `SELECT` list is a query expression evaluated as part of producing each output row. It is most commonly used to calculate a **single value per outer row**, such as a related record's attribute, an aggregate, or a derived status.

For example, returning each customer together with the timestamp of their most recent order:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

The outer query determines which customers are returned. The subquery derives an additional value for each customer.

This pattern is useful, but it requires careful attention to **cardinality, correlation, indexing, and whether a JOIN or window function would express the operation more efficiently**.

## Basic Structure

The general form is:

```sql
SELECT
    column_a,
    (
        SELECT expression
        FROM related_table
        WHERE related_table.foreign_key = outer_table.id
    ) AS derived_value
FROM outer_table;
```

The subquery must produce a scalar result for each outer row when used directly in the `SELECT` list.

A scalar subquery may return:

- One value.
- `NULL` when no row is produced.
- An error if multiple rows are returned where a single value is required.

For example:

```sql
SELECT
    c.id,
    (
        SELECT o.status
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_status
FROM customers AS c;
```

This is only valid if the correlated condition guarantees at most one matching order.

If a customer has multiple orders, the query can fail because the scalar subquery returns more than one row.

## Why Use Subqueries in `SELECT`

A `SELECT`-list subquery is useful when the outer result needs a **derived scalar attribute** without changing the number of outer rows.

Typical use cases include:

| Use case | Example |
|---|---|
| Latest related timestamp | Last order date |
| Related aggregate | Total order amount |
| Conditional existence indicator | Has paid order |
| Single related attribute | Current subscription plan |
| Derived metric | Number of failed payments |
| Correlated lookup | Latest status |
| Nested calculation | Percentage derived from related rows |

The key property is that the subquery contributes a value to an existing row rather than expanding the result set.

## Scalar Subqueries in the `SELECT` List

An aggregate is often the safest way to guarantee one result.

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count
FROM customers AS c;
```

For every customer, the subquery returns exactly one aggregate value.

Conceptually:

```text
Customer 101 ──► COUNT(orders for 101) ──► 12
Customer 102 ──► COUNT(orders for 102) ──►  4
Customer 103 ──► COUNT(orders for 103) ──►  0
```

This preserves one output row per customer.

## Correlation

A `SELECT`-list subquery is frequently correlated with the outer query.

```sql
SELECT
    p.id,
    p.name,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.product_id = p.id
    ) AS last_order_at
FROM products AS p;
```

The reference:

```sql
o.product_id = p.id
```

connects the inner query to the current outer row.

Without correlation:

```sql
SELECT
    p.id,
    p.name,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
    ) AS last_order_at
FROM products AS p;
```

the same global value is returned for every product.

This distinction is critical:

| Subquery | Meaning |
|---|---|
| Uncorrelated | One independent result can be reused conceptually across outer rows |
| Correlated | Result depends on the current outer row |

## A Practical Example: Customer Order Metrics

Consider:

```text
customers
---------
id
email

orders
------
id
customer_id
status
total_amount
created_at
```

A customer API may need:

- Customer ID.
- Email.
- Number of orders.
- Total paid revenue.
- Most recent order date.

A `SELECT`-list approach could be:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count,
    (
        SELECT COALESCE(SUM(o.total_amount), 0)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'paid'
    ) AS paid_revenue,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

This is readable and expresses each metric independently.

However, multiple correlated subqueries against the same large table can become expensive. A grouped derived relation or pre-aggregation may be preferable for high-volume workloads.

## `NULL` When No Related Row Exists

Consider:

```sql
SELECT
    c.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

For a customer with no orders:

```text
last_order_at = NULL
```

This is generally the correct representation because there is no timestamp.

If the application requires a fallback value, use `COALESCE`:

```sql
SELECT
    c.id,
    COALESCE(
        (
            SELECT MAX(o.created_at)
            FROM orders AS o
            WHERE o.customer_id = c.id
        ),
        TIMESTAMP '1970-01-01'
    ) AS last_order_at
FROM customers AS c;
```

Choose fallback values carefully. Converting "no order" into an artificial timestamp can make downstream business logic misleading.

For presentation-oriented defaults, it is often better to keep the database value as `NULL` and let the API layer represent the absence explicitly.

## Conditional Metrics

A `SELECT`-list subquery can calculate a conditional aggregate.

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'failed'
    ) AS failed_order_count
FROM customers AS c;
```

Multiple related metrics can be exposed as separate columns.

For example:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'paid'
    ) AS paid_orders,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'failed'
    ) AS failed_orders
FROM customers AS c;
```

For several metrics over the same relation, however, conditional aggregation with a single scan may be more efficient:

```sql
SELECT
    c.id,
    COUNT(*) FILTER (WHERE o.status = 'paid') AS paid_orders,
    COUNT(*) FILTER (WHERE o.status = 'failed') AS failed_orders
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

The better choice depends on the execution plan and workload.

## Getting a Single Related Value

A scalar subquery can retrieve one related attribute when the data model guarantees uniqueness.

Suppose each customer has at most one active subscription:

```sql
SELECT
    c.id,
    (
        SELECT s.plan_name
        FROM subscriptions AS s
        WHERE s.customer_id = c.id
          AND s.status = 'active'
    ) AS active_plan
FROM customers AS c;
```

This requires the database model to enforce the assumption that there cannot be multiple active subscriptions for the same customer.

In PostgreSQL, a partial unique index can enforce this invariant:

```sql
CREATE UNIQUE INDEX uq_active_subscription_per_customer
    ON subscriptions (customer_id)
    WHERE status = 'active';
```

This is stronger than relying on application code to ensure scalar-subquery cardinality.

## Latest Related Row

A common production requirement is:

> Return each customer and the details of their latest order.

A correlated subquery can retrieve a scalar attribute:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT o.id
        FROM orders AS o
        WHERE o.customer_id = c.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS latest_order_id
FROM customers AS c;
```

The secondary ordering by `o.id` provides deterministic tie-breaking when two orders have the same timestamp.

The same pattern can retrieve another scalar:

```sql
SELECT
    c.id,
    (
        SELECT o.total_amount
        FROM orders AS o
        WHERE o.customer_id = c.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS latest_order_amount
FROM customers AS c;
```

If several columns from the same latest row are required, repeating the subquery is usually undesirable. A window function, `LATERAL` join, or database-specific row construction may provide a better design.

## `SELECT`-List Subquery vs JOIN

Consider:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

A JOIN-based equivalent is:

```sql
SELECT
    c.id,
    c.email,
    MAX(o.created_at) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email;
```

The two approaches can represent the same business requirement.

The choice depends on what the query is trying to express.

| Requirement | Often clearer |
|---|---|
| Calculate one scalar per outer row | Scalar subquery |
| Aggregate several related metrics | JOIN + aggregation |
| Return related rows | JOIN |
| Determine existence only | `EXISTS` |
| Rank related rows | Window function |
| Fetch several columns from one correlated row | `LATERAL` or window function |

Do not choose based on syntax preference alone. Compare the execution plans for important production queries.

## `SELECT`-List Subquery vs Window Function

Suppose the requirement is:

> Show each order and the customer's latest order date.

A correlated subquery could be:

```sql
SELECT
    o.id,
    o.customer_id,
    o.created_at,
    (
        SELECT MAX(o2.created_at)
        FROM orders AS o2
        WHERE o2.customer_id = o.customer_id
    ) AS customer_last_order_at
FROM orders AS o;
```

A window function can express the same relationship:

```sql
SELECT
    o.id,
    o.customer_id,
    o.created_at,
    MAX(o.created_at) OVER (
        PARTITION BY o.customer_id
    ) AS customer_last_order_at
FROM orders AS o;
```

Window functions are often a better fit when the query is already operating over the related rows.

A scalar subquery is often easier to read when the outer row is conceptually the primary entity and the subquery provides one derived attribute.

## `SELECT`-List Subquery vs `EXISTS`

If the requirement is only:

> Does this customer have a paid order?

do not calculate a count when a boolean is sufficient.

A correlated count:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'paid'
    ) > 0 AS has_paid_order
FROM customers AS c;
```

An existence check is more directly aligned with the requirement:

```sql
SELECT
    c.id,
    EXISTS (
        SELECT 1
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'paid'
    ) AS has_paid_order
FROM customers AS c;
```

`EXISTS` communicates that the query only needs to know whether a qualifying row exists.

The database may also be able to stop searching after finding a qualifying row.

## Performance Model

A common misconception is:

> "A correlated subquery runs once for every outer row, so it is always slow."

That is too simplistic.

The optimizer may transform or execute a correlated expression using indexes, joins, aggregation, caching, or other strategies depending on the database.

Still, correlation creates an important optimization boundary to investigate.

For:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count
FROM customers AS c;
```

the database needs an efficient way to find orders by `customer_id`.

An index such as:

```sql
CREATE INDEX idx_orders_customer_id
    ON orders (customer_id);
```

may be important.

For a latest-row query:

```sql
SELECT
    c.id,
    (
        SELECT o.id
        FROM orders AS o
        WHERE o.customer_id = c.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS latest_order_id
FROM customers AS c;
```

an index aligned with the lookup and ordering can be valuable:

```sql
CREATE INDEX idx_orders_customer_created_id
    ON orders (customer_id, created_at DESC, id DESC);
```

Always validate the actual plan before adding an index.

## Execution Plan Analysis

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count
FROM customers AS c;
```

Inspect:

- Actual execution time.
- Outer row count.
- Subplan loops.
- Index scans versus sequential scans.
- Rows removed by filters.
- Buffer hits and reads.
- Cardinality estimates.
- Temporary disk activity.
- CPU-heavy operations.

A particularly important signal for correlated subqueries is the number of loops of the subplan.

A plan showing a subplan executed hundreds of thousands of times deserves careful investigation.

That does not automatically mean it is wrong; an indexed lookup returning quickly for each outer row can be perfectly acceptable. The goal is to measure actual cost rather than infer performance from SQL syntax.

## Multiple Subqueries Against the Same Table

Consider:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count,
    (
        SELECT COALESCE(SUM(o.total_amount), 0)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'paid'
    ) AS paid_revenue,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

This is readable, but the same `orders` relation is referenced three times.

A single grouped relation may consolidate the work:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count,
    COALESCE(
        SUM(o.total_amount) FILTER (WHERE o.status = 'paid'),
        0
    ) AS paid_revenue,
    MAX(o.created_at) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This can be substantially better for large datasets, but it is not a universal rule. An indexed correlated lookup can be competitive when the outer result set is small and the related table is large.

## `LATERAL` for Multiple Values from One Related Row

When several columns from one correlated row are needed, PostgreSQL's `LATERAL` can be cleaner than repeating scalar subqueries.

For example:

```sql
SELECT
    c.id,
    c.email,
    latest.id AS latest_order_id,
    latest.created_at AS latest_order_at,
    latest.total_amount AS latest_order_amount
FROM customers AS c
LEFT JOIN LATERAL (
    SELECT
        o.id,
        o.created_at,
        o.total_amount
    FROM orders AS o
    WHERE o.customer_id = c.id
    ORDER BY o.created_at DESC, o.id DESC
    LIMIT 1
) AS latest
    ON true;
```

This expresses:

> For each customer, find the latest matching order and expose multiple columns from that row.

It can also work well with an index such as:

```sql
CREATE INDEX idx_orders_customer_created_id
    ON orders (customer_id, created_at DESC, id DESC);
```

`LATERAL` is particularly useful when the inner query needs values from the current outer row and returns a small, controlled number of rows.

## Subqueries in `SELECT` and API Design

Suppose an API endpoint returns:

```json
{
  "id": 101,
  "email": "customer@example.com",
  "order_count": 42,
  "last_order_at": "2026-08-20T10:30:00Z"
}
```

A database query can calculate these fields in one round trip:

```sql
SELECT
    c.id,
    c.email,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c
WHERE c.id = :customer_id;
```

This is often preferable to:

1. Query customer.
2. Query order count.
3. Query latest order.
4. Assemble the response in Python.

The latter can create unnecessary database round trips.

The important distinction is between **one SQL statement containing several expressions** and several independent application-level queries.

## Django ORM

Django supports correlated subqueries using `OuterRef` and `Subquery`.

For example:

```python
from django.db.models import OuterRef, Subquery

latest_order = (
    Order.objects
    .filter(customer_id=OuterRef("pk"))
    .order_by("-created_at", "-id")
)

customers = Customer.objects.annotate(
    latest_order_id=Subquery(
        latest_order.values("id")[:1],
    ),
)
```

The ORM can generate SQL equivalent in concept to:

```sql
SELECT
    c.id,
    (
        SELECT o.id
        FROM orders AS o
        WHERE o.customer_id = c.id
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS latest_order_id
FROM customers AS c;
```

For boolean existence:

```python
from django.db.models import Exists, OuterRef

paid_orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
    status="paid",
)

customers = Customer.objects.annotate(
    has_paid_order=Exists(paid_orders),
)
```

For high-volume query paths, inspect the SQL and execution plan rather than assuming the ORM-generated query is optimal.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Returning multiple rows from a scalar subquery | Cardinality assumption is incorrect | Use an aggregate, `LIMIT 1` with deterministic ordering, or a JOIN |
| Assuming `LIMIT 1` without `ORDER BY` is deterministic | SQL does not guarantee arbitrary row selection | Define explicit ordering |
| Using several subqueries against the same large table | Each metric is expressed independently | Consider grouped aggregation or another set-oriented design |
| Using a count for an existence check | The requirement is expressed as a quantity instead of a boolean | Prefer `EXISTS` |
| Ignoring `NULL` | No matching related row naturally produces `NULL` | Define null semantics explicitly |
| Assuming correlated means always slow | Oversimplified mental model | Inspect the execution plan |
| Assuming JOIN is always faster | Physical plans vary by workload | Benchmark representative data |
| Repeating the same latest-row subquery for many columns | Each expression repeats the lookup | Consider `LATERAL` or window functions |
| Omitting a tie-breaker in latest-row queries | Equal timestamps can produce unstable selection | Order by timestamp plus a unique key |
| Moving derived calculations into Python unnecessarily | Application-level processing creates extra data movement | Push relational computation into SQL when appropriate |

## Production Considerations

### Index for the Correlation Predicate

If the inner query contains:

```sql
WHERE o.customer_id = c.id
```

the related table should generally have an appropriate index when the workload benefits from indexed lookups.

For latest-row access:

```sql
WHERE o.customer_id = c.id
ORDER BY o.created_at DESC, o.id DESC
LIMIT 1
```

consider an index aligned with both filtering and ordering.

### Keep Query Shape Intentional

A `SELECT`-list subquery is not inherently bad. It becomes problematic when it hides expensive repeated work.

Before optimizing, determine:

- How many outer rows are returned?
- How many inner rows match each outer row?
- How selective is the correlation predicate?
- Is an index available?
- How often is the endpoint called?
- What does `EXPLAIN (ANALYZE, BUFFERS)` show?

### Avoid Premature Denormalization

If an API needs `order_count`, do not immediately add a cached counter column.

First determine whether the query is actually a bottleneck.

For very high-volume systems, precomputed counters, materialized views, summary tables, or event-driven aggregation may eventually be justified. Those designs introduce consistency and operational complexity and should be driven by measured workload requirements.

### Transactions and Consistency

A derived value is only as consistent as the transaction snapshot from which it is calculated.

For example:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count
FROM customers AS c;
```

should not be interpreted as a permanent guarantee that the count remains unchanged after the query.

If the application uses the result to enforce an invariant, use database constraints and appropriate transaction semantics rather than relying on a read-only derived value.

## Security Considerations

Subqueries do not change the requirement for parameterized SQL.

Use:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = :status
    ) AS order_count
FROM customers AS c
WHERE c.tenant_id = :tenant_id;
```

and bind `:status` and `:tenant_id` through the database driver or framework.

In multi-tenant systems, tenant boundaries should be enforced consistently across related data.

Application authorization should also remain separate from query composition. Returning a derived field does not automatically make the underlying data access authorized.

## When to Prefer Another Technique

A `SELECT`-list subquery is not the default solution for every derived value.

| Situation | Consider |
|---|---|
| One aggregate per parent | Scalar subquery or grouped JOIN |
| Existence only | `EXISTS` |
| Multiple columns from latest related row | `LATERAL` |
| Ranking within a group | Window function |
| Multiple metrics over same relation | Conditional aggregation |
| Returning related rows | JOIN |
| Extremely expensive repeated metrics | Pre-aggregation/materialized data |
| Guaranteed one related row | Scalar subquery can be appropriate |

The best query is the one whose semantics are clear and whose physical plan matches the workload.

## Interview Traps

### Can a subquery in `SELECT` return multiple rows?

Not when it is being used as a scalar expression. It must return at most one row for each outer row.

### What happens when it returns no rows?

The scalar expression generally evaluates to `NULL`.

### Does a correlated subquery execute once per outer row?

That is the logical dependency, but the physical execution is determined by the optimizer. Never infer actual runtime behavior solely from the SQL text.

### Is a scalar subquery always slower than a JOIN?

No. An indexed correlated lookup can be efficient, especially for a small outer result set. The optimizer and workload determine the actual cost.

### Why add `id DESC` after `created_at DESC`?

To provide deterministic tie-breaking when multiple rows have identical timestamps.

### When should `EXISTS` replace a count?

When the application only needs to know whether at least one qualifying row exists. Counting all matching rows performs work that the requirement does not need.

## Key Takeaways

- **A `SELECT`-list subquery produces a derived scalar value for each outer row and must satisfy scalar cardinality requirements.**
- **Correlation makes the derived value depend on the current outer row; efficient indexes on the correlation and ordering columns are often critical.**
- **Use `EXISTS`, window functions, grouped aggregation, or `LATERAL` when they better match the required semantics or avoid repeated work.**
- **Do not assume correlated subqueries are inherently slow or JOINs are inherently faster; validate important queries with `EXPLAIN (ANALYZE, BUFFERS)`.**
- **Enforce one-row assumptions with database constraints whenever a scalar subquery depends on data uniqueness.**