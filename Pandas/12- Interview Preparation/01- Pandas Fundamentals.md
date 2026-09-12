# 01- Pandas Fundamentals

## Overview

Pandas is a Python library for working with labeled tabular data. Its two primary structures are:

```text
Series
DataFrame
```

For backend and data-engineering work, Pandas is most useful as an in-memory processing layer between systems such as:

```text
PostgreSQL
REST APIs
CSV / JSON
Parquet
S3
Kafka
reporting systems
```

The fundamentals matter because production Pandas work depends on understanding:

```text
how data is represented
how indexes behave
how columns are typed
how operations align data
how mutations work
how missing values propagate
how memory is consumed
```

The goal at this stage is not to memorize methods. It is to understand the execution model well enough to reason about unfamiliar DataFrame code during implementation, debugging, and interviews.

---

## Pandas Data Model

A useful mental model is:

```text
DataFrame
├── Index
├── Columns
└── Series objects
    ├── values
    ├── dtype
    └── index
```

A DataFrame is conceptually a collection of aligned Series sharing a common row index.

```python
import pandas as pd

orders = pd.DataFrame(
    {
        "order_id": ["O-1001", "O-1002"],
        "customer_id": ["C-101", "C-102"],
        "amount": [125.50, 300.00],
    }
)
```

The result can be visualized as:

```text
         order_id  customer_id  amount
index
0        O-1001    C-101        125.50
1        O-1002    C-102        300.00
```

The index is not just display metadata. It participates in alignment and many Pandas operations.

---

## Series

A `Series` is a one-dimensional labeled array.

```python
amounts = pd.Series(
    [125.50, 300.00, 75.25],
    name="amount",
)
```

It has:

```text
values
index
name
dtype
```

Inspect the structure:

```python
print(amounts.index)
print(amounts.dtype)
print(amounts.name)
```

A DataFrame column is normally returned as a Series:

```python
orders["amount"]
```

The result is:

```text
<class 'pandas.Series'>
```

---

## DataFrame

A `DataFrame` is a two-dimensional labeled table.

```python
orders = pd.DataFrame(
    {
        "order_id": ["O-1001", "O-1002", "O-1003"],
        "customer_id": ["C-101", "C-102", "C-101"],
        "amount": [125.50, 300.00, 75.25],
    }
)
```

Core properties include:

```python
orders.shape
orders.columns
orders.index
orders.dtypes
orders.size
orders.empty
```

Example:

```python
print(orders.shape)
# (3, 3)
```

`shape` is:

```text
(rows, columns)
```

---

## Index

Every Series and DataFrame has an index.

By default:

```python
orders.index
```

may be:

```text
RangeIndex(start=0, stop=3, step=1)
```

The index can also contain meaningful labels:

```python
orders = orders.set_index(
    "order_id"
)
```

Now:

```text
         customer_id  amount
order_id
O-1001   C-101        125.50
O-1002   C-102        300.00
O-1003   C-101         75.25
```

The index affects:

```text
selection
alignment
joins
grouping
assignment
result shape
```

Do not treat it as merely a row number.

---

## Positional vs Label-Based Access

Pandas supports different access models.

### Positional

```python
orders.iloc[0]
```

means:

```text
first row
```

### Label-Based

If `order_id` is the index:

```python
orders.loc["O-1001"]
```

means:

```text
row whose label is O-1001
```

The distinction is important:

```text
iloc → position
loc  → label
```

Interview questions often test this difference.

---

## Column Selection

Select one column:

```python
orders["amount"]
```

Result:

```text
Series
```

Select multiple columns:

```python
orders[
    [
        "order_id",
        "amount",
    ]
]
```

Result:

```text
DataFrame
```

This distinction matters when chaining operations.

---

## Attribute Access

Pandas also allows:

```python
orders.amount
```

when `amount` is a valid attribute-style column name.

Prefer:

```python
orders["amount"]
```

for production code because it is:

```text
explicit
consistent
safe for unusual column names
unambiguous when columns conflict with DataFrame attributes
```

Avoid relying on attribute access in reusable pipeline code.

---

## Row Selection

Select one row by position:

```python
row = orders.iloc[0]
```

Select multiple rows:

```python
rows = orders.iloc[
    0:2
]
```

Select by condition:

```python
completed = orders.loc[
    orders["amount"] > 100
]
```

The result of row filtering is typically a DataFrame when multiple rows or columns are involved.

---

## Boolean Filtering

Boolean indexing is one of the most important Pandas operations.

```python
large_orders = orders.loc[
    orders["amount"] > 100
]
```

Multiple conditions require element-wise operators:

```python
filtered = orders.loc[
    (orders["amount"] > 100)
    & (orders["customer_id"] == "C-101")
]
```

Use:

```text
& → and
| → or
~ → not
```

Do not use Python's:

```python
and
or
not
```

with Pandas Series.

---

## Operator Precedence

Wrap conditions in parentheses:

```python
orders.loc[
    (orders["amount"] > 100)
    & (orders["customer_id"] == "C-101")
]
```

Without parentheses, Python's operator precedence can produce incorrect expressions or errors.

This is a common interview and production mistake.

---

## `loc` with Columns

`loc` can select both rows and columns:

```python
result = orders.loc[
    orders["amount"] > 100,
    [
        "order_id",
        "amount",
    ],
]
```

This means:

```text
rows:
amount > 100

columns:
order_id, amount
```

The general form is:

```python
df.loc[row_selector, column_selector]
```

This becomes important for precise transformations and avoiding unnecessary data copies.

---

## `iloc` with Rows and Columns

`iloc` operates positionally:

```python
result = orders.iloc[
    :2,
    :2,
]
```

This selects:

```text
first two rows
first two columns
```

Use `iloc` when the operation is defined in terms of positions.

Use `loc` when the operation is defined in terms of labels or boolean conditions.

---

## Creating DataFrames

From dictionaries:

```python
orders = pd.DataFrame(
    {
        "order_id": ["O-1", "O-2"],
        "amount": [100, 200],
    }
)
```

From records:

```python
records = [
    {
        "order_id": "O-1",
        "amount": 100,
    },
    {
        "order_id": "O-2",
        "amount": 200,
    },
]

orders = pd.DataFrame.from_records(
    records
)
```

`from_records()` is particularly useful for:

```text
REST API responses
event batches
database-like record structures
```

---

## Creating Series

```python
amounts = pd.Series(
    [100, 200, 300],
    name="amount",
)
```

Explicitly naming a Series is useful when it later becomes a DataFrame column or participates in reporting logic.

---

## Inspecting Data

Before transforming external data, inspect it.

Useful operations:

```python
df.head()
df.tail()
df.sample(5)
df.shape
df.columns
df.dtypes
df.info()
df.describe()
```

For production debugging:

```python
print(df.shape)
print(df.dtypes)
print(df.isna().sum())
```

Do not rely only on `head()`.

A dataset can look correct in the first five rows while containing thousands of invalid records later.

---

## `info()`

`info()` is useful for understanding structure:

```python
orders.info()
```

It helps inspect:

```text
column names
non-null counts
dtypes
memory usage
```

For large DataFrames, this is often more useful initially than printing the entire dataset.

---

## `describe()`

For numeric columns:

```python
orders["amount"].describe()
```

provides statistics such as:

```text
count
mean
std
min
quartiles
max
```

This is useful for exploratory inspection and anomaly detection.

It is not a substitute for production data-quality rules.

---

## Data Types

Every Series has a dtype.

Example:

```python
orders.dtypes
```

may show:

```text
order_id        object
customer_id     object
amount         float64
```

Dtypes affect:

```text
correctness
memory
performance
missing-value behavior
database interoperability
serialization
```

Do not treat dtype normalization as cosmetic cleanup.

---

## Common Dtypes

Common Pandas dtypes include:

```text
int64
float64
bool
string
datetime64[ns]
datetime64[ns, UTC]
category
object
```

For modern production code, prefer appropriate specialized dtypes over relying on generic `object` storage when practical.

Example:

```python
orders["status"] = (
    orders["status"]
    .astype("string")
)
```

---

## Numeric Conversion

External sources frequently provide numeric values as strings.

```python
orders["amount"] = pd.to_numeric(
    orders["amount"],
    errors="raise",
)
```

`errors="raise"` is appropriate when invalid numeric values should stop processing.

Use:

```python
errors="coerce"
```

only when converting invalid values to missing data is an explicit business decision.

Silent coercion can hide source corruption.

---

## Datetime Conversion

Normalize timestamps explicitly:

```python
orders["created_at"] = pd.to_datetime(
    orders["created_at"],
    utc=True,
    errors="raise",
)
```

Using UTC at system boundaries avoids ambiguity when services operate across time zones.

Datetime normalization becomes especially important for:

```text
incremental processing
batch windows
reporting
event ordering
SLA measurements
```

---

## Missing Values

Pandas represents missing data using values such as:

```text
NaN
NaT
None
pd.NA
```

Detect missing values with:

```python
orders.isna()
```

Count them:

```python
orders.isna().sum()
```

Fill them explicitly:

```python
orders["discount"] = (
    orders["discount"]
    .fillna(0)
)
```

The correct replacement depends on business semantics.

---

## Missing Value Semantics

Do not assume:

```text
missing = zero
```

For example:

```text
discount missing
```

might mean:

```text
no discount
```

but:

```text
customer_id missing
```

may indicate:

```text
invalid record
```

The transformation should encode the meaning of the data rather than merely eliminate missing values.

---

## Null Behavior in Expressions

Missing values can propagate through calculations.

For example:

```python
orders["net_amount"] = (
    orders["amount"]
    - orders["discount"]
)
```

If `discount` is missing, the result may also be missing.

That may be correct or may indicate that the input needs normalization first.

Always define null behavior explicitly for important financial or business calculations.

---

## Assignment and Mutation

Pandas operations often return a new object unless explicitly performing an in-place operation.

Prefer clear assignments:

```python
orders = orders.copy()

orders["amount"] = pd.to_numeric(
    orders["amount"],
    errors="raise",
)
```

Avoid ambiguous mutation through chained indexing.

Unsafe style:

```python
orders[
    orders["amount"] > 100
]["status"] = "priority"
```

Prefer:

```python
orders.loc[
    orders["amount"] > 100,
    "status",
] = "priority"
```

The latter expresses the target rows and column explicitly.

---

## Copy Semantics

When a DataFrame is passed through transformations, make copying decisions explicit when necessary.

```python
subset = orders[
    [
        "order_id",
        "amount",
    ]
].copy()
```

This is useful when `subset` will be modified independently.

Unnecessary copying can increase memory usage, especially for large DataFrames.

The engineering goal is:

```text
avoid ambiguous mutation
+
avoid unnecessary allocations
```

---

## Index Alignment

Pandas aligns Series by index during many operations.

Example:

```python
left = pd.Series(
    [10, 20],
    index=["A", "B"],
)

right = pd.Series(
    [1, 2],
    index=["B", "A"],
)

result = left + right
```

The result is aligned by labels:

```text
A → 10 + 2
B → 20 + 1
```

This is powerful but can surprise developers who expect purely positional behavior.

---

## Alignment and Assignment

Consider:

```python
discounts = pd.Series(
    [10, 20],
    index=["O-2", "O-1"],
)

orders = orders.set_index(
    "order_id"
)

orders["discount"] = discounts
```

The values align by index label rather than by array position.

This behavior is useful for:

```text
joining derived Series
```

but dangerous when positional assumptions are incorrect.

---

## Index Resetting

Reset the index when labels should no longer define the row identity:

```python
orders = orders.reset_index()
```

Or avoid preserving the old index:

```python
orders = orders.reset_index(
    drop=True
)
```

The appropriate choice depends on whether the existing index contains meaningful information.

---

## Sorting

Sort by one column:

```python
orders = orders.sort_values(
    "amount",
    ascending=False,
)
```

Sort by multiple columns:

```python
orders = orders.sort_values(
    [
        "customer_id",
        "amount",
    ],
    ascending=[
        True,
        False,
    ],
)
```

Sorting can be expensive on large datasets, especially when performed unnecessarily.

---

## Vectorization

Prefer operations that operate on entire Series or DataFrames.

Good:

```python
orders["total"] = (
    orders["quantity"]
    * orders["unit_price"]
)
```

Less desirable for large datasets:

```python
orders["total"] = orders.apply(
    lambda row: (
        row["quantity"]
        * row["unit_price"]
    ),
    axis=1,
)
```

Vectorized operations usually provide clearer semantics and better performance.

---

## `apply()`

`apply()` can still be appropriate when vectorized alternatives do not express the required logic.

Example:

```python
orders["risk_code"] = orders[
    "amount"
].apply(classify_amount)
```

Before using `apply()`, ask:

```text
Can this be expressed with vectorized Pandas operations?
```

For large datasets, repeated Python-level function calls can become a bottleneck.

---

## Method Chaining

Readable method chains can express transformations clearly:

```python
result = (
    orders
    .loc[orders["amount"] > 100]
    .assign(
        tax=lambda frame: (
            frame["amount"] * 0.18
        )
    )
    .sort_values(
        "amount",
        ascending=False,
    )
)
```

Use chaining when the flow remains understandable.

Break complex transformations into named intermediate DataFrames when doing so improves readability, debugging, or testing.

---

## Common Table Operations

Several operations form the foundation of production Pandas work:

```text
select
filter
assign
rename
sort
groupby
merge
concat
fillna
dropna
drop_duplicates
```

The important interview skill is understanding:

```text
what each operation returns
how the index behaves
how missing values behave
whether input is mutated
what happens to dtypes
```

---

## `assign()`

`assign()` creates columns without mutating the original DataFrame.

```python
result = orders.assign(
    total=lambda frame: (
        frame["quantity"]
        * frame["unit_price"]
    )
)
```

This works particularly well in transformation pipelines.

Because the expression receives the current DataFrame, multiple derived columns can be built in a readable chain.

---

## `rename()`

Rename columns explicitly:

```python
orders = orders.rename(
    columns={
        "cust_id": "customer_id",
        "amt": "amount",
    }
)
```

This is useful at source boundaries where external naming conventions differ from internal schemas.

Explicit naming reduces downstream ambiguity.

---

## `drop()`

Drop columns:

```python
orders = orders.drop(
    columns=["debug_field"]
)
```

Drop rows by index:

```python
orders = orders.drop(
    index=["O-1001"]
)
```

Avoid using `drop()` as a substitute for understanding why data should be removed.

---

## `drop_duplicates()`

Remove duplicate rows:

```python
orders = orders.drop_duplicates(
    subset=["order_id"],
    keep="last",
)
```

The important question is not:

```text
"How do I remove duplicates?"
```

but:

```text
"What makes two records duplicates in this domain?"
```

A business key should usually determine the duplicate definition.

---

## `dropna()`

`dropna()` can remove rows or columns containing missing values.

```python
valid_orders = orders.dropna(
    subset=[
        "order_id",
        "customer_id",
    ]
)
```

Use targeted `subset=` rules rather than broad:

```python
orders.dropna()
```

when different fields have different business semantics.

---

## `fillna()`

Use `fillna()` when a missing value has a valid replacement.

```python
orders["discount"] = (
    orders["discount"]
    .fillna(0)
)
```

Do not use generic replacements without understanding the meaning of the missing value.

---

## Selecting by Membership

Use `isin()` for membership conditions:

```python
valid_statuses = {
    "pending",
    "processing",
    "completed",
}

filtered = orders.loc[
    orders["status"].isin(
        valid_statuses
    )
]
```

This is preferable to manually chaining many equality conditions.

---

## `query()`

`query()` can express filters compactly:

```python
filtered = orders.query(
    "amount > 100 and status == 'completed'"
)
```

It can be readable for straightforward expressions.

For complex or reusable logic, `.loc[]` may be clearer because the column references and Python variables are explicit.

---

## Grouping Fundamentals

`groupby()` splits data into groups and allows aggregation or transformation.

Example:

```python
revenue = (
    orders
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum"),
        order_count=(
            "order_id",
            "count",
        ),
    )
)
```

Conceptually:

```text
split
  ↓
apply
  ↓
combine
```

Groupby behavior becomes important for reporting, ETL, and incremental aggregation.

---

## Groupby and Missing Keys

Grouping behavior around missing keys depends on the operation and configuration.

When null groups matter, make the intent explicit rather than assuming missing keys will behave as expected.

For example:

```python
orders.groupby(
    "customer_id",
    dropna=False,
)
```

This can preserve a missing-key group in the result.

---

## Merging Fundamentals

Merge DataFrames using relational-style joins:

```python
enriched = orders.merge(
    customers,
    on="customer_id",
    how="left",
    validate="many_to_one",
)
```

The major join types are:

```text
inner
left
right
outer
cross
```

The correct join depends on the business relationship.

---

## Join Cardinality

Expected cardinality should be explicit.

Common relationships:

```text
one-to-one
one-to-many
many-to-one
many-to-many
```

For example:

```python
orders.merge(
    customers,
    on="customer_id",
    validate="many_to_one",
)
```

This verifies the assumption that one customer can correspond to many orders but each customer ID identifies one customer row.

A many-to-many join can unexpectedly multiply rows and create incorrect totals.

---

## Concatenation

Use `concat()` when combining compatible DataFrames:

```python
combined = pd.concat(
    [
        january,
        february,
        march,
    ],
    ignore_index=True,
)
```

`concat()` is commonly used for:

```text
files
partitions
API batches
monthly datasets
```

It is not a substitute for a relational join.

---

## Merge vs Concat

| Operation | Primary Purpose |
|---|---|
| `merge()` | Relational join using keys |
| `concat()` | Stack or combine aligned objects |
| `join()` | Index-oriented combining |
| `combine_first()` | Fill missing values from another aligned object |

Interview questions often test whether these operations are being used for the right problem.

---

## Performance Fundamentals

Basic performance rules:

```text
filter early
select fewer columns
prefer vectorization
avoid unnecessary copies
avoid Python loops
avoid repeated concat in loops
avoid unnecessary sorting
validate join cardinality
```

For example, this can be expensive:

```python
result = pd.DataFrame()

for batch in batches:
    result = pd.concat(
        [result, batch]
    )
```

Prefer collecting a bounded list and concatenating once when the complete result genuinely fits in memory:

```python
result = pd.concat(
    batches,
    ignore_index=True,
)
```

For large pipelines, stream and persist instead of accumulating everything.

---

## Memory Fundamentals

A DataFrame's memory usage depends on:

```text
number of rows
number of columns
dtype
string cardinality
intermediate allocations
```

Inspect memory:

```python
orders.info(
    memory_usage="deep"
)
```

For production workloads, measure process RSS as well as DataFrame-reported memory because temporary objects and runtime overhead may be significant.

---

## Categories

Categorical data can reduce memory when a column has a relatively small repeated set of values.

Example:

```python
orders["status"] = orders[
    "status"
].astype("category")
```

This can be useful for columns such as:

```text
status
country
department
product_type
```

Do not convert high-cardinality identifiers blindly. The benefit depends on the data distribution and workload.

---

## Empty DataFrames

Empty inputs should have explicit semantics.

```python
if orders.empty:
    return
```

An empty DataFrame may represent:

```text
valid no-op
empty API response
missing source data
unexpected filtering
failed extraction
```

Do not automatically treat all empty datasets as either success or failure.

---

## Unexpected Input

Production data can contain:

```text
missing columns
additional columns
invalid values
unexpected dtype
duplicate records
null keys
malformed JSON
incorrect timestamps
```

A robust pipeline should:

```text
validate
→
classify
→
fail or quarantine
```

rather than silently adapting to every unexpected input.

---

## Common Fundamental Mistakes

### Confusing `loc` and `iloc`

Remember:

```text
loc  → labels
iloc → positions
```

### Using `and` Instead of `&`

Series comparisons require element-wise operators.

### Forgetting Parentheses

Use:

```python
(condition_a) & (condition_b)
```

### Treating Index as Meaningless

Index alignment can change the result of arithmetic and assignments.

### Using `apply(axis=1)` Everywhere

It often turns vectorized operations into Python-level iteration.

### Assuming `merge()` Is Always Safe

Incorrect cardinality can multiply rows.

### Using `drop_duplicates()` Without a Business Key

The wrong duplicate definition can remove legitimate records.

### Blindly Using `dropna()`

It can delete valid records whose missing fields are acceptable.

### Silently Coercing Invalid Values

`errors="coerce"` can hide source corruption.

### Creating Many Intermediate Copies

Copies can become expensive on large DataFrames.

### Concatenating Repeatedly in a Loop

Repeated concatenation can create unnecessary allocations and poor scaling.

### Relying on Attribute Column Access

Prefer:

```python
df["column"]
```

over:

```python
df.column
```

for predictable production code.

---

## Backend Engineering Checklist

```text
[ ] DataFrame schema is understood
[ ] Index semantics are explicit
[ ] dtypes are appropriate
[ ] Missing-value behavior is defined
[ ] Filtering uses correct boolean operators
[ ] Selection uses loc/iloc intentionally
[ ] Transformations are vectorized where practical
[ ] Join cardinality is understood
[ ] Duplicate semantics are explicit
[ ] Empty input behavior is defined
[ ] External input is validated
[ ] Memory use is measured for large datasets
[ ] SQL filtering is pushed to the source when appropriate
[ ] Large inputs can be chunked
[ ] Transformations are testable and deterministic
[ ] Database writes use explicit transaction semantics
[ ] Retries and idempotency are considered for production pipelines
```

## Interview Perspective

### What Are the Two Core Pandas Data Structures?

`Series` is a labeled one-dimensional structure. `DataFrame` is a labeled two-dimensional table composed of aligned Series.

### What Is the Difference Between `loc` and `iloc`?

`loc` selects by labels and boolean conditions. `iloc` selects by integer position.

### Why Does the Pandas Index Matter?

The index participates in selection, alignment, assignment, joins, and many aggregation operations. It can change results even when the displayed values look identical.

### What Happens When Two Series Are Added with Different Index Order?

Pandas aligns them by index label before performing the arithmetic.

### Why Is `df["column"]` Usually Preferred Over `df.column`?

Bracket notation is explicit and works with arbitrary column names without colliding with DataFrame attributes or methods.

### What Is the Difference Between a Series and a DataFrame When Selecting Columns?

Selecting one column with:

```python
df["amount"]
```

returns a Series. Selecting multiple columns returns a DataFrame.

### Why Use `validate="many_to_one"` in `merge()`?

It turns an expected relationship into an executable check and can prevent silent row multiplication from an incorrect join.

### Why Can a Many-to-Many Join Be Dangerous?

Both sides may contain repeated keys, causing the result to contain the Cartesian product of matching rows and potentially inflating metrics.

### When Should You Use `apply()`?

When a required transformation cannot reasonably be expressed with vectorized operations. For large datasets, prefer vectorized methods where possible.

### What Is the Difference Between `merge()` and `concat()`?

`merge()` combines datasets according to relational keys. `concat()` combines objects along an axis, commonly stacking batches or partitions.

### How Does Pandas Handle Missing Values?

Missing values can be represented by `NaN`, `NaT`, `None`, or `pd.NA` depending on dtype and operation. Use explicit `isna()`, `fillna()`, or targeted filtering according to business semantics.

### Why Is `errors="coerce"` Potentially Dangerous?

It can convert invalid input into missing values, allowing corrupted source data to continue through the pipeline unnoticed.

### How Does Vectorization Improve Pandas Performance?

Vectorized operations operate over whole arrays or Series rather than invoking Python code once per row, generally reducing interpreter overhead and improving performance.

### Why Can Pandas Use More Memory Than the Source File?

In-memory representations, Python objects, indexes, temporary arrays, copies, joins, and transformations can all increase memory beyond the raw serialized input size.

### When Should You Use `copy()`?

Use it when you need an explicitly independent object that will be modified, particularly when working with a selected subset and wanting clear mutation semantics.

### How Would You Process a Dataset Larger Than Memory?

Reduce it at the source, select only required columns, process in chunks or incremental windows, persist results incrementally, and consider another execution engine when the workload exceeds Pandas' single-node model.

### What Makes a Pandas Transformation Production-Ready?

It should have explicit assumptions, predictable dtypes, defined null behavior, validation, deterministic logic, tests, appropriate performance characteristics, and a clear failure strategy.

## Key Takeaways

- Understand `Series`, `DataFrame`, indexes, dtypes, and alignment before relying on higher-level Pandas operations.
- Use `loc` and `iloc` intentionally, prefer vectorized operations, and treat missing values, copies, and dtype conversions as correctness concerns.
- Joins, filtering, grouping, and concatenation are foundational production operations; their cardinality and memory behavior matter as much as their syntax.
- Production Pandas requires explicit handling of invalid input, empty data, duplicates, memory limits, and transformation determinism.
- Strong interview answers explain not only how a Pandas method works, but also why it is appropriate, what can go wrong, and how the choice behaves at production scale.