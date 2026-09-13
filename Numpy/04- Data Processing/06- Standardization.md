# 06- Standardization

## Overview

Standardization transforms numerical values so that they are centered around a reference mean and scaled according to a reference standard deviation.

The most common form is z-score standardization:

```text
z = (x - mean) / std
```

Unlike min-max normalization, standardization does not constrain values to a fixed interval such as `[0, 1]`.

It is useful when numerical features have different scales and downstream processing should operate on comparable centered values.

Typical engineering use cases include:

- Standardizing numeric columns in data-processing pipelines.
- Comparing measurements with different units or scales.
- Preparing numerical data for downstream algorithms that are sensitive to feature scale.
- Creating consistent representations across repeated batch-processing jobs.
- Converting raw operational metrics into standardized scores.

The core production concern is consistency. The same statistics used to define the transformation must be used whenever the transformed representation needs to remain comparable.

```mermaid
flowchart LR
    A["Reference Dataset"] --> B["Calculate Mean / Std"]
    B --> C["Persist Versioned Statistics"]
    C --> D["Incoming Batch"]
    D --> E["Validate Values"]
    E --> F["Standardize"]
    F --> G["Downstream Processing"]
```

## Standardization vs Normalization

The terms are often used interchangeably in general discussions, but they represent different transformations in this engineering context.

| Technique | Transformation | Typical Property |
|---|---|---|
| Min-max normalization | `(x - min) / (max - min)` | Bounded range |
| Z-score standardization | `(x - mean) / std` | Centered and scale-adjusted |
| Max-absolute scaling | `x / max(abs(x))` | Preserves sign and zero |

Standardization is usually preferred when the important requirement is:

```text
center around a reference mean
+
scale according to variability
```

It is not the right choice merely because a dataset "needs normalization."

## Z-Score Standardization

Given values:

```python
import numpy as np

values = np.array(
    [10.0, 20.0, 30.0, 40.0],
)

mean = np.mean(values)
std = np.std(values)

standardized = (
    values - mean
) / std
```

The transformed values are centered around zero.

For the dataset above, the output is approximately:

```text
[-1.3416, -0.4472, 0.4472, 1.3416]
```

The exact result depends on the standard deviation definition.

## Mean and Standard Deviation

Standardization depends directly on two statistics:

```python
mean = np.mean(values)
std = np.std(values)
```

Then:

```python
standardized = (
    values - mean
) / std
```

The calculation has two stages:

```text
center
→ subtract mean

scale
→ divide by standard deviation
```

This makes the transformation easy to reason about and easy to reproduce when the statistics are stored.

## Population vs Sample Standard Deviation

NumPy's default is:

```python
np.std(
    values,
    ddof=0,
)
```

This treats the input as the complete population for the purpose of the calculation.

Using:

```python
np.std(
    values,
    ddof=1,
)
```

computes the sample standard deviation.

The choice matters because it changes the denominator and therefore the standardized output.

For example:

```python
population_std = np.std(
    values,
    ddof=0,
)

sample_std = np.std(
    values,
    ddof=1,
)
```

The `ddof` value should be treated as part of the processing contract.

Do not let one service standardize with `ddof=0` while another assumes `ddof=1` without explicitly defining the difference.

## Why `ddof` Matters

Suppose a transformation is persisted and reused later.

If the original pipeline uses:

```python
std = np.std(
    reference,
    ddof=0,
)
```

then the same convention must be used whenever that statistic is recomputed.

Otherwise:

```text
same raw value
+
different standard-deviation definition
=
different standardized value
```

This is a subtle interoperability issue between data pipelines and services.

## A Reusable Standardization Function

A clear implementation separates the transformation from how the statistics were obtained:

```python
import numpy as np


def standardize(
    values: np.ndarray,
    mean: float,
    std: float,
) -> np.ndarray:
    if std == 0.0:
        raise ValueError(
            "Standard deviation must be non-zero."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return (
        values - mean
    ) / std
```

This is preferable to recalculating statistics inside every call when a stable reference distribution is required.

## Fit and Transform

For production systems, think in terms of:

```text
fit
→ calculate statistics

transform
→ apply statistics
```

For standardization:

```text
fit:
    mean
    std
    ddof

transform:
    (x - mean) / std
```

Example:

```python
import numpy as np

reference = np.array(
    [10.0, 20.0, 30.0, 40.0],
)

mean = np.mean(
    reference,
)

std = np.std(
    reference,
)

incoming = np.array(
    [15.0, 25.0, 35.0],
)

standardized = (
    incoming - mean
) / std
```

The incoming batch is transformed according to the reference statistics rather than its own local distribution.

## Why Per-Batch Standardization Can Be Wrong

Consider two batches:

```text
batch A → mean=100, std=10
batch B → mean=200, std=20
```

If each batch is standardized independently:

```text
batch A → mean≈0
batch B → mean≈0
```

the transformed results are internally consistent within each batch but no longer preserve a common external scale.

This is a problem when data from different batches needs to be compared.

Use per-batch statistics only when the business requirement explicitly says:

```text
normalize relative to each batch
```

Otherwise, persist and reuse a reference set of statistics.

## Column-Wise Standardization

For a two-dimensional dataset:

```python
values = np.array(
    [
        [10.0, 100.0, 1000.0],
        [20.0, 200.0, 2000.0],
        [30.0, 300.0, 3000.0],
    ],
)
```

Standardize each feature independently:

```python
mean = np.mean(
    values,
    axis=0,
)

std = np.std(
    values,
    axis=0,
)

standardized = (
    values - mean
) / std
```

The resulting shapes are:

```text
values → (3, 3)
mean   → (3,)
std    → (3,)
```

NumPy broadcasts the per-column statistics across rows.

This is the common pattern when:

```text
rows    → records
columns → features
```

## Row-Wise Standardization

Sometimes each record should be standardized independently.

```python
values = np.array(
    [
        [10.0, 20.0, 30.0],
        [100.0, 200.0, 300.0],
    ],
)

mean = np.mean(
    values,
    axis=1,
    keepdims=True,
)

std = np.std(
    values,
    axis=1,
    keepdims=True,
)

standardized = (
    values - mean
) / std
```

`keepdims=True` preserves the `(n, 1)` shape needed for broadcasting.

This is appropriate only when the semantics require each record to be normalized relative to itself.

It is not interchangeable with column-wise standardization.

## Axis Semantics

The `axis` determines the population over which statistics are calculated.

For:

```text
values.shape == (records, features)
```

a common convention is:

```python
axis=0
```

for feature-wise statistics.

That gives:

```text
one mean per feature
one std per feature
```

Whereas:

```python
axis=1
```

gives:

```text
one mean per record
one std per record
```

The transformation can be mathematically valid in both cases while representing completely different business semantics.

## Broadcasting and `keepdims`

Consider:

```python
values.shape == (1000, 20)
```

Column-wise standardization:

```python
mean = np.mean(
    values,
    axis=0,
    keepdims=True,
)

std = np.std(
    values,
    axis=0,
    keepdims=True,
)
```

Now:

```text
mean → (1, 20)
std  → (1, 20)
```

and:

```python
standardized = (
    values - mean
) / std
```

broadcasts across all 1000 records.

Using `keepdims=True` makes the intended axis semantics explicit and reduces shape-related mistakes.

## Zero Standard Deviation

A constant feature has no variance:

```python
values = np.array(
    [50.0, 50.0, 50.0],
)

std = np.std(values)
```

Result:

```text
std = 0
```

Then:

```python
(values - mean) / std
```

is undefined.

A production pipeline must choose a policy.

| Constant Feature | Possible Policy |
|---|---|
| Feature has no useful information | Drop it |
| Constant value is meaningful | Map standardized result to `0` |
| Strict validation | Reject the feature |
| External contract | Apply configured fallback |

A practical implementation can map constant features to zero:

```python
mean = np.mean(
    values,
)

std = np.std(
    values,
)

standardized = np.zeros_like(
    values,
    dtype=np.float64,
)

if std != 0.0:
    standardized = (
        values - mean
    ) / std
```

Whether this is correct depends on the downstream contract.

## Zero Variance in Multiple Columns

For a matrix:

```python
values = np.array(
    [
        [10.0, 5.0, 100.0],
        [20.0, 5.0, 200.0],
        [30.0, 5.0, 300.0],
    ],
)
```

The second column is constant.

```python
std = np.std(
    values,
    axis=0,
)

zero_variance = std == 0.0
```

A robust implementation can standardize only non-constant columns:

```python
mean = np.mean(
    values,
    axis=0,
)

std = np.std(
    values,
    axis=0,
)

standardized = np.zeros_like(
    values,
    dtype=np.float64,
)

non_constant = std != 0.0

standardized[:, non_constant] = (
    (
        values[:, non_constant]
        - mean[non_constant]
    )
    / std[non_constant]
)
```

This keeps constant columns at zero while avoiding division by zero.

The policy should be explicit and tested.

## Missing Values

`NaN` can propagate into standardization statistics.

Consider:

```python
values = np.array(
    [10.0, np.nan, 30.0],
)

mean = np.mean(values)
std = np.std(values)
```

Both can become `NaN`.

If the policy is to ignore missing values:

```python
mean = np.nanmean(values)
std = np.nanstd(values)
```

Then:

```python
standardized = (
    values - mean
) / std
```

still leaves the missing input as `NaN`.

That can be desirable because:

```text
missing input
→ missing standardized output
```

preserves information about the original data quality.

## Infinity and Standardization

`np.nanstd()` ignores `NaN`, but it does not treat infinity as missing.

For:

```python
values = np.array(
    [10.0, np.inf, 30.0],
)
```

the statistics can still become invalid.

If only finite values are allowed:

```python
finite = np.isfinite(values)

finite_values = values[
    finite
]
```

Then compute statistics from the finite subset.

This creates a new array, so for large datasets use a batch-based approach when appropriate.

## Standardizing Only Finite Values

A strict data-quality pipeline can perform:

```python
finite = np.isfinite(
    values
)

finite_values = values[
    finite
]

if finite_values.size == 0:
    raise ValueError(
        "No finite values available."
    )

mean = np.mean(
    finite_values,
)

std = np.std(
    finite_values,
)
```

Then the transformation can preserve invalid positions according to the chosen policy.

For example:

```python
standardized = np.full(
    values.shape,
    np.nan,
    dtype=np.float64,
)

np.subtract(
    values,
    mean,
    out=standardized,
    where=finite,
)

np.divide(
    standardized,
    std,
    out=standardized,
    where=finite,
)
```

This makes the policy explicit:

```text
finite input → standardized
non-finite input → NaN
```

## Standardization and Outliers

Standardization is sensitive to the mean and standard deviation.

Consider:

```text
[10, 20, 30, 40, 1_000_000]
```

The extreme value can significantly change:

```text
mean
+
standard deviation
```

and therefore influence every standardized value.

This means:

```text
standardization
≠
outlier handling
```

If outlier handling is required, define it as a separate stage:

```text
validate
→ detect outliers
→ apply documented policy
→ calculate statistics
→ standardize
```

Do not silently remove values simply because they affect the standard deviation.

## Reference Statistics

A production standardization service often stores:

```python
statistics = {
    "method": "z_score",
    "mean": 125.4,
    "std": 32.7,
    "ddof": 0,
    "version": "2026-09-01",
}
```

For multi-feature data, store arrays:

```python
statistics = {
    "mean": mean,
    "std": std,
    "ddof": 0,
}
```

The statistics should be versioned alongside the transformation definition.

This is important when:

```text
API service
+
batch pipeline
+
historical processing
```

must produce compatible outputs.

## Persisted Statistics and Deployment

Suppose a new deployment changes the reference statistics.

Existing records may have been standardized using:

```text
version A
```

while new records use:

```text
version B
```

The transformed values are no longer directly comparable unless the pipeline explicitly supports versioned representations.

Treat standardization parameters as deployment-relevant configuration.

A robust data contract can include:

```text
transformation name
statistics version
mean
standard deviation
ddof
dtype
missing-value policy
```

## Standardization for Operational Metrics

Consider monitoring metrics with very different units:

```text
latency_ms
requests_per_second
error_rate
```

A common statistical transformation is:

```python
latency = np.array(
    [100.0, 120.0, 150.0, 300.0],
)

mean = np.mean(latency)
std = np.std(latency)

latency_z = (
    latency - mean
) / std
```

The standardized values indicate how far each observation lies from the reference mean in standard-deviation units.

This can be useful for numerical comparisons and anomaly-oriented processing, but a z-score is not automatically a production alert policy. Alert thresholds should be derived from the operational characteristics of the system.

## Batch Processing

For large datasets, calculate reference statistics once and transform each batch.

```python
import numpy as np


def standardize_batch(
    values: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if np.any(std == 0.0):
        raise ValueError(
            "Standard deviation contains zero values."
        )

    result = np.empty_like(
        values,
        dtype=np.float64,
    )

    np.subtract(
        values,
        mean,
        out=result,
    )

    np.divide(
        result,
        std,
        out=result,
    )

    return result
```

This pattern separates:

```text
statistics lifecycle
```

from:

```text
batch transformation lifecycle
```

which is useful in Kafka consumers, Celery workers, and large file-processing pipelines.

## Streaming Data

For continuously arriving data, the pipeline must define how statistics are established.

Possible strategies include:

| Strategy | Meaning |
|---|---|
| Fixed reference statistics | Stable across all batches |
| Rolling statistics | Scale follows a recent window |
| Batch statistics | Every batch defines its own scale |
| Periodically recomputed statistics | Reference distribution updated on schedule |

These strategies are not interchangeable.

For reproducibility and cross-batch comparability, fixed versioned statistics are usually easier to reason about.

## Incremental Mean and Variance

Mean and variance can be maintained across batches with appropriate running state.

Do not calculate:

```python
mean_of_batch_means = np.mean(
    batch_means
)
```

and assume it equals the global mean unless the batches have equal sizes.

Likewise, averaging batch standard deviations is not a correct way to recover a global standard deviation.

For large datasets, maintain sufficient statistics that include at least the information required to combine batches correctly, such as:

```text
count
mean
variance state
```

A production implementation should use a numerically appropriate incremental algorithm rather than ad hoc averaging of batch summaries.

## Memory Considerations

Standardization can involve several arrays:

```text
input
+
mean
+
std
+
intermediate subtraction
+
output
```

For:

```python
standardized = (
    values - mean
) / std
```

the subtraction creates an intermediate result before the division produces the final output.

For large arrays, consider:

- Processing in batches.
- Reusing an output buffer.
- Persisting compact statistics rather than raw reference data.
- Selecting an appropriate dtype.
- Avoiding unnecessary conversions.
- Measuring peak memory.

## Using `out=` to Reduce Allocations

A reusable output buffer can avoid an additional intermediate allocation:

```python
standardized = np.empty_like(
    values,
    dtype=np.float64,
)

np.subtract(
    values,
    mean,
    out=standardized,
)

np.divide(
    standardized,
    std,
    out=standardized,
)
```

This reuses `standardized` for both operations.

The trade-off is increased implementation complexity, so use it where allocation or peak-memory costs are relevant.

## Dtype Considerations

Standardization requires subtraction and division, so integer input is transformed into floating-point output.

For explicit control:

```python
values = np.asarray(
    values,
    dtype=np.float64,
)
```

The dtype choice affects:

```text
precision
+
range
+
memory consumption
+
downstream compatibility
```

A smaller dtype can reduce memory usage, but precision loss may become significant for large or closely spaced values.

Do not choose a dtype solely from memory size without considering numerical error.

## Numerical Stability

Mean and variance calculations can be sensitive to floating-point precision, especially for large-magnitude values with relatively small variation.

For example, data around:

```text
1_000_000_000
```

with differences of only a few units can be more sensitive to floating-point precision than values around:

```text
10
```

The practical response is:

- Choose an appropriate dtype.
- Use well-tested NumPy reductions.
- Avoid unnecessary conversions to lower precision.
- Validate the resulting statistics.
- Benchmark with realistic numeric ranges.

Standardization is not just an arithmetic expression; the statistics themselves are numerical computations.

## PostgreSQL Interaction

Standardization can sometimes be expressed in SQL:

```sql
SELECT
    value,
    (value - 100.0) / 20.0 AS standardized_value
FROM metrics;
```

This can be useful when the statistics are already stored as configuration and database-side processing reduces application work.

However, if the pipeline requires dense vectorized processing across large numerical arrays, NumPy may be more appropriate after data extraction.

The general decision is:

```text
simple relational transformation
→ consider SQL

dense numerical processing
→ consider NumPy
```

## Pandas Interaction

For a DataFrame:

```python
frame["standardized"] = (
    frame["value"] - mean
) / std
```

Pandas is often the natural abstraction when the transformation is part of broader tabular processing.

NumPy is preferable when:

```text
dense numerical arrays
+
vectorized computation
+
explicit memory behavior
```

are the main concerns.

Avoid repeatedly converting between representations when the surrounding pipeline already uses one representation effectively.

## Security and Resource Controls

A standardization service may process externally supplied arrays.

Before allocating output buffers:

- Enforce maximum payload size.
- Validate dimensionality.
- Validate element counts.
- Validate dtype expectations.
- Reject pathological inputs.
- Limit batch size.

A large request can otherwise require:

```text
input memory
+
statistics
+
temporary buffers
+
standardized output
```

which can cause significant memory pressure inside a Docker or Kubernetes workload.

## Monitoring

A production standardization stage should track:

```text
records_processed
non_finite_records
zero_variance_features
standardization_failures
out_of_range_records
processing_duration
```

For example:

```python
non_finite = np.count_nonzero(
    ~np.isfinite(values)
)

zero_variance = np.count_nonzero(
    std == 0.0
)
```

Monitor these rates over time.

A sudden rise can indicate:

- Upstream data drift.
- Schema changes.
- Unit changes.
- Broken transformations.
- Reference-statistics mismatch.
- New constant or inactive features.

## Common Mistakes

### Recomputing Statistics for Every Request

This creates request-specific scales and can make results incomparable.

### Standardizing Each Batch Independently

Per-batch standardization can destroy comparability across batches when a common reference distribution is required.

### Ignoring Zero Standard Deviation

A constant feature produces division by zero.

### Averaging Batch Standard Deviations

The average of standard deviations is not generally the global standard deviation.

### Averaging Batch Means Without Weighting

The mean of batch means is only equal to the global mean when batch sizes are appropriately accounted for, such as equal-sized batches.

### Ignoring `ddof`

Different `ddof` conventions produce different statistics and therefore different standardized outputs.

### Assuming `nanstd()` Ignores Infinity

It ignores `NaN`, not infinity.

### Treating Standardization as Outlier Removal

Extreme values influence the mean and standard deviation. Standardization itself does not identify whether an outlier is legitimate.

### Assuming Standardized Values Are Bounded

Z-scores are not constrained to `[0, 1]` or `[-1, 1]`.

### Creating Unnecessary Copies

Repeated dtype conversion and intermediate arrays can increase peak memory.

## Testing

Test both numerical correctness and edge cases.

```python
import numpy as np


def standardize(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    mean = np.mean(values)
    std = np.std(values)

    if std == 0.0:
        raise ValueError(
            "Cannot standardize constant input."
        )

    return (
        values - mean
    ) / std


def test_standardize():
    values = np.array(
        [10.0, 20.0, 30.0, 40.0],
    )

    result = standardize(values)

    np.testing.assert_allclose(
        np.mean(result),
        0.0,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        np.std(result),
        1.0,
        atol=1e-12,
    )
```

Also test:

- Zero-variance input.
- `NaN`.
- Infinity.
- Empty arrays.
- Integer input.
- `float32` and `float64`.
- Column-wise standardization.
- Row-wise standardization.
- `ddof=0`.
- `ddof=1`.
- Persisted statistics.
- Batch consistency.
- Large datasets.

## Debugging

Inspect the statistics before inspecting the standardized output:

```python
mean = np.mean(
    values,
)

std = np.std(
    values,
)

print("mean:", mean)
print("std:", std)

if not np.isfinite(mean):
    raise ValueError(
        "Mean is non-finite."
    )

if not np.isfinite(std):
    raise ValueError(
        "Standard deviation is non-finite."
    )

if std == 0.0:
    raise ValueError(
        "Standard deviation is zero."
    )
```

For feature-wise processing:

```python
mean = np.mean(
    values,
    axis=0,
)

std = np.std(
    values,
    axis=0,
)

print("zero variance features:")
print(
    np.flatnonzero(
        std == 0.0
    )
)
```

This helps distinguish:

```text
invalid input
vs
bad reference statistics
vs
wrong axis
vs
wrong transformation
```

## Interview Questions

### What is standardization?

Standardization transforms values using a reference mean and standard deviation:

```python
(x - mean) / std
```

### What is the difference between standardization and min-max normalization?

Standardization centers and scales values using mean and standard deviation. Min-max normalization maps values to a defined range such as `[0, 1]`.

### What happens when the standard deviation is zero?

The denominator is zero and standardization is undefined. The pipeline must apply an explicit policy for constant features.

### What does NumPy use by default for `np.std()`?

The default is `ddof=0`.

### Why can independently standardizing each batch be a problem?

Each batch gets its own mean and standard deviation, so the resulting values may not be comparable across batches.

### Why should normalization statistics be persisted?

Persisting the reference statistics makes the transformation reproducible and consistent across requests, batches, services, and deployments.

### Is a z-score bounded?

No. Standardized values can be arbitrarily large depending on the input distribution.

### Can `np.nanstd()` handle infinity?

No. It ignores `NaN`, but infinity can still make the result non-finite.

### Why shouldn't batch standard deviations simply be averaged?

Standard deviation is not linearly mergeable by averaging the batch results. Correct global variance requires count and other sufficient state.

### When should standardization happen in SQL instead of NumPy?

When the operation is simple relational arithmetic and executing it near the data source reduces application-side transfer and processing. NumPy is more appropriate for dense numerical array workloads.

## Key Takeaways

- Standardization typically uses `(x - mean) / std` and differs from min-max normalization because the result is centered and not bounded.
- Treat mean, standard deviation, `ddof`, axis semantics, missing-value policy, and statistics version as part of the transformation contract.
- Zero-variance features, `NaN`, infinity, and outliers require explicit handling rather than being silently converted into arbitrary values.
- For consistent processing across batches and services, calculate reference statistics separately from transformation and persist them when reproducibility matters.
- Large-scale standardization should account for dtype, temporary allocations, batching, output buffers, and memory limits in addition to numerical correctness.