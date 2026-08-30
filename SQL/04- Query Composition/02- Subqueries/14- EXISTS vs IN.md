# 14- EXISTS vs IN

## Overview

`EXISTS` and `IN` are both SQL predicates used to filter rows based on information from another relation. They often solve similar business requirements, but they express different logical questions:

- `IN` asks whether a value belongs to a set of values.
- `EXISTS` asks whether at least one qualifying row exists.

For example, these queries can represent the same requirement:

```sql
-- IN
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

```sql
-- EXISTS
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

The important engineering distinction is not simply performance. It is **semantics, NULL behavior, correlation, optimizer behavior, and the shape of the data being tested**.

For production SQL, choose the construct that most directly expresses the business rule, then verify the execution plan rather than assuming one predicate is universally faster.

## Core Difference

Consider:

```sql
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
)
```

The database is effectively asking:

> Is this `customer_id` a member of the result set produced by the subquery?

With:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

the question is:

> Does at least one order satisfying this condition exist for this customer?

The difference becomes especially useful when the subquery needs additional predicates or does not naturally represent a simple value set.

| Characteristic | `IN` | `EXISTS` |
|---|---|---|
| Primary question | Is a value in a set? | Does a qualifying row exist? |
| Typical subquery | Uncorrelated | Often correlated |
| Can reference outer query | Yes, but less commonly | Common use case |
| Multiple matching rows | Set membership remains one Boolean result | Existence remains one Boolean result |
| `NULL` behavior | Important, especially with `NOT IN` | Generally easier to reason about |
| Can inspect multiple columns | Row-value `IN` can | Correlated predicates can |
| Best mental model | Set membership | Existence test |
| Common use | Static or derived value sets | Relationship checks |

## `IN` With a Subquery

`IN` compares an expression against the values returned by a subquery.

Example:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

The subquery produces a set such as:

```text
101
105
108
```

The outer query keeps customers whose IDs belong to that set.

### When `IN` Is a Good Fit

Use `IN` when the business requirement naturally reads:

> Return rows whose value belongs to this set.

For example:

```sql
SELECT
    p.id,
    p.sku
FROM products AS p
WHERE p.category_id IN (
    SELECT c.id
    FROM categories AS c
    WHERE c.department = 'electronics'
);
```

The inner query identifies a set of category IDs. The outer query checks membership in that set.

## `EXISTS` With a Correlated Subquery

The equivalent relationship-oriented query is:

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

The subquery references:

```sql
c.id
```

from the outer query, making it a correlated subquery.

The database evaluates whether at least one matching order exists.

This is often clearer when the actual requirement is:

> Keep the customer if a related order satisfying these conditions exists.

## Choosing Based on Semantics

A useful decision rule is:

```text
Is the requirement about membership in a value set?
        │
        ├── Yes → Consider IN
        │
        └── No
             │
             ▼
     Is the requirement about
     existence of a related row?
             │
             └── Yes → Consider EXISTS
```

For example:

```sql
-- Set membership
WHERE status IN ('pending', 'processing')
```

is naturally expressed with `IN`.

Whereas:

```sql
-- Related-row existence
WHERE EXISTS (
    SELECT 1
    FROM payments AS p
    WHERE p.order_id = o.id
      AND p.status = 'completed'
)
```

is naturally expressed with `EXISTS`.

## `EXISTS` Does Not Care What You Select

The contents of an `EXISTS` subquery are not used as the result value.

These are logically equivalent:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

and:

```sql
WHERE EXISTS (
    SELECT o.id
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

The conventional form is:

```sql
SELECT 1
```

because it communicates that only existence matters.

Do not interpret `SELECT 1` as a performance optimization guaranteed by the SQL language. The optimizer determines the physical execution strategy.

## `IN` and Duplicate Values

Suppose the subquery returns:

```text
101
101
101
105
108
```

`IN` does not produce duplicate outer rows.

```sql
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
)
```

is still a Boolean membership test.

The outer customer is either:

```text
TRUE
```

or:

```text
FALSE / UNKNOWN
```

for the predicate.

This differs from a normal one-to-many join, which can multiply outer rows.

## `EXISTS` and Duplicate Related Rows

Similarly:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

does not multiply customers when a customer has 100 orders.

The result is still one qualifying outer row.

This makes `EXISTS` particularly useful when the application needs columns from the outer table but only needs to know whether a relationship exists.

## The `NULL` Difference

`NULL` is where comparisons involving `IN` and `NOT IN` become especially important.

Suppose:

```sql
SELECT customer_id
FROM orders;
```

returns:

```text
101
105
NULL
```

Then:

```sql
WHERE c.id IN (
    SELECT customer_id
    FROM orders
)
```

has three-valued SQL semantics.

For a customer ID that does not match `101` or `105`, the presence of `NULL` can cause the result to be `UNKNOWN` rather than simply `FALSE`.

For positive `IN`, this often does not produce the same operational surprise as `NOT IN`, because both `FALSE` and `UNKNOWN` fail a `WHERE` predicate. However, the distinction becomes critical when the predicate is negated or combined with other Boolean expressions.

`NOT IN` is particularly dangerous:

```sql
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
)
```

If the subquery contains `NULL`, the result can be unexpectedly empty or exclude rows that appear unrelated.

For negative relationship checks, prefer:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

when its semantics match the requirement.

## `EXISTS` vs `IN`: Correlated vs Uncorrelated

An `IN` subquery is commonly uncorrelated:

```sql
SELECT
    p.id
FROM products AS p
WHERE p.category_id IN (
    SELECT c.id
    FROM categories AS c
    WHERE c.department = 'electronics'
);
```

The inner query does not reference `p`.

An `EXISTS` query is commonly correlated:

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

The inner query references `c.id`.

However, correlation is not a requirement of `EXISTS`.

This is valid:

```sql
SELECT
    c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders
    WHERE status = 'completed'
);
```

It means:

> Return customers if at least one completed order exists anywhere.

The same is true for `IN`: correlation is possible, although it is less common.

## Performance: Do Not Use Keyword Folklore

A common interview claim is:

> `EXISTS` is always faster than `IN`.

That is incorrect.

Another common claim is:

> `IN` is always faster because it builds a set.

Also incorrect.

Modern relational optimizers can transform semantically equivalent queries into similar physical operations.

For example, PostgreSQL may transform membership and existence predicates into semi-join or related execution strategies.

The actual performance depends on:

- Table cardinality.
- Data distribution.
- Selectivity.
- Indexes.
- Statistics.
- Join strategy.
- Predicate complexity.
- Database engine.
- Query parameters.
- Available memory.
- Parallel execution.
- Current database version.

Use `EXPLAIN` or the equivalent tooling for the target database.

## PostgreSQL Example

Compare:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
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

The plans may be different or may converge to similar physical strategies.

The correct engineering process is:

```text
Choose semantically correct SQL
        ↓
Add appropriate indexes
        ↓
Inspect execution plan
        ↓
Measure with realistic data
        ↓
Optimize only if necessary
```

## Indexing Considerations

For:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
)
```

an index on the correlated column is often important:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

If the existence condition includes another selective predicate:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'completed'
)
```

consider an index aligned with the access pattern:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

For PostgreSQL, a partial index can be useful when the query repeatedly checks a stable subset:

```sql
CREATE INDEX idx_completed_orders_customer
ON orders (customer_id)
WHERE status = 'completed';
```

Index design should be based on actual workloads rather than the SQL keyword used.

## Practical Backend Pattern: Customers With Orders

Using `IN`:

```sql
SELECT
    c.id,
    c.email
FROM customers AS c
WHERE c.id IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

Using `EXISTS`:

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

Both express:

> Return customers with at least one order.

The `EXISTS` version makes the relationship explicit.

For complex related-row conditions, it often becomes easier to extend:

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
      AND o.total_amount >= 1000
);
```

## Practical Backend Pattern: Categories

Suppose products belong to categories and the API should return products belonging to categories in the electronics department.

`IN` is natural:

```sql
SELECT
    p.id,
    p.sku
FROM products AS p
WHERE p.category_id IN (
    SELECT c.id
    FROM categories AS c
    WHERE c.department = 'electronics'
);
```

An equivalent `EXISTS` form is:

```sql
SELECT
    p.id,
    p.sku
FROM products AS p
WHERE EXISTS (
    SELECT 1
    FROM categories AS c
    WHERE c.id = p.category_id
      AND c.department = 'electronics'
);
```

Here, `IN` communicates set membership more directly.

## Practical Backend Pattern: Permission Checks

Consider a request that needs to determine whether a user has a specific permission.

```sql
SELECT
    u.id,
    u.email
FROM users AS u
WHERE EXISTS (
    SELECT 1
    FROM user_permissions AS up
    WHERE up.user_id = u.id
      AND up.permission = 'reports.read'
);
```

This is naturally an existence question:

> Does a permission row exist for this user?

It avoids loading permission records into Python merely to evaluate a Boolean condition.

In Django, the same concept can be expressed using `Exists`:

```python
from django.db.models import Exists, OuterRef

permission = UserPermission.objects.filter(
    user_id=OuterRef("pk"),
    permission="reports.read",
)

users = User.objects.filter(
    Exists(permission),
)
```

The database performs the relational filtering rather than the application materializing a large list of IDs.

## Practical Backend Pattern: Anti-Join

For customers without orders, use:

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

Avoid blindly converting this to:

```sql
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

especially when `orders.customer_id` is nullable or the schema may evolve.

The distinction is particularly important in production systems where historical and partially populated data may exist.

## Multi-Column Membership

SQL supports row-value comparisons in databases such as PostgreSQL:

```sql
SELECT
    o.id
FROM orders AS o
WHERE (o.customer_id, o.currency) IN (
    SELECT
        a.customer_id,
        a.currency
    FROM allowed_customer_currencies AS a
);
```

This can be appropriate when the requirement genuinely concerns membership in a composite set.

An equivalent existence formulation is:

```sql
SELECT
    o.id
FROM orders AS o
WHERE EXISTS (
    SELECT 1
    FROM allowed_customer_currencies AS a
    WHERE a.customer_id = o.customer_id
      AND a.currency = o.currency
);
```

For relationship-style logic, `EXISTS` can be easier to extend with additional predicates.

## `IN` With a Small Static Set

Do not use a subquery when the values are already known:

```sql
SELECT
    id,
    email
FROM users
WHERE status IN ('active', 'pending');
```

This is clearer than constructing an unnecessary subquery.

For application-supplied values, use parameterized queries rather than interpolating values into SQL.

For example, application frameworks should generate parameterized SQL for a list of values rather than constructing SQL strings manually.

## `IN` With Application-Generated Lists

A common backend pattern is:

```python
user_ids = ...
```

followed by:

```sql
WHERE user_id IN (...)
```

This is reasonable for bounded lists, but large lists can introduce:

- Large SQL statements.
- High parse/planning overhead.
- Parameter-count limitations.
- Network overhead.
- Poor plan quality.
- Application memory pressure.

For large datasets, prefer database-side relations, temporary tables, staging tables, joins, or other database-native approaches.

Do not move a relational problem into Python merely because `IN` makes it syntactically convenient.

## Security Considerations

Both `IN` and `EXISTS` are safe SQL constructs when used with parameterized queries.

The security problem is usually how application code constructs the predicate.

Avoid:

```python
query = f"""
SELECT id
FROM users
WHERE status IN ({user_input})
"""
```

Build queries using your database driver's parameterization facilities or your ORM.

For Django and FastAPI applications, let the ORM or database driver bind values rather than concatenating user-controlled strings.

The same principle applies to dynamically generated lists.

## Scalability Considerations

At small scale, these queries may all appear equally fast.

At production scale, consider:

- Number of outer rows.
- Number of candidate related rows.
- Cardinality of the subquery.
- Index selectivity.
- Data skew.
- Partitioning.
- Query frequency.
- Connection pool pressure.
- Read replica capacity.

For a high-QPS REST API, a seemingly small existence check can become expensive when executed thousands of times per second.

Prefer a single set-oriented SQL query over application-side loops.

Avoid the N+1 pattern:

```python
for customer in customers:
    has_orders = check_orders(customer.id)
```

A single SQL query using `EXISTS` can usually express the relationship in one database round trip.

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Assuming `EXISTS` is always faster | Keyword folklore | Inspect the execution plan |
| Assuming `IN` is always faster | Oversimplified optimizer assumptions | Benchmark realistic workloads |
| Using `NOT IN` with nullable subquery data | Ignoring three-valued logic | Prefer `NOT EXISTS` for negative relationship checks |
| Using `IN` for complex relationship logic | Treating everything as set membership | Consider `EXISTS` |
| Using `EXISTS` when simple membership is clearer | Overengineering a simple predicate | Use `IN` when set membership is the actual requirement |
| Materializing huge ID lists in Python | Moving relational work into application code | Keep filtering in the database |
| Forgetting indexes | Testing only with small data | Inspect access paths and execution plans |
| Using application string interpolation | Convenience | Always parameterize values |
| Confusing existence with locking | Assuming a check prevents concurrent writes | Use transactions and appropriate constraints/locks |
| Ignoring tenant boundaries | Assuming outer filters are enough | Enforce tenant scoping consistently |

## Common `NULL` Pitfall

The most important practical rule is:

```sql
NOT IN
```

requires explicit thought about `NULL`.

For example:

```sql
SELECT
    c.id
FROM customers AS c
WHERE c.id NOT IN (
    SELECT o.customer_id
    FROM orders AS o
);
```

If `o.customer_id` can contain `NULL`, the result can have unintuitive behavior.

A safer relationship-oriented expression is:

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

This is one reason senior engineers often reach for `NOT EXISTS` when expressing negative relationship conditions.

## Interview Traps

### Is `EXISTS` always faster than `IN`?

No.

The optimizer may transform both into similar physical execution strategies. Performance depends on the database engine, indexes, cardinality, statistics, predicates, and data distribution.

### When should I prefer `EXISTS`?

Prefer it when the business question is:

> Does at least one related row satisfying these conditions exist?

It is particularly natural for correlated relationship checks.

### When should I prefer `IN`?

Prefer it when the business question is:

> Is this value a member of this set?

Examples include:

```sql
WHERE status IN ('active', 'pending')
```

or:

```sql
WHERE category_id IN (
    SELECT id
    FROM categories
    WHERE department = 'electronics'
)
```

### Which is safer with `NULL`?

For positive membership, both have SQL three-valued logic that must be understood.

For negative membership, `NOT IN` is the major trap because a `NULL` in the subquery result can make comparisons evaluate to `UNKNOWN`.

`NOT EXISTS` is generally the safer construct for negative relationship checks.

### Does `EXISTS` stop after the first match?

Logically, `EXISTS` only needs to establish that at least one qualifying row exists. Database optimizers can use physical strategies that avoid unnecessary work once existence has been established.

Do not interpret this as a guaranteed row-by-row early exit in every execution plan.

### Does `IN` always materialize the entire subquery?

No.

That is an implementation detail, not a SQL semantic requirement. The optimizer may transform the query into a semi-join or use another execution strategy.

### Can `EXISTS` and `IN` always be rewritten into each other?

Often, but not blindly.

Equivalent rewrites must preserve:

- `NULL` semantics.
- Correlation.
- Duplicate behavior.
- Row-value semantics.
- Boolean logic.
- Additional predicates.

Correctness should be established before treating two queries as equivalent.

## Production Decision Guide

| Requirement | Preferred starting point |
|---|---|
| Check membership in a small known list | `IN` |
| Check membership in a derived value set | `IN` |
| Check whether a related row exists | `EXISTS` |
| Check whether no related row exists | `NOT EXISTS` |
| Complex correlated relationship condition | `EXISTS` / `NOT EXISTS` |
| Negative membership against nullable data | `NOT EXISTS` |
| Need columns from the related relation | Consider a `JOIN` |
| Very large application-generated ID list | Consider a relational/staging approach |
| Performance-sensitive query | Choose semantically correct form, then inspect the plan |

## Production Checklist

Before shipping an `IN` or `EXISTS` query on a high-volume backend path:

- Confirm whether the requirement is **set membership** or **row existence**.
- Check `NULL` semantics, especially for `NOT IN`.
- Ensure correlated columns have appropriate indexes.
- Inspect the execution plan with production-scale cardinalities.
- Avoid materializing large subquery results in Python.
- Avoid N+1 database queries.
- Parameterize application-supplied values.
- Verify tenant isolation where applicable.
- Consider query frequency and connection-pool pressure.
- Measure actual latency and buffer/IO behavior before optimizing.
- Do not rely on generic claims that one predicate is universally faster.

## Key Takeaways

- **`IN` expresses set membership, while `EXISTS` expresses the existence of at least one qualifying row.**
- **Use `EXISTS` when the business rule is relationship-oriented, especially for correlated conditions with additional predicates.**
- **Do not assume `EXISTS` is always faster than `IN`; modern optimizers can transform both into efficient equivalent physical strategies.**
- **Treat `NULL` semantics carefully, especially with `NOT IN`; `NOT EXISTS` is generally safer for negative relationship checks.**
- **For production performance, optimize the complete query: indexes, cardinality, statistics, execution plan, data distribution, and application access pattern all matter.**