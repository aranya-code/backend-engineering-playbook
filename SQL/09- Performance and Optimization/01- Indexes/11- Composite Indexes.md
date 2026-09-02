# 11- Composite Indexes

## Overview

A **composite index** is an index built over two or more columns in a defined order.

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at);
```

The index is useful when queries commonly filter, join, sort, or otherwise access data using these columns together.

Composite indexes are not simply "multiple indexes combined." They are a single ordered index structure whose keys contain multiple column values:

```text
(customer_id, status, created_at)
```

Column order is therefore fundamental. It determines:

- Which query predicates can efficiently use the index.
- How much of the index can be searched.
- Whether the index can help with sorting.
- How selective the leading portion is.
- The storage and write-maintenance cost.

For backend systems, composite-index design should start from **actual query patterns**, not from the table schema alone.

## Why Composite Indexes Exist

Consider an orders table:

```sql
CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL,
    status text NOT NULL,
    created_at timestamptz NOT NULL,
    total_amount numeric(12, 2) NOT NULL
);
```

A common API query might be:

```sql
SELECT id, status, created_at, total_amount
FROM orders
WHERE customer_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 50;
```

Creating three independent indexes:

```sql
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_created ON orders (created_at);
```

is not necessarily equivalent to:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

The composite index can represent the query's access pattern directly:

```text
customer_id
     ↓
status
     ↓
created_at DESC
     ↓
matching rows
```

This can reduce the amount of data the database must inspect and may eliminate a separate sort.

## How a Composite Index Works

For an index:

```sql
CREATE INDEX idx_orders
ON orders (customer_id, status, created_at);
```

the logical ordering is based first on `customer_id`, then `status`, then `created_at`.

Conceptually:

```text
customer_id = 10
├── cancelled
│   ├── 2026-08-30
│   ├── 2026-08-29
│   └── ...
├── pending
│   ├── 2026-08-31
│   ├── 2026-08-30
│   └── ...
└── shipped
    ├── 2026-08-31
    └── ...

customer_id = 11
├── cancelled
├── pending
└── shipped
```

The physical implementation depends on the database and index type, but the important property is the **lexicographic ordering of the index key**.

This is why the first indexed column has a disproportionate effect on index usability.

## The Leftmost Prefix Principle

For a B-tree composite index:

```sql
CREATE INDEX idx_orders
ON orders (customer_id, status, created_at);
```

the index can generally support searches involving the leading portion of the key.

Think of the index as providing these logical prefixes:

```text
(customer_id)
(customer_id, status)
(customer_id, status, created_at)
```

For example:

```sql
WHERE customer_id = $1
```

can use the index.

```sql
WHERE customer_id = $1
  AND status = $2
```

can use more of the index.

```sql
WHERE customer_id = $1
  AND status = $2
  AND created_at >= $3
```

can use the full key structure effectively.

But:

```sql
WHERE status = $1
```

does not have the same direct access to the index because `status` is not the leading column.

Similarly:

```sql
WHERE created_at >= $1
```

cannot generally perform the same efficient ordered lookup through this index.

This is commonly called the **leftmost-prefix rule**.

## Why Column Order Matters

Compare:

```sql
CREATE INDEX idx_orders_a
ON orders (customer_id, status);
```

with:

```sql
CREATE INDEX idx_orders_b
ON orders (status, customer_id);
```

Both indexes contain the same columns, but they have different ordering.

| Query | `(customer_id, status)` | `(status, customer_id)` |
|---|---:|---:|
| `WHERE customer_id = ?` | Strong fit | Weak/not direct leading-prefix fit |
| `WHERE status = ?` | Weak/not direct leading-prefix fit | Strong fit |
| `WHERE customer_id = ? AND status = ?` | Strong fit | Strong fit |
| `ORDER BY customer_id, status` | Strong fit | Not equivalent |
| `ORDER BY status, customer_id` | Not equivalent | Strong fit |

Therefore:

> Composite-index design is about ordered access patterns, not merely selecting a set of columns.

## Equality, Range, and Sort Predicates

A practical way to reason about composite B-tree indexes is to classify query predicates as:

- **Equality:** `=`
- **Range:** `<`, `>`, `BETWEEN`, `>=`, `<=`
- **Ordering:** `ORDER BY`

For example:

```sql
SELECT id
FROM orders
WHERE customer_id = $1
  AND status = $2
  AND created_at >= $3
ORDER BY created_at DESC
LIMIT 50;
```

A natural index is:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

The equality predicates narrow the search first:

```text
customer_id = X
        ↓
status = Y
        ↓
created_at >= Z
        ↓
created_at DESC
```

This is often a strong design for high-volume APIs.

## Equality Columns Usually Come Before Range Columns

Suppose the query is:

```sql
WHERE tenant_id = $1
  AND status = $2
  AND created_at >= $3
```

A natural index is:

```sql
CREATE INDEX idx_events_tenant_status_created
ON events (tenant_id, status, created_at);
```

because the equality predicates define a narrow index region before the range predicate is evaluated.

Conceptually:

```text
tenant_id = 42
    ↓
status = 'pending'
    ↓
created_at >= cutoff
```

This is a useful heuristic, but it is not an absolute rule. The optimizer and database engine determine actual access strategies, and ordering requirements can change the optimal design.

## Selectivity and Column Order

Selectivity describes how effectively a predicate narrows the candidate rows.

Suppose:

```text
status:
pending → 40%
shipped → 40%
cancelled → 20%
```

and:

```text
customer_id:
individual customer → 0.001%
```

An index beginning with:

```sql
(customer_id, status)
```

may be more useful for customer-specific queries than:

```sql
(status, customer_id)
```

because `customer_id` dramatically narrows the search.

However, selectivity alone should not determine column order.

Also consider:

- Query frequency.
- Equality vs range predicates.
- Sorting requirements.
- Join patterns.
- Tenant boundaries.
- Data distribution.
- Index size.
- Write workload.
- Whether the query needs all indexed columns.

The correct design is workload-driven.

## Composite Indexes and ORDER BY

Composite indexes can sometimes eliminate an explicit sort.

Given:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at DESC);
```

this query is naturally aligned with the index:

```sql
SELECT id, created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

The database can navigate to the customer's portion of the index and read entries in the required order.

Without a suitable ordering index, the database may need to:

```text
Find matching rows
      ↓
Sort matching rows
      ↓
Return first 50
```

With a suitable index:

```text
Find customer range
      ↓
Read in required order
      ↓
Return first 50
```

This can be particularly valuable for high-traffic endpoints with `ORDER BY ... LIMIT`.

## Mixed Sort Directions

Modern relational databases can support useful ordering patterns with multi-column indexes.

For example:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id ASC, created_at DESC);
```

This can support:

```sql
WHERE customer_id = $1
ORDER BY customer_id ASC, created_at DESC;
```

or, depending on the database's index-scan capabilities, equivalent useful scan directions.

Do not assume every arbitrary combination of `ASC` and `DESC` is interchangeable. Verify the actual query plan on the target database.

## Composite Indexes and Range Predicates

Consider:

```sql
CREATE INDEX idx_orders_customer_created
ON orders (customer_id, created_at);
```

and:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
  AND created_at >= $2
  AND created_at < $3;
```

The database can first locate:

```text
customer_id = X
```

and then scan the relevant `created_at` range.

This is typically much more useful than an index beginning with `created_at` when the application almost always queries within a specific customer.

## A Range Predicate Can Limit Later Index Columns

Suppose:

```sql
CREATE INDEX idx_events
ON events (tenant_id, created_at, event_type);
```

and the query is:

```sql
WHERE tenant_id = $1
  AND created_at >= $2
  AND event_type = $3
```

The database can efficiently locate the tenant and timestamp range, but `event_type` is after the range column.

For B-tree access, a range condition on an earlier column generally limits how effectively later columns participate in narrowing the index scan.

This leads to a common design heuristic:

```text
Equality predicates
        ↓
Range predicate
        ↓
Ordering / remaining columns
```

The exact optimal arrangement depends on the workload and database engine.

## Composite Indexes vs Multiple Single-Column Indexes

These designs are not interchangeable.

### Separate Indexes

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);

CREATE INDEX idx_orders_status
ON orders (status);
```

The database may use one index, combine indexes, or choose a table scan depending on the optimizer and query.

### Composite Index

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

The index directly represents the combined access pattern.

| Characteristic | Separate Indexes | Composite Index |
|---|---|---|
| Independent predicates | Strong | Depends on leading column |
| Combined equality query | Potentially multiple strategies | Often strong |
| Ordered access | Limited | Can be excellent |
| Storage | Often higher | Can be lower than multiple overlapping indexes |
| Write maintenance | Multiple structures | One structure |
| Query flexibility | Higher for independent columns | More dependent on column order |

Do not automatically replace every single-column index with a composite index. They solve different workloads.

## Index Intersection and Bitmap Strategies

Some database engines can combine multiple indexes for a query.

For example:

```sql
WHERE customer_id = $1
  AND status = $2
```

may use both:

```text
customer_id index
       +
status index
       ↓
combined candidate set
```

PostgreSQL can use bitmap index scans to combine qualifying index results.

However, this does not mean separate indexes are always preferable.

A composite index may:

- Reduce candidate rows earlier.
- Avoid bitmap construction.
- Provide ordering.
- Reduce heap/table visits.
- Better support `LIMIT`.

Always compare actual execution plans.

## Covering Composite Indexes

A composite index can include columns used only to return results, depending on database capabilities.

PostgreSQL example:

```sql
CREATE INDEX idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC)
INCLUDE (total_amount);
```

Then:

```sql
SELECT created_at, total_amount
FROM orders
WHERE customer_id = $1
  AND status = $2
ORDER BY created_at DESC
LIMIT 50;
```

may be eligible for an index-only scan when visibility information and other conditions allow it.

The distinction is important:

```text
Key columns
→ determine index ordering/search

Included columns
→ provide additional payload without changing key ordering
```

Do not blindly include every selected column. Larger indexes increase storage and write costs.

## Composite Indexes in Multi-Tenant Systems

Multi-tenant applications often have access patterns such as:

```sql
SELECT id, status, created_at
FROM jobs
WHERE tenant_id = $1
  AND status = 'pending'
ORDER BY created_at
LIMIT 100;
```

A useful index may be:

```sql
CREATE INDEX idx_jobs_tenant_status_created
ON jobs (tenant_id, status, created_at);
```

The tenant boundary is often a critical part of the access pattern.

This can be especially important when:

- One database stores many tenants.
- Tenant sizes vary substantially.
- Most queries are tenant-scoped.
- Large tenants could otherwise force broad scans.

Do not assume `tenant_id` must always be first, though. Analyze actual queries and workload distribution.

## Composite Indexes for Pagination

Offset pagination:

```sql
SELECT id, created_at
FROM posts
WHERE tenant_id = $1
ORDER BY created_at DESC
LIMIT 50 OFFSET 50000;
```

can become expensive because the database may need to process a large number of preceding rows.

A composite index can support cursor/keyset pagination:

```sql
CREATE INDEX idx_posts_tenant_created_id
ON posts (tenant_id, created_at DESC, id DESC);
```

Query:

```sql
SELECT id, created_at
FROM posts
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

The `id` tie-breaker makes the ordering deterministic when multiple rows share the same `created_at`.

This pattern is highly useful for large datasets and high-throughput APIs.

## Django Example

Django supports composite indexes through `Meta.indexes`:

```python
from django.db import models


class Order(models.Model):
    tenant_id = models.BigIntegerField()
    customer_id = models.BigIntegerField()
    status = models.CharField(max_length=32)
    created_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(
                fields=["tenant_id", "customer_id", "-created_at"],
                name="order_tenant_customer_created_idx",
            ),
        ]
```

The field order mirrors the intended query pattern.

For a query:

```python
Order.objects.filter(
    tenant_id=tenant_id,
    customer_id=customer_id,
).order_by("-created_at")[:50]
```

the index is aligned with:

```text
tenant_id
    ↓
customer_id
    ↓
created_at DESC
```

Django model definitions should be treated as a source for database schema, but query plans should still be validated against the actual production database.

## FastAPI and SQLAlchemy Example

The same principle applies when using SQLAlchemy:

```python
from sqlalchemy import Index


class Order(Base):
    __tablename__ = "orders"

    # columns omitted for brevity

    __table_args__ = (
        Index(
            "ix_orders_tenant_customer_created",
            "tenant_id",
            "customer_id",
            "created_at",
        ),
    )
```

The ORM does not change the underlying database principles.

The important design input remains:

```text
Application query
        ↓
SQL generated
        ↓
Database access pattern
        ↓
Index design
```

## Practical Query-to-Index Workflow

A production index should normally be designed from observed or explicitly required queries.

### Identify the Query

Example:

```sql
SELECT id, status, created_at
FROM orders
WHERE tenant_id = $1
  AND customer_id = $2
  AND status = $3
ORDER BY created_at DESC
LIMIT 50;
```

### Identify Access Characteristics

```text
tenant_id     → equality
customer_id   → equality
status        → equality
created_at    → ordering
```

### Propose the Index

```sql
CREATE INDEX idx_orders_tenant_customer_status_created
ON orders (
    tenant_id,
    customer_id,
    status,
    created_at DESC
);
```

### Validate the Plan

PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, created_at
FROM orders
WHERE tenant_id = 42
  AND customer_id = 1001
  AND status = 'pending'
ORDER BY created_at DESC
LIMIT 50;
```

Look for evidence such as:

- Index Scan.
- Index Only Scan.
- Bitmap Index Scan.
- Actual rows.
- Rows removed by filter.
- Heap fetches.
- Buffer usage.
- Sort operations.
- Planning time.
- Execution time.

Do not judge an index solely by whether its name appears in the query plan.

## When a Composite Index Is a Good Choice

Use one when:

- A query frequently filters on multiple columns together.
- The same column combination appears in high-value queries.
- The index can support a frequent `ORDER BY`.
- A large table requires selective access within a tenant/customer/account boundary.
- Keyset pagination needs a deterministic ordered access path.
- A unique business rule applies to a combination of columns.

Example:

```sql
CREATE UNIQUE INDEX ux_memberships_tenant_user
ON memberships (tenant_id, user_id);
```

Here the index serves both integrity and lookup requirements.

## When Not to Add One

Avoid adding a composite index when:

- The query is rare and inexpensive.
- The table is small enough that sequential scans are cheaper.
- The index duplicates another existing index.
- The indexed columns have little useful relationship to actual queries.
- The write workload is extremely high and the performance benefit is negligible.
- The index is so wide that its storage and maintenance cost outweighs its benefit.

A common mistake is indexing every combination of columns developers encounter.

If a table has:

```text
A
B
C
D
```

it does not mean the system needs:

```text
(A)
(B)
(C)
(D)
(A,B)
(A,C)
(A,D)
(B,C)
...
```

Index design must be workload-driven.

## Redundant Composite Indexes

Suppose you have:

```sql
CREATE INDEX idx_orders_customer_status
ON orders (customer_id, status);
```

and then create:

```sql
CREATE INDEX idx_orders_customer
ON orders (customer_id);
```

The second index may be redundant for many workloads because the composite index has `customer_id` as its leading column.

However, redundancy is workload- and database-dependent.

Before removing an index, verify:

- Query plans.
- Index usage statistics.
- Write workload.
- Index size.
- Specialized query behavior.
- Constraints that depend on the index.

Do not delete indexes solely because one appears to be a prefix of another without validating production usage.

## Index Size and Write Amplification

A composite index is wider than a single-column index.

For:

```sql
(customer_id, status, created_at)
```

each index entry contains information needed to represent those key values.

Larger indexes generally mean:

- More disk space.
- More cache pressure.
- More pages to maintain.
- More write I/O.
- Potentially more index-page splits.
- More maintenance work.

For a high-write table, adding five wide indexes can materially increase write latency.

This is why senior-level index design balances:

```text
Read performance
        ↕
Write performance
        ↕
Storage
        ↕
Operational complexity
```

## Statistics and Data Distribution

The optimizer relies on statistics to estimate query costs.

For composite predicates, the relationship between columns can matter.

For example:

```text
tenant_id = 42
status = 'pending'
```

may not behave like two independent predicates if a tenant has a very different status distribution from the global table.

Modern PostgreSQL supports extended statistics for certain multi-column estimation problems:

```sql
CREATE STATISTICS orders_tenant_status_stats
ON tenant_id, status
FROM orders;

ANALYZE orders;
```

This can improve cardinality estimates for correlated columns.

Important distinction:

> Extended statistics improve query-planner estimates; they are not indexes.

They can complement, but do not replace, an appropriate composite index.

## Production Considerations

### Measure Before and After

For a significant index:

```text
Baseline query latency
        ↓
Create index
        ↓
Observe execution plan
        ↓
Measure latency
        ↓
Observe write impact
        ↓
Monitor storage/cache usage
```

Use representative production-like data.

A query that runs in 5 ms on 10,000 rows may behave very differently on 500 million rows.

### Consider Write Frequency

A composite index on a heavily updated table can be expensive.

Ask:

- How many inserts per second?
- How many updates touch indexed columns?
- How frequently does the index provide a measurable read benefit?
- Can the query tolerate a slightly slower plan?

### Avoid Wide Keys

Do not automatically index large text or payload columns.

Prefer compact, selective keys where possible.

For example:

```text
tenant_id
customer_id
created_at
```

is generally easier to maintain than a composite key containing several large text fields.

### Use Partial Indexes When the Workload Is Conditional

If most queries target active records:

```sql
CREATE INDEX idx_jobs_active_tenant_created
ON jobs (tenant_id, created_at DESC)
WHERE deleted_at IS NULL;
```

This can reduce index size and focus the access path on the relevant population.

## High Availability and Deployment

Creating an index on a large production table can consume substantial CPU, memory, disk I/O, and storage bandwidth.

For PostgreSQL:

```sql
CREATE INDEX CONCURRENTLY idx_orders_customer_status_created
ON orders (customer_id, status, created_at DESC);
```

can reduce blocking of ordinary writes compared with a standard index build.

However, concurrent index creation:

- Takes longer.
- Has additional resource overhead.
- Has transaction restrictions.
- Can leave an invalid index after certain failures.
- Requires operational monitoring.

Large index changes should therefore be handled as production schema changes, not casual application deployments.

## Monitoring Composite Indexes

Monitor:

| Signal | Why It Matters |
|---|---|
| Query latency | Determines whether the index solves the target problem |
| Index usage | Identifies valuable and unused indexes |
| Index size | Tracks storage and cache impact |
| Write latency | Detects index-maintenance overhead |
| Buffer/cache behavior | Shows memory pressure |
| Rows examined | Indicates selectivity |
| Sort operations | Shows whether ordering is being satisfied efficiently |
| Query-plan changes | Detects optimizer regressions |

In PostgreSQL, catalog statistics such as `pg_stat_user_indexes` can help identify index usage:

```sql
SELECT
    schemaname,
    relname,
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

Usage statistics should be interpreted over an appropriate observation window. An index used only during a monthly reporting workload can appear unused during a short monitoring period.

## Common Mistakes

### Treating a Composite Index as an Unordered Set

These are not equivalent for query access:

```sql
(customer_id, status)
```

and:

```sql
(status, customer_id)
```

Column order is part of the index design.

### Assuming Every Column in the Index Must Be Filtered

An index can also support:

- Ordering.
- Range scans.
- Covering access.
- Joins.
- Uniqueness.

Do not judge an index solely by whether every column appears in `WHERE`.

### Putting a Low-Value Column First Without a Reason

For:

```sql
(status, customer_id)
```

where `status` has only a few values, queries that primarily target individual customers may not benefit as much as they would from:

```sql
(customer_id, status)
```

Always start from actual access patterns.

### Creating Both Composite and Prefix Indexes Automatically

Given:

```sql
(customer_id, status, created_at)
```

do not automatically create:

```sql
(customer_id)
```

and:

```sql
(customer_id, status)
```

as well.

They may be redundant.

Validate query plans and usage before adding or removing indexes.

### Ignoring ORDER BY

A query such as:

```sql
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT 50
```

may benefit significantly from:

```sql
(customer_id, created_at DESC)
```

rather than merely:

```sql
(customer_id)
```

The latter can still filter efficiently but may require a separate sort.

### Indexing ORM Fields Without Looking at SQL

Django or SQLAlchemy model definitions do not reveal the complete production workload.

Inspect:

- Generated SQL.
- Query frequency.
- Execution plans.
- Cardinality.
- Ordering.
- Pagination strategy.

### Assuming an Index Is Always Faster

The optimizer may correctly choose a sequential scan.

For example, if a query returns a large percentage of a small table, traversing an index and then fetching many table rows can cost more than simply scanning the table.

An index is an access option, not a performance guarantee.

## Interview Traps

**"What is a composite index?"**

An index over multiple columns in a defined order, such as `(tenant_id, status, created_at)`.

**"Does column order matter?"**

Yes. For B-tree indexes, the leading columns determine which predicates can efficiently narrow the index scan and which ordering requirements can be supported.

**"Can `(a, b)` efficiently answer `WHERE b = ?`?"**

Generally not as a direct leading-prefix lookup. The exact plan is database- and workload-dependent, but `b` is not the leading column.

**"Can `(a, b)` answer `WHERE a = ? AND b = ?`?"**

Yes. This is a direct match for the composite key.

**"Should equality columns always come first?"**

It is a useful heuristic, especially when followed by a range or ordering column, but it is not an absolute law. Query shape, selectivity, ordering, and workload must be considered together.

**"Are `(a, b)` and `(b, a)` equivalent?"**

They enforce the same pairwise uniqueness if used as unique indexes, but they have different access and ordering characteristics.

**"Why not create an index for every query?"**

Indexes consume storage and increase insert/update/delete costs. Excessive indexing can make a write-heavy system substantially slower.

**"Are two single-column indexes equivalent to one composite index?"**

No. The optimizer may combine separate indexes, but a composite index can provide a more direct access path and can additionally support ordering and other query characteristics.

**"Can a composite index help pagination?"**

Yes. A properly ordered composite index is particularly useful for keyset pagination, often with a deterministic tie-breaker such as a primary key.

## Key Takeaways

- **A composite index is an ordered multi-column access structure; column order is fundamental to how a B-tree index can be used.**
- **Design indexes from real query patterns, considering equality predicates, range predicates, joins, ordering, pagination, and selectivity together.**
- **A composite index is not automatically equivalent to multiple single-column indexes and may provide better filtering, ordering, and `LIMIT` behavior.**
- **Every additional index has storage and write-maintenance costs, so redundant or unused indexes should be identified through production measurements and query-plan analysis.**
- **Validate composite indexes with realistic data using execution plans and workload metrics rather than assuming an index will improve performance.**