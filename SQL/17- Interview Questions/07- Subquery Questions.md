# 07- Subquery Questions

## Overview

Subqueries are a core SQL interview topic because they test whether you understand query composition, correlation, cardinality, `NULL` semantics, and how logical SQL expressions translate into execution plans.

A subquery is a query nested inside another SQL statement. It can appear in:

- `WHERE`
- `FROM`
- `SELECT`
- `HAVING`
- `INSERT`
- `UPDATE`
- `DELETE`

Common forms include:

- Scalar subqueries
- Multi-row subqueries
- Correlated subqueries
- `IN`
- `EXISTS`
- `NOT EXISTS`
- Derived tables
- Common table expressions
- Subqueries used for aggregation and comparison

The senior-level question is not:

> "Can you write a subquery?"

It is:

> "What result shape does the subquery produce, how does the outer query consume it, and is the resulting execution strategy appropriate for the workload?"

---

## What Is a Subquery?

A subquery is a query embedded inside another query.

Example:

```sql
SELECT *
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);
```

The inner query calculates the average salary.

The outer query then returns employees whose salary is above that average.

Conceptually:

```text
employees
    ↓
calculate AVG(salary)
    ↓
single value
    ↓
compare each employee
    ↓
result
```

---

## Why Subqueries Exist

Subqueries allow one query to use the result of another query without requiring multiple application-side operations.

They are useful when:

- One condition depends on another result
- You need existence checks
- You need aggregate comparisons
- You need a derived relation
- You need to compare rows against a calculated value
- You want to avoid transferring intermediate data to Python

For example, this is usually preferable to:

```text
query average salary
      ↓
send result to Python
      ↓
construct second SQL query
      ↓
query employees
```

when the calculation can be expressed safely in one SQL statement.

---

## Subquery Result Shapes

Understanding the result shape is critical.

| Subquery type | Result |
|---|---|
| Scalar | One value |
| Single-column multi-row | Multiple values in one column |
| Multi-column multi-row | Table-like rows |
| Correlated | Result depends on current outer row |
| `EXISTS` | Boolean existence condition |

The outer operator must be compatible with the subquery's shape.

---

## Scalar Subquery

A scalar subquery returns one value.

Example:

```sql
SELECT
    id,
    salary,
    salary - (
        SELECT AVG(salary)
        FROM employees
    ) AS difference_from_average
FROM employees;
```

The inner query must return at most one row.

---

## Scalar Subquery Returning Multiple Rows

This is invalid:

```sql
SELECT *
FROM employees
WHERE salary > (
    SELECT salary
    FROM employees
    WHERE department_id = 10
);
```

If department `10` contains multiple employees, the scalar subquery returns multiple rows.

PostgreSQL raises an error similar to:

```text
more than one row returned by a subquery used as an expression
```

Use an appropriate operator such as:

```sql
IN
ANY
ALL
EXISTS
```

or aggregate the result if one value is actually required.

---

## Scalar Subquery Returning No Rows

A scalar subquery that returns no rows produces `NULL` when used as a scalar expression.

For example:

```sql
SELECT
    (
        SELECT salary
        FROM employees
        WHERE id = -1
    ) AS salary;
```

The result is:

```text
NULL
```

This can interact with outer predicates through SQL's three-valued logic.

---

## `IN` With a Subquery

`IN` checks whether a value matches a value returned by the subquery.

```sql
SELECT *
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'paid'
);
```

This means:

> Return customers who have at least one paid order.

---

## `IN` vs JOIN

The same requirement can sometimes be written with a join:

```sql
SELECT DISTINCT c.*
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'paid';
```

Or with `EXISTS`:

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
);
```

The important difference is semantic intent.

If you only care whether a related row exists, `EXISTS` often expresses the requirement most directly.

---

## `EXISTS`

`EXISTS` returns true when the subquery produces at least one row.

```sql
SELECT *
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The database does not need the actual selected value.

Therefore:

```sql
SELECT 1
```

is commonly used inside `EXISTS`.

---

## Why `SELECT 1` in EXISTS?

This:

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

have the same existence semantics.

`SELECT 1` communicates:

> I only care whether a row exists.

The value itself is irrelevant.

---

## EXISTS and Performance

A database optimizer can often implement `EXISTS` as a semi-join.

Conceptually:

```text
customer
   ↓
look for matching order
   ↓
first match found
   ↓
TRUE
```

It does not conceptually need to count or return every matching order.

This can make `EXISTS` preferable when the requirement is purely existence.

However, never assume a specific plan without checking:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

---

## Correlated Subquery

A correlated subquery references a column from the outer query.

Example:

```sql
SELECT
    e.id,
    e.name,
    e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT AVG(e2.salary)
    FROM employees AS e2
    WHERE e2.department_id = e.department_id
);
```

The inner query depends on the current outer employee's department.

Conceptually:

```text
employee 1
   ↓
calculate department average
   ↓
compare salary

employee 2
   ↓
calculate department average
   ↓
compare salary
```

The optimizer may transform this into a more efficient plan, but the logical dependency remains.

---

## Correlated vs Non-Correlated Subqueries

### Non-Correlated

```sql
SELECT *
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);
```

The inner query does not reference the outer query.

### Correlated

```sql
SELECT *
FROM employees AS e
WHERE salary > (
    SELECT AVG(e2.salary)
    FROM employees AS e2
    WHERE e2.department_id = e.department_id
);
```

The inner query references:

```sql
e.department_id
```

from the outer query.

---

## Correlated Subquery Performance

A common interview misconception is:

> "A correlated subquery always executes once per outer row."

That is a useful conceptual model, but it is not necessarily how the optimizer executes it.

Modern optimizers can transform correlated subqueries into:

- Joins
- Semi-joins
- Aggregation plans
- Nested-loop strategies
- Other equivalent execution strategies

Therefore:

> Judge the actual execution plan rather than assuming the textual query determines the physical execution.

---

## `NOT EXISTS`

To find customers with no orders:

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This expresses:

> There is no matching order.

It is generally a strong choice for anti-existence queries.

---

## `NOT EXISTS` vs `NOT IN`

Consider:

```sql
WHERE customer_id NOT IN (
    SELECT customer_id
    FROM blocked_customers
);
```

If the subquery can return `NULL`, `NOT IN` can produce unexpected results because of three-valued logic.

`NOT EXISTS` avoids this particular problem:

```sql
WHERE NOT EXISTS (
    SELECT 1
    FROM blocked_customers AS b
    WHERE b.customer_id = customers.id
);
```

This is a classic SQL interview trap.

---

## `ANY`

PostgreSQL supports:

```sql
ANY
```

or equivalently:

```sql
SOME
```

Example:

```sql
SELECT *
FROM employees
WHERE salary > ANY (
    SELECT salary
    FROM employees
    WHERE department_id = 10
);
```

This means the salary must be greater than at least one value from the subquery.

---

## `ALL`

`ALL` requires the comparison to hold against every returned value.

```sql
SELECT *
FROM employees
WHERE salary > ALL (
    SELECT salary
    FROM employees
    WHERE department_id = 10
);
```

This means:

> The employee's salary is greater than every salary in department 10.

---

## ANY vs ALL

| Operator | Meaning |
|---|---|
| `> ANY` | Greater than at least one value |
| `> ALL` | Greater than every value |
| `= ANY` | Equivalent in common cases to `IN` |
| `<> ALL` | Closely related to `NOT IN`, with the same need to reason about `NULL` |

The result can also be affected by an empty or null-containing subquery, so SQL's three-valued logic still matters.

---

## Subquery in FROM

A subquery in `FROM` creates a derived table.

Example:

```sql
SELECT
    customer_id,
    revenue
FROM (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
) AS customer_revenue
WHERE revenue > 10000;
```

The inner query creates:

```text
customer_id | revenue
```

The outer query filters that derived result.

---

## Why Derived Tables Are Useful

They allow you to create intermediate relational results.

Typical uses:

- Aggregate first, filter later
- Transform data before joining
- Isolate complex logic
- Reuse calculated columns within the outer query
- Avoid repeating expressions

They are particularly useful when the intermediate result has a meaningful logical boundary.

---

## Subquery in SELECT

A scalar subquery can appear in the `SELECT` list.

Example:

```sql
SELECT
    c.id,
    c.name,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS order_count
FROM customers AS c;
```

This produces one order count per customer.

The subquery is correlated because it references:

```sql
c.id
```

---

## Scalar Subquery vs JOIN Aggregation

The same result can often be expressed using aggregation:

```sql
SELECT
    c.id,
    c.name,
    COUNT(o.id) AS order_count
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
GROUP BY
    c.id,
    c.name;
```

Which is better depends on:

- Query shape
- Optimizer
- Cardinality
- Indexes
- Required columns
- Additional relationships

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

for important workloads rather than applying a blanket rule such as "joins are always faster."

---

## Subquery in HAVING

A subquery can be used to compare aggregate results.

Example:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
HAVING SUM(total_amount) > (
    SELECT AVG(customer_revenue)
    FROM (
        SELECT
            customer_id,
            SUM(total_amount) AS customer_revenue
        FROM orders
        GROUP BY customer_id
    ) AS revenues
);
```

This finds customers whose revenue is above the average customer revenue.

The logic involves two aggregation levels.

---

## Subqueries for Multi-Level Aggregation

Multi-level aggregation is a common senior SQL problem.

Requirement:

> Find departments whose average employee salary is above the company-wide average department salary.

This requires distinguishing:

```text
employee
    ↓
department average
    ↓
average of department averages
```

The average of averages is not necessarily the same as the average across all employees.

The correct query depends on the intended business metric and weighting.

---

## Subquery vs CTE

A subquery:

```sql
SELECT *
FROM (
    SELECT ...
) AS x;
```

A CTE:

```sql
WITH x AS (
    SELECT ...
)
SELECT *
FROM x;
```

Both can represent intermediate query results.

CTEs can improve readability when the query contains several logical stages.

The choice should be based on:

- Readability
- Reuse
- Planner behavior
- Materialization requirements
- Maintainability

Do not assume CTEs are always slower or always faster than subqueries.

---

## CTE and Materialization

In PostgreSQL, CTE behavior depends on the query and PostgreSQL version.

A CTE may be inlined when appropriate, while explicit:

```sql
MATERIALIZED
```

can force materialization.

Example:

```sql
WITH customer_totals AS MATERIALIZED (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT *
FROM customer_totals
WHERE revenue > 10000;
```

Materialization can be useful when the intermediate result should be computed once and reused, but it can also prevent beneficial predicate pushdown.

---

## Subquery and Predicate Pushdown

Consider:

```sql
SELECT *
FROM (
    SELECT *
    FROM orders
) AS o
WHERE customer_id = $1;
```

A capable optimizer can often simplify this into an equivalent direct filter.

Do not assume every syntactic nesting level creates a physical intermediate table.

SQL describes the desired result; the optimizer determines the physical strategy.

---

## Subquery and JOIN Rewriting

A subquery may be rewritten as a join when the semantics permit.

For example:

```sql
SELECT *
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

can conceptually become a semi-join.

This does not mean you should mechanically rewrite every subquery into a join.

The semantic requirement comes first.

---

## EXISTS vs JOIN for Existence

Requirement:

> Find customers who have at least one paid order.

Preferred semantic expression:

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
);
```

A join may create multiple rows per customer if multiple paid orders exist.

You would then need:

```sql
DISTINCT
```

or grouping.

`EXISTS` avoids expressing an unnecessary one-to-many result.

---

## Subquery and Duplicate Rows

Suppose:

```sql
SELECT c.*
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

A customer with five orders appears five times.

A subquery using `EXISTS`:

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

returns each customer once.

This is a major reason to use existence predicates.

---

## Subqueries for Top-Level Comparisons

Find employees earning above the company average:

```sql
SELECT
    id,
    name,
    salary
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);
```

This is a classic interview question because it tests:

- Scalar subqueries
- Aggregation
- Comparison
- Query composition

---

## Find Rows Matching the Maximum Value

One approach:

```sql
SELECT *
FROM employees
WHERE salary = (
    SELECT MAX(salary)
    FROM employees
);
```

This returns all employees tied for the maximum salary.

That is different from:

```sql
ORDER BY salary DESC
LIMIT 1
```

which returns only one row.

---

## Find Second-Highest Distinct Salary

A subquery approach:

```sql
SELECT MAX(salary) AS second_highest_salary
FROM employees
WHERE salary < (
    SELECT MAX(salary)
    FROM employees
);
```

This returns the second-highest distinct salary.

If all employees have the same salary, the result is `NULL`.

---

## Find Employees Above Their Department Average

```sql
SELECT
    e.id,
    e.name,
    e.department_id,
    e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT AVG(e2.salary)
    FROM employees AS e2
    WHERE e2.department_id = e.department_id
);
```

This is a correlated subquery.

At large scale, compare it with a window-function solution:

```sql
SELECT *
FROM (
    SELECT
        e.*,
        AVG(salary) OVER (
            PARTITION BY department_id
        ) AS department_average
    FROM employees AS e
) AS x
WHERE salary > department_average;
```

Both are valid approaches; the execution plan and workload determine which is preferable.

---

## Subquery vs Window Function

Use a subquery when:

```text
one query result
    ↓
used as a condition/value
```

Use a window function when:

```text
aggregate/ranking
    ↓
must remain attached to individual rows
```

Example:

```sql
salary > company_average
```

can naturally use a scalar subquery.

But:

```text
employee + department average
```

often maps naturally to:

```sql
AVG(salary) OVER (PARTITION BY department_id)
```

---

## Subquery and Aggregation Before JOIN

A useful production pattern is:

```sql
SELECT
    c.id,
    c.name,
    r.revenue
FROM customers AS c
LEFT JOIN (
    SELECT
        customer_id,
        SUM(total_amount) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY customer_id
) AS r
    ON r.customer_id = c.id;
```

The orders are aggregated to customer grain before being joined to customers.

This helps prevent one-to-many joins from multiplying measures.

---

## Subquery for Latest Record

Suppose each customer has many orders and you need customers whose latest order was paid.

A correlated subquery can express the latest timestamp:

```sql
SELECT *
FROM customers AS c
WHERE (
    SELECT o.status
    FROM orders AS o
    WHERE o.customer_id = c.id
    ORDER BY o.created_at DESC, o.id DESC
    LIMIT 1
) = 'paid';
```

This requires appropriate indexing and careful handling of customers without orders.

A common supporting index could be:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC, id DESC);
```

Validate the actual plan before deploying.

---

## Latest Record With JOIN

Another approach is to identify the latest order first and then join it.

Depending on PostgreSQL and the query requirements, alternatives include:

- `DISTINCT ON`
- Window functions
- `LATERAL`
- Aggregate + join-back

The right approach depends on whether you need:

- One latest row
- Latest timestamp
- Complete latest record
- Top N rows per customer

---

## LATERAL Subqueries

PostgreSQL supports `LATERAL`, which allows a subquery in `FROM` to reference preceding `FROM` items.

Example:

```sql
SELECT
    c.id,
    c.name,
    o.id AS latest_order_id,
    o.created_at
FROM customers AS c
LEFT JOIN LATERAL (
    SELECT
        id,
        created_at
    FROM orders AS o
    WHERE o.customer_id = c.id
    ORDER BY created_at DESC, id DESC
    LIMIT 1
) AS o
    ON TRUE;
```

This is useful for:

- Top-N per parent
- Latest child row
- Per-row parameterized lookups

An index such as:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC, id DESC);
```

can support this access pattern.

---

## Subqueries and NULL

Subquery logic must account for `NULL`.

Example:

```sql
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
    WHERE department_id = $1
)
```

If the department contains no non-null salaries, the average can be `NULL`.

Then:

```text
salary > NULL
→ UNKNOWN
```

and the row is not returned.

If the business meaning is to treat missing average as zero:

```sql
COALESCE(
    (
        SELECT AVG(salary)
        FROM employees
        WHERE department_id = $1
    ),
    0
)
```

but only do this when zero is semantically correct.

---

## Subqueries and NULL With NOT IN

Consider:

```sql
SELECT *
FROM customers
WHERE id NOT IN (
    SELECT customer_id
    FROM orders
);
```

If `orders.customer_id` contains `NULL`, the result can be affected by three-valued logic.

Prefer:

```sql
SELECT *
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This is one of the most important subquery interview patterns.

---

## Empty Subqueries

Consider:

```sql
WHERE salary > ALL (
    SELECT salary
    FROM employees
    WHERE department_id = -1
)
```

If the subquery returns no rows, `ALL` and `ANY` have defined logical behavior that differs from simply treating the result as `NULL`.

Interview questions involving `ANY` and `ALL` should therefore consider:

- Empty result sets
- `NULL` values
- Comparison operator
- Three-valued logic

---

## Subquery and INSERT

Subqueries can supply rows for inserts.

```sql
INSERT INTO customer_metrics (
    customer_id,
    order_count
)
SELECT
    customer_id,
    COUNT(*)
FROM orders
GROUP BY customer_id;
```

This is technically a subquery-like query composition through `INSERT ... SELECT`.

For large data movement, database-side operations are often more efficient than loading rows into Python and reinserting them.

---

## Subquery and UPDATE

A subquery can be used in an update.

Example:

```sql
UPDATE customers AS c
SET lifetime_revenue = (
    SELECT COALESCE(SUM(o.total_amount), 0)
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This can be useful for controlled data migrations or recomputation.

For very large tables, however, consider batching, locking, WAL generation, and transaction duration.

---

## UPDATE With EXISTS

A safer pattern when only existence matters:

```sql
UPDATE customers AS c
SET has_paid_order = TRUE
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
);
```

The subquery expresses the condition without requiring a join that could multiply rows.

---

## Subquery and DELETE

Example:

```sql
DELETE FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This deletes customers with no orders.

In production, destructive queries require extra validation:

- Backup/recovery readiness
- Transaction strategy
- Row-count validation
- Lock impact
- Foreign-key dependencies
- Audit requirements

---

## Query Planning and Subqueries

A subquery does not automatically imply:

```text
execute inner query completely
→ store result
→ execute outer query
```

The optimizer can transform the query.

Depending on the query, PostgreSQL may produce:

- Nested loops
- Hash joins
- Merge joins
- Semi-joins
- Anti-joins
- Aggregation
- Materialization

Always inspect the actual plan for performance-sensitive queries.

---

## EXPLAIN for Subqueries

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

Review:

- Estimated rows
- Actual rows
- Loops
- Join strategy
- Index usage
- Buffer reads/hits
- Execution time
- Rows removed by filters

The goal is to understand the physical strategy rather than judging SQL syntax alone.

---

## Correlated Subquery and Indexing

For:

```sql
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
      AND o.status = 'paid'
)
```

an index such as:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

may support efficient lookup.

Whether it is useful depends on:

- Table size
- Selectivity
- Data distribution
- Query frequency
- Existing indexes
- Planner estimates

---

## Subquery Performance Problems

Common causes include:

- Missing indexes
- Poor cardinality estimates
- High outer-row cardinality
- Expensive correlated lookups
- Large `IN` result sets
- Repeated aggregation
- Large materialized intermediate results
- Join multiplication
- Poorly selective predicates

Do not rewrite a subquery merely because it looks nested.

First identify the actual bottleneck.

---

## When a Subquery Is a Good Choice

Use a subquery when it clearly expresses:

- Existence
- Non-existence
- Scalar comparison
- Aggregate comparison
- Intermediate transformation
- Parent-specific lookup

Examples:

```sql
WHERE EXISTS (...)
```

```sql
WHERE salary > (SELECT AVG(...))
```

```sql
FROM (
    SELECT ...
) AS derived
```

---

## When a Subquery May Be a Poor Choice

A subquery may deserve reconsideration when:

- It creates unnecessary repeated work
- A window function expresses the problem more naturally
- A join is required for multiple columns from the same related row
- The intermediate result is unnecessarily large
- A correlated pattern causes excessive random access
- The query becomes difficult to maintain

The answer is not automatically "replace it with a join."

Use semantics and execution evidence.

---

## Subqueries in Django

Django supports subqueries through `Subquery` and `Exists`.

Example:

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

This is a strong ORM representation of an existence query.

---

## Django `Subquery`

Example:

```python
from django.db.models import OuterRef, Subquery

latest_order = Order.objects.filter(
    customer_id=OuterRef("pk"),
).order_by("-created_at", "-id")

customers = Customer.objects.annotate(
    latest_order_id=Subquery(
        latest_order.values("id")[:1]
    )
)
```

This maps naturally to a correlated scalar subquery.

---

## Django and Query Shape

ORM abstractions do not remove SQL semantics.

A senior backend engineer should understand:

```text
Django QuerySet
    ↓
ORM compiler
    ↓
SQL
    ↓
PostgreSQL parser/planner
    ↓
execution
```

For complex subqueries, inspect the generated SQL and execution plan.

---

## SQLAlchemy Subqueries

SQLAlchemy supports scalar subqueries, `exists()`, derived tables, and correlated queries.

Example:

```python
from sqlalchemy import exists, select

stmt = select(Customer).where(
    exists(
        select(1)
        .where(
            Order.customer_id == Customer.id,
            Order.status == "paid",
        )
    )
)
```

The important skill is understanding the SQL generated by the expression.

---

## Subqueries and API Performance

A subquery can keep computation inside PostgreSQL.

Instead of:

```text
API
 ↓
fetch customers
 ↓
Python loop
 ↓
query orders for every customer
```

use a database-side existence or aggregation query.

This avoids an application-level N+1 pattern.

---

## Subquery vs N+1

Bad application pattern:

```python
customers = Customer.objects.all()

for customer in customers:
    customer.orders.count()
```

This can generate many database queries.

A database-side annotation or `Exists` query can consolidate the operation.

The important distinction is:

> A SQL subquery is not the same thing as an application-level N+1 query.

The database optimizer can reason about the entire SQL statement.

---

## Subqueries and Microservices

In a microservice architecture, subqueries can only operate within the database connection/schema accessible to that query.

You cannot write:

```sql
SELECT ...
FROM service_a_database
JOIN service_b_database
...
```

as though independent services were one relational system unless the architecture explicitly provides database-level access.

Service boundaries therefore affect query design.

Cross-service aggregation often requires:

- API composition
- Event-driven read models
- CDC
- Data warehouses
- Materialized projections

---

## Subqueries and Redis

Redis should not normally be used as an ad hoc replacement for relational subqueries.

For example:

```text
PostgreSQL
  → authoritative relational state
```

while:

```text
Redis
  → cache / ephemeral state
```

If a metric requires transactional relational consistency, prefer deriving it from the database or a deliberately designed read model.

---

## Subqueries and Kafka

For cross-service analytics:

```text
Service A
   ↓
Kafka
   ↓
Analytics consumer
   ↓
Read model / warehouse
   ↓
Query
```

This can be more scalable than trying to perform cross-service SQL queries against multiple operational databases.

The trade-off is eventual consistency and additional operational complexity.

---

## Security Considerations

Subqueries must use parameterized values.

Good:

```sql
SELECT *
FROM users
WHERE id IN (
    SELECT user_id
    FROM memberships
    WHERE organization_id = $1
);
```

Avoid dynamically interpolating values into SQL.

Also remember:

> A query that returns only aggregate or existence information can still leak sensitive information.

Authorization and tenant isolation must apply to the entire query.

---

## Multi-Tenant Subqueries

Tenant boundaries must be preserved inside subqueries.

Example:

```sql
SELECT c.*
FROM customers AS c
WHERE c.tenant_id = $1
  AND EXISTS (
      SELECT 1
      FROM orders AS o
      WHERE o.customer_id = c.id
        AND o.tenant_id = $1
        AND o.status = 'paid'
  );
```

Whether the repeated tenant predicate is required depends on the schema constraints and RLS model, but the important point is:

> Never allow a subquery to accidentally escape the tenant security boundary.

---

## Row-Level Security

If PostgreSQL RLS is enabled, subqueries interact with the database's row-level security policies.

This provides an additional database-level protection layer.

However, application engineers should understand:

- Which role executes the query
- Whether RLS is enabled
- Whether the role bypasses RLS
- Whether the table owner bypasses RLS
- Whether `FORCE ROW LEVEL SECURITY` is relevant
- How tenant context is established with connection pooling

Security should never depend on an assumption that a subquery "probably" remains tenant-scoped.

---

## Common Subquery Mistakes

### Using a Scalar Subquery That Returns Multiple Rows

Wrong:

```sql
WHERE salary > (
    SELECT salary
    FROM employees
    WHERE department_id = 10
);
```

Use an aggregate or multi-row operator when appropriate.

### Using NOT IN With Nullable Results

Prefer:

```sql
NOT EXISTS
```

when expressing non-existence.

### Using JOIN for Pure Existence

A join can multiply rows.

Use:

```sql
EXISTS
```

when only existence matters.

### Assuming Correlated Means One Execution Per Row

The optimizer may transform the query.

Inspect the plan.

### Assuming Subqueries Are Always Slow

SQL syntax does not determine the physical execution strategy.

### Assuming Joins Are Always Faster

Correctness and execution plans matter more than blanket rules.

### Ignoring NULL

Subquery results can interact with three-valued logic.

### Returning Too Many Rows From Scalar Subqueries

Ensure the subquery's cardinality matches the consuming operator.

### Forgetting Tenant Scope

Nested queries can accidentally expose cross-tenant data.

### Building Cross-Service SQL

Independent microservice databases should not be treated as one shared relational schema without deliberate architecture.

---

## Interview Traps

### What Is a Subquery?

A query nested inside another SQL statement.

---

### What Is a Correlated Subquery?

A subquery that references columns from the outer query.

---

### Does a Correlated Subquery Always Execute Once Per Outer Row?

No.

That is the logical model, but the optimizer can transform it into another execution strategy.

---

### What Is the Difference Between IN and EXISTS?

`IN` compares a value against a set of values.

`EXISTS` checks whether at least one matching row exists.

When only existence matters, `EXISTS` often communicates the intended semantics more directly.

---

### Why Is NOT EXISTS Often Preferred Over NOT IN?

Because nullable values in the `NOT IN` subquery can produce `UNKNOWN` and unexpected results.

---

### Can a Scalar Subquery Return Multiple Rows?

No.

It must produce at most one row.

---

### What Happens if a Scalar Subquery Returns No Rows?

When used as a scalar expression, it produces `NULL`.

---

### Can a Subquery Be Used in SELECT?

Yes, if it produces a scalar value per outer row.

---

### Can a Subquery Be Used in FROM?

Yes.

It becomes a derived table and normally requires an alias.

---

### Can a Subquery Be Used in UPDATE?

Yes.

For example:

```sql
UPDATE customers AS c
SET lifetime_revenue = (
    SELECT COALESCE(SUM(o.total_amount), 0)
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

---

### Can a Subquery Be Used in DELETE?

Yes.

`EXISTS` and `NOT EXISTS` are particularly useful for conditional deletion.

---

### Is a CTE the Same as a Subquery?

They can represent similar logical transformations, but they have different syntax and can have different planner/materialization behavior.

---

### When Should You Use EXISTS?

When the requirement is:

> Does at least one related row satisfy this condition?

---

### What Is an Anti-Join?

An anti-join returns rows from one relation for which no matching row exists in another.

A common SQL expression is:

```sql
WHERE NOT EXISTS (...)
```

---

## Production Troubleshooting Workflow

When a subquery is slow or returns unexpected results:

### Validate Result Semantics

Ask:

```text
What should the subquery return?
one value?
many values?
existence?
table-shaped rows?
```

### Validate Cardinality

Run:

```sql
SELECT COUNT(*)
FROM (...subquery...) AS x;
```

where appropriate.

### Test NULL Behavior

Check:

```sql
SELECT
    COUNT(*) AS total,
    COUNT(target_column) AS non_null
FROM ...;
```

### Check Correlation

Identify which outer columns the inner query references.

### Inspect the Execution Plan

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

### Check Indexes

Especially for correlated predicates such as:

```sql
WHERE child.parent_id = parent.id
```

### Compare Alternative Forms

Test:

```text
EXISTS
JOIN
window function
derived table
CTE
```

only when they are semantically equivalent.

---

## Senior-Level Subquery Decision Framework

Use this reasoning sequence:

```text
Define result requirement
        ↓
Determine subquery result shape
        ↓
Choose scalar / IN / EXISTS / derived table
        ↓
Check NULL semantics
        ↓
Check cardinality
        ↓
Check correlation
        ↓
Consider JOIN / window-function alternative
        ↓
Validate indexes
        ↓
Inspect EXPLAIN ANALYZE
        ↓
Validate security and tenant boundaries
        ↓
Measure production workload impact
```

This is more valuable than memorizing isolated query patterns.

---

## Production Checklist

Before deploying a complex subquery:

- [ ] The subquery's result cardinality is understood.
- [ ] Scalar subqueries cannot unexpectedly return multiple rows.
- [ ] `NULL` semantics are intentional.
- [ ] `NOT IN` is avoided when nullable values create ambiguity.
- [ ] `EXISTS` is considered for pure existence checks.
- [ ] Join multiplication is understood.
- [ ] Correlated predicates have appropriate access paths.
- [ ] The execution plan has been reviewed for important workloads.
- [ ] Query frequency and concurrency are understood.
- [ ] Tenant boundaries are enforced.
- [ ] Authorization applies to nested queries.
- [ ] Large intermediate results are controlled.
- [ ] OLTP workloads are protected from expensive analytics.
- [ ] Long-running reports can be moved to asynchronous processing or OLAP infrastructure when necessary.
- [ ] Django/SQLAlchemy generated SQL is reviewed when ORM subqueries are complex.

---

## Key Takeaways

- **Choose subqueries based on result semantics:** scalar values, multi-row comparisons, existence checks, and derived tables require different operators and query shapes.
- **`EXISTS` and `NOT EXISTS` are fundamental production patterns:** they express existence directly and avoid many duplicate-row and nullable-`NOT IN` problems.
- **Correlated subqueries are not automatically slow:** the optimizer can transform them, so evaluate actual execution plans rather than judging SQL by syntax alone.
- **Cardinality and `NULL` semantics determine correctness:** understand how many rows a subquery can return and how empty or null-containing results affect the outer predicate.
- **Senior SQL design connects query structure to architecture:** validate indexes, execution plans, tenant isolation, authorization, ORM-generated SQL, workload size, and whether the operation belongs in OLTP PostgreSQL or a separate analytical/read-model system.