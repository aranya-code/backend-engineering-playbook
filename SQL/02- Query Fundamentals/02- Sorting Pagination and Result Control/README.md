# README

## Overview

This section covers how SQL controls the order, size, and traversal of result sets. These capabilities are fundamental to backend APIs because database queries frequently need to return a predictable subset of a potentially large dataset.

The topics progress from basic ordering to production-grade pagination:

- `ORDER BY` for deterministic result ordering.
- `ASC` and `DESC` for controlling sort direction.
- Multi-column sorting for deterministic tie-breaking.
- Sorting expressions for computed and conditional ordering.
- `LIMIT` and database-specific row limiting syntax.
- `OFFSET` for position-based pagination.
- Offset pagination for page-oriented interfaces.
- Keyset pagination for efficient sequential traversal.
- Cursor pagination for opaque API continuation tokens.
- Tradeoffs between pagination strategies and when to use each.

The central engineering principle is:

> Pagination is not only a UI concern. It is a database access-pattern decision involving ordering, indexing, consistency, and API design.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- ORDER BY](./01-%20ORDER%20BY.md) | Sorting query results |
| 02 | [02- ASC and DESC](./02-%20ASC%20and%20DESC.md) | Ascending and descending order |
| 03 | [03- Sorting by Multiple Columns](./03-%20Sorting%20by%20Multiple%20Columns.md) | Deterministic ordering and tie-breaking |
| 04 | [04- Sorting Expressions](./04-%20Sorting%20Expressions.md) | Conditional and computed ordering |
| 05 | [05- LIMIT and TOP](./05-%20LIMIT%20and%20TOP.md) | Restricting returned rows |
| 06 | [06- OFFSET](./06-%20OFFSET.md) | Skipping rows |
| 07 | [07- Pagination Fundamentals](./07-%20Pagination%20Fundamentals.md) | Designing bounded result sets |
| 08 | [08- Offset Pagination](./08-%20Offset%20Pagination.md) | Page-number-based APIs |
| 09 | [09- Keyset Pagination](./09-%20Keyset%20Pagination.md) | Efficient sequential traversal |
| 10 | [10- Cursor Pagination](./10-%20Cursor%20Pagination.md) | Opaque API continuation |
| 11 | [11- Offset vs Keyset vs Cursor](./11-%20Offset%20vs%20Keyset%20vs%20Cursor.md) | Architectural tradeoffs |
| 12 | [12- Pagination Rules and Tradeoffs](./12-%20Pagination%20Rules%20and%20Tradeoffs.md) | Production constraints |
| 13 | [13- When to Choose Each Pagination Strategy](./13-%20When%20to%20Choose%20Each%20Pagination%20Strategy.md) | Requirement-driven decisions |

## Ordering Results with ORDER BY

SQL does not guarantee a meaningful row order unless the query specifies one.

Use:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
ORDER BY created_at DESC;
```

For deterministic ordering, especially when pagination is involved, include a unique tie-breaker:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
ORDER BY created_at DESC, id DESC;
```

The second ordering column is applied when two rows have the same `created_at`.

This distinction becomes critical when implementing keyset or cursor pagination.

## ASC and DESC

`ASC` sorts values from lower to higher according to the database's ordering rules, while `DESC` reverses the direction.

```sql
SELECT id, created_at
FROM orders
ORDER BY created_at DESC;
```

Multiple columns can use different directions:

```sql
SELECT
    id,
    status,
    created_at
FROM orders
ORDER BY status ASC, created_at DESC;
```

The direction is specified independently for each ordering expression.

## Multi-Column Sorting

Multi-column ordering creates a hierarchy of sorting rules.

```sql
ORDER BY
    status ASC,
    created_at DESC,
    id DESC;
```

Conceptually:

```text
status
  ↓
created_at
  ↓
id
```

The final unique column is often used as a deterministic tie-breaker.

This pattern is particularly important for pagination because a query such as:

```sql
ORDER BY created_at DESC
```

may not define a unique position for rows sharing the same timestamp.

A stronger pagination ordering is:

```sql
ORDER BY created_at DESC, id DESC
```

with a matching composite index where appropriate.

## Sorting Expressions

`ORDER BY` can sort by expressions rather than only raw columns.

Examples include:

```sql
ORDER BY
    CASE
        WHEN status = 'priority' THEN 0
        WHEN status = 'normal' THEN 1
        ELSE 2
    END,
    created_at DESC;
```

This is useful when business priority does not directly correspond to a stored column.

Other common expressions include:

- `CASE`.
- Date transformations.
- Numeric calculations.
- Conditional ranking.
- Database-supported functions.

Expression-based ordering can be useful, but it may prevent efficient use of ordinary indexes depending on the database, expression, and available functional indexes.

For production workloads, inspect the query plan rather than assuming the expression is cheap.

## LIMIT and TOP

Limiting results prevents an endpoint or query from returning an unbounded number of rows.

PostgreSQL and MySQL commonly use:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC
LIMIT 50;
```

SQL Server commonly uses:

```sql
SELECT TOP (50)
    id,
    created_at
FROM orders
ORDER BY created_at DESC;
```

Modern SQL Server queries can also use `OFFSET ... FETCH` for pagination.

The exact syntax varies by database, but the engineering purpose is the same:

```text
potentially large dataset
        ↓
ordering
        ↓
bounded result
```

Always pair a result limit with an appropriate ordering when the application depends on which rows are returned.

## OFFSET

`OFFSET` skips rows before returning the requested result set.

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 100;
```

This represents:

```text
skip 100 rows
return next 50 rows
```

Offset is useful for page-oriented interfaces:

```text
page = 3
page_size = 50

OFFSET = (3 - 1) × 50
       = 100
```

However, deep offsets can become increasingly expensive because the database may need to process or traverse many rows before producing the requested page.

## Pagination Fundamentals

Pagination exists to keep database and API responses bounded.

Without pagination:

```text
1,000,000 rows
       ↓
database
       ↓
application
       ↓
serialization
       ↓
network
       ↓
client
```

This can cause excessive:

- Database work.
- Application memory usage.
- CPU consumption.
- Serialization time.
- Network traffic.
- Request latency.

A production API should generally enforce a bounded page size:

```text
default limit = 50
maximum limit = 100
```

The client should not be allowed to request arbitrarily large result sets.

## Offset Pagination

Offset pagination represents position using a numeric offset or page number.

```http
GET /orders?page=20&page_size=50
```

The corresponding SQL concept is:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 950;
```

### Advantages

- Simple API model.
- Easy to understand.
- Natural page-number UX.
- Supports arbitrary page access.
- Straightforward implementation in frameworks such as Django.

### Limitations

- Deep offsets can become expensive.
- Concurrent inserts/deletes can shift positional boundaries.
- Large datasets may make deep-page traversal inefficient.
- Exact counts can add additional database work.

Offset pagination is often appropriate for administrative interfaces and moderate-sized datasets where users genuinely need numbered pages.

## Keyset Pagination

Keyset pagination represents the next position using values from the ordered columns.

For:

```sql
ORDER BY created_at DESC, id DESC
```

the next page can use:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE (created_at, id) < (:created_at, :id)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

An appropriate index could be:

```sql
CREATE INDEX idx_orders_created_id
ON orders (created_at DESC, id DESC);
```

Instead of asking the database to skip an absolute number of rows, the query identifies the next position from the existing ordering boundary.

### Advantages

- Efficient for deep sequential traversal.
- Works well with large datasets.
- Less sensitive to positional shifts caused by inserts.
- Naturally suited to infinite scrolling and feeds.

### Limitations

- Arbitrary page-number access is not natural.
- Requires deterministic ordering.
- Requires careful index design.
- More complex than basic offset pagination.

## Cursor Pagination

Cursor pagination exposes an opaque continuation token to the API client.

Example:

```http
GET /orders?limit=50
```

Response:

```json
{
  "results": [],
  "has_next": true,
  "next_cursor": "eyJ2IjoxLCJpZCI6MTA0Mn0="
}
```

The client then sends:

```http
GET /orders?limit=50&cursor=eyJ2IjoxLCJpZCI6MTA0Mn0=
```

The cursor can internally represent:

```text
created_at
id
sort direction
cursor version
```

The API does not need to expose those database details directly.

A common architecture is:

```text
Opaque cursor
     ↓
Decode + validate
     ↓
Keyset boundary
     ↓
Parameterized SQL
     ↓
Composite index
     ↓
Next page
```

Cursor pagination is therefore commonly implemented using keyset pagination internally.

## Offset vs Keyset vs Cursor

| Property | Offset | Keyset | Cursor |
|---|---|---|---|
| Page numbers | Excellent | Poor | Poor |
| Random page access | Excellent | Poor | Poor |
| Deep sequential traversal | Weaker | Strong | Strong |
| Large datasets | Conditional | Strong | Strong |
| Public API abstraction | Moderate | Low if exposed directly | Strong |
| Implementation complexity | Low | Moderate | Moderate/High |
| Requires deterministic ordering | Recommended | Required | Required |
| Infinite scrolling | Possible | Strong | Strong |
| Opaque continuation token | No | Not inherently | Yes |

The distinction between keyset and cursor is important:

> Keyset describes how the database finds the next rows; cursor describes how the API represents the continuation position.

## Pagination Rules and Tradeoffs

Several rules should be treated as production design constraints.

### Use Deterministic Ordering

Prefer:

```sql
ORDER BY created_at DESC, id DESC;
```

over:

```sql
ORDER BY created_at DESC;
```

when timestamps can collide.

### Bound Page Size

Use:

```text
default = 50
maximum = 100
```

rather than accepting unlimited values.

### Index the Access Pattern

If the query commonly uses:

```sql
WHERE customer_id = :customer_id
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

consider an index such as:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at DESC, id DESC);
```

The exact index should be validated using the database's execution plan and workload.

### Avoid Assuming Pagination Guarantees Snapshot Consistency

Separate HTTP requests normally execute against potentially different database states.

Pagination can provide a stable continuation boundary without providing a complete historical snapshot.

If strict snapshot semantics are required, a separate design is necessary.

## Choosing the Pagination Strategy

A useful decision table is:

| Requirement | Recommended starting point |
|---|---|
| Admin dashboard with page numbers | Offset |
| User jumps to page 50 | Offset |
| Small/moderate dataset | Offset |
| Deep pages are common | Keyset |
| Activity feed | Keyset + cursor |
| Infinite scroll | Keyset + cursor |
| Large public REST API | Keyset + cursor |
| Sequential data export | Keyset |
| Exact page counts required | Offset, with count costs considered |
| Sequential traversal without totals | Keyset/cursor |
| Database details should remain hidden | Cursor |

The goal is not to use the most sophisticated mechanism. The goal is to use the simplest strategy that satisfies:

```text
product requirements
+ data volume
+ access pattern
+ consistency requirements
+ performance requirements
```

## Backend API Considerations

Pagination is part of the API contract.

A production endpoint should define:

- Default page size.
- Maximum page size.
- Ordering semantics.
- Pagination mechanism.
- Invalid cursor behavior.
- Cursor versioning where applicable.
- Filter compatibility.
- Whether cursors expire.
- Whether previous-page traversal is supported.
- Consistency expectations.

For example:

```python
from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/orders")
def list_orders(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
):
    # Decode and validate cursor, then execute the appropriate query.
    ...
```

The API layer should validate pagination parameters before they reach the data-access layer.

## Django Considerations

Django's paginator is convenient for page-number-based interfaces:

```python
from django.core.paginator import Paginator

queryset = Order.objects.order_by("-created_at", "-id")

paginator = Paginator(queryset, 50)
page = paginator.get_page(page_number)
```

This is appropriate when offset-style pagination matches the product requirement.

For large sequential feeds, a queryset using keyset predicates may be more appropriate than relying exclusively on page numbers.

## Performance and Query Plans

Never select a pagination strategy based only on theoretical complexity.

Use realistic production-sized datasets and inspect execution plans:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE (created_at, id) < (:created_at, :id)
ORDER BY created_at DESC, id DESC
LIMIT 51;
```

Measure:

- Query latency.
- Rows scanned.
- Rows returned.
- Buffer reads.
- Database CPU.
- Application CPU.
- Memory usage.
- Serialization time.
- Response size.
- P95/P99 API latency.

Fetching `limit + 1` rows is a common technique for determining whether another page exists without performing an expensive total count:

```text
requested = 50
fetch = 51

50 rows → return page + has_next = false
51 rows → return first 50 + has_next = true
```

## Production Pitfalls

### Treating Offset as Always Bad

Offset is not inherently wrong. It is often the correct choice for moderate datasets and page-number-based interfaces.

### Treating Cursor as Always Better

Cursor pagination introduces additional API and implementation complexity. It should solve a real access-pattern problem.

### Sorting Only by a Non-Unique Column

This can create ambiguous pagination boundaries.

Prefer:

```sql
ORDER BY created_at DESC, id DESC;
```

when `created_at` alone is not unique.

### Allowing Unlimited Limits

A request such as:

```http
GET /orders?limit=1000000
```

can become a resource-exhaustion problem.

Always enforce server-side limits.

### Assuming an Index Automatically Solves Pagination

Indexes help only when they align with the query's filtering and ordering requirements.

Validate the actual query plan.

### Exposing Raw Cursor State

A cursor such as:

```text
created_at=...&id=...
```

can unnecessarily couple clients to database implementation details.

Opaque cursors provide stronger API abstraction.

### Assuming Pagination Provides a Consistent Snapshot

Pagination across multiple requests does not automatically freeze the underlying dataset.

Define the consistency model explicitly when it matters.

## Operational Considerations

Pagination should be observable like any other critical database access pattern.

Monitor:

- Endpoint latency by pagination type.
- P95/P99 database latency.
- Deep-offset frequency.
- Requested page sizes.
- Rows scanned versus rows returned.
- Slow query frequency.
- Invalid cursor rates.
- Database CPU and I/O.
- API response sizes.
- Error rates.

A useful migration signal is:

```text
high-volume endpoint
        +
large dataset
        +
frequent deep offsets
        ↓
evaluate keyset/cursor pagination
```

For high-traffic services, load testing should include realistic pagination depths and concurrent writes rather than testing only the first page.

## Interview-Level Decision Rule

A concise decision framework is:

```text
Need numbered/random pages?
    → Offset

Need efficient sequential traversal?
    → Keyset

Need an opaque public continuation token?
    → Cursor

Need both efficient traversal and a clean public API?
    → Cursor + Keyset
```

The final decision should still account for:

```text
dataset size
query shape
indexes
ordering
concurrency
consistency
API requirements
operational complexity
```


## Key Takeaways

- Use **offset pagination** when page numbers and arbitrary page access are genuine requirements.
- Use **keyset pagination** for large datasets and efficient sequential traversal with deterministic ordering.
- Use **cursor pagination** when a public API needs an opaque continuation token, commonly backed by keyset queries.
- Treat **ordering, indexing, page-size limits, and consistency** as part of the pagination design rather than separate concerns.
- Choose the simplest strategy that satisfies the workload, then validate it with realistic data, execution plans, and production-level load tests.