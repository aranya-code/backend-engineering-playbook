# 02- SQL Fundamentals Questions

## Overview

SQL fundamentals interview questions test whether you understand the language as a relational query system rather than as a collection of commands.

At intermediate and senior backend levels, interviewers commonly probe:

- Relational tables and result sets
- `SELECT`, `WHERE`, `ORDER BY`, and `LIMIT`
- `NULL` and three-valued logic
- Data types and type conversion
- Joins and relationship cardinality
- Aggregation and grouping
- Subqueries and `EXISTS`
- CTEs
- Set operations
- `INSERT`, `UPDATE`, and `DELETE`
- Constraints
- Keys and relationships
- Views
- Transactions
- SQL functions and expressions
- String and date operations
- Query readability and maintainability
- Basic performance reasoning

The goal is not to memorize isolated answers. A strong candidate should be able to explain **what the query means, what rows it produces, why it is correct, and what changes when the dataset becomes large or concurrent**.

For PostgreSQL-backed Python applications, this foundation is particularly important because Django and SQLAlchemy eventually translate application operations into SQL executed by the database engine.

---

## Relational Database Concepts

A relational database stores data in relations, commonly represented as tables.

A simplified model is:

```text
customers
┌────┬───────────────┬─────────────┐
│ id │ email         │ name        │
├────┼───────────────┼─────────────┤
│ 1  │ a@example.com │ Alice       │
│ 2  │ b@example.com │ Bob         │
└────┴───────────────┴─────────────┘

orders
┌────┬─────────────┬────────┬────────┐
│ id │ customer_id │ status │ amount │
├────┼─────────────┼────────┼────────┤
│ 10 │ 1           │ paid   │ 100.00 │
│ 11 │ 1           │ open   │ 50.00  │
└────┴─────────────┴────────┴────────┘
```

The relationship is:

```text
customers.id
     │
     │ 1:N
     ↓
orders.customer_id
```

SQL allows applications to retrieve and manipulate these related datasets.

---

## Tables, Rows, and Columns

A table consists conceptually of:

- Rows representing records
- Columns representing attributes
- A defined schema describing data types and constraints

Example:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL,
    name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
```

The column definitions are part of the database contract.

A production schema should encode important invariants rather than relying entirely on application code.

---

## `SELECT`

The basic query structure is:

```sql
SELECT column1, column2
FROM table_name;
```

Example:

```sql
SELECT
    id,
    email,
    name
FROM customers;
```

Avoid `SELECT *` in application queries when you do not need every column.

Prefer:

```sql
SELECT
    id,
    email
FROM customers;
```

This can reduce:

- Network transfer
- Database-to-application work
- Application memory usage
- Serialization cost

It also makes the query's data contract explicit.

---

## Column Aliases

Aliases make result columns easier to consume.

```sql
SELECT
    id AS customer_id,
    email AS customer_email
FROM customers;
```

Aliases are particularly useful in reporting queries and joins where multiple tables contain similarly named columns.

---

## Expressions

SQL can calculate values directly.

```sql
SELECT
    id,
    amount,
    amount * 1.18 AS amount_with_tax
FROM orders;
```

Expressions can contain:

- Arithmetic
- Functions
- Conditional expressions
- Type casts
- String operations
- Date/time operations

The database can perform these calculations close to the data.

---

## `WHERE`

`WHERE` filters rows.

```sql
SELECT
    id,
    email
FROM customers
WHERE id = 42;
```

Multiple predicates can be combined:

```sql
SELECT
    id,
    email
FROM customers
WHERE status = 'active'
  AND created_at >= $1;
```

### `AND` and `OR`

Be careful with precedence.

This:

```sql
WHERE status = 'active'
   OR status = 'pending'
  AND priority = 'high'
```

is interpreted according to SQL operator precedence, not necessarily the way a reader expects.

Use parentheses when the business condition requires explicit grouping:

```sql
WHERE (
    status = 'active'
    OR status = 'pending'
)
AND priority = 'high';
```

---

## Comparison Operators

Common operators include:

```sql
=
<>
!=
>
>=
<
<=
```

For example:

```sql
SELECT *
FROM orders
WHERE amount >= 100;
```

`<>` is the standard SQL "not equal" operator. PostgreSQL also accepts `!=`.

---

## `IN`

`IN` checks membership in a set of values.

```sql
SELECT *
FROM orders
WHERE status IN ('pending', 'paid', 'shipped');
```

It can be useful for relatively small application-provided lists.

For large lists, consider how values are supplied and whether a temporary/staging table, array operation, or join is more appropriate.

---

## `BETWEEN`

`BETWEEN` is inclusive at both boundaries.

```sql
SELECT *
FROM orders
WHERE amount BETWEEN 100 AND 500;
```

This is equivalent to:

```sql
WHERE amount >= 100
  AND amount <= 500
```

For timestamps, inclusive `BETWEEN` can be problematic when representing time ranges.

Prefer half-open intervals:

```sql
WHERE created_at >= $1
  AND created_at < $2;
```

For example:

```text
2026-09-01 00:00:00
≤ timestamp <
2026-10-01 00:00:00
```

This avoids ambiguity at boundary values.

---

## `LIKE`

`LIKE` performs pattern matching.

```sql
SELECT *
FROM customers
WHERE email LIKE '%@example.com';
```

Common patterns:

```text
'abc%'   → starts with abc
'%abc'   → ends with abc
'%abc%'  → contains abc
```

Leading wildcards can make ordinary B-tree index usage difficult.

For production search requirements, consider the actual workload and whether PostgreSQL features such as trigram indexes or a dedicated search system are more appropriate.

---

## `ILIKE` in PostgreSQL

PostgreSQL provides `ILIKE` for case-insensitive pattern matching.

```sql
SELECT *
FROM customers
WHERE email ILIKE '%example%';
```

Do not assume that `ILIKE` automatically provides efficient indexed search for arbitrary patterns.

Index strategy depends on the pattern and operator.

---

## `NULL`

`NULL` represents an absent or unknown value.

This is incorrect:

```sql
WHERE deleted_at = NULL
```

Use:

```sql
WHERE deleted_at IS NULL
```

or:

```sql
WHERE deleted_at IS NOT NULL
```

### Interview question

**Why does `NULL = NULL` not return `TRUE`?**

Because `NULL` represents an unknown value, so equality cannot establish that two unknown values are equal. SQL therefore uses three-valued logic.

---

## Three-Valued Logic

SQL predicates can produce:

```text
TRUE
FALSE
UNKNOWN
```

For example:

```sql
NULL = 10
```

produces `UNKNOWN`.

A `WHERE` clause returns rows only when its predicate evaluates to `TRUE`.

This explains many surprising results involving:

- `NULL`
- `NOT IN`
- `AND`
- `OR`
- `NOT`

---

## `COALESCE`

`COALESCE` returns the first non-`NULL` expression.

```sql
SELECT
    id,
    COALESCE(discount, 0) AS discount
FROM orders;
```

This is useful when producing API or reporting values.

However, wrapping indexed columns in functions inside predicates can affect index usage.

For example, instead of automatically writing:

```sql
WHERE COALESCE(status, 'unknown') = 'paid'
```

first determine whether the predicate can be expressed directly against the underlying data.

---

## `CASE`

`CASE` implements conditional logic.

```sql
SELECT
    id,
    amount,
    CASE
        WHEN amount >= 1000 THEN 'high'
        WHEN amount >= 500 THEN 'medium'
        ELSE 'low'
    END AS order_size
FROM orders;
```

It is useful for:

- Classification
- Conditional aggregation
- Business reporting
- Derived result fields

---

## `ORDER BY`

`ORDER BY` controls result ordering.

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC;
```

Multiple columns can be used:

```sql
ORDER BY created_at DESC, id DESC;
```

The second column acts as a deterministic tie-breaker.

This is particularly important for API pagination.

---

## `LIMIT`

`LIMIT` restricts the number of returned rows.

```sql
SELECT
    id,
    email
FROM customers
ORDER BY id
LIMIT 100;
```

`LIMIT` can reduce returned data, but it does not automatically make a query cheap.

The database may still need to:

- Scan rows
- Filter rows
- Sort data
- Join tables
- Perform aggregation

Whether `LIMIT` enables early termination depends on the execution plan.

---

## `OFFSET`

```sql
SELECT
    id,
    email
FROM customers
ORDER BY id
LIMIT 100
OFFSET 10000;
```

This is simple but can become inefficient for deep pagination because the database may process rows that are ultimately discarded.

For large APIs, keyset pagination is often preferable.

---

## Keyset Pagination

Instead of saying:

> Skip 10,000 rows.

the application can say:

> Continue after this known position.

Example:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

This works well with an appropriate index and stable ordering.

---

## `DISTINCT`

`DISTINCT` removes duplicate result rows.

```sql
SELECT DISTINCT customer_id
FROM orders;
```

Use it when uniqueness is part of the requested result.

Do not use `DISTINCT` as a generic solution for unexpected duplicate rows caused by an incorrect join.

---

## `DISTINCT ON` in PostgreSQL

PostgreSQL provides `DISTINCT ON`.

For example:

```sql
SELECT DISTINCT ON (customer_id)
    customer_id,
    id,
    created_at
FROM orders
ORDER BY customer_id, created_at DESC, id DESC;
```

This returns one row per customer according to the specified ordering.

It is concise and powerful but PostgreSQL-specific.

---

## Joins

Joins combine related datasets.

Example:

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id,
    o.amount
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

The join condition defines the relationship.

For a one-to-many relationship:

```text
1 customer
   ↓
many orders
```

the customer row can appear multiple times in the result.

---

## Inner Join

An `INNER JOIN` returns matching rows from both sides.

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
INNER JOIN orders AS o
    ON o.customer_id = c.id;
```

Customers without matching orders are excluded.

`JOIN` without a qualifier means `INNER JOIN`.

---

## Left Join

A `LEFT JOIN` preserves all rows from the left relation.

```sql
SELECT
    c.id,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

Customers without orders still appear, with `NULL` values for order columns.

---

## Join Cardinality

Always identify the relationship before joining.

Typical relationship types:

| Relationship | Example |
|---|---|
| One-to-one | User → Profile |
| One-to-many | Customer → Orders |
| Many-to-many | Students → Courses |
| Many-to-one | Orders → Customer |

A many-to-many join can multiply rows substantially.

For example:

```text
Customer
   ↓
Orders
   ↓
Order Items
   ↓
Products
```

Joining all four relations may produce multiple rows per customer and per order.

If the desired result is one row per customer, aggregation or `EXISTS` may be more appropriate than returning every joined combination.

---

## `CROSS JOIN`

A cross join produces a Cartesian product.

```sql
SELECT *
FROM colors
CROSS JOIN sizes;
```

If there are:

```text
5 colors × 10 sizes
```

the result contains:

```text
50 combinations
```

This can be intentional for generating combinations but can also cause catastrophic row multiplication when used accidentally.

---

## Aggregation

Aggregation summarizes rows.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
FROM orders
GROUP BY customer_id;
```

The result grain is:

> one row per customer.

This is an important interview concept.

---

## `COUNT(*)`

`COUNT(*)` counts rows.

```sql
SELECT COUNT(*)
FROM orders;
```

It includes rows regardless of whether individual columns contain `NULL`.

---

## `COUNT(column)`

`COUNT(column)` counts non-`NULL` values.

For:

```text
amount
------
100
200
NULL
```

the result is:

```sql
COUNT(*)      -- 3
COUNT(amount) -- 2
```

This distinction is frequently tested.

---

## `COUNT(DISTINCT ...)`

```sql
SELECT COUNT(DISTINCT customer_id)
FROM orders;
```

This counts unique non-`NULL` customer IDs.

It answers a different question from:

```sql
COUNT(*)
```

---

## `GROUP BY`

Every selected non-aggregated column generally needs to be represented in the grouping semantics.

Example:

```sql
SELECT
    customer_id,
    status,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id, status;
```

The result grain is:

```text
one row per customer + status
```

Always state the result grain when explaining aggregation in an interview.

---

## `HAVING`

`HAVING` filters groups.

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 10;
```

Contrast:

```sql
WHERE
```

with:

```sql
HAVING
```

`WHERE` filters rows before grouping.

`HAVING` filters groups after aggregation.

---

## Conditional Aggregation

PostgreSQL supports `FILTER`:

```sql
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'paid'
    ) AS paid_orders
FROM orders
GROUP BY customer_id;
```

This can be clearer than repeating separate queries.

---

## Window Functions

Window functions calculate across related rows without collapsing them.

```sql
SELECT
    id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

Each order remains in the result.

This differs from:

```sql
SELECT
    customer_id,
    SUM(amount)
FROM orders
GROUP BY customer_id;
```

which produces one row per customer.

---

## `ROW_NUMBER`

```sql
SELECT
    id,
    customer_id,
    created_at,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS row_number
FROM orders;
```

This is useful for:

- Latest record per group
- Top N per group
- Deduplication workflows
- Ranking

---

## `RANK` vs `DENSE_RANK`

Suppose scores are:

```text
100
100
90
```

The results are:

| Function | Ranking |
|---|---|
| `ROW_NUMBER()` | 1, 2, 3 |
| `RANK()` | 1, 1, 3 |
| `DENSE_RANK()` | 1, 1, 2 |

Choose based on whether ties should consume ranking positions.

---

## Subqueries

A subquery is a query nested inside another query.

Example:

```sql
SELECT *
FROM customers
WHERE id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'paid'
);
```

Subqueries can appear in:

- `WHERE`
- `FROM`
- `SELECT`
- `HAVING`

The best form depends on semantics, readability, and execution behavior.

---

## `EXISTS`

`EXISTS` checks whether a matching row exists.

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This expresses:

> Return customers for whom at least one order exists.

It avoids unnecessarily returning all matching order rows.

The optimizer may transform logically equivalent queries, so do not claim that `EXISTS` is always faster than a join.

---

## `NOT EXISTS`

`NOT EXISTS` is useful for anti-joins.

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This returns customers with no orders.

It is often preferable to `NOT IN` when nullable values could be involved.

---

## Correlated Subqueries

A correlated subquery references the outer query.

```sql
SELECT
    c.id,
    (
        SELECT MAX(o.created_at)
        FROM orders AS o
        WHERE o.customer_id = c.id
    ) AS latest_order_at
FROM customers AS c;
```

The database optimizer may transform such queries, but correlated expressions can still become expensive depending on the plan and cardinality.

Always inspect important queries rather than assuming a particular execution strategy.

---

## Common Table Expressions

A CTE gives a query expression a name.

```sql
WITH paid_orders AS (
    SELECT
        id,
        customer_id,
        amount
    FROM orders
    WHERE status = 'paid'
)
SELECT
    customer_id,
    SUM(amount) AS revenue
FROM paid_orders
GROUP BY customer_id;
```

CTEs improve readability for complex queries.

They are also useful for:

- Recursive queries
- Multi-step transformations
- Data modification workflows

Modern PostgreSQL can inline eligible CTEs. Do not assume every CTE automatically creates a materialization boundary.

---

## Recursive CTE

Recursive CTEs can process hierarchical data.

Example:

```sql
WITH RECURSIVE employee_tree AS (
    SELECT
        id,
        manager_id,
        name
    FROM employees
    WHERE id = $1

    UNION ALL

    SELECT
        e.id,
        e.manager_id,
        e.name
    FROM employees AS e
    JOIN employee_tree AS et
        ON e.manager_id = et.id
)
SELECT *
FROM employee_tree;
```

Typical use cases include:

- Organizational hierarchies
- Category trees
- Folder structures
- Graph-like traversal

Production systems should consider depth, cycles, indexes, and worst-case traversal size.

---

## Set Operations

SQL provides operators for combining compatible result sets.

### `UNION`

```sql
SELECT email
FROM customers

UNION

SELECT email
FROM subscribers;
```

`UNION` removes duplicates.

### `UNION ALL`

```sql
SELECT email
FROM customers

UNION ALL

SELECT email
FROM subscribers;
```

`UNION ALL` preserves duplicates and is generally cheaper when deduplication is unnecessary.

### Other operations

PostgreSQL also supports:

```sql
INTERSECT
EXCEPT
```

These are useful when the problem is naturally expressed as set comparison.

---

## `UNION` vs `UNION ALL`

A common interview question:

> Which is faster?

Usually `UNION ALL`, because it does not need to eliminate duplicates.

But performance should not override correctness.

If the requirement is:

> Return each value once.

then duplicate elimination is part of the business requirement.

---

## `INSERT`

Basic insert:

```sql
INSERT INTO customers (
    email,
    name
)
VALUES (
    $1,
    $2
);
```

Always specify columns explicitly.

This makes the statement more robust against schema changes and clearer to readers.

---

## Multi-Row Insert

```sql
INSERT INTO customers (
    email,
    name
)
VALUES
    ($1, $2),
    ($3, $4),
    ($5, $6);
```

For very large PostgreSQL ingestion workloads, application batching or `COPY` may be more appropriate than generating enormous `INSERT` statements.

---

## `RETURNING`

PostgreSQL supports `RETURNING`:

```sql
INSERT INTO customers (
    email,
    name
)
VALUES (
    $1,
    $2
)
RETURNING id, created_at;
```

It can also be used with updates and deletes:

```sql
UPDATE orders
SET status = 'paid'
WHERE id = $1
RETURNING id, status;
```

This can eliminate an additional query.

---

## `UPDATE`

```sql
UPDATE orders
SET status = 'cancelled'
WHERE id = $1;
```

Always verify the predicate.

Before executing a large update, it is often useful to inspect the affected rows using the equivalent `SELECT`.

For example:

```sql
SELECT id
FROM orders
WHERE status = 'pending'
  AND created_at < $1;
```

Then perform the update when the scope is verified.

---

## Atomic Updates

Prefer database-side atomic operations for concurrent state changes.

Instead of:

```text
SELECT inventory
calculate in application
UPDATE inventory
```

use:

```sql
UPDATE inventory
SET quantity = quantity - $1
WHERE product_id = $2
  AND quantity >= $1
RETURNING quantity;
```

This allows the database to evaluate the condition and perform the update atomically.

---

## `DELETE`

```sql
DELETE FROM sessions
WHERE expires_at < now();
```

Large deletes can generate substantial:

- WAL
- Dead tuples
- Vacuum work
- Replication traffic
- Lock pressure

For large datasets, consider batching or partition lifecycle operations.

---

## `TRUNCATE`

`TRUNCATE` removes all rows from a table much more efficiently than a row-by-row delete for appropriate use cases.

```sql
TRUNCATE TABLE staging_events;
```

However, it has different locking and transactional implications from `DELETE` and interacts with foreign keys and triggers differently.

It should not be treated as a faster substitute for application-level deletes when row-level business behavior is required.

---

## Upsert

PostgreSQL supports `INSERT ... ON CONFLICT`.

```sql
INSERT INTO users (
    email,
    name
)
VALUES (
    $1,
    $2
)
ON CONFLICT (email)
DO UPDATE
SET name = EXCLUDED.name
RETURNING id;
```

This is preferable to a naïve:

```text
SELECT
if not found:
    INSERT
```

because concurrent requests can race between the existence check and insert.

Database-enforced uniqueness is the foundation of reliable upsert behavior.

---

## `MERGE`

PostgreSQL also supports `MERGE` for conditionally applying insert/update/delete actions based on a source relation.

A simplified example:

```sql
MERGE INTO customers AS target
USING customer_updates AS source
ON target.email = source.email
WHEN MATCHED THEN
    UPDATE SET name = source.name
WHEN NOT MATCHED THEN
    INSERT (email, name)
    VALUES (source.email, source.name);
```

`MERGE` can be useful for synchronization and bulk transformation workloads.

For simple application-level upserts, `INSERT ... ON CONFLICT` is often more direct.

---

## Primary Keys

A primary key uniquely identifies rows.

Example:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL
);
```

A table has one primary key constraint, although that key can contain multiple columns.

---

## Composite Primary Keys

A composite primary key uses multiple columns:

```sql
CREATE TABLE memberships (
    user_id bigint NOT NULL,
    organization_id bigint NOT NULL,
    PRIMARY KEY (user_id, organization_id)
);
```

This models uniqueness of the combination.

Composite keys can be useful for association tables, but they also affect:

- Foreign-key design
- ORM mapping
- Index structure
- Query patterns

Choose them deliberately.

---

## Foreign Keys

A foreign key establishes referential integrity.

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL
        REFERENCES customers(id)
);
```

This prevents an order from referencing a nonexistent customer.

Foreign keys are particularly important because application-level validation alone is vulnerable to concurrent writes and alternate access paths.

---

## Unique Constraints

```sql
CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE
);
```

A unique constraint expresses a database-level invariant.

For more complex rules, a unique index may be appropriate.

Example:

```sql
CREATE UNIQUE INDEX idx_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

---

## `NOT NULL`

`NOT NULL` ensures a column contains a value.

```sql
email text NOT NULL
```

Use it when absence is not a valid state.

Avoid making every field `NOT NULL` merely for consistency; nullability should represent domain semantics.

---

## `CHECK`

`CHECK` enforces a row-level predicate.

```sql
CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    price numeric(12, 2) NOT NULL
        CHECK (price >= 0)
);
```

This protects the invariant even if data is inserted through:

- Django
- FastAPI
- Celery
- SQL scripts
- Administrative tools
- Other services

---

## Constraints vs Application Validation

Application validation is useful for:

- Friendly error messages
- Request validation
- Early rejection
- API-specific rules

Database constraints are essential for durable invariants.

For example:

```text
Application:
"Email looks valid."

Database:
"Email must be unique."
```

The application cannot reliably enforce uniqueness under concurrency without database participation.

---

## Default Values

A column can have a database default:

```sql
created_at timestamptz NOT NULL DEFAULT now()
```

Defaults are applied when a value is omitted.

They are useful for database-owned metadata such as:

- Creation timestamps
- Generated identifiers
- Status defaults

Be clear about whether the application or database is authoritative for a default.

---

## Views

A view stores a query definition rather than a separate copy of the underlying data.

```sql
CREATE VIEW active_customers AS
SELECT
    id,
    email,
    name
FROM customers
WHERE deleted_at IS NULL;
```

Then:

```sql
SELECT *
FROM active_customers;
```

Views can provide:

- Reusable query logic
- Controlled interfaces
- Abstraction
- Security boundaries in some architectures

They do not automatically cache query results.

---

## Materialized Views

A materialized view stores query results physically.

```sql
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT
    date_trunc('month', created_at) AS month,
    SUM(amount) AS revenue
FROM orders
GROUP BY 1;
```

It must be refreshed:

```sql
REFRESH MATERIALIZED VIEW monthly_revenue;
```

Materialized views can accelerate expensive analytical queries but introduce:

- Refresh cost
- Staleness
- Storage
- Operational complexity

They are often useful for reporting workloads rather than latency-sensitive transactional writes.

---

## SQL Functions

PostgreSQL supports database functions.

Example:

```sql
CREATE FUNCTION order_total(customer_id bigint)
RETURNS numeric
LANGUAGE sql
AS $$
    SELECT COALESCE(SUM(amount), 0)
    FROM orders
    WHERE orders.customer_id = order_total.customer_id;
$$;
```

Functions can centralize database-side logic, but excessive business logic inside stored procedures can make application architecture harder to maintain.

Use them deliberately.

---

## Stored Procedures vs Application Logic

Database-side logic is useful when:

- Data locality matters
- Atomic database operations are required
- The operation is naturally relational
- Database-level interfaces are valuable

Application-side logic is often preferable when:

- Business workflows span external services
- Logic requires complex application libraries
- Domain behavior belongs to a service
- Testing and deployment are easier outside the database

Senior engineers should decide based on boundaries rather than ideology.

---

## Date and Time Functions

PostgreSQL provides extensive date/time support.

Examples:

```sql
SELECT now();
```

Extract a component:

```sql
SELECT
    EXTRACT(YEAR FROM created_at) AS year
FROM orders;
```

Truncate to a reporting period:

```sql
SELECT
    date_trunc('month', created_at) AS month,
    COUNT(*) AS order_count
FROM orders
GROUP BY 1
ORDER BY 1;
```

For indexed operational queries, prefer range predicates when possible:

```sql
WHERE created_at >= $1
  AND created_at < $2
```

---

## String Functions

Common PostgreSQL functions include:

```sql
lower(text)
upper(text)
trim(text)
length(text)
substring(...)
replace(...)
concat(...)
```

Example:

```sql
SELECT
    lower(email) AS normalized_email
FROM customers;
```

If normalization is part of a frequently queried access path, consider storing normalized data or using an expression index where appropriate.

---

## Type Conversion

PostgreSQL supports explicit casts.

```sql
SELECT
    '42'::integer;
```

or:

```sql
SELECT
    CAST('42' AS integer);
```

Implicit and explicit conversions can affect correctness and query planning.

Avoid relying on accidental type conversion in important queries.

---

## Data Types Matter

Choose types based on semantics.

Examples:

| Requirement | Appropriate PostgreSQL type |
|---|---|
| Integer identifier | `bigint` |
| Exact monetary value | `numeric` |
| Timestamp with timezone | `timestamptz` |
| Boolean state | `boolean` |
| Arbitrary text | `text` |
| Structured JSON | `jsonb` |
| Binary data | `bytea` |

Do not store everything as text.

Strong typing improves:

- Correctness
- Constraint enforcement
- Query behavior
- Indexing
- Storage efficiency

---

## `CAST` in Predicates

Consider:

```sql
WHERE customer_id = $1
```

where `$1` is correctly typed.

This is generally preferable to unnecessary casting of indexed columns.

Be cautious with:

```sql
WHERE customer_id::text = $1
```

because transforming the indexed column can change the available access paths unless a matching expression index exists.

---

## SQL Aliases and Ambiguous Columns

Joining tables with common column names requires qualification.

Prefer:

```sql
SELECT
    c.id AS customer_id,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

rather than relying on unqualified:

```sql
SELECT id
```

Clear qualification reduces mistakes as queries become more complex.

---

## Query Readability

Production SQL should be readable enough to review.

Prefer:

```sql
SELECT
    o.id,
    o.customer_id,
    o.total_amount,
    o.created_at
FROM orders AS o
WHERE o.status = 'paid'
  AND o.created_at >= $1
ORDER BY o.created_at DESC, o.id DESC
LIMIT 100;
```

over compressed SQL that hides logic.

Readability matters because SQL often becomes part of:

- Application code
- Migration files
- Reporting systems
- Operational runbooks
- Incident investigations

---

## SQL Comments

Comments can document non-obvious business or performance decisions.

```sql
-- Partial index covers the active-order queue only.
SELECT
    id
FROM orders
WHERE status = 'pending'
ORDER BY created_at
LIMIT 100;
```

Avoid comments that merely restate obvious syntax.

---

## Transactions

A transaction groups operations into a unit of work.

Example:

```sql
BEGIN;

UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = $1
  AND quantity > 0;

INSERT INTO order_items (
    order_id,
    product_id
)
VALUES (
    $2,
    $1
);

COMMIT;
```

If an error occurs before commit, the transaction should be rolled back.

---

## Atomicity

Atomicity means a transaction's changes are committed together or rolled back together.

For example:

```text
Create payment record
+
Update order status
```

If both must represent one database state, they should normally belong to the same transaction when they are within the same database.

---

## Transaction Isolation

Isolation controls how concurrent transactions interact.

PostgreSQL commonly uses:

```text
READ COMMITTED
REPEATABLE READ
SERIALIZABLE
```

The default PostgreSQL isolation level is `READ COMMITTED`.

The correct isolation level depends on business requirements.

Do not answer:

> "SERIALIZABLE is always safest, so use it everywhere."

Higher isolation can increase retries, contention, and workload cost.

---

## Locking

Some operations acquire locks to coordinate concurrent access.

Example:

```sql
SELECT *
FROM inventory
WHERE product_id = $1
FOR UPDATE;
```

This can be useful when application logic must inspect and then modify the same row within a transaction.

Locks should be held for as little time as practical.

---

## Deadlocks

A deadlock occurs when transactions wait on each other indefinitely.

Conceptually:

```text
Transaction A:
locks Row 1
waits for Row 2

Transaction B:
locks Row 2
waits for Row 1
```

PostgreSQL detects deadlocks and aborts one transaction.

Applications should:

- Keep transactions short
- Acquire locks consistently
- Avoid unnecessary locks
- Retry appropriate deadlock failures safely

---

## SQL and Backend APIs

A typical request path is:

```text
Client
  ↓
Nginx / Load Balancer
  ↓
Django / FastAPI
  ↓
ORM / SQL
  ↓
Connection Pool
  ↓
PostgreSQL
  ↓
Result
  ↓
API serialization
  ↓
Client
```

SQL performance therefore affects the complete request path.

A database query that takes longer holds an application connection longer and can increase pool pressure.

---

## Django ORM and SQL Fundamentals

Django ORM operations ultimately generate SQL.

For example:

```python
orders = (
    Order.objects
    .filter(status="paid")
    .order_by("-created_at")
)
```

The backend engineer should understand the resulting SQL concepts:

```text
WHERE status = 'paid'
ORDER BY created_at DESC
```

When a query is unexpectedly slow, inspect the generated SQL and execution plan rather than treating the ORM as a black box.

---

## FastAPI and SQLAlchemy

With FastAPI and SQLAlchemy, the same principle applies.

Application code might express:

```python
stmt = (
    select(Order)
    .where(Order.status == "paid")
    .order_by(Order.created_at.desc())
)
```

SQLAlchemy ultimately generates SQL executed by PostgreSQL.

The database remains responsible for:

- Planning
- Index selection
- Joins
- Aggregation
- Locking
- Execution

---

## SQL Injection

Never construct SQL by concatenating untrusted values.

Unsafe:

```python
query = f"""
SELECT *
FROM users
WHERE email = '{email}'
"""
```

Use parameter binding:

```python
cursor.execute(
    """
    SELECT *
    FROM users
    WHERE email = %s
    """,
    (email,),
)
```

Parameterized queries separate SQL structure from values.

---

## Dynamic SQL

Parameterized values do not automatically make SQL identifiers safe.

For example:

```text
ORDER BY user_input
```

cannot simply be treated like an ordinary value.

For dynamic identifiers:

1. Validate against an allowlist.
2. Map application values to known SQL identifiers.
3. Use database-driver identifier APIs where available.

Never assume arbitrary user-provided SQL structure is safe.

---

## SQL Injection and ORMs

Using an ORM does not guarantee safety if developers bypass its parameterization mechanisms.

Unsafe raw SQL patterns can still introduce SQL injection.

For example, avoid constructing SQL strings directly from request parameters.

The correct rule is:

> Use the ORM's parameter binding or the database driver's parameter binding for values.

---

## Performance Fundamentals

A query's performance depends on more than SQL text.

Important factors include:

- Table size
- Indexes
- Statistics
- Selectivity
- Join cardinality
- Sorts
- Aggregations
- Memory
- CPU
- I/O
- Lock waits
- Query frequency
- Concurrency
- Result-set size

A query that is fast on 1,000 rows may behave very differently on 100 million rows.

---

## Sequential Scan vs Index Scan

A sequential scan reads table pages in sequence.

An index scan follows an index to locate qualifying rows.

Neither is universally better.

For a query returning a large fraction of a table, a sequential scan may be cheaper.

For a highly selective lookup, an index may be substantially better.

Use:

```sql
EXPLAIN
SELECT *
FROM orders
WHERE customer_id = $1;
```

to understand the planner's decision.

---

## Statistics

PostgreSQL maintains statistics about table data.

The optimizer uses them to estimate:

- Row counts
- Selectivity
- Data distribution

Poor statistics can lead to poor execution plans.

After major data changes, normal `ANALYZE`/autovacuum behavior should be considered when investigating unexpected plans.

---

## Indexes and Write Cost

Indexes improve some reads but introduce write overhead.

Every relevant insert/update/delete may require index maintenance.

Too many indexes can increase:

- Storage
- WAL
- Write latency
- Vacuum work
- Cache pressure

The goal is not:

> "Create an index for every query."

The goal is:

> "Create indexes that provide measurable value for important access patterns."

---

## Query Frequency

Consider:

```text
Query A:
500 ms × 10 executions/hour

Query B:
10 ms × 100,000 executions/hour
```

Query B may have a much larger system-wide impact.

Production performance should therefore consider:

```text
query cost
×
frequency
×
concurrency
```

Tools such as `pg_stat_statements` can help identify expensive workloads.

---

## Large Result Sets

Returning unnecessary rows can hurt:

- Database CPU
- Database memory
- Network bandwidth
- Application memory
- JSON serialization
- API latency

Prefer:

```sql
SELECT
    id,
    status
FROM orders
WHERE customer_id = $1;
```

when those are the only fields required.

Use pagination for large collections.

---

## Common Fundamentals Interview Traps

### "Is `NULL` equal to `NULL`?"

No. SQL uses three-valued logic.

Use:

```sql
IS NULL
```

for null checks.

### "Does `DISTINCT` fix duplicate rows?"

It can remove duplicate output rows, but it does not necessarily fix an incorrect join.

### "Is `UNION` faster than `UNION ALL`?"

Usually no. `UNION` must eliminate duplicates; `UNION ALL` does not.

### "Is an index always faster than a sequential scan?"

No. The optimizer chooses based on estimated cost and workload.

### "Is `LIMIT 1` always efficient?"

No. The database may still perform expensive filtering, joining, sorting, or aggregation before producing the result.

### "Is `NOT IN` equivalent to `NOT EXISTS`?"

Not in the presence of `NULL` semantics. `NOT EXISTS` is often safer for anti-existence logic.

### "Does an ORM mean I don't need SQL?"

No. ORM-generated SQL still executes inside the database.

---

## Common Beginner Mistakes

### Using `SELECT *` Everywhere

Problem:

- Transfers unnecessary columns
- Creates fragile application contracts
- Can increase memory and serialization cost

Prefer explicit projections.

### Forgetting `NULL`

Problem:

```sql
WHERE column = NULL
```

returns no rows as intended.

Use:

```sql
WHERE column IS NULL
```

### Using `DISTINCT` to Hide Join Errors

Problem:

The query may still process a large number of unnecessary rows.

Fix the relationship or query shape first.

### Filtering After an Unnecessary Join

Problem:

Joining tables before deciding whether you only need existence can create row multiplication.

Consider `EXISTS`.

### Ignoring Deterministic Ordering

Problem:

Pagination can return inconsistent pages when rows have equal ordering values.

Use a stable tie-breaker.

### Building One Giant Transaction

Problem:

Large transactions can increase:

- Lock duration
- WAL
- Bloat
- Replication lag
- Recovery time

Batch large operations where appropriate.

---

## Production Pitfalls

### Application Validation Without Constraints

Two concurrent requests can both pass:

```text
"Does this email exist?"
```

and then both attempt to insert.

Use a database uniqueness constraint.

### Unbounded Query Results

An API endpoint that returns millions of rows can exhaust application memory.

Use:

- Pagination
- Streaming where appropriate
- Async exports
- Workload isolation

### SQL Without Timeouts

A query waiting indefinitely can consume a connection and contribute to cascading failure.

Use appropriate database and application timeout policies.

### Excessive Connection Concurrency

More connections do not necessarily mean more throughput.

Connection pools should be sized against database capacity and total application concurrency.

---

## Interview Problem-Solving Framework

When given an SQL problem:

### Clarify the Result

Ask:

```text
What should one row represent?
```

Examples:

```text
one customer
one order
one customer per month
one latest order per customer
```

### Identify Relationships

Determine:

```text
one-to-one
one-to-many
many-to-many
```

### Build the Simplest Correct Query

Start with:

```text
FROM
JOIN
WHERE
```

then add:

```text
GROUP BY
HAVING
SELECT
ORDER BY
LIMIT
```

as required.

### Validate Edge Cases

Check:

- `NULL`
- Duplicate values
- Empty result
- Missing relationship
- Ties
- Multiple matching rows
- Boundary timestamps

### Consider Scale

Ask:

- How many rows?
- What indexes exist?
- How frequently does this run?
- Could the result become large?
- Is pagination needed?
- Is the query OLTP or analytical?

### Inspect the Plan

For important queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
...
```

Validate assumptions against actual behavior.

---

## Practical Interview Question Set

### What is the difference between `WHERE` and `HAVING`?

`WHERE` filters rows before aggregation.

`HAVING` filters groups after aggregation.

---

### What is the difference between `INNER JOIN` and `LEFT JOIN`?

`INNER JOIN` returns only matching combinations.

`LEFT JOIN` preserves every row from the left relation and supplies `NULL`s when no matching right-side row exists.

---

### What is the difference between `COUNT(*)` and `COUNT(column)`?

`COUNT(*)` counts rows.

`COUNT(column)` counts non-`NULL` values in that column.

---

### What is the difference between `UNION` and `UNION ALL`?

`UNION` removes duplicates.

`UNION ALL` preserves duplicates and usually avoids the additional deduplication work.

---

### When would you use `EXISTS`?

Use `EXISTS` when the requirement is whether at least one matching row exists.

Example:

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

---

### Why can `NOT IN` behave unexpectedly?

Because `NULL` participates in SQL's three-valued logic.

For anti-existence checks, `NOT EXISTS` is often easier to reason about.

---

### What is the difference between `DELETE` and `TRUNCATE`?

`DELETE` removes rows and can target a subset using a predicate.

`TRUNCATE` removes all rows from a table with different locking and trigger/foreign-key semantics and is intended for operations where row-by-row deletion behavior is unnecessary.

---

### Why should you use constraints?

Constraints enforce data integrity at the database boundary.

They protect invariants even when multiple applications, workers, scripts, or concurrent transactions interact with the database.

---

### What is a foreign key?

A foreign key enforces a relationship between rows in two tables.

For example:

```text
orders.customer_id
        ↓
customers.id
```

It prevents invalid references unless the constraint is explicitly configured to permit the relevant behavior.

---

### What is normalization?

Normalization organizes relational data to reduce unnecessary duplication and update anomalies.

Typical normalized transactional schemas separate entities such as:

```text
customers
orders
order_items
products
```

Normalization improves integrity but can require joins.

Denormalization can be appropriate when measured workload requirements justify duplicating derived data.

---

### What is denormalization?

Denormalization intentionally duplicates or precomputes data to improve particular access patterns.

Examples include:

- Cached aggregates
- Read models
- Materialized views
- Duplicated lookup attributes

The trade-off is increased write complexity and consistency management.

---

### What is a view?

A view is a named query definition.

It provides a reusable database-level interface without necessarily storing a separate result set.

---

### What is a materialized view?

A materialized view stores the result physically and must be refreshed.

It can accelerate expensive read workloads at the cost of refresh complexity and potentially stale data.

---

### What is a window function?

A window function computes values across related rows without collapsing them into grouped output.

Example:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

---

### When should you use `GROUP BY` instead?

Use `GROUP BY` when the result should collapse into groups.

Use window functions when you need group-level calculations while retaining individual rows.

---

### What is a CTE?

A Common Table Expression gives a query expression a name using `WITH`.

It improves readability and supports advanced patterns such as recursive queries.

It should not automatically be considered a performance optimization.

---

### What is a transaction?

A transaction groups database operations into an atomic unit with defined isolation and durability behavior.

Use transactions when multiple operations must preserve a consistent business state together.

---

### What is an index?

An index provides an alternative access path to table data.

It can significantly accelerate selective reads but adds storage and write-maintenance cost.

---

### Why might PostgreSQL ignore an index?

Possible reasons include:

- Low selectivity
- Small table size
- Poor statistics
- Mismatched index
- Type conversion
- Query shape
- Estimated cost favoring sequential access

The correct response is to inspect the execution plan.

---

## Senior-Level Reasoning

At senior level, SQL questions often become architecture questions.

Suppose an interviewer asks:

> "How would you optimize this query?"

Do not immediately answer with an index.

Reason through:

```text
Correctness
   ↓
Result cardinality
   ↓
Query shape
   ↓
Execution plan
   ↓
Indexes/statistics
   ↓
Query frequency
   ↓
Concurrency
   ↓
Connection pool
   ↓
Caching / replicas
   ↓
Workload architecture
```

Suppose the query is fast in isolation but the API still has high latency.

Potential causes include:

```text
N+1 queries
connection pool exhaustion
lock contention
network latency
large result serialization
replica lag
retry storms
```

This is the difference between SQL syntax knowledge and production database engineering.

---

## SQL Fundamentals and System Design

SQL decisions affect architecture.

For example:

```text
High read volume
      ↓
Indexes
      ↓
Read replicas
      ↓
Redis cache
      ↓
Read model / OLAP
```

For high write volume:

```text
Write contention
      ↓
Atomic SQL
      ↓
Batching
      ↓
Partitioning
      ↓
Queue-based serialization
      ↓
Sharding when justified
```

The database remains part of the overall backend architecture.

---

## Production SQL Decision Framework

When choosing a SQL technique, ask:

| Question | Example |
|---|---|
| What is the required result? | One row per customer |
| What is the relationship? | Customer → orders |
| Is existence enough? | Use `EXISTS` |
| Do rows need to collapse? | Use `GROUP BY` |
| Must rows remain visible? | Consider window functions |
| Is the data large? | Consider pagination/indexes |
| Is the operation concurrent? | Consider transactions/locking |
| Is the query frequent? | Measure aggregate workload |
| Is it read-heavy? | Consider caching/replicas |
| Is it analytical? | Consider OLAP isolation |
| Is it user-controlled? | Parameterize and validate |
| Is the invariant critical? | Use database constraints |

---

## SQL Fundamentals Checklist

Before considering your SQL fundamentals interview-ready, you should be comfortable explaining:

### Query Construction

- [ ] `SELECT`
- [ ] `WHERE`
- [ ] `ORDER BY`
- [ ] `LIMIT`
- [ ] `OFFSET`
- [ ] `DISTINCT`
- [ ] `CASE`
- [ ] `COALESCE`

### Relationships

- [ ] Inner joins
- [ ] Left joins
- [ ] Join cardinality
- [ ] One-to-many relationships
- [ ] Many-to-many relationships
- [ ] `EXISTS`
- [ ] `NOT EXISTS`

### Aggregation

- [ ] `COUNT(*)`
- [ ] `COUNT(column)`
- [ ] `COUNT(DISTINCT ...)`
- [ ] `SUM`
- [ ] `AVG`
- [ ] `GROUP BY`
- [ ] `HAVING`
- [ ] Conditional aggregation

### Advanced Querying

- [ ] Window functions
- [ ] Ranking
- [ ] Subqueries
- [ ] Correlated subqueries
- [ ] CTEs
- [ ] Recursive CTEs
- [ ] `UNION`
- [ ] `UNION ALL`
- [ ] `INTERSECT`
- [ ] `EXCEPT`

### Data Modification

- [ ] `INSERT`
- [ ] Multi-row insert
- [ ] `UPDATE`
- [ ] `DELETE`
- [ ] `TRUNCATE`
- [ ] Upsert
- [ ] `RETURNING`
- [ ] `MERGE`

### Data Integrity

- [ ] Primary keys
- [ ] Foreign keys
- [ ] Unique constraints
- [ ] `NOT NULL`
- [ ] `CHECK`
- [ ] Defaults
- [ ] Referential integrity

### Production Fundamentals

- [ ] Transactions
- [ ] Isolation
- [ ] Locks
- [ ] Deadlocks
- [ ] Indexes
- [ ] Execution plans
- [ ] Pagination
- [ ] Connection pools
- [ ] SQL injection
- [ ] ORM-generated SQL

---

## Key Takeaways

- **SQL fundamentals are about relational reasoning:** understand result grain, join cardinality, `NULL` semantics, aggregation, and set behavior rather than memorizing syntax.
- **Database constraints and transactions protect correctness:** application validation is useful, but critical invariants must survive concurrency and alternate access paths.
- **Query shape matters at scale:** indexes, pagination, projections, `EXISTS`, aggregation, and window functions should be chosen according to actual access patterns and result cardinality.
- **SQL knowledge extends beyond the query:** ORM behavior, connection pools, locks, replicas, caching, concurrency, and workload frequency all influence production performance.
- **Strong interview answers explain trade-offs:** distinguish correctness from optimization, validate assumptions with execution plans, and connect SQL decisions to real backend architecture.