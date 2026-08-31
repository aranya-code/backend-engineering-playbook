# 03- RANK

## Overview

`RANK()` is a SQL window function that assigns a ranking to rows according to an ordering while giving rows with equal ordering values the same rank. Unlike `ROW_NUMBER()`, ties do not receive unique positions, and gaps appear after tied ranks.

The general form is:

```sql
RANK() OVER (
    [PARTITION BY partition_columns]
    ORDER BY ordering_columns
)
```

`RANK()` is useful when the business meaning of a position is based on **rank**, rather than the physical position of an individual row.

Typical backend and analytics use cases include:

- Leaderboards.
- Top performers.
- Sales rankings.
- Product rankings.
- Competition results.
- Department-level employee rankings.
- Selecting all records within the top N ranks.

The key distinction is:

```text
ROW_NUMBER() → every row gets a unique number
RANK()       → tied rows share a rank and create gaps
DENSE_RANK() → tied rows share a rank without gaps
```

## Why `RANK()` Exists

Consider a leaderboard:

| player | score |
|---|---:|
| Alice | 100 |
| Bob | 100 |
| Carol | 90 |
| Dave | 80 |

Alice and Bob have the same score, so both should reasonably be ranked first.

`RANK()` produces:

| player | score | rank |
|---|---:|---:|
| Alice | 100 | 1 |
| Bob | 100 | 1 |
| Carol | 90 | 3 |
| Dave | 80 | 4 |

There is no rank `2` because two rows occupy rank `1`.

This behavior is appropriate when the ranking represents competition or ordinal placement where ties consume the same rank position.

## How `RANK()` Works

The database evaluates the rows according to the window definition:

```sql
RANK() OVER (
    ORDER BY score DESC
)
```

Conceptually:

```text
Input rows
    │
    ▼
Order by score
    │
    ▼
Identify equal ordering values
    │
    ▼
Assign shared ranks
    │
    ▼
Leave gaps after ties
```

For:

```text
100
100
90
80
80
70
```

the ranks are:

```text
100 → 1
100 → 1
 90 → 3
 80 → 4
 80 → 4
 70 → 6
```

The next rank is based on the number of preceding rows, not the number of distinct values.

## Basic Usage

A global ranking can be calculated without `PARTITION BY`:

```sql
SELECT
    employee_id,
    salary,
    RANK() OVER (
        ORDER BY salary DESC
    ) AS salary_rank
FROM employees;
```

Example:

| employee_id | salary | salary_rank |
|---:|---:|---:|
| 101 | 150000 | 1 |
| 102 | 150000 | 1 |
| 103 | 130000 | 3 |
| 104 | 120000 | 4 |

The `SELECT` still returns every employee. `RANK()` adds a calculated value to each row.

## `RANK()` With `PARTITION BY`

`PARTITION BY` creates independent ranking groups.

For example, rank employees within each department:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    RANK() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS department_rank
FROM employees;
```

Example:

| employee_id | department_id | salary | department_rank |
|---:|---:|---:|---:|
| 101 | 10 | 150000 | 1 |
| 102 | 10 | 150000 | 1 |
| 103 | 10 | 120000 | 3 |
| 201 | 20 | 180000 | 1 |
| 202 | 20 | 140000 | 2 |
| 203 | 20 | 140000 | 2 |

The rank restarts at `1` for every department.

`PARTITION BY` does not reduce the result set. It only defines the independent ranking populations.

## `RANK()` vs `ROW_NUMBER()` vs `DENSE_RANK()`

This comparison is fundamental for SQL interviews and production reporting.

Suppose the values are:

```text
100
100
90
80
80
70
```

| Value | `ROW_NUMBER()` | `RANK()` | `DENSE_RANK()` |
|---:|---:|---:|---:|
| 100 | 1 | 1 | 1 |
| 100 | 2 | 1 | 1 |
| 90 | 3 | 3 | 2 |
| 80 | 4 | 4 | 3 |
| 80 | 5 | 4 | 3 |
| 70 | 6 | 6 | 4 |

### `ROW_NUMBER()`

Every row receives a unique number.

Use it when the requirement is:

> Select exactly one physical row or exactly N rows.

### `RANK()`

Tied rows receive the same rank, and subsequent ranks contain gaps.

Use it when the requirement is:

> Preserve competition-style ranking where ties occupy the same position.

### `DENSE_RANK()`

Tied rows receive the same rank, but subsequent ranks do not contain gaps.

Use it when the requirement is:

> Rank distinct values without gaps.

## The Importance of the Window `ORDER BY`

The ordering expression defines what constitutes a ranking comparison.

For example:

```sql
RANK() OVER (
    ORDER BY revenue DESC
)
```

ranks customers according to revenue.

For a lowest-price ranking:

```sql
RANK() OVER (
    ORDER BY price ASC
)
```

For a most-recent ranking:

```sql
RANK() OVER (
    ORDER BY created_at DESC
)
```

The direction is part of the business rule.

## Ties and Secondary Ordering

A subtle but important property of `RANK()` is that adding a secondary column can eliminate ties.

Consider:

```sql
RANK() OVER (
    ORDER BY score DESC
)
```

Two players with score `100` receive the same rank.

Now consider:

```sql
RANK() OVER (
    ORDER BY score DESC, player_id
)
```

Because `player_id` is different, the complete ordering keys are different. The players no longer tie.

Example:

| player_id | score | rank |
|---:|---:|---:|
| 101 | 100 | 1 |
| 102 | 100 | 2 |
| 103 | 90 | 3 |

This is an important difference from `ROW_NUMBER()`.

### Production Rule

For `RANK()`:

> Only include columns in the window `ORDER BY` that should determine whether two rows are considered tied.

For deterministic presentation, a separate outer `ORDER BY` can be used without changing the ranking semantics:

```sql
SELECT
    player_id,
    score,
    RANK() OVER (
        ORDER BY score DESC
    ) AS score_rank
FROM players
ORDER BY score_rank, player_id;
```

Here `player_id` determines display order but does not break the score tie.

## Selecting the Top N Ranks

One of the most useful patterns is selecting all rows belonging to the top N ranks.

Suppose:

```text
score
-----
100
100
90
80
80
70
```

To select the top three ranks:

```sql
WITH ranked_players AS (
    SELECT
        player_id,
        score,
        RANK() OVER (
            ORDER BY score DESC
        ) AS score_rank
    FROM players
)
SELECT
    player_id,
    score,
    score_rank
FROM ranked_players
WHERE score_rank <= 3
ORDER BY score_rank, player_id;
```

The result contains:

| player_id | score | score_rank |
|---:|---:|---:|
| 101 | 100 | 1 |
| 102 | 100 | 1 |
| 103 | 90 | 3 |

There is no rank `2`, so rank `4` is outside the requested top three ranks.

This can return **more than three rows** because ties are preserved.

That is the primary reason to choose `RANK()` over `ROW_NUMBER()` for tie-aware top-N requirements.

## Top N Per Group

`RANK()` can select all tied records within the top N ranks of every group.

For example, find the top three salespeople in each region:

```sql
WITH ranked_salespeople AS (
    SELECT
        salesperson_id,
        region_id,
        revenue,
        RANK() OVER (
            PARTITION BY region_id
            ORDER BY revenue DESC
        ) AS region_rank
    FROM salesperson_revenue
)
SELECT
    salesperson_id,
    region_id,
    revenue,
    region_rank
FROM ranked_salespeople
WHERE region_rank <= 3
ORDER BY region_id, region_rank, salesperson_id;
```

If two salespeople tie at rank `3`, both are included.

Therefore:

```text
ROW_NUMBER() + rn <= 3
    → maximum 3 rows per region

RANK() + rank <= 3
    → all rows belonging to the top 3 ranks
```

This distinction should be explicit in API and product requirements.

## Ranking Aggregated Data

`RANK()` frequently operates on aggregated metrics rather than raw records.

For example, rank customers by total revenue:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS total_revenue
    FROM payments
    WHERE status = 'succeeded'
    GROUP BY customer_id
)
SELECT
    customer_id,
    total_revenue,
    RANK() OVER (
        ORDER BY total_revenue DESC
    ) AS revenue_rank
FROM customer_revenue
ORDER BY revenue_rank, customer_id;
```

The processing model is:

```text
payments
   │
   ▼
GROUP BY customer
   │
   ▼
customer revenue
   │
   ▼
RANK() by revenue
   │
   ▼
customer leaderboard
```

This is useful for:

- Customer leaderboards.
- Revenue dashboards.
- Sales reporting.
- Partner rankings.
- Marketplace analytics.

## Ranking Within Time Periods

Ranking can be reset for each reporting period.

For example, rank customers by monthly revenue:

```sql
WITH monthly_revenue AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', paid_at) AS month,
        SUM(amount) AS revenue
    FROM payments
    WHERE status = 'succeeded'
    GROUP BY
        customer_id,
        DATE_TRUNC('month', paid_at)
)
SELECT
    customer_id,
    month,
    revenue,
    RANK() OVER (
        PARTITION BY month
        ORDER BY revenue DESC
    ) AS monthly_rank
FROM monthly_revenue
ORDER BY month, monthly_rank, customer_id;
```

Each month has an independent leaderboard.

This pattern is common in analytics systems and scheduled reporting pipelines.

## Ranking With Filters

The rows entering the window calculation determine the ranking population.

For example:

```sql
SELECT
    employee_id,
    department_id,
    salary,
    RANK() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS department_rank
FROM employees
WHERE active = true;
```

Only active employees participate in the ranking.

If the requirement instead means:

> Rank all employees, then return only active employees,

the query needs another level:

```sql
WITH ranked_employees AS (
    SELECT
        employee_id,
        department_id,
        salary,
        active,
        RANK() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
        ) AS department_rank
    FROM employees
)
SELECT
    employee_id,
    department_id,
    salary,
    department_rank
FROM ranked_employees
WHERE active = true;
```

These queries answer different questions.

This is a common production bug when developers move predicates between query levels without considering the ranking population.

## Latest Rank Per Entity

`RANK()` can be used for time-based ordering, but it is important to understand the tie behavior.

For example:

```sql
WITH ranked_events AS (
    SELECT
        event_id,
        device_id,
        event_type,
        occurred_at,
        RANK() OVER (
            PARTITION BY device_id
            ORDER BY occurred_at DESC
        ) AS event_rank
    FROM device_events
)
SELECT
    event_id,
    device_id,
    event_type,
    occurred_at
FROM ranked_events
WHERE event_rank = 1;
```

This returns the latest event for each device **and all events tied for the latest timestamp**.

If exactly one event must be selected, use `ROW_NUMBER()` with a deterministic tie-breaker:

```sql
ROW_NUMBER() OVER (
    PARTITION BY device_id
    ORDER BY occurred_at DESC, event_id DESC
)
```

This is an important design decision.

## Multi-Tenant Ranking

For a multi-tenant backend, ranking often needs to be scoped to the tenant.

For example:

```sql
SELECT
    customer_id,
    tenant_id,
    revenue,
    RANK() OVER (
        PARTITION BY tenant_id
        ORDER BY revenue DESC
    ) AS tenant_rank
FROM customer_revenue
WHERE tenant_id = :tenant_id;
```

The tenant filter controls which rows are accessible.

The window partition controls how those rows are ranked.

These are separate responsibilities:

```text
Authorization / isolation
    ↓
WHERE tenant_id = :tenant_id

Business ranking
    ↓
PARTITION BY tenant_id
```

`RANK()` is not an authorization mechanism. Access control must be enforced independently.

## Backend Application Integration

### Django

Django supports ranking through `Window()`:

```python
from django.db.models import F, Window
from django.db.models.functions import Rank

queryset = (
    CustomerRevenue.objects
    .annotate(
        revenue_rank=Window(
            expression=Rank(),
            order_by=F("revenue").desc(),
        )
    )
    .order_by("revenue_rank", "customer_id")
)
```

For tenant-specific ranking:

```python
queryset = (
    CustomerRevenue.objects
    .filter(tenant_id=tenant_id)
    .annotate(
        tenant_rank=Window(
            expression=Rank(),
            partition_by=[F("tenant_id")],
            order_by=F("revenue").desc(),
        )
    )
    .order_by("tenant_rank", "customer_id")
)
```

For complex queries:

- Inspect the generated SQL.
- Verify that filters occur at the intended query level.
- Test tie behavior explicitly.
- Benchmark the database query rather than assuming ORM performance.
- Avoid loading all rows into Python merely to calculate rankings.

### FastAPI and REST APIs

A ranking query can back endpoints such as:

```text
GET /leaderboards
GET /regions/{region_id}/top-salespeople
GET /customers/rankings
```

API requirements should explicitly define whether ties are included.

For example:

```json
{
  "rank": 1,
  "customer_id": 42,
  "revenue": "150000.00"
}
```

If two customers have the same revenue, both should receive rank `1` when using `RANK()`.

Do not silently change the semantics to `ROW_NUMBER()` merely to force a fixed response size.

## Performance Considerations

Ranking requires the database to establish ordering for the rows participating in the window.

For large datasets, this can involve:

- Sorting.
- CPU consumption.
- Memory usage.
- Temporary disk usage.
- Large intermediate result sets.

Use PostgreSQL execution plans to validate the actual cost:

```sql
EXPLAIN (ANALYZE, BUFFERS)
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM payments
    WHERE tenant_id = 42
      AND status = 'succeeded'
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_revenue;
```

### Reduce the Ranking Input

If historical records are irrelevant, filter them before aggregation and ranking:

```sql
WITH customer_revenue AS (
    SELECT
        customer_id,
        SUM(amount) AS revenue
    FROM payments
    WHERE tenant_id = :tenant_id
      AND status = 'succeeded'
      AND paid_at >= :start_date
    GROUP BY customer_id
)
SELECT
    customer_id,
    revenue,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS revenue_rank
FROM customer_revenue;
```

Reducing the number of rows entering the aggregation and window operation can substantially improve performance.

The filter must still match the business definition of the ranking period.

## Indexing Considerations

Indexes can help reduce the cost of filtering and grouping, although they do not guarantee that a window operation will avoid sorting.

For example:

```sql
CREATE INDEX CONCURRENTLY idx_payments_tenant_status_paid_at
ON payments (
    tenant_id,
    status,
    paid_at
);
```

This can support workloads that frequently filter payments by tenant, status, and time period.

For ranking queries, evaluate:

- Filter selectivity.
- Group cardinality.
- Number of rows per tenant.
- Frequency of the query.
- Write overhead from additional indexes.
- PostgreSQL execution plans.

Do not create indexes solely because a query contains `RANK()`.

## Production Considerations

### Define Tie Semantics Explicitly

Before implementing a leaderboard, clarify:

- What value determines the ranking?
- Should equal values receive the same rank?
- Should gaps appear after ties?
- Should the API return all tied rows?
- Is exactly N rows required?

The answers determine whether to use:

```text
ROW_NUMBER()
RANK()
DENSE_RANK()
```

### Large Leaderboards

For very large or frequently requested leaderboards:

- Restrict the ranking population.
- Pre-aggregate expensive metrics.
- Use materialized views when appropriate.
- Refresh derived rankings asynchronously.
- Cache stable leaderboard results when business requirements allow it.
- Avoid recalculating millions of rows for every API request.

Redis can be useful for serving precomputed leaderboard data, but it should not replace the database as the source of truth unless the architecture explicitly supports that model.

### Materialized Reporting

If a leaderboard is requested frequently but changes relatively infrequently, consider a precomputed table:

```text
payments
   │
   ▼
Aggregation job
   │
   ▼
customer_revenue
   │
   ▼
Ranking job
   │
   ▼
leaderboard table
   │
   ▼
REST / gRPC API
```

This moves expensive computation away from latency-sensitive API requests.

### Reliability

Test ranking behavior for:

- Tied values.
- Null values.
- Empty groups.
- Single-row groups.
- Very large partitions.
- Concurrent data changes.
- Different reporting periods.
- Multiple tenants.

Do not assume the output is correct merely because the SQL executes successfully.

## Common Mistakes

| Mistake | Problem | Correct approach |
|---|---|---|
| Using `ROW_NUMBER()` for competition ranking | Equal values receive different positions | Use `RANK()` |
| Using `RANK()` when exactly N rows are required | Ties can produce more than N rows | Use `ROW_NUMBER()` |
| Using `RANK()` when gaps are undesirable | Ties create rank gaps | Use `DENSE_RANK()` |
| Adding a unique tie-breaker to `RANK()` | Equal business values stop tying | Keep only ranking attributes in the window `ORDER BY` |
| Filtering before ranking unintentionally | Changes the ranking population | Place filters at the correct query level |
| Filtering `rank` in the same query's `WHERE` clause | Window results are not available at that level | Use a CTE or subquery |
| Assuming rank numbers are unique | Multiple rows can share a rank | Use a primary key for row identity |
| Assuming top 10 ranks means 10 rows | Ties can produce more than 10 rows | Distinguish top N ranks from top N rows |
| Ranking huge raw tables repeatedly | Expensive sorting and aggregation | Pre-aggregate or materialize where appropriate |
| Using ranking for tenant isolation | Window functions do not enforce authorization | Apply explicit tenant/ownership predicates |

## Interview Traps

### Top Three Rows vs Top Three Ranks

These requirements are different.

**Exactly three rows:**

```sql
ROW_NUMBER() OVER (
    ORDER BY score DESC
)
```

**All rows in the top three ranks:**

```sql
RANK() OVER (
    ORDER BY score DESC
)
```

If scores are:

```text
100
100
90
80
80
70
```

then:

```text
ROW_NUMBER() <= 3
    → 100, 100, 90

RANK() <= 3
    → 100, 100, 90
```

But if the data is:

```text
100
90
90
90
80
```

then:

```text
ROW_NUMBER() <= 3
    → 100, 90, 90

RANK() <= 3
    → 100, 90, 90, 90
```

The difference is driven by ties.

### Second-Highest Salary

If the requirement is:

> Find employees whose salary is the second-highest distinct salary.

Use `DENSE_RANK()`:

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
SELECT
    employee_id,
    salary
FROM ranked
WHERE salary_rank = 2;
```

If the requirement is:

> Find the employees occupying the second competition rank.

`RANK()` may be appropriate:

```sql
WITH ranked AS (
    SELECT
        employee_id,
        salary,
        RANK() OVER (
            ORDER BY salary DESC
        ) AS salary_rank
    FROM employees
)
SELECT
    employee_id,
    salary
FROM ranked
WHERE salary_rank = 2;
```

The distinction is not syntactic; it is a business-definition decision.

## PostgreSQL Example: Regional Sales Leaderboard

A production-style query can combine filtering, aggregation, partitioning, ranking, and deterministic presentation:

```sql
WITH regional_sales AS (
    SELECT
        salesperson_id,
        region_id,
        SUM(amount) AS revenue
    FROM orders
    WHERE tenant_id = :tenant_id
      AND status = 'completed'
      AND created_at >= :start_date
      AND created_at < :end_date
    GROUP BY
        salesperson_id,
        region_id
),
ranked_sales AS (
    SELECT
        salesperson_id,
        region_id,
        revenue,
        RANK() OVER (
            PARTITION BY region_id
            ORDER BY revenue DESC
        ) AS region_rank
    FROM regional_sales
)
SELECT
    salesperson_id,
    region_id,
    revenue,
    region_rank
FROM ranked_sales
WHERE region_rank <= 3
ORDER BY
    region_id,
    region_rank,
    salesperson_id;
```

The query separates responsibilities:

```text
orders
  │
  ├── tenant/status/date filtering
  │
  ▼
regional aggregation
  │
  ▼
RANK() within region
  │
  ▼
top 3 ranks
  │
  ▼
deterministic API/report ordering
```

This structure is easier to test and reason about than attempting to combine every operation into one expression.

## Security Considerations

`RANK()` has no special security model. The security responsibility remains with the query's filtering and application authorization.

For tenant-aware applications:

```sql
WHERE tenant_id = :tenant_id
```

must be derived from authenticated application context rather than blindly trusting a client-provided tenant identifier.

Use parameterized queries:

```python
cursor.execute(
    """
    SELECT
        customer_id,
        revenue,
        RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
    FROM customer_revenue
    WHERE tenant_id = %s
    """,
    [tenant_id],
)
```

Do not concatenate request parameters into SQL.

For high-assurance PostgreSQL multi-tenant systems, row-level security can provide an additional database-level isolation boundary. The ranking function should then operate only on rows the database allows the session to access.

## Operational Monitoring

Ranking queries that execute on request paths should be monitored like other expensive database workloads.

Track:

- Query latency.
- Rows processed.
- Rows returned.
- CPU utilization.
- Temporary file usage.
- Buffer reads.
- Lock waits.
- Query frequency.
- Cache hit rate where applicable.

For PostgreSQL, use tools such as:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

and production query-statistics facilities such as `pg_stat_statements`.

Alert on regressions in query latency and resource consumption rather than simply monitoring whether the query succeeds.

## Key Takeaways

- **`RANK()` assigns the same rank to tied values and leaves gaps after ties, making it appropriate for competition-style rankings.**
- **Use `ROW_NUMBER()` for exactly-N physical rows, `RANK()` for tie-aware competition ranking, and `DENSE_RANK()` for distinct-value ranking without gaps.**
- **The columns in the window `ORDER BY` define tie semantics; adding a unique secondary key to `RANK()` can unintentionally eliminate ties.**
- **For production leaderboards, distinguish top N rows from top N ranks, control the ranking population, and pre-aggregate expensive workloads when necessary.**
- **Ranking is separate from authorization and tenant isolation; enforce access boundaries independently and validate expensive queries with realistic execution plans.**