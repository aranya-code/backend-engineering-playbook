# 14- Cut And Qcut

## Overview

`cut()` and `qcut()` convert continuous numeric values into discrete intervals, often called bins or buckets.

They are useful when raw numeric values are less useful than business categories such as:

```text
0–30 days
31–60 days
61–90 days
90+ days
```

or:

```text
Low
Medium
High
```

The two operations solve different problems:

- `cut()` creates bins using explicit numeric boundaries.
- `qcut()` creates bins based on quantiles so that observations are distributed approximately evenly across the bins.

The distinction is important in production systems because binning can encode business rules, affect reporting consistency, and change how downstream systems interpret a numeric field.

A useful mental model is:

```text
Continuous value
      │
      ▼
   Binning
      │
 ┌────┴────┐
 ▼         ▼
cut()    qcut()
rules     distribution
based      based
```

---

## Why Binning Exists

Suppose an e-commerce system stores:

```text
customer_id | lifetime_value
------------|---------------
101         | 84.50
102         | 1290.00
103         | 420.75
104         | 75.25
```

A dashboard might not need the exact value. It may need:

```text
customer_id | segment
------------|---------
101         | Low
102         | High
103         | Medium
104         | Low
```

Binning can make:

- Reporting easier to read.
- Business rules easier to express.
- Segment-based aggregation easier.
- Rule-based notifications easier.
- Model or feature pipelines more manageable when coarse categories are intentional.

The important engineering decision is whether the boundaries are business-defined or distribution-defined.

---

## `cut()` Versus `qcut()`

| Feature | `cut()` | `qcut()` |
| --- | --- | --- |
| Main idea | Fixed intervals | Quantile-based intervals |
| Boundaries | Explicitly provided or inferred from equal-width bins | Derived from data distribution |
| Bin sizes by value | Equal or explicitly controlled | Not equal |
| Rows per bin | Can vary significantly | Approximately equal when possible |
| Best for | Business thresholds | Relative ranking / distribution segmentation |
| Stability across datasets | High with fixed boundaries | Can change as data distribution changes |
| Typical use | SLA buckets, age bands, revenue thresholds | Percentiles, customer ranking, score segmentation |

A strong production rule is:

> Use `cut()` when the boundary itself has business meaning. Use `qcut()` when relative position within a dataset has business meaning.

---

## Basic `cut()` Syntax

The common form is:

```python
pd.cut(
    x,
    bins,
    labels=None,
    right=True,
    include_lowest=False,
)
```

Example:

```python
import pandas as pd

ages = pd.Series(
    [18, 27, 34, 49, 67],
    name="age",
)

age_groups = pd.cut(
    ages,
    bins=[0, 18, 30, 45, 60, 120],
)
```

The result contains interval categories:

```text
0    (0, 18]
1    (18, 30]
2    (30, 45]
3    (45, 60]
4    (60, 120]
Name: age, dtype: category
```

The exact interval notation depends on the boundary configuration.

---

## Why Interval Semantics Matter

By default, `cut()` uses right-closed intervals.

With:

```python
bins = [0, 18, 30]
```

the intervals are conceptually:

```text
(0, 18]
(18, 30]
```

So:

```text
18 → (0, 18]
30 → (18, 30]
```

This matters at boundary values.

You can change the side that is closed:

```python
age_groups = pd.cut(
    ages,
    bins=[0, 18, 30, 45],
    right=False,
)
```

Now the intervals are:

```text
[0, 18)
[18, 30)
[30, 45)
```

When implementing contractual business rules, boundary semantics should be explicit and tested.

---

## `include_lowest`

Suppose the lowest value should belong to the first interval.

Use:

```python
age_groups = pd.cut(
    ages,
    bins=[0, 18, 30, 45],
    include_lowest=True,
)
```

This is particularly important when the lower boundary represents a legitimate business minimum such as:

```text
0 days
0 dollars
0 units
```

Do not rely on assumptions about interval notation when exact edge behavior matters.

---

## Labels

By default, `cut()` returns interval labels.

Business applications often need simpler labels:

```python
age_groups = pd.cut(
    ages,
    bins=[0, 18, 30, 45, 60, 120],
    labels=[
        "Minor",
        "Young Adult",
        "Adult",
        "Senior",
        "Older Adult",
    ],
    include_lowest=True,
)
```

Result:

```text
0          Minor
1    Young Adult
2          Adult
3          Senior
4    Older Adult
Name: age, dtype: category
```

Labels should communicate business semantics rather than exposing implementation-specific interval syntax to API consumers.

---

## Category Dtype

`cut()` and `qcut()` commonly return a categorical result.

Check it with:

```python
print(age_groups.dtype)
```

Typical result:

```text
category
```

This is useful because the result is not merely a collection of arbitrary strings. Pandas tracks the set of categories explicitly.

For ordered categories:

```python
age_groups = pd.cut(
    ages,
    bins=[0, 18, 30, 45, 60, 120],
    labels=[
        "Minor",
        "Young Adult",
        "Adult",
        "Senior",
        "Older Adult",
    ],
    include_lowest=True,
    ordered=True,
)
```

This allows category ordering to carry business meaning.

---

## Ordered Categories

Suppose a customer segment is:

```text
Low
Medium
High
```

Lexicographic sorting is not sufficient:

```text
High
Low
Medium
```

Use ordered categorical labels:

```python
revenue = pd.Series(
    [50, 500, 5000],
    name="revenue",
)

segments = pd.cut(
    revenue,
    bins=[0, 100, 1000, float("inf")],
    labels=["Low", "Medium", "High"],
    include_lowest=True,
    ordered=True,
)
```

Then:

```python
print(segments.cat.categories)
```

The category order is:

```text
Index(['Low', 'Medium', 'High'], dtype='object')
```

This is valuable for:

- Sorting.
- Grouping.
- Reporting.
- Validation.
- Consistent dashboard ordering.

---

## Business Thresholds with `cut()`

`cut()` is especially useful when thresholds come from business requirements.

Example:

```python
orders = pd.DataFrame(
    {
        "order_id": [1001, 1002, 1003, 1004],
        "order_value": [
            49.99,
            125.00,
            749.00,
            1500.00,
        ],
    }
)

orders["order_value_band"] = pd.cut(
    orders["order_value"],
    bins=[
        0,
        50,
        100,
        500,
        1000,
        float("inf"),
    ],
    labels=[
        "Very Low",
        "Low",
        "Medium",
        "High",
        "Very High",
    ],
    include_lowest=True,
)
```

The resulting business rule is explicit:

```text
0–50
50–100
100–500
500–1000
1000+
```

This is a strong fit for production reporting because the boundaries remain stable across batches.

---

## Equal-Width Bins

Instead of explicitly supplying boundaries, `cut()` can divide the numeric range into a specified number of equal-width intervals.

```python
values = pd.Series(
    [10, 20, 30, 40, 50, 60, 70],
    name="score",
)

binned = pd.cut(
    values,
    bins=3,
)
```

The numeric range is divided into three approximately equal-width intervals.

This is useful for exploratory analysis but should be used carefully in production because the boundaries depend on the minimum and maximum values of the current dataset.

If the source range changes substantially, the generated intervals can change.

---

## Explicit Bins Versus Equal-Width Bins

| Approach | Example | Production Stability |
| --- | --- | --- |
| Explicit boundaries | `[0, 100, 500, 1000]` | High |
| Number of bins | `bins=5` | Depends on data range |
| Business labels | `["Low", "Medium", "High"]` | High if boundaries are fixed |
| Automatically derived thresholds | Current min/max | Potentially unstable |

For persistent reports and APIs, explicit business boundaries are usually safer.

---

## `qcut()` Basics

`qcut()` creates bins based on quantiles.

Syntax:

```python
pd.qcut(
    x,
    q,
    labels=None,
    retbins=False,
    duplicates="raise",
)
```

Example:

```python
scores = pd.Series(
    [12, 24, 31, 45, 52, 67, 71, 89, 94, 99],
    name="score",
)

segments = pd.qcut(
    scores,
    q=4,
)
```

This creates four quantile-based groups.

The goal is for each group to contain approximately the same number of observations, subject to duplicate values and quantile boundary constraints.

---

## Why `qcut()` Exists

Suppose customer spending is highly skewed:

```text
10
20
30
50
100
200
500
1000
5000
50000
```

Equal-width bins may produce heavily unbalanced groups.

`qcut()` instead asks:

> Where should the boundaries be placed so that the data is divided into approximately equal-sized groups?

This is useful for:

- Customer percentile segments.
- Risk ranking.
- Relative performance analysis.
- Score bands.
- Exploratory distribution analysis.

The important difference is that `qcut()` adapts to the current data distribution.

---

## Quartiles

A common use is quartiles:

```python
customer_value_quartile = pd.qcut(
    orders["order_value"],
    q=4,
    labels=[
        "Q1",
        "Q2",
        "Q3",
        "Q4",
    ],
)
```

Each quartile aims to contain approximately 25% of observations.

This is fundamentally different from saying:

```text
0–25,000
25,000–50,000
50,000–75,000
75,000–100,000
```

Those are fixed-width or fixed-boundary intervals.

Quartiles are relative to the observed distribution.

---

## Percentile Segmentation

Customer segmentation often uses quantiles:

```python
customers = pd.DataFrame(
    {
        "customer_id": range(1, 11),
        "lifetime_value": [
            50,
            75,
            90,
            110,
            150,
            220,
            350,
            600,
            1200,
            5000,
        ],
    }
)

customers["value_segment"] = pd.qcut(
    customers["lifetime_value"],
    q=4,
    labels=[
        "Bottom 25%",
        "25-50%",
        "50-75%",
        "Top 25%",
    ],
)
```

This answers:

```text
How valuable is this customer relative to the current population?
```

rather than:

```text
How much money did this customer spend?
```

That distinction should be explicit in business documentation.

---

## `retbins=True`

When using `qcut()`, you may need the actual boundaries.

```python
segments, boundaries = pd.qcut(
    customers["lifetime_value"],
    q=4,
    labels=[
        "Bottom 25%",
        "25-50%",
        "50-75%",
        "Top 25%",
    ],
    retbins=True,
)
```

Now:

```python
print(boundaries)
```

returns the quantile boundaries calculated from the current dataset.

This can be useful for analysis and diagnostics.

However, do not automatically persist these boundaries as production rules unless the business explicitly wants the thresholds frozen.

---

## `duplicates="drop"`

Quantile boundaries can collide when many records have identical values.

For example:

```python
values = pd.Series(
    [10, 10, 10, 10, 20, 20, 20, 30],
)
```

A request for many quantiles may result in repeated boundaries.

By default:

```python
pd.qcut(
    values,
    q=4,
)
```

may raise an error because the bin edges are not unique.

You can instead allow duplicate edges to be dropped:

```python
result = pd.qcut(
    values,
    q=4,
    duplicates="drop",
)
```

The number of resulting bins may then be smaller than requested.

Production code should validate the resulting category count rather than assuming that `q=4` always creates exactly four categories.

---

## Handling Duplicate Values in `qcut()`

Duplicate values are not merely a technical nuisance.

Consider a score column where 70% of records contain:

```text
0
```

Quantile-based segmentation may not be able to create equally populated bins while keeping equal values together at the same boundary.

This means:

```text
requested quantiles
        ≠
guaranteed number of distinct bins
```

For production segmentation, decide whether:

- Equal values must remain in the same segment.
- Approximate population balance is sufficient.
- Business thresholds are preferable.
- Ties need custom handling.

---

## Missing Values

Both functions produce missing output for values that cannot be assigned to a bin.

Example:

```python
values = pd.Series(
    [10, 25, None, 40, 80],
    name="score",
)

result = pd.cut(
    values,
    bins=[0, 20, 50, 100],
    labels=["Low", "Medium", "High"],
)
```

The missing input remains missing in the resulting category.

Check explicitly:

```python
print(result.isna().sum())
```

Do not silently interpret:

```text
NaN
```

as:

```text
Unknown category
```

unless that is the intended data contract.

---

## Out-of-Range Values

With explicit `cut()` boundaries, values outside the specified range may become missing.

Example:

```python
values = pd.Series(
    [10, 50, 150],
)

result = pd.cut(
    values,
    bins=[0, 100],
    labels=["Valid"],
)
```

The value:

```text
150
```

falls outside the defined interval.

Detect these cases:

```python
out_of_range = values[result.isna()]

print(out_of_range)
```

This is useful for validating incoming data.

For production systems, make boundary coverage deliberate:

```python
bins = [
    float("-inf"),
    100,
    500,
    float("inf"),
]
```

when values outside a normal range should still be categorized.

---

## Infinite Boundaries

Using infinity is a practical technique for open-ended categories:

```python
orders["segment"] = pd.cut(
    orders["order_value"],
    bins=[
        float("-inf"),
        100,
        500,
        float("inf"),
    ],
    labels=[
        "Low",
        "Medium",
        "High",
    ],
)
```

This avoids accidentally creating missing categories because the next batch contains a value larger than the previous maximum.

For recurring production pipelines, open-ended final buckets are often safer than hard-coded maximums when the business rule is inherently unbounded.

---

## Data Type and Categorical Efficiency

The categorical result from `cut()` can be much more memory-efficient than storing repeated labels as arbitrary Python strings, especially when the number of categories is small relative to the number of rows.

Example:

```python
orders["value_band"] = pd.cut(
    orders["order_value"],
    bins=[0, 100, 500, float("inf")],
    labels=["Low", "Medium", "High"],
)
```

Inspect:

```python
print(orders["value_band"].dtype)
print(orders["value_band"].memory_usage(deep=True))
```

This becomes particularly useful for large datasets with repeated category values.

---

## `cut()` with Datetimes

Although `cut()` is commonly demonstrated with numeric data, it can also be used to create explicit time intervals.

For example, age of an order:

```python
orders["order_age_days"] = (
    pd.Timestamp.now(tz="UTC")
    - pd.to_datetime(
        orders["created_at"],
        utc=True,
    )
).dt.days
```

Then:

```python
orders["age_band"] = pd.cut(
    orders["order_age_days"],
    bins=[
        0,
        1,
        7,
        30,
        90,
        float("inf"),
    ],
    labels=[
        "Same Day",
        "2-7 Days",
        "8-30 Days",
        "31-90 Days",
        "90+ Days",
    ],
    include_lowest=True,
)
```

This is useful for operational aging reports and SLA dashboards.

When exact calendar semantics matter, however, explicit datetime offsets or period-based logic can be more appropriate than converting everything to an integer number of days.

---

## API and Reporting Example

Suppose an order service exposes order aging:

```python
orders["created_at"] = pd.to_datetime(
    orders["created_at"],
    utc=True,
)

now = pd.Timestamp.now(tz="UTC")

orders["age_days"] = (
    now - orders["created_at"]
).dt.total_seconds() / 86_400
```

Bucket the values:

```python
orders["age_bucket"] = pd.cut(
    orders["age_days"],
    bins=[
        -float("inf"),
        1,
        7,
        30,
        90,
        float("inf"),
    ],
    labels=[
        "0-1 day",
        "2-7 days",
        "8-30 days",
        "31-90 days",
        "90+ days",
    ],
    include_lowest=True,
)
```

Now an API or reporting layer can aggregate:

```python
summary = (
    orders.groupby(
        "age_bucket",
        observed=True,
    )
    .size()
    .rename("order_count")
    .reset_index()
)
```

This keeps segmentation logic in the transformation layer rather than embedding business classification rules in the HTTP handler.

---

## Customer Segmentation Example

A realistic customer pipeline might combine fixed business rules with quantile analysis.

```python
customers = pd.DataFrame(
    {
        "customer_id": [101, 102, 103, 104, 105, 106],
        "lifetime_value": [
            50,
            120,
            350,
            700,
            1500,
            5000,
        ],
    }
)

customers["business_segment"] = pd.cut(
    customers["lifetime_value"],
    bins=[
        0,
        100,
        500,
        1000,
        float("inf"),
    ],
    labels=[
        "Low",
        "Standard",
        "Premium",
        "Enterprise",
    ],
    include_lowest=True,
)

customers["relative_segment"] = pd.qcut(
    customers["lifetime_value"],
    q=4,
    labels=[
        "Q1",
        "Q2",
        "Q3",
        "Q4",
    ],
)
```

The two columns answer different questions:

```text
business_segment
    → Which contractual/business tier is this customer in?

relative_segment
    → How does this customer rank relative to this dataset?
```

Do not interchange these concepts.

---

## `cut()` in ETL Pipelines

A production ETL process may look like:

```mermaid
flowchart LR
    Source[(SQL / API / Parquet)] --> Load[Load]
    Load --> Clean[Validate and Clean]
    Clean --> Numeric[Normalize Numeric Fields]
    Numeric --> Bin[cut() / qcut()]
    Bin --> Validate[Validate Categories]
    Validate --> Aggregate[Group and Aggregate]
    Aggregate --> Output[(Report / Database / API)]
```

Binning belongs after type validation but before downstream aggregation when the aggregated report depends on the generated categories.

---

## SQL Integration

If a database already stores a stable business classification rule, consider implementing the rule in SQL rather than transferring millions of rows into Pandas solely for binning.

For example:

```sql
SELECT
    order_id,
    order_value,
    CASE
        WHEN order_value <= 100 THEN 'Low'
        WHEN order_value <= 500 THEN 'Medium'
        ELSE 'High'
    END AS value_band
FROM orders;
```

Pandas is still useful when:

- The categorization is part of a larger in-memory transformation.
- The source is an API or file.
- The boundaries are dynamically computed.
- The result is specifically required for Pandas-based reporting.

A useful engineering rule is:

> Keep stable relational business rules close to the database when the database is already responsible for the authoritative transformation; use Pandas when it materially simplifies the surrounding workflow.

---

## Persisting Quantile Boundaries

One of the biggest production pitfalls with `qcut()` is that its boundaries are data-dependent.

Suppose today's values produce:

```text
Q1 <= 100
Q2 <= 250
Q3 <= 700
```

Tomorrow, the distribution shifts:

```text
Q1 <= 150
Q2 <= 400
Q3 <= 900
```

The same customer value can therefore move from one segment to another without the customer's own value changing.

This may be desirable for relative ranking, but it is dangerous for stable business classification.

For reproducible scoring systems, compute the boundaries from a defined reference population and persist them.

For example:

```python
reference = customers["lifetime_value"].dropna()

_, boundaries = pd.qcut(
    reference,
    q=4,
    retbins=True,
)

print(boundaries)
```

Then use explicit boundaries:

```python
customers["segment"] = pd.cut(
    customers["lifetime_value"],
    bins=boundaries,
    labels=[
        "Q1",
        "Q2",
        "Q3",
        "Q4",
    ],
    include_lowest=True,
)
```

This separates:

```text
threshold creation
```

from:

```text
threshold application
```

That separation is important for reproducibility and versioned data pipelines.

---

## Versioning Segmentation Rules

If categories influence financial decisions, customer treatment, or operational workflows, treat the boundaries as versioned configuration.

Example:

```yaml
customer_value_segmentation:
  version: "2026-09"
  boundaries:
    - 0
    - 100
    - 500
    - 1000
    - inf
  labels:
    - low
    - standard
    - premium
    - enterprise
```

Application code can load the configuration:

```python
import math

config = {
    "boundaries": [
        0,
        100,
        500,
        1000,
        math.inf,
    ],
    "labels": [
        "low",
        "standard",
        "premium",
        "enterprise",
    ],
}

customers["segment"] = pd.cut(
    customers["lifetime_value"],
    bins=config["boundaries"],
    labels=config["labels"],
    include_lowest=True,
)
```

This makes segmentation rules auditable and reproducible across pipeline runs.

---

## Monitoring Binned Data

Binning can conceal changes in source distributions.

For example:

```python
distribution = (
    orders["value_band"]
    .value_counts(
        dropna=False,
        normalize=True,
    )
)

print(distribution)
```

Monitor:

```text
category distribution
missing/unassigned percentage
minimum value
maximum value
quantile boundaries
unexpected category counts
```

A sudden increase in:

```text
NaN category
```

may indicate:

- New values outside configured boundaries.
- Invalid input.
- Dtype conversion failures.
- Upstream schema changes.

---

## Data Quality Validation

Validate that all expected categories exist when the schema is contractual.

```python
expected_categories = {
    "Low",
    "Medium",
    "High",
}

actual_categories = set(
    orders["value_band"]
    .dropna()
    .astype(str)
    .unique()
)

unexpected = actual_categories - expected_categories

if unexpected:
    raise ValueError(
        f"Unexpected categories: {sorted(unexpected)}"
    )
```

You can also validate missing assignments:

```python
missing_rate = (
    orders["value_band"]
    .isna()
    .mean()
)

if missing_rate > 0.01:
    raise ValueError(
        f"Too many unclassified records: {missing_rate:.2%}"
    )
```

The threshold should reflect the business contract.

---

## Empty Inputs

A production transformation should handle empty input predictably.

```python
def add_value_band(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    result = orders.copy()

    if result.empty:
        result["value_band"] = pd.Categorical(
            [],
            categories=[
                "Low",
                "Medium",
                "High",
            ],
            ordered=True,
        )
        return result

    result["value_band"] = pd.cut(
        result["order_value"],
        bins=[
            0,
            100,
            500,
            float("inf"),
        ],
        labels=[
            "Low",
            "Medium",
            "High",
        ],
        include_lowest=True,
    )

    return result
```

Returning the expected categorical schema is often safer than leaving downstream systems to infer it from an empty DataFrame.

---

## Unexpected Input Types

Numeric binning requires numeric-like values.

Validate first:

```python
orders["order_value"] = pd.to_numeric(
    orders["order_value"],
    errors="coerce",
)
```

Then identify invalid records:

```python
invalid = orders["order_value"].isna()

if invalid.any():
    raise ValueError(
        "Order value contains invalid numeric data."
    )
```

Do not expect `cut()` or `qcut()` to perform general-purpose input cleaning.

Separate:

```text
parsing
```

from:

```text
classification
```

so failures are easier to diagnose.

---

## Binning and Duplicates

Duplicate rows do not inherently cause a problem for `cut()` or `qcut()` because each value can independently be assigned to a category.

The important question is whether duplicate records are valid.

For example:

```text
customer_id | purchase_value
------------|---------------
101         | 500
101         | 500
```

could represent:

- Two purchases.
- A duplicate ingestion.
- Two records from separate systems.

Do not deduplicate merely because a categorical result repeats.

Binning is not a duplicate-removal operation.

---

## Performance Considerations

`cut()` and `qcut()` are substantially more efficient than implementing equivalent classification with Python loops.

Avoid:

```python
def classify(value):
    if value <= 100:
        return "Low"
    if value <= 500:
        return "Medium"
    return "High"


orders["segment"] = orders["order_value"].apply(
    classify
)
```

Prefer:

```python
orders["segment"] = pd.cut(
    orders["order_value"],
    bins=[
        -float("inf"),
        100,
        500,
        float("inf"),
    ],
    labels=[
        "Low",
        "Medium",
        "High",
    ],
)
```

The Pandas implementation is clearer, more declarative, and better aligned with vectorized data processing.

---

## Performance of `qcut()`

`qcut()` must determine quantile boundaries from the data distribution, making it more computationally involved than applying already-known `cut()` boundaries.

For large datasets:

- Compute quantile thresholds once when possible.
- Reuse frozen thresholds for repeated batches.
- Avoid recomputing segmentation boundaries for every API request.
- Push simple fixed-boundary classifications into SQL when practical.
- Precompute recurring reporting segments.

For batch systems, this pattern is often better:

```text
Reference Data
      │
      ▼
Compute Boundaries
      │
      ▼
Persist Versioned Rules
      │
      ▼
Batch Input
      │
      ▼
Apply cut()
      │
      ▼
Curated Output
```

---

## Concurrency and API Requests

A common anti-pattern is computing `qcut()` dynamically for every request:

```text
HTTP request
    │
    ▼
Load large dataset
    │
    ▼
qcut()
    │
    ▼
Return response
```

This can produce high CPU and memory usage and inconsistent segment boundaries across requests.

For FastAPI or Django applications, prefer:

```text
Scheduled batch
    │
    ▼
Compute reference quantiles
    │
    ▼
Store versioned thresholds
    │
    ▼
API reads precomputed classification
```

Redis can be used as a cache for frequently accessed summary results, while PostgreSQL or object storage can retain the authoritative classification data.

---

## Security Considerations

Binning itself has little direct security impact, but segmentation may encode sensitive or commercially important information.

Examples include:

- Credit-risk bands.
- Customer-value segments.
- Employee compensation bands.
- Fraud-risk categories.

Treat generated categories according to the sensitivity of the source data.

For APIs:

```text
Authenticate
    │
    ▼
Authorize
    │
    ▼
Load permitted records
    │
    ▼
Apply classification
    │
    ▼
Return allowed categories
```

Do not assume that replacing a precise numeric field with a category automatically makes the data non-sensitive.

---

## Testing `cut()`

Test boundary behavior explicitly.

```python
import pandas as pd
from pandas.testing import assert_series_equal


def test_cut_assigns_business_value_bands() -> None:
    values = pd.Series(
        [0, 100, 101, 500, 501],
        name="order_value",
    )

    actual = pd.cut(
        values,
        bins=[
            0,
            100,
            500,
            float("inf"),
        ],
        labels=[
            "Low",
            "Medium",
            "High",
        ],
        include_lowest=True,
    )

    expected = pd.Series(
        pd.Categorical(
            [
                "Low",
                "Low",
                "Medium",
                "Medium",
                "High",
            ],
            categories=[
                "Low",
                "Medium",
                "High",
            ],
            ordered=True,
        ),
        name="order_value",
    )

    assert_series_equal(
        actual,
        expected,
    )
```

Boundary tests are more valuable than testing only ordinary values.

---

## Testing `qcut()`

Test category count and expected relative behavior.

```python
def test_qcut_creates_quartile_segments() -> None:
    values = pd.Series(
        range(1, 101),
        name="score",
    )

    result = pd.qcut(
        values,
        q=4,
        labels=[
            "Q1",
            "Q2",
            "Q3",
            "Q4",
        ],
    )

    counts = result.value_counts(
        sort=False
    )

    assert list(counts) == [
        25,
        25,
        25,
        25,
    ]
```

For real-world data with ties, do not assert perfectly equal counts unless the input distribution guarantees them.

Instead, test the expected properties of the segmentation contract.

---

## Testing Out-of-Range Values

A business classification should test values beyond expected ranges:

```python
def test_out_of_range_value_is_unassigned() -> None:
    values = pd.Series(
        [50, 1500],
        name="order_value",
    )

    result = pd.cut(
        values,
        bins=[0, 1000],
        labels=["Valid"],
    )

    assert result.iloc[0] == "Valid"
    assert pd.isna(result.iloc[1])
```

This catches changes in upstream data distribution that silently produce unclassified records.

---

## Common Mistakes

### Using `qcut()` for Stable Business Thresholds

Incorrect:

```python
pd.qcut(
    customers["lifetime_value"],
    q=4,
)
```

when the categories are contractual business tiers.

Use fixed boundaries:

```python
pd.cut(
    customers["lifetime_value"],
    bins=[
        0,
        100,
        500,
        1000,
        float("inf"),
    ],
)
```

---

### Assuming `qcut()` Always Produces the Requested Number of Bins

Tied values can produce duplicate quantile edges.

With:

```python
duplicates="drop"
```

fewer categories may be created.

Always validate the resulting categories when bin count matters.

---

### Ignoring Boundary Semantics

These differ:

```python
right=True
```

and:

```python
right=False
```

A value exactly equal to a threshold may move between categories.

Test boundary values explicitly.

---

### Treating `NaN` as a Valid Segment

Missing category values can indicate:

- Missing input.
- Invalid data.
- Out-of-range values.
- Quantile boundary limitations.

Track them separately.

---

### Using `apply()` Instead of `cut()`

Manual Python classification is often slower and less expressive:

```python
orders["segment"] = orders["order_value"].apply(
    classify
)
```

Use vectorized binning for threshold-based segmentation.

---

### Recomputing Quantiles Per Batch Without Considering Semantics

If a customer's category depends on the current batch's distribution, the same customer or numeric value can move between segments over time.

Decide whether segmentation should be:

```text
relative to the current population
```

or:

```text
stable against a versioned reference population
```

before implementing `qcut()`.

---

## Production Pitfalls

### Data Drift

`cut()` makes boundaries stable but can produce increasing amounts of unclassified or heavily concentrated data as the source distribution changes.

Monitor:

```python
orders["segment"].value_counts(
    normalize=True,
    dropna=False,
)
```

### Quantile Drift

`qcut()` adapts to distribution changes, which may be desirable for ranking but undesirable for reproducible historical reporting.

Persist reference boundaries when stability matters.

### Category Ordering

A report may unexpectedly sort:

```text
High
Low
Medium
```

when categories are plain strings.

Use ordered categoricals for business-ordered values.

### Dynamic Segmentation in User Requests

Do not calculate expensive quantiles over a large dataset for each HTTP request. Precompute or cache where appropriate.

### Unbounded Categories

Avoid using too many unique labels or data-dependent thresholds that effectively turn a categorical column into an unstable schema.

---

## Choosing Between `cut()` and `qcut()`

Use this decision framework:

```mermaid
flowchart TD
    A[Need to bucket numeric data] --> B{Are boundaries business-defined?}

    B -->|Yes| C[Use cut()]
    B -->|No| D{Need approximately equal population per bucket?}

    D -->|Yes| E[Use qcut()]
    D -->|No| F{Need exploratory equal-width ranges?}

    F -->|Yes| G[Use cut with bins=N]
    F -->|No| H[Define an explicit segmentation rule]

    C --> I{Stable across batches?}
    I -->|Yes| J[Version boundaries and labels]
    I -->|No| K[Monitor out-of-range values]

    E --> L{Stable historical categories required?}
    L -->|Yes| M[Compute and persist reference quantile boundaries]
    L -->|No| N[Recompute from current distribution]
```

---

## Recommended Engineering Pattern

Keep classification logic explicit and separate from data loading.

```python
import pandas as pd


VALUE_BINS = [
    0,
    100,
    500,
    1_000,
    float("inf"),
]

VALUE_LABELS = [
    "Low",
    "Standard",
    "Premium",
    "Enterprise",
]


def classify_customer_value(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    required_columns = {"customer_id", "lifetime_value"}

    missing_columns = (
        required_columns.difference(customers.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    result = customers.copy()

    result["lifetime_value"] = pd.to_numeric(
        result["lifetime_value"],
        errors="coerce",
    )

    if result["lifetime_value"].isna().any():
        raise ValueError(
            "Invalid lifetime_value values detected."
        )

    result["value_segment"] = pd.cut(
        result["lifetime_value"],
        bins=VALUE_BINS,
        labels=VALUE_LABELS,
        include_lowest=True,
        ordered=True,
    )

    if result["value_segment"].isna().any():
        raise ValueError(
            "Some customers could not be classified."
        )

    return result
```

This pattern gives the transformation:

- Explicit inputs.
- Explicit boundaries.
- Explicit labels.
- Explicit validation.
- Stable categories.
- Easy unit testing.

---

## Key Takeaways

- `cut()` creates categories from explicit or equal-width boundaries, while `qcut()` creates approximately equal-sized groups based on quantiles.
- Use `cut()` for stable business rules and `qcut()` for relative population-based segmentation; do not confuse contractual thresholds with distribution-derived rankings.
- Boundary semantics, missing values, out-of-range data, tied values, and category ordering must be tested explicitly because they directly affect classification correctness.
- `qcut()` boundaries can drift as the source distribution changes; persist versioned reference boundaries when reproducible historical classification is required.
- Prefer vectorized binning over Python loops or `apply()`, and treat category distributions, unclassified rows, and segmentation drift as production data-quality signals.