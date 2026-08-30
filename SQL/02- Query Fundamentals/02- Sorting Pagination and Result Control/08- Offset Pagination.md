# 08- Offset Pagination

## Overview

Offset pagination divides a result set into pages using two values:

- `LIMIT` — maximum number of rows returned.
- `OFFSET` — number of qualifying rows skipped before returning results.

The basic pattern is:

```sql
SELECT
    id,
    email,
    created_at
FROM users
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 100;
```

Conceptually:

```text
Filtered + ordered result set

| 0 ... 99 | 100 ... 149 | 150 ... |
| skipped  | returned     | next     |
            ↑
          OFFSET
```

Offset pagination is simple, widely supported, and particularly useful when clients need numbered pages or direct navigation to a page. Its main weakness is that large offsets can require the database to process many rows that will ultimately be discarded.

For production systems, offset pagination should therefore be evaluated against:

- Dataset size.
- Maximum page depth.
- Query selectivity.
- Index design.
- Frequency of inserts/deletes.
- Consistency requirements.
- Whether users actually need arbitrary page navigation.

## Basic Syntax

The general form is:

```sql
SELECT columns
FROM table
WHERE conditions
ORDER BY sort_columns
LIMIT page_size
OFFSET offset_value;
```

For example:

```sql
SELECT
    id,
    status,
    total_amount,
    created_at
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC, id DESC
LIMIT 25
OFFSET 50;
```

This returns up to 25 rows after the first 50 qualifying rows in the specified order.

### Page Number Calculation

For page-based APIs:

```text
offset = (page - 1) × page_size
```

Example:

| Page | Page size | OFFSET |
|---:|---:|---:|
| 1 | 25 | 0 |
| 2 | 25 | 25 |
| 3 | 25 | 50 |
| 10 | 25 | 225 |
| 100 | 25 | 2475 |

Page 3 with a page size of 25 becomes:

```sql
SELECT
    id,
    status,
    created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 25
OFFSET 50;
```

The offset is a zero-based row position, while the page number exposed by an API is usually one-based.

## Why OFFSET Exists

Offset pagination is useful because it maps naturally to user-facing page navigation.

A web application can expose:

```text
Page 1  Page 2  Page 3  ...  Page 20
```

and translate:

```text
page=3&page_size=50
```

into:

```sql
LIMIT 50 OFFSET 100
```

This makes offset pagination particularly convenient for:

- Admin dashboards.
- Back-office applications.
- Search interfaces.
- Reporting screens.
- Moderate-sized datasets.
- APIs where arbitrary page navigation is a requirement.

Its simplicity is its primary advantage.

## Execution Model

It is important to understand what `OFFSET` means to the database.

Consider:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC
LIMIT 50
OFFSET 100000;
```

The database generally cannot simply jump to "row 100000" as if the result were an array with constant-time indexing.

Depending on the query and execution plan, the database may need to:

1. Identify qualifying rows.
2. Produce them in the requested order.
3. Traverse/process rows before the offset.
4. Discard the first 100,000 rows.
5. Return the next 50 rows.

Conceptually:

```text
Query
  │
  ▼
Filter
  │
  ▼
Order / index traversal
  │
  ▼
Rows 1 ──────────────── 100,000
  │                       │
  │                       └── discarded
  ▼
Rows 100,001 ────────── 100,050
  │
  └── returned
```

The exact behavior depends on the database engine, indexes, query predicates, statistics, and execution plan. `OFFSET` is therefore not inherently equivalent to an O(1) jump.

## LIMIT and OFFSET Together

`OFFSET` normally becomes useful when combined with `LIMIT`.

```sql
SELECT
    id,
    email
FROM users
ORDER BY id
LIMIT 50
OFFSET 100;
```

The logical result is:

```text
Skip 100
Return at most 50
```

Therefore:

```text
Rows requested = 100 + 50
Rows returned  = at most 50
```

A large `LIMIT` is also dangerous:

```sql
LIMIT 1000000 OFFSET 0;
```

Even with offset pagination, always enforce a maximum page size.

## The Importance of ORDER BY

Never build application pagination around an unordered result:

```sql
SELECT *
FROM users
LIMIT 50
OFFSET 100;
```

Without an explicit ordering requirement, the application cannot establish what "page 3" actually means.

Use:

```sql
SELECT *
FROM users
ORDER BY id
LIMIT 50
OFFSET 100;
```

For a timestamp-based ordering, use a unique tie-breaker:

```sql
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 100;
```

The unique `id` makes the ordering deterministic when multiple rows have the same `created_at`.

## Deterministic Pagination

Pagination assumes that the result set has a stable ordering.

Suppose:

```text
created_at
----------
10:00
10:00
10:00
10:01
```

If the query uses only:

```sql
ORDER BY created_at DESC
```

multiple rows can have the same ordering value.

Prefer:

```sql
ORDER BY created_at DESC, id DESC
```

This creates a deterministic ordering:

```text
(created_at, id)
```

The same principle is important for both offset and cursor pagination, although cursor pagination depends on it even more directly.

## Deep OFFSET Performance

Consider an API endpoint backed by a table containing 100 million rows:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 5000000;
```

The application only needs 50 rows, but the database may need to process a very large number of preceding rows before reaching them.

This can cause:

- Increased CPU usage.
- More index or heap page reads.
- Longer query latency.
- Increased database load.
- Greater contention with other workloads.
- Poor tail latency for deep pages.

The key misconception is:

> `LIMIT 50` means the database only has to process 50 rows.

That is not necessarily true when a large `OFFSET` is present.

## Indexing Offset Pagination

Indexes can substantially improve offset pagination, but they do not magically make arbitrarily large offsets free.

Suppose:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 1000;
```

A useful composite index may be:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (customer_id, created_at DESC, id DESC);
```

This aligns the index with:

```text
WHERE customer_id = ...
ORDER BY created_at DESC, id DESC
```

The database can then efficiently traverse the relevant ordered index entries.

Still, it may need to walk past the offset rows.

Always verify the actual plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 1000;
```

Do not judge pagination performance from SQL syntax alone.

## Offset Pagination with Filtering

Pagination normally applies after filtering.

For example:

```sql
SELECT
    id,
    email,
    created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 100;
```

The conceptual sequence is:

```text
users
  │
  ▼
WHERE status = 'active'
  │
  ▼
ORDER BY created_at DESC, id DESC
  │
  ▼
OFFSET 100
  │
  ▼
LIMIT 50
  │
  ▼
response
```

The page represents the filtered dataset, not the entire table.

For frequently executed queries, consider an index that supports the filtering and ordering pattern.

## Offset Pagination with JOINs

Be careful when pagination is combined with one-to-many joins.

Consider:

```sql
SELECT
    customers.id,
    customers.email,
    orders.id AS order_id
FROM customers
JOIN orders
    ON orders.customer_id = customers.id
ORDER BY customers.id
LIMIT 50
OFFSET 100;
```

If a customer has multiple orders, the query produces multiple result rows for the same customer.

Therefore:

```text
50 result rows
```

does not necessarily mean:

```text
50 customers
```

If the API promises 50 customers per page, paginate customers rather than the multiplied join result.

Possible approaches include:

- Paginating parent IDs first.
- Aggregating child rows.
- Fetching related records separately.
- Using `DISTINCT` when semantically correct.
- Designing the query around the actual API resource.

## Offset Pagination and Concurrent Changes

Offset pagination is sensitive to changes between requests.

Suppose page 1 is:

```text
A
B
C
D
E
```

The client then requests page 2.

Before that request, a new record `X` is inserted at the beginning:

```text
X
A
B
C
D
E
```

The row positions have shifted.

An offset-based request can therefore produce:

- Duplicate records.
- Missing records.
- Unexpected page boundaries.

Deletes can cause similar shifts.

This is especially noticeable in:

- Activity feeds.
- Notification streams.
- Order histories receiving continuous writes.
- Audit logs.
- Event timelines.

For frequently changing collections, cursor/keyset pagination is often a better fit.

## Offset Pagination and Transaction Isolation

Offset pagination does not inherently provide a consistent snapshot across separate HTTP requests.

A request for page 1 and a later request for page 2 are normally separate database transactions.

Even if each query individually runs under a consistent isolation level, the two requests do not automatically share the same database snapshot.

If the business requirement is:

> Every page must represent exactly the same point-in-time dataset.

then ordinary offset pagination is not sufficient by itself.

Possible designs include:

- Holding a database transaction open, where appropriate.
- Using a snapshot identifier.
- Materializing a result set.
- Querying an immutable dataset.
- Using an application-level export/report job.

Long-lived database transactions should be used carefully because they can create operational problems such as transaction bloat and resource retention.

## Total Count

Offset-based APIs often expose:

```json
{
  "page": 3,
  "page_size": 50,
  "total": 125430,
  "results": []
}
```

The `total` value commonly requires an additional query:

```sql
SELECT COUNT(*)
FROM orders
WHERE customer_id = 42;
```

This can be expensive when:

- The table is large.
- The filter is complex.
- Many users request the endpoint concurrently.
- The query involves joins.
- The count cannot be satisfied cheaply from available metadata or indexes.

Do not add exact counts merely because they are convenient for the frontend.

If the client only needs to know whether another page exists, fetch one additional row:

```sql
SELECT
    id,
    created_at
FROM orders
WHERE customer_id = 42
ORDER BY created_at DESC, id DESC
LIMIT 51
OFFSET 100;
```

Then:

```text
50 rows returned → has_next = true if 51st row exists
51 rows returned → return first 50 + has_next = true
≤50 rows returned → has_next = false
```

This avoids requiring an exact count.

## API Design

A simple page-number API can expose:

```text
GET /orders?page=3&page_size=50
```

The server calculates:

```python
offset = (page - 1) * page_size
```

A production implementation should validate both parameters.

For example:

```python
from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/orders")
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    offset = (page - 1) * page_size

    return {
        "page": page,
        "page_size": page_size,
        "offset": offset,
    }
```

The important production constraint is:

```text
page_size <= server-defined maximum
```

The client should not control an unlimited database result size.

## Django Example

Django QuerySets can express offset pagination through slicing:

```python
page = 3
page_size = 50
offset = (page - 1) * page_size

orders = (
    Order.objects
    .filter(customer_id=customer_id)
    .order_by("-created_at", "-id")
    [offset:offset + page_size]
)
```

Django translates the slice into database-level pagination rather than loading the entire QuerySet into Python.

Avoid:

```python
orders = list(
    Order.objects
    .filter(customer_id=customer_id)
    .order_by("-created_at", "-id")
)

page = orders[offset:offset + page_size]
```

This materializes potentially thousands or millions of records in application memory before slicing them.

The database should perform the filtering, ordering, and pagination.

## API Response Example

A page-number API might return:

```json
{
  "page": 3,
  "page_size": 50,
  "has_next": true,
  "has_previous": true,
  "results": [
    {
      "id": 1042,
      "status": "paid",
      "total_amount": "149.99"
    }
  ]
}
```

If exact totals are required:

```json
{
  "page": 3,
  "page_size": 50,
  "total": 125430,
  "has_next": true,
  "has_previous": true,
  "results": []
}
```

Avoid returning metadata that requires expensive database operations unless the product actually needs it.

## Input Validation

At the API boundary, validate:

```text
page >= 1
1 <= page_size <= maximum
```

For example:

```text
GET /orders?page=0
GET /orders?page=-5
GET /orders?page=1&page_size=1000000
```

should not result in unbounded or invalid database work.

A useful policy is:

| Parameter | Example | Constraint |
|---|---:|---|
| `page` | `3` | `>= 1` |
| `page_size` | `50` | `1–100` |
| `offset` | `100` | Derived server-side |

Prefer calculating `offset` on the server rather than accepting an arbitrary offset from untrusted clients.

## Maximum Page Depth

Even with a page-size limit, clients can request extremely deep pages:

```text
?page=1000000&page_size=100
```

which becomes:

```text
OFFSET 99,999,900
```

For systems where deep pages have no legitimate use, consider enforcing a maximum page number or replacing offset pagination with cursor pagination.

The appropriate policy depends on the product.

For an internal administrative interface, page 100 may be reasonable.

For a high-volume event feed, page 100,000 may indicate that cursor pagination is the correct model.

## Pagination and Sorting Changes

Offset pagination depends on the ordering remaining stable between requests.

Suppose:

```sql
ORDER BY created_at DESC, id DESC
```

is used for page 1.

If the client then changes the sort order:

```sql
ORDER BY total_amount DESC, id DESC
```

page 2 is no longer a continuation of the same logical result set.

Therefore an API should treat:

```text
filters + ordering + page
```

as one query state.

For example:

```text
GET /orders?
    status=paid
    &sort=-created_at
    &page=3
    &page_size=50
```

Changing `status` or `sort` should logically restart pagination from page 1.

## Performance Testing

Do not benchmark only page 1.

Test realistic depths:

```text
page 1
page 10
page 100
page 1,000
```

For PostgreSQL:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    id,
    created_at
FROM orders
ORDER BY created_at DESC, id DESC
LIMIT 50
OFFSET 100000;
```

Compare:

- Execution time.
- Rows examined/processed.
- Index scans.
- Heap fetches.
- Sort operations.
- Buffer reads.
- CPU utilization.

A query that performs well at:

```text
OFFSET 0
```

can behave very differently at:

```text
OFFSET 1,000,000
```

## Monitoring

For production APIs using offset pagination, monitor:

- Query latency by endpoint.
- Database CPU.
- Database I/O.
- Query execution plans for representative depths.
- P95/P99 latency.
- Requested page numbers.
- Requested page sizes.
- Database connection utilization.
- Error rates.
- Slow-query frequency.

A useful application metric is the distribution of requested pages:

```text
page 1     → 85%
page 2     → 9%
page 3–10  → 5%
page >100  → 1%
```

If deep pages are rare, offset pagination may be perfectly reasonable.

If deep pages represent a significant workload, investigate keyset pagination.

## Production Best Practices

### Always Specify an Order

Use:

```sql
ORDER BY created_at DESC, id DESC
```

rather than relying on physical or unspecified row order.

### Cap Page Size

Set a server-side maximum:

```text
page_size <= 100
```

or another value justified by the workload.

### Calculate OFFSET Server-Side

Use:

```text
offset = (page - 1) × page_size
```

rather than trusting arbitrary client-supplied offsets.

### Index the Actual Query

Design indexes around the complete workload:

```text
WHERE + ORDER BY + pagination
```

rather than blindly indexing every column individually.

### Avoid Unnecessary COUNT Queries

If the client only needs:

```text
has_next
```

fetch one additional row rather than calculating an exact total.

### Benchmark Deep Pages

Always test realistic offsets, not just:

```text
OFFSET 0
```

### Monitor Tail Latency

Pagination problems often appear in P95/P99 latency before average latency becomes obviously problematic.

### Set a Reasonable Maximum Page Depth

If users never legitimately need very deep pages, reject or redesign such requests.

### Move to Cursor Pagination When Necessary

If the workload requires:

- Very deep pagination.
- High-volume feeds.
- Large datasets.
- Continuous inserts.
- Stable sequential traversal.

consider cursor/keyset pagination.

## Common Mistakes and Pitfalls

| Mistake | Why it is problematic | Better approach |
|---|---|---|
| `LIMIT` without `ORDER BY` | Page boundaries are undefined | Use deterministic ordering |
| Very large `OFFSET` | Database may process many discarded rows | Use keyset pagination for deep traversal |
| Unlimited `page_size` | Clients can overload the database/API | Enforce a maximum |
| Application-side slicing | Large result sets consume application memory | Slice at the database |
| Assuming indexes make OFFSET constant-time | The database may still traverse skipped rows | Benchmark realistic offsets |
| Exact `COUNT(*)` on every request | Adds database work | Return `has_next` when possible |
| Paginating a multiplied JOIN result | Page size may represent rows, not entities | Paginate the intended resource |
| Ignoring concurrent inserts | Records can shift between pages | Consider cursor pagination |
| Allowing arbitrary page depth | Can create expensive pathological queries | Cap depth or change pagination strategy |
| Using mutable sort criteria carelessly | Page boundaries can become inconsistent | Keep ordering stable across requests |

## When Offset Pagination Is the Right Choice

Offset pagination is a strong choice when the product requires:

```text
Page 1
Page 2
Page 3
...
Page 20
```

and the dataset and access patterns are manageable.

Typical examples:

### Admin Dashboard

```text
GET /admin/users?page=5&page_size=50
```

Administrators may need to jump directly to a page.

### Search Results

```text
GET /products?q=laptop&page=4&page_size=25
```

For moderate result sets, offset pagination provides a simple user experience.

### Internal Reporting

Reports often naturally map to numbered pages and may not require continuous traversal through millions of records.

## When Offset Pagination Becomes a Poor Fit

Consider replacing it with cursor/keyset pagination when:

```text
large dataset
+
deep pages
+
frequent writes
+
sequential traversal
```

are all present.

Typical examples:

- Audit logs.
- Notification feeds.
- Activity streams.
- Large event histories.
- High-volume order histories.
- Time-series-like application records.

The conceptual difference is:

```text
Offset pagination:

"Skip N rows and return the next M."


Keyset pagination:

"Continue after this known ordering boundary."
```

Keyset pagination avoids the need to repeatedly skip an increasingly large number of rows.

## Offset vs Keyset

| Characteristic | Offset | Keyset |
|---|---|---|
| API simplicity | High | Moderate |
| Numbered pages | Excellent | Poor |
| Jump to arbitrary page | Easy | Difficult |
| Deep pages | Can degrade | Generally efficient |
| Large datasets | Can become expensive | Strong fit |
| Frequent inserts | Can shift pages | More stable |
| Implementation complexity | Low | Moderate |
| Exact total pages | Natural fit | Less natural |
| Infinite scrolling | Possible | Strong fit |
| Admin interfaces | Strong fit | Sometimes unnecessary |
| Large feeds | Usually poor fit | Strong fit |

The correct choice is driven by workload and product behavior, not by a blanket rule that one method is always better.

## Interview Traps

### "OFFSET 1,000,000 means the database jumps directly to row 1,000,000."

Not necessarily.

`OFFSET` describes how many rows from the ordered result should be discarded. The database may still need to traverse or process those rows.

### "An index solves deep OFFSET performance."

Not completely.

An appropriate index can make traversal much more efficient, but a large offset can still require substantial index traversal.

### "Pagination means LIMIT."

Not by itself.

A production pagination design includes:

```text
filtering
+ deterministic ordering
+ bounded result size
+ page boundary
+ API contract
+ consistency behavior
```

### "Offset pagination always gives stable pages."

No.

Concurrent inserts, deletes, and updates can shift rows between requests.

### "Cursor pagination is always better."

No.

If users need page numbers and arbitrary page navigation over a manageable dataset, offset pagination can be simpler and more appropriate.

### "LIMIT 50 means only 50 database rows are processed."

Not necessarily.

With:

```sql
LIMIT 50 OFFSET 500000;
```

the database may process a large number of rows before returning the final 50.

## Key Takeaways

- Offset pagination uses `LIMIT` and `OFFSET` to return bounded portions of an ordered result set and is well suited to simple page-number APIs.
- Large offsets can become expensive because the database may need to traverse or process many rows before reaching the requested page.
- Reliable offset pagination requires deterministic `ORDER BY`, bounded page sizes, appropriate indexes, and server-side validation.
- Concurrent inserts, deletes, and updates can shift offset-based page boundaries, making cursor/keyset pagination preferable for large, frequently changing feeds.
- Measure realistic page depths and move to keyset pagination when deep traversal becomes a meaningful performance or consistency problem.