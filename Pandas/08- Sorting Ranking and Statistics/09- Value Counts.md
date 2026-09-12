# 09- Value Counts

## Overview

`value_counts()` is a Pandas Series operation used to determine how frequently each distinct value occurs.

It is particularly useful for:

```text
categorical analysis
data profiling
data-quality validation
status distributions
customer behavior
event analysis
ETL diagnostics
reporting
```

The core question is:

```text
How many times does each value occur?
```

For example, an order-status column might contain:

```text
completed
completed
pending
failed
completed
```

Using:

```python
orders["status"].value_counts()
```

produces the frequency of each status.

This makes `value_counts()` different from related operations:

```text
count()
→ number of non-null observations

nunique()
→ number of distinct values

unique()
→ actual distinct values

value_counts()
→ frequency of each distinct value
```

---

## Basic Syntax

The basic form is:

```python
series.value_counts()
```

Example:

```python
status_counts = orders[
    "status"
].value_counts()
```

For:

```text
completed
completed
pending
failed
completed
```

the result is conceptually:

```text
completed    3
pending      1
failed       1
```

The result is a `Series`:

```text
index
→ unique values

values
→ occurrence counts
```

By default, the results are ordered by frequency in descending order.

---

## Example Dataset

```python
import pandas as pd


orders = pd.DataFrame(
    {
        "order_id": [
            "O1001",
            "O1002",
            "O1003",
            "O1004",
            "O1005",
            "O1006",
        ],
        "customer_id": [
            "C101",
            "C102",
            "C101",
            "C103",
            "C102",
            "C101",
        ],
        "status": [
            "completed",
            "completed",
            "pending",
            "failed",
            "completed",
            "completed",
        ],
        "payment_method": [
            "card",
            "upi",
            "card",
            "card",
            "upi",
            "card",
        ],
        "revenue": [
            100.0,
            250.0,
            300.0,
            50.0,
            500.0,
            125.0,
        ],
    }
)
```

Calculate status frequencies:

```python
status_counts = orders[
    "status"
].value_counts()
```

This gives the number of orders in each status.

---

## Why `value_counts()` Exists

Counting distinct values is useful, but the frequency distribution often contains more operational information.

For example:

```python
orders["status"].value_counts()
```

can reveal:

```text
completed    4
pending      1
failed       1
```

A backend engineer can immediately reason about:

```text
business state distribution
processing backlog
failure volume
pipeline anomalies
unexpected categories
```

This is often more actionable than only knowing:

```python
orders["status"].nunique()
```

which would return:

```text
3
```

---

## Output Type

For a Series:

```python
counts = orders[
    "status"
].value_counts()
```

the output is a `Series`.

The index contains the distinct values:

```text
completed
pending
failed
```

The Series values contain their counts:

```text
4
1
1
```

You can inspect them explicitly:

```python
counts.index
counts.to_numpy()
```

Convert the result to a DataFrame for reporting:

```python
status_report = (
    orders["status"]
    .value_counts()
    .rename_axis("status")
    .reset_index(name="count")
)
```

The result becomes:

```text
status       count
-----------  -----
completed       4
pending         1
failed          1
```

This shape is often easier to serialize to JSON, CSV, or an API response.

---

## Default Sorting

`value_counts()` sorts by frequency descending by default.

Example:

```python
counts = orders[
    "status"
].value_counts()
```

The most frequent value appears first.

To sort the resulting counts by the value itself:

```python
counts = (
    orders["status"]
    .value_counts()
    .sort_index()
)
```

This distinction matters when producing deterministic reports.

```text
sort by frequency
→ value_counts()

sort by category/value
→ value_counts().sort_index()
```

---

## `sort` Parameter

The `sort` parameter controls whether the result is sorted by frequency.

```python
counts = orders[
    "status"
].value_counts(
    sort=False
)
```

This avoids frequency sorting.

If deterministic ordering is required, follow it with an explicit sort:

```python
counts = (
    orders["status"]
    .value_counts(sort=False)
    .sort_index()
)
```

Do not rely on incidental ordering when the output is part of a contract.

---

## `ascending`

You can request ascending frequency order:

```python
counts = orders[
    "status"
].value_counts(
    ascending=True
)
```

This is useful when identifying:

```text
least common statuses
rarest categories
small-volume event types
```

For normal frequency reports, descending order is usually easier to interpret.

---

## Missing Values

By default, `value_counts()` excludes missing values.

Example:

```python
statuses = pd.Series(
    [
        "completed",
        "completed",
        "failed",
        None,
    ]
)

counts = statuses.value_counts()
```

The missing value is not included by default.

To include missing values:

```python
counts = statuses.value_counts(
    dropna=False
)
```

This is important for data-quality analysis.

---

## Missing Values as a Category

Including missing values can expose quality issues:

```python
status_counts = orders[
    "status"
].value_counts(
    dropna=False
)
```

For example:

```text
completed    4
pending      1
failed       1
NaN          20
```

A large missing category may indicate:

```text
upstream schema failure
failed transformation
partial API response
database nulls
ingestion issue
```

For production pipelines, this can be more useful than silently excluding missing values.

---

## `normalize`

Set:

```python
normalize=True
```

to return proportions instead of raw counts.

Example:

```python
status_distribution = (
    orders["status"]
    .value_counts(
        normalize=True
    )
)
```

Conceptually:

```text
completed    0.667
pending      0.167
failed       0.167
```

The values sum to approximately:

```text
1.0
```

This is useful for:

```text
percentage reporting
distribution monitoring
cohort analysis
quality metrics
```

---

## Percentage Reporting

Convert normalized counts into percentages:

```python
status_percentages = (
    orders["status"]
    .value_counts(
        normalize=True
    )
    .mul(100)
)
```

For a report:

```python
status_report = (
    orders["status"]
    .value_counts(
        normalize=True
    )
    .mul(100)
    .rename("percentage")
    .rename_axis("status")
    .reset_index()
)
```

This produces an API-friendly table such as:

```text
status       percentage
-----------  ----------
completed        66.67
pending          16.67
failed           16.67
```

---

## `bins`

For numeric data, `value_counts()` can group values into intervals using `bins`.

Example:

```python
revenue_bands = orders[
    "revenue"
].value_counts(
    bins=3
)
```

This creates interval-based frequency counts.

For business reporting, explicit boundaries can be easier to understand using `pd.cut()`:

```python
orders["revenue_band"] = pd.cut(
    orders["revenue"],
    bins=[
        0,
        100,
        500,
        1000,
        float("inf"),
    ],
    labels=[
        "0-100",
        "101-500",
        "501-1000",
        "1000+",
        ],
    include_lowest=True,
)
```

Then:

```python
revenue_distribution = (
    orders["revenue_band"]
    .value_counts(
        sort=False
    )
)
```

Use explicit business bands when the intervals themselves have domain meaning.

---

## `dropna` and `normalize` Together

For a data-quality report:

```python
status_distribution = (
    orders["status"]
    .value_counts(
        normalize=True,
        dropna=False,
    )
)
```

This answers:

```text
What percentage of all rows belongs to each observed status,
including missing status values?
```

This can be useful for schema monitoring and upstream reliability checks.

---

## `value_counts()` Versus `count()`

Consider:

```text
status
------
completed
completed
failed
pending
None
```

Then:

```python
orders["status"].count()
```

returns:

```text
4
```

while:

```python
orders["status"].value_counts()
```

returns frequencies for each distinct non-null status.

They answer different questions:

| Operation | Question |
| --- | --- |
| `count()` | How many non-null values exist? |
| `nunique()` | How many distinct non-null values exist? |
| `unique()` | Which distinct values exist? |
| `value_counts()` | How frequently does each value occur? |

---

## `value_counts()` Versus `nunique()`

Example:

```python
unique_statuses = orders[
    "status"
].nunique()

status_counts = orders[
    "status"
].value_counts()
```

The first returns:

```text
3
```

The second returns something like:

```text
completed    4
pending      1
failed       1
```

Use `nunique()` when only the number of categories matters.

Use `value_counts()` when frequency distribution matters.

---

## `value_counts()` Versus `unique()`

```python
statuses = orders[
    "status"
].unique()
```

returns the actual distinct values.

```python
status_counts = orders[
    "status"
].value_counts()
```

returns the frequency of each value.

Use:

```text
unique()
→ membership

value_counts()
→ distribution
```

---

## `value_counts()` Versus `groupby().size()`

For categorical counts, these can produce similar results:

```python
orders["status"].value_counts()
```

and:

```python
orders.groupby(
    "status"
).size()
```

But `value_counts()` is the more direct API for one-column frequency analysis.

Use `groupby()` when the requirement involves multiple grouping dimensions or additional aggregations.

For example:

```python
orders.groupby(
    ["customer_id", "status"]
).size()
```

is naturally expressed with `groupby()`.

---

## Grouped Frequency Analysis

For status counts per customer:

```python
customer_status_counts = (
    orders
    .groupby(
        "customer_id"
    )["status"]
    .value_counts()
)
```

This produces a MultiIndex Series:

```text
customer_id  status
C101         completed    2
             pending       1
C102         completed    2
C103         failed        1
```

To make it a DataFrame:

```python
customer_status_report = (
    orders
    .groupby(
        "customer_id"
    )["status"]
    .value_counts()
    .rename("count")
    .reset_index()
)
```

This is useful for:

```text
customer behavior
tenant state analysis
service usage
workflow monitoring
```

---

## Frequency by Multiple Dimensions

Suppose an operations report needs:

```text
region
+
order status
+
frequency
```

Use:

```python
regional_status_counts = (
    orders
    .groupby(
        "region"
    )["status"]
    .value_counts()
    .rename("count")
    .reset_index()
)
```

The output grain becomes:

```text
one row = one region/status combination
```

Always identify this grain before using the result downstream.

---

## `groupby().value_counts()`

This pattern is particularly useful because it avoids manually constructing nested loops or repeated filters.

Example:

```python
payment_status_counts = (
    orders
    .groupby(
        "payment_method"
    )["status"]
    .value_counts()
)
```

The resulting MultiIndex represents:

```text
payment method
    ↓
status
    ↓
frequency
```

It can be converted into a flat report:

```python
payment_status_report = (
    payment_status_counts
    .rename("count")
    .reset_index()
)
```

---

## API and Reporting Example

A FastAPI endpoint might return a status distribution:

```python
from fastapi import FastAPI


app = FastAPI()


@app.get("/orders/status-summary")
def order_status_summary() -> list[dict[str, object]]:
    report = (
        orders["status"]
        .value_counts(
            dropna=False
        )
        .rename_axis("status")
        .reset_index(name="count")
    )

    return report.to_dict(
        orient="records"
    )
```

The returned structure is suitable for JSON:

```json
[
  {
    "status": "completed",
    "count": 4
  },
  {
    "status": "pending",
    "count": 1
  },
  {
    "status": "failed",
    "count": 1
  }
]
```

In production, the DataFrame should normally be created from an appropriately scoped database query or service response rather than global in-memory state.

---

## SQL Equivalent

The SQL equivalent is:

```sql
SELECT
    status,
    COUNT(*) AS count
FROM orders
GROUP BY status
ORDER BY count DESC;
```

This maps conceptually to:

```python
orders["status"].value_counts()
```

The SQL form is often preferable when the source is already a database and the table is large.

---

## Database Pushdown

For millions of rows:

```text
PostgreSQL
    ↓
GROUP BY status
    ↓
small result
    ↓
Pandas
```

is usually more efficient than:

```text
PostgreSQL
    ↓
millions of rows
    ↓
Pandas
    ↓
value_counts()
```

Example:

```sql
SELECT
    status,
    COUNT(*) AS count
FROM orders
WHERE created_at >= :start_time
  AND created_at < :end_time
GROUP BY status;
```

Push filtering and aggregation into PostgreSQL when the database can execute them efficiently.

---

## Data Quality Validation

`value_counts()` can be used to detect unexpected categories.

Example:

```python
status_counts = orders[
    "status"
].value_counts(
    dropna=False
)

allowed_statuses = {
    "pending",
    "processing",
    "completed",
    "failed",
}

observed_statuses = set(
    orders["status"].dropna().unique()
)

unexpected_statuses = (
    observed_statuses
    - allowed_statuses
)

if unexpected_statuses:
    raise ValueError(
        "Unexpected statuses: "
        f"{sorted(unexpected_statuses)}"
    )
```

Frequency analysis shows what occurred.

Validation determines whether what occurred was acceptable.

---

## Detecting Rare Categories

Rare values can indicate:

```text
legitimate edge cases
new business states
data corruption
typos
upstream schema changes
```

Example:

```python
status_counts = orders[
    "status"
].value_counts()

rare_statuses = status_counts[
    status_counts < 10
]
```

Do not automatically classify rare values as invalid.

A low-frequency event may be completely legitimate.

---

## Detecting Dominant Categories

A useful monitoring check is the share of the most common value:

```python
status_distribution = (
    orders["status"]
    .value_counts(
        normalize=True
    )
)

dominant_share = (
    status_distribution.iloc[0]
)
```

A sudden shift in the dominant category may indicate:

```text
workflow failure
traffic change
product rollout
upstream bug
processing backlog
```

The threshold should be based on historical behavior rather than an arbitrary constant.

---

## Data Profiling

`value_counts()` is useful during ingestion profiling.

Example:

```python
profile = {
    "row_count": len(orders),
    "unique_customers": orders[
        "customer_id"
    ].nunique(),
    "status_distribution": (
        orders["status"]
        .value_counts(
            dropna=False
        )
        .to_dict()
    ),
}
```

This creates a compact snapshot of:

```text
volume
cardinality
category distribution
missingness
```

Such profiling is useful in ETL validation and pipeline debugging.

---

## Normalizing Categories Before Counting

Values that are semantically identical may appear differently:

```text
completed
Completed
 COMPLETED
```

Direct `value_counts()` treats them as different.

Normalize first when the business definition requires case-insensitive matching:

```python
normalized_status = (
    orders["status"]
    .astype("string")
    .str.strip()
    .str.lower()
)

status_counts = (
    normalized_status
    .value_counts(
        dropna=False
    )
)
```

Do not normalize categories blindly. Case and whitespace may be semantically meaningful in some domains.

---

## Incorrect Data Types

A numeric identifier may arrive as:

```text
1001
"1001"
1001.0
```

These can produce unexpected distinct categories if mixed without normalization.

For identifiers, establish a consistent representation:

```python
orders["order_id"] = (
    orders["order_id"]
    .astype("string")
    .str.strip()
)
```

Then:

```python
order_id_counts = (
    orders["order_id"]
    .value_counts()
)
```

This helps distinguish true duplicates from representation differences.

---

## Duplicate Records

Suppose an event table contains:

```text
event_id
--------
E1001
E1001
E1002
```

Then:

```python
event_counts = events[
    "event_id"
].value_counts()
```

returns:

```text
E1001    2
E1002    1
```

This is a useful diagnostic for repeated event IDs.

However, repeated values are not automatically duplicates.

For example:

```text
customer_id
C101
C101
C101
```

is entirely valid in an order table.

Always evaluate repetition against the table's intended row grain.

---

## Top-N Categories

For the most frequent statuses:

```python
top_statuses = (
    orders["status"]
    .value_counts()
    .head(3)
)
```

For the least frequent:

```python
least_common = (
    orders["status"]
    .value_counts()
    .tail(3)
)
```

When ties or deterministic ordering matter, define the ordering explicitly after counting.

---

## Frequencies After Filtering

The population should be filtered before counting.

Example:

```python
completed_orders = orders.loc[
    orders["status"].eq("completed")
]

customer_frequency = (
    completed_orders["customer_id"]
    .value_counts()
)
```

This answers:

```text
How many completed orders did each customer place?
```

It does not answer:

```text
How many total orders did each customer place?
```

The filtering rule is part of the metric definition.

---

## Time-Based Frequency Analysis

For event data:

```python
events["event_time"] = pd.to_datetime(
    events["event_time"],
    utc=True,
    errors="raise",
)

events["event_date"] = (
    events["event_time"]
    .dt.floor("D")
)

daily_event_counts = (
    events["event_date"]
    .value_counts()
    .sort_index()
)
```

This produces event volume per day.

For time-series reporting, `groupby()` or resampling may be preferable when you need multiple metrics per period.

---

## `value_counts()` and Categorical Dtypes

For low-cardinality dimensions:

```python
orders["status"] = orders[
    "status"
].astype("category")
```

Then:

```python
status_counts = orders[
    "status"
].value_counts()
```

Categorical data can reduce memory use for large datasets with many repeated values.

However, categorical behavior should be chosen based on workload and semantics, not simply because a column has strings.

---

## Empty Series

For an empty Series:

```python
empty = pd.Series(
    dtype="string"
)

counts = empty.value_counts()
```

the result is an empty Series.

Production reports should define whether:

```text
empty distribution
```

means:

```text
no records
```

or:

```text
upstream failure
```

Do not interpret absence of categories as zero activity without considering the pipeline's execution and filtering context.

---

## Performance Considerations

`value_counts()` requires determining distinct values and their frequencies.

Performance depends on:

```text
number of rows
cardinality
dtype
missing values
grouping dimensions
memory availability
```

Low-cardinality fields such as:

```text
status
country
region
```

are typically cheaper to analyze than high-cardinality identifiers.

For:

```text
millions of unique IDs
```

the distinct-value tracking itself can consume significant memory.

---

## High-Cardinality Columns

Avoid unnecessary full frequency analysis of enormous identifier columns.

For example:

```python
orders["transaction_id"].value_counts()
```

can be expensive when nearly every transaction ID is unique.

If the actual requirement is only:

```text
number of unique transaction IDs
```

use:

```python
orders["transaction_id"].nunique()
```

If the requirement is:

```text
detect duplicate transaction IDs
```

consider:

```python
duplicates = (
    orders["transaction_id"]
    .value_counts()
)

duplicates = duplicates[
    duplicates > 1
]
```

This narrows the downstream result to repeated identifiers.

---

## Chunked Processing

Frequency counting across batches is not as simple as summing a scalar.

A useful incremental pattern is to maintain counts per value:

```python
from collections import Counter


global_counts = Counter()

for batch in batches:
    batch_counts = (
        batch["status"]
        .value_counts()
        .to_dict()
    )

    global_counts.update(
        batch_counts
    )

global_status_counts = pd.Series(
    global_counts,
    dtype="int64",
).sort_values(
    ascending=False
)
```

This works because frequency counts are additive:

```text
global frequency
=
sum of per-batch frequencies
```

Unlike distinct counts, repeated values across batches should be counted repeatedly because they represent separate observations.

---

## Distributed Processing

Frequency counting is naturally composable:

```text
partition 1
    ↓
value frequencies

partition 2
    ↓
value frequencies

partition 3
    ↓
value frequencies

        ↓

merge frequency maps
        ↓
global frequencies
```

This makes frequency aggregation suitable for:

```text
SQL GROUP BY
Spark
MapReduce-style processing
warehouse aggregation
batch pipelines
```

Pandas remains appropriate when the working set fits within process memory.

---

## Monitoring and Observability

A service or ETL pipeline can emit category distributions as metrics.

Example:

```python
status_counts = (
    orders["status"]
    .value_counts(
        dropna=False
    )
)

observability = {
    "rows": len(orders),
    "completed": int(
        status_counts.get(
            "completed",
            0,
        )
    ),
    "failed": int(
        status_counts.get(
            "failed",
            0,
        )
    ),
    "pending": int(
        status_counts.get(
            "pending",
            0,
        )
    ),
}
```

Track these values over time rather than only looking at a single batch.

Useful alerts include:

```text
unexpected category appears
failure share exceeds threshold
missing-value share increases
dominant category changes sharply
total frequency differs from expected row count
```

---

## Security Considerations

Frequency distributions can reveal sensitive information.

Examples:

```text
number of customers by region
number of employees by department
number of accounts by status
number of users in a tenant
```

Apply authorization before aggregation.

For tenant-scoped reporting:

```python
authorized = orders.loc[
    orders["tenant_id"].isin(
        authorized_tenant_ids
    )
].copy()

status_counts = (
    authorized["status"]
    .value_counts()
)
```

Do not expose global frequency distributions through tenant-specific APIs.

---

## Reliability Considerations

A production frequency metric should define:

```text
source
reporting period
population filter
row grain
null policy
normalization policy
duplicate policy
timezone
aggregation semantics
```

For example:

```text
Metric: Failed Order Count
Population: orders created during reporting window
Grain: one row per order
Status normalization: lowercase and trimmed
Null status: reported separately
Duplicates: order_id must be unique
Calculation: value_counts()["failed"]
Timezone: UTC
```

This prevents apparently identical metrics from being calculated differently by different services.

---

## Testing

Test both frequencies and missing-value behavior.

```python
def test_status_value_counts() -> None:
    statuses = pd.Series(
        [
            "completed",
            "completed",
            "pending",
            "failed",
            None,
        ]
    )

    counts = statuses.value_counts(
        dropna=False
    )

    assert counts["completed"] == 2
    assert counts["pending"] == 1
    assert counts["failed"] == 1
    assert counts.isna().sum() == 1
```

A more robust assertion can verify the complete expected distribution:

```python
expected = pd.Series(
    {
        "completed": 2,
        "pending": 1,
        "failed": 1,
        None: 1,
    },
    dtype="int64",
)

actual = statuses.value_counts(
    dropna=False
)

assert (
    actual.sort_index(
        key=lambda index: index.astype("string")
    )
    .equals(
        expected.sort_index(
            key=lambda index: index.astype("string")
        )
    )
)
```

For production test suites, prefer assertions that directly verify the business behavior and expected schema.

---

## Common Mistakes

### Using `count()` Instead of `value_counts()`

Incorrect:

```python
orders["status"].count()
```

when the requirement is:

```text
number of orders in each status
```

Use:

```python
orders["status"].value_counts()
```

---

### Forgetting Missing Values

By default:

```python
value_counts()
```

excludes missing values.

When missingness is operationally important:

```python
value_counts(
    dropna=False
)
```

should be considered.

---

### Counting Before Filtering

Incorrect:

```python
status_counts = (
    orders["status"]
    .value_counts()
)

completed_orders = orders.loc[
    orders["status"].eq("completed")
]
```

when the actual requirement concerns a filtered population.

Define the population first.

---

### Treating Categories as Normalized

These may be counted separately:

```text
Completed
completed
 completed
COMPLETED
```

Normalize only when the business semantics require it.

---

### Running Frequency Counts on High-Cardinality IDs Unnecessarily

This:

```python
df["event_id"].value_counts()
```

may create a very large result and consume significant memory.

Use `nunique()` when only cardinality is required.

---

### Assuming Rare Means Invalid

A category occurring once may represent:

```text
valid edge case
new feature
production incident
data corruption
```

Frequency alone is not a validation rule.

---

### Summing Normalized Frequencies Incorrectly

Normalized frequencies describe proportions of the current population.

Do not combine percentages across batches by simple addition.

Combine raw counts first, then normalize:

```text
batch counts
    ↓
global counts
    ↓
global normalization
```

---

## Interview Traps

### Count Frequencies of a Column

Question:

> How many times does each status occur?

Answer:

```python
df["status"].value_counts()
```

---

### Include Missing Values

Question:

> How do you include null values in the frequency distribution?

Answer:

```python
df["status"].value_counts(
    dropna=False
)
```

---

### Convert Counts to Percentages

Use:

```python
df["status"].value_counts(
    normalize=True
)
```

---

### Find the Most Common Value

Use:

```python
most_common = (
    df["status"]
    .value_counts()
    .index[0]
)
```

For an empty Series, this needs explicit handling because there may be no first element.

A safer production pattern is:

```python
counts = df["status"].value_counts()

most_common = (
    counts.index[0]
    if not counts.empty
    else None
)
```

---

### Find Duplicate Identifiers

```python
duplicate_counts = (
    df["event_id"]
    .value_counts()
)

duplicates = duplicate_counts[
    duplicate_counts > 1
]
```

This identifies IDs appearing more than once without assuming every repeated value is invalid.

---

## Production Checklist

Before using `value_counts()` in a production pipeline, verify:

```text
[ ] Correct population selected
[ ] Correct row grain defined
[ ] Null behavior decided
[ ] Category normalization defined
[ ] Duplicate semantics understood
[ ] Frequency vs distinct-count requirement confirmed
[ ] High-cardinality impact evaluated
[ ] Deterministic sorting defined
[ ] Empty-input behavior defined
[ ] Database pushdown considered
[ ] Batch aggregation logic validated
[ ] Distribution monitored over time
```

---

## Key Takeaways

- `value_counts()` measures the frequency of each distinct value and is the direct Pandas operation for categorical distributions, data profiling, and operational reporting.
- Use `count()`, `nunique()`, `unique()`, and `value_counts()` for different questions: observations, cardinality, distinct values, and frequency distribution respectively.
- Missing values are excluded by default; use `dropna=False` when null frequency is itself an important data-quality or reporting signal.
- Define the population, normalization rules, row grain, and duplicate semantics before counting; filtering or normalization mistakes can create misleading distributions.
- For large or high-cardinality datasets, prefer database-side aggregation when appropriate and avoid materializing large frequency tables when only a scalar metric is required.