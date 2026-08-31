# 09- LAG vs LEAD

## Overview

`LAG()` and `LEAD()` are SQL value window functions used to access a value from another row within an ordered window without collapsing rows.

- `LAG()` looks **backward** to a preceding row.
- `LEAD()` looks **forward** to a following row.

They are fundamental for sequential analysis such as:

- Comparing the current value with the previous or next value
- Calculating time gaps
- Detecting state changes
- Measuring growth or decline
- Identifying missing events
- Sessionization
- Analyzing workflow transitions
- Building historical and forecasting-oriented reports

The key requirement is a well-defined sequence:

```sql
LAG(value)  OVER (PARTITION BY ... ORDER BY ...)
LEAD(value) OVER (PARTITION BY ... ORDER BY ...)
```

The `ORDER BY` determines what "previous" and "next" mean. `PARTITION BY` determines which rows belong to the same independent sequence.

## Core Difference

Consider:

| position | event | value |
|---:|---|---:|
| 1 | A | 100 |
| 2 | B | 120 |
| 3 | C | 110 |
| 4 | D | 140 |

Using:

```sql
LAG(value) OVER (ORDER BY position)
```

produces:

| event | value | previous_value |
|---|---:|---:|
| A | 100 | `NULL` |
| B | 120 | 100 |
| C | 110 | 120 |
| D | 140 | 110 |

Using:

```sql
LEAD(value) OVER (ORDER BY position)
```

produces:

| event | value | next_value |
|---|---:|---:|
| A | 100 | 120 |
| B | 120 | 110 |
| C | 110 | 140 |
| D | 140 | `NULL` |

The first row has no previous row, while the last row has no next row.

## Syntax

### `LAG()`

```sql
LAG(expression [, offset [, default_value]])
OVER (
    [PARTITION BY partition_expression]
    ORDER BY sort_expression
)
```

### `LEAD()`

```sql
LEAD(expression [, offset [, default_value]])
OVER (
    [PARTITION BY partition_expression]
    ORDER BY sort_expression
)
```

The common forms are:

```sql
LAG(amount) OVER (
    PARTITION BY customer_id
    ORDER BY transaction_date, transaction_id
)
```

and:

```sql
LEAD(amount) OVER (
    PARTITION BY customer_id
    ORDER BY transaction_date, transaction_id
)
```

## How They Work

Window functions operate on the rows produced by the query and preserve the row-level result.

For an ordered sequence:

```text
Row 1 → Row 2 → Row 3 → Row 4

LAG:
Row 1 ← Row 2 ← Row 3 ← Row 4

LEAD:
Row 1 → Row 2 → Row 3 → Row 4
```

More precisely:

```text
             LAG
              │
              ▼
Current ← Previous

Current → Next
              ▲
              │
             LEAD
```

For each row, the database evaluates the window ordering and retrieves a value at the requested offset.

The exact physical execution strategy is database-specific, but sorting or otherwise establishing the requested window order is often an important part of the execution cost.

## Basic Example

Given:

```sql
CREATE TABLE daily_sales (
    sale_date DATE PRIMARY KEY,
    revenue NUMERIC(12, 2) NOT NULL
);
```

Calculate the previous day's revenue:

```sql
SELECT
    sale_date,
    revenue,
    LAG(revenue) OVER (
        ORDER BY sale_date
    ) AS previous_revenue
FROM daily_sales
ORDER BY sale_date;
```

Calculate the next day's revenue:

```sql
SELECT
    sale_date,
    revenue,
    LEAD(revenue) OVER (
        ORDER BY sale_date
    ) AS next_revenue
FROM daily_sales
ORDER BY sale_date;
```

Neither function requires a self-join merely to access the adjacent row.

## Comparing Current and Previous Values

`LAG()` is the natural choice for change detection.

```sql
WITH sales AS (
    SELECT
        sale_date,
        revenue,
        LAG(revenue) OVER (
            ORDER BY sale_date
        ) AS previous_revenue
    FROM daily_sales
)
SELECT
    sale_date,
    revenue,
    previous_revenue,
    revenue - previous_revenue AS revenue_change
FROM sales
ORDER BY sale_date;
```

For percentage change:

```sql
WITH sales AS (
    SELECT
        sale_date,
        revenue,
        LAG(revenue) OVER (
            ORDER BY sale_date
        ) AS previous_revenue
    FROM daily_sales
)
SELECT
    sale_date,
    revenue,
    previous_revenue,
    CASE
        WHEN previous_revenue IS NULL OR previous_revenue = 0 THEN NULL
        ELSE (revenue - previous_revenue) / previous_revenue * 100
    END AS percentage_change
FROM sales
ORDER BY sale_date;
```

The explicit zero check prevents division-by-zero errors.

## Comparing Current and Next Values

`LEAD()` is useful when the question is forward-looking relative to the current row.

```sql
WITH sales AS (
    SELECT
        sale_date,
        revenue,
        LEAD(revenue) OVER (
            ORDER BY sale_date
        ) AS next_revenue
    FROM daily_sales
)
SELECT
    sale_date,
    revenue,
    next_revenue,
    next_revenue - revenue AS future_change
FROM sales
ORDER BY sale_date;
```

This is useful for questions such as:

> How does the current state compare with the next recorded state?

## `PARTITION BY` and Independent Sequences

In backend systems, sequential data is usually scoped to an entity.

For example:

```text
Customer A:
10:00 → 10:10 → 10:30

Customer B:
09:00 → 09:20 → 09:25
```

Use:

```sql
LAG(occurred_at) OVER (
    PARTITION BY customer_id
    ORDER BY occurred_at, event_id
)
```

rather than:

```sql
LAG(occurred_at) OVER (
    ORDER BY occurred_at
)
```

Without partitioning, the query can compare rows belonging to different customers.

The same applies to:

- `user_id`
- `order_id`
- `device_id`
- `account_id`
- `service_id`
- `tenant_id`

## Deterministic Ordering

The window ordering should be deterministic whenever possible.

Avoid:

```sql
ORDER BY occurred_at
```

if timestamps can collide.

Prefer:

```sql
ORDER BY occurred_at, event_id
```

For example:

| event_id | occurred_at |
|---:|---|
| 101 | 10:00:00 |
| 102 | 10:00:00 |
| 103 | 10:05:00 |

The timestamp alone does not establish the ordering between events 101 and 102.

A stable unique tie-breaker makes the sequence explicit.

This is especially important in distributed systems, where multiple events can legitimately have identical timestamps.

## Offset

The second argument specifies how many rows away to look.

### Previous Row

```sql
LAG(value, 1) OVER (
    ORDER BY sequence_id
)
```

### Two Rows Back

```sql
LAG(value, 2) OVER (
    ORDER BY sequence_id
)
```

### Next Row

```sql
LEAD(value, 1) OVER (
    ORDER BY sequence_id
)
```

### Two Rows Ahead

```sql
LEAD(value, 2) OVER (
    ORDER BY sequence_id
)
```

For example:

```sql
SELECT
    sale_date,
    revenue,
    LAG(revenue, 7) OVER (
        ORDER BY sale_date
    ) AS revenue_seven_rows_ago
FROM daily_sales;
```

Be careful with terminology: seven rows ago is not necessarily seven calendar days ago if dates are missing.

## Default Values

Both functions support a default value when the requested row does not exist.

```sql
SELECT
    sale_date,
    revenue,
    LAG(revenue, 1, 0) OVER (
        ORDER BY sale_date
    ) AS previous_revenue
FROM daily_sales;
```

The first row receives `0` instead of `NULL`.

However, replacing `NULL` with zero changes the semantics.

There is a meaningful difference between:

```text
No previous observation exists
```

and:

```text
Previous observation exists and its value is zero
```

For analytical queries, retaining `NULL` is often safer unless zero is explicitly the business meaning.

## Time-Series Gap Analysis

`LAG()` is commonly used to calculate elapsed time between events.

```sql
WITH ordered_events AS (
    SELECT
        user_id,
        event_id,
        occurred_at,
        LAG(occurred_at) OVER (
            PARTITION BY user_id
            ORDER BY occurred_at, event_id
        ) AS previous_occurred_at
    FROM user_events
)
SELECT
    user_id,
    event_id,
    occurred_at,
    previous_occurred_at,
    occurred_at - previous_occurred_at AS gap
FROM ordered_events;
```

The equivalent forward-looking analysis uses `LEAD()`:

```sql
WITH ordered_events AS (
    SELECT
        user_id,
        event_id,
        occurred_at,
        LEAD(occurred_at) OVER (
            PARTITION BY user_id
            ORDER BY occurred_at, event_id
        ) AS next_occurred_at
    FROM user_events
)
SELECT
    user_id,
    event_id,
    occurred_at,
    next_occurred_at,
    next_occurred_at - occurred_at AS upcoming_gap
FROM ordered_events;
```

Use `LAG()` when the requirement is naturally phrased as "since the previous event" and `LEAD()` when it is "until the next event."

## State Transition Analysis

Suppose an order has:

```text
pending → paid → packed → shipped → delivered
```

Use `LAG()` to identify the preceding state:

```sql
SELECT
    order_id,
    status,
    changed_at,
    LAG(status) OVER (
        PARTITION BY order_id
        ORDER BY changed_at, history_id
    ) AS previous_status
FROM order_status_history;
```

Use `LEAD()` to identify the upcoming state:

```sql
SELECT
    order_id,
    status,
    changed_at,
    LEAD(status) OVER (
        PARTITION BY order_id
        ORDER BY changed_at, history_id
    ) AS next_status
FROM order_status_history;
```

This enables transition analysis without manually joining each row to its neighbor.

## Sessionization

`LAG()` is particularly useful for determining whether a new session begins.

Suppose a user starts a new session after 30 minutes of inactivity:

```sql
WITH events AS (
    SELECT
        user_id,
        event_id,
        occurred_at,
        LAG(occurred_at) OVER (
            PARTITION BY user_id
            ORDER BY occurred_at, event_id
        ) AS previous_occurred_at
    FROM user_events
)
SELECT
    *,
    CASE
        WHEN previous_occurred_at IS NULL THEN 1
        WHEN occurred_at - previous_occurred_at > INTERVAL '30 minutes'
            THEN 1
        ELSE 0
    END AS new_session
FROM events;
```

A cumulative window can then turn those markers into session IDs:

```sql
WITH events AS (
    SELECT
        user_id,
        event_id,
        occurred_at,
        LAG(occurred_at) OVER (
            PARTITION BY user_id
            ORDER BY occurred_at, event_id
        ) AS previous_occurred_at
    FROM user_events
),
marked AS (
    SELECT
        *,
        CASE
            WHEN previous_occurred_at IS NULL THEN 1
            WHEN occurred_at - previous_occurred_at > INTERVAL '30 minutes'
                THEN 1
            ELSE 0
        END AS new_session
    FROM events
)
SELECT
    *,
    SUM(new_session) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, event_id
        ROWS UNBOUNDED PRECEDING
    ) AS session_id
FROM marked;
```

## Detecting State Changes

A common pattern is comparing the current state to the previous state.

```sql
WITH states AS (
    SELECT
        entity_id,
        changed_at,
        status,
        LAG(status) OVER (
            PARTITION BY entity_id
            ORDER BY changed_at, history_id
        ) AS previous_status
    FROM entity_status_history
)
SELECT
    entity_id,
    changed_at,
    previous_status,
    status
FROM states
WHERE previous_status IS DISTINCT FROM status;
```

In PostgreSQL, `IS DISTINCT FROM` provides null-safe comparison.

This can be preferable to:

```sql
WHERE previous_status <> status
```

because ordinary inequality with `NULL` produces an unknown result rather than `TRUE`.

## Finding the Next Business Event

`LEAD()` is useful when the next row represents a future workflow step.

```sql
SELECT
    order_id,
    status,
    changed_at,
    LEAD(status) OVER (
        PARTITION BY order_id
        ORDER BY changed_at, history_id
    ) AS next_status
FROM order_status_history;
```

You can then calculate transition duration:

```sql
WITH transitions AS (
    SELECT
        order_id,
        status,
        changed_at,
        LEAD(status) OVER (
            PARTITION BY order_id
            ORDER BY changed_at, history_id
        ) AS next_status,
        LEAD(changed_at) OVER (
            PARTITION BY order_id
            ORDER BY changed_at, history_id
        ) AS next_changed_at
    FROM order_status_history
)
SELECT
    order_id,
    status,
    next_status,
    next_changed_at - changed_at AS transition_duration
FROM transitions
WHERE next_status IS NOT NULL;
```

This is often convenient for workflow SLA analysis.

## Finding Increases and Decreases

`LAG()` can classify directional changes:

```sql
WITH metrics AS (
    SELECT
        recorded_at,
        value,
        LAG(value) OVER (
            ORDER BY recorded_at
        ) AS previous_value
    FROM service_metrics
)
SELECT
    recorded_at,
    value,
    previous_value,
    CASE
        WHEN previous_value IS NULL THEN 'initial'
        WHEN value > previous_value THEN 'increase'
        WHEN value < previous_value THEN 'decrease'
        ELSE 'unchanged'
    END AS direction
FROM metrics;
```

This pattern is useful for:

- Revenue trends
- Inventory levels
- Queue depth
- Error counts
- CPU metrics
- Account balances

## Finding the Next Higher or Lower Value

`LEAD()` only retrieves the next row according to the ordering. It does **not** search for the next row satisfying a condition.

For example:

```sql
LEAD(price) OVER (
    ORDER BY recorded_at
)
```

means:

> Give me the price in the next ordered row.

It does not mean:

> Find the next price greater than the current price.

That distinction is a common interview trap.

Conditional "next matching row" requirements may need:

- A different window strategy
- A self-join
- A lateral query
- Database-specific features
- Recursive SQL
- Precomputed data

## LAG vs LEAD

| Characteristic | `LAG()` | `LEAD()` |
|---|---|---|
| Direction | Previous row | Next row |
| Default offset | 1 | 1 |
| Common question | "What happened before?" | "What happens next?" |
| Gap analysis | Current minus previous | Next minus current |
| State analysis | Previous state | Next state |
| Change detection | Very common | Useful for forward comparison |
| Sessionization | Common | Less common |
| Workflow transition duration | Useful | Often convenient |
| First/last boundary | First row has no previous | Last row has no next |

## Choosing Between `LAG()` and `LEAD()`

The choice should follow the question rather than the implementation preference.

| Requirement | Preferred function |
|---|---|
| Compare current value to previous value | `LAG()` |
| Calculate time since previous event | `LAG()` |
| Detect a new session | `LAG()` |
| Identify previous status | `LAG()` |
| Compare current value to next value | `LEAD()` |
| Calculate time until next event | `LEAD()` |
| Identify next workflow state | `LEAD()` |
| Calculate duration until the next transition | `LEAD()` |
| Analyze both directions | Use both |

Using both in one query is completely valid:

```sql
SELECT
    event_id,
    occurred_at,
    LAG(occurred_at) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, event_id
    ) AS previous_occurred_at,
    LEAD(occurred_at) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, event_id
    ) AS next_occurred_at
FROM user_events;
```

## Combining `LAG()` and `LEAD()`

A three-point comparison can analyze the current observation against both neighbors:

```sql
SELECT
    recorded_at,
    value,
    LAG(value) OVER (
        ORDER BY recorded_at
    ) AS previous_value,
    value AS current_value,
    LEAD(value) OVER (
        ORDER BY recorded_at
    ) AS next_value
FROM measurements;
```

This is useful for:

- Local trend analysis
- Detecting peaks
- Detecting valleys
- Comparing before/after states
- Identifying local anomalies

For example, a simple local peak:

```sql
WITH neighbors AS (
    SELECT
        recorded_at,
        value,
        LAG(value) OVER (
            ORDER BY recorded_at
        ) AS previous_value,
        LEAD(value) OVER (
            ORDER BY recorded_at
        ) AS next_value
    FROM measurements
)
SELECT
    recorded_at,
    value
FROM neighbors
WHERE previous_value IS NOT NULL
  AND next_value IS NOT NULL
  AND value > previous_value
  AND value > next_value;
```

## Query Evaluation and Filtering

Window functions are evaluated after the `WHERE` clause of the same query block.

This can produce an important difference.

Suppose events exist at:

```text
10:00
10:10
10:20
11:00
```

If you filter first:

```sql
SELECT
    occurred_at,
    LAG(occurred_at) OVER (
        ORDER BY occurred_at
    ) AS previous_occurred_at
FROM user_events
WHERE occurred_at >= TIMESTAMP '2026-08-30 10:30:00';
```

the window sees only:

```text
11:00
```

If the requirement is to compare 11:00 against 10:20, calculate the window first:

```sql
WITH ordered_events AS (
    SELECT
        occurred_at,
        LAG(occurred_at) OVER (
            ORDER BY occurred_at
        ) AS previous_occurred_at
    FROM user_events
)
SELECT
    occurred_at,
    previous_occurred_at,
    occurred_at - previous_occurred_at AS gap
FROM ordered_events
WHERE occurred_at >= TIMESTAMP '2026-08-30 10:30:00';
```

This is a frequent source of incorrect analytics.

## Row Offset Is Not Time Offset

Consider:

```text
Monday
Wednesday
Thursday
```

Then:

```sql
LAG(value, 1)
```

on Thursday returns Wednesday's value.

It does not return Tuesday's value or the value from exactly 24 hours earlier.

Likewise:

```sql
LEAD(value, 1)
```

means the next row in the ordered result, not the next calendar day.

For calendar-aware analysis, consider:

- Date series generation
- Calendar tables
- Time buckets
- Explicit timestamp predicates
- Time-series-specific database features

## Performance Considerations

`LAG()` and `LEAD()` require the database to establish the window ordering.

For a large event table:

```sql
PARTITION BY user_id
ORDER BY occurred_at, event_id
```

an aligned index may help other parts of the query and can sometimes reduce sorting work:

```sql
CREATE INDEX idx_user_events_user_time_id
ON user_events (user_id, occurred_at, event_id);
```

Validate the actual query plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    user_id,
    occurred_at,
    LAG(occurred_at) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, event_id
    ) AS previous_occurred_at
FROM user_events;
```

Do not assume an index guarantees an index-only or sort-free execution plan. The optimizer considers table size, selectivity, statistics, available memory, and the complete query.

For large analytical workloads:

- Filter as early as semantics allow.
- Avoid repeatedly scanning entire event histories.
- Use appropriate indexes.
- Partition very large tables where justified.
- Precompute frequently requested aggregates.
- Move heavy analytical workloads away from latency-sensitive transactional databases when appropriate.

## Production Backend Example

A Django or FastAPI application may expose an endpoint such as:

```text
GET /users/{id}/activity
```

The endpoint may need to return:

```json
{
  "events": [
    {
      "event": "login",
      "occurred_at": "2026-08-30T09:00:00Z",
      "previous_occurred_at": null,
      "gap_seconds": null
    },
    {
      "event": "purchase",
      "occurred_at": "2026-08-30T09:12:00Z",
      "previous_occurred_at": "2026-08-30T09:00:00Z",
      "gap_seconds": 720
    }
  ]
}
```

The application does not need to load all events into Python and manually compare adjacent rows.

The database can perform the ordered comparison:

```sql
SELECT
    event_id,
    event_type,
    occurred_at,
    LAG(occurred_at) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, event_id
    ) AS previous_occurred_at
FROM user_events
WHERE user_id = $1
ORDER BY occurred_at, event_id;
```

This keeps set-oriented processing inside PostgreSQL and reduces application-side data manipulation.

For a high-traffic endpoint, however, avoid assuming that a complex historical window query is always appropriate synchronously. If the same analysis is requested repeatedly, consider caching, precomputation, or a read-optimized analytical path.

## Security and Multi-Tenant Systems

When analyzing tenant-scoped data, partitioning and filtering must respect tenant boundaries.

Prefer:

```sql
LAG(value) OVER (
    PARTITION BY tenant_id, account_id
    ORDER BY occurred_at, event_id
)
```

and ensure the input rows are constrained to authorized tenants.

A window function does not provide authorization.

In Django or FastAPI:

- Apply tenant/resource authorization before returning results.
- Use parameterized queries.
- Avoid constructing SQL with user-controlled identifiers or values.
- Do not expose events from another tenant through an analytical endpoint.

## Common Mistakes

| Mistake | Why it happens | Correct approach |
|---|---|---|
| Using `LAG()` without `ORDER BY` | Treating window functions like ordinary functions | Define the sequence explicitly |
| Omitting `PARTITION BY` | Forgetting that data contains multiple entities | Partition by the sequence owner |
| Ordering only by a timestamp | Assuming timestamps are unique | Add a stable tie-breaker |
| Treating `LAG(1)` as one time unit | Confusing rows with time | Use explicit temporal logic |
| Replacing missing rows with zero automatically | Losing the distinction between missing and zero | Preserve `NULL` unless zero is intentional |
| Filtering before the window calculation | Accidentally removing historical context | Calculate the window in a CTE/subquery when needed |
| Assuming `LEAD()` finds the next matching row | Misunderstanding row offset semantics | Use a condition-aware strategy |
| Comparing nullable values with `<>` | SQL three-valued logic | Use `IS DISTINCT FROM` where appropriate |
| Calculating everything in Python | Moving sequential processing unnecessarily into the application | Let SQL perform set-based window analysis |
| Running huge window queries on request paths | Ignoring analytical query cost | Precompute, cache, or use a read-optimized system |

## Interview Traps

### What is the main difference between `LAG()` and `LEAD()`?

`LAG()` accesses a preceding row in the window ordering. `LEAD()` accesses a following row.

### Does `LAG()` require `PARTITION BY`?

No. It is optional.

But if the data contains independent entity sequences, omitting it can produce incorrect comparisons across entities.

### What determines the previous row?

The window's `ORDER BY`.

For example:

```sql
LAG(value) OVER (
    PARTITION BY user_id
    ORDER BY occurred_at, event_id
)
```

The previous row is the preceding row according to `occurred_at, event_id` within that user's partition.

### What happens at the boundary?

By default:

- `LAG()` returns `NULL` when there is no preceding row.
- `LEAD()` returns `NULL` when there is no following row.

A default can be supplied explicitly.

### Can `LAG()` and `LEAD()` be used together?

Yes.

They are often combined to compare the current row with both neighboring observations.

### Why not use a self-join?

A self-join can solve adjacent-row problems, but window functions express ordered-row relationships directly and are generally clearer for this class of query.

Self-joins can still be appropriate when the relationship is not simply a fixed row offset or requires complex matching conditions.

### Does `LEAD()` look at future time?

Only relative to the ordering supplied to the window.

It does not understand "future" independently of the `ORDER BY`.

## Production Checklist

Before deploying a query using `LAG()` or `LEAD()`, verify:

- The ordering represents the actual business sequence.
- The ordering is deterministic.
- The correct entity is used in `PARTITION BY`.
- `NULL` at sequence boundaries is handled intentionally.
- Missing observations are not confused with zero values.
- Row offsets are not confused with temporal intervals.
- Filtering occurs at the correct stage.
- Duplicate events have defined semantics.
- Timestamp and timezone behavior is correct.
- The query plan has been evaluated for large datasets.
- Tenant boundaries and authorization rules are enforced.
- Heavy analytical work is not placed unnecessarily on latency-sensitive API paths.

## Key Takeaways

- **`LAG()` looks backward and `LEAD()` looks forward; both access rows relative to a deterministic window ordering.**
- **`PARTITION BY` defines independent sequences, while `ORDER BY` defines what previous and next mean.**
- **Use these functions for change detection, state transitions, time gaps, sessionization, and sequential analytics without application-side row processing.**
- **A row offset is not a time interval, and filtering before a window calculation can remove the historical context required for correct results.**
- **For production workloads, prioritize deterministic ordering, correct null semantics, tenant isolation, and query-plan validation.**