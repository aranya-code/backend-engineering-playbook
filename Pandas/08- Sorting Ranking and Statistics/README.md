# README.md

## Overview

The **Sorting, Ranking and Statistics** section covers the Pandas operations used to order data, compare observations, calculate descriptive statistics, and build cumulative metrics.

These operations become useful after data has already been loaded, selected, cleaned, transformed, grouped, or combined.

The section progresses from simple ordering to increasingly analytical operations:

```text
Sort Data
    ↓
Rank Observations
    ↓
Describe Distributions
    ↓
Calculate Aggregates
    ↓
Count and Measure Cardinality
    ↓
Analyze Frequencies
    ↓
Measure Quantiles
    ↓
Analyze Correlation
    ↓
Analyze Covariance
    ↓
Calculate Cumulative Metrics
```

| # | File | Description |
|---|---|---|
| 01 | [01- Sort Values](./01-%20Sort%20Values.md) | Order rows by one or more columns |
| 02 | [02- Sort Index](./02-%20Sort%20Index.md) | Order data by its index |
| 03 | [03- Ranking](./03-%20Ranking.md) | Assign relative positions to observations |
| 04 | [04- Rank](./04-%20Rank.md) | Work directly with `Series.rank()` and ranking strategies |
| 05 | [05- Descriptive Statistics](./05-%20Descriptive%20Statistics.md) | Produce broad statistical summaries |
| 06 | [06- Sum Mean Median](./06-%20Sum%20Mean%20Median.md) | Calculate totals and central-tendency metrics |
| 07 | [07- Min Max](./07-%20Min%20Max.md) | Identify observed boundaries and extremes |
| 08 | [08- Count And Nunique](./08-%20Count%20And%20Nunique.md) | Measure observations and distinct entities |
| 09 | [09- Value Counts](./09-%20Value%20Counts.md) | Analyze category and value frequencies |
| 10 | [10- Quantiles](./10-%20Quantiles.md) | Measure distribution thresholds |
| 11 | [11- Correlation](./11-%20Correlation.md) | Measure standardized association between variables |
| 12 | [12- Covariance](./12-%20Covariance.md) | Measure directional co-movement between variables |
| 13 | [13- Cumulative Operations](./13-%20Cumulative%20Operations.md) | Calculate running totals, extrema, and products |

The focus is not statistical theory for its own sake. The goal is to use Pandas statistics correctly inside:

```text
backend services
ETL pipelines
analytics workflows
financial reporting
operational monitoring
data-quality systems
batch processing
```

---

## Section Structure

| File | Topic | Primary Purpose |
| --- | --- | --- |
| `01- Sort Values.md` | Sort Values | Order rows by one or more columns |
| `02- Sort Index.md` | Sort Index | Order data by its index |
| `03- Ranking.md` | Ranking | Assign relative positions to observations |
| `04- Rank.md` | Rank | Work directly with `Series.rank()` and ranking strategies |
| `05- Descriptive Statistics.md` | Descriptive Statistics | Produce broad statistical summaries |
| `06- Sum Mean Median.md` | Sum, Mean, Median | Calculate totals and central-tendency metrics |
| `07- Min Max.md` | Min, Max | Identify observed boundaries and extremes |
| `08- Count And Nunique.md` | Count and Nunique | Measure observations and distinct entities |
| `09- Value Counts.md` | Value Counts | Analyze category and value frequencies |
| `10- Quantiles.md` | Quantiles | Measure distribution thresholds |
| `11- Correlation.md` | Correlation | Measure standardized association between variables |
| `12- Covariance.md` | Covariance | Measure directional co-movement between variables |
| `13- Cumulative Operations.md` | Cumulative Operations | Calculate running totals, extrema, and products |

---
## Section Structure

The section should be understood as a progression from **ordering data** to **describing distributions** and finally to **analyzing relationships and historical state**.

### Sorting

Sorting establishes a useful deterministic order:

```python
orders = orders.sort_values(
    ["created_at", "order_id"],
    kind="stable",
)
```

This is especially important before:

```text
ranking
cumulative calculations
time-series analysis
top-N reporting
```

A cumulative calculation over incorrectly ordered rows is logically incorrect even when the Pandas syntax is valid.

---

### Ranking

Ranking converts raw values into relative positions.

```python
orders["revenue_rank"] = (
    orders["revenue"]
    .rank(
        method="dense",
        ascending=False,
    )
)
```

Typical applications include:

```text
top customers
highest-value orders
employee performance ranking
regional comparisons
leaderboards
```

Ranking is different from sorting because sorting changes row order while ranking adds a relative position to each observation.

---

### Descriptive Statistics

Descriptive statistics provide a compact view of a distribution:

```python
stats = orders[
    "revenue"
].describe()
```

Typical metrics include:

```text
count
mean
std
min
quantiles
max
```

The statistic should always be interpreted alongside:

```text
population
grain
time period
missing-value policy
```

---

## Aggregation Metrics

Several files focus on individual statistical operations.

### Sum

```python
total_revenue = orders[
    "revenue"
].sum()
```

Answers:

```text
What is the total?
```

Typical uses:

```text
revenue
cost
units
usage
transactions
```

---

### Mean

```python
average_order_value = orders[
    "revenue"
].mean()
```

Answers:

```text
What is the arithmetic average?
```

Mean is sensitive to extreme observations.

---

### Median

```python
median_order_value = orders[
    "revenue"
].median()
```

Answers:

```text
What is the central observation?
```

Median is often useful for skewed operational and financial distributions.

---

### Minimum and Maximum

```python
minimum = orders[
    "revenue"
].min()

maximum = orders[
    "revenue"
].max()
```

These identify observed boundaries.

They are useful for:

```text
validation
anomaly investigation
operational monitoring
range analysis
```

A maximum is not the same as a percentile such as p99.

---

## Count and Cardinality

The section distinguishes several concepts that are commonly confused.

```text
len(df)
→ number of rows

Series.count()
→ non-null observations

Series.nunique()
→ distinct non-null values

Series.value_counts()
→ frequency of each value
```

For example:

```python
order_count = len(orders)

customer_observations = orders[
    "customer_id"
].count()

unique_customers = orders[
    "customer_id"
].nunique()
```

These metrics answer different business questions and should not be substituted for one another.

---

## Frequency Analysis

`value_counts()` is particularly useful for categorical data:

```python
status_counts = orders[
    "status"
].value_counts(
    dropna=False
)
```

This supports:

```text
data profiling
quality checks
status monitoring
category analysis
distribution reporting
```

For example:

```text
completed    95,000
pending       3,000
failed        2,000
```

may immediately expose changes in operational behavior.

---

## Quantiles

Quantiles describe the position of observations within a distribution.

For example:

```python
latency = requests[
    "latency_ms"
]

p50 = latency.quantile(0.50)
p95 = latency.quantile(0.95)
p99 = latency.quantile(0.99)
```

This is especially useful for:

```text
API latency
processing time
transaction value
customer behavior
resource consumption
```

Quantiles are often more informative than minimum and maximum for operational metrics because a single extreme observation can make the maximum unstable.

For example:

```text
min  → fastest request
p50  → typical request
p95  → high-end normal behavior
p99  → tail behavior
max  → slowest observed request
```

---

## Correlation

Correlation measures standardized association.

```python
correlation = requests[
    "payload_kb"
].corr(
    requests["latency_ms"]
)
```

The result lies between:

```text
-1 and +1
```

Correlation is useful for investigating questions such as:

```text
Does larger payload size tend to accompany higher latency?
Does order quantity tend to increase with revenue?
```

It does not establish causation.

---

## Covariance

Covariance measures directional co-movement without standardizing the result.

```python
covariance = orders[
    "quantity"
].cov(
    orders["revenue"]
)
```

Covariance is scale-dependent.

That makes it useful for some mathematical and financial workflows, while correlation is often easier to interpret when comparing relationships across different variables.

---

## Cumulative Operations

Cumulative operations retain state as rows progress.

```python
orders["running_revenue"] = (
    orders["revenue"]
    .cumsum()
)
```

Other important operations include:

```python
orders["running_max"] = (
    orders["revenue"]
    .cummax()
)

orders["running_min"] = (
    orders["revenue"]
    .cummin()
)
```

These are useful for:

```text
running revenue
inventory
account balances
peak traffic
capacity consumption
record detection
```

Unlike ordinary aggregations, cumulative operations depend on row order.

---

## Statistical Mental Model

A useful way to organize the section is:

```text
Ordering
    ↓
"Where should the rows appear?"

Ranking
    ↓
"How does each row compare to others?"

Aggregation
    ↓
"What is the total, average, boundary, or count?"

Distribution
    ↓
"How are values spread across the population?"

Relationship
    ↓
"How do variables move together?"

Cumulative State
    ↓
"How does the result evolve over time?"
```

This mental model prevents selecting an operation merely because its API name looks convenient.

---

## Common Business Questions

| Business Question | Typical Pandas Operation |
| --- | --- |
| What are the highest-value orders? | `sort_values()` / `nlargest()` |
| What is each customer's rank? | `rank()` |
| What is the overall revenue? | `sum()` |
| What is average order value? | `mean()` |
| What is the typical order value in a skewed dataset? | `median()` |
| What is the lowest inventory level? | `min()` / `cummin()` |
| What is the highest observed latency? | `max()` |
| How many orders exist? | `len(df)` |
| How many unique customers exist? | `nunique()` |
| How often does each status occur? | `value_counts()` |
| What is p95 latency? | `quantile(0.95)` |
| Is payload size associated with latency? | `corr()` |
| How do two variables co-move in raw units? | `cov()` |
| What is revenue accumulated so far? | `cumsum()` |

---

## Population and Grain

A statistic is only meaningful when the observation population and grain are defined.

Suppose:

```text
one row = one order
```

Then:

```python
orders["revenue"].mean()
```

means:

```text
average order value
```

It does not mean:

```text
average customer revenue
```

To calculate average customer spend:

```python
customer_totals = (
    orders
    .groupby("customer_id", as_index=False)
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

The observation grain changed from:

```text
order
```

to:

```text
customer
```

This is one of the most important concepts in analytical Pandas code.

---

## Ordering Before Time-Based Analysis

Time-dependent statistics should generally establish deterministic ordering.

```python
events = (
    events
    .sort_values(
        [
            "event_time",
            "event_id",
        ],
        kind="stable",
    )
    .copy()
)
```

This matters for:

```text
rank
cumulative operations
rolling calculations
event reconstruction
time-series reports
```

Do not rely on incidental DataFrame or SQL result ordering.

---

## Missing Values

Statistics often ignore missing values by default, but that does not mean missingness is irrelevant.

Example:

```python
average = orders[
    "revenue"
].mean()

missing_count = orders[
    "revenue"
].isna().sum()
```

A production report may need both:

```text
metric
+
data completeness
```

For example:

```text
average revenue = 1,250
revenue null rate = 4.8%
```

is more informative than publishing the average alone.

---

## Duplicates

Duplicate records can distort almost every statistic in this section:

```text
sum
mean
median
min
max
count
quantiles
correlation
covariance
cumulative metrics
```

Before calculating authoritative metrics, validate the intended business key.

```python
duplicate_ids = (
    orders["order_id"]
    .value_counts()
)

duplicate_ids = duplicate_ids[
    duplicate_ids > 1
]
```

Do not automatically deduplicate a foreign key such as `customer_id`. Repeated foreign keys are often valid.

Duplicate handling must follow the actual row-grain contract.

---

## Incorrect Dtypes

Statistical methods depend on meaningful dtypes.

External values may arrive as strings:

```text
"100"
"250"
"5000"
```

Normalize before statistical processing:

```python
orders["revenue"] = pd.to_numeric(
    orders["revenue"],
    errors="raise",
)
```

Datetime columns should also be parsed explicitly:

```python
orders["created_at"] = pd.to_datetime(
    orders["created_at"],
    utc=True,
    errors="raise",
)
```

Do not allow an upstream schema problem to become a downstream statistical problem.

---

## Units and Currency

Statistical calculations must use semantically compatible units.

Avoid mixing:

```text
USD + EUR
milliseconds + seconds
kilograms + pounds
```

without normalization.

This is especially important for:

```text
sum
mean
covariance
cumulative metrics
```

Correlation is less sensitive to positive scale changes mathematically, but malformed or inconsistently transformed input can still make the analysis invalid.

---

## SQL Relationship

Many operations in this section have direct SQL equivalents.

| Pandas | SQL Concept |
| --- | --- |
| `sum()` | `SUM()` |
| `mean()` | `AVG()` |
| `min()` | `MIN()` |
| `max()` | `MAX()` |
| `count()` | `COUNT(column)` |
| `nunique()` | `COUNT(DISTINCT column)` |
| `value_counts()` | `GROUP BY ... COUNT(*)` |
| `quantile()` | Percentile functions |
| `corr()` | `CORR()` where supported |
| `cov()` | Covariance aggregate |
| `cumsum()` | `SUM() OVER (...)` |
| `cummax()` | `MAX() OVER (...)` |
| `cummin()` | `MIN() OVER (...)` |
| `rank()` | `RANK()` / `DENSE_RANK()` / `ROW_NUMBER()` |

Understanding this mapping helps engineers decide where the computation should occur.

---

## Database Pushdown

If the source is a large PostgreSQL table, avoid loading millions of rows into Pandas solely to calculate a scalar metric.

Prefer:

```text
PostgreSQL
    ↓
WHERE
    ↓
GROUP BY / aggregate / window function
    ↓
small result
    ↓
Pandas
```

instead of:

```text
PostgreSQL
    ↓
millions of rows
    ↓
network transfer
    ↓
Pandas
    ↓
aggregate
```

Pushdown can reduce:

```text
network usage
memory usage
worker CPU
processing time
```

Pandas remains appropriate when the working dataset is already local and manageable or when downstream transformations require Python-side processing.

---

## API Data

For REST API workflows:

```text
API
    ↓
pagination
    ↓
raw records
    ↓
schema normalization
    ↓
data-quality validation
    ↓
Pandas statistics
```

Never calculate a supposedly global metric from a single API page unless page-level scope is intentional.

For example:

```python
page_counts = (
    page_df["status"]
    .value_counts()
)
```

describes the current page.

A global report requires complete population handling.

---

## Parquet Data

Parquet is particularly useful when working with large analytical datasets.

Read only the columns needed for the statistic:

```python
orders = pd.read_parquet(
    "orders.parquet",
    columns=[
        "created_at",
        "customer_id",
        "revenue",
        "status",
    ],
)
```

Column projection reduces:

```text
I/O
memory
deserialization
processing overhead
```

For partitioned datasets, filtering by partition-compatible columns can reduce the amount of data read.

---

## ETL Pattern

A production ETL workflow commonly follows:

```mermaid
flowchart LR
    Source[PostgreSQL / API / CSV / Parquet] --> Ingest[Ingest]
    Ingest --> Normalize[Normalize Dtypes and Units]
    Normalize --> Validate[Validate Schema, Nulls, Duplicates]
    Validate --> Scope[Define Population]
    Scope --> Order[Sort When Order Matters]
    Order --> Analyze[Statistics / Ranking / Cumulative Metrics]
    Analyze --> Quality[Validate Outputs]
    Quality --> Publish[Report / API / Warehouse]
```

The important principle is:

```text
do not calculate first and validate later
```

Metric generation should follow population and data-quality decisions.

---

## Performance Considerations

Not all operations in this section have equal cost.

| Operation | Typical Cost Profile |
| --- | --- |
| `sum()` / `count()` | Low |
| `min()` / `max()` | Low |
| `mean()` | Low |
| `nunique()` | Higher for high-cardinality data |
| `value_counts()` | Depends heavily on cardinality |
| `rank()` | Requires ordering |
| `quantile()` | More expensive than simple reductions |
| `corr()` | Pairwise computation |
| `cov()` | Pairwise computation |
| `cumsum()` | Usually linear once ordered |
| `sort_values()` | Often `O(n log n)` |

The largest cost in a statistical pipeline is frequently not the statistic itself.

It may be:

```text
database extraction
sorting
joining
copying
type conversion
memory pressure
```

Optimize the entire data flow rather than one method in isolation.

---

## High-Cardinality Data

Operations that track unique values can become expensive:

```python
df["request_id"].value_counts()
```

If nearly every identifier is unique, the result may contain millions of rows.

Use the smallest operation that satisfies the requirement:

```python
df["request_id"].nunique()
```

when only the distinct count is required.

Likewise, avoid constructing a complete correlation or covariance matrix when only one pair is needed.

---

## Cumulative and Incremental Processing

Some metrics combine naturally across batches:

```text
sum
count
min
max
frequency counts
```

Other metrics require more state:

```text
distinct counts
mean
quantiles
correlation
covariance
```

Cumulative operations also require ordered state.

For example:

```text
previous total
+
current batch
=
new cumulative state
```

For distributed or streaming pipelines, persist checkpoints and define replay and late-data behavior.

---

## Monitoring and Data Quality

Statistical metrics themselves can become observability signals.

Track:

```text
row count
null rate
duplicate rate
unique entity count
minimum
maximum
mean
median
selected quantiles
category distribution
```

For operational data:

```python
metrics = {
    "row_count": len(events),
    "error_count": events[
        "status"
    ].eq("error").sum(),
    "p95_latency_ms": events[
        "latency_ms"
    ].quantile(0.95),
    "max_latency_ms": events[
        "latency_ms"
    ].max(),
}
```

Monitor both:

```text
the value
+
the population that produced the value
```

A metric change may be caused by a change in data volume, completeness, or composition rather than a real business change.

---

## Statistical Interpretation

A senior engineer should distinguish:

```text
descriptive statistic
→ describes observed data

validation rule
→ determines whether observed data is acceptable

monitoring signal
→ detects unexpected change

causal claim
→ explains why a change occurred
```

For example:

```python
correlation = (
    payload["payload_kb"]
    .corr(payload["latency_ms"])
)
```

can describe association.

It cannot, by itself, prove:

```text
larger payloads caused higher latency
```

The same distinction applies to covariance and many other statistical measures.

---

## Testing Strategy

Tests should validate business meaning, not only method execution.

Examples:

```text
expected total revenue
expected number of unique customers
expected category frequencies
expected percentile thresholds
expected ranking behavior
expected cumulative values
```

For floating-point calculations:

```python
import pytest

assert result == pytest.approx(
    expected
)
```

Also test:

```text
empty input
missing values
duplicate records
incorrect dtypes
single-observation datasets
insufficient samples
tie behavior
```

For grouped metrics, verify both:

```text
output values
+
output grain
```

---

## Common Production Pitfalls

### Correct Operation, Wrong Population

A perfectly valid:

```python
mean()
```

can still be the wrong metric if:

```text
failed transactions
```

were included when the requirement was:

```text
completed transactions only
```

Define the population first.

---

### Correct Population, Wrong Grain

This is equally dangerous:

```text
average order value
```

versus:

```text
average customer spend
```

The same `mean()` method can produce both, depending on the rows being averaged.

---

### Filtering After Aggregation

Do not calculate an aggregate across all data and then filter the result when the filter defines the population.

Filter first.

---

### Ignoring Join Multiplication

A many-to-many join can multiply rows before statistical processing.

Use merge validation where appropriate:

```python
enriched = orders.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
```

---

### Treating Maximum as Tail Percentile

A maximum is a single extreme observation.

For production latency analysis, consider:

```text
p50
p95
p99
max
```

together.

---

### Summing Distinct Counts

Do not sum daily unique-user counts to calculate period-wide unique users.

Distinct counting must occur at the intended reporting grain.

---

### Averaging Group Means

A simple average of subgroup means gives every subgroup equal weight.

It is not generally equivalent to the global mean when group sizes differ.

---

### Ignoring Ordering

Cumulative and ranking operations can be incorrect when row order is not deterministic.

Sort explicitly.

---

### Using Pandas for Database-Scale Aggregation by Default

If PostgreSQL can efficiently calculate:

```sql
SUM()
AVG()
MIN()
MAX()
COUNT()
GROUP BY
window functions
```

consider pushing the computation to the database instead of transferring the complete dataset.

---

## Interview Guidance

Interview questions from this section often test whether you understand semantics rather than whether you remember method names.

Be prepared to explain:

```text
sort_values()
vs sort_index()

sort_values()
vs rank()

count()
vs len()
vs groupby().size()

count()
vs nunique()
vs value_counts()

mean()
vs median()

max()
vs quantile(0.99)

correlation
vs covariance

cumulative
vs rolling
```

Also be prepared to explain:

```text
missing values
duplicate rows
aggregation grain
SQL pushdown
large-data performance
deterministic ordering
```

A strong answer should explain not only:

```text
"which method?"
```

but:

```text
"why this method?"
"what population?"
"what grain?"
"what edge cases?"
"where should the computation run?"
```

---

## Recommended Production Workflow

A reusable workflow for statistics-heavy ETL is:

```text
1. Load only required data
2. Validate schema and dtypes
3. Normalize units and identifiers
4. Detect missing and duplicate records
5. Define the reporting population
6. Establish the required row grain
7. Sort when ordering matters
8. Calculate the required statistic
9. Validate output shape and values
10. Record population and metric metadata
11. Publish to downstream systems
12. Monitor metric and population changes
```

Example:

```python
working = (
    orders[
        [
            "order_id",
            "customer_id",
            "created_at",
            "status",
            "revenue",
        ]
    ]
    .loc[
        lambda frame: frame["status"].eq(
            "completed"
        )
    ]
    .copy()
)

working["created_at"] = pd.to_datetime(
    working["created_at"],
    utc=True,
    errors="raise",
)

working["revenue"] = pd.to_numeric(
    working["revenue"],
    errors="raise",
)

if working["order_id"].isna().any():
    raise ValueError(
        "Completed orders contain null order IDs."
    )

if working["order_id"].duplicated().any():
    raise ValueError(
        "Duplicate completed order IDs detected."
    )

statistics = {
    "order_count": len(working),
    "unique_customers": working[
        "customer_id"
    ].nunique(),
    "total_revenue": working[
        "revenue"
    ].sum(),
    "average_order_value": working[
        "revenue"
    ].mean(),
    "median_order_value": working[
        "revenue"
    ].median(),
    "p95_order_value": working[
        "revenue"
    ].quantile(0.95),
}
```

The important part is the surrounding engineering discipline rather than the individual function calls.

---

## Key Takeaways

- This section progresses from ordering and ranking into aggregation, distribution analysis, relationship analysis, and cumulative state; each operation answers a different analytical question.
- Statistical correctness depends on the population, row grain, ordering, dtype, missing-value policy, duplicate policy, units, and reporting window—not merely on choosing the right Pandas method.
- `count()`, `nunique()`, `value_counts()`, quantiles, correlation, covariance, and cumulative operations have materially different semantics and performance characteristics.
- For production ETL, validate inputs before calculating metrics, preserve enough context to reproduce results, and push large database-resident aggregations into PostgreSQL or another suitable analytical engine when practical.
- Treat statistics as engineering outputs: test business behavior, monitor both metrics and their populations, and avoid inferring causation from descriptive relationships.