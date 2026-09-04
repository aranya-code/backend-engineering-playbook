# 01- Core SQL Interview Questions

## Overview

Core SQL interviews evaluate much more than whether a candidate remembers SQL syntax. At intermediate and senior backend levels, interviewers typically test whether you can reason about:

- Result correctness and expected row cardinality
- Joins and relationship modeling
- `NULL` semantics
- Aggregation and window functions
- Subqueries and CTEs
- `INSERT`, `UPDATE`, `DELETE`, and upsert behavior
- Constraints and data integrity
- Indexes and execution plans
- Transactions and concurrency
- Pagination and large datasets
- SQL injection and parameterized queries
- ORM-generated SQL
- Production performance and reliability

For senior backend engineers, the strongest answers connect SQL syntax to database behavior. A query is not isolated code; it executes inside a database engine with indexes, statistics, transactions, locks, memory, connection pools, replication, and workload constraints.

A useful interview mindset is:

> **First prove the query is correct. Then explain why it is correct. Then optimize it based on evidence.**

---

## SQL Logical Processing Order

Although SQL is written using a particular syntax order, the database conceptually evaluates many queries in a different logical order.

A simplified model is:

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
DISTINCT
  ↓
ORDER BY
  ↓
LIMIT / OFFSET
```

For example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 5
ORDER BY order_count DESC
LIMIT 20;
```

The important reasoning is:

1. Start with rows from `orders`.
2. Filter completed orders.
3. Group remaining rows by customer.
4. Keep groups containing at least five rows.
5. Produce the selected columns.
6. Order the result.
7. Return the first 20 rows.

Understanding this order prevents common mistakes involving aliases, aggregates, joins, and filtering.

---

## `WHERE` vs `HAVING`

### `WHERE`

`WHERE` filters individual rows before grouping.

```sql
SELECT customer_id, COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

### `HAVING`

`HAVING` filters groups after aggregation.

```sql
SELECT customer_id, COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) >= 5;
```

### Interview question

**Can you use an aggregate function in `WHERE`?**

Generally, no.

This is invalid:

```sql
SELECT customer_id, COUNT(*)
FROM orders
WHERE COUNT(*) > 5
GROUP BY customer_id;
```

Use `HAVING` instead:

```sql
SELECT customer_id, COUNT(*) AS order_count
FROM orders
GROUP BY customer_id
HAVING COUNT(*) > 5;
```

### Senior-level consideration

Do not mechanically move conditions between `WHERE` and `HAVING`.

Filtering rows before aggregation can dramatically reduce the amount of data that must be grouped.

Prefer:

```sql
SELECT customer_id, COUNT(*)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

over unnecessarily grouping all rows and filtering afterward.

---

## `NULL` Semantics

`NULL` represents an unknown, missing, or inapplicable value. It is not equivalent to:

- `0`
- `''`
- `FALSE`
- `'NULL'`

The most important rule is that comparisons involving `NULL` do not behave like ordinary equality comparisons.

Incorrect:

```sql
WHERE deleted_at = NULL
```

Correct:

```sql
WHERE deleted_at IS NULL
```

And:

```sql
WHERE deleted_at IS NOT NULL
```

### Three-valued logic

SQL predicates can evaluate to:

- `TRUE`
- `FALSE`
- `UNKNOWN`

For example:

```sql
NULL = 10
```

does not evaluate to `FALSE`; it evaluates to `UNKNOWN`.

A `WHERE` clause keeps only rows for which the predicate evaluates to `TRUE`.

### `NOT IN` trap

Consider:

```sql
SELECT *
FROM customers
WHERE id NOT IN (
    SELECT customer_id
    FROM orders
);
```

If the subquery contains `NULL`, the result can behave unexpectedly because of SQL's three-valued logic.

When expressing anti-existence logic, `NOT EXISTS` is often safer:

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

### `COALESCE`

`COALESCE` returns the first non-`NULL` expression.

```sql
SELECT
    customer_id,
    COALESCE(discount, 0) AS discount
FROM orders;
```

Do not use `COALESCE` blindly in predicates if it prevents an otherwise useful index access path.

---

## `DISTINCT`

`DISTINCT` removes duplicate result rows based on the selected columns.

```sql
SELECT DISTINCT customer_id
FROM orders;
```

A common interview mistake is using `DISTINCT` to hide an incorrect join.

Suppose a customer has multiple orders:

```sql
SELECT DISTINCT c.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

This may return the desired customer list, but the real question is whether the join was necessary.

Sometimes this is clearer and more efficient:

```sql
SELECT c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

### Senior-level rule

`DISTINCT` should represent a real requirement, not serve as a generic duplicate-removal mechanism after an incorrectly modeled join.

---

## Joins

Joins combine rows from multiple relations according to a relationship.

Common join types include:

| Join | Typical meaning |
|---|---|
| `INNER JOIN` | Only matching rows from both sides |
| `LEFT JOIN` | All left rows plus matching right rows |
| `RIGHT JOIN` | All right rows plus matching left rows |
| `FULL OUTER JOIN` | All rows from both sides |
| `CROSS JOIN` | Cartesian product |
| `LATERAL` | Right-side expression can reference preceding `FROM` rows |

### Inner join

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Customers without orders disappear from the result.

### Left join

```sql
SELECT
    c.id,
    c.email,
    o.id AS order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

Customers without orders remain, with `NULL` values for the order columns.

---

## Join Cardinality

Understanding cardinality is one of the most important SQL interview skills.

Suppose:

```text
customers
1 customer → many orders
```

Then:

```sql
customers
JOIN orders
```

can produce multiple rows per customer.

For example:

```text
Customer 1 → Order 101
Customer 1 → Order 102
Customer 1 → Order 103
```

The customer row has effectively been multiplied.

### Common interview problem

> "I joined two tables and suddenly received duplicate users. Why?"

Usually the rows are not duplicates.

The join may correctly represent a one-to-many or many-to-many relationship.

The correct solution depends on the desired result grain.

Ask:

> **What should one output row represent?**

Examples:

- One row per customer
- One row per order
- One row per customer/month
- One row per product
- One row per customer with their latest order

Only after defining the result grain should you choose the SQL structure.

---

## Finding Customers With Orders

A common requirement is:

> Return customers who have at least one order.

Using a join:

```sql
SELECT DISTINCT c.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id;
```

Using `EXISTS`:

```sql
SELECT c.id
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The second query communicates the intent more directly: existence rather than row combination.

---

## `LEFT JOIN` and Filtering Mistakes

Consider:

```sql
SELECT c.id, o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.status = 'completed';
```

The `WHERE` condition eliminates rows where `o` is `NULL`, effectively making the query behave like an inner join for this condition.

If the requirement is:

> Return all customers, but only attach completed orders.

Move the predicate into the join:

```sql
SELECT c.id, o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
   AND o.status = 'completed';
```

This distinction is frequently tested in interviews.

---

## Aggregation

Aggregate functions operate over sets of rows.

Common functions:

```sql
COUNT(*)
COUNT(column)
SUM(column)
AVG(column)
MIN(column)
MAX(column)
```

Example:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id;
```

### `COUNT(*)` vs `COUNT(column)`

`COUNT(*)` counts rows.

```sql
COUNT(*)
```

`COUNT(column)` counts non-`NULL` values.

For:

```text
amount
------
100
200
NULL
```

the results differ:

```sql
COUNT(*)       -- 3
COUNT(amount)  -- 2
```

This is a common interview question.

---

## Conditional Aggregation

Conditional aggregation is extremely useful in production reporting queries.

```sql
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,
    COUNT(*) FILTER (
        WHERE status = 'cancelled'
    ) AS cancelled_orders
FROM orders
GROUP BY customer_id;
```

Another portable pattern is:

```sql
SELECT
    customer_id,
    SUM(
        CASE
            WHEN status = 'completed' THEN 1
            ELSE 0
        END
    ) AS completed_orders
FROM orders
GROUP BY customer_id;
```

---

## Grouping by Multiple Columns

Grouping by:

```sql
GROUP BY customer_id, status
```

produces one group for every unique combination.

For example:

```text
customer_id | status
------------+----------
1           | completed
1           | pending
2           | completed
```

The result grain is therefore:

> one row per customer and status combination.

Senior interviewers often care more about whether you can state the resulting grain than whether you remember the syntax.

---

## Window Functions

Window functions calculate values across related rows without collapsing those rows into one row per group.

Example:

```sql
SELECT
    customer_id,
    id AS order_id,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

Every order remains in the result.

Compare this with:

```sql
SELECT
    customer_id,
    SUM(total_amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

The `GROUP BY` query produces one row per customer.

The window query produces one row per order while also exposing the customer total.

---

## `ROW_NUMBER`

A very common interview problem is:

> Find the latest order for each customer.

One robust approach is:

```sql
SELECT
    customer_id,
    id,
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

The secondary `id` ordering makes the result deterministic when timestamps are equal.

### PostgreSQL-specific alternative

PostgreSQL supports `DISTINCT ON`:

```sql
SELECT DISTINCT ON (customer_id)
    customer_id,
    id,
    created_at
FROM orders
ORDER BY customer_id, created_at DESC, id DESC;
```

The syntax is concise but PostgreSQL-specific.

---

## Ranking Functions

Common ranking functions include:

```sql
ROW_NUMBER()
RANK()
DENSE_RANK()
```

Consider values:

```text
100
100
90
```

Their behavior differs:

| Function | Results |
|---|---|
| `ROW_NUMBER()` | `1, 2, 3` |
| `RANK()` | `1, 1, 3` |
| `DENSE_RANK()` | `1, 1, 2` |

Interview questions often test whether you understand the difference between ranking with and without gaps.

---

## Subqueries

A subquery is a query nested inside another query.

Common forms include:

- Scalar subqueries
- `IN`
- `EXISTS`
- Correlated subqueries
- Derived tables

### Scalar subquery

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

The inner query depends on the current outer row, making it correlated.

### `EXISTS`

Use `EXISTS` when the requirement is primarily existence.

```sql
SELECT c.*
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

The database optimizer may transform logically equivalent formulations, so do not claim that `EXISTS` is universally faster than joins. Choose based on semantics and validate performance with an execution plan.

---

## CTEs

A Common Table Expression provides a named query expression.

```sql
WITH completed_orders AS (
    SELECT
        id,
        customer_id,
        total_amount
    FROM orders
    WHERE status = 'completed'
)
SELECT
    customer_id,
    SUM(total_amount) AS revenue
FROM completed_orders
GROUP BY customer_id;
```

CTEs can improve readability and are also useful for recursive queries and complex data transformations.

### Important PostgreSQL consideration

Modern PostgreSQL can inline eligible CTEs rather than treating every CTE as an optimization barrier.

If materialization is explicitly required:

```sql
WITH completed_orders AS MATERIALIZED (
    SELECT *
    FROM orders
    WHERE status = 'completed'
)
SELECT ...
```

Do not assume that every CTE automatically improves performance.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

when performance matters.

---

## `INSERT`

Basic insert:

```sql
INSERT INTO customers (
    email,
    name
)
VALUES (
    'customer@example.com',
    'Example Customer'
);
```

Explicit column lists are preferable to relying on table column order.

### Returning inserted values

PostgreSQL supports:

```sql
INSERT INTO customers (
    email,
    name
)
VALUES (
    'customer@example.com',
    'Example Customer'
)
RETURNING id, created_at;
```

This avoids a separate query to retrieve generated values.

---

## `UPDATE`

Example:

```sql
UPDATE orders
SET status = 'completed'
WHERE id = $1;
```

The `WHERE` clause is critical.

This:

```sql
UPDATE orders
SET status = 'completed';
```

updates every row.

### Atomic updates

Instead of:

```text
SELECT balance
UPDATE balance
```

perform arithmetic inside the database:

```sql
UPDATE accounts
SET balance = balance - $1
WHERE id = $2
  AND balance >= $1
RETURNING balance;
```

This reduces application-side race conditions because the condition and modification happen as one database operation.

---

## `DELETE`

Example:

```sql
DELETE FROM sessions
WHERE expires_at < now();
```

Large deletes can create substantial:

- WAL
- dead tuples
- vacuum work
- lock pressure
- replication traffic

For very large datasets, batch deletion or partition lifecycle operations may be safer.

For example, use an indexed key or time boundary rather than attempting one enormous transaction.

---

## Upsert

PostgreSQL supports:

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

The unique constraint is important.

The database must have a matching uniqueness definition for the conflict target.

### Interview question

**Why not implement upsert using `SELECT` followed by `INSERT`?**

Because concurrent requests can both observe that the row does not exist and then race to insert it.

A database-enforced unique constraint plus `ON CONFLICT` provides the correct concurrency primitive.

---

## Constraints

Constraints enforce data integrity at the database boundary.

Common constraints include:

| Constraint | Purpose |
|---|---|
| `PRIMARY KEY` | Identifies a row uniquely |
| `FOREIGN KEY` | Enforces relationship integrity |
| `UNIQUE` | Prevents duplicate values/combinations |
| `NOT NULL` | Requires a value |
| `CHECK` | Enforces a predicate |

Example:

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    total_amount numeric(12, 2) NOT NULL CHECK (total_amount >= 0),
    external_id text UNIQUE
);
```

### Senior-level principle

Application validation improves user experience.

Database constraints protect correctness.

Both are useful, but application validation should not be the only protection for critical invariants.

---

## Primary Keys

A primary key provides row identity and uniqueness.

A typical PostgreSQL design is:

```sql
id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

The choice between integer-based and UUID-based identifiers depends on system requirements.

Consider:

- Index size
- Generation strategy
- Distributed ID generation
- External exposure
- Ordering characteristics
- Migration requirements
- Sharding requirements

Do not claim that UUIDs are always better or that integer IDs are always better.

---

## Foreign Keys

Foreign keys enforce referential integrity.

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL
        REFERENCES customers(id)
);
```

A foreign key prevents an order from referencing a nonexistent customer.

### Performance consideration

Foreign keys can introduce work during inserts, updates, and deletes.

Indexing the referencing column is often important:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

PostgreSQL does not automatically create an index on the referencing side merely because a foreign key exists.

---

## Unique Constraints

Uniqueness can represent a business invariant.

For example:

```sql
CREATE UNIQUE INDEX idx_users_email
ON users (lower(email));
```

This can enforce case-insensitive uniqueness if that matches the application's requirements.

For soft-deleted resources, a partial unique index can be useful:

```sql
CREATE UNIQUE INDEX idx_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

Now only active rows must have unique emails.

---

## Indexes

Indexes provide alternative access paths to table data.

The most common PostgreSQL index type is B-tree.

Example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

This may help queries such as:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

### Important interview trap

An index existing does not guarantee that PostgreSQL will use it.

The optimizer considers:

- Estimated row count
- Selectivity
- Table size
- Statistics
- Cost parameters
- Cache state
- Query predicates
- Ordering
- Available access paths

A sequential scan may be the correct plan.

---

## Composite Indexes

For:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

the order of columns matters.

A useful mental model for B-tree indexes is that PostgreSQL can efficiently exploit the leading portion of the index depending on the predicate and ordering.

Do not treat:

```text
(a, b, c)
```

as equivalent to:

```text
(b, a, c)
```

Index design should follow actual query patterns.

---

## Covering Indexes

PostgreSQL supports included columns:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id)
INCLUDE (status, created_at);
```

Included columns can allow index-only scans in suitable circumstances.

They do not replace careful index design.

Wider indexes increase:

- Storage
- Write cost
- WAL
- Maintenance work
- Cache pressure

---

## Partial Indexes

Partial indexes index only rows satisfying a predicate.

```sql
CREATE INDEX idx_orders_pending
ON orders (created_at)
WHERE status = 'pending';
```

This can be valuable when the application frequently queries a relatively small hot subset.

For example:

```sql
SELECT id
FROM orders
WHERE status = 'pending'
ORDER BY created_at
LIMIT 100;
```

The query predicate must be compatible with the index predicate for the planner to use it effectively.

---

## Functional and Expression Indexes

If queries normalize a value, an expression index can match that access pattern.

```sql
CREATE INDEX idx_users_lower_email
ON users (lower(email));
```

Then:

```sql
SELECT id
FROM users
WHERE lower(email) = lower($1);
```

can use the expression index.

Do not create expression indexes without examining actual workload and write/maintenance cost.

---

## Query Performance

A senior SQL interview should distinguish between:

```text
Correctness
    ↓
Query shape
    ↓
Execution plan
    ↓
Resource consumption
    ↓
Concurrency
    ↓
System-wide impact
```

A query that executes in 20 ms once may still be a production problem if it runs 50,000 times per minute.

Conversely, a 500 ms analytical query may be acceptable if it runs rarely and is isolated from transactional workloads.

---

## `EXPLAIN`

Use `EXPLAIN` to inspect the optimizer's selected plan.

```sql
EXPLAIN
SELECT
    id,
    customer_id,
    total_amount
FROM orders
WHERE customer_id = 42;
```

Important fields include:

- Scan type
- Estimated rows
- Estimated cost
- Join strategy
- Sort operations
- Aggregate operations
- Parallel execution

---

## `EXPLAIN ANALYZE`

`EXPLAIN ANALYZE` actually executes the query.

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    customer_id,
    total_amount
FROM orders
WHERE customer_id = 42;
```

It provides actual:

- Execution time
- Actual rows
- Loop counts
- Buffer activity
- Planning information

### Production warning

`EXPLAIN ANALYZE` executes the statement.

For `UPDATE`, `DELETE`, or other mutating statements, use an appropriate transaction strategy when testing so you do not unintentionally modify production data.

---

## Estimated Rows vs Actual Rows

Suppose the plan says:

```text
rows=100
```

but execution produces:

```text
actual rows=500000
```

The optimizer's cardinality estimate is significantly wrong.

This can cause poor decisions involving:

- Join order
- Nested loops
- Hash joins
- Sorts
- Parallelism
- Index vs sequential scans

Possible causes include:

- Stale statistics
- Data skew
- Correlated columns
- Complex predicates
- Parameter sensitivity

The solution is not automatically "add an index."

---

## Join Algorithms

PostgreSQL can use several join strategies.

### Nested loop

Conceptually:

```text
for each row from outer relation:
    find matching rows in inner relation
```

Very effective when the outer relation is small and the inner relation can be accessed efficiently.

### Hash join

Conceptually:

```text
build hash table from one input
probe hash table with the other input
```

Often useful for large equality joins.

### Merge join

Conceptually:

```text
walk through two sorted inputs together
```

Useful when inputs are already appropriately ordered or can be sorted efficiently.

### Interview trap

Do not memorize:

> "Nested loops are bad."

They are not.

The correct join algorithm depends on:

- Input cardinality
- Selectivity
- Available indexes
- Ordering
- Memory
- Cost estimates

---

## Pagination

### Offset pagination

```sql
SELECT id, created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50 OFFSET 10000;
```

Simple and useful for many applications, but deep offsets can require the database to process and discard many rows.

### Keyset pagination

```sql
SELECT id, created_at
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

This works well for large datasets when the ordering columns are indexed appropriately.

### Deterministic ordering

Avoid:

```sql
ORDER BY created_at DESC
```

alone when timestamps can be equal.

Prefer:

```sql
ORDER BY created_at DESC, id DESC
```

when `id` provides a deterministic tie-breaker.

---

## `LIMIT 1` Does Not Fix a Bad Query

This query:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
LIMIT 1;
```

may be efficient if the database can find the first qualifying row quickly.

But:

```sql
SELECT *
FROM orders
JOIN ...
WHERE ...
LIMIT 1;
```

does not automatically mean the database performs minimal work.

The optimizer still has to produce a valid plan, and joins or filters may require substantial processing.

`LIMIT` is not a universal performance solution.

---

## N+1 Queries

A classic backend problem is:

```python
customers = Customer.objects.all()

for customer in customers:
    print(customer.orders.count())
```

Depending on the ORM usage, this can produce:

```text
1 query for customers
+
N queries for orders
```

For a large result set, this becomes expensive.

Django can often address relationship fetching with:

```python
customers = Customer.objects.prefetch_related("orders")
```

For foreign-key relationships:

```python
orders = Order.objects.select_related("customer")
```

The correct choice depends on relationship type and access pattern.

### Senior-level consideration

Do not optimize merely for query count.

A single enormous query can be worse than several small queries if it causes:

- Large joins
- Excessive row multiplication
- High memory usage
- Large result sets
- Lock contention

Measure both query count and query cost.

---

## ORM and SQL

Django ORM, SQLAlchemy, and similar tools do not eliminate SQL.

They generate SQL that is ultimately processed by the database engine.

A senior backend engineer should be able to move between:

```text
Python code
    ↓
ORM expression
    ↓
Generated SQL
    ↓
Execution plan
    ↓
Database behavior
```

For example, a Django query should be inspected when performance is unexpected:

```python
queryset = (
    Order.objects
    .filter(status="completed")
    .select_related("customer")
)
```

The important question is not:

> "Is Django ORM fast?"

The useful question is:

> "What SQL does this generate, how often does it execute, and what plan does PostgreSQL choose?"

---

## Raw SQL in Backend Applications

Raw SQL is appropriate when:

- ORM expressiveness becomes awkward
- A specialized query is required
- PostgreSQL-specific features are valuable
- Complex reporting logic is easier to express directly
- Performance needs to be measured at SQL level

Always parameterize values.

For example with a DB-API style interface:

```python
cursor.execute(
    """
    SELECT id, email
    FROM users
    WHERE email = %s
    """,
    (email,),
)
```

Do not construct SQL using string interpolation:

```python
query = f"SELECT * FROM users WHERE email = '{email}'"
```

---

## SQL Injection

SQL injection occurs when untrusted input changes the structure or meaning of SQL.

Unsafe:

```python
query = f"""
SELECT *
FROM users
WHERE email = '{email}'
"""
```

Safe value binding:

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

### Important interview distinction

Parameterized queries protect SQL **values**.

They do not automatically make arbitrary SQL structure safe.

For example, identifiers such as:

```text
table name
column name
ORDER BY column
sort direction
operator
```

may require allowlisting or safe identifier APIs.

---

## Dynamic `ORDER BY`

This is dangerous:

```python
query = f"""
SELECT *
FROM users
ORDER BY {sort_column}
"""
```

Instead, map allowed application values to known SQL fragments.

For example:

```python
allowed_sort_columns = {
    "created": "created_at",
    "email": "email",
    "name": "name",
}

sort_sql = allowed_sort_columns.get(sort_key)
if sort_sql is None:
    raise ValueError("Invalid sort field")
```

The application should never treat arbitrary user input as a SQL identifier.

---

## Transactions

A transaction groups database operations into an atomic unit.

Typical properties are described using ACID:

| Property | Meaning |
|---|---|
| Atomicity | Transaction changes commit together or roll back |
| Consistency | Constraints/invariants remain valid |
| Isolation | Concurrent transactions have controlled visibility/interactions |
| Durability | Committed data survives appropriate failures |

A backend request might use:

```text
BEGIN
  ↓
validate/write order
  ↓
update inventory
  ↓
insert payment record
  ↓
COMMIT
```

If a failure occurs before commit, the transaction can be rolled back.

---

## Transaction Boundaries

A transaction should generally be:

- Explicit
- Short
- Focused
- Aligned with a business invariant

Avoid holding database transactions open while performing unrelated external operations:

```text
BEGIN
  ↓
database update
  ↓
HTTP request to external service
  ↓
wait
  ↓
COMMIT
```

This can hold locks and database connections unnecessarily.

A common production architecture is to use a transactional outbox when database changes need to trigger reliable asynchronous events.

```text
Database Transaction
      │
      ├── business state
      │
      └── outbox event
              │
              ↓
         Kafka / worker
```

---

## Isolation and Concurrency

Concurrency problems can arise when multiple transactions operate on the same data.

Typical concerns include:

- Lost updates
- Write skew
- Non-repeatable reads
- Serialization failures
- Deadlocks

For example, this application pattern can be unsafe:

```text
SELECT balance
application calculates balance - amount
UPDATE balance
```

An atomic statement can be safer:

```sql
UPDATE accounts
SET balance = balance - $1
WHERE id = $2
  AND balance >= $1
RETURNING balance;
```

The database can enforce the condition and update together.

---

## Optimistic Concurrency

A common optimistic approach is version checking.

Suppose:

```text
id = 10
version = 7
```

Update only if the version is still 7:

```sql
UPDATE documents
SET
    content = $1,
    version = version + 1
WHERE id = $2
  AND version = $3;
```

If zero rows are updated, another transaction modified the document first.

This is useful when conflicts are relatively uncommon.

---

## Pessimistic Concurrency

When contention is expected and a transaction needs to reserve a row, PostgreSQL can use row locks.

```sql
SELECT id, status
FROM jobs
WHERE id = $1
FOR UPDATE;
```

The lock is held until the transaction ends.

Django exposes this through:

```python
with transaction.atomic():
    job = (
        Job.objects
        .select_for_update()
        .get(id=job_id)
    )
```

Keep such transactions short.

---

## Deadlocks

A deadlock occurs when transactions wait on each other.

Example:

```text
Transaction A locks Row 1
Transaction B locks Row 2

A waits for Row 2
B waits for Row 1
```

PostgreSQL detects deadlocks and aborts one transaction.

A common prevention technique is consistent lock ordering.

For example, if a transaction modifies two accounts, always acquire them in ascending ID order:

```text
lock account 10
lock account 20
```

rather than sometimes:

```text
10 → 20
```

and elsewhere:

```text
20 → 10
```

Deadlocks can still happen despite careful design, so applications should understand how to retry appropriate transaction failures.

---

## Connection Pooling

Backend applications normally do not create a brand-new database connection for every request.

A pool maintains reusable connections.

```text
Request
  ↓
Acquire connection
  ↓
Execute SQL
  ↓
Commit / rollback
  ↓
Return connection
```

Pool sizing is a capacity decision.

If there are:

```text
20 pods
× 10 connections
```

the application fleet may create up to approximately:

```text
200 connections
```

before considering overflow, workers, administrative sessions, replicas, and other consumers.

Increasing pool size does not automatically improve performance.

It can instead increase:

- CPU contention
- Memory usage
- Lock contention
- Query concurrency
- Tail latency

---

## Read Replicas

Read replicas can scale read-heavy workloads.

A typical architecture is:

```text
                 ┌──────────────┐
                 │ Backend API  │
                 └──────┬───────┘
                        │
              ┌─────────┴─────────┐
              │                   │
          Writes              Reads
              │                   │
              ↓                   ↓
         ┌─────────┐        ┌─────────┐
         │ Primary │ ─────→ │ Replica │
         └─────────┘  WAL   └─────────┘
```

The major issue is replication lag.

Immediately after:

```text
POST /orders
```

a subsequent:

```text
GET /orders/123
```

may be routed to a replica that has not replayed the write yet.

Therefore read routing must account for consistency requirements.

---

## OLTP vs OLAP

### OLTP

Typical characteristics:

- Small transactions
- High concurrency
- Frequent inserts/updates
- Point lookups
- Strong transactional requirements

Examples:

```text
Order creation
Payment state
User profile updates
Inventory reservation
```

### OLAP

Typical characteristics:

- Large scans
- Aggregations
- Historical data
- Complex joins
- Long-running queries

Examples:

```text
Monthly revenue analysis
Customer cohort analysis
Business intelligence
Operational reporting
```

Running heavy analytical queries directly against a latency-sensitive OLTP primary can degrade production traffic.

Possible solutions include:

- Read replicas
- Materialized views
- Dedicated analytical databases
- Data warehouses
- Kafka/CDC pipelines

---

## Multi-Tenant SQL

In a shared-schema SaaS architecture, tables commonly include:

```sql
tenant_id
```

For example:

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    total_amount numeric(12, 2) NOT NULL
);
```

Queries must consistently scope tenant data:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND id = $2;
```

Indexes should reflect real access patterns:

```sql
CREATE INDEX idx_orders_tenant_customer
ON orders (tenant_id, customer_id);
```

### Security

Application-level tenant filtering is necessary but can be supplemented with PostgreSQL Row Level Security where appropriate.

The important principle is:

> Tenant isolation is a security boundary, not merely a query convention.

---

## Soft Deletes

A common pattern is:

```sql
deleted_at timestamptz
```

Active rows are:

```sql
WHERE deleted_at IS NULL
```

A common production optimization is a partial index:

```sql
CREATE INDEX idx_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

But soft deletes introduce complexity:

- Unique constraints
- Foreign keys
- Reporting
- Storage growth
- Index size
- Data retention
- Restore semantics

Do not assume soft delete is always the right lifecycle strategy.

---

## Date and Time Queries

Timestamp filtering should normally use ranges.

Prefer:

```sql
SELECT *
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

over wrapping the indexed column in a function:

```sql
WHERE DATE(created_at) = $1
```

The range form often preserves a straightforward index access path.

Always clarify:

- Time zone
- Inclusive/exclusive boundaries
- Business timezone
- Storage format
- Daylight-saving behavior

For APIs, UTC-based storage and explicit timezone handling are usually easier to reason about.

---

## JSON and Semi-Structured Data

PostgreSQL supports JSON and JSONB.

Example:

```sql
SELECT id
FROM events
WHERE payload @> '{"type": "payment"}';
```

`jsonb` supports indexing strategies such as GIN.

However, JSON should not automatically replace relational modeling.

If an attribute is:

- Frequently filtered
- Frequently joined
- Uniqueness-constrained
- Central to business invariants

it may deserve a proper relational column.

Use JSON where schema flexibility provides real value.

---

## Common SQL Interview Problem: Second Highest Salary

A classic question is:

> Find the second-highest distinct salary.

One approach is:

```sql
SELECT salary
FROM (
    SELECT
        salary,
        DENSE_RANK() OVER (
            ORDER BY salary DESC
        ) AS rank
    FROM employees
) AS ranked
WHERE rank = 2;
```

The use of `DENSE_RANK()` matters because multiple employees may share the highest salary.

The interviewer may then change the requirement:

> Find the second employee by salary, including duplicates.

That is a different problem and may require `ROW_NUMBER()`.

The key skill is clarifying semantics rather than memorizing one query.

---

## Common SQL Interview Problem: Duplicate Values

Find duplicate emails:

```sql
SELECT
    email,
    COUNT(*) AS occurrences
FROM users
GROUP BY email
HAVING COUNT(*) > 1;
```

To retrieve the actual duplicate rows:

```sql
SELECT u.*
FROM users AS u
JOIN (
    SELECT email
    FROM users
    GROUP BY email
    HAVING COUNT(*) > 1
) AS duplicates
    ON duplicates.email = u.email;
```

At production level, also ask:

> Why does the database allow these duplicates?

If uniqueness is a business invariant, the long-term solution may be a unique constraint rather than recurring cleanup queries.

---

## Common SQL Interview Problem: Latest Row Per Group

Requirement:

> Find the latest order for each customer.

Window function:

```sql
SELECT *
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

PostgreSQL-specific:

```sql
SELECT DISTINCT ON (customer_id)
    customer_id,
    id,
    created_at
FROM orders
ORDER BY customer_id, created_at DESC, id DESC;
```

The index should be evaluated based on the actual workload.

---

## Common SQL Interview Problem: Customers Without Orders

Use `NOT EXISTS`:

```sql
SELECT c.*
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.id
);
```

This is often preferable to:

```sql
WHERE c.id NOT IN (...)
```

because `NULL` values can make `NOT IN` semantics surprising.

Another valid approach is:

```sql
SELECT c.*
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id
WHERE o.id IS NULL;
```

The correct formulation should be selected based on semantics and measured performance.

---

## Common SQL Interview Problem: Top N Per Group

Requirement:

> Return the top three orders by value for every customer.

```sql
SELECT
    customer_id,
    id,
    total_amount
FROM (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS rn
    FROM orders AS o
) AS ranked
WHERE rn <= 3;
```

If ties should all be included, `RANK()` may be more appropriate.

Again, clarify whether "top three" means exactly three rows or the top three ranking positions.

---

## Common SQL Interview Problem: Running Total

```sql
SELECT
    customer_id,
    created_at,
    total_amount,
    SUM(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

The explicit frame can make the intended behavior clear.

A deterministic ordering is important when timestamps are not unique.

---

## Common SQL Interview Problem: Find Missing Relationships

For example:

> Find products that have never been ordered.

```sql
SELECT p.*
FROM products AS p
WHERE NOT EXISTS (
    SELECT 1
    FROM order_items AS oi
    WHERE oi.product_id = p.id
);
```

The same reasoning applies to:

- Customers without orders
- Users without logins
- Accounts without transactions
- Products without inventory records

---

## Query Correctness Before Performance

A common mistake is immediately asking:

> "What index should I create?"

Before that, ask:

1. What should one output row represent?
2. Are the joins correct?
3. Are `NULL`s handled correctly?
4. Are filters applied to the correct relation?
5. Is aggregation at the correct grain?
6. Is authorization enforced?
7. Are transaction semantics correct?
8. Is the result actually needed?

Only then investigate performance.

---

## Query Frequency Matters

Suppose:

```text
Query A: 2 seconds × 1 execution/hour
Query B: 20 ms × 10,000 executions/minute
```

Query B may have a much larger production impact.

A useful mental model is:

```text
Total database cost
≈
query cost × execution frequency × concurrency
```

Real systems also depend on:

- CPU
- I/O
- memory
- lock waits
- connection limits
- cache behavior
- replication
- workload overlap

This is why tools such as PostgreSQL's `pg_stat_statements` are valuable.

---

## SQL and Connection Pools

A slow query can create a secondary failure:

```text
Slow query
   ↓
Connection held longer
   ↓
Pool fills
   ↓
Requests wait for connections
   ↓
Application latency increases
   ↓
Retries increase
   ↓
Database load increases
```

This feedback loop is common in production incidents.

Therefore SQL performance must be analyzed together with connection pooling and application concurrency.

---

## SQL and Redis

Redis can reduce repeated database reads through caching.

A typical cache-aside flow is:

```text
API
 │
 ├── Redis hit ──→ return
 │
 └── miss
       ↓
    PostgreSQL
       ↓
    populate Redis
       ↓
     return
```

But Redis does not replace database correctness.

Critical state should still have durable ownership and transactional invariants in the database where appropriate.

Cache invalidation and stale data are architectural concerns.

---

## SQL and Kafka

Kafka is useful for asynchronous event propagation.

A database transaction can write:

```text
business record
+
outbox event
```

The outbox can then be published asynchronously.

This avoids assuming that:

```text
COMMIT database
+
send Kafka message
```

is automatically atomic.

If the process crashes between those operations, one side can succeed while the other does not.

---

## SQL and Celery

Long-running SQL work should not unnecessarily block API requests.

For example:

```text
POST /reports
     ↓
create report job
     ↓
Celery
     ↓
run expensive SQL
     ↓
store result
```

This is preferable to making a synchronous HTTP request wait for a large analytical query when the business operation does not require immediate completion.

Workers still need:

- Concurrency limits
- Database connection limits
- Timeouts
- Retry policies
- Idempotency
- Monitoring

---

## SQL and Microservices

In a database-per-service architecture:

```text
Order Service → Orders DB
Payment Service → Payments DB
Inventory Service → Inventory DB
```

Each service owns its data.

Avoid treating the database as a global integration API.

Cross-service workflows generally require:

- APIs
- Events
- Kafka
- Sagas
- Transactional outbox
- Explicit consistency models

A SQL join cannot naturally cross independent databases in the same way as tables in one PostgreSQL database.

---

## SQL Security

Production SQL security should include multiple layers.

### Application layer

- Authentication
- Authorization
- Input validation
- Parameterized queries
- Resource-level access checks

### Database layer

- Least-privilege roles
- Constraints
- Row Level Security where appropriate
- Separate migration/runtime users
- Read-only roles

### Infrastructure layer

- Private networking
- TLS
- Secret management
- Network access controls
- Auditing
- Backup protection

Do not assume that hiding PostgreSQL behind a private subnet eliminates SQL security risks.

---

## SQL Reliability

Reliable SQL systems account for:

- Transactions
- Deadlocks
- Serialization failures
- Connection failures
- Replica lag
- Timeouts
- Retry behavior
- Failover
- Backup and recovery

Retries require particular care.

A retry after a database timeout may occur when the original transaction actually committed but the client did not receive the response.

Therefore idempotency matters for operations that can be retried safely.

---

## SQL Scalability

Scaling options should be chosen based on the bottleneck.

| Problem | Potential strategy |
|---|---|
| CPU-heavy queries | Query optimization, workload isolation, vertical scaling |
| Read volume | Read replicas, caching |
| Large historical data | Partitioning, archival, OLAP |
| Write contention | Atomic operations, workload redesign, sharding where justified |
| Too many connections | Pool tuning, PgBouncer, concurrency control |
| Large tables | Partitioning, indexing, lifecycle management |
| Cross-service coupling | Database ownership, APIs/events |
| Analytical load | Warehouse/OLAP system |
| Very large tenant | Tenant placement/sharding |

Do not jump directly to sharding.

A typical progression is:

```text
Optimize queries
      ↓
Fix indexes/statistics
      ↓
Control concurrency
      ↓
Scale vertically
      ↓
Add caching/read replicas
      ↓
Partition/workload isolation
      ↓
Shard only when justified
```

---

## Production SQL Observability

Useful PostgreSQL signals include:

```sql
SELECT
    pid,
    usename,
    state,
    wait_event_type,
    wait_event,
    query_start,
    query
FROM pg_stat_activity
WHERE state <> 'idle';
```

For query-level statistics, `pg_stat_statements` can help identify:

- High total execution time
- High mean execution time
- Frequently executed queries
- Resource-heavy query patterns

For lock troubleshooting:

```sql
SELECT
    pid,
    pg_blocking_pids(pid) AS blocking_pids,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

The objective is not merely to identify a slow SQL statement.

It is to understand:

```text
Query
 ↓
Plan
 ↓
Resource consumption
 ↓
Concurrency
 ↓
Application impact
```

---

## Senior SQL Interview Questions

### How would you optimize a slow query?

A strong answer should describe a process:

1. Capture the exact SQL and parameters.
2. Measure frequency and latency.
3. Run `EXPLAIN (ANALYZE, BUFFERS)` safely.
4. Compare estimated and actual cardinality.
5. Inspect scans and joins.
6. Check indexes and statistics.
7. Check locks and waits.
8. Check result-set size.
9. Check application query frequency/N+1 behavior.
10. Benchmark the proposed change.
11. Monitor after deployment.

Avoid answering:

> "I would add an index."

That is a possible solution, not a diagnostic methodology.

---

### Why is the database using a sequential scan even though an index exists?

Possible reasons include:

- Query returns a large percentage of the table.
- Predicate has low selectivity.
- Table is small.
- Statistics are inaccurate.
- The index does not match the predicate.
- Data type conversion prevents useful index matching.
- Query requires additional filtering.
- Sequential access is estimated to be cheaper.
- The query is parameter-sensitive.

The correct answer is:

> Inspect the execution plan and estimates rather than assuming the planner is wrong.

---

### What causes an N+1 query problem?

The application loads a collection and then performs another query for each element.

```text
1 query
+
N queries
=
N+1
```

Typical fixes include:

- `select_related`
- `prefetch_related`
- Explicit joins
- Batch loading
- Aggregation
- Carefully designed SQL

But always inspect the generated SQL and result cardinality.

---

### When would you use a window function instead of `GROUP BY`?

Use `GROUP BY` when the result should collapse into groups.

Use a window function when you need calculations across related rows while retaining individual rows.

For example:

```text
GROUP BY:
one row per customer

Window:
one row per order + customer-level aggregate
```

---

### `DELETE` vs soft delete?

Hard delete physically removes the row logically from the table.

Soft delete marks the row:

```sql
deleted_at
```

Soft deletion can simplify recovery and audit requirements but increases query and lifecycle complexity.

Consider:

- Data retention
- Regulatory requirements
- Storage growth
- Uniqueness
- Foreign keys
- Reporting
- Restore behavior

---

### When should you use a transaction?

Use a transaction when multiple database operations must preserve a business invariant together.

For example:

```text
Create order
+
Reserve inventory
+
Create payment record
```

If those operations must commit as one database unit, they belong in the same transaction when they share the same database and transaction boundary.

Do not keep transactions open across slow external calls unless there is a deliberate architectural reason.

---

### How do you prevent lost updates?

Possible approaches include:

- Atomic SQL
- Optimistic version checks
- Row-level locks
- Appropriate transaction isolation

For example:

```sql
UPDATE inventory
SET quantity = quantity - $1
WHERE product_id = $2
  AND quantity >= $1;
```

The database performs the condition and update atomically.

---

### How do you handle deadlocks?

A strong production answer includes:

1. Keep transactions short.
2. Acquire locks in consistent order.
3. Avoid unnecessary locking.
4. Inspect `pg_locks` and `pg_stat_activity`.
5. Identify the conflicting transaction paths.
6. Retry retryable deadlock failures with bounded backoff and jitter.
7. Ensure the whole transaction is retried, not just one statement.
8. Monitor recurring deadlocks.

In PostgreSQL, deadlocks are reported using SQLSTATE:

```text
40P01
```

---

### Why can a larger connection pool make performance worse?

Because database connections represent concurrent work.

Increasing concurrency can increase:

- CPU contention
- Memory consumption
- Lock contention
- Context switching
- Queueing
- Tail latency

The correct pool size depends on:

```text
database capacity
+
query characteristics
+
application concurrency
+
number of instances
+
workers
+
other connection consumers
```

---

### How would you design SQL for a high-traffic API?

Start with access patterns.

For each endpoint:

```text
Request
 ↓
Expected result
 ↓
SQL shape
 ↓
Indexes
 ↓
Transaction boundary
 ↓
Connection behavior
 ↓
Caching
 ↓
Replica/read strategy
 ↓
Observability
```

Then test using realistic data volume and concurrency.

---

## Practical SQL Interview Checklist

Before answering a SQL problem, mentally ask:

### Correctness

- What does one result row represent?
- What relationships exist?
- Is the join cardinality correct?
- Are `NULL`s handled?
- Are duplicates expected?
- Is the aggregation correct?
- Is ordering deterministic?

### Performance

- How many rows are processed?
- What indexes are available?
- What is the expected selectivity?
- What does `EXPLAIN` show?
- Is the query executed frequently?
- Is there N+1 behavior?
- Is the result set unnecessarily large?

### Concurrency

- Can two requests modify the same row?
- Is the operation atomic?
- Is a transaction required?
- Could it deadlock?
- Could retries duplicate work?

### Production

- Is the query running against the primary?
- Could replica lag matter?
- Is connection pool capacity sufficient?
- Could this cause high CPU/I/O?
- Does the query interact with caching?
- Is this OLTP or analytical work?

### Security

- Are values parameterized?
- Can users influence SQL structure?
- Is authorization enforced?
- Could tenant data cross boundaries?
- Does the database role have excessive privileges?

---

## Production SQL Review Checklist

Before shipping an important SQL operation:

- [ ] Result cardinality is explicitly understood.
- [ ] Joins match the actual data relationships.
- [ ] `NULL` behavior is intentional.
- [ ] Business invariants have appropriate database constraints.
- [ ] Query parameters are bound safely.
- [ ] Dynamic identifiers are allowlisted.
- [ ] Execution plan has been reviewed for important queries.
- [ ] Indexes match actual access patterns.
- [ ] Query frequency is understood.
- [ ] Large result sets are avoided.
- [ ] Pagination is appropriate for dataset size.
- [ ] Transaction boundaries are intentional.
- [ ] Lock behavior is understood.
- [ ] Retry behavior is safe.
- [ ] Connection pool impact is understood.
- [ ] Replica consistency requirements are understood.
- [ ] Monitoring exists for important workloads.

---

## Interview Evaluation Heuristic

A useful way to evaluate your own SQL answer is:

```text
Syntax
  ↓
Semantics
  ↓
Cardinality
  ↓
Correctness
  ↓
Execution Plan
  ↓
Concurrency
  ↓
Production Impact
```

An intermediate candidate may stop at:

> "This query returns the required rows."

A senior candidate should be able to continue:

> "This produces one row per customer because the aggregation occurs after filtering. The customer/order relationship is one-to-many, so I would avoid an unnecessary join if I only need existence. I would verify the access path with `EXPLAIN (ANALYZE, BUFFERS)`, ensure the relevant foreign-key/filter columns are indexed, and consider query frequency and connection-pool impact under production concurrency."

That difference is often what separates syntax knowledge from backend engineering judgment.

## Key Takeaways

- **SQL interviews test reasoning more than syntax:** define result grain, understand cardinality, handle `NULL` correctly, and choose joins, aggregation, subqueries, or window functions based on semantics.
- **Correctness comes before optimization:** validate joins, duplicates, filtering, authorization, and transaction behavior before tuning execution plans or adding indexes.
- **Production SQL requires database internals awareness:** indexes, query plans, locks, transactions, connection pools, replicas, and workload characteristics all affect real-world behavior.
- **ORM knowledge does not replace SQL knowledge:** Django and SQLAlchemy ultimately rely on generated SQL, so backend engineers must understand the SQL and execution plans behind ORM operations.
- **Senior SQL answers connect queries to system design:** discuss concurrency, scalability, security, migrations, large datasets, observability, and recovery when the problem has production implications.