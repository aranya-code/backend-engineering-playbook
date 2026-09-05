# 05- Window Function Queries

## Overview

Window functions are one of the most important SQL capabilities for analytical and reporting workloads.

They allow calculations across a related set of rows while **preserving the individual rows in the result**.

This makes them fundamentally different from `GROUP BY`.

```text
GROUP BY

many rows
    ↓
one row per group


Window Function

many rows
    ↓
same rows
+
calculated value across related rows
```

Typical analytics use cases include:

- Ranking customers or products.
- Calculating running totals.
- Comparing a row with the previous or next row.
- Finding the latest record per entity.
- Calculating moving averages.
- Calculating percentages of totals.
- Detecting state changes.
- Building time-series reports.
- Selecting top-N records per group.

A strong understanding of window functions requires reasoning about:

```text
result grain
    ↓
PARTITION BY
    ↓
ORDER BY
    ↓
window frame
    ↓
calculation
    ↓
filtering
```

---

## What Is a Window Function?

A window function calculates a value across a set of related rows without collapsing those rows into a single result row.

Example:

```sql
SELECT
    order_id,
    customer_id,
    net_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM fact_orders;
```

If a customer has five orders, the query still returns five rows.

Each row contains:

```text
order information
+
total revenue for that customer
```

This is useful when both the individual row and aggregate context are required.

---

## `GROUP BY` vs Window Functions

Consider:

```sql
SELECT
    customer_id,
    SUM(net_amount) AS revenue
FROM fact_orders
GROUP BY customer_id;
```

Result:

```text
customer_id | revenue
-------------+--------
C001        | 15000
C002        | 22000
```

The result grain is:

```text
one row per customer
```

With a window function:

```sql
SELECT
    order_id,
    customer_id,
    net_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM fact_orders;
```

Result:

```text
order_id | customer_id | net_amount | customer_revenue
---------+-------------+------------+-----------------
1001     | C001        | 5000       | 15000
1002     | C001        | 3000       | 15000
1003     | C001        | 7000       | 15000
```

The result grain remains:

```text
one row per order
```

This distinction is one of the most important concepts in analytical SQL.

---

## Window Function Anatomy

A typical expression is:

```sql
SUM(net_amount) OVER (
    PARTITION BY customer_id
    ORDER BY occurred_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

Each component has a separate responsibility.

| Component | Purpose |
|---|---|
| `SUM(net_amount)` | Calculation |
| `OVER` | Converts it into a window calculation |
| `PARTITION BY` | Defines independent groups |
| `ORDER BY` | Defines row sequence |
| Frame | Defines which rows participate |

Not every window function requires every component.

---

## `PARTITION BY`

`PARTITION BY` divides rows into independent windows.

Example:

```sql
SELECT
    customer_id,
    order_id,
    net_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
    ) AS customer_revenue
FROM fact_orders;
```

Conceptually:

```text
Customer C001
    ├── Order 1
    ├── Order 2
    └── Order 3

Customer C002
    ├── Order 4
    └── Order 5
```

The calculation for C001 does not include C002.

---

## No `PARTITION BY`

Without `PARTITION BY`, the entire result is one window.

```sql
SELECT
    order_id,
    net_amount,
    SUM(net_amount) OVER () AS total_revenue
FROM fact_orders;
```

Every row receives the same total.

This is useful for:

- Percentage of total.
- Global ranking.
- Overall statistics.
- Comparing individual rows with global metrics.

---

## `ORDER BY` Inside a Window

Window `ORDER BY` defines the logical sequence used by the calculation.

Example:

```sql
SELECT
    customer_id,
    order_id,
    occurred_at,
    net_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, order_id
    ) AS cumulative_revenue
FROM fact_orders;
```

The cumulative total follows each customer's chronological order.

The tie-breaker:

```sql
order_id
```

is important when multiple rows have the same timestamp.

---

## Deterministic Ordering

This is dangerous:

```sql
ORDER BY occurred_at
```

if multiple rows can have the same `occurred_at`.

Prefer:

```sql
ORDER BY occurred_at, order_id
```

A window calculation that depends on row order should use a deterministic total ordering whenever possible.

This is especially important for:

- `ROW_NUMBER()`
- `LAG()`
- `LEAD()`
- Running totals.
- Cumulative metrics.
- Pagination-related analytics.

---

## Window Frames

A window `ORDER BY` and a window frame are related but different concepts.

Example:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

means:

```text
all preceding rows
+
current row
```

A running total can therefore be written explicitly as:

```sql
SUM(net_amount) OVER (
    PARTITION BY customer_id
    ORDER BY occurred_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

Explicit frames are often preferable when the exact semantics matter.

---

## `ROWS` vs `RANGE`

These are not interchangeable.

`ROWS` operates on physical rows in the ordered result.

```sql
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
```

means:

```text
current row
+
previous six rows
```

`RANGE` is based on the ordering values and peer rows.

This distinction becomes important when multiple rows have identical ordering values.

For production analytics, use an explicit frame when the business meaning depends on precise row behavior.

---

## Running Total

A common analytical requirement is cumulative revenue.

```sql
SELECT
    occurred_at,
    net_amount,
    SUM(net_amount) OVER (
        ORDER BY occurred_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM fact_orders
ORDER BY occurred_at, order_id;
```

Example:

```text
Order   Amount   Cumulative
------  -------  ----------
1001    100      100
1002    250      350
1003    150      500
```

---

## Running Total per Customer

```sql
SELECT
    customer_id,
    order_id,
    occurred_at,
    net_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS customer_running_revenue
FROM fact_orders;
```

The running total resets for each customer.

---

## Ranking Functions

PostgreSQL provides several important ranking functions:

| Function | Behavior |
|---|---|
| `ROW_NUMBER()` | Unique sequential number |
| `RANK()` | Same rank for ties, gaps after ties |
| `DENSE_RANK()` | Same rank for ties, no gaps |

Example:

```sql
SELECT
    product_id,
    revenue,
    ROW_NUMBER() OVER (
        ORDER BY revenue DESC
    ) AS row_number,
    RANK() OVER (
        ORDER BY revenue DESC
    ) AS rank,
    DENSE_RANK() OVER (
        ORDER BY revenue DESC
    ) AS dense_rank
FROM product_revenue;
```

---

## `ROW_NUMBER()`

`ROW_NUMBER()` assigns a unique sequence.

Example:

```sql
SELECT
    customer_id,
    order_id,
    occurred_at,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at DESC, order_id DESC
    ) AS row_number
FROM fact_orders;
```

This is particularly useful for:

- Latest row per entity.
- Deduplication.
- Top-N selection.
- Deterministic row numbering.

---

## Latest Row per Entity

A common production pattern is finding the latest record per customer.

```sql
WITH ranked_orders AS (
    SELECT
        order_id,
        customer_id,
        occurred_at,
        status,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY occurred_at DESC, order_id DESC
        ) AS row_number
    FROM fact_orders
)
SELECT
    order_id,
    customer_id,
    occurred_at,
    status
FROM ranked_orders
WHERE row_number = 1;
```

The inner query assigns:

```text
1 = latest
2 = second latest
3 = third latest
```

The outer query selects only the latest row.

---

## Top-N per Group

Example: top five products by revenue in each category.

```sql
WITH ranked_products AS (
    SELECT
        category_id,
        product_id,
        revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category_id
            ORDER BY revenue DESC, product_id
        ) AS position
    FROM product_revenue
)
SELECT
    category_id,
    product_id,
    revenue
FROM ranked_products
WHERE position <= 5
ORDER BY category_id, position;
```

This is different from:

```sql
ORDER BY revenue DESC
LIMIT 5
```

because the latter returns five rows globally rather than five rows per category.

---

## `RANK()`

`RANK()` gives tied rows the same position and leaves gaps.

For values:

```text
100
100
90
80
```

the ranks are:

```text
1
1
3
4
```

Use `RANK()` when tied values should share a competition position.

---

## `DENSE_RANK()`

`DENSE_RANK()` also gives ties the same rank but does not leave gaps.

For:

```text
100
100
90
80
```

the result is:

```text
1
1
2
3
```

Use it when rank numbers should remain contiguous.

---

## Choosing a Ranking Function

| Requirement | Function |
|---|---|
| Every row must have a unique position | `ROW_NUMBER()` |
| Competition ranking with gaps | `RANK()` |
| Competition ranking without gaps | `DENSE_RANK()` |
| Latest row per entity | `ROW_NUMBER()` |
| Top-N rows per group | Usually `ROW_NUMBER()` |
| Include all tied rows at cutoff | `RANK()` / `DENSE_RANK()` |

---

## `LAG()`

`LAG()` accesses a previous row within the window.

Example:

```sql
SELECT
    month,
    revenue,
    LAG(revenue) OVER (
        ORDER BY month
    ) AS previous_month_revenue
FROM monthly_revenue
ORDER BY month;
```

This enables comparisons such as:

```text
current revenue
vs
previous revenue
```

---

## Month-over-Month Growth

```sql
WITH monthly AS (
    SELECT
        date_trunc('month', occurred_at) AS month,
        SUM(net_amount) AS revenue
    FROM fact_orders
    GROUP BY 1
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (
        ORDER BY month
    ) AS previous_revenue,
    (
        revenue - LAG(revenue) OVER (
            ORDER BY month
        )
    ) / NULLIF(
        LAG(revenue) OVER (
            ORDER BY month
        ),
        0
    ) AS growth_rate
FROM monthly
ORDER BY month;
```

For maintainability, the repeated `LAG()` expression can also be calculated in an intermediate query.

---

## `LEAD()`

`LEAD()` accesses a subsequent row.

```sql
SELECT
    customer_id,
    occurred_at,
    LEAD(occurred_at) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, event_id
    ) AS next_event_at
FROM customer_events;
```

This is useful for:

- Time until next event.
- Session boundaries.
- State transitions.
- Duration calculations.
- Event sequence analysis.

---

## Event Duration

Example:

```sql
SELECT
    customer_id,
    occurred_at AS started_at,
    LEAD(occurred_at) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, event_id
    ) AS ended_at
FROM customer_events;
```

The next event can provide the end boundary for the current event.

The business meaning must be validated; the next event is not automatically a true end timestamp.

---

## Detecting State Changes

Suppose a subscription has historical status events.

```sql
WITH ordered_events AS (
    SELECT
        subscription_id,
        occurred_at,
        status,
        LAG(status) OVER (
            PARTITION BY subscription_id
            ORDER BY occurred_at, event_id
        ) AS previous_status
    FROM subscription_status_history
)
SELECT
    subscription_id,
    occurred_at,
    previous_status,
    status
FROM ordered_events
WHERE previous_status IS DISTINCT FROM status;
```

`IS DISTINCT FROM` provides NULL-safe comparison semantics.

---

## First and Last Values

Window functions include:

```text
FIRST_VALUE()
LAST_VALUE()
NTH_VALUE()
```

Example:

```sql
SELECT
    customer_id,
    occurred_at,
    net_amount,
    FIRST_VALUE(net_amount) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, order_id
    ) AS first_order_amount
FROM fact_orders;
```

`LAST_VALUE()` requires particular attention to the window frame.

For example, with a default frame, `LAST_VALUE()` may return the current row's value rather than the final row of the partition.

An explicit frame can make the intended semantics clear:

```sql
LAST_VALUE(net_amount) OVER (
    PARTITION BY customer_id
    ORDER BY occurred_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
)
```

---

## Moving Average

A seven-row moving average can be expressed as:

```sql
AVG(revenue) OVER (
    ORDER BY day
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
)
```

Example:

```sql
SELECT
    day,
    revenue,
    AVG(revenue) OVER (
        ORDER BY day
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_average
FROM daily_revenue
ORDER BY day;
```

Important: this is a seven-row window, not necessarily a seven-calendar-day window if dates are missing.

---

## Calendar-Based Windows

If the business requirement is:

```text
previous seven calendar days
```

but some dates have no records, a row-based frame may be incorrect.

A robust solution can involve a calendar dimension:

```text
dim_date
   ↓
complete date sequence
   ↓
left join daily metrics
   ↓
window calculation
```

This ensures missing dates are represented explicitly.

---

## Percentage of Total

Window functions can calculate each row's contribution to the overall total.

```sql
SELECT
    product_id,
    revenue,
    revenue / NULLIF(
        SUM(revenue) OVER (),
        0
    ) AS revenue_share
FROM product_revenue
ORDER BY revenue DESC;
```

The total is calculated without collapsing the product rows.

---

## Percentage Within a Group

```sql
SELECT
    category_id,
    product_id,
    revenue,
    revenue / NULLIF(
        SUM(revenue) OVER (
            PARTITION BY category_id
        ),
        0
    ) AS category_share
FROM product_revenue;
```

Each product is compared against its category total.

---

## Combining Aggregation and Windows

A common analytical pattern is:

```text
raw facts
    ↓
GROUP BY
    ↓
aggregated dataset
    ↓
window function
```

Example:

```sql
WITH monthly_customer_revenue AS (
    SELECT
        customer_id,
        date_trunc('month', occurred_at) AS month,
        SUM(net_amount) AS revenue
    FROM fact_orders
    GROUP BY
        customer_id,
        date_trunc('month', occurred_at)
)
SELECT
    customer_id,
    month,
    revenue,
    SUM(revenue) OVER (
        PARTITION BY customer_id
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM monthly_customer_revenue;
```

The first stage establishes the correct analytical grain.

The second stage performs the cross-row calculation.

---

## Filtering on Window Results

Window functions are evaluated after the query's filtering stages, so a window result generally cannot be referenced directly in the same `WHERE` clause.

This does not work:

```sql
SELECT
    customer_id,
    revenue,
    ROW_NUMBER() OVER (
        ORDER BY revenue DESC
    ) AS position
FROM customer_revenue
WHERE position <= 10;
```

Use a subquery or CTE:

```sql
WITH ranked AS (
    SELECT
        customer_id,
        revenue,
        ROW_NUMBER() OVER (
            ORDER BY revenue DESC
        ) AS position
    FROM customer_revenue
)
SELECT
    customer_id,
    revenue
FROM ranked
WHERE position <= 10;
```

PostgreSQL does not provide a general `QUALIFY` clause, so the subquery/CTE pattern is important.

---

## Logical Query Processing

A simplified conceptual order is:

```text
FROM
↓
JOIN
↓
WHERE
↓
GROUP BY
↓
HAVING
↓
Window calculations
↓
SELECT / ORDER BY semantics
```

The optimizer may physically execute operations differently.

The logical model is useful for understanding why:

```text
WHERE
```

cannot normally reference a window result computed later.

---

## Window Functions and Joins

Joins can change the row grain before the window function executes.

Consider:

```text
orders
   ↓
order_items
```

An order-level window applied after joining order items may operate over:

```text
one row per order item
```

rather than:

```text
one row per order
```

This can produce incorrect analytical results.

Always establish the intended grain before applying the window calculation.

---

## Correct Grain Before Window Calculation

Instead of:

```text
orders
   ↓
join items
   ↓
window
```

you may need:

```text
order items
   ↓
aggregate to orders
   ↓
window
```

Example:

```sql
WITH order_totals AS (
    SELECT
        order_id,
        SUM(line_amount) AS order_total
    FROM fact_order_items
    GROUP BY order_id
)
SELECT
    order_id,
    order_total,
    SUM(order_total) OVER (
        ORDER BY order_id
    ) AS cumulative_order_value
FROM order_totals;
```

---

## Multiple Window Functions

Multiple window calculations can be used together.

```sql
SELECT
    customer_id,
    order_id,
    occurred_at,
    net_amount,
    ROW_NUMBER() OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, order_id
    ) AS order_number,
    LAG(net_amount) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, order_id
    ) AS previous_order_amount,
    SUM(net_amount) OVER (
        PARTITION BY customer_id
        ORDER BY occurred_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_revenue
FROM fact_orders;
```

This can produce a rich analytical dataset in a single query.

However, each window operation may require sorting or additional processing, so inspect the plan for large datasets.

---

## Named Windows

PostgreSQL supports the `WINDOW` clause.

```sql
SELECT
    customer_id,
    order_id,
    occurred_at,
    net_amount,
    ROW_NUMBER() OVER w AS order_number,
    LAG(net_amount) OVER w AS previous_amount
FROM fact_orders
WINDOW w AS (
    PARTITION BY customer_id
    ORDER BY occurred_at, order_id
);
```

This is useful when several expressions share the same partitioning and ordering definition.

It reduces duplication and makes the analytical intent clearer.

---

## NULL Ordering

Ordering containing NULL values requires deliberate semantics.

PostgreSQL allows:

```sql
ORDER BY occurred_at NULLS LAST
```

or:

```sql
ORDER BY occurred_at DESC NULLS LAST
```

Do not assume NULL values automatically represent the earliest or latest meaningful event.

The correct choice depends on the data model.

---

## Window Functions and Pagination

Window functions can support ranking-based result sets, but they are not automatically the best pagination strategy.

For large APIs, keyset pagination is generally preferable to repeatedly calculating:

```sql
ROW_NUMBER()
```

across a huge dataset.

For example:

```sql
WHERE (revenue, product_id) < ($1, $2)
ORDER BY revenue DESC, product_id DESC
LIMIT 50;
```

can avoid processing all earlier rows.

Use window functions when the analytical calculation itself is required, not merely as a substitute for efficient pagination.

---

## Performance Considerations

Window functions can be expensive because PostgreSQL may need to:

```text
read rows
    ↓
partition/order rows
    ↓
sort
    ↓
execute window calculations
```

Performance depends on:

- Number of input rows.
- Number of partitions.
- Partition sizes.
- Ordering requirements.
- Number of window definitions.
- Available memory.
- Data distribution.
- Query concurrency.

Large partitions can be particularly expensive.

---

## Indexes and Window Functions

An index can sometimes help reduce input rows or provide useful ordering, but an index does not guarantee that PostgreSQL will avoid sorting.

For example:

```sql
PARTITION BY customer_id
ORDER BY occurred_at, order_id
```

may align with:

```sql
(customer_id, occurred_at, order_id)
```

but the planner still decides whether using that index is beneficial.

Always validate with:

```sql
EXPLAIN (ANALYZE, BUFFERS)
```

rather than assuming the index will eliminate the sort.

---

## Memory and Sorts

Large window operations may require substantial memory.

Potential symptoms include:

```text
Sort Method: external merge
Disk:
```

or other temporary-file activity.

Increasing `work_mem` can help some operations, but it should not be treated as a universal solution.

Remember that memory can multiply with:

```text
concurrent queries
×
multiple sort/hash operations
×
parallel workers
```

Tune based on actual workload behavior.

---

## Partition Size Matters

Consider:

```text
PARTITION BY customer_id
```

If one customer has:

```text
100 million rows
```

that partition can dominate execution.

Data skew therefore matters even when average partition size looks reasonable.

For large systems, monitor:

```text
largest tenant
largest customer
largest partition
largest time range
```

rather than relying only on averages.

---

## Reporting API Example

A FastAPI endpoint may expose ranked analytics:

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/v1/reports/top-customers")
def top_customers(
    limit: int = Query(default=20, ge=1, le=100),
):
    # Query the analytics repository here.
    return {"limit": limit}
```

The API should control:

- Maximum result size.
- Allowed grouping dimensions.
- Date-range limits.
- Tenant authorization.
- Supported metrics.
- Query timeout.

The database should remain responsible for set-based analytical computation.

---

## Django Reporting Query

Django can express some window functions through `Window`.

```python
from django.db.models import F, Window
from django.db.models.functions import RowNumber

queryset = (
    Order.objects
    .annotate(
        position=Window(
            expression=RowNumber(),
            partition_by=[F("customer_id")],
            order_by=[F("occurred_at").desc(), F("id").desc()],
        )
    )
)
```

For complex analytics, raw SQL may provide clearer control over:

```text
CTEs
frames
multiple windows
database-specific optimization
```

Use ORM support where it improves maintainability without obscuring the query's semantics.

---

## Analytics with Kafka

Kafka preserves ordering within a partition, not globally across all events.

If window calculations depend on business event time:

```text
Kafka arrival order
```

must not automatically be treated as:

```text
business event order
```

Late events can change historical window results.

Analytics pipelines should therefore define:

- Event timestamp.
- Processing timestamp.
- Ordering key.
- Late-event policy.
- Reprocessing strategy.

---

## Window Functions and Historical Corrections

Suppose a late event is inserted into a historical period.

A running total may change for every later row in that partition.

```text
Historical event inserted
        ↓
Earlier window rows unchanged
        ↓
Later cumulative results change
```

This is important when storing precomputed window results.

If derived values are materialized, define how corrections trigger recomputation.

---

## Security and Multi-Tenant Analytics

Window functions must respect tenant boundaries.

This is unsafe for tenant-specific rankings:

```sql
RANK() OVER (
    ORDER BY revenue DESC
)
```

if the input contains multiple tenants and users should only see rankings within their tenant.

Use:

```sql
RANK() OVER (
    PARTITION BY tenant_key
    ORDER BY revenue DESC
)
```

and ensure the underlying rows are authorized.

Tenant filtering should occur before the window calculation when appropriate.

---

## Materializing Window Results

Window calculations can be materialized when:

- The query is expensive.
- Results are requested frequently.
- Freshness requirements permit delay.
- Recalculation is manageable.

Example:

```text
raw facts
   ↓
daily aggregation
   ↓
ranking / window calculation
   ↓
reporting table
```

The trade-off is additional complexity around:

```text
refresh
backfill
late data
corrections
idempotency
```

---

## Common Mistakes

### Using `GROUP BY` When Row Context Is Required

**Problem:** individual rows disappear.

**Solution:** use a window function when the aggregate must remain alongside each row.

### Using a Window Function When Rows Should Be Collapsed

**Problem:** unnecessary data is retained.

**Solution:** use `GROUP BY` when only one row per group is required.

### Missing a Deterministic Tie-Breaker

**Problem:** equal timestamps or values can produce unstable row ordering.

**Solution:** add a unique or sufficiently deterministic secondary ordering column.

### Forgetting the Window Frame

**Problem:** default frame behavior can differ from the intended business semantics.

**Solution:** explicitly specify `ROWS` or another appropriate frame when required.

### Misusing `LAST_VALUE()`

**Problem:** the default frame can cause `LAST_VALUE()` to return the current row rather than the final row in the partition.

**Solution:** use an explicit frame extending through `UNBOUNDED FOLLOWING` when the final partition value is required.

### Applying Windows After a Multiplying Join

**Problem:** duplicated rows change the calculation.

**Solution:** aggregate or otherwise establish the correct grain before joining and windowing.

### Filtering a Window Alias in `WHERE`

**Problem:** window results are not available at that stage.

**Solution:** use a CTE or subquery.

### Treating `ROWS 6 PRECEDING` as Seven Calendar Days

**Problem:** missing dates change the meaning.

**Solution:** use a calendar dimension or complete time series when calendar-based semantics are required.

### Assuming Indexes Eliminate Window Sorts

**Problem:** the planner may still choose a sort.

**Solution:** validate with `EXPLAIN (ANALYZE, BUFFERS)`.

### Using Window Functions for Deep Pagination

**Problem:** the database may calculate far more rows than the API needs.

**Solution:** use keyset pagination for large ordered APIs.

### Ignoring Data Skew

**Problem:** one extremely large partition can dominate execution.

**Solution:** inspect distribution, not just average partition size.

---

## Production Troubleshooting

When a window query becomes slow:

1. Verify the input row grain.
2. Verify partition boundaries.
3. Check ordering columns and tie-breakers.
4. Inspect join cardinality.
5. Reduce unnecessary input rows.
6. Inspect `EXPLAIN (ANALYZE, BUFFERS)`.
7. Check sort methods and temporary files.
8. Compare estimated and actual row counts.
9. Check partition-size skew.
10. Evaluate indexes for filtering and ordering.
11. Consider pre-aggregation.
12. Consider materializing expensive recurring calculations.

Do not solve a slow window query by increasing `work_mem` first. Understand why the query needs that memory.

---

## Production Checklist

### Correctness

- [ ] Input grain is documented.
- [ ] Output grain is documented.
- [ ] `PARTITION BY` matches the business boundary.
- [ ] Window ordering is deterministic.
- [ ] NULL ordering is intentional.
- [ ] Window frame semantics are understood.
- [ ] Joins cannot unexpectedly multiply rows.
- [ ] Time-zone semantics are explicit.

### Query Design

- [ ] `GROUP BY` is used when row collapse is required.
- [ ] Window functions are used when row context must be preserved.
- [ ] Ranking function semantics are appropriate.
- [ ] `LAG()` / `LEAD()` offsets represent the intended row relationship.
- [ ] Window results are filtered through a valid outer query.
- [ ] Multiple windows share definitions where appropriate.

### Performance

- [ ] Input data is bounded.
- [ ] Large partitions are identified.
- [ ] Execution plans have been inspected.
- [ ] Sort and temporary-file behavior is understood.
- [ ] Statistics are current.
- [ ] Indexes support important filtering/order patterns where useful.
- [ ] Expensive recurring calculations have been evaluated for pre-aggregation.

### Backend

- [ ] Reporting APIs enforce maximum limits.
- [ ] Date ranges are bounded.
- [ ] Dynamic dimensions use allowlists.
- [ ] Tenant authorization is enforced.
- [ ] Large exports are asynchronous.
- [ ] Cached results have explicit freshness semantics.

### Analytics Pipeline

- [ ] Event time and processing time are distinct.
- [ ] Duplicate events are handled.
- [ ] Late events have a defined policy.
- [ ] Historical corrections can be reprocessed.
- [ ] Materialized window results have refresh semantics.

---

## Senior Decision Framework

When designing a window query, reason in this order:

```text
What does one input row represent?
        ↓
What should one output row represent?
        ↓
Should rows be collapsed?
        ↓
If not, what related rows form the window?
        ↓
What defines the partition?
        ↓
What defines deterministic order?
        ↓
What frame should participate?
        ↓
Does a join change the grain?
        ↓
How many rows must be sorted?
        ↓
Can the query execute within the workload budget?
```

A useful mental model is:

```text
GROUP BY
    = change the grain

WINDOW FUNCTION
    = keep the grain and add context
```

This distinction simplifies many analytical SQL problems.

## Interview Traps

### "Window Functions Are Aggregations"

Not necessarily.

Ranking functions such as:

```sql
ROW_NUMBER()
RANK()
DENSE_RANK()
```

are window functions but are not aggregate functions.

### "`PARTITION BY` Is the Same as `GROUP BY`"

No.

`GROUP BY` collapses rows.

`PARTITION BY` defines independent windows while preserving rows.

### "`ROW_NUMBER()` and `RANK()` Are Equivalent"

No.

`ROW_NUMBER()` gives every row a unique sequence.

`RANK()` assigns equal positions to ties and leaves gaps.

### "`ORDER BY` Always Makes the Query Deterministic"

Only if the ordering expressions produce a sufficiently complete ordering.

If multiple rows have equal ordering values, add a deterministic tie-breaker.

### "`ROWS 6 PRECEDING` Means Seven Days"

No.

It means six preceding rows plus the current row.

Missing calendar dates change the interpretation.

### "`LAST_VALUE()` Always Returns the Last Row"

Not with every default frame.

The frame must be examined when the intended result is the final value of the entire partition.

### "Indexes Make Window Functions Fast"

Indexes can help filtering or sometimes ordering, but window functions may still require sorting and substantial processing.

### "Window Functions Replace GROUP BY"

No.

They solve different problems and are frequently used together:

```text
GROUP BY
    ↓
establish analytical grain
    ↓
WINDOW
    ↓
calculate cross-row context
```

## Key Takeaways

- **Window functions preserve the result's row grain while adding calculations across related rows; `GROUP BY` instead collapses rows into groups.**
- **`PARTITION BY`, deterministic `ORDER BY`, and the correct window frame define the semantics of the calculation and must be chosen deliberately.**
- **`ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, and `LEAD()` solve different analytical problems and should not be treated as interchangeable.**
- **Join cardinality, partition size, sorting, memory, and late-arriving data can materially affect both correctness and performance of production window queries.**
- **For senior-level SQL design, establish the correct grain first, then define the window boundary and frame, validate the execution plan, and materialize expensive calculations only when workload requirements justify it.**