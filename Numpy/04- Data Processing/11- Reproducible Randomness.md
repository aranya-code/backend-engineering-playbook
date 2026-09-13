# 11- Reproducible Randomness

## Overview

Reproducible randomness means generating pseudorandom data in a way that can be recreated later from explicit random-state configuration.

In NumPy, the preferred interface is the `Generator` API:

```python
import numpy as np

rng = np.random.default_rng(42)
```

Reproducibility matters because numerical systems frequently depend on generated inputs for:

- Automated tests.
- Performance benchmarks.
- Synthetic ETL datasets.
- Failure reproduction.
- Data-quality testing.
- Batch-processing validation.
- Parallel workloads.
- Capacity experiments.

The key engineering principle is:

```text
reproducibility
=
explicit random state
+
stable generation logic
+
recorded configuration
```

A seed alone is not a complete reproducibility guarantee. The generator type, generation algorithm, call sequence, sizes, distribution parameters, and parallel-stream strategy can all affect the resulting data.

## Why Reproducible Randomness Matters

Without reproducible random input:

```text
test fails
→ generated input changes
→ failure may disappear
→ debugging becomes difficult
```

With reproducible random input:

```text
test fails
→ record seed/configuration
→ regenerate same input
→ reproduce failure
→ debug deterministically
```

This is especially valuable for numerical bugs that occur only for particular combinations of values.

For performance testing, reproducibility also makes comparisons more meaningful:

```text
same workload
+
same generated dataset
+
different implementation
=
more controlled benchmark
```

## NumPy's Generator Model

Create an explicit generator:

```python
import numpy as np

rng = np.random.default_rng(
    42,
)
```

The generator owns its internal pseudorandom state.

Random values are then produced through the generator:

```python
values = rng.random(
    10,
)
```

or:

```python
values = rng.integers(
    0,
    100,
    size=10,
)
```

This is preferable to relying on an implicit global random state.

## Seed vs Generator State

A seed initializes a generator's state.

```python
rng = np.random.default_rng(
    42,
)
```

After generating values:

```python
first = rng.random(
    10,
)

second = rng.random(
    10,
)
```

the generator has advanced.

Calling:

```python
rng.random(
    10,
)
```

again does not reproduce `first`.

To restart the same sequence, create a new generator with the same seed:

```python
rng_a = np.random.default_rng(
    42,
)

rng_b = np.random.default_rng(
    42,
)

np.testing.assert_array_equal(
    rng_a.random(10),
    rng_b.random(10),
)
```

The important distinction is:

```text
seed
→ initial state

generator state
→ current position in the pseudorandom sequence
```

## Reproducibility Contract

For a random dataset to be reproducible, record:

| Parameter | Why It Matters |
|---|---|
| Seed | Determines initial generator state |
| Generator type | Determines the random-number implementation |
| Distribution | Determines how values are produced |
| Distribution parameters | Change generated values |
| Shape / size | Changes how much state is consumed |
| Call order | Changes subsequent generator state |
| Dtype | Can change the generation behavior/output representation |
| Batch sizes | Change the sequence of random calls |
| Parallel strategy | Determines independent stream behavior |

A reproducible configuration might look like:

```python
config = {
    "seed": 42,
    "distribution": "normal",
    "loc": 100.0,
    "scale": 20.0,
    "size": 1_000_000,
    "dtype": "float64",
}
```

Persisting this configuration is more reliable than storing only:

```text
seed = 42
```

## Reproducible Integer Data

```python
import numpy as np

rng = np.random.default_rng(
    42,
)

values = rng.integers(
    low=0,
    high=1_000,
    size=10_000,
    dtype=np.int32,
)
```

A second generator initialized identically reproduces the same sequence:

```python
rng_a = np.random.default_rng(
    42,
)

rng_b = np.random.default_rng(
    42,
)

first = rng_a.integers(
    0,
    1_000,
    size=10_000,
)

second = rng_b.integers(
    0,
    1_000,
    size=10_000,
)

np.testing.assert_array_equal(
    first,
    second,
)
```

This pattern is useful for deterministic fixtures and benchmarks.

## Reproducible Floating-Point Data

```python
rng = np.random.default_rng(
    42,
)

values = rng.normal(
    loc=100.0,
    scale=15.0,
    size=100_000,
)
```

The generated values can be regenerated from the same configuration.

For tests, avoid asserting that a generated dataset has exactly a theoretical mean or standard deviation unless the test is specifically checking deterministic output. Finite random samples will vary around the theoretical distribution parameters.

## Reproducible Categorical Data

Random categorical data can also be deterministic:

```python
categories = np.array(
    [
        "pending",
        "completed",
        "failed",
    ],
)

rng = np.random.default_rng(
    42,
)

statuses = rng.choice(
    categories,
    size=10_000,
    p=[
        0.10,
        0.85,
        0.05,
    ],
)
```

Reproducing the exact values requires keeping the category order and probability configuration unchanged.

For production tests, treat the category list as part of the fixture contract.

## Stable Generation Functions

Pass the generator into functions instead of creating hidden global random state.

```python
import numpy as np


def generate_amounts(
    rng: np.random.Generator,
    size: int,
) -> np.ndarray:
    return rng.lognormal(
        mean=4.0,
        sigma=1.0,
        size=size,
    )
```

Then:

```python
rng = np.random.default_rng(
    42,
)

amounts = generate_amounts(
    rng,
    size=100_000,
)
```

This provides explicit dependency injection:

```text
caller owns random state
function consumes random state
```

It makes the function easier to test and reason about.

## Avoid Hidden Random State

Prefer:

```python
def generate_data(
    rng: np.random.Generator,
):
    ...
```

over:

```python
def generate_data():
    rng = np.random.default_rng()
    ...
```

The second version hides a critical dependency.

In test code, hidden random state makes it harder to reproduce failures.

In production batch jobs, it also makes it harder to coordinate deterministic runs.

## Random State and Call Order

Consider:

```python
rng = np.random.default_rng(
    42,
)

a = rng.random(100)
b = rng.random(100)
```

Now change the implementation:

```python
rng = np.random.default_rng(
    42,
)

a = rng.random(200)
b = rng.random(100)
```

Even though the seed is identical, `b` changes because the generator state was consumed differently.

This means a reproducible workflow depends on:

```text
same seed
+
same random calls
+
same call order
+
same sizes
```

Refactoring random-generation logic can therefore change downstream values.

## Reproducibility Across Batch Sizes

Batch processing introduces an important subtlety.

Suppose:

```python
rng = np.random.default_rng(
    42,
)

batch_1 = rng.random(
    100,
)

batch_2 = rng.random(
    100,
)
```

Changing to:

```python
rng = np.random.default_rng(
    42,
)

batch_1 = rng.random(
    50,
)

batch_2 = rng.random(
    150,
)
```

does not necessarily give the same logical grouping of values even though the total number of values is unchanged.

The generator produces a sequence, and batch boundaries determine which values belong to which batch.

For reproducible batch-level tests, batch size should therefore be part of the test configuration.

## Reproducible Batch Processing

A deterministic batch generator can look like:

```python
import numpy as np


def generate_batches(
    seed: int,
    total: int,
    batch_size: int,
):
    rng = np.random.default_rng(
        seed,
    )

    for start in range(
        0,
        total,
        batch_size,
    ):
        size = min(
            batch_size,
            total - start,
        )

        yield rng.normal(
            loc=100.0,
            scale=20.0,
            size=size,
        )
```

Then:

```python
for batch in generate_batches(
    seed=42,
    total=1_000_000,
    batch_size=100_000,
):
    process(batch)
```

Running the same configuration again reproduces the same batch sequence.

## Reproducibility in CI

Randomized tests should expose enough state to replay failures.

For example:

```python
import os
import numpy as np

seed = int(
    os.getenv(
        "TEST_SEED",
        "42",
    )
)

rng = np.random.default_rng(
    seed,
)
```

A CI job can run:

```bash
TEST_SEED=42 pytest
```

and a developer can reproduce the exact random configuration locally.

For high-value test suites, include the seed in failure output:

```python
print(
    f"random_seed={seed}"
)
```

A useful CI workflow is:

```mermaid
flowchart LR
    A["CI Test"] --> B["Seed from Configuration"]
    B --> C["Generator"]
    C --> D["Random Test Input"]
    D --> E["Test Failure"]
    E --> F["Record Seed"]
    F --> G["Local Reproduction"]
```

## Randomized Property Testing

Random inputs can complement fixed test cases.

For example:

```python
import numpy as np


def normalize(values: np.ndarray) -> np.ndarray:
    minimum = np.min(values)
    maximum = np.max(values)

    if minimum == maximum:
        raise ValueError(
            "Constant input is not supported."
        )

    return (
        (values - minimum)
        / (maximum - minimum)
    )
```

A test can generate reproducible valid datasets:

```python
def test_normalization_bounds():
    rng = np.random.default_rng(
        42,
    )

    values = rng.uniform(
        1.0,
        10_000.0,
        size=10_000,
    )

    result = normalize(
        values,
    )

    assert np.all(
        result >= 0.0
    )

    assert np.all(
        result <= 1.0
    )
```

The seed provides deterministic input while still exercising many values.

For stronger property-based testing, tools such as Hypothesis can generate inputs independently; NumPy remains useful for constructing large numerical arrays inside those tests.

## Reproducing a Failed Randomized Test

A production-quality failure report can include:

```text
seed=42
distribution=normal
loc=100
scale=20
size=1_000_000
dtype=float64
batch_size=100_000
```

Then the failure can be recreated:

```python
rng = np.random.default_rng(
    42,
)

values = rng.normal(
    loc=100.0,
    scale=20.0,
    size=1_000_000,
)
```

This is much more useful than a generic error such as:

```text
randomized test failed
```

## Independent Random Streams

Parallel workers should generally have independently managed random streams.

A simple configuration can use distinct generators:

```python
import numpy as np

worker_a = np.random.default_rng(
    101,
)

worker_b = np.random.default_rng(
    202,
)
```

For structured deterministic stream creation, use `SeedSequence`:

```python
import numpy as np

root = np.random.SeedSequence(
    42,
)

children = root.spawn(
    4,
)

generators = [
    np.random.default_rng(child)
    for child in children
]
```

Each worker receives its own generator.

This provides explicit stream ownership without having all workers mutate one shared generator.

## Reproducibility in Celery

A Celery workload can assign deterministic random streams based on a known root seed and task identity.

Conceptually:

```text
root seed
    ↓
task-specific seed state
    ↓
worker-local Generator
    ↓
synthetic batch
```

Avoid relying on worker process startup order to determine random state.

Worker scheduling can change between runs, so deterministic stream assignment should derive from explicit task or partition identifiers when reproducibility across distributed executions is required.

## Reproducibility in Kubernetes

Kubernetes deployments may have:

```text
multiple replicas
+
different startup order
+
different pod identities
```

A single global process seed is therefore not enough to define deterministic distributed data generation.

For deterministic workloads:

```text
job identifier
+
partition identifier
+
configured root seed
```

can be used to derive independent generator streams.

The design should ensure that rescheduling a pod does not silently change which random stream belongs to a logical partition.

## Parallel Stream Derivation

A useful conceptual model is:

```text
root seed
    │
    ├── partition 0 → generator 0
    ├── partition 1 → generator 1
    ├── partition 2 → generator 2
    └── partition 3 → generator 3
```

Each partition can then be regenerated independently.

This is more reliable than:

```text
worker startup order
→ random seed
```

because infrastructure scheduling is not a deterministic application-level property.

## Reproducible Performance Benchmarks

Random datasets are useful for performance testing:

```python
import numpy as np

rng = np.random.default_rng(
    42,
)

values = rng.random(
    10_000_000,
)
```

Generate the dataset before starting the timer:

```python
import time

start = time.perf_counter()

result = process(
    values
)

elapsed = (
    time.perf_counter()
    - start
)
```

Do not include random generation in the timed region unless the benchmark is specifically intended to measure:

```text
generation + processing
```

For a processing benchmark, random generation should be setup work.

## Benchmark Reproducibility

Use the same:

```text
seed
+
dataset shape
+
dtype
+
distribution
+
algorithm configuration
```

when comparing two implementations.

For example:

```text
implementation A
→ 10M float64 values
→ same seed

implementation B
→ 10M float64 values
→ same seed
```

This reduces one source of benchmark variance.

However, reproducibility does not mean a single run is statistically sufficient. Performance measurements should still use repeated runs and report suitable statistics.

## Persisting Random Fixtures

If generation itself is expensive, persist a known dataset:

```python
np.save(
    "fixtures/metrics.npy",
    values,
)
```

Then:

```python
values = np.load(
    "fixtures/metrics.npy",
)
```

Advantages:

- Faster CI startup.
- Stable exact fixture.
- Easier cross-language or cross-process testing.
- No dependence on random-generation logic at test runtime.

Trade-offs:

- Additional repository or artifact storage.
- Fixture versioning.
- Potentially large files.
- Need to regenerate deliberately when the schema changes.

A good rule is:

```text
generate repeatedly
→ keep generator configuration

generate expensively once
→ persist fixture
```

## Reproducibility and Schema Changes

A random generator can reproduce values only relative to the code and schema that interpret them.

Suppose:

```text
version A
→ amount, quantity

version B
→ amount, quantity, discount
```

The same random seed does not make the datasets semantically equivalent.

Include:

```text
schema version
+
generator version
+
seed
```

when generated datasets become long-lived artifacts.

## Randomness and Data Pipelines

A reproducible synthetic pipeline might look like:

```mermaid
flowchart LR
    A["Configuration"] --> B["SeedSequence / Generator"]
    B --> C["Synthetic Batch"]
    C --> D["Validation"]
    D --> E["Transformation"]
    E --> F["Aggregation"]
    F --> G["Persisted Results"]
```

Configuration should include:

```text
seed
distribution
parameters
shape
dtype
batch size
schema version
generator version
```

This makes rerunning the pipeline significantly easier.

## Reproducibility vs Production Randomness

Not every production workload should be deterministic.

For example:

```text
test dataset generation
→ reproducible

performance benchmark
→ reproducible

synthetic ETL fixture
→ reproducible

cryptographic token
→ secure and unpredictable

security nonce
→ secure randomness
```

These requirements are different.

Use reproducibility where deterministic replay matters and cryptographically secure randomness where unpredictability matters.

## Cryptographic Randomness

NumPy's pseudorandom generators are not intended for security-sensitive randomness.

Do not use:

```python
rng = np.random.default_rng(
    42,
)

token = rng.integers(
    0,
    2**64,
)
```

for:

- Authentication tokens.
- Password reset tokens.
- Session secrets.
- API credentials.
- Cryptographic keys.

Use Python's `secrets` module:

```python
import secrets

token = secrets.token_urlsafe(
    32,
)
```

The distinction is:

```text
reproducible pseudorandomness
→ testing / simulation / numerical processing

cryptographically secure randomness
→ security-sensitive values
```

## Reproducibility Across Environments

For consistent replay, control the environment as well as the random configuration.

A reproducible test setup may record:

```text
Python version
NumPy version
generator configuration
seed
dtype
dataset shape
schema version
```

This is especially relevant for long-lived benchmarks and debugging.

A fixed seed does not guarantee identical results across every possible version or implementation change.

For high-value historical fixtures, persisting the actual generated data can be more reliable than depending indefinitely on regeneration from a seed.

## Randomness and Serialization

If generated data is serialized:

```python
np.save(
    "fixtures/data.npy",
    values,
)
```

the persisted dataset becomes an exact artifact.

This is often preferable for:

```text
regression tests
+
benchmark fixtures
+
bug reproductions
```

where exact bytes or exact values matter more than regenerating the same conceptual distribution.

## Large-Scale Memory Management

Reproducible random generation does not eliminate memory costs.

Generating:

```python
values = rng.random(
    100_000_000,
)
```

creates a large array.

For large workloads:

- Use batches.
- Select dtype intentionally.
- Process data as it is generated.
- Avoid retaining intermediate datasets unnecessarily.
- Persist to disk incrementally when required.

For example:

```python
rng = np.random.default_rng(
    42,
)

for _ in range(100):
    batch = rng.normal(
        loc=100.0,
        scale=20.0,
        size=1_000_000,
    )

    process(batch)
```

The generator remains deterministic while memory remains bounded by the batch size and processing requirements.

## Common Mistakes

### Assuming a Seed Alone Guarantees Reproducibility

The generator, call order, distribution parameters, sizes, and environment can also affect the generated sequence.

### Creating a New Generator in Every Function

This can create fragmented random-state ownership and make deterministic replay difficult.

### Sharing One Generator Across Parallel Workers

Shared mutable random state makes distributed execution harder to reproduce and reason about.

### Depending on Worker Startup Order

Celery and Kubernetes scheduling is not a stable source of deterministic random-state assignment.

### Changing Batch Size Without Considering Sequence Consumption

Different batch boundaries change how generated values are grouped and can change later sequence state.

### Including Generation in Processing Benchmarks Accidentally

This measures both generation and processing.

### Treating Random Data as Realistic by Default

Random distributions rarely capture all business correlations, seasonality, or failure patterns found in production.

### Using Randomness Instead of Explicit Edge Cases

Rare boundary states may never occur in random sampling. Generate important edge cases deliberately.

### Using NumPy Randomness for Security

Use `secrets` or another cryptographically secure source for security-sensitive values.

### Assuming Reproducibility Forever Across Dependency Changes

A seed-based sequence may not be a permanent cross-version data contract. Persist exact fixtures when long-term byte-for-byte reproducibility is required.

## Testing

The simplest reproducibility test compares generators initialized identically:

```python
import numpy as np


def test_reproducible_generation():
    rng_a = np.random.default_rng(
        42,
    )

    rng_b = np.random.default_rng(
        42,
    )

    first = rng_a.normal(
        loc=100.0,
        scale=20.0,
        size=1_000,
    )

    second = rng_b.normal(
        loc=100.0,
        scale=20.0,
        size=1_000,
    )

    np.testing.assert_array_equal(
        first,
        second,
    )
```

Test configuration explicitly when it is part of the contract:

```python
def test_reproducible_batches():
    def generate(seed: int):
        rng = np.random.default_rng(seed)

        return [
            rng.integers(
                0,
                100,
                size=100,
            )
            for _ in range(3)
        ]

    first = generate(42)
    second = generate(42)

    for first_batch, second_batch in zip(
        first,
        second,
        strict=True,
    ):
        np.testing.assert_array_equal(
            first_batch,
            second_batch,
        )
```

Also test:

- Different seeds produce distinct sequences.
- Same seed and configuration reproduce identical output.
- Batch generation remains deterministic.
- Parallel streams remain independently reproducible.
- Generator configuration is recorded correctly.
- Persisted fixtures load correctly.
- Edge cases are generated explicitly.
- Production failures can be replayed from recorded configuration.

## Debugging

When a randomized test fails, capture the complete generation configuration.

```python
seed = 42
size = 100_000
loc = 100.0
scale = 20.0

print(
    {
        "seed": seed,
        "size": size,
        "distribution": "normal",
        "loc": loc,
        "scale": scale,
        "dtype": "float64",
    }
)
```

Reconstruct the generator:

```python
rng = np.random.default_rng(
    seed,
)

values = rng.normal(
    loc=loc,
    scale=scale,
    size=size,
)
```

If the failure occurred in a distributed system, also record:

```text
logical partition
task identifier
batch size
stream derivation
generator version
schema version
```

This turns a nondeterministic-looking failure into a deterministic debugging artifact.

## Interview Questions

### What is reproducible randomness?

It is the ability to recreate the same pseudorandom sequence from explicit random-state configuration and the same generation logic.

### Is a seed enough for reproducibility?

No. The generator type, call order, distribution parameters, requested sizes, batch boundaries, and relevant environment can also affect the result.

### Why should random generators be passed into functions?

It makes random state explicit, improves testability, and prevents hidden global state from controlling behavior.

### Why can changing a batch size change subsequent random values?

Random generation advances generator state. Different batch sizes consume the sequence differently.

### How would you make random data reproducible across distributed workers?

Use a root seed and derive independent worker or partition streams explicitly, for example with `SeedSequence.spawn()`.

### Why should benchmark data be generated outside the timed section?

Otherwise the benchmark measures data generation and processing together rather than the operation being compared.

### When should generated random data be persisted instead of regenerated?

When exact fixtures are expensive to generate, need long-term stability, or must remain reproducible across future dependency or implementation changes.

### Is NumPy randomness suitable for authentication tokens?

No. NumPy is intended for numerical pseudorandom generation, not cryptographic security. Use `secrets` for security-sensitive randomness.

### Does the same seed guarantee identical data across all future NumPy versions?

Not as a universal long-term contract. Dependency or algorithm changes can affect reproducibility. Persist exact fixtures when historical exactness matters.

### Why are explicit edge cases still necessary when using seeded randomness?

Random sampling may not reliably generate critical boundaries or rare failure states. Important conditions should be constructed deliberately.

## Key Takeaways

- Reproducible randomness requires more than a seed: generator configuration, distribution parameters, call order, shapes, batch sizes, and execution strategy all matter.
- Use explicit `np.random.Generator` instances and pass them into functions so random state is visible, testable, and controllable.
- For distributed workloads, derive independent random streams intentionally rather than depending on worker startup order or shared mutable state.
- Record seeds and generation configuration for CI, benchmarks, and failure reproduction; persist exact fixtures when long-term reproducibility must survive code or dependency changes.
- NumPy's pseudorandom generators are for numerical and testing workloads, not cryptographic security; use Python's `secrets` module for security-sensitive randomness.