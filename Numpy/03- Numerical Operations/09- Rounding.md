# 09- Rounding

## Overview

Rounding converts numerical values into a representation with fewer fractional digits or to a specified numerical boundary.

NumPy provides several related operations:

```python
np.round()
np.around()
np.rint()
np.floor()
np.ceil()
np.trunc()
```

These operations are not interchangeable.

For backend and data-processing systems, rounding is commonly used for:

- Display-oriented numerical output.
- Unit conversion.
- Capacity calculations.
- Bucket boundaries.
- Rate calculations.
- Aggregation cleanup.
- Data normalization.
- Fixed-precision analytical output.

The important engineering questions are:

```text
What rounding rule is required?
+
Is the result for computation or presentation?
+
How are negative values handled?
+
What happens at exact half values?
+
What dtype is produced?
+
Is exact decimal arithmetic required?
```

A production numerical pipeline should distinguish:

```text
rounding for representation
vs
rounding for business semantics
```

## `np.round()`

`np.round()` rounds values to a specified number of decimal places.

```python
import numpy as np

values = np.array(
    [1.234, 2.567, 10.125],
    dtype=np.float64,
)

rounded = np.round(
    values,
    decimals=2,
)

print(rounded)
# [ 1.23  2.57 10.12]
```

Negative `decimals` round to positions to the left of the decimal point:

```python
values = np.array(
    [1234.0, 1567.0, 1875.0],
)

rounded = np.round(
    values,
    decimals=-2,
)
```

This rounds to hundreds.

`np.around()` is an equivalent spelling of `np.round()`.

## Rounding Rules

A critical detail is that NumPy's default floating-point rounding follows **round-half-to-even** behavior.

For example:

```python
import numpy as np

values = np.array(
    [1.5, 2.5, 3.5, 4.5],
)

result = np.round(values)

print(result)
# [2. 2. 4. 4.]
```

This differs from the informal rule:

```text
"always round .5 upward"
```

because NumPy rounds ties toward the nearest even result.

This behavior is useful for reducing systematic bias when many values lie exactly at halfway boundaries.

Do not assume:

```text
1.5 → 2
2.5 → 3
```

for NumPy's default rounding semantics.

## Why Round-Half-to-Even Matters

Consider repeated rounding of many values.

Always rounding halfway values upward can introduce a systematic positive bias.

Round-half-to-even instead distributes exact halfway cases based on the parity of the neighboring integers.

This matters in:

- Large numerical datasets.
- Financial analytics where the exact business rule permits it.
- Statistical calculations.
- Repeated numerical transformations.

The correct rule is still domain-specific. Some business systems explicitly require another rule such as half-up or half-away-from-zero.

NumPy's default behavior should not be assumed to match an external accounting or regulatory specification.

## `np.around()`

`np.around()` is equivalent to `np.round()`:

```python
import numpy as np

values = np.array(
    [1.234, 5.678],
)

result = np.around(
    values,
    decimals=2,
)
```

In normal application code, use whichever spelling best matches the surrounding codebase. Consistency is more important than choosing between the two.

## `np.rint()`

`np.rint()` rounds each value to the nearest integer-valued floating-point representation.

```python
import numpy as np

values = np.array(
    [1.2, 1.8, 2.5, 3.5],
)

result = np.rint(values)
```

The result remains a floating-point array rather than necessarily becoming an integer dtype.

This is useful when:

```text
rounded numerical values
```

are still part of a floating-point numerical pipeline.

If an integer dtype is required, perform an explicit conversion after validating the numeric range:

```python
rounded = np.rint(values).astype(
    np.int64
)
```

Do not convert blindly when values can contain `NaN`, infinity, or values outside the target integer range.

## `np.floor()`

`np.floor()` rounds toward negative infinity.

```python
import numpy as np

values = np.array(
    [1.2, 1.8, -1.2, -1.8],
)

result = np.floor(values)

print(result)
# [ 1.  1. -2. -2.]
```

This distinction matters for negative numbers.

`floor()` does **not** mean:

```text
remove the decimal portion
```

For that behavior, use `trunc()`.

## `np.ceil()`

`np.ceil()` rounds toward positive infinity:

```python
import numpy as np

values = np.array(
    [1.2, 1.8, -1.2, -1.8],
)

result = np.ceil(values)

print(result)
# [ 2.  2. -1. -1.]
```

It is useful when the application must allocate enough capacity to cover a requirement.

For example:

```python
import numpy as np

requested_bytes = np.array(
    [1001, 2048, 4097],
    dtype=np.int64,
)

block_size = 4096

blocks = np.ceil(
    requested_bytes / block_size,
).astype(np.int64)
```

This expresses:

```text
number of blocks required
```

rather than:

```text
number of blocks that fit completely
```

## `np.trunc()`

`np.trunc()` removes the fractional part by moving toward zero.

```python
import numpy as np

values = np.array(
    [1.8, 1.2, -1.2, -1.8],
)

result = np.trunc(values)

print(result)
# [ 1.  1. -1. -1.]
```

Compare:

```text
value   floor   trunc   ceil
 1.8      1       1       2
-1.8     -2      -1      -1
```

This distinction is important for bucket calculations and signed numerical values.

## Rounding Function Comparison

| Function | Behavior | Example `-1.8` | Typical Use |
|---|---|---:|---|
| `np.round()` | Nearest, ties to even | `-2.0` | Decimal-place rounding |
| `np.around()` | Same as `round()` | `-2.0` | Same use |
| `np.rint()` | Nearest integer-valued float | `-2.0` | Numerical integer rounding |
| `np.floor()` | Toward `-∞` | `-2.0` | Lower boundary |
| `np.ceil()` | Toward `+∞` | `-1.0` | Capacity / upper boundary |
| `np.trunc()` | Toward `0` | `-1.0` | Remove fractional component |

Choosing the wrong function can produce a result that is numerically valid but operationally incorrect.

## Decimal Places vs Significant Digits

NumPy's `decimals` parameter controls decimal-place positioning:

```python
np.round(
    values,
    decimals=2,
)
```

It does **not** directly mean:

```text
two significant digits
```

For example:

```text
1234.56
```

rounded to two decimal places is:

```text
1234.56
```

while two significant digits would represent a different requirement.

If the application needs significant-figure formatting, treat that as a separate presentation or formatting problem rather than assuming `decimals` provides it.

## Rounding Negative Decimal Places

Negative `decimals` are useful for larger units:

```python
import numpy as np

values = np.array(
    [123, 456, 789],
)

hundreds = np.round(
    values,
    decimals=-2,
)

print(hundreds)
# [100. 500. 800.]
```

This can be useful for:

- Capacity estimates.
- Coarse bucketing.
- Operational summaries.
- Reporting.

Do not use coarse rounding in an authoritative calculation when the discarded precision matters.

## Floating-Point Representation

Rounding interacts with floating-point representation.

For example:

```python
import numpy as np

value = np.array(
    [2.675],
)

result = np.round(
    value,
    decimals=2,
)

print(result)
```

The result may not match an intuition formed from exact decimal arithmetic because `2.675` is represented approximately in binary floating-point.

This is not a NumPy-specific bug.

The engineering principle is:

```text
binary floating-point
≠
exact decimal arithmetic
```

When exact decimal semantics matter, use an appropriate decimal representation rather than relying on `float64` rounding.

## Rounding for Display vs Rounding for Computation

This distinction is critical.

For display:

```python
display_values = np.round(
    values,
    decimals=2,
)
```

may be acceptable.

For computation:

```python
values = np.round(
    values,
    decimals=2,
)

total = values.sum()
```

changes the underlying values before aggregation.

That can introduce accumulated error.

A safer general pattern is:

```text
retain full precision internally
        ↓
perform calculations
        ↓
round only at the required boundary
        ↓
format / serialize / present
```

Unless the domain explicitly requires rounding at each intermediate step.

## Example: Financial Calculation

Suppose:

```python
import numpy as np

prices = np.array(
    [10.125, 20.375],
    dtype=np.float64,
)

quantity = np.array(
    [10, 5],
    dtype=np.int64,
)

line_totals = prices * quantity
```

It may be tempting to round every line immediately:

```python
line_totals = np.round(
    line_totals,
    decimals=2,
)
```

Whether that is correct depends on the financial contract.

Some systems require:

```text
round each line
→ sum rounded lines
```

while others require:

```text
sum exact intermediate values
→ round final total
```

These produce different results in some cases.

The rounding policy should therefore come from the domain specification, not from NumPy convenience.

For authoritative monetary computation, exact decimal or fixed-precision database representations are often more appropriate than binary floating-point.

## Rounding and Integer Conversion

A common pattern is:

```python
rounded = np.rint(
    values
)

result = rounded.astype(
    np.int64
)
```

This should only be done after validation.

For example:

```python
import numpy as np


def rounded_int(
    values: np.ndarray,
) -> np.ndarray:
    if not np.all(np.isfinite(values)):
        raise ValueError(
            "Values must be finite"
        )

    rounded = np.rint(values)

    info = np.iinfo(np.int64)

    if np.any(rounded < info.min) or np.any(
        rounded > info.max
    ):
        raise ValueError(
            "Values exceed int64 range"
        )

    return rounded.astype(
        np.int64
    )
```

The validation prevents invalid or out-of-range floating-point values from being converted silently.

## Rounding and Dtype

Rounding generally preserves a floating-point representation when the input is floating-point.

For example:

```python
import numpy as np

values = np.array(
    [1.2, 2.8],
    dtype=np.float32,
)

result = np.round(values)

print(result.dtype)
# float32
```

If an integer representation is required, convert explicitly.

Do not conflate:

```text
rounded numerical value
```

with:

```text
integer dtype
```

They are separate properties.

## Rounding and NaN

Rounding does not make invalid values valid.

```python
import numpy as np

values = np.array(
    [1.234, np.nan, np.inf],
)

result = np.round(
    values,
    decimals=2,
)
```

`NaN` and infinity remain non-finite.

Before converting rounded values to integer types, validate:

```python
finite = np.isfinite(
    values
)
```

Do not assume rounding can safely sanitize non-finite inputs.

## Floor and Ceil for Resource Allocation

A common backend use case is converting a continuous request into discrete capacity units.

For example:

```python
import numpy as np

requested_cpu = np.array(
    [0.25, 0.50, 1.20, 2.01],
)

cores = np.ceil(
    requested_cpu
).astype(np.int64)
```

This ensures enough capacity is reserved.

Using `floor()` instead:

```python
cores = np.floor(
    requested_cpu
).astype(np.int64)
```

can under-allocate resources.

The choice should reflect the business semantics:

```text
need at least enough
→ ceil

need completed full units
→ floor
```

## Bucketing with Floor

Flooring can create deterministic buckets.

For example:

```python
import numpy as np

latency_ms = np.array(
    [12, 57, 103, 149, 202],
)

bucket = np.floor(
    latency_ms / 50
).astype(np.int64)

print(bucket)
# [0 1 2 2 4]
```

The bucket number can then represent:

```text
0 → 0–49
1 → 50–99
2 → 100–149
...
```

For very large datasets, bucket semantics should be documented carefully, especially around exact boundaries.

## Ceil for Pagination and Batching

Capacity calculations often use ceiling.

```python
import numpy as np

record_count = np.array(
    [101, 200, 201],
)

batch_size = 100

batch_count = np.ceil(
    record_count / batch_size
).astype(np.int64)
```

Expected result:

```text
[2, 2, 3]
```

This is appropriate because a partial final batch still requires one additional batch.

For scalar Python calculations, integer arithmetic may be simpler:

```python
batch_count = (
    record_count + batch_size - 1
) // batch_size
```

The NumPy implementation is useful when processing many values at once.

## Rounding and Vectorization

NumPy rounding operations are vectorized:

```python
rounded = np.round(
    values,
    decimals=2,
)
```

This avoids explicit Python loops:

```python
rounded = np.array(
    [
        round(value, 2)
        for value in values
    ]
)
```

For dense numerical arrays, the vectorized approach is usually the appropriate baseline.

The performance benefit comes from reducing Python-level per-element execution and operating directly on NumPy's numerical buffers.

It does not guarantee that every rounding expression will be memory-optimal.

## Temporary Arrays

Consider:

```python
rounded = np.round(
    values * exchange_rate,
    decimals=2,
)
```

The multiplication may create an intermediate array before rounding.

For moderate arrays this is normally acceptable.

For very large arrays:

```text
input
+
temporary multiplication result
+
rounded output
```

can increase peak memory.

When profiling identifies memory pressure, consider reusable buffers and staged computation.

Do not introduce complex output-buffer code unless the memory savings justify the added complexity.

## Output Buffers

NumPy functions that support `out=` can reuse storage in suitable situations.

For an element-wise operation:

```python
import numpy as np

values = np.array(
    [1.234, 5.678, 9.101],
)

result = np.empty_like(
    values
)

np.round(
    values,
    decimals=2,
    out=result,
)
```

This can be useful in repeated batch processing.

The trade-off is that buffer ownership becomes part of the function design.

## Rounding in Batch Pipelines

For large datasets:

```text
input file
    ↓
batch
    ↓
vectorized calculation
    ↓
round if required by contract
    ↓
persist / serialize
    ↓
next batch
```

A batch-oriented function might be:

```python
import numpy as np


def round_batches(
    values: np.ndarray,
    decimals: int,
    batch_size: int,
):
    for start in range(
        0,
        values.shape[0],
        batch_size,
    ):
        batch = values[
            start:start + batch_size
        ]

        yield np.round(
            batch,
            decimals=decimals,
        )
```

This keeps the working set bounded by the batch size.

## Rounding and PostgreSQL

PostgreSQL supports explicit numeric rounding:

```sql
SELECT ROUND(amount, 2)
FROM transactions;
```

When authoritative values already reside in PostgreSQL and the required semantics match the database's numeric representation and rounding rules, database-side rounding may be preferable.

This can reduce:

- Data transfer.
- Application memory usage.
- Serialization.
- Duplicate business logic.

When rounding is part of a dense numerical transformation already happening in Python, NumPy may be appropriate.

For financial systems, verify that both layers implement exactly the required rounding policy before moving calculations between them.

## Rounding and Pandas

Pandas provides:

```python
frame["amount"].round(2)
```

for labeled tabular data.

NumPy can still provide the underlying numerical operation:

```python
frame["normalized"] = np.round(
    frame["normalized"],
    decimals=3,
)
```

Use Pandas when labels, grouping, and tabular semantics are central.

Use NumPy when dense numerical array processing is already the abstraction.

Avoid unnecessary conversions simply to round a DataFrame column.

## Monitoring and Validation

Rounding can alter values enough to affect downstream thresholds.

For example:

```python
rounded = np.round(
    values,
    decimals=2,
)

exceeds_limit = rounded > limit
```

can produce a different decision from:

```python
exceeds_limit = values > limit
```

If the threshold is defined against the unrounded measurement, perform the comparison before rounding.

If the threshold is defined against the reported or billable rounded value, round first.

This ordering should be explicit in production logic.

## Example: Threshold Ordering

Suppose:

```text
raw value = 99.996
limit = 100.00
```

Then:

```python
raw_value > 100.0
```

is false.

After rounding:

```python
np.round(99.996, 2)
```

becomes:

```text
100.00
```

and:

```python
rounded_value >= 100.0
```

is true.

The difference is not numerical noise; it reflects different business rules.

## Common Mistakes

### Assuming `.5` Always Rounds Up

NumPy uses round-half-to-even behavior for `np.round()`.

### Using `round()` to Implement Financial Rules Automatically

Financial systems may require a specific rounding mode that does not match NumPy's default.

### Rounding Too Early

Early rounding can introduce cumulative error.

Retain precision until the calculation reaches the boundary where rounding is required.

### Confusing `floor()` with Truncation

For negative numbers:

```text
floor(-1.8) = -2
trunc(-1.8) = -1
```

### Using `ceil()` When Capacity Is Not the Requirement

Ceiling intentionally rounds upward and can over-allocate.

### Converting to Integer Without Validation

`NaN`, infinity, and out-of-range values should be handled before integer conversion.

### Assuming Floating-Point Decimal Values Are Exact

Binary floating-point cannot represent every decimal value exactly.

### Rounding Before a Threshold Comparison Without Checking the Contract

Rounding can change whether a value crosses a boundary.

### Repeatedly Rounding During a Pipeline

Each rounding step can discard information and introduce accumulated error.

### Treating Display Rounding as Data Mutation

Values shown as two decimal places do not necessarily need to be stored at two decimal places.

## Testing

Test the rounding rule explicitly:

```python
import numpy as np


def test_round_half_to_even():
    values = np.array(
        [1.5, 2.5, 3.5, 4.5],
    )

    result = np.round(values)

    np.testing.assert_array_equal(
        result,
        np.array(
            [2.0, 2.0, 4.0, 4.0],
        ),
    )
```

Test directional rounding:

```python
def test_floor_ceil_trunc():
    values = np.array(
        [-1.8, -1.2, 1.2, 1.8],
    )

    np.testing.assert_array_equal(
        np.floor(values),
        np.array([-2.0, -2.0, 1.0, 1.0]),
    )

    np.testing.assert_array_equal(
        np.ceil(values),
        np.array([-1.0, -1.0, 2.0, 2.0]),
    )

    np.testing.assert_array_equal(
        np.trunc(values),
        np.array([-1.0, -1.0, 1.0, 1.0]),
    )
```

Test decimal-place behavior:

```python
def test_decimal_places():
    values = np.array(
        [1.2345, 10.9876],
    )

    result = np.round(
        values,
        decimals=2,
    )

    np.testing.assert_allclose(
        result,
        np.array([1.23, 10.99]),
    )
```

Also test:

- Negative `decimals`.
- Negative values.
- `NaN`.
- Infinity.
- Different dtypes.
- Integer conversion.
- Boundary values.
- Exact half cases.
- Threshold comparisons before and after rounding.

## Debugging Rounding Issues

When a rounded result appears incorrect, inspect:

```python
print("dtype:", values.dtype)
print("values:", values)
```

Then verify:

```text
Which rounding operation?
Which decimal position?
What happens at exact half values?
Is the input already approximate floating-point data?
Is rounding being applied before or after a business rule?
```

For financial or compliance-sensitive code, write the rounding rule explicitly in tests rather than relying on a generic numerical expectation.

## Interview Questions

### What is the default rounding behavior of `np.round()` for exact halfway values?

It uses round-half-to-even.

### What is the difference between `round`, `floor`, `ceil`, and `trunc`?

- `round` selects the nearest value according to its rounding rule.
- `floor` moves toward negative infinity.
- `ceil` moves toward positive infinity.
- `trunc` moves toward zero.

### Why can `np.round(2.675, 2)` surprise developers?

Because `2.675` is represented approximately in binary floating-point, so the stored value is not necessarily the exact decimal value assumed by the developer.

### Should rounding happen before or after aggregation?

Usually after the full-precision calculation unless the domain explicitly requires each intermediate value to be rounded.

### Why can rounding affect threshold decisions?

Rounding changes the value being compared. A value just below or above a threshold can cross that boundary after rounding.

### When should `ceil()` be preferred over `floor()`?

When the system must allocate enough discrete capacity to satisfy a continuous requirement.

### Is NumPy rounding appropriate for authoritative monetary calculations?

Not automatically. Exact decimal or fixed-precision semantics may be required, depending on the financial contract.

### How can rounding affect memory usage?

Rounding creates a result array unless storage is reused, so very large transformations can increase peak memory.

### What should be checked before converting rounded values to integers?

Finite values, numeric range, expected dtype, and the required rounding semantics.

### When should rounding be performed in PostgreSQL instead of NumPy?

When the authoritative calculation already occurs in the database and database-side rounding can enforce the required policy before values cross the application boundary.

## Key Takeaways

- NumPy provides different rounding semantics through `round`, `rint`, `floor`, `ceil`, and `trunc`; selecting the correct operation is a business and numerical correctness decision.
- `np.round()` uses round-half-to-even behavior, so exact halfway values should not be assumed to round upward.
- Preserve full numerical precision during intermediate calculations unless the domain explicitly requires earlier rounding, because premature rounding can introduce cumulative error.
- Binary floating-point rounding is not equivalent to exact decimal arithmetic, making authoritative financial calculations a separate design concern.
- In production pipelines, define rounding order, threshold interaction, dtype conversion, invalid-value handling, and execution layer explicitly, especially when processing large datasets.