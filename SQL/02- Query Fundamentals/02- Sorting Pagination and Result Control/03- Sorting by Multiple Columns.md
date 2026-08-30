# 03- Sorting by Multiple Columns

## Overview

`ORDER BY` can sort a result set using multiple expressions, each with its own direction. This is essential when a single column does not uniquely determine the required order.

A multi-column ordering is evaluated lexicographically: SQL sorts by the first expression, then uses the second expression only for rows tied on the first, then the third expression for remaining ties.

```sql
SELECT
    id,
    status,
    priority,
    created_at
FROM orders
ORDER BY
    status ASC,
    priority DESC,
    created_at DESC;
```

The database evaluates the ordering in this sequence:

```text
status ASC
   ↓
priority DESC for equal statuses
   ↓
created_at DESC for equal status + priority
```

Multi-column sorting matters directly for:

- Deterministic API responses.
- Pagination and cursor-based pagination.
- Priority queues.
- Leaderboards and rankings.
- Administrative dashboards.
- Reporting.
- Index design.
- "Latest within category" queries.
- Stable ordering of records with duplicate values.

## How Multi-Column Sorting Works

Consider:

```sql
SELECT
    id,
    status,
    created_at
FROM orders
ORDER BY
    status ASC,
    created_at DESC;
```

The database first groups the rows logically by `status` according to ascending order. Within each `status` group, `created_at` is sorted from newest to oldest.

For example:

| id | status | created_at |
|---:|---|---|
| 5 | completed | 2026-08-30 |
| 3 | completed | 2026-08-28 |
| 8 | pending | 2026-08-30 |
| 2 | pending | 2026-08-27 |
| 7 | pending | 2026-08-25 |

The important distinction is that `created_at DESC` does **not** globally reorder all rows. It only determines ordering among rows whose preceding sort expressions compare equal.

## Sort Priority

The position of an expression determines its priority.

```sql
ORDER BY
    priority DESC,
    created_at DESC,
    id ASC;
```

The effective precedence is:

| Priority | Expression | Purpose |
|---:|---|---|
| 1 | `priority DESC` | Highest priority first |
| 2 | `created_at DESC` | Newest within the same priority |
| 3 | `id ASC` | Deterministic tie-breaker |

Changing the expression order changes the result:

```sql
ORDER BY
    created_at DESC,
    priority DESC;
```

is not equivalent to:

```sql
ORDER BY
    priority DESC,
    created_at DESC;
```

The first prioritizes recency globally. The second prioritizes priority globally.

## Mixed ASC and DESC

Each ordering expression can independently specify its direction.

```sql
SELECT
    id,
    priority,
    created_at,
    customer_id
FROM orders
ORDER BY
    priority DESC,
    created_at DESC,
    customer_id ASC;
```

This means:

1. Higher priority first.
2. For equal priority, newer orders first.
3. For equal priority and timestamp, lower customer ID first.

A common production pattern is:

```sql
ORDER BY
    business_field DESC,
    timestamp DESC,
    id DESC;
```

This gives business-specific ordering while maintaining deterministic behavior.

## Deterministic Ordering

A multi-column `ORDER BY` is not automatically deterministic.

This query:

```sql
ORDER BY
    status ASC,
    created_at DESC;
```

can still produce an unspecified order when multiple rows have identical `status` and `created_at`.

For example:

| id | status | created_at |
|---:|---|---|
| 101 | pending | 2026-08-30 10:00:00 |
| 102 | pending | 2026-08-30 10:00:00 |
| 103 | pending | 2026-08-30 10:00:00 |

Add a unique tie-breaker:

```sql
ORDER BY
    status ASC,
    created_at DESC,
    id DESC;
```

Now every row has a unique position assuming `id` is unique.

This is particularly important for pagination.

## Business Ordering vs Tie-Breaking

A useful way to design an `ORDER BY` clause is to separate business requirements from determinism.

```sql
ORDER BY
    priority DESC,      -- business ordering
    created_at DESC,    -- secondary business ordering
    id DESC             -- deterministic tie-breaker
```

This makes the intent clear:

```text
Business requirement
        ↓
Primary ordering
        ↓
Secondary ordering
        ↓
Unique tie-breaker
```

The unique key should normally be the final ordering expression rather than replacing meaningful business ordering.

## Sorting Within Groups

Multi-column sorting is useful when records belong to categories and each category needs its own internal ordering.

```sql
SELECT
    id,
    department,
    salary
FROM employees
ORDER BY
    department ASC,
    salary DESC;
```

This produces departments in ascending order, with the highest-paid employees first within each department.

Another backend example:

```sql
SELECT
    id,
    tenant_id,
    created_at
FROM events
ORDER BY
    tenant_id ASC,
    created_at DESC,
    id DESC;
```

Each tenant's events are ordered from newest to oldest.

This pattern frequently appears in multi-tenant systems where the application needs predictable ordering inside a partition-like grouping.

## Latest Record Per Group

Multi-column ordering is often part of solutions for "latest record per group" queries.

For example, to inspect orders by customer with newest orders first:

```sql
SELECT
    customer_id,
    id,
    created_at,
    total_amount
FROM orders
ORDER BY
    customer_id ASC,
    created_at DESC,
    id DESC;
```

The ordering itself does not select one row per customer. It only establishes the order.

If the requirement is specifically "return the latest order for every customer," use a query technique appropriate to the database, such as PostgreSQL's `DISTINCT ON`:

```sql
SELECT DISTINCT ON (customer_id)
    customer_id,
    id,
    created_at,
    total_amount
FROM orders
ORDER BY
    customer_id,
    created_at DESC,
    id DESC;
```

The ordering is important because `DISTINCT ON` retains the first row encountered for each `customer_id`.

For portable SQL, a window function is often preferable:

```sql
SELECT
    customer_id,
    id,
    created_at,
    total_amount
FROM (
    SELECT
        customer_id,
        id,
        created_at,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY
                created_at DESC,
                id DESC
        ) AS row_number
    FROM orders
) ranked
WHERE row_number = 1;
```

The ordering inside the window function determines which row receives `row_number = 1` within each customer.

## Multi-Column Sorting and Pagination

Pagination requires particular care because the ordering defines the position of every row.

Offset pagination:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY
    created_at DESC,
    id DESC
LIMIT 50
OFFSET 100;
```

is simple but becomes less attractive for deep pages.

Keyset pagination uses the last row of the previous page as a cursor.

For descending order:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY
    created_at DESC,
    id DESC
LIMIT 50;
```

The cursor represents:

```text
(created_at, id)
```

The ordering and cursor comparison must agree.

```text
ORDER BY created_at DESC, id DESC
              │         │
              └─────────┴── cursor columns
```

The `id` tie-breaker is critical. Without it, rows sharing the same timestamp can be skipped, duplicated, or inconsistently positioned across pages.

## Mixed-Direction Keyset Pagination

Mixed directions require more care.

Consider:

```sql
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC;
```

The cursor predicate cannot blindly use:

```sql
WHERE (priority, created_at, id) < (...)
```

because tuple comparison assumes a consistent comparison direction, while the desired ordering contains both `DESC` and `ASC`.

The predicate must represent the lexicographic ordering explicitly:

```sql
WHERE
       priority < $1
    OR (priority = $1 AND created_at > $2)
    OR (
        priority = $1
        AND created_at = $2
        AND id > $3
    )
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC
LIMIT 50;
```

This is an important senior-level pagination consideration: **the cursor predicate must encode the exact same ordering semantics as the `ORDER BY`.**

## Multi-Column Sorting and Indexes

Indexes can significantly reduce the work required to filter and order large datasets.

Consider:

```sql
SELECT
    id,
    tenant_id,
    status,
    priority,
    created_at
FROM jobs
WHERE tenant_id = $1
  AND status = $2
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC
LIMIT 50;
```

A potentially useful PostgreSQL index is:

```sql
CREATE INDEX idx_jobs_tenant_status_priority_created_id
ON jobs (
    tenant_id,
    status,
    priority DESC,
    created_at ASC,
    id ASC
);
```

The exact index should be validated using the actual workload and execution plan.

The general principle is:

```text
WHERE equality / selective predicates
                ↓
ORDER BY columns
                ↓
LIMIT / pagination
```

A well-aligned index can allow the database to retrieve a small ordered range instead of scanning many rows and performing a large sort.

### Indexes Are Workload-Specific

Do not automatically create an index for every `ORDER BY`.

Indexes introduce:

- Additional storage.
- Write amplification.
- Insert/update overhead.
- Vacuum or maintenance work.
- Operational complexity.

Evaluate the complete query:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    tenant_id,
    status,
    priority,
    created_at
FROM jobs
WHERE tenant_id = 42
  AND status = 'pending'
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC
LIMIT 50;
```

The optimizer may choose a different plan depending on table size, data distribution, selectivity, statistics, and available indexes.

## Sorting by Expressions

`ORDER BY` can use expressions rather than only raw columns.

```sql
SELECT
    id,
    first_name,
    last_name
FROM users
ORDER BY
    LOWER(last_name) ASC,
    LOWER(first_name) ASC,
    id ASC;
```

Another example:

```sql
SELECT
    id,
    price,
    discount_percent
FROM products
ORDER BY
    price * (1 - discount_percent / 100.0) ASC,
    id ASC;
```

Expression-based ordering can be useful, but it may prevent straightforward use of a normal index on the underlying column.

If this becomes performance-critical, consider an expression index or a schema-level representation appropriate to the database and workload.

## NULL Values in Multi-Column Ordering

`NULL` values require explicit consideration.

In PostgreSQL:

```sql
ORDER BY
    priority DESC NULLS LAST,
    created_at DESC,
    id DESC;
```

This means:

1. Highest non-NULL priorities first.
2. Rows without a priority after them.
3. Newest rows first within equal priority values.
4. `id` provides deterministic ordering.

Explicit `NULLS FIRST` or `NULLS LAST` makes business intent clearer and avoids depending on database-specific defaults.

## Backend API Example

Suppose an order-management API supports:

```text
GET /orders?sort=priority
GET /orders?sort=-priority
GET /orders?sort=recent
GET /orders?sort=oldest
```

Do not expose arbitrary SQL ordering expressions.

Instead, define an application-level ordering contract:

```python
ORDERING_MAP = {
    "priority": ("priority", "id"),
    "-priority": ("-priority", "-id"),
    "recent": ("-created_at", "-id"),
    "oldest": ("created_at", "id"),
}
```

With Django:

```python
ordering = ORDERING_MAP.get(
    requested_sort,
    ("-created_at", "-id"),
)

orders = (
    Order.objects
    .filter(tenant_id=tenant_id)
    .order_by(*ordering)
)
```

This provides:

- A controlled API contract.
- Protection against arbitrary SQL fragments.
- Predictable pagination behavior.
- A clear place to add supported sort modes.

## Production Example: Job Queue

Consider a database-backed job queue where jobs have priority and creation time.

The requirement is:

> Process higher-priority jobs first; among jobs with the same priority, process older jobs first.

The ordering is:

```sql
SELECT
    id,
    payload,
    priority,
    created_at
FROM jobs
WHERE status = 'pending'
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC
LIMIT 100;
```

The `id` tie-breaker ensures deterministic ordering.

For concurrent workers in PostgreSQL, row locking can be combined with this ordering:

```sql
SELECT
    id,
    payload,
    priority,
    created_at
FROM jobs
WHERE status = 'pending'
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

The responsibilities are different:

| Mechanism | Responsibility |
|---|---|
| `priority DESC` | Business priority |
| `created_at ASC` | FIFO behavior within priority |
| `id ASC` | Deterministic tie-breaking |
| `FOR UPDATE` | Row locking |
| `SKIP LOCKED` | Avoid waiting on rows claimed by another worker |

This distinction is important in production queue implementations.

## Common Mistakes

### Reversing Sort Priority

These queries have different semantics:

```sql
ORDER BY
    priority DESC,
    created_at DESC;
```

```sql
ORDER BY
    created_at DESC,
    priority DESC;
```

The first prioritizes priority. The second prioritizes recency.

Always identify the primary business requirement before adding secondary ordering.

### Assuming Multiple Columns Guarantee Uniqueness

This:

```sql
ORDER BY
    status,
    created_at;
```

may still leave ties.

If deterministic ordering matters, add a unique final key:

```sql
ORDER BY
    status,
    created_at,
    id;
```

### Using a Non-Unique Cursor

This is fragile:

```sql
ORDER BY created_at DESC;
```

with:

```text
cursor = created_at
```

Multiple rows can share the same timestamp.

Prefer:

```sql
ORDER BY
    created_at DESC,
    id DESC;
```

with a cursor containing both values.

### Using Incorrect Cursor Operators

For:

```sql
ORDER BY
    created_at DESC,
    id DESC;
```

the next-page predicate uses:

```sql
WHERE (created_at, id) < ($1, $2)
```

For ascending ordering:

```sql
ORDER BY
    created_at ASC,
    id ASC;
```

the corresponding predicate is:

```sql
WHERE (created_at, id) > ($1, $2)
```

Mixed directions require an explicit predicate that reflects each direction.

### Assuming ORDER BY Guarantees Queue Correctness

Ordering determines which rows are preferred. It does not prevent two workers from selecting the same row.

Concurrency control requires appropriate transactions and locking semantics.

### Creating Large Numbers of Sorting Indexes

Adding indexes for every possible API sort combination can create excessive write and storage overhead.

Prefer a small number of indexes aligned with important, high-volume query patterns.

### Sorting in Application Code

Avoid fetching a large dataset and then sorting it in Python:

```python
orders = list(Order.objects.filter(tenant_id=tenant_id))
orders.sort(key=lambda order: order.created_at, reverse=True)
```

when the database can perform the required ordering:

```python
orders = (
    Order.objects
    .filter(tenant_id=tenant_id)
    .order_by("-created_at", "-id")
)
```

Database-side filtering and sorting can reduce network transfer and application memory usage and allows the optimizer to use indexes.

## Production Best Practices

### Define Ordering Explicitly

If an API or report requires a specific order, put it in `ORDER BY`.

Do not depend on:

- Insertion order.
- Primary-key order.
- Physical row order.
- Current execution plans.
- Database storage behavior.

### Make API Ordering Stable

For production APIs, prefer:

```sql
ORDER BY created_at DESC, id DESC;
```

over:

```sql
ORDER BY created_at DESC;
```

when pagination or deterministic responses matter.

### Align Pagination With Ordering

The following three components should describe the same logical sequence:

```text
ORDER BY
   ↕
cursor fields
   ↕
cursor predicate
```

If one changes, the others usually need to change as well.

### Validate With Realistic Data

Use realistic row counts and distributions when evaluating sorting performance.

A query that is fast against 10,000 development rows may behave very differently against hundreds of millions of production rows.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

to understand whether the database is:

- Using an appropriate index.
- Scanning excessive rows.
- Performing an expensive sort.
- Reading heavily from disk.
- Returning a small result from a large amount of work.

### Keep Business Ordering Separate From Tie-Breaking

A readable ordering clause makes its intent obvious:

```sql
ORDER BY
    priority DESC,
    created_at ASC,
    id ASC;
```

The first expressions implement business semantics; the final expression provides deterministic behavior.

## Interview Traps

| Question | Correct answer |
|---|---|
| How does SQL evaluate multiple `ORDER BY` columns? | In the specified priority order; later expressions resolve ties from earlier expressions. |
| Can each column have a different direction? | Yes. |
| Does `ORDER BY a, b` mean `b` globally sorts the result? | No. `b` only orders rows tied on `a`. |
| Does multi-column ordering guarantee deterministic results? | Only if the complete ordering uniquely identifies every row or otherwise establishes the required deterministic order. |
| Why add `id` as the final ordering column? | To provide a unique tie-breaker. |
| Why is this important for cursor pagination? | It gives every row a deterministic position and prevents ambiguous cursors. |
| Can an index help with multi-column sorting? | Yes, when its structure aligns with the query's filtering and ordering requirements. |
| Does every `ORDER BY` require an index? | No. Indexes should be justified by workload and execution plans. |
| Does `ORDER BY` make concurrent queue processing safe? | No. Concurrency requires transaction and locking semantics. |
| Is `ORDER BY created_at DESC, id DESC` equivalent to `ORDER BY id DESC, created_at DESC`? | No. The first prioritizes `created_at`; the second prioritizes `id`. |

## Key Takeaways

- Multi-column `ORDER BY` is evaluated lexicographically: later expressions resolve ties created by earlier expressions.
- Each ordering expression can independently use `ASC` or `DESC`, allowing precise business ordering.
- Add a unique tie-breaker such as `id` when deterministic results or reliable cursor pagination are required.
- Design indexes around the complete query pattern—filtering, ordering, pagination, and workload—not around `ORDER BY` alone.
- Cursor predicates, ordering columns, and sort directions must describe the same logical sequence, especially when mixed `ASC` and `DESC` directions are used.