# README

## Overview

This section contains three practical NumPy projects designed to apply and demonstrate the concepts covered across the engineering playbook.

The projects progress from a foundational batch-processing pipeline through vectorized transformation to systematic performance benchmarking:

```text
Numerical Data Processor
→ validation, transformation, aggregation, export

Vectorized Data Transformation
→ masking, normalization, broadcasting, memory-aware pipeline

Performance Benchmarking
→ CPU vs loop overhead, dtype comparison, views vs copies, broadcasting cost
```

Each project is a standalone Python package with its own source, tests, configuration, and scripts. The emphasis is on production-oriented engineering patterns rather than academic exercises.

## Navigation

| # | File | Description |
|---|---|---|
| 01 | [01- Numerical Data Processor](./01-%20Numerical%20Data%20Processor/README.md) | Batch numerical pipeline covering validation, transformation, aggregation, and export |
| 02 | [02- Vectorized Data Transformation](./02-%20Vectorized%20Data%20Transformation/README.md) | Vectorized pipeline with masking, normalization, broadcasting, and memory-aware processing |
| 03 | [03- Performance Benchmarking](./03-%20Performance%20Benchmarking/README.md) | Systematic benchmarking of Python vs NumPy, dtypes, views vs copies, and broadcasting cost |

## Project Structure

Each project follows the same layout:

```text
<project>/
├── config/
│   ├── pyproject.toml
│   └── settings.yaml
├── src/
├── tests/
├── scripts/
└── README.md
```

`config/` holds tooling and runtime configuration. `src/` holds the implementation. `tests/` holds the test suite. `scripts/` holds standalone execution scripts.

## Project Summaries

### 01- Numerical Data Processor

A production-oriented numerical processing pipeline built around a validated batch workflow:

```text
Input file
    ↓
Loader
    ↓
Validator
    ↓
Processor
    ↓
Statistics
    ↓
Exporter
```

Key source modules:

| Module | Responsibility |
|---|---|
| `loader.py` | Read and deserialize numerical input |
| `validator.py` | Validate shape, dtype, and numerical constraints |
| `processor.py` | Apply vectorized transformations |
| `statistics.py` | Compute summary statistics |
| `exporter.py` | Persist processed output |
| `pipeline.py` | Orchestrate the full processing flow |
| `config.py` | Load and validate runtime configuration |

Concepts applied: array creation, validation, boolean masking, aggregation, dtype selection, batch processing, file I/O.

### 02- Vectorized Data Transformation

A vectorized data transformation pipeline focused on memory-aware numerical operations:

```text
Input file
    ↓
Loader
    ↓
Masking
    ↓
Transformations
    ↓
Normalization
    ↓
Aggregation
    ↓
Exporter
```

Key source modules:

| Module | Responsibility |
|---|---|
| `loader.py` | Read and validate numerical input |
| `masking.py` | Build and apply boolean masks |
| `transformations.py` | Apply vectorized scaling and offset operations |
| `normalization.py` | Normalize values into a target range |
| `aggregation.py` | Compute reductions across the processed dataset |
| `exporter.py` | Persist transformed output |
| `pipeline.py` | Orchestrate the transformation flow |
| `config.py` | Load and validate runtime configuration |

Concepts applied: vectorization, broadcasting, masking, normalization, temporary array awareness, memory-aware batching.

### 03- Performance Benchmarking

A systematic benchmarking suite that measures and compares NumPy execution across multiple performance dimensions:

```text
Datasets
    ↓
Python processor vs NumPy processor
    ↓
Benchmark runner
    ↓
Memory measurement
    ↓
Reporting
```

Key source modules:

| Module | Responsibility |
|---|---|
| `datasets.py` | Generate deterministic benchmark datasets |
| `python_processor.py` | Python-loop reference implementations |
| `numpy_processor.py` | Vectorized NumPy implementations |
| `benchmarks.py` | Benchmark orchestration and timing |
| `memory.py` | Memory usage measurement |
| `reporting.py` | Structured result output |

Benchmarks cover: Python loops vs vectorization, dtype memory and throughput, views vs copy-producing operations, and broadcasting cost.

Concepts applied: benchmarking methodology, vectorization vs loops, dtype optimization, views vs copies performance, broadcasting performance, memory usage.

## Engineering Focus

The projects emphasize the same principles as the playbook sections:

- Validate input before allocating or transforming.
- Choose dtypes appropriate for precision and memory constraints.
- Prefer vectorized operations over Python loops for dense numerical work.
- Understand whether operations return views or allocate copies.
- Process large datasets in bounded batches.
- Measure performance rather than assuming vectorization is always faster.
- Keep configuration, source, and tests clearly separated.

## Relationship to the Playbook

Each project draws on specific sections of the NumPy curriculum:

| Project | Primary Sections |
|---|---|
| Numerical Data Processor | Fundamentals, Numerical Operations, Data Processing |
| Vectorized Data Transformation | Array Manipulation, Numerical Operations, Data Processing |
| Performance Benchmarking | Performance, Fundamentals, Array Manipulation |

The playbook sections explain the design reasoning and trade-offs. The projects demonstrate those concepts in runnable, tested code.

## Key Takeaways

- The three projects cover the full range of practical NumPy workloads: batch processing, vectorized transformation, and performance measurement.
- Each project is a standalone package with its own configuration, tests, and scripts following a consistent layout.
- The implementations apply production-oriented patterns including validation, bounded batching, dtype selection, memory awareness, and structured configuration.
- Performance benchmarking is treated as a disciplined engineering activity with reproducible datasets, warmup runs, multiple timing statistics, and memory measurement.
