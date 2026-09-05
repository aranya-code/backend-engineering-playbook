# 14- Unnecessary Correlated Subqueries

## Overview

A correlated subquery is a subquery that references columns from the outer query. The inner query is therefore logically evaluated in the context of each outer row.

Correlated subqueries are valid SQL and can be the clearest solution for existence checks, per-row comparisons, and certain complex predicates. The anti-pattern is using correlation when the same result can be expressed more clearly or efficiently with a `JOIN`, `EXISTS`, aggregation, or window function.

For example:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE (
    SELECT COUNT(*)
    FROM orders AS o
    WHERE o.customer_id = c.id
) > 5;
```

The subquery references:

```sql
c.id
```

from the outer query, making it correlated.

A better formulation for this requirement may be:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.email
HAVING COUNT(*) > 5;
```

Or, when the requirement is existence rather than counting:

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

The important engineering principle is:

> **Correlation is a tool, not a default query pattern. Use it when its semantics are useful; remove unnecessary correlation when a set-based formulation better represents the workload.**

---

## What Is a Correlated Subquery?

A correlated subquery references a value from the outer query.

Example:

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

The inner query references:

```sql
c.id
```

from the outer query.

Conceptually:

```text
Outer customer row
       ↓
customer.id
       ↓
Correlated subquery
       ↓
search orders for that customer
```

This differs from an uncorrelated subquery:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT customer_id
    FROM orders
);
```

The inner query does not reference the outer `c` row.

---

## Why Correlated Subqueries Exist

Correlation is useful when the inner operation genuinely depends on the current outer row.

Common legitimate uses include:

- Existence checks.
- Anti-existence checks.
- Per-row comparisons.
- Finding related records under complex conditions.
- Expressing relational predicates naturally.
- Certain scalar calculations.

For example:

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

This directly expresses:

> Return customers for whom a matching completed order exists.

That is a good use of correlation because the inner query represents an existence predicate.

---

## Correlation Does Not Automatically Mean N Queries

A common misconception is:

```text
correlated subquery
=
one SQL query per outer row
```

That is not necessarily true.

PostgreSQL's optimizer can transform and optimize correlated constructs.

For example:

```sql
WHERE EXISTS (...)
```

may be planned as a semi-join.

Possible execution strategies include:

```text
Nested Loop Semi Join
Hash Semi Join
Merge Semi Join
```

depending on the query and available statistics.

Therefore, do not diagnose performance from SQL syntax alone.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

to inspect the actual execution plan.

---

## The Anti-Pattern

The anti-pattern occurs when correlation is used unnecessarily.

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

This is valid SQL.

But if the workload needs counts for a large number of customers, an aggregation may represent the operation more naturally:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

The correct choice still depends on:

- Number of customers.
- Number of orders.
- Selectivity.
- Indexes.
- Required rows.
- PostgreSQL's chosen plan.

---

## Why Unnecessary Correlation Can Be Expensive

A correlated expression creates a dependency:

```text
outer row
   ↓
inner operation
   ↓
outer row
   ↓
inner operation
   ↓
...
```

Even when the optimizer can execute it efficiently, a poorly structured correlated query can lead to repeated work.

Potential consequences include:

- Higher CPU usage.
- More buffer access.
- More expensive nested-loop execution.
- Increased query latency.
- Poor scalability with outer-row count.
- Increased database load under concurrency.

The risk is greatest when the correlated subquery performs expensive work for many outer rows.

---

## Scalar Correlated Subqueries

A scalar subquery returns a single value for each outer row.

Example:

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

The result is:

```text
customer
    ↓
last_order_at
```

for each customer.

This can be appropriate, but it should be evaluated against alternatives such as:

```sql
LEFT JOIN
+
GROUP BY
```

or:

```sql
window functions
```

depending on the required result.

---

## Correlated Subquery for Latest Related Row

A common pattern is:

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

This can be a legitimate and efficient query when the appropriate index exists:

```sql
CREATE INDEX orders_customer_created_id_idx
ON orders (
    customer_id,
    created_at DESC,
    id DESC
);
```

The database can potentially locate the latest order for each customer efficiently.

This is an example where correlation is not necessarily an anti-pattern.

---

## Correlation vs Window Functions

The same "latest row per group" requirement can sometimes be expressed with a window function:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
) AS ranked
WHERE rn = 1;
```

The two approaches have different execution characteristics.

| Requirement | Correlated approach | Window approach |
|---|---|---|
| Latest row for known parent set | Often useful | Useful |
| Rank every row | Poor fit | Excellent |
| Top N per group | Possible | Excellent |
| Small selective outer set | Often attractive | May process more rows |
| Need one scalar value | Natural | Sometimes verbose |

Do not replace every correlated query with a window function mechanically.

---

## Correlation vs JOIN

Consider:

```sql
SELECT
    c.id,
    (
        SELECT MAX(o.total_amount)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS max_order_value
FROM customers AS c;
```

An alternative is:

```sql
SELECT
    c.id,
    MAX(o.total_amount) AS max_order_value
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

The JOIN formulation exposes the relationship directly.

However, it can also generate a large intermediate row set when the relationship is highly one-to-many.

The better query depends on:

```text
outer rows
+
related rows
+
selectivity
+
required output
```

---

## Correlation vs EXISTS

For existence, prefer `EXISTS` over a correlated `COUNT()` or scalar lookup.

Avoid:

```sql
SELECT
    c.id
FROM customers AS c
WHERE (
    SELECT COUNT(*)
    FROM orders AS o
    WHERE o.customer_id = c.id
) > 0;
```

Prefer:

```sql
SELECT
    c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The semantics are clearer.

The database only needs to establish that at least one matching row exists rather than calculate an exact count.

An appropriate index such as:

```sql
CREATE INDEX orders_customer_id_idx
ON orders (customer_id);
```

can support the lookup.

---

## Correlation vs IN

Consider:

```sql
SELECT
    c.id
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

This expresses set membership.

The equivalent existence formulation is:

```sql
SELECT
    c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

Both can produce efficient plans.

Do not assume that `IN` is always faster or that `EXISTS` is always faster.

PostgreSQL can transform logically equivalent queries into similar physical plans.

Choose based on semantics first and validate performance with the execution plan.

---

## NOT EXISTS Is Often the Better Exclusion Pattern

Suppose the requirement is:

> Find customers who have never placed an order.

Use:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This is usually clearer than:

```sql
WHERE c.id NOT IN (
    SELECT customer_id
    FROM orders
);
```

because `NOT IN` has problematic three-valued logic when the subquery can contain `NULL`.

The correlation in `NOT EXISTS` is intentional and directly represents the relational condition.

---

## Unnecessary Correlated Aggregation

Consider:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'completed'
    ) AS completed_orders
FROM customers AS c;
```

If every customer's count is required, an aggregate can often express the set operation:

```sql
SELECT
    c.id,
    COUNT(o.id) FILTER (
        WHERE o.status = 'completed'
    ) AS completed_orders
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This makes the complete aggregation visible to the optimizer.

However, if only a small subset of customers is being returned and the correlated subquery can use a highly selective index efficiently, the original formulation may still be competitive.

Measure rather than applying a rule mechanically.

---

## Conditional Aggregation

Instead of multiple correlated subqueries:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'completed'
    ) AS completed_count,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'cancelled'
    ) AS cancelled_count
FROM customers AS c;
```

consider one set-based aggregation:

```sql
SELECT
    c.id,
    COUNT(o.id) FILTER (
        WHERE o.status = 'completed'
    ) AS completed_count,
    COUNT(o.id) FILTER (
        WHERE o.status = 'cancelled'
    ) AS cancelled_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This can avoid scanning the same relationship repeatedly.

---

## Multiple Correlated Subqueries

A particularly problematic pattern is:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count,
    (
        SELECT SUM(o.total_amount)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS revenue,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS last_order_at
FROM customers AS c;
```

The same `orders` relationship is being queried repeatedly.

A grouped query can often compute all metrics together:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count,
    COALESCE(SUM(o.total_amount), 0) AS revenue,
    MAX(o.created_at) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This is usually easier to maintain and gives the optimizer one relational operation to consider.

---

## Correlation With `LIMIT`

A correlated subquery with `LIMIT` can be a strong pattern.

For example:

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

With:

```sql
CREATE INDEX orders_customer_created_id_idx
ON orders (
    customer_id,
    created_at DESC,
    id DESC
);
```

the database may be able to perform a small ordered lookup for each relevant customer.

This can be preferable to scanning and ranking every order when:

```text
outer customer set = small
+
index lookup = cheap
```

This is a key senior-level distinction:

> **A correlated query can be intentionally efficient when the outer relation is selective and the inner operation has a highly effective access path.**

---

## Correlation and Outer-Row Cardinality

Consider:

```text
10 customers
```

versus:

```text
10 million customers
```

The same correlated query may behave very differently.

A useful mental model is:

```text
Cost ≈ outer rows × cost of correlated operation
```

This is conceptual rather than a literal optimizer cost formula.

The optimizer may transform the query or choose a different execution strategy.

Still, outer cardinality is an important factor when reasoning about correlated work.

---

## Indexing Correlated Subqueries

If correlation is intentional, the inner lookup should usually have an appropriate access path.

For:

```sql
WHERE o.customer_id = c.id
```

consider:

```sql
CREATE INDEX orders_customer_id_idx
ON orders (customer_id);
```

For:

```sql
WHERE o.customer_id = c.id
ORDER BY o.created_at DESC
LIMIT 1
```

consider:

```sql
CREATE INDEX orders_customer_created_id_idx
ON orders (
    customer_id,
    created_at DESC,
    id DESC
);
```

The index should match the complete inner operation, not just one predicate.

---

## Correlation and Composite Indexes

Suppose:

```sql
SELECT
    c.id,
    (
        SELECT o.id
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.status = 'completed'
        ORDER BY o.created_at DESC, o.id DESC
        LIMIT 1
    ) AS latest_completed_order
FROM customers AS c;
```

A candidate index may be:

```sql
CREATE INDEX orders_customer_status_created_idx
ON orders (
    customer_id,
    status,
    created_at DESC,
    id DESC
);
```

This aligns:

```text
customer_id equality
status equality
created_at ordering
id tie-breaker
```

The final choice should be based on the complete workload.

---

## Correlated UPDATE

Correlation is not limited to SELECT queries.

For example:

```sql
UPDATE customers AS c
SET last_order_at = (
    SELECT MAX(o.created_at)
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This may be valid for a controlled migration or maintenance operation.

But for a large table, consider whether the operation should instead be expressed as a set-based update using pre-aggregated results.

For example:

```sql
UPDATE customers AS c
SET last_order_at = x.last_order_at
FROM (
    SELECT
        customer_id,
        MAX(created_at) AS last_order_at
    FROM orders
    GROUP BY customer_id
) AS x
WHERE x.customer_id = c.id;
```

For production migrations, batch size, locking, WAL, and transaction duration must also be considered.

---

## Correlated DELETE

Consider:

```sql
DELETE FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This is a valid and often clear use of correlation.

It expresses:

```text
delete customers
for which no related order exists
```

A corresponding foreign-key design, business rule, and transaction strategy must be considered before running destructive operations.

Correlation itself is not the problem.

Unnecessary correlation is.

---

## Correlated Subqueries and ORM Code

ORMs can generate correlated SQL without the developer explicitly writing SQL.

Django provides `OuterRef` and `Subquery`.

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
        latest_order.values("id")[:1]
    )
)
```

This can generate a correlated subquery.

It is not inherently wrong.

The important questions are:

- Why is the correlation required?
- How many outer rows are involved?
- Is the inner lookup indexed?
- Would a join or aggregation be clearer?
- What does `EXPLAIN` show?

---

## Django: `Exists`

For existence checks, Django provides `Exists`:

```python
from django.db.models import Exists, OuterRef

completed_orders = Order.objects.filter(
    customer_id=OuterRef("pk"),
    status="completed",
)

customers = (
    Customer.objects
    .annotate(
        has_completed_order=Exists(completed_orders)
    )
    .filter(has_completed_order=True)
)
```

This communicates existence semantics directly.

It is generally preferable to constructing a correlated count when only a Boolean answer is required.

---

## SQLAlchemy Correlation

SQLAlchemy can express correlated subqueries explicitly.

For example:

```python
from sqlalchemy import select, func

latest_order = (
    select(func.max(Order.created_at))
    .where(Order.customer_id == Customer.id)
    .scalar_subquery()
)

stmt = select(
    Customer.id,
    latest_order.label("last_order_at"),
)
```

The generated SQL is correlated through the reference to `Customer.id`.

As with Django, ORM abstraction does not eliminate database-level performance analysis.

Inspect the generated SQL and execution plan.

---

## Correlation in REST APIs

Consider:

```text
GET /customers
```

returning:

```json
{
  "id": 123,
  "last_order_at": "...",
  "order_count": 17
}
```

A naive implementation might perform:

```text
customer query
+
count subquery
+
last-order subquery
```

for every customer.

A production design should first determine:

```text
How many customers?
How many orders?
Which metrics?
Which indexes?
What latency target?
```

Then choose:

- Aggregation.
- Join.
- Correlated scalar subquery.
- Window function.
- Precomputed read model.

---

## Microservices Consideration

A similar pattern can occur across services:

```text
GET /customers
    ↓
for every customer
    ↓
GET /orders/customer/{id}
```

This is effectively a distributed form of repeated correlated work.

Instead prefer:

```text
batch request
```

or:

```text
service-owned read model
```

when appropriate.

Do not move an inefficient relational access pattern into HTTP or gRPC and assume the problem disappears.

---

## Security Considerations

Correlation does not automatically introduce a security problem.

The important concern is whether the correlated predicate preserves authorization boundaries.

For multi-tenant data:

```sql
SELECT
    c.id,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
          AND o.tenant_id = c.tenant_id
    ) AS order_count
FROM customers AS c
WHERE c.tenant_id = $1;
```

Tenant boundaries should be explicit where the schema and authorization model require them.

Use parameterized values:

```sql
WHERE tenant_id = $1
```

Do not construct correlated SQL using string concatenation.

---

## RLS and Correlated Queries

PostgreSQL Row-Level Security can further constrain which rows are visible.

A query's logical structure may appear correct while RLS changes the effective visible dataset.

When investigating unexpected performance or results, consider:

- RLS policies.
- Role identity.
- Policy predicates.
- Indexes supporting policy conditions.
- Whether the role bypasses RLS.

Do not disable security controls merely to make a query faster.

---

## Execution Plan Investigation

When evaluating a correlated subquery:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    )
FROM customers AS c;
```

Inspect:

- Outer row count.
- Inner scan type.
- Number of loops.
- Actual rows.
- Buffer reads.
- Buffer hits.
- Total execution time.

A plan showing:

```text
Index Scan
loops=100
```

may be perfectly reasonable.

A plan showing:

```text
Seq Scan
loops=100000
```

is a strong reason to investigate.

The `loops` value is particularly useful when reasoning about repeated inner execution.

---

## The Importance of `loops`

Consider:

```text
Index Scan on orders
  loops=1000
```

The inner operation was executed many times.

That is not automatically bad.

If each execution performs a highly selective indexed lookup:

```text
1,000 loops
×
very small lookup
```

may be acceptable.

But:

```text
100,000 loops
×
large sequential scan
```

can be catastrophic.

Always evaluate:

```text
loops × work per loop
```

rather than looking at `loops` in isolation.

---

## Common Mistakes

### Mistake: Treating Every Correlated Subquery as Bad

Correlation is a valid SQL technique.

`EXISTS` and selective "latest row" lookups are common legitimate uses.

### Mistake: Assuming Correlation Means N SQL Statements

The database executes the statement as one SQL statement and the optimizer may transform correlated expressions into efficient join-like plans.

### Mistake: Replacing `EXISTS` With `COUNT(*)`

If you only need to know whether a row exists:

```sql
EXISTS
```

expresses the requirement better than:

```sql
COUNT(*) > 0
```

### Mistake: Ignoring Outer Cardinality

A correlated lookup that is excellent for 100 customers may be problematic for 10 million customers.

### Mistake: Ignoring Inner Indexes

If correlation is intentional, the inner predicate often needs an appropriate index.

### Mistake: Replacing Correlation With a Giant JOIN

A JOIN can multiply rows and create large intermediate results.

### Mistake: Optimizing SQL Syntax Without `EXPLAIN`

Equivalent SQL formulations can receive different or identical plans.

Measure before and after.

### Mistake: Forgetting NULL Semantics

Replacing `NOT EXISTS` with `NOT IN` can introduce incorrect results when NULLs are possible.

---

## Production Performance Checklist

When reviewing a correlated subquery:

- [ ] Identify why correlation is required.
- [ ] Determine the outer-row cardinality.
- [ ] Determine the inner-row cardinality.
- [ ] Check whether the operation is existence, aggregation, lookup, or ranking.
- [ ] Check existing indexes.
- [ ] Align indexes with correlated predicates.
- [ ] Inspect `EXPLAIN (ANALYZE, BUFFERS)`.
- [ ] Inspect inner-node `loops`.
- [ ] Compare actual vs estimated rows.
- [ ] Check buffer reads and hits.
- [ ] Compare JOIN, EXISTS, aggregation, and window alternatives where appropriate.
- [ ] Test with production-like data volume.
- [ ] Test high-concurrency behavior.
- [ ] Preserve tenant and authorization predicates.
- [ ] Check ORM-generated SQL.
- [ ] Measure before and after deployment.

---

## Decision Matrix

| Requirement | Preferred starting point |
|---|---|
| Does related row exist? | `EXISTS` |
| Does related row not exist? | `NOT EXISTS` |
| Aggregate all related rows | `JOIN` + `GROUP BY` |
| Multiple aggregates over same relation | Set-based aggregation |
| Latest related row for selective parents | Correlated subquery can be excellent |
| Top N per group | Window function |
| Membership in a set | `IN` / `EXISTS` |
| Complex per-row predicate | Correlated subquery may be appropriate |
| Large repeated outer workload | Investigate set-based alternatives |
| Cross-service repeated lookup | Batch API / read model |
| Large migration | Set-based/batched operation |

---

## Senior Decision Framework

Before rewriting a correlated subquery, ask:

### What is the semantic requirement?

Is it:

```text
existence?
absence?
scalar value?
aggregation?
latest row?
ranking?
```

### How many outer rows exist?

```text
10
1,000
1,000,000
```

The answer can materially change the best strategy.

### How expensive is the inner operation?

Determine whether it uses:

```text
Index Scan
Index Only Scan
Bitmap Scan
Seq Scan
```

and inspect its actual loops.

### Is the inner operation selective?

A highly selective lookup can make correlation efficient.

### Can the work be shared?

If several outer rows repeatedly scan the same relation, aggregation or another set-based approach may allow the database to perform shared work.

### Does the alternative change row cardinality?

A JOIN can eliminate correlation but introduce row multiplication.

### What does production require?

Consider:

- Latency.
- Throughput.
- Concurrency.
- Memory.
- CPU.
- I/O.
- Replica load.
- Operational cost.

---

## Practical Comparison

### Correlated Query

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

### Set-Based Aggregation

```sql
SELECT
    c.id,
    MAX(o.created_at) AS last_order_at
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

### Window-Based Approach

```sql
SELECT
    id,
    customer_id,
    created_at
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
) AS ranked
WHERE rn = 1;
```

These queries are not universally interchangeable.

They have different:

- Result grains.
- Intermediate row counts.
- Optimization opportunities.
- Memory requirements.
- Index requirements.

The correct approach is determined by the actual requirement and workload.

---

## Reliability and Scalability

Unnecessary correlated work can become especially expensive under concurrent API traffic.

Consider:

```text
500 requests/second
        ↓
10,000 outer rows/request
        ↓
correlated inner work
        ↓
database CPU/I/O saturation
```

The exact execution behavior depends on the query plan, but the multiplication effect is important.

At scale:

```text
query design
    ↓
database work
    ↓
connection occupancy
    ↓
API latency
    ↓
service capacity
```

Optimizing a query can therefore improve more than its individual latency.

---

## High Availability and Replicas

Under-indexed or inefficient correlated queries can consume resources on read replicas as well as the primary.

Consider:

```text
API
 ├── Primary
 └── Read Replica
        ↓
     expensive query
```

Read replicas provide additional read capacity but do not eliminate inefficient query execution.

When promoting a replica during failover, the promoted database must also have sufficient capacity for the production workload.

---

## Cost Considerations

An inefficient correlated query can increase:

- CPU consumption.
- I/O.
- Database instance requirements.
- Replica capacity.
- Connection utilization.
- Operational investigation time.

The best optimization is not necessarily the query with the fewest SQL keywords.

It is the query that produces the required result with an efficient and maintainable execution plan.

---

## Key Takeaways

- **Correlated subqueries are not inherently bad; they are often appropriate for `EXISTS`, `NOT EXISTS`, and selective per-parent lookups such as finding the latest related row.**
- **The anti-pattern is unnecessary correlation that repeatedly performs work that could be expressed more naturally through aggregation, JOINs, batching, or window functions.**
- **Never assume a correlated subquery means N separate database queries; PostgreSQL can transform correlated constructs into efficient plans, so validate behavior with `EXPLAIN (ANALYZE, BUFFERS)` and inspect inner-node `loops`.**
- **When correlation is intentional, outer cardinality, inner selectivity, and supporting indexes are critical; a highly selective indexed lookup can make a correlated query an excellent production solution.**
- **Choose between correlation and set-based alternatives based on semantics, cardinality, execution plan, concurrency, security boundaries, and production workload rather than applying a blanket rule to eliminate all correlated subqueries.**