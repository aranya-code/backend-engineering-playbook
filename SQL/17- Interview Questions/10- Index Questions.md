# 10- Index Questions

## Overview

Indexes are one of the highest-value SQL interview topics for backend engineers because they connect SQL correctness, query planning, storage architecture, write performance, and production operations.

An index is a data structure maintained by the database to make specific access patterns faster. The most common PostgreSQL index is a **B-tree**, but PostgreSQL also supports specialized index types such as:

- B-tree
- Hash
- GIN
- GiST
- SP-GiST
- BRIN

The senior-level question is not:

> "Does this table have an index?"

It is:

> **Does the index match the workload, does the planner have enough evidence to use it, and is the read-performance benefit worth the storage and write-maintenance cost?**

---

## Why Indexes Exist

Without an appropriate index, the database may need to inspect many rows to answer a query.

For example:

```sql
SELECT *
FROM orders
WHERE customer_id = $1;
```

Without a useful index, PostgreSQL may scan the table:

```text
Orders table
    ↓
scan many rows
    ↓
check customer_id
    ↓
return matching rows
```

With:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

the database has an additional access structure:

```text
Index
  ↓
matching row locations
  ↓
table rows
  ↓
result
```

The optimizer decides whether that path is actually cheaper.

---

## Indexes Do Not Guarantee Index Scans

A common interview mistake is:

> "If an index exists, PostgreSQL will use it."

Incorrect.

The optimizer considers:

- Estimated row count
- Selectivity
- Table size
- Data distribution
- Statistics
- Random vs sequential I/O
- Cache state
- Query predicates
- Sort requirements
- Join strategy
- Expected result size
- Cost of using the index

For example:

```sql
SELECT *
FROM users
WHERE is_active = true;
```

If 99% of users are active, a sequential scan may be cheaper than traversing the index and fetching almost every table row.

---

## Index Lifecycle

A typical query path looks like:

```text
Application
    ↓
SQL
    ↓
Parser / Analyzer
    ↓
Planner / Optimizer
    ↓
Index or sequential access path
    ↓
Executor
    ↓
Result
```

Index design therefore belongs to query design and workload architecture, not just database administration.

---

## B-tree Index

B-tree is PostgreSQL's default index type.

Example:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

B-tree is appropriate for many common predicates:

```sql
=
<
<=
>
>=
BETWEEN
ORDER BY
```

It is the default choice for most equality and range access patterns.

---

## B-tree Conceptual Structure

A B-tree keeps keys ordered and organizes them into balanced pages.

Conceptually:

```text
                 Root
              /       \
           Branch     Branch
           /   \       /   \
        Leaf  Leaf   Leaf  Leaf
          ↓     ↓      ↓     ↓
       row refs / indexed values
```

The database can navigate toward relevant key ranges instead of scanning every table row.

The exact PostgreSQL implementation includes page-level structures, tuples, metadata, and maintenance behavior, so this diagram is conceptual rather than a physical representation.

---

## Equality Queries

A simple equality predicate:

```sql
SELECT *
FROM users
WHERE email = $1;
```

is a classic B-tree use case.

Index:

```sql
CREATE UNIQUE INDEX idx_users_email
ON users (email);
```

If email must be unique, a unique constraint is usually preferable:

```sql
ALTER TABLE users
ADD CONSTRAINT users_email_key UNIQUE (email);
```

The constraint creates the supporting unique index.

---

## Range Queries

B-tree indexes are useful for ranges:

```sql
SELECT *
FROM orders
WHERE created_at >= $1
  AND created_at < $2;
```

Index:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at);
```

This is common for:

- Time-based queries
- Reports
- Recent records
- Retention workflows
- API filtering

---

## ORDER BY

An index can sometimes help avoid a separate sort.

Example:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
ORDER BY created_at DESC
LIMIT 50;
```

An index:

```sql
CREATE INDEX idx_orders_created_at
ON orders (created_at DESC);
```

may provide an efficient ordered access path.

The planner still determines whether using the index is cheaper.

---

## LIMIT and Indexes

Indexes can be particularly valuable when a query returns a small number of ordered rows.

For:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 50;
```

an appropriate index may allow PostgreSQL to find the first 50 qualifying rows without sorting the entire table.

This is one reason indexes and pagination strategy should be designed together.

---

## Composite Indexes

A composite index contains multiple columns.

```sql
CREATE INDEX idx_orders_customer_created
ON orders (
    customer_id,
    created_at
);
```

This is useful for queries such as:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC;
```

The column order matters.

---

## Leftmost Prefix Principle

For a B-tree index:

```sql
(customer_id, created_at)
```

the leading column is `customer_id`.

It is naturally useful for:

```sql
WHERE customer_id = $1
```

and:

```sql
WHERE customer_id = $1
ORDER BY created_at;
```

But it is generally not equivalent to an index beginning with:

```sql
created_at
```

for queries that only filter on `created_at`.

A simplified mental model:

```text
(customer_id, created_at)

customer_id
    ↓
created_at
```

The first indexed column establishes the primary ordering of the index.

---

## Composite Index Column Order

Suppose the workload is:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 50;
```

A possible index is:

```sql
CREATE INDEX idx_orders_tenant_status_created
ON orders (
    tenant_id,
    status,
    created_at DESC
);
```

The correct ordering depends on the actual workload.

Do not apply simplistic rules such as:

> "Put the most selective column first."

Instead consider:

- Equality predicates
- Range predicates
- Ordering requirements
- Join conditions
- Query frequency
- Cardinality
- Tenant access patterns

---

## Equality, Range, and Ordering

Consider:

```sql
WHERE tenant_id = $1
  AND created_at >= $2
ORDER BY created_at
```

A useful index may be:

```sql
(tenant_id, created_at)
```

because:

```text
tenant_id = equality
created_at = range/order
```

This is a common access pattern in multi-tenant APIs.

---

## Low-Cardinality Columns

Suppose:

```sql
status
```

has only:

```text
pending
completed
failed
```

An index on `status` alone may not always be useful.

If a query returns a large percentage of the table:

```sql
WHERE status = 'completed'
```

the planner may prefer a sequential scan.

But low cardinality does not automatically mean:

> "Never index the column."

The correct decision depends on:

- Distribution
- Table size
- Query frequency
- Additional predicates
- Partial indexes
- Physical locality

---

## Selectivity

Selectivity describes how effectively a predicate narrows the result set.

Highly selective:

```sql
WHERE id = $1
```

Potentially low selectivity:

```sql
WHERE status = 'active'
```

High selectivity often makes index access attractive.

But the planner evaluates estimated cost rather than applying a simple selectivity threshold.

---

## Partial Indexes

A partial index contains only rows satisfying a predicate.

Example:

```sql
CREATE INDEX idx_orders_pending_created
ON orders (created_at)
WHERE status = 'pending';
```

This can be valuable when:

- Only a small subset is queried frequently
- The subset changes less than the full table
- The predicate is stable and matches production queries

Query:

```sql
SELECT *
FROM orders
WHERE status = 'pending'
ORDER BY created_at
LIMIT 100;
```

can potentially benefit from the partial index.

---

## Partial Index and Soft Deletes

A common backend pattern:

```sql
CREATE INDEX idx_users_active_email
ON users (email)
WHERE deleted_at IS NULL;
```

This can make active-user queries efficient:

```sql
SELECT *
FROM users
WHERE deleted_at IS NULL
  AND email = $1;
```

It can also reduce index size compared with indexing every historical/deleted row.

---

## Unique Partial Index

PostgreSQL supports unique partial indexes.

Example:

```sql
CREATE UNIQUE INDEX idx_active_users_email
ON users (email)
WHERE deleted_at IS NULL;
```

This enforces:

> Email must be unique among active users.

This is often better than trying to enforce such a business rule purely in application code.

---

## Expression Indexes

An expression index indexes the result of an expression.

Example:

```sql
CREATE INDEX idx_users_lower_email
ON users (lower(email));
```

It supports queries such as:

```sql
SELECT *
FROM users
WHERE lower(email) = lower($1);
```

The indexed expression must match the query semantics closely enough for the planner to use the index.

---

## Expression Index and Application Semantics

If an application treats email addresses case-insensitively, you might consider:

```sql
CREATE UNIQUE INDEX idx_users_lower_email
ON users (lower(email));
```

Then:

```sql
SELECT *
FROM users
WHERE lower(email) = lower($1);
```

The important principle is:

> Index the expression the application actually queries.

---

## Covering Indexes and INCLUDE

PostgreSQL supports included columns:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC)
INCLUDE (total_amount, status);
```

The included columns are not part of the index's key ordering.

They can allow index-only scans when PostgreSQL can satisfy the query from the index and visibility conditions permit it.

---

## Index-Only Scan

An index-only scan can avoid fetching heap pages for every result row.

Conceptually:

```text
Index
 ├── filtering
 ├── ordering
 └── required columns
        ↓
      result
```

But index-only scans are not guaranteed.

PostgreSQL must also determine whether heap visibility information allows the index tuple to be trusted without visiting the heap.

Vacuum and the visibility map therefore influence how effective index-only scans can be.

---

## Index Size

Indexes consume storage.

Inspect relation sizes:

```sql
SELECT
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    indexrelid::regclass AS index_name
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

For total index storage associated with a table:

```sql
SELECT
    pg_size_pretty(pg_indexes_size('orders')) AS indexes_size;
```

Large indexes affect:

- Storage cost
- Cache pressure
- Backup size
- Replication/WAL behavior during maintenance
- Write performance

---

## Index Write Amplification

Every insert or relevant update may require index maintenance.

If a table has ten indexes, inserting a row may require maintaining many index structures.

Therefore:

```text
More indexes
    ↓
more write work
    ↓
more WAL / I/O
    ↓
more storage
    ↓
potentially slower writes
```

Indexes are not free.

---

## Indexes and UPDATE

An update can affect indexes when indexed columns change.

Even when indexed values do not change, PostgreSQL's MVCC architecture means updates create new row versions, and index/HOT-update behavior determines how much index maintenance is required.

Do not assume:

> "Indexes only affect SELECT."

They affect write workloads too.

---

## HOT Updates

PostgreSQL can perform Heap-Only Tuple updates in certain circumstances.

A HOT update can avoid creating new index entries when indexed columns do not need new index tuples and there is suitable space on the page.

Excessive indexing can reduce opportunities for HOT updates.

This is another reason to avoid unnecessary indexes on write-heavy tables.

---

## Index Bloat

Indexes can accumulate unused space due to:

- Updates
- Deletes
- Page splits
- Workload patterns

Do not automatically equate index size with bloat.

Use appropriate PostgreSQL statistics and operational tooling to determine whether an index actually needs maintenance.

---

## REINDEX

PostgreSQL supports:

```sql
REINDEX INDEX index_name;
```

and:

```sql
REINDEX TABLE table_name;
```

For production systems, understand the locking and availability implications.

PostgreSQL also supports concurrent index rebuilding in appropriate scenarios:

```sql
REINDEX INDEX CONCURRENTLY index_name;
```

Operational behavior and resource consumption should be validated before using it on large production indexes.

---

## CREATE INDEX CONCURRENTLY

For production systems where blocking writes must be minimized, PostgreSQL provides:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_id
ON orders (customer_id);
```

It reduces the locking impact on normal table writes compared with a regular index build.

However, it:

- Takes longer
- Performs more work
- Has additional failure states
- Cannot run inside a transaction block
- Can leave an invalid index if the operation fails

Inspect failed indexes when necessary.

---

## Checking Invalid Indexes

PostgreSQL catalog inspection:

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisready,
    indisvalid
FROM pg_index
WHERE NOT indisready
   OR NOT indisvalid;
```

An invalid index should not simply be ignored.

Determine why it exists and whether it should be removed and recreated.

---

## Foreign Key Indexes

A foreign key does not automatically mean the referencing column has an index in PostgreSQL.

Consider:

```sql
CREATE INDEX idx_orders_customer_id
ON orders (customer_id);
```

This can help queries joining:

```sql
orders.customer_id
```

to:

```sql
customers.id
```

It can also be important for efficient parent-row updates/deletes that must check referencing rows.

The correct index depends on workload and constraint behavior.

---

## Primary Keys and Indexes

A primary key creates a unique index in PostgreSQL.

Example:

```sql
CREATE TABLE customers (
    id bigint PRIMARY KEY
);
```

The database automatically creates supporting uniqueness enforcement.

Do not create another identical index on `id` unless there is a specific reason.

---

## Unique Constraints and Indexes

A unique constraint:

```sql
ALTER TABLE users
ADD CONSTRAINT users_email_key UNIQUE (email);
```

enforces a business invariant.

The supporting index also provides an efficient access path.

Use a constraint when the requirement is data integrity.

Use a standalone index when the requirement is query performance.

---

## Redundant Indexes

Suppose a table has:

```text
(customer_id)
(customer_id, created_at)
```

The first index may be redundant depending on the workload because the composite index can often support queries using its leading column.

But redundancy must be evaluated from actual access patterns.

Do not automatically delete the shorter index.

Check:

- Query plans
- Usage statistics
- Write workload
- Partial predicates
- Ordering requirements
- Index size

---

## Overlapping Indexes

These indexes overlap:

```text
(customer_id, created_at)
(customer_id, status)
(customer_id, created_at, status)
```

Some may be justified.

Others may create unnecessary maintenance cost.

Index review should be workload-driven rather than based solely on visual similarity.

---

## Index Usage Statistics

PostgreSQL provides index usage statistics through:

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

An index with zero scans may be a candidate for review.

But:

> Zero observed scans does not automatically mean the index is safe to delete.

The observation window, workload coverage, rare jobs, deployments, and failover behavior matter.

---

## Finding Large Indexes

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

Large unused indexes are especially valuable candidates for review because they consume storage without providing observed read value.

---

## EXPLAIN and Index Selection

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = $1;
```

Look for:

- `Index Scan`
- `Index Only Scan`
- `Bitmap Index Scan`
- `Bitmap Heap Scan`
- `Seq Scan`
- Estimated rows
- Actual rows
- Buffer usage
- Execution time

The scan type alone is not enough to diagnose index effectiveness.

---

## Sequential Scan Is Not Automatically Bad

For a small table:

```text
table = 20 pages
query returns = 15 pages
```

a sequential scan can be cheaper than using an index.

A sequential scan is a legitimate access strategy.

The real question is:

> Is the selected plan appropriate for the actual workload?

---

## Bitmap Scans

PostgreSQL can use a bitmap strategy:

```text
Index
  ↓
bitmap of matching heap pages
  ↓
heap scan
  ↓
rows
```

This can be useful when many rows match.

A bitmap scan is not evidence that an index is "bad."

It is one of PostgreSQL's access strategies.

---

## Sargability

A predicate is generally easier to optimize when the indexed column can be used directly.

Good:

```sql
WHERE created_at >= $1
```

Potentially problematic:

```sql
WHERE date(created_at) = $1
```

If the application needs expression-based filtering, consider an expression index:

```sql
CREATE INDEX idx_orders_created_date
ON orders ((date(created_at)));
```

But first determine whether the expression is actually the correct query semantics.

---

## Type Conversion and Indexes

Implicit or explicit casts can affect index usage depending on data types and expressions.

For example, avoid unnecessary conversions around indexed columns:

```sql
WHERE customer_id::text = $1
```

when:

```sql
customer_id = $1
```

with the correct parameter type is sufficient.

Prefer type-correct parameter binding.

---

## LIKE and Indexes

A B-tree index can support some prefix searches:

```sql
WHERE name LIKE 'Aran%'
```

but not generally an arbitrary leading wildcard:

```sql
WHERE name LIKE '%aran%'
```

For substring or fuzzy search, PostgreSQL-specific options such as trigram indexes may be more appropriate.

Do not create a B-tree index and assume every `LIKE` query will use it.

---

## GIN Index

GIN is useful for certain multi-valued and document-oriented data.

Common use cases include:

- Arrays
- `jsonb`
- Full-text search

Example:

```sql
CREATE INDEX idx_products_metadata
ON products
USING GIN (metadata);
```

The exact operator support depends on the indexed data type and operator class.

GIN indexes can be substantially larger and more expensive to maintain than simple B-tree indexes.

---

## GiST Index

GiST provides a framework for indexing complex data types and search strategies.

Common PostgreSQL use cases include:

- Geometric data
- Range types
- PostGIS workloads
- Similarity/search structures depending on extensions

Choose GiST based on the operators and data type being queried, not simply because the table is large.

---

## BRIN Index

BRIN indexes summarize physical ranges of table pages.

They are particularly useful for very large tables where column values correlate with physical storage order.

A common example is append-heavy time-series data:

```sql
CREATE INDEX idx_events_created_brin
ON events
USING BRIN (created_at);
```

BRIN indexes are typically much smaller than B-tree indexes.

They are not a universal replacement for B-tree indexes.

---

## Hash Index

PostgreSQL supports hash indexes for equality comparisons.

Example:

```sql
CREATE INDEX idx_users_external_id_hash
ON users
USING HASH (external_id);
```

In most conventional application workloads, B-tree is still the default choice because it supports a broader set of operations.

Use specialized index types when their access semantics provide a meaningful benefit.

---

## Index Type Comparison

| Index | Common Use |
|---|---|
| B-tree | Equality, range, ordering |
| Hash | Equality |
| GIN | Arrays, JSONB, full-text-related workloads |
| GiST | Ranges, geometric/search structures |
| SP-GiST | Specialized non-balanced search structures |
| BRIN | Huge tables with physical value correlation |

The data type and operator workload should drive index selection.

---

## Indexes and Partitioned Tables

Partitioned tables change index architecture.

Indexes are commonly created on partitions or through partitioned-index definitions so each partition has corresponding indexes.

For a partitioned table:

```text
orders
 ├── orders_2026_01
 │    └── indexes
 ├── orders_2026_02
 │    └── indexes
 └── orders_2026_03
      └── indexes
```

Partition pruning can reduce the partitions scanned, while indexes can reduce work inside the selected partitions.

These are complementary mechanisms.

---

## Indexes and Multi-Tenancy

Multi-tenant applications frequently need tenant-aware indexes.

Example:

```sql
CREATE INDEX idx_orders_tenant_created
ON orders (
    tenant_id,
    created_at DESC
);
```

This supports:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

For shared-schema multi-tenancy, tenant ID is often an important part of access-path design.

---

## Indexes and Row-Level Security

RLS can add tenant predicates to query execution.

If the common access pattern is:

```text
tenant_id + application filter
```

indexes should often reflect that combined access pattern.

For example:

```sql
CREATE INDEX idx_orders_tenant_status_created
ON orders (
    tenant_id,
    status,
    created_at DESC
);
```

But index design should be based on actual query plans and policy behavior.

Do not add every security predicate to every index automatically.

---

## Indexes and Keyset Pagination

For APIs returning recent records:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

A matching index:

```sql
CREATE INDEX idx_orders_created_id
ON orders (
    created_at DESC,
    id DESC
);
```

can support efficient navigation through ordered data.

This is usually preferable to large `OFFSET` values for high-volume APIs.

---

## Indexes and N+1 Queries

Suppose Django executes:

```text
SELECT customer
SELECT orders for customer 1
SELECT orders for customer 2
SELECT orders for customer 3
...
```

Adding an index may make each query faster, but it does not solve the N+1 architecture.

The correct fix may involve:

```text
select_related()
prefetch_related()
batch queries
```

or a different SQL shape.

Indexes optimize access paths.

They do not fix excessive query counts.

---

## Indexes and ORMs

Django:

```python
class Order(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        db_index=True,
    )
    created_at = models.DateTimeField()
```

For more complex indexes:

```python
class Meta:
    indexes = [
        models.Index(
            fields=["customer", "-created_at"],
            name="order_customer_created_idx",
        ),
    ]
```

Always validate that ORM-generated SQL matches the index design.

---

## Indexes and SQLAlchemy

SQLAlchemy:

```python
from sqlalchemy import Index

Index(
    "idx_orders_customer_created",
    Order.customer_id,
    Order.created_at.desc(),
)
```

Schema definitions should be reviewed alongside real query patterns.

An ORM migration can create an index successfully while the application still fails to benefit from it because the query shape does not match.

---

## Index Deployment in CI/CD

Production index deployment should be treated as an operational change.

A typical process:

```text
identify slow query
      ↓
validate query pattern
      ↓
design index
      ↓
test with representative data
      ↓
estimate size/resource impact
      ↓
deploy safely
      ↓
observe query plan
      ↓
observe write overhead
```

For large PostgreSQL production tables, consider:

```sql
CREATE INDEX CONCURRENTLY ...
```

when appropriate.

---

## Indexes and Replication

Creating or rebuilding large indexes can generate significant I/O and WAL-related activity.

On replicated systems, monitor:

- Replica lag
- WAL generation
- Replica replay rate
- Disk usage
- CPU
- I/O

An index deployment that is harmless on the primary can still create operational pressure downstream.

---

## Indexes and Read Replicas

Read replicas can absorb read workload, but indexes still matter on replicas.

Physical replication copies the database changes, including index-related changes.

A replica cannot magically use an index that does not exist on the primary.

For logical replication or independently managed analytical stores, schema/index management may differ.

---

## Indexes and Write-Heavy Workloads

For a write-heavy table:

```text
10 indexes
+
millions of writes
=
significant maintenance overhead
```

Ask:

- Is each index used?
- Can multiple indexes be combined?
- Is a partial index sufficient?
- Can an index be removed?
- Is the index required for a constraint?
- Is the query actually latency-sensitive?

Index count should be justified by workload value.

---

## Indexes and High Availability

Index maintenance is part of database operational planning.

Large index builds can affect:

- CPU
- I/O
- Storage
- Replication
- Backup windows
- Failover readiness

For high-availability systems, do not evaluate index changes only from the primary's perspective.

---

## Indexes and Disaster Recovery

Indexes increase:

- Database storage
- Backup size
- Restore workload

But they are normally part of the database's recoverable schema/data state.

After restoring a database, verify:

- Expected indexes exist
- Invalid indexes are absent or addressed
- Critical query plans are acceptable
- Statistics are refreshed as appropriate

---

## Monitoring Index Health

Useful signals include:

- Index size
- Index scan count
- Query latency
- Sequential vs index scans
- Write latency
- WAL volume
- Disk usage
- Bloat indicators
- Cache behavior
- Query plan changes

An index should be evaluated as part of a workload rather than as an isolated object.

---

## Production Index Review

For each proposed index, answer:

| Question | Why it matters |
|---|---|
| Which query needs it? | Prevents speculative indexes |
| How often does that query run? | Establishes ROI |
| How selective is the predicate? | Influences planner choice |
| What is the result size? | Determines access-path value |
| Does ordering matter? | May influence column order |
| Can an existing index support it? | Avoids redundancy |
| How large will it become? | Storage/cost |
| What is the write rate? | Maintenance cost |
| Is the table partitioned? | Deployment architecture |
| What happens during deployment? | Availability |
| Does replication tolerate the change? | HA/reliability |
| Can it be safely removed later? | Operational lifecycle |

---

## Common Index Mistakes

### Indexing Every Column

More indexes are not automatically better.

They increase:

- Storage
- Write overhead
- Maintenance
- Planner complexity

### Creating an Index Without a Query

Indexes should solve known access patterns.

### Assuming an Index Will Always Be Used

The planner may correctly prefer a sequential scan.

### Ignoring Composite Column Order

```text
(a, b)
```

is not equivalent to:

```text
(b, a)
```

### Creating Redundant Indexes

Overlapping indexes can create unnecessary write cost.

### Ignoring Write Performance

Every additional index has a maintenance cost.

### Using the Wrong Index Type

B-tree is not appropriate for every operator or data type.

### Ignoring Partial Indexes

A focused partial index can be much smaller and more useful for hot subsets.

### Ignoring Statistics

The planner can make poor decisions when cardinality estimates are inaccurate.

### Blaming the Index for an N+1 Problem

An index may optimize each query while the application still executes thousands of unnecessary queries.

### Using OFFSET for Deep Pagination

An index does not automatically make large offsets cheap.

### Dropping an Index Based on Short-Term Statistics

Rare but important jobs may not appear in a limited observation window.

---

## Interview Traps

### What Is an Index?

A database-maintained data structure that can provide a more efficient access path for particular query patterns.

---

### Why Doesn't PostgreSQL Always Use an Index?

Because the optimizer compares alternative plans using estimated costs.

A sequential scan can be cheaper when many rows are needed or the table is small.

---

### What Is the Default PostgreSQL Index Type?

B-tree.

---

### What Queries Are B-tree Indexes Good For?

Commonly:

```text
=
<
<=
>
>=
BETWEEN
ORDER BY
```

subject to data type/operator support and planner decisions.

---

### What Is a Composite Index?

An index containing multiple columns.

Example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

Column order matters.

---

### Why Does Column Order Matter?

The leading columns determine the index's ordering structure and therefore which query predicates and orderings can efficiently use the index.

---

### Does `(a, b)` Support `WHERE b = ...`?

Not generally as effectively as an index beginning with `b`.

PostgreSQL can sometimes use such an index in other ways, including bitmap strategies, but you should not treat `(a, b)` as equivalent to `(b)` for a query filtering only on `b`.

---

### What Is a Partial Index?

An index containing only rows satisfying a predicate.

Example:

```sql
CREATE INDEX idx_active_users_email
ON users (email)
WHERE deleted_at IS NULL;
```

---

### What Is an Expression Index?

An index on the result of an expression:

```sql
CREATE INDEX idx_users_lower_email
ON users (lower(email));
```

It is useful when queries repeatedly use the same expression.

---

### What Is a Covering Index?

An index that contains the columns needed to satisfy a query, potentially enabling an index-only scan.

In PostgreSQL, `INCLUDE` can add non-key columns:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id)
INCLUDE (status, total_amount);
```

---

### What Is an Index-Only Scan?

An execution strategy where PostgreSQL can obtain required data from the index without fetching every corresponding heap tuple, when visibility information permits it.

---

### What Is a Bitmap Index Scan?

PostgreSQL can first identify matching index entries and build a bitmap of heap pages before fetching rows.

It is useful for certain queries that match more rows than a highly selective index scan would.

---

### What Is Index Bloat?

Unused or fragmented space within an index caused by its workload and page-management behavior.

Do not diagnose bloat from size alone.

---

### Why Do Indexes Slow Down Writes?

Inserts, deletes, and relevant updates require index maintenance.

More indexes generally mean more work per write.

---

### Should Every Foreign Key Be Indexed?

Not automatically.

But foreign-key columns frequently benefit from indexes for joins and for efficient enforcement-related checks during parent-row modifications.

Evaluate the workload and constraints.

---

### What Is `CREATE INDEX CONCURRENTLY`?

A PostgreSQL index-building method designed to reduce blocking of normal table writes during index creation.

It has additional operational complexity and cannot run inside a transaction block.

---

### How Do You Determine Whether an Index Is Useful?

Combine:

```text
query workload
+
EXPLAIN
+
pg_stat_user_indexes
+
index size
+
write cost
+
production behavior
```

Do not rely on a single metric.

---

## Practical Interview Problems

### Design an Index for a Tenant-Aware API

Query:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND status = 'paid'
ORDER BY created_at DESC
LIMIT 50;
```

A reasonable starting point:

```sql
CREATE INDEX idx_orders_tenant_status_created
ON orders (
    tenant_id,
    status,
    created_at DESC
);
```

Then validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND status = 'paid'
ORDER BY created_at DESC
LIMIT 50;
```

The final design should depend on actual cardinality and workload.

---

### Design an Index for Latest Orders

Query:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Potential index:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (
    customer_id,
    created_at DESC,
    id DESC
);
```

The index matches:

```text
customer equality
→ created_at ordering
→ deterministic id tie-breaker
```

---

### Design an Index for Active Users

Query:

```sql
SELECT
    id,
    email
FROM users
WHERE deleted_at IS NULL
  AND email = $1;
```

Potential index:

```sql
CREATE INDEX idx_active_users_email
ON users (email)
WHERE deleted_at IS NULL;
```

If email uniqueness is required among active users:

```sql
CREATE UNIQUE INDEX idx_active_users_email_unique
ON users (email)
WHERE deleted_at IS NULL;
```

---

### Find Unused Index Candidates

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

Do not immediately drop zero-scan indexes.

First establish an adequate observation period and confirm that important workloads are represented.

---

## Senior-Level Index Reasoning

A senior engineer should reason through indexes in this order:

```text
Query
  ↓
Access pattern
  ↓
Expected cardinality
  ↓
Existing indexes
  ↓
Candidate index
  ↓
EXPLAIN
  ↓
Read benefit
  ↓
Write/storage cost
  ↓
Production deployment risk
  ↓
Long-term maintenance
```

This avoids the common anti-pattern:

> "The query is slow, so add an index."

Sometimes the real problem is:

- Bad join
- Incorrect cardinality
- Missing statistics
- N+1 queries
- Lock contention
- Connection pool exhaustion
- Replica lag
- Large result sets
- Poor pagination
- CPU saturation
- Wrong workload architecture

---

## Index Decision Framework

Use this sequence during an interview or production review:

1. Identify the exact slow query.
2. Confirm the expected result and cardinality.
3. Inspect existing indexes.
4. Run `EXPLAIN (ANALYZE, BUFFERS)`.
5. Determine whether the bottleneck is actually an access path.
6. Design an index around the complete access pattern.
7. Check for redundant or overlapping indexes.
8. Estimate storage and write overhead.
9. Choose an appropriate deployment strategy.
10. Measure the result after deployment.

---

## Production Index Checklist

- [ ] The index has a specific workload justification.
- [ ] The query pattern is known.
- [ ] Existing indexes have been reviewed.
- [ ] Composite column order matches the access pattern.
- [ ] Equality, range, and ordering requirements are understood.
- [ ] Selectivity and cardinality are understood.
- [ ] Partial indexing has been considered where appropriate.
- [ ] Expression indexing has been considered where appropriate.
- [ ] The index type matches the operators and data type.
- [ ] Index size has been estimated.
- [ ] Write amplification has been considered.
- [ ] Redundant indexes have been checked.
- [ ] Production query plans have been evaluated.
- [ ] `CREATE INDEX CONCURRENTLY` has been considered for large production tables.
- [ ] Replication impact has been considered.
- [ ] Monitoring is available after deployment.
- [ ] Rollback/removal strategy is understood.
- [ ] Tenant/RLS access patterns have been considered.
- [ ] ORM-generated SQL has been checked where applicable.
- [ ] The index is not being used to hide an application-level problem.

---

## Key Takeaways

- **Indexes are workload-specific access paths:** an index is valuable when it matches real filtering, joining, ordering, or lookup patterns and reduces meaningful work.
- **Index existence does not guarantee index usage:** PostgreSQL's cost-based optimizer may correctly choose sequential, bitmap, or other strategies based on cardinality, statistics, table size, and expected result volume.
- **Composite index design requires careful ordering:** equality predicates, range conditions, ordering, tenant boundaries, and deterministic pagination should be considered together rather than applying a single "most selective first" rule.
- **Indexes have operational costs:** storage, write amplification, maintenance, replication impact, cache pressure, and deployment risk must be balanced against read-performance gains.
- **Senior index tuning starts with evidence:** use exact workload data, `EXPLAIN (ANALYZE, BUFFERS)`, PostgreSQL statistics, and production behavior before adding, keeping, or removing an index.