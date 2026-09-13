# 10- Random Data Generation

## Overview

Random data generation is useful in backend and data-processing systems for creating synthetic datasets, controlled test inputs, simulations of operational conditions, and reproducible benchmarks.

NumPy provides random-number generation through the modern `Generator` API:

```python
import numpy as np

rng = np.random.default_rng()
```

The important engineering distinction is between:

```text
randomness
+
reproducibility
+
statistical distribution
+
parallel execution
+
security
```

Random data used for testing, benchmarking, and data pipelines should usually be reproducible. Random values used for security-sensitive operations should not rely on NumPy's pseudorandom generators.

A typical processing flow is:

```mermaid
flowchart LR
    A["Seed / Generator Configuration"] --> B["NumPy Generator"]
    B --> C["Random Dataset"]
    C --> D["Validation / Transformation"]
    D --> E["Benchmark / Test / Pipeline"]
```

## Why Random Data Generation Matters

Real production datasets are often difficult to reproduce during development.

A deterministic random dataset allows an engineer to create:

```text
same input
+
same seed
+
same generation logic
=
reproducible test data
```

This is useful for:

- Unit and integration testing.
- Performance benchmarking.
- Load-test dataset generation.
- ETL development.
- Data-cleaning validation.
- Batch-processing tests.
- Failure reproduction.
- Memory profiling.
- Numerical edge-case generation.

Random data should therefore be treated as test or pipeline input, not as an uncontrolled source of variation.

## The Modern NumPy Random API

Prefer:

```python
import numpy as np

rng = np.random.default_rng()
```

over older global-state usage such as:

```python
np.random.seed(42)
```

and repeated calls through the legacy `np.random` module-level API.

The modern design separates:

```text
Generator
+
random state
+
distribution methods
```

This makes ownership of random state more explicit.

For example:

```python
rng = np.random.default_rng(42)

values = rng.random(
    10,
)
```

The generator maintains its own state instead of relying on a single implicit global random stream.

## Reproducible Random Data

A seed makes a random sequence reproducible for the same generator configuration and generation logic.

```python
import numpy as np

rng = np.random.default_rng(
    42,
)

values = rng.integers(
    low=0,
    high=100,
    size=10,
)

print(values)
```

Running the same code with the same seed produces the same generated sequence under the same relevant NumPy generator implementation and call sequence.

This is valuable for:

```text
test reproduction
+
debugging
+
benchmark consistency
+
fixture generation
```

## Seed Is Part of the Test Configuration

Treat the seed as explicit test configuration:

```python
RANDOM_SEED = 42

rng = np.random.default_rng(
    RANDOM_SEED,
)
```

This makes it easier to reproduce a failing case.

For example:

```text
test failed
→ record seed
→ rerun with seed
→ reproduce generated input
→ debug deterministic case
```

A useful test failure report can include:

```text
test name
seed
dataset size
generator configuration
```

## Generator Ownership

Avoid creating a new generator inside every function unless that function intentionally owns its random sequence.

Prefer dependency injection:

```python
import numpy as np


def generate_amounts(
    rng: np.random.Generator,
    size: int,
) -> np.ndarray:
    return rng.integers(
        1,
        10_000,
        size=size,
    )
```

Then:

```python
rng = np.random.default_rng(42)

amounts = generate_amounts(
    rng,
    size=1_000,
)
```

This makes the random state explicit and testable.

It also prevents hidden global randomness from spreading through the application.

## Integer Generation

Use `Generator.integers()` for integer data:

```python
import numpy as np

rng = np.random.default_rng(42)

values = rng.integers(
    low=0,
    high=100,
    size=10,
)
```

The `high` value is exclusive in the common two-bound form:

```text
0 <= value < 100
```

For a specified dtype:

```python
values = rng.integers(
    0,
    100,
    size=10_000,
    dtype=np.int16,
)
```

Choose the dtype based on the generated range and downstream requirements.

## Floating-Point Generation

For uniformly distributed floating-point values over `[0.0, 1.0)`:

```python
values = rng.random(
    10_000,
)
```

For a different interval:

```python
values = (
    rng.random(10_000)
    * 100.0
)
```

or:

```python
values = rng.uniform(
    low=10.0,
    high=100.0,
    size=10_000,
)
```

Use the distribution method that communicates the intended semantics clearly.

## Common Distributions

NumPy provides generators for different statistical distributions.

Common backend/data-processing use cases include:

| Distribution | Typical Use |
|---|---|
| Uniform | Bounded synthetic values |
| Normal | Approximate continuous variation |
| Integers | IDs, counts, discrete test values |
| Poisson | Event/count-like synthetic data |
| Exponential | Waiting-time-like synthetic data |
| Binomial | Success/failure counts |
| Choice | Sampling from known categories |

The choice of distribution should reflect the behavior being tested.

Randomness alone does not make synthetic data realistic.

## Normal Distribution

For synthetic measurements:

```python
values = rng.normal(
    loc=100.0,
    scale=15.0,
    size=10_000,
)
```

This generates values according to a normal distribution with:

```text
mean     ≈ 100
std      ≈ 15
```

Actual finite samples will not have exactly those statistics.

If the downstream system requires hard bounds, validate or constrain the generated values explicitly rather than assuming the distribution will stay inside a range.

## Exponential Distribution

For skewed synthetic values:

```python
durations = rng.exponential(
    scale=2.0,
    size=10_000,
)
```

This can be useful for testing workloads where most values are small and occasional larger values occur.

The distribution should be chosen based on the intended workload characteristics rather than because it is easy to generate.

## Poisson Distribution

For count-like data:

```python
events = rng.poisson(
    lam=5.0,
    size=10_000,
)
```

This produces non-negative integer counts.

Potential uses include:

- Synthetic event counts.
- Batch record counts.
- Request arrivals in controlled simulations.
- Test datasets for count-oriented aggregation.

It should not be treated as a universal model of real traffic.

## Sampling from Categories

When a dataset should contain categorical values:

```python
statuses = np.array(
    [
        "pending",
        "completed",
        "failed",
    ],
)

sampled = rng.choice(
    statuses,
    size=1_000,
)
```

A custom probability distribution can be supplied:

```python
sampled = rng.choice(
    statuses,
    size=1_000,
    p=[
        0.10,
        0.85,
        0.05,
    ],
)
```

This is useful for generating realistic category frequencies for validation and benchmarking.

The probabilities should be documented when they influence test behavior.

## Sampling Without Replacement

For selecting unique elements:

```python
values = np.arange(
    100_000,
)

sample = rng.choice(
    values,
    size=1_000,
    replace=False,
)
```

This is useful for:

- Selecting unique test records.
- Sampling without duplicates.
- Creating controlled subsets.

The requested sample size cannot exceed the population size when:

```python
replace=False
```

## Random Permutations

To shuffle an existing array:

```python
values = np.arange(
    10,
)

rng.shuffle(
    values,
)
```

This mutates the array in place.

If the original order must remain unchanged:

```python
shuffled = rng.permutation(
    values,
)
```

The distinction is important:

| Operation | Behavior |
|---|---|
| `rng.shuffle(array)` | Mutates input |
| `rng.permutation(array)` | Returns a permuted result |

## Random Data for Backend Testing

A realistic transaction dataset might contain:

```python
import numpy as np


def generate_transactions(
    rng: np.random.Generator,
    size: int,
) -> dict[str, np.ndarray]:
    return {
        "amount": rng.lognormal(
            mean=4.0,
            sigma=1.0,
            size=size,
        ),
        "status": rng.choice(
            np.array(
                [
                    "pending",
                    "completed",
                    "failed",
                ]
            ),
            size=size,
            p=[
                0.10,
                0.85,
                0.05,
            ],
        ),
        "retry_count": rng.integers(
            0,
            5,
            size=size,
        ),
    }
```

This kind of generator can support:

```text
ETL tests
+
validation tests
+
aggregation tests
+
performance benchmarks
```

without depending on production data.

## Generating Edge Cases

Purely random values often fail to exercise the most important failure modes.

Production tests should explicitly generate edge cases such as:

```text
0
negative values
very large values
NaN
+inf
-inf
empty arrays
single-element arrays
maximum allowed values
minimum allowed values
duplicate categories
unknown categories
```

For example:

```python
edge_cases = np.array(
    [
        0.0,
        -1.0,
        1_000_000.0,
        np.nan,
        np.inf,
        -np.inf,
    ],
    dtype=np.float64,
)
```

Use random generation for variability and explicit fixtures for known boundary behavior.

## Random Data vs Production Data

Synthetic random data has major advantages:

- Reproducible.
- Safe to share.
- Easy to scale.
- Easy to control.
- Useful for load testing.
- Useful for deterministic debugging.

But random data may fail to reproduce:

```text
real distributions
+
real correlations
+
schema anomalies
+
business-specific edge cases
```

A mature test strategy often uses both:

```text
synthetic data
+
curated anonymized fixtures
+
boundary cases
```

depending on the test objective.

## Large Dataset Generation

For performance benchmarking:

```python
rng = np.random.default_rng(
    42,
)

values = rng.normal(
    loc=100.0,
    scale=20.0,
    size=10_000_000,
)
```

This creates a large array, so memory consumption matters.

For `float64` data:

```python
print(values.nbytes)
```

can be used to estimate the raw array data-buffer size.

Do not assume that the total process memory is equal to `nbytes`; generators, temporary arrays, Python objects, imported libraries, and other allocations consume additional memory.

## Batch Generation

When the complete synthetic dataset is not required simultaneously, generate it in batches:

```python
import numpy as np


def batches(
    rng: np.random.Generator,
    total: int,
    batch_size: int,
):
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
rng = np.random.default_rng(42)

for batch in batches(
    rng,
    total=10_000_000,
    batch_size=500_000,
):
    process(batch)
```

This keeps peak working memory bounded.

## Reproducible Batch Streams

If a single generator is used continuously:

```python
rng = np.random.default_rng(
    42,
)
```

successive batches consume successive portions of the same random sequence.

This provides deterministic reproduction as long as:

```text
seed
+
generator
+
call order
+
sizes
```

remain consistent.

Changing the number or order of random-generation calls can change later values even when the seed is unchanged.

This is important when tests are refactored.

## Independent Random Streams

Large services may require multiple components to generate random data independently.

Creating separate generators with manually chosen seeds can work:

```python
worker_a = np.random.default_rng(
    101,
)

worker_b = np.random.default_rng(
    202,
)
```

For more structured parallel generation, NumPy's `SeedSequence` can be used to derive child streams:

```python
import numpy as np

seed_sequence = np.random.SeedSequence(
    42,
)

children = seed_sequence.spawn(
    4,
)

generators = [
    np.random.default_rng(child)
    for child in children
]
```

This is useful when deterministic parallel streams are required without simply reusing the same generator across workers.

## Randomness in Parallel Systems

Do not share one mutable generator carelessly across unrelated concurrent workers.

Prefer explicit ownership:

```text
process
 ├── worker 1 → generator 1
 ├── worker 2 → generator 2
 ├── worker 3 → generator 3
 └── worker 4 → generator 4
```

For multiprocessing or distributed workloads, derive independent streams intentionally.

This is important for:

- Celery workers.
- Kubernetes replicas.
- Parallel test workers.
- Distributed benchmarks.
- Batch-processing jobs.

Reproducibility becomes harder when random state is implicitly shared.

## Randomness and Threading

A generator is stateful.

When concurrency is involved, make random-state ownership explicit instead of assuming a single global generator is the best design.

For concurrent workloads:

```text
worker-local generator
+
deterministic seed derivation
```

is often easier to reason about than shared mutable state.

The exact concurrency architecture should follow the worker model rather than relying on accidental behavior.

## Cryptographic Security

NumPy random generators are designed for numerical simulation and data generation, not cryptographic security.

Do not use:

```python
np.random.default_rng()
```

to generate:

- Passwords.
- Authentication tokens.
- API secrets.
- Session identifiers.
- Reset tokens.
- Cryptographic keys.

For security-sensitive randomness, use Python's cryptographically secure facilities such as:

```python
import secrets

token = secrets.token_urlsafe(
    32,
)
```

The distinction is:

```text
NumPy Generator
→ numerical / simulation randomness

secrets
→ security-sensitive randomness
```

## Random IDs vs Database IDs

Do not generate application identifiers with a numerical random generator merely because unique-looking numbers are convenient.

For persistent identity:

```text
database-generated IDs
+
UUIDs
+
application-specific identifiers
```

may be more appropriate.

Random-number collision probabilities and ordering semantics should be part of the identifier design rather than an accidental property of a test-data generator.

## Random Data for Load Testing

Synthetic random data is useful for exercising service capacity.

Example:

```python
rng = np.random.default_rng(
    42,
)

payload_amounts = rng.lognormal(
    mean=4.0,
    sigma=1.0,
    size=100_000,
)
```

A load-testing pipeline can then:

```text
generate
→ serialize
→ send requests
→ measure latency
→ record throughput
```

Keep the generation workload separate from the service under test when measuring application performance.

Otherwise, the generator itself can become the bottleneck.

## Random Data for ETL Testing

A batch-processing pipeline might generate:

```python
rng = np.random.default_rng(
    42,
)

batch = {
    "amount": rng.uniform(
        0.0,
        10_000.0,
        size=500_000,
    ),
    "quantity": rng.integers(
        1,
        100,
        size=500_000,
    ),
}
```

Then:

```text
synthetic batch
→ validation
→ cleaning
→ normalization
→ aggregation
→ output
```

This is useful for testing the numerical pipeline independently from the production source.

## Random Data and Failure Injection

Random generation can be combined with controlled invalid-data injection.

For example:

```python
import numpy as np


def generate_dataset(
    rng: np.random.Generator,
    size: int,
) -> np.ndarray:
    values = rng.normal(
        loc=100.0,
        scale=20.0,
        size=size,
    )

    invalid_count = max(
        1,
        size // 100,
    )

    indices = rng.choice(
        size,
        size=invalid_count,
        replace=False,
    )

    values[indices[: invalid_count // 2]] = np.nan
    values[indices[invalid_count // 2 :]] = np.inf

    return values
```

This creates a controlled mixture of:

```text
normal values
+
missing values
+
non-finite values
```

Such generators are useful for testing validation and data-quality handling.

## Distribution Parameters Are Part of the Test Contract

A test based on random data is only reproducible if the generation configuration is recorded.

For example:

```python
config = {
    "seed": 42,
    "distribution": "normal",
    "loc": 100.0,
    "scale": 20.0,
    "size": 1_000_000,
}
```

Changing any of these can change the generated dataset and potentially the observed benchmark or test result.

Treat important generation parameters as versioned test configuration.

## Randomness and Benchmarking

Random data is useful for benchmarking because it can create large inputs consistently:

```python
rng = np.random.default_rng(
    42,
)

values = rng.random(
    10_000_000,
)
```

However, avoid generating the dataset inside the timed section when benchmarking the processing algorithm.

Prefer:

```python
values = rng.random(
    10_000_000,
)

start = time.perf_counter()

result = process(values)

elapsed = (
    time.perf_counter()
    - start
)
```

Otherwise the benchmark measures:

```text
data generation
+
data processing
```

rather than the processing operation itself.

## Randomness and Memory Benchmarking

Synthetic data generation is also useful for testing memory behavior.

For example:

```python
values = rng.random(
    20_000_000,
    dtype=np.float64,
)
```

Then process it with:

```text
masking
+
aggregation
+
transformation
```

while observing:

```text
peak RSS
allocation behavior
processing time
throughput
```

Use representative sizes and distributions because memory behavior can differ substantially between small development datasets and production-scale workloads.

## Reproducibility Across Code Changes

A fixed seed does not guarantee that a test will remain identical after changing the generation algorithm.

For example:

```text
version A
→ generate 1 array
→ generate 2 arrays

version B
→ generate 2 arrays
→ generate 1 array
```

Both may use:

```python
np.random.default_rng(42)
```

but subsequent random values can differ because the generator state is consumed differently.

Therefore, reproducibility means:

```text
same seed
+
same generator
+
same algorithm
+
same call sequence
```

not simply:

```text
same seed
```

## Persisting Generated Test Data

For expensive test datasets, it may be useful to persist the generated result rather than regenerate it on every run.

For example:

```python
np.save(
    "fixtures/transactions.npy",
    values,
)
```

Then load:

```python
values = np.load(
    "fixtures/transactions.npy",
)
```

This trades:

```text
generation time
```

for:

```text
storage
+
fixture versioning
```

It can make CI more deterministic when generation itself is expensive.

## Reproducible Random Fixtures in CI/CD

A CI pipeline can use a fixed seed:

```python
rng = np.random.default_rng(
    12345,
)
```

This allows failures to be reproduced locally.

For better diagnostics, record the seed used by a randomized test:

```python
print(
    f"seed={seed}"
)
```

If the seed is configurable through CI:

```text
CI run
→ seed=12345
→ test fails
→ rerun locally with seed=12345
```

This is much more practical than debugging an unreproducible random failure.

## Random Generation with Pandas

Pandas can consume NumPy-generated arrays:

```python
import pandas as pd
import numpy as np

rng = np.random.default_rng(
    42,
)

frame = pd.DataFrame(
    {
        "amount": rng.uniform(
            0.0,
            10_000.0,
            size=100_000,
        ),
        "quantity": rng.integers(
            1,
            100,
            size=100_000,
        ),
    }
)
```

A common division of responsibility is:

```text
NumPy
→ generate numerical arrays

Pandas
→ organize and process tabular data
```

Avoid forcing generated data through Pandas when the downstream operation is purely numerical.

## File-Based Synthetic Data

Generated NumPy arrays can be persisted to `.npy` or other formats suitable for the workload.

For example:

```python
np.save(
    "data/synthetic_metrics.npy",
    values,
)
```

For a reusable pipeline:

```text
Generator
→ validation
→ `.npy` fixture
→ batch processing
```

For larger structured datasets, choose a storage format based on:

```text
schema
+
compression
+
interoperability
+
query requirements
+
batch access
```

NumPy random generation is independent of the choice of output storage format.

## Memory-Efficient Random Generation

If only one batch is needed at a time:

```python
rng = np.random.default_rng(
    42,
)

for _ in range(20):
    batch = rng.normal(
        loc=100.0,
        scale=20.0,
        size=500_000,
    )

    process(batch)
```

This avoids constructing a 10-million-element array when the consumer can operate incrementally.

Batch generation is particularly useful in constrained Kubernetes or containerized workers.

## Common Mistakes

### Using the Legacy Global Random API Everywhere

Prefer explicit `Generator` instances:

```python
rng = np.random.default_rng(
    42,
)
```

This makes random-state ownership clearer.

### Forgetting the Seed When Reproducibility Matters

Without a known seed, failures and benchmarks can be difficult to reproduce.

### Assuming the Seed Alone Guarantees Identical Output

Changing the generator type, call order, sizes, or generation logic can alter the sequence.

### Using NumPy Randomness for Security Tokens

NumPy is not a cryptographic randomness source.

Use `secrets` for security-sensitive values.

### Generating All Test Data at Once

Large synthetic arrays can consume significant memory. Generate in batches when possible.

### Including Data Generation in a Processing Benchmark

This measures the generator and processor together and can distort the benchmark.

### Using Unrealistic Distributions

Uniform random data is easy to generate but often unlike production data.

### Assuming Random Data Covers Edge Cases

Random generation may rarely produce critical boundaries such as exact zero, maximum values, `NaN`, or infinity. Generate those explicitly.

### Sharing Random State Carelessly Across Workers

Explicit generator ownership and deterministic stream derivation are easier to reason about in concurrent systems.

### Dynamically Expanding Category Vocabularies Without Limits

Unbounded random or externally supplied categories can create memory and operational problems.

## Testing

A random-data generator should itself be deterministic when given explicit configuration.

```python
import numpy as np


def generate_values(
    seed: int,
    size: int,
) -> np.ndarray:
    rng = np.random.default_rng(
        seed,
    )

    return rng.normal(
        loc=100.0,
        scale=20.0,
        size=size,
    )


def test_generation_is_reproducible():
    first = generate_values(
        seed=42,
        size=100,
    )

    second = generate_values(
        seed=42,
        size=100,
    )

    np.testing.assert_array_equal(
        first,
        second,
    )
```

Also test:

- Seed reproducibility.
- Different seeds produce different sequences.
- Requested shape.
- Requested dtype.
- Distribution parameters.
- Batch generation.
- Edge-case injection.
- Unknown category generation.
- Large dataset generation.
- Parallel stream behavior where applicable.

Do not test random values against exact statistical results for small samples unless the test is intentionally checking reproducibility. Prefer tolerance-based statistical assertions over brittle exact-value assumptions when validating distribution properties.

## Debugging

When a randomized test fails, capture the generation configuration:

```python
print(
    {
        "seed": seed,
        "size": size,
        "distribution": "normal",
        "loc": 100.0,
        "scale": 20.0,
    }
)
```

Then reproduce:

```python
rng = np.random.default_rng(
    seed,
)

values = rng.normal(
    loc=100.0,
    scale=20.0,
    size=size,
)
```

For complex generators, also record:

```text
generator type
+
seed
+
configuration
+
generation order
+
batch sizes
```

This makes randomized failures operationally useful rather than mysterious.

## Interview Questions

### Why should modern NumPy code use `default_rng()`?

It provides the modern `Generator` interface with explicit random-state ownership rather than relying on legacy module-level global state.

### Does setting a seed make random data deterministic?

It makes the generator sequence reproducible when the relevant generator, configuration, call order, and generation logic remain the same.

### What is the difference between `rng.shuffle()` and `rng.permutation()`?

`shuffle()` modifies the supplied array in place. `permutation()` returns a permuted result without requiring the input to be modified.

### Why should random generators be passed into functions?

Explicit generator ownership improves testability, reproducibility, and control over random state.

### How would you generate reproducible data for a large benchmark?

Create a seeded `Generator` once, generate the dataset outside the timed processing section, and benchmark the processing operation separately.

### How do you generate data in batches?

Use one generator and request bounded `size` values repeatedly:

```python
batch = rng.normal(
    size=batch_size,
)
```

while processing each batch before generating the next.

### Is NumPy randomness suitable for authentication tokens?

No. Use a cryptographically secure source such as Python's `secrets` module.

### How would you create independent random streams for parallel workers?

Use separate generators with intentionally derived state, such as child states created through `SeedSequence.spawn()`.

### Why doesn't a fixed seed guarantee stable output after refactoring?

The generator state depends on the sequence and sizes of random calls. Changing the generation order can change all later values.

### What is the difference between random test data and production-representative data?

Random test data provides controlled variability, while production-representative data should reflect realistic distributions, correlations, boundaries, and failure modes.

## Key Takeaways

- Prefer NumPy's `Generator` API with explicit ownership and seeds for reproducible numerical data generation.
- Treat the seed, generator, distribution parameters, call sequence, and batch sizes as part of the reproducibility contract.
- Generate realistic synthetic data for benchmarking, ETL, and testing, but add explicit boundary and failure cases because randomness alone does not guarantee useful edge coverage.
- For large workloads and parallel systems, use bounded batches and intentionally derived random streams to control memory and preserve reproducibility.
- Never use NumPy's numerical random generators for cryptographic or security-sensitive randomness; use a cryptographically secure facility such as Python's `secrets` module instead.