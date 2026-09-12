# 06- Sum Mean Median

## Overview

`sum()`, `mean()`, and `median()` are core Pandas aggregation operations for calculating totals and measures of central tendency.

They are commonly used for:

```text
financial reporting
customer analytics
operational metrics
ETL pipelines
data-quality checks
business dashboards
```

The three operations answer different questions:

```text
sum
→ What is the total?

mean
→ What is the arithmetic average?

median
→ What is the middle observation?
```

The choice between them is not merely statistical. It affects business interpretation.

For example, in an e-commerce dataset:

```text
sum
    → total revenue

mean
    → average order value

median
    → typical order value when extreme orders exist
```

Production correctness depends on:

```text
correct population
+
correct data grain
+
valid dtype
+
missing-value semantics
+
duplicate handling
+
unit and currency consistency
```

---

## Example Dataset

```python
import pandas as pd


orders = pd.DataFrame(
    {
        "order_id": [1001, 1002, 1003, 1004, 1005],
        "customer_id": [101, 102, 101, 103, 102],
        "revenue": [
            100.0,
            250.0,
            300.0,
            50.0,
            5000.0,
        ],
        "status": [
            "completed",
            "completed",
            "completed",
            "failed",
            "completed",
        ],
    }
)
```

For a completed-order report:

```python
completed_orders = orders.loc[
    orders["status"].eq("completed")
].copy()
```

The statistical population is now explicitly defined.

---

## `sum()`

`sum()` adds values across a Series or DataFrame.

Example:

```python
total_revenue = completed_orders[
    "revenue"
].sum()
```

For:

```text
100
250
300
5000
```

the total is:

```text
5650
```

Use `sum()` when the metric is additive and the rows represent distinct contributions to the total.

Typical examples:

```text
revenue
transaction amounts
units sold
storage consumed
bytes transferred
hours worked
```

---

## Why `sum()` Matters

A sum is often the primary business metric.

For example:

```python
daily_revenue = (
    completed_orders["revenue"]
    .sum()
)
```

can represent:

```text
revenue generated during the reporting period
```

But a sum is only meaningful when:

```text
rows are at the correct grain
+
duplicates are controlled
+
units are consistent
+
population is correct
```

A duplicated transaction can directly inflate the result.

---

## `sum()` and Missing Values

Pandas generally skips missing values during `sum()`.

Example:

```python
values = pd.Series(
    [100.0, 200.0, None]
)

total = values.sum()
```

This produces the sum of available numeric values.

When completeness matters, check nulls separately:

```python
missing_rate = (
    values.isna().mean()
)
```

A total calculated from incomplete data should not automatically be treated as fully reliable.

---

## `min_count`

For strict missing-data semantics, `sum()` supports `min_count`.

Example:

```python
values = pd.Series(
    [None, None]
)

result = values.sum(
    min_count=1
)
```

Instead of interpreting no observations as zero, this can preserve the distinction between:

```text
no valid values
```

and:

```text
total = 0
```

This is particularly useful in production reporting where zero and missing have different business meanings.

---

## Sum of an Empty Series

By default, an empty numeric Series can produce:

```python
empty = pd.Series(
    dtype="float64"
)

result = empty.sum()
```

which yields:

```text
0.0
```

That may be technically convenient but not always semantically correct.

For reporting systems, consider:

```python
result = empty.sum(
    min_count=1
)
```

when:

```text
no observations
```

should remain distinguishable from:

```text
zero observed value
```

---

## Grouped Sum

For customer-level revenue:

```python
customer_revenue = (
    completed_orders
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        total_revenue=(
            "revenue",
            "sum",
        )
    )
)
```

The output grain is:

```text
one row = one customer
```

This is different from:

```python
completed_orders["revenue"].sum()
```

which produces one global value.

Always identify the aggregation grain before interpreting the result.

---

## `mean()`

`mean()` calculates the arithmetic average:

```python
average_revenue = completed_orders[
    "revenue"
].mean()
```

Conceptually:

```text
mean = total of observations / number of observations
```

For:

```text
100
250
300
5000
```

the mean is:

```text
1412.5
```

The large `5000` transaction pulls the average substantially upward.

---

## When to Use Mean

Use `mean()` when:

```text
every observation should contribute proportionally
+
the arithmetic average is meaningful
```

Typical applications:

```text
average order value
average processing time
average transaction amount
average CPU usage
average daily sales
```

Mean is especially useful when the distribution is reasonably balanced or when the business specifically defines the metric as an arithmetic average.

---

## Mean and Outliers

The mean is sensitive to extreme values.

Example:

```text
100
110
120
130
10000
```

The mean is heavily influenced by:

```text
10000
```

while the median remains close to the typical observations.

For operational analysis, calculate both when skew is plausible:

```python
summary = {
    "mean": completed_orders["revenue"].mean(),
    "median": completed_orders["revenue"].median(),
}
```

A large mean/median difference is often a signal worth investigating.

---

## `median()`

`median()` returns the middle value of the ordered observations.

Example:

```python
median_revenue = completed_orders[
    "revenue"
].median()
```

For an odd number of observations:

```text
100
200
300
```

the median is:

```text
200
```

For an even number:

```text
100
200
300
400
```

the median is the average of the two middle values:

```text
250
```

---

## Why Median Exists

Median is useful when the distribution is skewed or contains large outliers.

Examples:

```text
API latency
customer spending
order value
salary-like measurements
processing time
```

For latency:

```text
20 ms
25 ms
28 ms
30 ms
3000 ms
```

the mean can become heavily influenced by the extreme request, while the median better reflects the typical observation.

---

## Mean Versus Median

| Property | Mean | Median |
| --- | --- | --- |
| Uses all numeric values | Yes | Uses ordered position |
| Sensitive to outliers | High | Lower |
| Easy arithmetic interpretation | Yes | Yes |
| Useful for skewed distributions | Sometimes | Often |
| Same unit as input | Yes | Yes |
| Common for additive business totals | No | No |
| Common for typical-observation reporting | Yes | Yes |

Do not treat median as universally better.

The correct measure depends on the question.

---

## Sum Versus Mean Versus Median

| Operation | Answers | Example |
| --- | --- | --- |
| `sum()` | What is the total? | Total revenue |
| `mean()` | What is the arithmetic average? | Average order value |
| `median()` | What is the central observation? | Typical order value |

These metrics describe different properties of the same population.

For example:

```python
metrics = {
    "total": orders["revenue"].sum(),
    "mean": orders["revenue"].mean(),
    "median": orders["revenue"].median(),
}
```

A report may legitimately expose all three.

---

## Missing Values

All three operations need an explicit missing-data policy.

Example:

```python
values = pd.Series(
    [100.0, 200.0, None, 400.0]
)

total = values.sum()
average = values.mean()
median = values.median()
```

Pandas normally excludes the missing value from these calculations.

This does not mean missing data is harmless.

Measure completeness separately:

```python
missing_count = values.isna().sum()

missing_rate = (
    values.isna().mean()
)
```

---

## `skipna`

Many Pandas reduction operations support `skipna`.

For example:

```python
average = values.mean(
    skipna=True
)
```

If missing values should invalidate the metric rather than be ignored, use an explicit validation step or appropriate logic instead of assuming the default semantics match the business requirement.

For production code, make missing-data policy visible in the surrounding pipeline.

---

## Missing Versus Zero

Consider:

```text
customer_id | revenue
------------|--------
101         | 500
102         | NaN
103         | 0
```

These can mean three different things:

```text
500
→ actual revenue

NaN
→ unavailable / missing

0
→ known zero revenue
```

Do not convert:

```python
NaN → 0
```

unless the business model explicitly defines missing as zero.

This distinction affects:

```text
sum
mean
median
reporting
data-quality metrics
```

---

## Numeric Dtypes

Convert external numeric data before aggregation:

```python
orders["revenue"] = pd.to_numeric(
    orders["revenue"],
    errors="coerce",
)
```

Then validate conversion:

```python
invalid_revenue = orders.loc[
    orders["revenue"].isna()
    & orders["status"].eq("completed")
]

if not invalid_revenue.empty:
    raise ValueError(
        "Completed orders contain invalid revenue values."
    )
```

Do not rely on automatic coercion when invalid financial values should fail the pipeline.

---

## String Numbers

A source may provide:

```text
"100.00"
"250.00"
"5000.00"
```

as strings.

Normalize:

```python
orders["revenue"] = pd.to_numeric(
    orders["revenue"],
    errors="raise",
)
```

Using:

```python
errors="raise"
```

is often preferable for strict production pipelines because malformed values immediately surface.

Use coercion when the pipeline explicitly handles invalid values separately.

---

## Duplicate Records

Duplicates can directly corrupt all three metrics.

Suppose:

```text
transaction_id | amount
---------------|-------
1001           | 500
1001           | 500
```

If the duplicate is accidental:

```python
transactions["transaction_id"].duplicated().any()
```

should trigger a validation failure or deterministic deduplication process.

Otherwise:

```python
transactions["amount"].sum()
```

will include the same transaction twice.

---

## Duplicate Keys After Joins

An even more dangerous pattern is:

```text
transactions
    ↓
many-to-many join
    ↓
row multiplication
    ↓
sum / mean / median
```

Example:

```python
enriched = transactions.merge(
    customers,
    on="customer_id",
    how="left",
)
```

Use validation:

```python
enriched = transactions.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
```

This prevents duplicate lookup records from silently inflating downstream metrics.

---

## Aggregation Grain

Suppose:

```text
orders
one row = one order
```

and the requirement is:

```text
average revenue per customer
```

First aggregate by customer:

```python
customer_totals = (
    orders
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        total_revenue=(
            "revenue",
            "sum",
        )
    )
)

average_customer_revenue = (
    customer_totals["total_revenue"]
    .mean()
)
```

This is different from:

```python
orders["revenue"].mean()
```

because the latter calculates:

```text
average order value
```

not:

```text
average customer revenue
```

This distinction is fundamental.

---

## Weighted Versus Unweighted Mean

Suppose customers have different numbers of orders.

A simple mean of order values:

```python
orders["revenue"].mean()
```

weights every order equally.

An average of customer totals:

```python
customer_totals["total_revenue"].mean()
```

weights every customer equally.

These answer different questions:

```text
average order value
```

versus:

```text
average customer spend
```

Do not calculate a grouped metric by habit without defining the unit being averaged.

---

## Mean of Means

Avoid blindly averaging subgroup means:

```python
regional_means = (
    orders
    .groupby("region")["revenue"]
    .mean()
)

incorrect_global_mean = (
    regional_means.mean()
)
```

This gives each region equal weight regardless of how many orders it contains.

A true global mean should be calculated from the underlying observations:

```python
correct_global_mean = orders[
    "revenue"
].mean()
```

Or from sufficient statistics:

```text
global mean
=
sum of all values
/
count of all values
```

This is an important aggregation trap.

---

## Grouped Mean

For average order value by region:

```python
regional_average = (
    orders
    .groupby(
        "region",
        as_index=False,
    )
    .agg(
        average_order_value=(
            "revenue",
            "mean",
        )
    )
)
```

The output grain is:

```text
one row = one region
```

Group-level means should always be interpreted in the context of group size.

---

## Grouped Median

For median transaction value by region:

```python
regional_median = (
    orders
    .groupby(
        "region",
        as_index=False,
    )
    .agg(
        median_order_value=(
            "revenue",
            "median",
        )
    )
)
```

This is useful when distributions differ significantly between regions.

A region with:

```text
10 transactions
```

and a region with:

```text
1,000,000 transactions
```

should not be interpreted as equally statistically reliable without considering sample size.

---

## Sum With Negative Values

Financial datasets can legitimately contain negative values:

```text
sale       +500
refund     -100
chargeback  -50
```

Then:

```python
net_revenue = transactions[
    "amount"
].sum()
```

may correctly calculate:

```text
350
```

Do not reject negative values automatically.

The validation rule should depend on the metric's business definition.

---

## Currency Consistency

Never combine:

```text
USD
EUR
INR
```

directly:

```python
orders["revenue"].sum()
```

if the values use different currencies.

Normalize first:

```text
source currencies
    ↓
exchange-rate conversion
    ↓
reporting currency
    ↓
sum / mean / median
```

Otherwise the resulting statistic has no coherent financial interpretation.

---

## Unit Consistency

The same principle applies to operational measurements.

Do not calculate:

```python
latency.mean()
```

when some values are:

```text
milliseconds
```

and others:

```text
seconds
```

Normalize units before aggregation.

The statistical operation cannot correct a unit mismatch.

---

## Time Windows

Always define the reporting window.

Example:

```python
monthly_orders = orders.loc[
    orders["created_at"].between(
        "2026-09-01",
        "2026-09-30 23:59:59",
    )
].copy()
```

Then:

```python
monthly_revenue = (
    monthly_orders["revenue"]
    .sum()
)
```

Production systems should also define:

```text
timezone
inclusive/exclusive boundaries
late-arriving records
snapshot timestamp
```

---

## `sum()`, `mean()`, and `median()` After Filtering

Filtering changes the statistical population.

Example:

```python
completed = orders.loc[
    orders["status"].eq("completed")
]

average_completed = completed[
    "revenue"
].mean()
```

This is not the same as:

```python
orders["revenue"].mean()
```

The first excludes failed orders.

The population definition should be explicit in business reports.

---

## Data Flow

A production statistical pipeline typically follows:

```mermaid
flowchart LR
    Source[PostgreSQL / API / CSV / Parquet] --> Ingest[Ingest]
    Ingest --> Schema[Validate Schema and Dtypes]
    Schema --> Quality[Validate Nulls and Duplicates]
    Quality --> Scope[Filter Reporting Population]
    Scope --> Grain[Establish Aggregation Grain]
    Grain --> Stats[Calculate Sum / Mean / Median]
    Stats --> Verify[Validate Metrics]
    Verify --> Publish[Report / API / Parquet]
```

The important ordering is:

```text
validate
→ scope
→ define grain
→ aggregate
→ verify
→ publish
```

---

## SQL Equivalents

Pandas:

```python
total = orders["revenue"].sum()
average = orders["revenue"].mean()
median = orders["revenue"].median()
```

SQL equivalents are conceptually:

```sql
SELECT
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS average_revenue
FROM orders;
```

Median is database-specific. PostgreSQL can calculate it with an ordered-set aggregate:

```sql
SELECT
    PERCENTILE_CONT(0.5)
    WITHIN GROUP (
        ORDER BY revenue
    ) AS median_revenue
FROM orders;
```

For large datasets, database-side aggregation is often preferable.

---

## PostgreSQL Grouped Example

```sql
SELECT
    customer_id,
    SUM(revenue) AS total_revenue,
    AVG(revenue) AS average_order_value,
    PERCENTILE_CONT(0.5)
        WITHIN GROUP (
            ORDER BY revenue
        ) AS median_order_value
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

This lets PostgreSQL reduce a large transaction table before Pandas receives the result.

---

## Database Pushdown

When the underlying data is already in PostgreSQL:

```text
millions of orders
    ↓
database filtering
    ↓
database aggregation
    ↓
small customer report
    ↓
Pandas
```

is often preferable to:

```text
millions of orders
    ↓
Pandas
    ↓
filter + group + aggregate
```

Pushdown can reduce:

```text
network traffic
Pandas memory consumption
processing time
worker cost
```

---

## API Data

For REST API responses:

```python
transactions = pd.DataFrame(
    response["items"]
)

transactions["amount"] = pd.to_numeric(
    transactions["amount"],
    errors="raise",
)

total_amount = transactions[
    "amount"
].sum()
```

Treat remote values as untrusted input.

Validate:

```text
schema
dtype
missing values
units
currency
duplicates
```

before exposing aggregate metrics.

---

## Parquet Workflow

For Parquet-backed processing:

```python
orders = pd.read_parquet(
    "input/orders.parquet",
    columns=[
        "order_id",
        "customer_id",
        "revenue",
        "status",
    ],
)
```

Then:

```python
completed = orders.loc[
    orders["status"].eq("completed")
]

stats = completed[
    "revenue"
].agg(
    [
        "sum",
        "mean",
        "median",
    ]
)
```

Reading only required columns reduces I/O and memory consumption.

---

## Performance Considerations

`sum()` and `mean()` are generally efficient reductions over a Series.

`median()` can be more computationally demanding because determining a median requires order-statistic processing.

The practical considerations are:

```text
row count
dtype
missing values
group count
memory
number of repeated calculations
```

Do not repeatedly calculate the same large-data statistics when a combined aggregation or database-side computation is more appropriate.

---

## Combined Aggregation

Instead of:

```python
total = orders["revenue"].sum()
average = orders["revenue"].mean()
median = orders["revenue"].median()
```

you can express the statistics together:

```python
stats = orders[
    "revenue"
].agg(
    [
        "sum",
        "mean",
        "median",
    ]
)
```

This is often clearer when the metrics form a single reporting unit.

For named output:

```python
summary = orders.agg(
    total_revenue=(
        "revenue",
        "sum",
    ),
    average_revenue=(
        "revenue",
        "mean",
    ),
    median_revenue=(
        "revenue",
        "median",
    ),
)
```

Use an explicit structure when the resulting schema is part of an API or report contract.

---

## Incremental Processing

Some aggregations can be safely combined across batches.

For `sum`:

```text
global sum
=
sum of batch sums
```

For `mean`, retain sufficient statistics:

```text
global mean
=
total sum across batches
/
total count across batches
```

Do not average batch means unless batch sizes are equal or weighted correctly.

For example:

```python
global_sum = (
    batch_1["amount"].sum()
    + batch_2["amount"].sum()
)

global_count = (
    batch_1["amount"].count()
    + batch_2["amount"].count()
)

global_mean = (
    global_sum
    / global_count
)
```

Exact median is not generally reconstructible from simple batch medians alone.

---

## Large Dataset Strategy

For very large datasets:

```text
sum
mean
    → easy to push down or combine incrementally

median
    → may require more expensive processing
```

If exact median is required at scale, consider:

```text
PostgreSQL
data warehouse
Spark
DuckDB
specialized percentile algorithms
```

depending on the workload.

Pandas is appropriate when the relevant working set fits comfortably in memory.

---

## Empty Data and No Observations

Production reports should define behavior for:

```text
zero rows
```

Example:

```python
completed_orders = orders.loc[
    orders["status"].eq("completed")
]

if completed_orders.empty:
    raise ValueError(
        "No completed orders found for reporting period."
    )
```

Whether an empty population should:

```text
return no report
return zero
return null
raise an error
```

is a business decision.

Do not let Pandas' default reduction behavior decide it accidentally.

---

## Testing `sum()`, `mean()`, and `median()`

```python
import pandas as pd
import pytest


def test_order_statistics() -> None:
    revenue = pd.Series(
        [100.0, 200.0, 300.0]
    )

    assert revenue.sum() == pytest.approx(
        600.0
    )

    assert revenue.mean() == pytest.approx(
        200.0
    )

    assert revenue.median() == pytest.approx(
        200.0
    )
```

Use approximate comparisons where floating-point behavior makes exact equality inappropriate.

---

## Testing Missing Values

```python
def test_statistics_ignore_missing_values() -> None:
    revenue = pd.Series(
        [100.0, None, 300.0]
    )

    assert revenue.sum() == pytest.approx(
        400.0
    )

    assert revenue.mean() == pytest.approx(
        200.0
    )

    assert revenue.median() == pytest.approx(
        200.0
    )
```

Also test the missing-data policy separately.

---

## Testing Median Resistance to Outliers

```python
def test_median_is_less_affected_by_outlier() -> None:
    revenue = pd.Series(
        [100.0, 110.0, 120.0, 130.0, 10_000.0]
    )

    assert revenue.median() == pytest.approx(
        120.0
    )

    assert revenue.mean() > (
        revenue.median() * 10
    )
```

This validates the intended analytical distinction rather than merely checking method execution.

---

## Testing Aggregation Grain

```python
def test_average_customer_revenue() -> None:
    orders = pd.DataFrame(
        {
            "customer_id": [101, 101, 102],
            "revenue": [
                100.0,
                300.0,
                500.0,
            ],
        }
    )

    customer_totals = (
        orders
        .groupby(
            "customer_id",
            as_index=False,
        )
        .agg(
            total_revenue=(
                "revenue",
                "sum",
            )
        )
    )

    result = customer_totals[
        "total_revenue"
    ].mean()

    assert result == pytest.approx(
        450.0
    )
```

This test verifies the distinction between:

```text
average order value
```

and:

```text
average customer revenue
```

---

## Common Mistakes

### Using `mean()` for a Total

Incorrect:

```python
orders["revenue"].mean()
```

when the requirement is:

```text
total revenue
```

Use:

```python
orders["revenue"].sum()
```

---

### Using `sum()` to Represent Typical Value

A total says nothing about the typical transaction.

Use:

```python
median()
```

or:

```python
mean()
```

depending on the business question.

---

### Assuming Mean Equals Typical

In skewed distributions:

```text
mean
```

can be far from the typical observation.

Compare with:

```python
median()
```

when outliers are plausible.

---

### Averaging Group Means

Do not calculate:

```python
group_means.mean()
```

as a substitute for the global mean unless equal weighting is actually intended.

Use the original observations or weighted sufficient statistics.

---

### Ignoring Duplicates

Duplicate source records can inflate sums and distort means and medians.

Validate logical keys before aggregation.

---

### Filling Nulls Blindly

Turning missing values into zeros changes the meaning of the metric.

Define null semantics first.

---

### Mixing Currencies or Units

Never calculate combined statistics across incompatible currencies or units.

Normalize first.

---

## Production Pitfalls

### Wrong Reporting Grain

The most common analytical error is calculating the right operation at the wrong grain.

For example:

```text
average orders
```

is not:

```text
average customers
```

unless every customer has the same number of orders.

Always identify what one row represents before aggregating.

---

### Hidden Join Multiplication

A bad merge before aggregation can silently inflate:

```text
sum
mean
median
```

Use:

```python
validate="many_to_one"
```

or the appropriate cardinality constraint.

---

### Null and Zero Confusion

A missing metric can indicate:

```text
no observation
```

while zero can indicate:

```text
observed value of zero
```

Reports should preserve this distinction until business logic resolves it.

---

### Empty Population Misinterpretation

An empty reporting period should not automatically become:

```text
revenue = 0
```

unless zero is explicitly the correct business representation.

---

### Large Pandas Reductions

Basic reductions can be efficient, but loading a massive raw dataset solely to calculate:

```text
sum
mean
median
```

may still be wasteful.

Push computation toward PostgreSQL, a warehouse, or another scalable engine when appropriate.

---

## Security Considerations

Aggregate metrics can reveal sensitive information even without exposing individual rows.

Examples:

```text
employee compensation averages
customer spending
tenant-level usage
internal financial metrics
```

Scope and authorize data before aggregation.

For tenant-specific reporting:

```python
tenant_orders = orders.loc[
    orders["tenant_id"].eq(
        tenant_id
    )
].copy()

tenant_revenue = tenant_orders[
    "revenue"
].sum()
```

Do not calculate a global metric and assume later filtering provides equivalent isolation.

---

## Reliability and Reproducibility

A production metric should have an explicit contract:

```text
metric name
population
row grain
time window
currency
unit
null policy
duplicate policy
aggregation function
```

Example:

```text
Metric: Average Completed Order Value
Population: completed orders
Grain: one row per order
Currency: USD
Null policy: reject null revenue
Duplicate policy: transaction_id unique
Calculation: mean(revenue)
```

This makes the metric reproducible and auditable.

---

## Monitoring

Monitor both the statistic and the population that generated it.

Example:

```python
metrics = {
    "row_count": len(completed_orders),
    "null_rate": completed_orders[
        "revenue"
    ].isna().mean(),
    "total_revenue": completed_orders[
        "revenue"
    ].sum(),
    "mean_revenue": completed_orders[
        "revenue"
    ].mean(),
    "median_revenue": completed_orders[
        "revenue"
    ].median(),
}
```

Useful monitoring dimensions include:

```text
row count
unique entity count
null rate
duplicate rate
mean
median
sum
min
max
p95
```

A change in the population can explain a metric change that otherwise looks anomalous.

---

## Recommended Production Pattern

```python
import pandas as pd


def summarize_completed_orders(
    orders: pd.DataFrame,
) -> dict[str, float | int]:
    required_columns = {
        "order_id",
        "revenue",
        "status",
    }

    missing = required_columns.difference(
        orders.columns
    )

    if missing:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing)}"
        )

    working = orders.loc[
        orders["status"].eq("completed"),
        [
            "order_id",
            "revenue",
        ],
    ].copy()

    if working.empty:
        raise ValueError(
            "No completed orders available."
        )

    working["revenue"] = pd.to_numeric(
        working["revenue"],
        errors="raise",
    )

    if working[
        "order_id"
    ].duplicated().any():
        raise ValueError(
            "Duplicate order IDs detected."
        )

    if working["revenue"].isna().any():
        raise ValueError(
            "Completed orders contain "
            "missing revenue values."
        )

    return {
        "order_count": int(
            working["order_id"].nunique()
        ),
        "total_revenue": float(
            working["revenue"].sum()
        ),
        "mean_order_value": float(
            working["revenue"].mean()
        ),
        "median_order_value": float(
            working["revenue"].median()
        ),
    }
```

The sequence is:

```text
validate schema
    ↓
define reporting population
    ↓
project required fields
    ↓
normalize dtype
    ↓
validate duplicates and nulls
    ↓
calculate statistics
    ↓
publish metrics
```

This is much safer than calling:

```python
df["revenue"].mean()
```

on raw data and assuming the result is production-ready.

---

## Decision Guide

| Requirement | Operation |
| --- | --- |
| Total revenue | `sum()` |
| Total transaction amount | `sum()` |
| Average order value | `mean()` |
| Average processing time | `mean()` |
| Typical value in a skewed distribution | `median()` |
| Robust central value | `median()` |
| Global metric across all observations | Aggregate original population |
| Average customer spend | Aggregate by customer, then `mean()` |
| Group-level total | `groupby().sum()` |
| Group-level average | `groupby().mean()` |
| Group-level median | `groupby().median()` |
| Preserve distinction between no observations and zero sum | `sum(min_count=1)` |
| Large database-backed sum/mean | SQL pushdown |
| Large database-backed median | Database percentile function |
| Incremental sum | Combine batch sums |
| Incremental mean | Combine total sums and counts |
| Exact global median from batch medians | Not generally valid |

---

## Key Takeaways

- `sum()` measures total magnitude, `mean()` measures arithmetic average, and `median()` identifies the central observation; choosing between them is a business-semantic decision.
- Always calculate these metrics at the correct population and row grain; the average order value and average customer spend are different metrics even when both use `mean()`.
- Missing values, duplicates, incorrect dtypes, mixed currencies, inconsistent units, and accidental join multiplication can make statistically valid results operationally incorrect.
- For skewed data and outlier-sensitive metrics, compare mean and median rather than assuming the mean represents a typical observation.
- Production pipelines should define metric contracts, validate inputs, monitor population quality, and push large database-backed aggregations into PostgreSQL or another suitable analytical engine when practical.