# 01- ORDER BY

## Overview

`ORDER BY` controls the order of rows in a SQL result set. It is essential whenever an application depends on deterministic presentation, ranking, pagination, or selecting the first or last qualifying row.

A relational table does not have an inherent display order. Without `ORDER BY`, the database is free to return qualifying rows in whatever order is produced by the chosen execution plan. An order that appears stable in development can change after an index is added, statistics change, a query plan changes, or the database is upgraded.

For backend systems, ordering is therefore a **correctness requirement**, not merely a presentation concern.

```sql
SELECT
    id,
    email,
    created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC, id DESC;
```

The query above explicitly defines:

- Primary ordering by `created_at`, newest first.
- A deterministic tie-breaker using `id`, also descending.
- A stable result order suitable for APIs and pagination.

## Basic Syntax

```sql
SELECT column1, column2
FROM table_name
ORDER BY column1 ASC;
```

`ASC` means ascending order and is the default.

```sql
SELECT column1, column2
FROM table_name
ORDER BY column1 DESC;
```

`DESC` means descending order.

Both are equivalent to explicitly specifying the direction:

```sql
ORDER BY created_at ASC;
```

```sql
ORDER BY created_at DESC;
```

Explicit direction is usually preferable in production SQL because it communicates intent clearly.

## Why ORDER BY Exists

SQL describes **what data is required**, not an inherent physical sequence in which rows must be returned.

Consider:

```sql
SELECT
    id,
    email
FROM users;
```

This query does not promise any particular order.

The database may return rows according to:

- A sequential table scan.
- An index scan.
- A bitmap scan.
- A join strategy.
- Parallel execution.
- Physical row layout.
- A different execution plan after statistics change.

Therefore, this is unsafe:

```sql
SELECT
    id,
    email
FROM users
LIMIT 20;
```

if the application expects "the newest 20 users."

Instead:

```sql
SELECT
    id,
    email
FROM users
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The second query expresses the business requirement explicitly.

## Ordering Multiple Columns

Multiple expressions can be supplied to `ORDER BY`:

```sql
SELECT
    id,
    status,
    created_at
FROM orders
ORDER BY
    status ASC,
    created_at DESC,
    id DESC;
```

The database sorts according to the first expression. Rows with equal values are then ordered by the second expression, and so on.

For example:

| status | created_at | id |
|---|---|---:|
| `completed` | 2026-08-30 10:00 | 105 |
| `completed` | 2026-08-30 10:00 | 101 |
| `completed` | 2026-08-29 09:00 | 99 |
| `pending` | 2026-08-30 11:00 | 108 |

The ordering is:

1. `status ASC`
2. `created_at DESC` within each status
3. `id DESC` when both previous values are equal

This is particularly important for pagination.

## Deterministic Ordering

A production query should have a deterministic ordering whenever the application relies on row position.

Consider:

```sql
ORDER BY created_at DESC
```

If ten rows have the same `created_at`, their relative order is not guaranteed.

A stronger ordering is:

```sql
ORDER BY created_at DESC, id DESC;
```

Assuming `id` is unique, every row now has a unique position in the ordering.

This matters for:

- Cursor/keyset pagination.
- Infinite scrolling.
- "Latest N records" endpoints.
- Batch processing.
- Reconciliation jobs.
- Export pipelines.
- Tests that compare ordered results.
- User-facing lists.

### Recommended Pattern

For timestamp-based ordering:

```sql
ORDER BY created_at DESC, id DESC;
```

For ascending traversal:

```sql
ORDER BY created_at ASC, id ASC;
```

The unique key acts as a tie-breaker.

## ORDER BY with LIMIT

`ORDER BY` and `LIMIT` are commonly used together to retrieve a bounded result set.

```sql
SELECT
    id,
    email,
    created_at
FROM users
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

This means:

> Return the first 50 rows according to the specified ordering.

Without `ORDER BY`, `LIMIT` means only:

> Return any 50 qualifying rows.

That distinction is critical.

### Latest Record

To retrieve the latest order:

```sql
SELECT
    id,
    customer_id,
    created_at
FROM orders
WHERE customer_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 1;
```

The tie-breaker ensures deterministic behavior when multiple orders share the same timestamp.

## ORDER BY with OFFSET

Offset pagination commonly looks like:

```sql
SELECT
    id,
    email,
    created_at
FROM users
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 1000;
```

The database still needs to identify and skip the preceding rows.

As offsets become large, this can become increasingly expensive.

For large or frequently accessed datasets, keyset pagination is often preferable.

## Keyset Pagination

Keyset pagination uses the previous page's ordering key as the cursor.

Suppose the previous page ended with:

```text
created_at = 2026-08-30 10:15:00
id = 5000
```

The next page can be requested with:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE tenant_id = $1
  AND (created_at, id) < ($2, $3)
ORDER BY created_at DESC, id DESC
LIMIT $4;
```

The tuple comparison corresponds to the ordering:

```text
created_at DESC
id         DESC
```

The result remains deterministic while avoiding the need to skip a large number of preceding rows.

For an ascending traversal:

```sql
WHERE (created_at, id) > ($1, $2)
ORDER BY created_at ASC, id ASC
LIMIT $3;
```

The cursor and `ORDER BY` direction must be designed together.

## NULL Ordering

`NULL` requires special attention because it does not behave like an ordinary value.

The exact default placement of `NULL` values depends on the SQL database and sort direction.

PostgreSQL defaults are:

| Ordering | Default NULL placement |
|---|---|
| `ASC` | Last |
| `DESC` | First |

PostgreSQL allows explicit control:

```sql
ORDER BY deleted_at ASC NULLS LAST;
```

or:

```sql
ORDER BY deleted_at DESC NULLS LAST;
```

This is useful when nullable fields have business meaning.

For example, an active-first ordering could be expressed as:

```sql
SELECT
    id,
    email,
    deleted_at
FROM users
ORDER BY
    deleted_at ASC NULLS FIRST,
    id ASC;
```

Always specify `NULLS FIRST` or `NULLS LAST` when the placement is part of the application's intended behavior and portability is not being delegated to database defaults.

## Ordering Expressions

`ORDER BY` can use expressions, not only stored columns.

For example:

```sql
SELECT
    id,
    first_name,
    last_name
FROM users
ORDER BY
    lower(last_name),
    lower(first_name),
    id;
```

It can also order by calculated values:

```sql
SELECT
    id,
    quantity,
    unit_price,
    quantity * unit_price AS line_total
FROM order_items
ORDER BY line_total DESC;
```

This is useful when ordering is based on a derived business value.

However, expressions can affect index usability. If a frequently executed query requires expression-based ordering, investigate whether an appropriate expression or generated-column index is supported by the database.

## ORDER BY Aliases

A selected column or expression can often be referenced by its alias:

```sql
SELECT
    id,
    quantity * unit_price AS line_total
FROM order_items
ORDER BY line_total DESC;
```

This improves readability when the expression is complex.

An alias is generally useful for:

- Computed columns.
- Reporting queries.
- Aggregated values.
- Long expressions.

Prefer meaningful aliases:

```sql
SELECT
    id,
    quantity * unit_price AS total_amount
FROM order_items
ORDER BY total_amount DESC;
```

## ORDER BY Ordinal Positions

Some SQL dialects allow ordering by the position of a selected expression:

```sql
SELECT
    id,
    email,
    created_at
FROM users
ORDER BY 3 DESC;
```

Here, `3` refers to `created_at`.

Although valid in systems such as PostgreSQL, ordinal ordering is generally less maintainable because changing the `SELECT` list can silently change the meaning of the query.

Prefer:

```sql
ORDER BY created_at DESC;
```

over:

```sql
ORDER BY 3 DESC;
```

## Ordering by Columns Not in SELECT

In many SQL queries, the ordering expression does not need to appear in the result projection.

For example:

```sql
SELECT
    id,
    email
FROM users
ORDER BY created_at DESC;
```

The application receives only `id` and `email`, while the database uses `created_at` to determine row order.

This is useful when ordering metadata is an implementation detail rather than part of the API response.

Database-specific restrictions can apply when using `DISTINCT`, `UNION`, or other set operations, so verify the behavior for the target database.

## Ordering Text

Text ordering depends on database collation and comparison rules.

For example:

```sql
SELECT
    id,
    name
FROM customers
ORDER BY name ASC;
```

The result may depend on:

- Database collation.
- Locale.
- Case sensitivity.
- Unicode comparison rules.
- Database configuration.

Do not assume that application-language string sorting and database sorting are identical.

If an API contract requires a specific ordering behavior, define and test that behavior explicitly.

## Case-Insensitive Ordering

A common PostgreSQL pattern is:

```sql
SELECT
    id,
    email
FROM users
ORDER BY lower(email) ASC;
```

This can provide case-normalized ordering.

However, applying `lower()` at query time may prevent a normal index from directly supporting the ordering.

For frequently executed workloads, investigate an expression index:

```sql
CREATE INDEX idx_users_lower_email
ON users (lower(email));
```

Then validate the actual plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    email
FROM users
ORDER BY lower(email)
LIMIT 50;
```

Do not add expression indexes solely because an expression appears in a query. Indexes have storage and write-maintenance costs.

## ORDER BY and Indexes

Sorting can require database work beyond filtering.

A query such as:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE tenant_id = $1
ORDER BY created_at DESC
LIMIT 50;
```

may benefit from an index aligned with both the filtering and ordering requirements:

```sql
CREATE INDEX idx_orders_tenant_created
ON orders (tenant_id, created_at DESC);
```

The exact optimal index depends on workload and database behavior.

Important factors include:

- Predicate selectivity.
- Column cardinality.
- Ordering direction.
- Leading index columns.
- `LIMIT` size.
- Table size.
- Data distribution.
- Write frequency.
- Whether additional columns are required.

For example, an index on:

```text
(tenant_id, created_at)
```

is fundamentally different from:

```text
(created_at, tenant_id)
```

because B-tree indexes are ordered around their leading columns.

### Senior-Level Rule

Do not ask:

> "Should I index the column used in ORDER BY?"

Ask:

> "Can an index efficiently support the complete access pattern of this query?"

That includes filtering, ordering, joins, and the expected result size.

## Sorting Cost

When an appropriate index cannot provide the requested order, the database may perform an explicit sort.

Conceptually:

```text
Rows
  │
  ▼
Filter
  │
  ▼
Sort
  │
  ▼
LIMIT
  │
  ▼
Result
```

Sorting can require:

- CPU.
- Memory.
- Temporary storage.
- Additional I/O when memory is insufficient.

For large result sets, this can become expensive.

However, a sort is not automatically a performance problem. The correct response is to inspect the execution plan and workload rather than eliminating every sort indiscriminately.

## Top-N Queries

A common production pattern is a top-N query:

```sql
SELECT
    id,
    score
FROM products
WHERE category_id = $1
ORDER BY score DESC, id DESC
LIMIT 20;
```

The database only needs the highest-ranked rows.

Depending on the execution plan and available indexes, the database may use an efficient top-N strategy rather than fully materializing and sorting every row.

This is one reason `LIMIT` can materially change query-planning decisions.

## Ordering Joined Data

Ordering after a join can use columns from related tables.

```sql
SELECT
    o.id,
    o.total_amount,
    c.name AS customer_name
FROM orders AS o
JOIN customers AS c
    ON c.id = o.customer_id
WHERE o.status = 'completed'
ORDER BY
    c.name ASC,
    o.created_at DESC,
    o.id DESC;
```

Be careful with join cardinality. If the join produces duplicate logical rows, `ORDER BY` does not fix the underlying data-shape problem.

Use the appropriate join, projection, aggregation, or deduplication strategy instead.

## ORDER BY with Aggregation

Ordering can be applied to aggregate results:

```sql
SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY customer_id
ORDER BY revenue DESC, customer_id ASC;
```

Here the database groups rows first and then orders the resulting groups.

This is useful for:

- Leaderboards.
- Revenue reports.
- Operational dashboards.
- Ranking customers.
- Batch prioritization.

For large analytical workloads, aggregate sorting can still be expensive even when the underlying filtering is efficient.

## ORDER BY and Window Functions

Window functions provide another form of ordered computation.

```sql
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS order_rank
FROM orders;
```

Here `ORDER BY` inside the window function defines the ordering used to calculate `ROW_NUMBER()`.

This is different from the query-level:

```sql
ORDER BY ...
```

The distinction is important:

| Location | Purpose |
|---|---|
| `ORDER BY` at query level | Controls final result ordering |
| `ORDER BY` inside `OVER(...)` | Controls window-function calculation |
| `ORDER BY` inside aggregate-specific constructs | Controls that specific operation where supported |

A window-function ordering does not automatically guarantee the final result order.

If the final rows must also be ordered, specify:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS order_rank
FROM orders
ORDER BY
    customer_id,
    order_rank;
```

## ORDER BY and DISTINCT

`DISTINCT` removes duplicate result rows:

```sql
SELECT DISTINCT
    customer_id
FROM orders
ORDER BY customer_id;
```

When `DISTINCT` and `ORDER BY` are combined, database-specific rules may restrict which expressions can be used for ordering.

More importantly, `DISTINCT` should not be used as a generic solution for duplicate rows introduced by an incorrect join.

If the query unexpectedly requires:

```sql
SELECT DISTINCT ...
```

investigate whether the underlying relational operation is producing more rows than intended.

## API Design and Ordering

Backend APIs should treat ordering as part of the API contract when clients depend on it.

For example:

```http
GET /orders?sort=-created_at
```

should not directly translate arbitrary client input into SQL identifiers.

Use an allowlist:

```python
SORT_FIELDS = {
    "created_at": "created_at",
    "total": "total_amount",
    "status": "status",
}
```

Then validate the requested field before constructing the SQL identifier.

Values should still be parameterized:

```python
query = """
    SELECT
        id,
        status,
        total_amount,
        created_at
    FROM orders
    WHERE tenant_id = %s
    ORDER BY created_at DESC, id DESC
    LIMIT %s
"""
```

The important distinction is:

- **Values** → parameterize them.
- **SQL identifiers** such as column names → validate against a trusted allowlist before interpolation.

Most database drivers cannot parameterize identifiers in the same way they parameterize values.

## Django Example

Django's ORM supports ordering directly:

```python
orders = (
    Order.objects
    .filter(tenant_id=tenant_id, status="completed")
    .order_by("-created_at", "-id")
)
```

Equivalent conceptual SQL:

```sql
ORDER BY created_at DESC, id DESC
```

For dynamic ordering, validate the allowed fields rather than blindly accepting request parameters.

For example:

```python
ALLOWED_ORDERING = {
    "created_at": "created_at",
    "-created_at": "-created_at",
    "total": "total_amount",
    "-total": "-total_amount",
}

ordering = ALLOWED_ORDERING.get(requested_ordering, "-created_at")

orders = (
    Order.objects
    .filter(tenant_id=tenant_id)
    .order_by(ordering, "-id")
)
```

This makes the supported API behavior explicit.

## FastAPI Example

A FastAPI endpoint might accept a controlled ordering parameter:

```python
from enum import Enum

from fastapi import FastAPI, Query

app = FastAPI()


class OrderSort(str, Enum):
    newest = "-created_at"
    oldest = "created_at"
    highest_total = "-total_amount"
    lowest_total = "total_amount"


@app.get("/orders")
def list_orders(
    sort: OrderSort = Query(default=OrderSort.newest),
):
    # Map the validated enum to a trusted SQL/ORM ordering expression.
    return {"sort": sort.value}
```

The key principle is that the API accepts a finite set of supported behaviors rather than arbitrary SQL syntax.

## Common Mistakes

### Assuming Row Order Without ORDER BY

Incorrect:

```sql
SELECT
    id,
    email
FROM users
LIMIT 20;
```

If the requirement is "20 newest users," use:

```sql
SELECT
    id,
    email
FROM users
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### Ordering by a Non-Unique Column

Potentially unstable:

```sql
ORDER BY created_at DESC;
```

Prefer:

```sql
ORDER BY created_at DESC, id DESC;
```

### Using OFFSET for Deep Pagination

Potentially expensive:

```sql
LIMIT 50 OFFSET 1000000;
```

For large datasets, evaluate keyset pagination.

### Using Ordinal Positions

Avoid:

```sql
ORDER BY 3 DESC;
```

Prefer:

```sql
ORDER BY created_at DESC;
```

### Trusting Client-Supplied Column Names

Do not construct:

```python
query = f"SELECT * FROM orders ORDER BY {requested_column}"
```

without strict validation.

Use an allowlist of permitted ordering expressions.

### Assuming ORDER BY Automatically Uses an Index

An `ORDER BY` clause does not guarantee an index-backed execution plan.

Validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...
```

### Forgetting NULL Behavior

If nullable columns are sorted, explicitly define the intended placement when it matters:

```sql
ORDER BY priority DESC NULLS LAST;
```

### Assuming Window Ordering Controls Final Output

This:

```sql
ROW_NUMBER() OVER (ORDER BY created_at DESC)
```

does not guarantee the final query result is returned in that order.

Use a query-level `ORDER BY` when final output ordering matters.

## Production Checklist

Before shipping a query that depends on ordering, verify:

- [ ] `ORDER BY` exists whenever result order matters.
- [ ] Sort direction is explicitly defined.
- [ ] A unique tie-breaker is included where deterministic ordering matters.
- [ ] `NULL` placement matches business requirements.
- [ ] Pagination is compatible with the ordering.
- [ ] Large offsets have been evaluated for performance.
- [ ] Keyset pagination is considered for large datasets.
- [ ] Dynamic ordering fields are allowlisted.
- [ ] User-provided values are parameterized.
- [ ] Indexes are evaluated against the complete query pattern.
- [ ] Important queries have been checked with realistic execution plans.
- [ ] API ordering behavior is documented and tested.

## Interview Traps

| Question | Correct reasoning |
|---|---|
| Does SQL guarantee row order without `ORDER BY`? | No. |
| Is `ASC` required? | No, it is the default, but explicit syntax can improve clarity. |
| Why add `id` after `created_at`? | To provide deterministic ordering when timestamps tie. |
| Does `LIMIT` imply an order? | No. |
| Does an index always eliminate sorting? | No. The optimizer chooses the execution strategy. |
| Is `ORDER BY` inside a window function the same as final result ordering? | No. |
| Is `ORDER BY 3` recommended? | Usually no; named expressions are clearer and safer. |
| Can arbitrary client column names be interpolated into `ORDER BY`? | No. SQL identifiers require validation/allowlisting. |
| Is offset pagination always wrong? | No. It can be appropriate for smaller datasets or shallow pages. |
| Is a sort operation automatically bad? | No. Measure its actual cost using the execution plan. |

## Key Takeaways

- SQL does not guarantee result order unless a query-level `ORDER BY` explicitly defines it.
- Use deterministic multi-column ordering, typically with a unique tie-breaker, whenever pagination or row position matters.
- Align `ORDER BY` with filtering, indexes, and pagination strategy; for large datasets, evaluate keyset pagination instead of deep offsets.
- Treat dynamic sort fields as trusted SQL identifiers only after strict allowlisting, while all user-provided values remain parameterized.
- Validate important ordering queries with realistic execution plans rather than assuming an index or sort strategy will be efficient.