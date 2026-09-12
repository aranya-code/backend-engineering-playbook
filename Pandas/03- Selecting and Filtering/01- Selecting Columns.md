# README

## Overview

The **Selecting and Filtering** section covers how to retrieve, constrain, and modify subsets of Pandas data safely and predictably.

Selection is foundational because most real-world DataFrame work starts with:

```text
Large dataset
    ↓
Select relevant columns
    ↓
Filter relevant rows
    ↓
Inspect / transform subset
    ↓
Produce result
```

These operations appear throughout:

```text
ETL pipelines
Reporting
API processing
Data validation
Database extraction
Feature preparation
Batch processing
```

The core objective is to understand the difference between:

```text
Selecting by label
Selecting by position
Filtering by condition
Selecting a single scalar
Setting values in a subset
```

and to use each mechanism deliberately.

## Section Scope

This section covers:

```text
Selecting Columns
Selecting Rows
loc
iloc
at and iat
Boolean Filtering
Multiple Conditions
isin
query
Filtering Missing Values
Indexing and Selection
Setting Values
```

The topics build from basic column and row selection toward composable filtering and safe mutation.

## Topic Progression

The recommended sequence is:

```text
Selecting Columns
        ↓
Selecting Rows
        ↓
loc
        ↓
iloc
        ↓
at and iat
        ↓
Boolean Filtering
        ↓
Multiple Conditions
        ↓
isin
        ↓
query
        ↓
Filtering Missing Values
        ↓
Indexing and Selection
        ↓
Setting Values
```

The progression moves from:

```text
"What data do I want?"
```

to:

```text
"How do I select it correctly and safely?"
```

and finally:

```text
"How do I update only the intended records?"
```

## Selecting Columns

Column selection is often the first operation applied to a DataFrame.

```python
orders = orders[
    [
        "order_id",
        "customer_id",
        "amount",
    ]
]
```

Selecting only required columns is important for:

```text
Readability
Memory usage
Security
Stable schemas
Downstream contracts
```

A useful production pattern is:

```text
Project only required fields
        ↓
Process smaller DataFrame
```

This principle is consistent with SQL projection and API field minimization.

## Selecting Rows

Rows can be selected using:

```python
orders.iloc[0:100]
```

or label-oriented mechanisms such as:

```python
orders.loc[
    some_index_value
]
```

Row selection should be based on the meaning of the index and the desired semantics.

Avoid assuming that:

```text
row position
=
business identifier
```

An index is a selection mechanism, not automatically a domain key.

## `loc`

`.loc` is label-based selection.

```python
orders.loc[
    orders["status"].eq("completed"),
    [
        "order_id",
        "amount",
    ],
]
```

It is particularly useful because it supports both:

```text
Row selection
+
Column selection
```

in one expression.

A common production pattern is:

```python
filtered = orders.loc[
    condition,
    required_columns,
]
```

This makes the selection boundary explicit.

## `iloc`

`.iloc` is position-based selection.

```python
recent = orders.iloc[
    :100,
    :4,
]
```

It is useful when the requirement is inherently positional:

```text
First N rows
Specific row positions
Specific column positions
```

Do not use `iloc` when the requirement is actually:

```text
customer_id = "C-1001"
status = "completed"
```

Use semantic filtering or label-based selection instead.

## `at` and `iat`

`at` and `iat` are scalar accessors.

Use `at` for label-based scalar access:

```python
amount = orders.at[
    order_index,
    "amount",
]
```

Use `iat` for position-based scalar access:

```python
amount = orders.iat[
    0,
    2,
]
```

They are useful when exactly one scalar value is required.

For broader DataFrame operations, prefer `loc` or `iloc` because they communicate intent more clearly.

## Boolean Filtering

Boolean filtering constructs a boolean mask and uses it to select rows.

```python
completed = orders.loc[
    orders["status"].eq("completed")
]
```

Conceptually:

```text
orders
  ↓
status == completed
  ↓
True / False mask
  ↓
Selected rows
```

Boolean filtering is the foundation of most Pandas row-selection logic.

## Multiple Conditions

Combine conditions with Pandas-compatible boolean operators:

```python
filtered = orders.loc[
    orders["status"].eq("completed")
    & orders["amount"].gt(1000)
]
```

Use:

```text
& → AND
| → OR
~ → NOT
```

Do not use Python's:

```text
and
or
not
```

for Series-based boolean conditions.

Parenthesize individual conditions:

```python
orders.loc[
    (
        orders["status"].eq("completed")
        & orders["amount"].gt(1000)
    )
]
```

This avoids Python operator-precedence mistakes.

## `isin`

`isin()` is useful when filtering against a set of allowed values.

```python
selected = orders.loc[
    orders["status"].isin(
        [
            "completed",
            "pending",
        ]
    )
]
```

It is generally clearer than a long sequence of equality comparisons.

It is especially useful for:

```text
Status sets
Region lists
Customer lists
Product categories
Allowlisted identifiers
```

## `query`

`query()` provides expression-oriented filtering:

```python
completed = orders.query(
    "status == 'completed' and amount > 1000"
)
```

It can improve readability for complex filtering expressions involving column names.

For example:

```python
result = orders.query(
    """
    status == 'completed'
    and amount >= 1000
    and quantity > 1
    """
)
```

Use it when the expression remains readable and the team is comfortable with the syntax.

Prefer ordinary boolean expressions when they are clearer or when programmatic expression construction would make `query()` difficult to maintain.

## `query` and External Variables

External values can be injected using `@`:

```python
minimum_amount = 1000

filtered = orders.query(
    "status == 'completed' "
    "and amount >= @minimum_amount"
)
```

This is useful for parameterized filtering inside Python code.

Keep externally supplied expressions out of dynamically assembled query strings when doing so could make behavior ambiguous or unsafe.

## Filtering Missing Values

Use `isna()` and `notna()` for explicit missing-value filtering.

```python
missing_amounts = orders.loc[
    orders["amount"].isna()
]
```

Non-missing records:

```python
valid_amounts = orders.loc[
    orders["amount"].notna()
]
```

Do not use:

```python
orders["amount"] == None
```

as the general missing-value test.

Pandas supports multiple missing-value representations, so dedicated missing-value APIs are more reliable.

## Indexing and Selection

Indexing should be understood as a semantic layer rather than simply a faster row lookup mechanism.

Important distinctions include:

```text
Index label
+
Row position
+
Column label
+
Boolean condition
```

For example:

```python
orders.loc[
    orders["customer_id"].eq("C-1001"),
    "amount",
]
```

uses:

```text
Rows → boolean condition
Column → label
```

while:

```python
orders.iloc[0, 3]
```

uses:

```text
Row → position
Column → position
```

The selection semantics should match the requirement.

## Setting Values

Use `.loc` for controlled conditional updates:

```python
orders.loc[
    orders["status"].eq("pending"),
    "status",
] = "awaiting_payment"
```

For multiple columns:

```python
mask = orders["amount"].lt(0)

orders.loc[
    mask,
    [
        "amount",
        "status",
    ],
] = [
    0,
    "invalid",
]
```

The key principle is:

```text
Build explicit selection
        ↓
Assign through .loc
```

This makes the mutation boundary visible.

## Selection and Mutation

Selection and mutation are related but should not be conflated.

For example:

```python
subset = orders.loc[
    orders["status"].eq("completed")
]

subset["amount"] = (
    subset["amount"] * 1.1
)
```

creates a separate object whose ownership and copy semantics should be considered.

For independent transformation logic, make intent explicit:

```python
subset = (
    orders.loc[
        orders["status"].eq("completed")
    ]
    .copy()
)
```

This avoids ambiguity around modifying a subset and aligns the ownership semantics with the transformation.

## Performance Principles

Selection should reduce data as early as practical.

Prefer:

```text
Filter early
Project early
Transform only required columns
```

For example:

```python
completed = orders.loc[
    orders["status"].eq("completed"),
    [
        "order_id",
        "customer_id",
        "amount",
    ],
]
```

This avoids carrying unnecessary columns through later transformations.

For database-backed workflows, apply the same idea at the SQL layer:

```text
PostgreSQL
    ↓
WHERE + SELECT
    ↓
Reduced result set
    ↓
Pandas
```

## Memory Considerations

Selecting fewer columns can reduce the DataFrame's memory footprint.

For large datasets:

```python
orders = orders.loc[
    :,
    [
        "order_id",
        "customer_id",
        "amount",
    ],
]
```

can be materially better than processing a wide DataFrame containing unrelated fields.

Measure memory when scale matters:

```python
memory_bytes = (
    orders
    .memory_usage(deep=True)
    .sum()
)
```

Selection is one of the simplest ways to reduce downstream memory and processing cost.

## Selection in ETL Pipelines

A typical ETL flow is:

```text
Raw Data
   ↓
Select required columns
   ↓
Filter relevant rows
   ↓
Normalize types
   ↓
Validate
   ↓
Transform
   ↓
Persist
```

For example:

```python
orders = raw_orders.loc[
    raw_orders["status"].isin(
        [
            "completed",
            "pending",
        ]
    ),
    [
        "order_id",
        "customer_id",
        "amount",
        "created_at",
    ],
]
```

This creates a narrower, semantically relevant working set.

## Selection in REST/API Processing

API responses often contain more fields than the downstream workflow requires.

After normalization:

```python
orders = orders.loc[
    :,
    [
        "order_id",
        "customer_id",
        "amount",
        "status",
    ],
]
```

This reduces:

```text
Memory
Processing
Accidental data exposure
Output schema drift
```

The same principle applies when preparing API responses.

## Selection in Reporting

Reports frequently require a specific business subset:

```python
report = orders.loc[
    orders["status"].eq("completed")
    & orders["amount"].gt(500),
    [
        "order_id",
        "customer_id",
        "amount",
    ],
]
```

Keep presentation-specific filtering near the reporting boundary rather than mutating the canonical dataset unnecessarily.

## Selection vs SQL

When the source is a relational database:

```python
orders = pd.read_sql_query(
    """
    SELECT
        order_id,
        customer_id,
        amount
    FROM orders
    WHERE status = %(status)s
    """,
    connection,
    params={
        "status": "completed",
    },
)
```

is usually preferable to loading all rows and then filtering in Pandas.

The principle is:

```text
Filter where the data lives
when the source system can do it efficiently.
```

Pandas remains useful for filtering after extraction when:

```text
The data is already in memory
The rule is Python-specific
The source is heterogeneous
The filter depends on transformed fields
```

## Readability vs Cleverness

This is technically valid:

```python
result = df.loc[
    (df["status"] == "completed")
    & (df["amount"] > 1000)
    & df["customer_id"].notna(),
    ["order_id", "amount"],
]
```

But for complex production logic, intermediate variables may be clearer:

```python
completed = orders["status"].eq(
    "completed"
)

high_value = orders["amount"].gt(
    1000
)

has_customer = orders[
    "customer_id"
].notna()

result = orders.loc[
    completed
    & high_value
    & has_customer,
    [
        "order_id",
        "amount",
    ],
]
```

Optimize for maintainability, not minimum line count.

## Common Selection Mistakes

### Using `iloc` for Semantic Selection

```python
orders.iloc[:, 3]
```

depends on column position.

**Better:** use the column label when the requirement is semantic:

```python
orders["amount"]
```

### Using Python `and` / `or`

Incorrect:

```python
orders[
    (orders["amount"] > 100)
    and (orders["status"] == "completed")
]
```

**Better:**

```python
orders.loc[
    (orders["amount"] > 100)
    & orders["status"].eq("completed")
]
```

### Forgetting Parentheses

Operator precedence can produce incorrect expressions.

**Better:** parenthesize each boolean condition.

### Treating the Index as a Primary Key

The DataFrame index is an indexing mechanism, not automatically a durable business identifier.

**Better:** preserve explicit business keys such as `order_id`.

### Selecting by Position After Column Reordering

This is fragile:

```python
df.iloc[:, 4]
```

when the schema can change.

**Better:** select named columns.

### Filtering After Loading Unnecessary Data

Loading hundreds of columns only to keep five wastes memory.

**Better:** project at ingestion or source-query time where possible.

### Building Giant Boolean Expressions

Very complex conditions can become difficult to debug.

**Better:** name important masks or encapsulate reusable predicates.

### Assigning Through Ambiguous Subsets

Code such as:

```python
subset = df[df["status"] == "pending"]
subset["amount"] = 0
```

can make mutation semantics unclear.

**Better:**

```python
df.loc[
    df["status"].eq("pending"),
    "amount",
] = 0
```

### Confusing Empty With Missing

These are different states:

```text
DataFrame with zero rows
```

versus:

```text
Rows containing missing values
```

**Better:** distinguish `df.empty` from `isna()` checks.

## Interview Traps

### What Is the Difference Between `loc` and `iloc`?

`loc` uses labels; `iloc` uses integer positions.

### When Should You Use `at` Instead of `loc`?

Use `at` for scalar label-based access when exactly one cell is needed.

### Why Does `isin()` Help With Multiple Values?

It expresses membership directly:

```python
orders["status"].isin(
    ["pending", "completed"]
)
```

and is clearer than repeatedly combining equality conditions.

### Why Are `and` and `or` Incorrect for Pandas Series?

Python's `and` and `or` operate on single truth values, while Pandas conditions are element-wise Series operations. Use `&`, `|`, and `~`.

### Why Is `df[condition]` Often Replaced by `df.loc[condition]`?

Both can filter rows, but `.loc` makes row and column selection explicit and is especially useful when performing conditional assignment.

### When Should Filtering Happen in SQL Instead of Pandas?

When the source is a database and it can efficiently perform the filter, especially for large datasets. This reduces network transfer and Pandas memory usage.

### What Is the Difference Between Row Label and Row Position?

A row label comes from the DataFrame index; a row position is its integer location. They can differ completely.

### Why Can Column Selection Affect Performance?

Carrying fewer columns reduces memory, processing, serialization, and often downstream transformation costs.

### Why Should IDs Often Be Selected by Label Rather Than Position?

Column positions can change as the schema evolves. Explicit labels make the code resilient to column reordering.

### How Do You Safely Update Rows Matching a Condition?

Use `.loc`:

```python
df.loc[
    condition,
    "column",
] = value
```

### Why Can Filtering and Assignment Produce Confusing Behavior?

Subsets can have copy/view semantics that depend on how they were produced and the current Pandas execution model. Make ownership explicit with `.copy()` when an independent object is required.

### How Do You Filter Missing Values?

Use:

```python
df.loc[df["amount"].isna()]
```

or:

```python
df.loc[df["amount"].notna()]
```

rather than relying on equality comparisons with `None`.

## Production Checklist

```text
[ ] Is the selection semantic or positional?
[ ] Are business keys explicit rather than hidden in the index?
[ ] Are required columns selected as early as practical?
[ ] Can filtering be pushed into SQL or another source system?
[ ] Are boolean expressions using &, |, and ~?
[ ] Are individual conditions parenthesized?
[ ] Are complex predicates named for readability?
[ ] Are missing values handled with isna() / notna()?
[ ] Are column labels preferred over positional selection when possible?
[ ] Is the resulting schema explicit?
[ ] Are sensitive columns excluded from downstream processing?
[ ] Is the DataFrame subset smaller before expensive transformations?
[ ] Are conditional assignments performed with .loc?
[ ] Is `.copy()` used when an independent working DataFrame is required?
[ ] Are empty datasets distinguished from datasets containing missing values?
[ ] Are cross-chunk/global uniqueness requirements understood?
[ ] Are selection operations tested against realistic edge cases?
[ ] Is memory usage measured for large DataFrames?
[ ] Are API, SQL, and reporting boundaries using explicit field selection?
```

## Key Takeaways

- Pandas selection has distinct semantics: use labels for semantic access, positions for inherently positional requirements, and boolean masks for row filtering.
- `.loc` is the central production-oriented selection tool because it combines label-based row selection, column projection, and safe conditional assignment.
- Filter and project as early as practical to reduce memory, CPU, network transfer, and accidental exposure of unnecessary data; push work into SQL when the database can execute it efficiently.
- Boolean filtering requires element-wise operators such as `&`, `|`, and `~`, while missing values should be handled through `isna()` and `notna()`.
- Treat selection as part of schema and correctness design: use explicit business keys, stable column labels, clear mutation boundaries, and tests for empty, missing, invalid, and evolving data.