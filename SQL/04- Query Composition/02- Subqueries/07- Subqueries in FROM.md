# 07- Subqueries in FROM

## Overview

A subquery in the `FROM` clause is a query whose result is treated as a temporary relation that the outer query can read from. It is commonly called a **derived table**.

This pattern is useful when a query needs to:

- Aggregate or transform data before joining or filtering it.
- Break a complex query into logical relational stages.
- Join against an intermediate result set.
- Filter or rank rows before applying another operation.
- Isolate a reusable query boundary within a single SQL statement.

For example, calculate customer revenue first and then filter the aggregated result:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS customer_revenue
WHERE total_revenue >= 10000;
```

The inner query produces a relation containing one row per customer. The outer query treats that relation as if it were a table.

The key engineering benefit is **relational composition**: perform one transformation, then use its result as the input to the next transformation.

## Basic Syntax

The general structure is:

```sql
SELECT
    ...
FROM (
    SELECT
        ...
    FROM ...
    WHERE ...
) AS derived_table
WHERE ...;
```

Most SQL databases require a derived table to have an alias:

```sql
FROM (
    SELECT ...
) AS derived_table
```

The alias gives the outer query a name through which it can reference the derived columns.

For example:

```sql
SELECT
    r.customer_id,
    r.total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS r;
```

## Why Subqueries in `FROM` Exist

SQL is fundamentally compositional. A query can produce a relation, and another query can operate on that relation.

A derived table provides an explicit boundary between these operations.

Consider a requirement:

> Find customers whose paid revenue exceeds the average customer's paid revenue.

The calculation naturally has multiple stages:

```text
orders
   │
   ▼
paid orders
   │
   ▼
revenue per customer
   │
   ▼
average customer revenue
   │
   ▼
customers above average
```

A `FROM` subquery allows the intermediate result to be represented directly:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS customer_revenue
WHERE total_revenue > (
    SELECT AVG(total_revenue)
    FROM (
        SELECT
            customer_id,
            SUM(total_amount) AS total_revenue
        FROM orders
        WHERE status = 'paid'
        GROUP BY customer_id
    ) AS revenue
);
```

Although valid, repeating the same derived table is not ideal. A CTE is often clearer when the intermediate relation needs to be referenced more than once.

## Derived Tables as Intermediate Relations

Suppose:

```text
orders
--------------------------------
customer_id | total_amount
--------------------------------
101         | 100
101         | 250
102         | 500
102         | 300
```

The derived table:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS total_revenue
FROM orders
GROUP BY customer_id;
```

produces:

```text
customer_id | total_revenue
---------------------------
101         | 350
102         | 800
```

The outer query can then operate on that relation:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS customer_revenue
WHERE total_revenue >= 500;
```

The important point is that the outer query does not need to reason about individual orders anymore. Its input relation already represents customer-level revenue.

## Aggregation Before JOIN

One of the most useful production patterns is to aggregate a large child table before joining it to another relation.

Suppose:

```text
customers
orders
```

You need customer information plus order revenue:

```sql
SELECT
    c.id,
    c.email,
    r.total_revenue
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id;
```

The derived table reduces `orders` to one row per customer before the JOIN.

This can be preferable to joining all matching orders and aggregating afterward when the intermediate cardinality would otherwise become unnecessarily large.

However, the optimizer may transform equivalent queries, so the correct decision should be based on the execution plan rather than syntax alone.

## Preventing Join Multiplication

Consider:

```text
customers
orders
payments
```

A customer can have many orders and many payments.

A naive query:

```sql
SELECT
    c.id,
    SUM(o.total_amount) AS order_revenue,
    SUM(p.amount) AS payment_total
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN payments AS p
    ON p.customer_id = c.id
GROUP BY c.id;
```

can produce incorrect totals because orders and payments multiply each other.

If a customer has:

- 5 orders
- 4 payments

the JOIN can produce up to:

```text
5 × 4 = 20 intermediate rows
```

Each order and payment may therefore be counted multiple times.

Pre-aggregate each child relation:

```sql
SELECT
    c.id,
    o.order_revenue,
    p.payment_total
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS order_revenue
    FROM orders
    GROUP BY customer_id
) AS o
    ON o.customer_id = c.id
LEFT JOIN (
    SELECT
        customer_id,
        SUM(amount) AS payment_total
    FROM payments
    GROUP BY customer_id
) AS p
    ON p.customer_id = c.id;
```

Now each derived relation has at most one row per customer, avoiding the many-to-many multiplication.

This is a high-value production pattern:

> **Reduce each one-to-many relation to the required grain before joining multiple child relations.**

## Grain Matters

A derived table has a **grain**: what one row represents.

For example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;
```

has:

```text
one row = one customer
```

Whereas:

```sql
SELECT
    customer_id,
    order_id,
    total_amount
FROM orders;
```

has:

```text
one row = one order
```

Before joining derived data, explicitly reason about its grain.

| Relation | Grain |
|---|---|
| `customers` | One row per customer |
| `orders` | One row per order |
| Revenue derived table | One row per customer |
| Monthly revenue | One row per customer per month |
| Daily order statistics | One row per day |

Many SQL bugs are actually **grain mismatches**.

## Filtering After Aggregation

A `FROM` subquery is useful when the outer query needs to filter an aggregate result.

For example:

```sql
SELECT
    customer_id,
    order_count
FROM (
    SELECT
        customer_id,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
) AS customer_orders
WHERE order_count >= 10;
```

This separates:

1. Grouping orders.
2. Filtering customer-level results.

The equivalent `HAVING` query is often simpler:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

Prefer `HAVING` when the only reason for the derived table is to filter an aggregate.

Use a derived table when the intermediate result has additional value or must participate in further relational operations.

## Filtering Before Aggregation

Filtering can often be pushed into the inner query:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS revenue
WHERE total_revenue >= 10000;
```

This is different from:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS revenue
WHERE total_revenue >= 10000;
```

The first query excludes non-paid orders before aggregation.

The second includes all orders in the revenue calculation and only filters customers afterward.

Predicate placement therefore changes semantics as well as performance.

## Derived Table vs CTE

A Common Table Expression provides another way to define an intermediate relation.

Derived table:

```sql
SELECT
    r.customer_id,
    r.total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS r
WHERE r.total_revenue >= 10000;
```

CTE:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_revenue
FROM customer_revenue
WHERE total_revenue >= 10000;
```

For a single intermediate relation, either can be appropriate.

| Concern | Derived table | CTE |
|---|---|---|
| Local intermediate operation | Excellent | Good |
| Readability for complex queries | Good | Often better |
| Reuse within statement | Awkward | Better |
| Recursive queries | No | Yes |
| Naming intermediate stages | Inline alias | Explicit name |
| Nesting deeply | Can become difficult | Usually easier to structure |

Do not assume a CTE is automatically materialized or that a derived table is automatically inlined. Modern optimizers can transform both, depending on the database and query.

## Derived Table vs Window Function

A common reason to use a `FROM` subquery is to calculate a value and then filter on it.

For example:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS r
WHERE total_revenue > 10000;
```

Window functions can solve different but related problems.

For example, rank customers by revenue:

```sql
SELECT
    customer_id,
    total_revenue,
    RANK() OVER (
        ORDER BY total_revenue DESC
    ) AS revenue_rank
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS r;
```

The derived table establishes the customer-level grain. The window function then operates over that result.

This is a common multi-stage SQL pattern.

## Derived Table with Window Functions

A particularly useful technique is:

```sql
SELECT
    customer_id,
    month,
    monthly_revenue,
    SUM(monthly_revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
    ) AS cumulative_revenue
FROM (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(total_amount) AS monthly_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
) AS monthly;
```

The inner query establishes:

```text
one row = one customer per month
```

The outer query can then calculate cumulative revenue across those monthly rows.

This is one of the strongest reasons to use derived tables: **change the grain of the data before applying another relational operation.**

## Joining Multiple Derived Tables

Derived tables can represent independent metrics.

```sql
SELECT
    c.id,
    c.email,
    COALESCE(o.order_count, 0) AS order_count,
    COALESCE(p.payment_total, 0) AS payment_total
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
        SUM(amount) AS payment_total
    FROM payments
    WHERE status = 'completed'
    GROUP BY customer_id
) AS p
    ON p.customer_id = c.id;
```

Each metric is calculated independently at customer grain.

This makes the query easier to reason about than joining raw `orders` and `payments` simultaneously.

## `NULL` Handling

A `LEFT JOIN` to a derived table produces `NULL` when there is no matching row.

For example:

```sql
SELECT
    c.id,
    r.total_revenue
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id;
```

A customer with no orders receives:

```text
total_revenue = NULL
```

If the application wants zero instead:

```sql
SELECT
    c.id,
    COALESCE(r.total_revenue, 0) AS total_revenue
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id;
```

Keep the distinction clear:

- `NULL` means no matching derived row/value.
- `0` means a known numeric result of zero.

## PostgreSQL Example: Top Customers

A production reporting endpoint may need the top customers by paid revenue:

```sql
SELECT
    c.id,
    c.email,
    r.total_revenue
FROM customers AS c
JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id
ORDER BY r.total_revenue DESC
LIMIT 100;
```

For a frequently executed dashboard, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    c.email,
    r.total_revenue
FROM customers AS c
JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id
ORDER BY r.total_revenue DESC
LIMIT 100;
```

Pay particular attention to:

- How many rows are scanned from `orders`.
- Whether the status filter is selective.
- Aggregation cost.
- Sort cost.
- Memory usage.
- Temporary disk spills.
- Join strategy.
- Buffer reads.

## Performance Considerations

A derived table does not inherently imply a temporary physical table.

The database optimizer may:

- Inline the subquery.
- Push predicates into it.
- Reorder joins.
- Eliminate unnecessary operations.
- Materialize an intermediate result when beneficial or required.

Therefore:

> SQL syntax describes the relational operation; the execution plan describes how the database actually performs it.

For production workloads, use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

in PostgreSQL and inspect the actual plan.

### Reduce Intermediate Cardinality

A useful optimization principle is:

> Reduce data as early as correctness allows.

For example:

```sql
SELECT
    c.id,
    r.total_revenue
FROM customers AS c
JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id;
```

The inner query filters and aggregates orders before the JOIN.

This can reduce:

- Rows flowing into subsequent operators.
- Join work.
- Memory requirements.
- Sort or hash-table size.
- Network transfer if the query is part of a distributed database architecture.

But do not mechanically push every predicate into every subquery. Predicate movement must preserve semantics.

## Materialization Is Not Guaranteed

A common misconception is:

> "A subquery in `FROM` creates a temporary table."

Not necessarily.

A derived table is a logical relation. The optimizer decides how to execute it.

The database might effectively inline it into the larger query or choose an execution strategy involving materialization.

If you need explicit materialization semantics in PostgreSQL for a CTE, PostgreSQL supports:

```sql
WITH customer_revenue AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_revenue;
```

Use explicit materialization only when there is a demonstrated reason. It can prevent useful optimizer transformations and increase memory or I/O costs.

## Pagination and Derived Tables

Derived tables can also be useful when pagination operates on an aggregated result.

For example:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS r
ORDER BY total_revenue DESC, customer_id
LIMIT 50;
```

For stable pagination, include a deterministic tie-breaker:

```sql
ORDER BY total_revenue DESC, customer_id
```

For large result sets, keyset pagination may be preferable to large offsets, but the pagination strategy must account for the derived ordering keys.

## Backend API Example

Suppose a FastAPI endpoint needs customer revenue rankings.

The database can perform the relational work:

```python
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter()

QUERY = text("""
    SELECT
        c.id,
        c.email,
        r.total_revenue
    FROM customers AS c
    JOIN (
        SELECT
            customer_id,
            SUM(total_amount) AS total_revenue
        FROM orders
        WHERE status = :status
        GROUP BY customer_id
    ) AS r
        ON r.customer_id = c.id
    ORDER BY r.total_revenue DESC, c.id
    LIMIT :limit
""")
```

The application should not fetch all orders into Python and calculate the aggregates itself.

Database-side aggregation:

- Reduces application memory usage.
- Avoids unnecessary network transfer.
- Uses database indexes and execution strategies.
- Keeps relational computation close to the data.

The API layer should still validate parameters and enforce authorization boundaries.

## Django ORM

Django can represent many derived-table patterns through annotations, aggregations, subqueries, and other ORM expressions.

However, complex relational transformations can become difficult to express clearly through an ORM.

For example, a straightforward aggregation:

```python
from django.db.models import Sum

customer_revenue = (
    Order.objects
    .filter(status="paid")
    .values("customer_id")
    .annotate(total_revenue=Sum("total_amount"))
)
```

For more complex queries, inspect the generated SQL:

```python
print(customer_revenue.query)
```

Then validate the database execution plan.

When the ORM expression becomes significantly harder to reason about than the SQL equivalent, a carefully parameterized raw query can be appropriate.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Forgetting the derived-table alias | SQL requires a relation name in many dialects | Always alias the subquery |
| Joining raw one-to-many tables together | Cardinality multiplication is overlooked | Pre-aggregate each child relation |
| Ignoring the grain | Developers reason about columns rather than rows | Define what one row represents |
| Assuming a derived table is physically materialized | Confusing logical and physical execution | Inspect the execution plan |
| Using a subquery when `HAVING` is simpler | Intermediate relation is unnecessary | Use `HAVING` for straightforward aggregate filtering |
| Repeating a complex derived table | Intermediate logic is duplicated | Consider a CTE |
| Applying filters at the wrong stage | SQL stages have different semantics | Decide whether filtering belongs before or after aggregation |
| Selecting unnecessary columns | Wider intermediate rows increase memory and I/O | Project only required columns |
| Assuming CTEs are always slower | Treating optimizer behavior as fixed | Benchmark the actual query |
| Ignoring duplicate keys before JOIN | Derived table may contain multiple rows per join key | Validate and control the derived relation's grain |

## Production Pitfalls

### Large Intermediate Results

A derived table can make SQL look modular while still producing millions of intermediate rows.

Always ask:

```text
How many rows enter the subquery?
How many rows leave it?
What is the resulting grain?
How many rows reach the JOIN?
```

A clean query is not necessarily an efficient query.

### Aggregation Before Filtering

This:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;
```

followed by:

```sql
WHERE revenue > 10000
```

requires the database to calculate all customer aggregates before filtering.

That may be correct, but if an earlier predicate can safely reduce the input rows, apply it before aggregation.

### Accidental Duplicate Rows

Suppose the derived table contains:

```text
customer_id | revenue
------------|--------
101         | 100
101         | 200
```

and it is joined to:

```sql
ON r.customer_id = c.id
```

the customer can appear twice.

The outer query cannot assume uniqueness merely because the relation has a convenient alias.

## Security Considerations

Derived tables do not change SQL injection requirements.

Use parameterized queries:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE status = :status
    GROUP BY customer_id
) AS r
WHERE total_revenue >= :minimum_revenue;
```

Do not construct predicates through string interpolation.

In multi-tenant systems, tenant filtering must be applied at the correct relational stage:

```sql
SELECT
    customer_id,
    total_revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS total_revenue
    FROM orders
    WHERE tenant_id = :tenant_id
      AND status = :status
    GROUP BY customer_id
) AS r;
```

Failing to constrain the derived relation can cause both **data leakage** and unnecessary computation.

## Operational Considerations

For important production queries:

- Capture execution plans for representative datasets.
- Monitor query latency and database CPU.
- Monitor buffer reads and temporary-file usage.
- Watch for changes in cardinality as data grows.
- Verify indexes on filtering and join columns.
- Test with realistic tenant and customer distributions.
- Avoid assuming development-sized data represents production behavior.
- Track slow-query logs and query fingerprints.
- Re-evaluate queries after significant schema or data-distribution changes.

A query that performs well with 100,000 orders may behave very differently with 500 million orders.

## When to Use a `FROM` Subquery

Use a derived table when it makes the relational transformation clearer or materially useful.

Good candidates include:

- Aggregating before a JOIN.
- Changing the grain of a relation.
- Preventing join multiplication.
- Filtering an intermediate result.
- Applying a window function to an aggregated result.
- Building a logical intermediate relation for a larger query.

Prefer simpler constructs when they express the requirement directly.

| Requirement | Preferred starting point |
|---|---|
| Filter aggregate results | `HAVING` |
| Reusable intermediate query | CTE |
| One scalar related value | Scalar subquery |
| Existence test | `EXISTS` |
| Ranking or running totals | Window function |
| Aggregate before JOIN | Derived table or CTE |
| Multiple independent child aggregates | Separate derived tables or CTEs |
| Frequently reused expensive result | Materialized view or summary structure, when justified |

## Interview Traps

### Is a `FROM` subquery a temporary table?

Not necessarily. It is a logical derived relation. The optimizer determines the physical execution strategy.

### Why alias a subquery?

The outer query needs a relation name to reference the derived table, and many SQL dialects require the alias syntactically.

### Why aggregate before joining multiple child tables?

To control cardinality and prevent independent one-to-many relationships from multiplying each other's rows.

### Are derived tables always faster?

No. They are a query-composition technique, not an optimization guarantee.

### When should you use a CTE instead?

Use a CTE when naming, readability, reuse, or recursive query structure makes it a better representation of the problem.

### What is the most important concept when using derived tables?

**Grain.** Know exactly what one row in the derived relation represents before joining it to another relation.

## Key Takeaways

- **A subquery in `FROM` creates a logical derived relation that the outer query can filter, join, aggregate, or apply window functions to.**
- **Always reason about the derived table's grain; controlling cardinality before JOINs prevents many production data-correctness bugs.**
- **Pre-aggregating independent one-to-many relations is a powerful technique for avoiding join multiplication and incorrect aggregates.**
- **Derived tables are logical query constructs, not guaranteed physical temporary tables; use execution plans to understand actual performance.**
- **Use derived tables when they improve relational composition, but prefer `HAVING`, CTEs, window functions, or other constructs when they express the requirement more directly.**