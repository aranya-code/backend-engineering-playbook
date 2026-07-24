# Redis Performance Cheat Sheet

## Overview

Performance is one of Redis's biggest strengths. However, achieving consistently low latency and high throughput requires proper data modeling, efficient commands, appropriate memory management, and continuous monitoring.

This cheat sheet summarizes the most important Redis performance concepts, optimization techniques, monitoring commands, and production best practices.

---

# Redis Performance Pillars

```
             Performance

      ┌─────────┼─────────┐

      ▼         ▼         ▼

 Memory     CPU       Network

      │         │         │

      ▼         ▼         ▼

 Commands  Data Model  Connections

      │         │         │

      └─────────┼─────────┘

                ▼

         Low Latency
```

---

# Performance Checklist

| Area | Check |
|------|-------|
| Memory | Avoid large keys |
| CPU | Avoid expensive commands |
| Network | Use pipelining |
| Data Structures | Choose the correct structure |
| Expiration | Configure proper TTLs |
| Monitoring | Enable metrics |
| Persistence | Balance durability vs performance |
| Scaling | Use Redis Cluster when necessary |

---

# Expected Performance

| Metric | Typical Value |
|---------|---------------|
| Read Latency | < 1 ms |
| Write Latency | < 1 ms |
| Throughput | Hundreds of thousands of ops/sec |
| Memory Access | Nanoseconds |
| Network Latency | Usually dominates request time |

---

# Time Complexity Cheat Sheet

| Command | Complexity |
|----------|------------|
| GET | O(1) |
| SET | O(1) |
| DEL | O(1) |
| HGET | O(1) |
| HSET | O(1) |
| LPUSH | O(1) |
| RPUSH | O(1) |
| SADD | O(1) |
| SISMEMBER | O(1) |
| ZADD | O(log N) |
| ZRANGE | O(log N) |
| KEYS | O(N) |
| SCAN | Incremental |

---

# Commands to Prefer

| Instead of | Use |
|-------------|-----|
| KEYS | SCAN |
| Large MGET loops | Pipeline |
| Individual SET calls | MSET |
| Large object Strings | Hashes |
| Polling | Pub/Sub or Streams |

---

# Dangerous Commands

| Command | Why |
|----------|-----|
| KEYS * | Blocks Redis |
| FLUSHALL | Deletes everything |
| FLUSHDB | Deletes database |
| MONITOR | High overhead |
| DEBUG | Administrative only |

---

# Pipelining

Without Pipeline

```
SET A

↓

Response

↓

SET B

↓

Response

↓

SET C

↓

Response
```

---

With Pipeline

```
SET A

SET B

SET C

↓

One Network Round Trip
```

Benefits

- Lower latency
- Higher throughput
- Fewer network calls

---

# Connection Pooling

Instead of

```
Request

↓

Open Connection

↓

Execute

↓

Close
```

Use

```
Connection Pool

↓

Reuse Existing Connections
```

Benefits

- Lower CPU usage
- Lower latency
- Better scalability

---

# Memory Optimization

## Use Appropriate Data Structures

| Bad | Better |
|------|--------|
| Large JSON String | Hash |
| Separate Keys | Hash |
| List for Rankings | Sorted Set |
| Set for Counting | HyperLogLog |

---

## Keep Values Small

Avoid

```
50 MB JSON
```

Prefer

```
Small Objects

↓

Hashes

↓

Logical Partitioning
```

---

## Configure Expiration

Example

```bash
SET session:101 token EX 1800
```

Temporary data should almost always have a TTL.

---

# Memory Monitoring

## Memory Usage

```bash
INFO MEMORY
```

---

## Key Memory

```bash
MEMORY USAGE user:101
```

---

## Memory Statistics

```bash
MEMORY STATS
```

---

## Memory Advisor

```bash
MEMORY DOCTOR
```

---

# Memory Fragmentation

Monitor

```bash
INFO MEMORY
```

Look at

```
mem_fragmentation_ratio
```

| Ratio | Meaning |
|---------|----------|
| ~1.0 | Excellent |
| 1.0–1.5 | Acceptable |
| >1.5 | Investigate |
| >2.0 | Serious |

---

# Slow Command Investigation

View Slow Log

```bash
SLOWLOG GET
```

Reset

```bash
SLOWLOG RESET
```

Typical causes

- KEYS
- Large SORT
- Huge Lua scripts
- Large collections

---

# Latency Investigation

Command

```bash
LATENCY DOCTOR
```

Also monitor

- CPU
- Network
- Clients
- Persistence

---

# CPU Optimization

Avoid

- KEYS
- Large Lua scripts
- Huge pipelines
- Massive SORT
- Large SMEMBERS

Prefer

- SCAN
- Incremental processing
- Pagination

---

# Network Optimization

Best practices

- Pipelining
- Connection pooling
- Deploy Redis close to applications
- Reduce payload size
- Compress large values when appropriate

---

# Cache Optimization

Good cache candidates

- Product catalog
- User profile
- Configuration
- API responses
- Feature flags

Poor cache candidates

- Frequently changing data
- Large binary files
- Permanent financial records

---

# Eviction Policies

| Policy | Description |
|----------|-------------|
| noeviction | Reject writes |
| allkeys-lru | Least Recently Used |
| allkeys-lfu | Least Frequently Used |
| volatile-lru | LRU for expiring keys |
| volatile-ttl | Shortest TTL first |

---

# Hot Keys

Symptoms

- High CPU
- Uneven load
- Increased latency

Solutions

```
Hot Key

↓

Replicas

↓

Local Cache

↓

Key Sharding

↓

CDN
```

---

# Large Keys

Find large keys using

```bash
redis-cli --bigkeys
```

Problems

- Slow replication
- High memory usage
- Slow persistence
- Increased latency

---

# Benchmarking

Basic

```bash
redis-benchmark
```

Concurrent clients

```bash
redis-benchmark -c 100
```

Pipeline

```bash
redis-benchmark -P 16
```

Custom requests

```bash
redis-benchmark -n 100000
```

---

# Replication Performance

Monitor

```bash
INFO REPLICATION
```

Watch

- Replica lag
- Sync status
- Connected replicas

---

# Cluster Performance

Check

```bash
CLUSTER INFO
```

Monitor

- Slot distribution
- Node balance
- Failover events
- Network traffic

---

# Monitoring Commands

| Command | Purpose |
|----------|----------|
| INFO | General information |
| INFO MEMORY | Memory |
| INFO CPU | CPU |
| INFO STATS | Statistics |
| INFO REPLICATION | Replication |
| MEMORY STATS | Memory |
| LATENCY DOCTOR | Latency |
| SLOWLOG GET | Slow commands |
| CLIENT LIST | Clients |

---

# Key Performance Metrics

| Metric | Target |
|----------|--------|
| Latency | <1 ms |
| Hit Ratio | >90% |
| Memory Usage | <80% |
| CPU Usage | Stable |
| Connected Clients | Within limits |
| Evictions | Minimal |
| Replica Lag | Near zero |

---

# Production Optimization Workflow

```text
High Latency

      │

      ▼

Check INFO

      │

      ▼

Check CPU

      │

      ▼

Check Memory

      │

      ▼

Slow Log

      │

      ▼

Hot Keys

      │

      ▼

Network

      │

      ▼

Optimize
```

---

# Performance Best Practices

- Choose the correct data structure.
- Prefer O(1) operations whenever possible.
- Use SCAN instead of KEYS.
- Enable connection pooling.
- Use pipelining for batch operations.
- Keep values reasonably small.
- Configure TTLs for temporary data.
- Monitor continuously.
- Benchmark before production changes.
- Scale horizontally with Redis Cluster when needed.

---

# Common Performance Mistakes

| Mistake | Better Approach |
|----------|-----------------|
| Using KEYS | Use SCAN |
| Huge JSON objects | Use Hashes |
| No TTL | Configure expiration |
| No monitoring | Monitor continuously |
| Opening new connections per request | Use connection pools |
| Ignoring Slow Log | Review regularly |
| Caching everything | Cache selectively |

---

# Performance Interview Tips

Senior interviewers often ask:

- Why is Redis fast?
- Why is KEYS dangerous?
- When should SCAN be used?
- How does pipelining improve performance?
- How do you investigate high CPU usage?
- What metrics would you monitor?
- How would you optimize a slow Redis deployment?

A strong answer should cover:

1. Root cause analysis.
2. Command complexity.
3. Memory considerations.
4. Network optimization.
5. Production monitoring.
6. Scalability trade-offs.