# Concurrent Data Processor

A production-oriented Python data processor that demonstrates all three concurrency models — `asyncio`, `threading`, and `multiprocessing` — applied to the same JSONL record-processing workload, with backpressure, metrics, atomic output, and benchmark scripts for measuring each model's performance characteristics.

---

## Overview

This project answers a question that comes up constantly in backend engineering: which Python concurrency model should I use for my workload? It implements the same processor using all three approaches so their trade-offs can be observed directly rather than theorized about.

The processor reads JSONL records, applies a configurable transformation per record, writes output atomically, and collects per-run metrics. A benchmark suite compares throughput and resource usage across concurrency models on realistic workloads.

---

## Architecture

```text
Input (JSONL)
     │
     ▼
InputReader (src/input.py)
     │  reads records in batches
     │  controls backpressure
     ▼
Concurrency Layer (src/concurrency.py)
     ├── AsyncIO mode    → asyncio.gather with Semaphore
     ├── Thread mode     → ThreadPoolExecutor
     └── Process mode    → ProcessPoolExecutor
     │
     ▼
Worker (src/worker.py)
     │  applies processor function to each record
     ▼
Processor (src/processor.py)
     │  validate and transform each record
     ▼
OutputWriter (src/output.py)
     │  collects results
     │  atomic write to JSONL / JSON
     ▼
Metrics (src/metrics.py)
     │  processed / failed / duration / throughput
```

### Source Modules

| Module | Responsibility |
|---|---|
| `src/processor.py` | `process_record()` — validates and transforms a single record |
| `src/concurrency.py` | Three concurrency adapters: asyncio, threads, processes |
| `src/worker.py` | Per-record execution with error isolation |
| `src/input.py` | JSONL reader with batch iteration and backpressure |
| `src/output.py` | Result collector and atomic JSONL/JSON writer |
| `src/metrics.py` | `ProcessingMetrics` — throughput, duration, failure counts |
| `src/config.py` | `ProcessorConfig` — typed runtime configuration |
| `src/main.py` | Orchestration — wires all components together |

### Benchmark Scripts

| Script | What it measures |
|---|---|
| `benchmarks/benchmark_asyncio.py` | asyncio throughput and concurrency scaling |
| `benchmarks/benchmark_threads.py` | threading throughput and GIL impact |
| `benchmarks/benchmark_processes.py` | multiprocessing throughput and CPU scaling |

---

## Project Structure

```text
04- Concurrent Data Processor/
├── benchmarks/
│   ├── benchmark_asyncio.py
│   ├── benchmark_threads.py
│   └── benchmark_processes.py
├── config/
│   ├── .gitignore
│   ├── pyproject.toml      # Project metadata and tooling
│   ├── settings.yaml       # Baseline configuration reference
│   └── README.md           # Configuration reference
├── scripts/
│   └── run_processor.py    # CLI entry point
├── src/
│   ├── __init__.py
│   ├── concurrency.py
│   ├── config.py
│   ├── input.py
│   ├── main.py
│   ├── metrics.py
│   ├── output.py
│   ├── processor.py
│   └── worker.py
└── tests/
    ├── __init__.py
    ├── test_concurrency.py
    ├── test_processor.py
    └── test_worker.py
```

---

## Key Concepts Demonstrated

### Concurrency Model Comparison

The same workload is run through all three Python concurrency models:

| Model | Best for | GIL impact | Parallelism |
|---|---|---|---|
| `asyncio` | I/O-bound, high concurrency | Not relevant | Cooperative, single thread |
| `threading` | I/O-bound with blocking calls | Limits CPU work | Concurrent, one CPU at a time |
| `multiprocessing` | CPU-bound (serialization, transformation) | Bypassed | True parallel execution |

This makes the trade-offs concrete and measurable rather than theoretical.

### Backpressure

The input reader uses bounded batching to prevent unbounded memory growth when records arrive faster than they can be processed. The concurrency layer respects this boundary rather than queuing unlimited work:

```text
InputReader → batch of N records
                    │
                    ▼
          Concurrency layer processes batch
                    │
                    ▼
          OutputWriter collects results
                    │
                    ▼
          Next batch (backpressure respected)
```

### Atomic Output

Results are written to a temporary file and replaced into the final output path atomically. Consumers always see a complete previous output or a complete new output — never a partially written file.

### Error Isolation

Each record is processed independently. One failed record does not abort the batch. Failed records are counted in metrics and can be written to a rejected output file.

### Bounded Concurrency

The asyncio adapter uses `asyncio.Semaphore` to limit concurrent coroutines. The thread and process adapters use `max_workers` in `ThreadPoolExecutor` / `ProcessPoolExecutor`. All three respect the configured worker count.

### Metrics

`ProcessingMetrics` collects per-run statistics:

- `total_records` — input record count
- `processed` — successfully transformed records
- `failed` — records that raised exceptions
- `duration_seconds` — total elapsed time
- `throughput_rps` — records per second

The benchmark scripts use these metrics to compare concurrency models.

### Typed Configuration

`ProcessorConfig` is loaded from environment variables and the settings file:

| Setting | Purpose |
|---|---|
| `input.path` | Source JSONL file |
| `output.path` | Destination file |
| `output.atomic_write` | Enable atomic replacement |
| `processing.mode` | `asyncio` / `threads` / `processes` |
| `processing.workers` | Worker count |
| `processing.batch_size` | Records per batch |
| `processing.fail_fast` | Abort on first error |
| `backpressure.max_pending` | Max queued batches |

---

## Configuration

See [`config/README.md`](config/README.md) for the full configuration reference.

---

## Requirements

- Python ≥ 3.12
- No external dependencies (stdlib only)

---

## Installation

```bash
pip install -e ".[dev]"
```

---

## Running the Processor

```bash
# asyncio mode
python scripts/run_processor.py \
  --input data/input/records.jsonl \
  --output data/output/processed.jsonl \
  --mode asyncio \
  --workers 10

# thread mode
python scripts/run_processor.py \
  --input data/input/records.jsonl \
  --output data/output/processed.jsonl \
  --mode threads \
  --workers 8

# process mode
python scripts/run_processor.py \
  --input data/input/records.jsonl \
  --output data/output/processed.jsonl \
  --mode processes \
  --workers 4

# installed entry point
run-processor --input ... --output ... --mode asyncio
```

---

## Running Benchmarks

```bash
python benchmarks/benchmark_asyncio.py --records 100000
python benchmarks/benchmark_threads.py --records 100000
python benchmarks/benchmark_processes.py --records 100000
```

Run on representative hardware with realistic record sizes. CPU speed, core count, record complexity, and I/O characteristics all affect results.

---

## Running Tests

```bash
pytest
pytest --cov=src --cov-report=term-missing

ruff check src tests scripts benchmarks
mypy src
```

---

## When to Use Each Model

| Workload | Recommended model | Reason |
|---|---|---|
| Calling external APIs, network I/O | `asyncio` | High concurrency with low overhead |
| File I/O, database queries | `asyncio` or `threads` | Both work; asyncio preferred for new code |
| CPU-intensive transformation | `multiprocessing` | Bypasses the GIL; real parallelism |
| Blocking third-party libraries | `threads` | Releases GIL during blocking calls |
| Mixed I/O + CPU | Hybrid executor | Asyncio for I/O, process pool for CPU work |

---

## Production Considerations

| Concern | Approach |
|---|---|
| Memory | Bounded batch size and backpressure prevent OOM |
| Reliability | Atomic output, error isolation, fail-fast option |
| Observability | Per-run metrics, failed record count, throughput |
| Scalability | Increase workers or switch to process mode for CPU-bound work |
| Data safety | Never overwrite output until all records processed (atomic write) |

---

## Navigation

| ↳ [01](../01-%20REST%20API%20Service/README.md) | REST API Service |
| ↳ [02](../02-%20Async%20API%20Client/README.md) | Async API Client |
| ↳ [03](../03-%20Background%20Job%20System/README.md) | Background Job System |
| ↳ [04](README.md) | Concurrent Data Processor |
| ↳ [05](../05-%20Webhook%20Processing%20Service/README.md) | Webhook Processing Service |
