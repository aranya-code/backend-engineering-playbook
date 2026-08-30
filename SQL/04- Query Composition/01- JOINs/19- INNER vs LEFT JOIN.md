# 19- INNER vs LEFT JOIN

## Overview

`INNER JOIN` and `LEFT JOIN` are the two most commonly used JOIN types in backend applications. The key difference is **which rows are guaranteed to survive the JOIN**.

- `INNER JOIN` returns only rows that have a match on both sides.
- `LEFT JOIN` returns every row from the left relation and matching rows from the right relation. If no match exists, right-side columns become `NULL`.

The choice is primarily a **data semantics decision**, not a performance preference. Using the wrong JOIN can silently remove records, introduce `NULL`s, change result cardinality, or produce incorrect API responses and reports.

For production systems, reason about:

- Which entity must be preserved.
- Whether the relationship is optional or mandatory.
- The expected result grain.
- How `NULL` should be handled.
- Whether filters belong in `ON` or `WHERE`.
- Whether the JOIN multiplies rows.
- What the execution plan does with the resulting query.

## Core Difference

Consider:

```text
customers
+----+----------+
| id | name     |
+----+----------+
| 1  | Alice    |
| 2  | Bob      |
| 3  | Charlie  |
+----+----------+

orders
+----+-------------+
| id | customer_id |
+----+-------------+
| 101| 1           |
| 102| 1           |
| 103| 2           |
+----+-------------+
```

Alice has two orders, Bob has one, and Charlie has none.

### INNER JOIN

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id;
```

Result:

```text
Alice    101
Alice    102
Bob      103
```

Charlie disappears because there is no matching order.

### LEFT JOIN

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

Result:

```text
Alice    101
Alice    102
Bob      103
Charlie  NULL
```

Charlie is preserved because `customers` is the left relation.

## Result Semantics

| JOIN | Left row with match | Left row without match | Right row without match |
|---|---|---|---|
| `INNER JOIN` | Preserved | Removed | Removed |
| `LEFT JOIN` | Preserved | Preserved with right-side `NULL`s | Removed |

A useful mental model is:

```text
INNER JOIN

Left ───── matching ───── Right
          ↓
       result only


LEFT JOIN

Left ───── matching ───── Right
  │
  └──── no match ──────── NULL
          ↓
       result
```

The word **LEFT** means that the left input is preserved, not that the database necessarily scans that table first.

## When to Use INNER JOIN

Use `INNER JOIN` when a result is meaningful only when the related record exists.

Typical examples include:

- Orders that belong to existing customers.
- Order items that belong to orders.
- Employees belonging to departments.
- Payments belonging to orders.
- Resources belonging to an authorized tenant.

Example:

```sql
SELECT
    o.id,
    o.created_at,
    c.email
FROM orders AS o
INNER JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.created_at >= :start_date;
```

The query expresses:

> Return orders for which a matching customer exists.

This is appropriate when the relationship is mandatory or when orphaned records should not appear in the result.

## When to Use LEFT JOIN

Use `LEFT JOIN` when the left-side entity must appear even if the related entity does not exist.

Typical examples include:

- All customers, including those without orders.
- All products, including products with zero sales.
- All users, including users without profiles.
- All accounts, including accounts without recent transactions.
- All tenants, including tenants without active resources.

Example:

```sql
SELECT
    c.id,
    c.email,
    o.id AS latest_order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

The semantics are:

> Customers are the required result set; orders are optional information.

## Relationship Optionality

The choice often follows the business relationship.

| Business requirement | Typical JOIN |
|---|---|
| Return only customers with orders | `INNER JOIN` |
| Return every customer and their orders if present | `LEFT JOIN` |
| Return only products with inventory records | `INNER JOIN` |
| Return every product, including out-of-stock products | `LEFT JOIN` |
| Return every user and optional profile | `LEFT JOIN` |
| Return only users with profiles | `INNER JOIN` |

The important question is:

> Which rows must survive when no related record exists?

That determines the JOIN semantics.

## INNER JOIN with Mandatory Relationships

Suppose:

```text
orders.customer_id → customers.id
```

is a required foreign key.

You might still use an `INNER JOIN`:

```sql
SELECT
    o.id,
    c.email
FROM orders AS o
INNER JOIN customers AS c
    ON c.id = o.customer_id;
```

The database knows the relationship is constrained, but the JOIN still communicates the query's intended result.

It says that an order should only appear together with its customer.

This can also allow the optimizer to reason about the relationship using constraints and statistics.

## LEFT JOIN with Optional Relationships

Suppose a customer may have no profile:

```text
customers
    │
    └── profiles
```

Use:

```sql
SELECT
    c.id,
    c.email,
    p.display_name
FROM customers AS c
LEFT JOIN profiles AS p
    ON p.customer_id = c.id;
```

For a customer without a profile:

```text
c.id             = 42
c.email          = alice@example.com
p.display_name   = NULL
```

The `NULL` does not mean the customer itself is missing. It means the optional right-side relationship has no matching row.

## Filtering INNER JOIN Results

With `INNER JOIN`, predicates on the joined table can commonly be expressed in either `ON` or `WHERE` without changing the intended result.

These are typically equivalent:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

and:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

The optimizer may produce the same execution plan.

For readability, a common convention is:

- `ON` for relationship conditions.
- `WHERE` for overall result filtering.

But semantics should take precedence over stylistic rules.

## Filtering LEFT JOIN Results

This is where a major difference appears.

Consider:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

A customer without an order receives:

```text
o.status = NULL
```

The predicate:

```sql
o.status = 'completed'
```

evaluates to `UNKNOWN`, not `TRUE`.

The row is therefore removed by `WHERE`.

The query effectively excludes customers without matching completed orders.

If the requirement is:

> Return all customers, but only join completed orders.

use:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

Now customers without completed orders remain.

## The Outer JOIN Trap

Compare these queries carefully.

### Query A

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

Meaning:

> Return customers that have a completed order.

### Query B

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

Meaning:

> Return every customer and attach completed orders when available.

The difference is business semantics, not merely SQL style.

## Finding Rows Without Matches

A common and useful pattern is an anti-join using `LEFT JOIN`.

For example:

> Find customers who have never placed an order.

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.id IS NULL;
```

The JOIN first preserves all customers. Customers with no matching order have `NULL` order columns. The `WHERE` clause selects those rows.

Conceptually:

```text
customers
    │
    ├── matching order → remove
    │
    └── no order → keep
```

For existence-only checks, `NOT EXISTS` is often clearer:

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

For complex production queries, compare execution plans rather than assuming one form is always faster.

## INNER JOIN vs LEFT JOIN with Aggregation

Consider a reporting requirement:

> Show every customer and their total completed order value.

A `LEFT JOIN` is appropriate because customers with no completed orders must remain.

```sql
SELECT
    c.id,
    c.email,
    COALESCE(SUM(o.amount), 0) AS total_amount
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed'
GROUP BY
    c.id,
    c.email;
```

The condition belongs in `ON` because it controls which orders participate without eliminating customers.

`COALESCE()` converts the absence of matching orders into a business-friendly zero.

If `WHERE` were used instead:

```sql
WHERE o.status = 'completed'
```

customers with no completed orders would disappear.

## JOIN Choice and Result Grain

JOIN type does not determine result grain by itself.

A `LEFT JOIN` from customers to orders still produces one row per matching order:

```text
customer 1
   ├── order 101
   └── order 102
```

Result:

```text
customer 1 → order 101
customer 1 → order 102
```

The query grain is therefore:

```text
one row per customer-order relationship
```

not:

```text
one row per customer
```

If an API requires one customer object with nested orders, the backend may need aggregation, JSON aggregation, an ORM prefetch, or separate queries.

## One-to-Many Relationships

With:

```text
customers 1 ─────── * orders
```

both JOIN types can produce multiple rows per customer.

### INNER JOIN

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id;
```

Only customers with orders appear.

### LEFT JOIN

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

Every customer appears, but customers with orders still produce multiple rows.

The important distinction is:

```text
INNER JOIN
    existence requirement

LEFT JOIN
    preservation requirement
```

Neither automatically removes one-to-many duplication.

## Multiple JOINs

Consider:

```sql
SELECT
    c.id,
    o.id AS order_id,
    oi.id AS item_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
LEFT JOIN order_items AS oi
    ON oi.order_id = o.id;
```

The result grain becomes:

```text
customer → order → order item
```

If an order contains five items, that order appears five times.

This is expected relational behavior.

Problems occur when the application assumes:

```text
one row = one customer
```

without accounting for the expanded relationship.

## INNER vs LEFT JOIN Performance

Neither JOIN type is inherently faster.

Performance depends on:

- Cardinality.
- Selectivity.
- Indexes.
- Statistics.
- Join predicates.
- Data distribution.
- Chosen join algorithm.
- Number of intermediate rows.
- Aggregation and sorting requirements.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

to evaluate actual behavior.

Do not change a `LEFT JOIN` to an `INNER JOIN` merely for performance unless the business semantics genuinely allow unmatched rows to be removed.

## Optimizer Behavior

For eligible inner joins, the optimizer can often reorder joins:

```text
Written:

A → B → C

Possible physical plan:

B → C → A
```

A `LEFT JOIN` introduces stronger semantic constraints because the left-side preservation requirement must be maintained.

This does not mean the database literally scans the left table first in every physical implementation. It means the optimizer must preserve the query's outer-join semantics.

This is one reason outer joins require more careful reasoning when optimizing complex queries.

## Predicate Pushdown

Consider:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

The order predicate is part of the JOIN condition.

The database may be able to apply:

```text
orders.status = 'completed'
```

while accessing the order relation, reducing the rows participating in the JOIN.

A suitable index may help, depending on workload:

```sql
CREATE INDEX idx_orders_customer_status
    ON orders(customer_id, status);
```

Index design should be validated with actual execution plans and production workload characteristics.

## LEFT JOIN and NULL Semantics

SQL uses three-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

Comparisons involving `NULL` normally produce `UNKNOWN`.

Therefore:

```sql
WHERE o.id = NULL
```

is incorrect.

Use:

```sql
WHERE o.id IS NULL
```

Similarly:

```sql
WHERE o.id <> NULL
```

does not identify non-NULL values.

Use:

```sql
WHERE o.id IS NOT NULL
```

This matters heavily with outer JOINs because unmatched rows are represented with `NULL` values on the non-preserved side.

## LEFT JOIN and `COUNT`

Consider:

```sql
SELECT
    c.id,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY c.id;
```

This correctly returns zero for customers with no orders because:

```sql
COUNT(o.id)
```

counts only non-NULL values.

Be careful with:

```sql
COUNT(*)
```

With a `LEFT JOIN`, the NULL-extended row still exists as a result row, so:

```sql
COUNT(*)
```

can return `1` for a customer with no orders.

For relationship counts, prefer:

```sql
COUNT(o.id)
```

or another non-nullable right-side identifier.

## LEFT JOIN and `DISTINCT`

Do not use:

```sql
SELECT DISTINCT ...
```

as a default solution for unexpected duplicates.

If a one-to-many JOIN produces multiple legitimate rows, `DISTINCT` may:

- Hide the actual cardinality problem.
- Add sorting or hashing work.
- Remove legitimate differences.
- Make query intent harder to understand.

First determine the intended grain.

If the requirement is one row per customer, explicitly aggregate or select the appropriate representative row.

## ORM Considerations

In Django, single-valued relationships are commonly loaded with SQL JOINs:

```python
orders = (
    Order.objects
    .select_related("customer")
    .filter(status="completed")
)
```

This is appropriate for foreign key and one-to-one relationships.

For collections:

```python
customers = Customer.objects.prefetch_related("orders")
```

Django can use separate queries and assemble the relationships in application memory.

This distinction is useful when deciding between:

```text
SQL JOIN
```

and:

```text
multiple targeted queries + application-side assembly
```

For large one-to-many relationships, blindly flattening everything into one JOIN can create excessive row counts and memory usage.

## API Design Implications

Suppose an endpoint returns:

```json
{
  "id": 42,
  "email": "alice@example.com",
  "orders": []
}
```

The API may require customers without orders to appear.

A backend query using:

```sql
INNER JOIN orders
```

would incorrectly remove such customers.

A `LEFT JOIN`, separate query, or ORM prefetch may be more appropriate.

For paginated APIs, be especially careful with one-to-many JOINs:

```sql
LIMIT 20
```

limits result rows, not necessarily parent entities.

A common production approach is:

```text
Query 1:
fetch page of customers

        ↓

Query 2:
fetch orders for those customer IDs

        ↓

assemble API response
```

This can provide more predictable parent-level pagination than directly joining a large collection.

## Security Considerations

JOIN selection does not provide authorization.

For multi-tenant systems, tenant boundaries should be explicit.

For example:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.tenant_id = c.tenant_id
WHERE c.tenant_id = :tenant_id;
```

The exact design depends on the schema and authorization model, but tenant isolation should not depend on an assumption that a JOIN will automatically prevent cross-tenant matches.

Always parameterize application inputs:

```sql
WHERE c.tenant_id = :tenant_id
```

rather than constructing SQL through string interpolation.

## Production Considerations

### Correctness

Choose JOIN type based on business semantics:

```text
Must matching record exist?
    → INNER JOIN

Must left record always survive?
    → LEFT JOIN
```

### Performance

Check:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and inspect:

- Estimated rows.
- Actual rows.
- Join algorithm.
- Loop count.
- Buffer usage.
- Sequential scans.
- Sorts.
- Hash operations.

### Scalability

Watch for:

- One-to-many row expansion.
- Many-to-many multiplication.
- Multiple independent child JOINs.
- Large result sets.
- Expensive aggregation after JOINs.

Consider:

- Pre-aggregation.
- `EXISTS` / `NOT EXISTS`.
- Separate queries.
- Pagination at the correct grain.
- Targeted indexes.

### Reliability

Queries should be tested against edge cases:

- Parent without child.
- Parent with one child.
- Parent with many children.
- Missing optional relationship.
- `NULL` values.
- Duplicate relationship rows.
- Empty result sets.

These cases frequently expose incorrect JOIN semantics.

### Monitoring

For important production queries, monitor:

- Query latency.
- Rows returned.
- Database CPU.
- Buffer reads.
- Temporary file usage.
- Lock contention.
- Connection pool utilization.

A JOIN that is acceptable at 10,000 rows may become a serious bottleneck at 100 million rows.

## Common Mistakes and Pitfalls

| Mistake | Why it is wrong | Better approach |
|---|---|---|
| Using `INNER JOIN` when parents without children must remain | Unmatched parents disappear | Use `LEFT JOIN` |
| Filtering a LEFT JOINed table in `WHERE` | Can eliminate NULL-extended rows | Put relationship filters in `ON` when appropriate |
| Assuming `LEFT JOIN` means one row per parent | One-to-many relationships still expand rows | Define the result grain explicitly |
| Using `COUNT(*)` with a LEFT JOIN | Counts NULL-extended rows | Count a non-null right-side key |
| Comparing values with `= NULL` | NULL comparisons produce UNKNOWN | Use `IS NULL` |
| Adding `DISTINCT` to hide duplication | Masks cardinality problems | Fix the underlying query grain |
| Choosing JOIN type based on performance assumptions | Semantics should drive JOIN choice | Choose semantics first, optimize second |
| Assuming FK constraints automatically make JOINs cheap | Integrity and performance are different concerns | Verify indexes and execution plans |
| Joining several child collections directly | Can create multiplicative row growth | Pre-aggregate or load separately |
| Treating ORM JOIN behavior as invisible | ORM-generated SQL can become expensive | Inspect generated SQL and query plans |

## Decision Guide

```text
Start
  │
  ▼
Must every left-side row appear?
  │
  ├── Yes ──► LEFT JOIN
  │             │
  │             └── Filter optional right-side rows in ON
  │
  └── No ───► Is a matching right-side row required?
                │
                ├── Yes ──► INNER JOIN
                │
                └── No ───► Reconsider the query semantics
```

A practical decision table:

| Requirement | Recommended pattern |
|---|---|
| Only entities with a related record | `INNER JOIN` |
| Every left entity regardless of related records | `LEFT JOIN` |
| Every left entity + only matching right records satisfying a condition | `LEFT JOIN ... ON ... AND condition` |
| Find left entities with no related records | `LEFT JOIN ... WHERE right.id IS NULL` or `NOT EXISTS` |
| Count related records including zero | `LEFT JOIN` + `COUNT(right.id)` |
| Parent-level pagination with large child collections | Paginate parents first, then load children |

## Interview Traps

### "Is LEFT JOIN slower than INNER JOIN?"

Not inherently.

`INNER JOIN` can sometimes allow more optimization freedom because there is no outer-row preservation requirement, but actual performance depends on the query plan, cardinality, indexes, predicates, and data distribution.

### "Can WHERE turn a LEFT JOIN into an INNER JOIN?"

Yes, for predicates that reject NULL-extended rows.

For example:

```sql
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed'
```

removes customers without matching orders.

### "Does LEFT JOIN return every row from both tables?"

No.

`LEFT JOIN` preserves every row from the **left** relation. Unmatched right-side columns become `NULL`. Unmatched right-side rows do not independently appear.

### "Does INNER JOIN eliminate duplicates?"

No.

If one customer has ten matching orders, the customer can appear ten times.

JOIN type determines matching and preservation semantics, not uniqueness.

### "Why use LEFT JOIN instead of INNER JOIN if a foreign key exists?"

A foreign key may guarantee that a matching parent exists, but the query may still intentionally require outer semantics, especially for optional relationships or reporting requirements. The correct choice follows the intended result.

### "What is the classic LEFT JOIN mistake?"

Putting a predicate on the optional side in `WHERE`:

```sql
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed'
```

when the actual requirement is to preserve customers without completed orders.

## Key Takeaways

- **`INNER JOIN` keeps only matching rows; `LEFT JOIN` preserves every row from the left relation and represents missing right-side matches as `NULL`.**
- **Choose JOIN type from business semantics: use `INNER JOIN` when a match is required and `LEFT JOIN` when the left-side entity must survive without a match.**
- **With `LEFT JOIN`, predicates on the optional side belong in `ON` when they should restrict matches without removing unmatched left-side rows.**
- **JOIN type does not determine result grain; one-to-many and many-to-many relationships can still multiply rows and require deliberate aggregation or separate loading.**
- **For production performance, validate JOIN-heavy queries with `EXPLAIN (ANALYZE, BUFFERS)` and optimize based on cardinality, indexes, predicates, and actual execution behavior.**