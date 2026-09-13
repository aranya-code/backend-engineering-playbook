# 09- Record Arrays

## Overview

Record arrays are a NumPy interface for working with structured arrays through convenient attribute-style field access.

A structured array provides named fields:

```python
records["amount"]
```

A record array can expose the same fields as attributes:

```python
records.amount
```

For example:

```python
import numpy as np

records = np.rec.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
        (103, 900.00, 1),
    ],
    dtype=[
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ],
)
```

Fields can then be accessed as:

```python
records.amount
records.status
```

Record arrays are primarily a convenience layer over structured-array data. They are useful when named field access improves readability, but they should not be treated as a general replacement for Pandas DataFrames, Python models, or database-backed records.

The practical hierarchy is:

```text
regular ndarray
→ homogeneous numerical data

structured array
→ fixed-schema heterogeneous records

record array
→ structured array + attribute-style field access
```

## Structured Arrays vs Record Arrays

A record array is closely related to a structured array.

```python
import numpy as np

dtype = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ]
)

structured = np.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
    ],
    dtype=dtype,
)

records = structured.view(
    np.recarray
)
```

Both represent the same field-oriented data.

The primary difference is access syntax:

```python
structured["amount"]
```

versus:

```python
records.amount
```

This distinction is mainly about interface and convenience, not a fundamentally different storage model.

## Creating Record Arrays

A record array can be created directly:

```python
import numpy as np

records = np.rec.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
        (103, 900.00, 1),
    ],
    dtype=[
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ],
)
```

The dtype defines the schema:

```text
id      → int64
amount  → float64
status  → int8
```

Inspect it with:

```python
print(records.dtype)
print(records.dtype.names)
print(records.shape)
```

The record array remains an `ndarray` with structured dtype semantics.

## Attribute-Style Field Access

The main reason to use record arrays is convenience:

```python
ids = records.id
amounts = records.amount
statuses = records.status
```

The equivalent structured-array syntax is:

```python
ids = records["id"]
amounts = records["amount"]
statuses = records["status"]
```

Attribute access can make fixed-schema record processing more readable:

```python
completed = (
    records.status == 1
)

total = np.sum(
    records.amount,
    where=completed,
)
```

The syntax is concise, but the field name must be suitable for attribute access.

## Field Names and Attribute Access

Not every field name is equally convenient as an attribute.

A field name should be a valid Python identifier when attribute access is expected:

```python
dtype = np.dtype(
    [
        ("transaction_id", np.int64),
        ("amount", np.float64),
    ]
)
```

Then:

```python
records.transaction_id
records.amount
```

are natural.

Field names containing spaces, punctuation, or names that collide with object attributes are better accessed through bracket notation:

```python
records["field name"]
```

For production schemas, use simple, stable field names.

## Attribute Access Is Convenience, Not Schema Magic

Record arrays do not turn field access into independent Python objects.

The underlying representation is still NumPy structured-array storage.

Therefore:

```python
records.amount
```

should be understood as field access into the structured array, not as a standalone DataFrame-like column abstraction.

This matters when reasoning about:

- Memory.
- Views.
- Mutation.
- Dtypes.
- Record layout.
- Performance.

## Accessing Fields for Vectorized Operations

Record arrays become useful when field-level numerical work is required:

```python
mean_amount = np.mean(
    records.amount
)

max_amount = np.max(
    records.amount
)

successful_count = np.count_nonzero(
    records.status == 1
)
```

The record container provides organization while NumPy operations still operate on homogeneous field data.

A common pattern is:

```text
record array
    ↓
field access
    ↓
NumPy vectorized operation
    ↓
aggregate / filter / transform
```

## Filtering Record Arrays

A record array can be filtered using normal boolean masking.

```python
mask = (
    (records.status == 1)
    & (records.amount >= 100.0)
)

filtered = records[
    mask
]
```

The result preserves the structured record schema.

The same pattern works for validation:

```python
valid = (
    np.isfinite(records.amount)
    & (records.amount >= 0.0)
)

cleaned = records[
    valid
]
```

The filtering operation is familiar NumPy masking; the main difference is that the conditions originate from named fields.

## Updating Record Fields

Fields can be modified through attribute access:

```python
records.amount *= 1.05
```

or:

```python
records.status[
    records.status == 0
] = 2
```

This mutates the underlying record array.

As with other NumPy views and field accesses, mutation should only be used when ownership is clear.

If the input must remain unchanged:

```python
cleaned = records.copy()

cleaned.amount *= 1.05
```

## Record Arrays and Views

Structured-field access can expose existing array storage rather than creating a fully independent copy.

For example:

```python
amounts = records.amount
```

The returned field data can be associated with the original structured array's memory.

Therefore:

```python
amounts *= 1.05
```

can modify:

```python
records.amount
```

This is useful for memory-efficient in-place processing but can produce unexpected changes when arrays are shared.

Use explicit copies when mutation isolation matters.

## Record Arrays and Boolean Indexing

Filtering:

```python
filtered = records[
    records.amount > 100
]
```

generally creates a new array.

This means a large filtering operation can temporarily require:

```text
original records
+
boolean mask
+
filtered records
```

The same memory considerations discussed for structured arrays and boolean indexing still apply.

For aggregation-only workloads, avoid materializing a filtered record array unnecessarily.

For example:

```python
total = np.sum(
    records.amount,
    where=records.amount > 100,
)
```

can express the aggregation directly.

## Record Array Attributes vs `__getitem__`

Although attribute access is convenient:

```python
records.amount
```

bracket notation remains more explicit:

```python
records["amount"]
```

Bracket notation is often preferable when:

- Field names are dynamic.
- Field names are not valid Python identifiers.
- Code is generic.
- Static analyzers or APIs expect dictionary-like access.
- The schema is generated programmatically.

For example:

```python
field_name = "amount"

values = records[field_name]
```

This cannot be expressed naturally with:

```python
records.field_name
```

because that accesses the literal attribute `field_name`.

## Dynamic Field Processing

For generic processing pipelines:

```python
numeric_fields = [
    "amount",
    "tax",
    "discount",
]

for field_name in numeric_fields:
    values = records[field_name]

    print(
        field_name,
        np.mean(values),
    )
```

Bracket access is therefore more flexible than attribute access for schema-driven systems.

Record arrays are convenient for known schemas, but dynamic pipelines should usually use explicit field indexing.

## `np.recarray`

`np.recarray` is the NumPy array subclass associated with record-array behavior.

For example:

```python
import numpy as np

records = np.recarray(
    3,
    dtype=[
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ],
)
```

Values can then be assigned:

```python
records.id = [101, 102, 103]
records.amount = [250.50, 125.75, 900.00]
records.status = [1, 0, 1]
```

This provides convenient attribute-based access to structured fields.

For most production code, create record arrays through clear construction methods or views rather than relying heavily on subclass-specific behavior.

## `np.rec.array()`

`np.rec.array()` is a convenient constructor for creating or viewing record-style arrays.

Example:

```python
records = np.rec.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
    ],
    dtype=[
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ],
)
```

This is useful when the record-array interface itself is desired.

The resulting object still follows the structured-array data model.

## `np.rec.fromrecords()`

`np.rec.fromrecords()` can construct a record array from a sequence of records.

```python
records = np.rec.fromrecords(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
        (103, 900.00, 1),
    ],
    names=[
        "id",
        "amount",
        "status",
    ],
)
```

The field names become:

```text
id
amount
status
```

and can be accessed through:

```python
records.id
records.amount
records.status
```

This can be convenient for ingesting already-record-oriented data.

## `np.rec.fromarrays()`

`np.rec.fromarrays()` is useful when the data is already separated into field arrays.

```python
ids = np.array(
    [101, 102, 103],
    dtype=np.int64,
)

amounts = np.array(
    [250.50, 125.75, 900.00],
    dtype=np.float64,
)

statuses = np.array(
    [1, 0, 1],
    dtype=np.int8,
)

records = np.rec.fromarrays(
    [
        ids,
        amounts,
        statuses,
    ],
    names=[
        "id",
        "amount",
        "status",
    ],
)
```

This is conceptually:

```text
separate arrays
      ↓
record representation
```

The input arrays must represent corresponding records consistently.

## Record Arrays and Shape

Record arrays can have more than one dimension.

For example:

```python
records = np.rec.array(
    [
        [
            (101, 100.0),
            (102, 200.0),
        ],
        [
            (103, 300.0),
            (104, 400.0),
        ],
    ],
    dtype=[
        ("id", np.int64),
        ("amount", np.float64),
    ],
)
```

The array shape is:

```text
(2, 2)
```

while each element is still one structured record.

Field access preserves the array's shape:

```python
records.amount.shape
# (2, 2)
```

This is useful for regular multidimensional record grids, though most backend datasets are naturally one-dimensional collections of records.

## Record Arrays vs Structured Arrays

| Capability | Structured Array | Record Array |
|---|---|---|
| Named fields | Yes | Yes |
| Field access with `[]` | Yes | Yes |
| Attribute-style fields | No | Yes |
| Structured dtype | Yes | Yes |
| Vectorized operations | Yes | Yes |
| Fixed record layout | Yes | Yes |
| Memory model | NumPy | NumPy |
| Best use | General structured storage | Convenience-oriented field access |

A record array should generally be viewed as:

```text
structured array
+
record-array interface
```

rather than as a separate numerical storage model.

## Record Arrays vs Pandas DataFrames

A DataFrame provides substantially higher-level tabular capabilities.

| Requirement | Record Array | Pandas DataFrame |
|---|---|---|
| Fixed typed fields | Strong | Strong |
| Attribute-like columns | Available | Available, with caveats |
| Rich joins | Limited | Strong |
| Grouping | Limited | Strong |
| Missing-data workflows | Low-level | Strong |
| Indexing semantics | NumPy | Rich labeled indexing |
| Binary record layout | Strong | Not primary purpose |
| General ETL | Limited | Strong |
| Compact fixed-width records | Strong | Depends on dtypes/representation |

Use a record array when:

```text
fixed schema
+
NumPy-oriented processing
+
record-style access
```

are the main requirements.

Use Pandas when:

```text
tabular ETL
+
labels
+
joins
+
grouping
+
mixed data processing
```

dominate.

## Record Arrays vs Dataclasses

Python dataclasses are often a better representation for application-domain entities:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Transaction:
    id: int
    amount: float
    status: int
```

Dataclasses are useful when:

- Business logic operates on individual objects.
- Validation is object-oriented.
- Methods and invariants belong to the model.
- Data volume is relatively small.

Record arrays are more appropriate when:

```text
many records
+
vectorized processing
+
compact array storage
```

are central to the workload.

A record array should not replace a domain model simply because both provide named fields.

## Backend Data-Processing Example

Suppose a batch contains transaction records:

```python
import numpy as np

transactions = np.rec.array(
    [
        (1001, 250.50, 1),
        (1002, -10.00, 0),
        (1003, 800.00, 1),
        (1004, np.nan, 1),
    ],
    dtype=[
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ],
)
```

Build a validity mask:

```python
valid = (
    np.isfinite(
        transactions.amount
    )
    & (
        transactions.amount
        >= 0.0
    )
)
```

Filter successful records:

```python
successful = (
    valid
    & (
        transactions.status
        == 1
    )
)
```

Compute an aggregate without creating a filtered record array:

```python
successful_total = np.sum(
    transactions.amount,
    where=successful,
)

successful_count = np.count_nonzero(
    successful
)
```

This pattern is useful when the workload is a fixed-schema numerical batch.

## Batch Processing

For large record arrays:

```python
batch_size = 500_000

for start in range(
    0,
    transactions.shape[0],
    batch_size,
):
    batch = transactions[
        start:start + batch_size
    ]

    valid = (
        np.isfinite(batch.amount)
        & (batch.amount >= 0.0)
    )

    total = np.sum(
        batch.amount,
        where=valid,
    )

    # Persist or emit the batch result.
```

This keeps temporary validation state bounded by the batch.

For high-volume workloads, this is generally preferable to constructing additional full-dataset copies.

## Record Arrays and Memory Mapping

Record arrays can represent large fixed-layout binary datasets through memory mapping:

```python
import numpy as np

dtype = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ]
)

records = np.memmap(
    "transactions.dat",
    dtype=dtype,
    mode="r",
    shape=(10_000_000,),
).view(np.recarray)
```

Now:

```python
records.amount
```

provides field-style access to the mapped data.

This can be useful for:

- Large binary datasets.
- Append/read pipelines with fixed schema.
- Offline numerical processing.
- Memory-constrained workers.

Memory mapping still depends on disk performance and operating-system page caching.

## Performance Considerations

Record arrays provide a convenient field-oriented interface, but attribute access itself is not the main source of performance.

For large numerical workloads, the important factors remain:

```text
Python overhead
+
vectorized operations
+
memory layout
+
dtype size
+
temporary allocations
+
cache behavior
+
data movement
```

A record array does not automatically make computation faster than every alternative.

For example:

```python
records.amount * 1.05
```

still performs numerical work over the field data.

The correct benchmark compares the complete workload, not whether:

```python
records.amount
```

looks shorter than:

```python
records["amount"]
```

## When Separate Arrays Are Better

Suppose the application repeatedly processes only:

```text
amount
```

and rarely uses:

```text
id
status
```

A dedicated homogeneous array can be simpler:

```python
amounts = np.array(
    [250.50, 125.75, 900.00],
    dtype=np.float64,
)
```

The application can keep other fields separately:

```python
ids = ...
statuses = ...
```

This is essentially a record-of-arrays design.

It can improve field-oriented numerical processing because each array is homogeneous and directly suited to vectorized operations.

The correct representation depends on access patterns rather than on the number of fields alone.

## Dtype and Memory Size

Record fields can use intentionally small dtypes:

```python
dtype = np.dtype(
    [
        ("id", np.uint64),
        ("status", np.uint8),
        ("priority", np.uint8),
        ("amount", np.float64),
    ]
)
```

Inspect:

```python
print(dtype.itemsize)
```

and:

```python
print(records.nbytes)
```

This helps estimate the raw array-storage cost.

Remember:

```text
nbytes
→ NumPy array data buffer

process RSS
→ entire process memory
```

Python objects, imported libraries, input buffers, temporary arrays, and other allocations are not included in `nbytes`.

## Schema Evolution

Record arrays are most useful when the schema is stable.

If the schema changes:

```text
v1:
id
amount
status

v2:
id
amount
currency
status
```

the dtype changes as well.

For long-lived files or distributed pipelines, include a schema version outside or alongside the raw record data.

For example:

```text
header
→ schema_version
→ record_count
→ dtype definition
→ records
```

This makes migrations explicit.

## Unknown and Invalid Data

Record arrays do not provide automatic validation for field values.

For example:

```python
records.amount = np.array(
    [100.0, -5.0, np.inf]
)
```

is structurally valid even though the values may violate the business contract.

Validation must remain explicit:

```python
valid = (
    np.isfinite(records.amount)
    & (records.amount >= 0.0)
)
```

This separation is useful:

```text
schema validation
+
value validation
```

A correct dtype does not imply correct data.

## Security Considerations

When loading record arrays from external binary files, validate:

- File size.
- Record count.
- Expected dtype.
- Field offsets.
- Alignment.
- Byte order.
- Schema version.
- Numerical ranges.

A malformed file can otherwise produce incorrect field interpretation or excessive resource usage.

For service boundaries, do not let an untrusted client select arbitrary NumPy dtypes or record sizes without strict validation.

## Operational Considerations

Record arrays are most appropriate when the operational environment benefits from a stable physical representation.

Examples include:

```text
binary ingestion
+
memory-mapped datasets
+
offline batch workers
+
fixed-width telemetry
+
legacy numerical formats
```

For normal REST or Django application state, structured domain models and database tables are usually easier to maintain.

Use record arrays where their fixed-layout and NumPy-oriented characteristics solve a real problem.

## Common Mistakes

### Treating Record Arrays as DataFrames

Record arrays provide fields and vectorized operations, but they do not provide the broader labeled-table semantics of Pandas.

### Assuming Attribute Access Changes Performance

`records.amount` is primarily a convenience interface. It should not be considered a performance optimization by itself.

### Using Dynamic Field Names with Attribute Access

For dynamic schemas:

```python
records[field_name]
```

is the correct access pattern.

### Mutating Fields Without Understanding Aliasing

Field access can reference underlying record storage, so in-place updates can modify the original array.

### Filtering Large Datasets Without Considering Copies

Boolean filtering generally creates a new array and can increase peak memory.

### Using Record Arrays for Highly Dynamic Schemas

They work best when the field schema is fixed and known.

### Converting Every Record to Python Objects

Doing so can eliminate the memory and vectorization advantages of array-based processing.

### Ignoring Binary Layout

Field order, padding, alignment, and byte order matter when interacting with external binary formats.

### Using Record Arrays When Separate Arrays Are Simpler

A field-oriented numerical workload may be easier to model as independent homogeneous arrays.

## Testing

Test both data values and the record-array interface.

```python
import numpy as np


def build_records() -> np.recarray:
    return np.rec.array(
        [
            (101, 250.50, 1),
            (102, 125.75, 0),
        ],
        dtype=[
            ("id", np.int64),
            ("amount", np.float64),
            ("status", np.int8),
        ],
    )


def test_record_array():
    records = build_records()

    assert isinstance(
        records,
        np.recarray,
    )

    assert records.shape == (2,)

    np.testing.assert_array_equal(
        records.id,
        np.array(
            [101, 102],
            dtype=np.int64,
        ),
    )

    np.testing.assert_allclose(
        records.amount,
        np.array(
            [250.50, 125.75],
            dtype=np.float64,
        ),
    )
```

Also test:

- Field names.
- Field dtypes.
- Attribute access.
- Bracket access.
- Filtering.
- Mutation.
- Copy behavior.
- Empty arrays.
- Batch processing.
- Schema versions.
- Binary compatibility.
- Memory-mapped files.

## Debugging

When a record-array operation behaves unexpectedly, inspect both the interface and the underlying dtype:

```python
print(
    type(records)
)

print(
    records.dtype
)

print(
    records.dtype.names
)

print(
    records.shape
)

print(
    records.dtype.itemsize
)
```

Compare attribute and bracket access:

```python
np.testing.assert_array_equal(
    records.amount,
    records["amount"],
)
```

For data corruption or binary parsing issues, inspect:

```text
dtype
+
field offsets
+
itemsize
+
byte order
+
schema version
```

This often reveals representation errors before numerical logic needs investigation.

## Interview Questions

### What is a record array?

A record array is a NumPy record-oriented interface over structured array data that provides named fields through attribute-style access.

### How is `records.amount` different from `records["amount"]`?

Both access the same named field conceptually. Attribute access is a convenience provided by the record-array interface, while bracket access is the more general structured-array field syntax.

### Is a record array a completely different data structure from a structured array?

No. A record array uses structured-array data and provides record-array behavior, particularly convenient attribute-style field access.

### When should record arrays be used?

For fixed-schema record-oriented data where NumPy processing, compact storage, memory mapping, or binary interoperability are important.

### Why are record arrays not a general replacement for Pandas?

They provide much lower-level functionality and do not offer the same labeled indexing, joins, grouping, and broad tabular-processing features.

### Can you perform vectorized operations on record-array fields?

Yes:

```python
records.amount * 1.05
```

and:

```python
np.mean(records.amount)
```

operate through normal NumPy semantics.

### Can record-array field access mutate the source?

Yes. Field access can reference the underlying structured storage, so in-place mutation can modify the original record array.

### When might separate homogeneous arrays be better?

When the workload repeatedly processes individual fields and benefits from simple homogeneous numerical arrays and their memory-access characteristics.

### What should you inspect when a record array does not match an external binary format?

Inspect field order, dtype, itemsize, offsets, alignment, byte order, and schema version.

### Does attribute access make record arrays faster?

No. Attribute access primarily improves readability and convenience. Performance should be evaluated based on the actual numerical and memory-processing workload.

## Key Takeaways

- Record arrays provide attribute-style access to structured-array fields while retaining NumPy's fixed-schema array representation.
- They are useful for fixed-record numerical workloads, binary formats, memory-mapped data, and low-level processing where named field access improves readability.
- `records.field` is a convenience interface; `records["field"]` remains important for dynamic schemas and explicit field handling.
- Record arrays inherit structured-array memory, dtype, view, mutation, filtering, and binary-layout considerations.
- Choose record arrays only when their fixed-layout and NumPy-oriented behavior provides a clear advantage over homogeneous ndarrays, Pandas, dataclasses, or separate field arrays.