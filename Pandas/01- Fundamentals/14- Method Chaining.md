# 14- Method Chaining

## Overview

Method chaining is the practice of applying a sequence of Pandas operations directly to the result of the previous operation.

Instead of creating many temporary variables:

```python
orders = pd.read_csv("orders.csv")

orders = orders[
    orders["status"] == "completed"
]

orders["amount"] = pd.to_numeric(
    orders["amount"],
    errors="coerce",
)

orders = orders[
    orders["amount"].notna()
]

orders = orders[
    [
        "order_id",
        "customer_id",
        "amount",
    ]
]

orders = orders.sort_values(
    "amount",
    ascending=False,
)
```

the same workflow can often be expressed as:

```python
orders = (
    pd.read_csv("orders.csv")
    .loc[lambda df: df["status"].eq("completed")]
    .assign(
        amount=lambda df: pd.to_numeric(
            df["amount"],
            errors="coerce",
        )
    )
    .loc[lambda df: df["amount"].notna()]
    .loc[
        :,
        [
            "order_id",
            "customer_id",
            "amount",
        ],
    ]
    .sort_values(
        "amount",
        ascending=False,
    )
)
```

The objective is not to make code shorter at any cost.

Good chaining makes a transformation pipeline:

- Easier to read.
- Easier to reason about.
- Easier to review.
- Less dependent on mutable intermediate state.
- Easier to test as a transformation pipeline.
- More explicit about operation order.

Poor chaining can do the opposite by producing excessively long, nested, or opaque expressions.

## Why Method Chaining Exists

Pandas methods generally return a Series or DataFrame that can become the input to another operation.

This supports a pipeline model:

```text
Input
  ↓
Filter
  ↓
Normalize
  ↓
Project
  ↓
Aggregate
  ↓
Sort
  ↓
Output
```

Method chaining makes that pipeline visible in the source code.

This is particularly useful in ETL and reporting code where the transformation sequence itself is the primary logic.

## Core Pattern

A basic chain looks like:

```python
result = (
    orders
    .dropna(subset=["order_id"])
    .assign(
        amount=lambda df: df["amount"] * 1.18
    )
    .sort_values("amount")
)
```

Each operation receives the result of the previous operation.

Conceptually:

```text
orders
  ↓
dropna()
  ↓
assign()
  ↓
sort_values()
  ↓
result
```

The parentheses allow the chain to be formatted vertically without explicit backslashes.

## Parentheses for Multi-Line Chains

Prefer:

```python
result = (
    orders
    .dropna(...)
    .assign(...)
    .sort_values(...)
)
```

over:

```python
result = orders \
    .dropna(...) \
    .assign(...) \
    .sort_values(...)
```

Implicit line continuation inside parentheses is clearer and follows normal Python formatting conventions.

## Common Chainable Operations

Many common Pandas operations naturally fit into chains:

| Operation | Typical purpose |
|---|---|
| `loc` | Filtering and selection |
| `iloc` | Positional selection |
| `assign()` | Adding or replacing columns |
| `rename()` | Renaming labels |
| `drop()` | Removing rows or columns |
| `dropna()` | Removing missing data |
| `fillna()` | Filling missing values |
| `astype()` | Type conversion |
| `sort_values()` | Sorting rows |
| `groupby()` | Grouped processing |
| `agg()` | Aggregation |
| `merge()` | Combining DataFrames |
| `query()` | Expression-based filtering |
| `melt()` | Wide-to-long transformation |
| `pipe()` | Passing data through custom functions |

The most useful chains normally contain a small number of logically related steps.

## `assign()` in Method Chains

`assign()` is one of the most useful methods for readable transformations.

Example:

```python
orders = (
    orders
    .assign(
        gross_amount=lambda df: (
            df["amount"] + df["tax"]
        ),
        net_amount=lambda df: (
            df["amount"] - df["discount"]
        ),
    )
)
```

The lambda receives the DataFrame at that stage of the chain.

This allows newly created columns to depend on columns already available in the same `assign()` call.

For example:

```python
orders = (
    orders
    .assign(
        subtotal=lambda df: (
            df["quantity"] * df["unit_price"]
        ),
        total=lambda df: (
            df["subtotal"] + df["shipping_fee"]
        ),
    )
)
```

This is useful when each transformation has a clear semantic name.

## `assign()` vs Direct Assignment

Direct assignment:

```python
orders["total"] = (
    orders["amount"]
    + orders["shipping_fee"]
)
```

is often clearer when the DataFrame is already local and mutable.

A chained transformation:

```python
orders = (
    orders
    .assign(
        total=lambda df: (
            df["amount"]
            + df["shipping_fee"]
        )
    )
)
```

is useful when the transformation is intentionally expressed as a pipeline.

Neither approach is universally better.

Use the form that makes ownership and transformation order easiest to understand.

## `loc` Inside a Chain

Use `loc` for explicit row and column selection:

```python
completed = (
    orders
    .loc[
        orders["status"].eq("completed")
    ]
)
```

For a more complex expression, a lambda can keep the entire operation inside the chain:

```python
completed = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
)
```

This is useful when the DataFrame name should not be referenced repeatedly.

## Multiple Filters

A production-style filter can be expressed as:

```python
filtered = (
    orders
    .loc[
        lambda df: (
            df["status"].eq("completed")
            & df["amount"].gt(100)
            & df["customer_id"].notna()
        )
    ]
)
```

The parentheses make Boolean precedence explicit.

Avoid overly compressed expressions that require the reader to mentally parse many conditions at once.

## `query()` in Chains

`query()` can improve readability for suitable expressions:

```python
filtered = (
    orders
    .query(
        "status == 'completed' and amount > 100"
    )
)
```

It is useful when the condition is simple and column names work naturally with the query expression syntax.

For complex or reusable conditions, boolean masks may be clearer:

```python
filtered = (
    orders
    .loc[
        lambda df: (
            df["status"].eq("completed")
            & df["amount"].gt(100)
        )
    ]
)
```

Use `query()` because it improves readability, not simply because it is shorter.

## `rename()` in Chains

Column normalization fits naturally into a chain:

```python
normalized = (
    orders
    .rename(
        columns={
            "customerId": "customer_id",
            "orderAmount": "amount",
        }
    )
)
```

When exact source-to-target mappings are known, explicit renaming is preferable to broad string manipulation because it makes the contract visible.

## `astype()` in Chains

Type normalization can be part of a chain:

```python
normalized = (
    orders
    .assign(
        customer_id=lambda df: (
            pd.to_numeric(
                df["customer_id"],
                errors="coerce",
            ).astype("Int64")
        ),
        status=lambda df: (
            df["status"]
            .astype("string")
            .str.strip()
            .str.lower()
        ),
    )
)
```

This keeps representation changes close to the stage where they are introduced.

## Missing-Value Handling in Chains

For example:

```python
cleaned = (
    orders
    .dropna(
        subset=[
            "order_id",
            "customer_id",
        ]
    )
    .assign(
        discount=lambda df: (
            df["discount"]
            .fillna(0)
        )
    )
)
```

The order matters.

Dropping required identifiers first and filling an optional discount afterward expresses different business semantics than applying a blanket `fillna()`.

## String Transformations in Chains

String normalization works well as a readable chain:

```python
normalized = (
    orders
    .assign(
        status=lambda df: (
            df["status"]
            .astype("string")
            .str.strip()
            .str.lower()
        )
    )
)
```

This is preferable to repeatedly mutating the same column through multiple statements when the transformation is simple and logically belongs together.

## Datetime Transformations in Chains

Example:

```python
prepared = (
    orders
    .assign(
        created_at=lambda df: (
            pd.to_datetime(
                df["created_at"],
                utc=True,
            )
        )
    )
    .loc[
        lambda df: (
            df["created_at"]
            >= start_date
        )
    ]
)
```

Parsing before filtering ensures the comparison uses datetime semantics rather than string comparison.

## Sorting in Chains

Sorting is straightforward:

```python
top_orders = (
    orders
    .sort_values(
        "amount",
        ascending=False,
    )
    .head(100)
)
```

The chain expresses:

```text
Sort by amount
    ↓
Take first 100
```

This is clearer than creating an intermediate sorted DataFrame when the sorted object has no independent purpose.

## Grouping and Aggregation

A common reporting pipeline is:

```python
customer_summary = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        order_count=("order_id", "count"),
        revenue=("amount", "sum"),
        average_order=("amount", "mean"),
    )
    .sort_values(
        "revenue",
        ascending=False,
    )
)
```

The entire business transformation is visible:

```text
Filter completed orders
        ↓
Group by customer
        ↓
Calculate metrics
        ↓
Sort by revenue
```

This is an excellent use of method chaining because each stage has a clear responsibility.

## Merge in a Chain

Joins can also participate in a pipeline:

```python
customer_orders = (
    orders
    .merge(
        customers[
            [
                "customer_id",
                "customer_name",
                "segment",
            ]
        ],
        on="customer_id",
        how="left",
        validate="many_to_one",
    )
)
```

The important production consideration is cardinality validation.

A chain should not hide potentially dangerous row multiplication.

## Chain Ordering Matters

Method chains are executed top-to-bottom.

Consider:

```python
result = (
    orders
    .dropna(subset=["amount"])
    .assign(
        amount_with_tax=lambda df: (
            df["amount"] * 1.18
        )
    )
)
```

versus:

```python
result = (
    orders
    .assign(
        amount_with_tax=lambda df: (
            df["amount"] * 1.18
        )
    )
    .dropna(
        subset=["amount"]
    )
)
```

These may produce different intermediate behavior and memory usage.

More importantly, a step may depend on a column created by a previous step.

Method order is therefore part of the transformation specification.

## Avoid Repeated Expensive Work

A readable chain should still avoid doing expensive operations unnecessarily.

Prefer:

```python
result = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
    [
        [
            "order_id",
            "customer_id",
            "amount",
        ]
    ]
)
```

rather than performing expensive transformations on columns that will later be discarded.

For large data, filter and project early when the semantics allow it.

## Method Chaining and Data Reduction

A typical efficient pipeline can be:

```text
Source
  ↓
Filter rows
  ↓
Select required columns
  ↓
Normalize dtypes
  ↓
Transform
  ↓
Aggregate
  ↓
Write
```

This limits the amount of data processed by later stages.

For example:

```python
summary = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        ),
        [
            "customer_id",
            "amount",
        ],
    ]
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum")
    )
)
```

Only required rows and columns enter the aggregation stage.

## `pipe()`

`pipe()` is useful when the chain needs to call reusable custom functions.

Example:

```python
def normalize_orders(
    df: pd.DataFrame,
) -> pd.DataFrame:
    return (
        df
        .assign(
            status=lambda frame: (
                frame["status"]
                .astype("string")
                .str.strip()
                .str.lower()
            )
        )
    )


def validate_orders(
    df: pd.DataFrame,
) -> pd.DataFrame:
    if df["order_id"].isna().any():
        raise ValueError(
            "Missing order_id"
        )

    return df
```

These functions can be composed:

```python
processed = (
    orders
    .pipe(normalize_orders)
    .pipe(validate_orders)
)
```

This allows application-specific logic to participate in the same pipeline without forcing everything into anonymous lambdas.

## Passing Arguments with `pipe()`

Use a tuple when the DataFrame should not be the first positional argument:

```python
def add_currency(
    currency: str,
    df: pd.DataFrame,
) -> pd.DataFrame:
    return df.assign(
        currency=currency,
    )
```

Then:

```python
processed = (
    orders
    .pipe(
        add_currency,
        "INR",
    )
)
```

This keeps configurable transformations readable.

## Why `pipe()` Matters in Production

Large ETL chains often contain domain-specific operations such as:

```text
normalize_schema()
validate_required_fields()
standardize_currency()
calculate_metrics()
apply_business_rules()
```

Embedding all of these inside one enormous chain makes maintenance difficult.

Instead:

```python
processed = (
    orders
    .pipe(normalize_schema)
    .pipe(validate_required_fields)
    .pipe(apply_business_rules)
    .pipe(build_metrics)
)
```

The chain now describes the pipeline architecture, while each function owns a focused transformation.

## Method Chaining and Testability

Small transformation functions are easier to unit test:

```python
def normalize_status(
    df: pd.DataFrame,
) -> pd.DataFrame:
    return df.assign(
        status=lambda frame: (
            frame["status"]
            .astype("string")
            .str.strip()
            .str.lower()
        )
    )
```

Test the function independently:

```python
def test_normalize_status():
    source = pd.DataFrame(
        {
            "status": [
                " Completed ",
                "Pending",
            ]
        }
    )

    result = normalize_status(
        source
    )

    expected = pd.DataFrame(
        {
            "status": [
                "completed",
                "pending",
            ]
        }
    )

    pd.testing.assert_frame_equal(
        result,
        expected,
    )
```

Then test the overall pipeline separately.

This gives a useful distinction:

```text
Unit tests
    ↓
Individual transformation

Pipeline tests
    ↓
Transformation ordering and integration
```

## Readability vs Compression

Consider:

```python
result = (
    orders
    .query("status == 'completed'")
    .assign(
        amount=lambda df: pd.to_numeric(
            df["amount"],
            errors="coerce",
        )
    )
    .dropna(subset=["amount"])
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum")
    )
    .sort_values(
        "revenue",
        ascending=False,
    )
)
```

This is reasonably readable because each line represents one meaningful stage.

Avoid compressing it into a dense expression such as:

```python
result = orders.query("status == 'completed'").assign(amount=lambda d: pd.to_numeric(d["amount"], errors="coerce")).dropna(subset=["amount"]).groupby("customer_id", as_index=False).agg(revenue=("amount", "sum")).sort_values("revenue", ascending=False)
```

Fewer characters do not necessarily mean better code.

## When to Break a Chain

Break the chain when an intermediate result has independent meaning.

For example:

```python
completed_orders = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
)

customer_summary = (
    completed_orders
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum")
    )
)
```

This is often better than one very long chain when:

- The intermediate dataset has a business meaning.
- Multiple downstream calculations use it.
- Debugging requires inspecting the intermediate result.
- A transformation has become difficult to understand.
- A stage needs separate tests or metrics.

## Named Intermediate DataFrames

Readable intermediate names are often more valuable than maximum chaining.

For example:

```python
clean_orders = (
    orders
    .dropna(
        subset=["order_id"]
    )
)

normalized_orders = (
    clean_orders
    .assign(
        status=lambda df: (
            df["status"]
            .astype("string")
            .str.lower()
        )
    )
)

customer_summary = (
    normalized_orders
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum")
    )
)
```

The names document the state of the pipeline.

## Method Chaining and Debugging

Long chains can make debugging harder because intermediate states are not directly named.

A practical debugging technique is to temporarily split the chain:

```python
filtered = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
)

normalized = (
    filtered
    .assign(
        amount=lambda df: pd.to_numeric(
            df["amount"],
            errors="coerce",
        )
    )
)

result = (
    normalized
    .dropna(subset=["amount"])
)
```

Once behavior is verified, the stages can be recombined if the resulting chain remains readable.

## Method Chaining and Logging

Do not log the entire DataFrame at every stage.

Instead, capture metadata:

```python
logger.info(
    "after_normalization rows=%d columns=%d",
    normalized.shape[0],
    normalized.shape[1],
)
```

For data-quality diagnostics:

```python
logger.info(
    "after_validation rows=%d null_amounts=%d",
    len(validated),
    validated["amount"].isna().sum(),
)
```

This keeps logs useful without exposing potentially sensitive records.

## Method Chaining and Performance

A method chain does not automatically make code faster.

For example:

```python
result = (
    orders
    .assign(...)
    .assign(...)
    .assign(...)
)
```

may create several intermediate results depending on the operations and Pandas execution behavior.

Conversely, a chain can make efficient data reduction easier to express:

```python
result = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        ),
        [
            "customer_id",
            "amount",
        ],
    ]
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum")
    )
)
```

The performance lesson is:

```text
Readable pipeline
+
Appropriate operation order
+
Controlled data volume
+
Measured workload
```

not "method chaining is faster".

## Method Chaining and Memory

Chaining can produce temporary intermediate objects.

For large DataFrames, consider:

- Filtering early.
- Selecting columns early.
- Avoiding unnecessary copies.
- Avoiding repeated transformations.
- Using appropriate dtypes.
- Processing in chunks.
- Pushing filtering and aggregation into PostgreSQL when practical.
- Using Parquet column projection.
- Measuring actual peak memory.

A visually elegant chain can still exceed a Kubernetes pod's memory limit if it processes an unnecessarily large working set.

## Method Chaining with Large Inputs

For chunked CSV processing:

```python
for chunk in pd.read_csv(
    "orders.csv",
    chunksize=100_000,
):
    result = (
        chunk
        .loc[
            lambda df: df["status"].eq(
                "completed"
            ),
            [
                "customer_id",
                "amount",
            ],
        ]
        .groupby(
            "customer_id",
            as_index=False,
        )
        .agg(
            revenue=("amount", "sum")
        )
    )

    write_result(result)
```

The chain is applied per bounded batch.

This is usually preferable to constructing one enormous DataFrame when the input can exceed worker memory.

## Method Chaining in API Pipelines

For API records:

```python
orders = pd.json_normalize(
    payload["orders"]
)

processed = (
    orders
    .assign(
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
    .loc[
        lambda df: df["order_id"].notna()
    ]
)
```

The network layer should remain separate from the transformation layer.

Do not put HTTP requests, retry loops, or authentication logic inside a Pandas method chain.

## Method Chaining and SQL Pipelines

When data originates from PostgreSQL:

```python
orders = pd.read_sql_query(
    query,
    connection,
)

summary = (
    orders
    .loc[
        lambda df: df["status"].eq(
            "completed"
        )
    ]
    .groupby(
        "customer_id",
        as_index=False,
    )
    .agg(
        revenue=("amount", "sum")
    )
)
```

But consider whether the grouping and aggregation should happen in SQL:

```sql
SELECT
    customer_id,
    SUM(amount) AS revenue
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;
```

For large relational datasets, pushing computation into PostgreSQL can reduce network transfer and Pandas memory consumption.

Pandas should not automatically become the execution engine for work the database can perform more efficiently.

## Method Chaining and Reusable Domain Functions

A mature codebase can keep chains at the orchestration level:

```python
report = (
    orders
    .pipe(normalize_order_schema)
    .pipe(validate_orders)
    .pipe(filter_billable_orders)
    .pipe(build_customer_metrics)
    .pipe(format_report)
)
```

Each function can have a narrow responsibility.

This is often a better architecture than one 30-line chain containing every transformation.

## Chain Design Guidelines

A useful production standard is:

```text
One chain
    ↓
One coherent transformation

Each method
    ↓
One understandable operation

Complex business rule
    ↓
Named function

Multiple consumers
    ↓
Named intermediate DataFrame

Large dataset
    ↓
Reduce rows/columns early

Shared pipeline
    ↓
Use pipe() for reusable stages
```

## Common Mistakes

### Chaining Everything Just Because You Can

A 20-step chain may be technically valid but difficult to debug and review.

**Better:** chain coherent transformations and extract named functions or intermediate DataFrames when complexity grows.

### Optimizing for Few Lines of Code

Shorter code is not automatically better.

**Better:** optimize for readability, correctness, and maintainability.

### Hiding Complex Business Rules in Lambdas

For example:

```python
.assign(
    score=lambda df: (
        ...
        complex business logic ...
    )
)
```

can become difficult to test.

**Better:** extract the logic into a named function and use `pipe()`.

### Creating Excessive Intermediate Copies

A chain does not eliminate memory costs.

**Better:** inspect operation order and avoid unnecessary copying or duplicated columns.

### Assuming Chaining Is Faster

Method chaining is primarily a code-organization technique.

**Better:** optimize based on operation complexity, data volume, memory, and measured benchmarks.

### Filtering Too Late

Processing unnecessary rows through expensive transformations wastes CPU and memory.

**Better:** filter early when business semantics allow it.

### Selecting Columns Too Late

Carrying dozens of unused columns through a pipeline increases memory and processing requirements.

**Better:** project required columns early.

### Hiding Join Cardinality

This chain:

```python
orders.merge(
    customers,
    on="customer_id",
)
```

can multiply rows if the relationship is not what was expected.

**Better:** use `validate="many_to_one"` or the appropriate cardinality constraint.

### Mixing I/O and Transformation Logic

Putting network calls, database calls, and Pandas transformations into one chain creates poor separation of concerns.

**Better:** isolate extraction from transformation.

### Losing Intermediate Business Meaning

A single huge expression can make it difficult to identify concepts such as:

```text
validated_orders
billable_orders
customer_summary
```

**Better:** name meaningful intermediate datasets.

### Ignoring Debugging and Observability

Long chains can make production failures harder to localize.

**Better:** add stage-level metrics and use `pipe()` functions that can be tested independently.

### Mutating Shared Inputs Unintentionally

A pipeline that mixes direct assignment and chained transformations can make ownership unclear.

**Better:** define whether functions mutate inputs or return independent results.

## Interview Traps

### Does Method Chaining Improve Performance?

Not inherently. It primarily improves expression and organization of transformations. Performance depends on the operations, data size, dtypes, memory pressure, and execution paths.

### Why Use `assign()` in a Chain?

It allows readable column creation or replacement while returning a DataFrame that can continue through the chain.

### Why Use `pipe()`?

`pipe()` allows reusable domain-specific functions to participate in a Pandas pipeline without forcing all logic into inline lambdas.

### When Should You Break a Method Chain?

When an intermediate result has independent business meaning, needs separate testing, is reused, requires debugging, or makes the chain difficult to understand.

### How Does Method Chaining Affect Memory?

Chaining does not eliminate intermediate allocations. Some operations can create new objects, so large pipelines still require memory analysis and careful operation ordering.

### How Can You Reduce Memory in a Pandas Chain?

Filter rows early, project required columns early, use appropriate dtypes, avoid unnecessary copies, process in chunks, and push suitable computation into databases or other execution engines.

### Is `query()` Always Better Than Boolean Indexing?

No. `query()` can improve readability for simple expressions, while boolean masks are often clearer for complex conditions and allow direct use of Series methods.

### Why Are Lambda Functions Common in `assign()` and `loc()` Chains?

They receive the current DataFrame at that point in the chain, allowing the expression to refer to columns without relying on an external DataFrame variable.

### How Would You Test a Chained Transformation?

Test focused transformation functions independently with `pd.testing.assert_frame_equal()` and add pipeline-level tests for ordering, integration, validation, and edge cases.

### Should API Requests Be Performed Inside a Pandas Chain?

No. HTTP transport concerns such as retries, authentication, timeouts, and pagination belong in the extraction layer, while the Pandas chain should operate on already retrieved data.

## Production Example

A practical order-processing pipeline can be structured as:

```python
def normalize_orders(
    df: pd.DataFrame,
) -> pd.DataFrame:
    return (
        df
        .assign(
            status=lambda frame: (
                frame["status"]
                .astype("string")
                .str.strip()
                .str.lower()
            ),
            amount=lambda frame: (
                pd.to_numeric(
                    frame["amount"],
                    errors="coerce",
                ).astype("Float64")
            ),
        )
    )


def validate_orders(
    df: pd.DataFrame,
) -> pd.DataFrame:
    required = [
        "order_id",
        "customer_id",
        "amount",
    ]

    invalid = (
        df[required]
        .isna()
        .any(axis=1)
    )

    if invalid.any():
        raise ValueError(
            "Required order fields are missing"
        )

    if df["amount"].lt(0).any():
        raise ValueError(
            "Order amount cannot be negative"
        )

    return df


def build_customer_report(
    df: pd.DataFrame,
) -> pd.DataFrame:
    return (
        df
        .loc[
            lambda frame: (
                frame["status"].eq(
                    "completed"
                )
            )
        ]
        .groupby(
            "customer_id",
            as_index=False,
        )
        .agg(
            order_count=("order_id", "count"),
            revenue=("amount", "sum"),
        )
        .sort_values(
            "revenue",
            ascending=False,
        )
    )


report = (
    orders
    .pipe(normalize_orders)
    .pipe(validate_orders)
    .pipe(build_customer_report)
)
```

The code communicates the pipeline architecture directly:

```text
Raw DataFrame
    ↓
Normalize
    ↓
Validate
    ↓
Filter Completed Orders
    ↓
Aggregate by Customer
    ↓
Sort
    ↓
Report
```

This is a strong use of method chaining because each function represents a meaningful transformation boundary.

## Operational Checklist

```text
[ ] Does the chain represent one coherent transformation?
[ ] Is every stage understandable without mentally expanding nested expressions?
[ ] Are complex business rules extracted into named functions?
[ ] Are independent intermediate datasets given meaningful names?
[ ] Is assign() being used for readable column transformations?
[ ] Is pipe() being used for reusable domain-specific stages?
[ ] Are rows filtered early where appropriate?
[ ] Are unused columns projected out early?
[ ] Are dtypes normalized before dependent operations?
[ ] Are join cardinalities validated?
[ ] Are missing-value rules explicit?
[ ] Is input mutation behavior clear?
[ ] Could intermediate operations create significant memory pressure?
[ ] Is the chain processing more data than necessary?
[ ] Could PostgreSQL or another system execute part of the workload more efficiently?
[ ] Should large inputs be processed in chunks?
[ ] Are stage-level metrics available for debugging?
[ ] Are transformation functions individually testable?
[ ] Are empty and malformed inputs tested?
[ ] Is the chain readable enough for production code review?
```

## Key Takeaways

- Method chaining expresses Pandas transformations as an ordered pipeline and is most valuable when each stage has a clear, readable responsibility.
- `assign()`, `loc()`, `query()`, and `pipe()` are especially useful for building maintainable transformation pipelines without excessive mutable intermediate state.
- Method chaining does not inherently improve performance; operation order, early data reduction, dtype selection, memory usage, and source-side computation remain the important optimization factors.
- Complex business rules, reused intermediate datasets, and difficult-to-debug pipelines should be extracted into named functions or intermediate DataFrames rather than forced into one long chain.
- Production Pandas chains should separate I/O from transformation, make ownership and validation explicit, preserve observability, and remain testable at both transformation and pipeline levels.