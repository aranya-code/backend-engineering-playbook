# Slow Commands

## Overview

Redis is designed to execute most operations in **O(1)** or **O(log N)** time, allowing millions of operations per second on modern hardware.

However, not all Redis commands are equally efficient. Some commands perform linear scans or operate on entire data structures, causing:

- Increased latency
- CPU spikes
- Blocked clients
- Replication lag
- Failover events
- Application slowdowns

In production, even a single poorly chosen command can affect every connected client because Redis processes commands using a **single-threaded event loop** (for command execution).

This chapter explains how to identify, diagnose, and optimize slow Redis commands.

---

# Why Slow Commands Matter

Redis executes commands sequentially.

```
              Client A

                 │

                 ▼

          Slow Command (5 sec)

                 │

                 ▼

        Every Other Client Waits

                 │

      ┌──────────┴──────────┐

      ▼                     ▼

   Client B             Client C

        Waiting...
```

One expensive command blocks all subsequent commands until it completes.

---

# Identifying Slow Commands

Redis provides the **Slow Log** feature.

Unlike normal logs, Slow Log records commands that exceed a configurable execution threshold.

View slow commands

```bash
SLOWLOG GET
```

View total entries

```bash
SLOWLOG LEN
```

Reset log

```bash
SLOWLOG RESET
```

---

# Configure Slow Log

Check configuration

```bash
CONFIG GET slowlog-log-slower-than
```

Example

```text
10000
```

Value is measured in

```
Microseconds
```

Example

| Value | Meaning |
|--------|----------|
| 1000 | 1 ms |
| 5000 | 5 ms |
| 10000 | 10 ms |

---

# Slow Log Entry

Example

```text
1

1722159000

15432

KEYS *

127.0.0.1:53411
```

Fields

- ID
- Timestamp
- Duration
- Command
- Client

---

# Complexity Matters

Redis command performance depends on algorithmic complexity.

| Complexity | Example |
|------------|----------|
| O(1) | GET, SET, INCR |
| O(log N) | ZADD |
| O(N) | KEYS, LRANGE |
| O(N log N) | SORT |
| O(N²) | Some Lua operations |

Avoid O(N) operations on very large datasets.

---

# Common Slow Commands

| Command | Complexity | Production Risk |
|----------|------------|-----------------|
| KEYS | O(N) | High |
| HGETALL | O(N) | Medium |
| LRANGE | O(N) | Medium |
| SMEMBERS | O(N) | High |
| ZRANGE | O(log N + M) | Medium |
| SORT | O(N log N) | High |
| SUNION | O(N) | Medium |
| FLUSHALL | O(N) | Critical |

---

# KEYS

Worst practice

```bash
KEYS *
```

Workflow

```
Entire Database

↓

Sequential Scan

↓

Return All Keys
```

Large databases

↓

CPU spike

↓

Latency

Never use

```
KEYS *
```

in production.

---

# Better Alternative

Use

```bash
SCAN
```

Example

```bash
SCAN 0 MATCH user:* COUNT 100
```

Workflow

```
Database

↓

Small Batch

↓

Next Cursor

↓

Continue
```

SCAN is incremental and non-blocking.

---

# HGETALL

Bad

```bash
HGETALL huge_hash
```

If a hash contains millions of fields,

execution time increases dramatically.

Alternative

```bash
HSCAN
```

---

# LRANGE

Bad

```bash
LRANGE logs 0 -1
```

Large lists

↓

Entire list returned

Better

```bash
LRANGE logs 0 100
```

Retrieve only the required range.

---

# SMEMBERS

Bad

```bash
SMEMBERS users
```

Large sets may contain millions of members.

Alternative

```bash
SSCAN users
```

---

# ZRANGE

Sorted sets are efficient,

but returning very large ranges is expensive.

Bad

```bash
ZRANGE leaderboard 0 -1
```

Better

```bash
ZRANGE leaderboard 0 100
```

---

# SORT

Example

```bash
SORT users
```

Sorting large collections consumes CPU.

Whenever possible,

maintain sorted data using

```
Sorted Sets
```

instead.

---

# Lua Scripts

Long-running scripts block Redis.

```
Lua Script

↓

Redis Busy

↓

Clients Wait
```

Monitor script duration carefully.

---

# Large Keys

Example

```
100 MB Hash

↓

HGETALL

↓

Slow Response
```

Find large keys

```bash
redis-cli --bigkeys
```

---

# Slow Log Workflow

```
Application Slow

        │

        ▼

SLOWLOG GET

        │

        ▼

Identify Command

        │

        ▼

Analyze Complexity

        │

        ▼

Replace Command

        │

        ▼

Verify Performance
```

---

# Monitor Latency

Use

```bash
LATENCY LATEST
```

History

```bash
LATENCY HISTORY command
```

Graph

```bash
LATENCY GRAPH command
```

---

# CPU Utilization

Monitor

```bash
INFO cpu
```

High CPU often accompanies expensive commands.

---

# Memory Impact

Commands returning large datasets consume additional memory.

Monitor

```bash
INFO memory
```

---

# Network Impact

Returning millions of records

↓

Large packets

↓

Network congestion

↓

Client timeouts

Slow commands often become network problems.

---

# Replication Impact

Slow commands delay replication.

```
Primary

↓

Slow Command

↓

Replication Delay

↓

Replica Lag
```

Monitor

```bash
INFO replication
```

---

# Docker Considerations

Monitor

```bash
docker stats
```

Watch

- CPU
- Memory
- Network

Container resource limits may amplify slow command effects.

---

# Kubernetes Considerations

Monitor

```bash
kubectl top pod redis
```

Also inspect

```bash
kubectl logs redis
```

Look for

- CPU throttling
- Memory pressure
- OOMKilled events

---

# AWS ElastiCache

Monitor CloudWatch

- EngineCPUUtilization
- CacheHits
- CacheMisses
- CurrConnections
- NetworkBytesIn
- NetworkBytesOut

Investigate latency spikes alongside Slow Log entries.

---

# Useful Commands

Slow Log

```bash
SLOWLOG GET
```

Latency

```bash
LATENCY LATEST
```

Memory

```bash
INFO memory
```

CPU

```bash
INFO cpu
```

Replication

```bash
INFO replication
```

Large keys

```bash
redis-cli --bigkeys
```

---

# Diagnostic Workflow

```
High Latency

        │

        ▼

SLOWLOG GET

        │

        ▼

Identify Command

        │

        ▼

Large Dataset?

        │

 ┌──────┴───────┐

 │              │

Yes             No

 │              │

Optimize     Check CPU

 │              │

 ▼              ▼

SCAN        Memory

 │              │

 ▼              ▼

Verify       Network
```

---

# Common Mistakes

## Using KEYS in Production

Replace

```
KEYS *
```

with

```
SCAN
```

---

## Returning Entire Collections

Retrieve only the required data instead of entire hashes, lists, or sets.

---

## Ignoring Slow Log

Slow Log is one of Redis' most valuable troubleshooting tools.

Review it regularly.

---

## Oversized Keys

Large keys increase command execution time and network transfer size.

---

## Long Lua Scripts

Break complex processing into smaller operations whenever possible.

---

# Best Practices

- Enable and monitor the Slow Log.
- Replace blocking commands with incremental alternatives.
- Limit the number of returned records.
- Use `SCAN`, `HSCAN`, `SSCAN`, and `ZSCAN` instead of full scans.
- Review command complexity before introducing new features.
- Continuously monitor CPU, memory, and latency metrics.
- Regularly identify and optimize large keys.
- Benchmark application changes before deploying to production.

---

# Performance Considerations

| Area | Recommendation |
|------|----------------|
| Slow Log | Review regularly |
| Command Complexity | Prefer O(1) or O(log N) operations |
| Large Keys | Split oversized structures |
| Network | Limit response sizes |
| CPU | Monitor expensive operations |
| Monitoring | Correlate latency with Slow Log |

---

# Production Considerations

For production deployments:

- Configure the Slow Log with an appropriate threshold (for example, **5–10 ms** depending on workload).
- Integrate Slow Log analysis into observability platforms such as Prometheus and Grafana.
- Alert on sustained increases in slow command frequency.
- Review command complexity during code reviews.
- Perform load testing with production-scale datasets to uncover expensive operations before release.
- Maintain runbooks describing how to identify and optimize slow commands.
- Periodically analyze large keys and command patterns as part of performance tuning.

---

# Summary

Slow Redis commands are a frequent cause of latency, CPU spikes, and degraded application performance. Because Redis executes commands sequentially, a single expensive operation can impact every connected client. By understanding command complexity, monitoring the Slow Log, replacing blocking operations with incremental alternatives, and continuously analyzing performance metrics, teams can keep Redis responsive even under heavy production workloads.

---

# Key Takeaways

- Redis command execution is sequential—one slow command affects all clients.
- Use `SLOWLOG GET` to identify expensive operations.
- Replace `KEYS`, `SMEMBERS`, and `HGETALL` with `SCAN`-based alternatives where appropriate.
- Avoid returning entire collections unless absolutely necessary.
- Monitor CPU, memory, replication, and latency together.
- Benchmark production workloads using realistic data volumes.
- Treat Slow Log analysis as a routine operational practice, not just an incident response tool.
- Understanding command complexity is essential for building scalable Redis applications.