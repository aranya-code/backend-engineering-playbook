# Performance Troubleshooting

## Overview

Redis is known for its exceptional performance, often handling **hundreds of thousands to millions of operations per second** with sub-millisecond latency. When performance degrades, the root cause is rarely Redis itself—it is usually a combination of workload characteristics, infrastructure limitations, application behavior, or configuration issues.

Common symptoms include:

- Increased response time
- CPU spikes
- Memory pressure
- High network latency
- Replica lag
- Slow client connections
- Reduced throughput
- Cache miss spikes

A structured troubleshooting methodology enables engineers to quickly isolate the bottleneck and restore optimal performance.

---

# Performance Troubleshooting Workflow

```
Users Report Slowness

        │

        ▼

Collect Metrics

        │

        ▼

Identify Bottleneck

        │

 ┌──────┼───────────┬───────────┐

 │      │           │           │

CPU   Memory     Network     Disk

 │      │           │           │

 ▼      ▼           ▼           ▼

Analyze Root Cause

        │

        ▼

Apply Fix

        │

        ▼

Benchmark

        │

        ▼

Monitor
```

---

# Step 1 — Verify Redis Health

Begin with

```bash
redis-cli INFO
```

Review:

- Server uptime
- Connected clients
- Operations per second
- Memory usage
- Replication status
- Persistence status

A healthy server eliminates many possible causes immediately.

---

# Step 2 — Check CPU Utilization

```bash
redis-cli INFO cpu
```

Linux

```bash
top
```

or

```bash
htop
```

High CPU usage may indicate:

- Expensive commands
- Large keys
- Lua scripts
- High request volume

---

# Step 3 — Check Memory

```bash
INFO memory
```

Important metrics

```text
used_memory

used_memory_peak

mem_fragmentation_ratio
```

Watch for

- High utilization
- Frequent evictions
- Fragmentation

---

# Step 4 — Check Latency

```bash
redis-cli --latency
```

Redis latency monitor

```bash
LATENCY LATEST
```

Typical healthy latency

```
< 1 ms
```

---

# Step 5 — Review Slow Log

```bash
SLOWLOG GET
```

Look for

- KEYS
- HGETALL
- Large LRANGE
- Lua scripts
- SORT

These frequently cause performance degradation.

---

# Step 6 — Check Connected Clients

```bash
CLIENT LIST
```

Monitor

- Connected clients
- Blocked clients
- Client buffers

Large output buffers often indicate slow consumers.

---

# Step 7 — Measure Throughput

```bash
INFO stats
```

Important metrics

```
instantaneous_ops_per_sec

total_commands_processed
```

Sudden throughput drops usually indicate a bottleneck elsewhere.

---

# CPU Bottlenecks

Typical causes

```
Large Keys

↓

Slow Commands

↓

High CPU

↓

High Latency
```

Mitigation

- Replace O(N) commands
- Reduce key size
- Optimize data structures

---

# Memory Bottlenecks

Symptoms

```
Memory Full

↓

Evictions

↓

Cache Misses

↓

Database Load
```

Monitor

```bash
INFO memory
```

---

# Network Bottlenecks

Architecture

```
Application

↓

Network

↓

Redis
```

Check

```bash
ping redis-server
```

Measure

```bash
mtr redis-server
```

Investigate

- Packet loss
- RTT
- DNS

---

# Disk Bottlenecks

Persistence operations depend on storage.

Monitor

```bash
iostat
```

Watch

- Write latency
- Queue depth
- Disk utilization

---

# Replication Bottlenecks

```bash
INFO replication
```

Monitor

- Replica lag
- Backlog size
- Network throughput

Heavy write workloads may delay replicas.

---

# Hot Keys

```
Millions of Clients

        │

        ▼

Single Key

        │

        ▼

CPU Spike
```

Find using

```bash
redis-cli --hotkeys
```

(Requires LFU eviction policy.)

Mitigation

- Sharding
- Local caching
- Replication

---

# Large Keys

Find

```bash
redis-cli --bigkeys
```

Large keys increase

- CPU
- Memory
- Network transfer

Split oversized structures.

---

# Connection Pool Problems

Poor design

```
Request

↓

New TCP Connection

↓

Disconnect
```

Better

```
Connection Pool

↓

Persistent Connections

↓

Redis
```

---

# Lua Scripts

Long-running Lua scripts block Redis.

Monitor execution time carefully.

Break complex scripts into smaller operations.

---

# Docker Performance

Monitor

```bash
docker stats
```

Verify

- CPU limits
- Memory limits
- Network

Avoid CPU throttling.

---

# Kubernetes Performance

Monitor

```bash
kubectl top pod redis
```

Check

```bash
kubectl describe pod redis
```

Look for

- OOMKilled
- CPU throttling
- Restart count

---

# AWS ElastiCache

Monitor CloudWatch

- EngineCPUUtilization
- DatabaseMemoryUsagePercentage
- CacheHits
- CacheMisses
- NetworkBytesIn
- NetworkBytesOut
- CurrConnections

Configure alerts before thresholds are reached.

---

# Benchmarking

Measure baseline performance

```bash
redis-benchmark
```

Example

```bash
redis-benchmark -q
```

Compare benchmark results after optimization.

---

# Performance Dashboard

Track

| Metric | Why It Matters |
|----------|----------------|
| CPU | Detect saturation |
| Memory | Prevent evictions |
| Latency | Measure responsiveness |
| Throughput | Detect bottlenecks |
| Cache Hit Ratio | Evaluate cache efficiency |
| Replication Lag | Monitor consistency |
| Network Traffic | Identify congestion |
| Connected Clients | Detect connection issues |

---

# End-to-End Diagnostic Flow

```
Slow Application

        │

        ▼

Redis Healthy?

        │

 ┌──────┴───────┐

 │              │

No             Yes

 │              │

Server       Network

 │              │

 ▼              ▼

CPU         Client

 │              │

 ▼              ▼

Memory      Database

 │              │

 ▼              ▼

Commands    Benchmark

 │

 ▼

Resolve
```

---

# Common Mistakes

## Looking Only at CPU

Performance problems often originate from memory, networking, or application design.

Always investigate multiple metrics together.

---

## Ignoring Slow Log

The Slow Log frequently identifies the exact root cause.

---

## No Baseline

Without baseline metrics, it's impossible to know whether performance has improved.

Benchmark regularly.

---

## Oversized Keys

Large keys affect CPU, memory, network, and replication simultaneously.

---

## Excessive Connections

Creating new connections for every request wastes CPU and increases latency.

Use pooling.

---

# Performance Investigation Checklist

```
✓ INFO reviewed

✓ CPU checked

✓ Memory checked

✓ Slow Log analyzed

✓ Latency measured

✓ Network tested

✓ Replication verified

✓ Benchmark completed

✓ Hot Keys analyzed

✓ Large Keys analyzed
```

---

# Best Practices

- Establish performance baselines before production deployment.
- Monitor CPU, memory, latency, and throughput together.
- Review the Slow Log regularly.
- Use connection pooling.
- Eliminate blocking commands.
- Continuously monitor cache hit ratios.
- Benchmark after every significant infrastructure or application change.
- Automate alerting for abnormal performance trends.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| CPU | Keep utilization below sustained saturation |
| Memory | Prevent frequent evictions |
| Latency | Monitor P95 and P99 response times |
| Networking | Keep Redis close to applications |
| Monitoring | Build comprehensive dashboards |
| Benchmarking | Test under production-like workloads |

---

# Production Considerations

For production environments:

- Create dashboards combining Redis metrics with application metrics.
- Alert on sustained CPU utilization, latency increases, memory pressure, and replication lag.
- Perform regular load testing to validate scaling assumptions.
- Use distributed tracing to correlate Redis latency with application requests.
- Maintain documented runbooks for common performance incidents.
- Review capacity planning quarterly based on growth trends.
- Continuously optimize workloads as data size and traffic evolve.

---

# Summary

Performance troubleshooting in Redis requires a holistic approach. CPU, memory, network, disk, persistence, replication, and application behavior all contribute to overall responsiveness. By collecting the right metrics, analyzing bottlenecks systematically, and validating improvements through benchmarking, engineers can maintain predictable, high-performance Redis deployments even under demanding production workloads.

---

# Key Takeaways

- Start every investigation with `INFO` and baseline metrics.
- Analyze CPU, memory, latency, network, and replication together.
- Use `SLOWLOG`, `LATENCY`, `--bigkeys`, and `--hotkeys` to identify workload issues.
- Benchmark before and after performance optimizations.
- Use connection pooling and avoid blocking commands.
- Build dashboards and alerts for proactive monitoring.
- Document troubleshooting workflows to reduce incident resolution time.
- Performance tuning is an ongoing operational practice, not a one-time task.