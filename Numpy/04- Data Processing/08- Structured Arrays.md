# 08- Structured Arrays

## Overview

NumPy structured arrays provide a way to store heterogeneous records inside a single `ndarray`, where each record contains named fields with explicitly defined dtypes.

A conventional NumPy array is typically homogeneous:

```python
import numpy as np

values = np.array(
    [10, 20, 30],
    dtype=np.int32,
)
```

Every element has the same dtype.

A structured array can instead represent records such as:

```text
id       int64
amount   float64
status   int8
```

inside one array.

```python
import numpy as np

dtype = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ]
)

records = np.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
        (103, 900.00, 2),
    ],
    dtype=dtype,
)
```

This is useful when a dataset is naturally record-oriented but still benefits from NumPy's compact fixed-width representation and array operations.

Structured arrays are most appropriate for:

- Fixed-schema numerical records.
- File-based binary or memory-mapped data.
- Interoperating with systems that expose C-like records.
- Low-level data-processing pipelines.
- Compact in-memory representations.
- Explicit field-level dtypes.

They are usually not the best abstraction for general-purpose tabular ETL. Pandas, database tables, or typed application models are often better for complex relational workflows.

## Structured Array Data Model

A structured array has:

```text
array shape
+
record dtype
+
named fields
```

For example:

```python
dtype = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ]
)
```

The dtype describes one complete record.

Then:

```python
records.shape
```

might be:

```text
(3,)
```

while:

```python
records.dtype
```

describes:

```text
id      → int64
amount  → float64
status  → int8
```

Conceptually:

```text
records
├── record 0
│   ├── id
│   ├── amount
│   └── status
├── record 1
│   ├── id
│   ├── amount
│   └── status
└── record 2
    ├── id
    ├── amount
    └── status
```

## Why Structured Arrays Exist

Ordinary NumPy arrays work best when elements have a shared dtype.

Real backend datasets often contain records with multiple field types:

```text
transaction_id → integer
amount         → float
status         → integer
```

A Python list of tuples can represent this naturally:

```python
records = [
    (101, 250.50, 1),
    (102, 125.75, 0),
]
```

But Python tuples and objects carry significantly more interpreter-level overhead than compact fixed-width NumPy storage.

Structured arrays provide a middle ground:

```text
heterogeneous fields
+
fixed schema
+
NumPy memory model
```

## Creating a Structured Dtype

The most common form is a list of field definitions:

```python
import numpy as np

dtype = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ]
)
```

Each tuple contains:

```text
field name
field dtype
```

You can inspect the structure:

```python
print(dtype.names)
# ('id', 'amount', 'status')
```

and:

```python
print(dtype.fields)
```

which exposes field metadata.

The dtype is part of the schema, so changing it can change memory layout and downstream compatibility.

## Creating Structured Arrays from Records

Once the dtype is defined:

```python
records = np.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
        (103, 900.00, 2),
    ],
    dtype=dtype,
)
```

The array now has a fixed record schema.

Individual fields can be accessed by name:

```python
ids = records["id"]
amounts = records["amount"]
statuses = records["status"]
```

The result is field-level NumPy data that can be processed independently.

## Field Access

A structured array can be treated as a collection of fields:

```python
amounts = records["amount"]
```

Then ordinary NumPy operations apply:

```python
total = np.sum(
    amounts
)

average = np.mean(
    amounts
)
```

This makes structured arrays useful when the overall dataset is record-oriented but most computation operates on one or a few fields at a time.

## Filtering Structured Records

Field-level comparisons can produce normal boolean masks:

```python
mask = (
    (records["amount"] >= 100.0)
    & (records["status"] == 1)
)
```

Then:

```python
filtered = records[
    mask
]
```

This preserves the structured dtype of the selected records.

The pattern is:

```text
structured records
→ field extraction
→ boolean condition
→ record-level mask
→ filtered structured records
```

## Record-Level Processing

Suppose:

```python
records = np.array(
    [
        (101, 250.50, 1),
        (102, 125.75, 0),
        (103, 900.00, 1),
    ],
    dtype=dtype,
)
```

Filter successful transactions above a threshold:

```python
mask = (
    (records["amount"] >= 200.0)
    & (records["status"] == 1)
)

selected = records[
    mask
]
```

The result contains complete records rather than isolated field values.

This makes structured arrays useful for fixed-schema record filtering.

## Updating Fields

Fields can be modified directly:

```python
records["amount"] *= 1.02
```

This updates the corresponding field for every record.

Conditional updates are also possible:

```python
mask = records["status"] == 0

records["amount"][mask] = 0.0
```

Be deliberate about mutation.

As with other NumPy arrays, in-place updates are useful when ownership is clear but can produce unintended side effects when multiple views reference the same underlying storage.

## Field Assignment and Dtype

Assigning values must respect the field dtype.

For:

```python
("status", np.int8)
```

the stored values are represented using an 8-bit signed integer.

Choose field dtypes according to:

```text
range
+
precision
+
memory requirements
+
external format
```

For example:

```text
transaction ID → int64
amount         → float64
status         → uint8
```

may be reasonable for a fixed schema.

Do not automatically use `int64` or `float64` for every field if a smaller representation is sufficient.

## Record Size

The structured dtype determines the size of each record.

For example:

```python
print(records.dtype.itemsize)
```

gives the size of one complete record in bytes.

The total data-buffer size can then be inspected with:

```python
print(records.nbytes)
```

This is useful when estimating memory requirements:

```text
record size × number of records
```

Keep in mind that `nbytes` describes the array's data buffer, not total process memory or every Python object associated with the processing pipeline.

## Field Offsets and Memory Layout

Structured fields occupy defined positions within each record.

You can inspect field metadata:

```python
for name, metadata in records.dtype.fields.items():
    field_dtype, offset = metadata[:2]

    print(
        name,
        field_dtype,
        offset,
    )
```

This is particularly useful when:

- Mapping binary file formats.
- Interoperating with C-compatible layouts.
- Debugging serialization.
- Controlling record size.

The layout is part of the data representation, so changes to field order, dtype, or alignment can affect compatibility.

## Aligned Structured Dtypes

NumPy can create structured dtypes with alignment rules:

```python
dtype = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ],
    align=True,
)
```

Alignment can introduce padding between fields.

This can be useful when matching a C-like memory layout or external binary structure.

However, alignment can increase the size of each record.

Therefore:

```text
alignment
→ compatibility benefits

padding
→ potentially larger memory footprint
```

Use it when the external representation requires it rather than as a generic optimization.

## Field Names Are Schema

Field names are part of the structured dtype:

```python
dtype.names
```

might return:

```text
("id", "amount", "status")
```

These names define how application code addresses the fields.

Renaming or removing fields is therefore a schema change.

For long-lived datasets, treat the structured dtype similarly to a database or message schema:

```text
field name
+
field type
+
field order/layout when relevant
+
version
```

## Nested Structured Fields

Structured dtypes can contain nested structures.

For example:

```python
import numpy as np

dtype = np.dtype(
    [
        (
            "customer",
            [
                ("id", np.int64),
                ("tier", np.int8),
            ],
        ),
        ("amount", np.float64),
    ]
)
```

This can represent nested records.

Field access becomes hierarchical:

```python
customer_ids = records["customer"]["id"]
```

Nested structured arrays can be useful for closely related fixed-layout binary data, but they can also make processing harder to understand.

Prefer simpler schemas unless the nested representation provides a clear interoperability or storage benefit.

## Structured Arrays vs Regular ndarrays

A regular numerical array is typically preferable when:

```text
all elements share one dtype
```

For example:

```python
values = np.array(
    [
        [10.0, 20.0],
        [30.0, 40.0],
    ],
    dtype=np.float64,
)
```

A structured array is useful when:

```text
each record contains multiple typed fields
```

For example:

```python
records = np.array(
    [
        (101, 10.5, 1),
        (102, 20.5, 0),
    ],
    dtype=dtype,
)
```

Structured arrays add schema richness but generally give up some of the simplicity and uniformity of homogeneous arrays.

## Structured Arrays vs Python Lists

| Property | Structured Array | Python List of Tuples |
|---|---|---|
| Field schema | Explicit dtype | Python-level convention |
| Memory layout | Fixed-width records | Object references and Python objects |
| Numerical operations | NumPy vectorization | Python loops usually required |
| Field access | Named fields | Tuple positions |
| Dtype control | Explicit | Implicit / Python objects |
| Binary interoperability | Strong | Limited |
| General application logic | Less flexible | More flexible |

Use Python-native structures when:

- The data is small.
- The schema is highly dynamic.
- Values are heterogeneous beyond fixed numerical fields.
- General application logic dominates.

Use structured arrays when:

- The schema is fixed.
- Numeric processing is important.
- Memory layout matters.
- File or systems interoperability matters.

## Structured Arrays vs Pandas DataFrames

Pandas is usually a better fit for higher-level tabular data processing.

| Requirement | Structured Array | Pandas DataFrame |
|---|---|---|
| Fixed typed record layout | Strong | Strong |
| Named fields/columns | Yes | Yes |
| Rich tabular ETL | Limited | Strong |
| Joins and grouping | Limited | Strong |
| Missing-data workflows | Lower-level | Higher-level |
| Indexing / labels | Lower-level | Strong |
| Binary interoperability | Strong | Usually not the primary goal |
| Dense numerical processing | Strong | Strong |
| Complex business data | Less suitable | Usually preferable |

Structured arrays should not become a substitute for the Pandas curriculum.

A useful rule is:

```text
fixed low-level record representation
→ structured array

labeled tabular data processing
→ Pandas
```

## Structured Arrays and File Formats

Structured arrays are particularly useful when a file has a known fixed binary layout.

For example:

```text
record 0:
    timestamp
    sensor_id
    reading
    status

record 1:
    timestamp
    sensor_id
    reading
    status
```

The dtype can describe that exact record layout.

This is useful for:

- Binary logs.
- Fixed-width records.
- Legacy systems.
- Memory-mapped files.
- C-compatible data.
- Low-level ingestion pipelines.

For CSV, JSON, or Parquet-based business data, Pandas or dedicated file-processing tools are often more appropriate.

## Memory-Mapped Structured Arrays

Structured arrays can be used with memory mapping for large fixed-layout files:

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
)
```

Now fields can be processed without eagerly materializing the full dataset:

```python
amounts = records["amount"]

total = np.sum(
    amounts
)
```

This is useful for large file-backed numerical datasets.

Memory mapping still involves I/O and operating-system page caching. It should not be treated as a way to eliminate storage latency.

## Batch Processing Structured Arrays

For large datasets:

```python
batch_size = 500_000

for start in range(
    0,
    records.shape[0],
    batch_size,
):
    batch = records[
        start:start + batch_size
    ]

    mask = (
        (batch["status"] == 1)
        & (batch["amount"] >= 0.0)
    )

    valid_batch = batch[
        mask
    ]

    # Process or persist valid_batch.
```

This keeps working memory bounded by the selected batch size plus the filtered result.

For streaming workloads, the same pattern can be applied to batches received from Kafka or a file-processing worker.

## Converting Structured Arrays to Dictionaries

A structured array is not a replacement for normal application objects.

When data must cross into application logic, an explicit conversion may be appropriate:

```python
record = records[0]

item = {
    "id": int(record["id"]),
    "amount": float(record["amount"]),
    "status": int(record["status"]),
}
```

Avoid repeatedly converting millions of records into Python dictionaries if the workload is intended to remain vectorized.

The conversion moves the representation from:

```text
compact array memory
```

to:

```text
Python objects
```

which can increase memory and interpreter overhead substantially.

## Field-Level Vectorization

One of the main advantages of structured arrays is that fields can still be processed with NumPy operations.

```python
total = np.sum(
    records["amount"]
)

average = np.mean(
    records["amount"]
)

successful = np.count_nonzero(
    records["status"] == 1
)
```

The record container remains structured while numerical operations are applied to specific homogeneous fields.

This is often the most effective way to use structured arrays:

```text
structured container
+
homogeneous field operations
```

## Filtering and Aggregation

A realistic transaction-processing example:

```python
completed = (
    records["status"] == 1
)

valid_amount = (
    np.isfinite(
        records["amount"]
    )
    & (
        records["amount"] >= 0.0
    )
)

mask = (
    completed
    & valid_amount
)

completed_total = np.sum(
    records["amount"],
    where=mask,
)
```

This avoids creating a filtered array when only the aggregate is required.

The same mask can also count valid records:

```python
completed_count = np.count_nonzero(
    mask
)
```

This pattern is appropriate for memory-conscious batch processing.

## Structured Arrays and Views

Field access has important memory semantics.

For example:

```python
amounts = records["amount"]
```

provides field-level access to the underlying structured array.

Depending on the dtype layout and access pattern, this can expose the existing data through a view rather than creating an independent copy.

This means mutations such as:

```python
amounts *= 1.05
```

can modify the corresponding field in the structured array.

For read-only workflows this is useful and memory-efficient.

For mutation, understand ownership and aliasing before modifying fields.

## Field Access vs Copying

When converting or selecting data, determine whether a new array is being created.

For example:

```python
amounts = records["amount"]
```

is fundamentally different from:

```python
selected = records[
    records["amount"] > 100
]
```

The first accesses a field from the structured representation.

The second performs boolean selection and generally creates a new array.

This distinction matters when estimating memory usage.

## Performance Considerations

Structured arrays can be efficient for fixed-layout record storage, but they should not be assumed to outperform every alternative.

Performance depends on:

- Record size.
- Field layout.
- Access pattern.
- Whether one field or many fields are processed.
- Memory locality.
- Number of conversions to Python objects.
- Alignment and padding.
- Cache behavior.

For field-heavy numerical processing, a homogeneous NumPy array can sometimes provide simpler and better memory locality than an array-of-records layout.

This leads to an important design choice:

```text
array of records
vs
record of arrays
```

## Array of Records vs Record of Arrays

A structured array is conceptually:

```text
array of records
```

For example:

```text
[
    {id, amount, status},
    {id, amount, status},
    {id, amount, status}
]
```

A collection of homogeneous NumPy arrays is conceptually:

```text
record of arrays

ids
amounts
statuses
```

The second representation can be attractive when numerical processing is dominated by one field or when operations need to be performed independently across large homogeneous vectors.

A useful decision rule is:

| Workload | Often Prefer |
|---|---|
| Fixed-record storage / binary interoperability | Structured array |
| Process one numerical field at a time | Separate homogeneous arrays |
| Rich tabular processing | Pandas |
| General application records | Dataclasses / typed models |
| Relational persistence | PostgreSQL |

Do not choose a structured array simply because the input looks like a table.

## Contiguity and Memory Locality

Structured records store fields according to the dtype layout.

This can be advantageous when entire records are read together.

However, if the application repeatedly accesses only one field:

```python
records["amount"]
```

the interleaved record layout can have different memory-access characteristics than a dedicated homogeneous `amounts` array.

Performance should therefore be evaluated with representative workloads.

The key distinction is:

```text
compact record representation
```

versus:

```text
optimal access pattern for numerical computation
```

These are not always the same.

## Dtype Alignment and Padding

With:

```python
dtype = np.dtype(
    [
        ("id", np.int64),
        ("status", np.int8),
    ],
    align=True,
)
```

the record may contain padding so fields satisfy alignment requirements.

This can increase:

```python
dtype.itemsize
```

Inspect the actual layout when memory size or binary interoperability matters:

```python
print(dtype.itemsize)
print(dtype.fields)
```

Do not assume field sizes simply add together when alignment is enabled.

## Structured Arrays and Binary Interoperability

Structured dtypes are particularly useful when a binary protocol or file format defines a fixed record layout.

For example:

```text
8-byte ID
8-byte timestamp
8-byte measurement
1-byte status
```

A matching structured dtype can expose fields directly:

```python
dtype = np.dtype(
    [
        ("id", np.uint64),
        ("timestamp", np.int64),
        ("measurement", np.float64),
        ("status", np.uint8),
    ]
)
```

When interoperating with external binary data, carefully define:

- Field order.
- Byte order.
- Field widths.
- Alignment.
- Padding.
- Version compatibility.

A layout mismatch can produce syntactically valid but semantically corrupted data.

## Byte Order

Structured dtypes can specify byte order for numeric fields.

For example:

```python
dtype = np.dtype(
    [
        ("id", ">u8"),
        ("value", ">f8"),
    ]
)
```

where the `>` indicates a big-endian representation for those fields.

This becomes relevant when reading binary data produced by systems with a known byte-order contract.

Never infer byte order from a file extension or environment. It should come from the format specification.

## Security Considerations

Structured arrays become security-sensitive when processing untrusted binary data.

Validate:

- Expected record count.
- File size.
- Record size.
- Dtype layout.
- Shape.
- Byte order.
- Version.
- Field ranges.

Never assume that a binary file has the schema your application expects.

A malicious or corrupted input can otherwise cause:

```text
incorrect parsing
+
misinterpreted offsets
+
large allocations
+
resource exhaustion
```

For external APIs, prefer schema-aware validation before constructing large structured arrays.

## Operational Considerations

For long-lived pipelines, treat the structured dtype as a schema artifact.

Version important changes such as:

```text
field additions
field removals
dtype changes
field order changes
alignment changes
byte-order changes
```

Document how old records should be read.

For fixed binary files, a schema version header can be useful:

```text
file header
→ schema version
→ record count
→ record layout
→ records
```

This makes migrations and recovery more predictable.

## Common Mistakes

### Using Structured Arrays for All Tabular Data

A structured array is a low-level fixed-record representation, not a general replacement for Pandas or SQL tables.

### Assuming Fields Are All the Same Dtype

Structured arrays intentionally allow different field dtypes.

### Treating Integer IDs as Ordinal Values

A field such as:

```text
status_id = 3
```

does not necessarily mean the status is "greater" than status `2`.

### Ignoring Memory Layout

Field order, alignment, and padding can affect record size and binary compatibility.

### Converting Every Record to a Python Dictionary

This can destroy the memory and performance advantages of the structured representation.

### Assuming Boolean Filtering Is Zero-Copy

Boolean indexing generally creates a new array.

### Mutating Fields Without Considering Aliasing

Field access can expose the original storage, so changes may modify the source structured array.

### Using `align=True` Without a Compatibility Requirement

Alignment can add padding and increase record size.

### Ignoring Byte Order

Binary data with the wrong endianness can be interpreted incorrectly without necessarily raising an obvious error.

### Using Structured Arrays Instead of Normal ndarrays for Homogeneous Data

A plain homogeneous NumPy array is generally simpler when all values share one dtype and one shape.

## Testing

Structured-array tests should validate both values and schema.

```python
import numpy as np


TRANSACTION_DTYPE = np.dtype(
    [
        ("id", np.int64),
        ("amount", np.float64),
        ("status", np.int8),
    ]
)


def test_structured_records():
    records = np.array(
        [
            (101, 250.50, 1),
            (102, 125.75, 0),
        ],
        dtype=TRANSACTION_DTYPE,
    )

    assert records.dtype == TRANSACTION_DTYPE
    assert records.shape == (2,)

    np.testing.assert_array_equal(
        records["id"],
        np.array(
            [101, 102],
            dtype=np.int64,
        ),
    )

    np.testing.assert_allclose(
        records["amount"],
        np.array(
            [250.50, 125.75],
            dtype=np.float64,
        ),
    )
```

For binary or memory-mapped workflows, also test:

- Record size.
- Field offsets.
- Byte order.
- Alignment.
- Schema versions.
- Truncated files.
- Invalid record counts.
- Unexpected field values.
- Compatibility with older data.

## Debugging

Inspect the schema before inspecting the records:

```python
print(
    records.dtype
)

print(
    records.dtype.names
)

print(
    records.dtype.fields
)

print(
    records.dtype.itemsize
)

print(
    records.shape
)
```

For field-specific issues:

```python
print(
    records["amount"].dtype
)

print(
    records["amount"].shape
)
```

For binary compatibility issues, inspect:

```text
dtype
+
field offsets
+
itemsize
+
byte order
+
record count
```

Many structured-array failures are schema mismatches rather than numerical algorithm errors.

## Interview Questions

### What is a structured NumPy array?

It is an `ndarray` whose dtype defines multiple named fields, allowing each record to contain values with different dtypes.

### When would you use a structured array?

For fixed-schema records, especially when compact storage, field-level NumPy processing, binary interoperability, or memory-mapped files are important.

### How is a structured array different from a normal NumPy array?

A normal numerical array generally uses one dtype for all elements. A structured array defines a record schema with multiple named fields and potentially different dtypes.

### When should you prefer a regular homogeneous array?

When numerical computation dominates and the values share one dtype. Homogeneous arrays usually provide a simpler model for vectorized numerical processing.

### How does a structured array differ from a Pandas DataFrame?

A structured array is a lower-level fixed-layout NumPy representation. A DataFrame provides higher-level labeled tabular operations such as joins, grouping, and richer missing-data handling.

### Can fields be processed with vectorized NumPy operations?

Yes. A field such as:

```python
records["amount"]
```

produces an array-like field view that can participate in NumPy operations.

### Why does `dtype.itemsize` matter?

It gives the size of one structured record and is important for memory estimation, alignment, and binary-file compatibility.

### Why can a structured array be less efficient for some numerical workloads?

Interleaved record storage can be less suitable for workloads that repeatedly process only one field, where a dedicated homogeneous array may provide a more convenient memory-access pattern.

### What is the difference between an array of records and a record of arrays?

A structured array is naturally an array of records. Separate homogeneous arrays represent a record of arrays, which can be preferable when numerical operations are primarily field-oriented.

### Why are alignment and byte order important?

They determine how the structured record is physically represented and are critical when interoperating with external binary formats or C-compatible memory layouts.

## Key Takeaways

- Structured arrays represent fixed-schema records inside a NumPy `ndarray`, with named fields that can have different dtypes.
- They are particularly useful for compact record storage, binary interoperability, memory-mapped files, and low-level numerical pipelines.
- Structured arrays should not replace homogeneous ndarrays for ordinary numerical computation or Pandas for rich tabular ETL.
- Field dtype, record size, alignment, byte order, and mutation semantics are important production concerns when structured arrays cross file or service boundaries.
- Choose between an array of records and separate homogeneous arrays based on the dominant access pattern, memory behavior, and interoperability requirements.