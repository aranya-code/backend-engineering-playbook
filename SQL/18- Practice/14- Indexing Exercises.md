# 14- Indexing Exercises

## Overview

Indexes are one of the primary mechanisms PostgreSQL uses to avoid scanning an entire table for selective queries. Good indexing reduces latency and I/O, but every index also consumes storage, increases write amplification, and creates maintenance work.

These exercises focus on **index design as an engineering problem**, not on memorizing index types.

The objective is to practice reasoning from:

```text
Application access pattern
        ↓
SQL predicate / ordering / join
        ↓
Expected result grain
        ↓
Selectivity and data distribution
        ↓
Index design
        ↓
EXPLAIN plan
        ↓
Production trade-offs
```

The exercises use PostgreSQL and a realistic backend schema. For every exercise, do not immediately create an index. First determine whether an index is actually the correct solution.

---

## Practice Schema

Use the following schema:

```sql
CREATE TABLE customers (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email text NOT NULL UNIQUE,
    name text NOT NULL,
    tenant_id bigint NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orders (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id bigint NOT NULL REFERENCES customers(id),
    tenant_id bigint NOT NULL,
    status text NOT NULL
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    total_amount numeric(12, 2) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE products (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    category text NOT NULL,
    price numeric(12, 2) NOT NULL,
    active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE order_items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    product_id bigint NOT NULL REFERENCES products(id),
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price numeric(12, 2) NOT NULL
);

CREATE TABLE payments (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id bigint NOT NULL REFERENCES orders(id),
    status text NOT NULL
        CHECK (status IN ('pending', 'paid', 'failed', 'refunded')),
    amount numeric(12, 2) NOT NULL,
    paid_at timestamptz
);
```

The primary keys and unique constraints already create indexes. Do not create redundant indexes on those columns without a demonstrated access pattern.

---

## Test Data

For meaningful indexing exercises, generate enough data to make query plans interesting.

A small development dataset can be useful for correctness, but index decisions should be validated with production-like cardinality and distribution.

Example:

```sql
INSERT INTO customers (email, name, tenant_id, status)
SELECT
    'customer-' || g || '@example.com',
    'Customer ' || g,
    ((g - 1) % 100) + 1,
    CASE
        WHEN g % 20 = 0 THEN 'inactive'
        ELSE 'active'
    END
FROM generate_series(1, 100000) AS g;
```

Generate orders after customers exist:

```sql
INSERT INTO orders (
    customer_id,
    tenant_id,
    status,
    total_amount,
    created_at
)
SELECT
    c.id,
    c.tenant_id,
    CASE
        WHEN g % 20 = 0 THEN 'cancelled'
        WHEN g % 10 = 0 THEN 'pending'
        WHEN g % 5 = 0 THEN 'processing'
        ELSE 'completed'
    END,
    round((random() * 1000 + 10)::numeric, 2),
    now() - (random() * interval '365 days')
FROM generate_series(1, 1000000) AS g
JOIN customers AS c
    ON c.id = ((g - 1) % 100000) + 1;
```

After significant data loading:

```sql
ANALYZE customers;
ANALYZE orders;
```

For realistic experiments, vary the data distribution rather than assuming uniform data.

---

## Index Investigation Workflow

Use the following workflow for every indexing problem.

1. Identify the actual SQL query.
2. Identify how frequently it executes.
3. Define the expected result size.
4. Identify filtering predicates.
5. Identify join conditions.
6. Identify ordering requirements.
7. Identify grouping requirements.
8. Check existing indexes.
9. Inspect the execution plan.
10. Evaluate selectivity and cardinality.
11. Design the smallest useful index.
12. Test the plan after adding the index.
13. Measure write and storage impact.
14. Decide whether the index is worth operating in production.

Useful commands:

```sql
\d orders
```

```sql
SELECT
    indexrelid::regclass AS index_name,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY pg_relation_size(indexrelid) DESC;
```

---

## Basic Equality Queries

Start with simple equality predicates.

### Exercise

Given:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345;
```

Determine:

1. Is an index useful?
2. Does the existing foreign-key definition automatically guarantee an index?
3. What index would you create?
4. How would you validate the decision?
5. What happens if the customer owns a very large percentage of the table?

A useful candidate is:

```sql
CREATE INDEX orders_customer_id_idx
    ON orders (customer_id);
```

Validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 12345;
```

---

## Foreign-Key Indexing

A foreign key enforces referential integrity, but it does not automatically mean PostgreSQL creates the supporting index on the referencing column.

### Exercise

Inspect:

```sql
\d orders
```

Determine whether `orders.customer_id` has an index.

Then evaluate:

```sql
DELETE FROM customers
WHERE id = 12345;
```

Explain why an index on the referencing foreign-key column can be important for foreign-key checks and cascading operations.

Repeat the analysis for:

```text
order_items.order_id
order_items.product_id
payments.order_id
```

Do not blindly index every foreign key. Evaluate actual workload and referential operations.

---

## Range Queries

Consider:

```sql
SELECT *
FROM orders
WHERE created_at >= now() - interval '7 days';
```

### Exercise

Determine whether:

```sql
CREATE INDEX orders_created_at_idx
    ON orders (created_at);
```

is useful.

Test:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE created_at >= now() - interval '7 days';
```

Then repeat with:

```sql
WHERE created_at >= now() - interval '365 days';
```

Explain why the same index can be useful for one selectivity level and unnecessary for another.

---

## Equality Plus Ordering

Consider a common API query:

```sql
SELECT
    id,
    total_amount,
    status,
    created_at
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### Exercise

Design an index for this access pattern.

Compare:

```sql
CREATE INDEX orders_customer_idx
    ON orders (customer_id);
```

with:

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC, id DESC);
```

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

to compare:

- Rows scanned.
- Sort operations.
- Execution time.
- Buffer activity.
- Whether the `LIMIT` can be exploited efficiently.

---

## Composite Index Column Order

Given:

```sql
WHERE tenant_id = $1
  AND customer_id = $2
ORDER BY created_at DESC
LIMIT 50
```

Evaluate these indexes:

```sql
(tenant_id, customer_id, created_at DESC)
```

```sql
(customer_id, tenant_id, created_at DESC)
```

```sql
(created_at DESC, tenant_id, customer_id)
```

### Exercise

Determine which index best matches the query.

Then test queries that filter by:

```text
tenant_id
tenant_id + customer_id
customer_id
created_at
```

Explain the leftmost-prefix behavior of B-tree indexes and why one composite index does not necessarily serve every query involving its columns.

---

## Multiple Equality Predicates

Consider:

```sql
SELECT *
FROM orders
WHERE tenant_id = 10
  AND status = 'completed';
```

### Exercise

Compare:

```sql
(tenant_id, status)
```

with:

```sql
(status, tenant_id)
```

For equality-only predicates, determine how column order affects this specific query.

Then introduce:

```sql
ORDER BY created_at DESC
LIMIT 100;
```

and determine how the optimal index changes.

---

## Low-Cardinality Columns

Consider:

```sql
SELECT *
FROM orders
WHERE status = 'completed';
```

The status column has only a few possible values.

### Exercise

Determine whether an index on:

```sql
(status)
```

is useful.

Test the query against different data distributions:

```text
completed = 95%
completed = 50%
completed = 10%
completed = 1%
```

Observe whether PostgreSQL changes from an index-based plan to a sequential scan.

The goal is to understand that **selectivity matters more than the existence of an index**.

---

## Partial Index

Suppose most application queries retrieve completed orders:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345
  AND status = 'completed'
ORDER BY created_at DESC
LIMIT 20;
```

### Exercise

Compare:

```sql
CREATE INDEX orders_customer_status_created_idx
    ON orders (customer_id, status, created_at DESC);
```

with:

```sql
CREATE INDEX orders_completed_customer_created_idx
    ON orders (customer_id, created_at DESC)
    WHERE status = 'completed';
```

Evaluate:

- Index size.
- Query performance.
- Write overhead.
- Applicability to other statuses.
- Predicate matching.

Explain when a partial index is preferable.

---

## Soft-Delete Pattern

Assume a table contains:

```sql
deleted_at timestamptz
```

and most application queries use:

```sql
WHERE deleted_at IS NULL
```

### Exercise

Design an index for:

```sql
SELECT *
FROM customers
WHERE tenant_id = 10
  AND deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 50;
```

Compare a full composite index with a partial index:

```sql
CREATE INDEX customers_active_tenant_created_idx
    ON customers (tenant_id, created_at DESC)
    WHERE deleted_at IS NULL;
```

Explain why the partial index can be significantly smaller when deleted records are common.

---

## Unique Partial Index

Suppose only active customers should have unique usernames.

Add:

```sql
ALTER TABLE customers
ADD COLUMN username text;
```

### Exercise

Create a constraint-equivalent unique partial index:

```sql
CREATE UNIQUE INDEX customers_active_username_uidx
    ON customers (username)
    WHERE status = 'active';
```

Test:

1. Two active customers with the same username.
2. An active and inactive customer sharing a username.
3. Changing an inactive customer to active.
4. Changing an active customer to inactive.

Explain why this is different from:

```sql
UNIQUE (username)
```

---

## Covering Index

Consider:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### Exercise

Compare:

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC, id DESC);
```

with:

```sql
CREATE INDEX orders_customer_created_covering_idx
    ON orders (customer_id, created_at DESC, id DESC)
    INCLUDE (total_amount);
```

Use `EXPLAIN (ANALYZE, BUFFERS)` and determine whether an index-only scan is possible.

Explain why `INCLUDE` columns are not the same as key columns.

---

## Index-Only Scan

An index-only scan can avoid fetching table pages when the index contains all required columns and PostgreSQL's visibility information permits it.

### Exercise

Build a covering index and test:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

Inspect:

```text
Index Only Scan
Heap Fetches
```

Then perform updates and vacuum activity and observe how visibility affects heap fetches.

Explain why a covering index does not guarantee zero heap access.

---

## Expression Index

Consider case-insensitive email lookup:

```sql
SELECT *
FROM customers
WHERE lower(email) = lower('USER@EXAMPLE.COM');
```

### Exercise

Create:

```sql
CREATE INDEX customers_lower_email_idx
    ON customers (lower(email));
```

Then compare the query plan before and after.

Explain why this index is different from:

```sql
CREATE INDEX customers_email_idx
    ON customers (email);
```

---

## Expression Index for Normalized Data

Suppose application data is normalized using:

```sql
lower(trim(email))
```

### Exercise

Create an index matching the expression:

```sql
CREATE INDEX customers_normalized_email_idx
    ON customers (lower(trim(email)));
```

Test queries using:

```sql
lower(trim(email))
```

and:

```sql
lower(email)
```

Explain why an expression index must match the query expression closely enough for the planner to use it.

---

## Sargability

Compare:

```sql
SELECT *
FROM orders
WHERE created_at >= now() - interval '7 days';
```

with:

```sql
SELECT *
FROM orders
WHERE date(created_at) >= current_date - 7;
```

### Exercise

Determine how applying a function to an indexed column can affect index usage.

Then investigate whether an expression index can support the second form.

Explain why rewriting predicates to preserve indexable column expressions is often preferable when semantics permit.

---

## Pattern Matching

Test:

```sql
SELECT *
FROM customers
WHERE email LIKE 'customer-123%';
```

and:

```sql
SELECT *
FROM customers
WHERE email LIKE '%123%';
```

### Exercise

Determine:

1. Whether a normal B-tree index can help.
2. Why a left-anchored pattern differs from a leading-wildcard pattern.
3. Whether PostgreSQL-specific operator classes or extensions are appropriate.
4. When trigram indexing is preferable.

If `pg_trgm` is available, investigate:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX customers_email_trgm_idx
    ON customers USING gin (email gin_trgm_ops);
```

Do not introduce GIN/trigram indexing merely because it exists. Validate the actual search workload.

---

## Hash Index

Investigate PostgreSQL hash indexes.

### Exercise

Compare a hash index with a B-tree index for:

```sql
WHERE customer_id = $1
```

Explain:

- Supported access pattern.
- Ordering limitations.
- Range-query behavior.
- Operational considerations.
- Why B-tree is generally the default for ordinary scalar lookup workloads.

The objective is not to memorize hash-index syntax but to understand when a specialized structure is justified.

---

## B-tree vs GIN vs GiST vs BRIN

Create a comparison matrix:

| Index type | Typical use | Strength | Limitation |
|---|---|---|---|
| B-tree | Equality, range, ordering | General-purpose | Not ideal for every data type/search |
| GIN | Arrays, JSONB, full-text-style inverted lookups | Multi-value containment/search | Larger/write-heavy |
| GiST | Geometric/range/specialized operators | Flexible operator framework | Workload/operator dependent |
| BRIN | Very large naturally ordered tables | Very small index | Requires favorable physical correlation |

### Exercise

For each index type:

1. Identify one realistic backend use case.
2. Create a representative table/query.
3. Create the index.
4. Compare query plans.
5. Measure index size.
6. Explain maintenance cost.

---

## JSONB Indexing

Add a metadata column:

```sql
ALTER TABLE customers
ADD COLUMN metadata jsonb NOT NULL DEFAULT '{}'::jsonb;
```

Consider:

```sql
SELECT *
FROM customers
WHERE metadata @> '{"plan": "enterprise"}';
```

### Exercise

Test:

```sql
CREATE INDEX customers_metadata_gin_idx
    ON customers USING gin (metadata);
```

Determine:

1. Whether GIN is appropriate.
2. What operators the index supports.
3. How index size changes.
4. How frequent JSONB updates affect write cost.
5. Whether frequently queried fields should instead become relational columns.

---

## BRIN Index

Assume an append-heavy event table:

```sql
CREATE TABLE audit_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id bigint NOT NULL,
    event_type text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    payload jsonb NOT NULL
);
```

### Exercise

Assume rows are naturally inserted in chronological order.

Test:

```sql
CREATE INDEX audit_events_created_brin_idx
    ON audit_events USING brin (created_at);
```

Compare it with:

```sql
CREATE INDEX audit_events_created_btree_idx
    ON audit_events (created_at);
```

Evaluate:

- Index size.
- Query performance.
- Physical correlation.
- Table size.
- Range query selectivity.

Explain why BRIN becomes attractive for very large naturally ordered tables.

---

## Index and Sorting

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345
ORDER BY created_at DESC;
```

### Exercise

Compare:

```sql
(customer_id)
```

with:

```sql
(customer_id, created_at DESC)
```

Determine whether PostgreSQL can avoid a separate sort.

Then add:

```sql
LIMIT 20;
```

and explain why an ordering-aware index becomes even more useful.

---

## Keyset Pagination

Consider:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

### Exercise

Design the index:

```sql
CREATE INDEX orders_customer_created_keyset_idx
    ON orders (customer_id, created_at DESC, id DESC);
```

Compare it with offset pagination:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
OFFSET 100000
LIMIT 50;
```

Measure the difference as the offset grows.

---

## Join Indexing

Consider:

```sql
SELECT
    o.id,
    o.total_amount,
    p.status
FROM orders AS o
JOIN payments AS p
    ON p.order_id = o.id
WHERE o.customer_id = $1;
```

### Exercise

Determine which columns should be indexed.

Investigate:

```text
orders.customer_id
payments.order_id
```

Then add:

```sql
CREATE INDEX payments_order_id_idx
    ON payments (order_id);
```

Explain why indexing the join column on the appropriate side can reduce lookup cost.

---

## Join Plus Filter

Consider:

```sql
SELECT
    o.id,
    p.amount
FROM orders AS o
JOIN payments AS p
    ON p.order_id = o.id
WHERE o.customer_id = $1
  AND p.status = 'paid';
```

### Exercise

Compare:

```sql
payments(order_id)
```

with:

```sql
payments(order_id, status)
```

and:

```sql
payments(order_id) WHERE status = 'paid'
```

Determine which is best under different workloads.

---

## Multi-Tenant Indexing

For a shared-schema application, many queries look like:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND status = 'completed'
ORDER BY created_at DESC
LIMIT 50;
```

### Exercise

Compare:

```sql
(status, created_at DESC)
```

```sql
(tenant_id, status, created_at DESC)
```

```sql
(tenant_id, created_at DESC)
WHERE status = 'completed'
```

Evaluate the trade-offs based on:

- Tenant count.
- Tenant size distribution.
- Status distribution.
- Query patterns.
- RLS policies.
- Write volume.

---

## Tenant-Aware Uniqueness

Suppose customer emails only need to be unique within a tenant.

### Exercise

Create:

```sql
CREATE UNIQUE INDEX customers_tenant_email_uidx
    ON customers (tenant_id, lower(email));
```

Test:

1. Same email in different tenants.
2. Same email within one tenant.
3. Case variations within one tenant.
4. Tenant-scoped API lookup.

Explain why application-level uniqueness checks are insufficient under concurrent writes.

---

## RLS and Indexes

Assume row-level security uses:

```sql
tenant_id = current_setting('app.tenant_id')::bigint
```

### Exercise

Evaluate:

```sql
SELECT *
FROM orders
WHERE status = 'completed'
ORDER BY created_at DESC
LIMIT 50;
```

Determine whether an index beginning with:

```text
tenant_id
```

could be useful for tenant-scoped access.

Explain why security predicates and application predicates should both be considered during index design.

Do not treat RLS as a substitute for application authorization.

---

## Partial Index for Hot Data

Suppose only pending orders are frequently polled:

```sql
SELECT *
FROM orders
WHERE status = 'pending'
ORDER BY created_at
LIMIT 100;
```

### Exercise

Compare:

```sql
CREATE INDEX orders_status_created_idx
    ON orders (status, created_at);
```

with:

```sql
CREATE INDEX orders_pending_created_idx
    ON orders (created_at)
    WHERE status = 'pending';
```

Measure:

- Index size.
- Lookup performance.
- Update behavior when orders leave `pending`.
- Applicability to other statuses.

---

## Index Redundancy

Create:

```sql
CREATE INDEX orders_customer_idx
    ON orders (customer_id);

CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC);
```

### Exercise

Determine whether both indexes are necessary.

Investigate:

```sql
SELECT
    indexrelname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY idx_scan DESC;
```

Explain:

- Why an index can be logically redundant.
- Why usage statistics must be interpreted over a representative period.
- Why dropping an index requires evidence.
- Why a low-use index may still be operationally important.

---

## Duplicate Index Detection

Create deliberately overlapping indexes:

```text
(customer_id)
(customer_id, created_at)
(customer_id, created_at, id)
```

### Exercise

Determine:

1. Which indexes overlap.
2. Which queries each can support.
3. Whether the narrower indexes provide unique value.
4. Which index should potentially be removed.
5. How index removal affects writes.

Do not remove indexes solely because another index contains the same leading columns.

---

## Wide Indexes

Create an index with several columns:

```sql
CREATE INDEX orders_wide_idx
    ON orders (
        tenant_id,
        customer_id,
        status,
        created_at,
        completed_at,
        total_amount
    );
```

### Exercise

Evaluate:

- Index size.
- Insert/update cost.
- Cache pressure.
- WAL impact.
- Query usefulness.
- Whether `INCLUDE` columns would be more appropriate.

Explain why a wider index is not automatically a better index.

---

## Index Write Amplification

Indexes accelerate reads by adding work to writes.

### Exercise

Create a table with:

```text
0 indexes
1 index
5 indexes
10 indexes
```

Measure bulk insertion performance.

Then update indexed columns and compare the cost.

Observe:

```text
INSERT
  ↓
Heap modification
  ↓
Index maintenance
  ↓
WAL
  ↓
Replication
```

Explain why a read-heavy workload may justify more indexes than a write-heavy workload.

---

## HOT Updates

Investigate PostgreSQL heap-only tuple updates.

### Exercise

Create a table with indexed and non-indexed columns.

Update:

1. A non-indexed column.
2. An indexed column.

Inspect table/index behavior and explain why updates to indexed columns can prevent some HOT-update opportunities.

Connect this to index design for frequently updated OLTP tables.

---

## Index Bloat

Indexes can accumulate dead entries and become larger than necessary.

### Exercise

Create a workload with frequent updates/deletes.

Measure:

```sql
pg_relation_size(indexrelid)
```

over time.

Investigate:

- Autovacuum.
- Dead tuples.
- Index growth.
- `REINDEX`.
- `REINDEX CONCURRENTLY`.

Explain why index bloat is an operational concern rather than simply a storage problem.

---

## Concurrent Index Creation

For a production-sized table, investigate:

```sql
CREATE INDEX CONCURRENTLY orders_customer_created_idx
    ON orders (customer_id, created_at DESC);
```

### Exercise

Compare it with:

```sql
CREATE INDEX orders_customer_created_idx
    ON orders (customer_id, created_at DESC);
```

Research and document:

- Lock behavior.
- Build duration.
- Write impact.
- Failure behavior.
- Invalid indexes.
- Transaction restrictions.
- Deployment implications.

Inspect potentially invalid indexes:

```sql
SELECT
    indexrelid::regclass AS index_name,
    indisvalid,
    indisready
FROM pg_index
WHERE NOT indisvalid
   OR NOT indisready;
```

---

## Index Deployment Exercise

Design a CI/CD deployment for a new production index.

Scenario:

```text
Orders table
1 billion rows
High write volume
24/7 API traffic
Read replicas
Strict latency SLO
```

Your deployment plan should address:

1. Index design.
2. Capacity requirements.
3. Disk space.
4. WAL generation.
5. Replica impact.
6. Build duration.
7. `CREATE INDEX CONCURRENTLY`.
8. Monitoring.
9. Abort criteria.
10. Rollback.
11. Application deployment ordering.
12. Post-deployment validation.

Explain why index creation is itself a production workload.

---

## Index and Read Replicas

A new index created on a primary must be considered alongside replication.

### Exercise

Design a plan for:

```text
Primary
 ├── Replica A
 └── Replica B
```

Determine:

- How index creation affects WAL.
- How replicas behave while replaying changes.
- Whether replica lag can increase.
- Whether reporting queries should continue during the build.
- Whether indexes must be created independently on replicas in any architecture.

---

## Index and Partitioned Tables

Create a partitioned orders table:

```sql
CREATE TABLE partitioned_orders (
    id bigint NOT NULL,
    customer_id bigint NOT NULL,
    status text NOT NULL,
    total_amount numeric(12, 2) NOT NULL,
    created_at timestamptz NOT NULL,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
```

### Exercise

Create monthly partitions.

Then investigate indexes on:

```text
customer_id
created_at
status
```

Determine:

1. How partition pruning interacts with indexes.
2. Whether every partition needs equivalent indexes.
3. How new partitions receive indexes.
4. How index maintenance differs across partitions.
5. Whether a global index is available in PostgreSQL.

---

## Index and Partition Pruning

Consider:

```sql
SELECT *
FROM partitioned_orders
WHERE created_at >= '2026-01-01'
  AND created_at < '2026-02-01'
  AND customer_id = 123;
```

### Exercise

Use:

```sql
EXPLAIN
```

to determine:

1. Which partitions are scanned.
2. Whether partition pruning occurs.
3. Whether an index is used inside each selected partition.
4. What happens if the query omits the partition key.

Explain:

```text
Partition pruning
    +
Index access
```

are separate optimization mechanisms.

---

## Partial Index vs Partitioning

Suppose completed orders older than one year are rarely accessed.

### Exercise

Compare three strategies:

1. Partial index.
2. Table partitioning.
3. Archival to another storage system.

For each, evaluate:

- Query performance.
- Write cost.
- Operational complexity.
- Retention management.
- Storage cost.
- Recovery implications.

---

## Index and Aggregation

Consider:

```sql
SELECT
    customer_id,
    SUM(total_amount)
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

### Exercise

Determine whether an index on:

```text
(status, customer_id)
```

is useful.

Test:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and determine whether the index actually improves the workload.

Explain why indexing a grouping column does not automatically make aggregation cheap.

---

## Index and `COUNT(*)`

Test:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = $1;
```

### Exercise

Compare:

```sql
(customer_id)
```

with no supporting index.

Determine:

- Whether the index reduces table scanning.
- Whether PostgreSQL still needs heap access.
- Whether an index-only scan is possible.
- How visibility information affects the result.

Then repeat with:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = $1
  AND status = 'completed';
```

---

## Index and `EXISTS`

Consider:

```sql
SELECT EXISTS (
    SELECT 1
    FROM payments
    WHERE order_id = $1
      AND status = 'paid'
);
```

### Exercise

Design an index for this query.

Compare:

```sql
(order_id)
```

with:

```sql
(order_id, status)
```

and a partial index:

```sql
CREATE INDEX payments_paid_order_idx
    ON payments (order_id)
    WHERE status = 'paid';
```

Explain why `EXISTS` can benefit substantially from an index when it only needs to establish whether a matching row exists.

---

## Index and `ORDER BY ... LIMIT`

Consider:

```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 20;
```

### Exercise

Determine whether:

```sql
CREATE INDEX orders_created_desc_idx
    ON orders (created_at DESC);
```

is useful.

Then compare:

```sql
LIMIT 20
```

with:

```sql
LIMIT 100000;
```

Explain how the size of the requested result changes the economics of using an index.

---

## Index and `NULL`

Consider:

```sql
SELECT *
FROM orders
WHERE completed_at IS NULL;
```

### Exercise

Determine whether a normal B-tree index can support this predicate.

Then investigate:

```sql
CREATE INDEX orders_incomplete_idx
    ON orders (created_at)
    WHERE completed_at IS NULL;
```

Test:

```sql
SELECT *
FROM orders
WHERE completed_at IS NULL
ORDER BY created_at
LIMIT 100;
```

Explain why a partial index can be particularly effective for a stable operational subset.

---

## Index and Date Ranges

Consider an API:

```text
GET /orders?from=...&to=...
```

Query:

```sql
SELECT *
FROM orders
WHERE created_at >= $1
  AND created_at < $2
ORDER BY created_at DESC
LIMIT 100;
```

### Exercise

Design the index.

Then test:

- One-hour range.
- One-day range.
- One-month range.
- One-year range.

Explain why index usefulness depends on selectivity and result size, not merely on the presence of a timestamp predicate.

---

## Index and OR Conditions

Compare:

```sql
SELECT *
FROM orders
WHERE customer_id = $1
   OR status = 'pending';
```

### Exercise

Investigate how PostgreSQL may combine indexes using bitmap scans.

Create:

```text
(customer_id)
(status)
```

Then inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM orders
WHERE customer_id = 12345
   OR status = 'pending';
```

Explain:

- Bitmap Index Scan.
- Bitmap Heap Scan.
- Why combining indexes is not always cheaper than a sequential scan.

---

## Index and `IN`

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id IN (101, 102, 103, 104);
```

### Exercise

Test the query with and without:

```sql
(customer_id)
```

Then increase the number of customer IDs significantly.

Determine when a sequential or bitmap-based plan may become preferable.

---

## Index and Type Conversion

Consider:

```sql
SELECT *
FROM orders
WHERE customer_id::text = '12345';
```

### Exercise

Compare it with:

```sql
SELECT *
FROM orders
WHERE customer_id = 12345;
```

Inspect both plans.

Explain why data types should be aligned between application parameters and database columns whenever possible.

---

## ORM Indexing Exercise

Implement an equivalent index in Django.

Example:

```python
class Order(models.Model):
    customer = models.ForeignKey("Customer", on_delete=models.PROTECT)
    tenant_id = models.BigIntegerField()
    status = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(
                fields=["customer", "-created_at", "-id"],
                name="orders_customer_created_idx",
            ),
        ]
```

### Exercises

1. Generate the migration.
2. Inspect the generated SQL.
3. Determine whether the migration is safe for a large table.
4. Decide whether `CREATE INDEX CONCURRENTLY` is required.
5. Understand Django migration transaction behavior.
6. Validate the resulting PostgreSQL plan.

Do not assume ORM index declarations automatically produce production-safe deployment behavior.

---

## SQLAlchemy Indexing Exercise

Define an equivalent SQLAlchemy index.

```python
from sqlalchemy import Index

Index(
    "orders_customer_created_idx",
    Order.customer_id,
    Order.created_at.desc(),
    Order.id.desc(),
)
```

### Exercises

1. Generate the migration with Alembic.
2. Inspect generated SQL.
3. Modify the migration for concurrent creation where appropriate.
4. Validate the resulting index.
5. Test the query plan.

---

## FastAPI Query Exercise

Design:

```text
GET /customers/{customer_id}/orders
```

Requirements:

- Latest orders first.
- 50 rows per page.
- Keyset pagination.
- Stable ordering.
- Customer isolation.
- Low latency.

Use:

```sql
WHERE customer_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

### Exercise

Determine the exact index required and explain why every key appears in the index.

---

## N+1 Detection Exercise

Assume a Django endpoint loads customers and then accesses orders individually.

### Exercise

Identify the SQL pattern that produces:

```text
1 query for customers
+
N queries for orders
```

Determine:

1. Whether an index can reduce the problem.
2. Why indexing does not eliminate N+1.
3. How `select_related()` or `prefetch_related()` changes the query pattern.
4. How query count should be measured separately from query latency.

The senior-level lesson is:

> An efficient query executed 10,000 times can still be an inefficient application design.

---

## Index vs Query Rewrite

Consider a slow query:

```sql
SELECT *
FROM orders
WHERE date(created_at) = current_date
ORDER BY created_at DESC;
```

### Exercise

Instead of immediately creating an expression index, rewrite it as a range:

```sql
SELECT *
FROM orders
WHERE created_at >= current_date
  AND created_at < current_date + interval '1 day'
ORDER BY created_at DESC;
```

Compare both approaches.

Evaluate:

- Index compatibility.
- Query readability.
- Time-zone semantics.
- Index size.
- Generality.
- Production correctness.

---

## Index vs Caching

Suppose:

```text
GET /customers/{id}/summary
```

executes a query frequently.

### Exercise

Determine whether to solve the latency problem using:

- B-tree index.
- Redis cache.
- Materialized view.
- Precomputed table.
- Query rewrite.

Use these decision factors:

| Factor | Index | Redis | Materialized View | Precomputed Table |
|---|---:|---:|---:|---:|
| Fresh data | ✓ | Depends | Depends | Depends |
| Read latency | Good | Very low | Very low | Very low |
| Write complexity | Low–medium | Medium | Medium | High |
| Staleness | None | Possible | Possible | Possible |
| Operational complexity | Low | Medium | Medium | High |

Explain why caching should not be used to hide an obviously inefficient database query.

---

## Production Index Review

Review the following hypothetical index set:

```text
orders_customer_idx
orders_customer_created_idx
orders_status_idx
orders_status_created_idx
orders_created_idx
orders_tenant_idx
orders_tenant_status_created_idx
orders_tenant_customer_created_idx
orders_customer_status_created_idx
orders_customer_created_covering_idx
```

### Exercise

For each index:

1. Identify the query that justifies it.
2. Determine overlap with other indexes.
3. Estimate write overhead.
4. Estimate storage cost.
5. Determine usage.
6. Decide whether it should remain.

Produce a review table:

| Index | Query | Frequency | Size | Overlap | Write Cost | Decision |
|---|---|---:|---:|---|---|---|

Do not approve indexes without identifying the workload they serve.

---

## Production Index Removal

Suppose an index has:

```text
idx_scan = 0
```

### Exercise

Determine whether it is safe to drop.

Investigate:

- Observation period.
- Application release history.
- Rare administrative queries.
- Reporting jobs.
- Failover behavior.
- Prepared statements.
- Seasonal workloads.
- Query statistics resets.

Develop a safe removal procedure:

```text
Identify candidate
    ↓
Validate workload coverage
    ↓
Observe representative period
    ↓
Confirm replacement indexes
    ↓
Drop safely
    ↓
Monitor query plans
    ↓
Restore if necessary
```

---

## Production Index Failure Scenario

A deployment adds:

```sql
CREATE INDEX orders_customer_status_created_idx
    ON orders (customer_id, status, created_at DESC);
```

Immediately afterward:

```text
Database CPU ↑
WAL ↑
Replica lag ↑
Write latency ↑
Disk usage ↑
```

### Exercise

Determine possible causes.

Consider:

- Index build cost.
- Concurrent write workload.
- WAL generation.
- Replica replay.
- Disk pressure.
- Cache pressure.
- Existing redundant indexes.
- Autovacuum interaction.

Define:

1. Immediate mitigation.
2. Evidence to collect.
3. Whether to cancel the build.
4. Whether to remove the index later.
5. How to prevent recurrence.

---

## Production Indexing Scenario

A customer API has:

```text
10 million customers
1 billion orders
20,000 requests/second
```

Endpoint:

```text
GET /customers/{id}/orders?cursor=...
```

Query:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE customer_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

### Exercise

Design the complete database strategy.

Address:

- Primary index.
- Composite index.
- Covering index.
- Connection pooling.
- Read replicas.
- Read-after-write consistency.
- Query timeout.
- Cache usage.
- Partitioning.
- Monitoring.
- Index maintenance.
- Failure handling.

Then explain why sharding should not be introduced merely because the table contains one billion rows.

---

## Production Workload Classification

For each workload, choose an appropriate indexing strategy:

| Workload | Candidate |
|---|---|
| Point lookup by primary key | B-tree |
| Tenant-scoped recent records | Composite B-tree |
| Active subset only | Partial index |
| Case-insensitive lookup | Expression index |
| JSONB containment | GIN |
| Huge time-ordered append table | BRIN |
| Spatial/range operations | GiST |
| Search substring | Trigram/GIN |
| Keyset pagination | Composite B-tree |
| Rare analytical aggregation | Possibly no additional OLTP index |

Explain why the workload, not the data type alone, determines the design.

---

## Performance Benchmark

Create a benchmark harness that compares:

```text
No index
    ↓
Single-column index
    ↓
Composite index
    ↓
Partial index
    ↓
Covering index
```

For each variation measure:

- Planning time.
- Execution time.
- Rows returned.
- Rows scanned.
- Buffer hits.
- Buffer reads.
- Temporary I/O.
- Index size.
- Insert throughput.
- Update throughput.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and PostgreSQL statistics where appropriate.

Repeat each test multiple times and distinguish cached from cold-cache behavior.

---

## Production Observability Exercise

Define the metrics you would monitor after deploying an important index.

### Database Metrics

Track:

- Query latency.
- Query execution count.
- Database CPU.
- I/O.
- Buffer hit behavior.
- Temporary file usage.
- Lock waits.
- Connection utilization.
- WAL generation.
- Replica lag.

### Index Metrics

Track:

- Index size.
- Scan count.
- Index usage.
- Index growth.
- Dead tuples/bloat indicators.
- Build duration.
- Invalid indexes.

Useful catalog/statistics sources include:

```sql
pg_stat_user_indexes
pg_stat_all_indexes
pg_indexes
pg_index
pg_stat_statements
```

### Exercise

Create an operational dashboard design that connects:

```text
Query
  ↓
Index
  ↓
CPU / I/O
  ↓
Latency
  ↓
Application SLO
```

---

## Security Exercise

Indexing is not an authorization mechanism.

### Exercise

Consider:

```sql
SELECT *
FROM orders
WHERE tenant_id = $1
  AND customer_id = $2;
```

Determine:

1. Which columns should be indexed.
2. How tenant authorization is enforced.
3. How RLS affects the query.
4. Whether an index can expose data across tenants.
5. Whether Redis caching can accidentally bypass tenant isolation.

The index may improve access to authorized data, but authorization must remain independently enforced.

---

## Scalability Exercise

Assume:

```text
10 tenants
100,000 rows each
```

Then scale to:

```text
100,000 tenants
10,000 rows each
```

### Exercise

Determine whether the same indexes remain optimal.

Consider:

- Tenant cardinality.
- Tenant size distribution.
- Index fan-out.
- Cache locality.
- Query frequency.
- RLS.
- Partitioning.
- Sharding.

Explain why tenant count and tenant size distribution can change index economics.

---

## Cost Exercise

Estimate the operational cost of adding five large indexes.

Consider:

```text
Storage
+
Index build CPU
+
Index build I/O
+
WAL
+
Replication
+
Cache pressure
+
Write amplification
+
Maintenance
```

### Exercise

Create a cost model that compares:

```text
Read latency improvement
        versus
Operational cost
```

Decide whether every measurable query improvement is worth deploying.

---

## Reliability Exercise

A critical index becomes invalid after an interrupted concurrent build.

### Exercise

Design the recovery process.

Address:

1. Detection.
2. Query-plan impact.
3. Rebuild strategy.
4. Disk capacity.
5. Concurrent workload.
6. Replica impact.
7. Application fallback.
8. Monitoring.

Explain why database reliability includes the ability to safely recover from failed schema operations.

---

## Indexing Decision Framework

Use this framework before creating an index:

```text
Is the query important?
        |
       Yes
        ↓
Is it actually slow?
        |
       Yes
        ↓
Is the bottleneck the access path?
        |
       Yes
        ↓
Is the predicate/order selective enough?
        |
       Yes
        ↓
Can an existing index serve it?
        |
     No / Poorly
        ↓
Design smallest useful index
        ↓
Benchmark
        ↓
Measure write/storage cost
        ↓
Deploy safely
        ↓
Monitor
```

If the bottleneck is instead:

```text
Lock contention
Connection pool exhaustion
N+1 queries
CPU-heavy computation
Network transfer
Poor cardinality estimates
Replica lag
Application serialization
```

then adding an index may not solve the real problem.

---

## Common Mistakes

| Mistake | Why it happens | Better approach |
|---|---|---|
| Indexing every column | Assuming more indexes are always faster | Index real access patterns |
| Indexing every foreign key blindly | Treating FK and index as identical concepts | Evaluate joins and FK checks |
| Assuming an index is always used | Ignoring selectivity and cost | Inspect `EXPLAIN` |
| Wrong composite-column order | Designing from columns instead of workload | Start with predicates and ordering |
| Ignoring `ORDER BY` | Focusing only on filtering | Design for the complete access pattern |
| Overusing covering indexes | Optimizing one query without cost analysis | Measure index size and write impact |
| Using `DISTINCT` to hide bad joins | Treating cardinality as an indexing issue | Fix query semantics |
| Adding an index to solve N+1 | Confusing query cost with query count | Fix application query shape |
| Ignoring partial indexes | Indexing large inactive datasets | Index stable hot subsets |
| Ignoring write amplification | Considering only reads | Measure write workload |
| Creating indexes inside risky deployments | Treating DDL as trivial | Plan capacity and deployment behavior |
| Assuming `CONCURRENTLY` means no impact | Ignoring CPU/I/O/WAL costs | Monitor the build |
| Dropping unused indexes immediately | Statistics may not cover all workloads | Observe representative periods |
| Using one giant composite index | Trying to support every query | Prefer focused indexes |
| Ignoring tenant scope | Designing indexes globally | Include tenancy in workload analysis |
| Assuming partitioning replaces indexes | Confusing pruning with access paths | Evaluate both separately |
| Using cache before query optimization | Hiding database inefficiency | Fix query/index design first |
| Ignoring index bloat | Treating indexes as static structures | Monitor maintenance and growth |
| Ignoring replicas during index builds | Focusing only on primary | Monitor WAL and replay |
| Testing only tiny datasets | Plans differ at scale | Benchmark production-like data |

---

## Production Index Checklist

### Query Analysis

- [ ] Actual SQL is known.
- [ ] Query frequency is known.
- [ ] Result size is known.
- [ ] Predicate selectivity is understood.
- [ ] Ordering requirements are known.
- [ ] Join conditions are understood.
- [ ] Query plan has been inspected.

### Index Design

- [ ] Existing indexes were reviewed.
- [ ] Composite column order is intentional.
- [ ] Partial indexing was considered.
- [ ] Expression indexing was considered.
- [ ] Covering/index-only behavior was evaluated.
- [ ] Index type matches the workload.
- [ ] Redundant indexes were considered.

### Performance

- [ ] `EXPLAIN (ANALYZE, BUFFERS)` was tested.
- [ ] Cardinality estimates were reviewed.
- [ ] Sorting behavior was reviewed.
- [ ] Buffer activity was measured.
- [ ] Index size was measured.
- [ ] Write amplification was evaluated.
- [ ] Large-scale data was used for testing.

### Deployment

- [ ] Disk capacity is sufficient.
- [ ] Build duration is understood.
- [ ] WAL impact is understood.
- [ ] Replica impact is understood.
- [ ] `CREATE INDEX CONCURRENTLY` was evaluated.
- [ ] Migration transaction behavior is understood.
- [ ] Abort criteria are defined.
- [ ] Rollback/removal strategy exists.

### Operations

- [ ] Index usage is monitored.
- [ ] Index growth is monitored.
- [ ] Query latency is monitored.
- [ ] Database CPU/I/O is monitored.
- [ ] Replica lag is monitored.
- [ ] Bloat is monitored.
- [ ] Invalid indexes are detectable.
- [ ] Index ownership is documented.

---

## Interview Traps

### Does PostgreSQL always use an index if one exists?

No. The optimizer compares estimated costs and may choose a sequential scan when it expects that to be cheaper.

### Does a foreign key automatically create an index?

The foreign key constraint enforces referential integrity, but PostgreSQL does not automatically create an index on the referencing columns merely because the foreign key exists.

### Which column comes first in a composite index?

Design based on the complete workload. Equality predicates, range predicates, ordering, selectivity, and common query combinations all matter.

### Is low cardinality always bad for indexing?

No. A low-cardinality column can still be useful as part of a composite or partial index, particularly when combined with other selective predicates or a small hot subset.

### Does `CREATE INDEX CONCURRENTLY` make index creation free?

No. It reduces certain locking effects on concurrent writes, but index creation still consumes CPU, I/O, storage, and WAL and can affect replicas.

### Does an index improve `ORDER BY`?

It can, when the index ordering matches the query's required ordering and the planner determines that using it is beneficial.

### Why can an index be slower than a sequential scan?

If a query needs a large fraction of the table, following index entries and fetching many heap pages can cost more than scanning the table sequentially.

### Does an index solve N+1?

No. It may make each individual query cheaper, but the application still executes N separate queries.

### Are more indexes always better?

No. Indexes trade read performance for storage, write amplification, cache usage, WAL, and maintenance cost.

### Does partitioning eliminate the need for indexes?

No. Partition pruning reduces the number of partitions considered; indexes can still accelerate access within the selected partitions.

---

## Senior-Level Review Questions

For every proposed index, answer:

1. Which production query requires it?
2. How frequently does that query execute?
3. What is its current latency?
4. What is the expected result cardinality?
5. What is the predicate selectivity?
6. What is the expected data distribution?
7. Does an existing index already serve the query?
8. Why is the proposed column order correct?
9. Can the index eliminate sorting?
10. Can it support keyset pagination?
11. Could a partial index be smaller?
12. Could an expression index be necessary?
13. Would a covering index provide meaningful benefit?
14. What is the index size?
15. What is the write amplification?
16. How will it affect WAL?
17. How will it affect replicas?
18. How will it affect cache pressure?
19. How will it be deployed safely?
20. How will it be monitored?
21. Under what conditions should it be removed?
22. What happens when data grows by 10x?
23. What happens when tenant distribution changes?
24. Could query rewriting solve the problem more cheaply?
25. Is an index actually the correct solution?

---

## Final Practice Set

Complete these without consulting reference solutions:

1. Create an index for customer-specific order lookup.
2. Index a foreign-key access path.
3. Design an index for recent orders.
4. Design an equality-plus-ordering composite index.
5. Determine correct composite column order.
6. Test low-cardinality index behavior.
7. Create a partial index for completed orders.
8. Create a partial index for active customers.
9. Create a unique partial index.
10. Create an expression index for normalized email.
11. Test index-only scans.
12. Create a covering index using `INCLUDE`.
13. Compare B-tree and GIN.
14. Compare GIN and GiST.
15. Test BRIN on an append-heavy table.
16. Test trigram indexing.
17. Test JSONB indexing.
18. Investigate hash indexing.
19. Optimize `ORDER BY ... LIMIT`.
20. Optimize keyset pagination.
21. Optimize an `EXISTS` query.
22. Optimize a join.
23. Optimize a join with a filter.
24. Design tenant-aware indexes.
25. Design indexes compatible with RLS workloads.
26. Detect redundant indexes.
27. Detect overlapping composite indexes.
28. Measure index write amplification.
29. Investigate HOT updates.
30. Investigate index bloat.
31. Practice `CREATE INDEX CONCURRENTLY`.
32. Recover from an invalid index.
33. Design an index deployment for a billion-row table.
34. Analyze replica impact.
35. Design indexes for partitioned tables.
36. Compare partial indexing with partitioning.
37. Analyze index usefulness for aggregation.
38. Analyze `COUNT(*)` with indexes.
39. Analyze `NULL` predicates.
40. Analyze date-range queries.
41. Analyze `OR` and bitmap scans.
42. Analyze `IN` predicates.
43. Analyze implicit and explicit type conversion.
44. Implement indexes in Django.
45. Implement indexes with SQLAlchemy/Alembic.
46. Design a FastAPI keyset-pagination query.
47. Diagnose N+1 independently from indexing.
48. Compare query rewriting with adding an index.
49. Compare indexing with Redis caching.
50. Perform a complete production index review.
51. Safely remove a redundant index.
52. Diagnose an index-build incident.
53. Design indexing for a billion-row orders table.
54. Build an index performance benchmark.
55. Design production index observability.
56. Evaluate indexing cost versus latency improvement.
57. Explain every index as if defending it in a production architecture review.

## Key Takeaways

- **Index from workload evidence:** start with real predicates, joins, ordering, cardinality, frequency, and execution plans rather than indexing columns mechanically.
- **Composite indexes encode access patterns:** column order, partial predicates, expressions, covering columns, and deterministic ordering can determine whether an index meaningfully improves a query.
- **Indexes have operational cost:** storage, write amplification, WAL, cache pressure, maintenance, replication impact, and deployment risk must be included in the decision.
- **Validate at production scale:** `EXPLAIN (ANALYZE, BUFFERS)`, workload statistics, representative data distribution, and realistic concurrency are required to prove an index is beneficial.
- **Senior indexing is a system-design problem:** query rewrites, N+1 behavior, caching, partitioning, replicas, RLS, connection pools, and OLTP/OLAP workload placement may matter more than adding another index.