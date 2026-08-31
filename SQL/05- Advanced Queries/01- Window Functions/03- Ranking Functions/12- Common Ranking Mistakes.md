# 12- Common Ranking Mistakes

## Overview

SQL ranking functions are powerful because they combine ordering, grouping, and row-level analysis without collapsing the result set. The same flexibility also creates subtle correctness bugs.

Most ranking mistakes are not syntax errors. They come from misunderstanding:

- Which rows participate in the ranking.
- How ties should behave.
- Whether ranking is global or partitioned.
- When filtering occurs relative to the window function.
- Whether ordering is deterministic.
- Whether `N` means rows, ranks, or distinct values.
- Whether ranking should happen before or after aggregation.

The safest approach is to define the business rule first and then select the ranking function and query shape that implements it.

## Ranking Function Selection Mistakes

The three common ranking functions have materially different semantics.

| Function | Ties | Rank gaps | Unique row position |
|---|---|---|---|
| `ROW_NUMBER()` | Broken | No | Yes |
| `RANK()` | Preserved | Yes | No |
| `DENSE_RANK()` | Preserved | No | No |

Given:

| value | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---:|---:|---:|---:|
| 100 | 1 | 1 | 1 |
| 90 | 2 | 2 | 2 |
| 90 | 3 | 2 | 2 |
| 80 | 4 | 4 | 3 |

Choosing the wrong function changes the result, even though the query may look completely valid.

### Mistake: Using `ROW_NUMBER()` for Tied Winners

Incorrect when all highest-scoring rows must be returned:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
        ) AS position
    FROM employees
)
SELECT *
FROM ranked
WHERE position = 1;
```

If two employees have the same highest salary, only one receives `position = 1`.

If both are valid winners, use `RANK()`:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        department_id,
        salary,
        RANK() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
        ) AS position
    FROM employees
)
SELECT *
FROM ranked
WHERE position = 1;
```

### Mistake: Using `RANK()` When Exactly N Rows Are Required

`RANK()` preserves ties, so:

```sql
RANK() OVER (
    PARTITION BY department_id
    ORDER BY salary DESC
)
```

can produce more than N rows when filtering with:

```sql
WHERE position <= 3
```

If the contract explicitly requires **at most three rows per department**, use `ROW_NUMBER()` with a deterministic tie-breaker.

### Mistake: Confusing `RANK()` and `DENSE_RANK()`

If values are:

```text
100
90
90
80
```

then:

```text
RANK()       → 1, 2, 2, 4
DENSE_RANK() → 1, 2, 2, 3
```

Use `RANK()` when skipped positions represent the intended competition ranking.

Use `DENSE_RANK()` when the requirement is based on the first N distinct metric values.

## Missing `PARTITION BY`

Without `PARTITION BY`, the ranking is global.

```sql
ROW_NUMBER() OVER (
    ORDER BY revenue DESC
)
```

produces one ranking across the entire dataset.

If the requirement is:

> Top five products within each category.

the ranking population must be separated:

```sql
ROW_NUMBER() OVER (
    PARTITION BY category_id
    ORDER BY revenue DESC, product_id
)
```

### Incorrect

```sql
WITH ranked AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS position
    FROM product_sales
)
SELECT *
FROM ranked
WHERE position <= 5;
```

This returns only five rows globally.

### Correct

```sql
WITH ranked AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS position
    FROM product_sales
)
SELECT *
FROM ranked
WHERE position <= 5;
```

Now every category gets its own ranking.

## Incorrect Partition Scope

A more subtle error occurs when `PARTITION BY` contains too many or too few columns.

Suppose ranking should be per:

```text
tenant → category
```

but the query uses only:

```sql
PARTITION BY category_id
```

then two tenants with the same category can compete against each other.

For a multi-tenant system:

```sql
ROW_NUMBER() OVER (
    PARTITION BY tenant_id, category_id
    ORDER BY revenue DESC, product_id
)
```

The partition definition should match the business ownership boundary.

The partition is not an authorization mechanism. Tenant access must still be enforced independently.

## Non-Deterministic `ROW_NUMBER()`

Consider:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

If two rows have exactly the same `created_at`, SQL has no required ordering between those tied rows unless additional ordering columns resolve the tie.

The query may return different rows as `position = 1` across executions or execution plans.

For deterministic selection:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC, id DESC
)
```

A stable unique column such as `id` should be used as the final tie-breaker when exactly one row must win.

### Important Distinction

Do not blindly add a unique column to every ranking.

For `RANK()`:

```sql
RANK() OVER (
    ORDER BY score DESC, player_id
)
```

the `player_id` breaks ties, meaning equal scores no longer receive the same rank.

If preserving ties is the requirement, rank only by the columns that define equality.

## Filtering at the Wrong Stage

Window functions operate over the rows visible to their query block.

This is one of the most important ranking concepts.

### Incorrect Population

Suppose the requirement is:

> Find the top three employees earning more than 50,000 in each department.

This query ranks everyone first:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC, employee_id
        ) AS position
    FROM employees
)
SELECT *
FROM ranked
WHERE salary > 50000
  AND position <= 3;
```

Employees earning 50,000 or less still participated in the ranking.

### Correct Population

Filter eligible rows before ranking:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC, employee_id
        ) AS position
    FROM employees
    WHERE salary > 50000
)
SELECT *
FROM ranked
WHERE position <= 3;
```

The distinction is:

```text
Input rows
    ↓
Eligibility filter
    ↓
Ranking
    ↓
Rank filter
```

not:

```text
Input rows
    ↓
Ranking
    ↓
Eligibility filter
    ↓
Rank filter
```

The correct order depends on the business definition, but the difference must be intentional.

## Trying to Filter a Window Function Directly in `WHERE`

This is invalid in PostgreSQL and most SQL implementations:

```sql
SELECT
    employee_id,
    ROW_NUMBER() OVER (
        ORDER BY salary DESC
    ) AS position
FROM employees
WHERE position <= 3;
```

The alias is not available to `WHERE`, and window functions cannot generally be evaluated directly as a `WHERE` predicate.

Use a subquery or CTE:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        salary,
        ROW_NUMBER() OVER (
            ORDER BY salary DESC
        ) AS position
    FROM employees
)
SELECT *
FROM ranked
WHERE position <= 3;
```

The outer query filters the already-computed ranking.

## Ranking Before Aggregation

Another common mistake is ranking raw transactional rows when the business metric is aggregated.

Suppose the requirement is:

> Top three customers by total order value per region.

This is wrong:

```sql
ROW_NUMBER() OVER (
    PARTITION BY region_id
    ORDER BY amount DESC
)
```

because it ranks individual orders.

Aggregate first:

```sql
WITH customer_totals AS (
    SELECT
        region_id,
        customer_id,
        SUM(amount) AS total_spend
    FROM orders
    GROUP BY
        region_id,
        customer_id
),
ranked AS (
    SELECT
        region_id,
        customer_id,
        total_spend,
        ROW_NUMBER() OVER (
            PARTITION BY region_id
            ORDER BY total_spend DESC, customer_id
        ) AS position
    FROM customer_totals
)
SELECT *
FROM ranked
WHERE position <= 3;
```

The general pattern is:

```text
Raw facts
    ↓
GROUP BY
    ↓
Business metric
    ↓
Window ranking
    ↓
Rank filtering
```

## Ranking After an Accidental Join Explosion

Joins can multiply rows before ranking.

Suppose:

```text
customers
    └── orders
          └── order_items
```

Joining all three tables and then applying `ROW_NUMBER()` can rank individual joined combinations instead of customers or orders.

For example:

```sql
SELECT
    c.id,
    o.id,
    ROW_NUMBER() OVER (
        PARTITION BY c.id
        ORDER BY o.created_at DESC
    ) AS position
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.id
JOIN order_items AS oi
    ON oi.order_id = o.id;
```

If an order has five items, it may appear five times.

The ranking population has already been corrupted.

Aggregate or deduplicate at the correct grain before ranking:

```sql
WITH customer_orders AS (
    SELECT DISTINCT
        c.id AS customer_id,
        o.id AS order_id,
        o.created_at
    FROM customers AS c
    JOIN orders AS o
        ON o.customer_id = c.id
    JOIN order_items AS oi
        ON oi.order_id = o.id
),
ranked AS (
    SELECT
        customer_id,
        order_id,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, order_id DESC
        ) AS position
    FROM customer_orders
)
SELECT *
FROM ranked
WHERE position = 1;
```

The senior-level question is:

> **What is the grain of the rows entering the window function?**

If the answer is unclear, the ranking query is probably not ready.

## Confusing Window `ORDER BY` with Final `ORDER BY`

This:

```sql
ROW_NUMBER() OVER (
    ORDER BY revenue DESC
)
```

defines ranking order.

It does not guarantee the final result is returned in revenue order.

Use:

```sql
SELECT
    product_id,
    revenue,
    ROW_NUMBER() OVER (
        ORDER BY revenue DESC, product_id
    ) AS position
FROM products
ORDER BY position;
```

A window's ordering and the query's final ordering serve different purposes.

| `ORDER BY` location | Purpose |
|---|---|
| `OVER (...)` | Determines ranking/window calculation |
| Outer query | Determines returned row order |

## Misunderstanding What "Top N" Means

"Top 3" is ambiguous.

It can mean:

| Requirement | Function |
|---|---|
| Exactly three physical rows | `ROW_NUMBER()` |
| First three competition ranks | `RANK()` |
| First three distinct values | `DENSE_RANK()` |

Consider:

```text
100
90
90
80
80
70
```

### Exactly Three Rows

```sql
ROW_NUMBER() <= 3
```

returns:

```text
100
90
90
```

### First Three Competition Ranks

```sql
RANK() <= 3
```

returns:

```text
100
90
90
```

because `80` has rank 4.

### First Three Distinct Values

```sql
DENSE_RANK() <= 3
```

returns:

```text
100
90
90
80
80
```

The SQL is only correct after the meaning of "top N" has been established.

## Ranking `NULL` Values Without Defining the Rule

`NULL` ordering can affect rankings.

For example:

```sql
ROW_NUMBER() OVER (
    ORDER BY score DESC
)
```

may place `NULL` values differently depending on the database's null-ordering rules.

In PostgreSQL, descending order places `NULL` values first by default unless explicitly changed.

If unknown scores should always be last:

```sql
ROW_NUMBER() OVER (
    ORDER BY score DESC NULLS LAST, player_id
)
```

For portable SQL, an explicit expression can be used when appropriate:

```sql
ROW_NUMBER() OVER (
    ORDER BY
        CASE WHEN score IS NULL THEN 1 ELSE 0 END,
        score DESC,
        player_id
)
```

Ranking requirements should explicitly define whether missing values are eligible and where they belong.

## Ranking Deleted or Inactive Data

Ranking historical or inactive records can produce incorrect business results.

For example:

```sql
WITH ranked AS (
    SELECT
        seller_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY seller_id
            ORDER BY revenue DESC, product_id
        ) AS position
    FROM products
)
SELECT *
FROM ranked
WHERE is_active = TRUE
  AND position <= 5;
```

Inactive products participated in ranking even though they should not.

If inactive products are not eligible:

```sql
FROM products
WHERE is_active = TRUE
```

must occur before the window calculation.

The same principle applies to:

- Soft-deleted rows.
- Archived records.
- Cancelled transactions.
- Disabled accounts.
- Expired offers.

## Ranking Historical Data Without a Time Boundary

A query such as:

```sql
ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY created_at DESC
)
```

considers the entire available history.

If the requirement is:

> Latest event per customer during the current month.

the time restriction belongs in the ranking input:

```sql
WITH ranked AS (
    SELECT
        customer_id,
        event_id,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY created_at DESC, event_id DESC
        ) AS position
    FROM customer_events
    WHERE created_at >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
)
SELECT *
FROM ranked
WHERE position = 1;
```

Otherwise, an older event can affect the ranking population.

## Assuming Ranking Is Stable

A ranking is normally derived state.

If a leaderboard is:

```sql
RANK() OVER (
    ORDER BY score DESC
)
```

then changing one player's score can change the ranks of multiple players.

Therefore:

- Rankings can change between requests.
- Concurrent writes can affect results.
- Historical rankings should not be inferred from current source data.
- A stable ranking snapshot may need to be materialized.

For audit-sensitive systems, store the ranking snapshot explicitly:

```text
leaderboard_snapshot
--------------------
snapshot_id
entity_id
score
rank
generated_at
```

Do not reconstruct historical business decisions from mutable source data unless that behavior is explicitly acceptable.

## Using Ranking as Pagination

This pattern:

```sql
ROW_NUMBER() OVER (
    ORDER BY created_at DESC
)
```

can assign positions, but it does not automatically make an efficient pagination strategy.

A query that calculates row numbers across a very large dataset may process many rows just to return one page.

For high-volume APIs, keyset pagination is often preferable:

```sql
SELECT
    id,
    created_at,
    title
FROM posts
WHERE (created_at, id) < (:cursor_created_at, :cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Use ranking when the position itself is part of the requirement.

Use pagination techniques when the requirement is efficient navigation through a large ordered result.

## Ranking Large Datasets Without Restricting Input

This query:

```sql
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC
        ) AS position
    FROM product_sales
)
SELECT *
FROM ranked
WHERE position <= 10;
```

may rank millions of rows even though only ten rows per category are ultimately required.

The database generally cannot assume that the outer filter can eliminate all ranking work.

For large production datasets:

- Restrict by tenant, time range, status, or other valid predicates before ranking.
- Aggregate before ranking.
- Select only required columns.
- Examine the actual execution plan.
- Consider summary tables or materialized views for repeated expensive workloads.
- Consider precomputed leaderboards when freshness requirements allow it.

Use:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

in PostgreSQL to validate the actual cost.

## Ignoring Index and Execution-Plan Behavior

Window functions frequently require ordering within partitions.

An index can help with filtering and may sometimes help the planner avoid or reduce sorting, but an index is not a guarantee that a window query will become cheap.

For:

```sql
ROW_NUMBER() OVER (
    PARTITION BY tenant_id
    ORDER BY created_at DESC, id DESC
)
```

a potentially useful index might be:

```sql
CREATE INDEX CONCURRENTLY idx_events_tenant_created_id
ON events (tenant_id, created_at DESC, id DESC);
```

But the right index depends on:

- Query predicates.
- Table size.
- Data distribution.
- Cardinality.
- PostgreSQL version.
- Existing indexes.
- Join strategy.
- Whether the query scans most of the table.

Always verify with the actual execution plan rather than adding indexes based solely on the window expression.

## Security Mistakes in Multi-Tenant Ranking

A ranking query can accidentally expose another tenant's data.

For example:

```sql
SELECT
    tenant_id,
    user_id,
    score,
    RANK() OVER (
        ORDER BY score DESC
    ) AS position
FROM user_scores;
```

This creates a global leaderboard.

If the API is supposed to expose only one tenant:

```sql
SELECT
    user_id,
    score,
    RANK() OVER (
        ORDER BY score DESC
    ) AS position
FROM user_scores
WHERE tenant_id = :tenant_id;
```

For stronger isolation, PostgreSQL Row-Level Security can provide a database-level enforcement layer.

The important distinction is:

```text
PARTITION BY → ranking scope
WHERE / RLS   → data visibility
```

A partition does not prevent unauthorized rows from being returned.

## Using Application Code for Database Ranking

A common anti-pattern is loading all rows into Python:

```python
records = list(queryset)

records.sort(key=lambda row: row.score, reverse=True)

for position, record in enumerate(records, start=1):
    ...
```

This can be problematic because:

- Large datasets consume application memory.
- Network transfer increases.
- Database sorting capabilities are bypassed.
- Multiple application instances may repeat the same expensive work.
- Pagination and consistency become harder to manage.

When ranking can be expressed naturally in SQL, keep the computation close to the data:

```sql
SELECT
    id,
    score,
    RANK() OVER (
        ORDER BY score DESC
    ) AS position
FROM scores;
```

Application code is still appropriate when ranking requires logic that is genuinely outside SQL's useful scope.

## Ignoring Transaction Consistency

A ranking query sees a database snapshot according to the transaction and isolation level in effect.

For a single SQL statement, the database can provide a consistent view appropriate to its isolation semantics. Across multiple statements, however, source data can change between reads.

This matters when an API does something like:

1. Query the total population.
2. Query the ranking.
3. Query individual records.
4. Return a combined response.

Those statements may observe different database states.

If the ranking must correspond to a consistent snapshot, use an appropriate transaction strategy or materialized snapshot.

Do not use stronger isolation blindly. Higher isolation can increase contention and reduce throughput.

## Interview Traps

### "Find the Second Highest Salary"

This question is often ambiguous.

Second highest **distinct salary**:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        salary,
        DENSE_RANK() OVER (
            ORDER BY salary DESC
        ) AS salary_rank
    FROM employees
)
SELECT *
FROM ranked
WHERE salary_rank = 2;
```

If exactly one employee must be selected, the business rule needs a tie-breaker and `ROW_NUMBER()` may be appropriate.

### "Top Three Employees"

Ask:

> Top three employees by row count, top three ranks, or top three distinct salaries?

Without that clarification, multiple valid SQL implementations exist.

### "Latest Record"

Ask:

> What happens when two records have the same timestamp?

If exactly one record must be returned, use a deterministic tie-breaker:

```sql
ORDER BY created_at DESC, id DESC
```

### "Top N per Group"

The standard solution is usually:

```sql
WITH ranked AS (
    SELECT
        ...,
        ROW_NUMBER() OVER (
            PARTITION BY group_id
            ORDER BY metric DESC, id
        ) AS position
    FROM source
)
SELECT ...
FROM ranked
WHERE position <= :n;
```

But the correct function changes if ties must be preserved.

## Production Review Checklist

Before approving a ranking query, verify:

| Review question | Expected decision |
|---|---|
| What is being ranked? | Explicit row grain |
| What defines the group? | Correct `PARTITION BY` |
| What defines order? | Explicit ranking columns |
| What happens on ties? | `ROW_NUMBER()`, `RANK()`, or `DENSE_RANK()` chosen intentionally |
| Is a unique winner required? | Stable tie-breaker included |
| What does N mean? | Rows, ranks, or distinct values |
| Which rows are eligible? | Filters applied at the correct stage |
| Is aggregation required? | Aggregate before ranking |
| Are joins multiplying rows? | Validate input grain |
| Are `NULL`s handled intentionally? | Explicit null ordering where required |
| Is the final result ordered? | Outer `ORDER BY` added if needed |
| Is the dataset large? | Execution plan reviewed |
| Is this multi-tenant? | Visibility and ranking scope separated |
| Is ranking expected to remain stable? | Materialize a snapshot if required |
| Is this an API pagination problem? | Consider keyset pagination instead |
| Is ranking repeated frequently? | Evaluate precomputation or caching |

## Debugging a Wrong Ranking Query

When a ranking query produces unexpected results, inspect the query in layers.

Start with the source population:

```sql
SELECT
    ...
FROM source
WHERE ...;
```

Then verify the grain:

```sql
SELECT
    group_id,
    COUNT(*)
FROM source
GROUP BY group_id;
```

Then add the ranking:

```sql
SELECT
    ...,
    ROW_NUMBER() OVER (
        PARTITION BY group_id
        ORDER BY metric DESC, id
    ) AS position
FROM source
WHERE ...;
```

Finally add the rank filter:

```sql
WITH ranked AS (
    ...
)
SELECT *
FROM ranked
WHERE position <= 3;
```

This makes it easier to determine whether the bug originates from:

- Input filtering.
- Joins.
- Aggregation.
- Partitioning.
- Ordering.
- Tie handling.
- Final filtering.

## Key Takeaways

- **Most ranking bugs are semantic rather than syntactic: define the ranking population, tie behavior, partition scope, and meaning of N before writing SQL.**
- **Use `ROW_NUMBER()` for deterministic row selection, `RANK()` for preserved competition ties, and `DENSE_RANK()` for distinct ranking levels.**
- **Filters and aggregation must occur at the correct stage because ranking operates on the rows visible to its query block.**
- **For production systems, explicitly handle tie-breakers, `NULL`s, tenant boundaries, execution-plan cost, and ranking consistency.**
- **Treat ranking as derived query state; materialize it when historical stability or high-volume repeated reads require a persistent snapshot.**