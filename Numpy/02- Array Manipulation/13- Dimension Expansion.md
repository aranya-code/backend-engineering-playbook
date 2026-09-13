# 13- Dimension Expansion

## Overview

Dimension expansion adds a size-one axis to an existing NumPy array without changing the underlying number of elements.

The primary tools are:

- `np.expand_dims()`
- `np.newaxis`
- `None` indexing

The essential transformation is:

```text
(3,)
   ↓ expand dimension
(1, 3)

(3,)
   ↓ expand dimension
(3, 1)
```

The values remain the same; only the array's dimensional structure changes.

Dimension expansion is especially important for broadcasting because a size-one axis controls **where** another array can align.

```mermaid
flowchart LR
    A["Existing ndarray"] --> B["Insert size-1 axis"]
    B --> C["New shape"]
    C --> D["Broadcasting"]
    D --> E["Vectorized operation"]
```

For backend and data-engineering workloads, dimension expansion is usually a shape-management operation rather than a data-materialization operation.

## Why Dimension Expansion Exists

Many numerical operations require arrays to have compatible shapes.

Suppose:

```text
records.shape = (1000, 8)
```

and you have one value per record:

```text
weights.shape = (1000,)
```

If the weight must apply across all eight features, the intended shape is:

```text
(1000, 1)
```

Dimension expansion makes that relationship explicit:

```python
weights = weights[:, np.newaxis]
```

Now:

```text
records → (1000, 8)
weights → (1000, 1)
```

and broadcasting produces:

```text
result → (1000, 8)
```

The extra dimension is not new data. It is structural information that controls how NumPy aligns the arrays.

## `np.expand_dims()`

The explicit API for dimension expansion is `np.expand_dims()`.

```python
import numpy as np

values = np.array([10, 20, 30])

expanded = np.expand_dims(
    values,
    axis=0,
)

print(values.shape)
# (3,)

print(expanded.shape)
# (1, 3)
```

The operation inserts a size-one dimension at the requested position.

The element count remains:

```text
3
```

Only the shape changes.

## Expanding at `axis=1`

```python
import numpy as np

values = np.array([10, 20, 30])

expanded = np.expand_dims(
    values,
    axis=1,
)

print(expanded.shape)
# (3, 1)
```

The two common transformations are:

```text
(3,)
→ axis=0
→ (1, 3)
```

and:

```text
(3,)
→ axis=1
→ (3, 1)
```

They contain the same values but have different broadcasting semantics.

## `np.newaxis`

`np.newaxis` is an indexing-based way to add a size-one dimension.

```python
import numpy as np

values = np.array([10, 20, 30])

row = values[np.newaxis, :]

column = values[:, np.newaxis]

print(row.shape)
# (1, 3)

print(column.shape)
# (3, 1)
```

`np.newaxis` is an alias for `None`.

Therefore:

```python
values[:, np.newaxis]
```

and:

```python
values[:, None]
```

have the same effect.

## `None` Indexing

The concise form is often used in numerical code:

```python
values[:, None]
```

For example:

```python
import numpy as np

values = np.array([1, 2, 3])

result = values[:, None]

print(result)
```

```text
[[1]
 [2]
 [3]]
```

Shape:

```text
(3, 1)
```

The operation is useful because the new axis can be inserted exactly where the indexing expression requires it.

## Comparing the Main Approaches

| Technique | Example | Result shape | Primary purpose |
|---|---|---|---|
| `np.expand_dims()` | `np.expand_dims(x, 0)` | `(1, n)` | Explicit dimension insertion |
| `np.newaxis` | `x[np.newaxis, :]` | `(1, n)` | Readable indexing-based expansion |
| `None` | `x[None, :]` | `(1, n)` | Concise form of `np.newaxis` |
| `reshape()` | `x.reshape(1, -1)` | `(1, n)` | General shape transformation |

A practical convention is:

```text
Need explicit axis insertion?
→ expand_dims()

Need concise broadcasting syntax?
→ newaxis / None

Already doing shape manipulation?
→ reshape()
```

## Dimension Expansion Does Not Increase Element Count

Consider:

```python
import numpy as np

values = np.arange(12)

expanded = values.reshape(1, 12)

print(values.size)
# 12

print(expanded.size)
# 12

print(values.nbytes)
# same data-buffer size
```

The shape changes:

```text
(12,)
→
(1, 12)
```

but:

```text
number of elements = unchanged
```

This makes dimension expansion fundamentally different from operations such as:

```text
repeat()
tile()
resize()
append()
```

which can change the number of stored elements.

## Dimension Expansion and Views

Dimension expansion can normally be represented without copying the underlying data.

```python
import numpy as np

values = np.arange(6)

expanded = np.expand_dims(
    values,
    axis=0,
)

print(np.shares_memory(values, expanded))
# True
```

Similarly:

```python
column = values[:, None]

print(np.shares_memory(values, column))
# True
```

This is why dimension expansion is generally cheap.

However, later operations may still allocate new output arrays.

The correct mental model is:

```text
expand dimension
→ usually metadata / stride change
→ little additional raw storage
```

not:

```text
expand dimension
→ duplicate data
```

## Dimension Expansion vs Copying

If independent storage is required, copy explicitly:

```python
expanded = np.expand_dims(
    values,
    axis=0,
).copy()
```

This is rarely necessary merely to add a dimension.

For production numerical pipelines, avoid copying solely because the array has gained an axis.

## Broadcasting with `np.newaxis`

One of the most common uses of dimension expansion is aligning arrays for broadcasting.

Suppose:

```python
import numpy as np

values = np.array(
    [
        [10.0, 20.0, 30.0],
        [40.0, 50.0, 60.0],
    ]
)

row_scale = np.array(
    [1.0, 2.0],
)
```

The intended operation is one scale per row.

Use:

```python
result = values * row_scale[:, None]
```

Shapes:

```text
values    → (2, 3)
row_scale → (2, 1)
```

Broadcasting produces:

```text
(2, 3)
```

with:

```text
row 1 × 1.0
row 2 × 2.0
```

## Column-Oriented Broadcasting

For one parameter per feature:

```python
feature_scale = np.array(
    [1.0, 2.0, 3.0],
)

result = values * feature_scale
```

No dimension expansion is needed because:

```text
values        → (2, 3)
feature_scale → (3,)
```

already aligns with the last dimension.

This gives an important engineering rule:

```text
Vector shape = (features,)
→ naturally broadcasts across records

Vector shape = (records,)
→ often needs [:, None] to broadcast across features
```

## Shape Transformation Example

Suppose:

```text
data:
(batch, feature)
→ (1000, 8)

per-batch parameter:
(batch,)
→ (1000,)
```

To apply one parameter across all eight features:

```python
parameters = parameters[:, None]
```

Now:

```text
data       → (1000, 8)
parameters → (1000, 1)
```

and:

```python
result = data * parameters
```

works through broadcasting.

Without dimension expansion:

```python
data * parameters
```

fails because:

```text
(1000, 8)
(1000,)
```

does not align from the right.

## `expand_dims()` with Higher Dimensions

Dimension expansion becomes more useful as arrays become multidimensional.

Consider:

```text
data.shape = (batch, timestamp, metric)
```

For example:

```python
import numpy as np

data = np.empty(
    (32, 1440, 8),
    dtype=np.float32,
)
```

Suppose each batch needs one scale:

```python
batch_scale = np.ones(
    32,
    dtype=np.float32,
)
```

Expand it:

```python
batch_scale = np.expand_dims(
    batch_scale,
    axis=(1, 2),
)
```

The shape becomes:

```text
(32, 1, 1)
```

Now:

```python
scaled = data * batch_scale
```

broadcasts the batch-specific scale across:

```text
timestamp
metric
```

dimensions.

## Multiple Axes with `expand_dims()`

`np.expand_dims()` can insert multiple axes.

```python
import numpy as np

values = np.array([1, 2, 3])

expanded = np.expand_dims(
    values,
    axis=(0, 2),
)

print(expanded.shape)
# (1, 3, 1)
```

This can make complex broadcasting contracts explicit.

Use multiple-axis expansion selectively. When the resulting shape becomes difficult to read, a sequence of clear operations may be easier to maintain.

## `reshape()` vs `expand_dims()`

These can often produce the same result:

```python
expanded = np.expand_dims(
    values,
    axis=1,
)
```

and:

```python
expanded = values.reshape(
    -1,
    1,
)
```

The difference is primarily semantic clarity.

Use `expand_dims()` when the intent is:

```text
insert a dimension here
```

Use `reshape()` when the operation is:

```text
transform this array to this exact shape
```

Both should preserve the same element count.

## Dimension Expansion vs Transpose

Dimension expansion adds a new size-one axis.

Transpose reorders existing axes.

For example:

```python
values.shape
# (3,)
```

Dimension expansion:

```python
values[:, None].shape
# (3, 1)
```

Transpose of a one-dimensional array:

```python
values.T.shape
# (3,)
```

A one-dimensional array has only one axis, so `.T` does not turn it into a column vector.

This is a common source of confusion.

If the goal is:

```text
(3,)
→ (3, 1)
```

use:

```python
values[:, None]
```

or:

```python
np.expand_dims(values, axis=1)
```

## Dimension Expansion vs Reshape

The operations are closely related.

```python
values.reshape(1, 3)
```

and:

```python
np.expand_dims(values, axis=0)
```

can both produce:

```text
(1, 3)
```

But dimension expansion communicates that an existing logical axis structure is being augmented by a singleton axis.

This can make broadcasting-oriented code easier to understand:

```python
row = np.expand_dims(
    values,
    axis=0,
)
```

versus:

```python
row = values.reshape(1, -1)
```

Both are valid; choose the one that best communicates intent.

## Dimension Expansion and Reduction

Reductions often remove dimensions.

For example:

```python
import numpy as np

values = np.empty(
    (1000, 8),
)

mean = values.mean(
    axis=0,
)

print(mean.shape)
# (8,)
```

If the mean should preserve its feature-axis position:

```python
mean = values.mean(
    axis=0,
    keepdims=True,
)

print(mean.shape)
# (1, 8)
```

Dimension expansion can then restore a desired singleton dimension if needed:

```python
mean = np.expand_dims(
    values.mean(axis=0),
    axis=0,
)
```

In practice, `keepdims=True` is usually clearer when the dimension should never have been removed.

## `keepdims` vs Explicit Expansion

Compare:

```python
mean = values.mean(
    axis=0,
    keepdims=True,
)
```

with:

```python
mean = np.expand_dims(
    values.mean(axis=0),
    axis=0,
)
```

Both produce:

```text
(1, features)
```

But `keepdims=True` expresses the intention at the reduction site:

```text
reduce this axis but preserve its position
```

Prefer `keepdims=True` when possible for reduction-driven broadcasting.

Use `expand_dims()` when starting from an already existing array whose shape needs to be adjusted independently.

## Dimension Expansion and Boolean Masks

Dimension expansion can also control how masks broadcast.

Suppose:

```python
import numpy as np

values = np.array(
    [
        [10, 20],
        [30, 40],
        [50, 60],
    ]
)

valid_rows = np.array(
    [True, False, True],
)
```

To apply the row mask while preserving column structure:

```python
filtered = values[valid_rows]
```

No dimension expansion is needed because boolean indexing has row-selection semantics.

However, for arithmetic or conditional operations, a row mask may need explicit expansion:

```python
row_mask = valid_rows[:, None]
```

Now:

```text
(3, 1)
```

can broadcast against:

```text
(3, 2)
```

For example:

```python
result = np.where(
    row_mask,
    values,
    0,
)
```

## Dimension Expansion with `where()`

A row-level condition can be applied to every feature:

```python
import numpy as np

values = np.array(
    [
        [10.0, 20.0],
        [30.0, 40.0],
        [50.0, 60.0],
    ]
)

valid_rows = np.array(
    [True, False, True],
)

result = np.where(
    valid_rows[:, None],
    values,
    np.nan,
)
```

Here:

```text
valid_rows[:, None] → (3, 1)
values              → (3, 2)
result              → (3, 2)
```

This is a clean pattern for row-level conditional processing.

## Dimension Expansion and Per-Record Parameters

A common backend numerical pattern is one parameter per record.

```python
import numpy as np


def apply_record_factor(
    records: np.ndarray,
    factors: np.ndarray,
) -> np.ndarray:
    if records.ndim != 2:
        raise ValueError(
            "records must have shape (batch, features)"
        )

    if factors.shape != (records.shape[0],):
        raise ValueError(
            "factors must contain one value per record"
        )

    return records * factors[:, None]
```

The shape contract is:

```text
records → (batch, features)
factors → (batch,)
factors[:, None] → (batch, 1)
result → (batch, features)
```

This avoids explicit repetition of each factor across all features.

## Dimension Expansion and Per-Feature Parameters

For one parameter per feature:

```python
import numpy as np


def apply_feature_factor(
    records: np.ndarray,
    factors: np.ndarray,
) -> np.ndarray:
    if records.ndim != 2:
        raise ValueError(
            "records must have shape (batch, features)"
        )

    if factors.shape != (records.shape[1],):
        raise ValueError(
            "factors must contain one value per feature"
        )

    return records * factors
```

No singleton dimension is required because:

```text
(batch, features)
+
(features,)
```

already broadcasts correctly.

Understanding this distinction prevents unnecessary reshaping.

## Dimension Expansion and Time-Series Data

Consider:

```text
data.shape = (batch, timestamp, feature)
```

A per-feature parameter:

```text
(feature,)
```

can broadcast directly:

```python
result = data * feature_scale
```

A per-timestamp parameter:

```text
(timestamp,)
```

needs its dimensions aligned:

```python
result = data * timestamp_scale[None, :, None]
```

A per-batch parameter:

```text
(batch,)
```

needs:

```python
result = data * batch_scale[:, None, None]
```

This gives a practical pattern:

```text
Parameter meaning
       ↓
Identify target axis
       ↓
Insert singleton dimensions
       ↓
Broadcast
```

## Dimension Expansion as Axis Alignment

A useful way to reason about the operation is:

```text
Original:
(batch,)

Need:
(batch, features)

Missing dimension:
features

Insert:
(batch, 1)

Broadcast:
(batch, features)
```

This is more precise than saying "reshape it until the multiplication works."

Senior-level code should make the intended axis alignment obvious.

## Backend Example: Validation Thresholds

Suppose each metric has lower and upper bounds:

```python
import numpy as np

records = np.array(
    [
        [10.0, 20.0, 30.0],
        [12.0, 18.0, 31.0],
    ]
)

minimum = np.array(
    [8.0, 15.0, 25.0],
)

maximum = np.array(
    [15.0, 25.0, 35.0],
)
```

These naturally broadcast:

```python
valid = (
    (records >= minimum)
    & (records <= maximum)
)
```

No dimension expansion is needed because the parameters are feature-oriented.

Now suppose every **row** has a different multiplier:

```python
multipliers = np.array(
    [1.0, 1.5],
)
```

Expand:

```python
scaled = records * multipliers[:, None]
```

This is a practical example of selecting dimension expansion based on semantic orientation.

## Backend Example: Batch Processing

For a batch-oriented service:

```text
batch
→ (records, features)
```

Suppose the worker receives a per-record penalty:

```text
penalty
→ (records,)
```

The processing pipeline can remain vectorized:

```python
adjusted = records - penalty[:, None]
```

No Python loop is required.

The shape contract is:

```text
records → (records, features)
penalty → (records, 1)
```

This pattern is suitable for FastAPI request processing, Celery batch jobs, Kafka consumer windows, and file-based ETL stages.

## Large Dataset Memory Behavior

Dimension expansion itself typically does not duplicate the source data.

```python
expanded = values[:, None]

print(expanded.nbytes)
```

The data buffer size remains tied to the number of elements:

```text
N elements × dtype.itemsize
```

not:

```text
N × expanded dimension
```

However, a subsequent operation can allocate a large output:

```python
result = expanded * large_matrix
```

Therefore:

```text
dimension expansion
→ cheap

broadcasted computation
→ may allocate output
```

Always evaluate the complete expression.

## `np.broadcast_to()` and Dimension Expansion

Sometimes an expanded array needs to be represented with a specific broadcasted shape:

```python
import numpy as np

values = np.array(
    [1, 2, 3],
)

expanded = np.expand_dims(
    values,
    axis=1,
)

broadcasted = np.broadcast_to(
    expanded,
    (3, 5),
)

print(broadcasted.shape)
# (3, 5)
```

The distinction is:

```text
expand_dims()
→ insert a size-one dimension

broadcast_to()
→ expose a broadcast-compatible shape
```

`broadcast_to()` should generally be treated as a read-only broadcasted view.

## Memory Layout Considerations

Adding a singleton dimension changes shape and strides.

```python
import numpy as np

values = np.arange(6)

expanded = values[:, None]

print(values.strides)
print(expanded.strides)
```

The underlying memory remains shared, but the new stride structure reflects the inserted axis.

For most application-level operations, this is exactly what you want.

For low-level performance-sensitive paths, inspect:

```python
expanded.flags.c_contiguous
expanded.strides
```

when the downstream operation is known to care about memory layout.

## Contiguity and Singleton Dimensions

A singleton dimension does not necessarily imply that the array is expensive or inefficient.

For example:

```python
values = np.empty(
    (1, 1_000_000),
    dtype=np.float32,
)
```

and:

```python
values = np.empty(
    (1_000_000, 1),
    dtype=np.float32,
)
```

contain the same number of elements but have different shapes and potentially different access patterns.

This distinction matters when the downstream operation interprets axes differently.

Shape design should therefore precede low-level layout optimization.

## Dimension Expansion and Pandas

Pandas generally manages row and column semantics at a higher abstraction level.

Dimension expansion becomes relevant after converting numerical data to NumPy:

```python
values = frame.to_numpy(
    dtype=np.float64,
)

row_weights = frame["weight"].to_numpy(
    dtype=np.float64,
)

result = values * row_weights[:, None]
```

Here:

```text
DataFrame
→ labeled tabular representation

NumPy
→ positional numerical representation

row_weights[:, None]
→ explicit broadcast axis
```

The conversion boundary should be intentional.

## Dimension Expansion and Python Lists

Python lists do not have NumPy-style axes.

This:

```python
values = [1, 2, 3]
```

does not have a `shape`.

After conversion:

```python
array = np.asarray(values)
```

NumPy provides:

```text
shape → (3,)
```

and dimension expansion becomes meaningful.

This is another example of NumPy serving as a numerical representation layer rather than replacing Python's general-purpose collections.

## Common Mistakes

### Using `.T` to Create a Column Vector

For:

```python
values.shape == (3,)
```

this:

```python
values.T
```

still has shape:

```text
(3,)
```

Use:

```python
values[:, None]
```

or:

```python
np.expand_dims(values, axis=1)
```

instead.

### Adding the Singleton Dimension on the Wrong Side

These are not equivalent:

```python
values[None, :]
values[:, None]
```

They produce:

```text
(1, n)
(n, 1)
```

respectively.

Choose based on which axis the data should align with.

### Expanding Dimensions Without Understanding the Data

A shape-compatible result can still be semantically wrong.

Always document what each dimension represents.

### Using `repeat()` Instead of `newaxis`

If the goal is only broadcasting:

```python
values[:, None]
```

is usually preferable to physically repeating the values.

### Using `reshape()` Just to Make Broadcasting Work

`reshape()` is valid, but `None` or `np.newaxis` can make axis insertion more obvious:

```python
weights[:, None]
```

### Forgetting `keepdims`

If an aggregation is immediately followed by broadcasting, preserving dimensions during the reduction can be cleaner:

```python
mean = values.mean(
    axis=0,
    keepdims=True,
)
```

### Creating Large Broadcasted Copies

Broadcasting itself does not require a materialized repeated input, but functions such as `np.broadcast_to()` should not be confused with allocating an independent expanded array.

### Ignoring Result Allocation

A zero-copy dimension expansion can still feed an operation that allocates a very large result.

Monitor the entire expression, not just the reshape step.

## Performance Considerations

Dimension expansion is generally inexpensive because it does not increase the number of stored elements.

A conceptual cost model is:

```text
expand_dims()
→ metadata / stride adjustment
→ approximately O(1) setup
```

By comparison:

```text
repeat()
tile()
→ materialize additional elements
→ O(output size)
```

This is why dimension expansion is a preferred tool for preparing arrays for broadcasting.

However, the downstream computation determines end-to-end cost.

## Benchmarking

A useful comparison is between broadcasting and explicit repetition.

```python
from time import perf_counter
import numpy as np

records = np.random.default_rng(42).random(
    (1_000_000, 8),
    dtype=np.float32,
)

weights = np.random.default_rng(7).random(
    1_000_000,
    dtype=np.float32,
)

start = perf_counter()

result = records * weights[:, None]

broadcast_time = perf_counter() - start

print(f"broadcasted operation: {broadcast_time:.6f}s")
print(f"result bytes: {result.nbytes}")
```

An explicit repetition approach would create a much larger intermediate:

```python
start = perf_counter()

expanded = np.repeat(
    weights[:, None],
    records.shape[1],
    axis=1,
)

result = records * expanded

repeat_time = perf_counter() - start

print(f"repeated operation: {repeat_time:.6f}s")
print(f"expanded bytes: {expanded.nbytes}")
print(f"result bytes: {result.nbytes}")
```

The important comparison is not only runtime but also:

```text
input allocation
+
temporary allocation
+
output allocation
+
peak memory
```

## Production Design Pattern

A robust numerical pipeline treats dimension expansion as a shape-alignment tool:

```mermaid
flowchart LR
    A["Validated ndarray"] --> B["Define axis semantics"]
    B --> C["Insert singleton dimension"]
    C --> D["Broadcast"]
    D --> E["Vectorized computation"]
    E --> F["Persist / aggregate"]
```

The design sequence is:

```text
Understand the data dimensions
        ↓
Identify the target axis
        ↓
Add size-one dimension if required
        ↓
Broadcast
        ↓
Perform vectorized operation
```

This is preferable to trial-and-error reshaping.

## Testing Dimension Expansion

Test both shape and memory behavior when relevant.

```python
import numpy as np


def test_expand_dims_row():
    values = np.array([1, 2, 3])

    result = np.expand_dims(
        values,
        axis=0,
    )

    assert result.shape == (1, 3)

    np.testing.assert_array_equal(
        result,
        np.array([[1, 2, 3]]),
    )


def test_expand_dims_column():
    values = np.array([1, 2, 3])

    result = values[:, None]

    assert result.shape == (3, 1)

    np.testing.assert_array_equal(
        result,
        np.array(
            [
                [1],
                [2],
                [3],
            ]
        ),
    )
```

Test broadcasting:

```python
def test_row_parameter_broadcasts():
    values = np.array(
        [
            [10.0, 20.0],
            [30.0, 40.0],
        ]
    )

    factors = np.array([1.0, 2.0])

    result = values * factors[:, None]

    np.testing.assert_allclose(
        result,
        np.array(
            [
                [10.0, 20.0],
                [60.0, 80.0],
            ]
        ),
    )
```

For production numerical code, test:

- Expected dimensions.
- Axis placement.
- Output shape.
- Broadcasting behavior.
- Dtype preservation.
- Large input sizes.
- Non-finite values where relevant.
- Memory-sensitive operations.

## Debugging Dimension Expansion

When broadcasting does not behave as expected, inspect:

```python
print("values shape:", values.shape)
print("values ndim:", values.ndim)
print("values dtype:", values.dtype)
print("values strides:", values.strides)
```

Then inspect the transformed array:

```python
expanded = values[:, None]

print("expanded shape:", expanded.shape)
print("expanded strides:", expanded.strides)
print(
    "shares memory:",
    np.shares_memory(values, expanded),
)
```

A useful debugging sequence is:

```text
Identify semantic axes
        ↓
Write current shape
        ↓
Write desired shape
        ↓
Insert singleton axis
        ↓
Check broadcast compatibility
        ↓
Check output shape
        ↓
Inspect memory only if performance requires it
```

For example:

```text
Current:
(batch,)

Required:
(batch, features)

Expansion:
(batch, 1)

Broadcast:
(batch, features)
```

## Interview Questions

### What is dimension expansion?

It adds one or more size-one dimensions to an array without changing its element count.

### What is the difference between `np.expand_dims()` and `np.newaxis`?

Both insert singleton dimensions. `expand_dims()` is an explicit function call, while `np.newaxis` is an indexing syntax.

### What is the difference between `x[:, None]` and `x[None, :]`?

They add the new axis at different positions:

```text
x[:, None] → (n, 1)
x[None, :] → (1, n)
```

### Why is dimension expansion useful for broadcasting?

It inserts size-one dimensions where needed so that NumPy's broadcasting rules can align arrays along the intended axes.

### Does `expand_dims()` copy data?

It generally returns a view that shares the original data buffer.

### How is dimension expansion different from `repeat()`?

Dimension expansion changes shape without increasing the number of stored elements. `repeat()` creates additional elements and therefore materializes more data.

### Why does `x.T` not create a column vector for a one-dimensional array?

A one-dimensional array has only one axis. Transpose can reorder existing axes but cannot create a new one.

### When should `keepdims=True` be used instead of `expand_dims()`?

When a reduction should preserve the reduced axis as a size-one dimension, `keepdims=True` expresses that intent directly at the reduction operation.

### How would you apply one value per row to a matrix?

For a matrix of shape `(rows, features)` and a vector of shape `(rows,)`, use:

```python
matrix * values[:, None]
```

which produces a broadcastable `(rows, 1)` shape.

## Key Takeaways

- Dimension expansion adds size-one axes without increasing the number of stored elements and is primarily a tool for controlling array shape.
- `np.expand_dims()`, `np.newaxis`, and `None` indexing provide equivalent ways to introduce singleton dimensions; choose the form that makes axis intent clearest.
- Dimension expansion is especially important for broadcasting because `(n,)`, `(1, n)`, and `(n, 1)` have different alignment semantics.
- Prefer dimension expansion or `keepdims=True` over `repeat()` or `tile()` when values only need to participate in a broadcasted computation.
- In production numerical code, treat shape and axis meaning as explicit contracts, validate them at function boundaries, and evaluate downstream memory allocation in addition to the cost of the dimension-expansion step.