# 02- ASC and DESC

## Overview

`ASC` and `DESC` define the direction in which SQL sorts rows when used with `ORDER BY`.

- `ASC` sorts values in ascending order.
- `DESC` sorts values in descending order.
- `ASC` is the default when no direction is specified.

Ordering direction is a small SQL feature with significant production impact. It affects API result ordering, pagination, reporting, ranking, index design, and queries that retrieve the first or last matching record.

```sql
SELECT
    id,
    email,
    created_at
FROM users
ORDER BY created_at DESC;
```

This returns the newest users first.

The database does **not** guarantee any ordering unless a query-level `ORDER BY` specifies it.

## ASC

`ASC` means ascending order.

For numeric values:

```sql
SELECT
    id,
    price
FROM products
ORDER BY price ASC;
```

Conceptually:

```text
10
25
50
75
100
```

For timestamps:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at ASC;
```

The oldest rows appear first.

For text, the exact ordering depends on the database's collation and comparison rules.

### Explicit vs Default ASC

These are equivalent:

```sql
ORDER BY created_at;
```

```sql
ORDER BY created_at ASC;
```

Although `ASC` is optional, explicitly specifying it can make intent clearer, especially in complex queries with multiple ordering expressions.

## DESC

`DESC` means descending order.

For numeric values:

```sql
SELECT
    id,
    price
FROM products
ORDER BY price DESC;
```

Conceptually:

```text
100
75
50
25
10
```

For timestamps:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC;
```

The newest rows appear first.

`DESC` is particularly common for:

- Latest records.
- Recent activity feeds.
- Most expensive products.
- Highest scores.
- Newest deployments.
- Most recent audit events.
- Descending pagination.

## ASC vs DESC

| Direction | Meaning | Typical use |
|---|---|---|
| `ASC` | Lowest/oldest/smallest first | Earliest events, lowest price, chronological processing |
| `DESC` | Highest/newest/largest first | Latest records, highest score, recent activity |

Example:

```sql
SELECT
    id,
    total_amount
FROM orders
ORDER BY total_amount ASC;
```

returns the lowest totals first.

```sql
SELECT
    id,
    total_amount
FROM orders
ORDER BY total_amount DESC;
```

returns the highest totals first.

## Multiple Sort Columns

Each `ORDER BY` expression can have its own direction.

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

The database first sorts by `status` ascending. For rows with the same status, it sorts by `created_at` descending.

This is a lexicographic ordering:

```text
status ASC
    └── created_at DESC
```

For example:

| status | created_at |
|---|---|
| completed | 2026-08-30 |
| completed | 2026-08-29 |
| pending | 2026-08-30 |
| pending | 2026-08-28 |

### Direction Is Per Expression

This:

```sql
ORDER BY
    priority DESC,
    created_at ASC;
```

is different from:

```sql
ORDER BY
    priority ASC,
    created_at DESC;
```

The direction applies to the individual expression immediately preceding it.

## Deterministic Ordering

Sorting by one non-unique column does not necessarily produce a deterministic order.

Consider:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC;
```

If several orders have exactly the same `created_at`, their relative order is unspecified.

For production APIs, add a unique tie-breaker:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY
    created_at DESC,
    id DESC;
```

Now the ordering is deterministic assuming `id` is unique.

A common pattern is:

```text
primary business ordering
        +
unique tie-breaker
```

For example:

```sql
ORDER BY updated_at DESC, id DESC;
```

or:

```sql
ORDER BY priority DESC, id ASC;
```

The tie-breaker's direction should be chosen deliberately based on the required ordering and pagination strategy.

## ASC/DESC with LIMIT

`ASC` and `DESC` become particularly important when combined with `LIMIT`.

To retrieve the oldest five orders:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY
    created_at ASC,
    id ASC
LIMIT 5;
```

To retrieve the newest five:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY
    created_at DESC,
    id DESC
LIMIT 5;
```

Without `ORDER BY`, this:

```sql
SELECT
    id,
    created_at
FROM orders
LIMIT 5;
```

does **not** mean "five newest" or "five oldest."

It means five qualifying rows in an unspecified order.

## Finding the Latest or Earliest Record

A common backend query is finding the most recent record.

```sql
SELECT
    id,
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY
    created_at DESC,
    id DESC
LIMIT 1;
```

For the earliest:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY
    created_at ASC,
    id ASC
LIMIT 1;
```

This pattern is preferable to retrieving every matching row and determining the first or last row in application code.

## NULL Values

`NULL` is not an ordinary comparable value, so its position during sorting requires attention.

The default `NULL` placement is database-specific.

For PostgreSQL:

| Ordering | Default |
|---|---|
| `ASC` | `NULL` values last |
| `DESC` | `NULL` values first |

PostgreSQL allows explicit placement:

```sql
ORDER BY deleted_at ASC NULLS LAST;
```

or:

```sql
ORDER BY deleted_at DESC NULLS LAST;
```

When `NULL` has business meaning, make the intended behavior explicit.

For example, to prioritize records with a known priority:

```sql
SELECT
    id,
    priority
FROM jobs
ORDER BY
    priority DESC NULLS LAST,
    id ASC;
```

This avoids relying on implicit database-specific behavior.

## ASC/DESC and Indexes

Ordering direction can interact with index design.

Suppose an API frequently executes:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
ORDER BY
    created_at DESC,
    id DESC
LIMIT 50;
```

An index aligned with the access pattern may help:

```sql
CREATE INDEX idx_orders_tenant_created_id
ON orders (tenant_id, created_at DESC, id DESC);
```

The exact index should be validated against the database engine, workload, and execution plans.

The important principle is not:

> "Every `ORDER BY` column needs an index."

Instead:

> "Design indexes around the complete access pattern: filtering, ordering, joins, and result size."

### Mixed Directions

Consider:

```sql
ORDER BY
    priority DESC,
    created_at ASC;
```

The index strategy may need to account for the mixed ordering.

In PostgreSQL, B-tree indexes can support forward or backward scans, and explicit index column directions become particularly relevant when different columns require different sort directions.

Always validate the actual plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    priority,
    created_at
FROM jobs
WHERE tenant_id = 42
ORDER BY
    priority DESC,
    created_at ASC
LIMIT 50;
```

## Pagination

Ordering direction must remain consistent with the pagination strategy.

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
OFFSET 1000;
```

is straightforward but can become expensive for deep pages.

Keyset pagination can use the last row from the previous page as a cursor.

For descending order:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY
    created_at DESC,
    id DESC
LIMIT $4;
```

The comparison operator and `ORDER BY` direction are related:

```text
DESC ordering → fetch rows after cursor using <
ASC ordering  → fetch rows after cursor using >
```

For ascending pagination:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND (created_at, id) > ($2, $3)
ORDER BY
    created_at ASC,
    id ASC
LIMIT $4;
```

A unique tie-breaker is critical because the cursor must identify an unambiguous position in the ordered result set.

## API Ordering

A backend API may expose supported sort options:

```http
GET /orders?sort=-created_at
```

The `-` convention commonly represents descending order.

Do not translate arbitrary client input directly into SQL:

```python
# Unsafe pattern
query = f"SELECT * FROM orders ORDER BY {sort_field}"
```

Instead, map API values to trusted SQL expressions:

```python
ORDERING_MAP = {
    "created_at": "created_at ASC",
    "-created_at": "created_at DESC",
    "total": "total_amount ASC",
    "-total": "total_amount DESC",
}

ordering = ORDERING_MAP.get(requested_sort, "created_at DESC")
```

Values should still be passed as parameters rather than interpolated into SQL.

The distinction is important:

| Input | Correct handling |
|---|---|
| `tenant_id = 123` | Parameterize |
| `limit = 50` | Validate and parameterize where supported |
| `sort = created_at` | Allowlist the identifier/expression |
| `sort = -created_at` | Map to a trusted expression |

## Django Ordering

Django represents descending ordering with a leading `-`.

```python
orders = (
    Order.objects
    .filter(tenant_id=tenant_id)
    .order_by("-created_at", "-id")
)
```

Ascending ordering:

```python
orders = (
    Order.objects
    .filter(tenant_id=tenant_id)
    .order_by("created_at", "id")
)
```

Dynamic API ordering should be constrained to known fields:

```python
ORDERING_MAP = {
    "newest": ("-created_at", "-id"),
    "oldest": ("created_at", "id"),
    "highest_total": ("-total_amount", "-id"),
    "lowest_total": ("total_amount", "id"),
}

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

This provides a controlled API contract and avoids exposing arbitrary query expressions.

## FastAPI Ordering

FastAPI can validate supported ordering options using an enum:

```python
from enum import Enum

from fastapi import FastAPI, Query

app = FastAPI()


class OrderSort(str, Enum):
    newest = "newest"
    oldest = "oldest"
    highest_total = "highest_total"
    lowest_total = "lowest_total"


ORDERING_MAP = {
    OrderSort.newest: ("created_at DESC", "id DESC"),
    OrderSort.oldest: ("created_at ASC", "id ASC"),
    OrderSort.highest_total: ("total_amount DESC", "id DESC"),
    OrderSort.lowest_total: ("total_amount ASC", "id ASC"),
}


@app.get("/orders")
def list_orders(
    sort: OrderSort = Query(default=OrderSort.newest),
):
    return {
        "ordering": ORDERING_MAP[sort],
    }
```

In a real application, the validated ordering would be passed to the ORM or a carefully constructed SQL query.

## Time-Based Ordering

Timestamp ordering is common in backend systems:

```sql
SELECT
    id,
    event_type,
    created_at
FROM audit_events
WHERE tenant_id = $1
ORDER BY
    created_at DESC,
    id DESC
LIMIT 100;
```

This is appropriate for an activity feed or recent audit events.

However, timestamps may have limited precision depending on the schema and database configuration. Multiple records can therefore share the same timestamp.

A unique secondary key avoids ambiguous ordering:

```sql
ORDER BY created_at DESC, id DESC;
```

For distributed systems, also consider the semantic meaning of the timestamp. `created_at`, event time, ingestion time, and processing time are not interchangeable.

## Processing Queues

Ascending ordering can be useful when processing work chronologically:

```sql
SELECT
    id,
    payload
FROM jobs
WHERE status = 'pending'
ORDER BY
    created_at ASC,
    id ASC
LIMIT 100;
```

This can implement a "process oldest pending work first" policy.

For concurrent workers, however, `ORDER BY` alone does not provide safe job claiming. PostgreSQL workloads may use row-locking patterns such as:

```sql
SELECT
    id,
    payload
FROM jobs
WHERE status = 'pending'
ORDER BY
    created_at ASC,
    id ASC
FOR UPDATE SKIP LOCKED
LIMIT 100;
```

The ordering determines which eligible rows are preferred; locking controls concurrent ownership.

This distinction matters in Celery-like worker systems and custom database-backed queues.

## Sorting Text

Text ordering is governed by database comparison and collation rules.

```sql
SELECT
    id,
    name
FROM customers
ORDER BY name ASC;
```

Do not assume that database ordering exactly matches Python sorting:

```python
sorted(names)
```

or browser-side JavaScript sorting.

Differences can arise from:

- Locale.
- Collation.
- Case sensitivity.
- Unicode rules.
- Database configuration.

If a user-facing API promises a specific lexical ordering, test the behavior using representative production data.

## Common Mistakes

### Assuming ASC Means "Oldest" for Every Data Type

`ASC` means the database's ascending comparison order.

For timestamps, this normally means oldest first:

```sql
ORDER BY created_at ASC;
```

For numbers, it means smallest first:

```sql
ORDER BY price ASC;
```

For text, ordering depends on collation.

Do not generalize "ASC = oldest" beyond naturally ordered temporal values.

### Assuming DESC Is Always Better for APIs

Many APIs use newest-first ordering:

```sql
ORDER BY created_at DESC;
```

but the correct direction depends on the business requirement.

For chronological event processing, `ASC` may be the correct choice.

### Omitting the Tie-Breaker

Potentially unstable:

```sql
ORDER BY created_at DESC;
```

More deterministic:

```sql
ORDER BY created_at DESC, id DESC;
```

### Using OFFSET Without Considering Scale

This can become expensive:

```sql
LIMIT 50 OFFSET 500000;
```

For large datasets, evaluate keyset pagination.

### Assuming NULL Ordering Is Universal

Do not rely on one database's defaults when portability or business correctness matters.

Use explicit syntax where supported:

```sql
ORDER BY priority DESC NULLS LAST;
```

### Allowing Arbitrary Sort Expressions

Do not let an API client provide unrestricted SQL fragments.

Bad:

```text
?sort=created_at DESC, (arbitrary SQL)
```

Use an allowlist or enum-based mapping.

### Assuming Index Direction Alone Determines Performance

An index with the correct columns may still not be selected.

Always inspect the actual execution plan and consider:

- Filtering predicates.
- Cardinality.
- Selectivity.
- `LIMIT`.
- Table size.
- Data distribution.
- Index maintenance cost.

## Production Considerations

### API Contracts

Define supported sorting behavior explicitly.

For example:

```text
newest
oldest
highest_total
lowest_total
```

This is more stable than exposing arbitrary database columns.

### Stable Pagination

For cursor-based pagination:

```text
ORDER BY fields
        ↓
must match
        ↓
cursor comparison
        ↓
must provide
        ↓
deterministic position
```

Changing the ordering direction or tie-breaker can invalidate existing cursor semantics.

### Index Validation

For latency-sensitive endpoints, benchmark the query with realistic data:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at
FROM orders
WHERE tenant_id = 42
ORDER BY
    created_at DESC,
    id DESC
LIMIT 50;
```

Do not optimize based solely on query text.

### Monitoring

For production queries where sorting contributes to latency, monitor:

- Query execution latency.
- Rows examined.
- Rows returned.
- Sort operations.
- Temporary disk usage where exposed by the database.
- Buffer/cache behavior.
- Query-plan changes.

PostgreSQL's `EXPLAIN (ANALYZE, BUFFERS)` is particularly useful when investigating whether an ordering strategy is causing excessive work.

## Interview Traps

| Question | Correct answer |
|---|---|
| What is the default direction of `ORDER BY`? | `ASC`. |
| Does `DESC` mean largest/newest first? | Usually for numeric/timestamp values, but technically it means descending according to the data type's comparison rules. |
| Can different columns use different directions? | Yes. |
| Does `ORDER BY created_at DESC` guarantee deterministic ordering? | Not when multiple rows have equal timestamps. |
| Why add `id DESC` after `created_at DESC`? | To provide a deterministic unique tie-breaker. |
| Does `LIMIT` establish ordering? | No. |
| Is `ASC` always equivalent to "oldest first"? | No; that interpretation applies naturally to temporal data. |
| Does an index always eliminate a sort? | No. The optimizer chooses the execution plan. |
| Can arbitrary client input safely become an `ORDER BY` expression? | No. Sort identifiers/expressions should be allowlisted. |
| Does ordering inside a window function determine final result order? | No. A query-level `ORDER BY` is required for final output ordering. |

## Key Takeaways

- `ASC` and `DESC` define per-expression sort direction, with `ASC` being the default.
- Use a unique tie-breaker such as `id` when ordering must be deterministic, especially for pagination and APIs.
- Match sort direction, cursor comparison, and index design when building scalable pagination or latency-sensitive queries.
- Treat client-controlled ordering as an allowlisted API capability, never as arbitrary SQL input.
- Explicitly handle `NULL` ordering and validate performance with realistic execution plans rather than assuming an index will make sorting cheap.