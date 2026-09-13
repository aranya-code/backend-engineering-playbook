# README

## Overview

The `config` directory contains runtime configuration for the Concurrent Data Processor. It separates operational settings from application logic so concurrency limits, input/output behavior, reliability controls, and observability defaults can be changed without modifying processing code.

The primary configuration file is `settings.yaml`. It provides development-oriented defaults, while environment variables or deployment-specific configuration should be used for production overrides.

The configuration is designed around four concerns:

- **Processing behavior** — input/output formats, batching, and error handling.
- **Concurrency** — thread, process, and asyncio execution limits.
- **Reliability** — backpressure and graceful shutdown behavior.
- **Operations** — logging, metrics, progress reporting, and runtime safety.

## Configuration Structure

```text
config/
├── settings.yaml
├── pyproject.toml
└── .gitignore
```

`settings.yaml` is intended to describe the operational configuration of the processor. `pyproject.toml` defines Python packaging, development dependencies, test configuration, linting, and type checking.

## Settings

The main configuration areas are:

| Section | Purpose |
|---|---|
| `environment` | Identifies the runtime environment |
| `application` | Application identity and version |
| `input` | Source file and input format |
| `output` | Destination, serialization, and write behavior |
| `processing` | Processing mode, worker count, batching, and failure behavior |
| `concurrency` | Per-model concurrency limits |
| `backpressure` | Bounds pending work to control memory usage |
| `performance` | Benchmarking and metrics configuration |
| `logging` | Application log configuration |
| `observability` | Metrics and progress reporting |
| `reliability` | Failure and shutdown behavior |
| `security` | Runtime restrictions on file paths |

## Input and Output

Input and output configuration should be explicit because data-processing jobs commonly operate on large files.

```yaml
input:
  path: data/input/records.jsonl
  format: jsonl
  encoding: utf-8

output:
  path: data/output/processed.jsonl
  format: jsonl
  encoding: utf-8
  atomic_write: true
```

For large datasets, the processor should stream records rather than loading the entire input into memory. Output should similarly be produced incrementally.

Atomic output is useful for batch jobs because a failed processing run should not leave a partially written file that appears to be a successful result. A production implementation can write to a temporary destination and replace the final file only after successful completion.

## Processing Configuration

```yaml
processing:
  concurrency_mode: thread
  max_workers: 4
  batch_size: 100
  continue_on_error: false
  preserve_order: true
```

`concurrency_mode` selects the execution model:

| Mode | Best suited for |
|---|---|
| `thread` | Blocking I/O and external service calls |
| `process` | CPU-intensive Python workloads |
| `asyncio` | High-volume asynchronous I/O |

`max_workers` should not be selected arbitrarily. Increasing concurrency can improve throughput until another resource becomes the bottleneck.

Typical constraints include:

- CPU capacity
- Memory
- File-system throughput
- Database connection limits
- External API rate limits
- Network bandwidth
- Downstream service capacity

`batch_size` controls how many records are grouped into a processing unit. Larger batches can reduce scheduling overhead but increase memory usage and failure granularity.

`preserve_order` is useful when output ordering must match input ordering. It can reduce opportunities for immediate result emission when tasks complete out of order.

## Concurrency Limits

The configuration defines separate limits for each concurrency model:

```yaml
concurrency:
  thread:
    max_workers: 4
  process:
    max_workers: 4
  asyncio:
    max_concurrency: 20
```

These limits should be treated as resource-protection controls rather than merely performance settings.

### Threads

Threads are appropriate for blocking I/O because other threads can continue while one thread waits on network or file operations.

For example:

```text
Record
  │
  ├── Thread 1 ──► External API
  ├── Thread 2 ──► External API
  ├── Thread 3 ──► External API
  └── Thread 4 ──► External API
```

Threads generally should not be used as a way to obtain CPU parallelism for Python bytecode in traditional GIL-enabled CPython.

### Processes

Processes provide separate Python interpreters and address spaces. They are useful when CPU-bound work needs parallel execution.

```text
                 ┌── Process 1 ──► CPU workload
Input ───────────┼── Process 2 ──► CPU workload
                 ├── Process 3 ──► CPU workload
                 └── Process 4 ──► CPU workload
```

The trade-off is higher process-management and serialization overhead.

### Asyncio

Asyncio uses cooperative concurrency. Tasks yield control while waiting for asynchronous I/O.

```text
Event Loop
   │
   ├── Task A ──► await I/O ──┐
   ├── Task B ──► await I/O ──┤
   ├── Task C ──► await I/O ──┤
   └── Task D ──► await I/O ──┘
                             │
                        Event Loop
```

Asyncio is effective for high numbers of I/O-bound operations, but blocking functions must not execute directly on the event loop.

## Backpressure

Backpressure prevents producers from generating work faster than consumers can process it.

```yaml
backpressure:
  enabled: true
  max_pending_tasks: 1000
```

Without a bound on pending work, a fast input reader can enqueue millions of records while workers process them slowly. This can cause excessive memory consumption and eventually process termination.

A production pipeline should generally follow:

```text
Input Reader
     │
     ▼
Bounded Queue
     │
     ├──► Worker
     ├──► Worker
     ├──► Worker
     └──► Worker
     │
     ▼
Output
```

The queue capacity acts as a memory and workload-control boundary.

## Error Handling

The processor should distinguish between:

- Record-level failures
- Batch-level failures
- Infrastructure failures
- Configuration failures
- Process termination

For a fail-fast workload:

```yaml
processing:
  continue_on_error: false
```

the first unrecoverable processing failure can terminate the run.

For workloads where individual bad records should not invalidate the entire dataset, error isolation can be enabled:

```yaml
processing:
  continue_on_error: true
```

When continuing after errors, failed records should be observable and, where appropriate, written to a dead-letter or error output rather than silently discarded.

## Observability

The configuration enables metrics and periodic progress reporting:

```yaml
performance:
  benchmark_enabled: true
  collect_metrics: true

observability:
  metrics_enabled: true
  log_progress: true
  progress_interval_records: 1000
```

Useful processing metrics include:

- Records processed
- Records succeeded
- Records failed
- Batches processed
- Processing duration
- Records per second
- Failure rate
- Queue depth
- Worker utilization
- Input and output throughput

Throughput should be measured at the system boundary, not inferred only from individual worker timings.

For production workloads, structured logs should include identifiers such as:

- Job or run ID
- Input source
- Processing mode
- Worker configuration
- Batch size
- Record counts
- Duration
- Failure counts

Avoid logging complete input records when they may contain credentials, personal data, tokens, or other sensitive information.

## Reliability

```yaml
reliability:
  fail_fast: true
  graceful_shutdown: true
  shutdown_timeout_seconds: 30
```

Graceful shutdown is important when running the processor inside Docker, Kubernetes, or CI/CD environments.

A graceful shutdown should generally:

1. Stop accepting new work.
2. Allow in-flight work to finish when possible.
3. Release thread/process/event-loop resources.
4. Flush or safely finalize output.
5. Emit final metrics.
6. Exit with an appropriate status code.

The shutdown timeout prevents a worker from hanging indefinitely.

## Configuration and Environment Separation

Development configuration can safely contain non-sensitive defaults:

```yaml
environment: development

processing:
  concurrency_mode: thread
  max_workers: 4
```

Production deployments should avoid committing secrets or environment-specific credentials to source control.

Prefer:

- Environment variables
- Container secrets
- Kubernetes Secrets
- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- Deployment-specific configuration

The configuration loader should establish a clear precedence model, for example:

```text
Built-in defaults
      │
      ▼
settings.yaml
      │
      ▼
Environment variables
      │
      ▼
Explicit CLI arguments
```

The highest-precedence value should be the most explicit runtime override.

## Path Safety

The configuration includes:

```yaml
security:
  allow_arbitrary_input_paths: false
  allow_arbitrary_output_paths: false
```

Path restrictions are relevant when configuration can be influenced by untrusted users or external systems. Arbitrary paths can potentially expose sensitive files or permit writes outside an intended working directory.

Production implementations should validate paths against approved directories when configuration is externally controlled.

For example, an application processing uploaded files should not blindly accept:

```text
../../../../etc/passwd
```

as an input path.

Path validation should complement operating-system permissions and container isolation rather than replace them.

## Benchmarking

The project contains dedicated benchmarks for the three concurrency models:

```text
benchmarks/
├── benchmark_threads.py
├── benchmark_processes.py
└── benchmark_asyncio.py
```

The benchmarks should be run independently from production processing runs.

Example:

```bash
python benchmarks/benchmark_threads.py
python benchmarks/benchmark_processes.py
python benchmarks/benchmark_asyncio.py
```

Benchmark results should be interpreted based on workload characteristics.

| Workload | Preferred model |
|---|---|
| Blocking HTTP requests | Threads or asyncio |
| Async HTTP client | asyncio |
| CPU-heavy Python transformation | Processes |
| Mixed I/O and CPU work | Separate stages or carefully bounded workers |
| Very large files | Streaming pipeline with bounded concurrency |

A benchmark should measure realistic workloads, include warm-up effects where relevant, use multiple repetitions, and avoid drawing conclusions from a single run.

## Production Deployment

For containerized execution, configuration should normally be supplied through the deployment environment rather than modifying the image.

```text
Container Image
      │
      ▼
Configuration
      │
      ├── Environment
      ├── Mounted configuration
      └── Secret provider
      │
      ▼
Concurrent Data Processor
      │
      ├── Input
      ├── Bounded Workers
      ├── Metrics / Logs
      └── Output
```

In Kubernetes, resource requests and limits should be considered together with `max_workers`. Setting a high worker count inside a container with a small CPU or memory limit can reduce performance or cause resource exhaustion.

For AWS batch-style workloads, concurrency should similarly account for the capacity of downstream services such as S3, RDS, DynamoDB, or external APIs.

## Common Configuration Mistakes

### Unbounded concurrency

Increasing worker counts without measuring resource usage can cause:

- Context-switching overhead
- Memory pressure
- Database connection exhaustion
- API throttling
- CPU saturation

Concurrency should be bounded and benchmarked.

### Using threads for CPU parallelism

Threads do not generally provide Python-bytecode CPU parallelism in traditional GIL-enabled CPython. Processes are usually the better model for CPU-heavy workloads.

### Blocking the asyncio event loop

Calling blocking file, database, or network APIs directly from an asyncio task can stall unrelated tasks.

Use asynchronous libraries where available or explicitly isolate unavoidable blocking work.

### Loading the entire dataset into memory

This pattern does not scale:

```python
records = list(reader.read())
```

Prefer streaming and bounded processing so memory usage remains approximately independent of total input size.

### Treating configuration as validation

Configuration values should be validated when loaded. Invalid worker counts, paths, formats, or concurrency modes should fail before processing begins.

### Committing secrets

API keys, database passwords, cloud credentials, and tokens should never be stored in `settings.yaml` or source control.

## Key Takeaways

- Configuration separates processing behavior and operational limits from application code.
- Concurrency limits, batch sizes, and backpressure are resource-protection mechanisms as much as performance settings.
- Large datasets should be processed through bounded, streaming pipelines rather than loaded entirely into memory.
- Production configuration should validate inputs, avoid secrets in source control, and account for container and downstream-service capacity.
- Benchmark threads, processes, and asyncio with representative workloads before selecting a concurrency model.