# 16- NumPy Coding Problems

## Overview

NumPy coding interviews are rarely about memorizing API names. The stronger interview problems test whether you understand:

- `ndarray` semantics
- shape and dimensionality
- broadcasting
- vectorization
- boolean masking
- aggregation
- dtype behavior
- views and copies
- memory efficiency
- batch processing
- numerical correctness

A good solution should not only produce the correct output. It should also make clear:

```text
What is the data model?
What are the input and output shapes?
Can the operation be vectorized?
Does it allocate additional memory?
Could broadcasting produce an unintended result?
Does dtype affect correctness?
Would the approach scale to production-sized inputs?
```

The problems below are ordered from core NumPy reasoning to production-oriented numerical processing.

## Problem Categories

| Category | Skills Tested |
|---|---|
| Array transformation | Shape, indexing, vectorization |
| Filtering | Boolean masks, conditions |
| Broadcasting | Shape compatibility |
| Aggregation | Axis semantics, reductions |
| Dtypes | Overflow, precision, memory |
| Views and copies | Ownership and mutation |
| Memory | Temporary arrays, allocation |
| Batch processing | Large datasets |
| Validation | Production input contracts |
| Performance | Vectorization and benchmarking |

## Problem: Normalize Positive Numeric Values

Given a one-dimensional NumPy array, replace negative values with `0` and normalize the resulting values by the maximum value.

### Requirements

- Do not use a Python loop.
- Preserve a floating-point result.
- Handle an empty array safely.
- Avoid division by zero.

### Solution

```python
import numpy as np


def normalize_positive(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)

    if values.size == 0:
        return values.copy()

    cleaned = np.maximum(values, 0.0)
    maximum = cleaned.max()

    if maximum == 0.0:
        return np.zeros_like(cleaned)

    return cleaned / maximum
```

### Reasoning

The transformation is naturally vectorized:

```text
negative values
    ↓
np.maximum
    ↓
maximum
    ↓
division
```

There is no Python-level iteration over individual elements.

### Complexity

For `n` elements:

```text
Time:  O(n)
Space: O(n)
```

The additional space comes from the cleaned and normalized arrays.

When memory is highly constrained, the implementation can be rewritten around reusable output buffers, but that should be justified by profiling.

## Problem: Filter Invalid Measurements

Given a one-dimensional numeric array, return only finite values greater than or equal to zero.

### Solution

```python
import numpy as np


def filter_measurements(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values)

    mask = (
        np.isfinite(values)
        & (values >= 0)
    )

    return values[mask]
```

### Important Details

The mask combines conditions using:

```python
&
```

rather than:

```python
and
```

Parentheses are required around each comparison.

Boolean indexing normally returns a new array.

### Production Consideration

If the input may contain extremely large arrays, remember that the Boolean mask itself consumes memory.

For example:

```text
input array
+
Boolean mask
+
selected output
```

can temporarily require significantly more memory than the input alone.

## Problem: Calculate Row Totals

Given a two-dimensional array where each row represents a transaction and each column represents a component amount, calculate the total for each transaction.

### Input

```python
values = np.array(
    [
        [10.0, 20.0, 5.0],
        [100.0, 25.0, 10.0],
        [7.0, 8.0, 9.0],
    ]
)
```

### Solution

```python
row_totals = values.sum(axis=1)
```

Output:

```text
[ 35. 135.  24.]
```

### Axis Reasoning

For shape:

```text
(rows, columns)
```

use:

```python
axis=1
```

to reduce columns and retain one result per row.

Use:

```python
axis=0
```

to reduce rows and produce one result per column.

### Interview Trap

Do not memorize `axis=0` and `axis=1` independently.

Reason from the dimension being removed:

```text
axis=1
→ collapse columns
→ one result per row

axis=0
→ collapse rows
→ one result per column
```

## Problem: Apply Per-Column Scaling

Given a matrix of measurements and one scaling factor per column, apply the factors without loops.

### Input

```python
values = np.array(
    [
        [10.0, 20.0, 30.0],
        [40.0, 50.0, 60.0],
    ]
)

scales = np.array(
    [1.0, 0.5, 2.0],
)
```

### Solution

```python
scaled = values * scales
```

### Why It Works

Shapes:

```text
values → (2, 3)
scales → (3,)
```

NumPy aligns dimensions from the right:

```text
(2, 3)
   (3)
------
(2, 3)
```

The one-dimensional array is treated as:

```text
(1, 3)
```

for broadcasting purposes.

### Production Risk

Broadcasting is powerful but can hide logic errors.

If the intended factor shape is:

```text
(2, 3)
```

but the code receives:

```text
(3,)
```

NumPy may still accept the operation while applying a different semantic interpretation.

Validate shapes when the relationship matters to business correctness.

## Problem: Calculate Column Statistics

Given a two-dimensional dataset, return the mean, minimum, and maximum for every column.

### Solution

```python
import numpy as np


def column_statistics(
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=np.float64)

    if values.ndim != 2:
        raise ValueError(
            f"Expected 2-D input, got {values.shape}"
        )

    if values.shape[0] == 0:
        raise ValueError("Dataset must contain at least one row.")

    if not np.isfinite(values).all():
        raise ValueError("Dataset contains non-finite values.")

    return (
        values.mean(axis=0),
        values.min(axis=0),
        values.max(axis=0),
    )
```

### Production Considerations

This solution validates:

```text
dimensionality
+
non-empty input
+
finite values
```

before calculating statistics.

Do not assume every numerical array is valid merely because NumPy accepts it.

## Problem: Replace Invalid Values With Column Means

Given a two-dimensional floating-point array, replace `NaN` values in each column with that column's mean.

### Solution

```python
import numpy as np


def fill_nan_with_column_mean(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    ).copy()

    if values.ndim != 2:
        raise ValueError(
            f"Expected 2-D input, got {values.shape}"
        )

    valid_counts = np.sum(
        ~np.isnan(values),
        axis=0,
    )

    if np.any(valid_counts == 0):
        raise ValueError(
            "At least one column contains no valid values."
        )

    column_sums = np.nansum(
        values,
        axis=0,
    )

    means = column_sums / valid_counts

    rows, columns = np.where(
        np.isnan(values)
    )

    values[rows, columns] = means[columns]

    return values
```

### Reasoning

The implementation separates:

```text
valid count
+
valid sum
→
column mean
```

and then applies the corresponding mean to missing entries.

### Production Consideration

Replacing missing values with the mean is not universally correct.

The numerical technique is valid only when the application's missing-data policy permits it.

## Problem: Find Duplicate Rows

Given a two-dimensional numerical array, identify duplicate rows.

### Solution

```python
import numpy as np


def duplicate_rows(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values)

    if values.ndim != 2:
        raise ValueError(
            f"Expected 2-D input, got {values.shape}"
        )

    _, unique_indices, counts = np.unique(
        values,
        axis=0,
        return_index=True,
        return_counts=True,
    )

    duplicate_indices = unique_indices[counts > 1]

    return np.sort(duplicate_indices)
```

This returns the first occurrence index of rows that appear more than once.

### Interview Discussion

Ask whether the requirement is:

```text
first duplicate occurrence
all rows belonging to duplicate groups
duplicate row values
duplicate row indices
```

These are different problems.

Interviewers often use ambiguity deliberately to evaluate requirement clarification.

## Problem: Find the Top N Values

Given a large one-dimensional array, return the largest `n` values.

### Simple Solution

```python
import numpy as np


def top_n(
    values: np.ndarray,
    n: int,
) -> np.ndarray:
    values = np.asarray(values)

    if n < 0:
        raise ValueError("n must be non-negative.")

    if n > values.size:
        raise ValueError(
            f"n={n} exceeds array size={values.size}"
        )

    indices = np.argpartition(
        values,
        -n,
    )[-n:]

    return values[indices]
```

### Why `argpartition` Matters

A full sort:

```python
np.sort(values)[-n:]
```

orders every element.

For large arrays where only the top `n` elements are required, partitioning can avoid fully sorting the entire dataset.

However, the resulting top values are not guaranteed to be sorted.

If sorted output is required:

```python
result = np.sort(
    values[indices]
)[::-1]
```

### Complexity Discussion

The exact implementation details depend on NumPy's selection algorithm, but the important engineering distinction is:

```text
full sort
→ order everything

partition
→ identify a boundary without fully ordering all elements
```

The latter can be more appropriate when `n` is small relative to the dataset.

## Problem: Find the Row With Maximum Revenue

Each row contains:

```text
quantity
unit_price
```

Return the index of the row with the highest revenue.

### Solution

```python
import numpy as np


def highest_revenue_row(
    orders: np.ndarray,
) -> int:
    orders = np.asarray(
        orders,
        dtype=np.float64,
    )

    if orders.ndim != 2 or orders.shape[1] != 2:
        raise ValueError(
            "Expected shape (n, 2)."
        )

    revenue = (
        orders[:, 0]
        * orders[:, 1]
    )

    return int(np.argmax(revenue))
```

### Memory Consideration

This creates a separate `revenue` array.

For very large datasets, one could write into a reusable output buffer:

```python
revenue = np.empty(
    orders.shape[0],
    dtype=np.float64,
)

np.multiply(
    orders[:, 0],
    orders[:, 1],
    out=revenue,
)
```

The optimization is useful only when allocation pressure is demonstrated.

## Problem: Normalize Each Row

Normalize every row by its row sum.

### Solution

```python
import numpy as np


def row_normalize(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 2:
        raise ValueError(
            f"Expected 2-D input, got {values.shape}"
        )

    totals = values.sum(axis=1, keepdims=True)

    if np.any(totals == 0):
        raise ValueError(
            "Cannot normalize rows with zero sum."
        )

    return values / totals
```

### Important Detail

The critical part is:

```python
keepdims=True
```

Without it:

```text
values.shape
→ (rows, columns)

totals.shape
→ (rows,)
```

With it:

```text
totals.shape
→ (rows, 1)
```

which broadcasts naturally across columns.

This is a common interview test of shape reasoning.

## Problem: Standardize Columns

Standardize each column using:

```text
(value - mean) / standard deviation
```

### Solution

```python
import numpy as np


def standardize_columns(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 2:
        raise ValueError(
            f"Expected 2-D input, got {values.shape}"
        )

    means = values.mean(
        axis=0,
        keepdims=True,
    )

    standard_deviation = values.std(
        axis=0,
        keepdims=True,
    )

    if np.any(standard_deviation == 0):
        raise ValueError(
            "Cannot standardize constant columns."
        )

    return (
        values - means
    ) / standard_deviation
```

### Shape Reasoning

```text
values
→ (rows, columns)

means
→ (1, columns)

std
→ (1, columns)

result
→ (rows, columns)
```

This is a common pattern for NumPy broadcasting.

## Problem: Compute Weighted Values

Given values and weights, compute a weighted average.

### Solution

```python
import numpy as np


def weighted_average(
    values: np.ndarray,
    weights: np.ndarray,
) -> float:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    weights = np.asarray(
        weights,
        dtype=np.float64,
    )

    if values.shape != weights.shape:
        raise ValueError(
            "values and weights must have identical shapes."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "values contains non-finite data."
        )

    if not np.isfinite(weights).all():
        raise ValueError(
            "weights contains non-finite data."
        )

    total_weight = weights.sum()

    if total_weight == 0:
        raise ValueError(
            "Sum of weights must not be zero."
        )

    return float(
        np.sum(values * weights)
        / total_weight
    )
```

### Production Considerations

Validate:

```text
shape
+
finite values
+
finite weights
+
non-zero total weight
```

before calculation.

Whether negative weights are permitted is a domain-specific requirement and should be validated separately when necessary.

## Problem: Clip Outliers to Bounds

Given numerical measurements, constrain values to a minimum and maximum.

### Solution

```python
import numpy as np


def clip_measurements(
    values: np.ndarray,
    minimum: float,
    maximum: float,
) -> np.ndarray:
    if minimum > maximum:
        raise ValueError(
            "minimum must not exceed maximum."
        )

    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return np.clip(
        values,
        minimum,
        maximum,
    )
```

### Why `np.clip`?

It expresses the operation directly and avoids explicit Python branching.

It also keeps the implementation concise and vectorized.

### Business Warning

Clipping is not the same as validation.

If values outside the allowed range indicate corrupted or malicious input, silently clipping them may conceal the problem.

The correct question is:

```text
Should invalid data be corrected, rejected, or quarantined?
```

## Problem: Calculate a Rolling Window Without a Python Loop

Given a one-dimensional array, calculate a simple fixed-width moving average.

### Solution

```python
import numpy as np


def moving_average(
    values: np.ndarray,
    window: int,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            "Expected a one-dimensional array."
        )

    if window <= 0:
        raise ValueError(
            "window must be positive."
        )

    if window > values.size:
        raise ValueError(
            "window must not exceed input size."
        )

    cumulative = np.cumsum(values)

    cumulative = np.concatenate(
        [
            np.array([0.0]),
            cumulative,
        ]
    )

    totals = (
        cumulative[window:]
        - cumulative[:-window]
    )

    return totals / window
```

### Reasoning

The cumulative-sum technique transforms repeated window summation into:

```text
cumulative sum
+
two aligned slices
→
window totals
```

This avoids a Python loop over every window.

### Memory Trade-Off

The cumulative array requires additional memory.

This is a good example of the difference between:

```text
less Python work
```

and:

```text
less total resource usage
```

They are not always the same.

## Problem: Remove Duplicate Values While Preserving Order

Given a one-dimensional array, return unique values in first-seen order.

### Solution

```python
import numpy as np


def unique_preserving_order(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values)

    _, first_indices = np.unique(
        values,
        return_index=True,
    )

    return values[
        np.sort(first_indices)
    ]
```

Example:

```python
values = np.array(
    [5, 2, 5, 3, 2, 8]
)

result = unique_preserving_order(values)

print(result)
```

Output:

```text
[5 2 3 8]
```

### Interview Trap

`np.unique(values)` sorts the unique values by default.

That is different from preserving first-seen order.

Understanding default behavior matters as much as knowing the API.

## Problem: Replace Values Based on Multiple Conditions

Replace values according to:

```text
< 0       → 0
0–100     → unchanged
> 100     → 100
```

### Solution

```python
import numpy as np


def clamp_values(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    return np.clip(
        values,
        0.0,
        100.0,
    )
```

### More Complex Conditional Logic

When the transformations are genuinely different:

```python
result = np.where(
    values < 0,
    0.0,
    np.where(
        values > 100,
        100.0,
        values,
    ),
)
```

Prefer `np.clip` when the operation is simply bounding values.

The more direct API communicates intent better.

## Problem: Find Missing Values Per Column

Return the count of `NaN` values in each column.

### Solution

```python
import numpy as np


def missing_counts(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values)

    if values.ndim != 2:
        raise ValueError(
            "Expected a two-dimensional array."
        )

    return np.isnan(values).sum(axis=0)
```

### Complexity

```text
Time:  O(rows × columns)
Space: O(columns)
```

The Boolean result is reduced immediately, so the final output is only one count per column, although intermediate operations still have memory implications.

## Problem: Calculate Global Sum Safely

Given an integer array, calculate a sum using an explicitly chosen accumulator dtype.

### Solution

```python
import numpy as np


def safe_sum(
    values: np.ndarray,
) -> int:
    values = np.asarray(values)

    if not np.issubdtype(
        values.dtype,
        np.integer,
    ):
        raise TypeError(
            "Expected an integer array."
        )

    return int(
        values.sum(dtype=np.int64)
    )
```

### Why Explicitly Choose the Accumulator Type?

Input dtype and accumulation dtype are separate concerns.

A memory-efficient input representation does not automatically imply that its accumulator has enough range.

This distinction is important in high-volume counters and financial or operational aggregates.

## Problem: Compare Two Large Arrays Efficiently

Determine whether two arrays are equal within numerical tolerance.

### Solution

```python
import numpy as np


def arrays_match(
    actual: np.ndarray,
    expected: np.ndarray,
) -> bool:
    if actual.shape != expected.shape:
        return False

    return bool(
        np.allclose(
            actual,
            expected,
            rtol=1e-6,
            atol=1e-8,
            equal_nan=True,
        )
    )
```

### Why Not `==`?

Element-wise equality:

```python
actual == expected
```

returns an array of Boolean values.

For floating-point data, exact equality is often too strict.

`np.allclose` provides tolerance-based comparison.

## Problem: Validate a Numerical Batch

Write a reusable validation function for a numerical batch used by an API or Celery worker.

### Requirements

- one-dimensional
- at most 100,000 elements
- `float64`
- finite values only
- non-empty

### Solution

```python
import numpy as np


def validate_batch(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected 1-D input, got {values.shape}"
        )

    if values.size == 0:
        raise ValueError(
            "Batch must not be empty."
        )

    if values.size > 100_000:
        raise ValueError(
            "Batch exceeds maximum size."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Batch contains non-finite values."
        )

    return values
```

### Why This Is Interview-Relevant

The problem tests more than syntax:

```text
dtype
+
shape
+
size
+
validity
+
resource limits
```

This resembles a real service boundary rather than an isolated numerical exercise.

## Problem: Process Data in Batches

Suppose a source contains more data than can safely fit in memory. Process each batch and calculate the global sum.

### Incorrect Approach

```python
batch_means = [
    batch.mean()
    for batch in batches
]

global_mean = np.mean(batch_means)
```

This is generally incorrect when batch sizes differ.

### Correct Sum and Count Approach

```python
import numpy as np


def global_mean(
    batches: list[np.ndarray],
) -> float:
    total = 0.0
    count = 0

    for batch in batches:
        batch = np.asarray(
            batch,
            dtype=np.float64,
        )

        total += batch.sum()
        count += batch.size

    if count == 0:
        raise ValueError(
            "No values were provided."
        )

    return total / count
```

### Why It Works

Global mean is:

```text
total sum
---------
total count
```

not:

```text
mean(batch 1)
+
mean(batch 2)
...
----------------
number of batches
```

unless all batches have equal size.

This is a common interview problem because it tests both numerical reasoning and streaming design.

## Problem: Compute a Global Standard Deviation From Batches

Batching creates a more subtle problem for variance.

Do not simply average batch variances:

```python
np.mean(
    [
        batch.var()
        for batch in batches
    ]
)
```

That generally does not produce the global variance.

A robust streaming implementation can maintain mergeable statistics, but the exact algorithm depends on the required numerical guarantees.

For an interview, state the principle clearly:

```text
variance is not generally mergeable by averaging
batch variances
```

For high-quality production numerical aggregation, use a numerically stable online or mergeable variance algorithm rather than inventing a shortcut.

## Problem: Detect Whether a Batch Is Sorted

Determine whether a one-dimensional array is non-decreasing.

### Solution

```python
import numpy as np


def is_non_decreasing(
    values: np.ndarray,
) -> bool:
    values = np.asarray(values)

    if values.ndim != 1:
        raise ValueError(
            "Expected a one-dimensional array."
        )

    if values.size < 2:
        return True

    return bool(
        np.all(values[:-1] <= values[1:])
    )
```

### Why This Is Better Than Sorting

Sorting would change the data and perform unnecessary work.

The requirement is only to validate ordering.

This is a common engineering principle:

```text
validate the required property
rather than performing a more expensive transformation.
```

## Problem: Find Gaps in a Sequence

Given integer IDs, determine the missing IDs between the minimum and maximum values.

### Solution

```python
import numpy as np


def missing_ids(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.int64,
    )

    if values.size == 0:
        return np.empty(0, dtype=np.int64)

    expected = np.arange(
        values.min(),
        values.max() + 1,
        dtype=np.int64,
    )

    return expected[
        ~np.isin(expected, values)
    ]
```

### Production Consideration

This implementation is inappropriate when the ID range is enormous.

For example:

```text
min = 1
max = 10^12
```

would make constructing the full expected range infeasible.

This illustrates an important interview distinction:

```text
correct for small inputs
```

versus:

```text
scalable for arbitrary production inputs
```

Always ask about the expected range and cardinality.

## Problem: Calculate Per-Batch Revenue

Each row contains:

```text
quantity
unit_price
```

Process the data in bounded batches and return revenue totals.

### Solution

```python
import numpy as np


def batch_revenue(
    batches: list[np.ndarray],
) -> list[float]:
    totals: list[float] = []

    for batch in batches:
        batch = np.asarray(
            batch,
            dtype=np.float64,
        )

        if batch.ndim != 2 or batch.shape[1] != 2:
            raise ValueError(
                "Each batch must have shape (n, 2)."
            )

        quantity = batch[:, 0]
        unit_price = batch[:, 1]

        revenue = np.multiply(
            quantity,
            unit_price,
        )

        totals.append(
            float(revenue.sum())
        )

    return totals
```

### Scaling Consideration

If there are millions of batches, storing all totals may itself be unnecessary.

The architecture may instead:

```text
process batch
→ accumulate global metric
→ persist checkpoint
→ release batch
```

Do not optimize only the inner NumPy expression while ignoring the surrounding pipeline.

## Problem: Avoid a Huge Broadcasted Output

Suppose:

```python
a.shape == (50_000, 1)
b.shape == (1, 50_000)
```

The operation:

```python
result = a + b
```

creates a:

```text
(50_000, 50_000)
```

result.

### Interview Question

How would you avoid materializing this result if the downstream operation only needs the row-wise maximum?

The key insight is:

```text
Do not calculate the full matrix
if the final result can be computed without materializing it.
```

For:

```text
a.shape = (n, 1)
b.shape = (1, m)
```

the row-wise maximum of:

```text
a + b
```

is:

```text
a + max(b)
```

so:

```python
row_max = a[:, 0] + b.max()
```

This reduces the operation from an `n × m` allocation to an `n`-element result.

### Why This Matters

This is a senior-level NumPy optimization:

```text
avoid the expensive intermediate
rather than optimizing the expensive intermediate.
```

## Problem: Implement a Vectorized Threshold Counter

Count how many measurements fall into each of these ranges:

```text
< 10
10–49
50–99
>= 100
```

### Solution

```python
import numpy as np


def threshold_counts(
    values: np.ndarray,
) -> dict[str, int]:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    if not np.isfinite(values).all():
        raise ValueError(
            "Values must be finite."
        )

    return {
        "lt_10": int(
            np.count_nonzero(values < 10)
        ),
        "10_49": int(
            np.count_nonzero(
                (values >= 10)
                & (values < 50)
            )
        ),
        "50_99": int(
            np.count_nonzero(
                (values >= 50)
                & (values < 100)
            )
        ),
        "ge_100": int(
            np.count_nonzero(values >= 100)
        ),
    }
```

### Interview Discussion

For a small number of explicit thresholds, this is readable.

For many bins, consider:

```python
np.histogram(...)
```

The right API depends on whether the requirement is a few business categories or generalized binning.

## Problem: Convert a Flat Event Buffer Into Batches

Given a one-dimensional buffer and a batch size, split it without unnecessary copying when possible.

### Solution

```python
import numpy as np


def batch_views(
    values: np.ndarray,
    batch_size: int,
) -> list[np.ndarray]:
    values = np.asarray(values)

    if values.ndim != 1:
        raise ValueError(
            "Expected one-dimensional input."
        )

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be positive."
        )

    return [
        values[start:start + batch_size]
        for start in range(
            0,
            values.size,
            batch_size,
        )
    ]
```

Basic slicing generally returns views, so these batches can share memory with the source.

### Important Trade-Off

Views are useful when:

```text
read-only processing
```

is intended.

They can be dangerous when a batch-processing function mutates its input.

If mutation isolation is required:

```python
batch.copy()
```

should be explicit.

## Problem: Benchmark Loop vs Vectorized Computation

Compare a Python loop with vectorized multiplication.

### Solution

```python
import time
import numpy as np


def benchmark() -> None:
    values = np.arange(
        1_000_000,
        dtype=np.float64,
    )

    start = time.perf_counter()

    vectorized = values * 1.18

    vectorized_time = (
        time.perf_counter() - start
    )

    start = time.perf_counter()

    loop_result = np.empty_like(values)

    for index, value in enumerate(values):
        loop_result[index] = value * 1.18

    loop_time = (
        time.perf_counter() - start
    )

    np.testing.assert_allclose(
        vectorized,
        loop_result,
    )

    print(
        f"vectorized={vectorized_time:.6f}s"
    )
    print(
        f"loop={loop_time:.6f}s"
    )
```

### What the Interviewer Is Testing

The expected explanation is not simply:

```text
"NumPy is faster."
```

A stronger answer explains:

```text
Python loop
→ per-element interpreter overhead

NumPy vectorization
→ array-level native implementation
→ less Python-level iteration
```

But also acknowledge:

```text
allocation
+
memory bandwidth
+
dtype
+
cache behavior
```

still affect performance.

## Problem: Implement an In-Place Transformation

Given a floating-point array, multiply every value by a constant while reusing the existing output buffer.

### Solution

```python
import numpy as np


def scale_in_place(
    values: np.ndarray,
    factor: float,
) -> None:
    if not np.issubdtype(
        values.dtype,
        np.floating,
    ):
        raise TypeError(
            "Expected a floating-point array."
        )

    np.multiply(
        values,
        factor,
        out=values,
    )
```

### Trade-Off

Advantages:

```text
less allocation
+
potentially lower peak memory
```

Limitations:

```text
mutates input
+
requires writable compatible storage
```

Use in-place operations only when ownership and mutation are explicit.

## Problem: Handle Zero-Safe Division

Calculate:

```text
numerator / denominator
```

without producing divisions by zero.

### Solution

```python
import numpy as np


def safe_divide(
    numerator: np.ndarray,
    denominator: np.ndarray,
) -> np.ndarray:
    numerator = np.asarray(
        numerator,
        dtype=np.float64,
    )

    denominator = np.asarray(
        denominator,
        dtype=np.float64,
    )

    result = np.zeros(
        np.broadcast_shapes(
            numerator.shape,
            denominator.shape,
        ),
        dtype=np.float64,
    )

    np.divide(
        numerator,
        denominator,
        out=result,
        where=denominator != 0,
    )

    return result
```

### Why This Pattern Matters

This explicitly controls:

```text
output allocation
+
division locations
+
zero-denominator behavior
```

The required result for zero denominators is a business rule.

This implementation chooses `0.0`, but another service might require:

```text
NaN
+
error
+
missing value
```

The contract must define the behavior.

## Problem: Detect Unexpected Memory Sharing

Write a function that reports whether two arrays overlap in memory.

### Solution

```python
import numpy as np


def describe_memory_relationship(
    left: np.ndarray,
    right: np.ndarray,
) -> dict[str, bool]:
    return {
        "shares_memory": bool(
            np.shares_memory(left, right)
        ),
        "may_share_memory": bool(
            np.may_share_memory(left, right)
        ),
    }
```

### Interview Discussion

Use:

```python
np.shares_memory(...)
```

when you need a definitive overlap check.

Use:

```python
np.may_share_memory(...)
```

when a conservative possible-overlap check is sufficient.

The latter can report potential sharing even when the arrays do not actually overlap.

## Problem: Build a Production Numerical Pipeline Function

Design a function that:

1. accepts arbitrary array-like numerical input
2. converts to `float64`
3. rejects non-finite values
4. limits input size
5. calculates a vectorized transformed result
6. returns a newly allocated array

### Solution

```python
import numpy as np


def process_measurements(
    raw_values: object,
    *,
    scale: float,
    offset: float,
    max_elements: int = 100_000,
) -> np.ndarray:
    values = np.asarray(
        raw_values,
        dtype=np.float64,
    )

    if values.ndim != 1:
        raise ValueError(
            f"Expected 1-D input, got {values.shape}"
        )

    if values.size > max_elements:
        raise ValueError(
            "Input exceeds configured element limit."
        )

    if not np.isfinite(values).all():
        raise ValueError(
            "Input contains non-finite values."
        )

    return values * scale + offset
```

### Why This Is a Strong Interview Problem

It combines:

```text
conversion
+
shape validation
+
resource validation
+
numerical validation
+
vectorization
```

This resembles a real backend numerical boundary.

## Problem: Preserve Dtype Intentionally

Suppose a function receives integer data but must return `float32` to reduce memory usage.

### Solution

```python
import numpy as np


def to_float32(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(values)

    if not np.issubdtype(
        values.dtype,
        np.integer,
    ):
        raise TypeError(
            "Expected integer input."
        )

    result = values.astype(
        np.float32,
        copy=False,
    )

    return result
```

### Interview Trap

`copy=False` is not a guarantee that no copy occurs.

It is a request to avoid copying when possible.

If conversion requires a new representation, NumPy still needs to allocate one.

## Problem: Detect Non-Contiguous Input

Write a function that returns a C-contiguous representation.

### Solution

```python
import numpy as np


def ensure_c_contiguous(
    values: np.ndarray,
) -> np.ndarray:
    return np.ascontiguousarray(values)
```

### Why This Is Useful

It provides a clear boundary before code that expects or benefits from C-contiguous storage.

Do not automatically call it on every array.

A copy can cost:

```text
O(n) time
+
O(n) memory
```

The optimization is justified when the downstream access pattern benefits from the layout.

## Problem: Find Values Outside an Allowed Range

Return invalid values and their indices.

### Solution

```python
import numpy as np


def invalid_values(
    values: np.ndarray,
    minimum: float,
    maximum: float,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    mask = (
        (values < minimum)
        | (values > maximum)
    )

    indices = np.flatnonzero(mask)

    return indices, values[indices]
```

### Why `flatnonzero`?

For a one-dimensional selection problem, it directly returns the indices where the condition is true.

The same debugging technique is useful for production validation because it tells you:

```text
how many values are invalid
+
where they occurred
+
what values caused the problem
```

For sensitive data, avoid logging the actual values unless policy permits it.

## Problem: Process Only Finite Values

Calculate the mean of finite values while rejecting a completely invalid batch.

### Solution

```python
import numpy as np


def finite_mean(
    values: np.ndarray,
) -> float:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    finite = np.isfinite(values)

    if not finite.any():
        raise ValueError(
            "No finite values available."
        )

    return float(
        values[finite].mean()
    )
```

### Design Decision

This function drops invalid values.

That behavior must be explicit.

Another system may require:

```text
reject entire batch
```

instead.

Filtering and validation solve different business problems.

## Problem: Write a Shape-Safe Matrix Transformation

Given:

```text
X → (n, features)
weights → (features,)
bias → (features,)
```

calculate:

```text
X * weights + bias
```

### Solution

```python
import numpy as np


def transform_matrix(
    X: np.ndarray,
    weights: np.ndarray,
    bias: np.ndarray,
) -> np.ndarray:
    X = np.asarray(
        X,
        dtype=np.float64,
    )

    weights = np.asarray(
        weights,
        dtype=np.float64,
    )

    bias = np.asarray(
        bias,
        dtype=np.float64,
    )

    if X.ndim != 2:
        raise ValueError("X must be two-dimensional.")

    expected_features = X.shape[1]

    if weights.shape != (expected_features,):
        raise ValueError(
            "weights shape does not match feature count."
        )

    if bias.shape != (expected_features,):
        raise ValueError(
            "bias shape does not match feature count."
        )

    return X * weights + bias
```

### Interview Value

This tests:

```text
shape contracts
+
broadcasting
+
dtype
+
validation
+
vectorization
```

It is a better interview problem than simply asking for element-wise multiplication.

## Performance-Oriented Problem Patterns

For NumPy interviews, recognize these transformations:

| Problem | Prefer |
|---|---|
| Element-wise arithmetic | Vectorization |
| Conditional selection | Boolean masks / `where` |
| Row/column reduction | `sum`, `mean`, `min`, `max`, etc. |
| Per-axis normalization | Broadcasting |
| Top-K selection | `argpartition` |
| Range restriction | `clip` |
| Finite-value validation | `isfinite` |
| NaN-aware aggregation | `nan*` functions |
| Numerical comparison | `allclose` |
| Large input processing | Batching |
| Reusable output | `out=` when justified |
| Memory-layout requirement | `ascontiguousarray` |
| Shared-memory debugging | `shares_memory` |

## Common Interview Mistakes

### Writing Python Loops Immediately

Start by identifying whether the operation is naturally element-wise, reduction-based, or broadcastable.

### Ignoring Shapes

Many incorrect solutions are syntactically correct but dimensionally wrong.

State the expected shapes before writing the transformation.

### Assuming Broadcasting Means Correctness

Broadcasting only describes how NumPy combines compatible shapes.

It does not understand business semantics.

### Sorting When Only a Maximum Is Needed

Use:

```python
np.max(...)
```

or:

```python
np.argmax(...)
```

instead of sorting the entire array.

### Sorting When Only Top-K Is Needed

Consider:

```python
np.argpartition(...)
```

rather than fully sorting all values.

### Using `np.where` for Every Conditional Problem

Use the simplest operation that communicates intent:

```text
clip
mask
maximum
minimum
where
```

depending on the requirement.

### Ignoring Allocation

A vectorized expression can still allocate several arrays.

For memory-sensitive workloads, inspect:

```text
nbytes
+
temporary arrays
+
output size
```

### Mutating a View Accidentally

Always understand whether an operation returns a view or copy before mutating the result.

### Choosing Dtypes Only for Memory

A smaller dtype can reduce memory use while increasing overflow or precision risk.

## Interview Evaluation Criteria

A strong NumPy interview solution should demonstrate more than working syntax.

| Level | Expected Behavior |
|---|---|
| Basic | Produces correct output |
| Intermediate | Uses vectorized operations |
| Strong | Explains shapes and dtype |
| Senior | Discusses memory and complexity |
| Production-ready | Handles validation, scale, failure modes, and operational constraints |

A senior candidate should naturally discuss:

```text
shape contract
+
dtype contract
+
memory complexity
+
time complexity
+
invalid input behavior
+
scalability
```

## How to Explain a Solution in an Interview

A concise structure is:

### State the Data Model

Example:

```text
"The input is an n × 3 float array."
```

### State the Operation

```text
"I can express this as a vectorized column operation."
```

### Explain the Shape

```text
"The scaling vector has shape (3,), so it broadcasts across rows."
```

### Explain Complexity

```text
"The operation is O(n), with an additional output allocation."
```

### Explain Production Concerns

```text
"I would validate input size and dtype because the data can originate from an API."
```

This demonstrates engineering judgment rather than API memorization.

## Mini Interview Set

Use these as rapid practice questions.

| Question | Core Concept |
|---|---|
| Reverse a one-dimensional array without a loop | Slicing |
| Select all values above a threshold | Boolean masking |
| Replace negative values with zero | `maximum` / masking |
| Normalize each row | Broadcasting + reduction |
| Normalize each column | Broadcasting + reduction |
| Calculate totals per row | `axis=1` |
| Calculate totals per column | `axis=0` |
| Find the index of the largest value | `argmax` |
| Find top K values | `argpartition` |
| Find missing values | `isnan` |
| Reject invalid numerical values | `isfinite` |
| Compare floating-point arrays | `allclose` |
| Avoid division by zero | `divide(..., where=...)` |
| Detect shared memory | `shares_memory` |
| Preserve input while modifying output | `copy` |
| Process a dataset larger than RAM | Batching |
| Diagnose an unexpected huge result | Broadcasting + shape |
| Diagnose memory pressure | `nbytes` + allocations |
| Diagnose integer corruption | Dtype + overflow |
| Diagnose slow vectorized code | Allocation + layout + benchmark |

## Final Practice Strategy

For each problem, solve it in three passes:

```text
Pass 1
→ make it correct

Pass 2
→ remove unnecessary Python loops

Pass 3
→ analyze memory, dtype, shape, and scale
```

Then ask:

```text
What happens for an empty input?
What happens for NaN or infinity?
What happens when input is 100× larger?
Does this allocate?
Could broadcasting produce the wrong shape?
Does the dtype preserve correctness?
Would this fit inside a Celery/Kubernetes worker?
Can PostgreSQL or the upstream system do part of this work first?
```

This approach turns NumPy coding practice into production-oriented engineering practice.

## Key Takeaways

- Strong NumPy interview solutions combine correct output with explicit reasoning about shape, dtype, vectorization, and memory.
- Prefer vectorized operations, reductions, masking, broadcasting, and specialized selection APIs over unnecessary Python loops or full-array transformations.
- Always analyze allocation behavior, especially for broadcasting, temporary arrays, copies, and large intermediate results.
- Production-quality solutions validate input shape, size, dtype, and numerical validity rather than assuming NumPy's permissive behavior matches business requirements.
- Senior-level answers explain not only how the code works, but why it scales, when it can fail, and what alternative architecture may be better for the workload.