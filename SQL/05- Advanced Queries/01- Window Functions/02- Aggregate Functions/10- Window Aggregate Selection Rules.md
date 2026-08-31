# 10- Window Aggregate Selection Rules

## Overview

Window aggregate functions such as `SUM()`, `AVG()`, `COUNT()`, `MIN()`, and `MAX()` are powerful because they calculate aggregate values while preserving the row-level result set.

The difficult part is usually not the aggregate function itself. The engineering decision is determining **which rows the window aggregate should see** and **which rows it should return**.

A production query commonly combines:

- `WHERE` to restrict the input rows.
- `GROUP BY` to change row granularity.
- `HAVING` to filter grouped results.
- `PARTITION BY` to define independent window groups.
- `ORDER BY` inside `OVER()` to define ordered processing.
- A window frame to define the rows contributing to the current calculation.
- An outer query or CTE to filter results produced by the window stage.

Understanding these boundaries prevents subtle reporting and analytics bugs.

## The Core Selection Rule

For a window aggregate:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

the `PARTITION BY` clause determines **which rows belong to the same logical group**, but the rows available to the window function have already been affected by earlier query stages such as `FROM`, `JOIN`, and `WHERE`.

For example:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE status = 'completed';
```

The window aggregate sees only completed orders.

If customer `101` has:

| order_id | status | amount |
|---|---|---:|
| 1 | completed | 100 |
| 2 | completed | 150 |
| 3 | cancelled | 200 |

the query returns:

| order_id | amount | customer_total |
|---|---:|---:|
| 1 | 100 | 250 |
| 2 | 150 | 250 |

The cancelled order is not part of the window calculation because it was removed by `WHERE`.

This is one of the most important rules for correctly designing window aggregate queries.

## Logical Query Processing

A useful logical model is:

```text
FROM / JOIN
      ↓
WHERE
      ↓
GROUP BY
      ↓
Grouped aggregates
      ↓
HAVING
      ↓
Window functions
      ↓
SELECT
      ↓
DISTINCT
      ↓
ORDER BY
      ↓
LIMIT / OFFSET
```

This describes SQL's logical semantics, not necessarily the exact physical execution plan chosen by the database optimizer.

The practical implication is that a window function generally cannot be referenced directly in clauses that logically execute before the window stage.

For example, this is invalid in the general SQL model:

```sql
SELECT
    order_id,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE customer_total > 1000;
```

Instead, introduce another query level:

```sql
WITH order_metrics AS (
    SELECT
        order_id,
        customer_id,
        amount,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
)
SELECT
    order_id,
    customer_id,
    amount,
    customer_total
FROM order_metrics
WHERE customer_total > 1000;
```

The second query level can now filter the already-computed window value.

## `WHERE` Controls the Window Input

`WHERE` is often the most important selection mechanism when working with window aggregates.

Consider:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE created_at >= DATE '2026-01-01';
```

The total is calculated from orders created on or after January 1, 2026.

It does **not** represent the customer's lifetime total unless the underlying dataset itself is restricted to that period by design.

This distinction matters for API and reporting requirements.

### Requirement: Total for the filtered period

Use:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS period_total
FROM orders
WHERE created_at >= :start_date
  AND created_at < :end_date;
```

### Requirement: Lifetime total while displaying a filtered period

Use an inner query for the window calculation:

```sql
WITH order_metrics AS (
    SELECT
        order_id,
        customer_id,
        created_at,
        amount,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS lifetime_total
    FROM orders
)
SELECT
    order_id,
    customer_id,
    created_at,
    amount,
    lifetime_total
FROM order_metrics
WHERE created_at >= :start_date
  AND created_at < :end_date;
```

The difference is entirely about **which query level performs the filtering**.

## `PARTITION BY` Does Not Filter Rows

A common misconception is that:

```sql
PARTITION BY customer_id
```

selects customer rows.

It does not.

It divides the rows visible to the window function into logical groups.

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

means:

> For each current row, calculate `SUM(amount)` over the rows belonging to the same `customer_id` partition.

It does not mean:

> Return only one row per customer.

That distinction separates window functions from `GROUP BY`.

| Feature | `GROUP BY` | `PARTITION BY` in a window |
|---|---|---|
| Changes row granularity | Yes | No |
| Produces one row per group | Usually | No |
| Preserves individual rows | No | Yes |
| Can calculate group totals | Yes | Yes |
| Can calculate running totals | No | Yes |
| Can be combined with row-level columns | Requires additional logic | Naturally |

## `GROUP BY` Before a Window Function

Window functions can operate over the output of a grouping operation.

Consider:

```sql
SELECT
    customer_id,
    DATE_TRUNC('month', created_at) AS month,
    SUM(amount) AS monthly_revenue,
    SUM(SUM(amount)) OVER (
        PARTITION BY customer_id
        ORDER BY DATE_TRUNC('month', created_at)
    ) AS cumulative_revenue
FROM orders
GROUP BY
    customer_id,
    DATE_TRUNC('month', created_at);
```

Here the window function does not operate over individual orders.

It operates over the **grouped monthly rows** produced by `GROUP BY`.

Conceptually:

```text
Raw orders
    ↓
GROUP BY customer + month
    ↓
Monthly revenue rows
    ↓
Window SUM()
    ↓
Cumulative monthly revenue
```

This pattern is extremely useful for dashboards because it avoids calculating cumulative metrics over every underlying transactional row.

## `HAVING` and Window Aggregate Selection

`HAVING` filters grouped results before the window stage.

For example:

```sql
SELECT
    customer_id,
    DATE_TRUNC('month', created_at) AS month,
    SUM(amount) AS monthly_revenue,
    SUM(SUM(amount)) OVER (
        PARTITION BY customer_id
        ORDER BY DATE_TRUNC('month', created_at)
    ) AS cumulative_revenue
FROM orders
GROUP BY
    customer_id,
    DATE_TRUNC('month', created_at)
HAVING SUM(amount) > 100;
```

Only monthly groups with revenue greater than `100` reach the window calculation.

Therefore, the cumulative calculation is based on the surviving grouped rows.

This can be surprising.

If the requirement is:

> Show months whose revenue exceeds 100, but calculate cumulative revenue across all months.

then calculate the cumulative value first and filter it afterward:

```sql
WITH monthly_metrics AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', created_at) AS month,
        SUM(amount) AS monthly_revenue
    FROM orders
    GROUP BY
        customer_id,
        DATE_TRUNC('month', created_at)
),
cumulative_metrics AS (
    SELECT
        customer_id,
        month,
        monthly_revenue,
        SUM(monthly_revenue) OVER (
            PARTITION BY customer_id
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM monthly_metrics
)
SELECT
    customer_id,
    month,
    monthly_revenue,
    cumulative_revenue
FROM cumulative_metrics
WHERE monthly_revenue > 100;
```

This preserves the intended semantic boundary.

## Window Frame Selection

`PARTITION BY` identifies the group, while the frame identifies the rows contributing to the current row when an ordered window is used.

For example:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

has three distinct concepts:

| Component | Responsibility |
|---|---|
| `SUM(amount)` | Aggregation |
| `PARTITION BY customer_id` | Group boundary |
| `ORDER BY created_at, order_id` | Sequence |
| `ROWS BETWEEN ...` | Calculation frame |

This separation is important when debugging incorrect running or moving aggregates.

## Deterministic Ordering

If an ordered window is used, the ordering should normally be deterministic.

Avoid relying solely on:

```sql
ORDER BY created_at
```

when multiple rows can have the same timestamp.

Prefer:

```sql
ORDER BY created_at, order_id
```

assuming `order_id` uniquely identifies the row.

For a running total:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS running_total
```

This makes the row sequence explicit.

Without a deterministic tie-breaker, multiple rows sharing the same ordering value can produce ambiguous results when a row-based frame is intended.

## Choosing Between Full-Partition and Framed Aggregates

The correct window specification depends on the business question.

| Business requirement | Window specification |
|---|---|
| Customer lifetime total | `PARTITION BY customer_id` |
| Customer average order value | `PARTITION BY customer_id` |
| Running customer total | `PARTITION BY customer_id ORDER BY ... ROWS ...` |
| Last 30-row moving total | `ORDER BY ... ROWS BETWEEN 29 PRECEDING AND CURRENT ROW` |
| Current and previous period | `ORDER BY ... ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` |
| Total within each tenant/customer | `PARTITION BY tenant_id, customer_id` |

Do not add `ORDER BY` simply because a window function "looks more complete." It changes the semantics and can affect performance.

## Multiple Aggregates Over the Same Partition

A single query can calculate several metrics over the same partition:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    COUNT(*) OVER (
        PARTITION BY customer_id
    ) AS order_count,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS total_spend,
    AVG(amount) OVER (
        PARTITION BY customer_id
    ) AS average_order,
    MIN(amount) OVER (
        PARTITION BY customer_id
    ) AS minimum_order,
    MAX(amount) OVER (
        PARTITION BY customer_id
    ) AS maximum_order
FROM orders;
```

This is useful for API responses and analytical datasets where the row-level entity and group-level metrics are both required.

However, do not assume that writing several window expressions always means several independent full-table operations. Database optimizers can share work, particularly when window specifications are compatible. Actual behavior should be validated with an execution plan.

## Window Specification Reuse

When several expressions use the same partition and ordering, a named window can improve readability.

PostgreSQL supports:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER customer_window AS running_total,
    AVG(amount) OVER customer_window AS running_average
FROM orders
WINDOW customer_window AS (
    PARTITION BY customer_id
    ORDER BY created_at, order_id
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
);
```

This reduces duplication and makes it harder for two related calculations to accidentally use different partitioning or frame definitions.

Named windows are particularly useful when a reporting query contains several related analytical metrics.

## `DISTINCT` and Window Aggregates

`DISTINCT` operates at a different query stage from window calculations.

For example:

```sql
SELECT DISTINCT
    customer_id,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders;
```

The window calculation is performed while individual rows still exist, and `DISTINCT` then removes duplicate result rows.

The result may therefore contain one row per customer because both selected values are identical within each customer.

This is different from using:

```sql
GROUP BY customer_id
```

The two queries can sometimes produce similar output but have different semantics and potentially different execution costs.

When only one row per group is required, `GROUP BY` is usually the clearer expression of intent.

## `LIMIT` and Window Aggregates

`LIMIT` is another important selection boundary.

Consider:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
ORDER BY created_at DESC
LIMIT 20;
```

The window calculation is logically based on the rows available before the final `LIMIT`.

Therefore, `customer_total` is not calculated only from the 20 returned rows.

This is useful when an API returns a page of orders but needs customer-level metrics calculated over the complete filtered dataset.

However, the database may still need to process a substantial number of rows to calculate the window aggregate.

Pagination does not automatically make a window query cheap.

## Window Aggregates and Pagination

Suppose an endpoint returns:

```text
GET /orders?page=1&page_size=50
```

and needs:

- The latest 50 orders.
- Each customer's total spend.

A query such as:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS customer_total
FROM orders
WHERE tenant_id = :tenant_id
ORDER BY created_at DESC, order_id DESC
LIMIT :page_size
OFFSET :offset;
```

can be semantically correct, but the window calculation may still require processing many rows for the tenant.

For large datasets, consider whether the customer total should instead come from:

- A customer summary table.
- A materialized view.
- A precomputed aggregate.
- A cache with explicit freshness semantics.

This is a classic distinction between **query correctness** and **operational scalability**.

## CTEs as Selection Boundaries

CTEs are useful for explicitly separating stages.

For example:

```sql
WITH customer_metrics AS (
    SELECT
        order_id,
        customer_id,
        amount,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
    WHERE tenant_id = :tenant_id
)
SELECT
    order_id,
    customer_id,
    amount,
    customer_total
FROM customer_metrics
WHERE customer_total >= :minimum_total;
```

This makes the intent obvious:

```text
Tenant filtering
      ↓
Window aggregation
      ↓
Filter aggregate result
```

Modern PostgreSQL versions can inline many non-recursive CTEs when doing so is beneficial, so using a CTE does not inherently mean that the intermediate result is materialized.

If materialization behavior matters, inspect the execution plan and use `MATERIALIZED` or `NOT MATERIALIZED` only when there is a concrete reason.

## Derived Tables as an Alternative

The same logic can be expressed with a derived table:

```sql
SELECT
    order_id,
    customer_id,
    amount,
    customer_total
FROM (
    SELECT
        order_id,
        customer_id,
        amount,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS customer_total
    FROM orders
) AS order_metrics
WHERE customer_total >= :minimum_total;
```

CTEs are generally preferable when the intermediate stage has a meaningful name or is reused.

Derived tables can be concise for a single transformation.

## Choosing the Correct Query Level

A useful engineering rule is:

> Put each filter at the query level where it should affect the calculation.

For example:

```text
                    All orders
                        │
                tenant / security
                        │
                        ▼
                 Relevant tenant
                        │
                 business period
                        │
                        ▼
                Relevant period
                        │
                window aggregate
                        │
                        ▼
             Rows with calculated metric
                        │
                 presentation filter
                        │
                        ▼
                  API response
```

The question to ask is:

> Should this condition change the rows used by the aggregate, or should it only remove rows after the aggregate has been calculated?

That answer determines where the condition belongs.

## Production Example: SaaS Revenue Dashboard

Suppose a SaaS API needs:

- Monthly revenue.
- Customer monthly revenue.
- Cumulative customer revenue.
- Only display months with revenue above a threshold.

A structured query could be:

```sql
WITH monthly_customer_revenue AS (
    SELECT
        tenant_id,
        customer_id,
        DATE_TRUNC('month', paid_at) AS month,
        SUM(amount) AS monthly_revenue
    FROM payments
    WHERE tenant_id = :tenant_id
      AND paid_at >= :start_date
      AND paid_at < :end_date
      AND status = 'succeeded'
    GROUP BY
        tenant_id,
        customer_id,
        DATE_TRUNC('month', paid_at)
),
customer_metrics AS (
    SELECT
        tenant_id,
        customer_id,
        month,
        monthly_revenue,
        SUM(monthly_revenue) OVER (
            PARTITION BY tenant_id, customer_id
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_revenue
    FROM monthly_customer_revenue
)
SELECT
    tenant_id,
    customer_id,
    month,
    monthly_revenue,
    cumulative_revenue
FROM customer_metrics
WHERE monthly_revenue >= :minimum_monthly_revenue
ORDER BY
    customer_id,
    month;
```

The stages have clear responsibilities:

| Stage | Responsibility |
|---|---|
| `WHERE` | Tenant, date, and payment-status filtering |
| `GROUP BY` | Convert payments into monthly customer revenue |
| Window `SUM()` | Calculate cumulative revenue |
| Outer `WHERE` | Filter displayed months without changing cumulative history |
| Final `ORDER BY` | Control presentation order |

This structure makes the business semantics much easier to review and test.

## Performance Considerations

Window aggregate performance depends heavily on:

- Number of input rows.
- Number and size of partitions.
- Ordering requirements.
- Frame definitions.
- Existing indexes.
- Filter selectivity.
- Memory available to the database.
- Data distribution and skew.

For PostgreSQL, inspect:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    customer_id,
    order_id,
    amount,
    SUM(amount) OVER (
        PARTITION BY customer_id
        ORDER BY created_at, order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM orders
WHERE tenant_id = 42;
```

Pay particular attention to:

- `Sort` nodes.
- Sort methods and disk usage.
- Rows entering the window stage.
- Buffer reads.
- Execution time.
- Temporary I/O.
- Large partitions.

An index such as:

```sql
CREATE INDEX CONCURRENTLY idx_orders_tenant_customer_created_order
ON orders (
    tenant_id,
    customer_id,
    created_at,
    order_id
);
```

may help a workload combining tenant filtering, customer partitioning, and chronological processing.

The correct index depends on the complete workload, table size, selectivity, and PostgreSQL version. Always validate with real execution plans.

## Partition Skew

Partition size matters more than average partition size.

A system might contain:

```text
Customer A → 20 orders
Customer B → 15 orders
Customer C → 30 orders
Enterprise Customer → 50,000,000 orders
```

A window operation partitioned by customer may have a severe outlier.

Potential consequences include:

- High memory usage.
- Large sort operations.
- Temporary disk usage.
- Increased latency.
- Database resource contention.

For very large analytical partitions, consider:

- Restricting the time range.
- Pre-aggregating data.
- Materialized views.
- Reporting tables.
- Read replicas.
- Analytical warehouses.
- Incremental aggregation pipelines.

## Security and Tenant Isolation

Window partitioning is not a security mechanism.

For multi-tenant applications, tenant restrictions should be applied explicitly:

```sql
WHERE tenant_id = :tenant_id
```

and the partition should respect the tenant boundary where necessary:

```sql
PARTITION BY tenant_id, customer_id
```

This protects against accidentally mixing logically separate customer identities.

The application should use parameterized queries:

```python
cursor.execute(
    """
    SELECT
        customer_id,
        SUM(amount) OVER (
            PARTITION BY tenant_id, customer_id
        ) AS customer_total
    FROM orders
    WHERE tenant_id = %s
    """,
    [tenant_id],
)
```

Do not construct SQL using string interpolation.

For sensitive systems, tenant isolation should also be enforced through appropriate database permissions, row-level security, service-layer authorization, or other defense-in-depth controls.

## ORM Considerations

Django supports window expressions through `Window()`:

```python
from django.db.models import F, Sum, Window

orders = Order.objects.annotate(
    customer_total=Window(
        expression=Sum("amount"),
        partition_by=[F("customer_id")],
    )
)
```

If a subsequent business rule needs to filter on the window result, the ORM may generate additional SQL layers depending on the expression and Django version.

The important production practice is to inspect the generated SQL and execution plan rather than assuming ORM syntax maps to an optimal database operation.

For high-volume analytical queries:

- Test generated SQL directly.
- Use realistic production-scale data.
- Inspect `EXPLAIN`.
- Monitor query latency.
- Verify indexes.
- Avoid unnecessary columns.

## Common Mistakes

### Filtering at the Wrong Query Level

Incorrect:

```sql
SELECT
    order_id,
    SUM(amount) OVER (
        PARTITION BY customer_id
    ) AS lifetime_total
FROM orders
WHERE created_at >= :start_date;
```

if `lifetime_total` is intended to represent lifetime revenue.

The date filter changes the window input.

Correct:

```sql
WITH metrics AS (
    SELECT
        order_id,
        customer_id,
        created_at,
        SUM(amount) OVER (
            PARTITION BY customer_id
        ) AS lifetime_total
    FROM orders
)
SELECT
    order_id,
    customer_id,
    created_at,
    lifetime_total
FROM metrics
WHERE created_at >= :start_date;
```

### Treating `PARTITION BY` Like `GROUP BY`

`PARTITION BY` does not reduce the number of rows.

If you need one result per customer, use `GROUP BY` unless there is a specific reason to use another pattern.

### Adding `ORDER BY` Without Understanding Frames

This:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
    ORDER BY created_at
)
```

is not equivalent to:

```sql
SUM(amount) OVER (
    PARTITION BY customer_id
)
```

Ordered window semantics can produce cumulative behavior depending on the frame and database semantics.

Use an explicit frame when cumulative row-based behavior is required:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

### Using `HAVING` When the Aggregate Must See Filtered-Out Groups

`HAVING` removes groups before the window stage.

If a window calculation must include those groups, calculate the window value first and filter in an outer query.

### Assuming `LIMIT` Makes Window Aggregates Cheap

`LIMIT 20` limits the returned rows but does not necessarily limit the rows required to calculate the window value.

### Ignoring Ties in Window Ordering

Prefer:

```sql
ORDER BY created_at, order_id
```

over:

```sql
ORDER BY created_at
```

when timestamps are not unique and deterministic row ordering matters.

### Mixing Tenant Scope With Customer Scope

In multi-tenant systems, this can be dangerous:

```sql
PARTITION BY customer_id
```

when `customer_id` is only unique inside a tenant.

Prefer:

```sql
PARTITION BY tenant_id, customer_id
```

when tenant identity forms part of the business key.

### Assuming a CTE Always Materializes

A CTE is a query expression, not automatically a temporary table.

In PostgreSQL, many CTEs can be inlined. Use execution plans to understand actual behavior.

## Practical Decision Matrix

| Question | Preferred mechanism |
|---|---|
| Should rows be removed before the calculation? | `WHERE` |
| Should grouped rows be removed before window processing? | `HAVING` |
| Should rows be grouped into one row per business entity? | `GROUP BY` |
| Should every row receive a group-level metric? | `PARTITION BY` |
| Should the calculation follow a sequence? | `ORDER BY` inside `OVER()` |
| Should only a subset of ordered rows contribute? | Window frame |
| Should a window result itself be filtered? | Outer query or CTE |
| Should only the final returned rows be limited? | `LIMIT` |
| Should the calculation include rows hidden from the final result? | Calculate in an inner query, filter outside |
| Should repeated expensive aggregates be served frequently? | Consider pre-aggregation or caching |

## Production Checklist

Before shipping a query containing window aggregates:

- [ ] Is the required calculation based on the filtered or unfiltered dataset?
- [ ] Are `WHERE` predicates at the correct query level?
- [ ] Is `GROUP BY` required before the window calculation?
- [ ] Is `HAVING` accidentally removing rows needed by the window?
- [ ] Is `PARTITION BY` aligned with the actual business key?
- [ ] Are tenant boundaries explicit?
- [ ] Is `ORDER BY` required?
- [ ] Is the ordering deterministic?
- [ ] Is the window frame explicit when necessary?
- [ ] Does filtering the window result require an outer query?
- [ ] Does pagination accidentally hide the true computational cost?
- [ ] Have large and skewed partitions been tested?
- [ ] Has `EXPLAIN (ANALYZE, BUFFERS)` been reviewed?
- [ ] Are query parameters safely bound?
- [ ] Is pre-aggregation more appropriate for the workload?

## Interview Traps

| Interview question | Correct answer |
|---|---|
| Does `PARTITION BY` filter rows? | No. It divides rows into logical windows. |
| Does `PARTITION BY` behave like `GROUP BY`? | No. `GROUP BY` changes row granularity; window partitioning preserves rows. |
| Does `WHERE` affect a window aggregate? | Yes. Rows removed by `WHERE` are not visible to the window calculation at that query level. |
| Can a window function normally be used directly in `WHERE`? | No. Use an outer query or CTE. |
| Does `HAVING` execute before or after a window function? | Logically before the window stage. |
| What happens if `HAVING` removes a grouped row? | That row is not available to a subsequent window calculation. |
| Can a window function operate on grouped results? | Yes. Window functions can operate over the rows produced by `GROUP BY`. |
| Does `LIMIT` restrict the rows used by a window function? | Not generally. The window calculation logically occurs before the final limiting stage. |
| Why use a CTE around a window query? | To create a new query level where the window result can be filtered or further transformed. |
| Why add a tie-breaker to window `ORDER BY`? | To make row ordering deterministic when the primary ordering column contains duplicates. |
| Is a CTE always materialized in PostgreSQL? | No. Modern PostgreSQL can inline eligible CTEs. |
| Is `PARTITION BY` a physical PostgreSQL table partition? | No. It is a logical window definition. |
| What determines the rows contributing to an ordered aggregate? | The partition, ordering, and applicable window frame. |

## Key Takeaways

- **The most important window-selection rule is to place each filter at the query level where it should affect the calculation.**
- **`WHERE` and `HAVING` can change the rows visible to a subsequent window aggregate, while an outer query can filter the computed window result without changing its input.**
- **`PARTITION BY`, `ORDER BY`, and the window frame have separate responsibilities: group boundary, sequence, and calculation range.**
- **For production queries, deterministic ordering, explicit tenant boundaries, realistic partition sizes, and execution-plan analysis are essential.**
- **When live window computation becomes expensive at scale, move repeated analytical work toward pre-aggregation, materialized views, reporting tables, or other fit-for-purpose data paths.**