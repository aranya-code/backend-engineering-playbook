# 16- Indexes for JOINs

## Overview

Indexes are critical to efficient SQL joins when the database must repeatedly locate matching rows in one table using values from another table.

Consider a typical backend query:

```sql
SELECT
    o.id,
    o.created_at,
    u.email
FROM orders AS o
JOIN users AS u
    ON u.id = o.user_id
WHERE o.status = 'pending';
```

The database must perform two distinct operations:

1. Identify the relevant `orders`.
2. Match each order's `user_id` to a row in `users`.

Indexes can make the second operation dramatically cheaper by providing an efficient lookup structure for the join key.

A common misconception is:

> "Every column used in a JOIN must have an index."

That is not correct. The optimizer chooses a join strategy based on table size, cardinality, statistics, available indexes, predicates, memory, and estimated cost. An index is useful when it makes the chosen access path cheaper than alternatives such as sequential scans or hash joins.

For backend systems, join-index design should therefore be driven by **actual query patterns and execution plans**, not by mechanically indexing every foreign key.

## Why JOIN Indexes Matter

Suppose:

```sql
orders.user_id
        ↓
users.id
```

`users.id` is typically indexed because it is a primary key.

The more important question is often whether:

```sql
orders.user_id
```

is indexed.

Without an index on `orders.user_id`, a query that needs to repeatedly find orders for a user may have to scan many rows.

With an index:

```text
users
  │
  │ user.id
  ▼
orders.user_id index
  │
  ▼
matching orders
```

This can reduce the amount of data the database must inspect.

However, the benefit depends heavily on the join algorithm and query shape.

## JOIN Execution and Indexes

A relational database does not execute every join the same way.

Common join strategies include:

| Join strategy | Typical behavior | Index dependency |
|---|---|---|
| Nested Loop | Finds matching rows repeatedly for each outer row | Often benefits strongly from an index on the inner relation |
| Hash Join | Builds a hash table and probes it | Usually does not require a join-key index |
| Merge Join | Walks two sorted inputs together | Can benefit from indexes that provide suitable ordering, but sorting may also be used |

The optimizer chooses among these strategies based on estimated cost.

Therefore:

```text
JOIN
 ↓
Query Planner
 ↓
Choose join algorithm
 ↓
Choose access path for each relation
 ↓
Execute
```

An index is an **access-path optimization**, not a requirement of SQL join semantics.

## Nested Loop JOINs

Nested loop joins are where join indexes are often most visibly valuable.

Conceptually:

```text
for each row in outer table:
    find matching rows in inner table
```

Without an index:

```text
Outer rows
   ↓
Repeated scan of inner table
   ↓
Potentially expensive
```

With an index:

```text
Outer row
   ↓
Lookup join key
   ↓
Index
   ↓
Matching inner rows
```

For example:

```sql
SELECT
    u.id,
    u.email,
    o.id AS order_id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id
WHERE u.id = 42;
```

If:

```sql
CREATE INDEX idx_orders_user_id
ON orders (user_id);
```

the database can efficiently locate orders belonging to user `42`.

The performance difference becomes significant when:

- The outer relation produces relatively few rows.
- The inner relation is large.
- The join key is selective.
- The inner-side lookup is executed many times.

## Hash JOINs

A hash join works differently.

Conceptually:

```text
Build side
    ↓
Build hash table on join key
    ↓
Probe side
    ↓
Find matching hash entries
```

For:

```sql
SELECT *
FROM orders AS o
JOIN users AS u
    ON u.id = o.user_id;
```

the database may build a hash table for one relation and probe it using the join key from the other.

An index on `orders.user_id` may not be necessary for this specific plan.

This is one of the most important interview points:

> **A join can be efficient without indexes because hash joins and merge joins can avoid indexed lookups entirely.**

Do not judge an index solely by whether a column appears in a `JOIN` condition.

## Merge JOINs

A merge join requires both inputs to be ordered by the join key.

Conceptually:

```text
Input A sorted by key ──┐
                        ├── Merge Join
Input B sorted by key ──┘
```

An existing index can sometimes provide the required ordering:

```sql
CREATE INDEX idx_orders_user_id
ON orders (user_id);
```

But the planner can also choose explicit sorting when that is cheaper.

Merge joins can be useful for:

- Large relations.
- Already sorted inputs.
- Equality joins.
- Queries where suitable indexes or ordering are available.

## The Most Important Rule: Index the Lookup Side

For a join:

```sql
A JOIN B
ON A.customer_id = B.id
```

`B.id` is normally indexed because it is a primary key.

The commonly missing index is:

```sql
A.customer_id
```

For example:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

This is particularly useful for queries such as:

```sql
SELECT
    c.id,
    c.name,
    o.id,
    o.total
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = $1;
```

The relationship can be visualized as:

```text
customers
    │
    │ primary key lookup
    ▼
customers.id
    │
    │ matches
    ▼
orders.customer_id
    │
    │ index lookup
    ▼
matching orders
```

## Primary Key Side vs Foreign Key Side

Consider:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE orders (
    id bigint PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    total numeric(12, 2) NOT NULL
);
```

The primary key creates an index on:

```text
customers.id
```

But the foreign key does **not universally imply that an index exists on**:

```text
orders.customer_id
```

In PostgreSQL, creating a foreign key does not automatically create an index on the referencing column.

Therefore, a production schema may need:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

This can improve both read queries and certain referential-integrity operations.

## Foreign Key Indexes

Foreign-key columns are strong candidates for indexes when they are frequently used for:

- JOINs.
- Filtering.
- Ordering.
- Parent-to-child lookups.
- Cascading updates/deletes.
- Existence checks.

Example:

```sql
CREATE INDEX idx_order_items_order_id
ON order_items (order_id);
```

For:

```sql
SELECT
    o.id,
    oi.product_id,
    oi.quantity
FROM orders AS o
JOIN order_items AS oi
    ON oi.order_id = o.id
WHERE o.id = $1;
```

the index allows efficient lookup of child rows.

This pattern is extremely common:

```text
Parent
  │
  │ 1
  ▼
Child
  │
  │ many
  ▼
foreign_key index
```

## One-to-Many JOINs

One-to-many relationships are especially important.

Example:

```text
customers
    1
    │
    │
    N
 orders
```

Query:

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = 42;
```

An index on:

```sql
orders(customer_id)
```

lets the database find the matching child rows efficiently.

Without it, retrieving the children may require scanning the entire `orders` table.

## Many-to-Many JOINs

Many-to-many relationships normally use a junction table.

Example:

```sql
CREATE TABLE students (
    id bigint PRIMARY KEY
);

CREATE TABLE courses (
    id bigint PRIMARY KEY
);

CREATE TABLE student_courses (
    student_id bigint NOT NULL REFERENCES students(id),
    course_id bigint NOT NULL REFERENCES courses(id),
    PRIMARY KEY (student_id, course_id)
);
```

The primary key creates an index on:

```text
(student_id, course_id)
```

This is excellent for:

```sql
SELECT course_id
FROM student_courses
WHERE student_id = $1;
```

But it is not equivalent to an index beginning with `course_id`.

For the reverse lookup:

```sql
SELECT student_id
FROM student_courses
WHERE course_id = $1;
```

you should consider:

```sql
CREATE INDEX idx_student_courses_course_id
ON student_courses (course_id);
```

This illustrates a key principle:

> **A composite index is directional with respect to its leading columns.**

## Composite JOIN Indexes

Real production queries often combine JOIN conditions with filters.

Consider:

```sql
SELECT
    o.id,
    o.total
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = $1
  AND o.status = 'pending';
```

A simple index:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

may already be useful.

But if the workload frequently performs:

```text
customer_id + status
```

lookups, consider:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

The database can then narrow the search using both values.

Conceptually:

```text
(customer_id, status)
        │
        ▼
customer = 42
        │
        ▼
status = pending
        │
        ▼
matching orders
```

The right index depends on the full workload rather than the JOIN condition alone.

## JOIN + WHERE Predicate

Indexes should be designed around the complete access pattern.

Consider:

```sql
SELECT
    u.id,
    u.email,
    o.id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id
WHERE u.status = 'active'
  AND o.created_at >= $1;
```

Possible indexes include:

```sql
CREATE INDEX idx_users_status
ON users (status);

CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at);
```

The second index can support the combination:

```text
user_id equality
        +
created_at range
```

This is often more useful than separate indexes:

```sql
orders(user_id)
orders(created_at)
```

but the actual best design must be verified against real query plans and workload distribution.

## Index Column Order in JOINs

Column order matters in composite indexes.

Compare:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

with:

```sql
CREATE INDEX idx_orders_status_customer
ON orders (status, customer_id);
```

These are not interchangeable.

For a query:

```sql
WHERE customer_id = $1
  AND status = 'pending'
```

both may be viable.

But different workloads can favor different orders.

A useful starting point is:

```text
Equality predicates
    ↓
frequently used filtering
    ↓
range predicates
    ↓
ordering requirements
```

This is a heuristic, not a universal law. Selectivity, join cardinality, ordering, query frequency, and planner behavior all matter.

## JOINs with Additional Predicates

A join condition may contain more than a simple foreign-key equality:

```sql
SELECT *
FROM orders AS o
JOIN users AS u
    ON u.id = o.user_id
   AND u.is_active = true;
```

The optimizer can use indexes on:

```text
users.id
users.is_active
```

depending on the selected plan.

Do not assume the textual order of predicates determines index usage.

SQL is declarative:

```text
SQL query
    ↓
Optimizer
    ↓
Reordered predicates
    ↓
Chosen join strategy
    ↓
Chosen indexes/access paths
```

## JOINs and Selectivity

Index usefulness depends heavily on selectivity.

Suppose:

```sql
orders.status
```

contains:

```text
pending
completed
cancelled
```

If 95% of rows are:

```text
completed
```

an index on `status` may provide limited benefit for queries requesting most completed rows.

Conversely, an index on:

```sql
customer_id
```

may be highly selective if each customer has relatively few orders.

For join performance, think in terms of:

```text
How many rows does this condition eliminate?
```

rather than:

```text
Is this column part of a JOIN?
```

## JOIN Cardinality

Cardinality is central to join performance.

Consider:

```sql
SELECT *
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

If one user has:

```text
3 orders
```

the join produces approximately three matching rows for that user.

If a customer has:

```text
500,000 orders
```

the same indexed lookup can still return a very large result.

An index makes locating the rows efficient; it does not make processing hundreds of thousands of matching rows cheap.

Therefore:

> **Indexes reduce search cost; they do not eliminate result-processing cost.**

## JOINs and `LIMIT`

Indexes become especially valuable when the query needs only a small number of rows.

For example:

```sql
SELECT
    o.id,
    o.created_at
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id
WHERE u.id = $1
ORDER BY o.created_at DESC
LIMIT 20;
```

A useful index may be:

```sql
CREATE INDEX idx_orders_user_created_desc
ON orders (user_id, created_at DESC);
```

This can potentially support:

```text
user_id lookup
      ↓
already ordered created_at
      ↓
take first 20
```

The database may avoid both scanning unrelated orders and sorting the complete result set.

## JOINs and Covering Indexes

If a query frequently retrieves a small set of columns, an index can sometimes include additional columns.

PostgreSQL example:

```sql
CREATE INDEX idx_orders_user_created
ON orders (user_id, created_at DESC)
INCLUDE (id, total);
```

Query:

```sql
SELECT
    id,
    created_at,
    total
FROM orders
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 20;
```

The index provides:

- Join/filter key: `user_id`
- Ordering key: `created_at`
- Returned columns: `id`, `total`

This may enable an index-only scan when PostgreSQL's visibility requirements are satisfied.

Do not automatically create covering indexes for every join. Wider indexes consume more storage and increase write amplification.

## JOINs Across Large Tables

Suppose:

```text
users       = 10 million rows
orders      = 500 million rows
```

and:

```sql
SELECT ...
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id
WHERE u.id = $1;
```

An index on:

```sql
orders(user_id)
```

can be highly valuable because the query needs only a small subset of the enormous `orders` table.

But consider:

```sql
SELECT ...
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id;
```

with no selective predicates and a requirement to return most rows.

A hash join or another sequential strategy may be cheaper than performing millions of random index lookups.

This distinction is critical at scale.

## JOINs and Data Distribution

The same index can behave differently depending on data distribution.

For example:

```text
Customer A → 3 orders
Customer B → 20 orders
Customer C → 8 million orders
```

An index on:

```sql
orders(customer_id)
```

is still useful, but queries involving Customer C may return so many rows that index traversal is no longer the dominant cost.

The planner may choose a different strategy depending on estimated cardinality.

This is why production tuning requires:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

rather than relying on index theory alone.

## Self-JOINs

Self-joins can also benefit from indexes.

Example:

```sql
SELECT
    e.id,
    e.name,
    manager.name AS manager_name
FROM employees AS e
LEFT JOIN employees AS manager
    ON manager.id = e.manager_id;
```

The primary key:

```text
employees.id
```

supports lookup of the manager.

The referencing column:

```text
employees.manager_id
```

may also be useful for queries that traverse the hierarchy in the opposite direction.

For example:

```sql
SELECT *
FROM employees
WHERE manager_id = $1;
```

An index on:

```sql
CREATE INDEX idx_employees_manager_id
ON employees (manager_id);
```

supports efficient subordinate lookup.

## Outer JOINs

For:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
LEFT JOIN orders AS o
    ON o.customer_id = c.id;
```

an index on:

```sql
orders(customer_id)
```

can be valuable because the database needs to find matching child rows for each relevant customer.

The fact that the join is an outer join does not eliminate the usefulness of indexes.

However, outer-join semantics can restrict query transformations, so the optimizer's chosen plan must still be inspected.

## JOINs and NULL Values

Foreign keys can be nullable:

```sql
customer_id bigint REFERENCES customers(id)
```

with some rows containing:

```text
customer_id = NULL
```

A join:

```sql
ON orders.customer_id = customers.id
```

does not match NULL values under normal SQL equality semantics.

Indexes can still support the non-null lookups, but NULL behavior must be understood when reasoning about:

- Cardinality.
- Selectivity.
- Outer joins.
- Partial indexes.
- Query semantics.

For example, if almost all rows have `customer_id IS NULL`, an index strategy based on customer lookups may behave differently from expectations.

## Partial Indexes for JOIN Workloads

If only a subset of rows participates in a frequent query, a partial index can be effective.

Example:

```sql
CREATE INDEX idx_orders_active_customer
ON orders (customer_id)
WHERE deleted_at IS NULL;
```

Query:

```sql
SELECT
    c.id,
    o.id
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = $1
  AND o.deleted_at IS NULL;
```

The index contains only active rows.

Benefits include:

- Smaller index.
- Lower storage usage.
- Less write maintenance for excluded rows.
- Potentially better cache efficiency.

The query predicate must be compatible with the index predicate for PostgreSQL to use the partial index effectively.

## Indexes and Referential Actions

Indexes on foreign-key columns are not only about SELECT queries.

Consider:

```sql
DELETE FROM customers
WHERE id = $1;
```

If child rows reference the customer:

```text
customers.id
    ↓
orders.customer_id
```

the database must check referential integrity.

An index on:

```sql
orders(customer_id)
```

can make locating referencing rows substantially cheaper.

This becomes especially important for:

- Large child tables.
- `ON DELETE CASCADE`.
- `ON DELETE RESTRICT`.
- `ON UPDATE` referential actions.

Therefore, foreign-key indexes can have important write-path implications as well as read-path benefits.

## Detecting Missing JOIN Indexes

A common symptom is a nested loop where the inner relation is repeatedly scanned.

Example conceptual plan:

```text
Nested Loop
  -> Index Scan on users
  -> Seq Scan on orders
```

If `orders` is large and the sequential scan happens repeatedly, investigate whether an index such as:

```sql
CREATE INDEX idx_orders_user_id
ON orders (user_id);
```

would improve the plan.

But do not blindly add the index. Validate the estimated and actual row counts first.

## Reading an Execution Plan

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    u.id,
    u.email,
    o.id AS order_id
FROM users AS u
JOIN orders AS o
    ON o.user_id = u.id
WHERE u.id = 42;
```

Pay attention to:

| Plan attribute | Why it matters |
|---|---|
| Join type | Shows nested loop, hash join, or merge join |
| Access method | Shows sequential, index, bitmap, or index-only scans |
| `actual rows` | Shows real cardinality |
| `loops` | Reveals repeated work, especially in nested loops |
| `Buffers` | Shows memory/cache and disk activity |
| Estimated rows | Shows planner expectations |
| Actual time | Shows where execution time is spent |

A particularly important pattern is:

```text
actual rows × loops
```

For nested loops, a seemingly cheap inner operation can become expensive when executed thousands or millions of times.

## Practical PostgreSQL Example

Schema:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    status text NOT NULL,
    created_at timestamptz NOT NULL,
    total numeric(12, 2) NOT NULL
);
```

Query:

```sql
SELECT
    c.id,
    c.name,
    o.id AS order_id,
    o.total
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = $1
  AND o.status = 'pending'
ORDER BY o.created_at DESC
LIMIT 20;
```

A workload-specific index might be:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC)
INCLUDE (id, total);
```

This index simultaneously addresses:

```text
JOIN
customer_id

FILTER
status

ORDER
created_at DESC

OUTPUT
id, total
```

Whether this is actually optimal must be confirmed with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    c.id,
    c.name,
    o.id AS order_id,
    o.total
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
WHERE c.id = $1
  AND o.status = 'pending'
ORDER BY o.created_at DESC
LIMIT 20;
```

Do not infer the correct index solely from the SQL text.

## ORM Considerations

Django and SQLAlchemy applications can hide join behavior behind ORM APIs.

Django:

```python
orders = (
    Order.objects
    .select_related("customer")
    .filter(
        customer_id=customer_id,
        status="pending",
    )
    .order_by("-created_at")[:20]
)
```

The ORM may generate a SQL join, but database performance still depends on the generated SQL and database indexes.

For collection relationships, Django's:

```python
prefetch_related()
```

usually uses separate queries rather than one large SQL join.

This means the relevant indexes may differ between:

```python
select_related()
```

and:

```python
prefetch_related()
```

Do not design indexes based only on ORM model relationships. Inspect the SQL generated by high-value queries.

## N+1 Queries vs JOIN Indexes

Indexes cannot fix an N+1 query architecture.

For example:

```text
1 query → fetch 100 users
100 queries → fetch orders for each user
```

Even if:

```sql
orders(user_id)
```

is perfectly indexed, the application may still perform 101 database round trips.

A better approach may be:

```text
1 query with JOIN
```

or:

```text
1 query for users
1 batched query for orders
```

Indexes and query structure solve different problems:

| Problem | Typical solution |
|---|---|
| Repeated database round trips | JOIN, eager loading, batching |
| Expensive row lookup | Appropriate index |
| Poor join algorithm | Query/index/statistics investigation |
| Excessive returned rows | Filtering, pagination, query redesign |
| Large result processing | Reduce projection/cardinality |

## Production Considerations

### Write Amplification

Every additional index must be maintained when indexed columns change.

For:

```sql
orders(customer_id)
orders(customer_id, status, created_at)
orders(created_at)
```

an insert into `orders` may require multiple index updates.

At high write volumes, unnecessary join indexes can become a significant cost.

### Storage

Indexes consume disk space and may require additional memory/cache capacity.

Large composite indexes can become substantial portions of database storage.

### Cache Efficiency

Smaller, targeted indexes can often remain hotter in memory than unnecessarily wide indexes.

This matters for high-throughput systems where database I/O is a primary bottleneck.

### Replication

Index creation and heavy write activity can affect:

- WAL generation.
- Replica lag.
- Storage throughput.
- Recovery time.

Production index creation should be planned around the database's replication and availability requirements.

### High Availability

For PostgreSQL production systems, large index creation may require operational planning.

When appropriate:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_id
ON orders (customer_id);
```

`CREATE INDEX CONCURRENTLY` reduces blocking of ordinary table writes compared with a regular index build, but it requires additional work and has operational constraints.

Always test index migrations against realistic table sizes.

## Monitoring JOIN Performance

Monitor both database and application signals.

### Database-level

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

for individual queries.

Monitor:

- Query execution time.
- Buffer hits and reads.
- Sequential scans.
- Index scans.
- Rows returned.
- Rows filtered.
- Join strategy.
- Planner estimates.
- Replica lag.

PostgreSQL statistics can help identify frequently executed queries and their resource consumption.

### Application-level

For Django/FastAPI services, monitor:

- p50 latency.
- p95 latency.
- p99 latency.
- Database connection utilization.
- Query count per request.
- Request error rate.
- Slow-query frequency.

A database optimization that reduces query time from 100 ms to 20 ms may have little value if the endpoint still performs 100 such queries per request.

## Common Mistakes

### Assuming Every JOIN Column Needs an Index

This creates unnecessary indexes.

A hash join may efficiently process a large join using sequential scans.

**Avoid it:** inspect the execution plan and workload before adding an index.

### Indexing Only the Parent Primary Key

Developers often assume:

```text
customers.id
```

being indexed is sufficient.

For parent-to-child lookups, the important missing index may be:

```text
orders.customer_id
```

**Avoid it:** inspect both sides of the relationship and the actual access pattern.

### Ignoring Composite Indexes

An index on:

```sql
orders(customer_id)
```

may be insufficient for a query heavily constrained by:

```text
customer_id + status + created_at
```

**Avoid it:** design around the complete high-frequency predicate and ordering requirements.

### Creating Duplicate Indexes

These indexes may overlap:

```sql
(customer_id)
(customer_id, status)
(customer_id, status, created_at)
```

Some may be justified, but blindly accumulating them increases write and storage costs.

**Avoid it:** audit existing indexes before creating new ones.

### Ignoring Join Cardinality

An index cannot make a query returning millions of rows inexpensive.

**Avoid it:** optimize result cardinality as well as lookup cost.

### Ignoring Statistics

Stale or inaccurate statistics can cause the optimizer to choose a poor join strategy.

**Avoid it:** keep database statistics current and investigate significant estimated-vs-actual row differences.

### Assuming Foreign Keys Automatically Have Indexes

Foreign-key constraints and indexes are separate concerns.

**Avoid it:** explicitly inspect the schema.

### Optimizing the SQL but Ignoring ORM Behavior

An ORM can introduce:

- N+1 queries.
- Unexpected joins.
- Large projections.
- Redundant queries.

**Avoid it:** inspect generated SQL and query counts.

## Interview Traps

### "Should both sides of a JOIN be indexed?"

Not necessarily.

A common relational pattern is:

```sql
child.parent_id = parent.id
```

where:

- `parent.id` is indexed by the primary key.
- `child.parent_id` is often worth indexing.

But the optimizer may choose a hash or merge join where an index is unnecessary.

### "Does PostgreSQL automatically index foreign keys?"

No. A foreign-key constraint does not automatically create an index on the referencing column.

### "Can a JOIN use an index?"

Yes. For example, a nested loop can use an index on the inner relation's join key.

But joins can also use hash or merge strategies without indexed lookups.

### "Why is my indexed JOIN still slow?"

Possible causes include:

- Low selectivity.
- Huge result set.
- Wrong composite index order.
- Poor join order.
- Bad cardinality estimates.
- Stale statistics.
- Random I/O.
- Expensive sorting.
- Large row widths.
- N+1 application queries.

### "Why might PostgreSQL ignore my JOIN index?"

Because the optimizer may estimate that another plan is cheaper.

Examples:

```text
small table
large percentage of rows matched
hash join cheaper
sequential scan cheaper
poor selectivity
```

Index usage is a cost-based decision.

### "What is usually the most important index in a one-to-many relationship?"

Often the foreign-key column on the many side:

```text
parent.id
    ↕
child.parent_id
```

because parent-to-child lookups need to find many child rows efficiently.

## Key Takeaways

- **Indexing JOIN columns is workload-dependent; nested loops often benefit from indexes, while hash and merge joins can be efficient without them.**
- **In a typical `child.foreign_key = parent.primary_key` relationship, the parent key is usually already indexed, while the child foreign-key column is the common candidate for an additional index.**
- **Design JOIN indexes around the complete query: JOIN keys, filters, ordering, `LIMIT`, and frequently returned columns may justify a composite or covering index.**
- **Always validate with `EXPLAIN (ANALYZE, BUFFERS)` because the optimizer chooses join strategies based on cardinality, selectivity, statistics, and estimated cost.**
- **Avoid indexing every JOIN column mechanically; unnecessary indexes increase storage, write amplification, WAL, maintenance, and operational complexity.**