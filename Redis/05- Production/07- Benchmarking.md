# Benchmarking

## Overview

Redis is known for its exceptional speed, often processing **hundreds of thousands to millions of operations per second** on modern hardware. However, performance varies significantly depending on:

- Hardware
- Dataset size
- Network latency
- Data structures
- Persistence settings
- Number of clients
- Command mix
- Application design

Benchmarking helps answer questions such as:

- Can Redis handle my expected traffic?
- What is the maximum throughput?
- What is the latency under load?
- Is my Redis server correctly configured?
- Which configuration performs better?
- When should I scale?

Benchmarking is an essential part of capacity planning and production readiness.

---

# Why Benchmark Redis?

Suppose an application is expected to receive

```
500,000 Requests/Minute
```

Can Redis handle it?

Without benchmarking

```
Production Deployment

↓

Traffic Spike

↓

Unexpected Failure
```

With benchmarking

```
Load Test

↓

Capacity Analysis

↓

Infrastructure Planning

↓

Production Deployment
```

Benchmarking reduces deployment risk.

---

# What Should Be Measured?

A Redis benchmark should measure:

- Throughput
- Latency
- CPU utilization
- Memory usage
- Network bandwidth
- Connection scalability
- Replication performance
- Persistence overhead

---

# Benchmark Architecture

```
           Benchmark Client

                   │

                   ▼

            Redis Server

                   │

        CPU / Memory / Network

                   │

                   ▼

          Performance Metrics
```

---

# Important Metrics

| Metric | Description |
|----------|-------------|
| Throughput | Operations per second |
| Average Latency | Mean response time |
| P95 Latency | 95th percentile |
| P99 Latency | Worst-case latency |
| CPU Usage | Server utilization |
| Memory Usage | RAM consumption |
| Network Usage | Bandwidth |
| Errors | Failed requests |

---

# Throughput

Throughput measures

```
Operations

────────────

Second
```

Example

```
850,000 ops/sec
```

Higher throughput generally indicates better performance.

---

# Latency

Latency measures how quickly Redis responds.

```
Request

↓

Redis

↓

Response
```

Typical production latency

```
< 1 ms
```

High latency often indicates bottlenecks.

---

# Percentile Latency

Average latency alone is misleading.

Example

```
Average

0.5 ms
```

But

```
P99

15 ms
```

Users experience the slower requests.

Always monitor:

- P50
- P95
- P99

---

# Redis Benchmark Tool

Redis includes

```bash
redis-benchmark
```

Example

```bash
redis-benchmark
```

Default benchmark

```
50 Clients

100000 Requests
```

---

# Basic Benchmark

```bash
redis-benchmark -q
```

Example output

```
PING_INLINE

SET

GET

INCR

LPUSH
```

Each command displays operations per second.

---

# Benchmark Specific Commands

Only benchmark GET

```bash
redis-benchmark GET -q
```

Only benchmark SET

```bash
redis-benchmark SET -q
```

Useful for workload-specific testing.

---

# Number of Requests

Increase requests

```bash
redis-benchmark -n 1000000
```

Meaning

```
1 Million Requests
```

Longer benchmarks produce more stable results.

---

# Concurrent Clients

Example

```bash
redis-benchmark -c 200
```

Meaning

```
200 Concurrent Clients
```

Useful for API workloads.

---

# Data Size

Example

```bash
redis-benchmark -d 1024
```

Meaning

```
1 KB Values
```

Larger payloads reduce throughput.

---

# Pipeline Benchmark

Example

```bash
redis-benchmark -P 16
```

Pipeline

```
16 Commands

↓

One Network Trip
```

Pipeline benchmarks demonstrate the impact of batching.

---

# Combined Example

```bash
redis-benchmark \
-c 200 \
-n 1000000 \
-d 512 \
-P 8
```

Meaning

- 200 clients
- 1 million requests
- 512-byte values
- Pipeline of 8

---

# TLS Benchmark

Benchmark encrypted connections

```bash
redis-benchmark --tls
```

Compare

```
Without TLS

↓

Higher Throughput
```

```
With TLS

↓

Higher Security

↓

Slight CPU Overhead
```

---

# Persistence Benchmark

Benchmark

```
Persistence OFF
```

Then

```
RDB
```

Then

```
AOF everysec
```

Then

```
AOF always
```

Compare performance.

---

# Benchmark Workflow

```
Baseline

↓

Configuration Change

↓

Benchmark

↓

Compare

↓

Deploy
```

Never deploy tuning changes without testing.

---

# Measuring Resource Usage

During benchmarking monitor

```
CPU

Memory

Disk

Network
```

Redis may appear fast while exhausting system resources.

---

# Benchmarking Read Workloads

```
GET

MGET

HGET

ZRANGE
```

Measure

- Throughput
- Latency
- Cache hit ratio

---

# Benchmarking Write Workloads

```
SET

INCR

LPUSH

HSET
```

Measure

- Write latency
- Replication delay
- Persistence impact

---

# Mixed Workloads

Production rarely performs only reads.

Example

```
80% Reads

20% Writes
```

Mixed benchmarks better represent real applications.

---

# Connection Scaling Benchmark

Increase

```
Clients

↓

50

↓

200

↓

500

↓

1000
```

Observe

- Latency
- CPU
- Errors

---

# Large Dataset Benchmark

Benchmark with realistic datasets.

Poor

```
100 Keys
```

Better

```
10 Million Keys
```

Dataset size affects:

- Memory
- Eviction
- Cache locality

---

# Cluster Benchmark

```
Benchmark Client

↓

Redis Cluster

↓

Node 1

Node 2

Node 3
```

Measure

- Slot routing
- Cluster latency
- Cross-node performance

---

# Replica Benchmark

Measure

```
Primary

↓

Writes
```

```
Replica

↓

Reads
```

Compare

- Read throughput
- Replication lag

---

# Network Benchmark

Sometimes Redis is not the bottleneck.

```
Application

↓

Slow Network

↓

Redis
```

Network latency increases response time.

Benchmark Redis close to the application.

---

# Application Benchmark

Do not benchmark only Redis.

Benchmark

```
User

↓

API

↓

Redis

↓

Database
```

End-to-end benchmarks reveal the real bottlenecks.

---

# Load Testing vs Stress Testing

| Test | Purpose |
|------|----------|
| Load Testing | Expected production traffic |
| Stress Testing | Beyond expected limits |
| Spike Testing | Sudden traffic increase |
| Soak Testing | Long-duration stability |

Each serves a different purpose.

---

# Benchmark Comparison

Example

| Configuration | Throughput | Latency |
|--------------|-----------:|---------:|
| No Pipeline | 120,000 ops/sec | 1.8 ms |
| Pipeline (8) | 520,000 ops/sec | 0.6 ms |
| Pipeline (32) | 810,000 ops/sec | 0.3 ms |

Benchmark data should guide optimization decisions.

---

# Capacity Planning

Suppose

```
Current

250,000 ops/sec
```

Expected growth

```
3×

↓

750,000 ops/sec
```

Infrastructure should be sized before reaching capacity.

---

# Benchmark Environment

Avoid benchmarking on:

- Shared laptops
- Development servers
- Busy production systems

Preferred

```
Dedicated Test Environment

↓

Same Hardware

↓

Same Configuration

↓

Repeatable Results
```

---

# Automating Benchmarks

Example CI/CD workflow

```
Configuration Change

↓

Automated Benchmark

↓

Compare Baseline

↓

Pass?

├── Yes

│

▼

Deploy

│

└── No

↓

Reject Change
```

Performance regressions are detected before production.

---

# Common Benchmark Mistakes

## Benchmarking on an Empty Dataset

Real workloads involve millions of keys.

---

## Ignoring Network Latency

A remote benchmark may measure network performance rather than Redis.

---

## Measuring Only Throughput

High throughput with poor P99 latency is unacceptable.

---

## Benchmarking Production During Peak Hours

Can impact real users.

Use staging or dedicated environments.

---

## Running a Single Test

Always repeat benchmarks multiple times.

Average the results.

---

# Best Practices

- Benchmark using realistic datasets and traffic patterns.
- Measure throughput and latency together.
- Include P95 and P99 latency in every report.
- Benchmark after every significant configuration change.
- Test persistence settings independently.
- Monitor CPU, memory, and network during benchmarks.
- Compare results against established baselines.
- Automate performance regression testing whenever possible.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Clients | Simulate production concurrency |
| Dataset | Use realistic key counts |
| Pipelines | Measure batching improvements |
| Persistence | Benchmark different durability settings |
| Network | Minimize latency during testing |
| Monitoring | Collect infrastructure metrics alongside Redis metrics |

---

# Production Considerations

For production environments:

- Maintain a historical benchmark baseline for every Redis version and hardware configuration.
- Execute benchmarks after operating system, Redis, or infrastructure upgrades.
- Validate cluster performance separately from standalone deployments.
- Benchmark application workloads instead of relying solely on synthetic Redis commands.
- Incorporate benchmarking into release validation and capacity planning processes.
- Document benchmark methodology so results are repeatable and comparable over time.

---

# Summary

Benchmarking provides objective data about Redis performance under realistic workloads. By measuring throughput, latency, concurrency, resource utilization, and persistence overhead, engineering teams can validate infrastructure capacity, compare configurations, and detect performance regressions before production deployment. Effective benchmarking is an ongoing practice that supports scalability, reliability, and informed architectural decisions.

---

# Key Takeaways

- Benchmark Redis before deploying major changes.
- Measure both throughput and latency, including P95 and P99.
- Use `redis-benchmark` for synthetic testing and application-level tests for real-world validation.
- Simulate realistic workloads with appropriate concurrency and dataset sizes.
- Monitor CPU, memory, network, and persistence during benchmarks.
- Compare benchmark results against established baselines.
- Automate benchmark execution where practical.
- Treat benchmarking as a continuous part of performance engineering rather than a one-time activity.