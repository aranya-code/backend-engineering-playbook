# 01- Arithmetic Operations

## Overview

NumPy arithmetic operations provide element-wise numerical computation over `ndarray` objects without requiring explicit Python loops.

For backend and data-processing workloads, arithmetic operations form the foundation of:

- Data transformation.
- Unit conversion.
- Normalization.
- Metric calculation.
- Threshold computation.
- Batch processing.
- Numerical validation.
- Aggregation pipelines.

The important engineering concepts are not the operators themselves, but how NumPy handles:

```text
dtype
+
shape
+
broadcasting
+
vectorization
+
allocation
+
overflow / precision
```

A typical pipeline looks like:

```mermaid
flowchart LR
    A["Raw Numerical Data"] --> B["Validate Shape / Dtype"]
    B --> C["Element-wise Arithmetic"]
    C --> D["Broadcast Parameters"]
    D --> E["Validate Result"]
    E --> F["Aggregate / Store / Return"]
```

## Element-wise Arithmetic

NumPy arithmetic operators operate element by element when applied to compatible arrays.

```python
import numpy as np

latency_ms = np.array(
    [120.0, 95.0, 140.0],
    dtype=np.float32,
)

baseline_ms = np.array(
    [100.0, 100.0, 100.0],
    dtype=np.float32,
)

delta_ms = latency_ms - baseline_ms

print(delta_ms)
# [20. -5. 40.]
```

The operation is conceptually:

```text
[120,  95, 140]
     -
[100, 100, 100]
     =
[ 20,  -5,  40]
```

The resulting array normally has the same shape as the operands after broadcasting.

Common element-wise operators include:

| Operator | Meaning |
|---|---|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `//` | Floor division |
| `%` | Modulo |
| `**` | Power |
| `-x` | Negation |
| `+x` | Unary positive |

The same operations can be expressed through NumPy functions such as:

```python
np.add()
np.subtract()
np.multiply()
np.divide()
np.floor_divide()
np.mod()
np.power()
```

The operator form is usually the clearest for straightforward expressions.

## Scalar Arithmetic

A scalar can be applied to every element.

```python
import numpy as np

prices = np.array(
    [100.0, 150.0, 200.0],
    dtype=np.float32,
)

discounted = prices * 0.90
```

Conceptually:

```text
price × 0.90
```

is applied independently to every element.

This is a simple case of broadcasting.

The Python equivalent would require an explicit loop:

```python
discounted = np.array(
    [price * 0.90 for price in prices],
    dtype=np.float32,
)
```

NumPy performs the operation using array-oriented execution rather than repeatedly executing Python-level arithmetic for every element.

## Arithmetic Between Arrays

Arrays can be combined when their shapes are compatible.

```python
import numpy as np

quantity = np.array(
    [2, 3, 4],
    dtype=np.int32,
)

unit_price = np.array(
    [10.0, 20.0, 15.0],
    dtype=np.float32,
)

line_total = quantity * unit_price

print(line_total)
# [20. 60. 60.]
```

The operation is useful in real processing pipelines:

```text
quantity × unit price
→ line total
```

The arrays must have compatible shapes according to NumPy's broadcasting rules.

## Broadcasting in Arithmetic

Broadcasting allows dimensions of compatible shapes to participate in element-wise arithmetic without explicitly replicating values.

For example:

```python
import numpy as np

records = np.array(
    [
        [100.0, 200.0, 300.0],
        [110.0, 210.0, 310.0],
    ],
    dtype=np.float32,
)

offsets = np.array(
    [1.0, 2.0, 3.0],
    dtype=np.float32,
)

adjusted = records + offsets
```

Shapes:

```text
records  → (2, 3)
offsets  → (3,)
result   → (2, 3)
```

The `offsets` array is logically aligned with the final dimension.

This is useful for operations such as:

- Per-feature offsets.
- Per-column scaling.
- Unit conversions.
- Threshold adjustments.
- Calibration values.

Do not confuse broadcasting with physically copying the smaller array. NumPy can often perform the operation without materializing repeated copies of the broadcast operand.

## Broadcasting Requirements

For each dimension, starting from the trailing dimension, sizes must either:

- Be equal.
- Have size `1`.
- Be missing from the smaller shape.

For example:

```text
(8, 1)
+
(1, 5)
→
(8, 5)
```

but:

```text
(8, 3)
+
(5,)
```

is incompatible because:

```text
3 != 5
```

Understanding this is essential for debugging arithmetic failures.

A useful diagnostic is:

```python
print(a.shape)
print(b.shape)
```

before the operation.

## Addition and Subtraction

Addition and subtraction are commonly used for offsets, differences, and transformations.

```python
import numpy as np

observed = np.array(
    [101.0, 98.0, 104.0],
    dtype=np.float32,
)

expected = 100.0

deviation = observed - expected
```

This pattern appears in:

- Monitoring.
- Quality checks.
- Sensor normalization.
- SLA calculations.
- Batch validation.

For example:

```python
within_tolerance = np.abs(deviation) <= 5.0
```

Combining arithmetic with boolean operations allows compact validation pipelines.

## Multiplication

Multiplication is commonly used for:

- Scaling.
- Unit conversion.
- Quantity × price calculations.
- Feature weighting.
- Percentage adjustments.

```python
import numpy as np

usage_kwh = np.array(
    [10.0, 14.0, 8.0],
    dtype=np.float32,
)

price_per_kwh = 6.5

cost = usage_kwh * price_per_kwh
```

For a matrix-like dataset:

```python
values *= 1.2
```

can update values in place when the dtype and operation permit it.

Be careful with in-place arithmetic because it mutates the original array.

## Division

Division deserves additional production attention because zero and dtype behavior matter.

```python
import numpy as np

completed = np.array(
    [100, 80, 120],
    dtype=np.float32,
)

total = np.array(
    [200, 100, 150],
    dtype=np.float32,
)

conversion_rate = completed / total
```

Result:

```text
[0.50, 0.80, 0.80]
```

### Division by Zero

For floating-point arrays:

```python
import numpy as np

values = np.array(
    [10.0, 20.0],
)

denominator = np.array(
    [2.0, 0.0],
)

result = values / denominator
```

This can produce:

```text
[5. inf]
```

with an associated floating-point warning depending on NumPy's error settings.

Do not rely on downstream code to discover invalid denominators.

Use an explicit condition when zero is invalid:

```python
safe_result = np.divide(
    values,
    denominator,
    out=np.zeros_like(values),
    where=denominator != 0,
)
```

Now the division occurs only where the denominator is non-zero.

The fallback value should be chosen according to the domain rather than assumed universally to be zero.

## Floor Division

Floor division uses:

```python
//
```

Example:

```python
import numpy as np

requests = np.array(
    [101, 205, 309],
    dtype=np.int64,
)

batch_size = 100

full_batches = requests // batch_size
```

This is useful for calculations such as:

```text
full batches
page groups
bucket indexes
```

Be careful with negative values because floor division rounds toward negative infinity rather than truncating toward zero.

## Modulo

Modulo uses:

```python
%
```

and is useful for:

- Remainders.
- Periodic grouping.
- Even/odd checks.
- Bucket calculations.

```python
import numpy as np

request_ids = np.array(
    [101, 102, 103, 104],
    dtype=np.int64,
)

shard_count = 4

shards = request_ids % shard_count
```

This can be useful for deterministic bucket assignment, although production sharding schemes should account for the distribution and stability requirements of the system.

## Powers

Element-wise exponentiation uses:

```python
import numpy as np

values = np.array(
    [2.0, 3.0, 4.0],
)

squared = values ** 2
```

NumPy also provides:

```python
np.square(values)
np.power(values, exponent)
```

Use the most readable form for the calculation.

Powers can increase numerical magnitude quickly, so overflow and dtype capacity should be considered for large values.

## Unary Operations

Negation is element-wise:

```python
import numpy as np

values = np.array(
    [10.0, -5.0, 3.0],
)

negated = -values
```

Absolute value is commonly used for tolerance and error calculations:

```python
absolute_error = np.abs(
    observed - expected
)
```

This is particularly useful for validating numerical outputs.

## Arithmetic and Dtype Promotion

NumPy arrays have fixed dtypes, and arithmetic can result in a dtype different from one or both inputs.

For example:

```python
import numpy as np

integers = np.array(
    [1, 2, 3],
    dtype=np.int32,
)

result = integers * 0.5

print(result.dtype)
```

The floating-point operand influences the resulting dtype.

Dtype promotion exists to produce a type capable of representing the operation's result without simply inheriting one operand's dtype.

Production code should still make important dtype requirements explicit.

For example:

```python
values = np.asarray(
    values,
    dtype=np.float32,
)
```

when a specific representation is part of the pipeline contract.

## Integer Overflow

Fixed-width integer dtypes have finite ranges.

For example:

```python
import numpy as np

values = np.array(
    [2_147_483_647],
    dtype=np.int32,
)

result = values + 1
```

The result cannot represent `2_147_483_648` in signed `int32` without overflow.

This differs from Python's built-in integers, which use arbitrary-precision arithmetic.

For counters, quantities, or database IDs, select an appropriate NumPy integer dtype based on the expected range.

Do not assume a smaller dtype is always safer or more efficient if the value range exceeds its capacity.

## Floating-Point Precision

Floating-point arithmetic is approximate.

For example:

```python
import numpy as np

result = np.array(
    [0.1],
    dtype=np.float64,
) + np.array(
    [0.2],
    dtype=np.float64,
)

print(result)
# [0.3]
```

Although this prints as expected, binary floating-point representation means exact decimal equality should not generally be assumed.

For numerical comparisons:

```python
np.isclose(actual, expected)
```

is usually safer than:

```python
actual == expected
```

For arrays:

```python
np.testing.assert_allclose(
    actual,
    expected,
)
```

is useful in tests.

## Arithmetic with `NaN` and Infinity

Arithmetic involving non-finite values propagates special floating-point values.

```python
import numpy as np

values = np.array(
    [10.0, np.nan, np.inf],
)

result = values * 2
```

The result contains:

```text
20.0
NaN
inf
```

Validate numerical inputs when required:

```python
finite = np.isfinite(values)
```

A production pipeline should distinguish between:

```text
NaN
→ missing / undefined numerical value

+inf / -inf
→ overflow, invalid operation, or domain-specific condition
```

Do not blindly replace all non-finite values without understanding their source.

## Conditional Arithmetic with `where`

`np.where()` is useful when the arithmetic depends on a condition.

For example:

```python
import numpy as np

values = np.array(
    [10.0, 0.0, 20.0],
)

result = np.where(
    values > 0,
    values * 1.1,
    0.0,
)
```

Conceptually:

```text
positive → multiply by 1.1
otherwise → 0
```

For actual division where zero denominators are possible, `np.divide(..., where=...)` is often more explicit because it controls where the division itself occurs.

## In-Place Arithmetic

Operations can sometimes be performed in-place:

```python
import numpy as np

values = np.array(
    [10.0, 20.0, 30.0],
    dtype=np.float32,
)

values *= 1.1
```

This can reduce allocations and memory pressure.

However, in-place operations have trade-offs:

- They mutate the original array.
- They may affect other views sharing the same data.
- They may require compatible dtypes.
- They can make debugging harder when mutation is unexpected.

Use in-place arithmetic when ownership is clear and avoiding the allocation has measurable value.

## Out-of-Place vs In-Place

| Approach | Memory | Mutation | Typical Use |
|---|---|---|---|
| `result = values * scale` | New result | No | Default, clear transformations |
| `values *= scale` | Usually reuses storage | Yes | Controlled performance-sensitive processing |
| `np.multiply(..., out=result)` | Explicit destination | Depends on destination | Reusable buffers / allocation control |

Prefer clarity until profiling demonstrates an allocation or memory bottleneck.

## `out=` and Allocation Control

NumPy ufuncs can write into a supplied output array.

```python
import numpy as np

values = np.array(
    [10.0, 20.0, 30.0],
    dtype=np.float32,
)

scaled = np.empty_like(values)

np.multiply(
    values,
    1.1,
    out=scaled,
)
```

This makes the destination explicit.

It is particularly useful in high-throughput loops where allocating a new result on every iteration would create avoidable memory pressure.

## Temporary Arrays

A mathematically simple expression may allocate multiple intermediate arrays.

For example:

```python
result = (values * scale + offset) / divisor
```

can conceptually involve:

```text
values * scale
       ↓
temporary
       ↓
+ offset
       ↓
temporary
       ↓
/ divisor
       ↓
result
```

For moderate arrays this is usually fine.

For very large arrays, temporary allocations can materially increase:

- Peak memory.
- Memory bandwidth.
- Garbage-collection pressure at the Python level.
- Overall runtime.

Optimization should be based on measurement rather than automatically rewriting every expression.

## Fusing Arithmetic Operations

When memory bandwidth is a bottleneck, reducing temporary arrays may improve performance.

For example, output-buffer operations can sometimes make intermediate storage explicit:

```python
import numpy as np

values = np.asarray(
    values,
    dtype=np.float32,
)

result = np.empty_like(values)

np.multiply(
    values,
    scale,
    out=result,
)

np.add(
    result,
    offset,
    out=result,
)
```

This can reduce allocations at the cost of more verbose code and a mutable output buffer.

For most application code, the straightforward vectorized expression is preferable unless profiling demonstrates a meaningful memory bottleneck.

## Vectorization and Python Loops

Compare:

```python
result = np.empty_like(values)

for index in range(values.size):
    result[index] = values[index] * scale + offset
```

with:

```python
result = values * scale + offset
```

The second approach avoids repeatedly entering Python-level loop execution for each element and allows NumPy's lower-level implementation to process the array efficiently.

The performance advantage depends on:

- Array size.
- Operation complexity.
- Memory bandwidth.
- Dtype.
- CPU.
- Number of temporary arrays.

Therefore:

```text
vectorized ≠ automatically optimal
```

but it is generally the right baseline for dense element-wise numerical processing.

## Arithmetic with Python Lists

Python lists and NumPy arrays have different data models.

```python
values = [10, 20, 30]
```

and:

```python
values = np.array(
    [10, 20, 30],
    dtype=np.int64,
)
```

are not interchangeable abstractions.

Python lists:

- Can contain heterogeneous objects.
- Store references to Python objects.
- Are general-purpose containers.

NumPy arrays:

- Use a homogeneous dtype.
- Store numerical values in a structured memory buffer.
- Support vectorized arithmetic.

For example, this:

```python
values * 2
```

does not mean the same thing for Python lists and NumPy arrays.

Python:

```python
[10, 20, 30] * 2
```

produces:

```python
[10, 20, 30, 10, 20, 30]
```

NumPy:

```python
np.array([10, 20, 30]) * 2
```

produces:

```text
[20, 40, 60]
```

Choose the data structure based on the workload rather than treating NumPy arrays as replacements for Python collections.

## Arithmetic in Batch Processing

For large numerical datasets, arithmetic should usually be applied in bounded batches.

```python
import numpy as np


def scale_batches(
    values: np.ndarray,
    scale: float,
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

        yield batch * scale
```

This pattern limits the amount of data processed simultaneously.

For file-backed or memory-mapped data, batch processing can prevent large arrays from being fully materialized in memory.

## Backend Example: Price Transformation

A backend data pipeline may receive:

```text
quantity
unit price
discount rate
tax rate
```

as dense numerical arrays.

The calculation can be expressed as:

```python
import numpy as np


def calculate_totals(
    quantity: np.ndarray,
    unit_price: np.ndarray,
    discount_rate: np.ndarray,
    tax_rate: np.ndarray,
) -> np.ndarray:
    subtotal = quantity * unit_price
    discounted = subtotal * (1.0 - discount_rate)
    total = discounted * (1.0 + tax_rate)

    return total
```

The pipeline is:

```text
quantity × unit_price
        ↓
    subtotal
        ↓
discount adjustment
        ↓
   taxable amount
        ↓
    tax adjustment
        ↓
     final total
```

Production validation should verify:

- Matching shapes.
- Valid rates.
- Finite values.
- Expected dtype.
- Domain-specific bounds.

For monetary systems, NumPy floating-point arithmetic may not be appropriate as the authoritative accounting representation. Database `NUMERIC`/decimal-based logic may be preferable when exact decimal semantics are required.

## Backend Example: Percentage Change

Percentage change can be expressed as:

```python
import numpy as np


def percentage_change(
    current: np.ndarray,
    previous: np.ndarray,
) -> np.ndarray:
    result = np.full(
        current.shape,
        np.nan,
        dtype=np.float64,
    )

    np.divide(
        current - previous,
        previous,
        out=result,
        where=previous != 0,
    )

    result *= 100.0

    return result
```

This pattern demonstrates several production concepts:

```text
arithmetic
+
safe division
+
preallocated output
+
explicit handling of zero denominators
```

The caller can then decide how undefined percentage changes should be represented.

## Arithmetic with Pandas

When working with labeled tabular data:

```python
frame["total"] = (
    frame["quantity"]
    * frame["unit_price"]
)
```

Pandas often provides the more readable abstraction because the column labels and missing-data semantics remain attached to the data.

NumPy becomes particularly useful after extracting dense numerical data for intensive array processing:

```python
values = frame[
    ["quantity", "unit_price"]
].to_numpy()

totals = values[:, 0] * values[:, 1]
```

Avoid converting between Pandas and NumPy repeatedly if the numerical calculation can be performed directly in the existing representation.

## Arithmetic with PostgreSQL

For relational operations such as:

```sql
SELECT quantity * unit_price
FROM order_items;
```

PostgreSQL may be the better location for the calculation when the data already resides there and only the resulting values are needed downstream.

NumPy is more appropriate when:

- Data has already crossed into Python.
- The operation is part of a larger numerical transformation.
- The input is file-based or array-oriented.
- Dense numerical processing is required.

Push computation toward the data source when this reduces:

```text
network transfer
+
memory usage
+
application CPU
```

without sacrificing the required numerical behavior.

## Monitoring and Validation

Arithmetic pipelines should expose enough telemetry to detect bad inputs and unexpected outputs.

Useful operational metrics include:

- Number of processed records.
- Number of invalid records.
- Number of non-finite results.
- Count of zero denominators.
- Minimum and maximum output values.
- Batch processing duration.
- Peak memory usage where important.

For example:

```python
result = calculate_totals(
    quantity,
    unit_price,
    discount_rate,
    tax_rate,
)

invalid = ~np.isfinite(result)

invalid_count = int(
    np.count_nonzero(invalid)
)
```

This can feed application metrics or structured logging.

Avoid logging entire numerical arrays in production because large payloads can create excessive log volume and may expose sensitive data.

## Security and Reliability Considerations

Arithmetic operations are not generally a security boundary, but numerical inputs can still create operational risks.

Validate:

- Maximum input sizes.
- Expected shapes.
- Allowed numeric ranges.
- Finite values where required.
- Denominators before division.
- Dtypes and conversions.
- Batch sizes.

Unbounded array inputs from an API can create memory exhaustion even when the arithmetic itself is simple.

For public APIs:

```text
request size limit
→ shape validation
→ dtype normalization
→ bounded processing
→ output validation
```

should happen before expensive numerical operations.

## Common Mistakes

### Using Python Loops for Dense Arithmetic

Element-by-element Python loops often add avoidable interpreter overhead.

Prefer vectorized NumPy operations for dense numerical arrays.

### Assuming Broadcasting Always Works

Shape compatibility must be checked according to NumPy's broadcasting rules.

### Ignoring Division by Zero

Unexpected `inf` or `NaN` values can silently contaminate later calculations.

Use explicit handling when zero denominators are possible.

### Mutating Shared Arrays Accidentally

In-place operations modify the original array and may also affect views sharing the same data.

### Ignoring Integer Overflow

Fixed-width NumPy integers have finite ranges.

### Treating Floating-Point Equality as Exact

Use tolerance-based comparisons for floating-point values.

### Creating Excessive Temporaries

Large arithmetic expressions can create intermediate arrays and increase peak memory usage.

Optimize only when measurement shows that temporary allocations are material.

### Using Floating-Point Arithmetic for Exact Monetary Semantics

Currency calculations may require decimal semantics and regulatory or accounting guarantees that binary floating-point arithmetic does not provide.

### Converting Between Pandas and NumPy Repeatedly

Repeated representation changes can allocate memory and make pipelines harder to reason about.

## Testing Arithmetic Operations

Test:

- Normal numerical values.
- Zero denominators.
- Negative values.
- Large values.
- `NaN`.
- Positive and negative infinity.
- Integer and floating dtypes.
- Broadcasting shapes.
- Empty inputs where supported.
- Numerical tolerance.

Example:

```python
import numpy as np


def test_percentage_change():
    current = np.array(
        [110.0, 80.0, 100.0],
    )

    previous = np.array(
        [100.0, 100.0, 100.0],
    )

    result = percentage_change(
        current,
        previous,
    )

    np.testing.assert_allclose(
        result,
        np.array([10.0, -20.0, 0.0]),
    )
```

Test the zero-denominator behavior separately:

```python
def test_percentage_change_zero_denominator():
    current = np.array(
        [10.0, 20.0],
    )

    previous = np.array(
        [0.0, 10.0],
    )

    result = percentage_change(
        current,
        previous,
    )

    assert np.isnan(result[0])
    assert result[1] == 100.0
```

For floating-point results, prefer:

```python
np.testing.assert_allclose(...)
```

over exact equality unless exact equality is genuinely part of the contract.

## Benchmarking Arithmetic

Benchmark realistic array sizes.

Avoid using only tiny examples such as:

```python
values = np.array([1, 2, 3])
```

because allocation and interpreter overhead can dominate the measurement.

A useful benchmark compares:

```text
Python loop
vs
vectorized NumPy
```

using the same input data and equivalent semantics.

For example:

```python
import time

start = time.perf_counter()

result = values * scale + offset

elapsed = time.perf_counter() - start

print(f"{elapsed:.6f}s")
```

For reliable performance analysis, prefer repeated measurements with tools such as `timeit` or a dedicated benchmark framework.

Measure:

- Runtime.
- Memory use when relevant.
- Input size.
- Dtype.
- Number of allocations where practical.

The goal is to explain **why** an implementation performs differently, not merely record a faster number.

## Interview Questions

### Why are NumPy arithmetic operations generally faster than equivalent Python loops?

NumPy operates on dense homogeneous arrays using optimized lower-level implementations, reducing Python interpreter overhead for each element.

### Does vectorized arithmetic always use less memory?

No. Vectorized expressions can still allocate temporary arrays. CPU efficiency and memory efficiency are separate concerns.

### What is broadcasting?

Broadcasting is NumPy's mechanism for applying compatible arrays with different shapes to element-wise operations without requiring explicit replication of the smaller operand.

### What happens when an integer NumPy array overflows?

The result is constrained by the fixed-width dtype and can wrap or otherwise produce a value that does not represent the mathematically expected result.

### Why can `a == b` be unsafe for floating-point results?

Binary floating-point arithmetic can introduce small representation errors. Tolerance-based comparison such as `np.isclose()` is usually more appropriate.

### When would you use an in-place operation such as `*=`, instead of creating a new array?

When the array is safely owned by the current operation, mutation is acceptable, and avoiding additional allocation materially benefits the workload.

### How would you safely divide an array by values that may contain zero?

Use `np.divide()` with `out=` and `where=` or otherwise validate the denominator before performing the division.

### How would you process arithmetic over a dataset larger than available RAM?

Read or access the data in bounded batches, perform vectorized arithmetic per batch, and persist or aggregate the results incrementally.

### When should arithmetic be performed in PostgreSQL instead of NumPy?

When the data is already relationally stored and the database can perform the operation efficiently before transferring the data to the application.

### Why should monetary calculations be treated differently?

Binary floating-point arithmetic does not provide exact decimal semantics. Systems requiring authoritative financial values may need decimal or database-native fixed-precision representations.

## Key Takeaways

- NumPy arithmetic is element-wise and vectorized, making it a strong foundation for dense numerical transformations when shape and dtype are well defined.
- Broadcasting enables arithmetic across compatible shapes without explicitly materializing repeated operands, but incompatible shapes fail at runtime.
- Production code must account for dtype promotion, integer overflow, floating-point precision, `NaN`, infinity, and division by zero.
- In-place operations and `out=` can reduce allocations, but they introduce mutation and ownership concerns that should be managed deliberately.
- Optimize arithmetic based on measured CPU and memory behavior; vectorization is the baseline, not a guarantee that every expression is allocation-efficient.