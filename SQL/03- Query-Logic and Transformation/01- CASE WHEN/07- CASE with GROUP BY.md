# 07- CASE with GROUP BY

## Overview

`CASE` and `GROUP BY` are commonly combined when a query needs to classify rows into business-defined categories and then aggregate those categories.

The key distinction is that `GROUP BY` determines **which rows belong to the same group**, while `CASE` determines **how values are classified or transformed**.

For example, an order system may store raw order amounts but report them as business-defined revenue bands:

```sql
SELECT
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS order_band,
    COUNT(*) AS order_count,
    SUM(amount) AS total_revenue
FROM orders
GROUP BY
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END;
```

The database conceptually performs:

```text
Rows
  ↓
Evaluate CASE
  ↓
Assign each row to a derived category
  ↓
GROUP BY category
  ↓
Aggregate each group
```

This pattern is useful for:

- Reporting
- Dashboards
- Operational analytics
- Customer segmentation
- Revenue analysis
- SLA reporting
- Status classification
- API metrics

## CASE as a Grouping Dimension

A `CASE` expression can create a derived grouping dimension without modifying the underlying table.

Consider:

```sql
SELECT
    CASE
        WHEN age < 18 THEN 'minor'
        WHEN age < 65 THEN 'adult'
        ELSE 'senior'
    END AS age_group,
    COUNT(*) AS customer_count
FROM customers
GROUP BY
    CASE
        WHEN age < 18 THEN 'minor'
        WHEN age < 65 THEN 'adult'
        ELSE 'senior'
    END;
```

The database does not physically create an `age_group` column. It evaluates the expression for the relevant rows and groups rows that produce the same result.

The result might be:

| age_group | customer_count |
| --- | ---: |
| minor | 120 |
| adult | 8,420 |
| senior | 1,130 |

This is useful when the grouping rule is derived from existing data rather than stored explicitly.

## Grouping by CASE Result

Some databases support referring to a `SELECT` alias in `GROUP BY`, but portability differs.

This form is widely portable:

```sql
SELECT
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS order_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END;
```

Some systems also allow:

```sql
SELECT
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS order_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY order_band;
```

Do not assume alias behavior is identical across SQL dialects. When writing portable SQL, repeating the expression or using a derived table is safer.

## Derived Table for Reusable Classification

Repeating a complex `CASE` expression can make a query difficult to maintain.

A derived table can calculate the classification once:

```sql
SELECT
    order_band,
    COUNT(*) AS order_count,
    SUM(amount) AS total_revenue
FROM (
    SELECT
        amount,
        CASE
            WHEN amount < 100 THEN 'low'
            WHEN amount < 1000 THEN 'medium'
            ELSE 'high'
        END AS order_band
    FROM orders
) AS classified_orders
GROUP BY order_band;
```

This separates two concerns:

```text
Inner query
    ↓
classify each order
    ↓
Outer query
    ↓
group and aggregate
```

For simple expressions, repeating the `CASE` may be perfectly reasonable. For complex transformations, a derived table or CTE can improve readability.

## CASE with Multiple Grouping Dimensions

`CASE` can be combined with ordinary columns.

For example:

```sql
SELECT
    tenant_id,
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS order_band,
    COUNT(*) AS order_count,
    SUM(amount) AS revenue
FROM orders
GROUP BY
    tenant_id,
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END;
```

The resulting groups are defined by the combination:

```text
tenant_id + order_band
```

So:

```text
Tenant A + low
Tenant A + medium
Tenant A + high

Tenant B + low
Tenant B + medium
Tenant B + high
```

This pattern is common in multi-tenant reporting.

## CASE with Status Groups

Suppose raw statuses are more detailed than the reporting categories.

```text
pending
processing
retrying
completed
cancelled
failed
```

A report may need:

```text
in_progress
successful
unsuccessful
```

SQL can perform the classification:

```sql
SELECT
    CASE
        WHEN status IN ('pending', 'processing', 'retrying')
            THEN 'in_progress'
        WHEN status = 'completed'
            THEN 'successful'
        WHEN status IN ('cancelled', 'failed')
            THEN 'unsuccessful'
        ELSE 'unknown'
    END AS status_group,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN status IN ('pending', 'processing', 'retrying')
            THEN 'in_progress'
        WHEN status = 'completed'
            THEN 'successful'
        WHEN status IN ('cancelled', 'failed')
            THEN 'unsuccessful'
        ELSE 'unknown'
    END;
```

This is particularly useful when the storage model contains operational states while the reporting model needs business categories.

## CASE with Aggregates After GROUP BY

`CASE` can also classify an aggregate result rather than define the grouping key.

For example:

```sql
SELECT
    tenant_id,
    COUNT(*) AS order_count,
    CASE
        WHEN COUNT(*) >= 10000 THEN 'large'
        WHEN COUNT(*) >= 1000 THEN 'medium'
        ELSE 'small'
    END AS tenant_size
FROM orders
GROUP BY tenant_id;
```

Here, the sequence is conceptually:

```text
orders
  ↓
GROUP BY tenant_id
  ↓
COUNT(*) per tenant
  ↓
CASE evaluates the count
  ↓
tenant_size
```

This is fundamentally different from:

```sql
GROUP BY
    CASE
        WHEN amount >= 1000 THEN 'high'
        ELSE 'low'
    END
```

In the first query, `CASE` classifies **groups**.

In the second query, `CASE` helps **create the groups**.

## CASE in GROUP BY vs CASE in SELECT

These two patterns solve different problems.

### CASE in GROUP BY

```sql
SELECT
    CASE
        WHEN amount >= 1000 THEN 'high'
        ELSE 'low'
    END AS amount_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN amount >= 1000 THEN 'high'
        ELSE 'low'
    END;
```

Purpose:

> Create groups based on a derived condition.

### CASE in SELECT with an Aggregate

```sql
SELECT
    tenant_id,
    COUNT(*) AS order_count,
    CASE
        WHEN COUNT(*) >= 1000 THEN 'high_volume'
        ELSE 'normal_volume'
    END AS volume_category
FROM orders
GROUP BY tenant_id;
```

Purpose:

> Calculate groups first, then classify each group.

Understanding this distinction prevents many reporting-query mistakes.

## Conditional Aggregation with GROUP BY

`CASE` can also remain inside aggregate expressions while another column provides the grouping key.

```sql
SELECT
    tenant_id,
    SUM(
        CASE
            WHEN status = 'completed' THEN amount
            ELSE 0
        END
    ) AS completed_revenue,
    SUM(
        CASE
            WHEN status = 'failed' THEN amount
            ELSE 0
        END
    ) AS failed_amount
FROM orders
GROUP BY tenant_id;
```

Here:

- `tenant_id` defines the groups.
- Each `CASE` defines which rows contribute to each metric.
- `SUM` aggregates the values within each tenant.

This is one of the most important production patterns involving `CASE` and `GROUP BY`.

## GROUP BY with Conditional Counts

A dashboard may require status counts per tenant:

```sql
SELECT
    tenant_id,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
FROM orders
GROUP BY tenant_id;
```

In PostgreSQL, the same query can be expressed using `FILTER`:

```sql
SELECT
    tenant_id,
    COUNT(*) FILTER (WHERE status = 'pending') AS pending_count,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_count,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_count
FROM orders
GROUP BY tenant_id;
```

The latter can be easier to read when the query contains many conditional metrics.

## Grouping by Ranges

A common reporting requirement is grouping numerical values into ranges.

```sql
SELECT
    CASE
        WHEN amount < 100 THEN '<100'
        WHEN amount < 500 THEN '100-499'
        WHEN amount < 1000 THEN '500-999'
        WHEN amount < 5000 THEN '1000-4999'
        ELSE '5000+'
    END AS amount_range,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN amount < 100 THEN '<100'
        WHEN amount < 500 THEN '100-499'
        WHEN amount < 1000 THEN '500-999'
        WHEN amount < 5000 THEN '1000-4999'
        ELSE '5000+'
    END;
```

The ordering of the conditions matters.

Because the first matching branch wins:

```text
amount < 100
       ↓ no
amount < 500
       ↓ no
amount < 1000
       ↓ yes
"500-999"
```

A poorly ordered `CASE` can place rows into incorrect groups.

## NULL and GROUP BY

`NULL` requires deliberate handling.

Consider:

```sql
SELECT
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS amount_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END;
```

A `NULL` amount does not satisfy either comparison, so it reaches `ELSE 'high'`.

That may be incorrect.

If `NULL` means the amount is unavailable:

```sql
SELECT
    CASE
        WHEN amount IS NULL THEN 'unknown'
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS amount_band,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN amount IS NULL THEN 'unknown'
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END;
```

A senior-level SQL review should always ask what `NULL` means in the domain.

## NULL Grouping Behavior

When a `CASE` expression itself returns `NULL`, rows producing `NULL` belong to the same SQL group.

For example:

```sql
SELECT
    CASE
        WHEN status = 'completed' THEN 'completed'
    END AS category,
    COUNT(*) AS row_count
FROM orders
GROUP BY
    CASE
        WHEN status = 'completed' THEN 'completed'
    END;
```

Non-completed rows produce `NULL` and therefore form a `NULL` group.

If the report should explicitly label them:

```sql
CASE
    WHEN status = 'completed' THEN 'completed'
    ELSE 'other'
END
```

Use the explicit category.

## WHERE vs HAVING with CASE

`WHERE` filters rows before grouping.

`HAVING` filters groups after aggregation.

For example:

```sql
SELECT
    tenant_id,
    COUNT(*) AS completed_orders
FROM orders
WHERE status = 'completed'
GROUP BY tenant_id
HAVING COUNT(*) >= 100;
```

The execution concept is:

```text
WHERE
  ↓
select completed rows
  ↓
GROUP BY
  ↓
count per tenant
  ↓
HAVING
  ↓
retain tenants with >= 100
```

A `CASE` can classify the resulting groups:

```sql
SELECT
    tenant_id,
    COUNT(*) AS completed_orders,
    CASE
        WHEN COUNT(*) >= 1000 THEN 'high'
        WHEN COUNT(*) >= 100 THEN 'medium'
        ELSE 'low'
    END AS volume_band
FROM orders
WHERE status = 'completed'
GROUP BY tenant_id;
```

## CASE with Date-Based Groups

Date classification is common in operational reporting.

For example:

```sql
SELECT
    CASE
        WHEN created_at >= CURRENT_DATE THEN 'today'
        WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 'last_7_days'
        WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 'last_30_days'
        ELSE 'older'
    END AS age_bucket,
    COUNT(*) AS order_count
FROM orders
GROUP BY
    CASE
        WHEN created_at >= CURRENT_DATE THEN 'today'
        WHEN created_at >= CURRENT_DATE - INTERVAL '7 days' THEN 'last_7_days'
        WHEN created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 'last_30_days'
        ELSE 'older'
    END;
```

The ranges overlap mathematically, but the first-match behavior makes them effectively exclusive.

The ordering must therefore go from the most specific or recent boundary toward the broader boundaries.

For production analytics, explicit half-open intervals are often easier to reason about when exact reporting boundaries matter.

## Performance Considerations

A `CASE` used in `GROUP BY` can affect query performance because the database must evaluate the expression for rows participating in grouping.

For example:

```sql
GROUP BY
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END
```

may require the database to:

1. Read qualifying rows.
2. Evaluate the `CASE`.
3. Build grouping state.
4. Aggregate each group.

For large datasets, inspect the execution plan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END AS amount_band,
    COUNT(*)
FROM orders
GROUP BY
    CASE
        WHEN amount < 100 THEN 'low'
        WHEN amount < 1000 THEN 'medium'
        ELSE 'high'
    END;
```

Do not assume that adding an index on `amount` will automatically eliminate the grouping cost. The optimizer chooses a plan based on cardinality, selectivity, available indexes, table statistics, and database engine behavior.

For stable, heavily queried classifications, consider whether the derived dimension should become part of the data model or reporting pipeline.

## Data-Driven Classification

Large `CASE` expressions can become a maintenance problem.

Avoid turning SQL into a hard-coded rule engine:

```sql
CASE
    WHEN country = 'IN' AND amount > 1000 AND ...
        THEN 'tier_a'
    WHEN country = 'US' AND amount > 500 AND ...
        THEN 'tier_b'
    ...
END
```

When business rules are configuration data, consider a mapping or rule table.

For example:

```text
pricing_tiers
-------------
tier
minimum_amount
maximum_amount
```

Then the classification can be represented through relational data rather than repeatedly deployed SQL code.

This provides better:

- Change management
- Auditability
- Testing
- Administrative control
- Versioning

However, dynamic rule systems introduce their own complexity. Use them when the rules genuinely need to be data-driven.

## Production Example: Tenant Order Dashboard

A backend API might need a per-tenant order dashboard.

A PostgreSQL query could calculate several metrics together:

```sql
SELECT
    tenant_id,

    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE status = 'completed'
    ) AS completed_orders,

    COUNT(*) FILTER (
        WHERE status = 'failed'
    ) AS failed_orders,

    COALESCE(
        SUM(amount) FILTER (
            WHERE status = 'completed'
        ),
        0
    ) AS completed_revenue,

    CASE
        WHEN COUNT(*) >= 10000 THEN 'high_volume'
        WHEN COUNT(*) >= 1000 THEN 'medium_volume'
        ELSE 'low_volume'
    END AS volume_band

FROM orders
WHERE tenant_id = $1
  AND created_at >= $2
  AND created_at < $3
GROUP BY tenant_id;
```

This combines three levels of logic:

- `WHERE` defines the authorized and time-bounded input set.
- Aggregates calculate tenant-level metrics.
- `CASE` classifies the resulting tenant group.

The application should consume the aggregate result directly rather than loading all matching orders into Python.

## ORM Considerations

Django's ORM can express grouping and conditional aggregation, but complex reporting queries should still be reviewed as SQL.

For example:

```python
from django.db.models import Count, Q, Sum

metrics = (
    Order.objects
    .filter(
        tenant_id=tenant_id,
        created_at__gte=start,
        created_at__lt=end,
    )
    .values("tenant_id")
    .annotate(
        total_orders=Count("id"),
        completed_orders=Count(
            "id",
            filter=Q(status="completed"),
        ),
        completed_revenue=Sum(
            "amount",
            filter=Q(status="completed"),
        ),
    )
)
```

The important engineering principle is not whether the query is written with raw SQL or an ORM.

The important questions are:

- What SQL is generated?
- Which rows are scanned?
- Is tenant isolation enforced?
- Are joins multiplying rows?
- Are `NULL` values handled correctly?
- Is the query latency acceptable at production scale?

Use query logging and `EXPLAIN` when a reporting query becomes performance-sensitive.

## Scalability Considerations

For large analytical workloads, repeatedly calculating complex classifications over billions of transactional rows may become expensive.

Potential strategies include:

- Pre-aggregated reporting tables
- Materialized views
- Incremental aggregation
- Data warehouses
- Event-driven analytics pipelines
- Partitioning
- Carefully designed indexes

For example:

```text
Transactional database
        ↓
Orders
        ↓
CDC / Kafka / ETL
        ↓
Analytics storage
        ↓
Dashboard aggregations
```

The right architecture depends on freshness requirements and workload.

Do not move every `GROUP BY` query into Kafka or a warehouse prematurely. A well-indexed PostgreSQL query over an appropriate time window may be sufficient.

## Reliability and Consistency

Reporting queries can produce surprising results when the underlying data changes during execution or when related services use different definitions.

For example, if one service defines:

```text
completed = status = 'completed'
```

while another defines:

```text
completed = status IN ('completed', 'settled')
```

their metrics will diverge.

Centralize important domain definitions where practical.

For high-value financial or operational reporting:

- Define metric semantics explicitly.
- Test boundary conditions.
- Test `NULL` behavior.
- Test empty datasets.
- Test unknown statuses.
- Use consistent time-zone rules.
- Validate aggregate results against known fixtures.

## Security Considerations

`GROUP BY` does not provide authorization.

A query such as:

```sql
SELECT
    tenant_id,
    COUNT(*)
FROM orders
GROUP BY tenant_id;
```

can expose information about every tenant if the caller is not authorized to access it.

Apply authorization constraints before aggregation:

```sql
SELECT
    tenant_id,
    COUNT(*) AS order_count
FROM orders
WHERE tenant_id = $1
GROUP BY tenant_id;
```

Use parameterized queries and avoid constructing SQL from untrusted category or column names.

For multi-tenant PostgreSQL systems, Row-Level Security can provide an additional database-level isolation boundary.

## Common Mistakes

### Grouping by a Different Expression Than the Selected CASE

This is incorrect if the intention is to group by the displayed classification:

```sql
SELECT
    CASE
        WHEN amount < 100 THEN 'low'
        ELSE 'high'
    END AS amount_band,
    COUNT(*)
FROM orders
GROUP BY
    amount;
```

The grouping is by exact `amount`, not by `amount_band`.

Group by the same classification:

```sql
GROUP BY
    CASE
        WHEN amount < 100 THEN 'low'
        ELSE 'high'
    END
```

### Overlapping Business Rules

This:

```sql
CASE
    WHEN amount < 1000 THEN 'medium'
    WHEN amount < 100 THEN 'low'
    ELSE 'high'
END
```

never reaches the `'low'` branch.

Amounts below `100` also satisfy `amount < 1000`.

Put more specific conditions first:

```sql
CASE
    WHEN amount < 100 THEN 'low'
    WHEN amount < 1000 THEN 'medium'
    ELSE 'high'
END
```

### Treating NULL as a Normal Category Accidentally

This:

```sql
CASE
    WHEN amount < 100 THEN 'low'
    ELSE 'high'
END
```

classifies `NULL` amounts as `'high'`.

If that is not intended, handle `NULL` explicitly.

### Using GROUP BY When a Simple WHERE Is Enough

If the requirement is simply:

> Count completed orders.

This is unnecessary:

```sql
SELECT
    CASE
        WHEN status = 'completed' THEN 'completed'
        ELSE 'other'
    END AS category,
    COUNT(*)
FROM orders
GROUP BY
    CASE
        WHEN status = 'completed' THEN 'completed'
        ELSE 'other'
    END;
```

If only completed orders are required:

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'completed';
```

Do not introduce derived grouping when the business requirement does not need it.

### Forgetting That Grouping Happens Before Final SELECT Classification

A query such as:

```sql
SELECT
    tenant_id,
    CASE
        WHEN COUNT(*) > 100 THEN 'large'
        ELSE 'small'
    END AS category
FROM orders
GROUP BY tenant_id;
```

classifies tenant groups.

It does not classify individual orders.

### Hard-Coding Large Rule Sets

A huge `CASE` inside `GROUP BY` can become a deployment and maintenance problem.

If the classification rules change frequently, consider whether they belong in a configuration or reference table.

### Ignoring Empty Groups

A query over existing rows cannot naturally produce categories with zero rows unless those categories are supplied separately.

For example, grouping orders by status will not automatically return:

```text
pending   0
completed 0
failed    0
```

for statuses with no matching rows.

If a dashboard requires all categories, including zero-count categories, generate the category set explicitly and use an appropriate join strategy.

## Interview Traps

| Question | Correct Reasoning |
| --- | --- |
| Can `CASE` be used in `GROUP BY`? | Yes; it can create a derived grouping dimension |
| What does `CASE` in `GROUP BY` do? | It classifies rows before grouping |
| What does `CASE` around `COUNT(*)` do? | It classifies the already aggregated group |
| Why must overlapping `CASE` conditions be ordered carefully? | The first matching `WHEN` wins |
| What happens when a `CASE` returns `NULL`? | Rows producing `NULL` belong to the same `NULL` group |
| Does `GROUP BY` provide authorization? | No; authorization predicates must still restrict the input rows |
| Why use `CASE` with `GROUP BY`? | To create business-defined groups from raw data |
| When is `GROUP BY status` better than `CASE`? | When the stored categories are already the desired reporting categories or are dynamically changing |
| Can a `SELECT` alias always be used in `GROUP BY`? | No; alias support differs by SQL dialect |
| Why use a derived table or CTE? | To separate classification from aggregation and avoid repeating complex expressions |
| Does an index automatically make `GROUP BY CASE` fast? | No; grouping cost depends on the execution plan and data distribution |
| What is the difference between `WHERE` and `HAVING`? | `WHERE` filters rows before grouping; `HAVING` filters groups after aggregation |

## Key Takeaways

- `CASE` in `GROUP BY` creates derived business categories, while `CASE` around aggregates classifies already-formed groups.
- The first matching `WHEN` wins, so overlapping ranges must be ordered from the most specific condition to the broader condition.
- Treat `NULL` explicitly when it has domain meaning; otherwise a broad `ELSE` branch can silently place missing values into the wrong group.
- Use conditional aggregation when the grouping dimension is separate from the metric conditions, and avoid unnecessary grouping when a simple `WHERE` predicate is sufficient.
- For production reporting, validate generated SQL, authorization boundaries, `NULL` and empty-set semantics, execution plans, and whether complex classifications should become data-driven or pre-aggregated.