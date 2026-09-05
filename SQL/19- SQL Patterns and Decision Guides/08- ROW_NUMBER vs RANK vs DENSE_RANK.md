# 08- ROW_NUMBER vs RANK vs DENSE_RANK

## Overview

`ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()` are SQL window functions used to assign positional values to rows within an ordered result set.

They look similar but have different behavior when multiple rows have the same ordering value:

- `ROW_NUMBER()` assigns a unique sequential number to every row.
- `RANK()` gives tied rows the same rank and leaves gaps after ties.
- `DENSE_RANK()` gives tied rows the same rank but does not leave gaps.

The distinction matters in common backend and data-engineering problems such as:

- Selecting the latest record per customer.
- Finding the top N records per group.
- Building leaderboards.
- Ranking products or sellers.
- Detecting duplicates.
- Implementing deterministic pagination or deduplication.
- Selecting the first, second, or third event within each entity.

These functions are often preferable to procedural application-side loops because PostgreSQL can perform the ordering and partitioning close to the data.

---

## Window Function Context

A window function calculates a value across related rows without collapsing those rows into a single result.

For example:

```sql
SELECT
    customer_id,
    id AS order_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC
    ) AS order_number
FROM orders;
```

Unlike:

```sql
GROUP BY customer_id
```

the window function preserves the individual order rows.

Conceptually:

```text
GROUP BY
multiple rows
     ↓
one row per group

Window function
multiple rows
     ↓
same rows + calculated window value
```

This distinction is fundamental when deciding between aggregation and ranking.

---

## Representative Dataset

Consider:

```text
customer_id | order_id | total_amount
-------------+----------+-------------
1            | 101      | 500
1            | 102      | 500
1            | 103      | 300
1            | 104      | 100
```

If ranking is based on:

```sql
ORDER BY total_amount DESC
```

the three ranking functions produce different results.

| order_id | total_amount | ROW_NUMBER | RANK | DENSE_RANK |
|---:|---:|---:|---:|---:|
| 101 | 500 | 1 | 1 | 1 |
| 102 | 500 | 2 | 1 | 1 |
| 103 | 300 | 3 | 3 | 2 |
| 104 | 100 | 4 | 4 | 3 |

The two orders with `500` are tied.

That tie is where the behavior differs.

---

## ROW_NUMBER

`ROW_NUMBER()` assigns a unique sequential integer to each row within its window.

```sql
SELECT
    order_id,
    total_amount,
    ROW_NUMBER() OVER (
        ORDER BY total_amount DESC
    ) AS row_number
FROM orders;
```

Possible result:

```text
order_id | total_amount | row_number
---------+--------------+-----------
101      | 500          | 1
102      | 500          | 2
103      | 300          | 3
104      | 100          | 4
```

Even tied rows receive different numbers.

---

## Why ROW_NUMBER Exists

Use `ROW_NUMBER()` when each row needs a unique position.

Typical production use cases:

- Latest record per entity.
- Deduplicating records.
- Top one row per group.
- Selecting the first N rows per group.
- Deterministic record selection.
- Identifying a specific occurrence.
- Batch processing ordered records.

The important property is:

> Every row gets exactly one row number.

---

## Determinism With ROW_NUMBER

Consider:

```sql
ROW_NUMBER() OVER (
    ORDER BY total_amount DESC
)
```

If two rows have the same `total_amount`, their relative ordering may not be deterministic.

If the application requires stable results, provide a tie-breaker:

```sql
ROW_NUMBER() OVER (
    ORDER BY total_amount DESC, id DESC
)
```

Now the database has a complete ordering.

This is particularly important for:

- Pagination.
- Deduplication.
- Selecting "latest" records.
- Data exports.
- Reproducible batch processing.

A senior engineer should ask:

> Is the ordering total and deterministic?

---

## RANK

`RANK()` assigns the same rank to tied rows and leaves gaps after ties.

```sql
SELECT
    order_id,
    total_amount,
    RANK() OVER (
        ORDER BY total_amount DESC
    ) AS rank
FROM orders;
```

Result:

```text
order_id | total_amount | rank
---------+--------------+-----
101      | 500          | 1
102      | 500          | 1
103      | 300          | 3
104      | 100          | 4
```

There are two rows ranked `1`, so the next rank is `3`.

---

## Why RANK Exists

`RANK()` models competition-style ranking.

For example:

```text
Player A → 100 points → Rank 1
Player B → 100 points → Rank 1
Player C → 90 points  → Rank 3
```

There is no rank `2`.

This is appropriate when tied positions consume multiple ranking positions.

Common uses include:

- Leaderboards.
- Competition rankings.
- Performance reports.
- Sales rankings.
- Exam results.
- Revenue rankings.

---

## DENSE_RANK

`DENSE_RANK()` also gives tied rows the same rank, but does not leave gaps.

```sql
SELECT
    order_id,
    total_amount,
    DENSE_RANK() OVER (
        ORDER BY total_amount DESC
    ) AS dense_rank
FROM orders;
```

Result:

```text
order_id | total_amount | dense_rank
---------+--------------+-----------
101      | 500          | 1
102      | 500          | 1
103      | 300          | 2
104      | 100          | 3
```

The next distinct value receives rank `2`.

---

## Why DENSE_RANK Exists

`DENSE_RANK()` is useful when ranking distinct value groups rather than physical positions.

For example:

```text
Revenue
10000 → rank 1
10000 → rank 1
8000  → rank 2
5000  → rank 3
```

There are three distinct revenue levels, so the ranks are `1`, `2`, and `3`.

Common uses include:

- Distinct price tiers.
- Salary bands.
- Product score levels.
- Grouped performance rankings.
- Finding the Nth distinct value.

---

## Direct Comparison

| Function | Ties share rank? | Gaps after ties? | Unique number per row? | Typical use |
|---|---:|---:|---:|---|
| `ROW_NUMBER()` | No | No | Yes | Select one row / deduplication |
| `RANK()` | Yes | Yes | No | Competition leaderboard |
| `DENSE_RANK()` | Yes | No | No | Distinct value ranking |

The simplest mental model is:

```text
ROW_NUMBER
1, 2, 3, 4

RANK
1, 1, 3, 4

DENSE_RANK
1, 1, 2, 3
```

---

## PARTITION BY

The `PARTITION BY` clause creates independent ranking groups.

Example:

```sql
SELECT
    customer_id,
    id AS order_id,
    created_at,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS row_number
FROM orders;
```

Each customer starts again at `1`.

Example:

```text
customer 1:
order 104 → 1
order 103 → 2
order 102 → 3

customer 2:
order 205 → 1
order 204 → 2
order 203 → 3
```

This pattern is extremely common in backend systems.

---

## Top One Row Per Group

One of the most important `ROW_NUMBER()` patterns is selecting the latest record per entity.

```sql
SELECT
    customer_id,
    order_id,
    created_at
FROM (
    SELECT
        customer_id,
        id AS order_id,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
) AS ranked
WHERE rn = 1;
```

The window function creates:

```text
customer_id | order_id | rn
------------+----------+---
1           | 104      | 1
1           | 103      | 2
1           | 102      | 3
2           | 205      | 1
2           | 204      | 2
```

The outer query keeps only:

```text
rn = 1
```

This produces one deterministic row per customer.

---

## Top N Per Group

The same pattern works for top N:

```sql
SELECT
    customer_id,
    order_id,
    total_amount
FROM (
    SELECT
        customer_id,
        id AS order_id,
        total_amount,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS rn
    FROM orders
) AS ranked
WHERE rn <= 3;
```

This returns at most three rows per customer.

The `id` tie-breaker makes the selection deterministic.

---

## Top N With Ties

If the requirement is:

> Return everyone whose score is within the top three distinct scores.

`DENSE_RANK()` is usually appropriate:

```sql
SELECT
    customer_id,
    order_id,
    total_amount
FROM (
    SELECT
        customer_id,
        id AS order_id,
        total_amount,
        DENSE_RANK() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC
        ) AS ranking
    FROM orders
) AS ranked
WHERE ranking <= 3;
```

This may return more than three rows per customer because multiple rows can share a rank.

---

## ROW_NUMBER vs RANK for Top N

Suppose scores are:

```text
100
100
90
80
80
70
```

### ROW_NUMBER

```text
1
2
3
4
5
6
```

`WHERE row_number <= 3` returns:

```text
100
100
90
```

Exactly three rows.

### RANK

```text
1
1
3
4
4
6
```

`WHERE rank <= 3` returns:

```text
100
100
90
```

### DENSE_RANK

```text
1
1
2
3
3
4
```

`WHERE dense_rank <= 3` returns:

```text
100
100
90
80
80
```

The correct function depends on whether "top N" means:

- N physical rows.
- N competition positions.
- N distinct ranking values.

---

## Latest Record Per Entity

For event or state tables, `ROW_NUMBER()` is often the safest generic pattern.

```sql
SELECT
    customer_id,
    status,
    changed_at
FROM (
    SELECT
        customer_id,
        status,
        changed_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY changed_at DESC, id DESC
        ) AS rn
    FROM customer_status_history
) AS ranked
WHERE rn = 1;
```

The `id` tie-breaker is important if two status events have the same timestamp.

Without it, "latest" may not be deterministic.

---

## Deduplication

Suppose an import process accidentally created duplicate records.

You can identify duplicates with:

```sql
SELECT
    id,
    email,
    created_at,
    ROW_NUMBER() OVER (
        PARTITION BY email
        ORDER BY created_at ASC, id ASC
    ) AS occurrence
FROM customers;
```

Then:

```text
occurrence = 1
```

can represent the record to retain.

A production cleanup should be carefully validated before deleting data.

For example:

```sql
SELECT
    id
FROM (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY email
            ORDER BY created_at ASC, id ASC
        ) AS occurrence
    FROM customers
) AS ranked
WHERE occurrence > 1;
```

Do not immediately convert this into a destructive `DELETE` without verifying the grouping key, retention policy, foreign keys, and business meaning.

---

## Ranking Within a Department

A typical reporting query:

```sql
SELECT
    department_id,
    employee_id,
    salary,
    RANK() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees;
```

Example:

```text
department 1:
salary 100000 → rank 1
salary 100000 → rank 1
salary 90000  → rank 3

department 2:
salary 120000 → rank 1
salary 110000 → rank 2
```

Each partition is ranked independently.

---

## Multiple Window Functions

You can calculate multiple rankings in one query:

```sql
SELECT
    id,
    customer_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY total_amount DESC, id DESC
    ) AS row_number,
    RANK() OVER (
        PARTITION BY customer_id
        ORDER BY total_amount DESC
    ) AS rank,
    DENSE_RANK() OVER (
        PARTITION BY customer_id
        ORDER BY total_amount DESC
    ) AS dense_rank
FROM orders;
```

This is useful for analysis and debugging because the different semantics become directly visible.

However, multiple different window orderings can increase sorting work.

---

## Window Functions Do Not Filter Rows

This is invalid:

```sql
SELECT
    customer_id,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC
    ) AS rn
FROM orders
WHERE rn = 1;
```

A window-function alias cannot generally be referenced in the same query block's `WHERE` clause because the window result is computed after the filtering phase.

Use a subquery:

```sql
SELECT *
FROM (
    SELECT
        customer_id,
        id,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
) AS ranked
WHERE rn = 1;
```

In PostgreSQL, `QUALIFY` is not available as a general replacement for this pattern, so subqueries or CTEs are commonly used.

---

## Logical Query Processing

A simplified conceptual order is:

```text
FROM
  ↓
WHERE
  ↓
GROUP BY
  ↓
HAVING
  ↓
SELECT expressions
  ↓
Window functions
  ↓
ORDER BY
  ↓
LIMIT
```

This is a conceptual model rather than a guarantee of the physical execution sequence.

The important point is that window functions operate on the rows remaining after earlier relational operations such as `FROM`, `WHERE`, and grouping.

---

## Window ORDER BY vs Final ORDER BY

These are different.

```sql
SELECT
    id,
    total_amount,
    ROW_NUMBER() OVER (
        ORDER BY total_amount DESC
    ) AS rn
FROM orders
ORDER BY created_at DESC;
```

The window's:

```sql
ORDER BY total_amount DESC
```

determines the row-number assignment.

The final:

```sql
ORDER BY created_at DESC
```

determines the presentation order.

Do not assume the result will be displayed in the same order used for ranking.

---

## NULL Ordering

Ranking depends on the window's `ORDER BY`.

PostgreSQL's NULL ordering should be considered explicitly when NULL values are possible.

For example:

```sql
ROW_NUMBER() OVER (
    ORDER BY score DESC NULLS LAST
)
```

makes the intended behavior clear.

For ascending order:

```sql
ROW_NUMBER() OVER (
    ORDER BY score ASC NULLS LAST
)
```

Explicit NULL ordering is useful when ranking semantics are part of a business rule.

---

## Deterministic Ordering

For production ranking, define tie-breakers when the exact selected rows matter.

Prefer:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, id DESC
)
```

over:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

when two records can share `created_at`.

A common mistake is assuming timestamps are unique.

They often are not.

Database-generated IDs or another immutable unique key can provide the final tie-breaker.

---

## Performance

Window functions can require significant sorting or other ordering work.

A query such as:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, id DESC
)
```

requires the database to establish the required ordering for the relevant rows.

For large tables, performance depends on:

- Number of rows processed.
- Number of partitions.
- Cardinality of partitions.
- Ordering columns.
- Selectivity of `WHERE`.
- Available indexes.
- Memory available for sorting.
- PostgreSQL execution strategy.
- Whether the query can reduce rows before the window operation.

A useful optimization is to filter early when the filter is semantically valid:

```sql
SELECT *
FROM (
    SELECT
        customer_id,
        id,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
    WHERE created_at >= $1
) AS ranked
WHERE rn = 1;
```

This can reduce the number of rows entering the window operation.

---

## Indexing Considerations

For a common latest-per-customer query:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, id DESC
)
```

an index such as:

```sql
CREATE INDEX idx_orders_customer_created_id
    ON orders (customer_id, created_at DESC, id DESC);
```

may support efficient access patterns.

However, an index does not guarantee that PostgreSQL will avoid sorting or use that index.

The optimizer considers:

- Table size.
- Selectivity.
- Cost estimates.
- Visibility.
- Query shape.
- Available indexes.

Always validate critical queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

---

## Avoid Ranking More Data Than Necessary

Suppose an API only needs orders from the last 30 days.

Do not rank the entire historical table if the business requirement permits filtering first.

Prefer:

```sql
FROM orders
WHERE created_at >= now() - interval '30 days'
```

before applying the window function.

This reduces:

- Rows processed.
- Sorting work.
- Memory consumption.
- I/O.
- Query latency.

The optimization is valid only if older rows cannot affect the required ranking semantics.

---

## Ranking and Pagination

`ROW_NUMBER()` can be used to number rows, but it is not automatically the best pagination mechanism.

For example:

```sql
SELECT *
FROM (
    SELECT
        id,
        created_at,
        ROW_NUMBER() OVER (
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
) AS ranked
WHERE rn BETWEEN 10001 AND 10020;
```

This can require processing and numbering a large prefix of the result set.

For large APIs, keyset pagination is often preferable:

```sql
SELECT
    id,
    created_at,
    total_amount
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

Use `ROW_NUMBER()` when the row position itself is required, not merely because an API needs pagination.

---

## Backend API Example

A FastAPI service might expose the latest order for each customer:

```text
GET /customers/latest-orders
```

The database can perform the grouping and ranking:

```sql
SELECT
    customer_id,
    order_id,
    status,
    created_at
FROM (
    SELECT
        customer_id,
        id AS order_id,
        status,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders
) AS ranked
WHERE rn = 1;
```

The API receives one row per customer rather than loading all orders and performing ranking in Python.

This reduces application-side work and keeps data-intensive operations close to the database.

---

## Django ORM

Django supports window expressions through `Window`.

Example:

```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber

queryset = Order.objects.annotate(
    row_number=Window(
        expression=RowNumber(),
        partition_by=[F("customer_id")],
        order_by=[F("created_at").desc(), F("id").desc()],
    )
)
```

The ORM should still be treated as a SQL-generation layer.

For performance-sensitive queries:

1. Inspect generated SQL.
2. Run `EXPLAIN`.
3. Validate index usage.
4. Test realistic data volumes.

Do not assume that an elegant ORM expression automatically produces the optimal execution plan.

---

## Data Processing and Celery

Window functions are useful for backend jobs such as:

- Generating daily leaderboards.
- Selecting latest customer state.
- Deduplicating imports.
- Ranking sellers.
- Producing reporting snapshots.

A Celery worker can execute the SQL and write the resulting dataset to a reporting table or object storage.

For very large analytical datasets, however, consider whether PostgreSQL is still the appropriate processing engine.

Potential alternatives include:

- Dedicated OLAP databases.
- AWS analytics services.
- Batch processing frameworks.
- Data warehouses.

The choice depends on workload size and architecture.

---

## Security Considerations

Window functions themselves are not an authorization mechanism.

For multi-tenant data:

```sql
SELECT
    customer_id,
    order_id,
    total_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY total_amount DESC, id DESC
    ) AS rn
FROM orders
WHERE tenant_id = $1;
```

The tenant filter must be applied before ranking if rankings must be tenant-specific.

A dangerous pattern is ranking global data and then attempting to filter tenants afterward.

The ranking scope must match the authorization scope.

Where appropriate, enforce tenant isolation with:

- Application-level authorization.
- Database roles.
- PostgreSQL Row Level Security.
- Correct tenant predicates.
- Appropriate indexes.

---

## Reliability Considerations

Ranking queries should be deterministic when their results drive downstream actions.

For example, if a Celery job selects:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, id DESC
)
```

then retries can reproduce the same selection.

Without a stable tie-breaker, two executions can potentially choose different rows when ordering values are tied.

This matters for:

- Data exports.
- Billing.
- Notifications.
- Deduplication.
- State reconstruction.
- ETL jobs.

Deterministic ordering is therefore a reliability concern, not merely a presentation concern.

---

## Common Mistakes

### Using RANK When Exactly N Rows Are Required

`RANK()` can produce fewer or more rows than expected when used with ranking filters.

Use `ROW_NUMBER()` when the requirement is exactly N rows per partition.

### Using ROW_NUMBER When Ties Must Be Preserved

`ROW_NUMBER()` arbitrarily distinguishes tied rows unless a deterministic tie-breaker is supplied.

Use `RANK()` or `DENSE_RANK()` when ties have business meaning.

### Confusing RANK and DENSE_RANK

Remember:

```text
RANK:
1, 1, 3

DENSE_RANK:
1, 1, 2
```

### Omitting Tie-Breakers

This is especially dangerous for:

```sql
ROW_NUMBER()
```

used to select a single row.

### Using Window Functions for Pagination by Default

For large datasets, keyset pagination is often more efficient than numbering every preceding row.

### Ranking Before Filtering

If the business rule is tenant-specific or time-window-specific, make sure filtering occurs at the correct stage.

### Ranking Massive Tables Without Measuring

Window operations can require substantial sorting and memory.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and test realistic volumes.

### Assuming an Index Guarantees No Sort

An index may help, but PostgreSQL still chooses the cheapest execution strategy.

### Performing Ranking in Python

Do not pull millions of rows into Django, FastAPI, or a Celery worker just to calculate rankings that PostgreSQL can perform efficiently.

---

## Production Decision Matrix

| Requirement | Recommended function |
|---|---|
| Unique sequential position for every row | `ROW_NUMBER()` |
| Exactly one latest row per entity | `ROW_NUMBER()` |
| Exactly N rows per group | `ROW_NUMBER()` |
| Competition-style leaderboard | `RANK()` |
| Tied rows share position and gaps matter | `RANK()` |
| Rank distinct values without gaps | `DENSE_RANK()` |
| N distinct score levels | `DENSE_RANK()` |
| Preserve ties in top-N results | `RANK()` or `DENSE_RANK()` |
| Deduplication | `ROW_NUMBER()` |
| Latest event per entity | `ROW_NUMBER()` |
| Large API pagination | Usually keyset pagination instead |

---

## Senior-Level Decision Framework

Ask what the ranking number means.

```text
Do every rows need a unique position?
        |
        +── Yes → ROW_NUMBER()
        |
        No
        |
        +── Should tied rows share a position?
                  |
                  +── Yes
                  |    |
                  |    +── Gaps after ties matter
                  |    |       ↓
                  |    |     RANK()
                  |    |
                  |    +── Gaps do not matter
                  |            ↓
                  |        DENSE_RANK()
```

Then ask:

```text
Is the result per entity/group?
        ↓
Use PARTITION BY

Can ordering values tie?
        ↓
Define explicit tie-breaking when deterministic selection matters

Is the dataset large?
        ↓
Filter early and inspect EXPLAIN

Is this pagination?
        ↓
Consider keyset pagination instead
```

The key engineering question is not:

> Which window function is fastest?

It is:

> What does the position actually mean to the business?

---

## Interview Traps

### "ROW_NUMBER, RANK, and DENSE_RANK are basically the same."

They differ specifically in how ties are handled.

### "RANK always produces consecutive numbers."

False.

With ties:

```text
1, 1, 3
```

### "DENSE_RANK gives every row a unique rank."

False.

Tied rows share the same rank.

### "ROW_NUMBER preserves ties."

False.

It assigns distinct row numbers.

### "ROW_NUMBER() OVER (ORDER BY id) and ORDER BY id are equivalent."

No.

The window `ORDER BY` controls the calculation; the final query `ORDER BY` controls output order.

### "Window functions collapse rows like GROUP BY."

False.

Window functions preserve the input rows and add calculated values.

### "ROW_NUMBER is always deterministic."

Only if the window ordering fully determines row order.

### "RANK <= 10 always returns ten rows."

False.

Ties can cause more or fewer rows than ten.

### "Window functions are always better than GROUP BY."

They solve different problems.

Use `GROUP BY` when rows need to be collapsed into groups; use window functions when row-level detail must be preserved while calculating across a group.

---

## Key Takeaways

- **`ROW_NUMBER()` gives every row a unique position, `RANK()` preserves ties with gaps, and `DENSE_RANK()` preserves ties without gaps:** choose based on the business meaning of the ranking.
- **`ROW_NUMBER()` is the standard pattern for latest-per-group, deduplication, and exactly-N-per-group queries:** use a deterministic tie-breaker when selecting specific rows.
- **`PARTITION BY` creates independent ranking scopes:** ensure the partition and filtering logic match tenant, customer, department, or other business boundaries.
- **Window functions can require significant sorting and memory:** reduce the input set when valid, use appropriate indexes, and validate critical queries with `EXPLAIN (ANALYZE, BUFFERS)`.
- **Do not use `ROW_NUMBER()` as a default pagination mechanism for large APIs:** keyset pagination is often more scalable when the requirement is simply navigating through ordered records.