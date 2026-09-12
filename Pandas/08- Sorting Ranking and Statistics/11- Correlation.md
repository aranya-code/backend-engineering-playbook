# 11- Correlation

## Overview

Correlation measures the strength and direction of the relationship between two numeric variables.

In Pandas, the primary tools are:

```python
Series.corr()
DataFrame.corr()
DataFrame.corrwith()
```

Correlation is useful for:

```text
feature analysis
data-quality investigation
performance analysis
business analytics
capacity planning
ETL diagnostics
model preparation
operational monitoring
```

Typical backend and data-engineering questions include:

```text
Does request latency increase with payload size?
Does order value relate to discount amount?
Does CPU utilization move with request volume?
Does revenue move with units sold?
```

Correlation describes association, not causation.

A high correlation can indicate that two variables move together, but it does not prove that one variable causes the other.

---

## Correlation Coefficients

The most commonly used measure is the Pearson correlation coefficient.

Its value is in the range:

```text
-1 ≤ r ≤ 1
```

Interpretation:

| Correlation | General Interpretation |
| --- | --- |
| `1` | Perfect positive linear relationship |
| Close to `1` | Strong positive linear relationship |
| `0` | No linear relationship detected |
| Close to `-1` | Strong negative linear relationship |
| `-1` | Perfect negative linear relationship |

The sign describes direction:

```text
positive
→ variables tend to increase together

negative
→ one tends to increase as the other decreases
```

The magnitude describes the strength of the linear relationship.

---

## Basic Series Correlation

Use:

```python
correlation = orders[
    "revenue"
].corr(
    orders["quantity"]
)
```

This returns a scalar.

For example:

```text
0.82
```

would indicate a strong positive linear association in that dataset.

The calculation is based on paired observations. Values must correspond to the same logical observations.

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
        "quantity": [
            1,
            2,
            3,
            4,
            5,
            6,
        ],
        "revenue": [
            100.0,
            195.0,
            310.0,
            390.0,
            505.0,
            590.0,
        ],
        "discount": [
            0.00,
            0.05,
            0.05,
            0.10,
            0.10,
            0.15,
        ],
        "processing_seconds": [
            2.1,
            2.4,
            2.8,
            3.1,
            3.5,
            3.9,
        ],
    }
)
```

Calculate the relationship between quantity and revenue:

```python
quantity_revenue_corr = orders[
    "quantity"
].corr(
    orders["revenue"]
)
```

This measures whether larger quantities tend to be associated with larger revenues.

---

## `DataFrame.corr()`

`DataFrame.corr()` calculates pairwise correlations between numeric columns by default.

```python
correlations = orders.corr(
    numeric_only=True
)
```

The result is a correlation matrix:

```text
                    quantity  revenue  discount
quantity               1.00     0.98      0.94
revenue                0.98     1.00      0.91
discount               0.94     0.91      1.00
```

The exact values depend on the data.

Important properties:

```text
rows
→ variables

columns
→ variables

cell(i, j)
→ correlation between variable i and variable j
```

The diagonal is:

```text
1.0
```

because each variable is perfectly correlated with itself.

---

## Correlation Matrix

A matrix is useful when multiple variables need to be compared.

```python
numeric_columns = [
    "quantity",
    "revenue",
    "discount",
    "processing_seconds",
]

correlation_matrix = orders[
    numeric_columns
].corr()
```

This is often used during:

```text
feature analysis
data exploration
anomaly investigation
capacity analysis
```

Because the matrix is symmetric:

```text
corr(A, B) == corr(B, A)
```

only one half is mathematically necessary, although both halves are returned.

---

## Pairwise Correlation

For focused analysis, prefer explicit Series correlation:

```python
revenue_vs_quantity = orders[
    "revenue"
].corr(
    orders["quantity"]
)

revenue_vs_discount = orders[
    "revenue"
].corr(
    orders["discount"]
)
```

This is often clearer in production metric code because the business relationship is explicitly named.

---

## Why Correlation Exists

Correlation provides a compact measure of whether two variables move together.

Without it, engineers may inspect:

```text
raw values
tables
plots
aggregates
```

and make subjective judgments.

Correlation gives a standardized numerical summary.

For example:

```text
revenue vs quantity
→ 0.92

latency vs payload size
→ 0.81

error rate vs request volume
→ 0.08
```

These numbers can help prioritize investigation, but they are not sufficient to establish causality.

---

## Pearson Correlation

Pandas uses Pearson correlation by default for `corr()`.

Pearson correlation measures the strength of a linear relationship.

A simplified interpretation is:

```text
positive linear relationship
→ high positive correlation

negative linear relationship
→ high negative correlation

no linear relationship
→ correlation near zero
```

A nonlinear relationship can still exist even when Pearson correlation is near zero.

---

## Spearman Correlation

Pandas supports:

```python
orders["revenue"].corr(
    orders["quantity"],
    method="spearman",
)
```

Spearman correlation evaluates monotonic association using ranked values rather than raw values.

Use it when:

```text
relationship is monotonic but not necessarily linear
outliers make Pearson less representative
relative ordering matters
```

Example:

```python
spearman_corr = orders[
    "processing_seconds"
].corr(
    orders["payload_kb"],
    method="spearman",
)
```

---

## Kendall Correlation

Pandas also supports:

```python
kendall_corr = orders[
    "revenue"
].corr(
    orders["quantity"],
    method="kendall",
)
```

Kendall correlation is rank-based and often useful when:

```text
sample sizes are smaller
ordinal relationships matter
rank agreement is important
```

It is generally more computationally expensive than Pearson.

---

## Correlation Methods

| Method | Measures | Typical Use |
| --- | --- | --- |
| `pearson` | Linear relationship | Numeric variables with approximately linear association |
| `spearman` | Monotonic rank relationship | Nonlinear monotonic relationships, ordinal-style analysis |
| `kendall` | Rank concordance | Rank-based analysis and smaller datasets |

Do not choose a correlation method solely because one coefficient appears larger.

The method should match the structure of the data and the analytical question.

---

## Missing Values

Correlation uses paired observations.

Consider:

```text
revenue | quantity
--------|---------
100     | 1
200     | 2
300     | null
400     | 4
```

The third pair cannot contribute to the pairwise correlation because one value is missing.

Pandas handles missing values according to the correlation operation's pairwise-valid observation semantics.

Inspect missingness explicitly:

```python
paired = orders[
    [
        "revenue",
        "quantity",
    ]
]

missing = paired.isna().sum()
```

Do not interpret correlation without considering how many valid pairs were available.

---

## `min_periods`

`corr()` supports `min_periods` for controlling the minimum number of valid observations needed.

```python
correlation = orders[
    "revenue"
].corr(
    orders["quantity"],
    min_periods=20,
)
```

This is useful when a correlation metric should not be reported from an extremely small sample.

For monitoring systems, setting a minimum sample threshold can prevent unstable metrics from being treated as meaningful.

---

## Pairwise Versus Global Missingness

With multiple columns, different pairs can have different numbers of valid observations.

For example:

```text
A vs B
→ 10,000 valid pairs

A vs C
→ 8,500 valid pairs

B vs C
→ 2,100 valid pairs
```

The correlation matrix may still contain values for all three relationships.

This means the matrix alone does not reveal statistical coverage.

Track pairwise sample size when correlation is used for important analytical or operational decisions.

---

## Checking Valid Pair Counts

A simple approach:

```python
pair = orders[
    [
        "revenue",
        "quantity",
    ]
].dropna()

pair_count = len(pair)

correlation = pair[
    "revenue"
].corr(
    pair["quantity"]
)
```

This makes the population explicit:

```text
drop invalid pair
→ count observations
→ calculate correlation
```

For reporting, store both:

```text
correlation coefficient
+
sample size
```

---

## Outliers

Correlation can be highly sensitive to outliers, especially Pearson correlation.

Example:

```text
quantity       revenue
1              100
2              200
3              300
4              400
100            1000000
```

The extreme observation may substantially affect the coefficient.

Investigate:

```text
data-entry errors
valid enterprise transactions
currency errors
unit mismatches
duplicate records
```

before removing or transforming outliers.

Do not delete an observation merely because it changes the correlation.

---

## Correlation Does Not Imply Causation

Suppose:

```text
request volume
```

and:

```text
CPU utilization
```

have high correlation.

This does not prove:

```text
request volume causes CPU usage
```

There may be a third variable:

```text
background workload
deployment change
cache behavior
traffic composition
```

Correlation is an investigative signal, not a causal proof.

---

## Spurious Correlation

Two variables can appear correlated because they both depend on another factor.

For example:

```text
month
  ↓
sales
  ↓
marketing spend
```

A high correlation between:

```text
sales
```

and:

```text
marketing spend
```

does not necessarily mean one directly causes the other.

Time trends, seasonality, and common external variables can create misleading correlations.

---

## Time-Series Correlation

Time-dependent data requires additional care.

Suppose:

```python
daily = (
    metrics
    .sort_values("date")
)
```

and calculate:

```python
correlation = daily[
    "requests"
].corr(
    daily["revenue"]
)
```

A strong relationship may reflect:

```text
shared trend
seasonality
weekly patterns
growth over time
```

rather than direct operational dependence.

For time-series systems, consider:

```text
lagged variables
rolling correlations
differenced series
seasonal effects
```

when appropriate.

---

## Lagged Correlation

Suppose increased traffic may affect infrastructure CPU with a delay.

Create a lagged Series:

```python
metrics["cpu_lagged"] = (
    metrics["cpu_percent"]
    .shift(1)
)

lagged_corr = metrics[
    "requests"
].corr(
    metrics["cpu_lagged"]
)
```

This tests a different relationship from contemporaneous correlation.

Be explicit about:

```text
time granularity
timezone
lag interval
missing periods
```

when working with operational time series.

---

## Grouped Correlation

Correlation can also be calculated within groups.

For example, correlation between:

```text
quantity
```

and:

```text
revenue
```

for each region:

```python
regional_correlation = (
    orders
    .groupby("region")
    .apply(
        lambda group: group[
            "quantity"
        ].corr(
            group["revenue"]
        )
    )
)
```

This is useful when relationships differ by:

```text
region
customer segment
product category
service
tenant
```

However, `apply()` executes Python-level logic and can be expensive for many groups.

For small numbers of groups it may be acceptable; for large-scale workloads, database or specialized analytical approaches may be more appropriate.

---

## Correlation Within a Segment

Before interpreting a global correlation, check whether the relationship is stable across important segments.

Example:

```python
premium = orders.loc[
    orders["customer_tier"].eq("premium")
]

premium_corr = premium[
    "quantity"
].corr(
    premium["revenue"]
)
```

A global correlation can hide important subgroup behavior.

This is especially relevant when:

```text
pricing
customer mix
product mix
regions
```

differ substantially.

---

## Data Types

Correlation requires meaningful numeric data.

Convert external numeric fields explicitly:

```python
orders["revenue"] = pd.to_numeric(
    orders["revenue"],
    errors="raise",
)

orders["quantity"] = pd.to_numeric(
    orders["quantity"],
    errors="raise",
)
```

Do not calculate correlation on values that are numerically encoded but semantically categorical.

For example:

```text
1 = bronze
2 = silver
3 = gold
```

is not automatically a continuous numeric variable suitable for Pearson correlation.

---

## Boolean Values

Boolean columns can participate in numeric operations through Pandas' dtype handling, but correlation should still be interpreted carefully.

For example:

```text
is_premium
```

may be useful when studying differences between groups, but:

```python
orders["is_premium"].corr(
    orders["revenue"]
)
```

should not automatically be interpreted as a conventional continuous-variable relationship.

Often, group-level comparisons are more interpretable:

```python
orders.groupby(
    "is_premium"
)["revenue"].mean()
```

Choose the statistic that matches the business question.

---

## Ordinal Categories

Consider:

```text
priority
1 = low
2 = medium
3 = high
4 = critical
```

A numeric encoding introduces ordering, but the distances between categories may not be equivalent.

Spearman correlation can sometimes be more appropriate for ordinal variables:

```python
correlation = tickets[
    "priority"
].corr(
    tickets["resolution_hours"],
    method="spearman",
)
```

Still, interpretation must respect the domain semantics.

---

## Duplicate Records

Duplicate rows can distort correlation because repeated observations effectively receive additional weight.

Before calculating important metrics:

```python
duplicate_count = orders.duplicated().sum()
```

For a business key:

```python
duplicate_order_ids = (
    orders["order_id"]
    .value_counts()
)

duplicate_order_ids = (
    duplicate_order_ids[
        duplicate_order_ids > 1
    ]
)
```

Do not automatically drop duplicates without determining whether repeated records are genuine events or ingestion errors.

---

## Incorrect Join Grain

A particularly dangerous production problem is correlation after an incorrect join.

For example:

```text
orders
    ↓
many-to-many join
    ↓
row multiplication
    ↓
distorted observations
    ↓
misleading correlation
```

Validate joins:

```python
enriched = orders.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
```

A correlation coefficient cannot identify that the underlying rows were incorrectly duplicated.

---

## Unit Consistency

Correlation is invariant to positive linear unit changes in the ideal mathematical sense, but unit correctness still matters operationally because transformations can create malformed or mixed values.

For example, do not compare:

```text
latency in milliseconds
```

against:

```text
latency in seconds
```

within the same column without normalization.

The resulting dataset may contain discontinuities or conversion artifacts that distort interpretation and downstream analysis.

---

## Currency Consistency

Similarly, financial fields should use a consistent currency or a well-defined normalized representation.

Do not mix:

```text
USD
EUR
INR
```

and then interpret correlations without understanding the conversion process.

Currency changes, exchange-rate transformations, and reporting windows can introduce artificial patterns.

---

## Correlation Matrix Filtering

For larger datasets, you may only need relationships with one target variable.

Example:

```python
correlation_with_revenue = (
    orders
    .corr(
        numeric_only=True
    )["revenue"]
    .sort_values(
        ascending=False
    )
)
```

This is more useful than inspecting an entire large matrix.

For feature screening:

```python
strong_relationships = (
    correlation_with_revenue
    .abs()
    .sort_values(
        ascending=False
    )
)
```

Remember that high correlation does not establish causal importance.

---

## Avoiding Redundant Matrix Work

For `n` numeric variables, a correlation matrix contains:

```text
n × n
```

entries, although it is symmetric.

For a DataFrame with hundreds or thousands of numeric columns, the matrix can become large.

Prefer:

```text
selected variables
+
target-oriented analysis
```

when a full matrix is unnecessary.

---

## Performance

Correlation is more computationally involved than simple scalar reductions such as:

```text
sum
mean
min
max
```

A full correlation matrix requires pairwise computation across multiple columns.

Cost increases with:

```text
row count
column count
missingness
number of pairwise combinations
correlation method
```

For `n` columns, pairwise relationships grow approximately as:

```text
n(n - 1) / 2
```

Ignoring symmetry optimizations, this grows quadratically with the number of variables.

---

## Large Dataset Strategy

For large database-backed datasets, consider pushing the calculation toward the database or analytical engine when supported.

PostgreSQL provides correlation aggregation:

```sql
SELECT
    CORR(quantity, revenue) AS quantity_revenue_corr
FROM orders
WHERE status = 'completed';
```

This can avoid transferring millions of rows to Pandas.

For very large analytical workloads, consider:

```text
PostgreSQL
data warehouse
DuckDB
Spark
```

depending on scale and workload characteristics.

---

## SQL Grouped Correlation

PostgreSQL can also calculate correlation by group:

```sql
SELECT
    region,
    CORR(quantity, revenue) AS correlation
FROM orders
WHERE status = 'completed'
GROUP BY region;
```

This can be preferable to loading the full dataset into Pandas merely to calculate grouped correlations.

---

## APIs and Correlation

For REST API data:

```python
events = pd.DataFrame(
    response["items"]
)

events["payload_kb"] = pd.to_numeric(
    events["payload_kb"],
    errors="raise",
)

events["latency_ms"] = pd.to_numeric(
    events["latency_ms"],
    errors="raise",
)

latency_correlation = events[
    "payload_kb"
].corr(
    events["latency_ms"]
)
```

Before trusting the result, verify:

```text
all pages were retrieved
timestamps are aligned
duplicates are controlled
units are consistent
missingness is understood
```

---

## Correlation in ETL

Correlation is often more useful as a diagnostic than as a core transformation.

A pipeline might use it as:

```text
raw data
    ↓
clean
    ↓
validate
    ↓
aggregate
    ↓
calculate correlation
    ↓
detect unexpected relationship
    ↓
produce monitoring report
```

For example, a sudden change in:

```text
request size vs latency correlation
```

could indicate:

```text
network changes
serialization changes
cache effects
database behavior
application deployment
```

Correlation should usually complement, not replace, direct operational metrics.

---

## Monitoring

Monitor both correlation and its supporting context.

Example:

```python
valid = orders[
    [
        "quantity",
        "revenue",
    ]
].dropna()

metrics = {
    "correlation": float(
        valid["quantity"].corr(
            valid["revenue"]
        )
    ),
    "sample_size": len(valid),
    "missing_quantity": int(
        orders["quantity"].isna().sum()
    ),
    "missing_revenue": int(
        orders["revenue"].isna().sum()
    ),
}
```

A correlation of:

```text
0.90
```

based on:

```text
10 observations
```

should be treated very differently from:

```text
0.90
```

based on:

```text
10 million observations
```

The coefficient and sample size should be monitored together.

---

## Correlation Drift

Historical correlation can be useful for detecting changes in system behavior.

For example:

```text
previous:
payload size ↔ latency = 0.32

current:
payload size ↔ latency = 0.81
```

Potential explanations include:

```text
serialization regression
network bottleneck
database query changes
cache behavior
traffic mix changes
```

Correlation drift should trigger investigation rather than automatic remediation.

---

## Production Data Flow

A correlation-analysis workflow can be represented as:

```mermaid
flowchart LR
    Source[PostgreSQL / API / Parquet] --> Ingest[Ingest Data]
    Ingest --> Clean[Validate Dtypes and Units]
    Clean --> Scope[Define Population]
    Scope --> Pair[Select Numeric Pairs]
    Pair --> Missing[Handle Missing Pairs]
    Missing --> Corr[Calculate Correlation]
    Corr --> Context[Record Sample Size and Window]
    Context --> Monitor[Monitor Correlation Drift]
    Monitor --> Report[Report / Investigation]
```

The coefficient is only one part of the output.

Production-grade analysis should retain the context that makes the coefficient interpretable.

---

## Security Considerations

Correlation analysis can expose information about sensitive business or user attributes.

Examples:

```text
employee compensation vs performance
customer spending vs segmentation
health-related operational data
tenant usage relationships
```

Apply authorization before loading or aggregating sensitive records.

For multi-tenant systems:

```python
authorized_orders = orders.loc[
    orders["tenant_id"].isin(
        authorized_tenant_ids
    )
].copy()

correlation = authorized_orders[
    "quantity"
].corr(
    authorized_orders["revenue"]
)
```

Do not calculate cross-tenant correlations and expose them through tenant-scoped APIs.

---

## Reliability Considerations

A production correlation metric should define:

```text
variables
population
time window
sample-size threshold
missing-value policy
outlier policy
units
grouping grain
correlation method
```

Example:

```text
Metric: Payload Size / API Latency Correlation
Variables: payload_kb, latency_ms
Population: successful requests
Window: UTC rolling 24 hours
Missing policy: exclude incomplete pairs
Method: Pearson
Minimum sample: 1,000 requests
Units: KB and milliseconds
```

This makes the metric reproducible.

---

## Testing

Test the operation with controlled data.

```python
import pandas as pd
import pytest


def test_perfect_positive_correlation() -> None:
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([2, 4, 6, 8, 10])

    correlation = x.corr(y)

    assert correlation == pytest.approx(1.0)
```

Test a perfect negative relationship:

```python
def test_perfect_negative_correlation() -> None:
    x = pd.Series([1, 2, 3, 4, 5])
    y = pd.Series([10, 8, 6, 4, 2])

    correlation = x.corr(y)

    assert correlation == pytest.approx(-1.0)
```

---

## Testing Missing Values

```python
def test_correlation_uses_valid_pairs() -> None:
    x = pd.Series(
        [1.0, 2.0, 3.0, None]
    )

    y = pd.Series(
        [2.0, 4.0, None, 8.0]
    )

    correlation = x.corr(y)

    assert correlation == pytest.approx(1.0)
```

The test verifies that only complete pairs contribute to the calculation.

In production testing, also verify the expected minimum sample threshold.

---

## Testing Insufficient Samples

```python
def test_min_periods_can_prevent_weak_results() -> None:
    x = pd.Series([1.0, 2.0])
    y = pd.Series([2.0, 4.0])

    correlation = x.corr(
        y,
        min_periods=3,
    )

    assert pd.isna(correlation)
```

This is useful when an analytical metric requires a minimum amount of evidence before publication.

---

## Common Mistakes

### Treating Correlation as Causation

Incorrect reasoning:

```text
A and B have correlation 0.9
→ A causes B
```

The correct conclusion is:

```text
A and B have a strong observed association
```

Causal reasoning requires additional evidence and methods.

---

### Ignoring Sample Size

A strong correlation from a tiny sample can be unstable.

Always consider:

```text
sample size
time window
population
```

alongside the coefficient.

---

### Ignoring Missing Pairs

Correlation is calculated from valid paired observations.

If missingness differs across variables, different correlations may be based on different populations.

Track valid-pair counts.

---

### Using Pearson for Every Relationship

Pearson measures linear association.

For monotonic but nonlinear relationships, consider:

```python
method="spearman"
```

Choose based on the structure of the data.

---

### Correlating Encoded Categories Blindly

Encoding:

```text
bronze = 1
silver = 2
gold = 3
```

does not automatically make the variable continuous.

Understand the semantics before applying Pearson correlation.

---

### Ignoring Time Dependence

High correlation between two growing time series may simply reflect shared trends.

Consider:

```text
lag
seasonality
differencing
rolling statistics
```

where appropriate.

---

### Calculating After a Bad Join

Many-to-many joins can duplicate observations and distort the result.

Validate join cardinality before analytical calculations.

---

### Mixing Units or Currencies

Malformed or inconsistently transformed values can create misleading relationships.

Normalize representations before analysis.

---

### Treating Outliers as Automatically Invalid

An extreme observation may be:

```text
valid
important
rare
```

Investigate before excluding it.

---

## Interview Traps

### Range of Pearson Correlation

Question:

> What values can Pearson correlation take?

Answer:

```text
-1 to +1
```

---

### Diagonal of a Correlation Matrix

Question:

> Why are diagonal values equal to 1?

Because each variable is perfectly correlated with itself.

---

### Symmetry

Question:

> Is `corr(A, B)` different from `corr(B, A)`?

No.

```text
corr(A, B) = corr(B, A)
```

for standard pairwise correlation.

---

### Pearson Versus Spearman

Question:

> When would you use Spearman instead of Pearson?

Use Spearman when the relationship is better understood through ranks or is monotonic without being well described by a linear relationship.

---

### Missing Values

Question:

> How does Pandas handle missing values in `corr()`?

Correlation is calculated from valid paired observations. Missing values reduce the number of observations contributing to the pairwise calculation.

---

### Correlation Matrix Size

For `n` variables, unique unordered pairs are:

```text
n(n - 1) / 2
```

The full matrix contains:

```text
n²
```

entries including the diagonal and mirrored relationships.

This matters when working with very wide DataFrames.

---

## Production Checklist

Before publishing a correlation metric, verify:

```text
[ ] Variables are correctly typed
[ ] Variables have compatible semantics
[ ] Units and currencies are consistent
[ ] Correct population is selected
[ ] Reporting window is defined
[ ] Missing-value policy is defined
[ ] Valid-pair count is tracked
[ ] Minimum sample size is defined
[ ] Outlier policy is understood
[ ] Correlation method matches the relationship
[ ] Joins are validated before analysis
[ ] Time-series effects are considered
[ ] Database pushdown is evaluated
[ ] Correlation drift is monitored
[ ] Causation is not inferred from correlation alone
```

---

## Key Takeaways

- Pandas provides `Series.corr()`, `DataFrame.corr()`, and related methods for measuring pairwise association, with Pearson as the default correlation method.
- Correlation measures association, not causation; a strong coefficient can result from confounding variables, shared trends, time effects, or data-processing artifacts.
- Missing values, sample size, outliers, duplicate rows, incorrect joins, category encoding, and inconsistent units can materially change the interpretation of a correlation.
- Use Pearson for linear relationships and consider Spearman or Kendall when rank or monotonic relationships better represent the data; record the calculation context alongside the coefficient.
- For large production datasets, validate the population and pairwise sample size, monitor correlation drift, and consider SQL or analytical-engineering pushdown instead of transferring large raw datasets into Pandas.