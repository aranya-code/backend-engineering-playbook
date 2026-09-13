# Large Dataset Processing

A production-oriented Pandas pipeline for memory-efficient processing of large CSV datasets, featuring chunked ingestion, categorical dtype optimization, checkpointing, partition-based Parquet output, and benchmarking utilities.

---

## Overview

This project demonstrates the engineering decisions required when a dataset is too large to load into memory at once. It covers chunked processing with configurable chunk sizes, dtype optimization through categoricals, per-chunk validation, checkpointing for crash recovery, deterministic partition writing, and a benchmark suite for measuring throughput and memory usage.

These are the techniques that appear in backend data engineering when batch pipelines move from prototype-scale CSV files to datasets with millions or tens of millions of rows.

---

## Architecture

```text
data/raw/input.csv (large file)
          │
          ▼
    Chunked Ingestion
    (pd.read_csv with chunksize · column projection · low_memory)
          │
          ▼  (chunk by chunk)
    Per-Chunk Validation
    (schema · required values · numeric validity · domain rules)
          │
          ├──── data/staging/rejected.csv  (invalid records)
          │
          ▼
    Per-Chunk Transformation
    (dtype coercion · categoricals · derived columns · normalization)
          │
          ▼
    Partition Write
    (data/processed/part-00000001.parquet, part-00000002.parquet, …)
          │
          ▼
    Checkpoint
    (data/staging/checkpoints/chunk-00000001.parquet, …)
          │
          ▼  (after all chunks)
    Global Aggregation
    (overall metrics across all partitions)
          │
          ▼
    Processing Report
    (reports/processing_report.parquet)
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/ingestion.py` | Chunked CSV reading with column projection and schema pre-validation |
| `src/chunk_processor.py` | Per-chunk processing loop — validates, transforms, and tracks metrics |
| `src/transformation.py` | dtype coercion, categorical conversion, derived columns |
| `src/validation.py` | Schema, required-value, uniqueness, and domain-rule checks per chunk |
| `src/aggregation.py` | Cross-chunk metric aggregation into overall pipeline statistics |
| `src/storage.py` | Partition writes, checkpoint writes, report publication, atomic output |
| `src/pipeline.py` | Full pipeline orchestration — chunk loop, checkpointing, report generation |
| `src/config.py` | Typed runtime configuration with environment-variable overrides |

### Benchmark Scripts

| Script | Measures |
|---|---|
| `benchmarks/benchmark_memory.py` | Peak memory usage by chunk size |
| `benchmarks/benchmark_processing.py` | Throughput (rows/second) and wall-clock time |
| `benchmarks/benchmark_formats.py` | CSV vs. Parquet read/write performance and output size |

---

## Project Structure

```text
03- Large Dataset Processing/
├── benchmarks/
│   ├── benchmark_formats.py
│   ├── benchmark_memory.py
│   └── benchmark_processing.py
├── config/
│   ├── settings.yaml       # Baseline operational configuration
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── .gitignore
│   └── README.md           # Configuration reference
├── scripts/
│   └── run_pipeline.py     # CLI entry point
├── src/
│   ├── __init__.py
│   ├── aggregation.py
│   ├── chunk_processor.py
│   ├── config.py
│   ├── ingestion.py
│   ├── pipeline.py
│   ├── storage.py
│   ├── transformation.py
│   └── validation.py
└── tests/
    ├── __init__.py
    ├── test_aggregation.py
    ├── test_chunk_processor.py
    ├── test_pipeline.py
    ├── test_transformation.py
    └── test_validation.py
```

---

## Key Concepts Demonstrated

### Chunked Ingestion

The pipeline never loads the entire input file into memory:

```python
pd.read_csv(
    input_path,
    chunksize=50_000,
    usecols=["order_id", "customer_id", "region", "status", "product", "quantity", "amount", "created_at"],
    low_memory=True,
)
```

**Column projection** (`usecols`) reduces memory per chunk by skipping unused columns at read time — before Pandas allocates any DataFrame storage.

**`low_memory=True`** allows Pandas to use mixed-type inference per chunk, which is acceptable when validation follows immediately.

### Chunk Size Tuning

Chunk size is the primary performance knob. There is no universally correct value:

| Chunk size | Effect |
|---|---|
| Too small | High Python overhead, many I/O operations, excessive checkpoint frequency |
| Too large | High peak memory, potential OOM on constrained machines |
| Right-sized | Measured against your actual data shape, row width, and transformation complexity |

The `benchmarks/` scripts exist specifically to make this measurement empirical rather than guesswork.

### Categorical Dtype Optimization

Low-cardinality string columns (`region`, `status`, `product`) are converted to `category` dtype after ingestion:

```python
df["region"] = df["region"].astype("category")
```

For a column with 5 unique values repeated across 5 million rows, `category` dtype stores the values once and uses integer codes for each row — typically reducing memory usage by 5–10× compared to `object` dtype.

**Do not categorize every string column.** High-cardinality columns (e.g., unique order IDs or free-form text) may gain nothing or even increase memory.

### Per-Chunk Validation

Each chunk is validated independently before any transformation runs:

- Schema presence check (required columns)
- Required-value check (non-null identifiers)
- Numeric validity (non-negative amounts, valid quantities)
- Domain-rule enforcement (allowed status values)
- Memory budget check (warn or fail if a chunk exceeds configured limits)

Invalid records per chunk are quarantined into `rejected.csv`. The pipeline can either continue processing remaining chunks or abort, depending on `fail_on_validation`.

### Deterministic Partition Output

Processed chunks are written as numbered Parquet partitions:

```text
data/processed/
├── part-00000001.parquet
├── part-00000002.parquet
├── part-00000003.parquet
└── ...
```

Deterministic naming is required for correct checkpoint-based resume semantics — a resumed run can identify which chunks were already completed and skip them.

### Checkpointing and Resume

The pipeline supports crash recovery for long-running batch jobs:

```text
data/staging/checkpoints/
├── chunk-00000001.parquet
├── chunk-00000002.parquet
└── ...
```

When `resume_enabled = true`, the pipeline reads the checkpoint directory on startup and skips already-completed chunks. This avoids re-processing the entire dataset after a mid-run failure.

Checkpoint metadata should include enough context to detect stale checkpoints from incompatible pipeline versions.

### Atomic Writes

All outputs (partitions, checkpoints, reports) are written via a temporary file and then moved atomically into place. Downstream consumers always see complete files.

---

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `chunk_size` | `50000` | Rows per processing chunk |
| `max_rows` | `null` | Optional row limit (useful for testing) |
| `parquet_compression` | `snappy` | Parquet output compression |
| `atomic_writes` | `true` | Atomic file replacement |
| `fail_on_schema_error` | `true` | Abort on schema violations |
| `fail_on_validation` | `true` | Abort on data-quality failures |
| `checkpointing.enabled` | `true` | Write checkpoints during processing |
| `checkpointing.interval` | `10` | Write checkpoint every N chunks |
| `checkpointing.resume_enabled` | `false` | Skip completed chunks on restart |
| `memory.target_memory_mb` | `512` | Target memory budget per chunk |
| `memory.warning_threshold_percent` | `80` | Warn when memory budget is approached |

Environment variable overrides:

```bash
LARGE_DATASET_PIPELINE_CHUNK_SIZE=100000
LARGE_DATASET_PIPELINE_TARGET_MEMORY_MB=1024
LARGE_DATASET_PIPELINE_LOG_LEVEL=INFO
```

See [`config/README.md`](config/README.md) for the full configuration reference including deployment profiles for local, CI, and production environments.

---

## Requirements

- Python ≥ 3.11
- pandas ≥ 2.2, < 3.0
- pyarrow ≥ 16, < 22
- PyYAML ≥ 6.0, < 7.0

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running the Pipeline

```bash
# Basic run
python scripts/run_pipeline.py \
  --input data/raw/input.csv \
  --output data/processed/output.parquet \
  --report reports/processing_report.parquet

# Override chunk size
python scripts/run_pipeline.py \
  --input data/raw/input.csv \
  --chunk-size 100000

# Enable checkpointing
python scripts/run_pipeline.py \
  --input data/raw/input.csv \
  --enable-checkpoints

# Resume an interrupted run
python scripts/run_pipeline.py \
  --input data/raw/input.csv \
  --resume
```

---

## Running Tests

```bash
# Full test suite
pytest

# Specific modules
pytest tests/test_chunk_processor.py
pytest tests/test_validation.py

# With coverage
pytest --cov=src --cov-report=term-missing

# Static analysis
ruff check src tests scripts benchmarks

# Type checking
mypy src
```

---

## Running Benchmarks

```bash
# Memory usage by chunk size
python benchmarks/benchmark_memory.py --rows 1000000

# Throughput benchmark
python benchmarks/benchmark_processing.py --rows 1000000 --repetitions 3

# Storage format comparison
python benchmarks/benchmark_formats.py --rows 1000000
```

Run benchmarks on infrastructure representative of your deployment environment. CPU speed, filesystem type, available RAM, Python version, and Pandas version all affect results. Vary at least: row count, chunk size, column count, and string cardinality.

---

## Memory Model

Understanding memory consumption requires thinking at the chunk level:

```text
raw CSV bytes
     ↓
parsed DataFrame (chunk)         ← baseline
     ↓
transformation intermediate      ← temporary expansion
     ↓
validated DataFrame              ← may be smaller after rejection
     ↓
serialized Parquet               ← columnar, compressed
```

Peak memory during a chunk can be 2–4× the final DataFrame size because of temporary columns, grouping structures, and Pandas internal copies.

Monitor:
- input chunk size in bytes
- DataFrame `.memory_usage(deep=True)` 
- process RSS via `psutil` or `memory_profiler`
- transformation expansion ratio

---

## Production Considerations

| Concern | Approach |
|---|---|
| Memory | Chunked reads, column projection, categorical dtypes |
| Reliability | Checkpointing, atomic writes, deterministic partition naming |
| Recoverability | Resume-on-crash with chunk-level checkpoints |
| Performance | Benchmarked chunk sizing, Parquet output, early column projection |
| Observability | Per-chunk metrics, overall aggregation, processing report |
| Scalability | For truly massive datasets (billions of rows), consider DuckDB, Polars, AWS Glue, or Spark |

---

## Navigation

| # | Section |
|---|---|
| [01](../01-%20Fundamentals/README.md) | Fundamentals |
| [02](../02-%20Reading%20and%20Writing%20Data/README.md) | Reading and Writing Data |
| [03](../03-%20Selecting%20and%20Filtering/README.md) | Selecting and Filtering |
| [04](../04-%20Data%20Cleaning/README.md) | Data Cleaning |
| [05](../05-%20Data%20Transformation/README.md) | Data Transformation |
| [06](../06-%20Grouping%20and%20Aggregation/README.md) | Grouping and Aggregation |
| [07](../07-%20Combining%20Data/README.md) | Combining Data |
| [08](../08-%20Sorting%20Ranking%20and%20Statistics/README.md) | Sorting Ranking and Statistics |
| [09](../09-%20Strings%20and%20Datetime/README.md) | Strings and Datetime |
| [10](../10-%20Performance%20and%20Memory/README.md) | Performance and Memory |
| [11](../11-%20Backend%20and%20Data%20Engineering/README.md) | Backend and Data Engineering |
| [12](../12-%20Interview%20Preparation/README.md) | Interview Preparation |
| **13** | **Projects** |
| ↳ [01](../01-%20E-Commerce%20Data%20Pipeline/README.md) | E-Commerce Data Pipeline |
| ↳ [02](../02-%20API%20Data%20Processing%20Pipeline/README.md) | API Data Processing Pipeline |
| ↳ [03](README.md) | Large Dataset Processing |
