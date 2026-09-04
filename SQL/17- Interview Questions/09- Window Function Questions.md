# 09- Window Function Questions

## Overview

Window functions are one of the most important SQL topics for intermediate and senior backend interviews because they solve problems that are awkward or inefficient with ordinary `GROUP BY` queries.

A window function performs a calculation across a related set of rows while **preserving the individual rows**.

Typical use cases include:

- Ranking rows
- Finding top-N records per group
- Comparing a row with previous or next rows
- Running totals
- Moving averages
- Percentiles
- Deduplication
- Latest-record selection
- Time-series analysis
- Pagination and reporting

The key distinction is:

> `GROUP BY` reduces rows into groups. A window function calculates across rows without collapsing the result set.

---

## Window Function Mental Model

Consider orders:

| id | customer_id | amount |
|---:|---:|---:|
| 101 | 1 | 500 |
| 102 | 1 | 300 |
| 103 | 2 | 700 |
| 104 | 2 | 200 |

A grouped query:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_amount
FROM orders
GROUP BY customer_id;
```

returns:

| customer_id | total_amount |
|---:|---:|
| 1 | 800 |
| 2 | 900 |

The individual orders disappear.

A window function:

```sql
SELECT
    id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

returns:

| id | customer_id | amount | customer_total |
|---:|---:|---:|---:|
| 101 | 1 | 500 | 800 |
| 102 | 1 | 300 | 800 |
| 103 | 2 | 700 | 900 |
| 104 | 2 | 200 | 900 |

The original rows remain available.

---

## Window Function Syntax

General form:

```sql
function_name(...) OVER (
    PARTITION BY ...
    ORDER BY ...
    frame_specification
)
```

Example:

```sql
SELECT
    id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at
    ) AS running_total
FROM orders;
```

The `OVER` clause defines the window over which the function operates.

---

## PARTITION BY

`PARTITION BY` divides rows into independent groups for the window calculation.

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

means:

> Calculate the sum independently for each customer.

It does **not** collapse the rows.

Conceptually:

```text
All orders
    │
    ├── Customer 1 → window calculation
    ├── Customer 2 → window calculation
    └── Customer 3 → window calculation
```

---

## ORDER BY Inside a Window

Window `ORDER BY` determines the logical order in which the function operates.

Example:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

This ranks orders from newest to oldest for each customer.

The `ORDER BY` inside `OVER (...)` is different from the final query's `ORDER BY`.

```sql
SELECT
    id,
    ROW_NUMBER() OVER (
        ORDER BY created_at DESC
    ) AS rn
FROM orders
ORDER BY id;
```

The window ordering determines `rn`.

The final `ORDER BY` determines the presentation order.

---

## Window Functions vs GROUP BY

| Requirement | `GROUP BY` | Window Function |
|---|---|---|
| Collapse rows | Yes | No |
| Calculate per group | Yes | Yes |
| Keep individual rows | No | Yes |
| Ranking | Awkward | Excellent |
| Running total | Awkward | Excellent |
| Compare adjacent rows | Difficult | Excellent |
| Top-N per group | Requires extra query | Excellent |
| Aggregate plus detail | Requires join/subquery | Excellent |

Interview rule:

> If you need both the original row and an aggregate/ranking derived from related rows, think about window functions.

---

## Common Window Functions

### Ranking

- `ROW_NUMBER()`
- `RANK()`
- `DENSE_RANK()`

### Navigation

- `LAG()`
- `LEAD()`
- `FIRST_VALUE()`
- `LAST_VALUE()`
- `NTH_VALUE()`

### Aggregation

- `SUM()`
- `AVG()`
- `COUNT()`
- `MIN()`
- `MAX()`

### Distribution

- `NTILE()`
- `PERCENT_RANK()`
- `CUME_DIST()`

---

## ROW_NUMBER

`ROW_NUMBER()` assigns a unique sequential number to rows in the window.

```sql
SELECT
    id,
    customer_id,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY amount DESC, id DESC
    ) AS rn
FROM orders;
```

Example result:

| id | customer_id | amount | rn |
|---:|---:|---:|---:|
| 101 | 1 | 500 | 1 |
| 102 | 1 | 500 | 2 |
| 103 | 1 | 300 | 3 |

Even when amounts are tied, `ROW_NUMBER()` assigns different numbers.

For deterministic production queries, provide a stable tie-breaker such as `id`.

---

## RANK

`RANK()` assigns the same rank to tied rows and leaves gaps after ties.

Example:

```sql
SELECT
    id,
    amount,
    RANK() OVER (
        ORDER BY amount DESC
    ) AS rank
FROM orders;
```

If amounts are:

```text
1000
1000
800
500
```

the ranks are:

```text
1
1
3
4
```

---

## DENSE_RANK

`DENSE_RANK()` also assigns the same rank to ties but does not leave gaps.

For:

```text
1000
1000
800
500
```

the result is:

```text
1
1
2
3
```

---

## ROW_NUMBER vs RANK vs DENSE_RANK

| Function | Ties share rank? | Gaps after ties? | Unique row number? |
|---|---:|---:|---:|
| `ROW_NUMBER()` | No | No | Yes |
| `RANK()` | Yes | Yes | No |
| `DENSE_RANK()` | Yes | No | No |

Interview question:

> "Which function should I use for top 3 employees?"

The answer depends on the business meaning.

If exactly three rows are required:

```sql
ROW_NUMBER()
```

If all employees tied within the top three ranks should be included:

```sql
RANK()
```

---

## Top-N Per Group

A classic interview problem:

> Find the top three orders for every customer.

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY total_amount DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE rn <= 3;
```

The window function creates the ranking.

The outer query filters the ranking.

---

## Why Can't You Use a Window Function Directly in WHERE?

This is invalid:

```sql
SELECT
    id,
    ROW_NUMBER() OVER (
        ORDER BY created_at DESC
    ) AS rn
FROM orders
WHERE rn <= 10;
```

The reason is that window functions are evaluated after the `WHERE` stage in SQL's logical processing model.

Use a subquery or CTE:

```sql
WITH ranked_orders AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            ORDER BY created_at DESC
        ) AS rn
    FROM orders
)
SELECT *
FROM ranked_orders
WHERE rn <= 10;
```

This is a very common interview question.

---

## Latest Row Per Group

Find the latest order for every customer:

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;
```

The `id DESC` tie-breaker makes the result deterministic when multiple orders have the same timestamp.

---

## PostgreSQL DISTINCT ON Alternative

PostgreSQL provides:

```sql
SELECT DISTINCT ON (customer_id)
    *
FROM orders
ORDER BY
    customer_id,
    created_at DESC,
    id DESC;
```

This can be concise and efficient for PostgreSQL-specific applications.

The window-function version is more portable and often easier to translate to other databases.

---

## Running Total

A running total is a classic window-function problem.

```sql
SELECT
    id,
    customer_id,
    created_at,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders;
```

Conceptually:

```text
Order 1 → amount
Order 2 → order1 + order2
Order 3 → order1 + order2 + order3
```

The explicit `ROWS` frame makes the intended semantics clear.

---

## Window Frames

A window has two related concepts:

```text
partition
    ↓
ordered rows
    ↓
frame used for current row
```

Example:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

The frame means:

> From the first row in the partition through the current row.

---

## ROWS vs RANGE

This is an important senior-level topic.

`ROWS` operates on physical row positions.

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

means:

> Current row plus the two preceding rows.

`RANGE` operates based on the ordering value and can include peer rows with equal ordering values.

Therefore, tied `ORDER BY` values can produce different behavior between `ROWS` and `RANGE`.

When you need row-count-based semantics, `ROWS` is often the safer explicit choice.

---

## Default Window Frames

Window-function defaults can be surprising, especially when `ORDER BY` is present.

For cumulative calculations, explicitly specify the frame when correctness depends on it:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

This avoids ambiguity around peer rows and makes the query intent obvious during code review.

---

## Moving Average

Example:

> Calculate a three-order moving average.

```sql
SELECT
    id,
    customer_id,
    created_at,
    amount,
    AVG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_average
FROM orders;
```

The first rows naturally have smaller frames because fewer preceding rows exist.

---

## LAG

`LAG()` accesses a previous row.

Example:

```sql
SELECT
    id,
    customer_id,
    created_at,
    amount,
    LAG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_amount
FROM orders;
```

This is useful for:

- Change detection
- Time-series comparisons
- Previous status
- Previous price
- Previous event

---

## Calculating Change From Previous Row

```sql
SELECT
    id,
    customer_id,
    amount,
    amount - LAG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS amount_change
FROM orders;
```

The first row in each partition has no previous row, so the result is `NULL`.

---

## LEAD

`LEAD()` accesses a following row.

```sql
SELECT
    id,
    customer_id,
    created_at,
    LEAD(created_at) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS next_order_at
FROM orders;
```

This can be used to calculate:

- Time until next event
- Session gaps
- Next status
- Next transaction
- User journey transitions

---

## FIRST_VALUE

`FIRST_VALUE()` returns the first value within the window frame.

```sql
SELECT
    id,
    customer_id,
    amount,
    FIRST_VALUE(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS first_order_amount
FROM orders;
```

Frame semantics matter.

For advanced queries, explicitly define the frame when using `FIRST_VALUE()` or `LAST_VALUE()`.

---

## LAST_VALUE Trap

A common interview trap:

```sql
LAST_VALUE(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at
)
```

may not return the last row in the entire partition because the default frame ends at the current row under common ordered-window semantics.

If you need the partition's last value, explicitly define the frame:

```sql
LAST_VALUE(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, id
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
```

This is an important distinction between:

```text
last value in current frame
```

and:

```text
last value in entire partition
```

---

## COUNT With Window Functions

You can calculate group counts while retaining individual rows:

```sql
SELECT
    id,
    customer_id,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS customer_order_count
FROM orders;
```

This is useful when an API needs both:

- Individual records
- Group-level metadata

without executing a separate count query.

---

## Aggregate Plus Detail

Example:

```sql
SELECT
    id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average
FROM orders;
```

One result row can contain:

```text
individual order
+
customer aggregate
```

This is one of the strongest use cases for window functions.

---

## Percentage of Group Total

```sql
SELECT
    id,
    customer_id,
    amount,
    amount / NULLIF(
        SUM(amount) OVER (
            PARTITION BY customer_id
        ),
        0
    ) AS percentage_of_customer_total
FROM orders;
```

`NULLIF` prevents division-by-zero errors.

For financial APIs, decide whether the database should return a numeric value, percentage, or rounded presentation value.

---

## Ranking Within a Group

```sql
SELECT
    id,
    customer_id,
    amount,
    RANK() OVER (
        PARTITION BY customer_id
        ORDER BY amount DESC
    ) AS amount_rank
FROM orders;
```

This answers:

> What is this order's rank among this customer's orders?

---

## Global Rank vs Partitioned Rank

Without `PARTITION BY`:

```sql
RANK() OVER (
    ORDER BY amount DESC
)
```

there is one global ranking.

With:

```sql
RANK() OVER (
    PARTITION BY customer_id
    ORDER BY amount DESC
)
```

there is one ranking per customer.

Interviewers frequently test whether you understand this distinction.

---

## NTILE

`NTILE(n)` divides ordered rows into approximately equal buckets.

Example:

```sql
SELECT
    id,
    amount,
    NTILE(4) OVER (
        ORDER BY amount DESC
    ) AS quartile
FROM orders;
```

This can support:

- Customer segmentation
- Percentile-style buckets
- Reporting
- Ranking bands

It does not mean the numeric values themselves are evenly distributed.

It distributes rows as evenly as possible.

---

## PERCENT_RANK

`PERCENT_RANK()` calculates relative rank:

```sql
SELECT
    id,
    amount,
    PERCENT_RANK() OVER (
        ORDER BY amount
    ) AS percentile_rank
FROM orders;
```

The result is normalized between `0` and `1` for a partition.

Be precise in interviews:

> `PERCENT_RANK()` is relative rank, not exactly the same thing as every statistical definition of a percentile.

---

## CUME_DIST

`CUME_DIST()` represents the proportion of rows with values less than or equal to the current row according to the window ordering.

```sql
SELECT
    id,
    amount,
    CUME_DIST() OVER (
        ORDER BY amount
    ) AS cumulative_distribution
FROM orders;
```

It is useful for distribution analysis.

---

## Window Functions and NULL

Ordering with nullable values can affect ranking.

PostgreSQL allows explicit ordering:

```sql
ORDER BY score DESC NULLS LAST
```

Example:

```sql
ROW_NUMBER() OVER (
    ORDER BY score DESC NULLS LAST
)
```

Be explicit when `NULL` placement affects business semantics.

---

## Deterministic Ordering

This is a critical production consideration.

Avoid:

```sql
ROW_NUMBER() OVER (
    ORDER BY created_at DESC
)
```

if multiple rows can share the same timestamp.

Prefer:

```sql
ROW_NUMBER() OVER (
    ORDER BY created_at DESC, id DESC
)
```

A stable unique tie-breaker makes pagination, ranking, deduplication, and tests more predictable.

---

## Deduplication With ROW_NUMBER

Suppose a table contains duplicate records and you need one preferred row.

```sql
WITH ranked AS (
    SELECT
        id,
        customer_id,
        email,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id, email
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM customer_contacts
)
SELECT *
FROM ranked
WHERE rn = 1;
```

This keeps the newest record for each `(customer_id, email)` pair.

For permanent data integrity, however, also consider an appropriate `UNIQUE` constraint.

Query-time deduplication is not a substitute for preventing invalid duplicates.

---

## Deleting Duplicates

A PostgreSQL-specific pattern can use `ROW_NUMBER()` to identify duplicate rows.

```sql
WITH duplicates AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id, email
            ORDER BY id
        ) AS rn
    FROM customer_contacts
)
DELETE FROM customer_contacts AS c
USING duplicates AS d
WHERE c.id = d.id
  AND d.rn > 1;
```

For production cleanup:

- Back up or verify recoverability
- Validate the duplicate definition
- Use transactions where practical
- Consider batching
- Check foreign-key dependencies
- Add the correct uniqueness constraint afterward

---

## Gaps and Islands

Window functions are commonly used for "gaps and islands" problems.

For example, consecutive activity dates can be grouped using row-number-based calculations.

A common conceptual pattern is:

```sql
date_value - row_number_based_offset
```

Rows sharing the same derived grouping key belong to the same island.

These problems are popular in senior SQL interviews because they test whether you can transform ordered data into groups.

---

## Sessionization

Window functions can help identify user sessions.

Example concept:

```sql
LAG(event_time)
```

can compare each event with the previous event.

If the gap exceeds a threshold:

```text
previous event
      ↓
gap > threshold?
      ↓
new session
```

A subsequent cumulative window calculation can assign session IDs.

This pattern is useful for:

- Web analytics
- User activity
- Event streams
- Product analytics

For very high-volume event data, dedicated analytical infrastructure may be more appropriate than repeatedly running sessionization on an OLTP database.

---

## Window Functions and Query Processing Order

A simplified logical order is:

```text
FROM
↓
WHERE
↓
GROUP BY
↓
HAVING
↓
SELECT
↓
WINDOW FUNCTIONS
↓
ORDER BY
↓
LIMIT
```

The exact SQL processing model is more nuanced, but this mental model explains why:

```sql
WHERE row_number <= 3
```

cannot directly reference a window-function result from the same query block.

Use a CTE/subquery or, where supported and appropriate, a later filtering mechanism such as `QUALIFY`.

PostgreSQL does not provide a native `QUALIFY` clause.

---

## Window Functions and GROUP BY

Window functions can operate over grouped results.

Example:

```sql
SELECT
    customer_id,
    SUM(amount) AS revenue,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS revenue_rank
FROM orders
GROUP BY customer_id;
```

Here:

```text
orders
  ↓
GROUP BY customer
  ↓
customer-level rows
  ↓
window ranking
```

This is a powerful combination.

---

## GROUP BY vs Window Function: Interview Example

Question:

> "Find each department's average salary and show every employee's salary alongside it."

Use a window function:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS department_average
FROM employees;
```

Using `GROUP BY` alone would lose the individual employee rows.

---

## Window Function and HAVING

Suppose:

```sql
SELECT
    customer_id,
    SUM(amount) AS revenue,
    RANK() OVER (
        ORDER BY SUM(amount) DESC
    ) AS revenue_rank
FROM orders
GROUP BY customer_id
HAVING SUM(amount) > 1000;
```

`HAVING` filters grouped rows before the window calculation operates on the resulting grouped relation.

This distinction is important when explaining query semantics in interviews.

---

## Multiple Window Functions

A single query can calculate several window metrics:

```sql
SELECT
    id,
    customer_id,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at DESC, id DESC
    ) AS row_number,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_average,
    LAG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_amount
FROM orders;
```

This can be powerful, but the query may become computationally expensive.

---

## Named Windows

SQL allows a window definition to be reused.

Example:

```sql
SELECT
    id,
    customer_id,
    amount,
    ROW_NUMBER() OVER w AS row_number,
    RANK() OVER w AS rank
FROM orders
WINDOW w AS (
    PARTITION BY customer_id
    ORDER BY amount DESC, id DESC
);
```

Named windows reduce repeated window definitions.

They can improve readability when multiple functions use the same partitioning and ordering.

---

## Window Functions and Indexes

Window functions often require ordered processing.

An index can sometimes help provide data in a useful order, but an index does not guarantee that the database will avoid sorting.

For:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at, id
)
```

an index such as:

```sql
CREATE INDEX idx_orders_customer_created_id
ON orders (
    customer_id,
    created_at,
    id
);
```

may support the access pattern.

Validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

---

## WindowAgg in PostgreSQL

PostgreSQL execution plans commonly contain a `WindowAgg` node for window-function evaluation.

Example:

```sql
EXPLAIN
SELECT
    id,
    ROW_NUMBER() OVER (
        ORDER BY created_at
    )
FROM orders;
```

Conceptually:

```text
Scan
  ↓
Sort if required
  ↓
WindowAgg
  ↓
Result
```

The exact plan depends on indexes, ordering, filters, cardinality, and PostgreSQL version.

---

## Sorting Cost

Many window queries require ordering.

Sorting can consume:

- CPU
- Memory
- Temporary disk I/O

For large datasets, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and look for:

- Sort nodes
- Sort method
- Disk-based sorting
- Actual rows
- Execution time

Do not increase `work_mem` globally just because one window query spills.

Understand concurrency and workload first.

---

## Window Functions and work_mem

Operations such as sorts and some window-related processing can consume memory.

A production system with many concurrent expensive queries can experience memory pressure if per-operation memory is configured aggressively.

The effective risk is:

```text
per-operation memory
× concurrent operations
× active connections
```

Therefore, optimize query shape and workload concurrency before blindly increasing memory settings.

---

## Window Functions and Large Tables

A query like:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at
)
```

over hundreds of millions of rows can be expensive.

Potential strategies include:

- Filtering earlier
- Indexing important predicates
- Partition pruning
- Pre-aggregation
- Materialized views
- Read replicas
- OLAP systems
- Precomputed read models

A window function does not eliminate the cost of processing its input relation.

---

## Filter Before the Window When Semantically Correct

Prefer:

```sql
SELECT ...
FROM (
    SELECT ...
    FROM orders
    WHERE status = 'paid'
) AS filtered_orders;
```

over computing the window across irrelevant rows when the business semantics permit filtering first.

For example:

```sql
SELECT
    id,
    customer_id,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY amount DESC, id DESC
    ) AS rn
FROM orders
WHERE status = 'paid';
```

Only paid orders participate in the ranking.

Be careful: moving predicates can change the meaning of the calculation.

---

## Window Functions and Pagination

Window functions can support ranking-based pagination, but they are not automatically the best pagination strategy.

For ordinary API pagination, keyset pagination is often preferable:

```sql
SELECT
    id,
    created_at,
    amount
FROM orders
WHERE (created_at, id) < ($1, $2)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Using:

```sql
ROW_NUMBER()
```

to generate page numbers across millions of rows can require much more work.

---

## Window Functions and APIs

Suppose a REST API returns:

```json
{
  "order_id": 101,
  "amount": 500,
  "customer_total": 2400,
  "customer_rank": 2
}
```

The database can calculate the metadata in one query.

This can reduce:

```text
API
 ├── order query
 ├── total query
 └── rank query
```

to:

```text
API
    ↓
one SQL query
    ↓
window calculations
    ↓
response
```

The trade-off is increased SQL complexity and potentially higher database CPU.

---

## Window Functions and Django

Django supports window expressions through `Window`.

Example:

```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber

queryset = (
    Order.objects
    .annotate(
        row_number=Window(
            expression=RowNumber(),
            partition_by=[F("customer_id")],
            order_by=F("created_at").desc(),
        )
    )
)
```

The generated SQL should still be inspected for:

- Correct partitioning
- Ordering
- Filters
- Query complexity
- Execution plan

ORM syntax does not change database execution behavior.

---

## Window Functions and SQLAlchemy

SQLAlchemy supports window expressions through `.over()`:

```python
from sqlalchemy import func

customer_total = func.sum(Order.amount).over(
    partition_by=Order.customer_id
)
```

For ranking:

```python
rank = func.row_number().over(
    partition_by=Order.customer_id,
    order_by=(Order.created_at.desc(), Order.id.desc()),
)
```

As with Django, inspect generated SQL and execution plans for production queries.

---

## Window Functions in Microservices

Window functions are useful inside a service's database boundary.

They are not a replacement for cross-service aggregation.

If customer data is in:

```text
Customer Service → DB A
Order Service → DB B
```

an order-service SQL window function cannot directly rank against customer-service tables unless an explicit database integration exists.

For cross-service analytics, consider:

- Kafka
- CDC
- Data warehouse
- Materialized read models
- Analytics pipelines

---

## Security Considerations

Window functions do not bypass SQL security controls.

Tenant filtering still matters:

```sql
SELECT
    id,
    tenant_id,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY tenant_id
        ORDER BY created_at DESC, id DESC
    ) AS rn
FROM orders
WHERE tenant_id = $1;
```

The tenant predicate must be applied correctly.

If PostgreSQL Row-Level Security is used, understand how RLS affects the underlying relation before the window calculation.

Never rely on the window's `PARTITION BY` as an authorization mechanism.

---

## Window Functions and RLS

A subtle issue arises when ranking is performed over tenant-scoped data.

The application may intend:

```text
rank within tenant
```

but accidentally calculate:

```text
rank across all visible tenants
```

Use the correct partition and security context.

Database authorization and analytical partitioning are separate concepts.

---

## Window Functions and Transactions

A window query executes against the transaction's database snapshot according to the database's isolation semantics.

For reporting queries, this means the result represents a consistent database view appropriate to the transaction isolation level.

For concurrent business decisions, however, do not assume a window query itself provides locking or prevents concurrent changes.

If the operation modifies shared state, explicit transaction and concurrency design may be required.

---

## Window Functions and Locking

Ordinary window queries are generally read operations and do not lock rows simply because they rank or aggregate them.

If you combine them with data modification or row-locking statements, understand the resulting lock behavior separately.

Do not confuse:

```text
window calculation
```

with:

```text
concurrency control
```

---

## Window Functions and Read Replicas

Analytical window queries can be good candidates for read replicas when stale data is acceptable.

For example:

```text
API
 ↓
read router
 ↓
read replica
 ↓
window query
```

But consider:

- Replica lag
- Query duration
- Replica CPU
- Long-running query impact
- Read-after-write requirements

For heavy analytics, a dedicated OLAP system may be more appropriate.

---

## Window Functions and Materialized Views

If the same expensive window calculation is repeatedly requested, precomputation may be preferable.

Architecture:

```text
Transactional PostgreSQL
        ↓
materialized view / ETL
        ↓
precomputed ranking
        ↓
API
```

This trades freshness for lower request-time computation.

Use it when:

- The calculation is expensive
- Data changes less frequently than it is queried
- Slightly stale results are acceptable

---

## Common Mistakes

### Using GROUP BY When Rows Must Be Preserved

`GROUP BY` collapses rows.

Use a window function when individual rows are required.

### Forgetting PARTITION BY

Without partitioning, ranking is global.

### Using the Wrong Ranking Function

`ROW_NUMBER`, `RANK`, and `DENSE_RANK` have different tie semantics.

### Ignoring Ties

Always consider whether ordering is deterministic.

### Using Window Results in WHERE

Use a CTE or subquery because the window result is not available to the same query block's `WHERE`.

### Ignoring Window Frames

Especially dangerous with:

- `LAST_VALUE`
- Running aggregates
- Duplicate ordering values

### Computing Windows Over Huge Unfiltered Datasets

Filter as early as semantics allow.

### Using Window Functions for Simple Pagination

Keyset pagination is usually more appropriate for large API datasets.

### Treating a Window Function as a Performance Optimization

Window functions solve relational problems; they do not automatically reduce database work.

### Using Query-Time Deduplication Instead of Constraints

If duplicates are invalid, enforce uniqueness in the schema.

---

## Interview Traps

### What Is a Window Function?

A function that performs a calculation across a related set of rows while preserving individual rows.

---

### Window Function vs GROUP BY?

`GROUP BY` collapses rows into groups.

Window functions calculate across rows without collapsing them.

---

### ROW_NUMBER vs RANK?

`ROW_NUMBER()` always assigns unique sequence numbers.

`RANK()` gives tied rows the same rank and leaves gaps.

---

### ROW_NUMBER vs DENSE_RANK?

`ROW_NUMBER()` produces unique row numbers.

`DENSE_RANK()` gives ties the same rank without gaps.

---

### How Do You Find Top 3 Rows Per Group?

Use a window function such as:

```sql
ROW_NUMBER() OVER (
    PARTITION BY group_id
    ORDER BY score DESC
)
```

and filter the generated row number in an outer query.

---

### Why Can't You Use ROW_NUMBER in WHERE?

Because the window calculation occurs later in the logical query-processing sequence than the `WHERE` clause.

Use a CTE or subquery.

---

### What Is PARTITION BY?

It divides rows into independent windows for the calculation.

It does not collapse rows like `GROUP BY`.

---

### What Does ORDER BY Inside OVER Do?

It defines the logical ordering used by the window function.

It is distinct from the final result ordering.

---

### What Is a Window Frame?

It defines the subset of rows within the window partition considered for the current row.

Examples include:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

and:

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

---

### Why Is LAST_VALUE Frequently Confusing?

Because the default frame may end at the current row, so `LAST_VALUE()` may return the current frame's last value rather than the entire partition's final value.

---

### Can Window Functions Be Used With GROUP BY?

Yes.

Grouped results can themselves be processed by window functions.

---

### Are Window Functions Expensive?

They can be.

Large partitions, sorting, high concurrency, and large intermediate results can consume significant CPU, memory, and temporary I/O.

Always validate with an execution plan.

---

### Can an Index Make a Window Function Faster?

Sometimes.

An index that matches filtering and ordering requirements can reduce scanning or sorting work, but the planner may still choose another strategy.

Validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

---

## Practical Interview Problems

### Find Top Three Products by Revenue

```sql
WITH product_revenue AS (
    SELECT
        product_id,
        SUM(amount) AS revenue
    FROM order_items
    GROUP BY product_id
),
ranked AS (
    SELECT
        product_id,
        revenue,
        DENSE_RANK() OVER (
            ORDER BY revenue DESC
        ) AS revenue_rank
    FROM product_revenue
)
SELECT
    product_id,
    revenue
FROM ranked
WHERE revenue_rank <= 3;
```

Use `ROW_NUMBER()` instead if the requirement is exactly three rows rather than all tied products.

---

### Find the Second Highest Salary Per Department

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        DENSE_RANK() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
        ) AS salary_rank
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary
FROM ranked_employees
WHERE salary_rank = 2;
```

---

### Calculate Running Revenue

```sql
SELECT
    created_at,
    amount,
    SUM(amount) OVER (
        ORDER BY created_at, id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_revenue
FROM orders
ORDER BY created_at, id;
```

---

### Compare Each Order With the Previous Order

```sql
SELECT
    id,
    customer_id,
    amount,
    amount - LAG(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS change_from_previous
FROM orders;
```

---

### Calculate Department Average Alongside Each Employee

```sql
SELECT
    employee_id,
    department_id,
    salary,
    AVG(salary) OVER (
        PARTITION BY department_id
    ) AS department_average
FROM employees;
```

---

### Find the Latest Record Per Customer

```sql
WITH ranked_orders AS (
    SELECT
        o.*,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, id DESC
        ) AS rn
    FROM orders AS o
)
SELECT *
FROM ranked_orders
WHERE rn = 1;
```

---

### Divide Customers Into Four Revenue Buckets

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    NTILE(4) OVER (
        ORDER BY revenue DESC
    ) AS revenue_bucket
FROM customer_revenue;
```

---

## Senior-Level Performance Reasoning

When reviewing a window-function query, ask:

### What Is the Input Cardinality?

How many rows enter the window operation?

Reducing unnecessary input can be more valuable than tuning the window expression itself.

### How Large Are the Partitions?

One enormous partition may behave very differently from millions of small partitions.

### Does the Query Require Sorting?

Check the execution plan.

### Can Filtering Happen Earlier?

Push filters toward the base relation when semantics allow.

### Is the Query Executed Frequently?

A 500 ms query executed once per hour may be harmless.

A 100 ms query executed thousands of times per second may be a major bottleneck.

### Is This the Correct Architecture?

If the query repeatedly performs expensive analytics over billions of rows, moving the workload to:

- Read replicas
- Materialized views
- Precomputed read models
- OLAP
- Data warehouse infrastructure

may be more appropriate than further SQL tuning.

---

## Production Troubleshooting Workflow

When a window query becomes slow:

1. Capture the exact SQL and parameters.
2. Check query frequency and concurrency.
3. Run `EXPLAIN (ANALYZE, BUFFERS)` in a representative environment.
4. Inspect input cardinality.
5. Identify sorting and temporary I/O.
6. Check filtering and partition pruning.
7. Review indexes.
8. Check memory pressure.
9. Check lock and connection-pool behavior.
10. Determine whether the workload belongs on OLTP PostgreSQL at all.

Useful PostgreSQL tools include:

```sql
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

and:

```sql
SELECT
    pid,
    state,
    wait_event_type,
    wait_event,
    query
FROM pg_stat_activity
WHERE state <> 'idle';
```

---

## Production Checklist

- [ ] Define the business meaning of the window clearly.
- [ ] Confirm the intended partition.
- [ ] Confirm the intended ordering.
- [ ] Use deterministic tie-breakers where required.
- [ ] Choose `ROW_NUMBER`, `RANK`, or `DENSE_RANK` based on tie semantics.
- [ ] Understand the window frame.
- [ ] Explicitly specify `ROWS` when row-based frame semantics matter.
- [ ] Validate `NULL` ordering.
- [ ] Filter unnecessary rows before the window when semantically correct.
- [ ] Inspect execution plans for large queries.
- [ ] Check sorting and temporary I/O.
- [ ] Evaluate index support.
- [ ] Consider partitioning for very large datasets.
- [ ] Avoid using window functions as a substitute for keyset pagination.
- [ ] Prevent invalid duplicates with database constraints.
- [ ] Validate ORM-generated SQL in Django or SQLAlchemy.
- [ ] Consider replicas, materialized views, or OLAP for expensive analytics.
- [ ] Protect tenant boundaries independently of `PARTITION BY`.
- [ ] Monitor query frequency, latency, CPU, memory, and connection usage.

---

## Key Takeaways

- **Window functions calculate across related rows without collapsing them:** they are ideal for ranking, running totals, comparisons, and group-level metrics alongside individual records.
- **`ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()` have different tie semantics:** choose based on whether ties should share ranks and whether gaps are meaningful.
- **Window correctness depends on partitioning, ordering, and frames:** deterministic ordering and explicit `ROWS` frames prevent many subtle production and interview bugs.
- **Window functions can be expensive at scale:** sorting, large partitions, memory usage, temporary I/O, and concurrency must be validated with execution plans and workload metrics.
- **Senior SQL design considers architecture, not just syntax:** expensive window workloads may belong on replicas, materialized views, precomputed read models, or OLAP systems rather than the transactional request path.