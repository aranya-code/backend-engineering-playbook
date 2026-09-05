# 09- LAG vs LEAD

## Overview

`LAG()` and `LEAD()` are SQL window functions used to access values from another row relative to the current row without joining the table to itself.

- `LAG()` looks backward to a preceding row.
- `LEAD()` looks forward to a following row.

They are especially useful for comparing events over time:

- Detecting status changes.
- Calculating period-over-period differences.
- Measuring time between events.
- Detecting gaps in activity.
- Comparing current and previous prices.
- Finding the next event in an entity's lifecycle.
- Building audit and event-history analysis.
- Calculating customer or service state transitions.

The key distinction is:

```text
LAG(current row)
    ↓
previous row

current row
    ↓
LEAD(current row)
    ↓
next row
```

Unlike a traditional self-join, the database can express the relative-row relationship directly through a window definition.

---

## Window Function Context

A window function calculates across a set of related rows while preserving the original row grain.

For example:

```sql
SELECT
    customer_id,
    created_at,
    status,
    LAG(status) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_status
FROM customer_status_history;
```

Each status-history row remains in the result, while `previous_status` contains the value from the preceding row for that customer.

This is different from `GROUP BY`, which collapses multiple rows into groups.

---

## LAG

`LAG()` returns a value from a preceding row in the window ordering.

Basic syntax:

```sql
LAG(value_expression [, offset] [, default])
OVER (
    [PARTITION BY ...]
    ORDER BY ...
)
```

Example:

```sql
SELECT
    id,
    customer_id,
    created_at,
    total_amount,
    LAG(total_amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_amount
FROM orders;
```

For each order, `previous_amount` contains the previous order amount for the same customer.

---

## Why LAG Exists

Without `LAG()`, comparing a row with its previous row often requires:

- Self-joins.
- Correlated subqueries.
- Application-side processing.
- Temporary intermediate state.

`LAG()` expresses the relationship directly:

```text
Current row
    |
    +── previous row → LAG()
```

This makes temporal and sequential comparisons substantially easier to express.

---

## Basic LAG Example

Given:

```text
date        revenue
----------  -------
2026-01-01  1000
2026-01-02  1200
2026-01-03  900
2026-01-04  1500
```

Query:

```sql
SELECT
    date,
    revenue,
    LAG(revenue) OVER (
        ORDER BY date
    ) AS previous_revenue
FROM daily_revenue;
```

Result:

```text
date        revenue  previous_revenue
----------  -------  ----------------
2026-01-01  1000     NULL
2026-01-02  1200     1000
2026-01-03  900      1200
2026-01-04  1500     900
```

The first row has no preceding row, so the result is `NULL` by default.

---

## LEAD

`LEAD()` returns a value from a following row in the window ordering.

Basic syntax:

```sql
LEAD(value_expression [, offset] [, default])
OVER (
    [PARTITION BY ...]
    ORDER BY ...
)
```

Example:

```sql
SELECT
    id,
    customer_id,
    created_at,
    status,
    LEAD(status) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS next_status
FROM customer_status_history;
```

Each row can now see the next status for the same customer.

---

## Basic LEAD Example

```sql
SELECT
    date,
    revenue,
    LEAD(revenue) OVER (
        ORDER BY date
    ) AS next_revenue
FROM daily_revenue;
```

Result:

```text
date        revenue  next_revenue
----------  -------  ------------
2026-01-01  1000     1200
2026-01-02  1200     900
2026-01-03  900      1500
2026-01-04  1500     NULL
```

The final row has no following row, so `LEAD()` returns `NULL`.

---

## LAG vs LEAD

| Function | Direction | Typical question |
|---|---|---|
| `LAG()` | Previous row | What happened before this row? |
| `LEAD()` | Next row | What happens after this row? |

Mental model:

```text
        LAG()
          ↓
Previous ← Current → Next
                    ↑
                  LEAD()
```

---

## Offset

The optional offset determines how many rows away to look.

For example:

```sql
LAG(revenue, 2) OVER (
    ORDER BY date
)
```

looks two rows backward.

Similarly:

```sql
LEAD(revenue, 2) OVER (
    ORDER BY date
)
```

looks two rows forward.

Example:

```sql
SELECT
    date,
    revenue,
    LAG(revenue, 7) OVER (
        ORDER BY date
    ) AS revenue_previous_week
FROM daily_revenue;
```

This can be useful for period comparisons when the dataset contains one row per day.

The offset is a row offset, not automatically a calendar interval.

That distinction is important when dates are missing.

---

## Default Value

The third argument provides a value when the requested row does not exist.

```sql
LAG(revenue, 1, 0) OVER (
    ORDER BY date
)
```

The first row receives `0` instead of `NULL`.

Likewise:

```sql
LEAD(revenue, 1, 0) OVER (
    ORDER BY date
)
```

can provide `0` when there is no following row.

Use defaults carefully.

A missing previous row and an actual previous value of `0` are semantically different states.

For analytics, preserving `NULL` can often be more correct than converting it to zero.

---

## PARTITION BY

`PARTITION BY` creates independent sequences.

For customer events:

```sql
SELECT
    customer_id,
    created_at,
    status,
    LAG(status) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_status
FROM customer_status_history;
```

The database never compares a row from customer `1` with a row from customer `2`.

Conceptually:

```text
Customer 1:
event A → event B → event C

Customer 2:
event X → event Y → event Z
```

Each customer has its own window.

---

## Ordering Is Critical

`LAG()` and `LEAD()` only have meaning relative to an ordering.

This is incomplete:

```sql
LAG(status) OVER (
    PARTITION BY customer_id
)
```

The database needs to know what "previous" means.

Prefer:

```sql
LAG(status) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, id
)
```

The ordering should represent the business sequence.

For event data, this might be:

```sql
ORDER BY occurred_at, id
```

For version history:

```sql
ORDER BY version
```

For financial periods:

```sql
ORDER BY period_start
```

---

## Deterministic Ordering

Ordering only by a timestamp can be insufficient:

```sql
ORDER BY created_at
```

Two rows may have the same timestamp.

Add a stable tie-breaker:

```sql
ORDER BY created_at, id
```

This makes the sequence deterministic.

This is especially important for:

- Audit logs.
- State transitions.
- Payment events.
- Event processing.
- Data exports.
- Reproducible ETL.
- Debugging production incidents.

A senior engineer should always ask:

> What makes the ordering deterministic?

---

## Comparing Current and Previous Values

A common `LAG()` pattern is calculating a difference.

```sql
SELECT
    date,
    revenue,
    LAG(revenue) OVER (
        ORDER BY date
    ) AS previous_revenue,
    revenue - LAG(revenue) OVER (
        ORDER BY date
    ) AS revenue_change
FROM daily_revenue;
```

Result:

```text
date        revenue  previous_revenue  revenue_change
----------  -------  ----------------  --------------
2026-01-01  1000     NULL              NULL
2026-01-02  1200     1000              200
2026-01-03  900      1200              -300
2026-01-04  1500     900               600
```

This can be extended to percentage change:

```sql
SELECT
    date,
    revenue,
    previous_revenue,
    CASE
        WHEN previous_revenue IS NULL
             OR previous_revenue = 0
        THEN NULL
        ELSE (revenue - previous_revenue) / previous_revenue
    END AS revenue_change_ratio
FROM (
    SELECT
        date,
        revenue,
        LAG(revenue) OVER (
            ORDER BY date
        ) AS previous_revenue
    FROM daily_revenue
) AS x;
```

Avoid dividing by zero and define how the first row should behave.

---

## Detecting State Changes

Suppose a customer status history contains:

```text
customer_id | status
------------+--------
1           | trial
1           | active
1           | active
1           | suspended
1           | active
```

Use `LAG()` to detect transitions:

```sql
SELECT
    customer_id,
    created_at,
    status,
    LAG(status) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_status
FROM customer_status_history;
```

Then:

```sql
SELECT *
FROM (
    SELECT
        customer_id,
        created_at,
        status,
        LAG(status) OVER (
            PARTITION BY customer_id
            ORDER BY created_at, id
        ) AS previous_status
    FROM customer_status_history
) AS history
WHERE previous_status IS DISTINCT FROM status;
```

`IS DISTINCT FROM` is useful when NULL values are possible because it provides NULL-safe comparison semantics.

---

## Detecting First Occurrences

A `LAG()` result of `NULL` can identify the first row in a partition when the underlying value itself is known to be non-NULL.

For example:

```sql
SELECT
    customer_id,
    created_at,
    event_type,
    LAG(id) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, id
    ) AS previous_event_id
FROM customer_events;
```

A `NULL` `previous_event_id` indicates there is no earlier row.

This is often clearer than inferring the first row from timestamps.

---

## Measuring Time Between Events

`LAG()` is particularly useful for event streams stored in PostgreSQL.

```sql
SELECT
    customer_id,
    occurred_at,
    LAG(occurred_at) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, id
    ) AS previous_occurred_at
FROM customer_events;
```

You can calculate the interval:

```sql
SELECT
    customer_id,
    occurred_at,
    occurred_at - previous_occurred_at AS time_since_previous
FROM (
    SELECT
        customer_id,
        occurred_at,
        LAG(occurred_at) OVER (
            PARTITION BY customer_id
            ORDER BY occurred_at, id
        ) AS previous_occurred_at
    FROM customer_events
) AS events;
```

This can support:

- Customer engagement analysis.
- Sessionization.
- Event latency analysis.
- Operational monitoring.
- SLA analysis.

---

## Detecting Gaps

Suppose events should normally occur within a given interval.

```sql
SELECT
    customer_id,
    occurred_at,
    occurred_at - previous_occurred_at AS gap
FROM (
    SELECT
        customer_id,
        occurred_at,
        LAG(occurred_at) OVER (
            PARTITION BY customer_id
            ORDER BY occurred_at, id
        ) AS previous_occurred_at
    FROM service_events
) AS events
WHERE occurred_at - previous_occurred_at > interval '1 hour';
```

This can identify periods of inactivity.

Be careful not to confuse a missing row with an actual business outage. Data ingestion failures can create apparent gaps.

---

## Finding the Next Event With LEAD

`LEAD()` is useful when the current row needs to know what happens next.

For example:

```sql
SELECT
    customer_id,
    status,
    changed_at,
    LEAD(changed_at) OVER (
        PARTITION BY customer_id
        ORDER BY changed_at, id
    ) AS next_changed_at
FROM customer_status_history;
```

The next timestamp can be used to determine how long a customer remained in the current state.

---

## Calculating State Duration

```sql
SELECT
    customer_id,
    status,
    changed_at,
    next_changed_at,
    next_changed_at - changed_at AS duration
FROM (
    SELECT
        customer_id,
        status,
        changed_at,
        LEAD(changed_at) OVER (
            PARTITION BY customer_id
            ORDER BY changed_at, id
        ) AS next_changed_at
    FROM customer_status_history
) AS states;
```

The final state has no next event and therefore has a `NULL` duration.

That may be the correct representation because the state is still active.

Do not automatically replace it with zero.

---

## Sessionization Pattern

`LAG()` can help identify new sessions.

Suppose events should belong to the same session when consecutive events are no more than 30 minutes apart.

First calculate the previous event:

```sql
SELECT
    user_id,
    occurred_at,
    LAG(occurred_at) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, id
    ) AS previous_occurred_at
FROM user_events;
```

Then mark session boundaries:

```sql
SELECT
    user_id,
    occurred_at,
    CASE
        WHEN previous_occurred_at IS NULL
          OR occurred_at - previous_occurred_at > interval '30 minutes'
        THEN 1
        ELSE 0
    END AS new_session
FROM (
    SELECT
        user_id,
        occurred_at,
        LAG(occurred_at) OVER (
            PARTITION BY user_id
            ORDER BY occurred_at, id
        ) AS previous_occurred_at
    FROM user_events
) AS events;
```

A cumulative `SUM()` window can then turn these boundaries into session IDs.

```sql
SELECT
    user_id,
    occurred_at,
    SUM(new_session) OVER (
        PARTITION BY user_id
        ORDER BY occurred_at, id
        ROWS UNBOUNDED PRECEDING
    ) AS session_number
FROM (
    SELECT
        user_id,
        occurred_at,
        id,
        CASE
            WHEN LAG(occurred_at) OVER (
                PARTITION BY user_id
                ORDER BY occurred_at, id
            ) IS NULL
            OR occurred_at - LAG(occurred_at) OVER (
                PARTITION BY user_id
                ORDER BY occurred_at, id
            ) > interval '30 minutes'
            THEN 1
            ELSE 0
        END AS new_session
    FROM user_events
) AS events;
```

For readability and maintainability, production SQL may instead calculate the `LAG()` result once in an intermediate CTE and then use it in later stages.

---

## LAG/LEAD vs Self-Join

Before window functions, a previous-row comparison might be implemented with a self-join.

Conceptually:

```sql
SELECT
    current_event.id,
    current_event.occurred_at,
    previous_event.occurred_at
FROM events AS current_event
LEFT JOIN events AS previous_event
    ON previous_event.user_id = current_event.user_id
   AND previous_event.occurred_at = (
       SELECT MAX(e2.occurred_at)
       FROM events AS e2
       WHERE e2.user_id = current_event.user_id
         AND e2.occurred_at < current_event.occurred_at
   );
```

This is significantly more complicated than:

```sql
LAG(occurred_at) OVER (
    PARTITION BY user_id
    ORDER BY occurred_at, id
)
```

Window functions communicate the intent directly.

A self-join can still be appropriate when the relationship is not simply positional or when the business rule requires a different relational lookup.

---

## LAG/LEAD vs Correlated Subqueries

A correlated query can find a previous value, but often at greater complexity:

```sql
SELECT
    e.id,
    e.occurred_at,
    (
        SELECT MAX(previous.occurred_at)
        FROM events AS previous
        WHERE previous.user_id = e.user_id
          AND previous.occurred_at < e.occurred_at
    ) AS previous_occurred_at
FROM events AS e;
```

`LAG()` is generally the clearer abstraction when "previous according to this ordering" is exactly the requirement.

Do not assume it will always be faster. Validate the execution plan for production workloads.

---

## Combining LAG and LEAD

Sometimes a row needs both neighboring values:

```sql
SELECT
    id,
    occurred_at,
    LAG(occurred_at) OVER (
        ORDER BY occurred_at, id
    ) AS previous_event_at,
    LEAD(occurred_at) OVER (
        ORDER BY occurred_at, id
    ) AS next_event_at
FROM events;
```

This produces:

```text
previous event
      ↓
current event
      ↓
next event
```

This is useful for:

- Interval analysis.
- Event transitions.
- Timeline reconstruction.
- State-duration analysis.
- Detecting anomalies.

---

## Multiple LAG/LEAD Expressions

You can use different offsets:

```sql
SELECT
    date,
    revenue,
    LAG(revenue, 1) OVER (
        ORDER BY date
    ) AS previous_day,
    LAG(revenue, 7) OVER (
        ORDER BY date
    ) AS previous_week,
    LEAD(revenue, 1) OVER (
        ORDER BY date
    ) AS next_day
FROM daily_revenue;
```

This can support reporting dashboards without performing multiple application-side queries.

Remember that offsets refer to rows, so missing dates can make `LAG(revenue, 7)` different from "seven calendar days ago."

---

## Missing Dates and Time Series

Consider:

```text
2026-01-01
2026-01-02
2026-01-05
```

Then:

```sql
LAG(revenue, 1)
```

returns the previous available row.

For `2026-01-05`, that is `2026-01-02`, not necessarily "yesterday."

If the requirement is calendar-based comparison, consider generating a date series or joining against a calendar table.

For example:

```sql
SELECT
    date,
    revenue
FROM daily_revenue;
```

should not be assumed to contain every calendar date.

This distinction is a common source of incorrect analytics.

---

## Filtering on LAG or LEAD Results

Window-function results cannot generally be filtered directly in the same query block's `WHERE` clause.

Instead:

```sql
SELECT *
FROM (
    SELECT
        customer_id,
        occurred_at,
        occurred_at - LAG(occurred_at) OVER (
            PARTITION BY customer_id
            ORDER BY occurred_at, id
        ) AS gap
    FROM customer_events
) AS events
WHERE gap > interval '1 hour';
```

A CTE is another readable option:

```sql
WITH events AS (
    SELECT
        customer_id,
        occurred_at,
        occurred_at - LAG(occurred_at) OVER (
            PARTITION BY customer_id
            ORDER BY occurred_at, id
        ) AS gap
    FROM customer_events
)
SELECT *
FROM events
WHERE gap > interval '1 hour';
```

---

## Performance Considerations

`LAG()` and `LEAD()` require the database to establish the requested window ordering.

Performance is influenced by:

- Number of rows.
- Partition cardinality.
- Number of partitions.
- Ordering columns.
- Filtering selectivity.
- Indexes.
- Memory available for sorting.
- Number of window definitions.
- Concurrent database workload.

A large query such as:

```sql
SELECT
    *,
    LAG(value) OVER (
        PARTITION BY tenant_id
        ORDER BY occurred_at, id
    )
FROM massive_events;
```

can be expensive if it processes the entire table.

Filter rows first when doing so does not change the required semantics:

```sql
SELECT
    *,
    LAG(value) OVER (
        PARTITION BY tenant_id
        ORDER BY occurred_at, id
    ) AS previous_value
FROM massive_events
WHERE tenant_id = $1;
```

---

## Indexing Considerations

For queries frequently ordered by:

```sql
PARTITION BY customer_id
ORDER BY occurred_at, id
```

an index such as:

```sql
CREATE INDEX idx_events_customer_time_id
    ON customer_events (customer_id, occurred_at, id);
```

may help.

However:

- Indexes do not guarantee a sort-free execution plan.
- The optimizer may choose a sequential scan.
- Query selectivity matters.
- Indexes add storage and write overhead.
- Different query shapes may require different indexes.

Validate important queries with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT ...;
```

---

## Memory and Large Partitions

Window processing can require substantial memory, especially for large partitions and complex queries.

A tenant with millions of events can create a very different execution profile from a tenant with thousands.

Monitor:

- Query execution time.
- Temporary file generation.
- Disk-based sorts.
- Database memory pressure.
- CPU utilization.
- I/O.
- Concurrent window queries.

Do not solve a database memory problem simply by increasing `work_mem` globally.

`work_mem` applies to individual query operations, and a single query can perform multiple memory-consuming operations. High concurrency can therefore multiply memory consumption.

---

## PostgreSQL Execution Plans

For a production query:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    occurred_at,
    LAG(occurred_at) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, id
    ) AS previous_event
FROM customer_events
WHERE tenant_id = 42;
```

Look for:

- Rows entering the window operation.
- Sort operations.
- Sort method.
- Temporary disk usage.
- Buffer reads.
- Actual vs estimated rows.
- Overall execution time.

The goal is not to eliminate every sort.

The goal is to ensure the execution plan is appropriate for the workload.

---

## Backend API Integration

Suppose a FastAPI endpoint needs to expose customer event transitions:

```text
GET /customers/{customer_id}/events
```

Instead of retrieving all events and calculating previous timestamps in Python:

```python
events = load_events(customer_id)

for index, event in enumerate(events):
    event["previous_at"] = (
        events[index - 1]["occurred_at"]
        if index > 0
        else None
    )
```

the database can produce the relationship:

```sql
SELECT
    id,
    occurred_at,
    event_type,
    LAG(occurred_at) OVER (
        ORDER BY occurred_at, id
    ) AS previous_occurred_at
FROM customer_events
WHERE customer_id = $1
ORDER BY occurred_at, id;
```

This keeps relational processing in PostgreSQL and reduces application-side computation.

For very large datasets, however, do not return the entire event history through one API request. Apply appropriate filtering and pagination.

---

## Django ORM

Django supports window expressions.

Example:

```python
from django.db.models import F, Window
from django.db.models.functions import Lag

queryset = CustomerEvent.objects.annotate(
    previous_occurred_at=Window(
        expression=Lag("occurred_at"),
        partition_by=[F("customer_id")],
        order_by=[F("occurred_at").asc(), F("id").asc()],
    )
)
```

For `LEAD()`:

```python
from django.db.models.functions import Lead

queryset = CustomerEvent.objects.annotate(
    next_occurred_at=Window(
        expression=Lead("occurred_at"),
        partition_by=[F("customer_id")],
        order_by=[F("occurred_at").asc(), F("id").asc()],
    )
)
```

For production queries:

- Inspect generated SQL.
- Check database execution plans.
- Test realistic volumes.
- Confirm ORM-generated filtering occurs at the intended stage.

Do not assume ORM syntax hides the database performance characteristics.

---

## Kafka and Event Data

Kafka consumers frequently process event streams sequentially, but Kafka and SQL window ordering solve different problems.

Kafka ordering is generally scoped to a partition.

PostgreSQL window ordering is defined by:

```sql
PARTITION BY ...
ORDER BY ...
```

For example, if customer events are persisted in PostgreSQL:

```sql
LAG(status) OVER (
    PARTITION BY customer_id
    ORDER BY occurred_at, id
)
```

provides a database-level historical comparison.

Do not assume Kafka arrival order is equivalent to business event time.

Events can be delayed, retried, duplicated, or delivered with timestamps that differ from processing time.

For event analytics, define explicitly whether ordering means:

- Event occurrence time.
- Kafka offset.
- Ingestion time.
- Database insertion time.
- Business sequence number.

---

## Redis Considerations

Redis can be useful for serving precomputed rankings or recent state, but it should not automatically replace relational analysis.

For example:

```text
PostgreSQL
    ↓
Historical event analysis
    ↓
Computed result
    ↓
Redis
    ↓
Low-latency API
```

If `LAG()` or `LEAD()` is part of a batch calculation, PostgreSQL can perform the relational computation and Redis can serve the resulting read model.

This is particularly useful when:

- The query is expensive.
- The result changes periodically.
- Low API latency is required.
- Slightly stale data is acceptable.

The freshness contract must be explicit.

---

## Security and Multi-Tenancy

Window functions must operate within the correct authorization boundary.

For tenant-specific event history:

```sql
SELECT
    customer_id,
    occurred_at,
    event_type,
    LAG(event_type) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, id
    ) AS previous_event_type
FROM customer_events
WHERE tenant_id = $1;
```

Do not allow rows from another tenant to enter the window if the calculated relationship is supposed to be tenant-local.

If PostgreSQL Row Level Security is used, understand how the policy interacts with the query and database role.

Application authorization and database isolation should reinforce each other rather than relying on an accidental query shape.

---

## Reliability Considerations

Temporal calculations are only as reliable as the ordering data.

For production event histories:

- Use immutable event identifiers.
- Define event timestamps clearly.
- Add deterministic tie-breakers.
- Handle duplicate events explicitly.
- Decide how late-arriving events affect historical calculations.
- Test replay behavior.
- Define NULL semantics.

If historical events can be inserted later, the result of:

```sql
LAG(...)
```

can legitimately change because the sequence has changed.

This is important for event-driven architectures and backfills.

A derived result should therefore not necessarily be treated as immutable unless the underlying event history is immutable and complete.

---

## Late-Arriving Events

Suppose the database initially contains:

```text
10:00 → A
10:10 → C
```

Then a late event arrives:

```text
10:05 → B
```

The sequence becomes:

```text
10:00 → A
10:05 → B
10:10 → C
```

Now the `LAG()` result for `C` changes.

This matters in:

- Event sourcing.
- Kafka ingestion.
- CDC pipelines.
- Data warehouses.
- Analytics systems.
- Audit processing.

If the system needs immutable historical conclusions, store the relevant derived state explicitly rather than assuming a future query will always produce the same result.

---

## LAG/LEAD and Transactions

`LAG()` and `LEAD()` operate on the rows visible to the query according to the database's transaction and isolation semantics.

They do not lock rows merely because they compare them.

If a workflow requires:

```text
read previous state
→ decide
→ update state
```

the window function alone does not provide concurrency protection.

Use appropriate database mechanisms such as:

- Transactions.
- Unique constraints.
- Row locks.
- Serializable isolation where justified.
- Atomic updates.

Analytical comparison and concurrency control are separate concerns.

---

## Production Checklist

Before deploying a query using `LAG()` or `LEAD()`:

- Define exactly what "previous" or "next" means.
- Use `PARTITION BY` when sequences are entity-specific.
- Provide a deterministic `ORDER BY`.
- Add a stable tie-breaker where timestamps can collide.
- Confirm whether row offsets or calendar intervals are required.
- Decide how the first/last row should be represented.
- Preserve `NULL` when it carries business meaning.
- Filter input rows when semantically safe.
- Inspect `EXPLAIN (ANALYZE, BUFFERS)` for expensive workloads.
- Test large partitions and realistic concurrency.
- Validate late-arriving and duplicate events.
- Keep authorization boundaries aligned with partitioning and filtering.
- Avoid pulling large datasets into Python solely for sequential comparisons.

---

## Common Mistakes

### Using LAG Without ORDER BY

There is no meaningful "previous row" without defining the sequence.

### Assuming LAG Offset Means Days

```sql
LAG(value, 7)
```

means seven rows backward, not necessarily seven calendar days.

### Ignoring Duplicate Timestamps

```sql
ORDER BY occurred_at
```

may not uniquely define event order.

Prefer:

```sql
ORDER BY occurred_at, id
```

when appropriate.

### Replacing NULL With Zero Automatically

The first row having no previous value is different from the previous value actually being zero.

### Filtering Too Late

Ranking or calculating windows over millions of unnecessary rows wastes database resources.

### Doing Sequential Comparisons in Python

If PostgreSQL can perform the relationship efficiently, avoid transferring large datasets to the application merely to calculate previous or next rows.

### Treating Arrival Order as Business Order

Kafka ingestion time, database insertion time, and event occurrence time can differ.

### Assuming Window Functions Solve Concurrency

They calculate values over a query result. They do not enforce write-side invariants.

### Ignoring Late Events

A newly inserted historical event can change the `LAG()` and `LEAD()` result for surrounding rows.

### Using a Window Function for Every Problem

If the requirement is a relational lookup based on a condition rather than positional adjacency, a join or `EXISTS` may be more appropriate.

---

## Choosing Between LAG and LEAD

| Requirement | Function |
|---|---|
| Compare current row with previous row | `LAG()` |
| Compare current row with next row | `LEAD()` |
| Calculate change from previous period | `LAG()` |
| Calculate expected next value | `LEAD()` |
| Measure time since previous event | `LAG()` |
| Measure time until next event | `LEAD()` |
| Detect gaps between events | `LAG()` |
| Determine duration until next state | `LEAD()` |
| Detect state transitions | Usually `LAG()` |
| Inspect both neighboring events | Both |

---

## LAG/LEAD vs Other SQL Patterns

| Requirement | Preferred pattern |
|---|---|
| Previous/next row in an ordered sequence | `LAG()` / `LEAD()` |
| Rank rows | `ROW_NUMBER()` / `RANK()` / `DENSE_RANK()` |
| Aggregate across a group while preserving rows | Window aggregate |
| Collapse rows into groups | `GROUP BY` |
| Test whether a related row exists | `EXISTS` |
| Retrieve related records based on relationships | `JOIN` |
| Large API pagination | Usually keyset pagination |
| Enforce uniqueness | `UNIQUE` constraint/index |
| Protect concurrent state transition | Transaction/locking/constraint |

The important point is that window functions solve positional analysis; they are not a universal replacement for joins, aggregates, or constraints.

---

## Interview Traps

### "LAG gives the previous physical row."

It gives the previous row according to the window's `ORDER BY`.

### "LEAD(7) means seven days later."

No. It means seven rows later.

### "LAG is always faster than a self-join."

Not necessarily. Query shape, indexes, data distribution, and optimizer decisions determine performance.

### "LAG changes the number of rows."

No. It adds a calculated value while preserving row grain.

### "The first LAG value is always zero."

No. It is `NULL` by default unless a default argument is explicitly supplied.

### "ORDER BY created_at is deterministic."

Only if `created_at` uniquely determines ordering.

### "LAG can be used in WHERE directly."

The window result must generally be computed in an inner query or CTE before it can be filtered.

### "LAG and LEAD understand business time."

They only understand the ordering supplied by the query. The application must define the correct business ordering columns.

### "Window functions guarantee consistent results across retries."

Only when the underlying data and ordering are stable and deterministic. Late-arriving or newly inserted historical rows can change the result.

### "LAG/LEAD can enforce state transitions."

They can analyze transitions, but constraints, transactions, and locking are responsible for enforcing write-side invariants.

---

## Key Takeaways

- **`LAG()` looks backward and `LEAD()` looks forward:** both compare neighboring rows while preserving the original row grain.
- **The window `ORDER BY` defines what previous and next actually mean:** use `PARTITION BY` for independent entity sequences and add deterministic tie-breakers when necessary.
- **Offsets count rows, not time:** `LAG(value, 7)` means seven rows earlier, so missing dates must be handled explicitly for calendar-based comparisons.
- **`LAG()` and `LEAD()` are powerful for event histories, state transitions, gaps, and durations:** keep these relational calculations in PostgreSQL when that is more efficient than application-side processing.
- **Temporal analysis is sensitive to data quality and concurrency:** late-arriving events, duplicate timestamps, NULL semantics, and transaction boundaries must be considered in production designs.