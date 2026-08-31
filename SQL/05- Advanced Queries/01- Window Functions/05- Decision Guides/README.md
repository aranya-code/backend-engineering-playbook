# README

## Overview

Window functions are powerful SQL features for performing calculations across related rows without collapsing the result set. They are especially useful for ranking, row-to-row analysis, running calculations, and analytical reporting.

The **Decision Guides** section focuses on choosing the right SQL technique for a requirement rather than memorizing window-function syntax. The key engineering skill is recognizing when a window function is appropriate and when `GROUP BY`, `JOIN`, subqueries, CTEs, or simpler ordering operations are better.

This folder provides practical decision rules for selecting between common SQL approaches and for understanding the performance and correctness trade-offs involved.

## Decision Guides

| Document | Focus |
|---|---|
| [Window Function Selection Guide](./01-%20Window%20Function%20Selection%20Guide.md) | Choose the appropriate window-function family and SQL technique based on the problem |
| [Window Function vs GROUP BY](./02-%20Window%20Function%20vs%20GROUP%20BY.md) | Decide between row-preserving window calculations and grouped aggregation |
| [Window Function vs Subquery](./03-%20Window%20Function%20vs%20Subquery.md) | Compare window functions with scalar, correlated, and derived subqueries |
| [Window Function vs CTE](./04-%20Window%20Function%20vs%20CTE.md) | Understand when window functions and CTEs solve different parts of the same query |
| [ROW_NUMBER vs RANK vs DENSE_RANK](./05-%20ROW_NUMBER%20vs%20RANK%20vs%20DENSE_RANK.md) | Select the correct ranking function based on tie behavior and business requirements |
| [LAG vs LEAD](./06-%20LAG%20vs%20LEAD.md) | Choose between previous-row and next-row analysis |
| [ROWS vs RANGE](./07-%20ROWS%20vs%20RANGE.md) | Understand physical-row versus peer/value-based window frames |
| [When to Use Window Functions](./08-%20When%20to%20Use%20Window%20Functions.md) | Identify workloads where window functions provide a natural and maintainable solution |
| [When Not to Use Window Functions](./09-%20When%20Not%20to%20Use%20Window%20Functions.md) | Recognize cases where simpler SQL constructs or architectural alternatives are preferable |

## How to Use This Folder

Use the documents as a decision layer after understanding the underlying window-function concepts.

A practical workflow is:

```text
Requirement
    |
    v
Does the calculation require row context?
    |
    +-- No --> GROUP BY / JOIN / EXISTS / DISTINCT / LIMIT
    |
    +-- Yes
          |
          v
Does it depend on ranking?
    |
    +-- Yes --> ROW_NUMBER / RANK / DENSE_RANK
    |
    +-- No
          |
          v
Does it depend on another row?
    |
    +-- Previous --> LAG
    +-- Next     --> LEAD
    |
    v
Does it require an ordered aggregate?
    |
    +-- Yes --> Window aggregate + appropriate frame
```

The most important question is not **"Which window function should I use?"** but:

> **"Does this problem actually require a window function?"**

## Core Decision Principles

### Preserve Rows vs Collapse Rows

Use a window function when individual rows must remain visible alongside an aggregate or analytical value.

```sql
SELECT
    customer_id,
    order_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

Use `GROUP BY` when the desired result is one row per group.

```sql
SELECT
    customer_id,
    SUM(amount) AS customer_total
FROM orders
GROUP BY customer_id;
```

### Global vs Partitioned Analysis

A global top-N query normally does not require a window function:

```sql
SELECT
    product_id,
    revenue
FROM products
ORDER BY revenue DESC
LIMIT 10;
```

Top-N **per group** does:

```sql
SELECT *
FROM (
    SELECT
        product_id,
        category_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS row_num
    FROM products
) AS ranked
WHERE row_num <= 10;
```

### Position vs Value

Ranking functions answer questions about **position**:

```sql
ROW_NUMBER()
RANK()
DENSE_RANK()
```

Value functions such as `LAG()` and `LEAD()` answer questions about **related rows**:

```sql
LAG(value)
LEAD(value)
```

This distinction makes function selection substantially easier.

### Physical Rows vs Peer Groups

Window frames determine which rows participate in an ordered window calculation.

`ROWS` operates on physical row positions:

```sql
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
```

`RANGE` operates according to the ordering value and can include peer rows with the same ordering value.

For financial and event-processing workloads, the distinction can materially change results.

## Production Considerations

Window-function decisions should be based on both semantics and execution characteristics.

Before shipping a query, evaluate:

- Result cardinality.
- Partition cardinality.
- Data skew.
- Required ordering.
- Sort operations.
- Memory consumption.
- Temporary disk usage.
- Index availability.
- Query concurrency.
- Expected table growth.
- API latency requirements.

For PostgreSQL, inspect the actual execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    order_id,
    amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
    ) AS row_num
FROM orders;
```

A syntactically elegant window query can still be a poor production query if it repeatedly sorts millions of rows for a latency-sensitive API.

## Result Shape Is a Primary Decision Tool

A useful mental model is:

| Requirement | Typical choice |
|---|---|
| One row per group | `GROUP BY` |
| Every row plus group aggregate | Window function |
| Check whether something exists | `EXISTS` |
| Combine related entities | `JOIN` |
| Remove duplicate values | `DISTINCT` |
| Global top-N | `ORDER BY ... LIMIT` |
| Top-N per group | Window function |
| Previous row | `LAG()` |
| Next row | `LEAD()` |
| Sequential row number | `ROW_NUMBER()` |
| Ranking with gaps | `RANK()` |
| Ranking without gaps | `DENSE_RANK()` |
| Running or moving calculation | Window aggregate |
| Multi-stage query organization | CTE |
| Very expensive recurring analytics | Precomputation / analytical workload |

## Backend Engineering Applications

Window-function decisions commonly appear in backend systems involving:

- Customer activity history.
- Order and payment analysis.
- Subscription lifecycle events.
- Audit logs.
- API usage metrics.
- Per-tenant rankings.
- Product recommendations.
- Financial transaction analysis.
- Time-series event processing.
- Operational dashboards.

For example, a REST API might need to return the latest event for every resource. A window function can solve this cleanly:

```sql
WITH ranked_events AS (
    SELECT
        resource_id,
        event_id,
        event_type,
        occurred_at,
        ROW_NUMBER() OVER (
            PARTITION BY resource_id
            ORDER BY occurred_at DESC, event_id DESC
        ) AS row_num
    FROM resource_events
)
SELECT
    resource_id,
    event_id,
    event_type,
    occurred_at
FROM ranked_events
WHERE row_num = 1;
```

The API layer in Django or FastAPI should normally consume this result rather than loading all historical events into Python and calculating the latest event in application memory.

## Common Mistakes

Avoid these patterns unless the requirement genuinely needs them:

- Using `ROW_NUMBER()` for a global top-N query.
- Using a window aggregate when `GROUP BY` already produces the required result.
- Using a window function merely to remove duplicates.
- Assuming `RANK()` and `DENSE_RANK()` behave identically for ties.
- Omitting a deterministic tie-breaker from ranking queries.
- Confusing `ROWS` with `RANGE`.
- Assuming `PARTITION BY` behaves like `GROUP BY`.
- Processing very large partitions without examining the execution plan.
- Moving large relational calculations into Python unnecessarily.
- Running heavy analytical window queries repeatedly against an OLTP database.

## Recommended Selection Order

When facing an analytical SQL requirement:

1. Define the required result shape.
2. Determine whether rows must be preserved.
3. Identify whether the requirement is global or partitioned.
4. Determine whether the calculation depends on row position, ordering, or neighboring rows.
5. Check whether `GROUP BY`, `JOIN`, `EXISTS`, `DISTINCT`, or `LIMIT` solves the problem more directly.
6. Select the appropriate window-function family if row context is required.
7. Make ordering deterministic when business correctness depends on it.
8. Validate the query with realistic data and `EXPLAIN (ANALYZE, BUFFERS)`.
9. Reconsider the architecture if the workload is analytical, large, and repeatedly executed against an OLTP database.

## Navigation

### Value Functions

- [Previous and Next Row Analysis](../04-%20Value%20Functions/06-%20Previous%20and%20Next%20Row%20Analysis.md)
- [Change Detection](../04-%20Value%20Functions/07-%20Change%20Detection.md)
- [Gap Analysis](../04-%20Value%20Functions/08-%20Gap%20Analysis.md)
- [LAG vs LEAD](../04-%20Value%20Functions/09-%20LAG%20vs%20LEAD.md)
- [Value Function Selection Rules](../04-%20Value%20Functions/10-%20Value%20Function%20Selection%20Rules.md)
- [Practical Value Function Patterns](../04-%20Value%20Functions/11-%20Practical%20Value%20Function%20Patterns.md)
- [Common Value Function Mistakes](../04-%20Value%20Functions/12-%20Common%20Value%20Function%20Mistakes.md)

## Key Takeaways

- **Choose SQL constructs based on result shape and semantics before choosing syntax.**
- **Use window functions when row-relative context, ranking, ordering, or row-preserving analytics are genuinely required.**
- **Prefer simpler constructs such as `GROUP BY`, `JOIN`, `EXISTS`, `DISTINCT`, and `LIMIT` when they directly solve the requirement.**
- **Treat partition size, ordering, memory, and execution plans as production concerns for large window queries.**
- **For repeated large-scale analytics, consider precomputation or workload separation instead of continuously querying an OLTP database.**