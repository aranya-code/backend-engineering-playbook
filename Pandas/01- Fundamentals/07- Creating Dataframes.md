# 07- Creating Dataframes

## Overview

Creating a DataFrame is the first point where external or in-memory records become a Pandas tabular structure.

The construction method matters because it determines:

- Column names.
- Row alignment.
- Initial dtypes.
- Missing-value behavior.
- Index semantics.
- Memory usage.
- Downstream transformation behavior.

In production systems, DataFrames commonly originate from:

```text
Python records
    ↓
API payloads
    ↓
CSV / JSON / Excel
    ↓
SQL query results
    ↓
Parquet datasets
    ↓
Existing DataFrames / Series
```

A reliable construction step should produce a DataFrame with an intentional schema rather than relying entirely on inference.

The fundamental pattern is:

```text
Source data
    ↓
DataFrame construction
    ↓
Schema inspection
    ↓
Dtype normalization
    ↓
Validation
    ↓
Transformation
```

## Creating a DataFrame from a Dictionary

The most common programmatic construction pattern is a dictionary of column names and values:

```python
import pandas as pd

orders = pd.DataFrame(
    {
        "order_id": [1001, 1002, 1003],
        "customer_id": [101, 102, 101],
        "status": [
            "completed",
            "pending",
            "completed",
        ],
        "amount": [250.0, 175.5, 500.0],
    }
)
```

Each key becomes a column and each sequence provides the column values.

The sequences must have compatible lengths:

```text
order_id     → 3 values
customer_id  → 3 values
status       → 3 values
amount       → 3 values
```

The resulting DataFrame has three rows.

## Dictionary of Series

The values can also be Series:

```python
orders = pd.DataFrame(
    {
        "customer_id": pd.Series(
            [101, 102],
            index=[1001, 1002],
        ),
        "amount": pd.Series(
            [250.0, 175.5],
            index=[1001, 1002],
        ),
    }
)
```

When constructing a DataFrame from Series, Pandas aligns them by index.

This is different from simply combining lists positionally.

## Why Series Alignment Matters

Consider:

```python
customer_ids = pd.Series(
    [101, 102],
    index=[1001, 1002],
)

amounts = pd.Series(
    [175.5, 250.0],
    index=[1002, 1001],
)

orders = pd.DataFrame(
    {
        "customer_id": customer_ids,
        "amount": amounts,
    }
)
```

Pandas produces:

```text
       customer_id  amount
1001           101   250.0
1002           102   175.5
```

The values are matched by index labels rather than their physical order.

This behavior is useful when labels represent record identity, but it can be dangerous if positional semantics were intended.

## Creating from Records

API payloads and application code often represent records as a list of dictionaries:

```python
records = [
    {
        "order_id": 1001,
        "customer_id": 101,
        "amount": 250.0,
    },
    {
        "order_id": 1002,
        "customer_id": 102,
        "amount": 175.5,
    },
]

orders = pd.DataFrame(
    records
)
```

This maps naturally to:

```text
one dictionary → one row
dictionary keys → columns
```

It is a practical representation for API normalization and service integration.

## Missing Keys in Records

Records do not have to contain exactly the same keys:

```python
records = [
    {
        "order_id": 1001,
        "customer_id": 101,
        "amount": 250.0,
    },
    {
        "order_id": 1002,
        "customer_id": 102,
    },
]
```

Pandas can create the missing `amount` value as missing data.

This is convenient for semi-structured input, but production code should validate whether the missing field is acceptable.

## Nested API Records

For nested JSON, `json_normalize()` is usually more appropriate than constructing a DataFrame directly:

```python
orders = pd.json_normalize(
    payload["orders"]
)
```

Example:

```python
payload = {
    "orders": [
        {
            "id": 1001,
            "customer": {
                "id": 101,
            },
            "amount": 250.0,
        }
    ]
}
```

Then:

```python
orders = pd.json_normalize(
    payload["orders"]
)
```

can flatten nested paths into columns.

This is especially useful for REST API ingestion.

## Creating from a List of Lists

A DataFrame can also be created from nested sequences:

```python
orders = pd.DataFrame(
    [
        [1001, 101, 250.0],
        [1002, 102, 175.5],
    ],
    columns=[
        "order_id",
        "customer_id",
        "amount",
    ],
)
```

Explicitly providing `columns` is strongly preferable to depending on integer column labels when the data has a defined schema.

## Creating from NumPy Arrays

NumPy arrays can be used as input:

```python
import numpy as np
import pandas as pd

values = np.array(
    [
        [1001, 250.0],
        [1002, 175.5],
    ]
)

orders = pd.DataFrame(
    values,
    columns=[
        "order_id",
        "amount",
    ],
)
```

Be aware that NumPy arrays generally have homogeneous dtype constraints.

If multiple logical columns require different physical types, constructing the DataFrame through a dictionary or records may provide clearer dtype semantics.

## Explicit Index

An Index can be provided during construction:

```python
orders = pd.DataFrame(
    {
        "customer_id": [101, 102, 103],
        "amount": [250.0, 175.5, 500.0],
    },
    index=[
        1001,
        1002,
        1003,
    ],
)
```

Now the index represents order identifiers.

Use an explicit Index when it provides actual value for:

- Label-based lookup.
- Alignment.
- Time-series processing.
- Hierarchical data.
- Index-oriented joins.

Do not introduce an application index merely because the DataFrame resembles a database table.

## Explicit Index vs Business Column

An identifier can remain a column:

```python
orders["order_id"]
```

or become the index:

```python
orders = orders.set_index(
    "order_id"
)
```

The choice depends on downstream use.

For relational ETL and API output, keeping:

```text
order_id
```

as a normal column is often simpler.

For index-heavy time-series or lookup workloads, an explicit Index may be useful.

## Constructing with `dtype`

A dtype can be specified when creating a DataFrame in cases where one dtype applies to the supplied values or when using typed Series.

For example:

```python
statuses = pd.Series(
    [
        "completed",
        "pending",
    ],
    dtype="string",
)

orders = pd.DataFrame(
    {
        "status": statuses,
    }
)
```

For multiple columns with different dtypes, typed Series provide a clearer schema:

```python
orders = pd.DataFrame(
    {
        "order_id": pd.Series(
            [1001, 1002],
            dtype="Int64",
        ),
        "customer_id": pd.Series(
            [101, 102],
            dtype="Int64",
        ),
        "status": pd.Series(
            ["completed", "pending"],
            dtype="string",
        ),
        "amount": pd.Series(
            [250.0, 175.5],
            dtype="Float64",
        ),
    }
)
```

This is useful when the schema must be predictable even before transformation begins.

## Creating an Empty DataFrame

An empty DataFrame can still have a complete schema:

```python
orders = pd.DataFrame(
    {
        "order_id": pd.Series(
            dtype="Int64"
        ),
        "customer_id": pd.Series(
            dtype="Int64"
        ),
        "status": pd.Series(
            dtype="string"
        ),
        "amount": pd.Series(
            dtype="Float64"
        ),
    }
)
```

This produces:

```text
Rows    → 0
Columns → 4
```

with predictable column names and dtypes.

This is particularly useful for:

- Empty API responses.
- No-data batch partitions.
- Unit tests.
- Conditional pipeline branches.
- Functions that must maintain a stable output contract.

## Why Empty Schemas Matter

An empty DataFrame contains insufficient observations for reliable dtype inference.

For example:

```python
empty = pd.DataFrame(
    columns=[
        "order_id",
        "amount",
    ]
)
```

may not have the exact dtypes expected by downstream logic.

Explicit schema construction avoids this ambiguity.

## Scalar Values During Construction

A scalar can be used when an explicit index is provided:

```python
orders = pd.DataFrame(
    {
        "status": "pending",
    },
    index=[1001, 1002, 1003],
)
```

The scalar is broadcast to each index label.

This is useful for initializing a known state across multiple records.

## Column Length Validation

When constructing from lists:

```python
pd.DataFrame(
    {
        "order_id": [1001, 1002],
        "amount": [250.0],
    }
)
```

all list-like columns must have compatible lengths.

A mismatch:

```python
pd.DataFrame(
    {
        "order_id": [1001, 1002, 1003],
        "amount": [250.0, 175.5],
    }
)
```

raises an error rather than silently inventing missing rows.

This strictness is useful because row alignment is ambiguous without an explicit index.

## Construction from Existing DataFrames

A DataFrame can be passed to `pd.DataFrame()`:

```python
copy = pd.DataFrame(
    orders
)
```

This should not automatically be interpreted as the preferred way to copy a DataFrame.

When explicit independent ownership is required:

```python
copy = orders.copy()
```

is clearer.

The distinction is especially important when large datasets are involved.

## Construction from a Series

A Series can become a one-column DataFrame:

```python
amounts = orders[
    "amount"
]

amount_df = amounts.to_frame()
```

This is often clearer than reconstructing the DataFrame manually.

A custom column name can be supplied:

```python
amount_df = amounts.to_frame(
    name="order_amount"
)
```

## Creating DataFrames from Multiple Series

Aligned Series can be combined:

```python
orders = pd.concat(
    [
        customer_ids.rename(
            "customer_id"
        ),
        amounts.rename(
            "amount"
        ),
    ],
    axis=1,
)
```

This is useful when different transformation stages produce independently labeled Series.

The shared Index determines row alignment.

## Construction from Dictionaries with an Explicit Column Order

For deterministic schemas:

```python
orders = pd.DataFrame(
    records,
    columns=[
        "order_id",
        "customer_id",
        "status",
        "amount",
    ],
)
```

This makes the expected output columns explicit.

Fields absent from the records can become missing values.

This can be useful when constructing DataFrames from external records with optional fields.

## Schema Projection During Construction

When only selected fields are required:

```python
orders = pd.DataFrame(
    records,
    columns=[
        "order_id",
        "customer_id",
        "amount",
    ],
)
```

This can be preferable to constructing every available field and dropping unwanted columns later.

The general principle is:

```text
Load only what you need
```

This reduces memory and clarifies the downstream contract.

## DataFrame Construction from SQL Results

Database APIs can produce records or directly return DataFrames.

Directly:

```python
orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        status,
        amount
    FROM orders
    WHERE created_at >= %s
    """,
    connection,
    params=[start_date],
)
```

The query should select the intended schema.

Avoid:

```sql
SELECT *
FROM orders
```

when only a subset of fields is required.

The database can often perform filtering and projection more efficiently than loading a larger result into Pandas.

## DataFrame Construction from API Responses

An API client may retrieve:

```python
payload = response.json()
```

Then:

```python
orders = pd.json_normalize(
    payload["orders"]
)
```

A production implementation should validate the payload before assuming:

```python
payload["orders"]
```

exists.

The transport layer should also handle:

```text
Authentication
Timeouts
Retries
Pagination
Rate limits
HTTP status codes
```

before Pandas processing begins.

## Construction from CSV

A CSV source should generally be read directly rather than manually constructing rows:

```python
orders = pd.read_csv(
    "orders.csv",
    usecols=[
        "order_id",
        "customer_id",
        "status",
        "amount",
    ],
)
```

This lets Pandas use its CSV parser and avoids intermediate Python structures.

For large datasets:

```python
for chunk in pd.read_csv(
    "orders.csv",
    chunksize=100_000,
):
    process_chunk(chunk)
```

## Construction from Parquet

For typed analytical data:

```python
orders = pd.read_parquet(
    "orders.parquet",
    columns=[
        "order_id",
        "customer_id",
        "amount",
    ],
)
```

Column projection at read time can reduce I/O and memory.

For recurring ETL pipelines, Parquet is often preferable to repeatedly reconstructing DataFrames from text formats.

## Column Name Normalization

External data should often be normalized immediately after construction:

```python
orders.columns = (
    orders.columns
    .str.strip()
    .str.lower()
    .str.replace(
        " ",
        "_",
    )
)
```

A more controlled API normalization is:

```python
orders = orders.rename(
    columns={
        "customerId": "customer_id",
        "orderAmount": "amount",
    }
)
```

The second approach is safer when exact source-to-target mappings are known.

## Duplicate Columns

Reject duplicate column labels when they violate the schema:

```python
if not orders.columns.is_unique:
    raise ValueError(
        "Duplicate column names detected"
    )
```

Duplicate columns make downstream selection and assignment ambiguous.

A production ingestion boundary should generally define whether duplicates are:

```text
Valid
Ignored
Renamed
Rejected
```

## Construction and Dtype Validation

After construction:

```python
print(orders.dtypes)
```

For a stronger contract:

```python
expected = {
    "order_id": "Int64",
    "customer_id": "Int64",
    "status": "string",
    "amount": "Float64",
}
```

Then compare the schema before proceeding.

The important distinction is:

```text
Construction
    ↓
Normalization
    ↓
Validation
```

Do not assume successful construction means the data is valid.

## Construction and Business Validation

A DataFrame can be structurally valid:

```text
order_id = 1001
amount = -500
```

The dtype can still be correct while the value violates business rules.

After construction, validate:

```python
if orders["amount"].lt(0).any():
    raise ValueError(
        "Negative amounts are not allowed"
    )
```

Schema validation and business validation are separate responsibilities.

## Construction and Row Grain

When creating a DataFrame, establish what a row represents.

For example:

```text
API records
→ one row per order

Nested item records
→ one row per order item
```

If a nested API payload contains both orders and items, do not flatten them together without considering the resulting grain.

A safer design may be:

```text
orders DataFrame
      +
order_items DataFrame
```

rather than one denormalized DataFrame containing repeated parent information.

## Construction and Copy Semantics

When creating a DataFrame from another object, understand ownership.

For example:

```python
processed = orders
```

creates another reference.

When independent processing is required:

```python
processed = orders.copy()
```

Avoid indiscriminate copies for large data.

The construction stage should minimize unnecessary duplication.

## Construction and Memory

DataFrame construction can be memory-intensive because source and target representations may coexist.

For example:

```text
List of dictionaries
       +
DataFrame
```

can temporarily consume substantially more memory than the final DataFrame.

For large inputs, prefer direct readers where practical:

```python
pd.read_csv(...)
pd.read_parquet(...)
pd.read_sql(...)
```

instead of:

```text
External source
    ↓
Huge Python list
    ↓
Huge DataFrame
```

## Construction and Large APIs

Consider an API returning hundreds of thousands of records.

An inefficient approach is:

```python
all_records = []

for page in pages:
    all_records.extend(
        page["orders"]
    )

orders = pd.DataFrame(
    all_records
)
```

This can keep both the Python objects and DataFrame representation in memory.

A more scalable approach is to process pages incrementally:

```python
for page in fetch_pages():
    page_df = pd.json_normalize(
        page["orders"]
    )

    process_page(page_df)
```

This bounds memory according to the page or batch size.

## Construction and Chunked ETL

Large file processing can use:

```python
for chunk in pd.read_csv(
    "orders.csv",
    chunksize=100_000,
):
    normalized = normalize(
        chunk
    )

    validated = validate(
        normalized
    )

    write_batch(
        validated
    )
```

The DataFrame construction and processing occur per bounded batch rather than across the complete source.

## Production Schema Pattern

A practical construction function can establish a stable schema:

```python
import pandas as pd


ORDER_COLUMNS = [
    "order_id",
    "customer_id",
    "status",
    "amount",
]


def build_orders(
    records: list[dict],
) -> pd.DataFrame:
    orders = pd.DataFrame(
        records,
        columns=ORDER_COLUMNS,
    )

    orders = orders.assign(
        order_id=lambda df: pd.to_numeric(
            df["order_id"],
            errors="coerce",
        ).astype("Int64"),
        customer_id=lambda df: pd.to_numeric(
            df["customer_id"],
            errors="coerce",
        ).astype("Int64"),
        status=lambda df: (
            df["status"]
            .astype("string")
            .str.strip()
            .str.lower()
        ),
        amount=lambda df: pd.to_numeric(
            df["amount"],
            errors="coerce",
        ).astype("Float64"),
    )

    return orders
```

This combines:

```text
Explicit columns
    ↓
Construction
    ↓
Dtype normalization
    ↓
Canonical schema
```

Validation should follow before the result is considered production-ready.

## Testing DataFrame Construction

Test the resulting contract rather than only checking that construction succeeds.

```python
def test_build_orders():
    records = [
        {
            "order_id": "1001",
            "customer_id": "101",
            "status": " Completed ",
            "amount": "250.00",
        }
    ]

    result = build_orders(records)

    assert list(result.columns) == [
        "order_id",
        "customer_id",
        "status",
        "amount",
    ]

    assert str(
        result["order_id"].dtype
    ) == "Int64"

    assert str(
        result["status"].dtype
    ) == "string"

    assert result.loc[
        0,
        "status",
    ] == "completed"

    assert result.loc[
        0,
        "amount",
    ] == 250.0
```

Also test:

- Empty input.
- Missing fields.
- Invalid numeric values.
- Duplicate records.
- Unexpected columns.
- Null values.
- Incorrect source types.

## Reliability Considerations

A DataFrame construction layer should be deterministic.

Given equivalent input records, it should produce:

```text
Same columns
Same intended dtypes
Same row grain
Same normalization rules
Same missing-value behavior
```

Avoid hidden global state or environment-dependent schema transformations.

This makes ETL jobs easier to retry and test.

## Security Considerations

Construction is also a good opportunity to minimize sensitive data.

For example, if the pipeline only needs:

```text
order_id
customer_id
amount
```

do not construct a DataFrame containing:

```text
password
payment_token
private_address
authentication_data
```

just because those fields exist in the source.

Data minimization reduces exposure in memory, logs, temporary files, and downstream storage.

## Monitoring

Production ingestion should monitor construction quality.

Useful metrics include:

```text
Records received
Rows constructed
Columns received
Missing required fields
Invalid values
Rejected records
Null-rate changes
Processing duration
Input size
Peak memory
```

Unexpected changes can reveal upstream contract changes.

For example:

```text
Yesterday:
10 columns
0.5% null amount

Today:
12 columns
18% null amount
```

may indicate source-system drift even though DataFrame construction still succeeds.

## Common Mistakes

### Building DataFrames from Large Lists of Dictionaries

This can create a large temporary Python representation before the DataFrame exists.

**Better:** use direct readers or bounded batches where appropriate.

### Relying on Automatic Dtype Inference

External data is often ambiguous.

**Better:** normalize and validate important dtypes explicitly.

### Using `object` for Everything

Generic object columns can be memory-heavy and semantically unclear.

**Better:** use appropriate string, numeric, datetime, boolean, or categorical dtypes.

### Treating Identifiers as Numbers

An identifier such as:

```text
000123
```

may lose meaning if converted to an integer.

**Better:** preserve it as a string when formatting is significant.

### Assuming Series Align Positionally

Series values are aligned by index during DataFrame construction.

**Better:** understand index semantics before combining Series.

### Using a Business ID as Index Automatically

An identifier does not need to be the Index.

**Better:** select index usage based on downstream access patterns.

### Constructing Every Available Column

This increases memory and expands the data contract unnecessarily.

**Better:** project required fields at the source or construction boundary.

### Ignoring Empty Input

An empty DataFrame can still need predictable schema and dtypes.

**Better:** define an explicit empty schema when the empty state is valid.

### Confusing Construction with Validation

A DataFrame can be constructed successfully while containing invalid business values.

**Better:** perform schema and business validation after construction.

### Flattening Nested API Data Without Modeling Grain

Nested arrays can represent one-to-many relationships.

**Better:** create separate DataFrames when the domain contains distinct entities.

### Copying Existing DataFrames Unnecessarily

Large copies can create memory spikes.

**Better:** establish ownership explicitly and copy only when independent mutation is required.

### Logging Raw Construction Input

Incoming records can contain sensitive information.

**Better:** log counts, schema metadata, safe identifiers, and error categories instead.

## Interview Traps

### What Are Common Ways to Create a DataFrame?

From dictionaries, lists of records, lists of lists, Series, NumPy arrays, existing DataFrames, database query results, and file readers.

### What Happens When Creating a DataFrame from Multiple Series?

Pandas aligns the Series by their indexes.

### What Happens When List-Like Columns Have Different Lengths?

Construction raises an error because Pandas cannot determine a valid row alignment from the lengths alone.

### How Do You Create a DataFrame with a Stable Empty Schema?

Use typed empty Series:

```python
pd.DataFrame(
    {
        "order_id": pd.Series(
            dtype="Int64"
        ),
        "status": pd.Series(
            dtype="string"
        ),
    }
)
```

### Should Every DataFrame Have a Business Identifier as Its Index?

No. Use an Index when label-based access, alignment, hierarchy, or time-series operations provide practical value.

### Why Might `pd.json_normalize()` Be Better Than `pd.DataFrame()` for API Data?

Nested API records may require flattening of dictionaries and extraction of nested record arrays before they can be represented tabularly.

### Why Should You Prefer Direct Readers for Large Files?

They avoid unnecessary intermediate Python structures and can support options such as column projection and chunked processing.

### Why Can a DataFrame Construction Step Consume More Memory Than Expected?

The source objects and DataFrame may coexist, and nested Python objects can have substantial overhead.

### How Would You Construct Data from a Large API?

Process paginated responses incrementally rather than accumulating the complete payload in a Python list.

### Why Separate Construction from Validation?

Construction determines the tabular representation. Validation determines whether the representation satisfies schema and business rules.

### What Should You Check After Construction?

At minimum:

```text
Columns
Dtypes
Row count
Row grain
Required fields
Missing values
Duplicates
Business constraints
```

## Practical Construction Checklist

```text
[ ] What is the source representation?
[ ] What does one row represent?
[ ] Which columns are required?
[ ] Are column names canonical?
[ ] Are column names unique?
[ ] Are only required fields being loaded?
[ ] Are dtypes explicit or normalized?
[ ] Are identifiers represented correctly?
[ ] Are leading zeros preserved where necessary?
[ ] Are nullable fields using appropriate dtypes?
[ ] Could Series index alignment affect construction?
[ ] Is an explicit Index actually needed?
[ ] Is the empty-data schema defined?
[ ] Are nested records modeled at the correct grain?
[ ] Can the source exceed worker memory?
[ ] Should construction happen in chunks?
[ ] Are source-side filtering and projection possible?
[ ] Is construction separated from validation?
[ ] Are sensitive fields minimized?
[ ] Are schema and quality metrics observable?
[ ] Are normal, empty, invalid, and unexpected inputs tested?
```

## Key Takeaways

- DataFrame construction establishes the initial tabular representation, so column names, row grain, index semantics, and dtypes should be deliberate rather than entirely inferred.
- Dictionaries, records, Series, NumPy arrays, files, databases, and APIs can all produce DataFrames, but each source has different alignment, schema, parsing, and memory considerations.
- Series are aligned by Index when combined into a DataFrame, while list-like columns require compatible lengths; understanding these semantics prevents silent row-association errors.
- For production workloads, prefer explicit schemas, source-side projection, appropriate dtypes, bounded batch construction, and separate validation rather than constructing oversized or weakly typed DataFrames.
- Reliable construction code treats empty inputs, malformed records, nested relationships, sensitive fields, memory limits, and schema drift as explicit engineering concerns.