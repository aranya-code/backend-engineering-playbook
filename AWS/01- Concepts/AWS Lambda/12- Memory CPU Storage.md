# 12- Memory CPU Storage

# Memory, CPU and Ephemeral Storage

One of the biggest misconceptions about AWS Lambda is that **memory is the only configurable compute resource**.

In reality, the memory configuration controls much more than RAM.

Increasing Lambda memory also increases:

- CPU allocation
- Network throughput
- Disk I/O
- Overall compute performance

Choosing the correct memory configuration is one of the easiest ways to improve Lambda performance while potentially reducing costs.

---

# Resource Allocation Model

Unlike EC2, Lambda does not let you configure CPU directly.

Instead, AWS automatically allocates CPU proportional to the configured memory.

```text
Configure Memory

↓

AWS Allocates

├── RAM
├── CPU
├── Network Bandwidth
└── Disk Throughput
```

---

# Configurable Resources

Lambda exposes three primary compute-related resources.

| Resource | Configurable |
|-----------|--------------|
| Memory | ✅ |
| Ephemeral Storage (/tmp) | ✅ |
| Timeout | ✅ |

CPU is automatically determined based on the memory setting.

---

# Memory Allocation

Lambda memory ranges from:

```
128 MB

↓

10,240 MB (10 GB)
```

Memory can be increased in **1 MB increments**.

Example:

```
128 MB

256 MB

512 MB

1024 MB

2048 MB

4096 MB

8192 MB

10240 MB
```

---

# CPU Allocation

AWS automatically scales CPU with memory.

Approximate relationship:

```text
128 MB

↓

Very Small CPU Share

------------------------

1024 MB

↓

Much Higher CPU

------------------------

2048 MB

↓

~1 vCPU Equivalent

------------------------

10240 MB

↓

Multiple vCPUs
```

The exact allocation is managed by AWS and may evolve over time.

---

# Why CPU Matters

CPU affects:

- JSON parsing
- Compression
- Encryption
- Image resizing
- Video transcoding
- PDF generation
- Machine learning inference

Example:

```
512 MB

↓

5 Seconds

----------------

2048 MB

↓

1.5 Seconds
```

Although the memory allocation is higher, the shorter execution time can result in a lower overall cost.

---

# Network Throughput

Higher memory settings increase available network throughput.

Example:

```text
Lambda

↓

Download from S3

↓

Upload to DynamoDB
```

Higher memory generally results in faster data transfers.

---

# Disk Throughput

Lambda also allocates higher disk throughput as memory increases.

Useful for workloads involving:

- ZIP extraction
- Image processing
- Temporary file creation
- Video processing

---

# Ephemeral Storage

Every Lambda execution environment includes temporary storage mounted at:

```text
/tmp
```

This storage is isolated to the execution environment.

---

# Default Storage

Default:

```
512 MB
```

Configurable up to:

```
10 GB
```

---

# Storage Lifecycle

```text
Execution Environment

↓

/tmp

↓

Freeze

↓

Warm Start

↓

Reuse

↓

Environment Destroyed

↓

Storage Deleted
```

Files survive warm starts but are removed when the execution environment is destroyed.

---

# Typical Use Cases

Use `/tmp` for:

- Image resizing
- PDF generation
- ZIP extraction
- CSV processing
- Temporary reports
- ML model caching

Example:

```python
with open("/tmp/report.pdf", "wb") as file:
    file.write(data)
```

---

# Memory vs /tmp

| Resource | Purpose |
|----------|----------|
| Memory | Runtime execution |
| /tmp | Temporary file storage |

Example:

```text
Memory

↓

Python Objects

↓

Variables

↓

Functions
```

```
/tmp

↓

Images

↓

PDFs

↓

CSV Files
```

---

# Memory Usage

Python objects consume memory.

Example:

```python
data = []

for i in range(1000000):
    data.append(i)
```

Large in-memory collections increase RAM usage.

---

# Memory Exhaustion

Suppose memory is configured as:

```
512 MB
```

Application requires:

```
900 MB
```

Result:

```text
Out Of Memory

↓

Lambda Terminated
```

CloudWatch logs:

```
Runtime exited with error: signal: killed
```

---

# CPU-Bound Workloads

Examples:

- Encryption
- Compression
- Image manipulation
- Video encoding
- Hash generation

Increasing memory often significantly improves execution time.

---

# Memory-Bound Workloads

Examples:

- Large JSON documents
- CSV parsing
- Data aggregation
- ML inference
- Large Pandas DataFrames

Choose sufficient memory to avoid out-of-memory failures.

---

# I/O-Bound Workloads

Examples:

- S3 downloads
- Database queries
- HTTP requests

Increasing memory has less impact unless network throughput becomes the bottleneck.

---

# Example Benchmark

Suppose the same function is tested with different memory settings.

| Memory | Duration |
|----------|----------|
| 128 MB | 8.5 sec |
| 512 MB | 3.4 sec |
| 1024 MB | 1.8 sec |
| 2048 MB | 1.1 sec |

Higher memory may actually reduce total cost because billing is based on both memory and execution duration.

---

# Memory and Cost

Lambda pricing is based on:

```text
Memory Allocated

×

Execution Duration
```

Example:

```
128 MB

↓

10 Seconds

----------------

1024 MB

↓

1 Second
```

Although the second configuration uses more memory, the shorter duration may make it equally expensive—or even cheaper.

Always benchmark rather than assuming smaller memory saves money.

---

# Monitoring Memory

CloudWatch Logs include memory metrics.

Example:

```text
REPORT RequestId: ...

Duration: 125 ms

Memory Size: 512 MB

Max Memory Used: 214 MB
```

Key metric:

```
Max Memory Used
```

---

# Choosing the Right Memory

General guidance:

| Workload | Recommended Starting Point |
|----------|-----------------------------|
| Lightweight API | 256–512 MB |
| CRUD API | 512–1024 MB |
| Image Processing | 1024–2048 MB |
| PDF Generation | 1024–2048 MB |
| Video Processing | 2048 MB+ |
| ML Inference | 4096 MB+ |

Always validate with performance testing.

---

# Memory Optimization

Good:

```python
for record in stream:
    process(record)
```

Bad:

```python
records = list(stream)

process(records)
```

Streaming data reduces memory usage.

---

# Temporary File Cleanup

Although `/tmp` is deleted when the execution environment is destroyed, remove unnecessary files during long-running executions.

Example:

```python
import os

os.remove("/tmp/report.csv")
```

---

# Common Mistakes

## Assuming More Memory Only Adds RAM

Incorrect.

Memory also increases:

- CPU
- Network
- Disk throughput

---

## Using /tmp as Permanent Storage

Incorrect.

`/tmp` exists only for the lifetime of the execution environment.

Use:

- S3
- DynamoDB
- EFS

for persistent storage.

---

## Choosing the Smallest Memory Setting

Smaller memory often results in:

- Slower execution
- Longer billing duration
- Higher latency

Benchmark before selecting a configuration.

---

# Best Practices

✅ Benchmark multiple memory configurations.

✅ Monitor **Max Memory Used** in CloudWatch.

✅ Use `/tmp` only for temporary data.

✅ Stream large files instead of loading everything into memory.

✅ Allocate enough memory for CPU-intensive workloads.

✅ Clean up temporary files when appropriate.

---

# Senior Backend Engineering Perspective

Senior backend engineers treat memory configuration as a **performance tuning parameter**, not merely a RAM setting.

Because memory controls CPU, network throughput, and disk performance, selecting the optimal configuration requires benchmarking under realistic production workloads.

Rather than minimizing memory, the goal is to minimize **overall latency and cost**. In many production systems, increasing memory reduces execution time enough that the total Lambda cost remains unchanged—or even decreases.

---

# Interview Questions

### Beginner

- What memory sizes are available for Lambda?
- Where are temporary files stored?
- Does `/tmp` persist forever?

### Intermediate

- Why does increasing memory improve CPU performance?
- What happens if a Lambda exceeds its memory allocation?
- Where can you find memory usage metrics?

### Senior

- Why can allocating more memory reduce Lambda costs?
- How would you benchmark the optimal memory configuration?
- When would you use `/tmp` versus Amazon EFS?
- How would you optimize a CPU-bound image processing Lambda?

---

# Key Takeaways

- Lambda memory is configurable from **128 MB to 10,240 MB**, and it also determines CPU allocation, network throughput, and disk I/O performance.
- Ephemeral storage (`/tmp`) is configurable up to **10 GB** and is intended for temporary data that persists only for the lifetime of the execution environment.
- Memory selection directly affects application performance and cost; benchmarking is essential to find the optimal configuration.
- Monitoring metrics such as **Max Memory Used** helps right-size functions and avoid both under-provisioning and unnecessary over-allocation.