# 04- Agg

## Overview

`agg()` is Pandas' flexible aggregation interface for applying one or more aggregation functions to grouped data, selected columns, Series, or DataFrames.

It becomes especially valuable when a business result requires several metrics from the same groups:

```text
region
    ├── total revenue
    ├── average order value
    ├── order count
    ├── maximum order value
    └── unique customers
```

For example:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        average_order_value=("revenue", "mean"),
        order_count=("order_id", "nunique"),
        max_order_value=("revenue", "max"),
    )
    .reset_index()
)
```

The result is a group-level DataFrame with an explicit output schema.

`agg()` is closely related to the broader `groupby()` topic, but its main purpose is to express **what metrics should be calculated for each group and how those metrics should be named**.

---

## Why `agg()` Exists

A simple aggregation is straightforward:

```python
orders.groupby("region")["revenue"].sum()
```

Real reporting usually requires several calculations:

```text
total revenue
average revenue
number of orders
number of customers
minimum revenue
maximum revenue
```

Without `agg()`, the code can become repetitive:

```python
revenue = orders.groupby("region")["revenue"].sum()
average = orders.groupby("region")["revenue"].mean()
orders_count = orders.groupby("region")["order_id"].nunique()
```

`agg()` lets the grouping and metric definitions live in one expression:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        average_revenue=("revenue", "mean"),
        order_count=("order_id", "nunique"),
    )
)
```

This improves:

- Readability.
- Schema control.
- Maintainability.
- Testability.
- Reporting consistency.

---

## Mental Model

A grouped aggregation can be viewed as:

```text
Input rows
    │
    ▼
Grouping keys
    │
    ▼
Groups
    │
    ├── metric 1 → aggregate
    ├── metric 2 → aggregate
    ├── metric 3 → aggregate
    └── metric 4 → aggregate
    │
    ▼
One output row per group
```

For example:

```text
Input grain:
one row = one order

Group key:
region

Output grain:
one row = one region
```

This grain change should always be explicit.

---

## Basic Syntax

The most useful production-oriented form is named aggregation:

```python
DataFrame.groupby(...).agg(
    output_name=("source_column", "aggregation"),
)
```

Example:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        order_count=("order_id", "count"),
    )
)
```

You can also use multiple source columns:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        average_discount=("discount", "mean"),
        unique_customers=("customer_id", "nunique"),
    )
)
```

---

## Named Aggregation

Named aggregation is usually the clearest approach for production code.

```python
summary = (
    orders.groupby(
        "region",
        as_index=False,
    )
    .agg(
        total_revenue=("revenue", "sum"),
        average_order_value=("revenue", "mean"),
        order_count=("order_id", "nunique"),
    )
)
```

Output:

```text
region | total_revenue | average_order_value | order_count
-------|---------------|---------------------|------------
East   | 250000        | 1250                | 200
West   | 180000        | 1000                | 180
```

Advantages:

- Output names are explicit.
- No unnecessary MultiIndex columns.
- Schema is easy to document.
- Downstream consumers get stable field names.
- Tests can assert exact columns.

This is generally preferable to relying on Pandas-generated MultiIndex column names.

---

## Aggregation Functions

Common built-in functions include:

| Function | Typical Meaning |
| --- | --- |
| `sum` | Total |
| `mean` | Average |
| `median` | Middle value |
| `min` | Minimum |
| `max` | Maximum |
| `count` | Non-null count |
| `size` | Number of rows |
| `nunique` | Distinct non-null values |
| `std` | Standard deviation |
| `var` | Variance |
| `first` | First value |
| `last` | Last value |

Example:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        average_revenue=("revenue", "mean"),
        median_revenue=("revenue", "median"),
        minimum_revenue=("revenue", "min"),
        maximum_revenue=("revenue", "max"),
        order_count=("order_id", "count"),
        unique_customers=("customer_id", "nunique"),
    )
)
```

Choose metrics according to business semantics rather than simply using every available aggregation.

---

## `count()` Versus `size()`

This is a common production and interview distinction.

Suppose:

```python
orders = pd.DataFrame(
    {
        "region": ["East", "East", "West"],
        "revenue": [100, None, 200],
    }
)
```

Then:

```python
orders.groupby("region")["revenue"].count()
```

counts non-null `revenue` values.

Whereas:

```python
orders.groupby("region").size()
```

counts rows.

Conceptually:

```text
East:
2 rows
1 non-null revenue

count(revenue) → 1
size()         → 2
```

Use the function that matches the metric definition.

---

## `nunique()`

Use `nunique()` when counting distinct entities.

```python
summary = (
    orders.groupby("region")
    .agg(
        unique_customers=("customer_id", "nunique"),
        unique_products=("product_id", "nunique"),
    )
)
```

This is different from:

```python
orders.groupby("region").size()
```

which counts records rather than distinct customers or products.

For reporting:

```text
orders
≠
customers
≠
products
```

Keep those metrics semantically distinct.

---

## Multiple Aggregations on One Column

Several aggregation functions can be applied to one source column.

```python
summary = (
    orders.groupby("region")
    .agg(
        revenue_sum=("revenue", "sum"),
        revenue_mean=("revenue", "mean"),
        revenue_min=("revenue", "min"),
        revenue_max=("revenue", "max"),
    )
)
```

This is useful for operational dashboards and quality reporting.

For financial reports, also consider:

```text
count
missing count
minimum
maximum
sum
```

so that unusual distributions are visible.

---

## Aggregating Different Columns

A group can calculate metrics from different source columns.

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        total_discount=("discount", "sum"),
        order_count=("order_id", "nunique"),
        unique_customers=("customer_id", "nunique"),
    )
)
```

The result remains one row per region.

This is generally preferable to creating several independent grouped objects and joining them later.

---

## Lambda Aggregations

A callable can be supplied when built-in functions are insufficient.

```python
summary = (
    orders.groupby("region")
    .agg(
        p90_revenue=(
            "revenue",
            lambda values: values.quantile(0.90),
        ),
    )
)
```

This is useful for custom statistics.

However, custom Python functions can be slower than optimized built-in reductions.

Prefer:

```python
"sum"
"mean"
"count"
"min"
"max"
"nunique"
```

when they express the requirement directly.

---

## Custom Aggregation Functions

For complex business rules:

```python
def revenue_range(values: pd.Series) -> float:
    return values.max() - values.min()


summary = (
    orders.groupby("region")
    .agg(
        revenue_range=("revenue", revenue_range),
    )
)
```

Keep custom aggregation functions:

- Deterministic.
- Side-effect free.
- Focused on one calculation.
- Independent of external services.

Avoid database calls, HTTP calls, Redis operations, file I/O, or network requests inside aggregation functions.

---

## Aggregating a SeriesGroupBy

`agg()` also works on a grouped Series.

```python
revenue_summary = (
    orders.groupby("region")["revenue"]
    .agg(
        ["sum", "mean", "min", "max"]
    )
)
```

This is concise but produces generic output names.

For production APIs and data contracts, named aggregation is usually clearer:

```python
revenue_summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum"),
        average_revenue=("revenue", "mean"),
        minimum_revenue=("revenue", "min"),
        maximum_revenue=("revenue", "max"),
    )
)
```

---

## Aggregating a DataFrame

`agg()` can also be used directly on a DataFrame.

```python
metrics = orders[
    [
        "revenue",
        "discount",
    ]
].agg(
    [
        "sum",
        "mean",
        "min",
        "max",
    ]
)
```

This reduces each selected column independently.

The output orientation differs from grouped aggregation.

Use this style when the task is:

```text
summarize columns globally
```

rather than:

```text
summarize columns within groups
```

---

## Grouped Versus Global Aggregation

Compare:

```python
orders.agg(
    total_revenue=("revenue", "sum"),
)
```

with:

```python
orders.groupby("region").agg(
    total_revenue=("revenue", "sum"),
)
```

The first produces a global result.

The second produces one result per region.

The distinction is:

```text
agg()
    → entire DataFrame

groupby().agg()
    → one result per group
```

This distinction becomes critical in larger data pipelines.

---

## MultiIndex Results

Older or less explicit aggregation styles can create hierarchical columns.

For example:

```python
summary = (
    orders.groupby("region")
    .agg(
        {
            "revenue": ["sum", "mean"],
            "discount": ["sum", "mean"],
        }
    )
)
```

This can produce:

```text
             revenue         discount
                 sum    mean     sum   mean
region
East            ...     ...      ...    ...
West            ...     ...      ...    ...
```

The hierarchical structure is valid Pandas, but it can be inconvenient for:

- JSON serialization.
- API responses.
- CSV exports.
- Database inserts.
- Schema validation.

Named aggregation avoids this in most production cases.

---

## Flattening MultiIndex Columns

If MultiIndex columns already exist:

```python
summary.columns = [
    "_".join(str(part) for part in column)
    for column in summary.columns.to_flat_index()
]
```

For example:

```text
revenue_sum
revenue_mean
discount_sum
discount_mean
```

A controlled naming convention is preferable to relying on whatever representation Pandas happens to generate.

---

## `as_index=False`

Grouping normally places group keys in the index.

Using:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum")
    )
)
```

produces:

```text
Index:
region
```

For a plain tabular result:

```python
summary = (
    orders.groupby(
        "region",
        as_index=False,
    )
    .agg(
        total_revenue=("revenue", "sum")
    )
)
```

This is convenient when the result goes directly to:

- API serialization.
- CSV.
- Parquet.
- Database loading.

An alternative is:

```python
summary = (
    orders.groupby("region")
    .agg(
        total_revenue=("revenue", "sum")
    )
    .reset_index()
)
```

---

## Multiple Grouping Keys

`agg()` works naturally with multiple grouping dimensions.

```python
summary = (
    orders.groupby(
        ["region", "channel"],
        as_index=False,
    )
    .agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique"),
    )
)
```

The output grain becomes:

```text
one row = one region + channel
```

For example:

```text
region | channel | revenue | order_count
-------|---------|---------|------------
East   | Online  | 120000  | 100
East   | Retail  | 80000   | 70
West   | Online  | 90000   | 85
West   | Retail  | 70000   | 95
```

Every additional key can increase group cardinality.

---

## Aggregating Time-Based Groups

Combine `groupby()` with a derived reporting period.

```python
orders["created_at"] = pd.to_datetime(
    orders["created_at"],
    utc=True,
)

orders["order_month"] = (
    orders["created_at"]
    .dt.to_period("M")
)

monthly_summary = (
    orders.groupby(
        ["order_month", "region"],
        as_index=False,
    )
    .agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique"),
    )
)
```

This gives an explicit reporting grain:

```text
one row = one month + region
```

The derived time dimension should be validated before aggregation if it affects contractual reports.

---

## Handling Missing Values

Aggregation functions have defined missing-value behavior.

For example:

```python
summary = (
    orders.groupby("region")
    .agg(
        average_revenue=("revenue", "mean"),
        revenue_count=("revenue", "count"),
    )
)
```

`mean()` generally ignores missing observations, while `count()` counts non-null values.

For critical metrics, do not assume this is always acceptable.

Validate completeness first:

```python
missing_revenue = orders["revenue"].isna().sum()

if missing_revenue:
    raise ValueError(
        f"Found {missing_revenue} missing revenue values."
    )
```

The correct approach depends on whether missing values mean:

```text
unknown
not collected
not applicable
zero
```

---

## Aggregating Empty Groups

An empty input should have a predictable result schema.

```python
def build_summary(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "region",
        "total_revenue",
        "order_count",
    ]

    if orders.empty:
        return pd.DataFrame(
            columns=columns
        )

    return (
        orders.groupby(
            "region",
            as_index=False,
        )
        .agg(
            total_revenue=("revenue", "sum"),
            order_count=("order_id", "nunique"),
        )
    )
```

This is useful in scheduled pipelines where a valid time window can legitimately contain no records.

---

## Aggregation and Data Types

Measure columns should have appropriate numeric types before aggregation.

```python
orders["revenue"] = pd.to_numeric(
    orders["revenue"],
    errors="coerce",
)
```

Validate afterward:

```python
if orders["revenue"].isna().any():
    raise ValueError(
        "Invalid revenue values detected."
    )
```

For financial systems, use appropriate monetary representations and avoid treating floating-point arithmetic as a universal substitute for exact currency semantics.

---

## Aggregation and Boolean Data

Boolean columns can be aggregated for counts.

Example:

```python
orders["is_cancelled"].sum()
```

can count `True` values because booleans are represented numerically in this context.

Within groups:

```python
summary = (
    orders.groupby("region")
    .agg(
        cancelled_orders=("is_cancelled", "sum"),
    )
)
```

For clarity in business-critical code, explicit boolean-count naming is preferable:

```text
cancelled_orders
```

rather than:

```text
is_cancelled_sum
```

---

## Conditional Aggregation

Sometimes the metric is defined by a condition.

Example:

```python
summary = (
    orders.assign(
        high_value=lambda frame:
            frame["revenue"].ge(5_000)
    )
    .groupby("region")
    .agg(
        total_orders=("order_id", "nunique"),
        high_value_orders=("high_value", "sum"),
    )
    .reset_index()
)
```

This separates:

```text
business condition
```

from:

```text
group aggregation
```

and is often easier to test.

---

## Multiple Metrics in One Pass

A well-designed `agg()` can create the complete report in one grouped operation.

```python
summary = (
    orders.groupby(
        ["region", "channel"],
        as_index=False,
    )
    .agg(
        total_revenue=("revenue", "sum"),
        average_revenue=("revenue", "mean"),
        total_discount=("discount", "sum"),
        order_count=("order_id", "nunique"),
        customer_count=("customer_id", "nunique"),
    )
)
```

This is usually preferable to calculating each metric independently and joining the resulting DataFrames.

It also makes the expected output schema immediately visible.

---

## Aggregation and Business Invariants

Aggregated metrics should be checked against expected relationships.

For example:

```python
summary = (
    orders.groupby("region", as_index=False)
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
    )
)

if (summary["revenue"] < 0).any():
    raise ValueError(
        "Revenue aggregation contains invalid negatives."
    )
```

For financial reports:

```python
source_total = orders["revenue"].sum()
output_total = summary["revenue"].sum()

if source_total != output_total:
    raise ValueError(
        "Grouped revenue does not reconcile with source."
    )
```

Reconciliation should be designed according to the aggregation grain and business rules.

---

## Aggregation After Filtering

Filtering before grouping can significantly reduce work.

Prefer:

```python
recent_orders = orders.loc[
    orders["created_at"].ge(start_date)
    & orders["created_at"].lt(end_date)
]

summary = (
    recent_orders.groupby("region")
    .agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique"),
    )
)
```

instead of grouping the entire historical dataset when only a time window is needed.

This improves both performance and semantic clarity.

---

## SQL Equivalent

The following Pandas expression:

```python
summary = (
    orders.groupby("region", as_index=False)
    .agg(
        revenue=("revenue", "sum"),
        order_count=("order_id", "nunique"),
    )
)
```

corresponds conceptually to:

```sql
SELECT
    region,
    SUM(revenue) AS revenue,
    COUNT(DISTINCT order_id) AS order_count
FROM orders
GROUP BY region;
```

For large datasets in PostgreSQL, database-side aggregation is often preferable before transferring the result into Pandas.

---

## SQL Pushdown Strategy

A production pipeline can use:

```text
PostgreSQL
    │
    ├── filter
    ├── join
    └── aggregate
    │
    ▼
Reduced result
    │
    ▼
Pandas
    │
    └── additional transformation / report formatting
```

For example:

```python
summary = pd.read_sql_query(
    """
    SELECT
        region,
        SUM(revenue) AS revenue,
        COUNT(DISTINCT order_id) AS order_count
    FROM orders
    WHERE order_date >= %(start_date)s
      AND order_date < %(end_date)s
    GROUP BY region
    """,
    connection,
    params={
        "start_date": start_date,
        "end_date": end_date,
    },
)
```

This reduces:

- Database-to-application transfer.
- Pandas memory usage.
- Application CPU requirements.

---

## API and Event Data

Grouping API or event records is a common backend workload.

```python
events = pd.DataFrame(
    {
        "service": [
            "payments",
            "payments",
            "orders",
            "orders",
        ],
        "environment": [
            "prod",
            "prod",
            "prod",
            "staging",
        ],
        "latency_ms": [
            120,
            150,
            90,
            110,
        ],
    }
)

summary = (
    events.groupby(
        ["service", "environment"],
        as_index=False,
    )
    .agg(
        average_latency_ms=(
            "latency_ms",
            "mean",
        ),
        max_latency_ms=(
            "latency_ms",
            "max",
        ),
        event_count=(
            "latency_ms",
            "count",
        ),
    )
)
```

This can feed an operational dashboard or a monitoring API.

---

## Reporting Architecture

A reporting service may use `agg()` as the metric-definition layer:

```mermaid
flowchart LR
    Source[(PostgreSQL / API / Parquet)] --> Filter[Filter Input]
    Filter --> Validate[Validate Schema and Grain]
    Validate --> Group[Group by Reporting Dimensions]
    Group --> Agg[agg() Metrics]
    Agg --> Reconcile[Reconcile / Validate]
    Reconcile --> Report[Report Dataset]
    Report --> Cache[(Redis)]
    Cache --> API[FastAPI / Django]
```

The key design principle is that the grouped DataFrame should be treated as a defined reporting dataset rather than an incidental intermediate result.

---

## Performance Considerations

`agg()` is usually efficient when using built-in aggregation functions.

Prefer:

```python
.agg(
    revenue=("revenue", "sum"),
    order_count=("order_id", "nunique"),
)
```

over Python loops.

Built-in aggregations are typically implemented through optimized Pandas internals.

Potential performance problems include:

- Very large row counts.
- High-cardinality group keys.
- Many grouping dimensions.
- Expensive custom Python functions.
- Unnecessary sorting.
- Excessive intermediate DataFrames.
- Large object/string columns.

---

## High-Cardinality Grouping

This can be expensive:

```python
summary = (
    events.groupby(
        [
            "customer_id",
            "request_id",
            "timestamp",
        ]
    )
    .agg(
        latency=("latency_ms", "mean"),
    )
)
```

If the combination is nearly unique, aggregation provides little reduction.

Before grouping, estimate group cardinality:

```python
group_count = (
    events[
        [
            "customer_id",
            "request_id",
            "timestamp",
        ]
    ]
    .drop_duplicates()
    .shape[0]
)

print(
    f"Potential groups: {group_count:,}"
)
```

If group count approaches input row count, reassess the intended grain.

---

## Memory Usage

Grouping and aggregation require memory for:

- Grouping keys.
- Group membership.
- Intermediate aggregation state.
- Result construction.

Reduce the working set first:

```python
working = orders[
    [
        "region",
        "order_id",
        "customer_id",
        "revenue",
    ]
]
```

Then:

```python
summary = (
    working.groupby("region")
    .agg(
        revenue=("revenue", "sum"),
        orders=("order_id", "nunique"),
        customers=("customer_id", "nunique"),
    )
)
```

Avoid carrying large unused columns such as raw JSON payloads or large text blobs through aggregation.

---

## Categorical Grouping

For low-cardinality dimensions:

```python
orders["region"] = orders["region"].astype(
    "category"
)
```

Then:

```python
summary = (
    orders.groupby(
        "region",
        observed=True,
    )
    .agg(
        revenue=("revenue", "sum"),
    )
)
```

Categorical dtypes can reduce memory use and can be useful for repeated dimensions.

Measure the benefit with realistic workloads rather than assuming categorical conversion is always faster.

---

## Custom Aggregation Performance

This:

```python
summary = (
    orders.groupby("region")
    .agg(
        p90=("revenue", lambda values: values.quantile(0.90))
    )
)
```

can be more expensive than built-in aggregations because Python-level functions may execute once per group.

For heavy workloads:

- Prefer native methods.
- Precompute reusable metrics.
- Aggregate in SQL when appropriate.
- Consider specialized analytical engines for large-scale workloads.

Use custom functions when they provide necessary business logic, not merely because they are convenient.

---

## Custom Aggregation Requirements

A custom aggregator should ideally satisfy:

```text
deterministic
pure
well-tested
null-aware
type-aware
bounded in complexity
```

Bad:

```python
def calculate_metric(values):
    send_to_external_api(values)
    return ...
```

Good:

```python
def revenue_spread(values: pd.Series) -> float:
    return values.max() - values.min()
```

Aggregation should remain a data-processing operation, not an orchestration mechanism.

---

## Error Handling

Validate inputs before aggregation.

```python
required_columns = {
    "region",
    "order_id",
    "revenue",
}

missing = required_columns.difference(
    orders.columns
)

if missing:
    raise ValueError(
        f"Missing columns: {sorted(missing)}"
)
```

Validate measures:

```python
orders["revenue"] = pd.to_numeric(
    orders["revenue"],
    errors="coerce",
)

if orders["revenue"].isna().any():
    raise ValueError(
        "Invalid revenue values detected."
    )
```

Failing early gives better diagnostics than discovering an incorrect aggregate later.

---

## Testing `agg()`

Tests should verify:

- Grouping keys.
- Output grain.
- Output columns.
- Aggregated values.
- Null behavior.
- Distinct counts.
- Empty input.
- Reconciliation where relevant.

Example:

```python
import pandas as pd
from pandas.testing import assert_frame_equal


def test_region_aggregation() -> None:
    orders = pd.DataFrame(
        {
            "region": [
                "East",
                "East",
                "West",
            ],
            "order_id": [
                1001,
                1002,
                1003,
            ],
            "customer_id": [
                501,
                501,
                502,
            ],
            "revenue": [
                100,
                200,
                300,
            ],
        }
    )

    actual = (
        orders.groupby(
            "region",
            as_index=False,
        )
        .agg(
            total_revenue=("revenue", "sum"),
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
        )
        .sort_values("region")
        .reset_index(drop=True)
    )

    expected = pd.DataFrame(
        {
            "region": [
                "East",
                "West",
            ],
            "total_revenue": [
                300,
                300,
            ],
            "order_count": [
                2,
                1,
            ],
            "customer_count": [
                1,
                1,
            ],
        }
    )

    assert_frame_equal(
        actual,
        expected,
    )
```

This verifies business behavior rather than merely testing that `agg()` runs.

---

## Common Mistakes

### Using Generic Aggregation Dictionaries for Production APIs

Less explicit:

```python
orders.groupby("region").agg(
    {
        "revenue": ["sum", "mean"],
    }
)
```

Preferred:

```python
orders.groupby("region").agg(
    total_revenue=("revenue", "sum"),
    average_revenue=("revenue", "mean"),
)
```

Named aggregation produces clearer schemas.

---

### Confusing `count()` with `size()`

`count()` measures non-null observations in a selected column.

`size()` measures rows.

This difference becomes important when missing values exist.

---

### Using `count()` for Unique Entities

This:

```python
orders.groupby("region")["customer_id"].count()
```

counts customer records, not unique customers.

Use:

```python
orders.groupby("region")["customer_id"].nunique()
```

when the metric is unique customers.

---

### Aggregating Before Defining the Grain

A report can be technically correct but conceptually wrong if the grouping keys are incorrect.

Always define:

```text
one row = ?
```

before implementing the aggregation.

---

### Hiding Duplicate Records

Aggregation can combine duplicate records without raising an error.

If duplicates should never exist, validate them before aggregation.

---

### Using Expensive Python Functions Unnecessarily

Prefer built-in aggregation functions.

Use custom functions only when the metric cannot be expressed cleanly through existing Pandas operations.

---

### Carrying Unnecessary Columns

Do not pass large unused data through the grouping stage.

Project the required columns first.

---

## Production Pitfalls

### Silent Metric Changes

Changing:

```python
sum
```

to:

```python
mean
```

can completely change report semantics while leaving the schema unchanged.

Metric definitions should therefore be documented and tested.

---

### Changing Grouping Keys

Changing:

```python
groupby("region")
```

to:

```python
groupby(["region", "channel"])
```

changes the output grain and potentially every downstream metric.

Treat grouping keys as part of the data contract.

---

### Missing-Value Semantics

Metrics can change when null-handling changes.

For example:

```text
average of observed values
```

is not the same as:

```text
average treating missing as zero
```

Define null behavior explicitly.

---

### Unbounded Group Cardinality

A production report should not unexpectedly start grouping by a high-cardinality field and generate millions of output groups.

Validate cardinality and schema changes.

---

### Synchronous API Aggregation

Avoid recalculating expensive grouped reports for every request.

Prefer:

```text
scheduled job
    ↓
aggregate
    ↓
persist / cache
    ↓
API reads result
```

Celery can run background aggregation jobs, while Redis can cache frequently accessed results.

---

## Reliability and Idempotency

`agg()` is naturally suitable for deterministic batch processing when:

```text
input data
+
grouping keys
+
aggregation definitions
```

are deterministic.

For recurring pipelines, persist:

```text
source partition
processing period
aggregation rule version
input row count
output group count
validation status
```

This makes failures and backfills easier to diagnose.

Keep raw or normalized source data so that the aggregate can be rebuilt after a rule change.

---

## Monitoring

Useful production metrics include:

```text
input_row_count
output_group_count
distinct_group_key_count
null_group_key_count
duplicate_input_key_count
aggregation_duration_ms
input_memory_bytes
output_memory_bytes
source_metric_total
output_metric_total
```

Monitor metric distributions as well.

For example:

```python
summary["total_revenue"].describe()
```

can help identify:

- Unexpected spikes.
- Zero-heavy output.
- Negative values.
- Extreme outliers.

---

## Security Considerations

Aggregation does not provide authorization or tenant isolation.

For multi-tenant reporting:

```text
Authenticate
    ↓
Authorize tenant
    ↓
Filter permitted records
    ↓
Aggregate
    ↓
Return report
```

Filtering after unrestricted aggregation is too late if the aggregate itself can expose data across tenants.

Also consider whether small groups expose sensitive information. An aggregated report may still reveal individual behavior when group sizes are very small.

---

## Cost Considerations

Reduce grouped-processing cost by:

```text
Filter early
    ↓
Select required columns
    ↓
Use efficient dtypes
    ↓
Reduce grouping dimensions
    ↓
Prefer built-in aggregators
    ↓
Push suitable aggregation into SQL
    ↓
Cache or precompute recurring reports
```

For AWS data pipelines, partitioned S3 data and database-side or distributed aggregation can prevent repeatedly loading full historical datasets into a single Pandas process.

---

## Recommended Engineering Pattern

A maintainable report function should keep validation, transformation, and output construction explicit.

```python
import pandas as pd


def build_sales_summary(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    required_columns = {
        "region",
        "order_id",
        "customer_id",
        "revenue",
    }

    missing = required_columns.difference(
        orders.columns
    )

    if missing:
        raise ValueError(
            f"Missing columns: {sorted(missing)}"
        )

    if orders.empty:
        return pd.DataFrame(
            columns=[
                "region",
                "total_revenue",
                "order_count",
                "customer_count",
            ]
        )

    working = orders[
        [
            "region",
            "order_id",
            "customer_id",
            "revenue",
        ]
    ].copy()

    working["revenue"] = pd.to_numeric(
        working["revenue"],
        errors="coerce",
    )

    if working["revenue"].isna().any():
        raise ValueError(
            "Invalid revenue values detected."
        )

    summary = (
        working.groupby(
            "region",
            as_index=False,
        )
        .agg(
            total_revenue=("revenue", "sum"),
            order_count=("order_id", "nunique"),
            customer_count=("customer_id", "nunique"),
        )
    )

    if (summary["total_revenue"] < 0).any():
        raise ValueError(
            "Negative revenue detected."
        )

    return summary
```

This structure provides:

- Explicit input validation.
- Controlled projection.
- Type normalization.
- Stable output columns.
- Clear aggregation rules.
- Explicit failure conditions.

---

## Decision Framework

Use the following model when choosing an aggregation strategy:

```mermaid
flowchart TD
    A[Need summary metrics?] --> B{Need grouping?}

    B -->|No| C[Use DataFrame / Series agg()]
    B -->|Yes| D[Define grouping keys]

    D --> E{Output one row per group?}
    E -->|Yes| F[Use groupby().agg()]
    E -->|No| G[Consider transform()]

    F --> H{Multiple metrics?}
    H -->|Yes| I[Use named aggregation]
    H -->|No| J[Use simple aggregation]

    I --> K{Large dataset?}
    J --> K

    K -->|Yes| L[Filter / project / SQL pushdown]
    K -->|No| M[Validate output]
    L --> M
```

The important question is not which syntax is shortest. It is whether the chosen aggregation matches the desired output grain and business semantics.

---

## `agg()` Versus Related Operations

| Operation | Output Shape | Typical Use |
| --- | --- | --- |
| `agg()` | Reduced summary | Several metrics |
| `groupby().agg()` | One row per group | Group-level reports |
| `transform()` | Original row count | Group metric per row |
| `filter()` | Rows from qualifying groups | Group-level filtering |
| `sum()` / `mean()` | Single reduction | Simple metric |
| `pivot_table()` | Aggregated wide table | Reporting matrix |

Use `agg()` when the goal is to define a structured collection of metrics from a DataFrame or each group.

---

## Section Completion Standard

A strong understanding of `agg()` means being able to design an aggregation by first defining:

```text
Input grain
    ↓
Grouping keys
    ↓
Business metrics
    ↓
Null semantics
    ↓
Duplicate semantics
    ↓
Output grain
    ↓
Output schema
    ↓
Validation
    ↓
Performance strategy
```

For any grouped reporting problem, the implementation should make these decisions visible in the code.

The goal is not to memorize aggregation names. The goal is to produce a result that is:

```text
correct
deterministic
schema-stable
testable
efficient
auditable
```

---

## Key Takeaways

- `agg()` provides a flexible way to define multiple metrics for a DataFrame or grouped DataFrame, and named aggregation is usually the clearest production pattern.
- Always define the grouping keys and output grain before choosing aggregation functions; `count()`, `size()`, and `nunique()` answer materially different business questions.
- Prefer built-in vectorized aggregations and explicit output names, while using custom Python aggregators only when the required metric cannot be expressed cleanly otherwise.
- For production workloads, validate nulls, duplicates, metric ranges, group cardinality, and reconciliation totals, and push suitable filtering and aggregation into SQL for large datasets.
- Treat aggregation definitions as part of the report contract: changes to grouping keys, metric formulas, or missing-value semantics can change business meaning without changing the DataFrame schema.