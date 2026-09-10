# 13- Copying Data

## Overview

Copying data in Pandas is primarily about **ownership, isolation, memory, and mutation semantics**.

This becomes important when multiple variables or pipeline stages refer to the same DataFrame or Series. A transformation may unintentionally affect another part of the application if object ownership is not understood.

The core distinction is:

```text
Reference
    ↓
Same Pandas object

Shallow copy
    ↓
New container
    ↓
Potentially shared underlying data

Deep copy
    ↓
New container
    ↓
Independent copied data
```

In modern Pandas, copy-on-write behavior can change when physical copies are made, but application code should still express ownership intent explicitly rather than depending on undocumented internals.

Copying matters particularly in:

- ETL pipelines.
- Data-cleaning functions.
- Batch processing.
- API processing.
- Background Celery jobs.
- Notebook or exploratory workflows.
- Tests.
- Reusable transformation libraries.

The goal is not to copy everything. The goal is to copy **when independent ownership is required** and avoid unnecessary copies when it is not.

## Assignment Does Not Copy

Consider:

```python
import pandas as pd

orders = pd.DataFrame(
    {
        "order_id": [1001, 1002],
        "amount": [250.0, 175.5],
    }
)

processed = orders
```

Now:

```text
orders    ─────┐
               ├── same DataFrame object
processed ─────┘
```

The assignment creates another reference to the same object.

You can verify identity:

```python
assert orders is processed
```

Changing the DataFrame through one reference changes the same object observed through the other reference.

## Why Assignment Sharing Matters

This is easy to write:

```python
def normalize_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    orders["amount"] = (
        orders["amount"]
        .fillna(0)
    )

    return orders
```

The function may be modifying the caller's DataFrame.

If callers expect transformation isolation, this can create hidden coupling.

A production function should make its mutation contract explicit.

## Mutation Contract

A transformation function should have one clear contract:

```text
Mutates input
OR
Returns an independent result
```

Avoid ambiguous behavior.

For example, an API such as:

```python
def clean_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    ...
```

should have documented or obvious ownership semantics.

A reusable library function often benefits from non-mutating behavior:

```python
def clean_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    result = orders.copy()

    result["status"] = (
        result["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    return result
```

The caller can then decide whether the returned DataFrame replaces the original.

## `DataFrame.copy()`

The standard explicit copy API is:

```python
copied = orders.copy()
```

For a Series:

```python
amounts_copy = orders["amount"].copy()
```

This communicates:

```text
The caller wants independent object ownership.
```

It is preferable to relying on accidental copying caused by another operation.

## Deep Copy

`copy()` accepts a `deep` parameter:

```python
copied = orders.copy(
    deep=True
)
```

`deep=True` is the default.

The important practical point is that Pandas' notion of a deep copy is not identical to recursively copying arbitrary Python objects stored inside the DataFrame.

For ordinary numeric, string, datetime, and other native Pandas data, `deep=True` provides independent Pandas data storage semantics appropriate for common use cases.

For object-dtype columns containing mutable Python objects, deeper recursive copying may require application-specific handling.

## Shallow Copy

A shallow copy can be requested with:

```python
copied = orders.copy(
    deep=False
)
```

This creates a new Pandas container while allowing the underlying data representation to be shared depending on the active copy semantics.

Shallow copying can be useful when structural independence is sufficient.

However, it is a more advanced optimization and should not be used casually.

When correctness requires isolated data ownership, prefer:

```python
orders.copy()
```

## Comparison of Copy Strategies

| Operation | New Pandas object | Independent data storage | Typical use |
|---|---:|---:|---|
| `new = old` | No | No | Shared reference |
| `old.copy()` | Yes | Yes for normal Pandas data | Independent working copy |
| `old.copy(deep=False)` | Yes | May share data | Advanced memory optimization |
| Rebuilding manually | Yes | Depends | Explicit schema transformation |
| `copy.deepcopy(old)` | Yes | Recursively attempts deeper Python copying | Object-rich structures; use selectively |

For normal DataFrame processing, `.copy()` is the clearest default when isolation is required.

## Copying a Series

The same concepts apply to Series:

```python
amounts = orders["amount"]

independent_amounts = amounts.copy()
```

The copied Series retains:

- Values.
- Index.
- Name.
- Dtype.

For example:

```python
assert (
    independent_amounts.name
    == amounts.name
)

assert (
    independent_amounts.dtype
    == amounts.dtype
)
```

## Copying Before Transformation

A common production pattern is:

```python
def normalize_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    result = orders.copy()

    result["status"] = (
        result["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    return result
```

The flow is:

```text
Caller DataFrame
      ↓
Explicit copy
      ↓
Transformation
      ↓
Independent result
```

This is appropriate when the function should not mutate caller-owned state.

## Copying at Pipeline Boundaries

For multi-stage processing:

```text
Raw data
   ↓
Cleaning
   ↓
Normalization
   ↓
Transformation
   ↓
Aggregation
```

the question is not whether every stage should copy.

Instead ask:

```text
Who owns this object?
Who will mutate it?
Does another consumer need the original state?
```

A pipeline may intentionally mutate a local DataFrame within a single stage:

```python
df["status"] = (
    df["status"]
    .astype("string")
)
```

without copying first.

The copy becomes important when the same object has multiple independent consumers or when a function promises non-mutating behavior.

## Example: Independent Pipeline Branches

Suppose one DataFrame feeds two reports:

```python
orders = load_orders()

finance_orders = orders.copy()
operations_orders = orders.copy()

finance_report = build_finance_report(
    finance_orders
)

operations_report = build_operations_report(
    operations_orders
)
```

Each branch can evolve independently.

Without deliberate ownership boundaries, mutations in one branch can produce unexpected effects in another.

## Avoid Copying Everything

This pattern is often unnecessarily expensive:

```python
df = source.copy()
df = df.copy()
df = df.copy()
df = df.copy()
```

For large DataFrames, unnecessary copies can cause:

- Higher peak memory.
- Longer processing time.
- More garbage collection pressure.
- Reduced worker concurrency.
- Container or pod memory exhaustion.

For example, a Kubernetes worker processing multiple large batches may fail because several full DataFrame copies temporarily coexist.

## Peak Memory Is More Important Than Final Memory

Suppose:

```text
Original DataFrame → 4 GB
Copy               → 4 GB
Temporary result   → 2 GB
```

The process may temporarily require substantially more than the final output size.

This matters for:

- Docker memory limits.
- Kubernetes pod limits.
- AWS batch workers.
- Celery worker concurrency.
- EC2 memory sizing.

A pipeline can therefore fail during an intermediate copy even if the final DataFrame would fit comfortably in memory.

## Copying and Method Chains

Method chaining can reduce explicit intermediate objects:

```python
cleaned = (
    orders
    .assign(
        status=lambda df: (
            df["status"]
            .astype("string")
            .str.strip()
            .str.lower()
        )
    )
    .dropna(
        subset=["order_id"]
    )
)
```

This can be readable and avoids manually creating multiple named copies.

However, method chaining does not guarantee zero copying. Pandas may create intermediate results internally.

The correct goal is clear transformation logic with reasonable memory behavior, not eliminating every temporary object.

## Copy vs View

Historically, Pandas operations could sometimes return objects that shared underlying data with their source.

This led to difficult questions such as:

```text
Did this selection create a copy?
Did this assignment modify the original?
```

Modern Pandas includes copy-on-write behavior, which makes many of these cases more predictable by deferring physical copies until mutation requires them.

The production rule remains:

```text
Do not depend on accidental aliasing.
Express ownership explicitly.
```

Use:

```python
result = source.copy()
```

when isolation is part of the contract.

## Avoid Relying on Internal Memory Details

Code should not depend on assumptions such as:

```text
This operation is always a view.
This operation is always a copy.
This particular array is always shared.
```

These details can vary with:

- Pandas version.
- Dtype.
- Operation.
- Data manager implementation.
- Copy-on-write configuration.
- Backend storage details.

Application code should depend on documented behavior and explicit ownership requirements.

## Copy and Column Selection

Consider:

```python
amounts = orders["amount"]
```

This produces a Series associated with the DataFrame.

When the Series is intended as an independent working object:

```python
amounts = orders[
    "amount"
].copy()
```

This is clearer than relying on implicit behavior.

## Copying Selected Columns

For an independent subset:

```python
working = orders[
    [
        "order_id",
        "amount",
        "status",
    ]
].copy()
```

This is especially useful when the subset will be modified independently.

For example:

```python
working["amount"] = (
    working["amount"]
    .fillna(0)
)
```

The original DataFrame remains available in its prior state.

## Copying Filtered Data

A filtered DataFrame can be turned into an explicitly independent working object:

```python
completed = orders.loc[
    orders["status"].eq("completed")
].copy()
```

This is a useful pattern when the filtered result will be transformed further.

The copy communicates:

```text
This subset now has independent ownership.
```

## Copying During ETL

An ETL stage may intentionally create an isolated working set:

```python
def prepare_for_reporting(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    report = orders[
        [
            "order_id",
            "customer_id",
            "amount",
            "status",
        ]
    ].copy()

    report["status"] = (
        report["status"]
        .astype("string")
        .str.lower()
    )

    return report
```

This makes the reporting transformation independent from the source DataFrame.

## When Not to Copy

Avoid a copy when:

- The function exclusively owns the input.
- The input is a local temporary object.
- Mutation is intentionally part of the function contract.
- The DataFrame is extremely large and isolation provides no benefit.
- A transformation already creates the necessary independent result.
- Memory pressure makes another full copy unsafe.

For example:

```python
def process_chunk(
    chunk: pd.DataFrame,
) -> None:
    chunk["status"] = (
        chunk["status"]
        .astype("string")
    )

    write_chunk(chunk)
```

If `chunk` is newly created for this processing iteration and no other code owns it, copying first may add unnecessary cost.

## Copy at Ownership Boundaries

A useful engineering rule is:

```text
External shared object
        ↓
Need isolation?
   ┌────┴────┐
  No        Yes
   ↓          ↓
Use object  copy()
directly      ↓
            mutate safely
```

Ownership boundaries often occur at:

- Public library APIs.
- Service-layer functions.
- ETL stages.
- Pipeline branches.
- Tests.
- Background job boundaries.

## Copying and Function Design

Consider a function with explicit non-mutating behavior:

```python
def add_net_amount(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    result = orders.copy()

    result["net_amount"] = (
        result["amount"]
        - result["discount"]
    )

    return result
```

The caller can safely retain:

```python
orders
```

and use:

```python
updated = add_net_amount(
    orders
)
```

without expecting the original DataFrame to gain a new column.

An alternative design can intentionally mutate:

```python
def add_net_amount_in_place(
    orders: pd.DataFrame,
) -> None:
    orders["net_amount"] = (
        orders["amount"]
        - orders["discount"]
    )
```

The explicit contract is easier to maintain than ambiguous behavior.

## Copying and Testing

Tests should verify that mutation does or does not occur as intended.

For a non-mutating function:

```python
def test_normalize_orders_does_not_mutate_input():
    source = pd.DataFrame(
        {
            "order_id": [1001],
            "status": [" Completed "],
        }
    )

    original = source.copy()

    result = normalize_orders(
        source
    )

    pd.testing.assert_frame_equal(
        source,
        original,
    )

    assert (
        result.loc[0, "status"]
        == "completed"
    )
```

This tests both:

```text
Output behavior
Input ownership contract
```

## Copying and DataFrame Equality

Use:

```python
pd.testing.assert_frame_equal(
    actual,
    expected,
)
```

rather than only:

```python
assert actual.equals(expected)
```

when the test needs detailed DataFrame contract validation.

The Pandas testing utilities can validate:

- Values.
- Index.
- Columns.
- Dtypes.
- Names.
- Other DataFrame metadata.

This is valuable when copy behavior and schema preservation matter.

## Copying Object-Dtype Data

The most important limitation of standard Pandas deep copying appears with object-dtype columns containing mutable Python objects.

Example:

```python
orders = pd.DataFrame(
    {
        "metadata": [
            {"priority": "high"},
            {"priority": "low"},
        ]
    }
)
```

A normal Pandas copy does not necessarily recursively duplicate every nested Python object inside an object-dtype column.

If the application mutates nested Python objects, explicit recursive copying may be required:

```python
import copy

metadata_copy = copy.deepcopy(
    orders["metadata"].tolist()
)
```

This is an advanced case and can be expensive.

Prefer normalized tabular structures over deeply nested mutable Python objects when practical.

## Copying and Serialization

Serialization can naturally create independent representations:

```python
payload = orders.to_dict(
    orient="records"
)
```

but this should not be treated as a general-purpose copy mechanism.

Serialization changes representation and may:

- Lose dtype details.
- Convert timestamps.
- Change missing-value representations.
- Consume significantly more memory.
- Be substantially slower.

Use `.copy()` when the requirement is specifically DataFrame ownership isolation.

## Copying and Database Loads

A DataFrame loaded from PostgreSQL is often already a newly materialized object:

```python
orders = pd.read_sql_query(
    query,
    connection,
)
```

Immediately copying it again:

```python
orders_copy = orders.copy()
```

may be unnecessary unless another processing branch requires independent ownership.

Avoid defensive copies without a concrete reason.

## Copying and API Payloads

When converting API data:

```python
orders = pd.json_normalize(
    payload["orders"]
)
```

the DataFrame is already constructed from the source representation.

The important question is whether later functions share and mutate that DataFrame.

Copy at the boundary only when ownership isolation is needed.

## Copying and Large Batch Processing

Consider a chunked pipeline:

```python
for chunk in pd.read_csv(
    "orders.csv",
    chunksize=100_000,
):
    process_chunk(chunk)
```

If `process_chunk()` immediately copies:

```python
def process_chunk(
    chunk: pd.DataFrame,
):
    working = chunk.copy()
    ...
```

peak memory can increase substantially.

If the function exclusively owns the current chunk, processing it directly may be better.

This is one reason ownership contracts are important for scalable ETL code.

## Copying and Concurrency

Pandas DataFrames are not a synchronization primitive.

Multiple threads or processes should not be assumed to safely coordinate mutation through shared DataFrame objects.

In backend systems:

```text
Celery worker A
    ↓
local DataFrame

Celery worker B
    ↓
local DataFrame
```

is generally easier to reason about than attempting shared mutable DataFrame state.

For inter-process workflows, pass serialized data or use durable external storage rather than relying on shared in-memory Pandas objects.

## Copying in Web Applications

Pandas is usually better suited to bounded request processing than long-lived shared application state.

Avoid patterns such as:

```python
GLOBAL_REPORT = pd.DataFrame(...)
```

and then mutating it across HTTP requests.

Django and FastAPI workers can handle concurrent requests, and shared mutable DataFrames introduce race-condition and data-isolation problems.

Prefer request-local or job-local objects:

```text
HTTP request
    ↓
Load data
    ↓
Construct DataFrame
    ↓
Transform
    ↓
Serialize response
```

For larger reporting workloads, move processing to background jobs or dedicated data-processing workers.

## Copy and Memory Measurement

Before optimizing copies, measure memory:

```python
before = (
    orders.memory_usage(
        index=True,
        deep=True,
    )
    .sum()
)

working = orders.copy()

after = (
    working.memory_usage(
        index=True,
        deep=True,
    )
    .sum()
)

print(
    {
        "before_bytes": before,
        "after_bytes": after,
    }
)
```

This measures the DataFrame-level memory footprint, but peak process memory can still be higher due to temporary allocations and Python runtime overhead.

## Copy Optimization Strategy

When copy pressure becomes significant:

```text
Identify unnecessary copies
        ↓
Reduce duplicated columns
        ↓
Project required fields earlier
        ↓
Use appropriate dtypes
        ↓
Process in chunks
        ↓
Reuse owned local objects
        ↓
Measure peak memory
```

Do not begin by replacing every `.copy()` with shallow copies.

Correctness should come before micro-optimizing ownership semantics.

## Production Recommendations

Use these rules as a practical default:

| Situation | Recommended approach |
|---|---|
| Need another reference to same object | Assignment |
| Need independent working DataFrame | `.copy()` |
| Need a filtered subset that will be mutated | `.loc[...] .copy()` |
| Function promises non-mutation | Copy inside function |
| Function exclusively owns temporary input | Avoid unnecessary copy |
| Memory-sensitive pipeline | Measure before changing copy behavior |
| Object-dtype nested mutable objects | Consider explicit recursive copying |
| Shared state across web requests | Avoid shared mutable DataFrames |
| Large ETL batches | Prefer ownership clarity and bounded memory |
| Advanced shallow-copy optimization | Use only with verified behavior |

## Common Mistakes

### Assuming Assignment Creates a Copy

```python
working = source
```

creates another reference.

**Better:** use:

```python
working = source.copy()
```

when independent ownership is required.

### Copying Every Intermediate DataFrame

Repeated full-frame copies can create substantial memory pressure.

**Better:** copy at meaningful ownership boundaries.

### Assuming `deep=True` Recursively Copies Every Python Object

Deep Pandas copying does not mean recursively cloning arbitrary nested Python objects in object-dtype columns.

**Better:** use explicit recursive copying only when nested mutable objects actually require it.

### Using Shallow Copies to Avoid Memory Problems Without Testing

```python
source.copy(deep=False)
```

can introduce shared-data assumptions that are difficult to reason about.

**Better:** first establish correctness with standard `.copy()`, then benchmark alternatives.

### Mutating DataFrames Inside Reusable Functions Without a Contract

Hidden mutation creates difficult-to-debug side effects.

**Better:** either copy and return a new object or clearly define intentional in-place mutation.

### Copying a Temporary Chunk Immediately

For chunk processing, defensive copies may double working-set memory.

**Better:** establish who owns the chunk before deciding whether a copy is necessary.

### Using Serialization as a Copy Mechanism

Converting to dictionaries and reconstructing a DataFrame changes representation.

**Better:** use `.copy()` when the requirement is simply independent DataFrame ownership.

### Sharing Mutable DataFrames Across Requests

A process-wide DataFrame can become shared state across concurrent requests.

**Better:** keep Pandas objects request-local or job-local.

### Ignoring Copy Cost in Kubernetes or Celery

A large copy can push a worker over its memory limit.

**Better:** account for peak memory, concurrency, batch size, and temporary allocations.

### Depending on View-or-Copy Internals

Code that assumes an operation is always a view or always a copy can become fragile.

**Better:** use documented APIs and explicit ownership semantics.

### Copying After Every Transformation

This:

```python
df = df.copy()
df["status"] = ...
df = df.copy()
df["amount"] = ...
```

may add no correctness value.

**Better:** consolidate transformations where ownership remains clear.

## Interview Traps

### Does `df2 = df1` Copy a DataFrame?

No. It creates another reference to the same DataFrame object.

### How Do You Explicitly Copy a DataFrame?

```python
df2 = df1.copy()
```

### What Is the Difference Between `deep=True` and `deep=False`?

`deep=True` requests independent Pandas data storage for the copied object, while `deep=False` creates a shallow copy that may share underlying data according to Pandas' copy semantics.

### Should You Always Use `.copy()` After Filtering?

Not always. Use it when the filtered result will be mutated independently and you want an explicit ownership boundary.

### Why Can Excessive Copying Be a Production Problem?

Full DataFrame copies can increase:

```text
Peak memory
CPU time
Worker pressure
Garbage collection overhead
Container failures
```

### Does a Pandas Deep Copy Recursively Copy Nested Python Dictionaries?

Not necessarily. Object-dtype elements are Python objects, and standard Pandas copying should not be treated as equivalent to recursively calling `copy.deepcopy()` on every nested value.

### Why Is Copy-on-Write Important?

It can defer physical copies until mutation requires them, reducing unnecessary data duplication in some workloads while making copy semantics more predictable.

### Should Application Code Depend on Copy-on-Write Internals?

No. Application code should express ownership requirements explicitly and rely on documented behavior.

### How Would You Test a Non-Mutating Transformation?

Keep a copy of the input, execute the function, and assert that the original remains unchanged:

```python
original = source.copy()

result = transform(source)

pd.testing.assert_frame_equal(
    source,
    original,
)
```

### How Does Copying Affect Large ETL Jobs?

A full copy can temporarily multiply the working set. For large batches, determine whether the current function owns the input and copy only when independent state is required.

## Practical Function Design

A clean production pattern is to make ownership behavior obvious:

```python
import pandas as pd


def normalize_orders(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    result = orders.copy()

    result["status"] = (
        result["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    result["amount"] = pd.to_numeric(
        result["amount"],
        errors="coerce",
    ).astype("Float64")

    return result
```

The contract is:

```text
Input
  ↓
Never intentionally mutated
  ↓
Independent working DataFrame
  ↓
Normalized output
```

For performance-sensitive ETL, an alternative can intentionally mutate an owned local batch:

```python
def normalize_owned_chunk(
    chunk: pd.DataFrame,
) -> pd.DataFrame:
    chunk["status"] = (
        chunk["status"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    return chunk
```

This is safe only when the caller guarantees that the function owns `chunk`.

## Ownership as an Engineering Contract

For every reusable transformation, ask:

```text
Who owns the input?
        ↓
Can this function mutate it?
        ↓
Does another consumer need the original?
        ↓
Is the object large enough for copying to matter?
        ↓
Should the function return a new object?
```

This turns copying from a mechanical habit into an intentional design decision.

## Production Checklist

```text
[ ] Is this assignment creating a shared reference?
[ ] Does the function promise to preserve the input?
[ ] Who owns the DataFrame?
[ ] Will the result be mutated independently?
[ ] Is a full copy actually necessary?
[ ] Could a copy increase peak memory significantly?
[ ] Are only required columns being copied?
[ ] Is the object large enough for copy cost to matter?
[ ] Is shallow copying genuinely required and understood?
[ ] Are object-dtype columns containing nested mutable objects?
[ ] Is the DataFrame being shared across requests or workers?
[ ] Are chunk-processing ownership boundaries explicit?
[ ] Are copy assumptions covered by tests?
[ ] Are memory measurements based on actual workload behavior?
[ ] Is the implementation relying on undocumented Pandas internals?
[ ] Are copy decisions visible in reusable transformation functions?
```

## Key Takeaways

- `df2 = df1` creates another reference, not an independent DataFrame; use `.copy()` when a separate ownership boundary is required.
- Copying is a correctness decision first and a performance decision second; unnecessary full-frame copies can significantly increase peak memory and reduce ETL throughput.
- Use explicit ownership contracts for reusable functions, pipeline branches, filtered subsets, and batch-processing stages rather than relying on accidental view or copy behavior.
- Pandas copy-on-write can defer physical copying, but production code should still use documented APIs and make mutation versus non-mutation semantics clear.
- For large backend and ETL workloads, minimize unnecessary copies, project required columns early, process bounded batches, and measure actual memory behavior before applying copy optimizations.